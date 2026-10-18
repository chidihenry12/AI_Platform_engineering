# 🧠 Simple Graph RAG: Employee Knowledge Assistant

A small **Graph RAG** application that answers questions about employees, projects and skills by combining two kinds of retrieval:

1. **Graph search (Neo4j)** for structured relationships: who reports to whom, who works on which project, who knows which skill.
2. **Vector search (PostgreSQL + pgvector)** for unstructured text: the meaning of project notes and profiles.
3. **LLM (OpenAI `gpt-4o-mini`)** reads both and writes a short, grounded answer.

| Layer | Tech | Port |
|---|---|---|
| Frontend | Streamlit | `8501` |
| Backend API | FastAPI + Uvicorn | `8000` |
| Graph DB | Neo4j 5.22 | `7474` (browser), `7687` (bolt) |
| Vector DB | PostgreSQL 16 + pgvector | `5432` |
| LLM / Embeddings | OpenAI `gpt-4o-mini`, `text-embedding-3-small` (1536-dim) | n/a |

---

## 📁 Project structure

```
GraphRagProject/
├── .env                      # OPENAI_API_KEY (not committed)
├── docker-compose.yml        # postgres + neo4j + backend + frontend
├── backend/
│   ├── main.py               # FastAPI app & endpoints
│   ├── rag.py                # graph_search, vector_search, ask() pipeline
│   ├── seed.py               # builds the Neo4j graph + ingests documents into pgvector
│   ├── db.py                 # Neo4j driver, Postgres connection, table creation
│   ├── config.py             # env vars & model settings
│   ├── documents/*.md        # sample docs that get chunked + embedded
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── app.py                # Streamlit UI
    ├── requirements.txt
    └── Dockerfile
```

---

## ✅ Prerequisites

- **Docker Desktop** (with Docker Compose v2), running
- **OpenAI API key**
- *(Only for Option B)* **Python 3.11**

---

## ⚙️ Configure the API key

Create or edit `.env` in the project root:

```env
OPENAI_API_KEY=sk-...your-key...
```

> Keep it as `KEY=value` with **no spaces around `=`**. Some tools read `OPENAI_API_KEY =...` as a different variable name, which leaves the key empty.

Optional overrides (defaults are in `backend/config.py`):

```env
CHAT_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/simple_rag
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

---

## 🚀 Option A: Run everything with Docker (recommended)

From the project root:

```bash
docker compose up --build
```

Wait until `backend` logs `Uvicorn running on http://0.0.0.0:8000`. Then open:

| What | URL |
|---|---|
| Streamlit UI | http://localhost:8501 |
| FastAPI Swagger docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 (login `neo4j` / `password123`) |

Stop the app with `Ctrl+C`, or tear everything down with:

```bash
docker compose down        # stop containers
docker compose down -v     # stop + delete database volumes
```

---

## 🛠️ Option B: Run backend & frontend locally (for development)

Use Docker only for the two databases, and run the Python apps on your machine so you can edit and debug them.

**1. Start the databases**

```bash
docker compose up -d postgres neo4j
```

**2. Backend** (terminal 1, Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

`config.py` calls `load_dotenv()`, which finds the root `.env`. The DB URLs default to `localhost`.

**3. Frontend** (terminal 2)

```powershell
cd frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

`BACKEND_URL` defaults to `http://localhost:8000`.

---

## ▶️ Using the app

1. Open http://localhost:8501.
2. Click **① Load sample data**. This calls `POST /seed`, which builds the graph and embeds the documents. Run it once; running it again resets the data cleanly.
3. Ask a question, or click a sample:
   - *Who reports to Rahul?*
   - *Who works on the Knowledge Assistant?*
   - *Who knows Python?*
   - *Tell me about the CRM System.*
4. You'll see the **answer**, plus the **graph facts** (from Neo4j) and **document chunks with similarity scores** (from pgvector) that were used to produce it.

### Or use the API directly

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/seed
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"Who reports to Rahul?\"}"
```

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Checks Neo4j and Postgres are reachable |
| POST | `/seed` | Builds the graph and ingests documents (run once) |
| GET | `/employees` | Lists all employees with title & department |
| GET | `/employees/{name}` | One employee with manager, skills, projects, reports |
| GET | `/projects` | Lists projects with department & team |
| GET | `/documents` | Ingested documents and chunk counts |
| POST | `/ask` | Runs the Graph RAG pipeline: `{"question": "..."}` |

---

## 🏗️ Architecture

### 1. System overview

```mermaid
flowchart LR
    U([👤 User]) --> FE

    subgraph Frontend["Frontend · Streamlit :8501"]
        FE[app.py<br/>Load data · Ask · Show evidence]
    end

    subgraph Backend["Backend · FastAPI :8000"]
        API[main.py<br/>REST endpoints]
        SEED[seed.py<br/>build_graph · ingest_documents]
        RAG[rag.py<br/>graph_search · vector_search · ask]
        DB[db.py<br/>neo4j_run · pg_connect · init_tables]
        CFG[config.py<br/>.env settings]
    end

    subgraph Stores["Data stores · Docker"]
        NEO[(Neo4j :7687<br/>Employee · Department<br/>Project · Skill)]
        PG[(PostgreSQL + pgvector :5432<br/>chunks table<br/>vector 1536)]
    end

    subgraph OpenAI["OpenAI API"]
        EMB[text-embedding-3-small]
        LLM[gpt-4o-mini]
    end

    DOCS[/"backend/documents/*.md"/]

    FE -- "POST /seed · POST /ask" --> API
    API --> SEED
    API --> RAG
    API -- "/employees · /projects · /documents · /health" --> DB
    SEED --> DB
    RAG --> DB
    DB --> NEO
    DB --> PG
    DOCS --> SEED
    SEED -- embed chunks --> EMB
    RAG -- embed question --> EMB
    RAG -- context + question --> LLM
    CFG -.-> DB
    CFG -.-> RAG
```

### 2. Ingestion flow: `POST /seed`

```mermaid
flowchart TD
    A[Click 'Load sample data'] --> B[POST /seed]
    B --> C[seed_all]

    C --> G1[build_graph]
    G1 --> G2[MATCH n DETACH DELETE n<br/>clear old graph]
    G2 --> G3[For each employee in EMPLOYEES:<br/>MERGE Employee + Department]
    G3 --> G4[MERGE REPORTS_TO manager]
    G4 --> G5[MERGE HAS_SKILL → Skill]
    G5 --> G6[MERGE WORKS_ON → Project<br/>Project BELONGS_TO Department]
    G6 --> NEO[(Neo4j)]

    C --> D1[ingest_documents]
    D1 --> D2[DELETE FROM chunks]
    D2 --> D3[Read each .md in documents/]
    D3 --> D4[split_text: ~400-char chunks]
    D4 --> D5[embed chunk → OpenAI<br/>1536-dim vector]
    D5 --> D6[INSERT source, content, embedding]
    D6 --> PG[(pgvector)]

    NEO --> R[Return people & documents count]
    PG --> R
```

### 3. Query flow: `POST /ask` (Graph RAG pipeline)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit UI
    participant API as FastAPI /ask
    participant RAG as rag.ask()
    participant Neo as Neo4j
    participant OAI as OpenAI
    participant PG as pgvector

    User->>UI: Types a question
    UI->>API: POST /ask {question}
    API->>RAG: ask(question)

    rect rgba(100,150,255,0.1)
    Note over RAG,Neo: Step 1: Graph search
    RAG->>Neo: Get all Employee / Project / Skill names
    RAG->>RAG: Match names that appear in the question
    RAG->>Neo: Cypher: department, manager, skills,<br/>projects, reports, team, people-with-skill
    Neo-->>RAG: Rows → "graph facts" sentences
    end

    rect rgba(100,200,120,0.1)
    Note over RAG,PG: Step 2: Vector search
    RAG->>OAI: Embed question (text-embedding-3-small)
    OAI-->>RAG: 1536-dim vector
    RAG->>PG: ORDER BY cosine distance, LIMIT 3
    PG-->>RAG: Top-3 chunks + similarity score
    end

    rect rgba(255,180,80,0.1)
    Note over RAG,OAI: Step 3: Generate answer
    RAG->>RAG: Build context = GRAPH FACTS + DOCUMENT TEXT
    RAG->>OAI: gpt-4o-mini (temp 0, grounded system prompt)
    OAI-->>RAG: Answer
    end

    RAG-->>API: {answer, graph_facts, documents}
    API-->>UI: JSON
    UI-->>User: Answer + evidence expanders
```

### 4. Knowledge graph schema (Neo4j)

```mermaid
graph LR
    E((Employee<br/>name, title)) -- WORKS_IN --> D((Department))
    E -- REPORTS_TO --> M((Employee))
    E -- HAS_SKILL --> S((Skill))
    E -- WORKS_ON --> P((Project))
    P -- BELONGS_TO --> D
```

**Sample data:** 8 employees across 3 departments (Generative AI, Data Science, Engineering), 3 projects (Knowledge Assistant, Recommendation Engine, CRM System), and skills like Python, Neo4j, RAG, pgvector, FastAPI and Docker.

**pgvector table:** `chunks(id SERIAL, source TEXT, content TEXT, embedding vector(1536))`

---

## 🧩 Why Graph + Vector?

| Question type | Best source | Example |
|---|---|---|
| Relationships / multi-hop | **Graph** | "Who reports to Rahul?" |
| Aggregation over entities | **Graph** | "Who knows Python?" |
| Descriptive / "what is" | **Vector** | "Tell me about the CRM System." |
| Mixed | **Both** | "What does Amit's project use for search?" |

Graph search gives exact, structured facts. Vector search adds descriptive context. Together they keep the LLM grounded, and it is told to say *"not enough information"* instead of guessing.

---

## 🩺 Troubleshooting

| Symptom | Fix |
|---|---|
| `/ask` or `/seed` returns 500 / auth error | `OPENAI_API_KEY` is missing or invalid. Check `.env` (no spaces around `=`), then `docker compose up --build` again. |
| Backend exits on startup | Databases weren't ready. Run `docker compose ps`; both should be `healthy`. Restart with `docker compose restart backend`. |
| `/health` shows `false` | Locally, make sure `docker compose up -d postgres neo4j` is running and ports 5432/7687 aren't already in use. |
| Answers say "not enough information" | Click **Load sample data** first (`POST /seed`). Check `GET /documents` returns 4 sources. |
| Port already in use | Stop the conflicting service, or change the left side of the port mapping in `docker-compose.yml` (e.g. `"5433:5432"`) and update `DATABASE_URL`. |
| Want a clean slate | `docker compose down -v`, then start again. |

---

## 🔧 Extending

- **Add documents:** drop `.md` files into `backend/documents/`, then re-run `/seed`.
- **Add people / projects:** edit the `EMPLOYEES` list in `backend/seed.py`, then re-run `/seed`.
- **Change models:** set `CHAT_MODEL` / `EMBED_MODEL` in `.env`. If the embedding size changes, update `EMBED_SIZE` in `config.py` and recreate the `chunks` table (`docker compose down -v`).
