FROM python:3.11-slim

WORKDIR /build
COPY summarizer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r securepsych && useradd -r -g securepsych securepsych

WORKDIR /app
COPY shared/ backend/shared/
COPY summarizer/ backend/summarizer/

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

USER securepsych
WORKDIR /app/backend/summarizer
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
