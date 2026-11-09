---
name: add-policy-rule
description: Add or change an action risk-tier rule in the ACSRP policy engine (low, medium, high or prohibited), with tests for every tier and the autonomy-mode overrides. Use when a tool's approval behaviour changes.
argument-hint: "[tool] [condition] -> [tier] [reason]"
---

Change the policy described here: $ARGUMENTS

Read LLD section 7.8 first. The policy engine runs outside the LLM (ADR-07) and must stay deterministic.

1. Edit `apps/agents/policy/policies/<server>.yaml`. Rules evaluate in order, so put the strictest matching rule where it wins. `prohibited` always beats lower tiers.
2. Conditions use only the whitelisted names the safe evaluator exposes (`args`, `customer`, `history`, `order`). Use `simpleeval`, never `eval`. If a new name is needed, add it to the evaluator's whitelist and say so.
3. Add a `reason:` for any rule that raises the tier, because it lands in `action_requests.policy_reasons`.
4. Tests (a table-driven pytest):
   - every rule fires and returns its tier;
   - the boundary values (for example 50 / 50.01 / 300 / 300.01);
   - the `default_tier` fallback;
   - the autonomy overrides: `copilot` makes everything `pending_approval`, `supervised` raises `low` to `medium`, `autonomous` applies the rules as written.
5. Approver roles: `medium` needs an agent, `high` needs a supervisor. If the change affects who approves, check `ApprovalService` and the RBAC matrix (LLD section 5.2).
6. Policies are versioned (FR-40). Bump the policy version and note the change for the audit trail.
