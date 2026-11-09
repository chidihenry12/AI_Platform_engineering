# Claude Code usage report (placeholder)

`/cost-report` runs `python -I scripts/claude_usage/report.py`. The script is
not written yet. This file describes it.

## What it should do

- Python standard library only (`json`, `pathlib`, `argparse`, `datetime`, `collections`).
- Read the session transcripts for this project from
  `~/.claude/projects/<project-slug>/*.jsonl`. On Windows `~` is
  `%USERPROFILE%`; this project's slug is `C--Users-pc-Desktop-resolva`.
  Also read subagent transcripts if they are stored next to the sessions
  (check the session folder layout first).
- For each assistant entry with `message.usage`, sum:
  `input_tokens`, `cache_creation_input_tokens` (split by
  `cache_creation.ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`),
  `cache_read_input_tokens`, `output_tokens`, grouped by day and by
  `message.model`.
- Cache-read share = `cache_read / (input + cache_creation + cache_read)`.
- Per-agent cost: attribute entries to an agent type only if the transcript
  identifies it (for example `isSidechain` plus a subagent type field or file
  name). Otherwise print `per-agent breakdown unavailable on this version`.
- Cost uses a price table kept at the top of the script (USD per MTok, first-party API,
  checked 2026-11-08 at platform.claude.com/docs/en/about-claude/pricing):

  | Model | Input | 5m write | 1h write | Cache read | Output |
  |---|---|---|---|---|---|
  | claude-opus-5-5 | 4.00 | 5.00 | 8.00 | 0.20 | 20.00 |
  | claude-sonnet-5-5 | 2.00 | 2.50 | 4.00 | 0.10 | 10.00 |
  | claude-haiku-5-5 (prompts up to 100k) | 0.10 | 0.125 | 0.20 | 0.01 | 0.50 |

  On a Claude subscription these are notional API-equivalent costs, not a bill.
- Flags: `--days N` (default 7), `--json`.
- Output: at most 30 lines, as listed in `.claude/skills/cost-report/SKILL.md`.
