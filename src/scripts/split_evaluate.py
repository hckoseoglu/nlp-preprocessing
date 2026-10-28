#!/usr/bin/env python3
"""Sentence splitting değerlendirmesi — rule-based vs NB (3 özellik seti) vs baseline'lar, 4 test case.

    python3 src/scripts/split_evaluate.py --split dev [--alpha 1.0] [--size 5] [--seed 0]
    python3 src/scripts/split_evaluate.py --split test          # yalnız BİR kez (kurallar dondurulduktan sonra)

Korpus: UD-BOUN cümleleri seed'li karıştırılıp `size`lık sahte paragraflara birleştirilir (corpus.build_paragraphs);
NB her zaman train'den eğitilir. Her sistem aday başına böl/bölme kararı verir.

Test case'ler:
  full         tüm adaylar
  challenging  tırnak/parantez bitişik, L kısaltma/baş harf/sayı, ya da `: ; ... ?!` (corpus.is_challenging)
  lowercase    aynı paragraflar tamamı Türkçe küçük harf (büyük harf ipucu yok)
  abbrev       elle hazırlanmış kısaltma/baş harf/sıra sayısı paragrafları (data/splitting/challenging_abbrev.txt)

Metrikler (aday düzeyi): accuracy; böl (S) ve bölme (N) sınıfları için P/R/F1; macro-F1.
Sınır düzeyi: gold sınırlar erişilemeyenler (noktalamasız biten cümleler) dâhil → boundary P/R/F1;
cümle düzeyi: gold cümlelerin birebir geri kazanılan oranı (sentence exact match).
Çıktı: results/tables_split_{split}.md, results/errors_split_{split}.tsv, resources/splitter_nb.json (set 3 modeli, CLI için).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from io_conllu import read_conllu  # noqa: E402
from splitting import AlwaysSplit, NBSplitter, RuleSplitter, build_paragraphs, labeled_candidates  # noqa: E402
from splitting.corpus import Candidate, is_challenging, lowercase_paragraph, unreachable_bounds  # noqa: E402
from splitting.ml import DEFAULT_MODEL  # noqa: E402
from textutil import load_abbreviations  # noqa: E402

DATA = ROOT / "data" / "UD_Turkish-BOUN"
ABBREV_SET = ROOT / "data" / "splitting" / "challenging_abbrev.txt"
RESULTS = ROOT / "results"
SEEDS = {"train": 1, "dev": 2, "test": 3}


# ----------------------------------------------------------------------------- metrikler

def _f(a: float, b: float) -> float:
    return a / b if b else 0.0


def candidate_metrics(decide, cands: list[Candidate]) -> dict[str, float]:
    tp = fp = fn = tn = 0
    for c in cands:
        p, g = decide(c), c.label
        if p and g:
            tp += 1
        elif p:
            fp += 1
        elif g:
            fn += 1
        else:
            tn += 1
    P, R = _f(tp, tp + fp), _f(tp, tp + fn)
    Pn, Rn = _f(tn, tn + fn), _f(tn, tn + fp)
    F, Fn = _f(2 * P * R, P + R), _f(2 * Pn * Rn, Pn + Rn)
    return {"n": len(cands), "acc": _f(tp + tn, len(cands)), "S_P": P, "S_R": R, "S_F": F,
            "N_P": Pn, "N_R": Rn, "N_F": Fn, "macro_F": (F + Fn) / 2}


def boundary_metrics(splitter, paras: list[tuple[str, set[int]]]) -> dict[str, float]:
    """Sınır düzeyi (erişilemeyen gold sınırlar FN) + cümle düzeyi exact match."""
    tp = fp = fn = 0
    sent_ok = sent_n = 0
    for text, bounds in paras:
        pred = set(splitter.boundaries(text))
        tp += len(pred & bounds)
        fp += len(pred - bounds)
        fn += len(bounds - pred)
        gold_sents = _cut(text, bounds)
        pred_sents = set(_cut(text, pred))
        sent_n += len(gold_sents)
        sent_ok += sum(s in pred_sents for s in gold_sents)
    P, R = _f(tp, tp + fp), _f(tp, tp + fn)
    return {"B_P": P, "B_R": R, "B_F": _f(2 * P * R, P + R), "sent_exact": _f(sent_ok, sent_n)}


def _cut(text: str, bounds: set[int]) -> list[str]:
    out, start = [], 0
    for b in sorted(bounds):
        out.append(text[start:b].strip())
        start = b
    out.append(text[start:].strip())
    return [s for s in out if s]


# ----------------------------------------------------------------------------- veri

def read_handmade(path: Path) -> list[tuple[str, set[int]]]:
    """Boş satırla ayrılmış bloklar; blok içinde her satır bir gold cümle → (paragraf, sınırlar)."""
    paras = []
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip() and not ln.startswith("#")]
        if lines:
            text, bounds, pos = "", set(), 0
            for j, ln in enumerate(lines):          # sıra korunur (build_paragraphs karıştırır)
                if j:
                    text, pos = text + " ", pos + 1
                text, pos = text + ln, pos + len(ln)
                if j < len(lines) - 1:
                    bounds.add(pos)
            paras.append((text, bounds))
    return paras


def load_split(name: str) -> list[str]:
    return [s.text for s in read_conllu(DATA / f"tr_boun-ud-{name}.conllu")]


# ----------------------------------------------------------------------------- ana

def fmt(m: dict[str, float], keys: tuple[str, ...]) -> str:
    return " | ".join(f"{m[k]:.3f}" if isinstance(m[k], float) else str(m[k]) for k in keys)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=("dev", "test"), default="dev")
    ap.add_argument("--alpha", type=float, default=1.0, help="NB Laplace α (dev'de seçilir)")
    ap.add_argument("--size", type=int, default=5, help="sahte paragraf uzunluğu (cümle)")
    ap.add_argument("--seed", type=int, default=0, help="karıştırma seed'ine eklenir")
    ap.add_argument("--no-save", action="store_true", help="resources/splitter_nb.json yazma")
    args = ap.parse_args()

    abbrs = load_abbreviations()
    train = build_paragraphs(load_split("train"), args.size, SEEDS["train"] + args.seed)
    train_c = [c for t, b in train for c in labeled_candidates(t, b)]
    eval_paras = build_paragraphs(load_split(args.split), args.size, SEEDS[args.split] + args.seed)
    cases: dict[str, tuple[list[tuple[str, set[int]]], list[Candidate]]] = {}
    full_c = [c for t, b in eval_paras for c in labeled_candidates(t, b)]
    cases["full"] = (eval_paras, full_c)
    cases["challenging"] = (eval_paras, [c for c in full_c if is_challenging(c, abbrs)])
    low_paras = [(lowercase_paragraph(t), b) for t, b in eval_paras]
    cases["lowercase"] = (low_paras, [c for t, b in low_paras for c in labeled_candidates(t, b)])
    if ABBREV_SET.exists():
        hand = read_handmade(ABBREV_SET)
        cases["abbrev"] = (hand, [c for t, b in hand for c in labeled_candidates(t, b)])

    systems = [("always-split (. ! ? ...)", AlwaysSplit()), ("rule-based", RuleSplitter(abbrs))]
    for lv in (1, 2, 3):
        systems.append((f"NB set {lv}", NBSplitter(level=lv, alpha=args.alpha, abbrevs=abbrs).fit(train_c)))
    punkt = _punkt()
    if punkt is not None:
        systems.append(("NLTK Punkt (tr)", punkt))

    unreach = sum(len(unreachable_bounds(t, b)) for t, b in eval_paras)
    n_bounds = sum(len(b) for t, b in eval_paras)
    suspect = sum(1 for c in full_c if not c.label and c.punct in (".", "!", "?", "...") and c.right[:1].isupper())
    lines = [f"# Sentence splitting — {args.split} (sahte paragraf {args.size} cümle, NB α={args.alpha}, train aday={len(train_c)}, "
             f"pozitif={sum(c.label for c in train_c)})", "",
             f"Gold sınır: {n_bounds}, noktalama ile erişilemeyen (noktalamasız/virgülle biten cümle): {unreach} "
             f"({100 * unreach / n_bounds:.1f}%) — sınır-düzeyi recall'da FN olarak sayılır.  ",
             f"Negatif adaylardan `. ! ?` + büyük harfle devam eden (gold'un tek birimde tuttuğu olası cümle sonu): {suspect}.", ""]
    keys = ("n", "acc", "S_P", "S_R", "S_F", "N_P", "N_R", "N_F", "macro_F")
    for case, (paras, cands) in cases.items():
        pos = sum(c.label for c in cands)
        lines += [f"## {case}  (aday={len(cands)}, böl={pos}, bölme={len(cands) - pos})", "",
                  "| sistem | n | acc | S P | S R | S F1 | N P | N R | N F1 | macro-F1 | B P | B R | B F1 | sent exact |",
                  "|---|" + "---|" * 13]
        for name, sp in systems:
            m = candidate_metrics(sp.decide, cands)
            if case == "challenging":
                bm = {"B_P": float("nan"), "B_R": float("nan"), "B_F": float("nan"), "sent_exact": float("nan")}
            else:
                bm = boundary_metrics(sp, paras)
            lines.append(f"| {name} | {fmt(m, keys)} | {fmt(bm, ('B_P', 'B_R', 'B_F', 'sent_exact'))} |")
        lines.append("")
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"tables_split_{args.split}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    # hata dökümü: rule ve NB set 3, full
    rule, nb3 = systems[1][1], systems[4][1]
    err = RESULTS / f"errors_split_{args.split}.tsv"
    with err.open("w", encoding="utf-8") as fh:
        fh.write("system\tgold\tpred\tpunct\tclose\tleft\tright\tcontext\n")
        for text, bounds in eval_paras:
            for c in labeled_candidates(text, bounds):
                for name, sp in (("rule", rule), ("nb3", nb3)):
                    p = sp.decide(c)
                    if p != c.label:
                        ctx = text[max(0, c.start - 30): c.end + 30].replace("\t", " ")
                        fh.write(f"{name}\t{int(c.label)}\t{int(p)}\t{c.punct}\t{c.close}\t{c.left}\t{c.right}\t{ctx}\n")
    print(f"\nhatalar → {err}")
    if not args.no_save and args.split == "dev":
        best_name, best = max(systems[2:5], key=lambda ns: candidate_metrics(ns[1].decide, full_c)["macro_F"])
        best.save(DEFAULT_MODEL)          # CLI dev'de macro-F1'i en yüksek seti kullanır (28 Eki: set 2)
        print(f"model → {DEFAULT_MODEL}  ({best_name}, dev macro-F1 en yüksek)")


def _punkt():
    """Dış baseline (cite: Kiss & Strunk 2006; NLTK). nltk ya da Türkçe Punkt modeli yoksa sessizce atlanır."""
    try:
        from nltk.tokenize import PunktTokenizer      # NLTK ≥ 3.9: punkt_tab verisi
        model = PunktTokenizer("turkish")
    except Exception:
        return None
    from splitting.rules import Splitter

    class Punkt(Splitter):
        def __init__(self):
            self._cache: dict[str, set[int]] = {}

        def boundaries(self, text: str) -> list[int]:
            if text not in self._cache:
                self._cache[text] = {e for _, e in model.span_tokenize(text)}
            return sorted(b for b in self._cache[text] if b < len(text.rstrip()))

        def decide(self, c: Candidate) -> bool:   # aday-düzeyi: Punkt bu ofsette böldü mü?
            text = c.meta.get("text", "")
            return c.end in set(self.boundaries(text)) if text else False

    return Punkt()


if __name__ == "__main__":
    main()
