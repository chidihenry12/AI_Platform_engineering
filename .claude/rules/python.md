---
paths:
  - "apps/api/**/*.py"
  - "apps/agents/**/*.py"
  - "apps/workers/**/*.py"
  - "apps/mcp-servers/**/*.py"
  - "packages/shared-schemas/**/*.py"
  - "evals/**/*.py"
---

# Python services (LLD sections 1, 4, 7, 15)

- Python 3.12, async throughout: async SQLAlchemy 2 + asyncpg, `httpx.AsyncClient`, async Redis.
- Pydantic v2 for DTOs and agent schemas. Contracts shared by api and agents live in `packages/shared-schemas`.
- Config only through `Settings` (`pydantic-settings`, env prefix `ACSRP_`). No ad hoc `os.environ`.
- Layering: thin routers, then services, then repositories. Authorise with `require("<permission>")`, and services re-check high-risk permissions.
- Errors use RFC 9457 Problem Details with the LLD section 19 `type` codes.
- Logging: structlog JSON with `tenant_id, ticket_id, run_id, trace_id, span_id`, plus the PII redaction processor.
- LLM calls go through the gateway by **tier** (`small`/`medium`/`large`), never by model ID. Agent outputs go through the `structured()` helper at temperature 0.1.
- MCP tools: Pydantic input model with strict patterns, a `risk_tier`, a `read_only` flag, a scoped JWT check, and `idempotency_key` from request metadata.
- Background jobs are idempotent: exponential backoff, max 5 retries, dead-letter to `arq:dlq`.
