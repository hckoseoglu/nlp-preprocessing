"""Multi-word expressions (MWE): an optional layer that runs after a tokenizer.

UD-BOUN keeps an MWE as separate tokens ("yavaş" "yavaş") and marks it with a dependency relation.
This layer finds the MWEs in a tokenized sentence and joins each one into a single token:

    ["yavaş", "yavaş", "yürüdü", "."]  →  ["yavaş yavaş", "yürüdü", "."]

Three kinds, taken from the UD relations (Türk et al. 2022; `flat` = multi-word names is left out):

    fixed    fixed grammatical expressions        ya da · hem de · ne var ki
    redup    reduplication                        yavaş yavaş · sık sık · ara sıra
    lvc      noun + light verb (et / ol / yap)     kabul etti · sahip olan · devam ediyor

How an MWE is found:
    1. lexicon (resources/mwe_tr.txt, built from the training split by src/scripts/tok_build_mwe.py):
       fixed and redup entries must match word by word; an lvc entry needs its noun followed by any
       form of its light verb (etti, ediyor, olan, yapacak ...).
    2. one rule for reduplication: the same word twice in a row (tek tek, pırıl pırıl).

UD's gold tokens never join MWEs, so the layer is off in the token tables; it is scored separately
against the MWE spans of UD (evaluate_mwes).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from io_conllu import Sentence
from textutil import tr_lower

from .metrics import Score, token_spans

LEXICON_FILE = Path(__file__).resolve().parents[2] / "resources" / "mwe_tr.txt"
DEPRELS = {"fixed": "fixed", "compound:redup": "redup", "compound:lvc": "lvc"}
KINDS = ("fixed", "redup", "lvc")
LIGHT_VERBS = {"et": ("et", "ed"), "ol": ("ol",), "yap": ("yap",)}   # lemma → how its forms start (etti, ediyor)

MWE = tuple[int, int, str]          # (first token, last token + 1, kind)


@dataclass(frozen=True)
class Entry:
    """A lexicon entry. `words` are lower case; for lvc the last word is the light verb lemma."""
    kind: str
    words: tuple[str, ...]

    def matches(self, words: list[str], i: int) -> bool:
        """Does this entry start at position i of the (lower-case) words?"""
        n = len(self.words)
        if i + n > len(words):
            return False
        if self.kind == "lvc":
            *noun, verb = self.words
            return words[i:i + n - 1] == noun and words[i + n - 1].startswith(LIGHT_VERBS[verb])
        return tuple(words[i:i + n]) == self.words


# --- gold MWEs from UD ----------------------------------------------------------------------------

def gold_mwes(sentence: Sentence) -> list[MWE]:
    """MWEs of a UD sentence, from the dependency relations (as token positions).

    An MWE is a head word together with its dependents in one of the MWE relations. Only MWEs whose
    words stand next to each other are kept (a few lvc / redup have other words in between).
    """
    token_of = {w.idx: i for i, t in enumerate(sentence.tokens) for w in t.words}
    groups: dict[tuple[int, str], set[int]] = defaultdict(set)
    for w in sentence.words:
        kind = DEPRELS.get(w.deprel)
        if kind and w.head in token_of:
            groups[(w.head, kind)] |= {w.head, w.idx}
    mwes = []
    for (_, kind), ids in groups.items():
        positions = sorted({token_of[i] for i in ids})
        words_together = sorted(ids) == list(range(min(ids), max(ids) + 1))
        if words_together and len(positions) > 1:
            mwes.append((positions[0], positions[-1] + 1, kind))
    return sorted(mwes)


def entry_of(sentence: Sentence, mwe: MWE) -> Entry | None:
    """The lexicon entry for a gold MWE (None for an lvc whose verb is not et / ol / yap)."""
    start, end, kind = mwe
    words = tuple(tr_lower(t.form) for t in sentence.tokens[start:end])
    if kind != "lvc":
        return Entry(kind, words)
    verb = sentence.tokens[end - 1].words[-1].lemma
    return Entry(kind, words[:-1] + (verb,)) if verb in LIGHT_VERBS else None


# --- the lexicon -----------------------------------------------------------------------------------

def build_lexicon(sentences: list[Sentence], min_share: float = 0.2) -> list[tuple[Entry, int, int]]:
    """Lexicon from UD sentences: (entry, times as MWE, times seen).

    An expression is kept only if it is an MWE in at least `min_share` of the places where it occurs,
    so that word pairs UD rarely marks as an MWE are left out. 0.2 was chosen on dev (MWE F1 0.5 →
    0.2: 70.7 → 74.9); with 0.5, "ya da" would be lost, because UD-BOUN marks it as `fixed` in only
    29 of its 90 occurrences in train (but in 7 of 8 in dev).
    """
    as_mwe: Counter = Counter()
    for s in sentences:
        for mwe in gold_mwes(s):
            entry = entry_of(s, mwe)
            if entry:
                as_mwe[entry] += 1
    by_first = defaultdict(list)
    for entry in as_mwe:
        by_first[entry.words[0]].append(entry)
    seen: Counter = Counter()
    for s in sentences:
        words = [tr_lower(t.form) for t in s.tokens]
        for i, word in enumerate(words):
            for entry in by_first.get(word, []):
                seen[entry] += entry.matches(words, i)
    lexicon = []
    for entry, n in as_mwe.items():
        total = max(seen[entry], n)
        if n / total >= min_share:
            lexicon.append((entry, n, total))
    return sorted(lexicon, key=lambda x: (KINDS.index(x[0].kind), -x[1], x[0].words))


def save_lexicon(lexicon: list[tuple[Entry, int, int]], path: Path = LEXICON_FILE) -> None:
    lines = ["# Turkish multi-word expressions, from the UD-BOUN training split (Türk et al. 2022).",
             "# Built by src/scripts/tok_build_mwe.py. Columns: kind, expression, times as MWE, times seen.",
             "# lvc: the last word is a light verb (et / ol / yap) and matches any of its forms (etti, olan, yapacak)."]
    lines += [f"{e.kind}\t{' '.join(e.words)}\t{n}\t{total}" for e, n, total in lexicon]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_lexicon(path: Path = LEXICON_FILE) -> list[Entry]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            kind, expression = line.split("\t")[:2]
            entries.append(Entry(kind, tuple(expression.split())))
    return entries


# --- the layer -------------------------------------------------------------------------------------

def is_repeat(words: list[str], i: int) -> bool:
    """The reduplication rule: the same word twice in a row (tek tek, pırıl pırıl)."""
    return i + 1 < len(words) and words[i] == words[i + 1] and words[i].isalpha() and len(words[i]) > 1


class MWEMerger:
    """Finds MWEs in a token list with the lexicon (+ the reduplication rule) and joins them."""

    def __init__(self, entries: list[Entry] | None = None, repeat_rule: bool = True):
        self.repeat_rule = repeat_rule
        self.by_first: dict[str, list[Entry]] = defaultdict(list)
        for entry in load_lexicon() if entries is None else entries:
            self.by_first[entry.words[0]].append(entry)
        for candidates in self.by_first.values():
            candidates.sort(key=lambda e: -len(e.words))          # try the longest expression first

    def find(self, tokens: list[str]) -> list[MWE]:
        """MWEs in a token list, from left to right, without overlaps."""
        words = [tr_lower(t) for t in tokens]
        found, i = [], 0
        while i < len(words):
            mwe = self._match_at(words, i)
            if mwe:
                found.append(mwe)
                i = mwe[1]
            else:
                i += 1
        return found

    def _match_at(self, words: list[str], i: int) -> MWE | None:
        for entry in self.by_first.get(words[i], []):
            if entry.matches(words, i):
                return (i, i + len(entry.words), entry.kind)
        if self.repeat_rule and is_repeat(words, i):
            return (i, i + 2, "redup")
        return None

    def merge(self, tokens: list[str]) -> list[str]:
        """Joins every MWE into one token: ["ya", "da", "sen"] → ["ya da", "sen"]."""
        out, last = [], 0
        for start, end, _ in self.find(tokens):
            out += tokens[last:start] + [" ".join(tokens[start:end])]
            last = end
        return out + tokens[last:]


def evaluate_mwes(merger: MWEMerger, tokenize: Callable[[str], list[str]],
                  sentences: list[Sentence]) -> dict[str, Score]:
    """MWE precision / recall / F1 per kind and for "all" (units = sentences).

    An MWE is correct if it covers exactly the same characters as a gold MWE (and, per kind, has the
    same kind). The MWEs are searched in the output of `tokenize` on the raw sentence text.
    """
    scores = {kind: Score() for kind in (*KINDS, "all")}
    for s in sentences:
        gold_spans = token_spans(s.text, [t.form for t in s.tokens])
        tokens = tokenize(s.text)
        pred_spans = token_spans(s.text, tokens)
        if gold_spans is None or pred_spans is None:
            scores["all"].skipped += 1
            continue
        gold = {(gold_spans[a][0], gold_spans[b - 1][1], kind) for a, b, kind in gold_mwes(s)}
        pred = {(pred_spans[a][0], pred_spans[b - 1][1], kind) for a, b, kind in merger.find(tokens)}
        for kind in KINDS:
            g = {m for m in gold if m[2] == kind}
            p = {m for m in pred if m[2] == kind}
            scores[kind].correct += len(g & p)
            scores[kind].gold += len(g)
            scores[kind].predicted += len(p)
        g_all, p_all = {m[:2] for m in gold}, {m[:2] for m in pred}
        scores["all"].correct += len(g_all & p_all)
        scores["all"].gold += len(g_all)
        scores["all"].predicted += len(p_all)
        for score in scores.values():
            score.units += 1
    return scores
