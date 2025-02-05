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
        pass  # Prevents the actual GUI from running

    monkeypatch.setattr(tk.Tk, "mainloop", mock_mainloop)  # Mock the GUI loop

    main()  # Run the main function to see if it executes properly

