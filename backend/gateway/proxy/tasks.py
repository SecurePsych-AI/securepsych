from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all_tasks(request: Request, path_name: str):
    raise HTTPException(status_code=501, detail="Phase 4 — not yet implemented")
