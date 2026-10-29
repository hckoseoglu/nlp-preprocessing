"""Token-level evaluation: compare predicted tokens with UD gold tokens by character offsets.

A predicted token is correct if its start and end offsets in the sentence are exactly the same as
those of a gold token (the token metric of the CoNLL 2018 UD shared task, Zeman et al. 2018). On top
of precision / recall / F1 we report sentence exact match: all tokens of the sentence are correct.
The gold can be taken in our "tdk" convention (main score) or as plain UD-BOUN ("ud"), see corpus.py.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from io_conllu import Sentence

from .corpus import gold_tokens

Span = tuple[int, int]


def token_spans(text: str, tokens: list[str]) -> list[Span] | None:
    """Character offsets of the tokens in the text, found from left to right.

    Only whitespace may lie between two tokens. Returns None if a token cannot be placed (the
    tokenizer changed the text, or a UD token form differs from the `# text` line).
    """
    spans: list[Span] = []
    pos = 0
    for token in tokens:
        start = text.find(token, pos)
        if start < 0 or text[pos:start].strip():
            return None
        spans.append((start, start + len(token)))
        pos = start + len(token)
    return spans


def error_regions(text: str, gold: list[Span], pred: list[Span]) -> list[tuple[str, str]]:
    """Places where the two tokenizations differ, as (gold tokens, predicted tokens) strings.

    Example: gold `Dr.` vs predicted `Dr` `.` → ("Dr.", "Dr .").
    """
    wrong = sorted(set(gold) ^ set(pred))
    regions: list[list[int]] = []
    for start, end in wrong:                      # merge overlapping wrong spans into regions
        if regions and start < regions[-1][1]:
            regions[-1][1] = max(regions[-1][1], end)
        else:
            regions.append([start, end])
    out = []
    for a, b in regions:
        g = " ".join(text[s:e] for s, e in gold if a <= s and e <= b)
        p = " ".join(text[s:e] for s, e in pred if a <= s and e <= b)
        out.append((g, p))
    return out


@dataclass
class Score:
    """Token counts with precision / recall / F1, and exact match over units.

    A unit is a sentence in the main tables, and a chunk in the hard-case table (hard_cases.py).
    """
    correct: int = 0
    predicted: int = 0
    gold: int = 0
    units: int = 0
    exact: int = 0                                # units whose tokens are all correct
    skipped: int = 0                              # sentences whose gold tokens do not fit `# text`
    errors: Counter = field(default_factory=Counter)

    def add(self, text: str, gold: list[Span], pred: list[Span]) -> None:
        """Adds one unit: its gold and predicted token spans in `text`."""
        self.units += 1
        self.gold += len(gold)
        self.predicted += len(pred)
        self.correct += len(set(gold) & set(pred))
        if pred == gold:
            self.exact += 1
        else:
            self.errors.update(error_regions(text, gold, pred))

    @property
    def precision(self) -> float:
        return self.correct / self.predicted if self.predicted else 0.0

    @property
    def recall(self) -> float:
        return self.correct / self.gold if self.gold else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def exact_match(self) -> float:
        return self.exact / self.units if self.units else 0.0


def gold_and_predicted(tokenize: Callable[[str], list[str]], sentence: Sentence,
                       convention: str = "tdk") -> tuple[list[Span] | None, list[Span]]:
    """Gold and predicted token spans of one sentence (gold is None if it does not fit `# text`)."""
    gold = token_spans(sentence.text, [form for form, _ in gold_tokens(sentence, convention)])
    if gold is None:
        return None, []
    pred = token_spans(sentence.text, tokenize(sentence.text)) or []
    return gold, pred


def evaluate(tokenize: Callable[[str], list[str]], sentences: list[Sentence],
             convention: str = "tdk") -> Score:
    """Runs `tokenize` on every sentence text and scores it against the gold tokens."""
    score = Score()
    for sentence in sentences:
        gold, pred = gold_and_predicted(tokenize, sentence, convention)
        if gold is None:
            score.skipped += 1
        else:
            score.add(sentence.text, gold, pred)
    return score
