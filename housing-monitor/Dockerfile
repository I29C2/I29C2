# Multi-arch base image works on Raspberry Pi 5 (arm64) and x86_64.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Berlin

WORKDIR /app

# System deps for lxml on slim images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libxml2 libxslt1.1 tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persisted data lives in mounted volumes.
RUN mkdir -p logs database

CMD ["python", "app.py"]
