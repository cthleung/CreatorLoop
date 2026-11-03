#!/usr/bin/env python3
"""
preservation_diff.py: what a new version dropped from the original it replaces.

Fixing one problem in a scene can quietly lose something good: a line of dialogue, a specific
detail, a joke. This lists, from the original:

    dialogue   every quoted line, and whether the new version kept it, reworded it or lost it
    phrases    2-word content phrases ("tangerine hat," "dried squid") with a word the new version lost
    words      content words that appear nowhere in the new version, most specific first

It never decides anything. A cut can be on purpose, but then it should be on a "cut on purpose"
list somewhere. Anything missing and not on that list is a candidate to bring back.

Usage:
    python3 tools/preservation_diff.py ORIGINAL NEW
    python3 tools/preservation_diff.py ORIGINAL NEW --lines 20-180 --new-lines 10-260
"""

import argparse
import difflib
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.common import STOP, strip, tokens  # noqa: E402

QUOTE_RE = re.compile(r"\"([^\"]+)\"|“([^”]+)”")
GENERIC = set("""said says asked looked look looking turned back down up felt feel made make went going came come took
take gave give saw see face hand hands eyes head thing things way time moment something someone nothing everything
anything little bit pretty really right left""".split())


def read(path, rng=None):
    with open(path, encoding="utf-8") as f:
        raw = f.read().split("\n")
    a, b = (1, len(raw)) if not rng else (int(x) for x in rng.split("-"))
    return "\n".join(re.sub(r"^\s*>\s?", "", strip(line)) for line in raw[a - 1:b])


def quotes(text):
    return [next(g for g in m.groups() if g).strip() for m in QUOTE_RE.finditer(text)]


def content(w):
    return w not in STOP and w not in GENERIC and len(w) > 3


def diff(orig, new):
    """Return dict(dialogue=[(line, state)], phrases=[...], words=[...])."""
    new_words, new_quotes = set(tokens(new)), quotes(new)
    dialogue = []
    for q in quotes(orig):
        if q in new:
            dialogue.append((q, "kept"))
            continue
        best = max(new_quotes, key=lambda d: difflib.SequenceMatcher(None, q.lower(), d.lower()).ratio(), default="")
        r = difflib.SequenceMatcher(None, q.lower(), best.lower()).ratio() if best else 0
        dialogue.append((q, f"reworded ({int(r * 100)}%): \"{best[:70]}\"" if r >= 0.55 else "gone"))
    phrases, seen = [], set()
    for clause in re.split(r"[.,;:!?()\-\n\"“”]+", orig):
        w = tokens(clause)
        for x, y in zip(w, w[1:]):
            if (x, y) in seen or not (content(x) and content(y)):
                continue
            seen.add((x, y))
            if x not in new_words or y not in new_words:
                phrases.append(f"{x} {y}")
    words = sorted({w for w in tokens(orig) if content(w) and w not in new_words}, key=lambda w: (-len(w), w))
    return dict(dialogue=dialogue, phrases=phrases, words=words)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original")
    ap.add_argument("new")
    ap.add_argument("--lines", help="range in the original, e.g. 20-180")
    ap.add_argument("--new-lines", help="range in the new version")
    a = ap.parse_args(argv)
    d = diff(read(a.original, a.lines), read(a.new, a.new_lines))
    out = [f"# Preservation diff: {os.path.basename(a.original)} against {os.path.basename(a.new)}", "", "## Dialogue", ""]
    out += [f"- \"{q[:90]}\" - {'**gone**' if s == 'gone' else s}" for q, s in d["dialogue"]] or ["none"]
    out += ["", f"## Phrases with a word the new version lost ({len(d['phrases'])})", "", ", ".join(d["phrases"]) or "none"]
    out += ["", f"## Words the new version lost ({len(d['words'])})", "", ", ".join(d["words"]) or "none"]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
