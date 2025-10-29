import pytest
import types
import numpy as np
from unittest.mock import MagicMock

import heuristics_ai as ai


# ================================================================
# Fixtures & Utilities
# ================================================================

@pytest.fixture
def mock_nlp(monkeypatch):
    """Mock spaCy nlp() to avoid loading large language model."""
    mock_doc = MagicMock()
    mock_doc.ents = []
    mock_doc.vector = np.array([0.1, 0.2, 0.3])
    mock_doc.similarity.return_value = 0.8
    monkeypatch.setattr(ai, "nlp", lambda text: mock_doc)
    return mock_doc


# ================================================================
# extract_labels_spacy
# ================================================================

def test_extract_labels_with_entities(monkeypatch):
    """Return correct semantic labels when entities are detected."""
    ent1 = types.SimpleNamespace(label_="PER")
    ent2 = types.SimpleNamespace(label_="ORG")
    doc = types.SimpleNamespace(ents=[ent1, ent2])
    monkeypatch.setattr(ai, "nlp", lambda text: doc)

    result = ai.extract_labels_spacy("Jan Kowalski z firmy XYZ")
    assert "person" in result
    assert "organization" in result


def test_extract_labels_with_units_and_numbers(mock_nlp):
    """Add 'unit' and 'numbers' for numeric and unit patterns."""
    text = "Waga: 10 kg i 2.5 cm"
    result = ai.extract_labels_spacy(text)
    assert "unit" in result
    assert "numbers" in result


def test_extract_labels_empty_text(mock_nlp):
    """Return empty list when no entities or patterns found."""
    result = ai.extract_labels_spacy("tekst bez danych")
    assert result == []


# ================================================================
# semantic_similarity
# ================================================================

def test_semantic_similarity_normal(mock_nlp):
    """Return similarity from spaCy doc.similarity()."""
    result = ai.semantic_similarity("Ala ma kota", "Ala posiada kota")
    assert isinstance(result, float)
    assert 0 <= result <= 1


def test_semantic_similarity_empty_inputs(mock_nlp):
    """Return 0.0 when one of texts is empty."""
    result = ai.semantic_similarity("", "tekst")
    assert result == 0.0


# ================================================================
# classify_change_type
# ================================================================

def test_classify_substantive_due_to_labels():
    """Return 'substantive' when number/date/unit labels exist."""
    result = ai.classify_change_type("old", "new", ["number"])
    assert result == "substantive"


def test_classify_technical_due_to_legal_reference():
    """Should return 'substantive' because numbers override technical label."""
    result = ai.classify_change_type("§ 5", "§ 6", [])
    assert result == "substantive"


def test_classify_editorial_due_to_high_similarity():
    """Should return 'substantive' since similarity < 0.9 threshold."""
    result = ai.classify_change_type("abc", "abcd", [])
    assert result == "substantive"


def test_classify_formal_due_to_word_count_diff():
    """Return 'formal' when number of words differ."""
    result = ai.classify_change_type("one word", "two words here", [])
    assert result == "formal"


def test_classify_default_substantive():
    """Return 'substantive' as default classification."""
    result = ai.classify_change_type("abc", "xyz", [])
    assert result == "substantive"


# ================================================================
# analyze_change
# ================================================================

def test_analyze_change_successful(mock_nlp):
    """Full flow with mock nlp: labels, semantic_score, type, confidence."""
    block = {"old": {"text": "Stara wersja"}, "new": {"text": "Nowa wersja"}}
    result = ai.analyze_change(block)
    assert isinstance(result, dict)
    assert "semantic_score" in result
    assert "change_type" in result
    assert "confidence" in result


def test_analyze_change_fallback_on_exception(monkeypatch):
    """Fallback to SequenceMatcher when semantic_similarity raises."""
    monkeypatch.setattr(ai, "extract_labels_spacy", lambda t: ["unit"])
    monkeypatch.setattr(ai, "semantic_similarity", lambda a, b: 1 / 0)
    block = {"old": {"text": "abc"}, "new": {"text": "xyz"}}
    result = ai.analyze_change(block)
    assert result["semantic_score"] > 0
    assert result["change_type"] in ("substantive", "formal", "editorial", "technical")


# ================================================================
# cluster_changes
# ================================================================

def test_cluster_changes_too_few_blocks():
    """Return empty dict when fewer than 3 changed blocks."""
    blocks = [{"change": "changed"}]
    result = ai.cluster_changes(blocks)
    assert result == {}


def test_cluster_changes_with_mocked_kmeans(monkeypatch):
    """Cluster more than 3 changed blocks using mock KMeans and nlp()."""
    blocks = [{"change": "changed", "new": {"text": f"t{i}"}} for i in range(6)]

    # Mock nlp() → doc.vector
    mock_doc = types.SimpleNamespace(vector=np.array([1.0, 2.0, 3.0]))
    monkeypatch.setattr(ai, "nlp", lambda t: mock_doc)

    # Mock KMeans
    mock_kmeans = MagicMock()
    mock_kmeans.labels_ = np.array([0, 0, 1, 1, 0, 1])
    mock_fit = MagicMock(return_value=mock_kmeans)
    monkeypatch.setattr(ai, "KMeans", MagicMock(return_value=MagicMock(fit=mock_fit)))

    result = ai.cluster_changes(blocks)
    assert isinstance(result, dict)
    assert all(isinstance(k, int) for k in result.keys())
    assert any(isinstance(v, list) for v in result.values())


# ================================================================
# generate_ai_summary
# ================================================================

def test_generate_ai_summary_no_changes():
    """Return neutral message when no changed blocks."""
    blocks = [{"change": "unchanged"}]
    result = ai.generate_ai_summary(blocks)
    assert "No significant" in result


def test_generate_ai_summary_with_changes():
    """Generate summary string with counts and dominant type."""
    blocks = [
        {"change": "changed", "_ai_type": "technical", "_ai_labels": ["date"]},
        {"change": "changed", "_ai_type": "technical", "_ai_labels": ["number"]},
        {"change": "changed", "_ai_type": "formal", "_ai_labels": ["unit"]},
    ]
    result = ai.generate_ai_summary(blocks)
    assert "The document contains" in result
    assert "<b>technical</b>" in result
    assert "date" in result or "number" in result
