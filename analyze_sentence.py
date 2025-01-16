from transformers import pipeline

# Load advanced NLP models
sentiment_analyzer = pipeline("sentiment-analysis")

# Function to analyze ambiguity and sentiment
def analyze_sentence(sentence):
    analysis = {}

    try:
        # Sentiment analysis
        if not sentence.strip():
            raise ValueError("Input sentence is empty.")

        sentiment = sentiment_analyzer(sentence)[0]
        analysis["sentiment"] = sentiment["label"]
        analysis["sentiment_score"] = sentiment["score"]

        # Improved ambiguity detection using heuristics
        ambiguous_keywords = ["it", "this", "that", "these", "those", "something", "anything"]
        ambiguous_phrases = [
            "might be", "could be", "possibly", "perhaps", "seems like", "appears to be"
        ]
        ambiguity_score = 0

        # Check for ambiguous keywords
        for keyword in ambiguous_keywords:
            if keyword in sentence.lower():
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