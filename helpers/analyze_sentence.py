import re
from transformers import pipeline

# Load sentiment analysis pipeline from Hugging Face Transformers
sentiment_analyzer = pipeline("sentiment-analysis")

# Precompile regex pattern for ambiguous keywords
ambiguous_pattern = re.compile(r"\b(it|this|that|these|those|something|anything)\b", re.IGNORECASE)

# List of ambiguous phrases that may indicate uncertainty
ambiguous_phrases = [
    "might be", "could be", "possibly", "perhaps", "seems like", "appears to be",
    "likely", "it is said", "suggests that", "it is believed", "somewhat",
    "arguably", "assumed to be", "reportedly", "allegedly", "uncertain",
    "not entirely clear", "rumored to be", "it is thought", "has been suggested",
    "estimated to be", "approximately", "more or less", "about", "around"
]

def analyze_sentence(sentence: str) -> dict:
    """
    Analyzes a sentence for ambiguity based on predefined keywords and phrases.

    Args:
        sentence (str): The input sentence to analyze.

    Returns:
        dict: A dictionary containing the ambiguity level:
            - "High" if multiple ambiguous terms are found.
            - "Medium" if one ambiguous term is found.
            - "Low" if no ambiguous terms are found.
    """
    # Count occurrences of ambiguous keywords using regex
    ambiguity_score = len(ambiguous_pattern.findall(sentence))

    # Count occurrences of ambiguous phrases
    ambiguity_score += sum(1 for phrase in ambiguous_phrases if phrase in sentence.lower())

    # Determine ambiguity level based on score
    ambiguity_level = "High" if ambiguity_score > 1 else "Medium" if ambiguity_score == 1 else "Low"

    return {"ambiguity": ambiguity_level}
