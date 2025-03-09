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

@pytest.mark.parametrize("sentence, expected", [
    ("It is believed that this might be approximately correct.", "High"),  # 2 frazy + 1 słowo
    ("It appears to be somewhat unclear.", "High"),  # 2 frazy
])
def test_multiple_ambiguities(sentence, expected):
    """Ensure function detects multiple ambiguous terms properly."""
    result = analyze_sentence(sentence)
    assert result["ambiguity"] == expected

@pytest.mark.parametrize("sentence", [None, 123, 3.14, [], {}])
def test_unexpected_input_types(sentence):
    """Ensure function handles unexpected input types gracefully."""
    try:
        result = analyze_sentence(str(sentence))
        assert isinstance(result, dict) and "ambiguity" in result
    except Exception:
        pytest.fail(f"analyze_sentence() crashed on input: {sentence}")
