import pytest
import tkinter as tk
from gui.gui import AppGUI
from helpers.processing import ProcessLogic
from main import main

@pytest.fixture
def app():
    """Fixture to initialize the main application for testing."""
    root = tk.Tk()
    process_logic = ProcessLogic()
    app = AppGUI(root, process_logic)
    yield app
    root.destroy()  # Clean up after the test

def test_app_initialization(app):
    """Test if the AppGUI initializes without errors."""
    assert app is not None


def test_main_function(monkeypatch):
    """Test the main function to ensure it initializes the app."""

    def mock_mainloop(self):
        pass  # Zapobiega uruchomieniu GUI

    monkeypatch.setattr(tk.Tk, "mainloop", mock_mainloop)

    root = tk.Tk()
    monkeypatch.setattr(tk, "Tk", lambda: root)  # Podstawia mockowane okno
    main()

    assert root.title() == "Document Dependency Mapper"

def test_gui_components(app):
    """Ensure all key GUI components are initialized."""
    assert hasattr(app, "covered_threshold_entry"), "Missing threshold entry field"
    assert hasattr(app, "problematic_threshold_entry"), "Missing problematic threshold field"
    assert hasattr(app, "report_text_widget"), "Missing report text widget"
