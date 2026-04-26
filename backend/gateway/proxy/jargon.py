from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from proxy.client import proxy_request
from config import settings

router = APIRouter()

JARGON_URL = str(settings.services.jargon_url)


@router.post("/simplify")
async def simplify_jargon(request: Request):
    if not settings.features.jargon_enabled:
        raise HTTPException(status_code=503, detail="Jargon service not enabled")

    user_id = getattr(request.state, "user_id", "unauthenticated")
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Missing 'file' form data")
        level = form.get("level", "3")
        file_bytes = await file.read()
        files = {"file": (file.filename, file_bytes, file.content_type)}
        resp = await proxy_request(
            "POST", f"{JARGON_URL}/simplify",
            user_id=user_id, files=files, data={"level": level},
        )
    else:
        body = await request.json()
        resp = await proxy_request(
            "POST", f"{JARGON_URL}/simplify",
            user_id=user_id, json=body,
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )
