# How it works

This is the loop step by step, with the tool or agent behind each step. Everything runs inside my code editor (VS Code with Claude Code), and all of it is just plain markdown files plus a handful of Python scripts that only use the standard library, so there's really nothing exotic to install. The [case study](../case-study/tangerine-drive/README.md) shows the same loop on a real scene, if you'd rather see it in action first.

Oh, and a quick note on names. The scanner, the merge, the blind test, the preservation diff, the number picker and the commit helper are in `tools/` under the names I use here, the 5 reader prompts are in [`agents/`](../agents/), with a small demo rule pack in `rules/` and tests for all of it, so you can run them on the case study yourself. The scanner here is a smaller rewrite of the one I use on the novel, since mine is full of rules about my own characters. `apply_check.py` hasn't been ported yet.

## 1. The AI reads the room first

Before it touches a scene, the AI reads the project's standing context. That's a rules file it loads at the start of every session (my house style, hard bans, how each narrator sounds), a style guide for how sentences should move, character briefs, and a folder of memory notes, each one a single fact about my taste or the story with the reason behind it. None of this is clever, honestly. It's just everything I'd otherwise have to repeat every session, written down once - which, it turns out, is most of the battle.

## 2. Everything happens in a plan file

Every scene gets a plan, which is just a markdown doc where the outline, the fact check, the options, the drafts and the review notes all live, in that order, with a dated log of my decisions at the top. Drafts go into the plan first, and nothing touches the actual manuscript until I say so. When a new version does go in, the old text gets commented out right beside it, so I can compare the two before cleaning up.

Wherever a line or a beat could go several ways, the plan gives numbered or lettered options with the AI's recommendation first. I pick 1, combine 2 or write my own. Section 2 of every plan is always the thing waiting on me, so I never have to dig for it.

## 3. The draft and its self-review

The AI drafts from the plan, then reviews its own draft before I see it, with a pass on the prose, a pass on the dialogue (anything that reads scripted, or just echoes the line before), and then a scan. In the case study, the dialogue pass caught "Later it's treasure" sounding like a fortune cookie, so the character undercuts it herself with "Write that down."

## 4. The scanner

The scanner, `rule_engine.py`, is the boring, predictable layer, and that's on purpose. It reads the draft against a rule pack of regex patterns, grouped into families (hedges, narrator distance, signposting, stock phrasing and so on), and writes a short label inline right after each phrase it's worried about:

```
She seemed tired. [check: hedge]
```

There are 2 kinds of label, and they're pretty different. A `hard` label means the rule's broken almost every time it fires. A `check` label means maybe, since it might be a tic, or it might just be the character's voice, and a person has to decide. That being said, the scanner never fixes anything. It only labels.

The part I'm proudest of is that labels can always come back out. **Stripping every ` [...]` from the file gives back the original byte for byte, line numbers never move, and the scanner won't save if that round trip ever fails.** So the labels can sit inside the manuscript while I work, and they can't damage it.

## 5. The cold readers

But some problems no regex can see, so 5 reader agents go through the scene as well.

| Reader | Looks for |
|---|---|
| Ear | lines nobody would actually say, where the narration slips into an essay or a romance-novel cover |
| Gloss | the narrator explaining what the scene already showed, or saying something a second time |
| Blocking | who's where, wearing what and holding what, and anything that contradicts (a jacket that comes off twice) |
| Fact check | every real-world claim, checked on the web, with a source |
| Strength | what the scene already does well (see below) |

They read cold, which just means each one gets a clean copy of the text with no labels and no plan, so it can't be swayed by anyone else's reasoning. They report in a strict 1-line format (the line number, the phrase they're quoting, a category, a short reason), and they never rewrite anything. A single script, `annotation_merge.py`, writes their reports into the file as labels, under the same byte-for-byte contract as the scanner.

## 6. The strength reader

This one's my favorite, and it exists because, well, the other readers were making the prose worse. Every reader hunts problems, so a pass full of fixes tends to sand off the good stuff along with the bad - the violent verb inside a clumsy sentence, the run of short lines that builds to a punchline. The strength reader looks only for what works: the mechanisms that make a stretch hit, the vivid words worth keeping even when a tic is wrapped around them, the jokes, the lines readers will remember.

When a strength and a tic sit on the same line, the verdict's got to name both, so the fix keeps the good word. And a rewrite only goes in if it beats the original, which I check side by side.

## 7. My review

Then it's my turn. I read the labeled draft, and every label gets a verdict inside its brackets - `keep` (it's fine here), `tic` (it's the reflex), `false alarm` (the rule misfired) or `ask` (only I can call it). The verdicts judge, but they don't propose new wording, because how to fix a line is my call.

My review notes are usually pretty short, though. In the case study, my whole review of draft 1 was 1 line, and the AI turned it into a full itemized sweep of the draft.

## 8. Applying it safely

Once I approve a version, a few checks run on the way into the manuscript.
- `apply_check.py` looks for anything a copy-paste leaves behind, like leftover labels, option markers like "(a)" or "(recommended)", stray quote marks, em dashes.
- `preservation_diff.py` lists what the new version dropped from the old one, down to individual lines of dialogue and specific word pairs. A cut can be on purpose, of course, but it's got to actually be on purpose.
- An edit hook in the editor blocks any edit that adds an em dash or a word I've banned outright, before it ever lands in the file.

## 9. Rulings become rules

When I overrule the AI, or make a call I'll want again, it doesn't stay in the chat. Depending on how general it is, it becomes a memory note, a line in the style guide, a new scanner rule, or a pair of test cases (a line the scanner must flag and a line it must leave alone). That's covered in [taste-memory.md](taste-memory.md), and the tests are in [evaluation.md](evaluation.md).

## 10. Keeping track of it all

I'd rather never lose a thing, so 2 smaller tools keep the whole setup safe to experiment in. My editor usually has several AI chats going at the same time, each one working on a different job, so a commit helper ([`tools/tree_triage.py`](../tools/tree_triage.py), with 2 [skills](../skills/README.md) around it) reads the chat transcripts to work out which chat changed which file, and commits only one chat's work at a time. And the [worktree-handoff](https://github.com/cthleung/worktree-handoff) tool carries my unfinished edits between computers, so nothing has to be committed before it's ready.
