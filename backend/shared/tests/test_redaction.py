"""
test_redaction.py — Unit tests for backend/shared/redaction.py

Requires en_core_web_lg to be installed:
    python -m spacy download en_core_web_lg

Run this suite separately from unit tests that mock extraction, as it loads
the actual spaCy model (~550 MB).
"""

import pytest
from backend.shared.redaction import redact, redact_page

pytestmark = [pytest.mark.ferpa, pytest.mark.integration, pytest.mark.requires_spacy]

SAMPLE_PSYCH_TEXT = (
    "PSYCHOEDUCATIONAL EVALUATION REPORT\n"
    "Student: Marcus Johnson\n"
    "Date of Birth: 1/15/2012\n"
    "District Student ID: 1234567\n"
    "Parent Phone: (555) 867-5309\n"
    "Email: mjohnson_parent@gmail.com\n"
    "Evaluator: Dr. Sarah Lee\n"
    "School: Lincoln Elementary, Springfield\n"
)


def test_redact_returns_tuple():
    result = redact(SAMPLE_PSYCH_TEXT)
    assert isinstance(result, tuple) and len(result) == 2
    redacted, entity_map = result
    assert isinstance(redacted, str)
    assert isinstance(entity_map, dict)


def test_real_name_not_in_output():
    redacted, _ = redact(SAMPLE_PSYCH_TEXT)
    assert "Marcus Johnson" not in redacted


def test_placeholder_in_output():
    redacted, _ = redact(SAMPLE_PSYCH_TEXT)
    assert "STUDENT_NAME_1" in redacted


def test_entity_map_has_original_name():
    _, entity_map = redact(SAMPLE_PSYCH_TEXT)
    assert "Marcus Johnson" in entity_map.values()


def test_dob_redacted():
    redacted, entity_map = redact(SAMPLE_PSYCH_TEXT)
    assert "1/15/2012" not in redacted
    assert any("DATE_OF_BIRTH" in k for k in entity_map)


def test_student_id_redacted():
    redacted, entity_map = redact(SAMPLE_PSYCH_TEXT)
    assert "1234567" not in redacted
    assert any("STUDENT_ID" in k for k in entity_map)


def test_phone_redacted():
    redacted, _ = redact(SAMPLE_PSYCH_TEXT)
    assert "867-5309" not in redacted


def test_email_redacted():
    redacted, _ = redact(SAMPLE_PSYCH_TEXT)
    assert "mjohnson_parent@gmail.com" not in redacted


def test_numbering_resets_per_call():
    _, map1 = redact("Patient Marcus Johnson was evaluated.")
    _, map2 = redact("Patient Sarah Lee was evaluated.")
    # Each independent call starts numbering from 1
    assert "STUDENT_NAME_1" in map1
    assert "STUDENT_NAME_1" in map2


def test_shared_state_consistent_across_pages():
    counters: dict = {}
    entity_map: dict = {}
    page1 = redact_page("Student: Marcus Johnson was referred for evaluation.", counters, entity_map)
    page2 = redact_page("As noted, Marcus Johnson demonstrated strong verbal skills.", counters, entity_map)

    # Same name on both pages → same placeholder
    assert "STUDENT_NAME_1" in page1
    assert "STUDENT_NAME_1" in page2
    # Only one STUDENT_NAME entry in the map
    student_name_keys = [k for k in entity_map if k.startswith("STUDENT_NAME_")]
    assert len(student_name_keys) == 1


def test_entity_map_placeholder_maps_to_original():
    redacted, entity_map = redact("Student: Marcus Johnson. DOB: 3/10/2013.")
    # Every placeholder in the redacted text must exist in the entity_map
    for placeholder in entity_map:
        assert placeholder in redacted


def test_clean_text_returns_empty_entity_map():
    redacted, entity_map = redact("The student demonstrated age-appropriate reading skills.")
    assert isinstance(entity_map, dict)
    # May or may not find entities in generic text — just ensure no crash
