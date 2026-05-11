import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── Security: enforce LangSmith data-scrubbing before any LangChain import ────
# LANGCHAIN_HIDE_INPUTS/OUTPUTS stop LangSmith from capturing prompt payloads
# (which contain full document text). Set unconditionally in code so they
# cannot be accidentally omitted from .env, preventing a FERPA violation.
os.environ["LANGCHAIN_HIDE_INPUTS"] = "true"
os.environ["LANGCHAIN_HIDE_OUTPUTS"] = "true"
# ─────────────────────────────────────────────────────────────────────────────

import yaml
from fastapi import FastAPI
from routes import health, simplify

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s — %(message)s",
)


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


config = _load_config()

app = FastAPI(
    title="SecurePsych Jargon Simplifier",
    description=(
        "Clinical text simplification for psychoeducational evaluations. "
        "Stateless — one request per call. No student data persisted."
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(simplify.router)
