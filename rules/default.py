"""
The demo rule pack for tools/rule_engine.py.

These are the rules the case study scene ran into, plus a few common AI-prose tells. My own
pack is much bigger and full of rules about my novel's characters, so this is a clean sample of
how the rules are written, and not the whole thing.

Each rule is a dict:
    label   the short name that goes in the label: [hard: label] or [check: label]
    level   "hard"  = broken almost every time it fires
            "check" = maybe a tic, maybe voice; a person decides
    regex   matched case-insensitively
    scope   "all", "narration" (outside quotes and *italics*) or "dialogue" (inside quotes)
    family  the group it belongs to, for the report

Every rule has a flag line and a pass line in rules/cases.txt, and the tests run all of them.
When a ruling changes a rule, change its regex here and add a pair of cases there.
"""

NUM_47 = (r"\b(?:[0-9]*[47][0-9]*|(?:four|seven)(?:teen|ty)?(?:-\w+)?|fourth|seventh"
          r"|(?:twenty|thirty|fifty|sixty|eighty|ninety)-(?:four|seven))\b")

RULES = [
    # house rules: a couple of my absolute bans, as examples
    dict(label="em dash", level="hard", scope="all", family="house",
         regex=r"\u2014|\u2013"),
    dict(label="half (any use)", level="hard", scope="all", family="house",
         regex=r"\bhal(?:f|ves)\w*"),

    # invented numbers: a 4 or a 7 is usually the reflex. A counted number is fine, and a person says which.
    dict(label="4/7: counted or invented?", level="check", scope="all", family="numbers",
         regex=NUM_47),
    dict(label="invented count", level="check", scope="narration", family="numbers",
         regex=r"\b(?:twice|three times|a (?:few|couple of) seconds)\b"),

    # hedges in narration (in a character's own mouth they're just how people talk)
    dict(label="hedge", level="check", scope="narration", family="hedges",
         regex=r"\b(?:seemed(?: to)?|kind of|sort of|somewhat|a bit|almost smiled|nearly smiled)\b"),

    # narrated non-events: telling the reader what didn't happen
    dict(label="non-event", level="check", scope="narration", family="non-events",
         regex=r"\b(?:instead of \w+ing|without (?:taking|looking|saying|answering)\b|"
               r"didn't say anything|(?:stayed|stay) where (?:they|it|she|he) (?:was|were)|"
               r"nothing (?:she|he|they) could do|to let nobody)"),

    # delivery similes: comparisons about how a line is said
    dict(label="delivery simile", level="check", scope="narration", family="delivery",
         regex=r"\b(?:said|asked|added|replied|told \w+)\b[^.\"]{0,30}?\b(?:\w+ as \w+ing\b|as \w+ as\b|like (?:she|he|they) (?:was|were)\b)"),

    # narrator distance: perception announced instead of shown, and talk handled as text
    dict(label="filtering", level="check", scope="narration", family="narrator distance",
         regex=r"\b(?:she|he|i|they) could (?:feel|hear|see|smell)\b"),
    dict(label="cognitive shortcut", level="hard", scope="narration", family="narrator distance",
         regex=r"\b(?:clocked|registered|catalogued)\b"),
    dict(label="language about language", level="hard", scope="narration", family="narrator distance",
         regex=r"\b(?:trailed off|mid-sentence|the words (?:died|dissolved|failed)|words failed (?:her|him|them))\b"),

    # signposting: labels and timing the scene doesn't need
    dict(label="something hook", level="hard", scope="narration", family="signposting",
         regex=r"\bsomething (?:shifted|stirred|broke|passed between|moved through|unspoken|unreadable)\b"),
    dict(label="stopwatch", level="check", scope="narration", family="signposting",
         regex=r"\b(?:for a (?:moment|second|beat)|a (?:moment|second|beat) later)\b"),

    # precision emphasis: careful-sounding words that are usually filler
    dict(label="precision emphasis", level="check", scope="narration", family="precision",
         regex=r"\b(?:exactly|genuinely|every single|truly)\b"),

    # the usual AI essay words
    dict(label="AI register", level="hard", scope="all", family="AI register",
         regex=r"\b(?:delve[sd]?|tapestry|testament to|it's worth noting)\b"),
]

FAMILY_OF = {r["label"]: r["family"] for r in RULES}
