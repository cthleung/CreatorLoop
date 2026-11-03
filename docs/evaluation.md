# Evaluation

Creative writing is honestly a pain to measure, since there's no right answer to score against. What I can measure, though, is whether the system respects calls I've already made, and whether its reviewers flag things I'd flag and leave alone the things I'd leave alone. So that's what the evals here do. This doc covers what runs today, and what I'm adding next, kept separate so it's clear which is which.

## Why false alarms matter more than misses

This is the one idea the rest of the doc hangs on. If a reviewer misses a tic, I'll probably just catch it myself when I read the draft. If a reviewer flags a line that was actually good, and nobody notices, the fix sands that line down into something safer and blander. Do that across a whole book and you get prose that's technically clean and has no voice left in it, which is pretty much the failure I built all this to avoid.

So every eval here treats a false alarm on a good line as worse than a miss. For the voice reader, the bar is zero false alarms on the lines that must pass, and if it fails that, its instructions get fixed before I trust any of its flags.

## What runs today

### The scanner's gold cases

The scanner has a file of gold cases, each one a line it must flag or a line it must leave alone, labeled with the rule.

```
flag | hedge | She seemed tired.
pass | hedge | "It's kinda making a really good point," she said.
```

There are 45 of them in my own setup right now, and every one comes from a ruling I made. The test suite runs all of them, along with tests for the other scripts (28 tests in all in the novel's repo, passing as of 2026-11-02, and this repo has its own suite of 35). The `pass` lines are the important ones - they keep a rule from creeping into territory I've already said is fine, like a hedge in dialogue, or a number the story actually counted ("Back in Scene 4, she'd lied").

The scanner also keeps score on itself. Every label it writes gets a verdict from the review (`keep`, `tic`, `false alarm` or `ask`), and a review report lists any rule where at least 50% of its reviewed hits, out of 3 or more, turned out to be false alarms. That rule's regex gets fixed at the source, so I'm not dismissing the same misfire forever.

### The blind voice test

The voice reader (the "ear") is a model, so it can't really be unit tested like a regex. Instead, it takes a blind test built from a gold set of lines, where each one is marked as must pass, must fail, or unruled.

- **Must pass:** mostly lines from scenes I've approved, picked because a naive "make it plainer" judge would wrongly flag them. They're grand, or strange, or run-on, or crude on purpose. "Also, technically, it was practicing." is one.
- **Must fail:** lines that should get flagged, with the register they slipped into (essay, poem, press release and so on).
- **Unruled:** lines I haven't called yet. They're not scored, but the reader's verdict gets reported so I can rule on them.

The test script shuffles the lines with a fixed seed (so reruns are comparable), strips the answers, and hands the reader a blind file. Scoring then separates false alarms, misses, and catches flagged under the wrong register. It also picks out the held-out lines, the ones that never appear in the reader's own instructions, since a reader that passes only the lines it's already been shown has memorized them, and that's not the same as understanding them.

The gold set has 49 lines today, with 28 that must pass, 15 that must fail and 6 unruled. In fairness, the AI proposed 14 of the failing lines, but I've gone through and signed off on every one (the 15th came from my own ruling, below), so the benchmark is all mine now. Whenever I overrule the reader on a real draft, the line goes into the gold set, so the same mistake gets caught next time.

## Treating the reader like the noisy model it is

A single run of the blind test only tells you what happened once, so I ran it like you'd test anything noisy. I gave my calibrated ear brief and a generic "spot the AI prose" judge the same blind file, 5 fresh runs each, and ran the results through `tools/eval_stats.py`, which reports the false-alarm and catch rates per run, a bootstrap confidence interval over items, how often each line flips between runs, and an exact McNemar test on the lines where the 2 briefs disagree. The full write-up is in [evals/results](../evals/results/2026-11-03-calibrated-vs-generic.md), and the short version goes like this:

| | Calibrated brief | Generic judge |
|---|---|---|
| False alarms (28 must-pass lines) | 4%, 95% interval 0% to 12% | 5%, 95% interval 0% to 13% |
| Catches (14 must-fail lines) | 87%, 95% interval 69% to 100% | 67%, 95% interval 43% to 89% |
| Lines that flipped between runs | 2 of 42 | 3 of 42 |

Honestly, the result I learned the most from wasn't the headline. Both briefs flagged 1 of my approved lines in all 10 runs, so neither one passed my zero-false-alarm bar. When I went back to rule on it, the readers were partly right: I kept the first sentence as a pass and turned the second into a must-fail line. The catch gap looks big too, but McNemar only had 3 disagreeing lines to work with, which can't get below p = 0.25 however they fall, so this gold set is too small to prove the calibrated brief is better. It needs more must-fail lines, not more runs, since the runs barely disagreed with each other.

Still missing:
- **More must-fail lines.** All 14 are signed off, but 14 is too few for a real difference to show up (the McNemar point above).
- **Score history.** Every rerun goes in `evals/results/` from now on, so there's a trend to look at.
- **Product-level numbers.** Once the preference log from [taste-memory.md](taste-memory.md) exists, a few come almost for free - how often I pick the AI's recommended option, how much I edit a line after approving it, and whether the same correction keeps coming back. That last one is the number I'd actually watch, because the whole point is to stop saying the same thing twice.

## Why this matters beyond my novel

That being said, any creative tool with an AI in it runs into the same wall I did. The tasks are open-ended, there's no answer key, and the person using the tool has a taste the model doesn't know about yet. So the questions are pretty much the ones this repo already asks. Does the system respect a call the creator already made? Does a reviewer flag what the creator would flag, and leave alone what they'd leave alone? And when you change a prompt or a model, did it actually get better, or did you just get a lucky run?

In other words, what I'd bring from this to a photo or video tool is mostly the shape of it. The gold cases come from the creator's own rulings, so nobody has to agree on a universal standard of taste, which is good, because nobody ever would. A false alarm counts as worse than a miss. Flattening someone's work is the failure they won't forgive, but a miss they'll usually just catch themselves. Held-out lines catch a reviewer that's memorized its examples, and the repeated-run stats are there to separate a real improvement from noise. None of that is specific to prose. That's the part I find most exciting about it, honestly.
