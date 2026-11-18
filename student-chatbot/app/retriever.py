import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Retriever:
    """Finds the knowledge-base entries closest in meaning to a question (TF-IDF)."""

    def __init__(self, path):
        self.docs = json.loads(Path(path).read_text(encoding="utf-8"))
        texts = [f"{d['title']} {d['question']} {d['answer']} {' '.join(d.get('keywords', []))}"
                 for d in self.docs]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, query: str, k: int = 3):
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        best = scores.argsort()[::-1][:k]
        return [{**self.docs[i], "score": float(scores[i])} for i in best if scores[i] > 0]
