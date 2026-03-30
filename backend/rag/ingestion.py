import sys
import uuid
import fitz
import chromadb


chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(name="documents")


# --- Config ---

CHUNK_SIZE = 600      # target tokens per chunk (within the 512-800 recommended range)
OVERLAP = 0.20        # 20% overlap between consecutive chunks


# --- Helpers ---

def approximate_tokens(text: str) -> int:
    """Rough token count: ~4 characters per token (good enough without a full tokenizer)."""
    return len(text) // 4


def extract_pages(file_bytes: bytes) -> list[dict]:
    """Extract text from each PDF page, returning page number alongside the text."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append({"page": page_num, "text": text})
    doc.close()
    return pages


def build_token_chunks(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: float = OVERLAP) -> list[dict]:
    """
    Split the full document text into overlapping token-sized chunks.

    Strategy:
    - Concatenate all page text, tracking which characters belong to which page.
    - Split into words (proxy for tokens at ~0.75 words/token).
    - Slide a window of `chunk_size` tokens forward by `chunk_size * (1 - overlap)` each step.
    - Record the page range covered by each chunk for citation metadata.
    """
    # Build a flat word list, keeping track of the source page for each word
    word_list = []       # list of str
    word_pages = []      # parallel list: which page this word came from

    for page in pages:
        words = page["text"].split()
        word_list.extend(words)
        word_pages.extend([page["page"]] * len(words))

    if not word_list:
        return []

    # ~0.75 words per token -> chunk_size tokens ≈ chunk_size * 0.75 words
    words_per_chunk = max(1, int(chunk_size * 0.75))
    step = max(1, int(words_per_chunk * (1 - overlap)))

    chunks = []
    chunk_index = 0
    start = 0

    while start < len(word_list):
        end = min(start + words_per_chunk, len(word_list))

        chunk_words = word_list[start:end]
        chunk_text = " ".join(chunk_words)

        # Page range: first and last page covered by this chunk
        pages_covered = word_pages[start:end]
        page_start = pages_covered[0]
        page_end = pages_covered[-1]

        chunks.append({
            "chunk_index": chunk_index,
            "text": chunk_text,
            "page_start": page_start,
            "page_end": page_end,
            "token_estimate": approximate_tokens(chunk_text),
        })

        chunk_index += 1
        start += step

        # Stop if the remaining words would make a chunk smaller than 10% of target
        # (avoids tiny trailing fragments — fold them into the last chunk instead)
        remaining = len(word_list) - start
        if 0 < remaining < int(words_per_chunk * 0.10):
            last = chunks[-1]
            extra_words = word_list[start:]
            last["text"] += " " + " ".join(extra_words)
            last["page_end"] = word_pages[-1]
            last["token_estimate"] = approximate_tokens(last["text"])
            break

    return chunks


# --- Ingest ---

def ingest_pdf_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Ingest a PDF from raw bytes — used by the FastAPI upload endpoint.
    Returns a summary dict instead of printing, so the API can return it as JSON.
    """
    pages = extract_pages(file_bytes)

    if not pages:
        return {"error": f"No extractable text found in {filename}"}

    chunks = build_token_chunks(pages)

    if not chunks:
        return {"error": f"Could not produce any chunks from {filename}"}

    document_id = str(uuid.uuid4())

    collection.add(
        ids=[f"{document_id}_chunk{chunk['chunk_index']}" for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": chunk["chunk_index"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "token_estimate": chunk["token_estimate"],
            }
            for chunk in chunks
        ],
    )

    avg_tokens = sum(c["token_estimate"] for c in chunks) // len(chunks)

    return {
        "document_id": document_id,
        "filename": filename,
        "chunks_stored": len(chunks),
        "avg_chunk_tokens": avg_tokens,
    }


def ingest_pdf(filepath: str):
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    filename = filepath.split("/")[-1]
    pages = extract_pages(file_bytes)

    if not pages:
        print(f"No extractable text found in {filename}")
        return

    chunks = build_token_chunks(pages)

    if not chunks:
        print(f"Could not produce any chunks from {filename}")
        return

    document_id = str(uuid.uuid4())

    collection.add(
        ids=[f"{document_id}_chunk{chunk['chunk_index']}" for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": chunk["chunk_index"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "token_estimate": chunk["token_estimate"],
            }
            for chunk in chunks
        ],
    )

    avg_tokens = sum(c["token_estimate"] for c in chunks) // len(chunks)

    print(f"Ingestion successful!")
    print(f"  File:            {filename}")
    print(f"  Document ID:     {document_id}")
    print(f"  Chunks stored:   {len(chunks)}")
    print(f"  Avg chunk size:  ~{avg_tokens} tokens")
    print(f"  Chunk size:      {CHUNK_SIZE} tokens  |  Overlap: {int(OVERLAP * 100)}%")


# --- Run ---

if __name__ == "__main__":
    if len(sys.argv) < 2:
        filepath = input("Enter the path to your PDF: ").strip()
    else:
        filepath = sys.argv[1]

    ingest_pdf(filepath)