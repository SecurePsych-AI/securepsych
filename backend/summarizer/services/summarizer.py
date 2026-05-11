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
Document content is blocked from LangSmith by the LANGCHAIN_HIDE_INPUTS/OUTPUTS
guards set unconditionally in main.py. Do not remove those guards.
"""

import logging
import os

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

logger = logging.getLogger(__name__)

_OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
_OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]

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


async def run_summarize_chain(docs: list[Document]) -> str:
    logger.info(
        "[summarizer] Starting summarization — total chunks: %d", len(docs))

    llm = OllamaLLM(
        model=_OLLAMA_MODEL,
        base_url=_OLLAMA_BASE_URL,
    )
    logger.info("[summarizer] LLM initialised — model: %s | base_url: %s",
                _OLLAMA_MODEL, _OLLAMA_BASE_URL)

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
