# Skills

A skill's just a written procedure an AI agent can load and follow, a markdown file with a short description up top so the agent knows when to reach for it. These 2 are the ones I built so I'd never have to type git myself.

| Skill | What I say | What it does |
|---|---|---|
| [tree-triage](tree-triage/SKILL.md) | "Sort out the working tree." | Reads every chat transcript to see which chat changed which file, then proposes 1 commit per job and asks before committing anything |
| [session-commit](session-commit/SKILL.md) | "Commit this session's work." | Commits only the current chat's finished files, runs the tests if code changed, and asks about anything another chat touched too |

Both lean on [`tools/tree_triage.py`](../tools/tree_triage.py), which does the actual detective work (reading `git status` and the transcripts) and never stages or commits anything on its own. The skill is the judgment around it: what's ready, what's being held, what needs a question, and the rules for staging safely.

## Why they exist

My editor usually has several AI chats going at the same time, each on its own job, and they all write into the same folder, which I then carry between a Mac and a Windows PC. So by the end of a day the working tree's a pile of changes from different jobs, some of them finished and some of them really not. Git can untangle that, technically. But even as a software engineer, I couldn't be bothered to remember the commands for staging 1 chat's files and not another's, so I wrote down how I'd want it done and let the agent do it. The third piece, carrying unfinished work between computers, turned into its own plugin, [worktree-handoff](https://github.com/cthleung/worktree-handoff).

These days I don't really type git for the novel at all. I say what I want, the agent shows me the plan, and it runs once I say yes. [version-control.md](../docs/version-control.md) is where that leads for other creators.

## Using them

Copy or symlink a skill's folder into `.claude/skills/` in your repo (or `~/.claude/skills/` for every repo), and Claude Code picks it up. That's it. They follow the house rules I use everywhere, so they stage by exact path, never push without asking, and never add AI attribution lines to commits.
