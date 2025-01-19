import os
from config import review_log_file

def initialize_log():
    if not os.path.exists(review_log_file):
        with open(review_log_file, "w") as log:
            log.write("Sentence - Action\n")

def update_review_log(sentence, action):
    with open(review_log_file, "a") as log:
        log.write(f"{sentence} - {action}\n")