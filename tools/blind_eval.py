#!/usr/bin/env python3
"""
blind_eval.py: a blind test for a reader agent, built from a gold set of lines.

    build   writes a blind test (lines shuffled with a fixed seed, answers stripped) and an
            answer key next to it
    score   grades the agent's report against the key

The gold set is a markdown file with one item per line:

    - P01 | pass | Seoyun narration | spoken | Trot was a rhythm game for grandpas, and she was full-comboing it.

    id       P (must pass), F (must fail) or U (unruled), plus a number
    expect   "pass", "unruled", or for a fail item, the register it slipped into ("essay", "poem"...)
    who      the speaker or narrator
    target   the register the scene allows there
    text     the line itself

The agent gets the blind file only, and reports flags the usual way (L<n> | phrase | register | reason).

Scoring separates:
    false alarms   pass items the agent flagged. This is the flattening risk, and it has to be 0.
    misses         fail items the agent left alone
    wrong register fail items caught, but filed under a different register (still a catch)
    unruled        not scored; the agent's verdict is listed so a person can rule on it
    held-out       items that don't appear in the agent's own instructions (--brief), so passing
                   them can't be memory

Usage:
    python3 tools/blind_eval.py build --gold evals/voice-gold.md --out DIR
    python3 tools/blind_eval.py score DIR/blind.md REPORT --brief agents/ear-reader.md
"""

import argparse
import json
import os
import random
import re
import sys

ITEM_RE = re.compile(r"^- ([PFU]\d+) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| (.+)$")
FLAG_RE = re.compile(r"^\s*L(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*)$")
SEED = 19  # fixed, so reruns get the same order and can be compared


def load_gold(path):
    items = []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        m = ITEM_RE.match(line.rstrip("\n"))
        if m:
            iid, expect, who, target, text = (g.strip() for g in m.groups())
            items.append(dict(id=iid, expect=expect, who=who, target=target, text=text))
    return items


def seen_in(brief_text, text):
    """True if any run of 6 words from the item appears in the agent's instructions."""
    norm = lambda t: re.sub(r"[^a-z ]", "", t.lower())
    b, w = norm(brief_text), norm(text).split()
    return any(" ".join(w[i:i + 6]) in b for i in range(max(1, len(w) - 5)))


def build(gold, out):
    items = load_gold(gold)
    order = items[:]
    random.Random(SEED).shuffle(order)
    os.makedirs(out, exist_ok=True)
    lines = ["# Blind test", "",
             "Each line below is one item. The braces give the target: who's speaking or narrating, and the "
             "register the scene allows there. Judge the text after the braces only, and quote phrases from it.", ""]
    key = {}
    for it in order:
        lines.append(f"{{{it['who']} | {it['target']}}} {it['text']}")
        key[len(lines)] = it
    blind = os.path.join(out, "blind.md")
    with open(blind, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out, "key.json"), "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in key.items()}, f, indent=1)
    return blind, len(order)


def score(blind, report, brief_text=""):
    """Return (markdown report, number of false alarms)."""
    with open(os.path.join(os.path.dirname(blind), "key.json"), encoding="utf-8") as f:
        key = {int(k): v for k, v in json.load(f).items()}
    flags = {}
    with open(report, encoding="utf-8") as f:
        report_lines = f.readlines()
    for line in report_lines:
        m = FLAG_RE.match(line)
        if m:
            flags.setdefault(int(m.group(1)), []).append(dict(phrase=m.group(2), register=m.group(3).lower(), reason=m.group(4)))
    fa, miss, caught, wrong, unruled = [], [], [], [], []
    for ln, it in sorted(key.items(), key=lambda kv: kv[1]["id"]):
        f = flags.get(ln, [])
        if it["expect"] == "pass":
            if f:
                fa.append((it, f))
        elif it["expect"] == "unruled":
            unruled.append((it, f))
        elif not f:
            miss.append(it)
        else:
            caught.append(it)
            if not any(it["expect"].lower() in x["register"] for x in f):
                wrong.append((it, f))
    held = [it for it in key.values() if it["expect"] != "unruled" and not seen_in(brief_text, it["text"])]
    n_pass = sum(it["expect"] == "pass" for it in key.values())
    n_fail = sum(it["expect"] not in ("pass", "unruled") for it in key.values())
    out = ["# Blind test score", "",
           f"- **False alarms:** {len(fa)} of {n_pass} pass items (must be 0)",
           f"- **Caught:** {len(caught)} of {n_fail} fail items ({len(wrong)} under a different register)",
           f"- **Missed:** {len(miss)}",
           f"- **Held-out items:** {len(held)}, with {sum(it in held for it, _ in fa)} false alarms "
           f"and {sum(it in held for it in miss)} misses"]
    if fa:
        out += ["", "## False alarms"] + [f"- {it['id']}: {it['text'][:90]} (agent: {x['register']}, {x['reason']})" for it, f in fa for x in f]
    if miss:
        out += ["", "## Missed"] + [f"- {it['id']} ({it['expect']}): {it['text'][:90]}" for it in miss]
    if wrong:
        out += ["", "## Caught under a different register"] + [f"- {it['id']}: expected {it['expect']}, agent said {', '.join(x['register'] for x in f)}" for it, f in wrong]
    if unruled:
        out += ["", "## Unruled (for a person to rule on)"]
        out += [f"- {it['id']}: {'flagged as ' + '; '.join(x['register'] for x in f) if f else 'clean'}: {it['text'][:90]}" for it, f in unruled]
    return "\n".join(out) + "\n", len(fa)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--gold", required=True)
    b.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("blind")
    s.add_argument("report")
    s.add_argument("--brief", nargs="*", default=[], help="the agent's instruction files, for the held-out count")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        blind, n = build(a.gold, a.out)
        print(f"Wrote {blind} ({n} items) and key.json. Give the agent the blind file only.")
        return 0
    parts = []
    for p in a.brief:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                parts.append(f.read())
    brief = " ".join(parts)
    text, false_alarms = score(a.blind, a.report, brief)
    print(text)
    return 1 if false_alarms else 0


if __name__ == "__main__":
    sys.exit(main())
