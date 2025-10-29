import pytest
from extractors.extract_docx import _safe_hex_color, extract_docx_blocks, DocxExtractor


class DummyRun:
    """Simple mock for a docx Run object."""

    def __init__(self, bold=False, italic=False, underline=False, color_rgb=None):
        self.bold = bold
        self.italic = italic
        self.underline = underline
        # font.color.rgb or None
        self.font = type("F", (), {"color": type("C", (), {"rgb": color_rgb})()})()


# --------------------------
# _safe_hex_color() tests
# --------------------------

def test_safe_hex_color_valid():
    """Should return formatted hex color when run.font.color.rgb exists."""
    run = DummyRun(color_rgb=(255, 0, 0))
    assert _safe_hex_color(run) == "#ff0000"


def test_safe_hex_color_no_color():
    """Should default to black (#000000) when color is None."""
    run = DummyRun()
    run.font.color = None
    assert _safe_hex_color(run) == "#000000"


def test_safe_hex_color_exception():
    """Should handle unexpected errors and return default color."""
    bad_run = object()
    assert _safe_hex_color(bad_run) == "#000000"


# --------------------------
# extract_docx_blocks() tests
# --------------------------

def test_extract_docx_blocks_missing_file(tmp_path):
    """Should raise FileNotFoundError for missing files."""
    f = tmp_path / "missing.docx"
    with pytest.raises(FileNotFoundError):
        extract_docx_blocks(f)


def test_extract_docx_blocks_paragraph(monkeypatch, tmp_path):
    """Should extract paragraph block with basic attributes."""
    # create a fake element instance that will be placed in doc.element.body
    fake_element = type("Elem", (), {})()
    fake_element.tag = "{w}p"  # endswith("}p")

    # prepare a fake paragraph where _element points to the same instance
    fake_para = type(
        "P",
        (),
        {
            "text": "Hello",
            "style": type("S", (), {"name": "Normal"})(),
            "runs": [DummyRun(bold=True, italic=False, underline=True)],
            "_element": fake_element,  # identity match
        },
    )()

    fake_doc = type(
        "Doc",
        (),
        {
            "paragraphs": [fake_para],
            "tables": [],
            "element": type("E", (), {"body": [fake_element]})(),
            "part": type("Part", (), {"related_parts": {}})(),
        },
    )()

    monkeypatch.setattr("extractors.extract_docx.Document", lambda _: fake_doc)

    f = tmp_path / "f.docx"
    f.write_text("dummy")

    result = extract_docx_blocks(f)
    assert isinstance(result, list)
    assert len(result) == 1
    block = result[0]
    assert block["type"] == "paragraph"
    assert block["text"] == "Hello"
    assert block["bold"] is True
    assert block["italic"] is False
    assert block["underline"] is True
    assert block["style"] == "Normal"


def test_extract_docx_blocks_table(monkeypatch, tmp_path):
    """Should extract table block correctly."""
    # create table cells/rows/tbl with _element set to the element instance
    fake_cell = type("C", (), {"text": "X"})()
    fake_row = type("R", (), {"cells": [fake_cell]})()
    fake_tbl = type("T", (), {"rows": [fake_row]})()
    # set _element on fake_tbl for identity match
    fake_tbl._element = type("ElemTbl", (), {})()
    fake_tbl._element.tag = "{w}tbl"

    fake_doc = type(
        "Doc",
        (),
        {
            "paragraphs": [],
            "tables": [fake_tbl],
            "element": type("E", (), {"body": [fake_tbl._element]})(),
            "part": type("Part", (), {"related_parts": {}})(),
        },
    )()

    monkeypatch.setattr("extractors.extract_docx.Document", lambda _: fake_doc)
    f = tmp_path / "tbl.docx"
    f.write_text("dummy")
    res = extract_docx_blocks(f)
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["type"] == "table"
    assert res[0]["table"] == [["X"]]


def test_extract_docx_blocks_image(monkeypatch, tmp_path):
    """Should handle embedded image extraction."""
    data = b"imagedata"
    fake_part = type("Part", (), {"blob": data, "partname": "img.png"})()
    related = {"rId1": fake_part}

    # simulate a blip object with get() returning the embed id
    fake_blip = type("B", (), {"get": lambda self, k: "rId1"})()

    # simulate run._element that has findall returning the fake_blip list
    class FakeRunElement:
        def findall(self, *args, **kwargs):
            return [fake_blip]

    fake_run_elem = FakeRunElement()

    # run with _element that returns blips
    fake_run = DummyRun()
    fake_run._element = fake_run_elem

    # paragraph whose _element must match element in doc.element.body
    elem = type("ElemP", (), {})()
    elem.tag = "{w}p"

    fake_para = type(
        "P",
        (),
        {
            "text": "Image",
            "style": type("S", (), {"name": "Normal"})(),
            "runs": [fake_run],
            "_element": elem,
        },
    )()

    fake_doc = type(
        "Doc",
        (),
        {
            "paragraphs": [fake_para],
            "tables": [],
            "element": type("E", (), {"body": [elem]})(),
            "part": type("Part", (), {"related_parts": related})(),
        },
    )()

    monkeypatch.setattr("extractors.extract_docx.Document", lambda _: fake_doc)

    f = tmp_path / "img.docx"
    f.write_text("dummy")

    blocks = extract_docx_blocks(f)
    assert isinstance(blocks, list)
    # should include paragraph block and an image block appended after paragraph processing
    assert any(b.get("type") == "image" for b in blocks)


def test_docx_extractor_wrapper(monkeypatch, tmp_path):
    """DocxExtractor should delegate to extract_docx_blocks."""
    called = {}

    def fake_extract(p):
        called["ok"] = True
        return [{"type": "paragraph", "text": "ok"}]

    monkeypatch.setattr("extractors.extract_docx.extract_docx_blocks", fake_extract)

    f = tmp_path / "f.docx"
    f.write_text("dummy")

    ex = DocxExtractor()
    res = ex.extract_blocks(f)
    assert called
    assert res[0]["text"] == "ok"
