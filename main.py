import os
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Define thresholds
COVERED_THRESHOLD = 0.8
PROBLEMATIC_THRESHOLD = 0.4

# Create DIR for docs
output_dir = "documents"
os.makedirs(output_dir, exist_ok=True)

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

# Function to generate recommendation
def generate_recommendation(best_matches):
    sources = {}
    for _, source, sim in best_matches:
        if source not in sources:
            sources[source] = []
        sources[source].append(sim)

    sorted_sources = sorted(sources.items(), key=lambda x: -np.mean(x[1]))[:3]  # Top 3 sources
    return [source for source, _ in sorted_sources]


def generate_report(results, output_file="report.html"):
    total_sentences = len(results)
    covered_count = sum(1 for _, max_sim, _ in results if max_sim >= COVERED_THRESHOLD)
    problematic_count = sum(1 for _, max_sim, _ in results if max_sim < COVERED_THRESHOLD)
    mapped_count = sum(1 for _, max_sim, _ in results if max_sim > 0)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("<html><body>")
        f.write("<h1>Document Analysis Report</h1>")

        for sentence, max_sim, best_matches in results:
            if max_sim >= COVERED_THRESHOLD:
                color = "green"
                label = "Covered"
            elif max_sim < PROBLEMATIC_THRESHOLD:
                color = "red"
                label = "Problematic"
            else:
                color = "orange"
                label = "Mapped"

            f.write(f"<p style='color:{color};'>{label} ({max_sim:.2f}): {sentence}")

            if best_matches:
                f.write("<details><summary>View Matches</summary><ul>")
                for match_sentence, source, sim in best_matches:
                    f.write(f"<li>({sim:.2f}) {match_sentence} <br>Source: {source}</li>")
                f.write("</ul></details>")

                # Add merging suggestions
                recommended_sources = generate_recommendation(best_matches)
                f.write("<p><strong>Merge Suggestion:</strong> " + ", ".join(recommended_sources) + "</p>")

            f.write("</p>")

        # Summary
        f.write("<h2>Summary Statistics</h2>")
        f.write(f"<p>Total Sentences: {total_sentences}</p>")
        f.write(f"<p>Mapped: {mapped_count} ({(mapped_count / total_sentences) * 100:.2f}%)</p>")
        f.write(f"<p>Covered: {covered_count} ({(covered_count / total_sentences) * 100:.2f}%)</p>")
        f.write(f"<p>Problematic: {problematic_count} ({(problematic_count / total_sentences) * 100:.2f}%)</p>")

        f.write("</body></html>")
    print(f"Report saved to {output_file}")

generate_report(results)
