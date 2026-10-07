# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -g 10001 appgroup \
    && useradd -m -u 10001 -g appgroup -s /usr/sbin/nologin appuser

COPY --chown=appuser:appgroup main.py .

USER appuser

ENTRYPOINT ["python", "main.py"]
