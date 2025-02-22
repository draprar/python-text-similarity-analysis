import networkx as nx
import matplotlib.pyplot as plt
from helpers.config import DEPENDENCY_GRAPH_PATH
import matplotlib
matplotlib.use('Agg')

def create_dependency_graph(results, sentence_labels, output_image=DEPENDENCY_GRAPH_PATH):
    """
    Generates a dependency graph from analysis results and saves it as an image.

    Args:
        results (list): List of tuples containing sentence, max similarity, and best matches.
        sentence_labels (dict): Dictionary mapping sentences to their labels (e.g., S1, S2).
        output_image (str): File path for saving the graph image.

    Returns:
        str: Path to the saved graph image.
    """
    G = nx.DiGraph()

    # Add nodes for sentences
    for sentence, _, _ in results:
        label = sentence_labels.get(sentence, "Unknown")
        G.add_node(label, type="sentence", color="lightblue")

    # Add edges for dependencies
    for sentence, _, best_matches in results:
        source_label = sentence_labels.get(sentence, "Unknown")
        for match_sentence, doc, sim in best_matches:
            if sim > 0:  # Only add meaningful dependencies
                target_label = sentence_labels.get(match_sentence, doc)  # Use doc name if no label
                G.add_edge(source_label, target_label, weight=sim)

    # Define node colors and edge labels
    node_colors = ["lightblue" if data.get("type") == "sentence" else "lightgrey" for _, data in G.nodes(data=True)]
    edge_labels = {(u, v): f"{w:.2f}" for u, v, w in G.edges(data="weight")}

    # Draw the graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)  # Consistent layout
    nx.draw(G, pos, with_labels=True, node_size=1500, node_color=node_colors, font_size=10, font_weight="bold")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("Dependency Graph")
    plt.savefig(output_image)
    plt.close()

    return output_image
