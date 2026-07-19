#!/usr/bin/env bash
set -euo pipefail
: "${MISTRAL_API_KEY:?Set MISTRAL_API_KEY locally; never commit it}"
command -v vibe >/dev/null || { echo "vibe not found; install mistral-vibe==2.21.0" >&2; exit 2; }

case "${1:-}" in
  1inch) slug=1inch ;;
  erc4626) slug=erc4626 ;;
  uniswap-v2) slug=uniswap-v2 ;;
  *) echo "usage: $0 {1inch|erc4626|uniswap-v2}" >&2; exit 2 ;;
esac
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WORK="$ROOT/workspaces/$slug"
PROMPT="$ROOT/examples/$slug/prompt.txt"
VHOME="$ROOT/.vibe-repro/tasks"
RAW="$VHOME/raw/$slug"
OUT="$ROOT/reproduction-logs/$slug"
[ -d "$WORK" ] || { echo "missing $WORK; run prepare_benchmark_workspaces.py" >&2; exit 2; }
mkdir -p "$VHOME" "$RAW" "$OUT"
cat > "$VHOME/config.toml" <<'EOF'
active_model = "leanstral"
system_prompt_id = "lean"
default_agent = "lean"
installed_agents = ["lean"]
enable_telemetry = false
enable_update_checks = false
enable_notifications = false
api_timeout = 180.0
auto_compact_threshold = 200000
EOF
export VIBE_HOME="$VHOME"
export LOG_LEVEL=DEBUG
set +e
vibe --prompt "$(cat "$PROMPT")" --agent lean --auto-approve \
  --max-turns 12 --max-tokens 50000 --output streaming \
  --trust --workdir "$WORK" >"$RAW/trace.ndjson" 2>"$RAW/stderr.log"
rc=$?
set -e
printf '%s\n' "$rc" > "$OUT/exit-code.txt"
python3 - "$ROOT" "$RAW" "$VHOME" "$OUT" <<'PY'
import os, pathlib, re, sys
root, raw, home, out = map(pathlib.Path, sys.argv[1:])
secret = os.environ['MISTRAL_API_KEY']
def clean(text: str) -> str:
    text = text.replace(secret, '[REDACTED]')
    text = re.sub(r'(?i)bearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer [REDACTED]', text)
    return text.replace(str(root), '<REPRO_ROOT>').replace(str(pathlib.Path.home()), '<HOME>')
for name in ('trace.ndjson', 'stderr.log'):
    src = raw / name
    (out / name).write_text(clean(src.read_text(errors='replace')) if src.exists() else '')
src = home / 'logs' / 'vibe.log'
if src.exists():
    (out / 'vibe.log').write_text(clean(src.read_text(errors='replace')))
PY
printf 'Vibe exited %s; sanitized logs: %s\n' "$rc" "$OUT"
exit "$rc"
