#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

git diff --check

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --config .gitleaks.toml --redact --verbose
else
  printf 'WARN: gitleaks is unavailable; secret scan skipped\n' >&2
fi

printf 'dmf-config-tool documentation checks completed\n'
