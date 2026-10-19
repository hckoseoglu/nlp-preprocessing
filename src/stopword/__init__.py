"""Stopword elimination paketi (static + dynamic). SAHİP: paylaşımlı.

Çekirdek API core.py'de; buradan re-export edilir.
- core.py      : compute_stats / dynamic_stopwords / load_static_stopwords / evaluate_list
Deney/figür scriptleri src/scripts/ altında: stopword_evaluate.py (static/dynamic/union P/R/F1), stopword_analyze.py
(K-vs-F1, tf-idf dağılımı), stopword_extrinsic.py (genre sınıflandırma), stopword_build_42bin.py (ikinci korpus).
"""
from .core import (
    CHUNK_SIZE,
    FUNCTION_POS,
    CorpusStats,
    compute_stats,
    dynamic_stopwords,
    evaluate_list,
    load_static_stopwords,
    remove_stopwords,
    tr_lower,
)

__all__ = [
    "CHUNK_SIZE", "FUNCTION_POS", "CorpusStats", "compute_stats",
    "dynamic_stopwords", "evaluate_list", "load_static_stopwords",
    "remove_stopwords", "tr_lower",
]
