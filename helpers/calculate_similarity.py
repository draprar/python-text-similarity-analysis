import os
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer, util
from multiprocessing import Pool, cpu_count
from diskcache import Cache

# Initialize cache
cache = Cache('./cache_dir')

# Function to generate a unique hash for caching purposes
def generate_doc_hash(doc_path):
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        raise IOError(f"Error hashing document {doc_path}: {e}")


def process_sentence_chunk(main_chunk, helper_embeddings, helper_sentences, helper_sources, model):
    results = []
    main_embeddings = model.encode(main_chunk, convert_to_tensor=True)
    for i, sentence_embedding in enumerate(main_embeddings):
        similarities = util.pytorch_cos_sim(sentence_embedding, helper_embeddings)
        if similarities.size(1) == 0:
            continue

        max_sim = np.max(similarities.numpy())
        best_matches = [
            (helper_sentences[j], helper_sources[j], sim.item())
            for j, sim in enumerate(similarities[0])
            if sim.item() > 0
        ]
        best_matches.sort(key=lambda x: x[2], reverse=True)  # Sort by similarity score
        results.append((main_chunk[i], max_sim, best_matches))
    return results


def calculate_similarity(main_doc, helper_docs):
    """
    Calculates sentence similarities between a main document and a list of helper documents,
    with parallel processing and caching.

    Args:
        main_doc (str): Path to the main document.
        helper_docs (list): List of paths to helper documents.

    Returns:
        list: A list of tuples containing the main sentence, maximum similarity score,
              and best matches with corresponding similarity scores and sources.
    """
    # Load the sentence transformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Generate unique hash for caching
    main_doc_hash = generate_doc_hash(main_doc)
    helper_doc_hashes = [generate_doc_hash(path) for path in helper_docs]
    cache_key = f"similarity_{main_doc_hash}_{'_'.join(helper_doc_hashes)}"

    # Check if results are cached
    if cache_key in cache:
        return cache[cache_key]

    # Read and process the main document
    try:
        with open(main_doc, "r", encoding="utf-8") as f:
            main_sentences = [sentence.strip() for sentence in f.read().split(". ") if sentence.strip()]
    except Exception as e:
        raise IOError(f"Error reading main document {main_doc}: {e}")

    # Read and process the helper documents
    helper_sentences = []
    helper_sources = []
    for path in helper_docs:
        try:
            with open(path, "r", encoding="utf-8") as f:
                sentences = [sentence.strip() for sentence in f.read().split(". ") if sentence.strip()]
                helper_sentences.extend(sentences)
                helper_sources.extend([os.path.basename(path)] * len(sentences))
        except Exception as e:
            print(f"Warning: Could not read helper file {path}: {e}")

    if not main_sentences or not helper_sentences:
        raise ValueError("Insufficient data to calculate similarities.")

    # Compute helper embeddings once
    helper_embeddings = model.encode(helper_sentences, convert_to_tensor=True)

    # Split main sentences into chunks for parallel processing
    num_workers = cpu_count()
    chunk_size = max(1, len(main_sentences) // num_workers)
    main_chunks = [main_sentences[i:i + chunk_size] for i in range(0, len(main_sentences), chunk_size)]

    # Use multiprocessing pool to process chunks
    with Pool(processes=num_workers) as pool:
        results = pool.starmap(
            process_sentence_chunk,
            [(chunk, helper_embeddings, helper_sentences, helper_sources, model) for chunk in main_chunks]
        )

    # Flatten the list of results
    flattened_results = [item for sublist in results for item in sublist]

    # Cache the results
    cache[cache_key] = flattened_results

    return flattened_results
