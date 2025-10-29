import logging
import pytest
from diff_engine import (
    html_inline_diff,
    _table_cell_diff,
    _diff_tables,
    compare_blocks,
)

# ================================================================
# Tests for html_inline_diff
# ================================================================

@pytest.mark.unit
def test_html_inline_diff_equal():
    """Verify that identical strings return unchanged plain text."""
    a = b = "hello"
    result = html_inline_diff(a, b)
    assert result == "hello"


@pytest.mark.unit
def test_html_inline_diff_insert():
    """Ensure that inserted text is wrapped in <ins> tags."""
    result = html_inline_diff("a", "abc")
    assert "<ins>" in result
    assert "a" in result


@pytest.mark.unit
def test_html_inline_diff_delete():
    """Ensure that deleted text is wrapped in <del> tags."""
    result = html_inline_diff("abc", "a")
    assert "<del>" in result


@pytest.mark.unit
def test_html_inline_diff_replace():
    """Ensure that replaced text includes both <del> and <ins> tags."""
    result = html_inline_diff("cat", "dog")
    assert "<del>" in result and "<ins>" in result


# ================================================================
# Tests for _table_cell_diff
# ================================================================

@pytest.mark.unit
def test_table_cell_diff_same():
    """Return type 'same' when both cells are identical."""
    cell = _table_cell_diff("A", "A")
    assert cell == {"type": "same", "text": "A"}


@pytest.mark.unit
def test_table_cell_diff_changed():
    """Return type 'changed' and include inline diff when cells differ."""
    cell = _table_cell_diff("A", "B")
    assert cell["type"] == "changed"
    assert "inline_html" in cell
    assert "<del>" in cell["inline_html"]
    assert "<ins>" in cell["inline_html"]


# ================================================================
# Tests for _diff_tables
# ================================================================

@pytest.mark.unit
def test_diff_tables_equal():
    """All cells marked as 'same' when tables are identical."""
    t1 = [["A", "B"], ["C", "D"]]
    t2 = [["A", "B"], ["C", "D"]]
    result = _diff_tables(t1, t2)
    assert all(cell["type"] == "same" for row in result for cell in row)


@pytest.mark.unit
def test_diff_tables_changed_and_extra_row():
    """Detects changed cells and handles additional rows."""
    old = [["A", "B"], ["C", "D"]]
    new = [["A", "X"], ["C", "D"], ["E", "F"]]
    result = _diff_tables(old, new)
    assert result[0][1]["type"] == "changed"
    # The last row doesn't exist in the old table → treated as changed
    assert result[-1][0]["type"] == "changed"


# ================================================================
# Tests for compare_blocks
# ================================================================

@pytest.mark.unit
def test_compare_blocks_equal_paragraphs():
    """Return 'unchanged' for identical paragraph blocks."""
    old = [{"type": "paragraph", "text": "Hello"}]
    new = [{"type": "paragraph", "text": "Hello"}]
    result = compare_blocks(old, new)
    assert result == [{"change": "unchanged", "type": "paragraph", "text": "Hello"}]


@pytest.mark.unit
def test_compare_blocks_changed_paragraph():
    """Return 'changed' and inline diff for modified paragraphs."""
    old = [{"type": "paragraph", "text": "Hi"}]
    new = [{"type": "paragraph", "text": "Hello"}]
    result = compare_blocks(old, new)
    assert result[0]["change"] == "changed"
    assert "<ins>" in result[0]["inline_html"]
    assert "<del>" in result[0]["inline_html"]


@pytest.mark.unit
def test_compare_blocks_added_and_deleted():
    """Detect 'changed' when old and new paragraphs differ."""
    old = [{"type": "paragraph", "text": "old"}]
    new = [{"type": "paragraph", "text": "new"}]
    result = compare_blocks(old, new)
    changes = [r["change"] for r in result]
    assert "changed" in changes


@pytest.mark.unit
def test_compare_blocks_with_table_changes():
    """Return 'changed' and table diff details for modified tables."""
    old = [{"type": "table", "table": [["A", "B"]]}]
    new = [{"type": "table", "table": [["A", "X"]]}]
    result = compare_blocks(old, new)
    assert result[0]["change"] == "changed"
    assert "table_changes" in result[0]
    assert result[0]["table_changes"][0][1]["type"] == "changed"


@pytest.mark.unit
def test_compare_blocks_insert_and_delete_mixed():
    """Detect both added and deleted paragraphs in mixed scenarios."""
    old = [
        {"type": "paragraph", "text": "A"},
        {"type": "paragraph", "text": "B"},
    ]
    new = [
        {"type": "paragraph", "text": "B"},
        {"type": "paragraph", "text": "C"},
    ]
    result = compare_blocks(old, new)
    changes = [r["change"] for r in result]
    assert "deleted" in changes or "added" in changes


@pytest.mark.unit
def test_compare_blocks_image_handling():
    """Mark image blocks with different SHA1 as 'changed'."""
    old = [{"type": "image", "sha1": "abc"}]
    new = [{"type": "image", "sha1": "def"}]
    result = compare_blocks(old, new)
    assert result[0]["change"] == "changed"
    assert "old" in result[0] and "new" in result[0]


@pytest.mark.unit
def test_compare_blocks_handles_exception_during_diff(monkeypatch, caplog):
    """Force an exception during diff generation to trigger logger.debug branch."""
    def broken_diff(a, b):
        raise ValueError("Boom")

    monkeypatch.setattr("diff_engine.html_inline_diff", broken_diff)
    old = [{"type": "paragraph", "text": "A"}]
    new = [{"type": "paragraph", "text": "B"}]

    with caplog.at_level(logging.DEBUG):
        result = compare_blocks(old, new)

    assert any("Error while generating diff details" in msg for msg in caplog.messages)
    assert result[0]["change"] == "changed"


@pytest.mark.unit
def test_compare_blocks_with_unknown_block_type():
    """Ensure unknown block types are handled gracefully (final 'return t' in key_of())."""
    old = [{"type": "weird"}]
    new = [{"type": "weird"}]
    result = compare_blocks(old, new)
    assert result[0]["change"] == "unchanged"
