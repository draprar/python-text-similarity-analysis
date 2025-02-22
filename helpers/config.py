import os

# Thresholds for sentence similarity analysis
COVERED_THRESHOLD = 0.8
PROBLEMATIC_THRESHOLD = 0.4

# Define base directory for storing documents
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Ensure required directories exist
for directory in [DOCUMENTS_DIR, LOGS_DIR, ASSETS_DIR]:
    os.makedirs(directory, exist_ok=True)

# File paths
REVIEW_LOG_FILE = os.path.join(LOGS_DIR, "reviewed_log.txt")
DEPENDENCY_GRAPH_PATH = os.path.join(ASSETS_DIR, "dependency_graph.png")
