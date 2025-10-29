import pytest
from extractors.extract_xlsx import XlsxExtractor


class FakeWS:
    def __init__(self, rows, title="Sheet1"):
        """
        rows: an iterable of tuples (values_only=True would yield tuples)
        """
        self._rows = rows
        self.title = title

    def iter_rows(self, values_only=True):
        for r in self._rows:
            yield r


class FakeWB:
    def __init__(self, worksheets):
        self.worksheets = worksheets


@pytest.mark.unit
def test_xlsx_missing_file(tmp_path):
    """Should raise FileNotFoundError when file does not exist."""
    ex = XlsxExtractor()
    p = tmp_path / "nope.xlsx"
    with pytest.raises(FileNotFoundError):
        ex.extract_blocks(p)


@pytest.mark.unit
def test_xlsx_single_sheet_with_values(monkeypatch, tmp_path):
    """Non-empty worksheet produces a single table block with stringified values."""
    # create an actual file path so Path.exists() is True
    p = tmp_path / "wb.xlsx"
    p.write_text("dummy")

    ws = FakeWS(rows=[(1, "a"), (None, 2.5)], title="Data")
    fake_wb = FakeWB([ws])

    monkeypatch.setattr("extractors.extract_xlsx.load_workbook", lambda filename, data_only, read_only: fake_wb)

    ex = XlsxExtractor()
    blocks = ex.extract_blocks(p)

    assert isinstance(blocks, list)
    assert len(blocks) == 1
    blk = blocks[0]
    assert blk["type"] == "table"
    assert blk["sheet"] == "Data"
    # values converted to strings; None -> ""
    assert blk["table"] == [["1", "a"], ["", "2.5"]]


@pytest.mark.unit
def test_xlsx_empty_sheet_skipped(monkeypatch, tmp_path):
    """Worksheets that are entirely empty should be skipped."""
    p = tmp_path / "wb2.xlsx"
    p.write_text("dummy")

    empty_ws = FakeWS(rows=[(None, None)], title="Empty")
    fake_wb = FakeWB([empty_ws])

    monkeypatch.setattr("extractors.extract_xlsx.load_workbook", lambda filename, data_only, read_only: fake_wb)

    ex = XlsxExtractor()
    blocks = ex.extract_blocks(p)

    # no blocks because the only sheet is empty
    assert blocks == []


@pytest.mark.unit
def test_xlsx_multiple_sheets_mixed(monkeypatch, tmp_path):
    """Only non-empty worksheets are returned, preserving order."""
    p = tmp_path / "wb3.xlsx"
    p.write_text("dummy")

    ws_empty = FakeWS(rows=[(None, None)], title="E1")
    ws_nonempty = FakeWS(rows=[("x",)], title="NotEmpty")
    ws_also_nonempty = FakeWS(rows=[(0, None)], title="Also")

    fake_wb = FakeWB([ws_empty, ws_nonempty, ws_also_nonempty])

    monkeypatch.setattr("extractors.extract_xlsx.load_workbook", lambda filename, data_only, read_only: fake_wb)

    ex = XlsxExtractor()
    blocks = ex.extract_blocks(p)

    assert len(blocks) == 2
    assert [b["sheet"] for b in blocks] == ["NotEmpty", "Also"]
    assert blocks[0]["table"] == [["x"]]
    assert blocks[1]["table"] == [["0", ""]]


@pytest.mark.unit
def test_xlsx_extractor_class_wrapper(monkeypatch, tmp_path):
    """XlsxExtractor.extract_blocks is callable via instance and returns expected blocks."""
    p = tmp_path / "wb4.xlsx"
    p.write_text("dummy")
    ws = FakeWS(rows=[("val",)], title="SheetA")
    fake_wb = FakeWB([ws])
    monkeypatch.setattr("extractors.extract_xlsx.load_workbook", lambda filename, data_only, read_only: fake_wb)

    ex = XlsxExtractor()
    res = ex.extract_blocks(p)
    assert isinstance(res, list)
    assert res[0]["sheet"] == "SheetA"
    assert res[0]["table"] == [["val"]]
