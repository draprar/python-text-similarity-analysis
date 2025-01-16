import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

def generate_graph(results, graph_file="graph.png"):
    G = nx.Graph()

    # Add nodes and edges
    for sentence, max_sim, best_matches in results:
        G.add_node(sentence, type="sentence")
        for match_sentence, source, sim in best_matches:
            G.add_node(match_sentence, type="match")
            G.add_node(source, type="source")
            G.add_edge(sentence, match_sentence, weight=sim)
            G.add_edge(match_sentence, source, weight=sim)

    # Draw the graph
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(12, 8))
    nx.draw(
        G, pos, with_labels=True, node_size=500, font_size=8, alpha=0.7,
        node_color="lightblue", edge_color="gray"
    )
    plt.title("Sentence and Document Relationships", fontsize=14)
    try:
        plt.savefig(graph_file)
    except IOError as e:
        print(f"Error saving graph to {graph_file}: {e}")
    finally:
        plt.close()

def generate_similarity_heatmap(results, heatmap_file="heatmap.png"):
    matrix = []
    sentences = [result[0] for result in results]
    for result in results:
        row = [sim for _, _, sim in result[2]]
        matrix.append(row)

    # Handle non-square matrices by padding rows with zeros
    max_cols = max(len(row) for row in matrix)
    padded_matrix = [row + [0] * (max_cols - len(row)) for row in matrix]

    plt.figure(figsize=(10, 8))
    try:
        sns.heatmap(padded_matrix, xticklabels=sentences, yticklabels=sentences, cmap="viridis", annot=False)
        plt.title("Similarity Heatmap")
        plt.savefig(heatmap_file)
    except ValueError as e:
        print(f"Error generating heatmap: {e}")
    except IOError as e:
        print(f"Error saving heatmap to {heatmap_file}: {e}")
    finally:
        plt.close()
