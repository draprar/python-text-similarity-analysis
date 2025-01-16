from calculate_similarity import calculate_similarity
from generate_report import generate_report

if __name__ == "__main__":
    # Calculate sentence similarities
    results = calculate_similarity()

    # Generate the final report
    generate_report(results)

    # Generate interactive graph and add to results.html
    generate_graph_interactive(results)
    