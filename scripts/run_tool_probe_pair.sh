#!/usr/bin/env bash
set -euo pipefail

: "${MISTRAL_API_KEY:?Set MISTRAL_API_KEY locally; never commit it}"
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT=${1:-"$ROOT/reproduction-logs/tool-protocol"}
mkdir -p "$OUT"

python3 "$ROOT/scripts/probe_tool_calling.py" \
  --base-url https://api.mistral.ai/v1 \
  --endpoint-label mistral-api \
  --api-key-env MISTRAL_API_KEY \
  --model labs-leanstral-1-5 \
  --attempts 10 \
  --output "$OUT/hosted.json"

if [ -n "${LEANSTRAL_LOCAL_BASE_URL:-}" ] && [ -n "${LEANSTRAL_LOCAL_API_KEY:-}" ]; then
  python3 "$ROOT/scripts/probe_tool_calling.py" \
    --base-url-env LEANSTRAL_LOCAL_BASE_URL \
    --endpoint-label local-openai-compatible \
    --api-key-env LEANSTRAL_LOCAL_API_KEY \
    --model "${LEANSTRAL_LOCAL_MODEL:-leanstral-1.5}" \
    --attempts 10 \
    --output "$OUT/local.json"
else
  printf '%s\n' 'Local probe skipped: set LEANSTRAL_LOCAL_BASE_URL and LEANSTRAL_LOCAL_API_KEY to compare a local server.' >&2
fi

python3 - "$OUT" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
for name in ("hosted", "local"):
    path = root / f"{name}.json"
    if not path.exists():
        continue
    data = json.loads(path.read_text())
    print(name, json.dumps(data["summary"], sort_keys=True))
PY
