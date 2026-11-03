# Why I built it

I honestly don't know anymore if my novel is a writing project or an engineering one. It's a long, character-driven story I've been writing with an AI, about 400,000 words so far, and somewhere along the way it grew its own scanners, review agents, regression tests (for prose, which still makes me laugh), memory files, workflow tools and a one-click installer, so I can sit down at my other computer and pick up right where I left off. CreatorLoop is all of that tooling pulled out of the novel, cleaned up, and written down, so other people can see how it works and why I made it like this.

This doc is the why. The [case study](../case-study/tangerine-drive/README.md) is the how, with 1 scene traced from start to finish.

## The computer I imagined as a kid

As a kid in the 2000s, I used to imagine that one day a computer would be able to make "fuzzy" decisions, the calls people make when there's no right answer, only better and worse ones. I didn't have the words for it then, but Steve Jobs did, and I idolized him for it (obviously): the computer as a bicycle for the mind, a tool that makes a person go further than they could on their own power.

So when LLMs came along, they looked to me like the thing I'd been picturing all along, a harness and a tool that could take a fuzzy, human request and actually do something useful with it. And because I'd been carrying that picture around for so long, I think I was a little ahead of the curve in working out what to do with it. As far as I can tell, very few people write a novel with an AI like I do, and even fewer build their own tooling to make it hold to their taste.

## The first version was at work

The first time I built that for real was at my day job, back in 2023. My team at the bank made an LLM agent that fills in the missing documentation for business datasets, and I'm one of the named inventors on the [patent](https://patents.google.com/patent/US12639279B2/en) it turned into. We split the agent into small steps (planning, pulling in context, generating, then writing it back), partly so each one could be checked on its own, since off-the-shelf agent tooling hadn't really caught up yet, and nothing it wrote counted until a data steward approved it.

Looking back, that's pretty much the loop I run my novel on now, with the machine doing the legwork in steps I can see and a person making the call. I just didn't know yet that I'd end up pointing it at my own creative work.

## Why I trust the tool anyway

The other big influence on me is Pixar. Part of that is storytelling (I've always believed the frivolous can contain the profound, and my novel pretty much runs on that belief), but part of it is what 3D animation did to the form. It lowered the bar, sure, and plenty of lazy work came out of it. It also raised the ceiling far above anything that was possible before, and some of the most incredible sequences I carry around in my head come from 3D animation (the lantern scene in *Tangled*, for one).

I see AI the same way, I think. **It can absolutely make slop, but whether you make slop is a human decision, made by whoever's using it.** Used carefully, it can help a creator tell a story in a way they couldn't have managed alone, and that's the only version of it I'm interested in.

## Why a novel, of all things

My background in storytelling is screenwriting and film analysis, and I'm a photographer and filmmaker on the side (Lightroom and Final Cut Pro, mostly). That being said, when I first sat down with the editing tools, they were hard to pick up blind - I had a strong sense of how a film should look and move, and the tool turned into a bottleneck in my process when it should've been the amplifier. So I put my filmmaking into writing instead. The novel is written like a film in a lot of ways - camera angles, cold opens, music cues, cuts - because that's how I see scenes in my head.

Writing itself was never the hard part. I'm widely read, I used to write a lot, and I've got very specific tastes (and demands, honestly) about what I want from a story and from the prose that tells it. What I'd never taken on was a novel, and this one kept growing. The story in my head turned into about 400,000 words of characters, plot and payoffs, and that's a scale I just can't deliver by hand, least of all for a hobby project that exists purely out of passion.

So that's where I figured AI could come in, as a way to scale up my own creativity. The catch was that everything I cared about lived in the vision, and I had to figure out how to keep that intact while a machine did a lot of the drafting. **Pretty much everything in this repo is my answer to that problem.**

## The problem: it kept forgetting me

The same thing kept happening. The AI would write a draft, and the draft would be clean on paper and dead on the page. The characters lost their voices. The narration explained things the scene already showed, and it invented little numbers and similes to sound precise. I'd fix it, and the next session it would make the same mistakes again, because nothing I'd taught it survived the end of the chat.

So I started writing my taste down where the machine could actually read it. First as a style guide. Then as rules a script could check, then as tests, so that once I'd ruled on something it stayed ruled. Every time I overrode the AI, that override became a case it had to get right from then on. The goal was always to carry my taste forward, so the system is imprinted with it and I don't have to do as much refinement in the future.

The scanners come from pretty specific standards I've got for what good prose sounds like. Most of the AI-isms on that list are things I'd cut from a person's draft too, so the rules are really just my taste written down, and the point was always to bend the model toward it.

## Options, then picks

Oh, and the habit that ended up mattering most is a really simple one. When I'm drafting, I always ask for several options. The AI gives me (a), (b) and (c), and I pick 1, or combine 2, or throw them all out and write my own line. That keeps me in charge of every choice that matters, and it means the AI is constantly learning what I'd pick, from thousands of tiny judgments, without me having to explain my taste up front (which I couldn't, anyway; most of the time I only know it when I see it).

## Keep what works

The rules are there to catch reflexes, but I never wanted them boxing in the style. A rule that fires on every interesting sentence is worse than no rule at all, because it trains the machine to flatten everything into the same safe prose. So the system has a reader whose whole job is to find what a scene already does well (the verb that hits, or a run of sentences that builds to a cut-off), and a fix has to keep those strengths. If a rewrite isn't better than the original, it doesn't go in.

## Never losing work

Creative work is mostly experimenting, and you can't experiment if you're scared of losing what you had. I version everything, and I work across 2 computers, which is where the [worktree-handoff](https://github.com/cthleung/worktree-handoff) tool came from. It started as a small utility because syncing my unfinished work between machines was a pain, but it turned out to be useful enough that I spun it off into its own project. Every unfinished edit travels with me, and nothing gets committed before it's ready. I handed off the committing too, to a couple of skills that read my chat transcripts and sort the changes into commits, since I honestly couldn't be bothered to remember the git for it, and if I can't, a creator definitely won't. That's turned into one of my favorite ideas, [version control you can see and talk to](version-control.md).

## Where this goes

Well, none of this is really about text, when you get down to it. My process for the novel is plan, draft, review what the AI produced, then approve or deny, and the evaluation stuff is there so the system corrects itself and keeps my taste. That loop works for any creative tool.

As a filmmaker, what I'd really want is just the same thing I have in my editor today, which is an agent that operates the computer for me. It'd organize my B-roll, shuffle a timeline toward a specific goal, dig up a sound effect from some vague description I give it, or find a soundtrack insert and work out where and how to cut it in, which are all the little things I already do with my novel, just in a medium where the tool's been the bottleneck so far. As far as I know, an intent-to-execution layer like that is only just starting to show up for photo and video editing, and nothing I've tried works like my writing setup does now. I've written more about that in [beyond-text.md](beyond-text.md).

That's the version of this I'd most like to build next.
