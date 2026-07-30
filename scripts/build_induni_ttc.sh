#!/usr/bin/env bash
# Rebuild fonts/IndUni-H.ttc from upstream IndUni-H.zip (maintainer helper).
# Requires: curl, unzip, and fonttools (pip install fonttools) — not a runtime dep.
# OTF→TTF conversion uses fontTools' upstream snippet (not vendored here):
#   https://github.com/fonttools/fonttools/blob/main/Snippets/otf2ttf.py
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/fonts"
TTC_PATH="$OUT_DIR/IndUni-H.ttc"
ZIP_URL="${INDUNI_H_URL:-https://bombay.indology.info/software/fonts/induni/IndUni-H.zip}"
OTF2TTF_URL="${OTF2TTF_URL:-https://raw.githubusercontent.com/fonttools/fonttools/main/Snippets/otf2ttf.py}"

if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PYTHON="${VIRTUAL_ENV}/bin/python"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

if ! "$PYTHON" -c 'import fontTools' >/dev/null 2>&1; then
  echo "error: fontTools required to rebuild (pip install fonttools)" >&2
  exit 1
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/induni-h.XXXXXX")"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT

echo "Downloading $ZIP_URL ..."
curl -fsSL -o "$tmp/IndUni-H.zip" "$ZIP_URL"
unzip -q "$tmp/IndUni-H.zip" -d "$tmp/src"

echo "Fetching fontTools Snippets/otf2ttf.py ..."
curl -fsSL -o "$tmp/otf2ttf.py" "$OTF2TTF_URL"

mkdir -p "$tmp/ttf"
faces=(
  IndUni-H-Regular
  IndUni-H-Bold
  IndUni-H-Oblique
  IndUni-H-BoldOblique
)
: > "$tmp/ttf_list.txt"
for face in "${faces[@]}"; do
  echo "  converting ${face}.otf → .ttf"
  "$PYTHON" "$tmp/otf2ttf.py" "$tmp/src/${face}.otf" -o "$tmp/ttf/${face}.ttf"
  printf '%s\n' "$tmp/ttf/${face}.ttf" >> "$tmp/ttf_list.txt"
done

"$PYTHON" - "$tmp/ttf_list.txt" "$TTC_PATH" <<'PY'
import sys
from pathlib import Path
from fontTools.ttLib import TTFont, TTCollection

list_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
paths = [line.strip() for line in list_path.read_text().splitlines() if line.strip()]
fonts = [TTFont(path) for path in paths]
out_path.parent.mkdir(parents=True, exist_ok=True)
collection = TTCollection()
collection.fonts = fonts
collection.save(str(out_path))
print(f"wrote {out_path} ({out_path.stat().st_size} bytes, {len(fonts)} faces)")
PY

cp -f "$tmp/src/README-H" "$OUT_DIR/README-H"
echo "Updated $OUT_DIR/README-H"
