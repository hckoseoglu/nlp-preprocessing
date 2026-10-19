#!/usr/bin/env python3
"""CMPE 561 — Türkçe preprocessing toolkit, tek giriş noktası (CLI).

Bir cümle, bir dosya ya da UD Turkish-BOUN'un bir split'i üzerinde istenen adımı çalıştırır.

  python3 run.py stem      --text "Kitapları okuyordum."            # → kitap oku .
  python3 run.py stopword  --text "Bu bir deneme cümlesidir."       # → deneme cümlesidir .
  python3 run.py pipeline  --text "..."                             # normalize → stopword → stem
  python3 run.py normalize --text "..."                             # Ecem'in modülü (src/normalization.py)
  python3 run.py tokenize  --text "..."                             # basit regex tokenizer
  python3 run.py stem      --file cumleler.txt                      # her satır bir cümle
  python3 run.py stem      --split dev --eval [--pos]               # gold token'lar, kök doğruluğu
  python3 run.py stopword  --split test --eval --list union         # UPOS-proxy P/R/F1
  python3 run.py stem      --conllu baska.conllu --eval --format tsv

Çıktı biçimi: --format text (varsayılan: işlenmiş cümle) | tsv (token başına satır) | json.
Yalnız standart kütüphane; stemmer için lexicon/, stopword için resources/ kullanılır.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # proje kökü (src/cli.py → ..)
for _p in (ROOT / "src", ROOT / "src" / "scripts"):
    sys.path.insert(0, str(_p))

from io_conllu import read_conllu  # noqa: E402
from tokenizer_baseline import tokenize  # noqa: E402

DATA_DIR = ROOT / "data" / "UD_Turkish-BOUN"
RESOURCES = ROOT / "resources"
STOPWORD_FILES = {"static": RESOURCES / "stopwords_tr.txt", "dynamic": RESOURCES / "stopwords_dynamic_boun.txt"}
TASKS = ("tokenize", "normalize", "stopword", "stem", "pipeline")


@dataclass
class Item:
    """Bir cümle: yüzey token'lar (+ dataset modunda gold POS ve Word nesneleri)."""
    tokens: list[str]
    pos: list[str] | None = None
    words: list = field(default_factory=list)
    sent_id: str = ""
    text: str = ""


# ----------------------------------------------------------------------------- girdi

def load_items(args) -> tuple[list[Item], list]:
    """--text / --file ham metin (regex tokenizer); --split / --conllu gold token'lar. Sentence listesi eval için."""
    if args.text is not None:
        return [Item(tokenize(args.text), text=args.text)], []
    if args.file:
        lines = [ln.strip() for ln in Path(args.file).read_text(encoding="utf-8").splitlines() if ln.strip()]
        return [Item(tokenize(ln), text=ln) for ln in lines], []
    path = Path(args.conllu) if args.conllu else DATA_DIR / f"tr_boun-ud-{args.split}.conllu"
    if not path.exists():
        sys.exit(f"CoNLL-U bulunamadı: {path}")
    sents = read_conllu(path)
    items = [Item([w.form for w in s.words], [w.upos for w in s.words], s.words, s.sent_id, s.text) for s in sents]
    return items, sents


# ----------------------------------------------------------------------------- adımlar

class Steps:
    """Adımlar tembel yüklenir: yalnız istenen görevin kaynakları okunur."""

    def __init__(self, args):
        self.args = args
        self._stemmer = None
        self._stopset = None
        self._normalize = None
        self._norm_warned = False

    # normalize ---------------------------------------------------------------
    def normalize(self, tokens: list[str]) -> list[str]:
        if self._normalize is None:
            from normalization import normalize_tokens  # src/normalization.py (Ecem)
            self._normalize = normalize_tokens
        try:
            return self._normalize(tokens)
        except NotImplementedError as e:
            if self.args.task == "normalize":
                sys.exit(f"normalization hazır değil: {e}")
            if not self._norm_warned:
                print(f"[uyarı] normalization atlandı: {e}", file=sys.stderr)
                self._norm_warned = True
            return tokens

    # stopword ----------------------------------------------------------------
    @property
    def stopset(self) -> set[str]:
        if self._stopset is None:
            from stopword import load_static_stopwords
            if self.args.stopword_file:
                self._stopset = load_static_stopwords(self.args.stopword_file)
            else:
                static = load_static_stopwords(STOPWORD_FILES["static"])
                dynamic = load_static_stopwords(STOPWORD_FILES["dynamic"])
                self._stopset = {"static": static, "dynamic": dynamic,
                                 "union": static | dynamic, "intersection": static & dynamic}[self.args.list]
        return self._stopset

    def stopword(self, tokens: list[str]) -> tuple[list[str], list[bool]]:
        from stopword import tr_lower
        keep = [tr_lower(t) not in self.stopset for t in tokens]
        return [t for t, k in zip(tokens, keep) if k], keep

    # stem --------------------------------------------------------------------
    @property
    def stemmer(self):
        if self._stemmer is None:
            from stemmer import Config, Stemmer
            cfg = Config(ranking=self.args.ranking)
            self._stemmer = Stemmer(self.args.lexicon, cfg)
        return self._stemmer

    def stem(self, tokens: list[str], pos: list[str] | None = None) -> list[str]:
        return self.stemmer.stem_tokens(tokens, pos if (self.args.pos and pos) else None)


def process(item: Item, steps: Steps, task: str) -> dict:
    """Bir cümleyi işler; token başına kayıt döndürür."""
    toks = item.tokens
    rec = {"sent_id": item.sent_id, "text": item.text or " ".join(toks), "tokens": toks}
    if task == "tokenize":
        rec["output"] = toks
        return rec
    if task == "normalize":
        rec["normalized"] = steps.normalize(toks)
        rec["output"] = rec["normalized"]
        return rec
    if task == "stopword":
        kept, keep = steps.stopword(toks)
        rec["kept"] = keep
        rec["output"] = kept
        return rec
    if task == "stem":
        rec["stems"] = steps.stem(toks, item.pos)
        rec["output"] = rec["stems"]
        return rec
    # pipeline: normalize → stopword → stem
    norm = steps.normalize(toks)
    kept, keep = steps.stopword(norm)
    pos_kept = [p for p, k in zip(item.pos, keep) if k] if item.pos else None
    rec.update(normalized=norm, kept=keep, stems=steps.stem(kept, pos_kept))
    rec["output"] = rec["stems"]
    return rec


# ----------------------------------------------------------------------------- çıktı

def emit(records: list[dict], task: str, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(records, ensure_ascii=False, indent=1))
        return
    if fmt == "text":
        for r in records:
            prefix = f"{r['sent_id']}\t" if r["sent_id"] else ""
            if task == "stopword" and "kept" in r:
                shown = [t if k else f"[{t}]" for t, k in zip(r["tokens"], r["kept"])]
                print(prefix + " ".join(shown))
            else:
                print(prefix + " ".join(r["output"]))
        return
    # tsv: token başına satır
    cols = ["sent_id", "token"]
    if task in ("normalize", "pipeline"):
        cols.append("normalized")
    if task in ("stopword", "pipeline"):
        cols.append("kept")
    if task in ("stem", "pipeline"):
        cols.append("stem")
    print("\t".join(cols))
    for r in records:
        norm = r.get("normalized", r["tokens"])
        keep = r.get("kept", [True] * len(r["tokens"]))
        stems = iter(r.get("stems", []))
        for i, tok in enumerate(r["tokens"]):
            row = [r["sent_id"], tok]
            if "normalized" in cols:
                row.append(norm[i])
            if "kept" in cols:
                row.append("1" if keep[i] else "0")
            if "stem" in cols:
                row.append(next(stems) if keep[i] else "")   # pipeline'da elenen token stem'lenmez
            print("\t".join(row))


# ----------------------------------------------------------------------------- değerlendirme

def evaluate(task: str, items: list[Item], sents: list, steps: Steps, args) -> None:
    if task == "stopword":
        from stopword import evaluate_list
        p, r, f = evaluate_list(steps.stopset, sents)
        print(f"\n[eval] stopword ({args.list}{' ' + args.stopword_file if args.stopword_file else ''}) — "
              f"UPOS-proxy gold: P={p:.3f} R={r:.3f} F1={f:.3f}")
        return
    if task == "stem":
        from stem_gold import CONTENT_EXCLUDE, Tok, _parse_misc, gold_root, read_derived
        from stemmer import fold
        derived = read_derived(ROOT / "lexicon" / "derived.tsv")
        n = ok = 0
        by_pos: dict[str, list[int]] = {}
        for it in items:
            for w in it.words:
                if w.upos in CONTENT_EXCLUDE or w.lemma in ("null", "_", ""):
                    continue
                gold = gold_root(Tok(w.form, w.lemma, w.upos, w.feats, _parse_misc(w.misc), args.split or "custom", it.sent_id), derived)
                pred = fold(steps.stemmer.stem(w.form, w.upos if args.pos else None))
                hit = pred == gold
                n += 1; ok += hit
                by_pos.setdefault(w.upos, [0, 0]); by_pos[w.upos][0] += hit; by_pos[w.upos][1] += 1
        pos_str = "  ".join(f"{p} {100 * a / b:.1f}" for p, (a, b) in sorted(by_pos.items(), key=lambda x: -x[1][1])[:6])
        print(f"\n[eval] stem{' + gold POS' if args.pos else ''} — root accuracy: {100 * ok / max(1, n):.1f}% (n={n})   {pos_str}")
        return
    print(f"\n[eval] {task} için otomatik değerlendirme yok (stem ve stopword destekleniyor).", file=sys.stderr)


# ----------------------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task", choices=TASKS, help="çalıştırılacak adım")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="tek cümle / metin (regex tokenizer ile bölünür)")
    src.add_argument("--file", help="metin dosyası, her satır bir cümle")
    src.add_argument("--split", choices=("train", "dev", "test"), help="UD Turkish-BOUN split'i (gold token'lar)")
    src.add_argument("--conllu", help="herhangi bir CoNLL-U dosyası (gold token'lar)")
    ap.add_argument("--format", choices=("text", "tsv", "json"), default="text")
    ap.add_argument("--limit", type=int, default=10, help="dataset modunda yazdırılacak cümle sayısı (0: hiç, -1: hepsi)")
    ap.add_argument("--eval", action="store_true", help="dataset modunda gold ile karşılaştır (stem: kök doğruluğu, stopword: P/R/F1)")
    # stem
    ap.add_argument("--pos", action="store_true", help="dataset modunda gold UPOS'u stemmer'a ver (üst sınır deneyi)")
    ap.add_argument("--lexicon", help="farklı bir lexicon/ klasörü (varsayılan: repo lexicon/)")
    ap.add_argument("--ranking", choices=("score", "longest", "attested"), default="score", help="kök seçim kuralı")
    # stopword
    ap.add_argument("--list", choices=("static", "dynamic", "union", "intersection"), default="static",
                    help="stopword listesi (varsayılan static: stopwords-iso; dynamic: BOUN TF-IDF K=75; union en yüksek recall, "
                         "intersection en yüksek precision)")
    ap.add_argument("--stopword-file", help="kendi stopword listen (satır başına bir kelime)")
    return ap


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    items, sents = load_items(args)
    steps = Steps(args)
    dataset_mode = bool(sents)
    shown = items if (not dataset_mode or args.limit < 0) else items[:args.limit]
    records = [process(it, steps, args.task) for it in shown]
    if records:
        emit(records, args.task, args.format)
    if args.eval:
        if not dataset_mode:
            sys.exit("--eval için --split veya --conllu gerekir")
        evaluate(args.task, items, sents, steps, args)


if __name__ == "__main__":
    main()
