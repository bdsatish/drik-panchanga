#!/usr/bin/env bash
# Ensure Swiss Ephemeris .se1 files exist under SE_EPHE_PATH (or a given directory).
# Used by local setup and CI. Sparse-clones aloistr/swisseph when needed.
set -euo pipefail

TARGET="${1:-${SE_EPHE_PATH:-}}"
if [[ -z "${TARGET}" ]]; then
  echo "usage: $0 /path/to/ephe   (or set SE_EPHE_PATH)" >&2
  exit 2
fi

SWISSEPH_REPO_URL="${SWISSEPH_REPO_URL:-https://github.com/aloistr/swisseph.git}"

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

git clone --depth 1 --filter=blob:none --sparse "${SWISSEPH_REPO_URL}" "${tmp}/swisseph"
git -C "${tmp}/swisseph" sparse-checkout set ephe
find "${tmp}/swisseph/ephe" -maxdepth 1 -type f \
  \( -name '*.se1' -o -name 'sefstars.txt' -o -name 'seleapsec.txt' \) \
  -exec cp -t "${TARGET}" {} +

if ! ephe_has_data "${TARGET}"; then
  echo "error: no .se1 files found after clone" >&2
  exit 1
fi
echo "ephe: ready ($(find "${TARGET}" -maxdepth 1 -name '*.se1' | wc -l) .se1 files)"
