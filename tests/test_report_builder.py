import io
import json
import builtins
import pytest
from unittest.mock import patch
import report_builder as rb


# --- BASIC STRUCTURE TESTS ---

def test_style_constant_contains_dark_and_light():
    """STYLE constant should contain both dark and light mode definitions."""
    assert "dark" in rb.STYLE
    assert "light" in rb.STYLE


# --- COMPUTE STATS AND SCORES ---

def test_compute_stats_and_scores_all_categories():
    """Should compute stats correctly for all change types and categories."""
    blocks = [
        {"change": "added", "type": "paragraph"},
        {"change": "deleted", "type": "table"},
        {"change": "unchanged", "type": "paragraph"},
        {"change": "changed", "type": "paragraph", "old": {"text": "abc"}, "new": {"text": "abcd"}},
        {"change": "changed", "type": "image"},
        {"change": "changed", "type": "table"},
    ]
    stats = rb.compute_stats_and_scores(blocks)
    assert all(k in stats for k in ["added", "deleted", "changed", "unchanged"])
    assert isinstance(stats["by_type"], dict)
    # Each block should have a _score
    assert all("_score" in b for b in blocks)
    # TOC indexes must correspond to changed/added/deleted
    assert all(blocks[i]["change"] in ("added", "deleted", "changed") for i in stats["top_changes"])


def test_compute_stats_and_scores_with_numbers_units_years():
    """Extra scoring for digits, units and years should increase the score."""
    blocks = [
        {"change": "changed", "type": "paragraph",
         "old": {"text": "value 12"}, "new": {"text": "value 13 kg 2024"}},
    ]
    stats = rb.compute_stats_and_scores(blocks)
    b = blocks[0]
    assert b["_score"] > 1.0
    assert isinstance(stats, dict)


# --- RENDER HELPERS ---

def test_render_ai_info_empty(monkeypatch):
    """_render_ai_info should render nothing when no AI data present."""
    f = io.StringIO()
    rb._render_ai_info(f, {})
    assert f.getvalue() == ""


def test_render_ai_info_full(monkeypatch):
    """Should render badges for all AI data fields."""
    f = io.StringIO()
    block = {
        "_ai_labels": ["person", "date"],
        "_ai_sem_score": 8.7,
        "_ai_type": "substantive",
        "_ai_conf": 0.95,
    }
    rb._render_ai_info(f, block)
    html = f.getvalue()
    assert "AI analysis" in html
    assert "person" in html
    assert "Type:" in html
    assert "Relevance" in html
    assert "Confidence" in html


def test_render_paragraph_changed_and_unchanged():
    """Should render correct HTML structure for changed and unchanged blocks."""
    changed = {
        "change": "changed",
        "old": {"text": "old text"},
        "new": {"text": "new text"},
        "inline_html": "<del>old</del><ins>new</ins>"
    }
    f1 = io.StringIO()
    rb._render_paragraph(f1, changed, "changed")
    html1 = f1.getvalue()
    assert "Inline diff" in html1
    assert "Old:" in html1
    assert "New:" in html1

    unchanged = {"change": "unchanged", "text": "no diff"}
    f2 = io.StringIO()
    rb._render_paragraph(f2, unchanged, "unchanged")
    assert "no diff" in f2.getvalue()


def test_render_table_with_table_changes_and_plain():
    """Render tables with both dict cells and plain text."""
    b1 = {"table_changes": [[{"type": "same", "text": "ok"}, {"type": "diff", "inline_html": "<ins>x</ins>"}]]}
    f1 = io.StringIO()
    rb._render_table(f1, b1, "changed")
    html1 = f1.getvalue()
    assert "<table>" in html1 and "ok" in html1 and "<ins>x</ins>" in html1

    b2 = {"table": [["a", "b"], ["c", "d"]]}
    f2 = io.StringIO()
    rb._render_table(f2, b2, "changed")
    html2 = f2.getvalue()
    assert "a" in html2 and "b" in html2


def test_render_image_with_and_without_sha():
    """Image render should include SHA when available."""
    b1 = {"sha1": "1234567890abcdef"}
    f1 = io.StringIO()
    rb._render_image(f1, b1, "added")
    assert "SHA1" in f1.getvalue()

    b2 = {"new": {"sha1": "abcdef123456"}}
    f2 = io.StringIO()
    rb._render_image(f2, b2, "added")
    assert "SHA1" in f2.getvalue()


# --- MAIN HTML REPORT ---

@patch("report_builder.analyze_change")
@patch("report_builder.generate_ai_summary", return_value="Summary OK")
def test_generate_html_report_success(mock_summary, mock_analyze, tmp_path):
    """Should generate a complete HTML report and fill AI fields."""
    mock_analyze.return_value = {
        "labels": ["person"], "semantic_score": 9.9,
        "change_type": "substantive", "confidence": 0.88
    }

    blocks = [
        {"change": "added", "type": "paragraph", "text": "abc"},
        {"change": "changed", "type": "paragraph",
         "old": {"text": "old"}, "new": {"text": "new"}},
    ]
    out = tmp_path / "report.html"
    rb.generate_html_report(blocks, output_path=str(out))
    html = out.read_text(encoding="utf-8")
    assert "<html>" in html
    assert "AI Summary" in html
    assert "Document Comparison Report" in html
    assert "Mode: light" in html
    # check that AI fields were added
    assert "_ai_labels" in blocks[1]


@patch("report_builder.analyze_change", side_effect=Exception("AI error"))
@patch("report_builder.generate_ai_summary", return_value="Summary fallback")
def test_generate_html_report_with_ai_exception(mock_summary, mock_analyze, tmp_path):
    """Should handle AI exceptions gracefully and still produce report."""
    blocks = [{"change": "changed", "type": "paragraph",
               "old": {"text": "a"}, "new": {"text": "b"}}]
    out = tmp_path / "report.html"
    rb.generate_html_report(blocks, output_path=str(out))
    html = out.read_text(encoding="utf-8")
    assert "AI Summary" in html
    # Even after exception, fields must be initialized
    assert "_ai_labels" in blocks[0]


# --- JSON EXPORT ---

def test_generate_json_report_success(tmp_path):
    """Should successfully create a JSON report."""
    blocks = [{"change": "added", "type": "paragraph"}]
    out = tmp_path / "rep.json"
    rb.generate_json_report(blocks, output_path=str(out))
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data[0]["type"] == "paragraph"


def test_generate_json_report_error(monkeypatch):
    """Should raise and log if JSON writing fails."""
    blocks = [{"change": "added"}]
    def bad_open(*a, **kw): raise IOError("fail")
    monkeypatch.setattr(builtins, "open", bad_open)
    with pytest.raises(IOError):
        rb.generate_json_report(blocks, output_path="x.json")
