import logging

import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def load_pdf_from_bytes(
    pdf_bytes: bytes,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> tuple[list[Document], int]:
    """
    Extract text from a PDF (in-memory, no disk write) and return LangChain
    Documents split into chunks, plus the raw page count.

    Each page is extracted first so that page-number metadata is preserved
    in every chunk — citations can reference back to the source page.

    Args:
        pdf_bytes:     Raw PDF bytes from the upload.
        chunk_size:    Max characters per chunk. Revisit after Research 1 & 2.
        chunk_overlap: Overlap between chunks to preserve sentence continuity.

    Returns:
        (docs, page_count) where docs is the list of chunked Documents and
        page_count is the total number of pages in the PDF.
    """
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(pdf)
    logger.info("[pdf_loader] PDF opened — pages: %d | chunk_size: %d | chunk_overlap: %d",
                page_count, chunk_size, chunk_overlap)

    page_docs: list[Document] = []
    for page_num, page in enumerate(pdf, start=1):
        text = page.get_text().strip()
        if text:
            page_docs.append(
                Document(
                    page_content=text,
                    metadata={"page": page_num, "source": "uploaded_pdf"},
                )
            )
    pdf.close()
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
