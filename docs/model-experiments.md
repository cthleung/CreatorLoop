# Model experiments

The loop doesn't care which model sits in the middle, and I tested that the hard way, by trying to replace Claude with a model I deployed myself. It lost, and it wasn't close. But I learned more about what I actually need from a model than any benchmark had ever told me.

## Why I tried

Most AI prose has a recognizable feel to it, and a lot of my tooling exists to catch it. So I got curious about fine-tunes built to train those habits out - the "de-slopped" creative-writing models, which are basically trying to fix the same problem I'd been fixing with regexes and reader agents, just from the other end. The one I went with was [Gemma 4 Scotoma](https://huggingface.co/ReadyArt/gemma-4-31B-it-scotoma-2), a fine-tune of Google's Gemma 4 31B. It really does write good prose, I'll give it that. And if it could also run inside my editor and keep up with the agent work, I'd have fewer tics to scan for in the first place.

## What I built

I'd tried a couple of hosted inference services first, then ended up serving it myself on Modal with vLLM, which is the version I learned the most from.

- **The model.** An 8-bit weight (W8A16 GPTQ) quantization of the 31B fine-tune, first on an A100-80GB and then on an H100.
- **Context.** Configured for 256K tokens, since a novel's worth of plans, style guides and chapters adds up fast.
- **Serving.** Prefix caching and chunked prefill turned on, plus tool calling, so it could work as an agent and not only a chat box.
- **Memory tuning.** The model has 50 sliding-window layers, and each one reserves KV cache slots for the tokens in flight. At 32,768 batched tokens that needed about 71 GiB at 256K context, so I capped it at 8,192, which brought it down to about 33 GiB and left room for everything else.
- **Cost control.** 1 container only, scaling down after 3 minutes idle, since a second container would've meant paying for a full cold start while requests stalled on it.

Then I pointed my editor at it, so I could switch between it and Claude without changing how I'd been working.

## How I judged it

I didn't run a formal benchmark, but I wasn't flying blind either. The yardstick was my own expectations of what writing with an AI should feel like, and the one I cared about most was time to first token, because I'm drafting live and waiting kills the flow. When the agent helping me deploy it asked for a latency target, I picked under 8 seconds, and that's the number everything else got measured against.

The first real test was rough, though. A plain "hi" took 30.8 seconds to come back, which I told the agent straight out was too long for me, and a normal-sized request from my editor (about 210 KB of prompt, since my setup sends a lot of context) took 82.3 seconds before the first byte arrived. Some of that turned out to be the request waiting in line behind another one, which wasn't the model's fault, so I let the server run 4 at a time, moved to the H100, and turned on chunked prefill. After that, a warm request got its first token in 0.35 seconds for a tiny prompt, 1.26 seconds for a medium one and 7.78 seconds for a 400 KB prompt - just under my target. But warm was the catch. A cold start took about 2 minutes, which isn't nothing, and the server shut down after 3 idle minutes to save money, so any pause to think about a scene meant waiting all over again.

Oh, and one thing I learned about measuring along the way. At one point a benchmark in the chat claimed the H100 had doubled the prompt speed, and a later check found the requests had been hitting the old A100 the whole time, because the new container kept failing to start. So I won't trust a speedup until I know which machine actually answered.

| What I need | Why it matters to me | Gemma 4 Scotoma | Claude in Claude Code |
|---|---|---|---|
| Prose quality | It's a novel, and fewer tics means less cleanup | Good | Good, with my tooling around it |
| Time to first token | I'm drafting live, and my target was under 8 seconds | 0.35 to 7.78 seconds warm, about 2 minutes cold | Fast enough to stay in the flow |
| Context | A chapter plus its plan, the style guide and the memory notes, all at once | Set up for 256K, but I had to cap editor requests at 128K context and 8K output to keep it usable | Fits |
| Cost | It's a personal project, running on $30 of credits | About $2.50 an hour for the A100, and keeping it warm meant paying for idle time | Worth it |
| Working in my editor | The whole loop runs on agents, tools and hooks | HTTP/2 protocol errors while the GPU booted, and agent mode still dragged | Built for it |

Claude won on every one that mattered, so that's where I ended the experiment. That being said, the prose result stuck with me. A model can write better sentences and still be the wrong choice, because the experience around it (how fast it answers, and whether it works with your tools) decides whether you can actually create with it.

## Where this goes next

Swapping out the model turned out to be the wrong move for me. I think the more interesting option is teaching a model my taste directly. My workflow already produces the data for it: every time I pick one option over another, or combine 2, or edit a line after approving it, that's a training example (see [taste-memory.md](taste-memory.md)). Here's the plan, roughly.

1. Log those choices as proper records, which is the next thing I'll build.
2. Use them to rerank the AI's options, so the one I'd probably pick comes first.
3. Once there's enough clean history, train a small LoRA adapter on the approved outputs and the picked-over-not-picked pairs, so the habits that show up across every scene get learned instead of reminded.
4. Try it on a local model on my Mac with MLX, which also tests how much of this can run on the device itself.

And none of it ships into my own workflow until the evals in [evaluation.md](evaluation.md) say it beats what I have now.
