from fastapi import APIRouter, Request, Response, HTTPException
from proxy.client import proxy_request
from config import settings
import sys
import os

try:
    from shared.extraction import extract_pdf
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from shared.extraction import extract_pdf

router = APIRouter()

JARGON_URL = settings.services.jargon_url
RAG_URL = settings.services.rag_url

@router.post("/simplify")
async def simplify_jargon(request: Request):
    # FERPA: currently bypassing due to pending domain constraints
    raise HTTPException(status_code=503, detail="Jargon service pending Phase 2 deployment")
    
    user_id = getattr(request.state, "user_id", "unauthenticated")
    content_type = request.headers.get("content-type", "")
    
    extracted_text = ""
    level = "parent" # default level
    
    if "application/json" in content_type:
        body = await request.json()
        level = body.get("level", "parent")
        
        if "text" in body:
            # Mode A
            extracted_text = body["text"]
        elif "document_id" in body:
            # Mode C
            document_id = body["document_id"]
            request.state.document_id = document_id
            
            rag_resp = await proxy_request("GET", f"{RAG_URL}/documents/{document_id}/content", user_id=user_id)
            if rag_resp.status_code != 200:
                raise HTTPException(status_code=rag_resp.status_code, detail="Failed to retrieve document from RAG service")
                
            rag_data = rag_resp.json()
            extracted_text = rag_data.get("text", "")
        else:
            raise HTTPException(status_code=400, detail="Must provide 'text' or 'document_id' in JSON")
            
    elif "multipart/form-data" in content_type:
        # Mode B
        form = await request.form()
        file = form.get("file")
        level_override = form.get("level")
        if level_override:
            level = level_override
            
        if not file:
            raise HTTPException(status_code=400, detail="Missing 'file' field")
            
        file_bytes = await file.read()
        
        # We need an ollama hook here. Since it's stubbed out, we'd pull from settings
        # ollama_url = "http://localhost:11434"
        # Since this is behind a 503, doing basic structure is enough
        result = await extract_pdf(file_bytes, file.filename, "http://localhost:11434")
        extracted_text = result.full_text
        
    else:
        raise HTTPException(status_code=415, detail="Unsupported Content-Type")
        
    # Forward the normalized text mapping
    payload = {
        "text": extracted_text,
        "level": level
    }
    
    resp = await proxy_request("POST", f"{JARGON_URL}/simplify", user_id=user_id, json=payload)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
