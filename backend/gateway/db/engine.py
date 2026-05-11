import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

from .models import Base


_ENCRYPTED_PREFIXES = (
    "/mnt/securepsych/",       # Linux production (LUKS)
    "/Volumes/securepsych/",   # macOS dev (encrypted disk image)
)


def _get_db_path() -> str:
    path = os.environ.get("GATEWAY_DB_PATH")
    if not path:
        raise RuntimeError("GATEWAY_DB_PATH must be set in environment — no fallback permitted.")
    # LUKS boundary check is skipped only in an explicitly declared test environment.
    # SECUREPSYCH_ENV=test must be set in test conftest; it must never appear in production config.
    if os.environ.get("SECUREPSYCH_ENV") != "test" and not any(
        path.startswith(p) for p in _ENCRYPTED_PREFIXES
    ):
        raise RuntimeError(
            f"FERPA Violation: GATEWAY_DB_PATH must be under /mnt/securepsych/ (Linux) or "
            f"/Volumes/securepsych/ (macOS dev) — got '{path}'. "
            "Database must reside on an encrypted mount."
        )
    return path


_DB_PATH = _get_db_path()

engine = create_async_engine(
    f"sqlite+aiosqlite:///{_DB_PATH}",
    connect_args={"timeout": 30},
    echo=False,
)


@event.listens_for(engine.sync_engine, "connect")
def _configure_sqlite(dbapi_conn, _connection_record):
    # WAL mode: concurrent reads alongside one writer; reduces lock contention significantly
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    # NORMAL is safe with WAL and avoids a full fsync on every commit
    dbapi_conn.execute("PRAGMA synchronous=NORMAL")
    # Wait up to 30 s for a lock to release before raising OperationalError
    dbapi_conn.execute("PRAGMA busy_timeout=30000")


AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def create_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
