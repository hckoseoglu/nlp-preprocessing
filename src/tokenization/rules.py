"""Rule-based tokenizer (Ecem): ordered regular-expression rules + one merge rule for periods.

It starts from the old regex baseline (src/tokenizer_baseline.py) and adds the UD-BOUN conventions
we found in the training split (the counts below are from train; dev is used only for measuring):

    ''              two single quotes used as a double quote → one token        12 of 12
    %25, %25'lik    the percent sign belongs to the number                      6 of 6
    gittim."        a period directly followed by a closing quote → one token   94 vs 42
    G.Saray, T.C.   capital initials with periods stay together                 8 vs 3
    vodka.com       domain names stay together                                  4 of 4
    !.. ?..         a ! or ? is split from the dots after it                    21 vs 10

plus our own convention for periods (TDK spelling, agreed with Hikmet; see tokenization/corpus.py):

    Dr. Ahmet, 3. sınıf   the period belongs to an abbreviation or an ordinal number when the
                          sentence continues after it; at the very end of the sentence it is the
                          sentence-final period and is split off: "... 1923 ."

Input is one sentence (in document mode the sentences come from Hikmet's splitter), output is the
list of tokens, e.g. RuleTokenizer().tokenize("Dr. Ahmet 3. kez geldi.") → ["Dr.", "Ahmet", "3.", "kez", "geldi", "."]
"""
from __future__ import annotations

import re

from .corpus import continues_after, keeps_period

# Alternatives are tried from top to bottom at every position; the first one that matches wins.
TOKEN_RE = re.compile(
    r"""
      https?://\S+?(?=[.,;:!?)"'”’]*(?:\s|$))          # URL, without trailing punctuation
    | [\w.+-]+@[\w-]+\.[\w.-]*\w                       # e-mail: ecem@gmail.com
    | [#@]\w+                                          # hashtag / mention: #nlp, @hikmet
    | \w+(?:[.-]\w+)*\.(?:com|net|org|edu|gov|info|tr)\b   # domain name: vodka.com, boun.edu.tr
    | %\d+(?:[.,]\d+)?(?:['’]\w+)?                     # percentage: %25, %25'lik
    | \d+(?:[.,:/]\d+)+(?:['’]\w+)?                    # number with separators: 19.30'da, 3,5, 08.02.2007
    | (?:[A-ZÇĞİÖŞÜ]\.)+(?:[A-ZÇĞİÖŞÜ]\w*(?:['’]\w+)?|['’]\w+)   # initials + word: G.Saray, F.Bahçe'yi, A.A.'yı
    | (?:[A-ZÇĞİÖŞÜ]\.){2,}                            # initials only: T.C., M.J.
    | \w+['’]\w+                                       # word with apostrophe suffix: Ankara'ya
    | (?<=[\w"”)])['’]\w+                              # suffix after a domain or a quote: Ucankus.com'da
    | \w+                                              # plain word or number
    | \.{2,}                                           # dots: ... ..
    | [!?]{2,}                                         # repeated ! and ?: !!! ?!
    | \.["”]                                           # period + closing quote: gittim."
    | ''                                               # two single quotes used as a double quote
    | [^\s\w]                                          # any other single symbol
    """,
    re.VERBOSE,
)
LIST_MARKER_RE = re.compile(r"\d+\.")              # a sentence that is only "1." (numbered list item)


class RuleTokenizer:
    """Tokenizes one sentence with TOKEN_RE, then attaches periods to abbreviations and ordinals."""

    def tokenize(self, sentence: str) -> list[str]:
        if LIST_MARKER_RE.fullmatch(sentence.strip()):
            return [sentence.strip()]
        spans = [m.span() for m in TOKEN_RE.finditer(sentence)]
        spans = self._attach_periods(sentence, spans)
        return [sentence[start:end] for start, end in spans]

    @staticmethod
    def _attach_periods(sentence: str, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Merges `Dr` + `.` → `Dr.` and `3` + `.` → `3.` when the sentence continues afterwards."""
        out: list[tuple[int, int]] = []
        for start, end in spans:
            previous = sentence[out[-1][0]:out[-1][1]] if out else ""
            is_attached_period = (sentence[start:end] == "." and out and out[-1][1] == start
                                  and keeps_period(previous) and continues_after(sentence[end:]))
            if is_attached_period:
                out[-1] = (out[-1][0], end)
            else:
                out.append((start, end))
        return out
