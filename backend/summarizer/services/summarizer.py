"""
Summarization chain using LangChain's Refine strategy.

Why Refine?
  Psychoeducational evaluation reports are long (40–60 pages) and
  self-referential — a recommendation on page 45 may reference a score from
  page 12. The Refine method processes chunks sequentially, carrying a running
  summary forward, which preserves these cross-page relationships better than
  map-reduce (which summarizes chunks independently then merges).

  Decision documented per Summarization_POC_Checklist item 2 (Research 3).

LangSmith tracing is enabled automatically via LANGCHAIN_TRACING_V2 env var.
Only token counts and latency metadata are transmitted — zero document content.
"""

import logging
import os

import yaml
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

logger = logging.getLogger(__name__)

# ── Prompts ────────────────────────────────────────────────────────────────────

_INITIAL_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""You are an expert in psychoeducational evaluations.
Analyze the following excerpt from a psychological evaluation report and extract all relevant information.

Focus specifically on:
- Diagnoses or eligibility findings (e.g., SLD, OHI, autism eligibility determinations)
- Key test scores and assessment results (include instrument names, score names, values, and percentiles where stated)
- Accommodations or recommendations
- Evaluation dates and relevant timeline information

Rules:
- Be factual. Only include information explicitly stated in the text.
- Do not infer, extrapolate, or fabricate any information.
- If a category has no information in this excerpt, omit it rather than guessing.

DOCUMENT EXCERPT:
{text}

STRUCTURED SUMMARY:""",
)

_REFINE_PROMPT = PromptTemplate(
    input_variables=["existing_answer", "text"],
    template="""You are an expert in psychoeducational evaluations.
You have a running summary of a psychological evaluation report built from earlier pages.
Refine and expand it using the new document content below.

Rules:
- Only add information explicitly stated in the new content.
- Preserve ALL existing findings — do not remove or shorten prior content.
- If the new content clarifies, updates, or contradicts earlier information, revise accordingly and note the correction.
- Pay particular attention to cross-references (e.g., a recommendation that references an earlier test score).
- Do not fabricate or infer anything not in the text.

EXISTING SUMMARY:
{existing_answer}

NEW DOCUMENT CONTENT:
{text}

REFINED STRUCTURED SUMMARY:""",
)

# ── Chain ──────────────────────────────────────────────────────────────────────


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


async def run_summarize_chain(docs: list[Document]) -> str:
    """
    Run the Refine summarization chain over a list of LangChain Documents.

    Processes chunks sequentially:
      1. First chunk  → initial summary via _INITIAL_PROMPT
      2. Each subsequent chunk → refine the running summary via _REFINE_PROMPT

    All inference is routed through the local Ollama instance — zero outbound
    network calls during a summarization request.

    Args:
        docs: Chunked Documents from pdf_loader.load_pdf_from_bytes()

    Returns:
        The final structured summary string.
    """
    cfg = _load_config()["summarizer"]
    logger.info(
        "[summarizer] Starting summarization — total chunks: %d", len(docs))

    llm = OllamaLLM(
        model=cfg["model"],
        base_url=cfg["ollama_base_url"],
    )
    logger.info("[summarizer] LLM initialised — model: %s | base_url: %s",
                cfg["model"], cfg["ollama_base_url"])

    initial_chain = _INITIAL_PROMPT | llm | StrOutputParser()
    refine_chain = _REFINE_PROMPT | llm | StrOutputParser()

    # Step 1: summarize first chunk
    logger.info(
        "[summarizer] Processing chunk 1/%d (initial prompt)", len(docs))
    summary = await initial_chain.ainvoke({"text": docs[0].page_content})
    logger.info(
        "[summarizer] Initial summary generated — length: %d chars", len(summary))

    # Step 2: refine with each subsequent chunk
    for idx, doc in enumerate(docs[1:], start=2):
        logger.info("[summarizer] Refining with chunk %d/%d", idx, len(docs))
        summary = await refine_chain.ainvoke(
            {
                "existing_answer": summary,
                "text": doc.page_content,
            }
        )
        logger.info(
            "[summarizer] Refined summary length after chunk %d: %d chars", idx, len(summary))

    logger.info(
        "[summarizer] Summarization complete — final summary length: %d chars", len(summary))
    return summary
