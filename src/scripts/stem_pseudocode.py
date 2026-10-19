"""Stemmer'ın yüksek seviyeli sözde kodu → reports/stemming_pseudocode.png (rapor figürü).

Kullanım: <venv>/python3 src/scripts/stem_pseudocode.py      (matplotlib gerekir; eval çalıştırmaz)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "stemming_pseudocode.png"

LINES = [
    ("STEM(word):", "kw"),
    ("    if word has no letters, or is a @mention / #hashtag / URL:   return word", ""),
    ("    if word contains an apostrophe (İstanbul'daki):   keep the part before it; if capitalized, strip noun", ""),
    ("        suffixes only and return the root if it is in the lexicon, otherwise that part itself       # → İstanbul", ""),
    ("    w ← lowercase(word)", ""),
    ("    if w is a copula fragment (dataset mode only):    return its UD placeholder lemma (y / i)", ""),
    ("    if word is capitalized and known as a proper noun: return w", ""),
    ("    candidates ← empty list;   PEEL(state = END, rest = w, suffixes = [], violations = 0)", ""),
    ("    if candidates is empty:    return w if word is capitalized (unknown proper noun) else FALLBACK(w)", ""),
    ("    best ← argmax SCORE(c) over candidates          # exceptions are lexicon entries with another canonical root (bana → ben)", ""),
    ("    return DERIVATION_MAP.get(best.root, best.root)  # önemli → önem, learned from the training split", ""),
    ("", ""),
    ("PEEL(state, rest, suffixes, violations):          # depth-first, backwards through the suffix automaton", "kw"),
    ("    if (state, rest, right context) was visited:   return", ""),
    ("    if state is a root state (N0 noun / V0 verb):", ""),
    ("        for each variant of rest — as is, devoiced (kitab → kitap), undoubled (hakk → hak), vowel inserted (burn → burun):", ""),
    ("            if variant is a lexicon root of that category, its flags allow the repair, |variant| ≥ 2,", ""),
    ("               and (suffixes is empty or the root is not a frozen closed-class word such as için):", ""),
    ("                append (variant, suffixes, repairs, violations) to candidates     # keep peeling: kalem vs kale + m", ""),
    ("    for each ε-edge into state:                   PEEL(previous state, rest, suffixes, violations)", ""),
    ("    if |rest| ≤ 1:                                 return", ""),
    ("    for each suffix allomorph s allowed right before `state` that rest ends with:", ""),
    ("        stem ← rest without s", ""),
    ("        if a hard phonological check fails (buffer letter, consonant assimilation, final ğ/k):   skip", ""),
    ("        v ← 1 if the vowel harmony between stem and s is broken, else 0         # soft: penalized, not rejected", ""),
    ("        for each stem' in {stem} ∪ narrowing variants (bekli → bekle, di → de):", ""),
    ("            PEEL(previous_state(s), stem', suffixes + [s], violations + v)", ""),
    ("", ""),
    ("SCORE(c) = min(log(freq(c.root) + 1), 5)     # how common the root is in the training split (capped)", "kw"),
    ("         + 0.5 · |c.root|                     # slight preference for longer roots", ""),
    ("         − Σ cost(s) over c.suffixes          # inflection 0.7, voice / participle 1.0, derivation 3.0", ""),
    ("         − 0.5 · (number of sound repairs)  −  5 · (harmony violations)", ""),
    ("         + 1 if nothing was stripped and the word occurs in the training split", ""),
    ("         (+ 1 if a POS tag is given and matches the root)        ties: longer root, then more frequent root", ""),
    ("", ""),
    ("FALLBACK(w):   lexicon-free peeling with strict harmony and no derivational suffixes; keep analyses whose", "kw"),
    ("               suffixes all have ≥ 2 letters and whose stem has ≥ 3 letters; return the shortest such stem", ""),
]


def main() -> None:
    fig_h = 0.27 * len(LINES) + 0.7
    fig, ax = plt.subplots(figsize=(12.6, fig_h))
    ax.axis("off")
    # açık gri kutu: "listing" görünümü
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor="#f9fafb", edgecolor="#d1d5db", lw=1))
    y = 0.975
    step = 0.955 / len(LINES)
    for text, style in LINES:
        if text:
            code, sep, comment = text.partition("  #")          # yorum: en az iki boşluk + '#'. (#hashtag kod sayılır)
            kw = ""
            if style == "kw":                                   # yalnız baş kısmı (':' ya da '=' dahil) kalın
                cut = min([i for i in (code.find(":"), code.find(" = ")) if i >= 0] or [len(code)])
                cut = cut + (1 if code[cut:cut + 1] == ":" else 0)
                kw, code = code[:cut], code[cut:]
                ax.text(0.015, y, kw, family="monospace", fontsize=9.6, va="top", ha="left", color="#111827",
                        fontweight="bold", transform=ax.transAxes)
            ax.text(0.015, y, " " * len(kw) + code, family="monospace", fontsize=9.6, va="top", ha="left",
                    color="#111827", transform=ax.transAxes)
            if sep:
                # yorumları gri yaz: kodun bittiği yerden sonra aynı satıra
                ax.text(0.015, y, " " * (len(kw) + len(code)) + "  #" + comment, family="monospace", fontsize=9.6,
                        va="top", ha="left", color="#6b7280", transform=ax.transAxes)
        y -= step
    fig.suptitle("Rule-based stemmer: high-level pseudo-code", fontsize=12.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=130, facecolor="white")
    print("yazıldı:", OUT)


if __name__ == "__main__":
    main()
