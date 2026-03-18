#!/usr/bin/env bash
set -euo pipefail

RUN_GIT_CHECKS="${RUN_GIT_CHECKS:-1}"
RUN_GIT_SECRETS_CACHED="${RUN_GIT_SECRETS_CACHED:-1}"
RUN_GIT_SECRETS_HISTORY="${RUN_GIT_SECRETS_HISTORY:-0}"
FAIL_ON_UNSTAGED_CHANGES="${FAIL_ON_UNSTAGED_CHANGES:-1}"
ENABLE_GITLEAKS="${ENABLE_GITLEAKS:-1}"
ENABLE_MARKDOWN_LINK_CHECKS="${ENABLE_MARKDOWN_LINK_CHECKS:-1}"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

have_command() {
  command -v "$1" >/dev/null 2>&1
}

run_markdown_link_check() {
  python3 - <<'PY'
from __future__ import annotations

import pathlib
import re
import sys

root = pathlib.Path.cwd()
pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
skip_prefixes = ("http://", "https://", "mailto:", "#")
failures: list[tuple[str, str]] = []

for path in root.rglob("*.md"):
    if any(part in {".git", ".venv", ".pytest_cache", ".ruff_cache"} for part in path.parts):
        continue
    text = path.read_text(encoding="utf-8")
    for target in pattern.findall(text):
        target = target.strip()
        if not target or target.startswith(skip_prefixes):
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        if not target or target.startswith(skip_prefixes):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        if not resolved.exists():
            failures.append((str(path.relative_to(root)), target))

if failures:
    print("FAIL: broken relative Markdown links detected:")
    for source, target in failures:
        print(f"- {source}: {target}")
    sys.exit(1)
PY
}

run_gitleaks() {
  local args=(--no-banner --redact --source .)
  if [[ -f ".gitleaks.toml" ]]; then
    args+=(--config .gitleaks.toml)
  fi

  if gitleaks detect "${args[@]}"; then
    return 0
  fi

  if gitleaks protect --help >/dev/null 2>&1; then
    gitleaks protect --no-banner --redact --staged
    return $?
  fi

  return 1
}

if [[ "$RUN_GIT_CHECKS" == "1" ]] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[git] status --short --branch"
  git status --short --branch

  echo "[git] current branch"
  git branch --show-current || true

  echo "[git] remotes"
  git remote -v || true

  if [[ "$FAIL_ON_UNSTAGED_CHANGES" == "1" ]] && ! git diff --quiet --exit-code; then
    echo "FAIL: unstaged changes are present. Stage intentionally before using this gate."
    exit 20
  fi

  echo "[git] diff --cached --stat"
  git diff --cached --stat || true

  echo "[git] diff --cached --name-status"
  git diff --cached --name-status || true

  echo "[git] diff --cached --check"
  git diff --cached --check

  if [[ "$RUN_GIT_SECRETS_CACHED" == "1" ]]; then
    if have_command git-secrets; then
      git secrets --scan --cached
      echo "OK: git-secrets cached scan passed"
    else
      echo "[git] WARN: git-secrets not installed; skipping cached scan."
    fi
  fi

  if [[ "$RUN_GIT_SECRETS_HISTORY" == "1" ]]; then
    if have_command git-secrets; then
      git secrets --scan-history
      echo "OK: git-secrets history scan passed"
    else
      echo "[git] WARN: git-secrets not installed; skipping history scan."
    fi
  fi
fi

echo "[format] uv run ruff format --check ."
uv run ruff format --check .

echo "[lint] uv run ruff check ."
uv run ruff check .

echo "[types] uv run pyright"
uv run pyright

echo "[tests] uv run pytest"
uv run pytest

echo "[security] uv run pip-audit"
uv run pip-audit

if [[ "$ENABLE_GITLEAKS" == "1" ]]; then
  if have_command gitleaks; then
    echo "[security] gitleaks"
    run_gitleaks
    echo "OK: gitleaks found no secrets"
  else
    echo "[security] WARN: gitleaks not installed; skipping secret scan."
  fi
fi

if [[ "$ENABLE_MARKDOWN_LINK_CHECKS" == "1" ]]; then
  echo "[docs] Markdown link check"
  run_markdown_link_check
fi

echo "[config] pyproject.toml syntax check"
python3 - <<'PY'
import pathlib
import tomllib

with pathlib.Path("pyproject.toml").open("rb") as handle:
    tomllib.load(handle)
PY

echo "OK: checks passed"
