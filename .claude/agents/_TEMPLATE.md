Agent template. This file has no frontmatter on purpose, so Claude Code does
not load it as an agent. To make a new agent, copy the block below into
`.claude/agents/<name>.md` as the file's first lines, without the code fence.

```markdown
---
name: <kebab-name>
description: Delegate here to <job>. Trigger - <phrases or situations>.
model: <haiku | sonnet | opus>   # opus only for planning, architecture, narrow consults
effort: <low | medium | high>
tools: <comma-separated minimal list>
maxTurns: <number>
---

<Instructions: scope, what not to touch, which checks to run.>

Return limit: <maximum size and shape of the reply>.
```
