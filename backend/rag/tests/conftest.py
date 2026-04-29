import os
import shutil
import sys
import tempfile

import pytest

# Ensure backend/rag/ is on sys.path so that intra-service imports like
# `from chroma_client import _ensure_collection` resolve correctly when
# test files import modules via the `backend.rag.*` package path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["CHROMA_COLLECTION"] = "securepsych_test"

_CHROMA_TMP = tempfile.mkdtemp(prefix="securepsych_test_chroma_")
_ENTITY_MAP_TMP = tempfile.mkdtemp(prefix="securepsych_test_entity_maps_")

# Forced overrides — must be set before backend.rag.ingestion is imported at
# collection time. load_dotenv() inside ingestion.py won't override already-set vars,
# so these temp dirs take precedence over whatever is in backend/rag/.env.
os.environ["CHROMA_PATH"] = _CHROMA_TMP
os.environ["ENCRYPTED_ENTITY_MAP_PATH"] = _ENTITY_MAP_TMP

# All other vars (ENTITY_MAP_FERNET_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL, etc.)
# load from backend/rag/.env via the load_dotenv() call inside ingestion.py.


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_chroma():
    yield
    shutil.rmtree(_CHROMA_TMP, ignore_errors=True)
    shutil.rmtree(_ENTITY_MAP_TMP, ignore_errors=True)
