---
paths:
  - "apps/api/alembic/**/*"
  - "apps/api/app/db/**/*.py"
---

# Database and migrations (LLD section 3.2)

- Schema changes go through Alembic only. Never edit an applied migration; add a new one.
- UUID primary keys via `gen_random_uuid()`, `TIMESTAMPTZ` with `now()`, `CHECK` constraints for text enums, `CITEXT` for emails.
- Every tenant table has `tenant_id` and an RLS policy `USING (tenant_id = current_setting('app.tenant_id')::uuid)`.
- `audit_log` is append-only: the app role gets no UPDATE or DELETE.
- `action_requests.idempotency_key` stays UNIQUE.
- LangGraph checkpoint tables live in the `langgraph` schema and are library-managed. Don't migrate them by hand.
- Migrations run as a Helm pre-upgrade hook Job, so keep them backward compatible with the running release.
- Migrations are sequential work. Never run two migration changes in parallel agents.
