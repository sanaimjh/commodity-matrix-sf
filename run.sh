#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
STREAMLIT="${ROOT}/.venv/bin/streamlit"

if [[ ! -x "$PYTHON" ]]; then
  echo "Creating virtual environment with Python 3.13..."
  /usr/local/bin/python3.13 -m venv .venv
  "$PYTHON" -m pip install --upgrade pip
  "$PYTHON" -m pip install -r requirements.txt
fi

exec "$STREAMLIT" run app.py
