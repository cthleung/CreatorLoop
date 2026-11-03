#!/usr/bin/env python3
"""
local_reader.py: run a reader agent's brief on a local model with MLX, several times over.

This is the on-device version of a reader run. It takes the reader's instructions (1 or more
brief files, joined in the order given) and a blind test from tools/blind_eval.py, asks a local
model for its flags N times with seeds seed, seed+1, ..., and writes:

    runK.md       only the well-formed flag lines (L<n> | ...), so tools/eval_stats.py can read it
    runK.raw.txt  everything the model said, for checking what the filter dropped
    timing.json   per run: prompt tokens, time to first token, total seconds, generated tokens,
                  tokens per second and peak memory

The blind file goes in with its line numbers at the start of each line, matching what an agent sees in a
file it reads, so the model can report the file's own line numbers. Any thinking block the model
writes is dropped before the filter, so draft flags in its reasoning don't count.

MLX only runs on Apple Silicon, so it's imported inside run(). Everything else works anywhere.

Usage:
    python3 tools/local_reader.py --model mlx-community/gemma-4-12B-it-4bit \\
        --brief agent.md guide.md --blind DIR/blind.md --runs 5 --temp 0.7 --seed 1 --thinking off \\
        --out DIR/local
"""

import argparse
import json
import os
import re
import sys
import time

FLAG_RE = re.compile(r"^L(\d+)\s*\|\s*\S")
LEAD_RE = re.compile(r"^[\s`>*-]+")
THINK_RE = re.compile(r"<think>.*?(</think>|$)|<\|channel>.*?(<channel\|>|$)", re.S)

BLIND_INTRO = ("The file to read follows. Each line starts with its line number and a tab, "
               "and the number isn't part of the text.")


def read_briefs(paths):
    """The brief files' text, joined in the order given."""
    parts = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            parts.append(f.read().strip())
    return "\n\n".join(parts) + "\n"


def number_lines(text):
    """Every line with its 1-based line number and a tab in front."""
    return "\n".join(f"{i}\t{line}" for i, line in enumerate(text.splitlines(), 1))


def build_messages(brief, blind_text):
    """The chat: the brief as the system turn, the numbered blind file as the user turn."""
    return [{"role": "system", "content": brief},
            {"role": "user", "content": BLIND_INTRO + "\n\n" + number_lines(blind_text)}]


def render_prompt(tokenizer, messages, thinking="auto"):
    """The prompt string from the tokenizer's own chat template. thinking "on" or "off" sets the
    template's enable_thinking switch, and "auto" leaves the tokenizer's default. A template that
    rejects a system turn gets the brief at the top of the user turn instead."""
    kw = {} if thinking == "auto" else {"enable_thinking": thinking == "on"}
    try:
        return tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False, **kw)
    except Exception:
        merged = [{"role": "user", "content": messages[0]["content"] + "\n\n" + messages[1]["content"]}]
        return tokenizer.apply_chat_template(merged, add_generation_prompt=True, tokenize=False, **kw)


def keep_flags(text):
    """The well-formed flag lines in a reply, with list bullets and code ticks taken off the front.
    Thinking blocks, tallies, headings and chatter are dropped."""
    text = THINK_RE.sub("", text)
    out = []
    for line in text.splitlines():
        line = LEAD_RE.sub("", line).rstrip().rstrip("`").rstrip()
        if FLAG_RE.match(line):
            out.append(line)
    return out


def line_numbers(flags):
    """The line numbers the flags point at."""
    return sorted({int(FLAG_RE.match(f).group(1)) for f in flags})


def run(model, briefs, blind, runs=5, temp=0.7, seed=1, max_tokens=2048, out="local_runs", thinking="auto",
        log=print):
    import mlx.core as mx
    from mlx_lm import load, stream_generate
    from mlx_lm.sample_utils import make_sampler

    os.makedirs(out, exist_ok=True)
    with open(blind, encoding="utf-8") as f:
        messages = build_messages(read_briefs(briefs), f.read())
    t0 = time.perf_counter()
    mdl, tok = load(model)
    load_s = time.perf_counter() - t0
    prompt = render_prompt(tok, messages, thinking)
    timing = {"model": model, "temp": temp, "max_tokens": max_tokens, "thinking": thinking, "load_seconds": round(load_s, 2), "runs": []}
    for k in range(runs):
        s = seed + k
        mx.random.seed(s)
        mx.reset_peak_memory()
        text, first, last = [], None, None
        start = time.perf_counter()
        for resp in stream_generate(mdl, tok, prompt, max_tokens=max_tokens, sampler=make_sampler(temp=temp)):
            if first is None:
                first = time.perf_counter() - start
            text.append(resp.text)
            last = resp
        total = time.perf_counter() - start
        reply = "".join(text)
        flags = keep_flags(reply)
        name = f"run{k + 1}"
        with open(os.path.join(out, name + ".md"), "w", encoding="utf-8") as f:
            f.write("\n".join(flags) + ("\n" if flags else ""))
        with open(os.path.join(out, name + ".raw.txt"), "w", encoding="utf-8") as f:
            f.write(reply)
        row = {"run": name, "seed": s, "prompt_tokens": last.prompt_tokens if last else 0,
               "ttft_seconds": round(first or 0.0, 2), "total_seconds": round(total, 2),
               "generated_tokens": last.generation_tokens if last else 0,
               "tokens_per_second": round(last.generation_tps, 2) if last else 0.0,
               "prompt_tokens_per_second": round(last.prompt_tps, 2) if last else 0.0,
               "peak_memory_gb": round(last.peak_memory, 2) if last else 0.0,
               "finish_reason": last.finish_reason if last else None,
               "flags": len(flags), "lines": line_numbers(flags)}
        timing["runs"].append(row)
        log(f"{name}: seed {s}, {row['flags']} flags, {row['total_seconds']}s, TTFT {row['ttft_seconds']}s")
    with open(os.path.join(out, "timing.json"), "w", encoding="utf-8") as f:
        json.dump(timing, f, indent=1)
    return timing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="an MLX model id or local path")
    ap.add_argument("--brief", nargs="+", required=True, help="instruction files, joined in this order")
    ap.add_argument("--blind", required=True, help="the blind test file")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--temp", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=1, help="the first seed; run K uses seed + K - 1")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--out", default="local_runs")
    ap.add_argument("--thinking", choices=("auto", "on", "off"), default="auto",
                    help="turn the model's thinking mode on or off; auto keeps the tokenizer's default")
    a = ap.parse_args(argv)
    run(a.model, a.brief, a.blind, a.runs, a.temp, a.seed, a.max_tokens, a.out, a.thinking)
    return 0


if __name__ == "__main__":
    sys.exit(main())
