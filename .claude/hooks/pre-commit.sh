#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash). Runs checks only when the Bash command is a
# git commit. Exit 0 lets the command run; exit 2 blocks it and shows stderr to
# Claude. Fails open (exit 0 with a note) when git or a tool is missing.
# POSIX shell features only.

set -u

note() { printf 'pre-commit hook: %s\n' "$*" >&2; }

payload=$(cat)

# Pull tool_input.command out of the JSON payload; fall back to the raw payload.
cmd=""
for py in python python3; do
  if command -v "$py" >/dev/null 2>&1; then
    cmd=$(printf '%s' "$payload" | "$py" -I -c 'import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception:
    pass' 2>/dev/null) && [ -n "$cmd" ] && break
    cmd=""
  fi
done
[ -n "$cmd" ] || cmd=$payload

case $cmd in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

root=${CLAUDE_PROJECT_DIR:-$(pwd)}
cd "$root" 2>/dev/null || { note "cannot cd to project dir, skipping checks"; exit 0; }

if ! command -v git >/dev/null 2>&1; then
  note "git not found, skipping checks"; exit 0
fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  note "not a git repository, skipping checks"; exit 0
fi

# Staged plus unstaged changes, so "git commit -a" and "git add ... && git commit" are covered.
changed=$( { git diff --cached --name-only --diff-filter=ACMR; git diff --name-only --diff-filter=ACMR; } | sort -u )
[ -n "$changed" ] || exit 0

# Map a path to its package directory (monorepo layout from CLAUDE.md).
pkg_of() {
  case $1 in
    apps/mcp-servers/*/*) printf '%s\n' "$1" | cut -d/ -f1-3 ;;
    apps/*/*|packages/*/*) printf '%s\n' "$1" | cut -d/ -f1-2 ;;
    *) : ;;
  esac
}

pkgs=$(printf '%s\n' "$changed" | while IFS= read -r f; do pkg_of "$f"; done | sort -u)

fail=0
check() {
  label=$1; shift
  if ! out=$("$@" 2>&1); then
    note "$label failed"
    printf '%s\n' "$out" | tail -n 20 >&2
    fail=1
  fi
}

# Files changed under $1, relative to $1, filtered by extension regex $2.
files_in() {
  printf '%s\n' "$changed" | while IFS= read -r f; do
    case $f in "$1"/*) printf '%s\n' "${f#"$1"/}" ;; esac
  done | grep -E "$2" || true
}

for pkg in $pkgs; do
  [ -d "$pkg" ] || continue

  if [ -f "$pkg/pyproject.toml" ]; then
    if ! command -v uv >/dev/null 2>&1; then
      note "uv not found, skipping Python checks for $pkg"
    else
      if grep -q mypy "$pkg/pyproject.toml"; then
        check "mypy ($pkg)" uv run --directory "$pkg" mypy .
      fi
      py_files=$(files_in "$pkg" '\.py$')
      if [ -n "$py_files" ] && grep -q ruff "$pkg/pyproject.toml"; then
        # shellcheck disable=SC2086
        check "ruff ($pkg)" uv run --directory "$pkg" ruff check $py_files
      fi
      if [ -d "$pkg/tests" ] && grep -q pytest "$pkg/pyproject.toml"; then
        out=$(uv run --directory "$pkg" pytest -q -m "not integration" 2>&1)
        rc=$?
        # 5 = no tests collected; treat as pass.
        if [ "$rc" -ne 0 ] && [ "$rc" -ne 5 ]; then
          note "pytest ($pkg) failed"; printf '%s\n' "$out" | tail -n 20 >&2; fail=1
        fi
      fi
    fi
  fi

  if [ -f "$pkg/package.json" ]; then
    if ! command -v npx >/dev/null 2>&1; then
      note "npx not found, skipping JS checks for $pkg"
    elif [ ! -d "$pkg/node_modules" ] && [ ! -d node_modules ]; then
      note "node_modules missing, skipping JS checks for $pkg"
    else
      if [ -f "$pkg/tsconfig.json" ]; then
        check "tsc ($pkg)" npx --no-install tsc --noEmit -p "$pkg"
      fi
      js_files=$(files_in "$pkg" '\.(ts|tsx|js|jsx)$')
      if [ -n "$js_files" ] && grep -q '"eslint"' "$pkg/package.json"; then
        # shellcheck disable=SC2086
        check "eslint ($pkg)" sh -c 'cd "$1" && shift && npx --no-install eslint "$@"' sh "$pkg" $js_files
      fi
      if [ -n "$js_files" ] && grep -q '"vitest"' "$pkg/package.json"; then
        # shellcheck disable=SC2086
        check "vitest ($pkg)" sh -c 'cd "$1" && shift && npx --no-install vitest related --run "$@"' sh "$pkg" $js_files
      fi
    fi
  fi
done

# Terraform formatting for changed .tf files outside packages.
tf_files=$(printf '%s\n' "$changed" | grep -E '\.tf$' || true)
if [ -n "$tf_files" ]; then
  if command -v terraform >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    check "terraform fmt" terraform fmt -check $tf_files
  else
    note "terraform not found, skipping fmt check"
  fi
fi

if [ "$fail" -ne 0 ]; then
  note "commit blocked: fix the failures above, then commit again"
  exit 2
fi
exit 0
