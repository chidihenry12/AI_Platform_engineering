---
name: scaffold-package
description: Scaffold a new ACSRP monorepo package (api, agents, workers, an mcp-server, web, shared-schemas, ui) with its manifest, lint/type/test config, Dockerfile and health checks. Use when starting Phase 2 Foundations or adding a service.
argument-hint: "[apps/<name> | apps/mcp-servers/<name> | packages/<name>]"
disable-model-invocation: true
---

Scaffold the package at: $ARGUMENTS

Follow the layout in CLAUDE.md "Repository Layout" and LLD sections 1, 2 and 16. Create only what the package needs.

**Python package** (api, agents, workers, mcp-servers/*, shared-schemas):
- `pyproject.toml` (uv-managed, Python 3.12) with deps from LLD section 1, plus dev deps `ruff`, `mypy`, `pytest`, `pytest-asyncio`, `httpx`;
- `[tool.ruff]`, `[tool.mypy]` (strict on the package), and `[tool.pytest.ini_options]` with an `integration` marker;
- the source package, `tests/` with one passing smoke test, and `README.md` listing the package's commands;
- for services:
  - a multi-stage `Dockerfile` (`python:3.12-slim`, uv, non-root user, read-only root FS friendly);
  - a `/healthz` + `/readyz` (API) or a metrics port (agents 9100, MCP 8100+).

**JS package** (web, ui):
- `package.json` with `lint`, `typecheck` (`tsc --noEmit`) and `test` (`vitest run`) scripts, plus `tsconfig.json` and the eslint config;
- web: Next.js 15 App Router, standalone output, `node:22-alpine` Dockerfile on port 3000.

**Then**:
- add the service to `infra/docker/compose.yaml` with a pinned image tag and `depends_on`;
- reuse `packages/shared-schemas` instead of duplicating contracts;
- run the package's lint, type and test commands and report the results.

Tell the user to update CLAUDE.md "Common Commands" and `.claude/settings.json` `permissions.allow` once commands are real. Don't edit those yourself.
