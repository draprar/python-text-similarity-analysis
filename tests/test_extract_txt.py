import pytest
from extractors.extract_txt import TxtExtractor


@pytest.mark.unit
def test_txt_extract_file_not_found(tmp_path):
    """Should raise FileNotFoundError when the input file does not exist."""
    ex = TxtExtractor()
    missing = tmp_path / "nope.txt"
    with pytest.raises(FileNotFoundError):
        ex.extract_blocks(missing)


@pytest.mark.unit
def test_txt_extract_nonempty_lines(tmp_path):
    """Non-empty lines should become paragraph blocks (preserve order)."""
    p = tmp_path / "test.txt"
    p.write_text("first line\nsecond line\n")  # normal text file

    ex = TxtExtractor()
    blocks = ex.extract_blocks(p)
    assert isinstance(blocks, list)
    assert blocks == [
        {"type": "paragraph", "text": "first line"},
        {"type": "paragraph", "text": "second line"},
    ]


@pytest.mark.unit
def test_txt_extract_ignores_empty_and_whitespace(tmp_path):
    """Empty lines and lines with only whitespace are ignored."""
    p = tmp_path / "ws.txt"
    p.write_text("a\n\n   \nb\n")  # includes blank and whitespace-only lines

    blocks = TxtExtractor().extract_blocks(p)
    assert [b["text"] for b in blocks] == ["a", "b"]


@pytest.mark.unit
def test_txt_extract_handles_invalid_bytes_and_replace(tmp_path):
    """Files with invalid UTF-8 bytes are opened with errors='replace' and produce non-empty lines."""
    p = tmp_path / "bin.txt"
    # write bytes including invalid UTF-8 sequences
    p.write_bytes(b"hello\n\x80\x80\nworld\n")

    blocks = TxtExtractor().extract_blocks(p)
    # the second line will be replaced (not empty) and therefore included
    assert len(blocks) == 3
    assert blocks[0]["text"] == "hello"
    assert blocks[2]["text"] == "world"
    # middle line should be present (replacement chars), ensure it's a non-empty string
    assert blocks[1]["text"].strip() != ""


@pytest.mark.unit
def test_txt_extractor_class_wrapper(tmp_path):
    """TxtExtractor.extract_blocks works when called via an instance (wrapper behavior)."""
    p = tmp_path / "wrap.txt"
    p.write_text("one\n")
    ex = TxtExtractor()
    res = ex.extract_blocks(p)
    assert res == [{"type": "paragraph", "text": "one"}]
