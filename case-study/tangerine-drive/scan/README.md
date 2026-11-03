# Scan output

These are the tools from `tools/` run on the case study, so you can see what their output looks like and just rerun it yourself from the repo root.

```bash
python3 tools/rule_engine.py case-study/tangerine-drive/04-draft-1.md --lines 11-9999
python3 tools/rule_engine.py case-study/tangerine-drive/07-final.md --lines 5-9999
python3 tools/preservation_diff.py case-study/tangerine-drive/04-draft-1.md case-study/tangerine-drive/07-final.md --lines 11-9999 --new-lines 5-9999
```

- [`draft-1-scan.md`](draft-1-scan.md) - draft 1 gets 1 hard label and 10 checks, including 7 narrated non-events and the word "half," which I've banned outright.
- [`final-scan.md`](final-scan.md) - the final gets 0 hard labels and 4 checks.
- [`draft-1-vs-final.md`](draft-1-vs-final.md) - every line of draft 1's dialogue, and whether the final kept it, reworded it or dropped it, plus the words and phrases that didn't survive.

Oh, and one thing I'd rather be upfront about. The demo rule pack was written after the fact, from the rulings this scene produced, so naturally it catches draft 1 - I turned draft 1's non-events into the patterns. That makes these files a demo of how the mechanism works, and they don't really measure anything. The measuring side is in [evaluation.md](../../../docs/evaluation.md).

The final's 4 checks are a pretty good example of why the `check` level exists, since every one of them is fine once a person actually looks at it.

| Line | Label | Verdict |
|---|---|---|
| 33 | 4/7: counted or invented? | `false alarm: a real date` (the song's from 1972) |
| 107 | hedge | `false alarm: literal` ("a bit of peel" is an actual bit of peel) |
| 133 | 4/7: counted or invented? | `false alarm: a real count` (223,700 won is the real bill) |
| 205 | precision emphasis | `keep: her voice` ("every single time" is Seoyun complaining) |

The AI's self-review made the same calls on the date and the peel back on draft 3. As for the diff, that's what the preservation check is for - a lot of draft 1's dialogue is gone or reworded, and every one of those changes should've been something I meant.
