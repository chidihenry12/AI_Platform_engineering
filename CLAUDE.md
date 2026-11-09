# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**ACSRP — Autonomous Customer Support & Resolution Platform** (working folder: `resolva`).

A multi-agent platform that acts like a production "AI Customer Resolution Engineer". For every support request it runs:

> **Understand → Investigate → Retrieve → Decide → Act → Escalate → Remember**

It does more than generate answers. It classifies the ticket, retrieves grounded evidence, pulls customer context, diagnoses, builds a resolution plan, **executes governed actions through MCP tools**, escalates risky cases to humans, and learns from resolved tickets. The same container images deploy to **AWS, Azure and GCP** with Terraform.

### Source-of-truth design docs (repo root)

| Doc | File | Use it for |
|---|---|---|
| PRD/BRD | `PRD_BRD_Autonomous_Customer_Support_Platform_md_94A6.md` | Requirements (FR-xx, NFR-xx), success metrics, scope, personas, journeys |
| HLD | `HLD_Autonomous_Customer_Support_Platform_md_GI9Q.md` | Components, agent graph, retrieval/memory design, security, cloud mapping, ADRs |
| LLD | `LLD_Autonomous_Customer_Support_Platform_md_5meL.md` | Stack, repo layout, DDL, API, state schemas, graph code, policies, config, IaC, CI |

The docs refer to themselves as `01_PRD_…`, `02_HLD_…`, `03_LLD_…`; those names mean the files above. When code and docs disagree, ask before changing either. Cite requirement IDs (e.g. `FR-16`, `NFR-09`) in PRs and commit messages when you implement them. The traceability table is LLD §21.

### Current status

Design phase. Only the three design docs exist so far. Build follows the release plan (PRD §9):

0 PRD → 1 Architecture → **2 Foundations** (repo, FastAPI skeleton, Postgres schema, Redis, auth, Next.js shell) → 3 Knowledge → 4 Agents → 5 MCP & Actions → 6 Memory & Learning → 7 Guardrails & Security → 8 Testing & Evals → 9 Containers & IaC → 10 CI/CD → 11 Multi-cloud deploy → 12 Observability & Ops.

When scaffolding, follow the monorepo layout below exactly, and move the design docs into `docs/`.

---

## Tech Stack (pinned baselines, LLD §1)

| Layer | Choice |
|---|---|
| Languages | Python **3.12** (backend), TypeScript 5.x (frontend) |
| Backend | FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x **async** + asyncpg, Alembic |
| Agents | LangGraph + `langgraph-checkpoint-postgres` (`AsyncPostgresSaver`), langchain-core |
| Tools | `mcp` Python SDK (FastMCP, **streamable HTTP** transport) |
| LLM gateway | LiteLLM (swappable for VexaRoute); model is config, never code |
| Vector DB | Qdrant (dense + sparse) by default; pgvector adapter as the low-ops option |
| Embeddings / rerank | `text-embedding-3-large` or `bge-m3`; reranker `bge-reranker-v2-m3` or Cohere Rerank |
| Guardrails | Presidio (PII), small-LLM + heuristic injection classifier, groundedness judge |
| Workers | arq on Redis (Celery is the alternative) |
| Cache / limits / queue | Redis 7 |
| DB | PostgreSQL 16 (OLTP, checkpoints, audit) |
| Auth | OIDC + JWT (python-jose / authlib); Keycloak locally |
| Frontend | Next.js 15 App Router, Tailwind, shadcn/ui, TanStack Query, Zustand, next-auth |
| Observability | OpenTelemetry, Langfuse, Prometheus client, structlog |
| Testing | pytest, pytest-asyncio, httpx, testcontainers, Playwright, schemathesis, RAGAS/DeepEval-style evals, k6/Locust |
| Packaging / infra | uv, Docker multi-stage, Helm, Terraform ≥ 1.8, GitHub Actions |

---

## Repository Layout (target monorepo, LLD §2)

```
acsrp/
├── apps/
│   ├── api/                 # FastAPI service
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── core/        # config, security, logging, telemetry, errors
│   │   │   ├── db/          # session, models, repositories
│   │   │   ├── api/v1/      # routers: tickets, messages, approvals, admin, auth, analytics, widget
│   │   │   ├── services/    # ticket_service, approval_service, memory_service, ...
│   │   │   ├── channels/    # email, webhook, ticketing adapters
│   │   │   ├── realtime/    # ws/sse manager
│   │   │   └── schemas/     # Pydantic DTOs
│   │   └── alembic/
│   ├── agents/              # LangGraph runtime (worker process)
│   │   ├── graph/           # state.py, builder.py, routing.py, nodes/
│   │   ├── prompts/         # versioned prompt templates (.md + metadata)
│   │   ├── guardrails/
│   │   ├── policy/          # engine + policies/*.yaml
│   │   ├── retrieval/       # hybrid, rerank, rewriting, sufficiency
│   │   ├── memory/
│   │   ├── llm/             # gateway client, model routing, cost
│   │   └── mcp_client/
│   ├── workers/             # ingestion, summaries, evals, SLA timers
│   ├── mcp-servers/         # crm/ billing/ orders/ ticketing/ status/ knowledge/
│   └── web/                 # Next.js dashboard + embeddable widget
├── packages/
│   ├── shared-schemas/      # Pydantic models shared by agents and api
│   └── ui/                  # shared React components
├── evals/                   # golden datasets, red-team sets, runners
├── infra/
│   ├── docker/              # compose.yaml, compose.observability.yaml
│   ├── helm/acsrp/
│   └── terraform/
│       ├── modules/{network,k8s,postgres,redis,storage,secrets,registry,observability}/{aws,azure,gcp}
│       └── envs/{aws,azure,gcp}/{dev,staging,prod}
├── .github/workflows/
└── docs/                    # PRD, HLD, LLD, ADRs, runbooks
```

Put Pydantic contracts used by both `api` and `agents` in `packages/shared-schemas`. Don't duplicate them.

---

## Common Commands (planned; update once tooling exists)

```bash
# Local stack: postgres, redis, qdrant, keycloak, minio, litellm, langfuse, api, agents, workers, mcp-*, web
docker compose -f infra/docker/compose.yaml up -d
docker compose -f infra/docker/compose.yaml -f infra/docker/compose.observability.yaml up -d

# Python (per app, uv-managed)
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy .
uv run pytest                          # unit
uv run pytest -m integration           # testcontainers: Postgres/Redis/Qdrant + mock LLM
uv run alembic upgrade head            # from apps/api

# Frontend (apps/web)
npm run lint && npx tsc --noEmit && npx vitest run
npx playwright test

# Evals (CI gate)
uv run python -m evals.run --suite all

# Infra
terraform -chdir=infra/terraform/envs/<cloud>/<env> plan
helm upgrade --install acsrp infra/helm/acsrp -f infra/helm/acsrp/values-<cloud>.yaml --atomic
```

Local ports: api 8000, web 3000, MCP servers 8100+, reranker 8080, agents metrics 9100, Postgres 5432, Redis 6379, Qdrant 6333.

---

## Architecture Essentials

### Request flow (HLD §9)
1. Widget/email/API/ticketing → `POST /api/v1/conversations/{id}/messages` → persist message, upsert ticket → enqueue `run_ticket_graph` → return **202** with `stream_url`.
2. Worker takes `lock:run:{ticket_id}` (120 s) so only one graph run is active per ticket, then starts or resumes the LangGraph thread (`thread_id = ticket_id`).
3. Graph streams events over SSE. Approvals pause the graph with `interrupt()`. The API resumes it with `Command(resume={"decisions": ...})`.
4. The run ends with output guardrails → reply → memory write-back, summary, audit and metrics.

### Agent graph (supervisor pattern, LLD §7.2)
Nodes: `input_guard → supervisor → {customer | investigate(fan-out knowledge + troubleshoot) | knowledge | resolution | escalation | clarify}` → `resolution → policy_gate → {execute | reply_only | replan | escalate}` → `output_guard → {respond | revise | escalate}` → `memory → END`.

| Agent | Output schema | Tools | Model tier |
|---|---|---|---|
| Support Supervisor | `Triage` + route | none | small |
| Customer | `CustomerContext` | crm, billing, orders, ticketing, memory (read) | none/small |
| Knowledge / RAG | `EvidencePack` | knowledge-mcp, vector DB | small + rerank |
| Troubleshooting | `Diagnosis` | **read-only** diagnostics, max 5 tool calls, stop at confidence ≥ 0.75 | large |
| Resolution | `ResolutionPlan` (with `ActionProposal[]`) | **only agent allowed write tools** (via policy) | large |
| Escalation | `EscalationBrief` | ticketing, notifications | medium |

Shared state is the typed `TicketState` (LLD §7.1). Use the reducers as specified: `add_messages`, and `operator.add` for `action_results`, `route_history` and `guardrail_flags`.

### Supervisor routing rules (deterministic; keep them in code, not in prompts)
In order:
1. `step_count >= MAX_STEPS (12)` → escalation.
2. Risk flags `security | legal | fraud | self_harm`, or P1 → escalation.
3. `needs_clarification` with fewer than 2 prior clarifications → clarify.
4. Customer known but context missing or stale (> 5 min) → customer.
5. `question` intent without evidence → knowledge.
6. `problem | request_action | complaint` without evidence and diagnosis → investigate (parallel via `Send`).
7. Min confidence < `0.6` after ≥ 2 investigate cycles → escalation.
8. Otherwise → resolution.

### Retrieval (agentic RAG, HLD §5 / LLD §7.5)
- Pipeline: query rewrite (1–3 sub-queries) → metadata filters (`tenant_id`, product, version) → dense k=40 + sparse k=40 → RRF (k=60) → cross-encoder rerank to top 8 (drop scores < 0.2) → sufficiency check. If evidence is insufficient, run **one** gap-driven retry.
- Collections: `kb_docs`, `resolved_tickets`, `resolution_cards` (status=approved only), `customer_memory`. Every query is filtered by `tenant_id`.
- Chunking: heading-aware, target 600 tokens with 80 overlap, tables kept whole, each chunk prefixed with `title > section path`.
- Freshness boost for tickets and cards: `score *= 1 + 0.05 * recency_bucket`.
- Fallback: Postgres full-text search when Qdrant is down. Set the `retrieval_degraded` flag.
- Postgres is the source of truth. Qdrant point ID = row UUID, and the index must always be rebuildable from Postgres + object storage.

### Policy engine & HITL (LLD §7.8)
- Risk tiers: `low` = auto-execute, `medium` = agent approval, `high` = supervisor approval, `prohibited` = never execute (escalate).
- Policies are YAML in `agents/policy/policies/*.yaml`, evaluated with a **safe expression evaluator** (`simpleeval` with whitelisted names). Never use `eval`.
- Tenant `autonomy_mode` overrides: `copilot` → every action needs approval and replies are never auto-sent; `supervised` → `low` is raised to `medium`; `autonomous` → policy as written.
- Reference rules: `billing.refund` ≤ $50 (standard/premium, < 2 refunds in 90 days) is low, $50–300 is medium, > $300 or ≥ 3 refunds in 90 days is high, a `fraud_review` flag is prohibited. `crm.close_account` is prohibited. `orders.reship` is medium, or low if value ≤ $75 and the order is lost in transit. `crm.reset_password_link` is low.
- Approval timeout → expire → escalate → notify supervisor. Every decision goes to `audit_log`.

### Memory (HLD §6 / LLD §7.11)
- Layers: working (graph state), conversation (checkpoints + Redis), customer long-term (Postgres facts + Qdrant), organisational (`resolution_cards`).
- Write-back: summary → `ticket_summaries`. Extract `MemoryFact[]` and keep only confidence ≥ 0.7. **Never store payment data, government IDs or health data.** Then upsert to Postgres and Qdrant.
- Resolution cards are distilled only after CSAT ≥ 4 or an agent "good" label. They are created as `draft` and an admin must approve them before indexing.
- Right to erasure: `DELETE /customers/{id}/memory` must purge both Postgres and Qdrant.

---

## Non-Negotiable Invariants

Treat these as hard rules. Code that breaks one is a bug, even if tests pass.

1. **The LLM never executes anything directly.** Actions flow `ActionProposal → policy_gate → (approval) → execute_actions_node → MCP`. Only Resolution may call write tools, and the **tool registry** enforces that, not the prompt.
2. **The policy engine runs outside the LLM** (ADR-07). Risk decisions are deterministic and auditable.
3. **Every action is idempotent.** Key = `f"{ticket_id}:{tool}:{stable_hash(arguments)}"`, stored with a UNIQUE constraint on `action_requests.idempotency_key` and passed to MCP in request metadata. Check for a prior result before executing, and retry 5xx errors with the **same** key.
4. **Validate tool arguments twice**: against the registry's Pydantic `input_model`, and with a provenance check. IDs and amounts must come from customer context or tool results, never from untrusted free text.
5. **Untrusted content is data, not instructions.** Wrap retrieved docs, emails and attachments in `<untrusted>…</untrusted>`, scan chunks for injection, and drop flagged chunks.
6. **Grounded replies.** Every factual claim cites a provided `chunk_id` (FR-10). The output groundedness judge must score ≥ 0.8. Allow at most 1 revision, then escalate. Never promise anything outside policy.
7. **Structured outputs everywhere.** Validate all agent outputs against Pydantic schemas with the `structured()` helper (temperature ≤ 0.2, default 0.1). Repair-retry on validation error, then escalate.
8. **Tenant isolation.** Every tenant table has `tenant_id` and Postgres RLS: `USING (tenant_id = current_setting('app.tenant_id')::uuid)`. The API runs `SET LOCAL app.tenant_id` per transaction. Every vector query filters on `tenant_id`.
9. **`audit_log` is append-only.** The app DB role has no UPDATE or DELETE on it. Log tool executions, approvals, policy/admin changes and memory deletes.
10. **No PII in logs or traces.** Run the structlog redaction processor. Use `messages.body_redacted` for analytics. Store `agent_steps.output` redacted.
11. **No secrets in code or images.** Load them through the `SecretProvider` adapter from the cloud secret manager via workload identity. CI uses OIDC federation, never static keys.
12. **Cloud-specific code stays behind adapters** (`ObjectStore`, `SecretProvider`, `EmailSender`), selected by `settings.cloud`. One image runs on every cloud.
13. **Loop and cost limits.** `MAX_STEPS = 12`, at most 5 troubleshooting tool calls, at most 2 clarification turns, at most 2 knowledge retrieval rounds, and tenant token budgets: alert at 80%, switch to copilot-only at 100%.
14. **Graceful degradation.** When the LLM provider fails, go retry → fallback model → circuit breaker → `degraded`. The supervisor then escalates with an "AI temporarily unavailable" holding reply. Tickets are never lost.

---

## Coding Conventions

### Python
- Async throughout: async SQLAlchemy sessions, `httpx.AsyncClient`, async Redis.
- Pydantic v2 for all DTOs and agent schemas. Use `model_validator(mode="after")` for cross-field rules (see `ApprovalDecision`).
- Configuration: `pydantic-settings` with the `ACSRP_` env prefix (LLD §15). Add new settings to `Settings`. Never read `os.environ` ad hoc.
- Layering: routers stay thin → services hold business logic → repositories handle DB access. Services re-check sensitive permissions; for example, `ApprovalService` re-checks `approval:decide:high`.
- Authorisation via the `require("<permission>")` dependency, using the RBAC matrix in LLD §5.2. Roles: `customer`, `agent`, `supervisor`, `admin`, `platform_engineer`, `service`.
- Errors: RFC 9457 Problem Details with types `validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `rate_limited`, `budget_exceeded`, `upstream_unavailable`, `internal_error`.
- Logging: structlog JSON with `ts, level, msg, tenant_id, ticket_id, run_id, trace_id, span_id`.
- Tracing: a manual OTel span per graph node (`agent.node`, attributes `ticket.id`, `run.id`, `node`, `model`, `tokens`). Propagate trace context API → job payload → agents → MCP.
- Every LLM call records `tenant_id, run_id, node, model, tokens_in/out, latency, cost` to `agent_steps`, Langfuse and the Redis budget.
- Prompts live in `agents/prompts/` as versioned `.md` files with metadata. Record prompt versions on `agent_runs.prompt_versions`.
- Model names are placeholders in `config/models.yaml` (tiers `small`/`medium`/`large` with fallbacks). Code references **tiers**, never model IDs.
- Background jobs must be idempotent: exponential backoff, max 5 retries, dead-letter to `arq:dlq`.

### Database
- Schema changes go through Alembic only. Follow the DDL in LLD §3.2: UUID PKs via `gen_random_uuid()`, `TIMESTAMPTZ` with `now()`, `CHECK` constraints for enums-as-text, `CITEXT` for emails.
- Ticket status enum: `new, in_progress, awaiting_customer, awaiting_approval, escalated, resolved, closed`. Severity: `P1–P4`.
- LangGraph checkpoint tables live in a dedicated `langgraph` schema.
- Migrations run as a Helm pre-upgrade hook Job.

### Redis keys (LLD §3.4)
`rl:{tenant}:{user|ip}:{route}`, `tok:{tenant}:{yyyymmdd}` (48 h), `sess:widget:{sid}` (24 h), `ctx:customer:{tenant}:{cid}` (5 min), `sem:faq:{tenant}:{hash}` (1 h, low-risk informational only), `emb:{model}:{sha}` (7 d), `lock:run:{ticket_id}` (120 s), `pub:ticket:{id}` / `pub:tenant:{id}`. Rate limiting uses a token bucket in an atomic Lua script.

### MCP servers
- One FastMCP server per domain, on streamable HTTP, cluster-internal. A NetworkPolicy allows only `agent-runtime` pods to reach them.
- Each tool declares a Pydantic input model with strict field patterns (e.g. `invoice_id: ^INV-\d{6,}$`), MCP annotations (`readOnlyHint`, `idempotentHint`, …), a default `risk_tier` and a `read_only` flag.
- Verify the scoped service JWT (`aud=mcp:{server}`, `scope=tools:read|tools:write`) and read `idempotency_key` from request metadata.
- After a write, the executor does a read-back verification.

### Frontend
- Next.js App Router routes: `/inbox`, `/tickets/[id]`, `/approvals`, `/escalations`, `/analytics`, `/admin/{knowledge,policies,tools,users,tenant}`.
- TanStack Query for server state. WebSocket events invalidate query keys (`['ticket', id]`, `['approvals']`). Approval decisions use optimistic updates with rollback.
- The UI is role-aware via session claims, but the server stays the authority.
- `ChatWidget` is a React-built Web Component (Shadow DOM, SSE).
- The UI must meet WCAG 2.1 AA.

### API surface
Base path `/api/v1`. Every request carries `X-Request-ID` and responses include `traceparent`. List endpoints use cursor pagination. Webhooks (`/channels/email/inbound`, `/channels/ticketing/webhook`) are verified with HMAC + timestamp (5 min skew). Dedupe messages by `client_message_id` or email `Message-ID`. SSE event types: `run.started, node.started, token, citation, action.proposed, approval.pending, action.executed, escalated, message.final, run.completed, error`.

---

## Testing & Quality Gates

| Level | Scope | Tooling |
|---|---|---|
| Unit | services, policy rules, routers, chunker, RRF, schemas | pytest |
| Contract | MCP tool schemas, OpenAPI snapshot | schemathesis, pytest |
| Integration | API + Postgres + Redis + Qdrant + mock LLM | testcontainers |
| Graph | deterministic runs with a scripted fake LLM | LangGraph + `FakeListChatModel` |
| E2E | widget → resolution; approval round-trip | Playwright |
| Load | 1k concurrent chats | k6 / Locust |

- Aim for ≥ 80% unit coverage on core services (NFR-15).
- Required tests: a cross-tenant RLS isolation test, a log/secret redaction test, idempotency (no double refund), and the policy tier for every rule.
- **Graph tests must not call real LLMs.** Use scripted fakes.

**CI eval gate (the build fails if any is missed)**, using datasets in `evals/`:
triage accuracy ≥ 0.90 · Recall@10 ≥ 0.90 · faithfulness ≥ 0.92 · tool-call correctness ≥ 0.95 · escalation recall ≥ 0.98 · **any** red-team injection-to-action success or data leak = fail.

Datasets: `triage_golden.jsonl` (500), `retrieval_golden.jsonl` (300), `resolution_golden.jsonl` (200), `escalation_cases.jsonl` (150), `redteam_injection.jsonl` (200).

CI pipeline: lint/type/unit → integration → eval gate → security (bandit, pip-audit, npm audit, gitleaks, trivy) → build and sign (buildx, Syft SBOM, Cosign) → push to ECR/ACR/Artifact Registry → Terraform per cloud → `helm upgrade --atomic` to dev → smoke tests → manual promotion to staging and then prod with the **same image digest**.

---

## Product Targets (keep in mind when making trade-offs)

| Metric | Target |
|---|---|
| Autonomous resolution (L1) | ≥ 40% |
| First response (chat) | P50 < 30 s, P95 < 2 min; first token P95 < 3 s |
| Full resolution plan | P95 < 20 s (excluding approval waits) |
| Retrieval (hybrid + rerank) | P95 < 800 ms |
| Escalation precision / recall | ≥ 85% / ≥ 98% |
| Unsafe autonomous actions | **0** |
| CSAT (AI-resolved) / reopen rate | ≥ 4.3 / < 8% |
| LLM cost per ticket | < US$0.08 (route triage and guardrails to small models, cache embeddings and FAQs) |
| Capacity | 50 concurrent conversations per API replica; 100k tickets/month per tenant; 1M+ chunks |
| Availability | 99.9%; RPO 15 min / RTO 1 h |

## Out of Scope for v1.0
Voice/telephony, more than one helpdesk adapter (one mock Zendesk/Jira-style adapter only), model fine-tuning, multi-language UI (replies may still be in the customer's language), and real payments (the billing MCP hits a sandbox).

## Infra Notes
- Terraform: every cloud module (`modules/*/{aws,azure,gcp}`) exposes the **same inputs and outputs** (LLD §17.1). Keep the interface identical to prevent multi-cloud drift.
- Helm: `api` HPA 2–20, `agents` KEDA on queue length 1–30, Qdrant StatefulSet with 3 replicas unless managed, default-deny NetworkPolicies, PDBs, probes, and cloud specifics only in `values-{aws,azure,gcp}.yaml`.
- Images: run as non-root on a read-only root FS, with health checks, `python:3.12-slim` multi-stage with uv, and `node:22-alpine` standalone for web. Pin image tags; the Compose excerpt in the LLD uses `latest` only for illustration.
- Environments: `local` (Compose) → `dev` → `staging` → `prod` per cloud, promoted by Git tag.

## Working Agreements for Claude
- Read the relevant LLD section before implementing a component, and match its names: tables, schemas, node names, Redis keys, metrics (`acsrp_*`).
- Don't weaken a safety invariant, guardrail threshold or eval gate to make something pass. Raise it instead.
- New tools need: an MCP input schema, a registry entry with an agent allow-list, a policy YAML (or an explicit default tier), audit logging, and tests.
- New config needs: a field on `Settings`, an `.env` example entry, Helm values for each cloud, and a matching secret if it's sensitive.
- If a design doc is ambiguous or contradictory, flag it rather than guess.
