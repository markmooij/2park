FROM python:3.12-slim

RUN pip install --no-cache-dir requests fastapi uvicorn pydantic python-dateutil python-dotenv

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY api.py api_client.py models.py errors.py auth.py rate_limit.py ./
COPY .env.example ./

RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

USER appuser

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/health')" || exit 1

ENV PYTHONUNBUFFERED=1
ENV PORT=8090

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8090"]
