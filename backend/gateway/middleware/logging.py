import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import settings

# Setup logger directed to the encrypted log_dir
LOG_DIR = Path(settings.storage.log_dir)

logger = logging.getLogger("gateway.access")
logger.setLevel(logging.INFO)

try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "access.log"
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE)
        logger.addHandler(file_handler)
except OSError as e:
    # Graceful degradation for local testing where /mnt is typically read-only
    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        logger.addHandler(stream_handler)
        logger.warning(f"Could not secure access log mount at {LOG_DIR}: {e}. Defaulting back to stream.")

class AccessLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            user_id = getattr(request.state, "user_id", "unauthenticated")
            
            # Simple heuristic for document_id from path (e.g., /api/rag/documents/{id}/content)
            document_id = getattr(request.state, "document_id", None)
            if not document_id:
                parts = request.url.path.split("/")
                if "documents" in parts:
                    idx = parts.index("documents")
                    if len(parts) > idx + 1:
                        # Extract next part if it isn't empty
                        potential_id = parts[idx + 1]
                        if potential_id and potential_id != "content":
                            document_id = potential_id

            log_entry = {
                "timestamp": timestamp,
                "user_id": user_id,
                "endpoint": f"{request.method} {request.url.path}",
                "response_status": status_code
            }
            if document_id:
                log_entry["document_id"] = document_id
                
            logger.info(json.dumps(log_entry))
            
        return response
