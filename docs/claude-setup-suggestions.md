# Claude Code setup: suggestions

Written 2026-11-08 against Claude Code 2.1.319 on the first-party Anthropic platform
(claude.ai login). This is the only place where changes to protected files are
proposed. Nothing here has been applied.

## 1. Protected files found

| Path | Lines | Location |
|---|---|---|
| `CLAUDE.md` | 308 | root |

No `SKILLS.md` exists anywhere in the project.

## 2. Suggested changes to `CLAUDE.md`

The root `CLAUDE.md` loads in full every session and is part of the cached
prefix. At 308 lines it is over the 200-line target.

1. **Move area-specific conventions into scoped rules.** These rules now exist
   and load only when Claude touches matching files:
   - "Coding Conventions > Python", "MCP servers", "API surface" are in `.claude/rules/python.md`
   - "Coding Conventions > Database" is in `.claude/rules/migrations.md`
   - "Coding Conventions > Frontend" is in `.claude/rules/frontend.md`
   - "Infra Notes" is in `.claude/rules/infra.md`
   - "Redis keys" can move to `python.md` or stay as a pointer to LLD section 3.4

   After moving them, replace each section with a one-line pointer. That saves
   roughly 70 to 90 lines.
2. **Shorten reference material that Claude can read on demand.** "Tech Stack",
   "Repository Layout", "Product Targets" and "Testing & Quality Gates" repeat
   the LLD and PRD. Keep a 3 to 5 line summary of each and point to the LLD
   section.
3. **Keep in CLAUDE.md:** Project overview, current status, the
   "Non-Negotiable Invariants", "Common Commands", "Working Agreements".
4. **Add a Cost and delegation section.** It currently lives in
   `.claude/rules/cost-and-delegation.md` (an unscoped rule, which loads every
   session). If you prefer it in CLAUDE.md, paste this and delete the rule file:

   ```markdown
   ## Cost and delegation
   - Finish one task before starting another; keep a session to one topic.
   - Don't edit CLAUDE.md, `.claude/rules/`, agents, skills or settings during a session; change them between sessions.
   - Batch questions into one message.
   - Use `/plan` → `/implement` → `/review`; `/consult-opus` for one narrow question; `/cost-report` for spend.
   - Send search to `Explore` and long output to `log-triage`.
   - Commit only after `/review` and green tests.
   ```
5. **No conflicts found** with the cost plan. CLAUDE.md doesn't ask for
   auto-commits or a fixed model.
6. **Commands are planned, not real.** "Common Commands" says so. Update it,
   and `permissions.allow` in `.claude/settings.json`, once `pyproject.toml` and
   `package.json` files exist.

## 3. `SKILLS.md`

None found, so nothing to migrate. Claude Code loads skills from
`.claude/skills/<name>/SKILL.md`, not from `SKILLS.md`.

## 4. Per-run budgets (tool calls per run, guideline)

Going past a budget means the task should be split. It doesn't mean the run failed.

| Agent | Model | Budget | maxTurns set |
|---|---|---|---|
| Explore | haiku | 10 | 30 |
| log-triage | haiku | 10 | 15 |
| opus-consultant | opus | 10 | 10 |
| code-reviewer | sonnet | 30 | 60 |
| planner | opus | 40 | 40 |
| architect | opus | 40 | 40 |
| implementer | sonnet | 120 | 120 |
| test-engineer (not created) | sonnet | 80 | – |

Scale these up once the monorepo has real code. They are starting points for an
empty repo.

## 5. Skipped agents and skills

| Item | Why skipped | Add it when |
|---|---|---|
| `test-engineer` agent | No test command exists yet; all commands are planned | `uv run pytest` or `vitest` runs in at least one package |
| `test` skill | Its target agent `test-engineer` isn't created | Same as above |
| `tests.md` rule | No tests exist yet | First `tests/` folder lands |
| `wait` skill | No long-running jobs exist yet (no builds, deploys or test suites) | Docker builds, testcontainers suites or Terraform applies exist |
| `pr-review` skill | Neither `gh` nor `glab` is installed | `gh` is installed and authenticated |
| `fix-issue` skill | No issue tracker is referenced | The repo links a GitHub/Jira project |

## 6. Other notes and deviations from the setup spec

- **`Agent(opus-consultant)` isn't enforced inside subagents.** The 2.1.319
  docs say the `Agent(type)` allowlist works only for an agent running as the
  main thread, and that parentheses in a subagent's `tools` list are ignored.
  `implementer` and `code-reviewer` therefore list plain `Agent`, with the
  limit written in their instructions. The spawn-depth limit of 2 stops deeper
  chains.
- **`cost-report` runs as a fork on Haiku, not inline.** The docs say an
  inline skill whose `model` differs from the session model is a model switch,
  so the next main-conversation request re-reads the whole history uncached. A
  fork sets the subagent's model instead and leaves the main cache alone.
- **`_TEMPLATE.md` has no frontmatter.** With frontmatter it would load as a
  real agent and add itself to every session's agent list. The template sits
  inside a code fence instead.
- **Auto memory is on (the default).** It wasn't changed, because the spec
  says only not to *enable* memory before measuring it. To measure without it,
  set `"autoMemoryEnabled": false` in `.claude/settings.local.json` for a week
  and compare the cache-read share.
- **The `.env*` read deny also blocks `.env.example`.** If agents need the
  example file, add `"Read(./.env.example)"` to `permissions.allow`. Check that
  allow wins over deny for this case before relying on it.
- **Read-deny rules don't stop `cat .env` through Bash.** Add Bash deny rules
  or a hook if that matters.
- **Hook timeout isn't set.** A full test run on commit may exceed the default
  hook timeout. Check the hooks reference for the `timeout` field before adding
  one.
