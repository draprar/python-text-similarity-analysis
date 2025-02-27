import logging
import re
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from helpers.calculate_similarity import calculate_similarity
from helpers.config import REVIEW_LOG_FILE, DEPENDENCY_GRAPH_PATH
from helpers.dependency_graph import create_dependency_graph


class ProcessLogic:
    """
    Handles the core processing logic for text similarity analysis,
    including threshold settings, report generation, and dependency graph creation.
    """

    def __init__(self):
        """Initialize default similarity thresholds."""
        self.covered_threshold = 0.7  # Default threshold for 'covered' similarity
        self.problematic_threshold = 0.3  # Default threshold for 'problematic' similarity

    def set_thresholds(self, covered: float, problematic: float):
        """
        Sets user-defined similarity thresholds.

        Args:
            covered (float): Threshold for sentences to be considered 'covered'.
            problematic (float): Threshold below which sentences are 'problematic'.
        """
        self.covered_threshold = covered
        self.problematic_threshold = problematic

    @staticmethod
    def strip_html_tags(html: str) -> str:
        """
        Removes HTML tags from a given string.

        Args:
            html (str): Input string with HTML tags.

        Returns:
            str: Cleaned string without HTML tags.
        """
        return re.sub(r'<.*?>', '', html)

    def generate_report(self, main_document_path: str, helper_documents_paths: list, text_widget=None) -> str:
        """
        Generates a report based on text similarity analysis and updates the GUI.

        Args:
            main_document_path (str): Path to the main document.
            helper_documents_paths (list): List of paths to helper documents.
            text_widget (tk.Text, optional): GUI text widget to display report results.

        Returns:
            str: Plain text version of the report.
        """
        if not main_document_path:
            messagebox.showerror("Error", "Main document is not selected!")
            return
        if not helper_documents_paths:
            messagebox.showerror("Error", "No helper documents are selected!")
            return

        try:
            file_path = self.prompt_save_report()
            if not file_path:
                return

            # Perform similarity analysis
            results = calculate_similarity(main_document_path, helper_documents_paths)
            summary_stats = self.calculate_summary_stats(results)
            sentence_labels = self.generate_sentence_labels(results)

            # Generate reports
            html_report = self.generate_html_report(results, summary_stats, sentence_labels)
            plain_text_report = self.generate_plain_text_report(results, summary_stats, sentence_labels)

            # Save report
            self.save_report(file_path, html_report)

            # Display results in the GUI if applicable
            if text_widget and plain_text_report:
                self.display_report_in_gui(text_widget, plain_text_report)

            # Ensure old dependency graph is removed before regenerating
            if os.path.exists(DEPENDENCY_GRAPH_PATH):
                os.remove(DEPENDENCY_GRAPH_PATH)

            create_dependency_graph(results, sentence_labels)

            messagebox.showinfo("Success", f"Report saved as {file_path}")
            return plain_text_report
        except Exception as e:
            logging.error(f"Failed to generate report: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    @staticmethod
    def generate_html_report(results: list, summary_stats: dict, sentence_labels: dict) -> str:
        """
        Generates an HTML-formatted analysis report.

        Args:
            results (list): List of analyzed sentences and their similarity scores.
            summary_stats (dict): Summary statistics of the analysis.
            sentence_labels (dict): Mapping of sentences to unique labels.

        Returns:
            str: HTML-formatted report string.
        """
        report = f"""
        <html><head><title>Document Analysis Report</title></head><body>
        <h1>Document Analysis Report</h1>
        <p>Total Sentences: {summary_stats['total']}</p>
        <p>Mapped Sentences: {summary_stats['mapped']} ({(summary_stats['mapped'] / summary_stats['total']) * 100:.2f}%)</p>
        <p>Covered Sentences: {summary_stats['covered']} ({(summary_stats['covered'] / summary_stats['total']) * 100:.2f}%)</p>
        <p>Problematic Sentences: {summary_stats['problematic']} ({(summary_stats['problematic'] / summary_stats['total']) * 100:.2f}%)</p>
        <h2>Detailed Sentence Analysis</h2>
        """
        for sentence, max_sim, best_matches in results:
            label = sentence_labels.get(sentence, "Unknown")
            report += f"<p><b>{label}:</b> {sentence} (Similarity: {max_sim:.2f})</p>"
            if best_matches:
                report += "<ul>"
                for match_sentence, doc, sim in best_matches:
                    report += f"<li>{match_sentence} (from {doc}, Sim: {sim:.2f})</li>"
                report += "</ul>"
        report += "</body></html>"
        return report

    def generate_data_for_report(self, main_document_path: str, helper_documents_paths: list):
        """
        Generates processed data for report creation.

        Args:
            main_document_path (str): Path to the main document.
            helper_documents_paths (list): List of paths to helper documents.

        Returns:
            tuple: (results, summary_stats, sentence_labels)
        """
        results = calculate_similarity(main_document_path, helper_documents_paths)
        summary_stats = self.calculate_summary_stats(results)
        sentence_labels = self.generate_sentence_labels(results)
        return results, summary_stats, sentence_labels

    @staticmethod
    def generate_plain_text_report(results: list, summary_stats: dict, sentence_labels: dict) -> str:
        """
        Generates a plain-text version of the analysis report.

        Args:
            results (list): List of analyzed sentences and their similarity scores.
            summary_stats (dict): Summary statistics of the analysis.
            sentence_labels (dict): Mapping of sentences to unique labels.

        Returns:
            str: Plain text report.
        """
        report = [
            "Document Analysis Report",
            "=========================",
            f"Total Sentences: {summary_stats['total']}",
            f"Mapped Sentences: {summary_stats['mapped']} ({(summary_stats['mapped'] / summary_stats['total']) * 100:.2f}%)",
            f"Covered Sentences: {summary_stats['covered']} ({(summary_stats['covered'] / summary_stats['total']) * 100:.2f}%)",
            f"Problematic Sentences: {summary_stats['problematic']} ({(summary_stats['problematic'] / summary_stats['total']) * 100:.2f}%)",
            "\nDetailed Sentence Analysis:",
        ]
        for sentence, max_sim, best_matches in results:
            label = sentence_labels.get(sentence, "Unknown")
            migration_score = "Safe" if max_sim >= 0.8 else "Warning" if max_sim >= 0.4 else "Danger"
            report.append(f"{label}: {sentence} (Similarity: {max_sim:.2f}, Score: {migration_score})")
            for match_sentence, doc, sim in best_matches:
                report.append(f"  - Matched: {match_sentence} (from {doc}, Sim: {sim:.2f})")
        return "\n".join(report)

    @staticmethod
    def prompt_save_report() -> str:
        """Prompts the user to select a location for saving the report."""
        return filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML Files", "*.html")])

    def calculate_summary_stats(self, results: list) -> dict:
        """
        Computes summary statistics for the analysis.

        Args:
            results (list): List of analyzed sentence data.

        Returns:
            dict: Summary of total, mapped, covered, and problematic sentences.
        """
        total_sentences = len(results)
        covered_count = sum(1 for _, max_sim, _ in results if max_sim >= self.covered_threshold)
        problematic_count = sum(1 for _, max_sim, _ in results if max_sim < self.covered_threshold)
        mapped_count = sum(1 for _, max_sim, _ in results if max_sim > 0)
        return {"total": total_sentences, "covered": covered_count, "problematic": problematic_count,
                "mapped": mapped_count}

    @staticmethod
    def generate_sentence_labels(results: list) -> dict:
        """Generates unique labels for each analyzed sentence."""
        return {result[0]: f"S{i + 1}" for i, result in enumerate(results)}

    @staticmethod
    def save_report(file_path: str, html_report: str):
        """Saves the HTML report to the specified file path."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html_report)
        except Exception as e:
            logging.error(f"Error saving report: {e}")

    @staticmethod
    def display_report_in_gui(text_widget: tk.Text, plain_text_report: str):
        """Displays the plain text report in the provided GUI text widget."""
        if plain_text_report:
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, plain_text_report)
