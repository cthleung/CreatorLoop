# Beyond text

Nothing in the loop is really about prose. My process for the novel is plan, draft, review what the AI produced, then approve or deny, and that works for any creative tool where an AI could do the hands-on part while a person keeps the taste. Photo and video editing are the 2 I care about most, since I shoot and edit myself (and when I first picked up Final Cut blind, it turned into a bottleneck in my process when it should've been the amplifier, which is a big part of why an agent that knows the tools inside out sounds so good to me).

This doc is how I'd carry the loop over. None of it's built yet, so the examples below are just illustrations, but every piece of it maps onto something that already works for me in text.

## The same loop, in a different medium

Stripped down, what I do with the novel looks something like this.

```
intent -> options -> I choose or combine -> execute on a recoverable version
       -> compare -> approve or restore -> remember the choice
```

The medium changes, but the control loop carries over pretty much as is. That being said, the interesting part was never the model writing a sentence - it's that I get to stay the one deciding, while the machine does the legwork and slowly learns what I'd decide.

| In my writing setup | In a photo or video app |
|---|---|
| Scene outline and plan | Shoot brief, storyboard or rough-cut plan |
| Character voices and the style guide | My visual language, pacing habits and the project's mood |
| Lettered options for a line | A few alternate grades, crops or cuts, previewed side by side |
| The draft | A proposed set of edits, applied on a copy |
| Inline labels and the side by side | Before and after previews, plus a list of every change |
| My review and verdicts | Accept, tweak, disable or revert each edit |
| The scanner | Objective checks (clipped highlights, broken audio sync, loudness, export settings) |
| The strength reader | A check that protects what I did on purpose |
| The ear | "Does this look and move like something I'd make?" |
| Taste memory | Approved and rejected edits, kept with the context they were made in |

## An assistant editor with hands

As a filmmaker, what I want is the thing I already have in my code editor - an agent that operates the computer for me. I put my filmmaking into writing because the editing tools were hard to pick up blind, even with a clear picture of the film in my head, and I'd bet a lot of creators are in the same spot: they know what a scene should feel like, but the gap is all the panels/commands/menus between that and the result. That gap, as far as I'm concerned, is the job.

The first useful mode is assistant-editor work, which is really just the stuff nobody got into filmmaking to do.
- Organizing B-roll by scene, subject and what each clip is good for.
- Syncing audio, marking technical problems and pulling selects.
- Searching footage from a vague description ("the empty hallway, before anyone walks in").
- Finding a sound effect or a soundtrack insert from a description, and working out where and how to cut it in.
- Shuffling a timeline toward a specific goal, on a copy.

Then it'd become a collaborator. Say I tell it the reveal's happening too early, so hold her face back, open on the empty hallway, and let the door sound carry across the cut. It shouldn't just go and do it, though. It's got to come back with a plan first.

1. Duplicate the current timeline.
2. Move the close-up later.
3. Insert 2 candidate hallway shots.
4. Extend the room tone under the transition.
5. Keep the dialogue in sync, and render a preview with every change listed.

Then I approve the hallway insert, put the close-up back where it was, and stretch the room tone further than it suggested. Every one of those calls is information about my taste, and that's what I'd want it to keep. That's the part that makes the next request go better, and honestly, it's how a scene already goes with my novel today, just with a timeline in place of a paragraph and a lot more rendering.

## Options as previews

The habit that matters most in my writing is asking for options and picking 1, or combining 2, because I recognize what I want long before I can explain it. I think that works even better with images. Show me 3 grades of the same frame, or 3 cuts of the same 20 seconds (side by side, playing at the same time), and I'll know in a glance which one's right, or that I want the pacing from the second with the music entrance from the third.

A pick like that says way more than a thumbs up ever could. "B over A" is a preference. "B's pacing with C's music" says which part of each option worked. And when I take an approved edit and adjust it by hand afterward, the size of that adjustment says how far off the agent still was.

## What taste memory has to keep

For text, my taste lives in rules, memory notes and test cases, but for photo and video, every interaction should keep enough context to be useful later.
- The project and the feeling it's going for.
- The image or the timeline as it was before the edit.
- What the agent proposed, and the preview I actually judged.
- What I approved, what I rejected, and what I changed by hand afterward.
- Any reason I gave, and what I finally exported.

Approved edits become examples, and rejected ones become boundaries, which is really the same split as my pass and fail lines. Most of the personalization can come from retrieval before any training happens - when I'm grading a concert photo, the agent pulls up my earlier concert decisions, the same way my writing setup pulls up a character's voice card before a scene.

Taste's got modes, too. How I'd treat a portrait probably isn't how I'd treat documentary footage, where noise and awkward framing might be the whole point, so an agent that averages everything into a single "Charles preset" would get both wrong. My novel already works this way, since every narrator's got their own voice card and each chapter licenses its own registers.

## Checks before I ever look

A lot of what my scanner does has a direct equivalent in an edit suite, and it's the boring, objective stuff a machine should catch before a person spends any attention on it.
- **Photo:** Clipped channels, damaged skin texture, mask edges leaking past the subject, white balance drifting between shots in a set, export settings.
- **Video:** Broken audio sync, loudness, duplicate or dropped frames, continuity slips, delivery settings.

Taste stays with me, of course. What the checks buy is that when I sit down to judge something, I'm judging the creative call and not hunting for a clipped highlight.

## Keep what works, for pictures

On that note, the tool I'd miss most is the strength reader, the agent whose only job is to find what a draft already does well so the fixes don't flatten it. Editing needs the same protection, maybe even more, because "fix everything" in a photo app means smoothing every texture, denoising every shadow and straightening every horizon. Sometimes the grain's the point. Sometimes the crooked frame is what makes the shot feel lived in (ask anyone who's shot street photography). An agent that knows what I'd done on purpose, and just leaves it alone, is worth more to me than one that's technically better at denoising.

## Versions are the safety net, and the training data

Honestly, a timeline's a lot easier to wreck than a paragraph. So every agent edit should land on a copy or a new version, never on the working cut, and I should always be able to compare versions and go back. That's the same instinct behind my [handoff tool](https://github.com/cthleung/worktree-handoff), just applied inside the app, and if every edit can be undone, I can let the agent try bolder things.

The version history ends up doing a second job, too. Every version I kept, every one I abandoned, and every manual fix between them is a record of what I wanted, so the creator's version history turns into the training history.

And a creator shouldn't have to learn git to get any of this. I don't type git for my novel anymore (a couple of skills do it for me, from plain requests), so I'd want the history to be something you look at as frames and talk to in plain words. I've written that up in [version-control.md](version-control.md).

## Training the decisions before the pixels

If I were teaching a model my editing taste, I'd start with the agent's decisions and leave image generation for later. The app still does the actual cutting and grading, which it's already great at anyway, and the model learns which operations to propose and in what order. A training example would look something like this.

```
Input:      my request, the transcript and clip notes, the current timeline,
            any reference frames, and what's in my taste memory
Preferred:  the clips, edits, music placement and tool calls I approved
Rejected:   the alternative plan I turned down
```

That's the same shape as the preference data my writing loop's already producing (see [taste-memory.md](taste-memory.md)), and it'd support the same steps. Retrieval and reranking come first, since they work from day 1 (no training needed). I'd add a small adapter (a LoRA) later, once there's enough clean history for it to learn the habits that show up across every project, like preferring a longer reaction shot or a quiet music entrance. And versioned evals decide whether a new adapter actually beats the old setup before it touches real work, which is the lesson from [model-experiments.md](model-experiments.md): a model can be better on paper and still be the wrong experience.

## What I'd measure

The numbers I'd watch are the same ones from [evaluation.md](evaluation.md), translated - most of them come straight out of the preference log.
- How often I accept the agent's edit as is, by kind of edit.
- How much I adjust an edit after accepting it.
- Which kinds of edit I keep undoing.
- How stable the agent's proposals are when it gets the same request twice.
- How often its own self-review agrees with my final call.
- Whether the same correction stops coming back over time.

That last one's still the one that really matters, I think. If I've told it once that I like room tone carried across a cut, I shouldn't have to tell it again on the next project.
