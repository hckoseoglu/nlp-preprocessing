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

    def test_normalize_text(self):
        out = run("normalize", "--text", "Gunes dogdu, cooook guzel!").strip()
        self.assertEqual(out, "güneş doğdu , çok güzel !")

    def test_raw_text_passthrough_and_no_copula_table(self):
        out = run("stem", "--text", "Dur orada! @ali_veli #nlp https://x.com/a ise burada").split()
        self.assertEqual(out[0], "dur")                      # ham metinde ek-fiil tablosu kapalı: dur → i olmaz
        for keep in ("@ali_veli", "#nlp", "https://x.com/a", "ise"):
            self.assertIn(keep, out)
        self.assertEqual(run("tokenize", "--text", "olur zaten ...... bilginize ?!").split(), ["olur", "zaten", "......", "bilginize", "?!"])

    def test_split_text(self):
        out = run("split", "--text", 'Dr. Ahmet geldi. "Neden gelmedin?" diye sordu. Cevap veremedim.', "--method", "rule")
        self.assertEqual(out.splitlines(), ["Dr. Ahmet geldi.", '"Neden gelmedin?" diye sordu.', "Cevap veremedim."])
        recs = json.loads(run("split", "--text", "Ali geldi. Sonra gitti.", "--format", "json"))
        self.assertEqual(recs[0]["output"], ["Ali geldi.", "Sonra gitti."])

    def test_doc_mode_pipeline(self):
        doc = ROOT / "results" / "_tmp_doc.txt"
        doc.write_text('Dr. Ahmet toplantıya geç kaldı. "Neden gelmedin?" diye sordu. Cevap veremedim.', encoding="utf-8")
        try:
            lines = run("pipeline", "--doc", str(doc), "--method", "rule").splitlines()
        finally:
            doc.unlink(missing_ok=True)
        self.assertEqual(len(lines), 3)                                   # üç cümle, satır başına bir cümle
        self.assertTrue(lines[0].startswith("s1\t") and lines[2].startswith("s3\t"))
        self.assertIn("kal", lines[0].split())
        self.assertIn("cevap", lines[2].split())

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
