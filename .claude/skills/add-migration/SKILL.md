---
name: add-migration
description: Create an Alembic migration for ACSRP tables, with tenant RLS, enums-as-CHECK, audit rules and an isolation test. Use for any schema change. Never run two migration tasks in parallel.
argument-hint: "[what changes, e.g. add column X to tickets]"
---

Create the migration described here: $ARGUMENTS

Read LLD section 3.2 (DDL) and `.claude/rules/migrations.md` first. This is sequential work, so don't parallelise it.

1. Update the SQLAlchemy model in `apps/api/app/db/`.
2. Generate the migration with `uv run alembic revision --autogenerate -m "<message>"` from `apps/api`, then review it by hand. Autogenerate misses RLS, CHECK constraints and extensions.
3. Conventions:
   - UUID PK `gen_random_uuid()`;
   - `TIMESTAMPTZ NOT NULL DEFAULT now()`;
   - text enums as `CHECK (... IN (...))`;
   - `CITEXT` for emails;
   - the indexes the access pattern needs.
4. For a new tenant table:
   - add a `tenant_id UUID NOT NULL`;
   - `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`;
   - add the policy `USING (tenant_id = current_setting('app.tenant_id')::uuid)`.
5. Never grant UPDATE or DELETE on `audit_log` to the app role. Never edit an applied migration. Never touch the `langgraph` schema.
6. Keep it backward compatible with the running release, because it runs as a Helm pre-upgrade Job. Use expand, then migrate, then contract across releases for renames and drops.
7. Write a downgrade, or explain why it is irreversible.
8. Tests:
   - `upgrade head` then `downgrade -1` on a testcontainers Postgres;
   - for tenant tables, extend the cross-tenant RLS isolation test.
