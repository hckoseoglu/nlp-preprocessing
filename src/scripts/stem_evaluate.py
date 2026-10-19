"""Stemmer değerlendirmesi: UD-BOUN gold kök accuracy — toplam, POS, alt kümeler, baseline'lar, hata listesi.

Kullanım:
  python3 src/scripts/stem_evaluate.py --split dev            # tablo + results/errors_dev.tsv + results/tables_dev.md
  python3 src/scripts/stem_evaluate.py --split dev --ablation # Config varyantları
  python3 src/scripts/stem_evaluate.py --split test           # yalnız final (bir kez)
Baseline'lar: no-stem, fixed-prefix-5, Snowball (snowballstemmer), TurkishStemmer (pip; yalnız isim ekleri).
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "scripts"))
from stem_gold import Tok, fold, gold_root, load_split, read_derived  # noqa: E402
from stemmer import Config, Stemmer  # noqa: E402
from stemmer.lexicon import NOMINAL_POS  # noqa: E402

try:
    import snowballstemmer
    _SNOW = snowballstemmer.stemmer("turkish")
except Exception:  # pragma: no cover
    _SNOW = None
try:
    from TurkishStemmer import TurkishStemmer as _TS
    _TSTEM = _TS()
except Exception:  # pragma: no cover
    _TSTEM = None

POS_COLS = ["NOUN", "VERB", "ADJ", "PROPN", "ADV", "PRON", "AUX"]
SUBSETS = ["bare", "inflected", "derived", "oov", "copula", "lexical"]


def is_copula_fragment(t: Tok) -> bool:
    return t.upos in ("AUX", "PART") and t.lemma_n in ("y", "i")


def subsets_of(t: Tok, gold: str, train_forms: set[str]) -> set[str]:
    f = fold(t.form)
    s = set()
    cop = is_copula_fragment(t)
    if cop:
        s.add("copula")
    else:
        s.add("lexical")
    if f == gold:
        s.add("bare")
    elif gold == t.lemma_n:
        s.add("inflected")
    if gold != t.lemma_n:
        s.add("derived")
    if f not in train_forms:
        s.add("oov")
    return s


def accuracy_table(rows: list[tuple[str, list[str]]], toks: list[Tok], golds: list[str],
                   subs: list[set[str]]) -> str:
    cols = ["genel"] + POS_COLS + SUBSETS
    n_col = Counter()
    for t, sb in zip(toks, subs):
        n_col["genel"] += 1
        n_col[t.upos] += 1
        for x in sb:
            n_col[x] += 1
    out = ["| yöntem | " + " | ".join(f"{c} (n={n_col[c]})" for c in cols) + " |",
           "|---|" + "---|" * len(cols)]
    for name, preds in rows:
        ok = Counter()
        for t, g, p, sb in zip(toks, golds, preds, subs):
            if p == g:
                ok["genel"] += 1
                ok[t.upos] += 1
                for x in sb:
                    ok[x] += 1
        cells = [f"{100 * ok[c] / n_col[c]:.1f}" if n_col[c] else "-" for c in cols]
        out.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def classify_error(t: Tok, gold: str, pred: str, lex_roots: set[str]) -> str:
    f = fold(t.form)
    if is_copula_fragment(t):
        return "UD-kopula-parçacığı"
    if gold != t.lemma_n and pred == t.lemma_n:
        return "türetim-soyulmadı (under)"
    if gold == t.lemma_n and t.derived_from and pred == t.derived_from:
        return "türetim-fazla-soyuldu (over; gold lemma'yı korur)"
    if gold.startswith(pred) and len(pred) < len(gold):
        return "over-stemming"
    if pred.startswith(gold) and len(pred) > len(gold):
        return "under-stemming"
    if gold[:2] != f[:2] and gold[:1] != f[:1]:
        return "gold-gürültüsü/typo"
    if gold not in lex_roots:
        return "OOV-kök"
    if len(pred) == len(gold) and sum(a != b for a, b in zip(pred, gold)) <= 2:
        return "fonoloji"
    if pred in lex_roots and gold in lex_roots:
        return "belirsizlik (iki geçerli kök)"
    return "diğer"


def run(split: str, cfg: Config, n_errors: int, out_dir: Path, ablation: bool, use_pos: bool = False) -> None:
    derived = read_derived(ROOT / "lexicon" / "derived.tsv")
    toks = load_split(split)
    golds = [gold_root(t, derived) for t in toks]
    train_forms = {fold(t.form) for t in load_split("train")}
    subs = [subsets_of(t, g, train_forms) for t, g in zip(toks, golds)]

    st = Stemmer(config=cfg)
    t0 = time.time()
    ours_nopos = [fold(st.stem(t.form)) for t in toks]
    dt = time.time() - t0
    ours = ours_nopos
    rows = [("bizim (kural + sözlük)", ours_nopos)]
    if use_pos:
        ours = [fold(st.stem(t.form, t.upos)) for t in toks]
        rows.append(("bizim + gold POS", ours))
    rows += [
            ("no-stem", [fold(t.form) for t in toks]),
            ("fixed-prefix-5", [fold(t.form)[:5] for t in toks])]
    if _SNOW is not None:
        rows.append(("Snowball (snowballstemmer)", [fold(_SNOW.stemWord(fold(t.form))) for t in toks]))
    if _TSTEM is not None:
        rows.append(("TurkishStemmer (pip)", [fold(_TSTEM.stem(fold(t.form))) for t in toks]))

    tag = " (+gold POS)" if use_pos else ""
    lines = [f"# Stemming değerlendirmesi — {split}{tag} (n={len(toks)} içerik token; {dt:.1f}s)", "",
             "Gold = UD lemma, tip-seviyesi tutarlı DerivedFrom ile köke indirgenmiş (bkz. src/scripts/stem_gold.py).",
             "Alt kümeler: bare=form==gold · inflected=yalnız çekim · derived=gold≠lemma (türetim eşlemesi) · "
             "oov=form train'de görülmemiş · copula=UD'nin ayrı sözcük yaptığı ek-fiil parçacıkları (du, ydı, ken…) · "
             "lexical=copula dışı.", "", "## Accuracy (%)", "", accuracy_table(rows, toks, golds, subs), ""]

    # hata analizi
    lex_roots = set(st.lex.entries)
    errs: Counter = Counter()
    err_cls: dict = {}
    for t, g, p in zip(toks, golds, ours):
        if p != g:
            key = (fold(t.form), g, p, t.upos)
            errs[key] += 1
            err_cls[key] = classify_error(t, g, p, lex_roots)
    cls_tot = Counter()
    for key, n in errs.items():
        cls_tot[err_cls[key]] += n
    n_err = sum(errs.values())
    lines += [f"## Hata sınıfları ({split}; toplam {n_err} hata, {len(errs)} farklı)", "",
              "| sınıf | token | % hataların |", "|---|---|---|"]
    for c, n in cls_tot.most_common():
        lines.append(f"| {c} | {n} | {100 * n / n_err:.1f} |")
    lines += ["", f"## En sık {n_errors} hata", "", "| form | gold | bizim | UPOS | n | sınıf |", "|---|---|---|---|---|---|"]
    for (f, g, p, u), n in errs.most_common(n_errors):
        lines.append(f"| {f} | {g} | {p} | {u} | {n} | {err_cls[(f, g, p, u)]} |")
    suffix = "_pos" if use_pos else ""
    with (out_dir / f"errors_{split}{suffix}.tsv").open("w", encoding="utf-8") as fh:
        fh.write("form\tgold\tpred\tupos\tn\tclass\n")
        for (f, g, p, u), n in errs.most_common():
            fh.write(f"{f}\t{g}\t{p}\t{u}\t{n}\t{err_cls[(f, g, p, u)]}\n")

    if ablation:
        lines += ["", "## Ablation (genel accuracy, %)", "", "| varyant | genel | lexical | derived | oov |", "|---|---|---|---|---|"]
        variants = [("tam sistem", cfg),
                    ("ünlü uyumu kapalı", replace(cfg, harmony="off")),
                    ("ünlü uyumu katı", replace(cfg, harmony="strict")),
                    ("kaynaştırma kısıtı kapalı", replace(cfg, strict_buffer=False)),
                    ("ünsüz benzeşmesi kapalı", replace(cfg, strict_assimilation=False)),
                    ("onarım bayrakları kapalı", replace(cfg, strict_flags=False)),
                    ("derived.tsv eşlemesi kapalı", replace(cfg, use_derived=False)),
                    ("DER soyma kuralları kapalı", replace(cfg, use_der_rules=False)),
                    ("kopula tablosu kapalı", replace(cfg, use_copula=False)),
                    ("özel ad (kesme) yolu kapalı", replace(cfg, propn_apostrophe=False)),
                    ("OOV: dokunma", replace(cfg, oov="none")),
                    ("OOV: en kısa gövde", replace(cfg, oov="shortest")),
                    ("OOV: en uzun gövde", replace(cfg, oov="longest"))]
        for name, c in variants:
            s2 = Stemmer(config=c)
            preds = [fold(s2.stem(t.form)) for t in toks]
            acc = {k: [0, 0] for k in ("genel", "lexical", "derived", "oov")}
            for g, p, sb in zip(golds, preds, subs):
                for k in acc:
                    if k == "genel" or k in sb:
                        acc[k][1] += 1
                        acc[k][0] += (p == g)
            lines.append(f"| {name} | " + " | ".join(f"{100 * a / b:.1f}" for a, b in acc.values()) + " |")

    text = "\n".join(lines) + "\n"
    (out_dir / f"tables_{split}{suffix}.md").write_text(text, encoding="utf-8")
    print(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--errors", type=int, default=50)
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--oov", default=None)
    ap.add_argument("--harmony", default=None)
    ap.add_argument("--ranking", default=None)
    ap.add_argument("--pos", default=None, help="'gold': UPOS etiketi stemmer'a verilir (üst sınır / karşılaştırma)")
    args = ap.parse_args()
    cfg = Config()
    if args.oov:
        cfg = replace(cfg, oov=args.oov)
    if args.harmony:
        cfg = replace(cfg, harmony=args.harmony)
    if args.ranking:
        cfg = replace(cfg, ranking=args.ranking)
    run(args.split, cfg, args.errors, Path(args.out), args.ablation, use_pos=(args.pos == "gold"))


if __name__ == "__main__":
    main()
