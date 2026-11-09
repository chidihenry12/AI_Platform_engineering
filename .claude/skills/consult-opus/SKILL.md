---
name: consult-opus
description: Ask Opus one narrow, hard question, such as a design trade-off, a bug hypothesis, or how an invariant applies. Answers in 300 words or fewer.
argument-hint: "[one specific question, with file paths if relevant]"
context: fork
agent: opus-consultant
disable-model-invocation: true
---

Question: $ARGUMENTS
