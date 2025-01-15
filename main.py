import os
from sentence_transformers import SentenceTransformer, util
import numpy as np
from transformers import pipeline
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

# Define thresholds
COVERED_THRESHOLD = 0.8
PROBLEMATIC_THRESHOLD = 0.4

# Create DIR for docs
output_dir = "documents"
os.makedirs(output_dir, exist_ok=True)

# Log file for reviewed sentences
review_log_file = "reviewed_log.txt"
if not os.path.exists(review_log_file):
    with open(review_log_file, "w", encoding="utf-8") as log:
        log.write("Reviewed Sentences Log\n")

# Load advanced NLP models
sentiment_analyzer = pipeline("sentiment-analysis")

# Function to calculate similarity
def calculate_similarity():
    # Load model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Read docs
    file_paths = [os.path.join(output_dir, file) for file in os.listdir(output_dir)]

    with open(file_paths[0], "r", encoding="utf-8") as f:
        main_sentences = f.read().split(". ")

    helper_sentences = []
    helper_sources = []
    for path in file_paths[1:]:
        with open(path, "r", encoding="utf-8") as f:
            sentences = f.read().split(". ")
            helper_sentences.extend(sentences)
            helper_sources.extend([os.path.basename(path)] * len(sentences))

    # Compute embeddings
    main_embeddings = model.encode(main_sentences, convert_to_tensor=True)
    helper_embeddings = model.encode(helper_sentences, convert_to_tensor=True)

    # Calculate sentence similarities
    results = []
    for i, sentence_embedding in enumerate(main_embeddings):
        similarities = util.pytorch_cos_sim(sentence_embedding, helper_embeddings)
        max_sim = np.max(similarities.numpy())
        best_matches = [
            (helper_sentences[j], helper_sources[j], sim.item())
            for j, sim in enumerate(similarities[0])
            if sim.item() > 0
        ]
        best_matches = sorted(best_matches, key=lambda x: x[2], reverse=True)  # Sort by similarity
        results.append((main_sentences[i], max_sim, best_matches))

    return results

results = calculate_similarity()

# Function to analyze ambiguity and sentiment
def analyze_sentence(sentence):
    analysis = {}

    # Sentiment analysis
    sentiment = sentiment_analyzer(sentence)[0]
    analysis["sentiment"] = sentiment["label"]
    analysis["sentiment_score"] = sentiment["score"]

    # Improved ambiguity detection using heuristics
    ambiguous_keywords = ["it", "this", "that", "these", "those", "something", "anything"]
    ambiguous_phrases = [
        "might be", "could be", "possibly", "perhaps", "seems like", "appears to be"
    ]
    ambiguity_score = 0

    # Check for ambiguous keywords
    for keyword in ambiguous_keywords:
        if keyword in sentence.lower():
            ambiguity_score += 1

    # Check for ambiguous phrases
    for phrase in ambiguous_phrases:
        if phrase in sentence.lower():
            ambiguity_score += 1

    # Determine ambiguity level
    if ambiguity_score > 1:
        analysis["ambiguity"] = "High"
    elif ambiguity_score == 1:
        analysis["ambiguity"] = "Medium"
    else:
        analysis["ambiguity"] = "Low"

    return analysis

# Function to generate recommendation
def generate_recommendation(best_matches):
    sources = {}
    for _, source, sim in best_matches:
        if source not in sources:
            sources[source] = []
        sources[source].append(sim)

    sorted_sources = sorted(sources.items(), key=lambda x: -np.mean(x[1]))[:3]  # Top 3 sources
    return [source for source, _ in sorted_sources]

# Function to update the log file
def update_review_log(sentence, action):
    with open(review_log_file, "a", encoding="utf-8") as log:
        log.write(f"{sentence} - {action}\n")

# Function to generate and save the graph
def generate_graph(results, graph_file="graph.png"):
    G = nx.Graph()

    # Add nodes and edges
    for sentence, max_sim, best_matches in results:
        G.add_node(sentence, type="sentence")
        for match_sentence, source, sim in best_matches:
            G.add_node(match_sentence, type="match")
            G.add_node(source, type="source")
            G.add_edge(sentence, match_sentence, weight=sim)
            G.add_edge(match_sentence, source, weight=sim)

    # Draw the graph
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(12, 8))
    nx.draw(
        G, pos, with_labels=True, node_size=500, font_size=8, alpha=0.7,
        node_color="lightblue", edge_color="gray"
    )
    plt.title("Sentence and Document Relationships", fontsize=14)
    plt.savefig(graph_file)
    plt.close()

# Function to generate heatmap
def generate_similarity_heatmap(results, heatmap_file="heatmap.png"):
    matrix = []
    sentences = [result[0] for result in results]
    for result in results:
        row = [sim for _, _, sim in result[2]]
        matrix.append(row)

    plt.figure(figsize=(10, 8))
    sns.heatmap(matrix, xticklabels=sentences, yticklabels=sentences, cmap="viridis", annot=False)
    plt.title("Similarity Heatmap")
    plt.savefig(heatmap_file)
    plt.close()

# Function to generate report
def generate_report(results, output_file="report.html"):
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
            ambiguity = analysis["ambiguity"]
            sentiment = analysis["sentiment"]

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

# Generate the final report
generate_report(results)
