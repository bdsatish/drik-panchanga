#!/usr/bin/env python3
"""Download Swiss Ephemeris data files into $SE_EPHE_PATH (used by the Docker build)."""

import io
import os
import sys
import tarfile
import urllib.request

URL = "https://github.com/aloistr/swisseph/archive/refs/heads/master.tar.gz"
DEST = os.environ.get("SE_EPHE_PATH", "/app/ephe")
SUFFIXES = (".se1", "sefstars.txt", "seleapsec.txt")


def main():
  print(f"Downloading {URL} ...", flush=True)
  with urllib.request.urlopen(URL, timeout=300) as response:
    payload = response.read()
  os.makedirs(DEST, exist_ok=True)
  count = 0
  with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
    for member in archive.getmembers():
      parts = member.name.split("/")
      if len(parts) != 3 or parts[1] != "ephe" or not member.name.endswith(SUFFIXES):
        continue
      extracted = archive.extractfile(member)
      if extracted is None:
        continue
      with open(os.path.join(DEST, parts[2]), "wb") as handle:
        handle.write(extracted.read())
      count += 1
  print(f"Extracted {count} ephemeris files into {DEST}")
  if not any(name.endswith(".se1") for name in os.listdir(DEST)):
    sys.exit("ERROR: no .se1 files found after extraction")


if __name__ == "__main__":
  main()
