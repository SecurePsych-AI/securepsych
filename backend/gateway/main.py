import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from db import create_all_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SecurePsych API Gateway",
        description="FERPA-compliant API gateway routing to core deterministic microservices.",
        version="1.0.0",
        lifespan=lifespan,
    )

    _raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS")
    if not _raw_origins:
        raise RuntimeError("CORS_ALLOWED_ORIGINS is required. Set it in .env (e.g. http://localhost:5173).")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _raw_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from middleware.logging import AccessLoggingMiddleware
    from auth.middleware import JWTAuthMiddleware
    app.add_middleware(JWTAuthMiddleware)
    app.add_middleware(AccessLoggingMiddleware)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "gateway"}

    @app.get("/api/config")
    async def get_config():
        """Returns non-sensitive feature flags to the frontend."""
        return settings.features.model_dump()

    # Routers
    from auth.routes import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

    from proxy.rag import router as rag_router
    app.include_router(rag_router, prefix="/api/rag", tags=["rag"])

    from proxy.summarizer import router as summarizer_router
    app.include_router(summarizer_router, prefix="/api/summarize", tags=["summarizer"])

    from proxy.jargon import router as jargon_router
    app.include_router(jargon_router, prefix="/api/jargon", tags=["jargon"])

    from routes.projects import router as projects_router
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])

    return app

app = create_app()
