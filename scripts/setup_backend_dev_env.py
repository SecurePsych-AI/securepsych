"""Generate dev-only .env files for each backend service.

Idempotent: if a .env exists, the script preserves it and prints a notice.
All paths target SECUREPSYCH_ENV=test so the production LUKS-mount checks
(/mnt/securepsych/) are bypassed for local dev.

Run once: python scripts/setup_backend_dev_env.py
"""
from __future__ import annotations

import secrets
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"

DEV_GATEWAY_USERNAME = "dr.lee"
DEV_GATEWAY_PASSWORD = "demo-pass-2026"

# Cross-platform writable scratch dir for dev artifacts (entity maps, sqlite, logs).
DEV_DATA_DIR = (REPO_ROOT / "dev_data").as_posix()


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        print(f"  skip (exists): {path.relative_to(REPO_ROOT)}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote: {path.relative_to(REPO_ROOT)}")
    return True


def gateway_env() -> str:
    jwt_secret = secrets.token_hex(32)
    student_hash_secret = secrets.token_hex(32)
    return (
        f"JWT_SECRET={jwt_secret}\n"
        f"GATEWAY_USERNAME={DEV_GATEWAY_USERNAME}\n"
        f"GATEWAY_PASSWORD={DEV_GATEWAY_PASSWORD}\n"
        "CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000\n"
        f"GATEWAY_DB_PATH={DEV_DATA_DIR}/gateway/gateway.db\n"
        f"STUDENT_HASH_SECRET={student_hash_secret}\n"
        f"GATEWAY_LOG_DIR={DEV_DATA_DIR}/gateway/logs\n"
        "GATEWAY_LOG_RETENTION_DAYS=30\n"
        "SECUREPSYCH_ENV=test\n"
    )


def rag_env() -> str:
    # Cryptography-style Fernet key (urlsafe-b64 32 bytes).
    import base64
    fernet_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
    return (
        "OLLAMA_BASE_URL=http://localhost:11434\n"
        "OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M\n"
        f"CHROMA_PATH={DEV_DATA_DIR}/chroma\n"
        "CHROMA_COLLECTION=securepsych\n"
        "CHUNK_SIZE=512\n"
        "CHUNK_OVERLAP=64\n"
        f"ENCRYPTED_ENTITY_MAP_PATH={DEV_DATA_DIR}/entity_maps\n"
        f"ENTITY_MAP_FERNET_KEY={fernet_key}\n"
        "LANGCHAIN_TRACING_V2=false\n"
        "LANGCHAIN_API_KEY=\n"
        "LANGCHAIN_PROJECT=securepsych-rag\n"
        "SECUREPSYCH_ENV=test\n"
    )


def summarizer_env() -> str:
    return (
        "OLLAMA_BASE_URL=http://localhost:11434\n"
        "OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M\n"
        "LANGCHAIN_TRACING_V2=false\n"
        "SECUREPSYCH_ENV=test\n"
    )


def jargon_env() -> str:
    return (
        "OLLAMA_BASE_URL=http://localhost:11434\n"
        "OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M\n"
        "LANGCHAIN_TRACING_V2=false\n"
        "SECUREPSYCH_ENV=test\n"
    )


def main() -> None:
    print(f"Generating dev .env files (data dir: {DEV_DATA_DIR})")
    print()

    writers = [
        (BACKEND / "gateway" / ".env", gateway_env),
        (BACKEND / "rag" / ".env", rag_env),
        (BACKEND / "summarizer" / ".env", summarizer_env),
        (BACKEND / "jargon" / ".env", jargon_env),
    ]
    written_any = False
    for path, factory in writers:
        if write_if_missing(path, factory()):
            written_any = True

    # Pre-create writable scratch dirs so first request doesn't 500.
    Path(DEV_DATA_DIR, "gateway", "logs").mkdir(parents=True, exist_ok=True)
    Path(DEV_DATA_DIR, "chroma").mkdir(parents=True, exist_ok=True)
    Path(DEV_DATA_DIR, "entity_maps").mkdir(parents=True, exist_ok=True)
    print(f"  ensured: dev_data/ subdirs")

    print()
    if written_any:
        print(f"Done. Login: {DEV_GATEWAY_USERNAME} / {DEV_GATEWAY_PASSWORD}")
    else:
        print("All .env files already existed — left as-is.")
    print("dev_data/ is gitignored. Do not commit it.")


if __name__ == "__main__":
    main()
