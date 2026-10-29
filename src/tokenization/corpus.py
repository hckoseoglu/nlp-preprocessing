"""Candidate point corpus for tokenization: "should we split here?" examples from UD-BOUN.

The gold standard is UD's surface tokens (`Sentence.tokens`; multi-word tokens such as `yılındayız`
stay in one piece) together with `SpaceAfter=No`. Whitespace is always a token boundary, so we only
look inside chunks that contain no whitespace.

Candidate point: every position inside a chunk where at least one of the two neighbouring characters
is not a letter or digit (punctuation, symbol, apostrophe). Examples (| split, · no split):

    gittim,     → gittim|,
    Ankara'ya   → Ankara·'·ya
    19.30'da.   → 19·.·30·'·da|.

A position between two letters/digits is not a candidate; UD-BOUN has almost no boundaries there
(33 in train, most of them a missing space in the source: `kadınlardakiAğır`). These are counted as
`missed`.

Gold conventions (decided with Hikmet, see CLAUDE.md):
    "ud"   UD-BOUN tokens exactly as they are.
    "tdk"  (our default) the same, except for one rule taken from TDK spelling: the period after an
           abbreviation or an ordinal number belongs to that word when the sentence continues after
           it. UD-BOUN mostly splits these periods off (`Dr` `.`, `3` `.`); we merge them back:
               Dr . Ahmet      →  Dr. Ahmet
               3 . sınıf       →  3. sınıf
               ... 1923 .      →  unchanged (the sentence ends, so this is the sentence-final period)

For the counts:  python src/scripts/tok_corpus_stats.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from io_conllu import Sentence, read_conllu
from textutil import is_abbreviation, load_abbreviations

DATA = Path(__file__).resolve().parents[2] / "data" / "UD_Turkish-BOUN"
ABBREVIATIONS = load_abbreviations()        # TDK abbreviation list, shared with the sentence splitter
CONVENTIONS = ("tdk", "ud")


def keeps_period(word: str) -> bool:
    """Our convention: an abbreviation (TDK list) or an ordinal number keeps its period."""
    return word.isdigit() or is_abbreviation(word, ABBREVIATIONS)


def continues_after(text: str) -> bool:
    """Does the sentence go on (is there another word or number in `text`)?"""
    return any(ch.isalnum() for ch in text)


@dataclass
class Candidate:
    """A possible token boundary inside a chunk: between chunk[pos - 1] and chunk[pos]."""
    chunk: str                 # chunk without whitespace, e.g. "gittim,"
    pos: int                   # position of the boundary inside the chunk (1 .. len(chunk) - 1)
    label: bool | None = None  # does the gold split here? (unknown for raw text → None)
    sentence_continues: bool = True   # is there another word or number in a later chunk?

    @property
    def left(self) -> str:
        """Character before the boundary."""
        return self.chunk[self.pos - 1]

    @property
    def right(self) -> str:
        """Character after the boundary."""
        return self.chunk[self.pos]


def is_candidate(chunk: str, pos: int) -> bool:
    """A position is a candidate point if at least one of its two neighbours is not a letter/digit."""
    return not (chunk[pos - 1].isalnum() and chunk[pos].isalnum())


def chunk_candidates(chunk: str, bounds: set[int] | None = None,
                     sentence_continues: bool = True) -> list[Candidate]:
    """Candidate points of a chunk. If `bounds` (gold boundaries) is given, each candidate is labelled."""
    return [Candidate(chunk, pos, None if bounds is None else pos in bounds, sentence_continues)
            for pos in range(1, len(chunk))
            if is_candidate(chunk, pos)]


def continuation_flags(chunks: list[str]) -> list[bool]:
    """For every chunk: does the sentence go on after it (a later chunk with a word or number)?"""
    flags, seen_word = [], False
    for chunk in reversed(chunks):
        flags.append(seen_word)
        seen_word = seen_word or continues_after(chunk)
    return flags[::-1]


def gold_tokens(sentence: Sentence, convention: str = "tdk") -> list[tuple[str, bool]]:
    """Gold tokens of a sentence as (form, is there a space after it) pairs, in the given convention."""
    tokens = [(t.form, t.space_after) for t in sentence.tokens]
    if convention == "ud":
        return tokens
    merged: list[tuple[str, bool]] = []
    i = 0
    while i < len(tokens):
        form, space_after = tokens[i]
        next_form = tokens[i + 1][0] if i + 1 < len(tokens) else None
        rest = "".join(f for f, _ in tokens[i + 2:])
        if next_form == "." and not space_after and keeps_period(form) and continues_after(rest):
            merged.append((form + ".", tokens[i + 1][1]))     # "Dr" + "." → "Dr."
            i += 2
        else:
            merged.append((form, space_after))
            i += 1
    return merged


def gold_chunks(sentence: Sentence, convention: str = "tdk") -> list[tuple[str, set[int]]]:
    """Groups the gold tokens of a sentence into chunks: (chunk, token boundaries inside the chunk).

    Example: `Ankara'ya gittim, 19.30'da.` →
        ("Ankara'ya", {}), ("gittim,", {6}), ("19.30'da.", {8})
    """
    out: list[tuple[str, set[int]]] = []
    chunk, bounds = "", set()
    for form, space_after in gold_tokens(sentence, convention):
        if chunk:                       # the previous token ended without a space → this is a token boundary
            bounds.add(len(chunk))
        chunk += form
        if space_after:
            out.append((chunk, bounds))
            chunk, bounds = "", set()
    if chunk:
        out.append((chunk, bounds))
    return out


def sentence_candidates(sentence: Sentence, convention: str = "tdk") -> list[Candidate]:
    """All labelled candidate points of a UD sentence."""
    chunks = gold_chunks(sentence, convention)
    flags = continuation_flags([chunk for chunk, _ in chunks])
    return [cand
            for (chunk, bounds), continues in zip(chunks, flags)
            for cand in chunk_candidates(chunk, bounds, continues)]


def load_split(split: str) -> list[Sentence]:
    """UD-BOUN train / dev / test sentences."""
    return read_conllu(DATA / f"tr_boun-ud-{split}.conllu")


def corpus_stats(sentences: list[Sentence], convention: str = "tdk") -> dict[str, int]:
    """Corpus counts (the progress report's 22,713 / 16,701 are the "ud" convention)."""
    stats = dict.fromkeys(("sentences", "tokens", "chunks", "chunks_to_split",
                           "candidates", "splits", "missed"), 0)
    for sentence in sentences:
        stats["sentences"] += 1
        stats["tokens"] += len(gold_tokens(sentence, convention))
        for chunk, bounds in gold_chunks(sentence, convention):
            cands = chunk_candidates(chunk, bounds)
            stats["chunks"] += 1
            stats["chunks_to_split"] += bool(bounds)
            stats["candidates"] += len(cands)
            stats["splits"] += sum(c.label for c in cands)
            stats["missed"] += sum(not is_candidate(chunk, pos) for pos in bounds)
    return stats


def show(sentence: Sentence, convention: str = "tdk") -> str:
    """Shows the candidate points of a sentence: | split, · no split."""
    parts = []
    for chunk, bounds in gold_chunks(sentence, convention):
        marks = {c.pos: "|" if c.label else "·" for c in chunk_candidates(chunk, bounds)}
        parts.append("".join(marks.get(i, "") + ch for i, ch in enumerate(chunk)))
    return " ".join(parts)
