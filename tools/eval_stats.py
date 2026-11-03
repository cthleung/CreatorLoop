#!/usr/bin/env python3
"""
eval_stats.py: repeated runs of a blind test, and whether a difference is real or noise.

A reader agent is a model, so running the same blind test twice won't give the same answers.
This takes several runs of the test (from tools/blind_eval.py) for 1 or 2 versions of a reader's
instructions, and reports:

    per run        false alarms on the must-pass items, catches on the must-fail items
    spread         how much those numbers move from run to run
    95% interval   a bootstrap confidence interval over items, so a small gold set doesn't get
                   read as more certain than it is
    flip rate      the items whose verdict changes between runs of the same brief. A line that
                   flips a lot is a line the instructions leave ambiguous
    McNemar        with 2 briefs: an exact McNemar test on each item's majority verdict, which
                   only looks at the items where the 2 briefs disagree

Usage:
    python3 tools/eval_stats.py KEY.json --a run1.md run2.md run3.md --b run1.md run2.md run3.md \\
        --name-a "my brief" --name-b "generic judge"
"""

import argparse
import json
import random
import re
import sys
from math import comb

FLAG_RE = re.compile(r"^\s*L(\d+)\s*\|")
SEED = 19
RESAMPLES = 10000


def load_key(path):
    with open(path, encoding="utf-8") as f:
        return {int(k): v for k, v in json.load(f).items()}


def flagged_lines(report):
    with open(report, encoding="utf-8") as f:
        return {int(m.group(1)) for m in map(FLAG_RE.match, f) if m}


def kind(item):
    e = item["expect"]
    return "pass" if e == "pass" else "unruled" if e == "unruled" else "fail"


def matrix(key, runs):
    """{line: [flagged in run 1, flagged in run 2, ...]} for every scored item."""
    flags = [flagged_lines(r) for r in runs]
    return {ln: [ln in f for f in flags] for ln, it in key.items() if kind(it) != "unruled"}


def rate(lines, m, run):
    return sum(m[ln][run] for ln in lines) / len(lines) if lines else 0.0


def bootstrap(lines, m, seed=SEED, n=RESAMPLES):
    """95% interval for the flag rate, resampling items (each item's rate is its mean over runs)."""
    if not lines:
        return (0.0, 0.0)
    per_item = [sum(m[ln]) / len(m[ln]) for ln in lines]
    rng = random.Random(seed)
    stats = sorted(sum(rng.choice(per_item) for _ in per_item) / len(per_item) for _ in range(n))
    return stats[int(0.025 * n)], stats[int(0.975 * n) - 1]


def flips(lines, m):
    return [ln for ln in lines if 0 < sum(m[ln]) < len(m[ln])]


def majority(m, ln):
    return sum(m[ln]) * 2 > len(m[ln])


def mcnemar(lines, ma, mb):
    """Exact 2-sided McNemar on majority verdicts. Returns (A only, B only, p)."""
    a_only = sum(1 for ln in lines if majority(ma, ln) and not majority(mb, ln))
    b_only = sum(1 for ln in lines if majority(mb, ln) and not majority(ma, ln))
    n = a_only + b_only
    if n == 0:
        return a_only, b_only, 1.0
    tail = sum(comb(n, i) for i in range(min(a_only, b_only) + 1)) / 2 ** n
    return a_only, b_only, min(1.0, 2 * tail)


def summarize(name, key, m):
    passes = [ln for ln in m if kind(key[ln]) == "pass"]
    fails = [ln for ln in m if kind(key[ln]) == "fail"]
    runs = len(next(iter(m.values()))) if m else 0
    fa = [rate(passes, m, r) for r in range(runs)]
    ca = [rate(fails, m, r) for r in range(runs)]
    lo, hi = bootstrap(passes, m)
    clo, chi = bootstrap(fails, m)
    pf, ff = flips(passes, m), flips(fails, m)
    pct = lambda x: f"{100 * x:.0f}%"
    out = [f"## {name} ({runs} runs)", "",
           f"- **False alarms** on {len(passes)} must-pass items: mean {pct(sum(fa) / runs)}, "
           f"runs ranged {pct(min(fa))} to {pct(max(fa))}, 95% interval {pct(lo)} to {pct(hi)}",
           f"- **Catches** on {len(fails)} must-fail items: mean {pct(sum(ca) / runs)}, "
           f"runs ranged {pct(min(ca))} to {pct(max(ca))}, 95% interval {pct(clo)} to {pct(chi)}",
           f"- **Flip rate:** {len(pf)} of {len(passes)} pass items and {len(ff)} of {len(fails)} fail items "
           f"changed verdict between runs"]
    if pf or ff:
        out.append("- Flipped: " + ", ".join(key[ln]["id"] for ln in sorted(pf + ff, key=lambda l: key[l]["id"])))
    return out, passes, fails


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("key")
    ap.add_argument("--a", nargs="+", required=True, help="reports from brief A")
    ap.add_argument("--b", nargs="+", help="reports from brief B")
    ap.add_argument("--name-a", default="brief A")
    ap.add_argument("--name-b", default="brief B")
    a = ap.parse_args(argv)
    key = load_key(a.key)
    ma = matrix(key, a.a)
    out = ["# Repeated-run eval", ""]
    sec, passes, fails = summarize(a.name_a, key, ma)
    out += sec
    if a.b:
        mb = matrix(key, a.b)
        sec, _, _ = summarize(a.name_b, key, mb)
        out += [""] + sec
        out += ["", f"## {a.name_a} against {a.name_b} (McNemar, exact, on each item's majority verdict)", ""]
        for label, lines in (("must-pass items (flagging is a false alarm)", passes), ("must-fail items (flagging is a catch)", fails)):
            x, y, p = mcnemar(lines, ma, mb)
            out.append(f"- **{label}:** flagged only by {a.name_a}: {x}, only by {a.name_b}: {y}, p = {p:.3g}")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
