FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir playwright fastapi uvicorn pydantic python-dateutil

RUN python -m playwright install chromium

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libatspi2.0-0 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY api.py scraper.py models.py errors.py auth.py rate_limit.py ./
COPY .env.example ./

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
