# Execution Steps

This document provides a clear sequence to start the Drik Panchanga application.

## Option 1: Run API with Docker (recommended)

1. Open terminal in project root:

```bash
cd /Users/gduggirala/projects/drik-panchanga
```

2. (Optional) Stop old container if running:

```bash
docker ps
docker stop distracted_chatterjee 2>/dev/null || true
docker rm distracted_chatterjee 2>/dev/null || true
docker stop drik-panchanga-api 2>/dev/null || true
docker rm drik-panchanga-api 2>/dev/null || true
```

3. Build latest image:

```bash
docker build -t drik-panchanga-api:latest .
```

4. Run container:

```bash
docker run -d --name drik-panchanga-api -p 8000:8000 drik-panchanga-api:latest
```

5. Verify server is up:

```bash
docker ps
curl -sS http://127.0.0.1:8000/
```

6. Open API docs:

```text
http://127.0.0.1:8000/docs
```

7. View logs if needed:

```bash
docker logs -f drik-panchanga-api
```

## Option 2: Run API locally (without Docker)

1. Open terminal in project root:

```bash
cd /Users/gduggirala/projects/drik-panchanga
```

2. Install API dependencies:

```bash
python3 -m pip install -r api/requirements.txt
```

3. Start FastAPI server:

```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

4. Verify:

```bash
curl -sS http://127.0.0.1:8000/
```

## Stop Commands

- Stop Docker container:

```bash
docker stop drik-panchanga-api
```

- Stop local uvicorn process (if running in background):

```bash
pkill -f "uvicorn api.main:app"
```
