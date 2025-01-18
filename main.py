from calculate_similarity import calculate_similarity
from app import generate_analysis_report

if __name__ == "__main__":
    # Test with hardcoded paths
    main_doc = "path_to_main_document.txt"
    helper_docs = ["path_to_helper_doc1.txt", "path_to_helper_doc2.txt"]

    # Calculate sentence similarities
    results = calculate_similarity(main_doc, helper_docs)
