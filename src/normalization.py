"""Normalization — genel domain (haber vb.), Türkçe.

SAHİP: Ecem
Bileşenler (sırayla, her token için):
  1. biçim birliği (Türkçe yazım standardı, TDK): Unicode NFC + görünmez karakterler; noktalama
     (’ -> ', “ ” -> ", – — -> -, … / .. -> ..., !!! -> !); sayı/tarih (16/10/2026 -> 16.10.2026,
     19:30 -> 19.30, 25% -> %25, 1,000,000 -> 1.000.000)
  2. Türkçe küçük harf (İ -> i, I -> ı; ama Türkçe bilmeyen BÜYÜK HARF'te I belirsizdir)
  3. yazım-hata/kısaltma lexicon'u (resources/normalization_lexicon.tsv)
  4. harf tekrarı kısaltma (çoooook -> çok)
  5. deasciification (gelecegim -> geleceğim): önce UD train sözlüğü (+ önceki kelime bağlamı);
     sözlükte yoksa kök (kelime başı) sözlüğü + kalan harfler için soldan sağa harf bağlamı
     istatistiği (her c/g/i/o/s/u için çevresindeki harflere bakılır -> ünlü uyumu yakalanır)
  6. typo düzeltme: kelime ne sözlükte var ne de "bilinen kök + bilinen ek" olarak
     açıklanabiliyorsa (ya da train'de görülmemiş harf üçlüsü içeriyorsa) typo sayılır;
     1 düzenleme uzaklığındaki geçerli adaylardan en olası olanı seçilir (kök ve ek sıklığı).
     Geçerli aday yoksa harf dizisi skoru (karakter n-gram) en yüksek olan. Cümle ortasında
     büyük harfle başlayan kelimelere (özel isim) dokunulmaz.
Sözlük ve istatistikler yalnızca UD train'den. Değerlendirme: src/scripts/norm_evaluate.py.
Bkz. CLAUDE.md.

Arayüz sözleşmesi: normalize(token) ve normalize_tokens(List[str]) -> List[str].
Çıktı Türkçe küçük harftir. Çalışma-zamanı zinciri: NORMALIZE -> stopword -> stem.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .io_conllu import iter_conllu
except ImportError:  # src/ altındaki script'ler doğrudan çalıştırıldığında
    from io_conllu import iter_conllu

_ROOT = Path(__file__).resolve().parent.parent
_TRAIN = _ROOT / "data" / "UD_Turkish-BOUN" / "tr_boun-ud-train.conllu"
_LEXICON = _ROOT / "resources" / "normalization_lexicon.tsv"

_TR_LETTERS = set("çğıöşüâîûÇĞİÖŞÜÂÎÛ")
_TO_ASCII = str.maketrans("çğıöşüâîû", "cgiosuaiu")
_TR_OF = {"c": "ç", "g": "ğ", "i": "ı", "o": "ö", "s": "ş", "u": "ü"}
_PUNCT = str.maketrans({"’": "'", "‘": "'", "‚": "'", "`": "'", "´": "'", "′": "'",
                        "“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "‹": '"', "›": '"',
                        "–": "-", "—": "-", "―": "-", "‒": "-",
                        "​": None, "‌": None, "‍": None, "⁠": None,
                        "﻿": None, "­": None})   # görünmez karakterler silinir
_DOTS = re.compile(r"^\.{2,}$")                                     # .. / .... -> ...
_REPEAT_PUNCT = re.compile(r"^[!?]{2,}$")                           # !!! -> !, ?!?! -> ?!
_DATE = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4}|\d{2})(?=$|')")   # 16/10/2026
_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)(?=$|')")                 # 19:30
_PERCENT = re.compile(r"^(\d+(?:[.,]\d+)?)%(?=$|')")                       # 25%
_THOUSANDS_EN = re.compile(r"^\d{1,3}(?:,\d{3}){2,}(?=$|')")               # 1,000,000
_AMBIG_I = "\x01"           # Türkçe bilmeyen büyük harften gelen I: i mi ı mı belli değil
_WORD = re.compile(r"^[^\W\d_]+(?:'[^\W\d_]+)*$")   # harflerden oluşan kelime (kesmeli olabilir)
_RUN3 = re.compile(r"([^\W\d_])\1{2,}")              # aynı harfin 3+ tekrarı
_ROMAN = re.compile(r"^[IVXLCDM]+$")
_TR_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyz"
_ASCII_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
_LM_ORDER = 4


def turkish_lower(text: str) -> str:
    """Türkçe küçük harf: İ -> i, I -> ı (Python'un lower()'ı ikisini de yanlış çevirir)."""
    return text.replace("İ", "i").replace("I", "ı").lower()


def to_ascii(text: str) -> str:
    """Türkçe karakterleri ASCII karşılığına indirir (sözlük anahtarı)."""
    return text.translate(_TO_ASCII)


def normalize_format(token: str) -> str:
    """Biçim birliği (Türkçe yazım standardı, TDK; UD-BOUN da bu biçimi kullanır): Unicode NFC
    (Mac'ten gelen ayrık ş = s + çengel gibi), görünmez karakterler, noktalama ve sayı/tarih."""
    token = unicodedata.normalize("NFC", token).translate(_PUNCT).replace("…", "...")
    if token == "''":
        return '"'
    if _DOTS.match(token):
        return "..."
    if _REPEAT_PUNCT.match(token):
        return "".join(dict.fromkeys(token))
    token = _DATE.sub(r"\1.\2.\3", token)
    token = _TIME.sub(r"\1.\2", token)
    token = _PERCENT.sub(r"%\1", token)
    m = _THOUSANDS_EN.match(token)
    if m:
        token = m.group(0).replace(",", ".") + token[m.end():]
    return token


def canonical(token: str) -> str:
    """Bir temiz tokenin beklenen çıktısı: biçim birliği + Türkçe küçük harf (eval gold'u)."""
    return turkish_lower(normalize_format(token))


def _trigrams(word: str) -> list[str]:
    padded = f"#{word}#"
    return [padded[i:i + 3] for i in range(len(padded) - 2)]


def _edits1(word: str, alphabet: str) -> set[str]:
    """1 düzenleme (sil/yer değiştir/değiştir/ekle) uzaklığındaki tüm diziler."""
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a, b in splits if b]
    swaps = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
    replaces = [a + c + b[1:] for a, b in splits if b for c in alphabet]
    inserts = [a + c + b for a, b in splits for c in alphabet]
    return set(deletes + swaps + replaces + inserts)


class _CharLM:
    """Kelime tipleri üzerinde karakter n-gram skoru (stupid backoff). Bir harf dizisinin ne kadar
    "Türkçe kelimeye benzediğini" ölçer; typo adaylarını sıralamak için."""

    def __init__(self, words: list[str], order: int = _LM_ORDER):
        self.order = order
        self.counts: Counter[str] = Counter()
        for w in words:
            padded = "#" * (order - 1) + w + "#"
            for n in range(1, order + 1):
                for i in range(len(padded) - n + 1):
                    self.counts[padded[i:i + n]] += 1
        self.total = sum(c for g, c in self.counts.items() if len(g) == 1)

    def score(self, word: str) -> float:
        """Harf başına ortalama log-olasılık."""
        padded = "#" * (self.order - 1) + word + "#"
        logp = 0.0
        for i in range(self.order - 1, len(padded)):
            penalty = 1.0
            for n in range(self.order, 0, -1):
                hist, gram = padded[i - n + 1:i], padded[i - n + 1:i + 1]
                denom = self.counts[hist] if hist else self.total
                if self.counts[gram] and denom:
                    logp += math.log(penalty * self.counts[gram] / denom)
                    break
                penalty *= 0.4
            else:
                logp += math.log(1e-7)
        return logp / (len(word) + 1)


class Normalizer:
    """UD train'den sözlük + istatistik kurar, tokenları normalize eder.

    Bayraklar ablation için: her bileşen ayrı açılıp kapatılabilir.
    """

    def __init__(self, train_path: str | Path = _TRAIN, lexicon_path: str | Path = _LEXICON, *,
                 lexicon: bool = True, repeats: bool = True, deasciify: bool = True,
                 context: bool = True, typos: bool = True, typo_margin: float | None = 2.0,
                 typo_min_freq: int | None = 30, min_stem: int = 2, min_end: int = 2,
                 ctx_size: int = 4, min_ctx: int = 1):
        self.use_lexicon, self.use_repeats, self.use_deasciify = lexicon, repeats, deasciify
        self.use_context, self.use_typos = context, typos
        # Türkçe'ye benzeyen (harf üçlüleri görülmüş) ama sözlükte olmayan ve kök+ek olarak da
        # açıklanamayan kelime, ancak 1 düzenleme ötesinde en az bu sıklıkta bir sözlük kelimesi
        # varsa düzeltilir (None: bu tür kelimelere hiç dokunma)
        self.typo_min_freq = typo_min_freq
        # geçerli aday bulunamazsa: harf dizisi skoru orijinalden en az bu kadar yüksek olan
        # aday seçilir (None: bu son çare kapalı)
        self.typo_margin = typo_margin
        # "kök + ek" geçerliliği: kök en az min_stem harf, ek train'de en az min_end farklı
        # kelimede son olarak görülmüş olmalı
        self.min_stem, self.min_end = min_stem, min_end
        self.ctx_size, self.min_ctx = ctx_size, min_ctx
        self._pad = "#" * ctx_size
        self._build(Path(train_path))
        self.lexicon = self._load_lexicon(Path(lexicon_path))

    # --- kaynaklar ---------------------------------------------------------------------

    def _build(self, path: Path) -> None:
        self.freq: Counter[str] = Counter()
        self.bigram: Counter[tuple[str, str]] = Counter()
        for sent in iter_conllu(path):
            prev = "<s>"
            for tok in sent.tokens:
                w = canonical(tok.form)
                self.freq[w] += 1
                self.bigram[(prev, w)] += 1
                prev = w

        # ASCII anahtar -> o anahtara inen sözlük formları (en sık önce)
        self.by_key: dict[str, list[str]] = defaultdict(list)
        for w in self.freq:
            self.by_key[to_ascii(w)].append(w)
        for forms in self.by_key.values():
            forms.sort(key=self.freq.__getitem__, reverse=True)

        words = [w for w in self.freq if _WORD.match(w)]

        # Kök (kelime başı) sözlüğü: ASCII önek -> Türkçe önekler (en sık önce). Türkçe sondan
        # eklemeli olduğu için sözlükte olmayan kelimenin başı çoğunlukla bilinen bir kelimenin
        # başıdır: gelecegimizi -> "geleceğimiz" + "i".
        prefix_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for w in words:
            a = to_ascii(w)
            for n in range(2, len(w) + 1):
                prefix_counts[a[:n]][w[:n]] += self.freq[w]
        self.prefix = {k: [f for f, _ in c.most_common(3)] for k, c in prefix_counts.items()}

        # Harf bağlamı istatistiği: (pencere, sol Türkçe harfler, harf, sağ ASCII harfler) ->
        # [ASCII kalır, Türkçe olur]. Soldan sağa çözülürken sol taraf zaten karara bağlanmış
        # olduğundan ünlü uyumu yakalanır. Her kelime tipi bir kez sayılır.
        k = self.ctx_size
        self.ctx: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])
        for w in words:
            a = to_ascii(w)
            left, right = self._pad + w, a + self._pad
            for i, ch in enumerate(a):
                if ch not in _TR_OF:
                    continue
                if w[i] == ch:
                    label = 0
                elif w[i] == _TR_OF[ch]:
                    label = 1
                else:   # î, û gibi şapkalı harfler — öğrenme dışı
                    continue
                for n in range(1, k + 1):
                    self.ctx[(n, left[i + k - n:i + k], ch, right[i + 1:i + 1 + n])][label] += 1
        self.ctx = dict(self.ctx)

        # Kök + ek istatistiği (typo tespiti ve adayları için): sözlükteki bir kelime başka bir
        # sözlük kelimesiyle başlıyorsa kalan kısım bir "ek"tir (öğretmenler = öğretmen + ler).
        # Hem Türkçe harflerle hem ASCII anahtarlarla tutulur (Türkçe karaktersiz yazım için).
        self.n_tokens = sum(self.freq.values())
        self.key_freq: Counter[str] = Counter()
        for w, f in self.freq.items():
            self.key_freq[to_ascii(w)] += f
        self.end_tr, self.end_ascii = Counter(), Counter()
        vocab_tr = set(words)
        vocab_ascii = {to_ascii(w) for w in words}
        for w in words:
            a = to_ascii(w)
            for k in range(self.min_stem, len(w)):
                if w[:k] in vocab_tr:
                    self.end_tr[w[k:]] += 1
                if a[:k] in vocab_ascii:
                    self.end_ascii[a[k:]] += 1
        self.n_end_tr = sum(self.end_tr.values())
        self.n_end_ascii = sum(self.end_ascii.values())

        # Typo tespiti (görülmemiş harf üçlüsü) ve aday sıralama (karakter n-gram) için
        self.tri_tr = Counter(t for w in words for t in _trigrams(w))
        self.tri_ascii = Counter(t for w in words for t in _trigrams(to_ascii(w)))
        self.lm_tr = _CharLM(words)
        self.lm_ascii = _CharLM([to_ascii(w) for w in words])

    @staticmethod
    def _load_lexicon(path: Path) -> dict[str, str]:
        lex: dict[str, str] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#"):
                    noisy, clean = line.split("\t")[:2]
                    lex[turkish_lower(noisy.strip())] = clean.strip()
        return lex

    # --- adımlar -------------------------------------------------------------------------

    @staticmethod
    def _lower(token: str) -> tuple[str, bool]:
        """Küçük harfe indirir. Dönüş: (küçük form, Türkçe klavyeyle mi yazılmış).

        Türkçe karakter içermeyen token'da her c/g/i/o/s/u belirsizdir (deasciify karar verir).
        Türkçe karakter içeren token'da yalnızca büyük I belirsizdir (KİTAP yerine KITAP).
        """
        if not any(c in _TR_LETTERS for c in token):
            return token.lower(), False
        return token.replace("İ", "i").replace("I", _AMBIG_I).lower(), True

    @staticmethod
    def _fits(form: str, w: str) -> bool:
        """Aday form, belirsiz olmayan harflerde w ile aynı mı?"""
        return all(c == _AMBIG_I or f == c for f, c in zip(form, w))

    def _lookup(self, w: str, tr_keyboard: bool, prev: str) -> str | None:
        """Sözlükteki en uygun formu bulur; belirsiz harfler dışındaki harfler aynı kalmalı."""
        forms = self.by_key.get(to_ascii(w.replace(_AMBIG_I, "i")), [])
        if tr_keyboard:
            forms = [f for f in forms if self._fits(f, w)]
        if not forms:
            return None
        if self.use_context and len(forms) > 1:
            return max(forms, key=lambda f: (self.bigram[(prev, f)], self.freq[f]))
        return forms[0]

    def _predict_tr(self, left: str, ch: str, right: str) -> bool:
        """Harf Türkçe karşılığına mı dönmeli? Yeterince görülmüş en geniş bağlamdan karar ver."""
        for n in range(self.ctx_size, 0, -1):
            c = self.ctx.get((n, left[-n:], ch, right[:n]))
            if c and c[0] + c[1] >= self.min_ctx and c[0] != c[1]:
                return c[1] > c[0]
        return False

    def _restore_by_context(self, w: str, tr_keyboard: bool) -> str:
        """Sözlükte olmayan kelime: kökü önek sözlüğünden al, kalan belirsiz harfleri soldan
        sağa harf bağlamı istatistiğiyle çöz."""
        a = to_ascii(w.replace(_AMBIG_I, "i"))
        out: list[str] = []
        for n in range(len(a), 1, -1):
            fitting = [f for f in self.prefix.get(a[:n], ()) if not tr_keyboard or self._fits(f, w)]
            if fitting:
                out = list(fitting[0])
                break
        right = a + self._pad
        for i in range(len(out), len(w)):
            ch = w[i]
            ambiguous = (ch == _AMBIG_I) if tr_keyboard else (ch in _TR_OF)
            if ambiguous:
                base = a[i]
                left = self._pad + "".join(out)
                out.append(_TR_OF[base] if self._predict_tr(left, base, right[i + 1:]) else base)
            else:
                out.append(ch)
        return "".join(out)

    def _collapse_repeats(self, w: str, tr_keyboard: bool, prev: str) -> str:
        """3+ tekrar eden harfleri 1 veya 2'ye indirir; sözlükte olan aday tercih edilir."""
        runs = list(_RUN3.finditer(w))
        if not runs:
            return w
        candidates = [""]
        last = 0
        for m in runs:
            ch = m.group(1)
            candidates = [c + w[last:m.start()] + k for c in candidates for k in (ch, ch * 2)]
            last = m.end()
        candidates = [c + w[last:] for c in candidates]
        known = [(c, f) for c in candidates if (f := self._lookup(c, tr_keyboard, prev))]
        if known:
            return max(known, key=lambda cf: self.freq[cf[1]])[0]
        return candidates[0]    # hepsi tek harfe (Türkçe'de çift harf azdır)

    def _looks_like_typo(self, w: str, tr_keyboard: bool) -> bool:
        """Train'deki hiçbir kelimede görülmemiş bir harf üçlüsü varsa Türkçe'ye benzemiyor."""
        if tr_keyboard:
            return any(self.tri_tr[t] == 0 for t in _trigrams(w))
        return any(self.tri_ascii[t] == 0 for t in _trigrams(to_ascii(w)))

    def _word_logp(self, w: str, tr_keyboard: bool) -> float | None:
        """Kelimenin log-olasılığı: sözlükteyse sıklığından, değilse en iyi "kök + ek"
        ayrımından. Hiçbiriyle açıklanamıyorsa None (geçersiz kelime)."""
        vocab = self.freq if tr_keyboard else self.key_freq
        ends, n_end = (self.end_tr, self.n_end_tr) if tr_keyboard else (self.end_ascii, self.n_end_ascii)
        if vocab.get(w):
            return math.log(vocab[w] / self.n_tokens)
        best = None
        for k in range(self.min_stem, len(w)):
            fs, fe = vocab.get(w[:k], 0), ends.get(w[k:], 0)
            if fs and fe >= self.min_end:
                lp = math.log(fs / self.n_tokens) + math.log(fe / n_end)
                if best is None or lp > best:
                    best = lp
        return best

    def _correct_typo(self, w: str, tr_keyboard: bool, prev: str) -> str | None:
        """Kelime geçerliyse None. Değilse 1 düzenleme uzaklığındaki geçerli adaylardan en
        olası olanı (önceki kelimeyle birlikte görülmüşse küçük bir bonusla); geçerli aday yoksa
        harf dizisi skoru en yüksek olanı döndürür."""
        odd = self._looks_like_typo(w, tr_keyboard)
        if not odd and (self.typo_min_freq is None or self._word_logp(w, tr_keyboard) is not None):
            return None
        alphabet = _TR_ALPHABET if tr_keyboard else _ASCII_ALPHABET
        edits = _edits1(w, alphabet)
        scored = []
        for c in edits:
            lp = self._word_logp(c, tr_keyboard)
            if lp is not None:
                if self.use_context and tr_keyboard:
                    lp += math.log1p(self.bigram[(prev, c)])
                scored.append((lp, c))
        if not odd:
            # Türkçe'ye benzeyen ama açıklanamayan kelime: yalnızca çok sık bir sözlük kelimesine
            # düzelt (nadir ama doğru kelimeleri bozmamak için)
            vocab = self.freq if tr_keyboard else self.key_freq
            scored = [(lp, c) for lp, c in scored if vocab.get(c, 0) >= self.typo_min_freq]
            if not scored:
                return None
        if scored:
            best = max(scored)[1]
            if tr_keyboard:
                return best
            return self._lookup(best, False, prev) or self._restore_by_context(best, False)
        if self.typo_margin is None:
            return None
        plausible = [c for c in edits if len(c) >= 2 and not self._looks_like_typo(c, tr_keyboard)]
        if not plausible:
            return None
        lm = self.lm_tr if tr_keyboard else self.lm_ascii
        best = max(plausible, key=lm.score)
        if lm.score(best) - lm.score(w) < self.typo_margin:
            return None
        return best if tr_keyboard else self._restore_by_context(best, False)

    # --- ana arayüz ----------------------------------------------------------------------

    def normalize(self, token: str, prev: str = "<s>") -> str:
        """Tek bir tokeni normalize eder. `prev`: bir önceki tokenin normalize hâli."""
        token = normalize_format(token)
        if "://" in token or "@" in token or token.startswith("#"):
            return token                          # URL / e-mail / hashtag / mention: dokunma
        if not _WORD.match(token) or _ROMAN.match(token):
            return turkish_lower(token)           # sayı, kısaltma (Dr.), noktalama, romen rakamı

        w, tr_keyboard = self._lower(token)
        plain = w.replace(_AMBIG_I, "ı")
        # BÜYÜK HARFLİ kısa token kısaltmadır (TM, ABD, TRT): lexicon'a sokma
        use_lexicon = self.use_lexicon and not (token.isupper() and len(token) <= 4)

        if use_lexicon and plain in self.lexicon:
            return self.lexicon[plain]
        if self.use_repeats:
            w = self._collapse_repeats(w, tr_keyboard, prev)
            plain = w.replace(_AMBIG_I, "ı")
            if use_lexicon and plain in self.lexicon:
                return self.lexicon[plain]
        if not self.use_deasciify:
            return plain

        found = self._lookup(w, tr_keyboard, prev)
        if found is not None:
            return found
        proper_noun = token[:1].isupper() and prev != "<s>"   # cümle ortasında büyük harf
        if self.use_typos and w.isalpha() and len(w) >= 4 and not proper_noun:
            fixed = self._correct_typo(plain if tr_keyboard else w, tr_keyboard, prev)
            if fixed is not None:
                return fixed
        return self._restore_by_context(w, tr_keyboard)

    def normalize_tokens(self, tokens: list[str]) -> list[str]:
        """Token listesini soldan sağa normalize eder (bağlam için önceki çıktı kullanılır)."""
        out: list[str] = []
        prev = "<s>"
        for t in tokens:
            n = self.normalize(t, prev)
            out.append(n)
            prev = n
        return out


_DEFAULT: Normalizer | None = None


def _default() -> Normalizer:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = Normalizer()
    return _DEFAULT


def normalize(token: str) -> str:
    """Tek bir tokeni normalize et (ortak arayüz)."""
    return _default().normalize(token)


def normalize_tokens(tokens: list[str]) -> list[str]:
    """Token listesini normalize eder (ortak arayüz)."""
    return _default().normalize_tokens(tokens)


if __name__ == "__main__":
    print(normalize_tokens("Bugun cooook guzel bir gun , KITAP okudum ve ISIK yandı !".split()))
