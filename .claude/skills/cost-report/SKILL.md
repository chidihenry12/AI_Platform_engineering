---
name: cost-report
description: Report Claude Code token cost, cache-read share of input, and per-model or per-agent cost for the last 7 days (or the window given). Use to check spend and cache health.
argument-hint: "[--days N]"
context: fork
agent: log-triage
model: haiku
---

Produce a usage report for this project.

1. If `scripts/claude_usage/report.py` exists, run:
   `python -I scripts/claude_usage/report.py --days 7 $ARGUMENTS`
   (an explicit `--days` in the arguments wins).
2. If the script is missing, say "usage report script not written yet (see scripts/claude_usage/README.md)", tell the user `/usage` shows the current session's cache hit ratio, and stop.

Report, in at most 30 lines:
- total cost (USD) and tokens, by model;
- cache-read share = cache_read / (input + cache_creation + cache_read), for the whole window and per day;
- cost per agent type, or the line "per-agent breakdown unavailable on this version" if the script can't attribute it;
- any day where the cache-read share dropped more than 10 points from the previous day.
