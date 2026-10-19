"""lexicon/roots.tsv üretir: TRmorph kök sözlüğü (Çöltekin 2010, MIT) + UD-BOUN train gold kökleri.

Kullanım:
  python3 src/scripts/stem_build_roots.py --trmorph /path/to/TRmorph [--derived lexicon/derived.tsv]

TRmorph lexicon notasyonu (lexicon/<file>: "kök Sınıf; ! yorum"):
  ^k ^t ^p ^c ^g  son ünsüz ünlü önünde yumuşar (kita^p → kitap/kitabı)       → voicing=1
  @DEL@          önceki ünlü ek alınca düşer (buru@DEL@n → burun/burnu)        → vowel_drop=1
  @DUP@          son ünsüz ünlü önünde ikizleşir (ha@DUP@k → hak/hakkı)         → doubling=1
  ^pA ^pO ^pU ^pÂ art ünlü ama ince ek alır (sa^pAt → saat/saati)              → inv_harmony=1
  ˈ              vurgu işareti (silinir);  a:b  iki yazım;  %  boşluk (çok sözcüklü → atla)
  "! derived" yorumu → derived=1 (sözlükselleşmiş türetim)
Sütunlar: root pos voicing vowel_drop inv_harmony doubling derived freq source
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stem_gold import ROOT, fold, gold_root, load_split, read_derived  # noqa: E402

TRMORPH_FILES = ["noun", "verb", "verb_la", "adjective", "adverb", "pronoun", "postposition",
                 "conjunction", "determiner", "interjection", "qwords", "clitics"]
VOWELS = set("aeıioöuü")
BACK = set("aıou")
VOICED = {"p": "b", "ç": "c", "t": "d", "k": "ğ", "g": "ğ"}
ALPHA = re.compile(r"^[a-zçğıöşü][a-zçğıöşü\-]*$")
COLS = ["root", "pos", "voicing", "vowel_drop", "inv_harmony", "doubling", "derived", "freq", "source"]


def map_class(cls: str) -> str:
    if cls.startswith("V"):
        return "AUX" if cls == "V_i" else "VERB"
    if cls.startswith("N") or cls in ("p", "s"):
        return "NOUN"
    if cls.startswith("Adj"):
        return "ADJ"
    if cls.startswith("Adv"):
        return "ADV"
    if "Prn" in cls:
        return "PRON"
    if "PostP" in cls:
        return "ADP"
    if cls.startswith("Cnj"):
        return "SCONJ" if cls == "CnjSub" else "CCONJ"
    if cls.startswith("Det"):
        return "DET"
    if cls == "Interjection":
        return "INTJ"
    if cls.startswith("Q"):
        return {"QAdj": "ADJ", "QAdv": "ADV", "QNum": "DET"}.get(cls, "PRON")
    if cls in ("mI", "degil"):
        return "PART"
    if cls in ("var", "yok"):
        return "ADJ"
    return "NOUN"


def parse_trmorph(lex_dir: Path) -> tuple[dict, Counter]:
    """→ {(root, pos): flags-dict}, istatistik."""
    entries: dict[tuple[str, str], dict] = {}
    st = Counter()
    for fname in TRMORPH_FILES:
        for line in (lex_dir / fname).open(encoding="utf-8"):
            body, _, comment = line.partition("!")
            body = body.strip()
            if not body:
                continue
            m = re.match(r"(\S+)\s+(\S+);", body)
            if not m:
                st["unparsed"] += 1
                continue
            raw, cls = m.groups()
            if "%" in raw or "^s" in raw or "#" in raw:
                st["skipped_multiword_or_foreign"] += 1
                continue
            flags = {
                "voicing": int(bool(re.search(r"\^[kptcçg](?![A-ZÂ])", raw))),
                "inv_harmony": int(bool(re.search(r"\^p[AOUÂ]", raw))),
                "vowel_drop": int("@DEL@" in raw),
                "doubling": int("@DUP@" in raw),
                "derived": int("derived" in comment),
            }
            s = raw.replace("ˈ", "")
            s = re.sub(r"\^p([AOUÂ])", lambda mm: mm.group(1).lower(), s)
            s = re.sub(r"@DELS?@|@DUP@|\^", "", s)
            pos = map_class(cls)
            for surf in s.split(":"):
                surf = fold(surf)
                if not ALPHA.match(surf):
                    st["skipped_nonalpha"] += 1
                    continue
                key = (surf, pos)
                if key in entries:
                    for k in flags:
                        entries[key][k] |= flags[k]
                    st["dup_merged"] += 1
                else:
                    entries[key] = dict(flags)
                    st[f"trmorph_{pos}"] += 1
    return entries, st


def infer_ud_flags(root: str, forms: list[str]) -> dict:
    """Train yüzey formlarından morfofonemik bayrak kanıtı çıkar."""
    f = {"voicing": 0, "vowel_drop": 0, "inv_harmony": 0, "doubling": 0}
    last = root[-1]
    for w in forms:
        if len(w) <= len(root):
            continue
        # yumuşama: kitap → kitabı
        if last in VOICED and w.startswith(root[:-1] + VOICED[last]) and w[len(root)] in VOWELS:
            f["voicing"] = 1
        # ikizleşme: hak → hakkı
        if last not in VOWELS and w.startswith(root + last) and w[len(root) + 1:len(root) + 2] in VOWELS:
            f["doubling"] = 1
        # ünlü düşmesi: burun → burnu
        if len(root) >= 3 and root[-2] in "ıiuü" and root[-1] not in VOWELS and root[-3] not in VOWELS:
            dropped = root[:-2] + root[-1]
            if w.startswith(dropped) and w[len(dropped):len(dropped) + 1] in VOWELS:
                f["vowel_drop"] = 1
        # ters uyum: saat → saati, alkol → alkolü
        if w.startswith(root):
            nxt = w[len(root):]
            m = re.match(r"[yns]?([aeıioöuü])", nxt)
            rv = [c for c in root if c in VOWELS]
            if m and rv and rv[-1] in BACK and m.group(1) in "eiöü":
                f["inv_harmony"] += 1
    f["inv_harmony"] = int(f["inv_harmony"] >= 2)
    return f


def write_roots(path: str, entries: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(COLS) + "\n")
        for (r, p) in sorted(entries):
            e = entries[(r, p)]
            fh.write("\t".join(map(str, [r, p, e["voicing"], e["vowel_drop"], e["inv_harmony"],
                                         e["doubling"], e["derived"], e["freq"], e["source"]])) + "\n")


PURE_INFL = {"PLUR", "POSS", "CASE", "CASE_N", "KI", "NEG", "ABIL", "NEGABIL", "TENSE", "TENSE_NEG", "TENSE2",
             "CONV2", "IMP", "PERS_A", "PERS_B", "CONV"}   # ek-fiil yolu yok (gök-tür-k gibi sahte çözümler)


def prune_noise(entries: dict, lex_dir: Path) -> list:
    """UD lemma gürültüsü: yalnız UD'den gelen, ≤2 kez görülen ve sık bir kökün SAF ÇEKİMİ olarak
    çözümlenebilen 'kökler' (beni, insanlar, suyunu, olma) atılır. İkinci geçiş: stemmer budanmamış sözlükle yüklenir."""
    sys.path.insert(0, str(ROOT / "src"))
    from stemmer import Config, Stemmer
    st_ = Stemmer(lex_dir, Config(use_derived=False, use_der_rules=False, use_copula=False))
    dropped = []
    for (r, pos), e in list(entries.items()):
        if e["source"] != "ud" or e["freq"] > 4 or pos == "PROPN":
            continue
        if r.endswith("y") and len(r) > 2 and r[-2] in VOWELS and any(x["freq"] >= 5 for (rr, _), x in entries.items() if rr == r[:-1]):
            dropped.append((r, pos, e["freq"], f"{r[:-1]} + y (kaynaştırma harfi lemma'da kalmış)"))
            del entries[(r, pos)]
            continue
        cat = "V" if pos == "VERB" else "N"
        for c in sorted(st_._analyze(r, allow_der=False), key=st_._key):
            if (c.suffixes and c.entry is not None and c.root != r and c.entry.freq >= 5
                    and c.entry.category == cat and all(cl in PURE_INFL for cl in c.classes)):
                dropped.append((r, pos, e["freq"], str(c)))
                del entries[(r, pos)]
                break
    return dropped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trmorph", required=True, help="TRmorph klon kök dizini")
    ap.add_argument("--no-prune", action="store_true")
    ap.add_argument("--derived", default=str(ROOT / "lexicon" / "derived.tsv"))
    ap.add_argument("--out", default=str(ROOT / "lexicon" / "roots.tsv"))
    ap.add_argument("--stats", default=str(ROOT / "results" / "roots_stats.md"))
    args = ap.parse_args()

    entries, st = parse_trmorph(Path(args.trmorph) / "lexicon")
    for key in entries:
        entries[key]["freq"] = 0
        entries[key]["source"] = "trmorph"

    # --- UD train gold kökleri
    derived = read_derived(Path(args.derived))
    train = load_split("train")
    lemma_upos: dict[str, Counter] = defaultdict(Counter)
    for t in train:
        lemma_upos[t.lemma_n][t.upos] += 1
    trm_pos: dict[str, set] = defaultdict(set)
    for (r, p) in entries:
        trm_pos[r].add(p)

    root_freq: Counter = Counter()
    root_forms: dict[str, list[str]] = defaultdict(list)
    for t in train:
        g = gold_root(t, derived)
        if not ALPHA.match(g) or g == "y":
            st["ud_skipped_nonalpha"] += 1
            continue
        if g != t.lemma_n:                      # türetim eşlemesi → kökün kendi UPOS'u
            if g in lemma_upos:
                pos = lemma_upos[g].most_common(1)[0][0]
            elif g in trm_pos:
                pos = sorted(trm_pos[g])[0]
            else:
                pos = t.upos
        else:
            pos = t.upos
        if pos == "AUX" and ("VERB" in trm_pos.get(g, ())):
            pos = "VERB"
        root_freq[(g, pos)] += 1
        root_forms[g].append(fold(t.form))

    for (g, pos), n in root_freq.items():
        flags = infer_ud_flags(g, root_forms[g])
        if (g, pos) in entries:
            e = entries[(g, pos)]
            for k in flags:
                e[k] |= flags[k]
            e["freq"] += n
            e["source"] = "trmorph+ud"
            st["ud_merged"] += 1
        else:
            if n == 1 and g in trm_pos:          # tek örnek + yüzey TRmorph'ta başka POS'la var → annotasyon gürültüsü
                st["ud_dropped_noise_pos"] += 1
                continue
            flags.update(derived=0, freq=n, source="ud")
            # aynı yüzey başka POS ile TRmorph'ta varsa bayraklarını miras al
            for p2 in trm_pos.get(g, ()):
                for k in ("voicing", "vowel_drop", "inv_harmony", "doubling"):
                    flags[k] |= entries[(g, p2)][k]
            entries[(g, pos)] = flags
            st[f"ud_new_{pos}"] += 1

    write_roots(args.out, entries)
    if not args.no_prune:
        dropped = prune_noise(entries, Path(args.out).parent)
        st["ud_pruned_noise_lemma"] = len(dropped)
        write_roots(args.out, entries)
        Path(args.stats).with_name("roots_pruned.tsv").write_text(
            "root\tpos\tfreq\tanalysis\n" + "".join(f"{r}\t{p}\t{f}\t{a}\n" for r, p, f, a in dropped),
            encoding="utf-8")

    pos_c = Counter(p for (_, p) in entries)
    src_c = Counter(e["source"] for e in entries.values())
    flag_c = {k: sum(e[k] for e in entries.values()) for k in ("voicing", "vowel_drop", "inv_harmony", "doubling", "derived")}
    lines = ["# Kök sözlüğü istatistikleri (stem_build_roots.py)", "",
             f"- toplam (kök, POS) satırı: {len(entries)}; farklı yüzey: {len({r for r, _ in entries})}",
             f"- kaynak: {dict(src_c)}", f"- POS: {dict(pos_c.most_common())}", f"- bayraklar: {flag_c}", "",
             "## Ayrıştırma istatistikleri", ""] + [f"- {k}: {v}" for k, v in sorted(st.items())]
    Path(args.stats).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
