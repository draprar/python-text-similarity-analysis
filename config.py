import os

# Thresholds
COVERED_THRESHOLD = 0.8
PROBLEMATIC_THRESHOLD = 0.4

# Output directory for documents
output_dir = "documents"
os.makedirs(output_dir, exist_ok=True)

# Paths
review_log_file = "logs/review_log.txt"
dependency_graph_path = "assets/dependency_graph.png"