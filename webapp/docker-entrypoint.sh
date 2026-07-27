#!/bin/sh
# Railway injects PORT at runtime; keep bind address explicit and logs on stdout.
set -eu
PORT="${PORT:-8080}"
echo "panchanga: starting gunicorn on 0.0.0.0:${PORT}"
exec gunicorn webapp.app:app \
  --bind "0.0.0.0:${PORT}" \
  --workers 1 \
  --threads 2 \
  --timeout 120 \
  --no-control-socket \
  --access-logfile - \
  --error-logfile -
