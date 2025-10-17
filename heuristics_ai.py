"""
AI Semantic Heuristics (Level 2)
Block analysis using spaCy (pl_core_news_md):
 - detects content types: people, organizations, dates, numbers, locations, units, etc.
 - evaluates the semantic significance of a change (semantic_score)
 - classifies change type: substantive, editorial, formal, technical
 - groups changes thematically (AI clustering)
 - generates a summary of changes (AI summary)
"""

import spacy
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List
from sklearn.cluster import KMeans
import numpy as np

# Load the Polish language model
try:
    nlp = spacy.load("pl_core_news_md")
except OSError:
    raise RuntimeError("spaCy model 'pl_core_news_md' is not installed. Run:\n"
                       "python -m spacy download pl_core_news_md")

# Entity categories of interest
NER_MAP = {
    "PER": "person",
    "ORG": "organization",
    "LOC": "place",
    "GPE": "location",
    "DATE": "date",
    "MONEY": "amount",
    "PERCENT": "percent",
    "TIME": "time",
    "NUM": "number",
    "PRODUCT": "product",
    "WORK_OF_ART": "title/work",
}


# ----------------------------------------------------------
# BASIC FUNCTIONS
# ----------------------------------------------------------

def extract_labels_spacy(text: str) -> List[str]:
    """Returns a list of semantic labels detected in the text."""
    doc = nlp(text)
    labels = set()

    for ent in doc.ents:
        if ent.label_ in NER_MAP:
            labels.add(NER_MAP[ent.label_])

    # heuristics for technical units and numeric values
    if re.search(r"\b(kg|m|mm|cm|km|%)\b", text):
        labels.add("unit")
    if re.search(r"\b\d+[.,]?\d*\b", text):
        labels.add("numbers")

    return sorted(labels)


def semantic_similarity(old_text: str, new_text: str) -> float:
    """Compares two texts semantically (cosine similarity) using spaCy vectors."""
    if not old_text.strip() or not new_text.strip():
        return 0.0
    doc1 = nlp(old_text)
    doc2 = nlp(new_text)
    return doc1.similarity(doc2)


# ----------------------------------------------------------
# CHANGE ANALYSIS
# ----------------------------------------------------------

def classify_change_type(old_text: str, new_text: str, labels: List[str]) -> str:
    """Classifies change type: substantive, editorial, formal, technical."""
    ratio = SequenceMatcher(None, old_text, new_text).ratio()
    combined = (old_text + " " + new_text).lower()

    # Substantive – differences in data, numbers, dates, amounts
    if any(l in labels for l in ["number", "amount", "date", "unit"]):
        return "substantive"

    # Technical – references to legal articles, paragraphs, etc.
    if re.search(r"\b(§|art\.|ust\.|pkt\.|dz\.u\.|poz\.)\b", combined):
        return "technical"

    # Editorial – high text similarity, stylistic differences only
    if ratio > 0.9:
        return "editorial"

    # Default: formal if structure of sentences differs
    if len(old_text.split()) != len(new_text.split()):
        return "formal"

    return "substantive"


def analyze_change(block: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main AI function:
     - detects content types in 'old' and 'new'
     - calculates semantic_score (lower similarity → greater change)
     - classifies change type (substantive/editorial/formal/technical)
    """
    result = {"labels": [], "semantic_score": 0.0, "change_type": "undefined", "confidence": 0.0}

    old_text = (block.get("old", {}) or {}).get("text", "") or ""
    new_text = (block.get("new", {}) or {}).get("text", "") or ""
    merged_text = old_text + " " + new_text

    # 1. labels
    labels = extract_labels_spacy(merged_text)
    result["labels"] = labels

    # 2. semantic distance
    try:
        sim = semantic_similarity(old_text, new_text)
        score = round((1 - sim) * 10, 2)
    except Exception:
        ratio = SequenceMatcher(None, old_text, new_text).ratio()
        score = round((1 - ratio) * 10, 2)

    result["semantic_score"] = score

    # 3. change type classification
    result["change_type"] = classify_change_type(old_text, new_text, labels)

    # 4. confidence (simple model – 1 - |sim - threshold|)
    conf = 1.0 - abs(0.85 - sim if "sim" in locals() else 0.5)
    result["confidence"] = round(conf, 2)

    return result


# ----------------------------------------------------------
# CLUSTERING AND SUMMARY
# ----------------------------------------------------------

def cluster_changes(blocks: List[Dict[str, Any]]) -> Dict[int, List[int]]:
    """Groups semantically similar changes (spaCy embeddings + KMeans)."""
    changed_blocks = [b for b in blocks if b.get("change") == "changed"]
    if len(changed_blocks) < 3:
        return {}

    vectors = []
    for b in changed_blocks:
        txt = (b.get("new", {}).get("text") or b.get("old", {}).get("text") or "").strip()
        doc = nlp(txt)
        vectors.append(doc.vector)
    X = np.vstack(vectors)

    n_clusters = max(2, min(10, len(changed_blocks) // 5))
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init="auto").fit(X)
    labels = kmeans.labels_

    clusters: Dict[int, List[int]] = {}
    for i, lbl in enumerate(labels):
        clusters.setdefault(int(lbl), []).append(i)
    return clusters


def generate_ai_summary(blocks: List[Dict[str, Any]]) -> str:
    """Generates a short summary of detected changes."""
    total = len(blocks)
    changed = [b for b in blocks if b.get("change") == "changed"]
    if not changed:
        return "No significant changes detected in the document."

    type_counts = {}
    for b in changed:
        t = b.get("_ai_type") or "undefined"
        type_counts[t] = type_counts.get(t, 0) + 1

    top_type = max(type_counts, key=type_counts.get)
    percent_major = round(type_counts[top_type] / len(changed) * 100, 1)

    return (
        f"The document contains {len(changed)} changes (out of {total} blocks), "
        f"of which {percent_major}% are of type <b>{top_type}</b>. "
        f"Dominant AI labels: "
        f"{', '.join(sorted({l for b in changed for l in (b.get('_ai_labels') or [])})) or 'none'}."
    )
