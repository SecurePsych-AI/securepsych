import sys
import os
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest

FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"


def _pdf_fixture(filename: str):
    path = FIXTURES_DIR / filename
    if not path.exists():
        pytest.skip(f"{filename} not present — place hand-scrubbed PDF at backend/tests/fixtures/{filename}")
    return path


@pytest.fixture(scope="session")
def redacted_eval_pdf() -> Path:
    """Hand-scrubbed PDF with no real PII (unnumbered variant per test guide)."""
    return _pdf_fixture("redacted_eval.pdf")


@pytest.fixture(scope="session")
def redacted_eval_pdf_1() -> Path:
    """First hand-scrubbed eval PDF — used for extraction, ingestion, and AI smoke tests."""
    return _pdf_fixture("redacted_eval_1.pdf")


@pytest.fixture(scope="session")
def redacted_eval_pdf_2() -> Path:
    """Second hand-scrubbed eval PDF."""
    return _pdf_fixture("redacted_eval_2.pdf")


@pytest.fixture(scope="session")
def iep_pdf() -> Path:
    """Hand-scrubbed IEP PDF."""
    return _pdf_fixture("iep_1.pdf")
