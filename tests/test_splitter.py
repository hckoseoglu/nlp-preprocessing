"""Sentence splitter testleri: aday çıkarımı, sahte paragraf etiketleri, rule-based kararlar, NB eğitimi (stdlib)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from splitting import NBSplitter, RuleSplitter, build_paragraphs, candidates, labeled_candidates  # noqa: E402
from splitting.corpus import lowercase_paragraph, unreachable_bounds  # noqa: E402
from splitting.features import extract  # noqa: E402
from textutil import is_abbreviation, is_initial, is_number, load_abbreviations, tr_lower  # noqa: E402

ABBRS = load_abbreviations()
UD_TRAIN = ROOT / "data" / "UD_Turkish-BOUN" / "tr_boun-ud-train.conllu"


class TextUtilTests(unittest.TestCase):
    def test_tr_lower_keeps_length(self):
        self.assertEqual(tr_lower("İSTANBUL Iğdır"), "istanbul ığdır")
        self.assertEqual(len(tr_lower("İİİ")), 3)

    def test_word_classes(self):
        self.assertTrue(is_abbreviation("Dr", ABBRS) and is_abbreviation("vb.", ABBRS) and is_abbreviation("\"Prof", ABBRS))
        self.assertFalse(is_abbreviation("geldi", ABBRS))
        self.assertTrue(is_initial("A") and is_initial("T.C") and is_initial("M.Ö"))
        self.assertFalse(is_initial("Ali"))
        self.assertTrue(is_number("2") and is_number("19.30") and is_number("08.02.2007") and is_number("%25"))
        self.assertFalse(is_number("2a"))


class CandidateTests(unittest.TestCase):
    def test_candidates_left_right(self):
        c = candidates('"Geldi." dedi. Sonra gitti.')
        self.assertEqual([(x.punct, x.close, x.left, x.right) for x in c],
                         [(".", '"', '"Geldi', "dedi."), (".", "", "dedi", "Sonra"), (".", "", "gitti", "")])
        self.assertTrue(c[-1].at_end)

    def test_ellipsis_and_combos(self):
        c = candidates("Olsun... Ne?! Peki… tamam; evet: hayır")
        self.assertEqual([x.punct for x in c], ["...", "?!", "...", ";", ":"])

    def test_lone_opening_quote_merges_with_next_word(self):
        c = candidates('Soruyor sınavda. " Fakat biri itiraz etti.')
        self.assertEqual(c[0].right, '"Fakat')

    def test_paragraph_labels(self):
        paras = build_paragraphs(["Ali geldi.", "Dr. Ayşe gitti.", "Hava soğuk"], size=3, seed=0)
        self.assertEqual(len(paras), 1)
        text, bounds = paras[0]
        labeled = labeled_candidates(text, bounds)
        self.assertEqual(sum(c.label for c in labeled), len(bounds) - len(unreachable_bounds(text, bounds)))
        for c in labeled:
            self.assertEqual(c.label, c.end in bounds)
        self.assertEqual(len(lowercase_paragraph(text)), len(text))


class RuleSplitterTests(unittest.TestCase):
    sp = RuleSplitter(ABBRS)

    def test_basic(self):
        self.assertEqual(self.sp.split("Ali geldi. Sonra gitti."), ["Ali geldi.", "Sonra gitti."])

    def test_abbreviation_initial_ordinal_not_split(self):
        self.assertEqual(self.sp.split("Dr. Ahmet geldi. Sonra gitti."), ["Dr. Ahmet geldi.", "Sonra gitti."])
        self.assertEqual(self.sp.split("A. Hamdi Tanpınar yazdı. Okudum."), ["A. Hamdi Tanpınar yazdı.", "Okudum."])
        self.assertEqual(self.sp.split("Kitabın 3. bölümü zor. Yine de okudum."), ["Kitabın 3. bölümü zor.", "Yine de okudum."])

    def test_quote_internal_eos_followed_by_lowercase(self):
        self.assertEqual(self.sp.split('"Neden gelmedin?" diye sordu. Cevap veremedim.'),
                         ['"Neden gelmedin?" diye sordu.', "Cevap veremedim."])
        self.assertEqual(self.sp.split('"Dikkat et!" diye bağırdı. Ama geçti.'), ['"Dikkat et!" diye bağırdı.', "Ama geçti."])

    def test_colon_semicolon_and_ellipsis(self):
        self.assertEqual(self.sp.split("Şunları alın: ekmek, süt. Yeter."), ["Şunları alın: ekmek, süt.", "Yeter."])
        self.assertEqual(self.sp.split("Bilemedim; eve döndüm. Annem bekliyordu."), ["Bilemedim; eve döndüm.", "Annem bekliyordu."])
        self.assertEqual(self.sp.split("Söylemiştim... kimse dinlemedi. Neyse."), ["Söylemiştim... kimse dinlemedi.", "Neyse."])

    def test_no_trailing_punctuation(self):
        self.assertEqual(self.sp.split("Ali geldi. Sonra gitti"), ["Ali geldi.", "Sonra gitti"])
        self.assertEqual(self.sp.split("   "), [])


class NBSplitterTests(unittest.TestCase):
    def test_features_nested(self):
        c = candidates("Dr. Ahmet geldi.")[0]
        f1, f2, f3 = (extract(c, ABBRS, lv) for lv in (1, 2, 3))
        self.assertLess(set(f1), set(f2))
        self.assertLess(set(f2), set(f3))
        self.assertEqual((f2["left_abbr"], f2["left_len"], f3["left_suf2"]), ("y", "2", "dr"))

    def test_fit_on_tiny_corpus(self):
        sents = ["Ali geldi.", "Dr. Ayşe gitti.", "Ne oldu?", "Prof. Can konuştu.", "Hava soğuktu.", "Kar yağdı."] * 3
        sp = NBSplitter(level=2, abbrevs=ABBRS).fit_sentences(sents, size=3, seed=1)
        self.assertEqual(sp.split("Dr. Ayşe geldi. Kar yağdı."), ["Dr. Ayşe geldi.", "Kar yağdı."])

    @unittest.skipUnless(UD_TRAIN.exists(), "UD verisi yok")
    def test_train_from_ud_and_roundtrip(self):
        sp = NBSplitter.train_from_conllu(UD_TRAIN, level=3)
        self.assertEqual(sp.split("Dr. Ahmet geldi. Sonra gitti."), ["Dr. Ahmet geldi.", "Sonra gitti."])
        tmp = ROOT / "results" / "_tmp_splitter.json"
        sp.save(tmp)
        try:
            sp2 = NBSplitter.load(tmp)
            self.assertEqual(sp2.split("Ali geldi. Sonra gitti."), ["Ali geldi.", "Sonra gitti."])
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
