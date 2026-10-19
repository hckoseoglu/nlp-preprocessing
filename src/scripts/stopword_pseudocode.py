"""Stopword eliminasyonunun sade sözde kodu → reports/stopword_pseudocode.png (rapor figürü).

Kullanım: <venv>/python3 src/scripts/stopword_pseudocode.py      (matplotlib gerekir)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stem_pseudocode import render  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "stopword_pseudocode.png"

LINES = [
    ("BUILD_DYNAMIC_LIST(training sentences, K = 75):          # K = best F1 on dev", "kw"),
    ("    shuffle the sentences with a fixed seed and group every 20 sentences into one pseudo-document", ""),
    ("    for each word w (lowercased, tokens starting with a letter):", ""),
    ("        tf(w, d)  ← count of w in d / length of d", ""),
    ("        df(w)     ← number of documents containing w", ""),
    ("        idf(w)    ← log(N / df(w))                                 # N = number of documents", ""),
    ("        tfidf(w)  ← (Σ_d tf(w, d) / df(w)) · idf(w)", ""),
    ("    return the K words with the lowest tfidf                       # seen everywhere, carries little information", ""),
]


if __name__ == "__main__":
    render(LINES, "Dynamic stopword list: simplified pseudo-code", OUT, width=11.0)
