"""Hand-designed features of a candidate point for the Logistic Regression tokenizer.

The three feature sets are cumulative (set 1 ⊂ set 2 ⊂ set 3), so comparing them shows what each new
kind of information adds. Example candidate: "gittim|." (between "m" and "."):

    set 1  neighbouring characters    L=m  R=.  classes: lower | punct
    set 2  + wider window             L3=tim  R3=.  the boundary is at the end of the chunk
    set 3  + lexicon and patterns     left word is not an abbreviation / number, no URL in the chunk,
                                      the sentence ends here
"""
from __future__ import annotations

import re

from textutil import is_abbreviation

from .corpus import ABBREVIATIONS, Candidate, continues_after

FEATURE_LEVELS = (1, 2, 3)
QUOTES = "\"“”«»'‘’"

# Special entities inside a chunk (used by set 3). A URL stops before trailing punctuation.
ENTITY_RE = re.compile(
    r"""
      (?:https?://|www\.)\S+?(?=[.,;:!?)"'”’]*$)                # URL
    | [\w.+-]+@[\w-]+\.[\w.-]*\w                                 # e-mail
    | [#@]\w+                                                    # hashtag / mention
    | \w+(?:[.-]\w+)*\.(?:com|net|org|edu|gov|info|tr)\b         # domain name
    """,
    re.VERBOSE,
)


def char_class(ch: str) -> str:
    """Coarse class of a character: upper / lower / digit / quote / punct / symbol."""
    if ch.isalpha():
        return "upper" if ch.isupper() else "lower"
    if ch.isdigit():
        return "digit"
    if ch in QUOTES:
        return "quote"
    if ch in ".,;:!?…-()[]{}":
        return "punct"
    return "symbol"


def set1(c: Candidate) -> dict[str, int]:
    """Set 1: the two characters next to the boundary and their classes."""
    left, right = char_class(c.left), char_class(c.right)
    return {f"L={c.left}": 1, f"R={c.right}": 1,
            f"Lclass={left}": 1, f"Rclass={right}": 1, f"classes={left}|{right}": 1}


def set2(c: Candidate) -> dict[str, int]:
    """Set 2: a wider window (2 and 3 characters on each side) and where the boundary is in the chunk."""
    chunk, pos = c.chunk, c.pos
    where = "start" if pos == 1 else "end" if pos == len(chunk) - 1 else "middle"
    return {f"L2={chunk[max(0, pos - 2):pos]}": 1, f"R2={chunk[pos:pos + 2]}": 1,
            f"L3={chunk[max(0, pos - 3):pos]}": 1, f"R3={chunk[pos:pos + 3]}": 1,
            f"where={where}": 1}


def set3(c: Candidate) -> dict[str, int]:
    """Set 3: lexicon and pattern information (abbreviations, numbers, special entities, suffixes)."""
    chunk, pos = c.chunk, c.pos
    feats: dict[str, int] = {}
    left_word = re.search(r"\w+$", chunk[:pos])
    left_word = left_word.group() if left_word else ""
    if left_word and is_abbreviation(left_word, ABBREVIATIONS):
        feats["left_is_abbreviation"] = 1
    if left_word.isdigit():
        feats["left_is_number"] = 1
    if len(left_word) == 1 and left_word.isupper():
        feats["left_is_initial"] = 1
    if c.right in "'’" and chunk[pos + 1:pos + 2].islower():
        feats["apostrophe_suffix"] = 1                       # Ankara|'ya
    for m in ENTITY_RE.finditer(chunk):
        if m.start() < pos < m.end():
            feats["inside_entity"] = 1                       # www.boun|.|edu.tr
        elif pos == m.end():
            feats["entity_ends_here"] = 1                    # boun.edu.tr|,
    if c.sentence_continues or continues_after(chunk[pos + 1:]):
        feats["sentence_continues"] = 1                      # Dr|. Ahmet  vs  ... 1923|.
    return feats


def extract(c: Candidate, level: int = 3) -> dict[str, int]:
    """All features of a candidate up to the given feature set (1, 2 or 3)."""
    feats = set1(c)
    if level >= 2:
        feats.update(set2(c))
    if level >= 3:
        feats.update(set3(c))
    return feats
