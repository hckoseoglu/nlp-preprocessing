"""Rule-based sentence splitter (rapor bölüm 4.2) + "her noktalamada böl" baseline'ı.

Kurallar, aday başına:
  1. `:` ve `;` cümle sonu sayılmaz.
  2. Soldaki kelime kısaltma (TDK listesi), baş harf (A. / T.C.) ya da nokta ile biten sayı (sıra sayısı: 2.) ise bölme.
  3. Sağdaki kelime küçük harfle başlıyorsa bölme — tırnak içindeki noktalamadan sonra `dedi` gibi devam eden
     cümleleri yakalar ("Geldi." dedi.).
  4. Aksi hâlde sağdaki kelime büyük harf / rakam / tırnak+büyük harf ile başlıyorsa böl.
"""
from __future__ import annotations

from textutil import ABBREV_FILE, first_alpha_case, is_abbreviation, is_initial, is_number, load_abbreviations, strip_quotes

from .corpus import Candidate, candidates


class Splitter:
    """Ortak iskelet: adayları çıkar, `decide` ile sınıfla, metni kes."""

    def decide(self, c: Candidate) -> bool:  # pragma: no cover - alt sınıflar
        raise NotImplementedError

    def boundaries(self, text: str) -> list[int]:
        return [c.end for c in candidates(text) if not c.at_end and self.decide(c)]

    def split(self, text: str) -> list[str]:
        sents, start = [], 0
        for b in self.boundaries(text):
            sents.append(text[start:b].strip())
            start = b
        tail = text[start:].strip()
        if tail:
            sents.append(tail)
        return [s for s in sents if s]


class AlwaysSplit(Splitter):
    """Baseline: `. ! ? ...` gördüğü her yerde böler (çoğunluk sınıfı; Gillick 2009'daki baseline)."""

    def decide(self, c: Candidate) -> bool:
        return c.punct not in (":", ";")


class RuleSplitter(Splitter):
    def __init__(self, abbrevs: set[str] | None = None):
        self.abbrevs = abbrevs if abbrevs is not None else load_abbreviations(ABBREV_FILE)

    def decide(self, c: Candidate) -> bool:
        if c.punct in (":", ";"):
            return False
        left = strip_quotes(c.left)
        if c.punct == "." and (is_abbreviation(left, self.abbrevs) or is_initial(left) or is_number(left)):
            return False
        case = first_alpha_case(c.right)
        return case in ("upper", "digit")
