#!/usr/bin/env python3
"""
rule_engine.py: labels prose against a rule pack, inline, without ever damaging it.

Each hit becomes a short label right after the phrase it's about:

    She seemed tired. [check: hedge]

    hard   the rule is broken almost every time it fires
    check  maybe a tic, maybe the character's voice; a person decides

The contract: removing every " [...]" gives back the original text byte for byte, and line
numbers never move. --write refuses to save if that round trip fails. The engine only labels;
it never fixes anything, because how to fix a line is the writer's call.

After a person reviews the labels, each one gets a verdict after a pipe, inside the brackets:

    [check: hedge | keep: her own voice]      [hard: em dash | tic: pasted from a draft]
    [check: stopwatch | false alarm: literal]  [check: invented count | ask: real count?]

--review tallies those verdicts and lists any rule that misfires so often it needs fixing.

This is a smaller rewrite of the scanner I use on my novel. The rules live in rules/default.py.

Usage:
    python3 tools/rule_engine.py FILE                     # dry run: print the report
    python3 tools/rule_engine.py FILE --lines 20-180      # only scan these lines
    python3 tools/rule_engine.py FILE --write --backup DIR
    python3 tools/rule_engine.py FILE --strip             # print the text with every label removed
    python3 tools/rule_engine.py FILE --verify ORIGINAL   # does FILE strip back to ORIGINAL?
    python3 tools/rule_engine.py FILE --review            # tally the verdicts
"""

import argparse
import os
import re
import shutil
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rules.default import FAMILY_OF, RULES  # noqa: E402
from tools.common import STRIP_RE, strip  # noqa: E402

REVIEW_RE = re.compile(r" \[(hard|check): ([^\]|]+?)(?: \| ([^\]:]+?)(?::\s*([^\]]*))?)?\]")
VERDICTS = ("keep", "tic", "false alarm", "ask")
ITALIC_RE = re.compile(r"(?<![*\w])\*(?![*\s])(.+?)(?<![\s*])\*(?![*\w])")
NOSCAN_RE = re.compile(r"https?://\S+|<[^>]+>|`[^`]*`|\]\([^)]*\)")
DIVIDER_RE = re.compile(r"^\s*(?:\*\s*){3,}$|^\s*-{3,}\s*$")


def compile_rules(rules=RULES):
    out = [dict(r, order=i, rx=re.compile(r["regex"], re.I)) for i, r in enumerate(rules)]
    out.sort(key=lambda r: (r["level"] != "hard", r["order"]))  # hard rules claim their spans first
    return out


def skip_line(s):
    t = s.strip()
    return (not t or t.startswith(("#", "|", ">", "<!--", "```")) or bool(DIVIDER_RE.match(t))
            or (t.startswith("**") and t.endswith("**")))


def zones(s):
    """One character per position: n = narration, q = dialogue, i = italics, x = don't scan."""
    z, inq = ["n"] * len(s), False
    for i, ch in enumerate(s):
        if ch == '"':
            z[i] = "q"
            inq = not inq
        elif ch == "“":
            inq, z[i] = True, "q"
        elif ch == "”":
            inq, z[i] = False, "q"
        elif inq:
            z[i] = "q"
    for m in ITALIC_RE.finditer(s):
        for i in range(m.start(), m.end()):
            if z[i] == "n":
                z[i] = "i"
    for m in NOSCAN_RE.finditer(s):
        for i in range(m.start(), m.end()):
            z[i] = "x"
    return z


def in_scope(rule, z, at):
    zone = z[at] if at < len(z) else "n"
    if zone == "x":
        return False
    return rule["scope"] == "all" or (rule["scope"] == "narration" and zone == "n") or (rule["scope"] == "dialogue" and zone == "q")


def scan_line(s, rules):
    """Return a list of (position, level, label) hits for one line."""
    z, taken, hits = zones(s), [], []
    for r in rules:
        for m in r["rx"].finditer(s):
            a, b = m.start(), m.end()
            if a == b or not in_scope(r, z, a):
                continue
            if r["level"] == "check" and any(a < tb and ta < b for ta, tb in taken):
                continue  # a check never doubles up on a span a hard rule already labeled
            taken.append((a, b))
            pos = b
            while 0 < pos < len(s) and s[pos - 1].isalnum() and s[pos].isalnum():
                pos += 1  # never split a word
            while pos > a and s[pos - 1] == " ":
                pos -= 1
            hits.append((pos, r["level"], r["label"]))
    return hits


def label_text(text, rules, first=1, last=None):
    """Return (labeled text, findings). Findings are (line number, level, label)."""
    out, findings = [], []
    for n, raw in enumerate(text.splitlines(keepends=True), 1):
        body = raw.rstrip("\r\n")
        nl = raw[len(body):]
        if n < first or (last and n > last) or skip_line(body):
            out.append(raw)
            continue
        seen = set()
        for pos, level, label in sorted(scan_line(body, rules), key=lambda h: (-h[0], h[1] != "hard")):
            if (pos, label) not in seen:
                seen.add((pos, label))
                body = body[:pos] + f" [{level}: {label}]" + body[pos:]
                findings.append((n, level, label))
        out.append(body + nl)
    return "".join(out), findings


def report(path, findings):
    total = Counter(level for _, level, _ in findings)
    fam = defaultdict(Counter)
    for _, level, label in findings:
        fam[FAMILY_OF.get(label, "other")][level] += 1
    lines = [f"# Scan: {os.path.basename(path)}", "",
             f"**{total['hard']} hard, {total['check']} check** on {len({n for n, *_ in findings})} lines.", "",
             "| Family | Hard | Check |", "|---|---|---|"]
    lines += [f"| {f} | {c['hard']} | {c['check']} |" for f, c in sorted(fam.items(), key=lambda kv: -sum(kv[1].values()))]
    lines += ["", "| Line | Level | Label |", "|---|---|---|"]
    lines += [f"| {n} | {level} | {label} |" for n, level, label in findings]
    return "\n".join(lines) + "\n"


def review(path, text):
    """Tally verdicts. Returns (report, number of labels still waiting on a verdict)."""
    by_label, waiting = defaultdict(Counter), []
    for n, line in enumerate(text.splitlines(), 1):
        for m in REVIEW_RE.finditer(line):
            verdict = (m.group(3) or "").strip()
            verdict = verdict if verdict in VERDICTS else "unreviewed"
            by_label[m.group(2).strip()][verdict] += 1
            if verdict == "unreviewed":
                waiting.append(f"L{n}: [{m.group(1)}: {m.group(2).strip()}]")
    cols = list(VERDICTS) + ["unreviewed"]
    lines = [f"# Review: {os.path.basename(path)}", "", "| Label | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    lines += [f"| {lbl} | " + " | ".join(str(c[v]) for v in cols) + " |" for lbl, c in sorted(by_label.items())]
    # a rule that keeps misfiring gets its regex fixed at the source, instead of being dismissed forever
    misfiring = [lbl for lbl, c in by_label.items()
                 if sum(c[v] for v in VERDICTS) >= 3 and c["false alarm"] * 2 >= sum(c[v] for v in VERDICTS)]
    if misfiring:
        lines += ["", "**Rules to fix** (at least 50% false alarms out of 3 or more reviewed hits): " + ", ".join(misfiring)]
    if waiting:
        lines += ["", f"**Waiting on a verdict ({len(waiting)}):**"] + [f"- {w}" for w in waiting]
    return "\n".join(lines) + "\n", len(waiting)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--lines", help="only scan this range, e.g. 20-180")
    ap.add_argument("--write", action="store_true", help="write the labels into the file")
    ap.add_argument("--backup", help="folder for a clean copy before --write")
    ap.add_argument("--strip", action="store_true")
    ap.add_argument("--verify")
    ap.add_argument("--review", action="store_true")
    a = ap.parse_args(argv)
    with open(a.file, encoding="utf-8", newline="") as f:
        text = f.read()

    if a.strip:
        sys.stdout.write(strip(text))
        return 0
    if a.verify:
        with open(a.verify, encoding="utf-8", newline="") as f:
            same = strip(text) == f.read()
        print("OK: strips back to the original byte for byte." if same else "MISMATCH: the stripped text differs from the original.")
        return 0 if same else 1
    if a.review:
        rep, waiting = review(a.file, text)
        print(rep)
        return 1 if waiting else 0

    if STRIP_RE.search(text):
        print("The file already has labels. Strip them first (--strip), so the scan starts clean.", file=sys.stderr)
        return 2
    first, last = (int(x) for x in a.lines.split("-")) if a.lines else (1, None)
    labeled, findings = label_text(text, compile_rules(), first, last)
    if strip(labeled) != text:
        print("Refusing: the labeled text doesn't strip back to the original, so nothing was written.", file=sys.stderr)
        return 3
    print(report(a.file, findings))
    if a.write:
        if a.backup:
            os.makedirs(a.backup, exist_ok=True)
            shutil.copy2(a.file, os.path.join(a.backup, os.path.basename(a.file)))
        with open(a.file, "w", encoding="utf-8", newline="") as f:
            f.write(labeled)
        print("Written. The strip check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
