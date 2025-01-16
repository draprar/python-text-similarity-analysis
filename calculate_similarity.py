import os
from sentence_transformers import SentenceTransformer, util
import numpy as np

output_dir = "documents"

# Function to calculate similarity
def calculate_similarity():
    # Load model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Read docs
    file_paths = [os.path.join(output_dir, file) for file in os.listdir(output_dir)]

    if not file_paths:
        raise FileNotFoundError(f"No files found in the directory: {output_dir}")

    try:
        with open(file_paths[0], "r", encoding="utf-8") as f:
            main_sentences = f.read().split(". ")
    except Exception as e:
        raise IOError(f"Error reading main file {file_paths[0]}: {e}")

    helper_sentences = []
    helper_sources = []
    for path in file_paths[1:]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                sentences = f.read().split(". ")
                helper_sentences.extend(sentences)
                helper_sources.extend([os.path.basename(path)] * len(sentences))
        except Exception as e:
            print(f"Warning: Could not read file {path}: {e}")

    if not main_sentences or not helper_sentences:
        raise ValueError("Insufficient data to calculate similarities.")

    # Compute embeddings
    main_embeddings = model.encode(main_sentences, convert_to_tensor=True)
    helper_embeddings = model.encode(helper_sentences, convert_to_tensor=True)

    # Calculate sentence similarities
    results = []
    for i, sentence_embedding in enumerate(main_embeddings):
        similarities = util.pytorch_cos_sim(sentence_embedding, helper_embeddings)
        if similarities.shape[1] == 0:
            continue

        max_sim = np.max(similarities.numpy())
        best_matches = [
            (helper_sentences[j], helper_sources[j], sim.item())
            for j, sim in enumerate(similarities[0])
            if sim.item() > 0
        ]
        best_matches = sorted(best_matches, key=lambda x: x[2], reverse=True)  # Sort by similarity
        results.append((main_sentences[i], max_sim, best_matches))

    return results