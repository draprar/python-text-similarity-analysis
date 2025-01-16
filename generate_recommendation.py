import numpy as np

# Function to generate recommendations
def generate_recommendation(best_matches):
    if not best_matches:
        print("No matches available for generating recommendations.")
        return []

    sources = {}
    for _, source, sim in best_matches:
        if source not in sources:
            sources[source] = []
        sources[source].append(sim)

    if not sources:
        print("Insufficient data in matches for generating recommendations.")
        return []

    sorted_sources = sorted(sources.items(), key=lambda x: -np.mean(x[1]))[:3]  # Top 3 sources
    return [source for source, _ in sorted_sources]
