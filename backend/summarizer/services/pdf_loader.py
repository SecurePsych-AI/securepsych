import logging
import asyncio
import os

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.shared.extraction import extract_pdf

logger = logging.getLogger(__name__)


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def load_pdf_from_bytes(
    pdf_bytes: bytes,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> tuple[list[Document], int]:
    """
    Extract text from a PDF and return LangChain Documents split into chunks.
    Uses shared extraction logic with Ollama vision fallback.
    """
    logger.info("[pdf_loader] Processing PDF with chunk_size: %d | chunk_overlap: %d",
                chunk_size, chunk_overlap)

    extraction_result = asyncio.run(extract_pdf(pdf_bytes, "uploaded_pdf", OLLAMA_URL))
    page_count = extraction_result.page_count
    
    page_docs: list[Document] = []
    for page_obj in extraction_result.pages:
        if page_obj.text:
            page_docs.append(
                Document(
                    page_content=page_obj.text,
                    metadata={"page": page_obj.page_num, "source": "uploaded_pdf"},
                )
            )

    logger.info("[pdf_loader] Text extracted — pages with content: %d/%d",
                len(page_docs), page_count)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    docs = splitter.split_documents(page_docs)
    logger.info(
        "[pdf_loader] Splitting complete — total chunks: %d", len(docs))
    return docs, page_count
