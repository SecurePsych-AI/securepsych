import sys
import os
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest

FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"


@pytest.fixture(scope="session")
def redacted_eval_pdf() -> Path:
    """Hand-scrubbed PDF with no real PII — used for extraction/ingestion tests."""
    path = FIXTURES_DIR / "redacted_eval.pdf"
    if not path.exists():
        pytest.skip(
            "redacted_eval.pdf not present — place hand-scrubbed PDF at "
            "backend/tests/fixtures/redacted_eval.pdf"
        )
    return path
