import pytest
from utils.flesch_kincaid import flesch_kincaid_grade, _count_syllables

pytestmark = [pytest.mark.jargon, pytest.mark.unit]


def test_simple_text_low_grade():
    grade = flesch_kincaid_grade("See Spot run. See Spot play.")
    assert grade < 2.0, f"Expected grade < 2.0, got {grade}"


def test_complex_text_higher_grade():
    text = (
        "The student demonstrates significant deficits in phonological processing "
        "and rapid automatized naming, consistent with a diagnosis of Specific "
        "Learning Disability in reading comprehension and decoding."
    )
    grade = flesch_kincaid_grade(text)
    assert grade > 8.0, f"Expected grade > 8.0, got {grade}"


def test_empty_string_returns_zero():
    assert flesch_kincaid_grade("") == 0.0


def test_no_sentence_terminator_returns_zero():
    assert flesch_kincaid_grade("hello") == 0.0


def test_syllable_monosyllabic():
    assert _count_syllables("cat") == 1
    assert _count_syllables("dog") == 1
    assert _count_syllables("run") == 1


def test_syllable_polysyllabic():
    assert _count_syllables("education") >= 4
    assert _count_syllables("processing") >= 3


def test_syllable_silent_e():
    assert _count_syllables("make") == 1


def test_return_type_is_float():
    result = flesch_kincaid_grade("The cat sat. The dog ran.")
    assert isinstance(result, float)
