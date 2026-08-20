#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

if command -v uv >/dev/null 2>&1; then
  uv sync --extra dev
else
  PYTHON_BIN=""
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3,11))'; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
  if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3.11+ is required" >&2
    exit 1
  fi
  "$PYTHON_BIN" -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e '.[dev]'
fi

PYTHON_RUN=".venv/bin/python"
[ -x "$PYTHON_RUN" ] || PYTHON_RUN="$(command -v python3)"
"$PYTHON_RUN" benchmarks/check1_text_excel/generate_input.py
"$PYTHON_RUN" benchmarks/check2_visual_artifact/generate_input.py
mkdir -p state/codex-deepseek-home workspaces runs results packages
cp config/codex-deepseek-config.toml state/codex-deepseek-home/config.toml
chmod 700 state state/codex-deepseek-home
if [ -f config/.env.local ]; then chmod 600 config/.env.local; fi
chmod +x scripts/*.sh tools/vision_daemon.py tools/vision_helper.py
echo "Bootstrap complete. Activate with: . .venv/bin/activate"

