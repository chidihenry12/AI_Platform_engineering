---
name: add-api-endpoint
description: Add a FastAPI endpoint under /api/v1 with router, service, repository, RBAC permission, Problem Details errors, tenant scoping and tests. Use for any new or changed REST route.
argument-hint: "[METHOD] [/path] [roles] [purpose]"
---

Add the endpoint described here: $ARGUMENTS

Read LLD section 4 (endpoints, contracts, SSE events) and section 5 (auth, RBAC matrix) first.

1. **Schemas**: Pydantic request and response DTOs in `apps/api/app/schemas/`, with length limits and cross-field rules via `model_validator(mode="after")`.
2. **Router** in `apps/api/app/api/v1/`:
   - keep it thin;
   - guard it with `Depends(require("<permission>"))`, adding the permission to `ROLE_PERMISSIONS` if it's new;
   - list endpoints use cursor pagination.
3. **Service** in `app/services/`: business logic, plus re-checks for higher-risk permissions such as `approval:decide:high`.
4. **Repository** in `app/db/`: every query runs in a transaction that did `SET LOCAL app.tenant_id`, so RLS applies.
5. **Errors**: RFC 9457 Problem Details using the LLD section 19 `type` codes. Rate-limited routes return 429 with `Retry-After`.
6. **Writes that trigger agent runs** return 202 and enqueue `run_ticket_graph`. Never run the graph inside the request.
7. **Idempotency and dedupe**: honour `client_message_id`. Verify webhooks with HMAC + timestamp (5 min skew).
8. **Audit**: admin, policy, approval and memory changes write to `audit_log`.
9. **Tests**:
   - an httpx test per role (allowed / 403);
   - a cross-tenant access test (another tenant sees 404);
   - validation errors;
   - an OpenAPI snapshot update.
