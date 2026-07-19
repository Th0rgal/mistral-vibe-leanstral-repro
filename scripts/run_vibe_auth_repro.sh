#!/usr/bin/env bash
set -euo pipefail

: "${MISTRAL_API_KEY:?Set MISTRAL_API_KEY in your local environment; never commit it}"
command -v vibe >/dev/null || { echo "vibe not found; install mistral-vibe==2.21.0" >&2; exit 2; }

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VHOME="$ROOT/.vibe-repro/auth"
OUT="$ROOT/reproduction-logs/vibe-auth"
mkdir -p "$VHOME" "$OUT" "$ROOT/workspaces/auth-empty"
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
vibe --prompt 'Reply exactly AUTH_OK. Do not call tools.'   --agent lean --max-turns 1 --max-tokens 1000 --output json   --trust --workdir "$ROOT/workspaces/auth-empty"   >"$OUT/stdout.log" 2>"$OUT/stderr.log"
rc=$?
set -e
printf '%s
' "$rc" > "$OUT/exit-code.txt"
# Vibe logs do not normally contain the key, but review before publishing.
if [ -f "$VHOME/logs/vibe.log" ]; then cp "$VHOME/logs/vibe.log" "$OUT/vibe.log"; fi
printf 'Vibe exited %s; logs: %s
' "$rc" "$OUT"
exit "$rc"
