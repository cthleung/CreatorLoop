# For reviewers

If you're hiring for an ML role on creative tools, this page is pretty much the shortcut. It goes through what those roles tend to ask for, in roughly the order they ask, and points at the evidence in this repo for each one. Where the evidence lives outside the repo (my day job, mostly), I've just said so, and the last section is an honest list of what I'm still building toward.

## How I built these repos

Both repos were built with coding agents, mostly Claude Code, and I'd rather just say so up front. The agent did most of the typing, code and first drafts of docs alike (the docs then go through a voice check I built against my own writing samples, so they still sound like me). That check's there for the same reason as the novel's scanners, since I know how I want my writing to sound, and I'd hardly be hiding the AI on a page that tells you about it. **The problems, the rules, the picks and every merge were mine.** [Section 9 of worktree-handoff's engineering page](https://github.com/cthleung/worktree-handoff/blob/main/docs/how-i-engineer.md#9-working-with-a-coding-agent) has the stories of where the checks caught the agent, and honestly, building with agents every day is where a lot of my opinions about creator tools come from.

## Shipping reliable, tested code

I've worked full time as a software engineer for 3 years, most recently building AI tooling at a large bank. That work isn't public, so here's the short version first.
- **Deploying an ML model to production GPUs:** I deployed a PII-detection NER model to our internal inference platform (NVIDIA Triton, on H100s) and wrote nearly all of that repo, CI/CD included: deploys across pre-production environments, signed release bundles, container image scanning, and a config-only deploy so a tuning run didn't need a full rebuild.
- **Tuning it like an experiment:** Each phase changed 1 variable (batch size, queue delay, pod count, GPU split, CPU allocation) against a recorded baseline, and every table in the write-up ended with a verdict. 2 pods splitting 1 GPU beat 1 pod with a full GPU, for the same GPU budget, with 21 to 31 times lower latency and 55 to 58% more throughput at typical load. At extreme load, though, throughput dropped by about a quarter, and I wrote that down just as plainly as the win, since anyone picking that config should know.
- **An agent with a person in charge:** I'm a named inventor on [US 12,639,279](https://patents.google.com/patent/US12639279B2/en), granted in 2026, for an LLM agent that fills in missing documentation for business datasets. It works in small steps you can check on their own, and a data steward approves what it writes, which is really the same loop as everything in this repo - just a few years earlier.
- **Rolling it out safely:** A feature toggle across the shared protocol library, the gateway and the worker, with the worker falling back to the existing path if the new inference service was down.
- **Ownership:** I wrote the first version of a backend memory service and became its largest contributor, and I'm the largest individual contributor on the tool server our AI assistant talks to. I ship in small PRs, several a day when the work allows, because a change that's reviewable in one sitting is a change I'd want to inherit.

And here's what's public.
- [`tools/`](../tools/) with [48 tests](../tests/) that run on Linux, macOS and Windows on every push. The scanner refuses to save if its labels don't strip back to the original text byte for byte.
- [worktree-handoff](https://github.com/cthleung/worktree-handoff), a plugin I spun off from this setup and the repo I'd point to for how I build. It has 44 tests (end to end against real git on Linux, macOS and Windows, plus fast unit tests), lint, type checks and 84% coverage in CI, [design notes](https://github.com/cthleung/worktree-handoff/blob/main/docs/design.md) for every decision behind its safety guards, and a [build log](https://github.com/cthleung/worktree-handoff/blob/main/docs/building-log.md) that walks through it 1 small, green pull request at a time.

## Applying LLMs to a real project

That's honestly the entire repo, but the clearest pieces are probably these.
- **Agents and prompting:** 5 reader agents with strict output formats, run cold so they can't see each other's reasoning ([the prompts](../agents/), and how they fit in [how-it-works.md](how-it-works.md)).
- **Evaluation:** Gold sets built from my own rulings, a blind test with held-out lines, and repeated runs ([evaluation.md](evaluation.md)).
- **Deployment and model choice:** I served an open fine-tuned 31B model myself (a community fine-tune, so I didn't train it) and measured it against Claude on time to first token, context and cost ([model-experiments.md](model-experiments.md)), and ran a 12B model on my own laptop with MLX against the same blind test ([results](../evals/results/2026-11-03-local-mlx.md)).
- **Personalization:** How my picks and overrides become rules and tests, and the preference data a LoRA adapter could train on later ([taste-memory.md](taste-memory.md)).

## Experimental design, and telling a real effect from noise

The [first repeated-run experiment](../evals/results/2026-11-03-calibrated-vs-generic.md) compares my calibrated voice reader against a generic judge, blind, 5 runs each, with bootstrap intervals and an exact McNemar test. The result I'm proudest of is, oddly, the boring one - **the calibrated brief caught 87% of the bad lines against 67%, and I still can't claim it's better**, because only 3 lines separated them and that can't get below p = 0.25. The write-up says why, and what it'd take to find out (more must-fail lines, not more runs).

That being said, the same habit shows up elsewhere too. At work, I tuned the GPU deployment above one variable at a time against a baseline. When I deployed my own model, I set a latency target first (under 8 seconds to the first token) and measured against it. And when a benchmark claimed my new GPU had doubled the prompt speed, a later check found the requests had been hitting the old one the whole time, so I just don't trust a speedup until I know which machine answered.

## Product sense: is this the right experience?

- **[The tangerine drive](../case-study/tangerine-drive/README.md)** shows where I overrode the AI and why. That includes the times I pulled the other way, like letting a stock smirk stay so the scene didn't get over-written, because a fix that touches every line does real damage too.
- **[Model experiments](model-experiments.md)** is the "can the model do it, versus is it the right experience" question in real life. I really liked the fine-tune's prose, and it was still the wrong choice, because a 2-minute cold start kills a writing session.
- **[Keep what works](how-it-works.md):** A reader agent exists only to protect what a draft already does well.
- **[Version control you can see and talk to](version-control.md)** started as my own pain point (several AI chats in 1 folder, 2 computers, and no patience for git), and it ends with what I'd want in an editing app.

## Agentic systems, tool use and evaluation harnesses

- **[The harness](the-harness.md):** Hooks on every message and every edit, skills, cold subagents, MCP servers, and 1 config shared by 2 AI editors.
- **[How it works](how-it-works.md):** The loop step by step, with the tool behind each step.
- **[Skills](../skills/README.md):** 2 skills that run git for me from plain requests, with [`tools/tree_triage.py`](../tools/tree_triage.py) underneath, which reads every chat transcript to work out which chat changed which file.
- At work, the tool-serving layer an AI assistant calls into (not public).

## Using creative tools from the inside

I'm a photographer and filmmaker on the side (Lightroom and Final Cut Pro, mostly), with a background in screenwriting and film analysis, and I write the novel like I'd shoot a film. [Why I built it](why-i-built-it.md) is the story, and [beyond-text.md](beyond-text.md) is what I'd actually want from an agent inside a photo or video app, from someone who's watched a tool turn into the bottleneck and knows where it gets in the way.

## A non-traditional path

I came to the novel from film and a lot of reading and writing, and to SWE/ML from an engineering physics degree. The story grew to about 400,000 words, which is more than I could ever write by hand for a passion project, so most of what's in here I built to scale up my own creativity without losing the vision, and pretty much learned it all as I went. [Why I built it](why-i-built-it.md) covers how that happened.

## What I'm still building toward

- **A bigger gold set,** so the experiments have enough must-fail lines to show a real difference.
- **On-device work:** [A first MLX run](../evals/results/2026-11-03-local-mlx.md) put Gemma 4 12B on my MacBook Air as the voice reader, with the same blind test and stats as the Claude runs. It matched Claude on 38 of 42 lines, but the first token took a median 151 seconds, so the next step is the prompt cache and a bigger gold set.
- **Swift and Apple-platform code:** I've studied Swift, but nothing in this repo is native app code.
- **The preference log and an adapter trained on it,** which are designed but not built.
