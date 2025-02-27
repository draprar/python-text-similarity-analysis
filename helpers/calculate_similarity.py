### helpers/calculate_similarity.py
import os
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer, util
from multiprocessing import Pool, cpu_count
from diskcache import Cache
import matplotlib

# Use non-GUI backend for Matplotlib to avoid threading issues
matplotlib.use('Agg')

# Initialize cache for storing document similarity results
cache = Cache('./cache_dir')


class SimilarityModel:
    """
    Singleton class for loading and reusing the SentenceTransformer model.
    This prevents reloading the model multiple times, improving performance.
    """
    _model = None

    @classmethod
    def get_model(cls):
        """Loads the model if not already initialized and returns it."""
        if cls._model is None:
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model


def generate_doc_hash(doc_path: str) -> str:
    """
    Generates a unique hash for a document's content.
    This helps in caching results efficiently.

    Args:
        doc_path (str): Path to the document.

    Returns:
        str: A SHA-256 hash of the document's content.

    Raises:
        IOError: If the file cannot be read.
    """
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        raise IOError(f"Error hashing document {doc_path}: {e}")


def process_sentence_chunk(args):
    """
    Processes a chunk of main document sentences, computing their similarity
    to helper document embeddings.

    Args:
        args (tuple): Contains:
            - main_chunk (list): Sentences from the main document.
            - helper_embeddings (tensor): Encoded helper document sentences.
            - helper_sentences (list): Helper sentences as raw text.
            - helper_sources (list): Source file names of helper sentences.

    Returns:
        list: A list of tuples containing:
            - The original main document sentence.
            - The maximum similarity score.
            - A list of best matching helper sentences with similarity scores.
    """
    main_chunk, helper_embeddings, helper_sentences, helper_sources = args
    results = []
    model = SimilarityModel.get_model()
    main_embeddings = model.encode(main_chunk, convert_to_tensor=True)

    for i, sentence_embedding in enumerate(main_embeddings):
        similarities = util.pytorch_cos_sim(sentence_embedding, helper_embeddings)
        max_sim = np.max(similarities.numpy()) if similarities.size(1) > 0 else 0  # Maximum similarity

        # Retrieve best matching sentences from helper documents
        best_matches = [
            (helper_sentences[j], helper_sources[j], sim.item())
            for j, sim in enumerate(similarities[0]) if sim.item() > 0
        ]
        best_matches.sort(key=lambda x: x[2], reverse=True)  # Sort matches by similarity score

        results.append((main_chunk[i], max_sim, best_matches))

    return results


def calculate_similarity(main_doc: str, helper_docs: list) -> list:
    """
    Computes sentence-level similarity between a main document and multiple helper documents.
    Uses parallel processing for efficiency and caches results to avoid redundant computations.

    Args:
        main_doc (str): Path to the main document.
        helper_docs (list): List of paths to helper documents.

    Returns:
        list: A list of tuples containing:
            - The original main document sentence.
            - The maximum similarity score.
            - A list of best matching helper sentences with similarity scores.

    Raises:
        ValueError: If there is insufficient data to perform similarity analysis.
    """
    model = SimilarityModel.get_model()

    # Generate unique cache key based on document contents
    main_doc_hash = generate_doc_hash(main_doc)
    helper_doc_hashes = [generate_doc_hash(path) for path in helper_docs]
    cache_key = f"similarity_{main_doc_hash}_{'_'.join(helper_doc_hashes)}"

    # Return cached results if available
    if cache_key in cache:
        return cache[cache_key]

    # Read and process the main document
    with open(main_doc, "r", encoding="utf-8") as f:
        main_sentences = [sentence.strip() for sentence in f.read().split(". ") if sentence.strip()]

    # Read and process helper documents
    helper_sentences, helper_sources = [], []
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

    # Encode helper document sentences
    helper_embeddings = model.encode(helper_sentences, convert_to_tensor=True)

    # Determine the number of workers for parallel processing
    num_workers = min(cpu_count(), len(main_sentences))
    chunk_size = max(1, len(main_sentences) // num_workers)
    main_chunks = [main_sentences[i:i + chunk_size] for i in range(0, len(main_sentences), chunk_size)]

    # Process chunks in parallel
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_sentence_chunk,
                           [(chunk, helper_embeddings, helper_sentences, helper_sources) for chunk in main_chunks])

    # Flatten results and cache them
    flattened_results = [item for sublist in results for item in sublist]
    cache[cache_key] = flattened_results

    return flattened_results
