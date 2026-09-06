#!/usr/bin/env bash
# Ensure Swiss Ephemeris .se1 files exist under SE_EPHE_PATH (or a given directory).
# Used by local setup, CI, and the Docker build. Downloads the upstream tarball
# with Python stdlib (portable: no git/curl/wget/apt) and extracts ephe/ with tar.
set -euo pipefail

TARGET="${1:-${SE_EPHE_PATH:-}}"
if [[ -z "${TARGET}" ]]; then
  echo "usage: $0 /path/to/ephe   (or set SE_EPHE_PATH)" >&2
  exit 2
fi

SWISSEPH_TARBALL_URL="${SWISSEPH_TARBALL_URL:-https://github.com/aloistr/swisseph/archive/refs/heads/master.tar.gz}"

ephe_has_data() {
  local dir="$1"
  [[ -d "$dir" ]] || return 1
  compgen -G "${dir}/*.se1" >/dev/null
}

if ephe_has_data "${TARGET}"; then
  echo "ephe: using existing data in ${TARGET}"
  exit 0
fi

echo "ephe: fetching Swiss Ephemeris files into ${TARGET}"
mkdir -p "${TARGET}"
tmp="$(mktemp -d)"
cleanup() { rm -rf "${tmp}"; }
trap cleanup EXIT

tarball="${tmp}/swisseph.tar.gz"
python3 - "${SWISSEPH_TARBALL_URL}" "${tarball}" <<'EOF'
import sys, urllib.request
url, dest = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(url, timeout=300) as response, open(dest, "wb") as handle:
  handle.write(response.read())
EOF

tar -xzf "${tarball}" -C "${tmp}"
# Flatten ephe/ (incl. nested ephe/sat/) into TARGET: planetary .se1 files
# plus the star catalog and leap-second table; skip ephe/ep4/ and docs.
find "${tmp}" -path '*/ephe/*' -type f \
  \( -name '*.se1' -o -name 'sefstars.txt' -o -name 'seleapsec.txt' \) \
  -exec cp -t "${TARGET}" {} +

if ! ephe_has_data "${TARGET}"; then
  echo "error: no .se1 files found after download" >&2
  exit 1
fi
echo "ephe: ready ($(find "${TARGET}" -maxdepth 1 -name '*.se1' | wc -l) .se1 files)"
