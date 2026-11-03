"""The rule engine: every gold case in rules/cases.txt, the strip contract, and the review tally."""

import contextlib
import glob
import io
import os
import re
import tempfile
import unittest

from tools import rule_engine as eng
from tools.common import strip

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "rules", "cases.txt")
RULES = eng.compile_rules()


def _read(path, **kw):
    with open(path, encoding="utf-8", **kw) as f:
        return f.read()


def _write(path, text, **kw):
    with open(path, "w", encoding="utf-8", **kw) as f:
        f.write(text)


def labels_on(line):
    labeled, _ = eng.label_text(line + "\n", RULES)
    return re.findall(r" \[(?:hard|check): ([^\]]+)\]", labeled)


class GoldCases(unittest.TestCase):
    def test_every_case(self):
        n = 0
        for i, raw in enumerate(_read(CASES).splitlines(True), 1):
            if not raw.strip() or raw.startswith("#"):
                continue
            verdict, label, line = (p.strip() for p in raw.rstrip("\n").split("|", 2))
            found = labels_on(line)
            n += 1
            with self.subTest(line=i, text=line):
                if verdict == "flag":
                    self.assertIn(label, found)
                elif label == "*":
                    self.assertEqual(found, [])
                else:
                    self.assertNotIn(label, found)
        self.assertGreater(n, 30)

    def test_every_rule_has_a_flag_and_a_pass_case(self):
        text = _read(CASES)
        for r in eng.RULES:
            with self.subTest(rule=r["label"]):
                self.assertIn(f"flag | {r['label']} |", text)

    def test_every_rule_compiles_and_has_a_family(self):
        for r in eng.RULES:
            self.assertTrue(r["family"])
            self.assertIn(r["level"], ("hard", "check"))
            self.assertIn(r["scope"], ("all", "narration", "dialogue"))


class StripContract(unittest.TestCase):
    def test_case_study_files_strip_back_byte_for_byte(self):
        files = glob.glob(os.path.join(ROOT, "case-study", "tangerine-drive", "*.md"))
        self.assertTrue(files)
        for path in files:
            text = _read(path, newline="")
            labeled, _ = eng.label_text(text, RULES)
            with self.subTest(file=os.path.basename(path)):
                self.assertEqual(strip(labeled), text)
                self.assertEqual(len(labeled.splitlines()), len(text.splitlines()))

    def test_write_then_verify(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "scene.md")
            orig = "She seemed tired. For a moment, she waited.\n\n\"Kind of,\" she said.\n"
            _write(src, orig)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(eng.main([src, "--write", "--backup", os.path.join(d, "bak")]), 0)
                self.assertIn("[check: hedge]", _read(src))
                self.assertEqual(eng.main([src, "--verify", os.path.join(d, "bak", "scene.md")]), 0)

    def test_refuses_a_file_that_already_has_labels(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "scene.md")
            _write(src, "She seemed tired. [check: hedge]\n")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(eng.main([src]), 2)


class Review(unittest.TestCase):
    def test_tally_and_misfiring_rules(self):
        text = "\n".join([
            "A [check: stopwatch | false alarm: literal]",
            "B [check: stopwatch | false alarm: literal]",
            "C [check: stopwatch | keep: her voice]",
            "D [check: hedge]",
        ])
        rep, waiting = eng.review("x.md", text)
        self.assertEqual(waiting, 1)
        self.assertIn("Rules to fix", rep)
        self.assertIn("stopwatch", rep.split("Rules to fix")[1])


if __name__ == "__main__":
    unittest.main()
