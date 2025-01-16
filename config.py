import os

# Thresholds
COVERED_THRESHOLD = 0.8
PROBLEMATIC_THRESHOLD = 0.4

# Output directory for documents
output_dir = "documents"
os.makedirs(output_dir, exist_ok=True)

# Log file for reviewed sentences
review_log_file = "reviewed_log.txt"
if not os.path.exists(review_log_file):
    with open(review_log_file, "w", encoding="utf-8") as log:
        log.write("Reviewed Sentences Log\n")

# Function to update the log file
def update_review_log(sentence, action):
    with open(review_log_file, "a", encoding="utf-8") as log:
        log.write(f"{sentence} - {action}\n")