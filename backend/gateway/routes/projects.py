import json
import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, field_validator

from db import AsyncSessionLocal, crud
from hashing import hash_student_id

router = APIRouter()

# ---------------------------------------------------------------------------
# PII guard patterns for display_label
# ---------------------------------------------------------------------------
_PII_PATTERNS = [
    re.compile(r"\d{3}[-\s]\d{2}[-\s]\d{4}"),         # SSN: 123-45-6789
    re.compile(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b"),  # DOB: 1/15/2012 or 01-15-12
    re.compile(r"\b\d{6,}\b"),                          # Long digit string (district ID)
]


def _has_pii(text: str) -> bool:
    return any(p.search(text) for p in _PII_PATTERNS)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CreateProjectRequest(BaseModel):
    student_id: str
    display_label: str | None = None

    @field_validator("display_label")
    @classmethod
    def reject_pii_in_label(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if len(v) > 80:
            raise ValueError("display_label must be 80 characters or fewer")
        if _has_pii(v):
            raise ValueError(
                "display_label must not contain PII patterns (SSN, DOB, or district ID). "
                "Use a case code such as 'Case 2024-031' instead."
            )
        return v


class ProjectResponse(BaseModel):
    id: str
    display_label: str | None
    created_at: datetime


class UploadedFileResponse(BaseModel):
    id: str
    document_id: str
    filename_redacted: str
    strategy: str
    chunks_added: int
    uploaded_at: datetime


class ThreadSummaryResponse(BaseModel):
    id: str
    title: str | None
    created_at: datetime


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: list[Any]
    created_at: datetime


class ThreadWithMessagesResponse(BaseModel):
    id: str
    title: str | None
    created_at: datetime
    messages: list[MessageResponse]


class SummaryRunResponse(BaseModel):
    id: str
    document_id: str | None
    filename_redacted: str | None
    summary: str
    page_count: int
    created_at: datetime


class JargonRunResponse(BaseModel):
    id: str
    level: int
    input_preview: str
    simplified_text: str
    fk_grade: float
    created_at: datetime


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _require_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", status_code=201, response_model=ProjectResponse)
async def create_project(body: CreateProjectRequest, request: Request):
    user_id = _require_user(request)
    role = getattr(request.state, "role", "psychologist")
    h = hash_student_id(body.student_id)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await crud.get_or_create_user(session, user_id, role)
            project = await crud.create_project(session, user_id, h, body.display_label)
    return ProjectResponse(
        id=project.id,
        display_label=project.display_label,
        created_at=project.created_at,
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    user_id = _require_user(request)
    async with AsyncSessionLocal() as session:
        projects = await crud.list_projects(session, user_id, skip=skip, limit=limit)
    return [
        ProjectResponse(id=p.id, display_label=p.display_label, created_at=p.created_at)
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, request: Request):
    user_id = _require_user(request)
    async with AsyncSessionLocal() as session:
        project = await crud.get_project_by_id(session, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(id=project.id, display_label=project.display_label, created_at=project.created_at)


@router.get("/{project_id}/files", response_model=list[UploadedFileResponse])
async def list_files(
    project_id: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    user_id = _require_user(request)
    async with AsyncSessionLocal() as session:
        project = await crud.get_project_by_id(session, project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        files = await crud.list_uploaded_files(session, project_id, skip=skip, limit=limit)
    return [
        UploadedFileResponse(
            id=f.id,
            document_id=f.document_id,
            filename_redacted=f.filename_redacted,
            strategy=f.strategy,
            chunks_added=f.chunks_added,
            uploaded_at=f.uploaded_at,
        )
        for f in files
    ]


@router.get("/{project_id}/threads", response_model=list[ThreadSummaryResponse])
async def list_threads(
    project_id: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    user_id = _require_user(request)
    async with AsyncSessionLocal() as session:
        project = await crud.get_project_by_id(session, project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        threads = await crud.list_threads(session, project_id, skip=skip, limit=limit)
    return [
        ThreadSummaryResponse(id=t.id, title=t.title, created_at=t.created_at)
        for t in threads
    ]


@router.get("/{project_id}/threads/{thread_id}", response_model=ThreadWithMessagesResponse)
async def get_thread(project_id: str, thread_id: str, request: Request):
    user_id = _require_user(request)
    async with AsyncSessionLocal() as session:
        project = await crud.get_project_by_id(session, project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        thread = await crud.get_thread_with_messages(session, thread_id, project_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadWithMessagesResponse(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=json.loads(m.sources_json),
                created_at=m.created_at,
            )
            for m in thread.messages
        ],
    )


@router.get("/{project_id}/summaries", response_model=list[SummaryRunResponse])
async def list_summaries(
    project_id: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    user_id = _require_user(request)
    async with AsyncSessionLocal() as session:
        project = await crud.get_project_by_id(session, project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        runs = await crud.list_summary_runs(session, project_id, skip=skip, limit=limit)
    return [
        SummaryRunResponse(
            id=r.id,
            document_id=r.document_id,
            filename_redacted=r.filename_redacted,
            summary=r.summary,
            page_count=r.page_count,
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/{project_id}/jargon-runs", response_model=list[JargonRunResponse])
async def list_jargon_runs(
    project_id: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    user_id = _require_user(request)
    async with AsyncSessionLocal() as session:
        project = await crud.get_project_by_id(session, project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        runs = await crud.list_jargon_runs(session, project_id, skip=skip, limit=limit)
    return [
        JargonRunResponse(
            id=r.id,
            level=r.level,
            input_preview=r.input_preview,
            simplified_text=r.simplified_text,
            fk_grade=r.fk_grade,
            created_at=r.created_at,
        )
        for r in runs
    ]
