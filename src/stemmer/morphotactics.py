"""Morfotaktik FSA (lexicon/morphotactics.tsv) — ileri geçişler okunur, ters indeks kurulur.

Ters yürütme: ileri `s -x-> t` geçişi için END'den başlayan DFS, t durumunda x allomorfunu kelimenin
sonundan eşleştirip s durumuna geçer. Allomorflar son harfe göre indekslenir (hız).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .suffixes import Allomorph, Suffix

START = "END"
ROOT_STATES = {"N0": "N", "V0": "V"}   # kök kabul durumları → kök kategorisi


@dataclass
class Transition:
    src: str
    label: str
    dst: str


class Morphotactics:
    def __init__(self, path: Path, suffixes: list[Suffix], allomorphs: list[Allomorph]):
        self.transitions: list[Transition] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            src, label, dst = line.split("\t")[:3]
            self.transitions.append(Transition(src, label, dst))
        self.states = {t.src for t in self.transitions} | {t.dst for t in self.transitions}

        by_id: dict[str, list[Allomorph]] = defaultdict(list)
        by_cls: dict[str, list[Allomorph]] = defaultdict(list)
        for a in allomorphs:
            by_id[a.suffix.id].append(a)
            by_cls[a.suffix.cls].append(a)
        known = set(by_id) | set(by_cls) | {"EPS"}

        # ters indeks: dst → {son harf → [(allomorf, src)]} ; eps: dst → [src]
        self.rev: dict[str, dict[str, list[tuple[Allomorph, str]]]] = defaultdict(lambda: defaultdict(list))
        self.rev_eps: dict[str, list[str]] = defaultdict(list)
        for t in self.transitions:
            if t.label == "EPS":
                self.rev_eps[t.dst].append(t.src)
                continue
            if t.label not in known:
                raise ValueError(f"morphotactics: bilinmeyen etiket {t.label!r}")
            allos = by_id.get(t.label) or by_cls.get(t.label, [])
            for a in allos:
                self.rev[t.dst][a.surface[-1]].append((a, t.src))

    def reverse_edges(self, state: str, last_char: str) -> list[tuple[Allomorph, str]]:
        return self.rev.get(state, {}).get(last_char, [])

    def reverse_eps(self, state: str) -> list[str]:
        return self.rev_eps.get(state, [])
