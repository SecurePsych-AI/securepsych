from fastapi import APIRouter, Request, Response, HTTPException
from proxy.client import proxy_request
from config import settings

router = APIRouter()

SUMMARIZER_URL = settings.services.summarizer_url
RAG_URL = settings.services.rag_url

@router.post("")
@router.post("/")
async def summarize(request: Request):
    user_id = getattr(request.state, "user_id", "unauthenticated")
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # Mode B: Look up document from RAG service orchestrator
        body = await request.json()
        document_id = body.get("document_id")
        if not document_id:
            raise HTTPException(status_code=400, detail="Missing document_id in JSON body")
            
        request.state.document_id = document_id
            
        # Call RAG GET content endpoint
        rag_resp = await proxy_request("GET", f"{RAG_URL}/documents/{document_id}/content", user_id=user_id)
        if rag_resp.status_code != 200:
            return Response(content=rag_resp.content, status_code=rag_resp.status_code, media_type=rag_resp.headers.get("content-type"))
            
        rag_data = rag_resp.json()
        doc_text = rag_data.get("text", "")
        
        # Post text bytes to Summarizer
        file_bytes = doc_text.encode('utf-8')
        files = {"file": (f"{document_id}.txt", file_bytes, "text/plain")}
        
        sum_resp = await proxy_request("POST", f"{SUMMARIZER_URL}/summarize", user_id=user_id, files=files)
        return Response(content=sum_resp.content, status_code=sum_resp.status_code, media_type=sum_resp.headers.get("content-type"))
        
    elif "multipart/form-data" in content_type:
        # Mode A: Direct file upload
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Missing 'file' form data")
            
        file_bytes = await file.read()
        files = {"file": (file.filename, file_bytes, file.content_type)}
        
        sum_resp = await proxy_request("POST", f"{SUMMARIZER_URL}/summarize", user_id=user_id, files=files)
        return Response(content=sum_resp.content, status_code=sum_resp.status_code, media_type=sum_resp.headers.get("content-type"))
        
    else:
        raise HTTPException(status_code=415, detail="Unsupported Content-Type. Expected application/json or multipart/form-data")
