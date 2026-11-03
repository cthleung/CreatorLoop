"""The merge, the blind test, the preservation diff and the number picker."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from tools import annotation_merge, blind_eval, preservation_diff
from tools.common import strip

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICK = os.path.join(ROOT, "tools", "pick_number.py")


def _read(path, **kw):
    with open(path, encoding="utf-8", **kw) as f:
        return f.read()


def _write(path, text, **kw):
    with open(path, "w", encoding="utf-8", **kw) as f:
        f.write(text)


class Merge(unittest.TestCase):
    TEXT = "Line one.\nThe defrost had eaten her potato farm in from the edges.\nLine three.\n"

    def test_places_label_after_phrase_and_strips_back(self):
        new, placed, missing = annotation_merge.merge(self.TEXT, [("2", "eaten her potato farm", "image", "the joke comes back")], "strength")
        self.assertEqual(missing, [])
        self.assertIn("eaten her potato farm [strength: image, the joke comes back] in from", new)
        self.assertEqual(strip(new), self.TEXT)

    def test_looks_a_line_either_side_and_reports_misses(self):
        new, placed, missing = annotation_merge.merge(self.TEXT, [("3", "potato farm", "lift", "x"), ("1", "not in the text", "x", "y")], "ear")
        self.assertEqual(placed[0][0], 2)
        self.assertEqual(len(missing), 1)

    def test_label_text_cannot_break_the_syntax(self):
        new, _, _ = annotation_merge.merge(self.TEXT, [("1", "Line one", "essay", "reads like [a] thesis | yes")], "ear")
        self.assertEqual(strip(new), self.TEXT)


class BlindEval(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.gold = os.path.join(self.d, "gold.md")
        _write(self.gold, "\n".join([
            "- P01 | pass | narrator | spoken | The trees came out lumpy.",
            "- P02 | pass | narrator | spoken | Against the black, the window turned into a mirror.",
            "- F01 | essay | narrator | spoken | It was a moment that taught her the true meaning of home.",
            "- U01 | unruled | narrator | spoken | Her shoulders came down from around her ears.",
        ]) + "\n")
        self.blind, n = blind_eval.build(self.gold, os.path.join(self.d, "t"))
        self.assertEqual(n, 4)
        self.key = {int(k): v for k, v in json.loads(_read(os.path.join(self.d, "t", "key.json"))).items()}

    def line_of(self, iid):
        return next(ln for ln, it in self.key.items() if it["id"] == iid)

    def report(self, *flags):
        path = os.path.join(self.d, "report.md")
        _write(path, "\n".join(flags) + "\n")
        return path

    def test_blind_file_has_no_answers(self):
        text = _read(self.blind)
        for word in ("pass", "unruled", "P01", "F01"):
            self.assertNotIn(word, text)

    def test_same_order_every_build(self):
        again, _ = blind_eval.build(self.gold, os.path.join(self.d, "t2"))
        self.assertEqual(_read(self.blind), _read(again))

    def test_perfect_run(self):
        rep, fa = blind_eval.score(self.blind, self.report(f"L{self.line_of('F01')} | true meaning of home | essay | states the lesson"))
        self.assertEqual(fa, 0)
        self.assertIn("**Caught:** 1 of 1", rep)

    def test_false_alarm_and_wrong_register(self):
        rep, fa = blind_eval.score(self.blind, self.report(
            f"L{self.line_of('P02')} | turned into a mirror | poem | too pretty",
            f"L{self.line_of('F01')} | true meaning of home | press release | sounds like a brochure"))
        self.assertEqual(fa, 1)
        self.assertIn("under a different register", rep)

    def test_held_out_ignores_lines_quoted_in_the_brief(self):
        rep, _ = blind_eval.score(self.blind, self.report(), brief_text="Against the black, the window turned into a mirror.")
        self.assertIn("**Held-out items:** 2", rep)


class PreservationDiff(unittest.TestCase):
    def test_reports_lost_dialogue_and_words(self):
        orig = '"Is that a house?"\n"It\'s a potato farm," she said, holding the dried squid.'
        new = '"Is that a house?"\nShe shrugged.'
        d = preservation_diff.diff(orig, new)
        self.assertIn(("Is that a house?", "kept"), d["dialogue"])
        self.assertTrue(any(q.startswith("It's a potato farm") and s == "gone" for q, s in d["dialogue"]))
        self.assertIn("squid", d["words"])
        self.assertIn("dried squid", d["phrases"])


class Picker(unittest.TestCase):
    def pick(self, *args):
        r = subprocess.run([sys.executable, "-I", PICK, *args], capture_output=True, text=True)
        return r.returncode, r.stdout.strip().splitlines(), r.stderr

    def test_range_and_step(self):
        for _ in range(20):
            code, out, _ = self.pick("10", "60", "--step", "5")
            self.assertEqual(code, 0)
            self.assertTrue(10 <= int(out[0]) <= 60 and int(out[0]) % 5 == 0, out)

    def test_clock_and_words(self):
        _, out, _ = self.pick("9:00am", "10:30am")
        self.assertRegex(out[0], r"^(9|10):\d\d AM$")
        _, out, _ = self.pick("21", "21", "--words")
        self.assertEqual(out, ["21  (twenty-one)"])

    def test_log_only_when_asked(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "log.md")
            self.pick("1", "9", "--for", "a test")
            self.assertFalse(os.path.exists(log))
            self.pick("1", "9", "--for", "a test", "--log", log)
            self.assertIn("a test", _read(log))


if __name__ == "__main__":
    unittest.main()


class EvalStats(unittest.TestCase):
    def setUp(self):
        from tools import eval_stats
        self.es = eval_stats
        self.d = tempfile.mkdtemp()
        key = {"5": {"id": "P01", "expect": "pass"}, "6": {"id": "P02", "expect": "pass"},
               "7": {"id": "F01", "expect": "essay"}, "8": {"id": "F02", "expect": "poem"},
               "9": {"id": "U01", "expect": "unruled"}}
        self.key = os.path.join(self.d, "key.json")
        _write(self.key, json.dumps(key))

    def run_file(self, name, lines):
        p = os.path.join(self.d, name)
        _write(p, "".join(f"L{n} | x | x | x\n" for n in lines))
        return p

    def test_flip_rate_and_rates(self):
        key = self.es.load_key(self.key)
        m = self.es.matrix(key, [self.run_file("a1", [7, 8]), self.run_file("a2", [7, 5])])
        self.assertNotIn(9, m)  # unruled items aren't scored
        self.assertEqual(self.es.flips([5, 6], m), [5])
        self.assertEqual(self.es.rate([7, 8], m, 0), 1.0)
        self.assertEqual(self.es.rate([7, 8], m, 1), 0.5)

    def test_mcnemar_exact(self):
        ma = {1: [True], 2: [True], 3: [True], 4: [False]}
        mb = {1: [False], 2: [False], 3: [False], 4: [False]}
        a_only, b_only, p = self.es.mcnemar([1, 2, 3, 4], ma, mb)
        self.assertEqual((a_only, b_only), (3, 0))
        self.assertAlmostEqual(p, 0.25)  # 3 to 0 can never reach p < 0.05
        self.assertEqual(self.es.mcnemar([4], ma, mb)[2], 1.0)

    def test_bootstrap_is_repeatable_and_bounded(self):
        m = {1: [True, False], 2: [False, False], 3: [True, True]}
        lo, hi = self.es.bootstrap([1, 2, 3], m)
        self.assertEqual((lo, hi), self.es.bootstrap([1, 2, 3], m))
        self.assertTrue(0 <= lo <= 0.5 <= hi <= 1)
