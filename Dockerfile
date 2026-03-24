FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libatspi2.0-0 \
    libnspr4 \
    libnss3 \
    libgbm1 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright fastapi uvicorn pydantic python-dateutil python-dotenv

# Install Playwright browser
RUN python -m playwright install chromium

# Create user first
RUN useradd --create-home --shell /bin/bash appuser

# Create directory for browser cache and copy from root's cache
RUN mkdir -p /app/.cache/ms-playwright && \
    cp -r /root/.cache/ms-playwright/* /app/.cache/ms-playwright/ && \
    chown -R appuser:appuser /app/.cache

# Set the browser path for the appuser
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright

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
