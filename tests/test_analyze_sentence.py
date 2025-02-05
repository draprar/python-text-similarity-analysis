import pytest
from helpers.analyze_sentence import analyze_sentence

@pytest.mark.parametrize("sentence, expected", [
    ("This might be a problem.", "High"),   # Both ambiguous keyword and phrase
    ("It is unclear what to do.", "Medium"), # Single ambiguous keyword
    ("This is a test.", "Medium"),          # Single ambiguous keyword
    ("The analysis appears to be wrong.", "Medium"),  # Single ambiguous phrase
    ("Everything is clear and precise.", "Low"),  # No ambiguous words
    ("", "Low"),  # Empty sentence
    ("Unrelated words without ambiguity.", "Low") # No ambiguous words or phrases
])
def test_analyze_sentence(sentence, expected):
    """Test ambiguity detection in different sentences."""
    result = analyze_sentence(sentence)
    assert result["ambiguity"] == expected, f"Failed for input: {sentence}"

def test_analyze_sentence_no_crash():
    """Ensure function does not crash on unexpected input."""
    try:
        analyze_sentence(None)  # Passing None as input
    except Exception:
        pytest.fail("analyze_sentence() crashed on None input.")
