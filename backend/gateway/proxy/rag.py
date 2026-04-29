import logging

from fastapi import APIRouter, Form, Request, UploadFile, File, Response
from fastapi.responses import JSONResponse
from proxy.client import proxy_request
from config import settings
from db import AsyncSessionLocal, crud

logger = logging.getLogger(__name__)
router = APIRouter()
RAG_URL = settings.services.rag_url


async def _resolve_project(session, project_id: str, user_id: str):
    """Look up project, verify ownership, return the student_id_hash."""
    project = await crud.get_project_by_id(session, project_id, user_id)
    if not project:
        return None
    return project.student_id_hash


@router.post("/upload/preview")
async def preview_document(request: Request, file: UploadFile = File(...)):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    file_bytes = await file.read()
    files = {"file": (file.filename, file_bytes, file.content_type)}
    resp = await proxy_request(
        method="POST",
        url=f"{RAG_URL}/upload/preview",
        user_id=user_id,
        files=files,
    )
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    project_id: str = Form(...),
    strategy: str = Form("standard"),
    preview_token: str | None = Form(None),
):
    user_id = getattr(request.state, "user_id", "unauthenticated")

    async with AsyncSessionLocal() as session:
        student_id_hash = await _resolve_project(session, project_id, user_id)

    if not student_id_hash:
        return JSONResponse(status_code=404, content={"detail": "Project not found or access denied"})

    file_bytes = await file.read()
    files = {"file": (file.filename, file_bytes, file.content_type)}
    data = {"student_id": student_id_hash, "strategy": strategy}
    if preview_token:
        data["preview_token"] = preview_token

    resp = await proxy_request(
        method="POST",
        url=f"{RAG_URL}/upload",
        user_id=user_id,
        student_id_hash=student_id_hash,
        files=files,
        data=data,
    )

    if resp.status_code == 200:
        rag_data = resp.json()
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await crud.log_file_upload(
                    session,
                    project_id=project_id,
                    document_id=rag_data.get("document_id", ""),
                    filename_redacted=rag_data.get("source", file.filename),
                    strategy=rag_data.get("strategy", strategy),
                    chunks_added=rag_data.get("chunks_added", 0),
                )
        # Strip internal fields — student_id_hash and redaction_key must not
        # cross the gateway→client boundary; they have no use in the UI.
        return JSONResponse(content={
            "status": rag_data.get("status"),
            "document_id": rag_data.get("document_id"),
            "source": rag_data.get("source"),
            "strategy": rag_data.get("strategy"),
            "chunks_added": rag_data.get("chunks_added"),
            "avg_chunk_tokens": rag_data.get("avg_chunk_tokens"),
        })

    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))


@router.post("/query")
async def query_document(request: Request):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    body = await request.json()

    project_id = body.get("project_id")
    if not project_id:
        return JSONResponse(status_code=400, content={"detail": "project_id is required"})

    async with AsyncSessionLocal() as session:
        student_id_hash = await _resolve_project(session, project_id, user_id)

    if not student_id_hash:
        return JSONResponse(status_code=404, content={"detail": "Project not found or access denied"})

    # Gateway owns the student namespace — overwrite any client-provided value
    body["student_id"] = student_id_hash
    # Remove project_id before forwarding (RAG service has no concept of it)
    thread_id = body.pop("thread_id", None)
    body.pop("project_id", None)

    if "document_id" in body:
        request.state.document_id = body["document_id"]

    resp = await proxy_request(
        method="POST",
        url=f"{RAG_URL}/query",
        user_id=user_id,
        student_id_hash=student_id_hash,
        json=body,
    )

    if resp.status_code == 200:
        data = resp.json()
        if "chunks" in data:
            del data["chunks"]  # FERPA sanitization requirement

        question = body.get("question", "")
        answer = data.get("answer", "")
        sources = data.get("sources", [])

        async with AsyncSessionLocal() as session:
            async with session.begin():
                thread = await crud.get_or_create_thread(session, project_id, thread_id)
                await crud.add_message(session, thread.id, "user", question, [])
                await crud.add_message(session, thread.id, "assistant", answer, sources)
                thread_id = thread.id

        data["thread_id"] = thread_id
        return JSONResponse(content=data)

    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))


@router.get("/documents")
async def list_documents(request: Request, project_id: str):
    user_id = getattr(request.state, "user_id", "unauthenticated")

    async with AsyncSessionLocal() as session:
        student_id_hash = await _resolve_project(session, project_id, user_id)

    if not student_id_hash:
        return JSONResponse(status_code=404, content={"detail": "Project not found or access denied"})

    resp = await proxy_request(
        method="GET",
        url=f"{RAG_URL}/documents?student_id={student_id_hash}",
        user_id=user_id,
        student_id_hash=student_id_hash,
    )
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))


@router.get("/documents/{document_id}/content")
async def get_document_content(request: Request, document_id: str):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    request.state.document_id = document_id
    resp = await proxy_request(method="GET", url=f"{RAG_URL}/documents/{document_id}/content", user_id=user_id)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))


@router.delete("/documents/{document_id}")
async def delete_document(request: Request, document_id: str, project_id: str):
    user_id = getattr(request.state, "user_id", "unauthenticated")

    # Verify project ownership and that the document belongs to this project
    # before forwarding to RAG — prevents cross-project deletes.
    from sqlalchemy import select
    from db.models import UploadedFile

    file_record_id: str | None = None
    async with AsyncSessionLocal() as session:
        project = await crud.get_project_by_id(session, project_id, user_id)
        if not project:
            return JSONResponse(status_code=403, content={"detail": "Project not found or access denied"})
        result = await session.execute(
            select(UploadedFile).where(
                UploadedFile.document_id == document_id,
                UploadedFile.project_id == project.id,
            )
        )
        file_record = result.scalar_one_or_none()
        if not file_record:
            return JSONResponse(status_code=403, content={"detail": "Document not found in this project"})
        file_record_id = file_record.id

    request.state.document_id = document_id
    resp = await proxy_request(method="DELETE", url=f"{RAG_URL}/documents/{document_id}", user_id=user_id)

    if resp.status_code == 200 and file_record_id:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(UploadedFile).where(UploadedFile.id == file_record_id)
                )
                record = result.scalar_one_or_none()
                if record:
                    await session.delete(record)

    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
