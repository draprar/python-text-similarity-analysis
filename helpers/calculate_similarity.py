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

# Initialize cache
cache = Cache('./cache_dir')


# Load model once and reuse
class SimilarityModel:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._model


# Function to generate a unique hash for caching purposes
def generate_doc_hash(doc_path):
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        raise IOError(f"Error hashing document {doc_path}: {e}")


def process_sentence_chunk(args):
    main_chunk, helper_embeddings, helper_sentences, helper_sources = args
    results = []
    model = SimilarityModel.get_model()
    main_embeddings = model.encode(main_chunk, convert_to_tensor=True)

    for i, sentence_embedding in enumerate(main_embeddings):
        similarities = util.pytorch_cos_sim(sentence_embedding, helper_embeddings)
        max_sim = np.max(similarities.numpy()) if similarities.size(1) > 0 else 0

        best_matches = [
            (helper_sentences[j], helper_sources[j], sim.item())
            for j, sim in enumerate(similarities[0]) if sim.item() > 0
        ]
        best_matches.sort(key=lambda x: x[2], reverse=True)
        results.append((main_chunk[i], max_sim, best_matches))

    return results


def calculate_similarity(main_doc, helper_docs):
    """
    Calculates sentence similarities between a main document and helper documents,
    utilizing parallel processing and caching.
    """
    model = SimilarityModel.get_model()

    # Generate unique hash for caching
    main_doc_hash = generate_doc_hash(main_doc)
    helper_doc_hashes = [generate_doc_hash(path) for path in helper_docs]
    cache_key = f"similarity_{main_doc_hash}_{'_'.join(helper_doc_hashes)}"

    if cache_key in cache:
        return cache[cache_key]

    # Read and process the main document
    with open(main_doc, "r", encoding="utf-8") as f:
        main_sentences = [sentence.strip() for sentence in f.read().split(". ") if sentence.strip()]

    # Read and process the helper documents
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

    helper_embeddings = model.encode(helper_sentences, convert_to_tensor=True)

    num_workers = min(cpu_count(), len(main_sentences))
    chunk_size = max(1, len(main_sentences) // num_workers)
    main_chunks = [main_sentences[i:i + chunk_size] for i in range(0, len(main_sentences), chunk_size)]

    with Pool(processes=num_workers) as pool:
        results = pool.map(process_sentence_chunk,
                           [(chunk, helper_embeddings, helper_sentences, helper_sources) for chunk in main_chunks])

    flattened_results = [item for sublist in results for item in sublist]
    cache[cache_key] = flattened_results
    return flattened_results
