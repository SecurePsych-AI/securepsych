# SecurePsych RAG Deep Retrieval Update Summary

## 1. Ingestion Pipeline (`ingestion.py`)
- **What we built**: A Python script using `PyMuPDF` to read PDFs and chunk the text.
- **The Magic (`parent_id`)**: The most important change here was adding the `parent_id` to the ChromaDB metadata. We structured it as `"{pagenumber}_{chunk_number}"` (e.g., `"3_2"`). This is what enables the new deep retrieval mode to understand which chunks belong to the exact same page.
- **Endpoints**: We added `ingest_pdf()` for file paths and `ingest_pdf_bytes()` to allow your `api.py` endpoint to directly accept user uploads.

## 2. Core Query Logic (`rag_query.py`)
We refactored the retrieval logic to support two different modes:
- **`retrieve_chunks` (Fast Mode)**: This is standard vector search. It just asks ChromaDB for the top `N` chunks that match the query semantically.
- **`deep_retrieve_chunks` (Deep Mode)**: This works in two steps. First, it runs the standard vector search. Then, it drops the chunk numbers and looks strictly at the `page` numbers from the matched chunks. Finally, it goes back into ChromaDB and pulls **all other chunks** that share those same page numbers. It gives the LLM full section context to read from instead of isolated snippets.
- **Routing Engine (`answer_question`)**: Updated to accept a `"fast"` or `"deep"` mode argument, and routes the request to the correct query logic. It defaults to `"fast"` to not accidentally break any existing parts of the app. It also now points to `llama3.2` as the default model.

## 3. Benchmarking Framework (`test_top_k.py`)
- **What we built**: A standalone script that ingests `sample_psycheval.pdf` and tests 4 realistic school-psychology questions.
- **How it tests**: It loops through both `fast` and `deep` modes and tests `top_k` values of `2, 3, 4,` and `5` across all questions. 
- **The Result**: We successfully ran this using a local Ollama model to prove everything works perfectly end-to-end. We found that `deep mode` paired with `top_k=2` provides excellent answers for psych evaluations without feeding the LLM too much repetitive context.

## 4. Dependencies (`requirements.txt`)
- Created a fresh, pinned list of Python libraries required for the RAG service to work (ChromaDB, LangChain, PyMuPDF, FastAPI, etc.).

All files have been successfully developed, tested, and tracked locally on the `feat/deep-mode-retrieval` branch!
