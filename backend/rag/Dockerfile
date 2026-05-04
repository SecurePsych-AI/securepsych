FROM python:3.11-slim

# build-essential needed for some chromadb/spacy native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY rag/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model used by presidio-analyzer (en_core_web_sm = lightweight)
# Replace with en_core_web_lg for production-grade NER accuracy
RUN python -m spacy download en_core_web_sm

RUN groupadd -r securepsych && useradd -r -g securepsych securepsych

WORKDIR /app
COPY shared/ backend/shared/
COPY rag/ backend/rag/

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 8001)); s.close()" || exit 1

USER securepsych
WORKDIR /app/backend/rag
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
