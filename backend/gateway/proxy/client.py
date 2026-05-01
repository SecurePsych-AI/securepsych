import httpx
from typing import Dict, Any

# Connection pool maintained globally for proxy instances
shared_client = httpx.AsyncClient(timeout=60.0)

async def proxy_request(
    method: str,
    url: str,
    user_id: str,
    student_id_hash: str | None = None,
    **kwargs,
) -> httpx.Response:
    """
    Execute an HTTP request, forwarding user and student-namespace context headers.
    student_id_hash is the gateway-resolved BLAKE2b hash — never the raw student ID.
    """
    headers = kwargs.pop("headers", {})

    if user_id:
        headers["X-User-ID"] = user_id
    if student_id_hash:
        headers["X-Student-ID-Hash"] = student_id_hash

    return await shared_client.request(method, url, headers=headers, **kwargs)
