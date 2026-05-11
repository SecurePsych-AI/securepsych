import logging

from fastapi import APIRouter, Request, Response, HTTPException
from proxy.client import proxy_request
from config import settings
from db import AsyncSessionLocal, crud

logger = logging.getLogger(__name__)
router = APIRouter()

SUMMARIZER_URL = settings.services.summarizer_url
RAG_URL = settings.services.rag_url


@router.post("")
@router.post("/")
async def summarize(request: Request):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    content_type = request.headers.get("content-type", "")

    project_id: str | None = None
    document_id: str | None = None
    filename_redacted: str | None = None

    if "application/json" in content_type:
        # Mode B: look up document from RAG, then summarize
        body = await request.json()
        document_id = body.get("document_id")
        project_id = body.get("project_id")
        if not document_id:
            raise HTTPException(status_code=400, detail="Missing document_id in JSON body")

        request.state.document_id = document_id

        rag_resp = await proxy_request("GET", f"{RAG_URL}/documents/{document_id}/content", user_id=user_id)
        if rag_resp.status_code != 200:
            return Response(content=rag_resp.content, status_code=rag_resp.status_code, media_type=rag_resp.headers.get("content-type"))

        rag_data = rag_resp.json()
        doc_text = rag_data.get("text", "")
        filename_redacted = rag_data.get("filename", f"{document_id}.txt")

        file_bytes = doc_text.encode("utf-8")
        files = {"file": (f"{document_id}.txt", file_bytes, "text/plain")}

        sum_resp = await proxy_request("POST", f"{SUMMARIZER_URL}/summarize", user_id=user_id, files=files)

    elif "multipart/form-data" in content_type:
        # Mode A: direct file upload
        form = await request.form()
        file = form.get("file")
        project_id = form.get("project_id")
        if not file:
            raise HTTPException(status_code=400, detail="Missing 'file' form data")

        filename_redacted = file.filename
        file_bytes = await file.read()
        files = {"file": (file.filename, file_bytes, file.content_type)}

        sum_resp = await proxy_request("POST", f"{SUMMARIZER_URL}/summarize", user_id=user_id, files=files)

    else:
        raise HTTPException(status_code=415, detail="Unsupported Content-Type. Expected application/json or multipart/form-data")

    if sum_resp.status_code == 200 and project_id:
        sum_data = sum_resp.json()
        async with AsyncSessionLocal() as session:
            async with session.begin():
                project = await crud.get_project_by_id(session, project_id, user_id)
                if project:
                    await crud.log_summary_run(
                        session,
                        project_id=project_id,
                        document_id=document_id,
                        filename_redacted=filename_redacted,
                        summary=sum_data.get("summary", ""),
                        page_count=sum_data.get("page_count", 0),
                    )
                else:
                    logger.warning("summarize: project_id %s not found for user %s — skipping persistence", project_id, user_id)
        return Response(content=sum_resp.content, status_code=sum_resp.status_code, media_type=sum_resp.headers.get("content-type"))

    if sum_resp.status_code == 200 and not project_id:
        logger.warning("summarize: no project_id provided — output will not be persisted")

    return Response(content=sum_resp.content, status_code=sum_resp.status_code, media_type=sum_resp.headers.get("content-type"))
