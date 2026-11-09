---
name: implement
description: Execute an approved plan from docs/plans/ with the implementer agent (Sonnet). Pass the plan path, and optionally a step range or file scope.
argument-hint: "[docs/plans/<topic>.md] [steps or file scope]"
context: fork
agent: implementer
disable-model-invocation: true
---

Implement the approved plan described here:

$ARGUMENTS

Read the plan first. Work only on the named steps, or on all steps if none are named, and only inside the plan's file scope. Run the checks for every package you change. Don't commit.
