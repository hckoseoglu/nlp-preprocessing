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
    ("    if word has no letters:                 return word          # punctuation, numbers", ""),
    ("    if word looks like Name'suffix:         return PROPER(word)  # İstanbul'daki → İstanbul", ""),
    ("    w ← lowercase(word)", ""),
    ("    candidates ← empty list", ""),
    ("    PEEL(state = END, rest = w, suffixes = [], right = none)        # fills `candidates`", ""),
    ("    if candidates is empty:                 return FALLBACK(w)   # unknown root: strip ≥2-letter suffixes only", ""),
    ("    best ← argmax SCORE(c) for c in candidates", ""),
    ("    return DERIVATION_MAP.get(best.root, best.root)             # önemli → önem (learned from training data)", ""),
    ("", ""),
    ("PEEL(state, rest, suffixes, right):          # depth-first, backwards through the suffix automaton;", "kw"),
    ("                                             # right = first letter of the suffix just stripped", ""),
    ("    if (state, rest, right) was visited before:   return       # same remainder, different right context → different options", ""),
    ("    if state is a root state and rest is a lexicon root, or becomes one after a sound repair", ""),
    ("       that `right` allows (kitab → kitap only before a vowel-initial suffix; gid → git, burn → burun):", ""),
    ("        append (root, suffixes) to candidates                  # record it, but keep peeling: kalem vs kale + m", ""),
    ("    for each suffix s that the automaton allows right before `state`:", ""),
    ("        if rest ends with an allomorph of s and the phonology allows it (buffer letter, voicing, final ğ/k vs `right`;", ""),
    ("           a broken vowel harmony is allowed but penalized):", ""),
    ("            PEEL(previous_state(s), rest without s, suffixes + [s], right = first letter of s)", ""),
    ("", ""),
    ("SCORE(c) = min(log freq(c.root), 5)          # how common the root is in the training data (capped)", "kw"),
    ("         + 0.5 · |c.root|                    # slight preference for longer roots", ""),
    ("         − Σ cost(s) over c.suffixes         # inflection 0.7, voice / participle 1.0, derivation 3.0", ""),
    ("         − 0.5 · (number of sound repairs)  −  5 · (vowel harmony violations)", ""),
    ("         + 1 if the whole word is itself a known word", ""),
]


def render(lines: list[tuple[str, str]], title: str, out: Path, width: float = 12.2) -> None:
    """Satır listesini (metin, stil) 'listing' görünümlü figüre çevirir; yorum = en az iki boşluk + '#'."""
    fig_h = 0.29 * len(lines) + 0.7
    fig, ax = plt.subplots(figsize=(width, fig_h))
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, facecolor="#f9fafb", edgecolor="#d1d5db", lw=1))
    y = 0.975
    step = 0.955 / len(lines)
    for text, style in lines:
        if text:
            code, _, comment = text.partition("  #")
            ax.text(0.015, y, code.rstrip("\n"), family="monospace", fontsize=10.2, va="top", ha="left",
                    color="#111827", fontweight="bold" if style == "kw" else "normal", transform=ax.transAxes)
            if comment:
                ax.text(0.015, y, " " * len(code) + "  #" + comment, family="monospace", fontsize=10.2, va="top",
                        ha="left", color="#6b7280", transform=ax.transAxes)
        y -= step
    fig.suptitle(title, fontsize=12.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=130, facecolor="white")
    plt.close(fig)
    print("yazıldı:", out)


def main() -> None:
    render(LINES, "Rule-based stemmer: high-level pseudo-code", OUT)


if __name__ == "__main__":
    main()
