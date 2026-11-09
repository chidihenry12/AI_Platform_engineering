---
name: plan
description: Write an implementation plan to docs/plans/ before coding a multi-file, cross-package, schema or migration change. Runs on Opus via the planner agent.
argument-hint: "[change request or topic]"
context: fork
agent: planner
disable-model-invocation: true
---

Plan this change for the ACSRP monorepo:

$ARGUMENTS

Write the plan to `docs/plans/<topic>.md` as your agent instructions describe, and return only the path.
