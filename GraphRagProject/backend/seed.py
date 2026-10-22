#==========================================================#
# Data Ingestion and Seeding Script for Neo4j and Postgres #
#==========================================================#

#========#
# Step-1 #
#========#
# This script populates the Neo4j graph database with sample employee data and their relationships, as well as ingests documents into a Postgres database for vector search.
# The script defines a set of sample employees, their departments, skills, and projects, and establishes relationships between them in the Neo4j database. 

import os

from db import neo4j_run, pg_connect
from rag import embed

# ── The sample people. Each person is a simple dictionary. ───────────────
# "manager" is who they report to (None = no manager).
EMPLOYEES = [
    {"name": "Rahul", "title": "Engineering Manager", "dept": "Generative AI",
     "manager": None, "skills": ["Python", "Neo4j"], "projects": ["Knowledge Assistant"]},
    {"name": "Amit", "title": "AI Engineer", "dept": "Generative AI",
     "manager": "Rahul", "skills": ["Python", "Neo4j", "RAG"], "projects": ["Knowledge Assistant"]},
    {"name": "Neha", "title": "AI Engineer", "dept": "Generative AI",
     "manager": "Rahul", "skills": ["Python", "pgvector", "RAG"], "projects": ["Knowledge Assistant"]},
    {"name": "Priya", "title": "Data Science Manager", "dept": "Data Science",
     "manager": None, "skills": ["Python", "Machine Learning"], "projects": ["Recommendation Engine"]},
    {"name": "Rohan", "title": "Data Scientist", "dept": "Data Science",
     "manager": "Priya", "skills": ["Python", "Machine Learning"], "projects": ["Recommendation Engine"]},
    {"name": "Sanjana", "title": "Data Scientist", "dept": "Data Science",
     "manager": "Priya", "skills": ["Python", "SQL"], "projects": ["Recommendation Engine"]},
    {"name": "Arjun", "title": "Engineering Manager", "dept": "Engineering",
     "manager": None, "skills": ["Python", "Docker"], "projects": ["CRM System"]},
    {"name": "Aditya", "title": "Backend Engineer", "dept": "Engineering",
     "manager": "Arjun", "skills": ["Python", "FastAPI", "Docker"], "projects": ["CRM System"]},
]

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "documents")

def build_graph():
    """Create all people, departments, projects, skills and their relationships."""
    # Start empty so we can run this again without making duplicates.
    neo4j_run("MATCH (n) DETACH DELETE n")

    for person in EMPLOYEES:
        # Create the employee and their department, and connect them.
        neo4j_run(
            """
            MERGE (e:Employee {name: $name}) SET e.title = $title
            MERGE (d:Department {name: $dept})
            MERGE (e)-[:WORKS_IN]->(d)
            """,
            {"name": person["name"], "title": person["title"], "dept": person["dept"]},
        )
        # Connect to their manager (if they have one).
        if person["manager"]:
            neo4j_run(
                """
                MATCH (e:Employee {name: $name})
                MATCH (m:Employee {name: $manager})
                MERGE (e)-[:REPORTS_TO]->(m)
                """,
                {"name": person["name"], "manager": person["manager"]},
            )
        # Connect to each skill.
        for skill in person["skills"]:
            neo4j_run(
                """
                MATCH (e:Employee {name: $name})
                MERGE (s:Skill {name: $skill})
                MERGE (e)-[:HAS_SKILL]->(s)
                """,
                {"name": person["name"], "skill": skill},
            )
        # Connect to each project (and link the project to the department).
        for project in person["projects"]:
            neo4j_run(
                """
                MATCH (e:Employee {name: $name})
                MATCH (d:Department {name: $dept})
                MERGE (p:Project {name: $project})
                MERGE (e)-[:WORKS_ON]->(p)
                MERGE (p)-[:BELONGS_TO]->(d)
                """,
                {"name": person["name"], "dept": person["dept"], "project": project},
            )
            
#========#
# Step-2 #
#========#
# It reads markdown documents, splits them into chunks, generates embeddings for each chunk, 
# and stores them in a Postgres database.

def split_text(text, size=400):
    """Cut a long text into smaller pieces of about `size` characters each."""
    text = " ".join(text.split())  # tidy up spaces and newlines
    return [text[i : i + size] for i in range(0, len(text), size)]



def ingest_documents():
    """Read every .md file, split it, embed each chunk, and store it in Postgres."""
    with pg_connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM chunks")  # start fresh

        for filename in sorted(os.listdir(DOCUMENTS_DIR)):
            if not filename.endswith(".md"):
                continue
            path = os.path.join(DOCUMENTS_DIR, filename)
            with open(path, encoding="utf-8") as f:
                text = f.read()

            for chunk in split_text(text):
                vector = embed(chunk)  # turn the chunk into a list of numbers
                vector_str = "[" + ",".join(str(x) for x in vector) + "]"
                cur.execute(
                    "INSERT INTO chunks (source, content, embedding) VALUES (%s, %s, %s)",
                    (filename, chunk, vector_str),
                )
        conn.commit()
        
        
def seed_all():
    """Build the graph and ingest the documents. Returns a small summary."""
    build_graph()
    ingest_documents()
    return {"people": len(EMPLOYEES), "documents": 4}
