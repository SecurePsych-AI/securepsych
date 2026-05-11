"""
redaction.py — SecurePsych shared PII redaction library

Uses Microsoft Presidio + spaCy (en_core_web_lg) for fully local, zero-network NER.
All processing happens in-process; no data ever leaves the machine.

Public API
----------
redact(text)               → (redacted_text, entity_map)
    Single-document call. Counters reset per call.

redact_page(text, counters, entity_map) → redacted_text
    Per-page call with shared state so numbering is consistent across pages
    of the same document (STUDENT_NAME_1 on page 1 and page 3 refers to the
    same person).

One-time setup (run during provisioning, not at runtime):
    python -m spacy download en_core_web_lg
"""

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

# ---------------------------------------------------------------------------
# Custom recognizers
# ---------------------------------------------------------------------------

DOB_RECOGNIZER = PatternRecognizer(
    supported_entity="DATE_OF_BIRTH",
    patterns=[
        Pattern("dob_slash", r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", score=0.5),
        Pattern("dob_dash",  r"\b\d{1,2}-\d{1,2}-\d{2,4}\b", score=0.5),
    ],
    context=["date of birth", "dob", "born", "birth date", "birthdate"],
)

# District student IDs are 6-7 digit numbers; context words raise confidence.
STUDENT_ID_RECOGNIZER = PatternRecognizer(
    supported_entity="STUDENT_ID",
    patterns=[Pattern("district_id", r"\b\d{6,7}\b", score=0.75)],
    context=["student", "id", "student id", "pupil", "district"],
)

# ---------------------------------------------------------------------------
# Entity configuration
# ---------------------------------------------------------------------------

ENTITY_DISPLAY_MAP: dict[str, str] = {
    "PERSON":        "STUDENT_NAME",
    "DATE_OF_BIRTH": "DATE_OF_BIRTH",
    "US_SSN":        "US_SSN",
    "PHONE_NUMBER":  "PHONE_NUMBER",
    "EMAIL_ADDRESS": "EMAIL_ADDRESS",
    "LOCATION":      "LOCATION",
    "STUDENT_ID":    "STUDENT_ID",
}

SUPPORTED_ENTITIES: list[str] = list(ENTITY_DISPLAY_MAP.keys())

# ---------------------------------------------------------------------------
# Singleton — spaCy model is expensive to load; initialize once per process
# ---------------------------------------------------------------------------

_analyzer: AnalyzerEngine | None = None


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        _analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["en"],
        )
        _analyzer.registry.add_recognizer(DOB_RECOGNIZER)
        _analyzer.registry.add_recognizer(STUDENT_ID_RECOGNIZER)
    return _analyzer


# ---------------------------------------------------------------------------
# Core redaction logic
# ---------------------------------------------------------------------------

def redact_page(
    text: str,
    counters: dict[str, int],
    entity_map: dict[str, str],
) -> str:
    """
    Redact PII from a single page's text, updating shared counters and entity_map.

    If the same original string was already seen in a prior page, the existing
    placeholder is reused so STUDENT_NAME_1 is consistent across the whole document.

    Parameters
    ----------
    text       : Raw page text (already boilerplate-stripped).
    counters   : Mutable counter dict shared across all pages of one document.
    entity_map : Mutable map (placeholder → original value) shared across pages.

    Returns
    -------
    redacted text with PII replaced by typed numbered placeholders.
    """
    analyzer = _get_analyzer()
    results = analyzer.analyze(
        text=text,
        language="en",
        entities=SUPPORTED_ENTITIES,
        score_threshold=0.5,
    )
    # Replace right-to-left so earlier offsets remain valid after substitution.
    results.sort(key=lambda r: r.start, reverse=True)

    redacted = text
    for result in results:
        display_type = ENTITY_DISPLAY_MAP.get(result.entity_type, result.entity_type)
        original = redacted[result.start : result.end]

        # Reuse placeholder if this exact string was already mapped.
        existing = next(
            (k for k, v in entity_map.items()
             if v == original and k.startswith(display_type + "_")),
            None,
        )
        if existing:
            placeholder = existing
        else:
            counters[display_type] = counters.get(display_type, 0) + 1
            placeholder = f"{display_type}_{counters[display_type]}"
            entity_map[placeholder] = original

        redacted = redacted[: result.start] + placeholder + redacted[result.end :]

    return redacted


def redact(text: str) -> tuple[str, dict[str, str]]:
    """
    Redact PII from a single string. Counters reset per call.

    Returns
    -------
    (redacted_text, entity_map)
        entity_map: {"STUDENT_NAME_1": "Marcus Johnson", "DATE_OF_BIRTH_1": "1/15/2012", ...}
    """
    counters: dict[str, int] = {}
    entity_map: dict[str, str] = {}
    redacted_text = redact_page(text, counters, entity_map)
    return redacted_text, entity_map
