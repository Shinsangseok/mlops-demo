FROM python:3.11-slim

RUN pip install --no-cache-dir huggingface_hub

RUN groupadd -g 10001 appgroup \
    && useradd -m -u 10001 -g appgroup -s /usr/sbin/nologin appuser

USER appuser
