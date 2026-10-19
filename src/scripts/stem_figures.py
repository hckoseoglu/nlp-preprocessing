"""Stemming figürleri → reports/stemming_*.png (stopword figürleriyle aynı stil: matplotlib/Agg, dpi 130).

Kullanım: <venv>/python3 src/scripts/stem_figures.py          (matplotlib + snowballstemmer + TurkishStemmer venv'de)
Üretilenler:
  stemming_system_comparison.png  — yöntemler (baseline'lar, bizim, bizim + gold POS) dev/test genel accuracy
  stemming_pos_breakdown.png      — POS sınıfına göre: Snowball vs bizim vs bizim + gold POS (dev)
  stemming_subsets.png            — alt kümeler (bare / inflected / derived / unseen / copula): POS'suz vs POS'lu (dev)
  stemming_test_breakdown.png     — rapor figürü: yalnız bizim, yalnız test; POS + alt küme kırılımı (Tablo 7'nin yerine)
  stemming_ranking_ablation.png   — kök seçim kuralı ilerlemesi + bileşen ablation'ı (dev)
  stemming_error_classes.png      — hata sınıfı dağılımı: POS'suz vs POS'lu (dev)
  stemming_rule_only_pos_effect.png — kural-only sistemde POS'un etkisi: Snowball + fiil kuralları POS'suz vs gold POS (bizimle birlikte)
  stemming_snowball_pos.png       — yalnız Snowball: isim kuralları / +fiil kuralları POS'suz / +fiil kuralları gold POS
  stemming_pos_filtered_eval.png  — Snowball/TurkishStemmer vs bizim: tüm tokenler (POS'suz) ve gold POS ile süzülmüş
                                    token kümeleri (isim sınıfı / yalnız NOUN / yalnız VERB), dev + test
Kullanılan tüm sayılar results/figures_data.json'a yazılır.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "scripts"))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from stem_evaluate import _SNOW, _TSTEM, classify_error, subsets_of  # noqa: E402
from stem_gold import fold, gold_root, load_split, read_derived  # noqa: E402
from stemmer import Config, Stemmer  # noqa: E402

REPORTS, RESULTS = ROOT / "reports", ROOT / "results"
BLUE, AMBER, PURPLE, GRAY, GREEN, RED = "#2563eb", "#f59e0b", "#7c3aed", "#9ca3af", "#16a34a", "#dc2626"
POS = ["NOUN", "VERB", "ADJ", "PROPN", "ADV", "PRON"]
SUBSETS = [("bare", "bare\n(form = root)"), ("inflected", "inflected\nonly"), ("derived", "derived\n(root ≠ lemma)"),
           ("oov", "unseen\nin train"), ("copula", "copula\nfragments")]
METHODS = [("no-stem", "no stemming"), ("prefix5", "first 5\nletters"), ("snowball", "Snowball"),
           ("turkishstemmer", "Turkish-\nStemmer"), ("ours", "ours"), ("ours_pos", "ours +\ngold POS")]


def pct(preds, golds, mask=None):
    idx = range(len(golds)) if mask is None else [i for i in range(len(golds)) if mask[i]]
    return 100.0 * sum(preds[i] == golds[i] for i in idx) / max(1, len(idx))


def run_split(split, st, derived, train_forms):
    toks = load_split(split)
    golds = [gold_root(t, derived) for t in toks]
    subs = [subsets_of(t, g, train_forms) for t, g in zip(toks, golds)]
    preds = {
        "ours": [fold(st.stem(t.form)) for t in toks],
        "ours_pos": [fold(st.stem(t.form, t.upos)) for t in toks],
        "no-stem": [fold(t.form) for t in toks],
        "prefix5": [fold(t.form)[:5] for t in toks],
    }
    if _SNOW is not None:
        preds["snowball"] = [fold(_SNOW.stemWord(fold(t.form))) for t in toks]
    if _TSTEM is not None:
        preds["turkishstemmer"] = [fold(_TSTEM.stem(fold(t.form))) for t in toks]
    return toks, golds, subs, preds


def label_bars(bars, fmt="{:.1f}", dy=0.6, fs=7):
    for b in bars:
        v = b.get_height()
        plt.text(b.get_x() + b.get_width() / 2, v + dy, fmt.format(v), ha="center", va="bottom", fontsize=fs)


def main() -> None:
    derived = read_derived(ROOT / "lexicon" / "derived.tsv")
    train_forms = {fold(t.form) for t in load_split("train")}
    st = Stemmer()
    data: dict = {}
    dev = run_split("dev", st, derived, train_forms)
    test = run_split("test", st, derived, train_forms)
    d_toks, d_golds, d_subs, d_preds = dev
    t_toks, t_golds, t_subs, t_preds = test

    # ---------------- 1) sistem karşılaştırması (dev/test genel) ----------------
    methods = [(k, lab) for k, lab in METHODS if k in d_preds]
    dev_acc = [pct(d_preds[k], d_golds) for k, _ in methods]
    test_acc = [pct(t_preds[k], t_golds) for k, _ in methods]
    data["system_comparison"] = {k: {"dev": a, "test": b} for (k, _), a, b in zip(methods, dev_acc, test_acc)}
    x = list(range(len(methods))); w = 0.38
    plt.figure(figsize=(8.5, 4.8))
    b1 = plt.bar([i - w / 2 for i in x], dev_acc, w, label="dev", color=BLUE)
    b2 = plt.bar([i + w / 2 for i in x], test_acc, w, label="test", color=AMBER)
    label_bars(b1); label_bars(b2)
    plt.xticks(x, [lab for _, lab in methods]); plt.ylim(0, 105); plt.ylabel("root accuracy (%)")
    plt.title("Stemming: our system vs baselines (UD Turkish-BOUN)")
    plt.legend(loc="upper left"); plt.grid(axis="y", alpha=0.3); plt.tight_layout()
    plt.savefig(REPORTS / "stemming_system_comparison.png", dpi=130); plt.close()

    # ---------------- 2) POS kırılımı (dev) ----------------
    series = [("Snowball", "snowball", GRAY), ("ours", "ours", BLUE), ("ours + gold POS", "ours_pos", AMBER)]
    series = [s for s in series if s[1] in d_preds]
    data["pos_breakdown_dev"] = {}
    plt.figure(figsize=(9, 4.8))
    x = list(range(len(POS))); w = 0.8 / len(series)
    for j, (name, key, col) in enumerate(series):
        vals = [pct(d_preds[key], d_golds, [t.upos == p for t in d_toks]) for p in POS]
        data["pos_breakdown_dev"][key] = dict(zip(POS, vals))
        bars = plt.bar([i + (j - (len(series) - 1) / 2) * w for i in x], vals, w, label=name, color=col)
        label_bars(bars)
    n_pos = Counter(t.upos for t in d_toks)
    plt.xticks(x, [f"{p}\n(n={n_pos[p]})" for p in POS]); plt.ylim(0, 115); plt.ylabel("root accuracy (%)")
    plt.title("Stemming accuracy by POS class (dev)")
    plt.legend(loc="upper center", ncol=3, frameon=False); plt.grid(axis="y", alpha=0.3); plt.tight_layout()
    plt.savefig(REPORTS / "stemming_pos_breakdown.png", dpi=130); plt.close()

    # ---------------- 3) alt kümeler (dev) ----------------
    data["subsets_dev"] = {}
    plt.figure(figsize=(8.5, 4.8))
    x = list(range(len(SUBSETS))); w = 0.38
    n_sub = Counter(k for sb in d_subs for k in sb)
    for j, (name, key, col) in enumerate([("ours", "ours", BLUE), ("ours + gold POS", "ours_pos", AMBER)]):
        vals = [pct(d_preds[key], d_golds, [k in sb for sb in d_subs]) for k, _ in SUBSETS]
        data["subsets_dev"][key] = {k: v for (k, _), v in zip(SUBSETS, vals)}
        bars = plt.bar([i + (j - 0.5) * w for i in x], vals, w, label=name, color=col)
        label_bars(bars)
    plt.xticks(x, [f"{lab}\n(n={n_sub[k]})" for k, lab in SUBSETS]); plt.ylim(0, 115)
    plt.ylabel("root accuracy (%)"); plt.title("Stemming accuracy by token type (dev)")
    plt.legend(loc="upper center", ncol=2, frameon=False); plt.grid(axis="y", alpha=0.3); plt.tight_layout()
    plt.savefig(REPORTS / "stemming_subsets.png", dpi=130); plt.close()

    # ---------------- 3b) tek panel çifti: POS + alt küme kırılımı (yalnız test, yalnız bizim) ----------------
    n_pos_t = Counter(t.upos for t in t_toks)
    n_sub_t = Counter(k for sb in t_subs for k in sb)
    overall_t = pct(t_preds["ours"], t_golds)
    pos_vals = [pct(t_preds["ours"], t_golds, [t.upos == p for t in t_toks]) for p in POS]
    sub_vals = [pct(t_preds["ours"], t_golds, [k in sb for sb in t_subs]) for k, _ in SUBSETS]
    data["test_breakdown"] = {"overall": overall_t, "pos": dict(zip(POS, pos_vals)),
                              "subsets": {k: v for (k, _), v in zip(SUBSETS, sub_vals)},
                              "n_pos": {p: n_pos_t[p] for p in POS}, "n_subsets": {k: n_sub_t[k] for k, _ in SUBSETS}}
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), gridspec_kw={"width_ratios": [6, 5]})
    for ax, labels, vals, title in (
        (axes[0], [f"{p}\n(n={n_pos_t[p]:,})" for p in POS], pos_vals, "by POS tag"),
        (axes[1], [f"{lab}\n(n={n_sub_t[k]:,})" for k, lab in SUBSETS], sub_vals, "by token type"),
    ):
        bars = ax.bar(range(len(vals)), vals, 0.62, color=BLUE)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8, f"{b.get_height():.1f}", ha="center", va="bottom", fontsize=8)
        ax.axhline(overall_t, color=GRAY, ls="--", lw=1, label=f"all tokens: {overall_t:.1f}")
        ax.legend(loc="upper right", frameon=False, fontsize=8)
        ax.set_xticks(range(len(vals))); ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylim(0, 114); ax.set_title(title, fontsize=10); ax.grid(axis="y", alpha=0.3)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("root accuracy (%)")
    fig.suptitle("Our stemmer by POS tag and token type", fontsize=12)
    plt.tight_layout(); plt.savefig(REPORTS / "stemming_test_breakdown.png", dpi=130); plt.close()

    # ---------------- 4) kök seçim kuralı + ablation (dev) ----------------
    cfg = st.cfg
    def dev_acc_cfg(c: Config, pos: bool = False) -> float:
        s2 = Stemmer(config=c)
        return pct([fold(s2.stem(t.form, t.upos if pos else None)) for t in d_toks], d_golds)
    ranking = [("longest root\nin lexicon", dev_acc_cfg(replace(cfg, ranking="longest"))),
               ("attested roots\nfirst, then\nlongest", dev_acc_cfg(replace(cfg, ranking="attested"))),
               ("frequency\nscore (ours)", dev_acc[[k for k, _ in methods].index("ours")]),
               ("frequency\nscore +\ngold POS", dev_acc[[k for k, _ in methods].index("ours_pos")])]
    full = ranking[2][1]
    ablation = [("vowel harmony off", replace(cfg, harmony="off")),
                ("buffer-consonant rule off", replace(cfg, strict_buffer=False)),
                ("consonant assimilation off", replace(cfg, strict_assimilation=False)),
                ("repair flags off", replace(cfg, strict_flags=False)),
                ("apostrophe / proper-noun path off", replace(cfg, propn_apostrophe=False, propn_whole=False)),
                ("derivational stripping rules off", replace(cfg, use_der_rules=False)),
                ("derivation map (train) off", replace(cfg, use_derived=False)),
                ("copula fragment table off", replace(cfg, use_copula=False))]
    abl_vals = [(name, dev_acc_cfg(c) - full) for name, c in ablation]
    data["ranking_dev"] = {n.replace("\n", " "): v for n, v in ranking}
    data["ablation_delta_dev"] = {n: v for n, v in abl_vals}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw={"width_ratios": [1, 1.2]})
    cols = [GRAY, GRAY, BLUE, AMBER]
    bars = ax1.bar(range(4), [v for _, v in ranking], color=cols)
    for b, (_, v) in zip(bars, ranking):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    ax1.set_xticks(range(4)); ax1.set_xticklabels([n for n, _ in ranking], fontsize=8.5)
    ax1.set_ylim(80, 100); ax1.set_ylabel("root accuracy (%)"); ax1.set_title("Root selection rule (dev)")
    ax1.grid(axis="y", alpha=0.3)
    names = [n for n, _ in abl_vals]; deltas = [v for _, v in abl_vals]
    hb = ax2.barh(range(len(names)), deltas, color=[PURPLE if d < -0.3 else GRAY for d in deltas])
    for b, d in zip(hb, deltas):
        ax2.text(d - 0.06 if d < 0 else d + 0.06, b.get_y() + b.get_height() / 2, f"{d:+.2f}",
                 va="center", ha="right" if d < 0 else "left", fontsize=8)
    ax2.set_yticks(range(len(names))); ax2.set_yticklabels(names, fontsize=8)
    ax2.axvline(0, color="black", lw=0.8); ax2.set_xlim(min(deltas) - 0.8, 0.8)
    ax2.set_xlabel(f"change in dev accuracy vs full system ({full:.1f}%)")
    ax2.set_title("Component ablation (dev)"); ax2.grid(axis="x", alpha=0.3)
    plt.tight_layout(); plt.savefig(REPORTS / "stemming_ranking_ablation.png", dpi=130); plt.close()

    # ---------------- 5) hata sınıfları (dev): POS'suz vs POS'lu ----------------
    lex_roots = set(st.lex.entries)
    def err_classes(preds):
        c: Counter = Counter()
        for t, g, p in zip(d_toks, d_golds, preds):
            if p != g:
                c[classify_error(t, g, p, lex_roots)] += 1
        return c
    e0, e1 = err_classes(d_preds["ours"]), err_classes(d_preds["ours_pos"])
    classes = [k for k, _ in (e0 + e1).most_common()]
    EN = {"over-stemming": "over-stemming", "under-stemming": "under-stemming",
          "türetim-fazla-soyuldu (over; gold lemma'yı korur)": "derivation stripped\n(gold keeps the lemma)",
          "türetim-soyulmadı (under)": "derivation not stripped", "UD-kopula-parçacığı": "copula fragment\n(UD lemma convention)",
          "belirsizlik (iki geçerli kök)": "two valid roots", "OOV-kök": "root not in lexicon",
          "gold-gürültüsü/typo": "gold noise / typo", "fonoloji": "phonology", "diğer": "other"}
    data["error_classes_dev"] = {"ours": dict(e0), "ours_pos": dict(e1)}
    plt.figure(figsize=(9, 5))
    y = list(range(len(classes))); h = 0.38
    plt.barh([i + h / 2 for i in y], [e0[k] for k in classes], h, label=f"ours ({sum(e0.values())} errors)", color=BLUE)
    plt.barh([i - h / 2 for i in y], [e1[k] for k in classes], h, label=f"ours + gold POS ({sum(e1.values())} errors)", color=AMBER)
    for i, k in enumerate(classes):
        plt.text(e0[k] + 2, i + h / 2, str(e0[k]), va="center", fontsize=7)
        plt.text(e1[k] + 2, i - h / 2, str(e1[k]), va="center", fontsize=7)
    plt.yticks(y, [EN.get(c, c) for c in classes], fontsize=8); plt.gca().invert_yaxis()
    plt.xlabel("errors (tokens, dev)"); plt.title("Remaining stemming errors by class (dev)")
    plt.legend(loc="lower right"); plt.grid(axis="x", alpha=0.3); plt.tight_layout()
    plt.savefig(REPORTS / "stemming_error_classes.png", dpi=130); plt.close()

    # ---------------- 6) POS ile süzülmüş değerlendirme: Snowball vs bizim (dev + test) ----------------
    NOMINAL = {"NOUN", "PROPN", "ADJ", "PRON", "ADV"}
    token_sets = [("all tokens", lambda t: True), ("nominals\n(NOUN/PROPN/ADJ/PRON/ADV)", lambda t: t.upos in NOMINAL),
                  ("NOUN only", lambda t: t.upos == "NOUN"), ("VERB only", lambda t: t.upos == "VERB")]
    series6 = [("Snowball", "snowball", GRAY), ("TurkishStemmer", "turkishstemmer", PURPLE), ("ours", "ours", BLUE)]
    series6 = [s_ for s_ in series6 if s_[1] in d_preds]
    data["pos_filtered_eval"] = {}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, (split, toks_, golds_, preds_) in zip(axes, [("dev", d_toks, d_golds, d_preds), ("test", t_toks, t_golds, t_preds)]):
        x = list(range(len(token_sets))); w = 0.8 / len(series6)
        data["pos_filtered_eval"][split] = {}
        for j, (name, key, col) in enumerate(series6):
            vals = [pct(preds_[key], golds_, [f(t) for t in toks_]) for _, f in token_sets]
            data["pos_filtered_eval"][split][key] = {lab.replace("\n", " "): v for (lab, _), v in zip(token_sets, vals)}
            bars = ax.bar([i + (j - (len(series6) - 1) / 2) * w for i in x], vals, w, label=name, color=col)
            for b in bars:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.6, f"{b.get_height():.1f}",
                        ha="center", va="bottom", fontsize=7)
        ns = [sum(1 for t in toks_ if f(t)) for _, f in token_sets]
        ax.set_xticks(x); ax.set_xticklabels([f"{lab}\n(n={n})" for (lab, _), n in zip(token_sets, ns)], fontsize=8)
        ax.set_ylim(0, 115); ax.set_title(f"{split}"); ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel("root accuracy (%)")
    axes[0].legend(loc="upper center", ncol=3, frameon=False)
    fig.suptitle("Snowball vs our stemmer: all tokens (no POS) vs POS-filtered token sets (gold UPOS)")
    plt.tight_layout(); plt.savefig(REPORTS / "stemming_pos_filtered_eval.png", dpi=130); plt.close()

    # ---------------- 7) Kural-tabanlı sistemlerde POS bilgisinin etkisi (Snowball + fiil kuralları) ----------------
    if _SNOW is not None:
        def snow(t):
            return fold(_SNOW.stemWord(fold(t.form)))
        def verb_rule(t):
            return st.rule_stem(t.form, "V", "strip2")
        systems7 = [
            ("Snowball\n(noun rules only)", lambda t: snow(t), GRAY),
            ("Snowball + verb rules,\nno POS (verb rule fires\n→ treat as verb)", lambda t: (verb_rule(t) if verb_rule(t) != fold(t.form) else snow(t)), PURPLE),
            ("Snowball + verb rules,\ngold POS (VERB → verb rules,\nothers → Snowball)", lambda t: verb_rule(t) if t.upos == "VERB" else snow(t), AMBER),
            ("ours\n(lexicon + score, no POS)", lambda t: fold(st.stem(t.form)), BLUE),
            ("ours + gold POS", lambda t: fold(st.stem(t.form, t.upos)), GREEN),
        ]
        groups7 = [("all tokens", lambda t: True), ("NOUN", lambda t: t.upos == "NOUN"), ("VERB", lambda t: t.upos == "VERB")]
        data["rule_only_pos_effect"] = {}
        fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), sharey=True)
        for ax, (split, toks_, golds_) in zip(axes, [("dev", d_toks, d_golds), ("test", t_toks, t_golds)]):
            x = list(range(len(groups7))); w = 0.8 / len(systems7)
            data["rule_only_pos_effect"][split] = {}
            for j, (name, fn, col) in enumerate(systems7):
                preds_ = [fn(t) for t in toks_]
                vals = [pct(preds_, golds_, [f(t) for t in toks_]) for _, f in groups7]
                data["rule_only_pos_effect"][split][name.replace("\n", " ")] = dict(zip([g for g, _ in groups7], vals))
                bars = ax.bar([i + (j - (len(systems7) - 1) / 2) * w for i in x], vals, w, label=name.replace("\n", " "), color=col)
                for b in bars:
                    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.6, f"{b.get_height():.1f}",
                            ha="center", va="bottom", fontsize=6.5)
            ns = [sum(1 for t in toks_ if f(t)) for _, f in groups7]
            ax.set_xticks(x); ax.set_xticklabels([f"{g}\n(n={n})" for (g, _), n in zip(groups7, ns)])
            ax.set_ylim(0, 112); ax.set_title(split); ax.grid(axis="y", alpha=0.3)
        axes[0].set_ylabel("root accuracy (%)")
        fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False, fontsize=8)
        fig.suptitle("Does knowing the POS help a rule-only stemmer? Snowball + verb rules without / with gold POS")
        plt.tight_layout(rect=(0, 0.12, 1, 1)); plt.savefig(REPORTS / "stemming_rule_only_pos_effect.png", dpi=130); plt.close()

    # ---------------- 8) Yalnız Snowball: POS'suz vs POS'lu (test) ----------------
    if _SNOW is not None:
        systems8 = [
            ("Snowball (noun rules only, no POS)", lambda t: snow(t), GRAY),
            ("Snowball + verb rules, no POS", lambda t: (verb_rule(t) if verb_rule(t) != fold(t.form) else snow(t)), PURPLE),
            ("Snowball + verb rules, gold POS", lambda t: verb_rule(t) if t.upos == "VERB" else snow(t), AMBER),
        ]
        groups8 = [("all tokens", lambda t: True), ("NOUN", lambda t: t.upos == "NOUN"),
                   ("ADJ", lambda t: t.upos == "ADJ"), ("VERB", lambda t: t.upos == "VERB")]
        data["snowball_pos"] = {}
        plt.figure(figsize=(8.5, 4.8))
        x = list(range(len(groups8))); w = 0.8 / len(systems8)
        for j, (name, fn, col) in enumerate(systems8):
            preds_ = [fn(t) for t in t_toks]
            vals = [pct(preds_, t_golds, [f(t) for t in t_toks]) for _, f in groups8]
            data["snowball_pos"][name] = dict(zip([g for g, _ in groups8], vals))
            bars = plt.bar([i + (j - (len(systems8) - 1) / 2) * w for i in x], vals, w, label=name, color=col)
            label_bars(bars, fs=7.5)
        ns = [sum(1 for t in t_toks if f(t)) for _, f in groups8]
        plt.xticks(x, [f"{g}\n(n={n})" for (g, _), n in zip(groups8, ns)])
        plt.ylim(0, 90); plt.ylabel("root accuracy (%)"); plt.grid(axis="y", alpha=0.3)
        plt.title("Snowball with and without POS information")
        plt.legend(loc="upper left", frameon=False, fontsize=8.5); plt.tight_layout()
        plt.savefig(REPORTS / "stemming_snowball_pos.png", dpi=130); plt.close()

    (RESULTS / "figures_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
