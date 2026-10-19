"""UD Turkish-BOUN okuma + STEMMING GOLD tanımı (ortak yardımcı; build_gold / build_roots / evaluate kullanır).

Gold kök tanımı (bkz. results/progress_report_section.md):
  * İçerik tokeni: UPOS ∉ {PUNCT, SYM, NUM, X}; lemma 'null'/'_' değil.
  * gold = LEMMA (normalize: Türkçe lowercase, şapka düzleştirme, "din(I)" → "din").
  * (LEMMA, UPOS) tipi için MISC'teki DerivedFrom tip seviyesinde tutarlıysa gold = DerivedFrom kökü
    (train+dev+test üzerinden çoğunluk oyu; kabul: kök ≥2 harf, LEMMA'nın ön-eki (son ünsüz
    yumuşama toleransı), korpusta kendisi de lemma, destek ≥ min_count, tipin tokenlerinin ≥ min_ratio'su
    DerivedFrom taşıyor). Zincir: kök de türetilmişse köküne kadar (max 3 adım).
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # proje kökü (src/scripts/ → ../..)
sys.path.insert(0, str(ROOT / "src"))
from io_conllu import iter_conllu  # noqa: E402

DATA_DIR = ROOT / "data" / "UD_Turkish-BOUN"
SPLITS = ("train", "dev", "test")
CONTENT_EXCLUDE = {"PUNCT", "SYM", "NUM", "X"}
# kök-sonu ünsüz yumuşaması toleransı (kök 'kitap', lemma 'kitabevi' → ön-ek sayılır)
VOICED = {"p": "b", "ç": "c", "t": "d", "k": "ğ", "g": "ğ"}
_CIRC = str.maketrans("âîûÂÎÛ", "aiuaiu")


def tr_lower(s: str) -> str:
    """Türkçe'ye duyarlı küçük harf: önce I→ı, İ→i, sonra lower()."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def fold(s: str) -> str:
    """Değerlendirme normalizasyonu: tr_lower + şapka düzleştirme (â→a)."""
    return tr_lower(s).translate(_CIRC)


def norm_lemma(lemma: str) -> str:
    """UD lemma → karşılaştırılabilir biçim: 'din(I)' → 'din', şapka düz, küçük harf."""
    lemma = re.sub(r"\([^)]*\)$", "", lemma)
    return fold(lemma)


@dataclass
class Tok:
    form: str
    lemma: str          # ham UD lemma
    upos: str
    feats: str
    misc: dict
    split: str
    sent_id: str = ""

    @property
    def lemma_n(self) -> str:
        return norm_lemma(self.lemma)

    @property
    def derived_from(self) -> str | None:
        d = self.misc.get("DerivedFrom")
        return norm_lemma(d) if d else None


def _parse_misc(misc: str) -> dict:
    if not misc or misc == "_":
        return {}
    out = {}
    for kv in misc.split("|"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            out[k] = v
    return out


def load_split(split: str, data_dir: Path = DATA_DIR, content_only: bool = True) -> list[Tok]:
    """Bir split'in (içerik) tokenlerini döndürür. 'null' lemmalı tokenler atlanır."""
    toks: list[Tok] = []
    for sent in iter_conllu(data_dir / f"tr_boun-ud-{split}.conllu"):
        for w in sent.words:
            if content_only and w.upos in CONTENT_EXCLUDE:
                continue
            if w.lemma in ("null", "_", ""):
                continue
            toks.append(Tok(w.form, w.lemma, w.upos, w.feats, _parse_misc(w.misc), split, sent.sent_id))
    return toks


# --- derived.tsv ----------------------------------------------------------------

@dataclass
class DerivedEntry:
    lemma: str
    upos: str
    root: str          # zincirlenmiş nihai kök
    direct: str        # tek adımlık DerivedFrom kökü
    n_lemma: int       # bu (lemma, upos) tipinin toplam token sayısı
    n_df: int          # DerivedFrom taşıyan token sayısı
    n_agree: int       # çoğunluk köküyle aynı fikirde olan token sayısı
    splits: str        # tipin görüldüğü split'ler ("train,dev")
    depth: int = 1
    n_lemma_all: int = 0   # bu lemma'nın TÜM UPOS'lardaki toplam token sayısı (stemmer eşleme oranı için)


def root_is_prefix(lemma: str, root: str) -> bool:
    if lemma.startswith(root):
        return True
    last = root[-1]
    if last in VOICED and lemma.startswith(root[:-1] + VOICED[last]):
        return True
    return False


def build_derived(tokens: list[Tok], min_count: int = 2, min_ratio: float = 0.5,
                  chain: bool = True, max_depth: int = 3) -> tuple[dict[tuple[str, str], DerivedEntry], dict]:
    """(lemma, upos) → DerivedEntry. İkinci dönüş: istatistikler.

    Tip-seviyesi tutarlılık: tipin tokenlerinin en az `min_ratio`'su DerivedFrom taşımalı (yoksa
    annotator'lar sözcüğü sözlükselleşmiş saymış demektir: öğretmen 4/38 → kalır; önemli 39/46 → önem)
    ve çoğunluk kökünü en az `min_count` token desteklemeli.
    """
    all_lemmas = {t.lemma_n for t in tokens}
    by_type: dict[tuple[str, str], list[Tok]] = defaultdict(list)
    lemma_total: Counter = Counter()
    for t in tokens:
        by_type[(t.lemma_n, t.upos)].append(t)
        lemma_total[t.lemma_n] += 1

    stats = Counter()
    accepted: dict[tuple[str, str], DerivedEntry] = {}
    for key, toks in by_type.items():
        dfs = [t.derived_from for t in toks if t.derived_from]
        if not dfs:
            continue
        stats["types_with_df"] += 1
        lemma, upos = key
        root, n_agree = Counter(dfs).most_common(1)[0]
        reason = None
        if len(root) < 2:
            reason = "short_root"
        elif root == lemma:
            reason = "root_eq_lemma"
        elif not root_is_prefix(lemma, root):
            reason = "not_prefix"
        elif root not in all_lemmas:
            reason = "root_not_lemma"
        elif n_agree < min_count:
            reason = "low_count"
        elif len(dfs) / len(toks) < min_ratio:
            reason = "low_ratio"
        if reason:
            stats["rejected_" + reason] += 1
            continue
        splits = ",".join(s for s in SPLITS if any(t.split == s for t in toks))
        accepted[key] = DerivedEntry(lemma, upos, root, root, len(toks), len(dfs), n_agree, splits,
                                     n_lemma_all=lemma_total[lemma])
        stats["accepted"] += 1

    if chain:
        by_lemma: dict[str, list[DerivedEntry]] = defaultdict(list)
        for e in accepted.values():
            by_lemma[e.lemma].append(e)
        for e in accepted.values():
            seen = {e.lemma}
            cur = e.direct
            depth = 1
            while depth < max_depth:
                nxt = [x for x in by_lemma.get(cur, []) if x.upos != "PROPN" and x.n_lemma >= 3]
                if not nxt or cur in seen:
                    break
                # aynı UPOS varsa onu, yoksa en sık tipi al
                cand = sorted(nxt, key=lambda x: (x.upos != e.upos, -x.n_lemma))[0]
                if cand.direct in seen:
                    break
                seen.add(cur)
                cur = cand.direct
                depth += 1
            if depth > 1:
                stats["chained"] += 1
            e.root, e.depth = cur, depth
    return accepted, stats


DERIVED_COLS = ["lemma", "upos", "root", "direct", "depth", "n_lemma", "n_lemma_all", "n_df", "n_agree", "splits"]


def write_derived(path: Path, entries: dict[tuple[str, str], DerivedEntry]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(DERIVED_COLS) + "\n")
        for e in sorted(entries.values(), key=lambda x: (x.lemma, x.upos)):
            fh.write("\t".join(map(str, [e.lemma, e.upos, e.root, e.direct, e.depth,
                                         e.n_lemma, e.n_lemma_all, e.n_df, e.n_agree, e.splits])) + "\n")


def read_derived(path: Path) -> dict[tuple[str, str], DerivedEntry]:
    out: dict[tuple[str, str], DerivedEntry] = {}
    with open(path, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            if not line.strip():
                continue
            d = dict(zip(header, line.rstrip("\n").split("\t")))
            e = DerivedEntry(d["lemma"], d["upos"], d["root"], d["direct"], int(d["n_lemma"]),
                             int(d["n_df"]), int(d["n_agree"]), d["splits"], int(d["depth"]),
                             int(d.get("n_lemma_all", d["n_lemma"])))
            out[(e.lemma, e.upos)] = e
    return out


def gold_root(tok: Tok, derived: dict[tuple[str, str], DerivedEntry]) -> str:
    e = derived.get((tok.lemma_n, tok.upos))
    return e.root if e else tok.lemma_n
