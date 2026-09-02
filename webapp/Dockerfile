# Railway / container image for the panchanga PDF web UI.
# Build from the repository root:
#   docker build -f webapp/Dockerfile -t panchanga .
FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         ca-certificates build-essential \
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

# Swiss Ephemeris .se1 data (~100 MB) — downloaded at build time via Python.
ENV SE_EPHE_PATH=/app/ephe
ENV PYTHONPATH=/app
RUN python3 -c "
import os, sys, io, urllib.request, tarfile
url = 'https://github.com/aloistr/swisseph/archive/refs/heads/master.tar.gz'
print('Downloading ephemeris data...')
resp = urllib.request.urlopen(url, timeout=120)
tf = tarfile.open(fileobj=io.BytesIO(resp.read()), mode='r:gz')
members = [
    m for m in tf.getmembers()
    if m.name.startswith('swisseph-master/ephe/')
    and (m.name.endswith('.se1') or m.name.endswith('sefstars.txt') or m.name.endswith('seleapsec.txt'))
]
os.makedirs('/app/ephe', exist_ok=True)
for m in members:
    f = tf.extractfile(m)
    with open(f'/app/ephe/{os.path.basename(m.name)}', 'wb') as out:
        out.write(f.read())
print(f'Extracted {len(members)} ephemeris files')
if not any(f.endswith('.se1') for f in os.listdir('/app/ephe')):
    sys.exit('ERROR: no .se1 files found in /app/ephe')
"

# Railway injects PORT at runtime.
ENV PORT=8080
EXPOSE 8080

# One worker: Swiss Ephemeris is process-global. Timeout stays generous for
# cold starts and high-latitude edge cases even though a typical PDF is ~0.4s.
# Entrypoint expands $PORT and disables gunicorn's control socket (fails on
# read-only / missing $HOME layouts used by some hosts).
ENTRYPOINT ["/docker-entrypoint.sh"]
