#!/usr/bin/env python3
"""
tree_triage.py: sort a working tree that several AI chat sessions edited at once.

When a few Claude Code sessions work in the same repo side by side, their changes pile up in
one working tree, and nobody remembers which chat touched what. This reads every session
transcript for the repo, works out which session edited each dirty file, and prints a plan for
scoped commits. It never stages or commits anything.

How a file gets credited: every Edit / Write / MultiEdit / NotebookEdit call, and every Bash
command that names the file and rewrites files (sed -i, mv, cp, a redirect, a Python write),
counts for the session that made it, as long as it came after the file's last commit. Fork
sessions copy their parent's history, so a tool call that shows up in several transcripts goes
to the earliest session. Subagent transcripts count for the session that launched them.

For each dirty file it also checks:

    quotes-only   the file matches HEAD once curly quotes are straightened. These go in one
                  commit of their own
    gate          hard-rule hits from tools/rule_engine.py in the lines a .md file ADDED
    markers       [?? gaps, TODO / TBD / FIXME and merge conflict markers left in a .md file.
                  "new" means the count went up since HEAD

The plan: the quotes-only batch, one block per session, files more than one session edited,
files no session edited (hand edits, scripts, or sessions too old to read), and SpecStory logs.

Transcripts are read from ~/.claude/projects/<key>, where the key is the repo's absolute path
with every character that isn't a letter or a digit turned into "-".

Usage:
    python3 tools/tree_triage.py                     # the plan for the repo you're in
    python3 tools/tree_triage.py --repo PATH         # another repo
    python3 tools/tree_triage.py --json              # the same data for other scripts
    python3 tools/tree_triage.py --diffs             # also show +/- line counts
    python3 tools/tree_triage.py --session           # only this chat's files (or --session ID_OR_NAME)
    python3 tools/tree_triage.py --transcripts DIR   # read transcripts from another folder
"""

import argparse
import functools
import glob
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime

sys.dont_write_bytecode = True
CODE_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CODE_HOME)
try:
    from tools import rule_engine as _engine
    HARD_RULES = [r for r in _engine.compile_rules() if r["level"] == "hard"]
    scan_line = _engine.scan_line
except Exception:  # the gate is a convenience here, never a requirement
    HARD_RULES, scan_line = [], None

ROOT = ""        # the repo being sorted, set by set_root()
ROOT_FORMS = ()  # ROOT as given and with symlinks resolved, in the form fold() makes

QUOTE_TABLE = str.maketrans({c: "'" for c in "\u2018\u2019\u201a\u201b\u2032"}
                            | {c: '"' for c in "\u201c\u201d\u201e\u201f\u2033"})
CURLY = "".join(chr(c) for c in QUOTE_TABLE)
MARKER_RE = re.compile(r"\[\?\?|\bTODO\b|\bTBD\b|\bFIXME\b|^<{7} |^>{7} |^={7}\r?$", re.M)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
MCP_EDIT_TOOLS = {"mcp__filesystem__write_file", "mcp__filesystem__edit_file"}
# Bash commands that rewrite files without an Edit call. <F> stands for the dirty file's own
# name. cp counts because sessions often back a file up right before rewriting it with a script.
_TARGET = r"(?:\"[^\"]*|'[^']*|[^\s\"'|;&<>]*)<F>"
MUTATORS = [(label, re.compile(rx)) for label, rx in (
    ("sed -i", r"\bsed\b[^|;&]*?\s-[a-zA-Z]*i"),
    ("perl -i", r"\bperl\b[^|;&]*?\s-[a-zA-Z]*i"),
    ("git mv/rm/checkout/restore", r"\bgit\s+(?:mv|rm|checkout|restore)\b"),
    ("mv", r"\bmv\s"),
    ("rm", r"\brm\s"),
    ("cp", r"\bcp\s"),
    ("python write", r"\.write\(|write_(?:text|bytes)\(|open\(.*?['\"][wa]b?\+?['\"]"),
    ("redirect", r">>?\s*" + _TARGET),
    ("tee", r"\btee\s+(?:-a\s+)?" + _TARGET),
)]
# what may sit right before a path in a shell command: a space, a quote, = ( : or a shell operator
_PATH_START = set(" \t\n\"'=(:<>|;&`")


def fold(path):
    """A path in the form used for comparing: normalized, and lowercased on Windows."""
    return os.path.normcase(os.path.normpath(path))


def set_root(path=None):
    """Point the tool at the git repo that holds PATH (default: the current folder)."""
    global ROOT, ROOT_FORMS
    start = os.path.abspath(path or os.getcwd())
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True)
    if r.returncode:
        raise SystemExit(f"tree_triage: {start} isn't inside a git repo")
    ROOT = os.path.normpath(r.stdout.decode("utf-8", "replace").strip())
    ROOT_FORMS = tuple(dict.fromkeys(fold(p) for p in (ROOT, os.path.realpath(ROOT))))
    return ROOT


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if check and r.returncode:
        raise SystemExit(r.stderr.decode("utf-8", "replace"))
    return r.stdout if r.returncode == 0 else b""


def short_status(code):
    """Git's 2-letter porcelain code as 1 letter: ? untracked, A added, D deleted, R renamed,
    U unmerged, M everything else."""
    if code == "??":
        return "?"
    if "U" in code or code in ("AA", "DD"):
        return "U"
    if "D" in code:
        return "D"
    if code[0] in "RC":
        return "R"
    return "A" if "A" in code else "M"


def dirty_files():
    """[(status, path)] from porcelain -z. Renames report the new path."""
    out = git("status", "--porcelain=v1", "-z", "-uall").decode("utf-8", "replace").split("\0")
    files, i = [], 0
    while i < len(out):
        e = out[i]
        i += 1
        if len(e) < 4:
            continue
        code, path = e[:2], e[3:]
        if code[0] in "RC":
            i += 1  # skip the old name
        files.append((short_status(code), path))
    return files


def last_commit_time(path):
    """When the file was last committed, or 0 if it never was (or the repo has no commits)."""
    out = git("log", "-1", "--format=%ct", "--", path, check=False).decode().strip()
    return int(out) if out.isdigit() else 0


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def project_key(path):
    """Claude Code's folder name for a project: anything that isn't a letter or digit becomes '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def project_dir():
    base = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"), "projects")
    for form in (ROOT, os.path.realpath(ROOT)):
        d = os.path.join(base, project_key(form))
        if os.path.isdir(d):
            return d
    return os.path.join(base, project_key(ROOT))


@functools.lru_cache(maxsize=None)
def _real(path):
    return os.path.realpath(path)


def _inside(path):
    low = os.path.normcase(path)
    for root in ROOT_FORMS:
        if low.startswith(root + os.sep):
            return path[len(root) + 1:].replace(os.sep, "/")
    return None


def rel(path, cwd=None):
    """A path from a transcript as a repo path with forward slashes, or None if it's outside."""
    if not path or not isinstance(path, str):
        return None
    if not os.path.isabs(path):
        path = os.path.join(cwd or ROOT, path)
    path = os.path.normpath(path)
    return _inside(path) or _inside(_real(path))


def read_session(path):
    """-> (meta, events). An event is (tool_use_id, ts, kind, payload)."""
    meta = {"title": None, "custom": None, "agent": None, "last_prompt": None, "start": None}
    events = []
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        for line in fh:
            wanted = ("tool_use" in line or '"ai-title"' in line or '"custom-title"' in line
                      or '"agent-name"' in line or '"last-prompt"' in line)
            if meta["start"] is not None and not wanted:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if not isinstance(o, dict):
                continue
            ts = parse_ts(o["timestamp"]) if isinstance(o.get("timestamp"), str) else 0.0
            if ts:
                meta["start"] = ts if meta["start"] is None else min(meta["start"], ts)
            t = o.get("type")
            if t == "ai-title":
                meta["title"] = o.get("aiTitle")
            elif t == "custom-title":
                meta["custom"] = o.get("customTitle")
            elif t == "agent-name":
                meta["agent"] = o.get("agentName")
            elif t == "last-prompt":
                meta["last_prompt"] = o.get("lastPrompt")
            elif t == "assistant":
                content = (o.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                cwd = o.get("cwd")
                for b in content:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name, inp, tid = b.get("name"), b.get("input") or {}, b.get("id")
                    if name in EDIT_TOOLS:
                        p = rel(inp.get("file_path") or inp.get("notebook_path"), cwd)
                        if p:
                            events.append((tid, ts, "edit", p))
                    elif name in MCP_EDIT_TOOLS:
                        p = rel(inp.get("path"), cwd)
                        if p:
                            events.append((tid, ts, "edit", p))
                    elif name == "Bash":
                        events.append((tid, ts, "bash", inp.get("command") or ""))
    return meta, events


def load_sessions(folder=None):
    """{session id: meta with its events}, for every transcript in the folder."""
    folder = folder or project_dir()
    sessions = {}
    if not os.path.isdir(folder):
        return sessions
    for f in sorted(glob.glob(os.path.join(folder, "*.jsonl"))):
        sid = os.path.basename(f)[:-6]
        meta, events = read_session(f)
        # subagent transcripts belong to the session that launched them
        for sub in sorted(glob.glob(os.path.join(folder, sid, "subagents", "*.jsonl"))):
            events += read_session(sub)[1]
        meta["events"] = events
        sessions[sid] = meta
    return sessions


def session_label(sid, meta):
    name = meta.get("custom") or meta.get("agent") or meta.get("title") or "(untitled)"
    return f"{name} [{sid[:8]}]"


@functools.lru_cache(maxsize=None)
def _prefixes(root):
    """ROOT/ the ways a shell command might spell it: as given or resolved, either slash."""
    forms = (root, _real(root))
    return tuple({f.replace("\\", "/") + "/" for f in forms} | {f + os.sep for f in forms})


def mentions(command, path):
    """The command with every real mention of PATH swapped for <F>, or None if it never names it.
    "a.md" inside "data.md" or "docs/a.md" doesn't count; "a.md", "./a.md" and ROOT/a.md do."""
    if path not in command:
        return None
    roots = _prefixes(ROOT)
    out, last, found, i = [], 0, False, command.find(path)
    while i != -1:
        j = i + len(path)
        before = command[:i]
        starts = (not before or before[-1] in _PATH_START or before.endswith("./")
                  or any(before.endswith(r) for r in roots))
        ends = j == len(command) or not (command[j].isalnum() or command[j] in "_-")
        if starts and ends:
            out += [command[last:i], "<F>"]
            last, found = j, True
        i = command.find(path, i + 1)
    return "".join(out) + command[last:] if found else None


def attribute(sessions, dirty):
    """file -> {sid: {"edits": n, "bash": n, "last": ts, "scripts": set}}, post-commit work only."""
    paths = [p for _, p in dirty]
    since = {p: last_commit_time(p) for p in paths}
    lookup = {(p.lower() if os.name == "nt" else p): p for p in paths}
    # earliest session wins for a tool call that forks copied
    order = sorted(sessions, key=lambda s: (sessions[s]["start"] or 0, s))
    owner = {}
    for sid in order:
        for tid, *_ in sessions[sid]["events"]:
            if tid and tid not in owner:
                owner[tid] = sid
    by_file = defaultdict(lambda: defaultdict(lambda: {"edits": 0, "bash": 0, "last": 0.0, "scripts": set()}))
    claimed = set()
    for sid in order:
        for tid, ts, kind, payload in sessions[sid]["events"]:
            if tid and (owner.get(tid) != sid or tid in claimed):
                continue
            if tid:
                claimed.add(tid)
            if kind == "edit":
                p = lookup.get(payload.lower() if os.name == "nt" else payload)
                if p and ts >= since[p]:
                    d = by_file[p][sid]
                    d["edits"] += 1
                    d["last"] = max(d["last"], ts)
                continue
            for p in paths:
                if ts < since[p]:
                    continue
                marked = mentions(payload, p)
                if marked is None:
                    continue
                hits = [label for label, rx in MUTATORS if rx.search(marked)]
                if hits:
                    d = by_file[p][sid]
                    d["bash"] += 1
                    d["last"] = max(d["last"], ts)
                    d["scripts"].update(hits)
    return {p: dict(by) for p, by in by_file.items()}


def read_head(path):
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True)
    if r.returncode:
        return None  # not in HEAD, or no commits yet
    try:
        return r.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def read_work(path):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return None
    try:
        with open(full, encoding="utf-8", newline="") as fh:
            return fh.read()
    except Exception:
        return None


def added_lines(path, status, work):
    if status in ("?", "A"):
        return (work or "").splitlines()
    out = git("diff", "--no-color", "--no-ext-diff", "HEAD", "-U0", "--", path, check=False).decode("utf-8", "replace")
    return [ln[1:] for ln in out.split("\n") if ln.startswith("+") and not ln.startswith("+++")]


def inspect(status, path):
    info = {"path": path, "status": status, "quotes_only": False, "quote_cleanup": False,
            "gate": [], "markers": 0, "markers_new": False, "plus": 0, "minus": 0}
    ns = git("diff", "--no-ext-diff", "HEAD", "--numstat", "--", path, check=False).decode("utf-8", "replace").split()
    if len(ns) >= 2 and ns[0].isdigit() and ns[1].isdigit():
        info["plus"], info["minus"] = int(ns[0]), int(ns[1])
    work = read_work(path)
    if status == "D" or work is None:
        return info
    head = read_head(path) if status not in ("?", "A") else None
    if head is None and not (info["plus"] or info["minus"]):
        info["plus"] = len(work.splitlines())  # a new file: every line is an added line
    if head is not None:
        if head != work and head.translate(QUOTE_TABLE) == work.translate(QUOTE_TABLE):
            info["quotes_only"] = True
        elif sum(map(head.count, CURLY)) > sum(map(work.count, CURLY)):
            info["quote_cleanup"] = True
    if path.endswith(".md"):
        info["markers"] = len(MARKER_RE.findall(work))
        info["markers_new"] = info["markers"] > (len(MARKER_RE.findall(head)) if head else 0)
        if HARD_RULES and not info["quotes_only"]:
            for line in added_lines(path, status, work):
                info["gate"] += [label for _, _, label in scan_line(line, HARD_RULES)]
    return info


def when(ts):
    return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else "?"


def flags(i):
    out = []
    if i["gate"]:
        out.append("GATE: " + ", ".join(f"{k} x{v}" for k, v in Counter(i["gate"]).items()))
    if i["markers"]:
        out.append(f"{i['markers']} open marker(s)" + (" (new)" if i["markers_new"] else ""))
    if i["quote_cleanup"]:
        out.append("includes smart-quote cleanup")
    if i["status"] == "D":
        out.append("deleted")
    elif i["status"] == "?":
        out.append("untracked")
    elif i["status"] == "U":
        out.append("unmerged")
    return out


def build_plan(dirty, infos, attrib):
    plan = {"quotes_only": [], "specstory": [], "sessions": {}, "shared": [], "unattributed": []}
    for _, path in dirty:
        if path.startswith(".specstory/"):
            plan["specstory"].append(path)
        elif infos[path]["quotes_only"]:
            plan["quotes_only"].append(path)
        elif len(attrib.get(path, {})) > 1:
            plan["shared"].append(path)
        elif attrib.get(path):
            plan["sessions"].setdefault(next(iter(attrib[path])), []).append(path)
        else:
            plan["unattributed"].append(path)
    return plan


def triage(folder=None):
    """Everything the plan needs, for the repo set_root() pointed at."""
    folder = folder or project_dir()
    dirty = dirty_files()
    sessions = load_sessions(folder) if dirty else {}
    infos = {p: inspect(s, p) for s, p in dirty}
    attrib = attribute(sessions, dirty)
    return {"folder": folder, "dirty": dirty, "sessions": sessions, "infos": infos,
            "attrib": attrib, "plan": build_plan(dirty, infos, attrib)}


def file_line(t, path, diffs):
    i = t["infos"][path]
    bits = flags(i)
    stat = f"  (+{i['plus']}/-{i['minus']})" if diffs and (i["plus"] or i["minus"]) else ""
    return f"  - {path}{stat}" + (f"  <- {'; '.join(bits)}" if bits else "")


def about(meta):
    out = []
    if meta.get("title") and (meta.get("custom") or meta.get("agent")):
        out.append(f"Topic: {meta['title']}")
    if meta.get("last_prompt"):
        out.append("Last prompt: " + meta["last_prompt"].strip().replace("\n", " ")[:160])
    return out


def render(t, diffs=False):
    plan, attrib, sessions = t["plan"], t["attrib"], t["sessions"]
    L = [f"# Working tree triage: {len(t['dirty'])} dirty files, {len(sessions)} transcripts read\n"]
    if not sessions:
        L.append(f"No transcripts found in {t['folder']}\n")
    if plan["quotes_only"]:
        L.append(f"## Quotes only ({len(plan['quotes_only'])} files): one commit, safe to stage now")
        L.append("Each file matches HEAD once smart quotes are straightened.")
        L += [file_line(t, p, diffs) for p in plan["quotes_only"]]
        L.append("")
    last = {s: max(attrib[p][s]["last"] for p in files) for s, files in plan["sessions"].items()}
    for sid in sorted(plan["sessions"], key=lambda s: -last[s]):
        files = plan["sessions"][sid]
        L.append(f"## {session_label(sid, sessions[sid])}  ({len(files)} files, last edit {when(last[sid])})")
        L += about(sessions[sid])
        L += [file_line(t, p, diffs) for p in files]
        scripts = sorted({s for p in files for s in attrib[p][sid]["scripts"]})
        if scripts:
            L.append("  (also ran: " + ", ".join(scripts) + ")")
        L.append("")
    if plan["shared"]:
        L.append(f"## Edited by more than one session ({len(plan['shared'])} files): needs a look")
        for p in plan["shared"]:
            who = ", ".join(f"{session_label(s, sessions[s])} x{d['edits'] + d['bash']}"
                            for s, d in sorted(attrib[p].items(), key=lambda kv: -kv[1]["last"]))
            L.append(file_line(t, p, diffs))
            L.append(f"      sessions: {who}")
        L.append("")
    if plan["unattributed"]:
        L.append(f"## No session edited these ({len(plan['unattributed'])} files)")
        L.append("Hand edits in the editor, a script run from a terminal, or a session that is gone.")
        L += [file_line(t, p, diffs) for p in plan["unattributed"]]
        L.append("")
    if plan["specstory"]:
        L.append(f"## SpecStory chat logs ({len(plan['specstory'])} files): commit these on their own")
        L.append("")
    return "\n".join(L)


def find_session(sessions, want):
    """'current' (this chat, from CLAUDE_CODE_SESSION_ID), an id prefix, or part of a name."""
    if want == "current":
        want = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        if not want:
            raise SystemExit("tree_triage: no CLAUDE_CODE_SESSION_ID here; pass --session ID")
    hits = [s for s in sessions if s.startswith(want)]
    if not hits:
        low = want.lower()
        hits = [s for s, m in sessions.items()
                if any(low in (m.get(k) or "").lower() for k in ("custom", "agent", "title"))]
    if len(hits) != 1:
        found = ", ".join(session_label(s, sessions[s]) for s in hits[:8]) or "none"
        raise SystemExit(f"tree_triage: --session {want!r} matched {len(hits)} sessions ({found})")
    return hits[0]


def session_view(plan, attrib, sid):
    """The plan cut down to one session: the files only it edited, the files it shares with
    other sessions, and the quotes-only and SpecStory files it touched."""
    touched = {p for p, by in attrib.items() if sid in by}
    return {
        "mine": plan["sessions"].get(sid, []),
        "shared": [p for p in plan["shared"] if p in touched],
        "quotes_only": [p for p in plan["quotes_only"] if p in touched],
        "specstory": [p for p in plan["specstory"] if p in touched],
    }


def render_session(t, sid, view, diffs=False):
    meta = t["sessions"][sid]
    L = [f"# {session_label(sid, meta)}: what this session changed"] + about(meta) + [""]
    L.append(f"## Only this session edited these ({len(view['mine'])} files)")
    L += [file_line(t, p, diffs) for p in view["mine"]] or ["  (none)"]
    L.append("")
    if view["shared"]:
        L.append(f"## Other sessions edited these too ({len(view['shared'])} files): ask before committing")
        for p in view["shared"]:
            others = ", ".join(session_label(s, t["sessions"][s]) for s in t["attrib"][p] if s != sid)
            L.append(file_line(t, p, diffs))
            L.append(f"      also: {others}")
        L.append("")
    if view["quotes_only"]:
        L.append(f"## Quotes only ({len(view['quotes_only'])} files): commit these on their own")
        L += [file_line(t, p, diffs) for p in view["quotes_only"]]
        L.append("")
    if view["specstory"]:
        L.append(f"## SpecStory chat logs ({len(view['specstory'])} files): commit these on their own")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", metavar="PATH", help="the repo to sort (default: the one you're in)")
    ap.add_argument("--transcripts", metavar="DIR", help="read transcripts from this folder")
    ap.add_argument("--json", action="store_true", help="print the plan as JSON")
    ap.add_argument("--diffs", action="store_true", help="show +/- line counts per file")
    ap.add_argument("--session", nargs="?", const="current", metavar="ID_OR_NAME",
                    help="only one session's files; with no value, this chat's")
    a = ap.parse_args(argv)

    set_root(a.repo)
    t = triage(a.transcripts)
    if not t["dirty"]:
        print("Working tree is clean.")
        return 0
    infos = t["infos"]

    if a.session:
        sid = find_session(t["sessions"], a.session)
        view = session_view(t["plan"], t["attrib"], sid)
        if a.json:
            out = dict(view, session=session_label(sid, t["sessions"][sid]),
                       flags={p: flags(infos[p]) for ps in view.values() for p in ps if flags(infos[p])})
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            print(render_session(t, sid, view, a.diffs))
        return 0

    if a.json:
        out = dict(t["plan"])
        out["sessions"] = {session_label(s, t["sessions"][s]): f for s, f in t["plan"]["sessions"].items()}
        out["flags"] = {p: flags(i) for p, i in infos.items() if flags(i)}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(render(t, a.diffs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
