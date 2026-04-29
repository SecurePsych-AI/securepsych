import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    ConversationThread,
    JargonRun,
    Message,
    Project,
    SummaryRun,
    UploadedFile,
    User,
)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def get_or_create_user(session: AsyncSession, user_id: str, role: str) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=user_id, username=user_id, role=role)
        session.add(user)
        await session.flush()
    return user


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

async def create_project(
    session: AsyncSession,
    owner_id: str,
    student_id_hash: str,
    display_label: str | None,
) -> Project:
    project = Project(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        student_id_hash=student_id_hash,
        display_label=display_label,
    )
    session.add(project)
    await session.flush()
    return project


async def get_project_by_id(
    session: AsyncSession, project_id: str, owner_id: str
) -> Project | None:
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
    )
    return result.scalar_one_or_none()


async def list_projects(
    session: AsyncSession, owner_id: str, skip: int = 0, limit: int = 100
) -> list[Project]:
    result = await session.execute(
        select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Uploaded files
# ---------------------------------------------------------------------------

async def log_file_upload(
    session: AsyncSession,
    project_id: str,
    document_id: str,
    filename_redacted: str,
    strategy: str,
    chunks_added: int,
) -> UploadedFile:
    record = UploadedFile(
        project_id=project_id,
        document_id=document_id,
        filename_redacted=filename_redacted,
        strategy=strategy,
        chunks_added=chunks_added,
    )
    session.add(record)
    await session.flush()
    return record


async def list_uploaded_files(
    session: AsyncSession, project_id: str, skip: int = 0, limit: int = 100
) -> list[UploadedFile]:
    result = await session.execute(
        select(UploadedFile)
        .where(UploadedFile.project_id == project_id)
        .order_by(UploadedFile.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Conversation threads
# ---------------------------------------------------------------------------

async def get_or_create_thread(
    session: AsyncSession,
    project_id: str,
    thread_id: str | None = None,
) -> ConversationThread:
    if thread_id:
        result = await session.execute(
            select(ConversationThread).where(
                ConversationThread.id == thread_id,
                ConversationThread.project_id == project_id,
            )
        )
        thread = result.scalar_one_or_none()
        if thread:
            return thread
    thread = ConversationThread(project_id=project_id)
    session.add(thread)
    await session.flush()
    return thread


async def list_threads(
    session: AsyncSession, project_id: str, skip: int = 0, limit: int = 100
) -> list[ConversationThread]:
    result = await session.execute(
        select(ConversationThread)
        .where(ConversationThread.project_id == project_id)
        .order_by(ConversationThread.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_thread_with_messages(
    session: AsyncSession, thread_id: str, project_id: str
) -> ConversationThread | None:
    result = await session.execute(
        select(ConversationThread)
        .where(
            ConversationThread.id == thread_id,
            ConversationThread.project_id == project_id,
        )
        .options(selectinload(ConversationThread.messages))
    )
    return result.scalar_one_or_none()


async def add_message(
    session: AsyncSession,
    thread_id: str,
    role: str,
    content: str,
    sources: list[Any] | None = None,
) -> Message:
    message = Message(
        thread_id=thread_id,
        role=role,
        content=content,
        sources_json=json.dumps(sources or []),
    )
    session.add(message)
    await session.flush()
    return message


# ---------------------------------------------------------------------------
# Summary runs
# ---------------------------------------------------------------------------

async def log_summary_run(
    session: AsyncSession,
    project_id: str,
    document_id: str | None,
    filename_redacted: str | None,
    summary: str,
    page_count: int,
) -> SummaryRun:
    record = SummaryRun(
        project_id=project_id,
        document_id=document_id,
        filename_redacted=filename_redacted,
        summary=summary,
        page_count=page_count,
    )
    session.add(record)
    await session.flush()
    return record


async def list_summary_runs(
    session: AsyncSession, project_id: str, skip: int = 0, limit: int = 100
) -> list[SummaryRun]:
    result = await session.execute(
        select(SummaryRun)
        .where(SummaryRun.project_id == project_id)
        .order_by(SummaryRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Jargon runs
# ---------------------------------------------------------------------------

async def log_jargon_run(
    session: AsyncSession,
    project_id: str,
    level: int,
    input_preview: str,
    simplified_text: str,
    fk_grade: float,
) -> JargonRun:
    record = JargonRun(
        project_id=project_id,
        level=level,
        input_preview=input_preview[:200],
        simplified_text=simplified_text,
        fk_grade=fk_grade,
    )
    session.add(record)
    await session.flush()
    return record


async def list_jargon_runs(
    session: AsyncSession, project_id: str, skip: int = 0, limit: int = 100
) -> list[JargonRun]:
    result = await session.execute(
        select(JargonRun)
        .where(JargonRun.project_id == project_id)
        .order_by(JargonRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
