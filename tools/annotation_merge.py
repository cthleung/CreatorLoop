#!/usr/bin/env python3
"""
annotation_merge.py: writes a reader agent's report into a file as inline labels.

The reader agents only report. This script is the only thing that writes their findings into the
text, so every label follows the same contract as rule_engine.py: each flag becomes
" [KIND: category, reason]" right after the phrase it quotes, nothing else on the line changes,
and the file still strips back to its original text byte for byte. It refuses to save if not.

A reader's report has one flag per line:

    L123 | exact phrase from the line | essay | states the lesson the scene already showed

A phrase that isn't on the line the agent named gets looked for 2 lines either side, and if it
still isn't found, it's reported instead of guessed at.

Usage:
    python3 tools/annotation_merge.py FILE REPORT --kind ear            # dry run
    python3 tools/annotation_merge.py FILE REPORT --kind strength --write
"""

import argparse
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.common import STRIP_RE, strip  # noqa: E402

FLAG_RE = re.compile(r"^\s*L(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*$")
KINDS = ("ear", "gloss", "blocking", "fact", "strength")


def write_file(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def clean(s):
    """Keep a label's text from breaking the label syntax."""
    return re.sub(r"\s+", " ", s.replace("]", ")").replace("[", "(").replace("|", "/")).strip()


def visible(s):
    """The line with labels and * marks removed, plus a map back to the real positions."""
    keep = [True] * len(s)
    for m in STRIP_RE.finditer(s):
        for j in range(m.start(), m.end()):
            keep[j] = False
    idx = [j for j in range(len(s)) if keep[j] and s[j] != "*"]  # agents quote words without the italics
    return "".join(s[j] for j in idx), idx


def merge(text, flags, kind):
    """Return (new text, placed, missing)."""
    lines = text.split("\n")
    placed, missing = [], []
    for ln, phrase, category, reason in flags:
        ln = int(ln)
        phrase = phrase.strip().strip('"').strip().replace("*", "")
        label = f" [{kind}: {clean(category.lower())}, {clean(reason)}]"
        hit = None
        for cand in [ln, ln - 1, ln + 1, ln - 2, ln + 2]:
            if 1 <= cand <= len(lines):
                vis, idx = visible(lines[cand - 1])
                p = vis.find(phrase)
                if p >= 0 and phrase:
                    hit = (cand, idx[p + len(phrase) - 1] + 1)
                    break
        if not hit:
            missing.append((ln, phrase))
            continue
        cand, pos = hit
        s = lines[cand - 1]
        if s[pos:].startswith(f" [{kind}:"):
            continue  # the same kind of label is already on this phrase
        lines[cand - 1] = s[:pos] + label + s[pos:]
        placed.append((cand, ln, phrase, label))
    return "\n".join(lines), placed, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("report")
    ap.add_argument("--kind", required=True, choices=KINDS)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    with open(a.file, encoding="utf-8", newline="") as f:
        text = f.read()
    with open(a.report, encoding="utf-8") as f:
        flags = [m.groups() for m in map(FLAG_RE.match, f) if m]
    new, placed, missing = merge(text, flags, a.kind)
    if strip(new) != strip(text):
        print("Refusing: the strip check failed, so nothing was written.", file=sys.stderr)
        return 3
    for cand, ln, phrase, label in placed:
        moved = "" if cand == ln else f" (the agent said L{ln})"
        print(f"L{cand}{moved}: ...{phrase[-40:]}{label}")
    for ln, phrase in missing:
        print(f"NOT FOUND near L{ln}: {phrase!r}", file=sys.stderr)
    print(f"{len(placed)} labels placed, {len(missing)} not found, {len(flags)} flags read.")
    if a.write:
        write_file(a.file, new)
        print("Written. The strip check passed.")
    else:
        print("(dry run: add --write to label the file)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
