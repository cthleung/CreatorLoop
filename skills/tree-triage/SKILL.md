---
name: tree-triage
description: Sorts a messy working tree into scoped commits. Reads every Claude Code session transcript for this repo to see which session edited which uncommitted file, batches the quotes-only files, flags files that two sessions touched or that still hold open markers, then stages and commits only what the author approves. Use when the author asks to clean up, triage, sort or commit the working tree, or runs /tree-triage.
argument-hint: "[session name to focus on]"
---

# Tree triage

The author works in several AI sessions at once, so the working tree is usually a pile from several jobs. This skill works out who made which change and turns the pile into a few scoped commits, 1 per job. It never stages or commits without the author's say-so, and it never pushes.

## 1. Run the script

```
python3 tools/tree_triage.py
```

It prints a plan in a few seconds. Add `--diffs` for +/- line counts per file, or `--json` to process it. The groups:

- **Quotes only.** Files that match HEAD once smart quotes are straightened, so a quote cleanup is the only change. Safe to commit together, and they always go in a commit of their own, apart from any content work.
- **One block per session.** Files that only that session edited since the file's last commit. The block carries the session's name, topic and last prompt, which is enough to write a commit subject from.
- **Edited by more than one session.** Never put these in a session's commit without asking.
- **No session edited these.** Hand edits in the editor, a script run from a terminal, a session from another folder, or a transcript that's gone.
- **SpecStory logs.** If chat history syncs into `.specstory/`, its own hook commits these. Leave them alone.

Flags on a file:
- `GATE`: a hard rule from `rules/` (an em dash, a banned word) in the lines the file added.
- `open marker(s)`: `[?? ??]` gaps, TODO/TBD/FIXME or merge markers. "New" means more than HEAD has.
- `includes smart-quote cleanup`: real edits with a quote run mixed in.
- `deleted`, `untracked`, `unmerged`.

A deleted file plus an untracked file with a similar name is a rename (git shows it as a delete and an add). Commit them together.

## 2. Judge what's ready

The script gives evidence. The call gets made here.

- **Ready:** the session's job is done, no `GATE` flags, and no new markers that mean unfinished work.
- **Hold:** new open markers in a draft, `GATE` flags, or a session whose last prompt shows it's still mid-task. `[?? ??]` gaps inside a plan file are normal and don't block a commit.
- **Unsure:** read the diff (`git diff HEAD -- "path"`) before deciding. A big prose diff gets a skim for what changed, and it doesn't need a full edit review.

Markers inside a style guide or a rules file are usually the text of a rule being documented, so check before treating them as unfinished work.

## 3. Ask other sessions only when the files don't settle it

For "no session edited these" files and for shared files, the diff and the session names usually answer it. If they don't:

1. Run `ListAgents` to see the live sessions. Their names match the script's session names. Closed sessions don't appear there and don't need to, since their transcripts already fed the script.
2. Ask the author before messaging a session, because it wakes that session and spends their usage.
3. Send each session 1 question with `SendMessage`: which of these files did you change, is that job finished, and should it be committed with anything else. Name the files in the message. A session's reply is its own summary, so check it against the diff.

## 4. Propose the commits

Show the author a short numbered plan: each commit's files, a one-line subject, and a verdict (ready, hold, unsure). Put the quotes-only batch first. Use the repo's style, a lowercase prefix then a plain subject, like `case study: side by sides for the opening`, `rules: flag delivery similes`, `tools: repeated-run stats` or `fix: typo in the README`. Check `git log --oneline -30` if the prefixes need refreshing.

No `Co-Authored-By` or "Generated with" lines in commit messages.

## 5. Stage and commit what's approved

- Stage by exact path with `git add -- "path" "path"`. File names can have spaces, so quote every one. Never `git add -A` or `git add .`.
- A file that mixes quote cleanup with real edits goes in its session's commit. Splitting the quote run out of it needs `git add -p`, which an agent can't drive interactively, so mention it to the author and leave it.
- After each commit, run `git status --short` to confirm only the intended files left the tree.
- Leave held files in the tree, and list them at the end with the reason each one's held.
- Pushing is a separate ask. Offer it at the end, and only do it on a yes.

## 6. Report

End with 1 short list: what got committed (hash and subject), what's still uncommitted and why, and anything the author needs to decide.
