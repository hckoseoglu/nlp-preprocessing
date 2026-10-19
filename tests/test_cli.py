"""run.py CLI duman testleri (stdlib; stemmer + stopword gerçek kaynaklarla yüklenir)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = [sys.executable, str(ROOT / "run.py")]


def run(*args: str) -> str:
    out = subprocess.run(RUN + list(args), capture_output=True, text=True, cwd=ROOT, check=True)
    return out.stdout


class CliTests(unittest.TestCase):
    def test_stem_text(self):
        self.assertEqual(run("stem", "--text", "Kitapları okuyordum.").strip(), "kitap oku .")

    def test_stopword_text_marks_removed(self):
        out = run("stopword", "--text", "Bu bir deneme cümlesidir.").strip()
        self.assertIn("[bir]", out)
        self.assertIn("deneme", out)

    def test_pipeline_json(self):
        recs = json.loads(run("pipeline", "--text", "Bu kitapları okuyordum.", "--format", "json"))
        self.assertEqual(len(recs), 1)
        self.assertIn("kitap", recs[0]["output"])
        self.assertNotIn("bu", [t.lower() for t in recs[0]["output"]])

    def test_tokenize_and_tsv(self):
        self.assertEqual(run("tokenize", "--text", "Merhaba, dünya!").split(), ["Merhaba", ",", "dünya", "!"])
        tsv = run("stem", "--text", "evlerimizden", "--format", "tsv").splitlines()
        self.assertEqual(tsv[0].split("\t"), ["sent_id", "token", "stem"])
        self.assertEqual(tsv[1].split("\t")[1:], ["evlerimizden", "ev"])

    @unittest.skipUnless((ROOT / "data" / "UD_Turkish-BOUN" / "tr_boun-ud-dev.conllu").exists(), "UD verisi yok")
    def test_split_eval_runs(self):
        out = run("stopword", "--split", "dev", "--limit", "1", "--eval", "--list", "dynamic")
        self.assertIn("[eval] stopword", out)


if __name__ == "__main__":
    unittest.main()
