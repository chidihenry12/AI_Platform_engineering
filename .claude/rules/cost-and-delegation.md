# Cost and delegation

- Finish one task before starting another. Keep a session to one topic, and use `/clear` or a new session for a new topic.
- Don't edit CLAUDE.md, `.claude/rules/`, `.claude/agents/`, `.claude/skills/` or `.claude/settings.json` during a working session. Make those changes between sessions.
- Don't add or remove MCP servers mid-session. Don't switch models with `/model` mid-session unless the task needs it.
- Batch questions to the user into one message.
- Use the skills:
  - `/plan` (Opus) to write a plan, `/implement` (Sonnet) to execute it, `/review` (Sonnet) to check the diff;
  - `/consult-opus` for one narrow hard question;
  - `/cost-report` for spend and cache health.
- Send codebase search to `Explore` (Haiku), and long command output (test runs, builds, logs) to `log-triage` (Haiku). Keep raw logs out of the main conversation.
- Run agents in parallel only for independent tasks with disjoint file scopes, such as different packages, separate test files or separate searches:
  - at most 3 agents, one git worktree each (`isolation: worktree`);
  - give each agent an explicit file scope;
  - check for overlap first.
- Run work in sequence when it touches the same file, a migration, a lock file, shared config, generated code or a schema. Until this folder is a git repository, run everything in sequence.
- Commit only after `/review` and green tests.
