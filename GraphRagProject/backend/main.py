from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import db
import rag
import seed


@asynccontextmanager
async def lifespan(app):
    # Make sure the Postgres table exists when the app starts.
    db.init_tables()
    yield
    
app = FastAPI(title="Simple Graph RAG", version="1.0", lifespan=lifespan)

class Question(BaseModel):
    question: str
    

@app.get("/health")
def health():
    """Check that both databases are reachable."""
    try:
        db.neo4j_run("RETURN 1")
        neo4j_ok = True
    except Exception:
        neo4j_ok = False
    try:
        with db.pg_connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        postgres_ok = True
    except Exception:
        postgres_ok = False
    return {"neo4j": neo4j_ok, "postgres": postgres_ok}

@app.post("/seed")
def seed_data():
    """Load the sample graph and documents. Run this once at the start."""
    return seed.seed_all()

@app.get("/employees")
def list_employees():
    """List every employee with their title and department."""
    return db.neo4j_run(
        """
        MATCH (e:Employee)
        OPTIONAL MATCH (e)-[:WORKS_IN]->(d:Department)
        RETURN e.name AS name, e.title AS title, d.name AS department
        ORDER BY e.name
        """
    )

@app.get("/employees/{name}")
def get_employee(name: str):
    """Show one employee and all of their relationships."""
    rows = db.neo4j_run(
        """
        MATCH (e:Employee {name: $name})
        OPTIONAL MATCH (e)-[:WORKS_IN]->(d:Department)
        OPTIONAL MATCH (e)-[:REPORTS_TO]->(m:Employee)
        OPTIONAL MATCH (e)-[:HAS_SKILL]->(s:Skill)
        OPTIONAL MATCH (e)-[:WORKS_ON]->(p:Project)
        OPTIONAL MATCH (r:Employee)-[:REPORTS_TO]->(e)
        RETURN e.name AS name, e.title AS title, d.name AS department,
               m.name AS manager,
               collect(DISTINCT s.name) AS skills,
               collect(DISTINCT p.name) AS projects,
               collect(DISTINCT r.name) AS reports
        """,
        {"name": name},
    )
    return rows[0] if rows else {"error": "Employee not found"}

@app.get("/projects")
def list_projects():
    """List every project with its department and team."""
    return db.neo4j_run(
        """
        MATCH (p:Project)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(d:Department)
        OPTIONAL MATCH (e:Employee)-[:WORKS_ON]->(p)
        RETURN p.name AS name, d.name AS department, collect(e.name) AS team
        ORDER BY p.name
        """
    )
    
@app.get("/documents")
def list_documents():
    """List the ingested documents and how many chunks each produced."""
    with db.pg_connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT source, count(*) FROM chunks GROUP BY source ORDER BY source")
        rows = cur.fetchall()
    return [{"source": r[0], "chunks": r[1]} for r in rows]



@app.post("/ask")
def ask_question(body: Question):
    """Ask a question — this runs the Graph RAG pipeline (graph + documents + LLM)."""
    return rag.ask(body.question)