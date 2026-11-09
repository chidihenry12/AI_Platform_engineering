---
name: add-graph-node
description: Add or change a node in the ACSRP LangGraph agent runtime, covering the schema, the structured() call, routing edges, timeouts, tracing, cost recording and fake-LLM graph tests. Use for any agent or graph change.
argument-hint: "[node name] [purpose]"
---

Add or change the graph node described here: $ARGUMENTS

Read LLD sections 7.1 to 7.4 and the supervisor routing rules in CLAUDE.md first.

1. **Schema**: define the output model in `packages/shared-schemas` if the API reads it, otherwise in `apps/agents/graph/state.py`. Extend `TicketState` only with fields that have a clear reducer (`operator.add` for lists that accumulate).
2. **Node** in `apps/agents/graph/nodes/<name>.py`:
   - return a partial state dict and append its name to `route_history`;
   - call the LLM only through `structured(tier, Schema, messages)` (temperature 0.1, repair retries);
   - wrap untrusted content in `<untrusted>…</untrusted>`.
3. **Contract**: add a row to the node table (model tier, output schema, timeout, retries) and enforce the timeout in code.
4. **Routing**: wire edges in `builder.py`. Deterministic routing stays in `routing.py`, not in prompts. Respect `MAX_STEPS`, the clarification cap (2) and the knowledge-round cap (2).
5. **Tools**: a read-only node may call only read tools through the registry. Only `resolution` proposes write actions, as `ActionProposal`, never by executing them.
6. **Observability**:
   - add an OTel span `agent.node` with `ticket.id`, `run.id`, `node`, `model`, `tokens`;
   - record `tokens_in/out`, latency and cost to `agent_steps`, Langfuse and the Redis budget;
   - update `acsrp_node_latency_seconds`.
7. **Failure**: on LLM failure, return `degraded` so the supervisor escalates. Never lose the ticket.
8. **Prompt**: add a versioned prompt in `apps/agents/prompts/` and record its version on `agent_runs.prompt_versions`.
9. **Tests**:
   - a graph test with `FakeListChatModel` scripted outputs covering each outgoing edge;
   - an invalid-output repair test;
   - never call a real LLM in tests.
