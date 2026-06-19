import os
from transformers import pipeline

MODEL_NAME = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")

_classifier = None


def load_model():
    """Load the model once into memory. Called at backend startup so the
    first real request during the demo isn't slow."""
    global _classifier
    if _classifier is None:
        _classifier = pipeline("sentiment-analysis", model=MODEL_NAME, tokenizer=MODEL_NAME)
    return _classifier


def analyze(text: str):
    classifier = load_model()
    result = classifier(text, truncation=True)[0]
    return result["label"], float(result["score"])