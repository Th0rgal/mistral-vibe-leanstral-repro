#!/usr/bin/env bash
set -euo pipefail

: "${MISTRAL_API_KEY:?Set MISTRAL_API_KEY in your local environment; never commit it}"
command -v vibe >/dev/null || { echo "vibe not found; install mistral-vibe==2.21.0" >&2; exit 2; }

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VHOME="$ROOT/.vibe-repro/auth"
RAW="$VHOME/raw"
OUT="$ROOT/reproduction-logs/vibe-auth"
mkdir -p "$VHOME" "$RAW" "$OUT" "$ROOT/workspaces/auth-empty"
cat > "$VHOME/config.toml" <<'EOF'
active_model = "leanstral"
system_prompt_id = "lean"
default_agent = "lean"
installed_agents = ["lean"]
enable_telemetry = false
enable_update_checks = false
enable_notifications = false
api_timeout = 30.0
api_retry_max_elapsed_time = 5.0
EOF

export VIBE_HOME="$VHOME"
export LOG_LEVEL=DEBUG
set +e
vibe --prompt 'Reply exactly AUTH_OK. Do not call tools.' \
  --agent lean --max-turns 1 --max-tokens 1000 --output json \
  --trust --workdir "$ROOT/workspaces/auth-empty" \
  >"$RAW/stdout.log" 2>"$RAW/stderr.log"
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
for name in ('stdout.log', 'stderr.log'):
    src = raw / name
    (out / name).write_text(clean(src.read_text(errors='replace')) if src.exists() else '')
src = home / 'logs' / 'vibe.log'
if src.exists():
    (out / 'vibe.log').write_text(clean(src.read_text(errors='replace')))
PY
printf 'Vibe exited %s; sanitized logs: %s\n' "$rc" "$OUT"
exit "$rc"
