import logging
import re
import os
import tkinter as tk
import matplotlib.pyplot as plt
from tkinter import messagebox, filedialog
from helpers.calculate_similarity import calculate_similarity
from helpers.config import ASSETS_DIR, DEPENDENCY_GRAPH_PATH
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
    def generate_dependency_graph(results, sentence_labels):
        """Generates a dependency graph and saves it as an image."""
        try:
            graph_path = os.path.join(ASSETS_DIR, "dependency_graph.png")
            create_dependency_graph(results, sentence_labels, graph_path)
            return graph_path
        except Exception as e:
            logging.error(f"Failed to generate dependency graph: {e}")
            return None

    @staticmethod
    def generate_pie_chart(summary_stats):
        """Generates a pie chart visualization of sentence categorization and saves it as an image."""
        try:
            labels = ["Covered", "Problematic", "Mapped"]
            values = [summary_stats["covered"], summary_stats["problematic"], summary_stats["mapped"]]
            colors = ["#4CAF50", "#FF5722", "#2196F3"]  # Green, Red, Blue

            plt.figure(figsize=(6, 6))
            plt.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140)
            plt.title("Sentence Categorization")

            chart_path = os.path.join(ASSETS_DIR, "sentence_pie_chart.png")
            plt.savefig(chart_path)
            plt.close()

            return chart_path
        except Exception as e:
            logging.error(f"Failed to generate pie chart: {e}")
            return None

    @staticmethod
    def generate_match_distribution_chart(results):
        """Generates a histogram of sentence match counts."""
        try:
            labels = [f"S{i + 1}" for i in range(len(results))]
            match_counts = [len(matches) for _, _, matches in results]

            plt.figure(figsize=(8, 5))
            plt.bar(labels, match_counts, color="skyblue")
            plt.xlabel("Sentence")
            plt.ylabel("Number of Matches")
            plt.title("Sentence Match Distribution")

            match_chart_path = os.path.join(ASSETS_DIR, "match_distribution.png")
            plt.savefig(match_chart_path)
            plt.close()

            return match_chart_path
        except Exception as e:
            logging.error(f"Failed to generate match distribution chart: {e}")
            return None

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
        """Generates a report based on text similarity analysis and updates the GUI."""
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

            chart_path = self.generate_pie_chart(summary_stats)
            match_chart_path = self.generate_match_distribution_chart(results)
            graph_path = self.generate_dependency_graph(results, sentence_labels)

            html_report = self.generate_html_report(results, summary_stats, sentence_labels, chart_path, match_chart_path, graph_path)
            plain_text_report = self.generate_plain_text_report(results, summary_stats, sentence_labels)

            self.save_report(file_path, html_report)

            if text_widget and plain_text_report:
                self.display_report_in_gui(text_widget, plain_text_report)

            messagebox.showinfo("Success", f"Report saved as {file_path}")
            return plain_text_report
        except Exception as e:
            logging.error(f"Failed to generate report: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    @staticmethod
    def generate_html_report(results, summary_stats, sentence_labels, chart_path, match_chart_path, graph_path):
        """
        Generates an improved HTML-formatted analysis report.
        """
        report = f"""
        <html>
        <head>
            <title>Document Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f4; }}
                h1, h2 {{ color: #333; }}
                .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px #ccc; }}
                .summary {{ font-size: 16px; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #007BFF; color: white; }}
                .safe {{ background-color: #c8e6c9; }} /* Zielony */
                .warning {{ background-color: #fff9c4; }} /* Żółty */
                .danger {{ background-color: #ffcdd2; }} /* Czerwony */
                .visualization-container {{ display: flex; justify-content: space-around; gap: 20px; flex-wrap: wrap; }}
                .visualization img {{ width: 300px; height: auto; cursor: pointer; transition: transform 0.2s ease-in-out; }}
                .visualization img:hover {{ transform: scale(1.05); }}
                .popup {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); justify-content: center; align-items: center; }}
                .popup img {{ max-width: 90%; max-height: 90%; border: 5px solid white; border-radius: 8px; }}
            </style>
            <script>
                function openImage(src) {{
                    document.getElementById("popup-image").src = src;
                    document.getElementById("image-popup").style.display = "flex";
                }}
                function closeImage() {{
                    document.getElementById("image-popup").style.display = "none";
                }}
            </script>
            </style>
        </head>
        <body>
            <div class='container'>
                <h1>Document Analysis Report</h1>

                <h2>Summary</h2>
                <p class='summary'>Total Sentences: {summary_stats['total']}</p>
                <p class='summary'>Mapped Sentences: {summary_stats['mapped']} ({(summary_stats['mapped'] / summary_stats['total']) * 100:.2f}%)</p>
                <p class='summary'>Covered Sentences: {summary_stats['covered']} ({(summary_stats['covered'] / summary_stats['total']) * 100:.2f}%)</p>
                <p class='summary'>Problematic Sentences: {summary_stats['problematic']} ({(summary_stats['problematic'] / summary_stats['total']) * 100:.2f}%)</p>
                <h2>Visualizations</h2>
                <div class="visualization-container">
        """

        if chart_path:
            report += f"""
                    <div class="visualization">
                        <h3>Sentence Categorization</h3>
                        <img src="{chart_path}" alt="Sentence Categorization" onclick="openImage(this.src)">
                    </div>
                """
        if match_chart_path:
            report += f"""
                    <div class="visualization">
                        <h3>Sentence Match Distribution</h3>
                        <img src="{match_chart_path}" alt="Match Distribution" onclick="openImage(this.src)">
                    </div>
                """
        if graph_path:
            report += f"""
                    <div class="visualization">
                        <h3>Dependency Graph</h3>
                        <img src="{graph_path}" alt="Dependency Graph" onclick="openImage(this.src)">
                    </div>
                    """

        report += """
                </div>
                
                <h2>Thresholds Used</h2>
                <p><strong>Covered Threshold:</strong> ≥ 0.7 (Green)</p>
                <p><strong>Problematic Threshold:</strong> ≤ 0.3 (Red)</p>

                <h2>Detailed Sentence Analysis</h2>
                <table>
                    <tr>
                        <th>Sentence</th>
                        <th>Similarity</th>
                        <th>Matched Sentences</th>
                    </tr>
        """

        for sentence, max_sim, best_matches in results:
            label = sentence_labels.get(sentence, "Unknown")
            row_class = "safe" if max_sim >= 0.7 else "warning" if max_sim >= 0.3 else "danger"

            report += f"""
                    <tr class="{row_class}">
                        <td><b>{label}:</b> {sentence}</td>
                        <td>{max_sim:.2f}</td>
                        <td>
                            <ul>
            """

            for match_sentence, doc, sim in best_matches:
                report += f"<li>{match_sentence} (from {doc}, Sim: {sim:.2f})</li>"

            report += """
                            </ul>
                        </td>
                    </tr>
            """

        report += """
                </table>
                <div id="image-popup" class="popup" onclick="closeImage()">
                    <img id="popup-image">
                </div>
            </div>
        </body>
        </html>
        """

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
            report.append(f"{label}: {sentence} (Similarity: {max_sim:.2f})")
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
