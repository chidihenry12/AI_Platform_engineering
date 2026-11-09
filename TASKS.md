# TASKS.md — ACSRP Development Plan

Development plan for the **Autonomous Customer Support & Resolution Platform (ACSRP)**. It is built from the PRD/BRD, HLD, LLD and `CLAUDE.md`.

**Status legend:** Pending ❌ · Completed ✅

**Branch convention:** every sub-task is built on its own branch, `feature/<repo-area>-<topic>`, and merged to `main` through a reviewed PR with green CI. The `<repo-area>` prefix names the part of the monorepo the branch touches:

| Prefix | Area | Prefix | Area |
|---|---|---|---|
| `api` | `apps/api` | `web` | `apps/web`, `packages/ui` |
| `agents` | `apps/agents` | `mcp` | `apps/mcp-servers/*` |
| `workers` | `apps/workers` | `retrieval` | `apps/agents/retrieval` |
| `llm` | `apps/agents/llm` | `guardrails` | `apps/agents/guardrails` |
| `db` | `apps/api/alembic` | `shared` | `packages/shared-schemas` |
| `platform` | cross-cutting libs | `sandbox` | mock back-office and data |
| `channels` | `apps/api/app/channels` | `evals` | `evals/` |
| `infra` | `infra/` | `ci` / `cd` | `.github/workflows` |
| `deploy` / `ops` | environments, operations | `docs` / `repo` / `tooling` | docs, repo setup, Claude setup |

---

## How the plan keeps dependencies low

1. **Contracts first.** Phase 2 freezes the shared Pydantic schemas and the OpenAPI v1 contract. Back-office tools, guardrails, retrieval and the dashboard then build against contracts, not against each other.
2. **Pure components early.** The policy engine, guardrails, chunker and MCP servers have no runtime dependencies. They are scheduled before the agent graph that uses them.
3. **Parallel tracks.** After Phase 2, Phases 3, 4 and 5 can run at the same time. The dashboard (Phase 11) and Terraform (Phase 13) can start early against mocks.
4. **Sequential where it must be.** Database migrations (Phase 3.1 to 3.3) and anything that touches a shared schema, lock file or migration run one after another, never in parallel.

### Phase dependency map

| Phase | Name | Depends on | Can run in parallel with |
|---|---|---|---|
| 0 | Product & architecture | — | — |
| 1 | Repository bootstrap | 0 | — |
| 2 | Shared contracts & platform core | 1 | 13 (Terraform only) |
| 3 | Data layer & API foundations | 2 | 4, 5, 11, 13 |
| 4 | Sandbox back-office, MCP servers & policy engine | 2 | 3, 5, 11, 13 |
| 5 | LLM gateway & guardrails | 2 | 3, 4, 11, 13 |
| 6 | Knowledge & retrieval | 3, 5 (6.7 also needs 4.3) | 4, 11, 13 |
| 7 | Agent runtime | 4, 5, 6 | 11, 13 |
| 8 | Conversation flow & channels | 3, 7 | 11, 13 |
| 9 | Actions & human-in-the-loop | 8 | 10, 11, 13 |
| 10 | Memory & learning | 7, 8 | 9, 11, 13 |
| 11 | Dashboard & chat widget | 2 (against mocks); 8 to 10 for live integration | 3 to 10, 13 |
| 12 | Evaluation & test hardening | 9, 10 | 13 |
| 13 | Containerisation & IaC | 1 (Terraform), 8 (images, Helm) | 2 to 12 |
| 14 | CI/CD & multi-cloud deploy | 12, 13 | — |
| 15 | Observability, ops & release | 14 | — |

### Progress summary

| Phase | Sub-tasks | Completed | Status |
|---|---|---|---|
| 0 | 7 | 5 | Pending ❌ |
| 1 | 6 | 0 | Pending ❌ |
| 2 | 5 | 0 | Pending ❌ |
| 3 | 9 | 0 | Pending ❌ |
| 4 | 11 | 0 | Pending ❌ |
| 5 | 7 | 0 | Pending ❌ |
| 6 | 10 | 0 | Pending ❌ |
| 7 | 10 | 0 | Pending ❌ |
| 8 | 6 | 0 | Pending ❌ |
| 9 | 6 | 0 | Pending ❌ |
| 10 | 5 | 0 | Pending ❌ |
| 11 | 12 | 0 | Pending ❌ |
| 12 | 6 | 0 | Pending ❌ |
| 13 | 6 | 0 | Pending ❌ |
| 14 | 6 | 0 | Pending ❌ |
| 15 | 5 | 0 | Pending ❌ |
| **Total** | **117** | **5** | |

---

## Phase 0 — Product & Architecture

**Goal:** agree what to build and how. **Depends on:** —

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 0.1 | PRD/BRD: requirements, metrics, scope, personas, journeys | `feature/docs-prd` | — | Completed ✅ |
| 0.2 | High-Level Design: components, agent graph, cloud mapping, ADR summary | `feature/docs-hld` | 0.1 | Completed ✅ |
| 0.3 | Low-Level Design: stack, DDL, API, state, policies, IaC, CI | `feature/docs-lld` | 0.2 | Completed ✅ |
| 0.4 | `CLAUDE.md` project guidance for Claude Code | `feature/docs-claude-md` | 0.3 | Completed ✅ |
| 0.5 | Claude Code setup: agents, skills, rules, hooks, cost governance | `feature/tooling-claude-setup` | 0.4 | Completed ✅ |
| 0.6 | Write ADR-01 to ADR-08 as files in `docs/adr/` | `feature/docs-adr` | 0.2 | Pending ❌ |
| 0.7 | Synthetic dataset spec (docs, ~5–10k tickets, customers, orders) | `feature/docs-dataset-spec` | 0.1 | Pending ❌ |

---

## Phase 1 — Repository Bootstrap

**Goal:** a working monorepo that lints, tests and runs local infrastructure. **Depends on:** Phase 0

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 1.1 | `git init`, `main` branch protection, `.editorconfig`, move design docs to `docs/` | `feature/repo-bootstrap` | — | Pending ❌ |
| 1.2 | Monorepo skeleton: uv workspace, npm workspaces, empty `apps/*` and `packages/*` | `feature/repo-monorepo-layout` | 1.1 | Pending ❌ |
| 1.3 | Local Compose stack: Postgres 16, Redis 7, Qdrant, Keycloak, MinIO, LiteLLM, Langfuse (pinned tags) | `feature/infra-local-compose` | 1.1 | Pending ❌ |
| 1.4 | CI baseline: ruff, mypy, pytest, eslint, tsc, vitest, gitleaks on every PR | `feature/ci-baseline` | 1.2 | Pending ❌ |
| 1.5 | Developer task runner (Makefile/justfile) for lint, test, up, down, migrate | `feature/repo-dev-tasks` | 1.2 | Pending ❌ |
| 1.6 | Sync real commands into `.claude/settings.json` and propose the `CLAUDE.md` commands update | `feature/tooling-commands-sync` | 1.4, 1.5 | Pending ❌ |

---

## Phase 2 — Shared Contracts & Platform Core

**Goal:** freeze the contracts and cross-cutting libraries every later phase builds on. **Depends on:** Phase 1 · **Covers:** NFR-11, NFR-14, NFR-15

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 2.1 | Shared schemas: `Ticket`, `Message`, `Triage`, `Citation`, `EvidencePack`, `Diagnosis`, `ActionProposal`, `ResolutionPlan`, `EscalationBrief`, `GuardResult`, `PolicyDecision` | `feature/shared-schemas-core` | — | Pending ❌ |
| 2.2 | `Settings` (`ACSRP_` prefix) and cloud adapter interfaces (`ObjectStore`, `SecretProvider`, `EmailSender`) with local/MinIO implementations | `feature/platform-config-adapters` | — | Pending ❌ |
| 2.3 | Observability library: structlog JSON with PII redaction, OTel setup, Prometheus `acsrp_*` metric registry | `feature/platform-observability` | — | Pending ❌ |
| 2.4 | Error model: RFC 9457 Problem Details and the shared error codes | `feature/platform-errors` | — | Pending ❌ |
| 2.5 | OpenAPI v1 contract from LLD §4, published for frontend mocks and contract tests | `feature/api-contract-v1` | 2.1, 2.4 | Pending ❌ |

---

## Phase 3 — Data Layer & API Foundations

**Goal:** database schema with tenant isolation, plus an authenticated, rate-limited API skeleton. **Depends on:** Phase 2 · **Covers:** FR-42, NFR-07, NFR-10

> 3.1 → 3.2 → 3.3 are migrations and **must run in sequence**.

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 3.1 | Alembic setup and core tables: `tenants`, `users`, `customers`, `tickets`, `messages` | `feature/db-core-schema` | — | Pending ❌ |
| 3.2 | Agent tables: `agent_runs`, `agent_steps`, `action_requests`, `approvals`, `escalations` | `feature/db-agent-schema` | 3.1 | Pending ❌ |
| 3.3 | Knowledge, memory, feedback and audit tables; RLS on all tenant tables; append-only grants on `audit_log` | `feature/db-knowledge-memory-schema` | 3.2 | Pending ❌ |
| 3.4 | Cross-tenant RLS isolation test suite (testcontainers) | `feature/db-rls-tests` | 3.3 | Pending ❌ |
| 3.5 | FastAPI skeleton: `/healthz`, `/readyz`, `X-Request-ID`, `traceparent`, async DB session with `SET LOCAL app.tenant_id` | `feature/api-skeleton` | 3.1 | Pending ❌ |
| 3.6 | Auth and RBAC: OIDC JWT validation, JWKS cache, `Principal`, `require()`, role matrix, Keycloak realm export | `feature/api-auth-rbac` | 3.5 | Pending ❌ |
| 3.7 | Rate limiting: Redis token bucket (Lua) per tenant/user/IP and LLM token budget counters | `feature/api-rate-limiting` | 3.5 | Pending ❌ |
| 3.8 | Append-only audit log service | `feature/api-audit-log` | 3.3, 3.5 | Pending ❌ |
| 3.9 | Widget sessions: site key, origin check, signed customer JWT | `feature/api-widget-sessions` | 3.6 | Pending ❌ |

---

## Phase 4 — Sandbox Back-Office, MCP Servers & Policy Engine

**Goal:** governed, typed tools and deterministic risk decisions, built and tested on their own. **Depends on:** Phase 2 · **Parallel with:** 3, 5 · **Covers:** FR-08, FR-15, FR-16, FR-18, FR-19

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 4.1 | Synthetic data generator: customers, orders, invoices, charges, devices, incidents, historical tickets | `feature/sandbox-synthetic-data` | 0.7 | Pending ❌ |
| 4.2 | Sandbox back-office mock services (CRM, billing, orders, status) seeded from 4.1 | `feature/sandbox-backoffice` | 4.1 | Pending ❌ |
| 4.3 | MCP service-auth library: client-credentials JWT, `aud`/`scope` checks, idempotency metadata | `feature/mcp-auth-lib` | — | Pending ❌ |
| 4.4 | `crm-mcp`: `get_customer`, `get_devices`, `list_notes`, `update_contact`, `reset_password_link`, `close_account` | `feature/mcp-crm` | 4.2, 4.3 | Pending ❌ |
| 4.5 | `billing-mcp`: `list_invoices`, `list_charges`, `refund`, `apply_credit` | `feature/mcp-billing` | 4.2, 4.3 | Pending ❌ |
| 4.6 | `orders-mcp`: `get_order`, `track_shipment`, `reship`, `cancel_order` | `feature/mcp-orders` | 4.2, 4.3 | Pending ❌ |
| 4.7 | `ticketing-mcp`: mock Zendesk/Jira-style adapter (`create_ticket`, `add_internal_note`, `assign_queue`) | `feature/mcp-ticketing` | 4.3 | Pending ❌ |
| 4.8 | `status-mcp`: `get_incidents`, `get_service_health` | `feature/mcp-status` | 4.2, 4.3 | Pending ❌ |
| 4.9 | MCP contract tests: tool schema snapshots, bad-ID and amount rejection | `feature/mcp-contract-tests` | 4.4–4.8 | Pending ❌ |
| 4.10 | Policy engine: YAML loader, `simpleeval` evaluator, autonomy-mode overrides, reference policies, tests for every tier | `feature/agents-policy-engine` | 2.1 | Pending ❌ |
| 4.11 | Tool registry with per-agent allow-lists, plus the MCP client | `feature/agents-tool-registry` | 2.1, 4.3 | Pending ❌ |

---

## Phase 5 — LLM Gateway & Guardrails

**Goal:** provider-agnostic, cost-tracked model access and safety checks, ready before any agent exists. **Depends on:** Phase 2 · **Parallel with:** 3, 4 · **Covers:** NFR-05, NFR-08, NFR-09, NFR-13, AI requirements (PRD §7)

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 5.1 | LiteLLM `models.yaml`: small/medium/large tiers, fallbacks, timeouts, circuit breaker | `feature/llm-gateway-config` | — | Pending ❌ |
| 5.2 | Gateway client and `structured()` helper with repair retries; token/cost accounting to `agent_steps`, Langfuse and Redis budget | `feature/llm-structured-client` | 5.1 | Pending ❌ |
| 5.3 | Scripted fake-LLM harness for deterministic tests | `feature/llm-fake-harness` | 5.2 | Pending ❌ |
| 5.4 | Input guardrails: size limits, injection/jailbreak classifier, Presidio PII, toxicity, security/legal/self-harm detectors | `feature/guardrails-input` | 5.2 | Pending ❌ |
| 5.5 | Content isolation (`<untrusted>` wrapper) and injection scan on retrieved chunks | `feature/guardrails-content-isolation` | — | Pending ❌ |
| 5.6 | Output guardrails: groundedness judge (≥ 0.8), policy compliance, PII leakage, tone | `feature/guardrails-output` | 5.2 | Pending ❌ |
| 5.7 | Versioned prompt registry (`agents/prompts/*.md` + metadata) | `feature/agents-prompt-registry` | — | Pending ❌ |

---

## Phase 6 — Knowledge & Retrieval

**Goal:** grounded evidence through hybrid, agentic RAG. **Depends on:** Phases 3 and 5 · **Covers:** FR-06, FR-07, FR-09, FR-10, FR-39, NFR-02

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 6.1 | Qdrant collections (`kb_docs`, `resolved_tickets`, `resolution_cards`, `customer_memory`), payload indexes, pgvector adapter interface | `feature/retrieval-vector-store` | — | Pending ❌ |
| 6.2 | Ingestion worker: PDF/MD/HTML/URL loaders, clean, dedupe by `content_hash`, PII scrub | `feature/workers-ingestion` | 6.1, 3.3 | Pending ❌ |
| 6.3 | Heading-aware chunker (600 tokens, 80 overlap, tables whole, contextual header) and enrichment | `feature/retrieval-chunking` | — | Pending ❌ |
| 6.4 | Embeddings client and Redis embedding cache | `feature/retrieval-embeddings` | 5.1 | Pending ❌ |
| 6.5 | Hybrid search: dense + sparse, RRF, cross-encoder rerank, freshness boost, Postgres FTS fallback | `feature/retrieval-hybrid-search` | 6.1, 6.4 | Pending ❌ |
| 6.6 | Agentic loop: query rewrite and sufficiency check with one gap-driven retry | `feature/retrieval-agentic` | 6.5, 5.2 | Pending ❌ |
| 6.7 | `knowledge-mcp`: `search_docs`, `get_document` | `feature/mcp-knowledge` | 6.5, 4.3 | Pending ❌ |
| 6.8 | `index_resolved_ticket` worker job | `feature/workers-index-resolved-tickets` | 6.4, 6.1 | Pending ❌ |
| 6.9 | Retrieval golden set (300 queries) and Recall@10 / nDCG@5 / MRR eval | `feature/evals-retrieval` | 6.5 | Pending ❌ |
| 6.10 | Admin knowledge-sources API and reindex job trigger | `feature/api-knowledge-admin` | 3.6, 6.2 | Pending ❌ |

---

## Phase 7 — Agent Runtime (LangGraph)

**Goal:** the six-agent supervisor graph with durable checkpoints. **Depends on:** Phases 4, 5 and 6 · **Covers:** FR-02, FR-03, FR-05, FR-11–FR-14, FR-22, FR-23

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 7.1 | `TicketState`, graph builder and `AsyncPostgresSaver` checkpointer (`thread_id = ticket_id`) | `feature/agents-graph-core` | — | Pending ❌ |
| 7.2 | Input-guard node, supervisor triage and deterministic router | `feature/agents-supervisor` | 7.1, 5.4 | Pending ❌ |
| 7.3 | Customer agent node and 5-minute context cache | `feature/agents-customer` | 7.1, 4.11 | Pending ❌ |
| 7.4 | Knowledge agent node | `feature/agents-knowledge` | 7.1, 6.6 | Pending ❌ |
| 7.5 | Troubleshooting agent (ReAct, read-only tools, max 5 calls) | `feature/agents-troubleshooting` | 7.1, 4.11 | Pending ❌ |
| 7.6 | Resolution agent: plan, cited reply draft, `ActionProposal`s | `feature/agents-resolution` | 7.1 | Pending ❌ |
| 7.7 | Escalation agent: brief, queue routing, holding reply | `feature/agents-escalation` | 7.1, 4.7 | Pending ❌ |
| 7.8 | Clarify and respond nodes, output-guard wiring and revise loop | `feature/agents-respond-clarify` | 7.6, 5.6 | Pending ❌ |
| 7.9 | Graph tests with the fake LLM covering every edge and the step/loop limits | `feature/agents-graph-tests` | 7.2–7.8, 5.3 | Pending ❌ |
| 7.10 | Triage golden set (500) and escalation cases (150) evals | `feature/evals-triage-escalation` | 7.2, 7.7 | Pending ❌ |

---

## Phase 8 — Conversation Flow & Channels

**Goal:** an end-to-end message → graph run → streamed reply over every channel. **Depends on:** Phases 3 and 7 · **Covers:** FR-01, FR-04, FR-38, NFR-06

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 8.1 | Conversations and messages API (202 + enqueue), `client_message_id` dedupe | `feature/api-conversations` | 3.6 | Pending ❌ |
| 8.2 | `run_ticket_graph` worker: run lock, trace propagation, resume per message | `feature/workers-run-ticket-graph` | 8.1, 7.9 | Pending ❌ |
| 8.3 | Realtime: SSE stream and dashboard WebSocket over Redis pub/sub | `feature/api-realtime` | 8.2 | Pending ❌ |
| 8.4 | Tickets API: list (cursor), detail, runs timeline, patch, handoff | `feature/api-tickets` | 3.6 | Pending ❌ |
| 8.5 | Email channel: inbound HMAC webhook, `Message-ID` dedupe, outbound adapter | `feature/channels-email` | 8.1, 2.2 | Pending ❌ |
| 8.6 | Ticketing-system webhook adapter | `feature/channels-ticketing` | 8.1 | Pending ❌ |

---

## Phase 9 — Actions & Human-in-the-Loop

**Goal:** safe, idempotent action execution with approvals that pause and resume the graph. **Depends on:** Phase 8 · **Covers:** FR-15–FR-21, FR-24, BO-5

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 9.1 | `policy_gate` node: tier decisions, `interrupt()`, pending `action_requests` and `approvals` rows | `feature/agents-policy-gate` | 4.10, 8.2 | Pending ❌ |
| 9.2 | Execute node: idempotency key, registry allow-list, schema and provenance checks, read-back verification, audit | `feature/agents-action-execution` | 9.1, 3.8 | Pending ❌ |
| 9.3 | Approvals API: queue by required role, approve/reject/edit, resume with `Command(resume=...)` | `feature/api-approvals` | 9.1 | Pending ❌ |
| 9.4 | `approval_timeout` and `sla_monitor` jobs with auto-escalation | `feature/workers-sla-timers` | 9.3 | Pending ❌ |
| 9.5 | Escalations API and AI-to-human handoff | `feature/api-escalations` | 7.7, 8.4 | Pending ❌ |
| 9.6 | Safety tests: no double refund, prohibited never executes, supervised/copilot overrides | `feature/agents-action-tests` | 9.2, 9.3 | Pending ❌ |

---

## Phase 10 — Memory & Learning

**Goal:** customer memory, summaries and reusable resolution cards. **Depends on:** Phases 7 and 8 · **Parallel with:** 9 · **Covers:** FR-25–FR-30

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 10.1 | Memory write-back node: ticket summary, `MemoryFact` extraction (confidence ≥ 0.7), blocked PII categories | `feature/agents-memory-writeback` | 7.1, 6.1 | Pending ❌ |
| 10.2 | Customer memory API: view, and erase across Postgres and Qdrant (right to erasure) | `feature/api-customer-memory` | 10.1, 3.8 | Pending ❌ |
| 10.3 | `distil_resolution_card` job and admin approval before indexing | `feature/workers-resolution-cards` | 10.1, 6.8 | Pending ❌ |
| 10.4 | Feedback API (CSAT, labels) linked to runs and Langfuse traces | `feature/api-feedback` | 8.4 | Pending ❌ |
| 10.5 | `memory_ttl_sweep` and tenant retention enforcement | `feature/workers-retention` | 10.1 | Pending ❌ |

---

## Phase 11 — Dashboard & Chat Widget (Next.js)

**Goal:** agent, supervisor and admin UI plus the embeddable customer widget. **Depends on:** 2.5 (built against MSW mocks), then 8–10 for live data · **Covers:** FR-31–FR-38, NFR-16

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 11.1 | Next.js 15 shell, next-auth OIDC (PKCE), layout, role-aware navigation | `feature/web-shell-auth` | 1.2 | Pending ❌ |
| 11.2 | Typed API client from OpenAPI v1, plus MSW mocks | `feature/web-api-client` | 2.5 | Pending ❌ |
| 11.3 | Inbox with filters (status, severity, channel, assignee, AI state) | `feature/web-inbox` | 11.1, 11.2 | Pending ❌ |
| 11.4 | Ticket detail: conversation, AI timeline, evidence panel, plan, action cards | `feature/web-ticket-detail` | 11.1, 11.2 | Pending ❌ |
| 11.5 | Approvals queue with argument diff and optimistic decisions | `feature/web-approvals` | 11.1, 11.2 | Pending ❌ |
| 11.6 | Escalations queue | `feature/web-escalations` | 11.1, 11.2 | Pending ❌ |
| 11.7 | Analytics overview API (KPIs) | `feature/api-analytics` | 8.4 | Pending ❌ |
| 11.8 | Analytics dashboard: volume, autonomous rate, FRT, MTTR, CSAT, cost, escalation reasons | `feature/web-analytics` | 11.2 | Pending ❌ |
| 11.9 | Admin pages: knowledge, policies (YAML editor + test console), tools, users, tenant | `feature/web-admin` | 11.1, 11.2 | Pending ❌ |
| 11.10 | Embeddable chat widget (React Web Component, Shadow DOM, SSE) | `feature/web-chat-widget` | 11.2 | Pending ❌ |
| 11.11 | Live realtime integration: WebSocket events invalidate query keys | `feature/web-realtime` | 8.3, 11.3–11.6 | Pending ❌ |
| 11.12 | WCAG 2.1 AA accessibility audit and fixes | `feature/web-accessibility` | 11.3–11.10 | Pending ❌ |

---

## Phase 12 — Evaluation & Test Hardening

**Goal:** release gates that prove quality and safety. **Depends on:** Phases 9 and 10 · **Covers:** NFR-12, PRD §8 and §12

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 12.1 | Resolution golden set (200), eval runner and CI gate thresholds | `feature/evals-resolution-gate` | 9.6 | Pending ❌ |
| 12.2 | Red-team injection suite (200), with zero injection-to-action and zero leakage required | `feature/evals-redteam` | 9.2, 5.5 | Pending ❌ |
| 12.3 | `online_eval_sample` job (5–10% LLM-judge scoring to Langfuse) | `feature/workers-online-eval` | 8.2 | Pending ❌ |
| 12.4 | Playwright E2E: widget to resolution, and the approval round-trip | `feature/e2e-playwright` | 11.10, 11.5, 9.3 | Pending ❌ |
| 12.5 | Load tests (k6/Locust): 1k concurrent chats against NFR-01/03 | `feature/perf-load-tests` | 8.3 | Pending ❌ |
| 12.6 | Security checklist: JWT edge cases, CORS/CSP, upload limits, webhook HMAC, secret-redaction test | `feature/security-hardening` | 8.5, 3.6 | Pending ❌ |

---

## Phase 13 — Containerisation & Infrastructure as Code

**Goal:** identical images and one Terraform interface across AWS, Azure and GCP. **Depends on:** Phase 1 (Terraform), Phase 8 (images, Helm) · **Covers:** NFR-14

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 13.1 | Hardened multi-stage images for all services (non-root, read-only FS), Syft SBOM, Trivy scan | `feature/infra-docker-images` | 8.2 | Pending ❌ |
| 13.2 | Helm chart: HPA/KEDA, NetworkPolicies, PDBs, probes, migration hook, `values-{aws,azure,gcp}.yaml` | `feature/infra-helm-chart` | 13.1 | Pending ❌ |
| 13.3 | Terraform modules for AWS (VPC, EKS, RDS, ElastiCache, S3, Secrets Manager, ECR, edge) | `feature/infra-terraform-aws` | 1.1 | Pending ❌ |
| 13.4 | Terraform modules for Azure (VNet, AKS, Postgres Flexible, Redis, Blob, Key Vault, ACR, Front Door) | `feature/infra-terraform-azure` | 1.1 | Pending ❌ |
| 13.5 | Terraform modules for GCP (VPC, GKE, Cloud SQL, Memorystore, GCS, Secret Manager, Artifact Registry, Cloud Armor) | `feature/infra-terraform-gcp` | 1.1 | Pending ❌ |
| 13.6 | Module-interface conformance tests (same inputs and outputs on every cloud) | `feature/infra-terraform-conformance` | 13.3–13.5 | Pending ❌ |

---

## Phase 14 — CI/CD & Multi-Cloud Deployment

**Goal:** the same commit and image digest deployed to all three clouds. **Depends on:** Phases 12 and 13 · **Covers:** PRD §12 items 4 and 6

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 14.1 | Pipeline: eval gate, security scans, buildx, Cosign signing, push to ECR/ACR/Artifact Registry over OIDC | `feature/ci-build-sign-push` | 12.1, 13.1 | Pending ❌ |
| 14.2 | Deploy-dev matrix (aws/azure/gcp): Terraform apply, `helm upgrade --atomic`, smoke tests | `feature/cd-deploy-dev` | 14.1, 13.2, 13.6 | Pending ❌ |
| 14.3 | Tag-based promotion dev → staging → prod with environment protection | `feature/cd-promotion` | 14.2 | Pending ❌ |
| 14.4 | AWS dev, staging and prod environments | `feature/deploy-aws` | 14.2 | Pending ❌ |
| 14.5 | Azure dev, staging and prod environments | `feature/deploy-azure` | 14.2 | Pending ❌ |
| 14.6 | GCP dev, staging and prod environments | `feature/deploy-gcp` | 14.2 | Pending ❌ |

---

## Phase 15 — Observability, Operations & v1.0 Release

**Goal:** a production-ready platform with dashboards, alerts, runbooks and signed-off acceptance criteria. **Depends on:** Phase 14 · **Covers:** NFR-11, BO-7, PRD §12

| # | Sub-task | Branch | Depends on | Status |
|---|---|---|---|---|
| 15.1 | OTel collector, Grafana dashboards (golden signals plus AI signals) per cloud | `feature/ops-dashboards` | 14.4–14.6 | Pending ❌ |
| 15.2 | Alerts: error rate, P95 latency, tool failures, circuit open, pending approvals, budget, DLQ, groundedness | `feature/ops-alerts` | 15.1 | Pending ❌ |
| 15.3 | Runbooks for the top 5 failure modes | `feature/ops-runbooks` | 15.2 | Pending ❌ |
| 15.4 | Per-tenant and per-ticket cost monitoring (target < US$0.08/ticket) | `feature/ops-cost-monitoring` | 15.1 | Pending ❌ |
| 15.5 | v1.0 acceptance sign-off against PRD §12 (Must FRs, eval targets, red-team, load, three-cloud smoke) | `feature/release-v1-acceptance` | 15.1–15.4 | Pending ❌ |
