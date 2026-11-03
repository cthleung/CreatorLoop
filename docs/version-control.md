# Version control you can see and talk to

This one started as a pain in my own workflow, and it's turned into the idea I'm probably most excited about. Version tracking has been one of the most important parts of writing my novel with an AI, and the tools I built for it ended up showing me what I'd want from a photo or video app - git's history, made visual, and run by the agent, so a creator never has to type a single command.

## The pain point

My editor usually has several AI chats going at the same time, one fixing a chapter while another polishes a script, and they all write into the same folder. I also switch between a Mac and a Windows PC. So by the end of a day, the working tree's a pile of changes from different jobs on 2 computers, and some of it's finished and some of it really isn't.

Git can untangle that, technically. Staging 1 chat's files and not another's, working out what to do with a file 2 chats touched, moving unfinished work to the other computer without committing it - every one of those is a git command I'd have to look up. I'm a software engineer, but I still couldn't be bothered to remember them. So why would a creator?

## What I built

I stopped typing git myself, and built 3 things that do it for me.

- **[worktree-handoff](https://github.com/cthleung/worktree-handoff)** bundles my unfinished edits into a hidden git ref when a chat closes, and unpacks them when a chat opens on the other computer. Nothing has to be committed before it's ready.
- **[tree-triage](../skills/tree-triage/SKILL.md)** sorts the whole pile. Its script, [`tools/tree_triage.py`](../tools/tree_triage.py), reads every chat transcript to see which chat changed which file since its last commit, and the skill turns that into a plan with 1 commit per job. It flags anything 2 chats touched or that's still unfinished, and it asks before it commits a thing.
- **[session-commit](../skills/session-commit/SKILL.md)** does the same for a single chat. I say "commit this session's work," it shows me the files and the commit message, and I say yes.

These days I don't really type git for the novel at all. I say what I want, and the agent works out the commands, shows me the plan, and runs it once I approve. Now that I think about it, that's the same loop as the writing, just pointed at the history instead of the prose.

## What it taught me

Git's model fits creative work really well. Each commit is a decision plus the outcome it produced, and if you use it right, each one's atomic, so you can take back 1 decision without losing everything that came after it. A branch is just an option you haven't picked yet. My style rules and memory notes live in git too, so when I take back a ruling, reverting its commit takes the rule and its test pair with it, and my preferences get the same version control as the prose.

The catch is "if you use it right." Nobody commits at the size of a single decision by hand, and I'm no exception. The remaster that holds the [tangerine drive](../case-study/tangerine-drive/README.md) went into git as 1 commit. The [replay](../demo/index.html) only exists because the plan file kept every draft next to my dated decisions, and the chat transcripts kept my words. But an agent doesn't have that problem. It can commit once per approved step, every time, and use my request and my verdict as the message. That's the history I'd want, and the discipline I'd never keep up myself.

## For every other creator

A creator's got the same gap between intent and execution that I had with git, except it's everywhere in the app. They know the reveal needs to come later, and the gap is all the panels and menus between that and the result. My answer for the novel was an agent that does the operating, and I'd want the same thing for the history, with 2 ways into it.

- **A picture for looking.** The session as a graph of decisions, each with a frame you can actually see, and the options as branches. Nobody reads a commit log to decide whether a grade's right.
- **A conversation for doing.** The creator says what they want, and the agent runs the git underneath.

| The creator says | What the agent does |
|---|---|
| "Go back to before the hallway, but keep the music change." | Reverts 1 commit and keeps the later ones |
| "Try a warmer grade without touching my cut." | Makes a branch |
| "Show me yesterday's version next to this one." | A diff, rendered as 2 previews |
| "What's changed since the client saw it?" | The log since a tag, summed up in plain words |
| "Forget the room-tone thing, that was for 1 scene." | Reverts the preference and keeps the edits |

It's buildable, too. A timeline's already text underneath (Final Cut can export one as FCPXML), and a photo edit is just a list of settings, so git can track what changed without ever touching the media. Claude Code already lets me rewind a session to before a change, and I'd want that for a timeline, with the preferences rewinding along with it.

The rules from my skills carry straight over. The agent shows what it's about to do to the history before it does it, it never rewrites anything another session or another person is still using without asking, and abandoned branches stay around, since a rejected option is a boundary worth remembering.

## Where the industry is

The first editing agents are only just showing up in pro apps as I write this (November 2026). From what I can tell, they record their steps in the app's ordinary undo stack as a single line (Premiere's assistant logs its actions in the same undo and history stacks as everything else, according to [Adobe's docs](https://helpx.adobe.com/premiere/desktop/premiere-ai-assistant/overview.html)). There are git-for-video experiments like [Vit](https://github.com/LucasHJin/vit) for DaVinci Resolve, and research on [creative version control](https://ssterman.web.illinois.edu/assets/pdfs/towards_creative_version_control.pdf), but I haven't found anything that shows an agent session as decisions you can see, branch, take back 1 at a time and talk to.

That's the piece I'd most like to build. Steps 5 to 7 of the [edit-suite concept](../demo/edit-suite.html#step-5) show what it'd look like.
