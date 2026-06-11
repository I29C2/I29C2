FROM python:3.12-slim

# Dependențe de sistem pentru Docling (parsare PDF) și psycopg.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalăm întâi dependențele (cache mai bun la rebuild).
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

COPY . .

EXPOSE 8000

# Comanda implicită e suprascrisă în docker-compose per serviciu.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
