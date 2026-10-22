from openai import OpenAI

import config
from db import neo4j_run, pg_connect


client = OpenAI(api_key=config.OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are a helpful Employee Knowledge Assistant. "
    "Answer the question using ONLY the graph facts and document text provided. "
    "Do not make up people, projects or skills. "
    "If the information is not there, say you don't have enough information. "
    "Keep the answer short and clear."
)


def embed(text):
    """Turn a piece of text into a list of numbers (its embedding)."""
    response = client.embeddings.create(model=config.EMBED_MODEL, input=text)
    return response.data[0].embedding


def _names_of(label):
    """Return all names of a given node type, e.g. every Employee name."""
    rows = neo4j_run(f"MATCH (n:{label}) RETURN n.name AS name")
    return [row["name"] for row in rows]

#======================================================================================#
# We have 2 Main Tasks:                                                                #
# 1. Graph search: find known names in the question and fetch their relationships.     #
# 2. Vector search: find the document chunks whose meaning is closest to the question. #
#======================================================================================#

def graph_search(question):
    """Look for known names in the question and fetch their relationships.

    Returns a list of short, human-readable fact sentences.
    """
    q = question.lower()
    facts = []

    # 1. Any employee mentioned? -> department, manager, skills, projects, reports.
    for name in _names_of("Employee"):
        if name.lower() in q:
            rows = neo4j_run(
                """
                MATCH (e:Employee {name: $name})
                OPTIONAL MATCH (e)-[:WORKS_IN]->(d:Department)
                OPTIONAL MATCH (e)-[:REPORTS_TO]->(m:Employee)
                OPTIONAL MATCH (e)-[:HAS_SKILL]->(s:Skill)
                OPTIONAL MATCH (e)-[:WORKS_ON]->(p:Project)
                OPTIONAL MATCH (r:Employee)-[:REPORTS_TO]->(e)
                RETURN d.name AS department, m.name AS manager,
                       collect(DISTINCT s.name) AS skills,
                       collect(DISTINCT p.name) AS projects,
                       collect(DISTINCT r.name) AS reports
                """,
                {"name": name},
            )[0]
            if rows["department"]:
                facts.append(f"{name} works in the {rows['department']} team.")
            if rows["manager"]:
                facts.append(f"{name} reports to {rows['manager']}.")
            if rows["skills"]:
                facts.append(f"{name} knows {', '.join(rows['skills'])}.")
            if rows["projects"]:
                facts.append(f"{name} works on {', '.join(rows['projects'])}.")
            if rows["reports"]:
                facts.append(f"{', '.join(rows['reports'])} report to {name}.")

    # 2. Any project mentioned? -> who is on the team.
    for project in _names_of("Project"):
        if project.lower() in q:
            rows = neo4j_run(
                """
                MATCH (e:Employee)-[:WORKS_ON]->(p:Project {name: $project})
                RETURN collect(e.name) AS team
                """,
                {"project": project},
            )[0]
            if rows["team"]:
                facts.append(f"The {project} team is: {', '.join(rows['team'])}.")

    # 3. Any skill mentioned? -> who has that skill.
    for skill in _names_of("Skill"):
        if skill.lower() in q:
            rows = neo4j_run(
                """
                MATCH (e:Employee)-[:HAS_SKILL]->(s:Skill {name: $skill})
                RETURN collect(e.name) AS people
                """,
                {"skill": skill},
            )[0]
            if rows["people"]:
                facts.append(f"People who know {skill}: {', '.join(rows['people'])}.")

    return facts



def vector_search(question, k=3):
    """Find the document chunks whose meaning is closest to the question."""
    vector = embed(question)
    vector_str = "[" + ",".join(str(x) for x in vector) + "]"

    with pg_connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT source, content, 1 - (embedding <=> %s::vector) AS score
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (vector_str, vector_str, k),
        )
        rows = cur.fetchall()

    return [
        {"source": row[0], "content": row[1], "score": round(row[2], 2)}
        for row in rows
    ]



def ask(question):
    """Run the full pipeline and return the answer plus the evidence used."""
    facts = graph_search(question)          # step 1: graph
    documents = vector_search(question)     # step 2: documents

    # Build one simple context text from both sources.
    context = "GRAPH FACTS:\n"
    context += "\n".join("- " + f for f in facts) if facts else "- (none)"
    context += "\n\nDOCUMENT TEXT:\n"
    context += "\n".join(f"- ({d['source']}) {d['content']}" for d in documents)

    # step 3: let the LLM write the final answer from that context.
    response = client.chat.completions.create(
        model=config.CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\nQuestion: {question}"},
        ],
    )
    answer = response.choices[0].message.content

    return {"answer": answer, "graph_facts": facts, "documents": documents}
