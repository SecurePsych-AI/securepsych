import os
import sys
import yaml

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ValidationError, field_validator

from services.simplifier import run_simplify_chain
from utils.flesch_kincaid import flesch_kincaid_grade

# Shared extraction — package path works in test env (backend/pytest.ini pythonpath=..)
# Fallback handles running uvicorn directly from backend/jargon/
try:
    from backend.shared.extraction import extract_pdf
except ImportError:
    # Add securepsych/ root so backend.shared is importable when running uvicorn
    # directly from backend/jargon/ rather than via pytest with configured pythonpath
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
    from backend.shared.extraction import extract_pdf

_MAX_PDF_BYTES = 50 * 1024 * 1024
_OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]

# Load all prompt templates at startup — fail fast if any file is missing
_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_TEMPLATES: dict[int, str] = {}
for _level in range(1, 6):
    _path = os.path.join(_PROMPT_DIR, f"level_{_level}.txt")
    with open(_path) as _f:
        _TEMPLATES[_level] = _f.read()

router = APIRouter()


def _feature_enabled() -> bool:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_path) as f:
        return yaml.safe_load(f).get("jargon", {}).get("enabled", True)


class SimplifyRequest(BaseModel):
    text: str
    level: int = 3

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: int) -> int:
        if not (1 <= v <= 5):
            raise ValueError("level must be between 1 and 5")
        return v


class SimplifyResponse(BaseModel):
    simplified_text: str
    flesch_kincaid_grade: float
    level: int


@router.post("/simplify", response_model=SimplifyResponse)
async def simplify(request: Request) -> SimplifyResponse:
    if not _feature_enabled():
        raise HTTPException(status_code=503, detail="Feature unavailable")

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()
        try:
            req = SimplifyRequest(**body)
        except ValidationError as exc:
            # exc.errors() may contain non-serializable ctx values (e.g. ValueError);
            # keep only the JSON-safe fields that match FastAPI's standard 422 format
            raise HTTPException(
                status_code=422,
                detail=[{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()],
            )
        text = req.text
        level = req.level

    elif "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=422, detail="Missing 'file' field")

        try:
            level = int(form.get("level", 3))
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="'level' must be an integer")
        if not (1 <= level <= 5):
            raise HTTPException(status_code=422, detail="level must be between 1 and 5")

        pdf_bytes = await file.read(_MAX_PDF_BYTES + 1)
        if len(pdf_bytes) > _MAX_PDF_BYTES:
            raise HTTPException(status_code=413, detail="PDF exceeds maximum allowed size")

        result = await extract_pdf(pdf_bytes, file.filename or "upload.pdf", _OLLAMA_BASE_URL)
        text = result.full_text
        if not text.strip():
            raise HTTPException(status_code=422, detail="No extractable text found in the PDF")

    else:
        raise HTTPException(
            status_code=415,
            detail="Content-Type must be application/json or multipart/form-data",
        )

    output = await run_simplify_chain(text, _TEMPLATES[level])
    grade = flesch_kincaid_grade(output)
    return SimplifyResponse(simplified_text=output, flesch_kincaid_grade=grade, level=level)
