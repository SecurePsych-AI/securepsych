FROM python:3.11-slim

WORKDIR /build
COPY jargon/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r securepsych && useradd -r -g securepsych securepsych

WORKDIR /app
COPY shared/ backend/shared/
COPY jargon/ backend/jargon/

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

USER securepsych
WORKDIR /app/backend/jargon
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
