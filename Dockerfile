FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for MariaDB drivers if needed (pymysql is pure-Python; leave minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    nano \
  && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for better caching
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt

RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install -r requirements-dev.txt

# Copy source
COPY . .

ENV PYTHONPATH=/app/src

# Entrypoint handles waiting for DB and migrations
RUN chmod +x docker/entrypoint.sh
ENTRYPOINT ["/app/docker/entrypoint.sh"]

# Default command: run the app smoke entrypoint
CMD ["python", "-m", "app"]
