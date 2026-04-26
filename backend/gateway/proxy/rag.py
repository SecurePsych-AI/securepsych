from fastapi import APIRouter, Request, UploadFile, File, Response
from fastapi.responses import JSONResponse
from proxy.client import proxy_request
from config import settings

router = APIRouter()
RAG_URL = settings.services.rag_url

@router.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    file_bytes = await file.read()
    files = {"file": (file.filename, file_bytes, file.content_type)}
    
    resp = await proxy_request(
        method="POST",
        url=f"{RAG_URL}/upload",
        user_id=user_id,
        files=files
    )
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))

@router.post("/query")
async def query_document(request: Request):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    body = await request.json()
    
    # If the user targets a specific document, mark the request state for our access logger
    if "document_id" in body:
        request.state.document_id = body["document_id"]
        
    resp = await proxy_request(
        method="POST",
        url=f"{RAG_URL}/query",
        user_id=user_id,
        json=body
    )
    
    if resp.status_code == 200:
        data = resp.json()
        if "chunks" in data:
            del data["chunks"] # FERPA sanitization requirement
        return JSONResponse(content=data)
    
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))

@router.get("/documents")
async def list_documents(request: Request):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    resp = await proxy_request(method="GET", url=f"{RAG_URL}/documents", user_id=user_id)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))

@router.get("/documents/{document_id}/content")
async def get_document_content(request: Request, document_id: str):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    request.state.document_id = document_id
    resp = await proxy_request(method="GET", url=f"{RAG_URL}/documents/{document_id}/content", user_id=user_id)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))

@router.delete("/documents/{document_id}")
async def delete_document(request: Request, document_id: str):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    request.state.document_id = document_id
    resp = await proxy_request(method="DELETE", url=f"{RAG_URL}/documents/{document_id}", user_id=user_id)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
