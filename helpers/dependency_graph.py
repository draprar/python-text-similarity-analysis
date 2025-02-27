import networkx as nx
import matplotlib.pyplot as plt
from helpers.config import DEPENDENCY_GRAPH_PATH
import matplotlib

# Use non-GUI backend to avoid threading issues in multi-threaded environments
matplotlib.use('Agg')

def create_dependency_graph(results: list, sentence_labels: dict, output_image: str = DEPENDENCY_GRAPH_PATH) -> str:
    """
    Generates a dependency graph from analysis results and saves it as an image.

    Args:
        results (list): A list of tuples containing:
            - sentence (str): The sentence from the main document.
            - max_similarity (float): The highest similarity score.
            - best_matches (list): List of tuples with best matches (sentence, document, similarity score).
        sentence_labels (dict): A dictionary mapping sentences to unique labels (e.g., S1, S2).
        output_image (str, optional): File path for saving the graph image. Defaults to DEPENDENCY_GRAPH_PATH.

    Returns:
        str: Path to the saved graph image.
    """
    G = nx.DiGraph()  # Create a directed graph

    # Add nodes representing sentences
    for sentence, _, _ in results:
        label = sentence_labels.get(sentence, "Unknown")  # Use predefined label, default to "Unknown"
        G.add_node(label, type="sentence", color="lightblue")  # Nodes represent sentences

    # Add edges representing dependencies between sentences
    for sentence, _, best_matches in results:
        source_label = sentence_labels.get(sentence, "Unknown")  # Label for source sentence
        for match_sentence, doc, sim in best_matches:
            if sim > 0:  # Only add meaningful dependencies
                target_label = sentence_labels.get(match_sentence, doc)  # Use doc name if no label
                G.add_edge(source_label, target_label, weight=sim)  # Add weighted edge

    # Define node colors and edge labels for visualization
    node_colors = ["lightblue" if data.get("type") == "sentence" else "lightgrey" for _, data in G.nodes(data=True)]
    edge_labels = {(u, v): f"{w:.2f}" for u, v, w in G.edges(data="weight")}  # Display similarity scores

    # Draw and save the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)  # Consistent layout
    nx.draw(G, pos, with_labels=True, node_size=1500, node_color=node_colors, font_size=10, font_weight="bold")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("Dependency Graph")
    plt.savefig(output_image)  # Save as image file
    plt.close()  # Close the plot to free resources

    return output_image  # Return the saved image path
