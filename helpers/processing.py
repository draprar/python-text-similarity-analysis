import logging
import re
import tkinter as tk
from tkinter import messagebox, filedialog
from helpers.analyze_sentence import analyze_sentence
from helpers.calculate_similarity import calculate_similarity
from helpers.config import review_log_file
from helpers.dependency_graph import create_dependency_graph
from logs.review_log import update_review_log


class ProcessLogic:
    def __init__(self):
        self.covered_threshold = 0.7
        self.problematic_threshold = 0.3

    def set_thresholds(self, covered, problematic):
        self.covered_threshold = covered
        self.problematic_threshold = problematic

    @staticmethod
    def strip_html_tags(html):
        """Helper function to remove HTML tags from a string."""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html)

    def generate_report(self, main_document_path, helper_documents_paths, text_widget=None):
        if not main_document_path:
            messagebox.showerror("Error", "Main document is not selected!")
            return

        if not helper_documents_paths:
            messagebox.showerror("Error", "No helper documents are selected!")
            return

        try:
            # Prompt user to save the report
            file_path = self.prompt_save_report()
            if not file_path:
                return

            # Calculate similarity results
            results = calculate_similarity(main_document_path, helper_documents_paths)

            # Generate report components
            summary_stats = self.calculate_summary_stats(results)
            reviewed_sentences = self.read_review_log()
            sentence_labels = self.generate_sentence_labels(results)

            # Generate both reports
            html_report = self.generate_html_report(
                results, summary_stats, reviewed_sentences, sentence_labels
            )
            plain_text_report = self.generate_plain_text_report(
                results, summary_stats, reviewed_sentences, sentence_labels
            )

            # Save the report
            self.save_report(file_path, html_report)

            # Display the plain text report in the GUI
            if text_widget:
                self.display_report_in_gui(text_widget, plain_text_report)

            # Render dependency graph in GUI
            create_dependency_graph(results, sentence_labels, "dependency_graph_gui.png")

            # Notify user of success
            messagebox.showinfo("Success", f"Report saved as {file_path}")

        except Exception as e:
            logging.error(f"Error generating report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {e}")

        return plain_text_report

    def prompt_save_report(self):
        file_types = [("HTML Files", "*.html")]
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=file_types)
        if not file_path:
            messagebox.showinfo("Cancelled", "Report generation cancelled by user.")
        return file_path

    def calculate_summary_stats(self, results):
        total_sentences = len(results)
        covered_count = sum(1 for _, max_sim, _ in results if max_sim >= self.covered_threshold)
        problematic_count = sum(1 for _, max_sim, _ in results if max_sim < self.covered_threshold)
        mapped_count = sum(1 for _, max_sim, _ in results if max_sim > 0)
        return {
            "total": total_sentences,
            "covered": covered_count,
            "problematic": problematic_count,
            "mapped": mapped_count,
        }

    def generate_plain_text_report(self, results, summary_stats, reviewed_sentences, sentence_labels):
        """
        Generates a formatted plain text report based on the analysis results,
        summary statistics, reviewed sentences, and sentence labels.
        """
        try:
            # Debug input validation
            if not results:
                logging.error("No results provided for plain text report generation.")
                return "No results available to generate the report.\n"
            if not summary_stats:
                logging.error("No summary statistics provided for plain text report generation.")
                return "No summary statistics available to generate the report.\n"
            if not sentence_labels:
                logging.error("No sentence labels provided for plain text report generation.")
                return "No sentence labels available to generate the report.\n"

            logging.debug(f"Generating report with {len(results)} results.")
            logging.debug(f"Summary statistics: {summary_stats}")
            logging.debug(f"Number of reviewed sentences: {len(reviewed_sentences)}")
            logging.debug(f"Number of sentence labels: {len(sentence_labels)}")

            # Generate report
            plain_text_report = (
                "=========================\n"
                "Document Analysis Report\n"
                "=========================\n\n"
            )

            plain_text_report += (
                "Summary Statistics\n"
                "-------------------\n"
                f"Total Sentences: {summary_stats['total']}\n"
                f"Mapped Sentences: {summary_stats['mapped']} "
                f"({(summary_stats['mapped'] / summary_stats['total']) * 100:.2f}%)\n"
                f"Covered Sentences: {summary_stats['covered']} "
                f"({(summary_stats['covered'] / summary_stats['total']) * 100:.2f}%)\n"
                f"Problematic Sentences: {summary_stats['problematic']} "
                f"({(summary_stats['problematic'] / summary_stats['total']) * 100:.2f}%)\n\n"
            )

            # Add sentences
            plain_text_report += "Sentence-by-Sentence Analysis\n"
            plain_text_report += "-----------------------------\n"
            for sentence, max_sim, best_matches in results:
                # Validate and log each sentence
                if sentence is None or max_sim is None:
                    logging.warning(f"Invalid result entry: {sentence}, {max_sim}, {best_matches}")
                    continue

                label = (
                    "Covered" if max_sim >= self.covered_threshold
                    else "Problematic" if max_sim < self.problematic_threshold
                    else "Mapped"
                )
                reviewed_status = "Reviewed" if sentence in reviewed_sentences else "Unreviewed"
                label_id = sentence_labels.get(sentence, "Unknown")

                plain_text_report += (
                    f"\n{label_id}: {label} ({max_sim:.2f}) [{reviewed_status}]\n"
                    f"  Text: {sentence}\n"
                )

                if best_matches:
                    plain_text_report += "  Best Matches:\n"
                    for match_sentence, source, sim in best_matches:
                        plain_text_report += (
                            f"    - ({sim:.2f}) {match_sentence} [Source: {source}]\n"
                        )

            return plain_text_report

        except Exception as e:
            logging.error(f"Error in generate_plain_text_report: {e}")
            return "An error occurred while generating the plain text report.\n"

    def read_review_log(self):
        reviewed_sentences = set()
        with open(review_log_file, "r", encoding="utf-8") as log:
            for line in log.readlines()[1:]:
                reviewed_sentences.add(line.split(" - ")[0].strip())
        return reviewed_sentences

    def generate_sentence_labels(self, results):
        return {result[0]: f"S{i + 1}" for i, result in enumerate(results)}

    def generate_html_report(self, results, summary_stats, reviewed_sentences, sentence_labels):
        html_report = "<html><head>"
        html_report += "<style>.collapsible {cursor: pointer; padding: 10px; border: 1px solid #ccc;}</style>"
        html_report += "<script>"
        html_report += "function toggleVisibility(id) { var x = document.getElementById(id); x.style.display = x.style.display === 'none' ? 'block' : 'none'; }"
        html_report += "</script>"
        html_report += "</head><body>"
        html_report += "<h1>Document Analysis Report</h1>"

        # Summary Section
        html_report += "<div class='collapsible' onclick='toggleVisibility(\"summary\")'>Summary Statistics</div>"
        html_report += "<div id='summary' style='display:none;'>"
        html_report += f"<p>Total Sentences: {summary_stats['total']}</p>"
        html_report += f"<p>Mapped: {summary_stats['mapped']} ({(summary_stats['mapped'] / summary_stats['total']) * 100:.2f}%)</p>"
        html_report += f"<p>Covered: {summary_stats['covered']} ({(summary_stats['covered'] / summary_stats['total']) * 100:.2f}%)</p>"
        html_report += f"<p>Problematic: {summary_stats['problematic']} ({(summary_stats['problematic'] / summary_stats['total']) * 100:.2f}%)</p>"
        html_report += "</div>"

        # Sentence Analysis Section
        html_report += "<div class='collapsible' onclick='toggleVisibility(\"sentence_analysis\")'>Sentence-by-Sentence Analysis</div>"
        html_report += "<div id='sentence_analysis' style='display:none;'>"
        for sentence, max_sim, best_matches in results:
            # Determine the category and color
            if max_sim >= self.covered_threshold:
                color = "green"
                label = "Covered"
                action = "Merge"
            elif max_sim < self.problematic_threshold:
                color = "red"
                label = "Problematic"
                action = "Remove"
            else:
                color = "orange"
                label = "Mapped"
                action = "Review"

            reviewed_status = "(Reviewed)" if sentence in reviewed_sentences else ""
            analysis = analyze_sentence(sentence)
            ambiguity = analysis.get("ambiguity", "N/A")

            label_with_id = f"{sentence_labels[sentence]}: {label}"
            html_report += f"<p style='color:{color};'>{label_with_id} ({max_sim:.2f}): {sentence} {reviewed_status}"
            html_report += f"<br><strong>Ambiguity:</strong> {ambiguity}"

            if best_matches:
                html_report += "<details><summary>View Matches</summary><ul>"
                for match_sentence, source, sim in best_matches:
                    html_report += f"<li>({sim:.2f}) {match_sentence} <br>Source: {source}</li>"
                html_report += "</ul></details>"
            html_report += "</p>"

            if sentence not in reviewed_sentences:
                update_review_log(sentence, action)
        html_report += "</div>"

        html_report += "</body></html>"
        return html_report

    def save_report(self, file_path, html_report):
        if file_path.endswith(".html"):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_report)
        else:
            logging.error("Unsupported file format for saving report.")

    def display_report_in_gui(self, text_widget, plain_text_report):
        logging.debug(f"Displaying plain text report: {plain_text_report[:500]}")  # Debugging output
        if text_widget:
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, plain_text_report)
