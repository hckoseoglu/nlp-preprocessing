"""Kategorik Naïve Bayes — sıfırdan, yalnız standart kütüphane.

Her örnek {özellik_adı: değer} sözlüğüdür (değerler kategorik: "upper", "y", "3", ...). Sınıf c için

    log P(c | x) ∝ log P(c) + Σ_f log P(x_f | c, f)

P(x_f | c, f) = (count(c, f, v) + α) / (n_c + α · (|V_f| + 1))   — Laplace/add-α düzeltmesi; |V_f| + 1'deki
fazladan 1, eğitimde görülmemiş değerler için ayrılan "bilinmeyen" kovasıdır (olasılık asla sıfırlanmaz).

İkili özellikler için bu, Bernoulli NB ile aynıdır (McCallum & Nigam 1998); tanım ve düzeltme
Jurafsky & Martin, Speech and Language Processing (3. baskı taslağı) böl. 4'ü izler.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path


class NaiveBayes:
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.classes: list[str] = []
        self.class_count: dict[str, int] = {}
        # counts[c][f][v] = sınıf c'de f özelliğinin v değerini kaç kez aldığı
        self.counts: dict[str, dict[str, dict[str, int]]] = {}
        self.values: dict[str, set[str]] = defaultdict(set)   # f → eğitimde görülen değerler

    # ------------------------------------------------------------------ eğitim
    def fit(self, X: list[dict[str, str]], y: list[str]) -> "NaiveBayes":
        if len(X) != len(y) or not X:
            raise ValueError("X ve y aynı uzunlukta ve boş olmayan listeler olmalı")
        self.class_count = defaultdict(int)
        self.counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.values = defaultdict(set)
        for x, c in zip(X, y):
            self.class_count[c] += 1
            for f, v in x.items():
                v = str(v)
                self.counts[c][f][v] += 1
                self.values[f].add(v)
        self.classes = sorted(self.class_count)
        return self

    # ------------------------------------------------------------------ tahmin
    def _log_likelihood(self, c: str, f: str, v: str) -> float:
        n_c = self.class_count[c]
        k = len(self.values[f]) + 1
        count = self.counts[c][f].get(v, 0) if f in self.counts[c] else 0
        return math.log((count + self.alpha) / (n_c + self.alpha * k))

    def log_scores(self, x: dict[str, str]) -> dict[str, float]:
        """Normalize edilmemiş log P(c) + Σ log P(x_f | c)."""
        total = sum(self.class_count.values())
        scores = {}
        for c in self.classes:
            s = math.log(self.class_count[c] / total)
            for f, v in x.items():
                if f not in self.values:      # eğitimde hiç görülmemiş özellik: bilgi yok, atla
                    continue
                s += self._log_likelihood(c, f, str(v))
            scores[c] = s
        return scores

    def predict_proba(self, x: dict[str, str]) -> dict[str, float]:
        scores = self.log_scores(x)
        m = max(scores.values())
        z = sum(math.exp(s - m) for s in scores.values())
        return {c: math.exp(s - m) / z for c, s in scores.items()}

    def predict(self, x: dict[str, str]) -> str:
        scores = self.log_scores(x)
        return max(self.classes, key=lambda c: (scores[c], c))

    # ------------------------------------------------------------------ kaydet / yükle
    def to_dict(self) -> dict:
        return {
            "alpha": self.alpha,
            "class_count": dict(self.class_count),
            "counts": {c: {f: dict(vs) for f, vs in fs.items()} for c, fs in self.counts.items()},
            "values": {f: sorted(vs) for f, vs in self.values.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NaiveBayes":
        nb = cls(alpha=d["alpha"])
        nb.class_count = dict(d["class_count"])
        nb.classes = sorted(nb.class_count)
        nb.counts = {c: {f: dict(vs) for f, vs in fs.items()} for c, fs in d["counts"].items()}
        nb.values = defaultdict(set, {f: set(vs) for f, vs in d["values"].items()})
        return nb

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=0), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "NaiveBayes":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
