import os
from unittest.mock import patch, MagicMock
from helpers.dependency_graph import create_dependency_graph


def test_create_dependency_graph():
    results = [
        ("Sentence 1", 0.9, [("Sentence A", "Doc1", 0.8)]),
        ("Sentence 2", 0.7, [("Sentence B", "Doc2", 0.6)])
    ]
    sentence_labels = {
        "Sentence 1": "S1",
        "Sentence 2": "S2",
        "Sentence A": "A1",
        "Sentence B": "B1"
    }
    output_image = "test_dependency_graph.png"

    # Run function
    returned_path = create_dependency_graph(results, sentence_labels, output_image)

    # Check if output path is correct
    assert returned_path == output_image

    # Check if file is created
    assert os.path.exists(output_image)

    # Cleanup
    os.remove(output_image)


def test_graph_structure():
    results = [
        ("Sentence 1", 0.9, [("Sentence A", "Doc1", 0.8)]),
        ("Sentence 2", 0.7, [("Sentence B", "Doc2", 0.6)])
    ]
    sentence_labels = {"Sentence 1": "S1", "Sentence 2": "S2", "Sentence A": "A1", "Sentence B": "B1"}

    with patch("networkx.DiGraph") as mock_graph:
        mock_instance = MagicMock()
        mock_graph.return_value = mock_instance

        create_dependency_graph(results, sentence_labels, "mock_output.png")

        # Ensure nodes are added
        expected_nodes = {'S1', 'S2'}
        added_nodes = {call.args[0] for call in mock_instance.add_node.call_args_list}
        assert expected_nodes == added_nodes

        # Ensure edges are added correctly
        expected_edges = {('S1', 'Doc1'), ('S2', 'Doc2')}
        added_edges = {(call.args[0], call.args[1]) for call in mock_instance.add_edge.call_args_list}
        assert expected_edges == added_edges