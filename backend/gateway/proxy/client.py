import httpx
from typing import Dict, Any

# Connection pool maintained globally for proxy instances
shared_client = httpx.AsyncClient(timeout=60.0)

async def proxy_request(method: str, url: str, user_id: str, **kwargs) -> httpx.Response:
    """
    Executes an HTTP request forwarding the X-User-ID mapping the token payload.
    """
    headers = kwargs.pop("headers", {})
    
    # Inject FERPA-compliant user metadata
    if user_id:
        headers["X-User-ID"] = user_id
        
    return await shared_client.request(method, url, headers=headers, **kwargs)
