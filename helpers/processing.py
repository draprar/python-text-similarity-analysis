import logging
import re
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from helpers.calculate_similarity import calculate_similarity
from helpers.config import REVIEW_LOG_FILE, DEPENDENCY_GRAPH_PATH
from helpers.dependency_graph import create_dependency_graph

class ProcessLogic:
    def __init__(self):
        self.covered_threshold = 0.7
        self.problematic_threshold = 0.3

    def set_thresholds(self, covered, problematic):
        """Set thresholds for sentence categorization."""
        self.covered_threshold = covered
        self.problematic_threshold = problematic

    @staticmethod
    def strip_html_tags(html):
        """Helper function to remove HTML tags from a string."""
        return re.sub(r'<.*?>', '', html)

    def generate_report(self, main_document_path, helper_documents_paths, text_widget=None):
        """Generates and displays the report based on document analysis."""
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

            results = calculate_similarity(main_document_path, helper_documents_paths)
            summary_stats = self.calculate_summary_stats(results)
            sentence_labels = self.generate_sentence_labels(results)

            html_report = self.generate_html_report(results, summary_stats, sentence_labels)
            plain_text_report = self.generate_plain_text_report(results, summary_stats, sentence_labels)

            self.save_report(file_path, html_report)
            if text_widget and plain_text_report:
                self.display_report_in_gui(text_widget, plain_text_report)

            # Ensure the old graph is deleted before regenerating
            if os.path.exists(DEPENDENCY_GRAPH_PATH):
                os.remove(DEPENDENCY_GRAPH_PATH)

            create_dependency_graph(results, sentence_labels)

            messagebox.showinfo("Success", f"Report saved as {file_path}")
            return plain_text_report
        except Exception as e:
            logging.error(f"Failed to generate report: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    @staticmethod
    def generate_html_report(results, summary_stats, sentence_labels):
        """Generates an HTML version of the analysis report."""
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

    @staticmethod
    def generate_plain_text_report(results, summary_stats, sentence_labels):
        """Generates a plain-text version of the analysis report."""
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
            report.append(f"{label}: {sentence} (Similarity: {max_sim:.2f})")
            for match_sentence, doc, sim in best_matches:
                report.append(f"  - Matched: {match_sentence} (from {doc}, Sim: {sim:.2f})")
        return "\n".join(report)


    @staticmethod
    def prompt_save_report():
        """Prompts the user to select a location for saving the report."""
        return filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML Files", "*.html")])

    def calculate_summary_stats(self, results):
        """Calculates summary statistics for the analysis results."""
        total_sentences = len(results)
        covered_count = sum(1 for _, max_sim, _ in results if max_sim >= self.covered_threshold)
        problematic_count = sum(1 for _, max_sim, _ in results if max_sim < self.covered_threshold)
        mapped_count = sum(1 for _, max_sim, _ in results if max_sim > 0)
        return {"total": total_sentences, "covered": covered_count, "problematic": problematic_count, "mapped": mapped_count}

    @staticmethod
    def read_review_log():
        """Reads the review log file to get reviewed sentences."""
        try:
            with open(REVIEW_LOG_FILE, "r", encoding="utf-8") as log:
                return {line.split(" - ")[0].strip() for line in log.readlines()[1:]}
        except FileNotFoundError:
            logging.warning(f"Review log file not found: {REVIEW_LOG_FILE}")
            return set()

    @staticmethod
    def generate_sentence_labels(results):
        """Generates unique labels for each analyzed sentence."""
        return {result[0]: f"S{i + 1}" for i, result in enumerate(results)}

    @staticmethod
    def save_report(file_path, html_report):
        """Saves the HTML report to the specified file path."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html_report)
        except Exception as e:
            logging.error(f"Error saving report: {e}")

    @staticmethod
    def display_report_in_gui(text_widget, plain_text_report):
        """Displays the plain text report in the provided GUI text widget."""
        if plain_text_report:
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, plain_text_report)
