#!/usr/bin/env bash
# Create a local virtual environment and install calendar-generator dependencies.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT/.venv}"
# Same rules as panchanga.default_se_ephe_path() (stdlib only; no import).
DEFAULT_EPHE_PATH="$(python3 - <<'PY'
import os, sys
if sys.platform == "win32":
    base = os.environ.get("LOCALAPPDATA") or os.path.join(
        os.path.expanduser("~"), "AppData", "Local")
else:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share")
print(os.path.join(base, "swisseph"))
PY
)"
# Swiss Ephemeris .se1 directory baked into venv activate. Override at setup:
#   SE_EPHE_PATH=/path/to/ephemeris/files ./setup_venv.sh
SE_EPHE_PATH="${SE_EPHE_PATH:-$DEFAULT_EPHE_PATH}"
SWISSEPH_REPO_URL="${SWISSEPH_REPO_URL:-https://github.com/aloistr/swisseph.git}"

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

ephe_has_data() {
  local dir="$1"
  [[ -d "$dir" ]] || return 1
  compgen -G "${dir}/*.se1" >/dev/null
}

download_ephemeris() {
  local dest="$1"
  local tmp

  if ! command -v git >/dev/null 2>&1; then
    echo "warning: git is required to download Swiss Ephemeris files; skipping download" >&2
    return 1
  fi

  mkdir -p "$dest"
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/swisseph-ephe.XXXXXX")"

  echo "Downloading Swiss Ephemeris data into $dest ..."
  echo "(sparse clone of ${SWISSEPH_REPO_URL} ephe/)"
  if ! git clone --depth 1 --filter=blob:none --sparse "$SWISSEPH_REPO_URL" "$tmp/swisseph"; then
    rm -rf "$tmp"
    echo "warning: failed to clone $SWISSEPH_REPO_URL; skipping download" >&2
    return 1
  fi
  if ! git -C "$tmp/swisseph" sparse-checkout set ephe; then
    rm -rf "$tmp"
    echo "warning: sparse-checkout of ephe/ failed; skipping download" >&2
    return 1
  fi

  # Planet/moon/asteroid .se1 files plus star catalog; skip seasnam.txt and extras.
  find "$tmp/swisseph/ephe" -maxdepth 1 -type f \( \
      -name '*.se1' -o -name 'sefstars.txt' -o -name 'seleapsec.txt' \
    \) -exec cp -t "$dest" {} +
  rm -rf "$tmp"

  if ! ephe_has_data "$dest"; then
    echo "warning: download finished but no .se1 files found in $dest" >&2
    return 1
  fi
  echo "Ephemeris files ready in $dest"
}

warn_missing_ephemeris() {
  local dest="$1"
  cat >&2 <<EOF

warning: no Swiss Ephemeris .se1 files in:
  $dest

Without those files, pyswisseph cannot use the high-precision Swiss
Ephemeris (SEFLG_SWIEPH). Planet/moon calls typically error or silently
fall back to the coarser built-in Moshier ephemeris, so panchanga dates
and the PDF calendar will be wrong or fail until you place the .se1
files under SE_EPHE_PATH (then re-run this script, or copy them yourself
from https://github.com/aloistr/swisseph/tree/master/ephe).

EOF
}

confirm_ephemeris_download() {
  local reply
  # Non-interactive / CI: do not download.
  if [[ ! -t 0 ]]; then
    echo "No .se1 files found and stdin is not a TTY; skipping download." >&2
    return 1
  fi
  echo
  echo "Swiss Ephemeris .se1 data files (~100 MB) were not found in:"
  echo "  $SE_EPHE_PATH"
  echo "They can be downloaded from:"
  echo "  ${SWISSEPH_REPO_URL%.git}/tree/master/ephe"
  echo "(sparse git clone of the ephe/ directory)."
  read -r -p "Download them now? [y/N] " reply
  case "$reply" in
    [yY]|[yY][eE][sS]) return 0 ;;
    *) return 1 ;;
  esac
}

ensure_ephemeris() {
  local dest="$1"
  if ephe_has_data "$dest"; then
    echo "Using existing ephemeris files in $dest"
    return 0
  fi
  if confirm_ephemeris_download; then
    if ! download_ephemeris "$dest"; then
      warn_missing_ephemeris "$dest"
    fi
  else
    echo "Skipping ephemeris download."
    warn_missing_ephemeris "$dest"
  fi
}

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "Using existing virtual environment in $VENV_DIR"
fi

# Auto-fetch only for the default location (or an empty custom path the user chose).
ensure_ephemeris "$SE_EPHE_PATH"

configure_se_ephe_path() {
  local activate="$VENV_DIR/bin/activate"
  local begin="# >>> drik-panchanga SE_EPHE_PATH >>>"
  local end="# <<< drik-panchanga SE_EPHE_PATH <<<"
  local quoted_path
  quoted_path="$(printf '%q' "$SE_EPHE_PATH")"

  if [[ ! -f "$activate" ]]; then
    echo "error: missing venv activate script: $activate" >&2
    exit 1
  fi

  # Idempotent: replace any previous injection block.
  if grep -qF "$begin" "$activate"; then
    sed -i "\\|$begin|,\\|$end|d" "$activate"
  fi

  cat >> "$activate" <<EOF

$begin
# Swiss Ephemeris data directory (.se1 files). Set at venv creation via
# SE_EPHE_PATH=... ./setup_venv.sh
export SE_EPHE_PATH=$quoted_path
$end
EOF

  echo "Configured SE_EPHE_PATH=$SE_EPHE_PATH in $activate"
}

configure_se_ephe_path

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$ROOT/requirements.txt"

cat <<EOF

Setup complete.

SE_EPHE_PATH (exported on activate):
  $SE_EPHE_PATH

Activate the environment:
  source "$VENV_DIR/bin/activate"

Generate a calendar PDF:
  python "$ROOT/generate_panchanga_calendar.py" --city Bangalore --start 2026-03

Run tests:
  python -m unittest discover -s "$ROOT" -p 'test_*.py'
EOF
