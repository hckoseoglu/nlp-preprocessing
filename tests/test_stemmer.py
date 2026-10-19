"""Stemmer birim testleri: python3 -m unittest tests.test_stemmer -v"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stemmer import Stemmer  # noqa: E402
from stemmer.suffixes import Suffix, expand  # noqa: E402

CASES = [
    # (girdi, beklenen kök)
    # --- isim çekimi + yumuşama / ünlü düşmesi / ikizleşme
    ("kitabı", "kitap"), ("kitaplar", "kitap"), ("kitaplarımızdan", "kitap"), ("kalemler", "kalem"),
    ("öğretmenlerimizin", "öğretmen"), ("burnu", "burun"), ("ağzında", "ağız"), ("oğlu", "oğul"),
    ("hakkında", "hak"), ("rengi", "renk"), ("gözlüğü", "göz"), ("ağacın", "ağaç"), ("suyu", "su"),  # gözlük korpusta görülmemiş → türetim soyulur
    ("çağırıyorlardı", "çağır"), ("geliyorlardı", "gel"), ("gelirlerdi", "gel"),  # -yor/-ir + 3pl -lar + ek-fiil: UD böler, ham metinde bütün gelir
    ("arabası", "araba"), ("arabasıyla", "araba"), ("evdekiler", "ev"), ("evinde", "ev"), ("saati", "saat"),
    # --- ek-fiil
    ("önemliydi", "önem"), ("güzeldi", "güzel"), ("öğrenciyim", "öğrenci"), ("evdeyken", "ev"), ("hastaymış", "hasta"),
    # --- fiil çekimi
    ("gidiyordum", "git"), ("gittik", "git"), ("ediyoruz", "et"), ("edilmiş", "et"), ("bekliyor", "bekle"),
    ("diyor", "de"), ("diyecek", "de"), ("yiyip", "ye"), ("anlıyorum", "anla"), ("gelmedi", "gel"),
    ("gelemeyecekler", "gel"), ("gelebilirdik", "gel"), ("öldürülen", "öl"), ("yapılabilir", "yap"),
    ("okumak", "oku"), ("geldiğimizde", "gel"), ("koşarken", "koş"), ("unutmayın", "unut"),
    ("gelmezse", "gel"), ("yaşadığını", "yaşa"), ("olduğunu", "ol"), ("söylüyor", "söyle"),
    # --- türetim
    ("gelişmelerden", "geliş"), ("çocukluğumuzda", "çocuk"), ("hastalık", "hasta"), ("oyuncular", "oyun"),
    # --- belirsizlik: en uzun kök
    ("kalem", "kalem"), ("kalemi", "kalem"), ("evinde", "ev"), ("içinde", "iç"),
    # --- özel ad / kesme işareti / sayı
    ("İstanbul'daki", "İstanbul"), ("Ankara'ya", "Ankara"), ("Tesisleri'nde", "Tesis"), ("19.30'da", "19.30"),
    # --- zamir düzensizlikleri
    ("bana", "ben"), ("onların", "o"), ("bunu", "bu"), ("benimki", "ben"), ("onun", "o"), ("beni", "ben"),
    # --- ek-fiil parçacıkları (UD sözleşmesi)
    ("ydı", "y"), ("dır", "i"), ("ise", "i"), ("mı", "mi"), ("musunuz", "mi"),
    # --- değişmeyenler
    ("ve", "ve"), ("çok", "çok"), ("...", "..."), ("2023", "2023"),
]


class TestStemmer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.st = Stemmer()

    def test_cases(self):
        fails = []
        for w, exp in CASES:
            got = self.st.stem(w)
            if got != exp:
                fails.append(f"{w} → {got} (beklenen {exp})")
        self.assertFalse(fails, "\n" + "\n".join(fails))

    def test_case_count(self):
        self.assertGreaterEqual(len(CASES), 40)

    def test_stem_tokens_interface(self):
        self.assertEqual(self.st.stem_tokens(["kitabı", "gidiyordum"]), ["kitap", "git"])


class TestAllomorphs(unittest.TestCase):
    def test_imiz(self):
        surf = {a.surface for a in expand(Suffix("POSS1P", "(I)mIz", "POSS", "-", "-"))}
        self.assertEqual(surf, {"mız", "miz", "muz", "müz", "ımız", "imiz", "umuz", "ümüz"})

    def test_dir(self):
        surf = {a.surface for a in expand(Suffix("COP_DIR", "DIr", "COP_DIR", "-", "-"))}
        self.assertEqual(len(surf), 8)

    def test_acak(self):
        surf = {a.surface for a in expand(Suffix("FUT", "(y)AcAK", "TENSE", "-", "-"))}
        self.assertIn("yeceğ", surf)
        self.assertIn("acak", surf)
        self.assertEqual(len(surf), 8)


if __name__ == "__main__":
    unittest.main()
