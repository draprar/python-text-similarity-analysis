import os
from helpers.config import REVIEW_LOG_FILE

def initialize_log():
    """
    Initializes the review log file if it does not exist.

    - Creates the file at the specified REVIEW_LOG_FILE path.
    - Adds a header line to indicate log format.

    This function should be called once at startup to ensure the log file is ready.
    """
    if not os.path.exists(REVIEW_LOG_FILE):
        with open(REVIEW_LOG_FILE, "w", encoding="utf-8") as log:
            log.write("Sentence - Action\n")  # Log format header

def update_review_log(sentence: str, action: str):
    """
    Appends a reviewed sentence and its associated action to the review log.

    Args:
        sentence (str): The sentence being reviewed.
        action (str): The action taken on the sentence (e.g., "Accepted", "Rejected").
    """
    if not sentence.strip() or not action.strip():
        return  # Don't save empty values

    try:
        with open(REVIEW_LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"{sentence} - {action}\n")  # Append to log file
    except Exception as e:
        print(f"Error updating review log: {e}")  # Handle file I/O errors

