# For reviewers

If you're hiring for an ML role on creative tools, this page is pretty much the shortcut. It goes through what those roles tend to ask for, in roughly the order they ask, and points at the evidence in this repo for each one. Where the evidence lives outside the repo (my day job, mostly), I've just said so, and the last section is an honest list of what I'm still building toward.

## Shipping reliable, tested code

I've worked full time as a software engineer for 3 years, most recently building AI tooling at a large bank, including the tool layer an assistant calls and a personal-memory service I originally wrote. That work isn't public, but here's what is.
- [`tools/`](../tools/) with [35 tests](../tests/) that run on Linux, macOS and Windows on every push. The scanner refuses to save if its labels don't strip back to the original text byte for byte.
- [worktree-handoff](https://github.com/cthleung/worktree-handoff), a plugin I spun off from this setup, with its own cross-platform test suite and guards against overwriting work it didn't expect.

## Applying LLMs to a real project

That's honestly the entire repo, but the clearest pieces are probably these.
- **Agents and prompting.** 5 reader agents with strict output formats, run cold so they can't see each other's reasoning ([the prompts](../agents/), and how they fit in [how-it-works.md](how-it-works.md)).
- **Evaluation.** Gold sets built from my own rulings, a blind test with held-out lines, and repeated runs ([evaluation.md](evaluation.md)).
- **Deployment and model choice.** I served a fine-tuned 31B model myself and measured it against Claude on time to first token, context and cost ([model-experiments.md](model-experiments.md)).
- **Personalization.** How my picks and overrides become rules and tests, and the preference data a LoRA adapter could train on later ([taste-memory.md](taste-memory.md)).

## Experimental design, and telling a real effect from noise

The [first repeated-run experiment](../evals/results/2026-11-03-calibrated-vs-generic.md) compares my calibrated voice reader against a generic judge, blind, 5 runs each, with bootstrap intervals and an exact McNemar test. The result I'm proudest of is, oddly, the boring one - the calibrated brief caught 87% of the bad lines against 67%, and I still can't claim it's better, because only 3 lines separated them and that can't get below p = 0.25. The write-up says why, and what it'd take to find out (more must-fail lines, not more runs).

That being said, 2 smaller habits show up elsewhere too. When I deployed my own model, I set a latency target first (under 8 seconds to the first token) and measured against it. And when a benchmark claimed my new GPU had doubled the prompt speed, a later check found the requests had been hitting the old one the whole time, so I just don't trust a speedup until I know which machine answered.

## Product sense: is this the right experience?

- **[The tangerine drive](../case-study/tangerine-drive/README.md)** shows where I overrode the AI and why. That includes the times I pulled the other way, like letting a stock smirk stay so the scene didn't get over-written, because a fix that touches every line does real damage too.
- **[Model experiments](model-experiments.md)** is the "can the model do it, versus is it the right experience" question in real life. The fine-tune actually wrote better sentences and was still the wrong choice, because a 2-minute cold start kills a writing session.
- **[Keep what works](how-it-works.md).** A reader agent exists only to protect what a draft already does well.
- **[Version control you can see and talk to](version-control.md)** started as my own pain point (several AI chats in 1 folder, 2 computers, and no patience for git), and it ends with what I'd want in an editing app.

## Agentic systems, tool use and evaluation harnesses

- **[The harness](the-harness.md).** Hooks on every message and every edit, skills, cold subagents, MCP servers, and 1 config shared by 2 AI editors.
- **[How it works](how-it-works.md).** The loop step by step, with the tool behind each step.
- **[Skills](../skills/README.md).** 2 skills that run git for me from plain requests, with [`tools/tree_triage.py`](../tools/tree_triage.py) underneath, which reads every chat transcript to work out which chat changed which file.
- At work, the tool-serving layer an AI assistant calls into (not public).

## Using creative tools from the inside

I'm a photographer and filmmaker on the side (Lightroom and Final Cut Pro, mostly), with a background in screenwriting and film analysis, and I write the novel like I'd shoot a film. [Why I built it](why-i-built-it.md) is the story, and [beyond-text.md](beyond-text.md) is what I'd actually want from an agent inside a photo or video app, from someone who's watched a tool turn into the bottleneck and knows where it gets in the way.

## A non-traditional path

I came to prose from film, and to SWE/ML from an engineering physics degree. In other words, most of what's in here I learned by just building it to support me with a creative project I really cared about. [Why I built it](why-i-built-it.md) covers how that happened.

## What I'm still building toward

- **A bigger gold set,** so the experiments have enough must-fail lines to show a real difference.
- **On-device work.** The plan is a local model on my Mac with MLX, which I haven't really started yet.
- **Swift and Apple-platform code.** I've studied Swift, but nothing in this repo is native app code.
- **The preference log and an adapter trained on it,** which are designed but not built.
