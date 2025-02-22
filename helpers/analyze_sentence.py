import re
from transformers import pipeline

sentiment_analyzer = pipeline("sentiment-analysis")

ambiguous_pattern = re.compile(r"\b(it|this|that|these|those|something|anything)\b", re.IGNORECASE)
ambiguous_phrases = ["might be", "could be", "possibly", "perhaps", "seems like", "appears to be"]

def analyze_sentence(sentence):
    ambiguity_score = len(ambiguous_pattern.findall(sentence))
    ambiguity_score += sum(1 for phrase in ambiguous_phrases if phrase in sentence.lower())

    return {"ambiguity": "High" if ambiguity_score > 1 else "Medium" if ambiguity_score == 1 else "Low"}