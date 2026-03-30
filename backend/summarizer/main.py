from routes import health, summarize
import logging
import os

import yaml
from fastapi import FastAPI

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
    title="SecurePsych Summarizer",
    description=(
        "Structured document summarization for psychoeducational evaluations. "
        "Stateless — one document per request. No student data persisted."
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(summarize.router)
