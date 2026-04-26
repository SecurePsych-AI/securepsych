from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from config import settings
from .backends.base import BaseAuthBackend
from .backends.local_jwt import LocalJWTBackend
from .backends.school_directory import SchoolDirectoryBackend

EXEMPT_PATHS = {"/health", "/api/config", "/api/auth/login"}
ALLOWED_ROLES = {"psychologist", "admin"}

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.backend: BaseAuthBackend = self._init_backend()

    def _init_backend(self) -> BaseAuthBackend:
        if settings.auth.backend == "local_jwt":
            return LocalJWTBackend()
        elif settings.auth.backend == "school_directory":
            return SchoolDirectoryBackend()
        else:
            raise ValueError(f"Unknown auth backend: {settings.auth.backend}")
            
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})
            
        token = auth_header.split(" ")[1]
        
        from .store import token_denylist
        if token in token_denylist:
            return JSONResponse(status_code=401, content={"detail": "Token revoked"})
        
        try:
            payload = self.backend.verify_token(token)
        except Exception:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        role = payload.get("role")
        if role not in ALLOWED_ROLES:
            return JSONResponse(status_code=403, content={"detail": "Insufficient permissions"})

        request.state.user_id = payload.get("sub")
        request.state.role = role
        return await call_next(request)
