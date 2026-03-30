import chromadb
import requests


# Connect to the same Chroma database Noble used
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(name="documents")


def get_available_documents():
    """Return a dictionary of {document_id: filename} from stored metadata."""
    results = collection.get(include=["metadatas"])

    documents = {}
    for metadata in results.get("metadatas", []):
        document_id = metadata.get("document_id")
        filename = metadata.get("filename", "Unknown file")

        if document_id and document_id not in documents:
            documents[document_id] = filename

    return documents


def choose_document():
    """Let the user choose a document from available ingested PDFs."""
    documents = get_available_documents()

    if not documents:
        print("No documents found in ChromaDB.")
        return None

    print("\nAvailable documents:")
    doc_ids = list(documents.keys())

    for i, doc_id in enumerate(doc_ids, start=1):
        print(f"{i}. {documents[doc_id]} ({doc_id})")

    choice = input("\nChoose a document number, or press Enter to search all: ").strip()

    if not choice:
        return None

    if choice.isdigit():
        choice_num = int(choice)
        if 1 <= choice_num <= len(doc_ids):
            return doc_ids[choice_num - 1]

    print("Invalid choice. Searching all documents instead.")
    return None


def retrieve_chunks(question: str, top_k: int = 2, document_id: str | None = None):
    """Retrieve the most relevant chunks from ChromaDB."""
    where_filter = {"document_id": document_id} if document_id else None

    print("\nRetrieving chunks from ChromaDB...")
    results = collection.query(
        query_texts=[question],
        n_results=top_k,
        where=where_filter
    )

    print("\nRAW RETRIEVAL RESULTS:")
    print(results)

    return results


def deduplicate_citations(citations):
    """Remove duplicate filename + page-range citation pairs."""
    seen = set()
    unique = []

    for citation in citations:
        key = (citation["filename"], citation["page_start"], citation["page_end"])
        if key not in seen:
            seen.add(key)
            unique.append(citation)

    return unique


def format_context(results):
    """Turn retrieved documents into prompt context and citation list."""
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        return "", []

    context_parts = []
    citations = []

    for doc, meta in zip(documents, metadatas):
        filename = meta.get("filename", "Unknown file")
        page_start = meta.get("page_start", "?")
        page_end = meta.get("page_end", "?")

        if page_start == page_end:
            page_label = f"page {page_start}"
        else:
            page_label = f"pages {page_start}-{page_end}"

        context_parts.append(f"[Source: {filename}, {page_label}]\n{doc}")
        citations.append({"filename": filename, "page_start": page_start, "page_end": page_end})

    context = "\n\n".join(context_parts)
    return context, deduplicate_citations(citations)


def build_prompt(question: str, context: str):
    """Build a grounded prompt for the LLM."""
    return f"""You are a helpful assistant answering questions about a PDF.

Use only the context below to answer the question.
If the answer is not in the context, say: "I could not find that in the document."

Answer clearly and briefly.
Do NOT invent page numbers.
Only use page numbers explicitly shown in the context headers like:
[Source: filename, page X]

Context:
{context}

Question:
{question}
"""


def generate_answer(prompt: str, model: str = "llama3.2:1b"):
    """Send the prompt to Ollama and return the generated answer."""
    print("\nSending prompt to Ollama...")

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 256,
                    "temperature": 0.2
                }
            },
            timeout=300
        )

        response.raise_for_status()
        data = response.json()

        print("Received response from Ollama.\n")
        return data.get("response", "No response generated.")

    except requests.exceptions.Timeout:
        return "Error: Ollama request timed out. Try again."

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Make sure Ollama is running."

    except Exception as e:
        return f"Unexpected error from Ollama: {e}"


def answer_question(question: str, top_k: int = 2, document_id: str | None = None):
    """Run the full RAG pipeline."""
    results = retrieve_chunks(question, top_k=top_k, document_id=document_id)
    context, citations = format_context(results)

    if not context:
        return {
            "answer": "I could not find that in the document.",
            "citations": []
        }

    print("\nCONTEXT SENT TO MODEL:\n")
    print(context)

    prompt = build_prompt(question, context)
    answer = generate_answer(prompt)

    return {
        "answer": answer,
        "citations": citations
    }


if __name__ == "__main__":
    print("Connected to ChromaDB.")
    print("Collection count:", collection.count())

    selected_document_id = choose_document()
    question = input("\nEnter your question: ").strip()

    result = answer_question(question, top_k=2, document_id=selected_document_id)

    print("\nAnswer:\n")
    print(result["answer"])

    print("\nCitations:")
    if result["citations"]:
        for c in result["citations"]:
            ps, pe = c["page_start"], c["page_end"]
            page_label = f"page {ps}" if ps == pe else f"pages {ps}-{pe}"
            print(f"- {c['filename']}, {page_label}")
    else:
        print("No citations found.")