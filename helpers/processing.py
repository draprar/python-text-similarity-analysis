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

    # Function to generate analysis report
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
            file_types = [("HTML Files", "*.html"), ("PDF Files", "*.pdf")]
            file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=file_types)
            if not file_path:
                messagebox.showinfo("Cancelled", "Report generation cancelled by user.")
                return

            # Calculate similarity results
            results = calculate_similarity(main_document_path, helper_documents_paths)

            # Initialize summary stats
            total_sentences = len(results)
            covered_count = sum(1 for _, max_sim, _ in results if max_sim >= self.covered_threshold)
            problematic_count = sum(1 for _, max_sim, _ in results if max_sim < self.covered_threshold)
            mapped_count = sum(1 for _, max_sim, _ in results if max_sim > 0)

            # Generate sentence labels
            sentence_labels = {result[0]: f"S{i + 1}" for i, result in enumerate(results)}

            # Read reviewed sentences from the log file
            reviewed_sentences = set()
            with open(review_log_file, "r", encoding="utf-8") as log:
                for line in log.readlines()[1:]:
                    reviewed_sentences.add(line.split(" - ")[0].strip())

            # Prepare the HTML report
            html_report = "<html><head>"
            html_report += "<style>.collapsible {cursor: pointer; padding: 10px; border: 1px solid #ccc;}</style>"
            html_report += "<script>"
            html_report += "function toggleVisibility(id) { var x = document.getElementById(id); x.style.display = x.style.display === 'none' ? 'block' : 'none'; }"
            html_report += "</script>"
            html_report += "</head><body>"
            html_report += "<h1>Document Analysis Report</h1>"

            # Add Summary Section
            html_report += "<div class='collapsible' onclick='toggleVisibility(\"summary\")'>Summary Statistics</div>"
            html_report += "<div id='summary' style='display:none;'>"
            html_report += f"<p>Total Sentences: {total_sentences}</p>"
            html_report += f"<p>Mapped: {mapped_count} ({(mapped_count / total_sentences) * 100:.2f}%)</p>"
            html_report += f"<p>Covered: {covered_count} ({(covered_count / total_sentences) * 100:.2f}%)</p>"
            html_report += f"<p>Problematic: {problematic_count} ({(problematic_count / total_sentences) * 100:.2f}%)</p>"
            html_report += "</div>"

            # Add Sentence Analysis Section
            plain_text_report = "Document Analysis Report\n"
            plain_text_report += "Summary Statistics:\n"
            plain_text_report += f"- Total Sentences: {total_sentences}\n"
            plain_text_report += f"- Mapped: {mapped_count} ({(mapped_count / total_sentences) * 100:.2f}%)\n"
            plain_text_report += f"- Covered: {covered_count} ({(covered_count / total_sentences) * 100:.2f}%)\n"
            plain_text_report += f"- Problematic: {problematic_count} ({(problematic_count / total_sentences) * 100:.2f}%)\n\n"

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

                # Check if the sentence was reviewed
                reviewed_status = "(Reviewed)" if sentence in reviewed_sentences else ""

                # Analyze sentence for ambiguity
                analysis = analyze_sentence(sentence)
                ambiguity = analysis.get("ambiguity", "N/A")

                # Write sentence details to HTML report
                label_with_id = f"{sentence_labels[sentence]}: {label}"
                html_report += f"<p style='color:{color};'>{label_with_id} ({max_sim:.2f}): {sentence} {reviewed_status}"
                html_report += f"<br><strong>Ambiguity:</strong> {ambiguity}"

                # Add sentence details to plain text report
                plain_text_report += f"{label_with_id} ({max_sim:.2f}): {sentence} {reviewed_status}\n"
                plain_text_report += f"  - Ambiguity: {ambiguity}\n"

                if best_matches:
                    html_report += "<details><summary>View Matches</summary><ul>"
                    plain_text_report += "  Matches:\n"
                    for match_sentence, source, sim in best_matches:
                        html_report += f"<li>({sim:.2f}) {match_sentence} <br>Source: {source}</li>"
                        plain_text_report += f"    - ({sim:.2f}) {match_sentence} (Source: {source})\n"
                    html_report += "</ul></details>"

                plain_text_report += "\n"

                # Update the review log for unreviewed sentences
                if sentence not in reviewed_sentences:
                    update_review_log(sentence, action)

            # Generate dependency graph
            graph_image_path = "assets/dependency_graph.png"
            create_dependency_graph(results, sentence_labels, graph_image_path)

            # Add a note to the plain text report
            plain_text_report += "\nDependency Graph:\n"
            plain_text_report += f"[Graph saved at {graph_image_path}]"

            # Embed the graph in the HTML report
            html_report += "<h2>Dependency Graph</h2>"
            html_report += f"<img src='{graph_image_path}' alt='Dependency Graph'>"

            html_report += "</div>"
            html_report += "</body></html>"

            # Save the report
            if file_path.endswith(".html"):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_report)
            elif file_path.endswith(".pdf"):
                from weasyprint import HTML
                HTML(string=html_report).write_pdf(file_path)

            # Display the plain text report in the GUI
            if text_widget:
                text_widget.delete("1.0", tk.END)
                text_widget.insert(tk.END, plain_text_report)

            # Notify user of success
            messagebox.showinfo("Success", f"Report saved as {file_path}")

        except Exception as e:
            # Log the error with detailed information
            logging.error(f"Error generating report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {e}")

        return html_report