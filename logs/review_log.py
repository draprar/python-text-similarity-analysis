import os
from helpers.config import REVIEW_LOG_FILE

def initialize_log():
    """Initialize the review log file if it doesn't exist."""
    if not os.path.exists(REVIEW_LOG_FILE):
        with open(REVIEW_LOG_FILE, "w", encoding="utf-8") as log:
            log.write("Sentence - Action\n")

def update_review_log(sentence, action):
    """Append a sentence and its action to the review log."""
    try:
        with open(REVIEW_LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"{sentence} - {action}\n")
    except Exception as e:
        print(f"Error updating review log: {e}")