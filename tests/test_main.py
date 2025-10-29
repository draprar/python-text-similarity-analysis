import pytest
import sys
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

sys.path.append(str(Path(__file__).resolve().parents[2]))

import main


# --- ARGUMENT PARSING ---

@pytest.mark.unit
def test_parse_args_basic(monkeypatch):
    """Ensure command-line arguments are parsed correctly with defaults."""
    test_args = ["prog", "old.docx", "new.docx"]
    monkeypatch.setattr(sys, "argv", test_args)
    args = main.parse_args()
    assert args.old == Path("old.docx")
    assert args.new == Path("new.docx")
    assert args.output == Path("report.html")  # default value


# --- LOGGING SETUP ---

@pytest.mark.unit
def test_setup_logging_sets_correct_level(caplog):
    """Verify that setup_logging allows capturing DEBUG messages when verbose=True."""
    with caplog.at_level(logging.DEBUG):
        main.setup_logging(verbose=True)
        logging.debug("debug message")
    assert any("debug message" in r.message for r in caplog.records)


# --- EXTRACTOR SELECTION ---

@pytest.mark.unit
@pytest.mark.parametrize(
    "ext, expected_cls",
    [
        (".docx", main.DocxExtractor),
        (".doc", main.DocxExtractor),
        (".txt", main.TxtExtractor),
        (".xlsx", main.XlsxExtractor),
    ],
)
def test_choose_extractor_valid(ext, expected_cls, tmp_path):
    """Ensure correct extractor class is chosen based on file extension."""
    f = tmp_path / f"file{ext}"
    f.touch()
    ex = main.choose_extractor(f)
    assert isinstance(ex, expected_cls)


@pytest.mark.unit
def test_choose_extractor_invalid(tmp_path):
    """Verify that unsupported extensions raise ValueError."""
    f = tmp_path / "file.pdf"
    f.touch()
    with pytest.raises(ValueError):
        main.choose_extractor(f)


# --- MAIN FUNCTION: FILE EXISTENCE ERRORS ---

@pytest.mark.unit
def test_main_returns_old_not_found(monkeypatch, tmp_path):
    """Return OLD_NOT_FOUND if the old file does not exist."""
    fake_new = tmp_path / "new.txt"
    fake_new.write_text("abc")

    args = SimpleNamespace(old=tmp_path / "old.txt", new=fake_new, output="x.html", json=None, verbose=False)
    monkeypatch.setattr(main, "parse_args", lambda: args)

    code = main.main()
    assert code == main.ExitCode.OLD_NOT_FOUND


@pytest.mark.unit
def test_main_returns_new_not_found(monkeypatch, tmp_path):
    """Return NEW_NOT_FOUND if the new file does not exist."""
    fake_old = tmp_path / "old.txt"
    fake_old.write_text("abc")

    args = SimpleNamespace(old=fake_old, new=tmp_path / "new.txt", output="x.html", json=None, verbose=False)
    monkeypatch.setattr(main, "parse_args", lambda: args)

    code = main.main()
    assert code == main.ExitCode.NEW_NOT_FOUND


# --- MAIN FUNCTION: PARSE / HTML / JSON ERRORS ---

@pytest.mark.unit
def test_main_parse_error(monkeypatch, tmp_path):
    """Return PARSE_ERROR if any extractor raises an exception while reading files."""
    fake_old = tmp_path / "old.txt"
    fake_new = tmp_path / "new.txt"
    fake_old.write_text("x")
    fake_new.write_text("y")

    args = SimpleNamespace(old=fake_old, new=fake_new, output="x.html", json=None, verbose=False)
    monkeypatch.setattr(main, "parse_args", lambda: args)
    monkeypatch.setattr(main, "choose_extractor", lambda path: MagicMock(extract_blocks=MagicMock(side_effect=Exception("boom"))))

    code = main.main()
    assert code == main.ExitCode.PARSE_ERROR


@pytest.mark.unit
def test_main_html_error(monkeypatch, tmp_path):
    """Return HTML_ERROR if generating the HTML report fails."""
    fake_old = tmp_path / "old.txt"
    fake_new = tmp_path / "new.txt"
    fake_old.write_text("x")
    fake_new.write_text("y")

    args = SimpleNamespace(old=fake_old, new=fake_new, output="x.html", json=None, verbose=False)
    monkeypatch.setattr(main, "parse_args", lambda: args)

    fake_extractor = MagicMock()
    fake_extractor.extract_blocks.return_value = [{"type": "paragraph", "text": "ok"}]
    monkeypatch.setattr(main, "choose_extractor", lambda p: fake_extractor)
    monkeypatch.setattr(main, "compare_blocks", lambda o, n: ["diff"])
    monkeypatch.setattr(main, "generate_html_report", MagicMock(side_effect=Exception("save error")))

    code = main.main()
    assert code == main.ExitCode.HTML_ERROR


@pytest.mark.unit
def test_main_json_error(monkeypatch, tmp_path):
    """Return JSON_ERROR if JSON report generation fails."""
    fake_old = tmp_path / "old.txt"
    fake_new = tmp_path / "new.txt"
    fake_old.write_text("x")
    fake_new.write_text("y")

    fake_json = tmp_path / "out.json"

    args = SimpleNamespace(old=fake_old, new=fake_new, output="x.html", json=fake_json, verbose=False)
    monkeypatch.setattr(main, "parse_args", lambda: args)

    fake_extractor = MagicMock()
    fake_extractor.extract_blocks.return_value = [{"type": "paragraph", "text": "ok"}]
    monkeypatch.setattr(main, "choose_extractor", lambda p: fake_extractor)
    monkeypatch.setattr(main, "compare_blocks", lambda o, n: ["diff"])
    monkeypatch.setattr(main, "generate_html_report", MagicMock())
    monkeypatch.setattr(main, "generate_json_report", MagicMock(side_effect=Exception("fail")))

    code = main.main()
    assert code == main.ExitCode.JSON_ERROR


# --- MAIN FUNCTION: SUCCESSFUL EXECUTION ---

@pytest.mark.unit
def test_main_ok(monkeypatch, tmp_path):
    """Return OK when both HTML and JSON reports are generated successfully."""
    fake_old = tmp_path / "old.txt"
    fake_new = tmp_path / "new.txt"
    fake_old.write_text("x")
    fake_new.write_text("y")

    fake_json = tmp_path / "out.json"

    args = SimpleNamespace(old=fake_old, new=fake_new, output="x.html", json=fake_json, verbose=True)
    monkeypatch.setattr(main, "parse_args", lambda: args)

    fake_extractor = MagicMock()
    fake_extractor.extract_blocks.return_value = [{"type": "paragraph", "text": "ok"}]
    monkeypatch.setattr(main, "choose_extractor", lambda p: fake_extractor)
    monkeypatch.setattr(main, "compare_blocks", lambda o, n: ["diff"])
    monkeypatch.setattr(main, "generate_html_report", MagicMock())
    monkeypatch.setattr(main, "generate_json_report", MagicMock())

    code = main.main()
    assert code == main.ExitCode.OK
