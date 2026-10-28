"""Kendi Naïve Bayes'imizin birim testleri (stdlib)."""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ml import NaiveBayes  # noqa: E402

X = [
    {"punct": ".", "cap": "y"}, {"punct": ".", "cap": "y"}, {"punct": "?", "cap": "y"},
    {"punct": ".", "cap": "n"}, {"punct": ".", "cap": "n"}, {"punct": "?", "cap": "n"},
]
Y = ["S", "S", "S", "N", "N", "N"]


class NaiveBayesTests(unittest.TestCase):
    def test_counts_and_prior(self):
        nb = NaiveBayes().fit(X, Y)
        self.assertEqual(nb.classes, ["N", "S"])
        self.assertEqual(nb.class_count["S"], 3)
        self.assertEqual(nb.counts["S"]["cap"]["y"], 3)

    def test_laplace_matches_hand_computation(self):
        nb = NaiveBayes(alpha=1.0).fit(X, Y)
        # P(cap=y | S) = (3 + 1) / (3 + 1 * (|{y,n}| + 1)) = 4/6
        self.assertAlmostEqual(nb._log_likelihood("S", "cap", "y"), math.log(4 / 6))
        # görülmemiş değer sıfırlanmaz: (0 + 1) / 6
        self.assertAlmostEqual(nb._log_likelihood("S", "cap", "zzz"), math.log(1 / 6))

    def test_predict_and_proba(self):
        nb = NaiveBayes().fit(X, Y)
        self.assertEqual(nb.predict({"punct": ".", "cap": "y"}), "S")
        self.assertEqual(nb.predict({"punct": "?", "cap": "n"}), "N")
        p = nb.predict_proba({"punct": ".", "cap": "y"})
        self.assertAlmostEqual(sum(p.values()), 1.0)
        self.assertGreater(p["S"], 0.5)

    def test_unknown_feature_is_ignored(self):
        nb = NaiveBayes().fit(X, Y)
        self.assertEqual(nb.predict({"punct": ".", "cap": "y", "yeni": "x"}), "S")

    def test_json_roundtrip(self):
        nb = NaiveBayes(alpha=0.5).fit(X, Y)
        nb2 = NaiveBayes.from_dict(json.loads(json.dumps(nb.to_dict())))
        x = {"punct": "?", "cap": "y"}
        self.assertEqual(nb.log_scores(x), nb2.log_scores(x))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            NaiveBayes().fit([], [])


if __name__ == "__main__":
    unittest.main()
