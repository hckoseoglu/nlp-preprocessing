"""Hard cases for tokenization (test case 2): the chunks of real UD sentences where the decision is not obvious.

A chunk (a piece of text without whitespace) is a hard case if it belongs to at least one of these
kinds. The kinds are found from the raw text only, not from the gold, so every tokenizer is scored on
exactly the same chunks. A chunk can belong to more than one kind (19.30'da: apostrophe + number).

    apostrophe    a suffix after an apostrophe or a quote       Ankara'ya  19.30'da  yerde"nin
    number        a number with a separator or a % sign         19.30  3,5  08.02.2007  %25
    period        a period after a word, the sentence goes on   Dr. Ahmet  3. sınıf  T.C.  G.Saray
    punctuation   two or more punctuation marks together        gittim."  (1999),  Gel!..  ''

Only the tokens inside these chunks are scored (precision / recall / F1), and a chunk counts as exact
if all of its tokens are correct.
"""
from __future__ import annotations

import re
from typing import Callable

from io_conllu import Sentence

from .corpus import continuation_flags, continues_after
from .metrics import Score, Span, gold_and_predicted

HARD_CASES = ("apostrophe", "number", "period", "punctuation")

APOSTROPHE_RE = re.compile(r"\w['’]\w|\w[\"”]\w|[\"”)]['’]\w")   # Ankara'ya · yerde"nin · "Venüs"'ü
NUMBER_RE = re.compile(r"\d[.,:/]\d|%\d")                         # 19.30 · 3,5 · 1/2 · %25
PERIOD_RE = re.compile(r"\w\.(?!\.)")                             # a period after a word (not "...")
PUNCTUATION_RE = re.compile(r"[^\w\s]{2,}")                       # ." · ), · !.. · ''


def has_inner_period(chunk: str, sentence_continues: bool) -> bool:
    """Is there a period after a word that is not the end of the sentence? (Dr. / 3. / T.C. / G.Saray)

    A period between two digits (19.30) belongs to the "number" kind instead.
    """
    for m in PERIOD_RE.finditer(chunk):
        after = chunk[m.end():]
        if chunk[m.start()].isdigit() and after[:1].isdigit():
            continue
        if sentence_continues or continues_after(after):
            return True
    return False


def hard_case_kinds(chunk: str, sentence_continues: bool = True) -> list[str]:
    """The hard-case kinds of one chunk (empty list → an easy chunk)."""
    kinds = []
    if APOSTROPHE_RE.search(chunk):
        kinds.append("apostrophe")
    if NUMBER_RE.search(chunk):
        kinds.append("number")
    if has_inner_period(chunk, sentence_continues):
        kinds.append("period")
    if PUNCTUATION_RE.search(chunk):
        kinds.append("punctuation")
    return kinds


def spans_inside(spans: list[Span], start: int, end: int) -> list[Span]:
    """The token spans that lie inside the character range [start, end)."""
    return [s for s in spans if start <= s[0] and s[1] <= end]


def evaluate_hard_cases(tokenize: Callable[[str], list[str]], sentences: list[Sentence],
                        convention: str = "tdk") -> dict[str, Score]:
    """One Score per hard-case kind, plus "all" (every hard chunk once). Units are chunks."""
    scores = {kind: Score() for kind in (*HARD_CASES, "all")}
    for sentence in sentences:
        gold, pred = gold_and_predicted(tokenize, sentence, convention)
        if gold is None:
            scores["all"].skipped += 1
            continue
        chunks = list(re.finditer(r"\S+", sentence.text))
        flags = continuation_flags([m.group() for m in chunks])
        for m, continues in zip(chunks, flags):
            kinds = hard_case_kinds(m.group(), continues)
            if not kinds:
                continue
            gold_here = spans_inside(gold, m.start(), m.end())
            pred_here = spans_inside(pred, m.start(), m.end())
            for kind in (*kinds, "all"):
                scores[kind].add(sentence.text, gold_here, pred_here)
    return scores
