import logging

import pytest
import os
import shutil
from unittest.mock import MagicMock, patch
from tkinter import Tk, Text
from helpers.config import ASSETS_DIR
from helpers.processing import ProcessLogic


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Setup and cleanup test environment."""
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    yield  # Testy wykonują się tutaj
    shutil.rmtree(ASSETS_DIR, ignore_errors=True)


def test_set_thresholds():
    logic = ProcessLogic()
    logic.set_thresholds(0.8, 0.2)
    assert logic.covered_threshold == 0.8
    assert logic.problematic_threshold == 0.2


@patch("helpers.processing.create_dependency_graph")  # 🎯 Poprawna ścieżka
def test_generate_dependency_graph(mock_create_graph):
    logic = ProcessLogic()

    expected_path = os.path.join(ASSETS_DIR, "dependency_graph.png")
    result = logic.generate_dependency_graph({}, {})

    assert result == expected_path  # ✅ Sprawdzamy poprawną ścieżkę
    mock_create_graph.assert_called_once()  # ✅ Upewniamy się, że funkcja została wywołana


@patch("matplotlib.pyplot.savefig")
def test_generate_pie_chart(mock_savefig):
    logic = ProcessLogic()
    summary_stats = {"covered": 10, "problematic": 5, "mapped": 15}
    chart_path = logic.generate_pie_chart(summary_stats)

    expected_path = os.path.join(ASSETS_DIR, "sentence_pie_chart.png")
    assert chart_path == expected_path
    mock_savefig.assert_called_once()


@patch("matplotlib.pyplot.savefig")
def test_generate_match_distribution_chart(mock_savefig):
    logic = ProcessLogic()
    results = [("Sentence 1", 0.8, ["Match 1"]), ("Sentence 2", 0.5, ["Match 2"])]

    expected_path = os.path.join(ASSETS_DIR, "match_distribution.png")
    chart_path = logic.generate_match_distribution_chart(results)

    assert chart_path == expected_path  # ✅ Poprawna ścieżka
    mock_savefig.assert_called_once()  # ✅ Sprawdzamy czy zapisano plik


def test_strip_html_tags():
    logic = ProcessLogic()
    html = "<p>Hello <b>world</b></p>"
    clean_text = logic.strip_html_tags(html)
    assert clean_text == "Hello world"


def test_generate_sentence_labels():
    logic = ProcessLogic()
    results = [("Sentence 1", 0.8, []), ("Sentence 2", 0.5, [])]
    labels = logic.generate_sentence_labels(results)
    assert labels == {"Sentence 1": "S1", "Sentence 2": "S2"}


@patch("builtins.open", new_callable=MagicMock)
def test_save_report(mock_open, tmp_path):
    logic = ProcessLogic()
    file_path = tmp_path / "test_report.html"
    logic.save_report(str(file_path), "<html></html>")
    mock_open.assert_called_once_with(str(file_path), "w", encoding="utf-8")


def test_calculate_summary_stats():
    logic = ProcessLogic()
    results = [
        ("Sentence 1", 0.8, []),
        ("Sentence 2", 0.4, []),
        ("Sentence 3", 0.2, [])
    ]
    stats = logic.calculate_summary_stats(results)
    assert stats["total"] == 3
    assert stats["covered"] == 1
    assert stats["problematic"] == 2
    assert stats["mapped"] == 3  # Wszystkie są mapped, bo mają jakiś wynik


@patch("helpers.processing.ProcessLogic.generate_html_report", return_value="<html></html>")
@patch("helpers.processing.ProcessLogic.save_report")
@patch("helpers.processing.ProcessLogic.generate_pie_chart", return_value="chart.png")
@patch("helpers.processing.ProcessLogic.generate_match_distribution_chart", return_value="match_chart.png")
@patch("helpers.processing.ProcessLogic.generate_dependency_graph", return_value="graph.png")
def generate_report(self, main_document_path: str, helper_documents_paths: list, text_widget=None) -> str:
    logging.info("📌 Generowanie raportu...")  # 🐛 Debugging

    chart_path = self.generate_pie_chart(summary_stats)
    logging.info(f"✅ Wygenerowano pie chart: {chart_path}")  # 🐛 Debugging

    match_chart_path = self.generate_match_distribution_chart(results)
    logging.info(f"✅ Wygenerowano match chart: {match_chart_path}")  # 🐛 Debugging

    graph_path = self.generate_dependency_graph(results, sentence_labels)
    logging.info(f"✅ Wygenerowano dependency graph: {graph_path}")  # 🐛 Debugging

    logic = ProcessLogic()
    main_doc = "main.txt"
    helper_docs = ["helper1.txt", "helper2.txt"]

    with patch("helpers.processing.ProcessLogic.prompt_save_report", return_value="report.html"):
        logic.generate_report(main_doc, helper_docs)

    mock_pie_chart.assert_called_once()  # ✅ Sprawdzamy, czy wykres został wygenerowany
    mock_match_chart.assert_called_once()  # ✅ Sprawdzamy histogram
    mock_graph.assert_called_once()  # ✅ Sprawdzamy wykres zależności


def test_generate_html_report():
    logic = ProcessLogic()
    results = [("Sentence 1", 0.8, [("Match 1", "doc1.txt", 0.8)])]
    summary_stats = {"total": 1, "mapped": 1, "covered": 1, "problematic": 0}
    sentence_labels = {"Sentence 1": "S1"}
    chart_path = "chart.png"
    match_chart_path = "match_chart.png"
    graph_path = "graph.png"

    html_report = logic.generate_html_report(results, summary_stats, sentence_labels, chart_path, match_chart_path,
                                             graph_path)
    assert "<html>" in html_report
    assert "Sentence Categorization" in html_report
    assert "Dependency Graph" in html_report


def test_display_report_in_gui():
    root = Tk()
    text_widget = Text(root)
    logic = ProcessLogic()
    test_text = "This is a test report."

    logic.display_report_in_gui(text_widget, test_text)

    assert text_widget.get("1.0", "end-1c") == test_text
