import os

# Thresholds for sentence similarity analysis
COVERED_THRESHOLD = 0.8
PROBLEMATIC_THRESHOLD = 0.4

# Output directory for storing documents
OUTPUT_DIR = "../documents"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# File paths
REVIEW_LOG_FILE = "logs/reviewed_log.txt"
DEPENDENCY_GRAPH_PATH = "assets/dependency_graph.png"
