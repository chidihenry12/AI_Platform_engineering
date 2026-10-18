import os

from dotenv import load_dotenv

load_dotenv()  # load a .env file if one exists

# PostgreSQL (used with the pgvector extension to search documents by meaning).
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/simple_rag"
)

# Neo4j (the graph database that stores people and their relationships).
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# OpenAI (used to create embeddings and to write the final answer).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_SIZE = 1536  # text-embedding-3-small produces vectors of this length