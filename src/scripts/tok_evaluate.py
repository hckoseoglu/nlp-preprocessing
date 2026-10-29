"""Tokenization evaluation on UD-BOUN: every tokenizer on the same sentences, one table per test case.

Tuning is done on dev; the test split is run only once at the end (like the other tasks).
Rows: whitespace split and the old regex tokenizer (baselines), then our tokenizers: rule-based and
Logistic Regression with feature set 1, 2 and 3 (each trained on the training split).

    Test case 1   all UD-BOUN sentences. Main gold: "tdk" (abbreviations and ordinals keep their
                  period, see tokenization/corpus.py); plain UD-BOUN is shown for transparency.
    Test case 2   hard cases: only the chunks with an apostrophe suffix, a number, a period after a
                  word, or a punctuation cluster (tokenization/hard_cases.py)
    Test case 3   special entities: every sentence with one synthetic URL / e-mail / hashtag / mention
                  (data/tokenization/special_<split>.conllu, made by src/scripts/tok_build_special.py)
    MWE layer     the optional MWE layer on top of the rule-based tokenizer, against UD's MWE
                  relations (tokenization/mwe.py)

Output: printed and saved to results/tables_tok_<split>.md.
Usage:  python src/scripts/tok_evaluate.py [dev|test] [--errors N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import tokenizer_baseline  # noqa: E402
from io_conllu import read_conllu  # noqa: E402
from tokenization.corpus import load_split  # noqa: E402
from tokenization.features import FEATURE_LEVELS  # noqa: E402
from tokenization.hard_cases import HARD_CASES, evaluate_hard_cases  # noqa: E402
from tokenization.metrics import Score, evaluate  # noqa: E402
from tokenization.ml import LRTokenizer  # noqa: E402
from tokenization.mwe import KINDS, MWEMerger, evaluate_mwes  # noqa: E402
from tokenization.rules import RuleTokenizer  # noqa: E402
from tokenization.special import MAKERS, evaluate_entities  # noqa: E402

SPECIAL = ROOT / "data" / "tokenization"
RESULTS = ROOT / "results"


def build_tokenizers() -> dict:
    """Baselines, the rule-based tokenizer and one LR tokenizer per feature set (trained on train)."""
    train = load_split("train")
    tokenizers = {
        "whitespace": str.split,
        "regex baseline": tokenizer_baseline.tokenize,
        "rule-based": RuleTokenizer().tokenize,
    }
    for level in FEATURE_LEVELS:
        tokenizers[f"LR set {level}"] = LRTokenizer.train(train, level).tokenize
    return tokenizers


def pct(x: float) -> str:
    return f"{x:.2%}"


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    """A markdown table."""
    return ["| " + " | ".join(header) + " |",
            "|" + "---|" * len(header),
            *("| " + " | ".join(row) + " |" for row in rows),
            ""]


def prf(s: Score) -> list[str]:
    return [pct(s.precision), pct(s.recall), pct(s.f1)]


def token_table(title: str, sentences, tokenizers: dict, convention: str, n_errors: int) -> list[str]:
    """Test case 1 (and 3): token precision / recall / F1 and sentence exact match."""
    rows, errors = [], []
    for name, tokenize in tokenizers.items():
        s = evaluate(tokenize, sentences, convention)
        rows.append([name, *prf(s), f"{pct(s.exact_match)} ({s.exact}/{s.units})"])
        errors += [f"- {name}: {n}× gold `{gold}` predicted `{pred}`" for (gold, pred), n in s.errors.most_common(n_errors)]
    lines = [title, ""] + table(["tokenizer", "precision", "recall", "F1", "sentence exact"], rows)
    if s.skipped:
        lines += [f"({s.skipped} sentence(s) skipped: gold token forms do not match the `# text` line)", ""]
    return lines + (["Most common errors:", *errors, ""] if errors else [])


def hard_case_table(sentences, tokenizers: dict) -> list[str]:
    """Test case 2: tokens inside hard chunks only; chunk exact match per kind."""
    rows, counts = [], {}
    for name, tokenize in tokenizers.items():
        scores = evaluate_hard_cases(tokenize, sentences)
        counts = {kind: s.units for kind, s in scores.items()}
        rows.append([name, *prf(scores["all"]), pct(scores["all"].exact_match),
                     *(pct(scores[kind].exact_match) for kind in HARD_CASES)])
    header = ["tokenizer", "precision", "recall", "F1", f"chunk exact ({counts['all']})",
              *(f"{kind} ({counts[kind]})" for kind in HARD_CASES)]
    return ["## Test case 2: hard cases (gold: tdk; only the tokens inside hard chunks; "
            "per kind: chunk exact match)", ""] + table(header, rows)


def special_table(sentences, tokenizers: dict) -> list[str]:
    """Test case 3: sentences with a synthetic special entity; share of entities kept as one token."""
    rows, totals = [], {}
    for name, tokenize in tokenizers.items():
        s = evaluate(tokenize, sentences)
        entities = evaluate_entities(tokenize, sentences)
        totals = {kind: total for kind, (_, total) in entities.items()}
        rows.append([name, *prf(s), pct(s.exact_match),
                     *(pct(kept / total) for kept, total in entities.values())])
    header = ["tokenizer", "precision", "recall", "F1", "sentence exact",
              *(f"{kind} kept ({totals[kind]})" for kind in MAKERS)]
    return [f"## Test case 3: special entities ({len(sentences)} sentences, one synthetic entity each; gold: tdk)",
            ""] + table(header, rows)


def mwe_table(sentences) -> list[str]:
    """The optional MWE layer on top of the rule-based tokenizer, per MWE kind."""
    tokenize = RuleTokenizer().tokenize
    full = evaluate_mwes(MWEMerger(), tokenize, sentences)
    lexicon_only = evaluate_mwes(MWEMerger(repeat_rule=False), tokenize, sentences)
    rows = [[kind, str(full[kind].gold), str(full[kind].predicted), str(full[kind].correct), *prf(full[kind])]
            for kind in (*KINDS, "all")]
    s = lexicon_only["all"]
    rows.append(["all, lexicon only (no repeat rule)", str(s.gold), str(s.predicted), str(s.correct), *prf(s)])
    return ["## MWE layer (rule-based tokenizer + resources/mwe_tr.txt + repeat rule; gold: UD MWE relations)",
            ""] + table(["MWE kind", "gold", "predicted", "correct", "precision", "recall", "F1"], rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("split", nargs="?", default="dev", choices=["dev", "test"])
    ap.add_argument("--errors", type=int, default=0, help="list the N most common errors per tokenizer (test case 1)")
    args = ap.parse_args()

    special_file = SPECIAL / f"special_{args.split}.conllu"
    if not special_file.exists():
        sys.exit(f"{special_file} is missing — run: python src/scripts/tok_build_special.py")
    sentences = load_split(args.split)
    special = read_conllu(special_file)
    tokenizers = build_tokenizers()

    lines = [f"# Tokenization — UD-BOUN {args.split}", ""]
    lines += token_table(f"## Test case 1: all sentences ({len(sentences)}), gold: UD-BOUN + TDK periods "
                         "(Dr. / 3.) — main score", sentences, tokenizers, "tdk", args.errors)
    lines += token_table("## Test case 1: all sentences, gold: plain UD-BOUN — for transparency",
                         sentences, tokenizers, "ud", 0)
    lines += hard_case_table(sentences, tokenizers)
    lines += special_table(special, tokenizers)
    lines += mwe_table(sentences)

    text = "\n".join(lines)
    print(text)
    out = RESULTS / f"tables_tok_{args.split}.md"
    out.write_text(text, encoding="utf-8")
    print(f"→ {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
