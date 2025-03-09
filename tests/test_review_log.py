import os
import pytest
from unittest.mock import patch
from logs.review_log import initialize_log, update_review_log


@pytest.fixture
def temp_log_file(tmp_path):
    """Creates a temporary log file and patches REVIEW_LOG_FILE properly."""
    temp_log = tmp_path / "review_log.txt"

    with patch("logs.review_log.REVIEW_LOG_FILE", str(temp_log)):  # Correct patching
        yield str(temp_log)  # Provide the temp log path to tests


def test_initialize_log(temp_log_file):
    """Test log file initialization."""
    initialize_log()
    assert os.path.exists(temp_log_file), "Log file was not created"

    with open(temp_log_file, "r", encoding="utf-8") as log:
        lines = log.readlines()

    assert lines[0].strip() == "Sentence - Action", "Log file does not contain the correct header"


def test_update_review_log(temp_log_file):
    """Test logging a sentence-action pair."""
    initialize_log()

    update_review_log("Test sentence", "KEEP")
    update_review_log("Another test", "REMOVE")

    with open(temp_log_file, "r", encoding="utf-8") as log:
        lines = log.readlines()

    assert len(lines) == 3, "Log file should contain 3 lines (header + 2 entries)"
    assert lines[1].strip() == "Test sentence - KEEP"
    assert lines[2].strip() == "Another test - REMOVE"


@patch("builtins.open", side_effect=IOError("Simulated file error"))
def test_update_review_log_error_handling(mock_open):
    """Ensure update_review_log() handles I/O errors gracefully."""
    try:
        update_review_log("Test", "KEEP")
    except Exception:
        pytest.fail("update_review_log() should handle exceptions gracefully")

    mock_open.assert_called_once()  # Sprawdź, czy open został wywołany


def test_initialize_log_existing_file(temp_log_file):
    """Ensure initialize_log() does not overwrite existing content."""
    with open(temp_log_file, "w", encoding="utf-8") as log:
        log.write("Existing data\n")

    initialize_log()

    with open(temp_log_file, "r", encoding="utf-8") as log:
        lines = log.readlines()

    assert lines[0].strip() == "Existing data", "Existing log data should not be overwritten"

def test_update_review_log_empty_entries(temp_log_file):
    """Ensure empty sentences or actions are not logged."""
    initialize_log()

    update_review_log("", "KEEP")
    update_review_log("Valid sentence", "")
    update_review_log("", "")

    with open(temp_log_file, "r", encoding="utf-8") as log:
        lines = log.readlines()

    assert len(lines) == 1, "Empty entries should not be added to the log"
