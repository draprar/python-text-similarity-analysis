from analyze_sentence import analyze_sentence
from config import review_log_file, update_review_log, COVERED_THRESHOLD, PROBLEMATIC_THRESHOLD
from generate_graphs import generate_graph, generate_similarity_heatmap
from generate_recommendation import generate_recommendation

# Function to generate report
def generate_report(results, output_file="report.html"):
    try:
        total_sentences = len(results)
        covered_count = sum(1 for _, max_sim, _ in results if max_sim >= COVERED_THRESHOLD)
        problematic_count = sum(1 for _, max_sim, _ in results if max_sim < COVERED_THRESHOLD)
        mapped_count = sum(1 for _, max_sim, _ in results if max_sim > 0)

        reviewed_sentences = set()
        with open(review_log_file, "r", encoding="utf-8") as log:
            for line in log.readlines()[1:]:
                reviewed_sentences.add(line.split(" - ")[0].strip())

        # Generate the graph
        graph_file = "graph.png"
        generate_graph(results, graph_file)

        # Generate heatmap
        heatmap_file = "heatmap.png"
        generate_similarity_heatmap(results, heatmap_file)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("<html><head>")
            f.write("<style>.collapsible {cursor: pointer; padding: 10px; border: 1px solid #ccc;}</style>")
            f.write("<script>")
            f.write("function toggleVisibility(id) { var x = document.getElementById(id); x.style.display = x.style.display === 'none' ? 'block' : 'none'; }")
            f.write("</script>")
            f.write("</head><body>")
            f.write("<h1>Document Analysis Report</h1>")

            # Summary Section
            f.write("<div class='collapsible' onclick='toggleVisibility(\"summary\")'>Summary Statistics</div>")
            f.write("<div id='summary' style='display:none;'>")
            f.write(f"<p>Total Sentences: {total_sentences}</p>")
            f.write(f"<p>Mapped: {mapped_count} ({(mapped_count / total_sentences) * 100:.2f}%)</p>")
            f.write(f"<p>Covered: {covered_count} ({(covered_count / total_sentences) * 100:.2f}%)</p>")
            f.write(f"<p>Problematic: {problematic_count} ({(problematic_count / total_sentences) * 100:.2f}%)</p>")
            f.write("</div>")

            # Sentence Analysis Section
            f.write("<div class='collapsible' onclick='toggleVisibility(\"sentence_analysis\")'>Sentence-by-Sentence Analysis</div>")
            f.write("<div id='sentence_analysis' style='display:none;'>")
            for sentence, max_sim, best_matches in results:
                if max_sim >= COVERED_THRESHOLD:
                    color = "green"
                    label = "Covered"
                    action = "Merge"
                elif max_sim < PROBLEMATIC_THRESHOLD:
                    color = "red"
                    label = "Problematic"
                    action = "Remove"
                else:
                    color = "orange"
                    label = "Mapped"
                    action = "Review"

                reviewed_status = "(Reviewed)" if sentence in reviewed_sentences else ""

                # Analyze sentence for ambiguity and sentiment
                analysis = analyze_sentence(sentence)
                ambiguity = analysis.get("ambiguity", "N/A")
                sentiment = analysis.get("sentiment", "N/A")

                f.write(f"<p style='color:{color};'>{label} ({max_sim:.2f}): {sentence} {reviewed_status}")
                f.write(f"<br><strong>Ambiguity:</strong> {ambiguity}")
                f.write(f"<br><strong>Sentiment:</strong> {sentiment}")

                if best_matches:
                    f.write("<details><summary>View Matches</summary><ul>")
                    for match_sentence, source, sim in best_matches:
                        f.write(f"<li>({sim:.2f}) {match_sentence} <br>Source: {source}</li>")
                    f.write("</ul></details>")

                    # Add merging suggestions
                    recommended_sources = generate_recommendation(best_matches)
                    f.write("<p><strong>Merge Suggestion:</strong> " + ", ".join(recommended_sources) + "</p>")

                f.write("</p>")

                # Update log for unreviewed sentences
                if sentence not in reviewed_sentences:
                    update_review_log(sentence, action)

            f.write("</div>")

            # Visualization Section
            f.write("<div class='collapsible' onclick='toggleVisibility(\"visualization\")'>Visualization</div>")
            f.write("<div id='visualization' style='display:none;'>")
            f.write(f"<h2>Relationship Graph</h2><img src='{graph_file}' alt='Graph'>")
            f.write(f"<h2>Similarity Heatmap</h2><img src='{heatmap_file}' alt='Heatmap'>")
            f.write("</div>")

            f.write("</body></html>")

    except Exception as e:
        print(f"Error generating report: {e}")