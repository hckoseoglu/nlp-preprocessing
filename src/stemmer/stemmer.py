"""Ana stemmer: END'den geriye DFS ile ek soyma + kök sözlüğünde EN UZUN kök seçimi.

Algoritma (bkz. lexicon/SOURCES.md ve results/progress_report_section.md):
  stem(word):
    w = tr_lower(word); kesme işareti varsa sol parça; büyük harfle başlıyorsa özel ad yolu
    ek-fiil parçacığı ise (du, ydı, ken ...) UD lemma sözleşmesi ('y'/'i')
    DFS(state=END, rest=w): ters geçişlerden allomorf eşleştir, kısıtları uygula (kaynaştırma, ünsüz
      benzeşmesi, K-son, ünlü uyumu[soft]); N0/V0'da gövde ∪ onarım varyantlarını sözlükte ara
      (POS uyumlu, bayraklar izin veriyorsa) → aday
    seçim: uyum ihlali olmayan > en uzun kök > frekans > az onarım > az ek
    türetim: seçilen kök train derived.tsv'de ise köküne eşle
    aday yoksa: OOV stratejisi (büyük harfli ise dokunma; değilse ≥2 harfli geçerli ekleri soy)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from .lexicon import Lexicon, RootEntry
from .morphotactics import ROOT_STATES, START, Morphotactics
from .phonology import (DEVOICE, VOWELS, assimilation_ok, buffer_ok, fold, harmony_ok,
                        narrowing_variants, root_variants, tr_capitalize)
from .suffixes import Allomorph, load_allomorphs

LEX_DIR = Path(__file__).resolve().parents[2] / "lexicon"   # proje kökü/lexicon
NOMINAL_CLASSES = {"PLUR", "POSS", "CASE", "CASE_N", "KI"}   # özel ad dalında izin verilen ekler (ek-fiil yok)
FROZEN_POS = {"ADP", "CCONJ", "SCONJ", "INTJ"}   # bu sınıftaki kökler ek almaz (için-de ✗ → iç-in-de)


@dataclass
class Config:
    strict_buffer: bool = True        # Kısıt 1: kaynaştırma harfi ünlü/ünsüz dağılımı
    strict_assimilation: bool = True  # Kısıt 3: D→t/C→ç yalnız sert ünsüzden sonra
    harmony: str = "soft"             # Kısıt 2: ünlü uyumu — "off" | "soft" (ceza) | "strict" (ele)
    strict_flags: bool = True         # onarımlar (yumuşama/düşme/ikizleşme) kök bayrağı ister
    use_derived: bool = True          # train derived.tsv eşlemesi
    use_der_rules: bool = True        # sözlükte olmayan gövdeler için DER ek soyma
    use_copula: bool = True           # ek-fiil parçacık tablosu
    propn_apostrophe: bool = True     # Kesme + büyük harf → özel ad yolu
    propn_whole: bool = True          # Büyük harfli ve sözlükte görülmüş tam sözcük → dokunma
    oov: str = "strip2"               # "none" | "strip2" | "shortest" | "longest"
    min_oov_root: int = 3
    ranking: str = "score"            # "score" (log-frekans skoru) | "longest" (saf en uzun kök) | "attested" (önce UD'de görülen)
    # skor = w_freq·ln(freq+1) + w_len·|kök| − Σ ek maliyeti − w_repair·#onarım − w_harmony·ihlal
    # ek maliyeti sınıfa göre: çekim (w_infl) < çatı (w_voice) ≈ isim-fiil/sıfat-fiil (w_vn) < türetim (w_der)
    w_freq: float = 1.0
    w_len: float = 0.5
    w_infl: float = 0.7
    w_voice: float = 1.0
    w_vn: float = 1.0
    w_der: float = 3.0
    w_repair: float = 0.5
    w_harmony: float = 5.0
    w_whole: float = 1.0              # ek soyulmamış, korpusta görülmüş tam sözcük bonusu (biri, deniz, kim)
    w_whole0: float = 0.0             # ek soyulmamış, yalnız TRmorph'ta olan tam sözcük bonusu (yoksun, kesinlikle)
    w_pos: float = 1.0                # (isteğe bağlı POS girdisi varsa) kökün sözlük POS'u verilen etiketle aynıysa bonus
    f_cap: float = 5.0                # ln(freq+1) tavanı: çok sık kökler (bir, de, o) her şeyi yutmasın
    min_root: int = 2                 # tek harfli kök yalnız zamir (o)


@dataclass
class Candidate:
    root: str                 # sözlükte eşleşen yüzey (onarım sonrası)
    canonical: str            # döndürülecek kök
    entry: RootEntry | None
    state: str
    suffixes: tuple[str, ...] # soyulan ek id'leri (sağdan sola)
    classes: tuple[str, ...] = ()   # soyulan eklerin sınıfları
    repairs: frozenset[str] = field(default_factory=frozenset)
    violations: int = 0

    @property
    def der_stripped(self) -> bool:
        return any(s.startswith("DER_") for s in self.suffixes)

    def sort_key(self, cfg: "Config") -> tuple:
        inv = self.entry.inv_harmony if self.entry else False
        viol = 0 if inv else self.violations
        freq = self.entry.freq if self.entry else 0
        if cfg.ranking == "score":
            cost = 0.0
            for c in self.classes:
                if c.startswith("DER"):
                    cost += cfg.w_der
                elif c == "VOICE":
                    cost += cfg.w_voice
                elif c in ("VN", "PART"):
                    cost += cfg.w_vn
                else:
                    cost += cfg.w_infl
            whole = 0.0 if self.suffixes else (cfg.w_whole if freq > 0 else cfg.w_whole0)
            score = (cfg.w_freq * min(math.log(freq + 1), cfg.f_cap) + cfg.w_len * len(self.root) - cost
                     - cfg.w_repair * len(self.repairs) - cfg.w_harmony * viol + whole)
            return (-score, -len(self.root), -freq)
        penalty = 0 if viol == 0 else 1
        tier = 0 if (cfg.ranking != "attested" or freq > 0) else 1
        return (penalty, tier, -len(self.root), -freq, len(self.repairs), len(self.suffixes))

    def __str__(self) -> str:
        sfx = "+".join(self.suffixes) if self.suffixes else "∅"
        pos = self.entry.pos if self.entry else "?"
        extra = []
        if self.repairs:
            extra.append("repair=" + ",".join(sorted(self.repairs)))
        if self.violations:
            extra.append(f"harmony_viol={self.violations}")
        return f"{self.canonical}[{pos}] ← {self.root} + {sfx}" + (" (" + "; ".join(extra) + ")" if extra else "")


class Stemmer:
    def __init__(self, lex_dir: str | Path | None = None, config: Config | None = None):
        lex_dir = Path(lex_dir) if lex_dir else LEX_DIR
        self.cfg = config or Config()
        self.suffixes, self.allomorphs = load_allomorphs(lex_dir / "suffixes.tsv")
        self.mt = Morphotactics(lex_dir / "morphotactics.tsv", self.suffixes, self.allomorphs)
        self.lex = Lexicon(lex_dir)

    # ------------------------------------------------------------------ public API
    def stem(self, word: str, pos: str | None = None) -> str:
        """Kök döndürür. `pos` (UPOS; isteğe bağlı) verilirse adaylar fiil/isim ağına göre süzülür ve
        sözlük POS'u eşleşen kök bonus alır; AUX için süzme yapılmaz (ol- fiil, değil/mi isim)."""
        w0 = word.strip()
        if not w0 or not any(ch.isalpha() for ch in w0):
            return w0
        if w0[0] in "@#" or "://" in w0 or ("@" in w0 and "." in w0):
            return w0                                 # @mention, #hashtag, URL, e-posta: dokunma (ham metin)
        if "'" in w0 or "’" in w0:
            base = w0.replace("’", "'").split("'")[0]
            if not base:
                return fold(w0)
            if not base[0].isalpha():
                return fold(base)                     # 19.30'da → 19.30
            if base[0].isupper() and self.cfg.propn_apostrophe:
                return self._stem_proper(base)
            w0 = base
        w = fold(w0)
        if not w.replace("-", "").isalpha():
            return w
        if self.cfg.use_copula and w in self.lex.copula:
            return self.lex.copula[w]
        if w0[0].isupper() and self.cfg.propn_whole and any(e.pos == "PROPN" and e.freq > 0 for e in self.lex.lookup(w)):
            return w                                  # büyük harfli + korpusta ÖZEL AD olarak görülmüş: Deniz, Haldun
        best = self._select(self._analyze(w, allow_der=self.cfg.use_der_rules), pos)
        if best is not None:
            root = best.canonical
            if self.cfg.use_derived:
                root = self.lex.derived.get(root, root)
            return root
        if w0[0].isupper():                           # büyük harfli OOV: özel ad varsay, dokunma
            return w
        return self._oov(w)

    def stem_tokens(self, tokens: list[str], pos_tags: list[str] | None = None) -> list[str]:
        if pos_tags is None:
            return [self.stem(t) for t in tokens]
        return [self.stem(t, p) for t, p in zip(tokens, pos_tags)]

    def analyze(self, word: str, pos: str | None = None) -> list[Candidate]:
        """Hata ayıklama: tüm adaylar, en iyisi başta."""
        w = fold(word.split("'")[0] if "'" in word else word)
        cands = self._pos_filter(self._analyze(w, allow_der=self.cfg.use_der_rules), pos)
        return sorted(cands, key=lambda c: self._key(c, pos))

    # ------------------------------------------------------------------ core
    def _analyze(self, w: str, allow_der: bool = True, allowed: set[str] | None = None) -> list[Candidate]:
        results: list[Candidate] = []
        visited: set = set()
        self._dfs(START, w, None, (), (), 0, results, visited, allow_der, allowed)
        return results

    def _dfs(self, state: str, rest: str, right: str | None, path: tuple[str, ...], classes: tuple[str, ...],
             viol: int, results: list[Candidate], visited: set, allow_der: bool, allowed: set[str] | None) -> None:
        key = (state, rest, right)
        if key in visited:
            return
        visited.add(key)
        if state in ROOT_STATES:
            self._try_root(state, rest, right, path, classes, viol, results)
        for prev in self.mt.reverse_eps(state):
            self._dfs(prev, rest, right, path, classes, viol, results, visited, allow_der, allowed)
        if len(rest) <= 1:
            return
        for allo, prev in self.mt.reverse_edges(state, rest[-1]):
            if allowed is not None and allo.cls not in allowed:
                continue
            if not allow_der and allo.cls.startswith("DER"):
                continue
            s = allo.surface
            if len(s) >= len(rest) or not rest.endswith(s):
                continue
            stem_rest = rest[:-len(s)]
            ok, v = self._check(stem_rest, allo, right)
            if not ok:
                continue
            for sr in [stem_rest] + narrowing_variants(stem_rest, s, allo.is_yor):
                self._dfs(prev, sr, s[0], path + (allo.id,), classes + (allo.cls,), viol + v, results, visited,
                          allow_der, allowed)

    def _check(self, stem: str, allo: Allomorph, right: str | None) -> tuple[bool, int]:
        cfg = self.cfg
        if cfg.strict_buffer and not buffer_ok(stem, allo.opt, allo.opt_present):
            return False, 0
        if cfg.strict_assimilation and not assimilation_ok(stem, allo.surface[0], allo.init_archi):
            return False, 0
        if allo.final_k == "ğ" and (right is None or right not in VOWELS):
            return False, 0
        if allo.final_k == "k" and right is not None and right in VOWELS:
            return False, 0
        v = 0
        if allo.first_vowel is not None and cfg.harmony != "off":
            if not harmony_ok(stem, allo.first_vowel, allo.first_archi):
                if cfg.harmony == "strict":
                    return False, 0
                v = 1
        return True, v

    def _try_root(self, state: str, rest: str, right: str | None, path: tuple[str, ...], classes: tuple[str, ...],
                  viol: int, results: list[Candidate]) -> None:
        cat = ROOT_STATES[state]
        for variant, repairs in root_variants(rest, right):
            for e in self.lex.lookup(variant):
                if e.category != cat:
                    continue
                if path and e.pos in FROZEN_POS:
                    continue
                if len(variant) < self.cfg.min_root and not (e.pos == "PRON" and path):
                    continue
                if self.cfg.strict_flags and not e.allows(repairs):
                    continue
                results.append(Candidate(variant, e.canonical, e, state, path, classes, repairs, viol))

    def _key(self, c: Candidate, pos: str | None = None) -> tuple:
        k = c.sort_key(self.cfg)
        if pos and self.cfg.ranking == "score" and c.entry is not None and c.entry.pos == pos:
            k = (k[0] - self.cfg.w_pos,) + k[1:]      # skor tuple'ında ilk eleman -skor
        return k

    def _pos_filter(self, cands: list[Candidate], pos: str | None) -> list[Candidate]:
        """POS verilmişse adayları kök kategorisine göre süz (VERB → fiil kökü, diğerleri → isim kökü).
        Süzme sonucu boşsa tüm adaylar korunur. AUX süzülmez."""
        if not pos or pos == "AUX" or not cands:
            return cands
        want = "V" if pos == "VERB" else "N"
        kept = [c for c in cands if c.entry is not None and c.entry.category == want]
        return kept or cands

    def _select(self, cands: list[Candidate], pos: str | None = None) -> Candidate | None:
        cands = self._pos_filter(cands, pos)
        if not cands:
            return None
        return min(cands, key=lambda c: self._key(c, pos))

    # ------------------------------------------------------------------ special paths
    def _stem_proper(self, base: str) -> str:
        """Kesme işaretli özel ad: yalnız isim çekimi soyulur, kök sözlükte olmalı; yoksa olduğu gibi."""
        w = fold(base)
        cands = [c for c in self._analyze(w, allow_der=False, allowed=NOMINAL_CLASSES)
                 if c.entry is not None and c.entry.category == "N"]
        best = self._select(cands)
        if best is None or not best.suffixes:
            return base
        return tr_capitalize(best.canonical)

    def _oov(self, w: str) -> str:
        cfg = self.cfg
        if cfg.oov == "none":
            return w
        stems: list = []
        self._dfs_stems(START, w, None, (), stems, set())
        good = [(r, p, right) for r, p, right, _st in stems
                if p and len(r) >= cfg.min_oov_root and any(ch in VOWELS for ch in r)]
        if cfg.oov == "strip2":                       # tek harfli ekler OOV'de güvenilmez
            good = [(r, p, right) for r, p, right in good if all(len(a) >= 2 for a in p)]
        if not good:
            return w
        if cfg.oov == "longest":
            r, p, right = max(good, key=lambda x: len(x[0]))
        else:
            r, p, right = min(good, key=lambda x: (len(x[0]), len(x[1])))
        if right is not None and right in VOWELS and r[-1] in DEVOICE:
            r = r[:-1] + DEVOICE[r[-1]]
        return r

    def _dfs_stems(self, state: str, rest: str, right: str | None, path: tuple[str, ...],
                   out: list, visited: set, skip_cls: frozenset = frozenset({"DER_NN", "DER_NV", "DER_VN"})) -> None:
        """Sözlüksüz DFS (OOV yolu ve kural-tabanlı baseline): ünlü uyumu KATI; `skip_cls` sınıfları soyulmaz;
        yol allomorf yüzeyleri olarak tutulur; çıktı (kalan, yol, sağ bağlam, kök durumu)."""
        key = (state, rest, right)
        if key in visited:
            return
        visited.add(key)
        if state in ROOT_STATES:
            out.append((rest, path, right, state))
        for prev in self.mt.reverse_eps(state):
            self._dfs_stems(prev, rest, right, path, out, visited, skip_cls)
        if len(rest) <= 1:
            return
        for allo, prev in self.mt.reverse_edges(state, rest[-1]):
            if allo.cls in skip_cls:
                continue
            s = allo.surface
            if len(s) >= len(rest) or not rest.endswith(s):
                continue
            stem_rest = rest[:-len(s)]
            if not buffer_ok(stem_rest, allo.opt, allo.opt_present):
                continue
            if not assimilation_ok(stem_rest, s[0], allo.init_archi):
                continue
            if allo.first_vowel is not None and not harmony_ok(stem_rest, allo.first_vowel, allo.first_archi):
                continue
            for sr in [stem_rest] + narrowing_variants(stem_rest, s, allo.is_yor):
                self._dfs_stems(prev, sr, s[0], path + (s,), out, visited, skip_cls)

    def rule_stem(self, word: str, network: str = "V", strategy: str = "shortest", strip_voice: bool = True,
                  min_stem: int = 2) -> str:
        """SÖZLÜKSÜZ kural-tabanlı soyma (Eryiğit & Adalı tarzı baseline): yalnız ek listesi + FSA + ses kısıtları.
        network: "V" fiil ağı, "N" isim ağı, None ikisi. strategy: "shortest" (en çok soy; makaledeki 'en kısa kök')
        | "longest" (en az soy) | "strip2" (yalnız ≥2 harfli eklerden oluşan en uzun zincir). Kök sözlüğü, frekans,
        türetim eşlemesi kullanılmaz."""
        w = fold(word)
        if not w.replace("-", "").isalpha():
            return w
        skip = {"DER_NN", "DER_NV", "DER_VN"}
        if not strip_voice:
            skip.add("VOICE")
        stems: list = []
        self._dfs_stems(START, w, None, (), stems, set(), frozenset(skip))
        want = {"V": "V0", "N": "N0"}.get(network)
        good = [(r, p, right) for r, p, right, st_ in stems
                if (want is None or st_ == want) and len(r) >= min_stem and any(ch in VOWELS for ch in r)]
        if not good:
            return w
        if strategy == "strip2":                      # tek harfli ekleri sayma (OOV yolundaki politika)
            good = [g for g in good if all(len(a) >= 2 for a in g[1])] or [(w, (), None)]
        if strategy == "longest":
            r, p, right = max(good, key=lambda x: (len(x[0]), -len(x[1])))
        else:
            r, p, right = min(good, key=lambda x: (len(x[0]), len(x[1])))
        if right is not None and right in VOWELS and r[-1] in DEVOICE:
            r = r[:-1] + DEVOICE[r[-1]]
        return r


if __name__ == "__main__":
    import sys
    st = Stemmer()
    words = sys.argv[1:] or ["kitabı", "gidiyordum", "öğretmenlerimizin", "önemliydi", "öldürülen",
                              "gelişmelerden", "İstanbul'daki", "burnu", "bekliyor", "kalemler"]
    for w in words:
        print(f"{w:22} → {st.stem(w)}")
        for c in st.analyze(w)[:4]:
            print("      ", c)
