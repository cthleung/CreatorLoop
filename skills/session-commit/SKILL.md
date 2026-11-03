---
name: session-commit
description: Commits the finished work from the current Claude Code session only, leaving every other session's changes in the working tree. Finds this chat's files from its transcript, runs the tests when code changed, flags files another session also edited, then stages and commits only what the author approves. Use when the author asks to commit this session's work, wrap up the session, or runs /session-commit. For sorting the whole tree across every session, use tree-triage.
argument-hint: "[session id or name, default: this chat]"
---

# Session commit

The working tree usually holds several sessions' jobs at once. This skill commits 1 of them: the session it runs in, or the one named in the argument. Everything else stays uncommitted. It never stages or commits without the author's say-so, and pushing is a separate ask.

## 1. Find this session's files

```
python3 tools/tree_triage.py --session --diffs
```

With no value, `--session` reads this chat's id from `CLAUDE_CODE_SESSION_ID`. For another session, pass its id prefix or part of its name (`--session 58ae9ee8`, `--session "harness doc"`). The output has up to 3 groups:

- **Only this session edited these.** The commit candidates.
- **Other sessions edited these too.** Never commit these without asking (step 3).
- **Quotes only.** A quote cleanup is the only change. These go in a commit of their own.

Flags on a file (`GATE`, `open marker(s)`, `untracked`, `deleted`) mean the same as in tree-triage's step 1.

## 2. Check what's ready

- **Tests:** if any file in the session's list is in `tools/`, `rules/` or `tests/`, run `python3 -m unittest`. A failure holds every code file until it's fixed or the author says to commit anyway. Report the failing test's name and message.
- **Ready, hold or unsure:** judge the rest by tree-triage's step 2. A file this session created and never finished is a hold.
- **Check against the chat:** this session's own conversation says which jobs the author signed off on. A file whose change the author rejected or never saw is a hold, even when it scans clean.

## 3. Shared files

For each file another session also edited:

1. Show the author `git diff HEAD -- "path"` and say which parts this session made, from the chat.
2. Ask: commit the whole file now (it carries the other session's edits too), leave it for the other session, or ask the other session first (tree-triage's step 3 covers `ListAgents` and `SendMessage`).
3. Splitting 1 file's changes between commits needs `git add -p`, which an agent can't drive interactively. Say so if the author asks for it.

## 4. Propose the commit

Show a short numbered plan: each commit's files, a one-line subject, and the verdict for anything held. Usually that's 1 commit per session. If the session did unrelated jobs (a doc fix and a script), split it into 1 commit per job. Use the repo's style, a lowercase prefix then a plain subject (`git log --oneline -30` for current prefixes). No `Co-Authored-By` or "Generated with" lines.

## 5. Commit what's approved

- Stage by exact path: `git add -- "path" "path"`. Quote every path, since names can have spaces. Never `git add -A` or `git add .`.
- Run `git diff --cached --name-only` before committing and check it's exactly the approved list. Something the author staged by hand earlier shows up here too, so ask before committing with it.
- After each commit, run `git status --short` to confirm only those files left the tree.
- Offer to push at the end, and push only on a yes.

## 6. Report

1 short list: the commits (hash and subject), the files held and why, and the shared files still waiting on a decision. If [worktree-handoff](https://github.com/cthleung/worktree-handoff) is installed, mention that the uncommitted rest goes to the other computer when the chat closes.
