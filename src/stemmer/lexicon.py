"""Kök sözlüğü (lexicon/roots.tsv), istisnalar (exceptions.tsv), türetim eşlemesi (derived.tsv, yalnız
train satırları) ve ek-fiil parçacıkları (copula_fragments.tsv)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

NOMINAL_POS = {"NOUN", "ADJ", "ADV", "PRON", "PROPN", "DET", "ADP", "CCONJ", "SCONJ", "PART", "INTJ",
               "AUX", "NUM"}
VERBAL_POS = {"VERB"}


@dataclass(frozen=True)
class RootEntry:
    root: str            # yüzey (sözlükte eşleşen biçim; istisnalarda düzensiz biçim)
    canonical: str       # döndürülecek kök (istisnalarda farklı: bana → ben)
    pos: str
    voicing: bool
    vowel_drop: bool
    inv_harmony: bool
    doubling: bool
    derived: bool
    freq: int
    source: str

    @property
    def category(self) -> str:
        return "V" if self.pos in VERBAL_POS else "N"

    def allows(self, repairs: frozenset[str]) -> bool:
        """Onarım bayrakları kökün izin verdikleriyle uyumlu mu?"""
        for r in repairs:
            if r == "voicing" and not self.voicing:
                return False
            if r == "vowel_drop" and not self.vowel_drop:
                return False
            if r == "doubling" and not self.doubling:
                return False
        return True


class Lexicon:
    def __init__(self, lex_dir: Path):
        self.entries: dict[str, list[RootEntry]] = defaultdict(list)
        self._load_roots(lex_dir / "roots.tsv")
        self._load_exceptions(lex_dir / "exceptions.tsv")
        self.derived: dict[str, str] = {}
        p = lex_dir / "derived.tsv"
        if p.exists():
            self._load_derived(p)
        self.copula: dict[str, str] = {}
        p = lex_dir / "copula_fragments.tsv"
        if p.exists():
            self._load_copula(p)

    def _load_roots(self, path: Path) -> None:
        with path.open(encoding="utf-8") as fh:
            header = fh.readline().rstrip("\n").split("\t")
            for line in fh:
                if not line.strip():
                    continue
                d = dict(zip(header, line.rstrip("\n").split("\t")))
                e = RootEntry(d["root"], d["root"], d["pos"], d["voicing"] == "1", d["vowel_drop"] == "1",
                              d["inv_harmony"] == "1", d.get("doubling", "0") == "1", d["derived"] == "1",
                              int(d["freq"]), d.get("source", ""))
                self.entries[e.root].append(e)

    def _load_exceptions(self, path: Path) -> None:
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            form, root, pos = line.split("\t")[:3]
            freq = max((e.freq for e in self.entries.get(root, [])), default=0)
            self.entries[form].append(RootEntry(form, root, pos, False, False, False, False, False, freq, "exc"))

    def _load_derived(self, path: Path) -> None:
        """lemma → kök; yalnız train'de görülen tipler (dev/test sızıntısı olmasın). Lemma'nın türetim-eşlemeli
        tiplerinin token toplamı, lemma'nın tüm tokenlerinin en az yarısı olmalı (özellik NOUN→özellik kalır)."""
        rows: dict[str, list[tuple[int, int, str]]] = defaultdict(list)   # lemma → [(n_lemma, n_all, root)]
        with path.open(encoding="utf-8") as fh:
            header = fh.readline().rstrip("\n").split("\t")
            for line in fh:
                if not line.strip():
                    continue
                d = dict(zip(header, line.rstrip("\n").split("\t")))
                if "train" not in d["splits"].split(","):
                    continue
                rows[d["lemma"]].append((int(d["n_lemma"]), int(d.get("n_lemma_all", d["n_lemma"])), d["root"]))
        for lemma, lst in rows.items():
            n_all = max(x[1] for x in lst)
            if sum(x[0] for x in lst) * 2 < n_all:
                continue
            self.derived[lemma] = max(lst)[2]

    def _load_copula(self, path: Path) -> None:
        with path.open(encoding="utf-8") as fh:
            header = fh.readline().rstrip("\n").split("\t")
            for line in fh:
                if not line.strip() or line.startswith("#"):
                    continue
                d = dict(zip(header, line.rstrip("\n").split("\t")))
                self.copula[d["form"]] = d["lemma"]

    def lookup(self, surface: str) -> list[RootEntry]:
        return self.entries.get(surface, [])

    def __contains__(self, surface: str) -> bool:
        return surface in self.entries

    def max_freq(self, surface: str) -> int:
        return max((e.freq for e in self.entries.get(surface, [])), default=0)
