import os

# ------------------------------
# CONFIGURATION SETTINGS
# ------------------------------

# Thresholds for sentence similarity classification
COVERED_THRESHOLD = 0.8  # Minimum similarity for a sentence to be considered "covered"
PROBLEMATIC_THRESHOLD = 0.4  # Below this similarity, a sentence is considered problematic

# Define base directory for storing documents and logs
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Paths to key directories
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")  # Directory for storing processed documents
LOGS_DIR = os.path.join(BASE_DIR, "logs")  # Directory for logging analysis results
ASSETS_DIR = os.path.join(BASE_DIR, "assets")  # Directory for storing visual assets (e.g., dependency graphs)

# Ensure required directories exist before use
for directory in [DOCUMENTS_DIR, LOGS_DIR, ASSETS_DIR]:
    os.makedirs(directory, exist_ok=True)  # Create if missing

# Define file paths for logs and output assets
REVIEW_LOG_FILE = os.path.join(LOGS_DIR, "reviewed_log.txt")  # Log file for reviewed sentences
DEPENDENCY_GRAPH_PATH = os.path.join(ASSETS_DIR, "dependency_graph.png")  # Path to the generated dependency graph
