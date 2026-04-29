import sys
import os
from pathlib import Path

import pytest

# Add backend/summarizer/ to sys.path so service-relative imports work
# (e.g. `from main import app`)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

# Summarizer service reads OLLAMA_BASE_URL / OLLAMA_MODEL at module import time
# and has no load_dotenv() of its own. Load from the service's .env so tests use
# the real configured values. override=True ensures .env wins over any stale shell vars.
# If a required var is missing, the import fails clearly.
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

# backend/conftest.py is outside rootdir when running `cd backend/summarizer && pytest`.
# Define the shared PDF fixture here so smoke tests work in isolated sessions.
_FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


@pytest.fixture(scope="session")
def redacted_eval_pdf_1() -> Path:
    path = _FIXTURES_DIR / "redacted_eval_1.pdf"
    if not path.exists():
        pytest.skip(f"redacted_eval_1.pdf not present — place hand-scrubbed PDF at backend/tests/fixtures/redacted_eval_1.pdf")
    return path
