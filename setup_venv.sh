#!/usr/bin/env bash
# Create a local virtual environment and install calendar-generator dependencies.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT/.venv}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found in PATH" >&2
  exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_MINOR="$(python3 -c 'import sys; print(sys.version_info.minor)')"
if (( PYTHON_MINOR < 9 )); then
  echo "error: Python 3.9+ is required (found ${PYTHON_VERSION})" >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "Using existing virtual environment in $VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$ROOT/requirements.txt"

cat <<EOF

Setup complete.

Activate the environment:
  source "$VENV_DIR/bin/activate"

Generate a calendar PDF:
  python "$ROOT/generate_panchanga_calendar.py" --city Bangalore --start 2026-03

Run tests:
  python -m unittest discover -s "$ROOT" -p 'test_*.py'
EOF
