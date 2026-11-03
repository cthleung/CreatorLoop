# Taste memory

Every chat with an AI starts from zero, which is fine for a one-off question and pretty miserable for a novel, especially one where every character has to sound like themselves for hundreds of pages. The whole point of this setup is that a call I make once keeps getting made, by the machine, without me having to make it again. This doc covers where those calls go, and what I'd like to do with them next.

## Where a call goes

Not every call is the same size, so they don't all go to the same place - roughly, from smallest to biggest.

| Where | What goes there | Example from the case study |
|---|---|---|
| The plan's decisions log | A call about this scene only, dated | The ending uses her real reply, "That'd be nice" |
| A memory note | A fact about my taste or the story that should outlive the scene, with the reason and how to apply it | "A stock face now and then is fine" (a smirk here and there keeps the blocking from getting overwritten) |
| The style guide | A general rule about how sentences should work | Delivery similes are out ("casual as suggesting lunch"), so use an adverb |
| A scanner rule | A rule a regex can check | The same simile pattern, flagged automatically from then on |
| A pair of test cases | A line the scanner must flag, and a line it must leave alone | Keeps the rule from drifting the next time anyone touches its regex |
| The reader's gold set | A line I overruled a reader agent on | Goes in as a line that must come back clean |

Memory notes are probably the part people ask about most, so a little more on those. Each one is a small markdown file holding a single fact, with a line on why it matters and a line on how to apply it, plus an index the AI reads at the start of every session. "Seoyun never calls Haeun unnie" is a memory note, and so is the spelling of a Korean interjection. They're tiny on purpose - a note that tries to say everything ends up saying nothing.

## The test pair is the clever bit

When I rule on a scanner rule, it becomes 2 lines in a gold-case file, 1 the scanner must flag and 1 it must leave alone:

```
flag | hedge | She seemed tired.
pass | hedge | "It's kinda making a really good point," she said.
```

The `pass` line is what actually protects my taste. A hedge in narration is a reflex, but the same hedge in a character's own mouth is just how people talk, and without that `pass` line, the next person (or the next AI) to widen the regex would quietly start flagging dialogue again. Every ruling I make on a rule goes into that file, and the test suite runs all of them. Weirdly, it's my favorite file.

## Too many rules is its own problem

I learned this one the hard way. For a while, every correction I made turned into a new rule with examples, and eventually the rules had gotten so tight that the drafts were coming back stiff and over-careful, like the AI was tiptoeing around a minefield. So I just relaxed them. Now the rules are there to catch reflexes I clearly dislike, in broad terms, and my own edits are the target voice. A correction only becomes a rule when it's general, and otherwise it stays a note (or stays in the chat, which is where most of them belong anyway).

## What's next: a proper preference log

Right now most of my picks live in plan files and chat history, which works fine for me but honestly isn't great data. The next step is writing every choice down as its own record, something like this.

```json
{
  "request": "the house question needs a real answer",
  "candidates": [
    {"id": "a", "text": "\"*Mm*.\" / \"Is that a yes?\" / \"*Mm*.\""},
    {"id": "b", "text": "\"*Mm*,\" and nothing else"},
    {"id": "c", "text": "\"Only if I get the room with the big window.\""}
  ],
  "picked": "a",
  "final": "\"*Mm*.\" / \"Is that a yes?\" / \"That'd be nice.\"",
  "reason": "her real reply from the footage",
  "model": "...",
  "prompt_version": "..."
}
```

That's the plan, and none of it exists yet. Once those records pile up, they'd be the data you'd want for teaching a model someone's taste directly.
- **Request to final version** is a supervised example of what I wanted.
- **Picked over not picked** is a preference pair, the raw material for preference tuning.
- **Combined picks** ("(b)'s pacing with (c)'s ending") say which part of each option worked, which a thumbs-up never could.
- **My edits after approval** show how far off the AI still was.

Before any training, the same log could rerank the AI's options so the one I'd probably pick comes first. With enough clean history, a small personal adapter (a LoRA) could learn the habits that show up across every scene, while the memory notes keep handling the rules that change week to week. I'd really want the evals in [evaluation.md](evaluation.md) to decide whether a new adapter actually beats the old setup before I'd trust it with anything.
