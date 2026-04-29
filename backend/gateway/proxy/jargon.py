import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from proxy.client import proxy_request
from config import settings
from db import AsyncSessionLocal, crud

logger = logging.getLogger(__name__)
router = APIRouter()

JARGON_URL = str(settings.services.jargon_url)


@router.post("/simplify")
async def simplify_jargon(request: Request):
    if not settings.features.jargon_enabled:
        raise HTTPException(status_code=503, detail="Jargon service not enabled")

    user_id = getattr(request.state, "user_id", "unauthenticated")
    content_type = request.headers.get("content-type", "")

    project_id: str | None = None
    input_text: str | None = None
    level: int = 3

    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Missing 'file' form data")
        project_id = form.get("project_id")
        level = int(form.get("level", "3"))
        file_bytes = await file.read()
        files = {"file": (file.filename, file_bytes, file.content_type)}
        resp = await proxy_request(
            "POST", f"{JARGON_URL}/simplify",
            user_id=user_id, files=files, data={"level": str(level)},
        )
    else:
        body = await request.json()
        project_id = body.pop("project_id", None)
        input_text = body.get("text", "")
        level = int(body.get("level", 3))
        resp = await proxy_request(
            "POST", f"{JARGON_URL}/simplify",
            user_id=user_id, json=body,
        )

    if resp.status_code == 200 and project_id:
        jargon_data = resp.json()
        async with AsyncSessionLocal() as session:
            project = await crud.get_project_by_id(session, project_id, user_id)
            if project:
                preview = (input_text or "")[:200]
                async with session.begin():
                    await crud.log_jargon_run(
                        session,
                        project_id=project_id,
                        level=level,
                        input_preview=preview,
                        simplified_text=jargon_data.get("simplified_text", ""),
                        fk_grade=jargon_data.get("flesch_kincaid_grade", 0.0),
                    )
            else:
                logger.warning("simplify: project_id %s not found for user %s — skipping persistence", project_id, user_id)

    if resp.status_code == 200 and not project_id:
        logger.warning("simplify: no project_id provided — output will not be persisted")

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )
