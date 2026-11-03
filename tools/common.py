"""Shared pieces for the CreatorLoop tools: the label pattern and a word tokenizer."""

import re

# A label is " [kind: ...]" right after a phrase, where kind is a lowercase word: [check: hedge],
# [ear: essay, states the lesson]. Ordinary brackets ("[...]", "[a later chapter]") aren't labels.
# Stripping every label gives back the original text byte for byte, which every tool checks.
STRIP_RE = re.compile(r" \[[a-z][a-z-]*: [^\]]*\]")

WORD_RE = re.compile(r"[a-z][a-z']*")

STOP = set("""a an the and or but so if then than that this these those it its it's i me my we our you your he him his
she her they them their to of in on at by for with from up down out over into onto off as is was were be been being am are
do did does done have has had not no just all any some one ones there here what which who whom whose when where why how too
very can could would should will shall may might must like get got gets getting let lets s t d ll ve re m don didn doesn isn
wasn weren couldn wouldn shouldn ain more most much many even still again back only also own same other another each every
""".split())


def strip(text):
    """Remove every label."""
    return STRIP_RE.sub("", text)


def tokens(text):
    return [w.strip("'") for w in WORD_RE.findall(text.lower()) if w.strip("'")]
