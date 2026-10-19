"""Ek sözlüğü (lexicon/suffixes.tsv) okuma ve allomorf üretimi.

Şablon notasyonu: A={a,e} I={ı,i,u,ü} D={d,t} C={c,ç} K={k,ğ}; (x) = opsiyonel tampon (y/s/n/ş ya da I/A).
Üretimde ek-içi ünlü uyumu uygulanır: (I)mIz → mız miz muz müz ımız imiz umuz ümüz (16 değil 8).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .phonology import VOWELS, harmonic

ARCHI_CONS = {"D": "dt", "C": "cç", "K": "kğ"}


@dataclass(frozen=True)
class Suffix:
    id: str
    form: str
    cls: str
    cat_in: str   # DER için girdi kategorisi (N/V), diğerlerinde "-"
    cat_out: str


@dataclass(frozen=True)
class Allomorph:
    surface: str
    suffix: Suffix
    opt: str | None          # opsiyonel tampon harfi/arşifonemi ("y", "s", "n", "ş", "I", "A") ya da None
    opt_present: bool        # tampon bu allomorfta var mı
    first_vowel: str | None  # ilk arşifonem ünlünün gerçekleşmesi (uyum kısıtı için); literal ise None
    first_archi: str | None  # ilk ünlünün arşifonemi ("A"/"I") ya da None
    init_archi: str | None   # ilk harf D/C arşifoneminden geldiyse ("D"/"C"), benzeşme kısıtı için
    final_k: str | None      # son harf K arşifoneminden geldiyse gerçekleşen harf ("k"/"ğ")

    @property
    def id(self) -> str:
        return self.suffix.id

    @property
    def cls(self) -> str:
        return self.suffix.cls

    @property
    def is_yor(self) -> bool:
        return self.suffix.id == "PROG"


def _tokens(form: str) -> list[tuple[str, bool]]:
    """Şablonu (sembol, opsiyonel mi) listesine çevir."""
    out: list[tuple[str, bool]] = []
    i = 0
    while i < len(form):
        ch = form[i]
        if ch == "(":
            j = form.index(")", i)
            for c in form[i + 1:j]:
                out.append((c, True))
            i = j + 1
        else:
            out.append((ch, False))
            i += 1
    return out


def expand(suffix: Suffix) -> list[Allomorph]:
    """Şablonu allomorflara aç. Durum: (surface, prev_vowel, first_vowel, first_archi, init_archi, final_k);
    first_archi "" ise ilk ünlü literal'dir (uyum kısıtı uygulanmaz)."""
    toks = _tokens(suffix.form)
    has_opt = any(o for _, o in toks)
    opt_sym = next((c for c, o in toks if o), None)
    results: list[Allomorph] = []
    for present in ([True, False] if has_opt else [True]):
        syms = [c for c, o in toks if present or not o]
        n = len(syms)
        partial = [("", None, None, None, None, None)]
        for idx, sym in enumerate(syms):
            nxt = []
            for surf, prev, fv, fa, ia, fk in partial:
                if sym in ("A", "I"):
                    for v in harmonic(sym, prev):
                        nxt.append((surf + v, v, fv if fv is not None else v,
                                    fa if fa is not None else sym, ia, None))
                elif sym in ARCHI_CONS:
                    for c in ARCHI_CONS[sym]:
                        nia = ia if ia is not None else (sym if idx == 0 and sym in "DC" else None)
                        nfk = c if (sym == "K" and idx == n - 1) else None
                        nxt.append((surf + c, prev, fv, fa, nia, nfk))
                elif sym in VOWELS:                       # literal ünlü (yor, ki, ken ...)
                    nxt.append((surf + sym, sym, fv if fv is not None else sym,
                                fa if fa is not None else "", ia, None))
                else:
                    nxt.append((surf + sym, prev, fv, fa, ia, None))
            partial = nxt
        for surf, prev, fv, fa, ia, fk in partial:
            if not surf:
                continue
            results.append(Allomorph(
                surface=surf, suffix=suffix, opt=opt_sym, opt_present=present if has_opt else False,
                first_vowel=fv if fa else None, first_archi=fa if fa else None, init_archi=ia, final_k=fk))
    return results


def load_suffixes(path: Path) -> list[Suffix]:
    out: list[Suffix] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        sid, form, cls = parts[:3]
        cin = parts[3] if len(parts) > 3 else "-"
        cout = parts[4] if len(parts) > 4 else "-"
        out.append(Suffix(sid, form, cls, cin, cout))
    return out


def load_allomorphs(path: Path) -> tuple[list[Suffix], list[Allomorph]]:
    suffixes = load_suffixes(path)
    allos: list[Allomorph] = []
    for s in suffixes:
        allos.extend(expand(s))
    return suffixes, allos
