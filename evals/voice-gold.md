# Voice gold set (demo)

The blind test for the voice reader (the "ear") is built from this file by `tools/blind_eval.py build`. It's a small demo built from the case study scene. My own gold set for the novel is bigger, and most of its lines can't leave the novel.

- **Pass:** lines that must come back clean. All of these are from the published scene, so I've already approved every one, and they're picked because a "make it plainer" judge would be tempted to flag them (run-ons, jokes, a strange picture).
- **Fail:** lines that must get flagged, with the register they slipped into. None yet. A fail line counts only once I've ruled on it, and I'd rather leave this empty than fill it with lines the AI picked for itself.
- **Unruled:** lines nobody's called yet. These come from draft 1, where only the AI's own self-review flagged them. They aren't scored; the reader's verdict on them gets listed so I can rule.

Format: `- ID | expect | speaker or narrator | allowed register | text`

## Pass

- P01 | pass | Seoyun narration | spoken | Trot was a rhythm game for grandpas, and she was full-comboing it.
- P02 | pass | Seoyun narration | spoken | Every few bends the fog tore open on a canola field so yellow it looked photoshopped, then shut again.
- P03 | pass | Seoyun narration | spoken | People who shook them were animals, and the fun was waiting to see how it came out.
- P04 | pass | Seoyun narration | spoken | Haeun signaled every turn for the benefit of the fog, and in the dark that ticking was the Haeddeong she knew.
- P05 | pass | Seoyun narration | spoken | Something about flowers reminding her of Seoyun. Gross.
- P06 | pass | Seoyun narration | spoken | Maybe it'd been stuck in her hair since last November.
- P07 | pass | Seoyun narration | spoken | Against the black, the window turned into a mirror.
- P08 | pass | Seoyun narration | spoken | The defrost had eaten her potato farm in from the edges until only the roof was left, and past it the fog had thinned to black stone walls going by.
- P09 | pass | Seoyun narration | spoken | Tangerines, and the ocean, and that black rock, and the ocean again, and then tangerines, going round with the song, round again.
- P10 | pass | Seoyun dialogue | spoken | "It's a hassle now," Seoyun said. "Later it's treasure. Write that down."
- P11 | pass | Haeun dialogue | spoken | "If I close mine, we both go off this mountain, and then who sings our parts?"
- P12 | pass | Seoyun dialogue | spoken | "Say that again and there's no pajeon for you tonight."

## Fail

(None yet: these wait on my ruling.)

## Unruled

- U01 | unruled | Seoyun dialogue | spoken | "It's a hassle now," Seoyun said. "Later it's treasure."
- U02 | unruled | Seoyun narration | spoken | She gave it her best face, lip curled up on one side and an eyebrow hiked up to her hairline, then reached up and tilted it at the windshield, where there was nothing to film but fog.
- U03 | unruled | Seoyun narration | spoken | Haeun chewed, and her shoulders came down from around her ears.
- U04 | unruled | Seoyun narration | spoken | Haeun was taking every hairpin so slowly for their sake that Seoyun could have gotten out and walked beside the car.
