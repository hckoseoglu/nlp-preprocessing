"""Aday sınır çıkarımı + UD'den sahte paragraf korpusu.

Aday: `. ! ? …` dizisi ya da `: ;`, ardından isteğe bağlı kapanış tırnağı/parantez, ardından boşluk ya da
metin sonu (Reynar & Ratnaparkhi 1997: her `. ? !` bir aday; Gillick 2009: "L. R" bağlamı). Sol kelime L ve
sağ kelime R boşluk sınırlarından alınır — tokenizer gerekmez.

Sahte paragraf: UD-BOUN cümleleri doküman sırasında değil (sent_id'ler tür karışık) → seed'li karıştırıp
ardışık `size` cümleyi boşlukla birleştiririz; birleştirme noktaları gold sınırdır.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from textutil import OPEN_QUOTES, tr_lower

CANDIDATE_RE = re.compile(r"([.!?…]+|[;:])([\"”»’')\]}]*)(?=\s|$)")
_ELLIPSIS = {"…": "...", "....": "...", ".....": "..."}


@dataclass
class Candidate:
    start: int            # noktalamanın başladığı ofset
    end: int              # kapanış tırnağından sonraki ofset (sınır buradadır)
    punct: str            # normalize edilmiş noktalama: . ? ! ... ?! : ;
    close: str            # kapanış tırnağı/parantez ("" yoksa)
    left: str             # soldaki kelime, noktalama hariç (ham; tırnaklar duruyor)
    right: str            # sağdaki kelime (ham; "" → metin sonu)
    label: bool | None = None
    meta: dict = field(default_factory=dict)

    @property
    def at_end(self) -> bool:
        return self.right == ""


def _normalize_punct(p: str) -> str:
    p = p.replace("…", "...")
    if set(p) == {"."} and len(p) >= 2:
        return "..."
    if "." in p and len(p) > 1 and set(p) <= {".", "!", "?"}:
        # "?.." / "!..." gibi karışımlar → ilk işaret + ...
        return p[0] + "..." if p.endswith("..") else p[0]
    if len(p) > 1 and set(p) <= {"!", "?"}:
        return "?!" if "?" in p else "!"
    return p


def candidates(text: str) -> list[Candidate]:
    out: list[Candidate] = []
    for m in CANDIDATE_RE.finditer(text):
        before = text[: m.start()]
        after = text[m.end():]
        left = before.rsplit(None, 1)[-1] if before.strip() else ""
        parts = after.split(None, 2)
        right = parts[0] if parts else ""
        if right and not right.lstrip(OPEN_QUOTES) and len(parts) > 1:   # tek başına açılış tırnağı: `. " Fakat` → `"Fakat`
            right += parts[1]
        out.append(Candidate(start=m.start(), end=m.end(), punct=_normalize_punct(m.group(1)),
                             close=m.group(2), left=left, right=right))
    return out


def build_paragraphs(sentences: list[str], size: int = 5, seed: int = 0) -> list[tuple[str, set[int]]]:
    """Seed'li karıştır, `size`lık gruplar hâlinde boşlukla birleştir → (metin, gold sınır ofsetleri)."""
    sents = [s.strip() for s in sentences if s.strip()]
    rnd = random.Random(seed)
    rnd.shuffle(sents)
    paras: list[tuple[str, set[int]]] = []
    for i in range(0, len(sents), size):
        group = sents[i : i + size]
        text, bounds, pos = "", set(), 0
        for j, s in enumerate(group):
            if j:
                text += " "
                pos += 1
            text += s
            pos += len(s)
            if j < len(group) - 1:
                bounds.add(pos)
        paras.append((text, bounds))
    return paras


def labeled_candidates(text: str, bounds: set[int], include_end: bool = False) -> list[Candidate]:
    """Adayları gold sınırlarla etiketle. Metin sonundaki aday belirsiz değildir → varsayılan dışarıda."""
    out = []
    for c in candidates(text):
        if c.at_end and not include_end:
            continue
        c.label = c.end in bounds
        c.meta["text"] = text
        out.append(c)
    return out


def unreachable_bounds(text: str, bounds: set[int]) -> set[int]:
    """Hiçbir adayın denk gelmediği gold sınırlar (noktalamasız biten cümleler) — recall kaybı olarak sayılır."""
    ends = {c.end for c in candidates(text)}
    return {b for b in bounds if b not in ends}


def lowercase_paragraph(text: str) -> str:
    """'Tamamı küçük harf' test case'i. tr_lower uzunluğu korur → ofsetler/etiketler değişmez."""
    low = tr_lower(text)
    assert len(low) == len(text)
    return low


def is_challenging(c: Candidate, abbrs: set[str]) -> bool:
    """Zor durum: tırnak/parantez bitişik, L kısaltma/baş harf/sayı, ya da `: ; ...` işaretleri."""
    from textutil import is_abbreviation, is_initial, is_number
    if c.close or (c.right and c.right[0] in OPEN_QUOTES):
        return True
    if c.punct in (":", ";", "...", "?!"):
        return True
    if is_abbreviation(c.left, abbrs) or is_initial(c.left) or is_number(c.left):
        return True
    return False
