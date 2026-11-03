# The harness

The model's honestly the smallest part of this. Most of what makes the loop work is everything I've built around it inside my editor - the context it reads, the hooks that fire on every message and every edit, the agents and skills it can call, the scripts and tests that check its work - which is what people call harness engineering these days, and it's the part I've spent the most time on. I honestly didn't know it had a name when I started. I just kept hitting the same problems, and every fix turned into another piece of the editor.

This doc walks through those pieces as they're set up in my novel's repo, using the tools Claude Code and VS Code already give you. Nothing here needed a custom app, which still kind of surprises me, and I'd guess it'd surprise most people.

## 1 config, 2 editors

I work in VS Code with Claude Code, and sometimes with GitHub Copilot's agent, so the first problem was keeping 2 AI assistants following the same rules, which isn't as easy as it sounds. All the rules live in a single file, `AGENTS.md`, and the other editor's config files just point at it. That way I edit rules in 1 place, and both assistants read the same thing at the start of every session.

## Hooks

Hooks are small scripts the editor runs on its own at set moments. **The rules in a config file are really just suggestions, but a hook is where they stop being optional.**

| When | What it does |
|---|---|
| Every message I send | Injects a short reminder of the house rules before the model sees my message, because long sessions drift |
| Before every file edit | The edit gate. It blocks any edit that adds an em dash or a word I've banned outright to a prose file. Both editors' hooks call the same script, so they can never disagree |
| When a chat opens, closes, or every 20 minutes | Syncs the chat history, and carries my unfinished work to my other computer (below) |

The edit gate only looks at what an edit adds, so the AI can still quote an old line that breaks a rule while it's labeling it. That being said, everything softer than an absolute ban goes to the scanner instead, which labels it for a person to judge, since blocking's only worth it for the rules that have no exceptions.

## Skills and subagents

A skill's just a written procedure the AI can load and follow, and I use them for the jobs that have a lot of steps I'd otherwise forget. The big one's the remaster scan, which runs all the scripts on a chapter in one go, sends the 5 reader agents through it, gives every label a verdict, and starts the plan file with a map of the scenes and a list of questions for me. The other 2 handle committing, because even as a software engineer I couldn't be bothered to remember the git for it. [session-commit](../skills/session-commit/SKILL.md) commits only the current chat's finished work, and [tree-triage](../skills/tree-triage/SKILL.md) sorts a messy working tree into commits by reading every chat transcript to see which chat changed which file. I just say what I want, and they show me the plan before running anything ([version-control.md](version-control.md) is where that idea goes next).

The 5 readers (voice, gloss, blocking, fact check and strength) are subagents. Each one runs in its own fresh context with only the clean text and its brief, and that's what makes them "cold." They only report, though, and a script writes their findings into the file, so no agent ever edits the manuscript directly.

## The rest of the toolbox

- **Scripts:** 18 Python scripts, standard library only, for scanning, merging labels, splitting scenes, finding repeated phrases, checking cadence against each narrator's baseline, spell checking, picking numbers and so on.
- **Tests:** A test suite that runs every scanner gold case plus the other scripts (28 tests right now), and a rule that it runs after any change to a script or a rule.
- **MCP servers:** Filesystem and git servers, mostly so the agents can read and search the repo like I would myself. Nothing exotic, but they're handy.
- **Memory:** The memory notes live in the repo and get linked into Claude Code's memory folder, so my taste travels with git instead of living on one machine.
- **An output style:** Even how the AI talks to me in chat is configured, believe it or not. It talks like I write in my own DMs, measured against samples of my writing, because a stiff, corporate chat partner wears me out over a long session.

## Working across 2 computers

I actually write on a Mac and a Windows PC, so the setup's got to install and run on both. The repo has a one-shot setup for each machine, plus a setup doc written so that Claude Code can just do the install itself from a single prompt, and the scripts don't choke on Windows quirks like a missing `python3` command or Korean text in the console.

Unfinished work was the harder problem, though. I didn't want to commit unfinished edits just to switch computers, so I built a tool that bundles the working tree into a hidden git ref when a chat closes, pushes it, and unpacks it as ordinary uncommitted edits when a chat opens on the other machine. It skips anything that looks like a secret, and it won't touch a tree with local changes it didn't expect, which I'm pretty glad about. It turned out to be useful enough that I spun it off as its own plugin, [worktree-handoff](https://github.com/cthleung/worktree-handoff), with its own tests running on Linux, macOS and Windows.

## What I'd want a reader to take from this

In other words, very little of it's clever on its own. A hook's a shell script, and a skill's a markdown file. What took the work was noticing each failure while I was actually writing (the AI forgetting a rule partway through a long session, an edit sneaking in a banned word, a fix quietly losing a good line, work stuck on the wrong computer) and putting a check right where that failure happens. But that's the habit I'd bring to any creative tool.
