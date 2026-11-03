# 2026-11-03: calibrated voice brief vs a generic judge

**Question:** Does my calibrated voice reader (the "ear") flag the lines I'd flag and leave alone the ones I'd leave alone, better than a generic "spot the AI prose" judge does, by more than run-to-run noise?

## Setup

- **Gold set:** My novel's voice gold set, 48 lines. 28 must pass (lines from scenes I'd approved, picked because a plainness judge would be tempted to flag them), 14 must fail (proposed by the AI, and I signed off on all 14 after this run, so the catch numbers stand), 6 unruled. The lines themselves stay in the novel's repo. This file only has IDs.
- **Blind file:** Built by `blind_eval.py build`, shuffled with the fixed seed, answers stripped. Every run got the same file.
- **Brief A, calibrated:** My ear-reader agent, which reads my style guide's voice sections, the voice cards for each narrator and the reference list before judging.
- **Brief B, generic:** A general agent told to flag "AI-generated, overwritten or unnatural prose," with the same register names and output format, reading nothing but the blind file.
- **Runs:** 5 fresh sessions per brief, 10 in all, on the same underlying model, run in parallel.
- **Analysis:** `tools/eval_stats.py`, with 10,000 bootstrap resamples over items and an exact McNemar test on each item's majority verdict.

## Results

| | Calibrated brief | Generic judge |
|---|---|---|
| False alarms on 28 must-pass lines | mean 4% (runs 4% to 7%), 95% interval 0% to 12% | mean 5% (runs 4% to 11%), 95% interval 0% to 13% |
| Catches on 14 must-fail lines | mean 87% (runs 86% to 93%), 95% interval 69% to 100% | mean 67% (runs 64% to 71%), 95% interval 43% to 89% |
| Lines that flipped between runs | 2 of 42 (F13, P24) | 3 of 42 (F13, P24, P25) |
| Must-fail lines missed in every run | F10 | F03, F04, F07, F10 |

McNemar on majority verdicts:
- **Must-pass lines:** The 2 briefs disagreed on 0 lines, p = 1.
- **Must-fail lines:** 3 lines were caught only by the calibrated brief and 0 only by the generic judge, p = 0.25.

## What it says

- **Both briefs failed the zero-false-alarm bar, on the same line:** P23 got flagged in all 10 runs. So either my brief needed to learn that line was fine, or my pass label on it was wrong. I ruled on it after the run, and the answer was a bit of both. P23 was 2 sentences, and I kept the first ("Still performing, even with the rest of her gone numb." is her voice) as a must-pass, while the second, which states the theme as a paradox, became a must-fail line, F15. Honestly it's the most useful thing this run found, because without the gold set I'd never have looked at that sentence again.
- **The calibrated brief catches more, but this gold set is too small to prove it:** 87% against 67% looks like a big gap, but McNemar only counts the lines where the 2 briefs disagree, and there were just 3 of those. A 3-to-0 split can't get below p = 0.25 however you slice it. It takes at least 6 lines going one way with none the other way to get under 0.05, so the fix is more must-fail lines, not more runs.
- **Run-to-run noise was small:** Only 2 or 3 of the 42 scored lines ever changed verdict, so 5 runs per brief was probably plenty for this test.
- **My assumption about generic judges was wrong:** I really expected a plainness judge to flag lots of the grand, strange lines I'd approved, and it didn't (5% against 4%). Its weakness was the other way round - it just let more of the bad lines through.

## Raw data

Every verdict from all 10 runs is in [2026-11-03-calibrated-vs-generic-runs.csv](2026-11-03-calibrated-vs-generic-runs.csv), 1 row per gold item (IDs only), with a 1 where that run flagged the line. The `expect` column uses the labels as they stood on 2026-11-03, after I signed off on the 14 fail lines.

## Reproducing it

The gold set lives in my novel's repo, so the lines aren't here, but the steps are the same for any gold set in this format (see [evals/voice-gold.md](../voice-gold.md)):

```bash
python3 tools/blind_eval.py build --gold GOLD.md --out run/
# give run/blind.md to each brief in a fresh session, 5 times each, saving the reports
python3 tools/eval_stats.py run/key.json --a A1.md A2.md A3.md A4.md A5.md --b B1.md B2.md B3.md B4.md B5.md \
    --name-a "calibrated brief" --name-b "generic judge"
```

## Next

1. Rerun on the updated set, with P23 split into a must-pass and a new must-fail line, F15. (The numbers above are on the set as it stood for this run.)
2. Grow the must-fail set until a real difference has room to show up.
3. Rerun, and keep each run's results in this folder.
