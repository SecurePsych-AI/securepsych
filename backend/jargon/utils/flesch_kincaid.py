import re


def _count_syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    count = len(re.findall(r"[aeiouy]+", word))
    # Silent trailing 'e' (e.g. "make" → 1, not 2)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def flesch_kincaid_grade(text: str) -> float:
    """FK Grade Level: 0.39*(words/sentences) + 11.8*(syllables/words) - 15.59"""
    # Require sentence-ending punctuation so bare fragments don't count
    sentences = re.findall(r"[^.!?]+[.!?]+", text)
    words = re.findall(r"\b[a-zA-Z]+\b", text)
    if not sentences or not words:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    grade = (
        0.39 * len(words) / len(sentences)
        + 11.8 * syllables / len(words)
        - 15.59
    )
    return round(grade, 1)
