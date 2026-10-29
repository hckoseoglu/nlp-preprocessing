"""Logistic Regression tokenizer (Ecem): decides "split / do not split" at every candidate point.

Training: the candidate points of the UD-BOUN training sentences (our "tdk" gold) plus copies of 20%
of them with a synthetic URL / e-mail / hashtag / mention (tokenization/special.py), because UD has
none of these. scikit-learn's LogisticRegression (Pedregosa et al. 2011) learns from the
hand-designed features in tokenization/features.py.

Tokenizing a sentence:
    "Ankara'ya gittim."  →  chunks: Ankara'ya | gittim.
                         →  candidate points: Ankara·'·ya  gittim·.
                         →  model decisions:  no, no       yes
                         →  tokens: Ankara'ya | gittim | .
"""
from __future__ import annotations

from io_conllu import Sentence
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

from .corpus import chunk_candidates, continuation_flags, sentence_candidates
from .features import extract
from .special import augment


class LRTokenizer:
    """Logistic Regression over candidate points, with feature set `level` (1, 2 or 3)."""

    def __init__(self, level: int = 3):
        self.level = level
        self.vectorizer = DictVectorizer()
        self.model = LogisticRegression(max_iter=2000)

    @classmethod
    def train(cls, sentences: list[Sentence], level: int = 3, augment_rate: float = 0.2,
              seed: int = 0) -> "LRTokenizer":
        """Trains on the candidate points of `sentences` + their synthetic special-entity copies."""
        tokenizer = cls(level)
        training = sentences + augment(sentences, augment_rate, seed)
        candidates = [c for s in training for c in sentence_candidates(s)]
        X = tokenizer.vectorizer.fit_transform([extract(c, level) for c in candidates])
        y = [c.label for c in candidates]
        tokenizer.model.fit(X, y)
        return tokenizer

    def tokenize(self, sentence: str) -> list[str]:
        chunks = sentence.split()
        per_chunk = [chunk_candidates(chunk, sentence_continues=continues)
                     for chunk, continues in zip(chunks, continuation_flags(chunks))]
        candidates = [c for cands in per_chunk for c in cands]
        decisions = iter(self.model.predict(self.vectorizer.transform(
            [extract(c, self.level) for c in candidates])) if candidates else [])
        tokens: list[str] = []
        for chunk, cands in zip(chunks, per_chunk):
            start = 0
            for c in cands:                                  # cut the chunk at every "split" decision
                if next(decisions):
                    tokens.append(chunk[start:c.pos])
                    start = c.pos
            tokens.append(chunk[start:])
        return tokens
