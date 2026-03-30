import chromadb
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from rag_query import answer_question
from ingestion import ingest_pdf_bytes


app = FastAPI(title="RAG API", version="1.0")

chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(name="documents")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    document_id: str | None = None
    top_k: int = 2


# ---------------------------------------------------------------------------
# POST /upload
# Upload and ingest a PDF file into ChromaDB.
#
# Usage:
#   curl -X POST http://localhost:8000/upload \
#        -F "file=@sample_psycheval.pdf"
# ---------------------------------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = ingest_pdf_bytes(file_bytes, file.filename)

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


# ---------------------------------------------------------------------------
# GET /documents
# List all documents currently stored in ChromaDB.
#
# Usage:
#   curl http://localhost:8000/documents
# ---------------------------------------------------------------------------

@app.get("/documents")
def list_documents():
    results = collection.get(include=["metadatas"])
    metadatas = results.get("metadatas", [])

    # Deduplicate by document_id — one entry per document, not per chunk
    seen = {}
    for meta in metadatas:
        doc_id = meta.get("document_id")
        if doc_id and doc_id not in seen:
            seen[doc_id] = {
                "document_id": doc_id,
                "filename": meta.get("filename", "Unknown"),
            }

    documents = list(seen.values())

    return {
        "total_documents": len(documents),
        "documents": documents,
    }


# ---------------------------------------------------------------------------
# DELETE /documents/{document_id}
# Remove all chunks belonging to a document from ChromaDB.
#
# Usage:
#   curl -X DELETE http://localhost:8000/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6
# ---------------------------------------------------------------------------

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    # Find all chunk IDs that belong to this document
    results = collection.get(
        where={"document_id": document_id},
        include=["metadatas"],
    )

    ids_to_delete = results.get("ids", [])

    if not ids_to_delete:
        raise HTTPException(
            status_code=404,
            detail=f"No document found with ID: {document_id}"
        )

    filename = results["metadatas"][0].get("filename", "Unknown") if results.get("metadatas") else "Unknown"
    chunks_removed = len(ids_to_delete)

    collection.delete(ids=ids_to_delete)

    return {
        "deleted": True,
        "document_id": document_id,
        "filename": filename,
        "chunks_removed": chunks_removed,
    }


# ---------------------------------------------------------------------------
# POST /query
# Ask a question against an ingested document (or all documents).
#
# Usage:
#   curl -X POST http://localhost:8000/query \
#        -H "Content-Type: application/json" \
#        -d '{"question": "What medications were prescribed?", "document_id": "..."}'
# ---------------------------------------------------------------------------

@app.post("/query")
def query_document(request: QueryRequest):
    result = answer_question(
        question=request.question,
        top_k=request.top_k,
        document_id=request.document_id,
    )
    return result