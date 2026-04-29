"""
Centralized ChromaDB client singleton for the RAG service.

All three modules (api.py, ingestion.py, rag_query.py) import _ensure_collection
from here so that HNSW index parameters are applied consistently at collection
creation time. get_or_create_collection silently ignores HNSW parameters when
the collection already exists; the explicit get-then-create pattern here ensures
the parameters are applied on first run and the existing index is used thereafter.
"""

import os
from typing import Optional

import chromadb
from chromadb.config import Settings

CHROMA_PATH: str = os.environ["CHROMA_PATH"]
COLLECTION_NAME: str = os.environ["CHROMA_COLLECTION"]

_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None


def _ensure_collection() -> chromadb.Collection:
    """
    Return the ChromaDB collection, creating it with explicit HNSW parameters
    if it does not already exist.  Calling this multiple times is safe — the
    singleton is reused after the first call.
    """
    global _client, _collection
    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )

    existing = {c.name for c in _client.list_collections()}
    if COLLECTION_NAME in existing:
        _collection = _client.get_collection(name=COLLECTION_NAME)
    else:
        _collection = _client.create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine",
                # M: connections per layer — higher improves recall at the cost of
                # index build time and memory; 16 is the ChromaDB default.
                "hnsw:M": 16,
                # ef_construction: search width during index build — 100 is the
                # default; increase for higher recall if build time allows.
                "hnsw:ef_construction": 100,
                # ef (ef_search): query-time search width — 50 gives better recall
                # than the default (10) with minimal latency impact on local hardware.
                "hnsw:ef": 50,
            },
        )

    return _collection
