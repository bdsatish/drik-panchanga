"""Web UI and CGI helpers for the panchanga calendar PDF generator.

Run locally from the repository root::

    python -m webapp.app

Gunicorn (Railway)::

    gunicorn webapp.app:app --bind 0.0.0.0:$PORT
"""

import sys
from pathlib import Path

# Ensure repo root is importable when CGI scripts load this package alone.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(_REPO_ROOT))
