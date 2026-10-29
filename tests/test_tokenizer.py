"""Tokenizer tests: candidate point corpus, gold conventions, rule-based and LR tokenizers.

The LR tests need scikit-learn (requirements.txt); everything else is stdlib.
"""
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from io_conllu import Sentence, Token, Word, read_conllu  # noqa: E402
from tokenization import RuleTokenizer, chunk_candidates, gold_chunks, gold_tokens, sentence_candidates  # noqa: E402
from tokenization.corpus import corpus_stats, load_split  # noqa: E402
from tokenization.features import extract  # noqa: E402
from tokenization.hard_cases import hard_case_kinds  # noqa: E402
from tokenization.metrics import evaluate, token_spans  # noqa: E402
from tokenization.mwe import Entry, MWEMerger, gold_mwes, load_lexicon  # noqa: E402
from tokenization.special import TEST_VOCAB, evaluate_entities, with_entity, write_conllu  # noqa: E402


def sentence(*tokens: tuple[str, bool]) -> Sentence:
    """A small UD sentence from (form, is there a space after it) pairs."""
    toks = [Token(form=f, space_after=sp) for f, sp in tokens]
    return Sentence(sent_id="t", text="", tokens=toks)


class CorpusTests(unittest.TestCase):
    def test_apostrophe_word_is_not_split(self):
        cands = chunk_candidates("Ankara'ya", bounds=set())
        self.assertEqual([c.pos for c in cands], [6, 7])          # Ankara|'  and  '|ya
        self.assertFalse(any(c.label for c in cands))

    def test_comma_is_split(self):
        s = sentence(("gittim", False), (",", True))
        self.assertEqual(gold_chunks(s), [("gittim,", {6})])
        [cand] = sentence_candidates(s)
        self.assertTrue(cand.label)
        self.assertEqual((cand.left, cand.right), ("m", ","))

    def test_letters_inside_word_are_not_candidates(self):
        self.assertEqual(chunk_candidates("kitaplar"), [])

    def test_raw_text_has_no_labels(self):
        self.assertTrue(all(c.label is None for c in chunk_candidates("19.30'da.")))

    def test_counts_match_progress_report(self):
        stats = corpus_stats(load_split("train"), convention="ud")
        self.assertEqual((stats["candidates"], stats["splits"]), (22_713, 16_701))


class ConventionTests(unittest.TestCase):
    def test_abbreviation_and_ordinal_keep_their_period(self):
        s = sentence(("Dr", False), (".", True), ("Ahmet", True), ("3", False), (".", True),
                     ("kez", True), ("geldi", False), (".", True))
        self.assertEqual([f for f, _ in gold_tokens(s)], ["Dr.", "Ahmet", "3.", "kez", "geldi", "."])
        self.assertEqual([f for f, _ in gold_tokens(s, "ud")], ["Dr", ".", "Ahmet", "3", ".", "kez", "geldi", "."])

    def test_sentence_final_period_stays_split(self):
        s = sentence(("Yıl", True), ("1923", False), (".", True))
        self.assertEqual([f for f, _ in gold_tokens(s)], ["Yıl", "1923", "."])


class RuleTokenizerTests(unittest.TestCase):
    def setUp(self):
        self.tok = RuleTokenizer().tokenize

    def test_examples(self):
        cases = {
            "Dr. Ahmet 3. kez geldi.": ["Dr.", "Ahmet", "3.", "kez", "geldi", "."],
            "Yıl 1923.": ["Yıl", "1923", "."],
            "1.": ["1."],
            "Ankara'ya 19.30'da gittim, %25'lik indirim.": ["Ankara'ya", "19.30'da", "gittim", ",", "%25'lik", "indirim", "."],
            "G.Saray ve T.C. sınırları": ["G.Saray", "ve", "T.C.", "sınırları"],
            'Bitti." dedi.': ["Bitti", '."', "dedi", "."],
            "Gel!.. Hadi...": ["Gel", "!", "..", "Hadi", "..."],
            "''Merhaba'' dedi": ["''", "Merhaba", "''", "dedi"],
        }
        for text, tokens in cases.items():
            self.assertEqual(self.tok(text), tokens, text)

    def test_special_entities(self):
        self.assertEqual(self.tok("Site https://boun.edu.tr/a, mail: ecem@gmail.com #nlp @hikmet vodka.com'da"),
                         ["Site", "https://boun.edu.tr/a", ",", "mail", ":", "ecem@gmail.com", "#nlp", "@hikmet",
                          "vodka.com", "'da"])

    def test_beats_regex_baseline_on_dev(self):
        sentences = load_split("dev")
        self.assertGreater(evaluate(self.tok, sentences).f1, 0.995)


class FeatureTests(unittest.TestCase):
    def test_feature_sets_are_cumulative(self):
        [cand] = chunk_candidates("gittim.", sentence_continues=False)
        f1, f2, f3 = (set(extract(cand, level)) for level in (1, 2, 3))
        self.assertTrue(f1 < f2 <= f3)
        self.assertIn("L=m", f1)
        self.assertIn("L3=tim", f2)

    def test_set3_knows_abbreviations_and_entities(self):
        [dr] = chunk_candidates("Dr.")
        self.assertIn("left_is_abbreviation", extract(dr))
        inside = [c for c in chunk_candidates("www.boun.edu.tr,") if c.right == "."]
        self.assertTrue(all("inside_entity" in extract(c) for c in inside))


class SpecialEntityTests(unittest.TestCase):
    def test_entity_is_one_gold_token(self):
        rng = random.Random(1)
        for s in load_split("dev")[:50]:
            new = with_entity(s, rng)
            forms = [f for f, _ in gold_tokens(new)]
            self.assertIsNotNone(token_spans(new.text, forms), new.text)   # gold fits the text
            self.assertTrue(any(f[0] in "#@" or "@" in f or "." in f[1:] for f in forms))

    def test_saved_test_set_reads_back(self):
        rng = random.Random(1)
        sentences = [with_entity(s, rng, TEST_VOCAB) for s in load_split("dev")[:30]]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "special.conllu"
            write_conllu(sentences, path)
            back = read_conllu(path)
        self.assertEqual([s.text for s in back], [s.text for s in sentences])
        self.assertEqual([gold_tokens(s) for s in back], [gold_tokens(s) for s in sentences])
        kept = evaluate_entities(RuleTokenizer().tokenize, back)
        self.assertEqual(sum(n for n, _ in kept.values()), 30)            # every entity is kept in one piece


class HardCaseTests(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(hard_case_kinds("Ankara'ya"), ["apostrophe"])
        self.assertEqual(hard_case_kinds("19.30'da"), ["apostrophe", "number"])
        self.assertEqual(hard_case_kinds("Dr."), ["period"])
        self.assertEqual(hard_case_kinds('gittim."', sentence_continues=False), ["punctuation"])
        self.assertEqual(hard_case_kinds("geldi.", sentence_continues=False), [])
        self.assertEqual(hard_case_kinds("kitap"), [])


class MWETests(unittest.TestCase):
    def test_gold_mwe_from_ud_relations(self):
        words = [Word(1, "Yavaş", "yavaş", "ADV", head=3, deprel="advmod"),
                 Word(2, "yavaş", "yavaş", "ADV", head=1, deprel="compound:redup"),
                 Word(3, "yürüdü", "yürü", "VERB", head=0, deprel="root")]
        s = Sentence(sent_id="t", text="Yavaş yavaş yürüdü", words=words,
                     tokens=[Token(form=w.form, words=[w]) for w in words])
        self.assertEqual(gold_mwes(s), [(0, 2, "redup")])

    def test_merge(self):
        merger = MWEMerger([Entry("fixed", ("ya", "da")), Entry("lvc", ("kabul", "et"))])
        self.assertEqual(merger.merge(["Ya", "da", "kabul", "ediyor", "tek", "tek", "."]),
                         ["Ya da", "kabul ediyor", "tek tek", "."])
        self.assertEqual(merger.merge(["kabul", "gördü"]), ["kabul", "gördü"])     # not a light verb

    def test_lexicon_file(self):
        entries = load_lexicon()
        for entry in (Entry("fixed", ("ya", "da")), Entry("redup", ("yavaş", "yavaş")), Entry("lvc", ("kabul", "et"))):
            self.assertIn(entry, entries)


class LRTokenizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tokenization.ml import LRTokenizer       # needs scikit-learn
        cls.tok = LRTokenizer.train(load_split("train")[:3000], level=3).tokenize

    def test_examples(self):
        cases = {
            "Dr. Ahmet 3. kez geldi.": ["Dr.", "Ahmet", "3.", "kez", "geldi", "."],
            "Ankara'ya gittim, çok güzeldi!": ["Ankara'ya", "gittim", ",", "çok", "güzeldi", "!"],
            "ecem@boun.edu.tr, #nlp ve https://boun.edu.tr/a adresi.":
                ["ecem@boun.edu.tr", ",", "#nlp", "ve", "https://boun.edu.tr/a", "adresi", "."],
        }
        for text, tokens in cases.items():
            self.assertEqual(self.tok(text), tokens, text)


if __name__ == "__main__":
    unittest.main()
