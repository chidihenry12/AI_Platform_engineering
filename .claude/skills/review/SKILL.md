---
name: review
description: Review the current uncommitted diff, or a named path or commit range, and return ranked findings. Runs on Sonnet via the code-reviewer agent.
argument-hint: "[optional path or commit range]"
context: fork
agent: code-reviewer
---

Review this target: $ARGUMENTS

If the target is empty, review `git diff` plus `git diff --cached`. If this isn't a git repository, say so and review the files the caller named instead.

Return ranked findings only.
