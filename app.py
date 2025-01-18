import logging
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from fpdf import FPDF
from analyze_sentence import analyze_sentence
from calculate_similarity import calculate_similarity
from config import COVERED_THRESHOLD, PROBLEMATIC_THRESHOLD, review_log_file, update_review_log
from generate_recommendation import generate_recommendation

# Global variables for thresholds and file paths
covered_threshold = COVERED_THRESHOLD
problematic_threshold = PROBLEMATIC_THRESHOLD
main_document_path = None
helper_documents_paths = []

# Function to load the main document
def load_main_document():
    global main_document_path
    main_document_path = filedialog.askopenfilename(
        title="Select Main Document",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not main_document_path:
        messagebox.showerror("Error", "Main document not selected!")
    else:
        messagebox.showinfo("Main Document Loaded", f"Main document loaded: {main_document_path}")

# Function to load helper documents
def load_helper_documents():
    global helper_documents_paths
    helper_documents_paths = filedialog.askopenfilenames(
        title="Select Helper Documents",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not helper_documents_paths:
        messagebox.showerror("Error", "No helper documents selected!")
    else:
        messagebox.showinfo("Helper Documents Loaded", f"{len(helper_documents_paths)} helper documents loaded.")

# Function to set thresholds
def set_thresholds():
    global covered_threshold, problematic_threshold
    try:
        covered_threshold = float(covered_threshold_entry.get())
        problematic_threshold = float(problematic_threshold_entry.get())
        messagebox.showinfo("Thresholds Set", "Thresholds updated successfully!")
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers for thresholds.")

# Function to save the report as an HTML or PDF file
def save_report(stats_text, detailed_analysis):
    file_path = filedialog.asksaveasfilename(
        title="Save Report",
        defaultextension=".html",
        filetypes=[("HTML Files", "*.html"), ("PDF Files", "*.pdf")]
    )
    if not file_path:
        return

    try:
        if file_path.endswith(".html"):
            with open(file_path, "w") as f:
                f.write("<html><body><pre>")
                f.write(stats_text)
                f.write(detailed_analysis)
                f.write("</pre></body></html>")
        elif file_path.endswith(".pdf"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)

            for line in stats_text.split("\n"):
                pdf.multi_cell(0, 10, line)
            for line in detailed_analysis.split("\n"):
                pdf.multi_cell(0, 10, line)
            pdf.output(file_path)

        messagebox.showinfo("Success", f"Report saved successfully as {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save report: {e}")

# Function to generate analysis report
def strip_html_tags(html):
    """Helper function to remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html)

def generate_analysis_report(main_document_path=None, helper_documents_paths=None, text_widget=None):
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
        covered_count = sum(1 for _, max_sim, _ in results if max_sim >= covered_threshold)
        problematic_count = sum(1 for _, max_sim, _ in results if max_sim < covered_threshold)
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
            if max_sim >= covered_threshold:
                color = "green"
                label = "Covered"
                action = "Merge"
            elif max_sim < problematic_threshold:
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

# GUI setup
root = tk.Tk()
root.title("Sentence Analysis Tool")

# Frame for loading documents
file_frame = tk.LabelFrame(root, text="Load Documents", padx=10, pady=10)
file_frame.pack(padx=10, pady=10, fill="x")
tk.Button(file_frame, text="Load Main Document", command=load_main_document).pack(side="left", padx=5, pady=5)
tk.Button(file_frame, text="Load Helper Documents", command=load_helper_documents).pack(side="left", padx=5, pady=5)

# Frame for thresholds
threshold_frame = tk.LabelFrame(root, text="Set Thresholds", padx=10, pady=10)
threshold_frame.pack(padx=10, pady=10, fill="x")
tk.Label(threshold_frame, text="Covered Threshold:").grid(row=0, column=0, padx=5, pady=5)
covered_threshold_entry = tk.Entry(threshold_frame)
covered_threshold_entry.insert(0, str(COVERED_THRESHOLD))
covered_threshold_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Label(threshold_frame, text="Problematic Threshold:").grid(row=1, column=0, padx=5, pady=5)
problematic_threshold_entry = tk.Entry(threshold_frame)
problematic_threshold_entry.insert(0, str(PROBLEMATIC_THRESHOLD))
problematic_threshold_entry.grid(row=1, column=1, padx=5, pady=5)
tk.Button(threshold_frame, text="Set Thresholds", command=set_thresholds).grid(row=2, column=0, columnspan=2, pady=10)

# Frame for displaying results
report_frame = tk.LabelFrame(root, text="Analysis Results", padx=10, pady=10)
report_frame.pack(padx=10, pady=10, fill="both", expand=True)
report_text_widget = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, width=100, height=30)
report_text_widget.pack(padx=10, pady=10, fill="both", expand=True)

# Frame for action buttons
button_frame = tk.Frame(root)
button_frame.pack(padx=10, pady=10, fill="x")
tk.Button(button_frame, text="Generate Report", command=lambda: generate_analysis_report(
    main_document_path, helper_documents_paths, report_text_widget
)).pack(side="right", padx=5, pady=5)

root.mainloop()
