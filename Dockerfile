FROM python:3.11-slim

# System deps for building pyswisseph
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy entire repo (including panchanga.py and api/)
COPY . /app

# Install API dependencies
RUN pip install --no-cache-dir -r api/requirements.txt

EXPOSE 8000

# Start FastAPI with uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
