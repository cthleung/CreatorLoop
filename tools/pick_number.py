#!/usr/bin/env python3
"""Pick random numbers for prose, so nobody invents them by reflex.

AI drafts love inventing oddly specific numbers ("seventeen minutes," "7:42 AM"), and they land
on 4s and 7s far too often. When a scene really needs a number, I pick it with this instead,
and a number it picked counts as counted.

The output copies the format of the range you type in:
  plain numbers   15 40, 20,000 90,000, 1.5 3.0
  timers          00:55.00 01:45.00 (M:SS, MM:SS.cc, H:MM:SS.ffffff)
  clock times     22:00 23:30 --clock, or 9:00am 11:30am (AM/PM turns on --clock)

Rounding (pick one, or neither for plain precision):
  --step S   land on multiples of S (units: plain number, seconds for timers,
             minutes for clock times)
  --sig N    keep N significant figures

Precision comes from the decimals in the range (00:55.31 means hundredths).
--dp overrides it, e.g. --dp 6 for microseconds.

Examples:
  python3 tools/pick_number.py 15 40 --step 5 --for "minutes she waited"
  python3 tools/pick_number.py 20,000 90,000 --sig 1 --count 3
  python3 tools/pick_number.py 00:55.00 01:45.00 --for "the stopwatch"
  python3 tools/pick_number.py 9:00am 10:30am --step 5 --log "number log.md"

--log PATH appends every pick to a markdown log, with what it was for.
With --count above 1, results come out in the order they were drawn, unsorted,
so the first one is as random as the rest.
"""
import argparse
import random
import re
import sys
from datetime import datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

TIME_RE = re.compile(r"^(\d+):(\d{1,2})(?::(\d{1,2}))?(?:\.(\d+))?$")
AMPM_RE = re.compile(r"\s*([ap])\.?m\.?$", re.IGNORECASE)
rng = random.SystemRandom()


def fail(msg):
    sys.exit(f"pick_number: {msg}")


def parse(text, clock):
    """Turn one end of the range into (value, shape). Shape records the format to copy."""
    raw = text.strip()
    ampm = AMPM_RE.search(raw)
    if ampm:
        clock = True
        raw = raw[: ampm.start()].strip()
        if ":" not in raw:
            raw += ":00"
    m = TIME_RE.match(raw)
    if m:
        a, b, c, frac = m.groups()
        if clock:
            if c is not None or frac:
                fail(f"clock times are H:MM, got {text!r}")
            hour = int(a)
            if ampm:
                if not 1 <= hour <= 12:
                    fail(f"bad 12-hour time {text!r}")
                hour = hour % 12 + (12 if ampm.group(1).lower() == "p" else 0)
            return Decimal(hour * 60 + int(b)), {"kind": "clock", "pad": len(a), "dp": 0, "ampm": bool(ampm)}
        if c is not None:
            secs, parts = int(a) * 3600 + int(b) * 60 + int(c), 3
        else:
            secs, parts = int(a) * 60 + int(b), 2
        value = Decimal(secs) + (Decimal("0." + frac) if frac else 0)
        return value, {"kind": "timer", "parts": parts, "pad": len(a), "dp": len(frac or "")}
    if clock:
        fail(f"clock times are H:MM, got {text!r}")
    num = raw.replace(",", "")
    try:
        value = Decimal(num)
    except InvalidOperation:
        fail(f"can't read {text!r} as a number or time")
    dp = len(num.split(".")[1]) if "." in num else 0
    return value, {"kind": "number", "commas": "," in raw, "dp": dp}


def merge(a, b):
    if a["kind"] != b["kind"]:
        fail("both ends of the range need the same format")
    shape = dict(a)
    for key in ("pad", "dp", "parts"):
        if key in a:
            shape[key] = max(a[key], b[key])
    for key in ("commas", "ampm"):
        if key in a:
            shape[key] = a[key] or b[key]
    return shape


def pick_on_grid(low, high, step):
    lo_k = (low / step).to_integral_value(ROUND_CEILING)
    hi_k = (high / step).to_integral_value(ROUND_FLOOR)
    if lo_k > hi_k:
        fail(f"no multiple of {step} between the two ends of the range")
    return rng.randint(int(lo_k), int(hi_k)) * step, int(hi_k - lo_k + 1)


def round_sig(x, sig):
    if x == 0:
        return x
    return x.quantize(Decimal(1).scaleb(x.adjusted() - sig + 1), ROUND_HALF_UP)


def decimals_of(x):
    return max(0, -x.normalize().as_tuple().exponent)


def fmt(value, shape, dp):
    kind = shape["kind"]
    if kind == "number":
        return f"{value:,.{dp}f}" if shape["commas"] else f"{value:.{dp}f}"
    if kind == "clock":
        h, m = divmod(int(value) % 1440, 60)
        if shape["ampm"]:
            return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"
        return f"{h:0{shape['pad']}d}:{m:02d}"
    whole = int(value)
    h, rest = divmod(whole, 3600)
    m, s = divmod(rest, 60)
    if shape["parts"] == 3 or h:
        out = f"{h:0{shape['pad']}d}:{m:02d}:{s:02d}"
    else:
        out = f"{m:0{shape['pad']}d}:{s:02d}"
    if dp:
        out += "." + f"{value - whole:.{dp}f}"[2:]
    return out


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
SCALES = ((10**9, "billion"), (10**6, "million"), (1000, "thousand"))


def words_int(n):
    if n < 0:
        return "minus " + words_int(-n)
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t] + (f"-{ONES[o]}" if o else "")
    if n < 1000:
        h, r = divmod(n, 100)
        return f"{ONES[h]} hundred" + (f" {words_int(r)}" if r else "")
    for size, name in SCALES:
        if n >= size:
            q, r = divmod(n, size)
            return f"{words_int(q)} {name}" + (f" {words_int(r)}" if r else "")


def words(text):
    whole, _, frac = text.replace(",", "").partition(".")
    out = words_int(int(whole))
    if frac:
        out += " point " + " ".join(ONES[int(d)] for d in frac)
    return out


def write_log(log, label, low, high, rounding, results):
    new = not log.exists()
    with log.open("a", encoding="utf-8") as f:
        if new:
            f.write("# Number log\n\n"
                    "Numbers picked by `tools/pick_number.py`. A number in this log "
                    "counts as counted, 4s and 7s included.\n\n"
                    "| When | For | Range | Rounding | Result |\n|---|---|---|---|---|\n")
        cells = [datetime.now().strftime("%Y-%m-%d %H:%M"), label, f"{low} to {high}", rounding, ", ".join(results)]
        f.write("| " + " | ".join(c.replace("|", "/") for c in cells) + " |\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("low")
    p.add_argument("high")
    p.add_argument("-n", "--count", type=int, default=1, help="how many numbers (default 1)")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--step", help="round to multiples of this")
    group.add_argument("--sig", type=int, help="significant figures")
    p.add_argument("--dp", type=int, help="decimal places, overrides what the range implies")
    p.add_argument("--clock", action="store_true", help="read H:MM as a time of day")
    p.add_argument("--words", action="store_true", help="also spell plain numbers out")
    p.add_argument("--for", dest="label", default="-", help="what the number is for, goes in the log")
    p.add_argument("--log", help="append each pick to this markdown log")
    args = p.parse_args()

    low, s1 = parse(args.low, args.clock)
    high, s2 = parse(args.high, args.clock)
    shape = merge(s1, s2)
    if shape["kind"] == "clock" and high < low:
        high += 1440  # range runs past midnight
    if high < low:
        low, high = high, low
    dp = args.dp if args.dp is not None else shape["dp"]
    base = Decimal(1).scaleb(-dp)

    results, seen = [], set()
    if args.step:
        step = Decimal(args.step)
        if step <= 0:
            fail("--step has to be above zero")
        dp = max(dp, decimals_of(step))
        _, size = pick_on_grid(low, high, step)
        if size < args.count:
            fail(f"only {size} distinct values in that range at that step")
        rounding = f"step {args.step}"
        draw = lambda: pick_on_grid(low, high, step)[0]
    elif args.sig:
        if args.sig < 1:
            fail("--sig has to be 1 or more")
        rounding = f"{args.sig} sig fig{'s' if args.sig > 1 else ''}"

        def draw():
            for _ in range(1000):
                x = round_sig(pick_on_grid(low, high, base)[0], args.sig)
                if low <= x <= high:
                    return x
            fail("couldn't find a value at that many sig figs inside the range")
    else:
        _, size = pick_on_grid(low, high, base)
        if size < args.count:
            fail(f"only {size} distinct values in that range")
        rounding = f"{dp} dp" if dp else "whole"
        draw = lambda: pick_on_grid(low, high, base)[0]

    for _ in range(args.count * 200):
        x = draw()
        if x not in seen:
            seen.add(x)
            places = max(0, -x.as_tuple().exponent) if args.sig else dp
            results.append(fmt(x, shape, places))
        if len(results) == args.count:
            break
    if len(results) < args.count:
        found = len(results)
        print(f"pick_number: only found {found} distinct value{'s' if found > 1 else ''}", file=sys.stderr)

    for r in results:
        print(f"{r}  ({words(r)})" if args.words and shape["kind"] == "number" else r)
    if args.log:
        write_log(Path(args.log), args.label, args.low, args.high, rounding, results)


if __name__ == "__main__":
    main()
