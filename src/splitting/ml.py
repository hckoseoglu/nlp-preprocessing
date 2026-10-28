"""Naïve Bayes sentence splitter — kendi NB'miz (src/ml/naive_bayes.py) + features.py setleri."""
from __future__ import annotations

import json
from pathlib import Path

from ml import NaiveBayes
from textutil import ABBREV_FILE, load_abbreviations

from .corpus import Candidate, build_paragraphs, labeled_candidates
from .features import extract
from .rules import Splitter

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = ROOT / "resources" / "splitter_nb.json"


class NBSplitter(Splitter):
    def __init__(self, level: int = 3, alpha: float = 1.0, abbrevs: set[str] | None = None, threshold: float = 0.5):
        self.level = level
        self.alpha = alpha
        self.threshold = threshold
        self.abbrevs = abbrevs if abbrevs is not None else load_abbreviations(ABBREV_FILE)
        self.model = NaiveBayes(alpha=alpha)

    # ------------------------------------------------------------------ eğitim
    def fit(self, cands: list[Candidate]) -> "NBSplitter":
        X = [extract(c, self.abbrevs, self.level) for c in cands]
        y = ["S" if c.label else "N" for c in cands]
        self.model.fit(X, y)
        return self

    def fit_sentences(self, sentences: list[str], size: int = 5, seed: int = 0) -> "NBSplitter":
        cands = [c for text, bounds in build_paragraphs(sentences, size, seed) for c in labeled_candidates(text, bounds)]
        return self.fit(cands)

    @classmethod
    def train_from_conllu(cls, path: str | Path, level: int = 3, alpha: float = 1.0, seed: int = 0) -> "NBSplitter":
        from io_conllu import read_conllu
        return cls(level=level, alpha=alpha).fit_sentences([s.text for s in read_conllu(path)], seed=seed)

    # ------------------------------------------------------------------ karar
    def proba(self, c: Candidate) -> float:
        return self.model.predict_proba(extract(c, self.abbrevs, self.level)).get("S", 0.0)

    def decide(self, c: Candidate) -> bool:
        return self.proba(c) > self.threshold

    # ------------------------------------------------------------------ kaydet / yükle
    def save(self, path: str | Path = DEFAULT_MODEL) -> None:
        d = self.model.to_dict()
        d.update(level=self.level, threshold=self.threshold)
        Path(path).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path = DEFAULT_MODEL) -> "NBSplitter":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        sp = cls(level=d["level"], alpha=d["alpha"], threshold=d.get("threshold", 0.5))
        sp.model = NaiveBayes.from_dict(d)
        return sp
