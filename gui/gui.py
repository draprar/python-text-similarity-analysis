import ttkbootstrap as ttk
import tkinter as tk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askopenfilenames
from PIL import Image, ImageTk
import threading

from helpers.config import DEPENDENCY_GRAPH_PATH


class AppGUI:
    """
    The main graphical user interface (GUI) for the Document Dependency Mapper.
    Handles document selection, threshold settings, analysis execution, and results display.
    """

    def __init__(self, root, process_logic):
        """
        Initialize the main application window.

        Args:
            root (tk.Tk): The root window for the application.
            process_logic (ProcessLogic): The backend logic for text similarity processing.
        """
        self.root = root
        self.process_logic = process_logic
        self.main_document_path = None
        self.helper_documents_paths = []

        self.covered_threshold_entry = None
        self.problematic_threshold_entry = None
        self.report_text_widget = None

        self.create_widgets()

    def create_widgets(self):
        """Create and layout all GUI widgets in the application."""
        # Document Loading Section
        file_frame = ttk.LabelFrame(self.root, text="Load Documents", padding=(10, 10))
        file_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(file_frame, text="Load Main Document", command=self.load_main_document).pack(side=LEFT, padx=5)
        ttk.Button(file_frame, text="Load Helper Documents", command=self.load_helper_documents).pack(side=LEFT, padx=5)

        # Threshold Inputs Section
        threshold_frame = ttk.LabelFrame(self.root, text="Set Thresholds", padding=(10, 10))
        threshold_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(threshold_frame, text="Covered Threshold:").grid(row=0, column=0, padx=5, pady=5)
        self.covered_threshold_entry = ttk.Entry(threshold_frame)
        self.covered_threshold_entry.insert(0, "0.7")  # Default value
        self.covered_threshold_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(threshold_frame, text="Problematic Threshold:").grid(row=1, column=0, padx=5, pady=5)
        self.problematic_threshold_entry = ttk.Entry(threshold_frame)
        self.problematic_threshold_entry.insert(0, "0.3")  # Default value
        self.problematic_threshold_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(threshold_frame, text="Set Thresholds", command=self.set_thresholds).grid(
            row=2, column=0, columnspan=2, pady=10
        )

        # Report Output Section
        report_frame = ttk.LabelFrame(self.root, text="Analysis Results", padding=(10, 10))
        report_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

        self.report_text_widget = ScrolledText(report_frame, wrap="word", width=100, height=30)
        self.report_text_widget.pack(padx=10, pady=10, fill=BOTH, expand=True)

        # Action Buttons Section
        button_frame = ttk.Frame(self.root)
        button_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(button_frame, text="Generate Report", command=self.run_report_thread).pack(side=RIGHT, padx=5)
        ttk.Button(button_frame, text="Quit", command=self.root.quit).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Show Dependency Graph", command=self.show_dependency_graph).pack(side=LEFT,
                                                                                                        padx=5)

    def run_report_thread(self):
        """Runs report generation in a separate thread to prevent GUI freezing."""
        threading.Thread(target=self.generate_report, daemon=True).start()

    def generate_report(self):
        """Generate and display the analysis report asynchronously."""
        if not self.main_document_path or not self.helper_documents_paths:
            self.root.after(0,
                            lambda: Messagebox.show_error("Error", "Please load the main and helper documents first."))
            return

        try:
            result, summary_stats, sentence_labels = self.process_logic.generate_data_for_report(
                self.main_document_path,
                self.helper_documents_paths
            )
            report_text = self.process_logic.generate_plain_text_report(result, summary_stats, sentence_labels)

            self.root.after(0, lambda: self.report_text_widget.delete("1.0", "end"))
            self.root.after(0, lambda: self.report_text_widget.insert("end", report_text))
            self.root.after(0, lambda: Messagebox.show_info("Success", "Report generated successfully!"))

        except Exception as e:
            self.root.after(0, lambda: Messagebox.show_error("Error", f"Failed to generate report: {e}"))

    def set_thresholds(self):
        """Set user-defined thresholds for analysis."""
        try:
            covered = float(self.covered_threshold_entry.get())
            problematic = float(self.problematic_threshold_entry.get())
            self.process_logic.set_thresholds(covered, problematic)
            self.root.after(0, lambda: Messagebox.show_info("Thresholds Set", "Thresholds updated successfully!"))
        except ValueError:
            self.root.after(0, lambda: Messagebox.show_error("Error", "Invalid thresholds! Please enter numbers."))

    def load_main_document(self):
        """Opens a file dialog for selecting the main document."""
        self.main_document_path = askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if self.main_document_path:
            self.root.after(0,
                            lambda: Messagebox.show_info("Main Document Loaded", f"Loaded: {self.main_document_path}"))

    def load_helper_documents(self):
        """Opens a file dialog for selecting helper documents."""
        self.helper_documents_paths = askopenfilenames(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if self.helper_documents_paths:
            self.root.after(0, lambda: Messagebox.show_info("Helper Documents Loaded",
                                                            f"Loaded {len(self.helper_documents_paths)} documents."))

    def show_dependency_graph(self):
        """Displays the generated dependency graph in a new window."""
        try:
            graph_window = tk.Toplevel(self.root)
            graph_window.title("Dependency Graph")
            img = Image.open(DEPENDENCY_GRAPH_PATH)
            tk_img = ImageTk.PhotoImage(img)
            label = ttk.Label(graph_window, image=tk_img)
            label.image = tk_img
            label.pack()
        except Exception as e:
            self.root.after(0, lambda: Messagebox.show_error("Error", f"Failed to display dependency graph: {e}"))

    @staticmethod
    def calculate_migration_score(similarity_score):
        if similarity_score >= 0.8:
            return "Safe"
        elif similarity_score >= 0.4:
            return "Warning"
        else:
            return "Danger"
