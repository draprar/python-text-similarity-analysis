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


def test_update_review_log_error_handling(monkeypatch):
    """Test error handling when file writing fails."""

    def mock_open(*args, **kwargs):
        raise IOError("Simulated file error")

    monkeypatch.setattr("builtins.open", mock_open)

    try:
        update_review_log("Test", "KEEP")
    except Exception:
        pytest.fail("update_review_log() should handle exceptions gracefully")
