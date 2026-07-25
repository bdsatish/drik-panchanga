"""Web UI and CGI helpers for the panchanga calendar PDF generator.

Run locally from the repository root::

    python -m webapp.app

Gunicorn (Railway)::

    gunicorn webapp.app:app --bind 0.0.0.0:$PORT
"""
