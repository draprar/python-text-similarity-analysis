from transformers import pipeline
import re

# Load advanced NLP models
sentiment_analyzer = pipeline("sentiment-analysis")

def analyze_sentence(sentence):
    """
    Analyzes the ambiguity of a given sentence.

    Args:
        sentence (str): The sentence to analyze.

    Returns:
        dict: Analysis results, including ambiguity level.
    """
    analysis = {}
    try:
        ambiguous_keywords = ["it", "this", "that", "these", "those", "something", "anything"]
        ambiguous_phrases = [
            "might be", "could be", "possibly", "perhaps", "seems like", "appears to be"
        ]
        ambiguity_score = 0

        # Check for ambiguous keywords as whole words
        for keyword in ambiguous_keywords:
            if re.search(rf"\b{keyword}\b", sentence, re.IGNORECASE):
                ambiguity_score += 1

        # Check for ambiguous phrases
        for phrase in ambiguous_phrases:
            if phrase in sentence.lower():
                ambiguity_score += 1

        # Determine ambiguity level
        if ambiguity_score > 1:
            analysis["ambiguity"] = "High"
        elif ambiguity_score == 1:
            analysis["ambiguity"] = "Medium"
        else:
            analysis["ambiguity"] = "Low"

    except Exception as e:
        analysis = {"error": str(e)}

    return analysis