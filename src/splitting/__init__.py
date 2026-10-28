"""Sentence splitting paketi — rule-based (RuleSplitter) ve Naïve Bayes (NBSplitter).

Her splitter ham metin alır, cümle listesi döndürür. Aday sınır = noktalama + (kapanış tırnağı) + boşluk
(corpus.candidates); karar her aday için `decide(cand) -> bool`. Tokenizer gerekmez (bkz. CLAUDE.md "Sıra kararı").
"""
from .corpus import Candidate, build_paragraphs, candidates, labeled_candidates  # noqa: F401
from .features import FEATURE_LEVELS, extract  # noqa: F401
from .ml import NBSplitter  # noqa: F401
from .rules import AlwaysSplit, RuleSplitter, Splitter  # noqa: F401
