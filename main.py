from calculate_similarity import calculate_similarity
from dependency_graph import create_dependency_graph

if __name__ == "__main__":
    # Test with hardcoded paths
    main_doc = None
    helper_docs = None

    # Calculate sentence similarities
    results = calculate_similarity(main_doc, helper_docs)

    # Generate graph
    sentence_labels = {result[0]: f"S{i + 1}" for i, result in enumerate(results)}
    create_dependency_graph(results, sentence_labels)
