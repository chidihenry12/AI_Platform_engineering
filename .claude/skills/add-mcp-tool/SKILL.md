---
name: add-mcp-tool
description: Add a new tool to an ACSRP MCP server (crm, billing, orders, ticketing, status, knowledge), with schema, registry entry, policy tier, audit and tests. Use whenever a new back-office action or read is exposed to agents.
argument-hint: "[server].[tool_name] [read|write] [short purpose]"
---

Add the MCP tool described here: $ARGUMENTS

Read LLD section 8 (tool catalogue, example server) and section 7.8 (policy) first. Do these steps in order:

1. **Input model** in `apps/mcp-servers/<server>/`:
   - a Pydantic model with strict field patterns (IDs like `^INV-\d{6,}$`), `Literal` enums, `condecimal` for money;
   - no free-text fields that could carry amounts or IDs.
2. **Tool function** with `@mcp.tool(annotations={...})`:
   - set `readOnlyHint`, `destructiveHint` and `idempotentHint` honestly;
   - call `authorize(ctx, scope="tools:read"|"tools:write")`;
   - for write tools, read `idempotency_key` from `ctx.request_context.meta` and pass it to the backend;
   - pass `tenant=caller.tenant_id` to the backend.
3. **Registry entry** in `apps/agents/mcp_client/`:
   - set `server`, `name`, `input_model`, `read_only`, and the default `risk_tier`;
   - add an agent allow-list. Write tools are allowed for `resolution` only; read tools for the agents in HLD 4.2.
4. **Policy**:
   - write tools get a `agents/policy/policies/<server>.yaml` entry (`default_tier` + `rules`), or an explicit default tier;
   - `prohibited` is used for account-destroying actions.
5. **Verification**: for write tools, add the read-back check that `execute_actions_node` calls after the call.
6. **Audit**: confirm `tool.execute` audit logging covers the tool (it's generic in the executor; add it only if the tool bypasses the executor).
7. **Tests**:
   - schema rejects bad IDs and amounts;
   - the policy tier for every rule;
   - an idempotent replay returns the prior result;
   - a non-allowed agent is refused by the registry;
   - a contract snapshot of the tool schema.
8. Update the tool table in LLD section 8.1 only if the user asks. Otherwise list the doc change in your summary.

Never let the prompt be the enforcement point. The registry and policy engine enforce access (CLAUDE.md invariants 1 to 4).
