from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title="SecurePsych API Gateway",
        description="FERPA-compliant API gateway routing to core deterministic microservices.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
    
    from proxy.visualizer import router as visualizer_router
    app.include_router(visualizer_router, prefix="/api/visualizer", tags=["visualizer"])
    
    from proxy.tasks import router as tasks_router
    app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])

    return app

app = create_app()
