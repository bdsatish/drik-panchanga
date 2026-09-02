# Railway / container image for the panchanga PDF web UI.
# Build from the repository root:
#   docker build -f webapp/Dockerfile -t panchanga .
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer cache).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Core calendar library + web package (see root .dockerignore).
COPY generate_panchanga_calendar.py generate_monthly_calendar.py festival_rules.py panchanga.py \
     cities.json festivals.cfg sanskrit_names.json ./
COPY fonts ./fonts
COPY webapp ./webapp
COPY webapp/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Swiss Ephemeris .se1 data (~100 MB) — required for accurate calculations.
ENV SE_EPHE_PATH=/app/ephe
ENV PYTHONPATH=/app
RUN mkdir -p /app/ephe \
    && git clone --depth 1 https://github.com/aloistr/swisseph.git /tmp/swisseph \
    && cp /tmp/swisseph/ephe/*.se1 /tmp/swisseph/ephe/sefstars.txt /tmp/swisseph/ephe/seleapsec.txt /app/ephe/ 2>/dev/null || true \
    && rm -rf /tmp/swisseph \
    && test -n "$(ls /app/ephe/*.se1 2>/dev/null | head -1)"

# Railway injects PORT at runtime.
ENV PORT=8080
EXPOSE 8080

# One worker: Swiss Ephemeris is process-global. Timeout stays generous for
# cold starts and high-latitude edge cases even though a typical PDF is ~0.4s.
# Entrypoint expands $PORT and disables gunicorn's control socket (fails on
# read-only / missing $HOME layouts used by some hosts).
ENTRYPOINT ["/docker-entrypoint.sh"]
