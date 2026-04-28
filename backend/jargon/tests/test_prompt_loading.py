import re
import pytest
from routes.simplify import _TEMPLATES

pytestmark = [pytest.mark.jargon, pytest.mark.unit]


def test_all_five_levels_loaded():
    assert set(_TEMPLATES.keys()) == {1, 2, 3, 4, 5}


def test_each_template_has_text_placeholder():
    for level, template in _TEMPLATES.items():
        assert "{text}" in template, f"Level {level} template missing {{text}} placeholder"


def test_no_extra_placeholders():
    for level, template in _TEMPLATES.items():
        placeholders = re.findall(r"\{(\w+)\}", template)
        assert placeholders == ["text"], (
            f"Level {level} template has unexpected placeholders: {placeholders}"
        )


def test_templates_are_non_empty():
    for level, template in _TEMPLATES.items():
        assert len(template.strip()) > 50, f"Level {level} template looks suspiciously short"
