import psycopg
from neo4j import GraphDatabase

import config

# The Neo4j driver is safe to share for the whole app, so we make it once.
neo4j_driver = GraphDatabase.driver(
    config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)


def pg_connect():
    """Open a new PostgreSQL connection."""
    return psycopg.connect(config.DATABASE_URL)


def init_tables():
    """Create the pgvector extension and the 'chunks' table if they don't exist."""
    with pg_connect() as conn, conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id        SERIAL PRIMARY KEY,
                source    TEXT,
                content   TEXT,
                embedding vector({config.EMBED_SIZE})
            )
            """
        )
        conn.commit()


def neo4j_run(query, params=None):
    """Run a Cypher query in Neo4j and return the rows as a list of dicts.

    Values are always passed as `params` (never glued into the query text),
    which keeps the queries safe.
    """
    with neo4j_driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]
