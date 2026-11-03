"""The working tree triage: which session gets which file, the quotes-only batch, the gate and markers."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import tree_triage as tt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "tree_triage.py")
PAST = "2026-01-01T00:00:00Z"  # every test commit is made at this time
DASH = "\u2014"
S1, S2 = "11111111-aaaa-0000-0000-000000000001", "22222222-bbbb-0000-0000-000000000002"


@unittest.skipIf(shutil.which("git") is None, "git isn't installed")
class Triage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = os.path.join(self.tmp, "repo")
        self.logs = os.path.join(self.tmp, "transcripts")
        os.makedirs(self.repo)
        os.makedirs(self.logs)
        config = os.path.join(self.tmp, "gitconfig")  # keep the machine's own git config out of it
        open(config, "w").close()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=config, GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com",
                        GIT_AUTHOR_DATE=PAST, GIT_COMMITTER_DATE=PAST)
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")
        tt.set_root(self.repo)

    # helpers

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, env=self.env, check=True, capture_output=True)

    def write(self, name, text):
        path = os.path.join(self.repo, *name.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def commit(self, files):
        for name, text in files.items():
            self.write(name, text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")

    def path(self, name, root=None):
        return os.path.join(root or tt.ROOT, *name.split("/"))

    def edit(self, tid, ts, name, tool="Edit"):
        return (tid, ts, tool, {"file_path": self.path(name)})

    def bash(self, tid, ts, command):
        return (tid, ts, "Bash", {"command": command})

    def transcript(self, sid, calls, start=None, title=None, custom=None, prompt=None, parent=None):
        """A fake transcript in Claude Code's shapes. calls: (tool_use id, timestamp, tool, input)."""
        rows = []
        if start:
            rows.append({"type": "user", "timestamp": start, "cwd": tt.ROOT,
                         "message": {"role": "user", "content": "go"}})
        for tid, ts, name, inp in calls:
            rows.append({"type": "assistant", "timestamp": ts, "cwd": tt.ROOT,
                         "message": {"content": [{"type": "tool_use", "id": tid, "name": name, "input": inp}]}})
        if title:
            rows.append({"type": "ai-title", "aiTitle": title})
        if custom:
            rows.append({"type": "custom-title", "customTitle": custom})
        if prompt:
            rows.append({"type": "last-prompt", "lastPrompt": prompt})
        folder = os.path.join(self.logs, parent, "subagents") if parent else self.logs
        os.makedirs(folder, exist_ok=True)
        name = f"agent-{sid}.jsonl" if parent else f"{sid}.jsonl"
        with open(os.path.join(folder, name), "w", encoding="utf-8", newline="") as f:
            f.write("".join(json.dumps(r) + "\n" for r in rows))

    def cli(self, *args, **env):
        r = subprocess.run([sys.executable, TOOL, "--repo", self.repo, "--transcripts", self.logs, *args],
                           cwd=self.tmp, env=dict(os.environ, PYTHONUTF8="1", **env),
                           capture_output=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    # 1-2: who gets which file

    def test_each_session_gets_its_own_files(self):
        self.commit({"a.md": "one\n", "b.md": "two\n"})
        self.write("a.md", "one more\n")
        self.write("b.md", "two more\n")
        self.transcript(S1, [self.edit("toolu_1", "2026-11-01T10:00:00Z", "a.md")], title="Fix the intro")
        # a relative path counts too, resolved against the line's cwd
        self.transcript(S2, [("toolu_2", "2026-11-01T11:00:00Z", "Write", {"file_path": "b.md"})],
                        title="Tidy the docs", custom="docs pass", prompt="tighten the second section")
        t = tt.triage(self.logs)
        self.assertEqual(t["plan"]["sessions"], {S1: ["a.md"], S2: ["b.md"]})
        self.assertEqual(t["plan"]["shared"] + t["plan"]["unattributed"], [])
        text = tt.render(t)
        self.assertIn("## Fix the intro [11111111]", text)
        self.assertIn("## docs pass [22222222]", text)
        self.assertIn("Topic: Tidy the docs", text)
        self.assertIn("Last prompt: tighten the second section", text)

    def test_file_both_sessions_edited_is_shared(self):
        self.commit({"c.md": "base\n"})
        self.write("c.md", "base, edited twice\n")
        self.transcript(S1, [self.edit("toolu_1", "2026-11-01T10:00:00Z", "c.md")])
        self.transcript(S2, [self.edit("toolu_2", "2026-11-01T11:00:00Z", "c.md", tool="MultiEdit")])
        t = tt.triage(self.logs)
        self.assertEqual(t["plan"]["shared"], ["c.md"])
        self.assertEqual(t["plan"]["sessions"], {})
        self.assertIn("sessions: (untitled) [22222222] x1, (untitled) [11111111] x1", tt.render(t))

    # 3: quotes

    def test_quotes_only_change_goes_in_its_own_batch(self):
        self.commit({"q.md": "\u201cHi,\u201d she said. It\u2019s late.\n", "m.md": "\u201cHi\u201d\n"})
        self.write("q.md", "\"Hi,\" she said. It's late.\n")
        self.write("m.md", "\"Hi\"\nA new line.\n")
        self.transcript(S1, [self.edit("toolu_1", "2026-11-01T10:00:00Z", "q.md")])
        t = tt.triage(self.logs)
        self.assertEqual(t["plan"]["quotes_only"], ["q.md"])
        self.assertEqual(t["plan"]["sessions"], {})
        self.assertEqual(t["plan"]["unattributed"], ["m.md"])
        self.assertIn("includes smart-quote cleanup", tt.flags(t["infos"]["m.md"]))

    # 4: only work after the last commit counts

    def test_edit_before_the_last_commit_does_not_count(self):
        self.commit({"old.md": "base\n"})
        self.write("old.md", "changed by hand\n")
        self.write("new.md", "never committed\n")
        self.transcript(S1, [self.edit("toolu_1", "2025-12-01T10:00:00Z", "old.md"),
                             self.edit("toolu_2", "2025-12-01T10:00:00Z", "new.md")])
        t = tt.triage(self.logs)
        self.assertEqual(t["plan"]["unattributed"], ["old.md"])
        self.assertNotIn("old.md", t["attrib"])
        self.assertEqual(t["plan"]["sessions"], {S1: ["new.md"]})  # no commit, so any edit counts

    # 5: forks

    def test_a_tool_call_copied_into_a_fork_goes_to_the_earlier_session(self):
        parent, fork = "99999999-parent", "00000000-fork"  # the fork's id sorts first, so order comes from time
        self.commit({"a.md": "x\n", "b.md": "y\n"})
        self.write("a.md", "x2\n")
        self.write("b.md", "y2\n")
        copied = self.edit("toolu_copied", "2026-11-01T10:00:00Z", "a.md")
        self.transcript(parent, [copied], start="2026-11-01T09:00:00Z")
        self.transcript(fork, [copied, self.edit("toolu_new", "2026-11-01T12:00:00Z", "b.md")],
                        start="2026-11-01T11:00:00Z")
        t = tt.triage(self.logs)
        self.assertEqual(set(t["attrib"]["a.md"]), {parent})
        self.assertEqual(t["plan"]["sessions"], {parent: ["a.md"], fork: ["b.md"]})

    # 6: Bash

    def test_bash_sed_on_a_dirty_file_credits_the_session(self):
        self.commit({"conf.txt": "a=1\n"})
        self.write("conf.txt", "a=2\n")
        self.transcript(S1, [self.bash("toolu_1", "2026-11-01T10:00:00Z", f"sed -i '' 's/1/2/' {self.path('conf.txt')}")])
        self.transcript(S2, [self.bash("toolu_2", "2026-11-01T11:00:00Z", "cat conf.txt")])  # only reads it
        t = tt.triage(self.logs)
        self.assertEqual(t["plan"]["sessions"], {S1: ["conf.txt"]})
        self.assertEqual(t["attrib"]["conf.txt"][S1]["scripts"], {"sed -i"})
        self.assertIn("(also ran: sed -i)", tt.render(t))

    def test_bash_needs_the_whole_path_and_catches_redirects(self):
        self.commit({"a.md": "y\n", "docs/a.md": "x\n"})
        self.write("a.md", "y2\n")
        self.write("docs/a.md", "x2\n")
        self.write("out.txt", "hi\n")
        self.transcript(S1, [self.bash("toolu_1", "2026-11-01T10:00:00Z", "sed -i 's/x/z/' docs/a.md")])
        self.transcript(S2, [self.bash("toolu_2", "2026-11-01T11:00:00Z",
                                       f"cat > {self.path('out.txt')} <<'EOF'\nhi\nEOF")])
        t = tt.triage(self.logs)
        self.assertEqual(t["plan"]["sessions"], {S1: ["docs/a.md"], S2: ["out.txt"]})
        self.assertEqual(t["plan"]["unattributed"], ["a.md"])
        self.assertEqual(t["attrib"]["out.txt"][S2]["scripts"], {"redirect"})

    # 7: subagents

    def test_subagent_edits_count_for_the_parent(self):
        self.write("sub.md", "written by a subagent\n")
        self.transcript(S1, [], start="2026-11-01T09:00:00Z", title="Launch a helper")
        # the subagent writes the path the way the folder was spelled, before symlinks were resolved
        self.transcript("helper", [("toolu_9", "2026-11-01T10:00:00Z", "Write",
                                    {"file_path": self.path("sub.md", root=self.repo)})], parent=S1)
        t = tt.triage(self.logs)
        self.assertEqual(list(t["sessions"]), [S1])
        self.assertEqual(t["plan"]["sessions"], {S1: ["sub.md"]})

    # 8: the gate and the markers

    def test_gate_flags_added_lines_and_markers_flag_new_todos(self):
        self.assertTrue(tt.HARD_RULES, "tools/rule_engine.py should import here")
        self.commit({"doc.md": f"Old line {DASH} already here.\n", "code.py": "x = 1\n"})
        self.write("doc.md", f"Old line {DASH} already here.\nA new line {DASH} with a dash.\nTODO: check this.\n")
        self.write("code.py", f"x = '{DASH}'  # TODO\n")
        self.write("clean.md", "A fine new line.\n")
        t = tt.triage(self.logs)
        doc = tt.flags(t["infos"]["doc.md"])
        self.assertIn("GATE: em dash x1", doc)  # the old line's dash isn't counted again
        self.assertIn("1 open marker(s) (new)", doc)
        self.assertEqual(tt.flags(t["infos"]["code.py"]), [])  # only .md files are checked
        self.assertEqual(tt.flags(t["infos"]["clean.md"]), ["untracked"])

    # 9: one session's view

    def test_session_view_has_only_its_own_and_shared_files(self):
        self.commit({"a.md": "1\n", "b.md": "2\n", "both.md": "3\n", "q.md": "\u2018q\u2019\n"})
        for name, text in (("a.md", "1+\n"), ("b.md", "2+\n"), ("both.md", "3+\n"), ("q.md", "'q'\n"),
                           (".specstory/history/chat.md", "log\n")):
            self.write(name, text)
        self.transcript(S1, [self.edit("toolu_1", "2026-11-01T10:00:00Z", "a.md"),
                             self.edit("toolu_2", "2026-11-01T10:05:00Z", "both.md"),
                             self.edit("toolu_3", "2026-11-01T10:10:00Z", "q.md"),
                             self.edit("toolu_4", "2026-11-01T10:15:00Z", ".specstory/history/chat.md")],
                        custom="docs pass")
        self.transcript(S2, [self.edit("toolu_5", "2026-11-01T11:00:00Z", "b.md"),
                             self.edit("toolu_6", "2026-11-01T11:05:00Z", "both.md")])
        t = tt.triage(self.logs)
        self.assertEqual(tt.find_session(t["sessions"], "1111"), S1)
        self.assertEqual(tt.find_session(t["sessions"], "DOCS"), S1)
        view = tt.session_view(t["plan"], t["attrib"], S1)
        self.assertEqual(view, {"mine": ["a.md"], "shared": ["both.md"], "quotes_only": ["q.md"],
                                "specstory": [".specstory/history/chat.md"]})
        self.assertIn("also: (untitled) [22222222]", tt.render_session(t, S1, view))

    # 10: the command line, and a repo with no commits

    def test_cli_json(self):
        self.commit({"a.md": "1\n"})
        self.write("a.md", "1+\n")
        self.transcript(S1, [self.edit("toolu_1", "2026-11-01T10:00:00Z", "a.md")], title="Fix the intro")
        out = json.loads(self.cli("--json"))
        self.assertEqual(out["sessions"], {"Fix the intro [11111111]": ["a.md"]})
        self.assertEqual(out["unattributed"], [])
        view = json.loads(self.cli("--json", "--session", CLAUDE_CODE_SESSION_ID=S1))
        self.assertEqual(view["mine"], ["a.md"])
        self.assertEqual(view["session"], "Fix the intro [11111111]")

    def test_repo_with_no_commits_yet(self):
        self.write("a.md", "TODO: the intro\n")
        self.write("b.txt", "notes\n")
        self.git("add", "b.txt")  # one staged, one untracked
        self.transcript(S1, [self.edit("toolu_1", "2026-11-01T10:00:00Z", "a.md")])
        t = tt.triage(self.logs)
        self.assertEqual({p: s for s, p in t["dirty"]}, {"a.md": "?", "b.txt": "A"})
        self.assertEqual(t["plan"]["sessions"], {S1: ["a.md"]})
        self.assertEqual(t["plan"]["unattributed"], ["b.txt"])
        self.assertEqual(tt.flags(t["infos"]["a.md"]), ["1 open marker(s) (new)", "untracked"])
        self.assertIn("  - a.md  (+1/-0)", self.cli("--diffs"))


class ProjectKey(unittest.TestCase):
    def test_every_character_but_letters_and_digits_becomes_a_dash(self):
        self.assertEqual(tt.project_key("/home/x/My Repo.v2"), "-home-x-My-Repo-v2")
        self.assertEqual(tt.project_key("C:\\work\\repo"), "C--work-repo")


if __name__ == "__main__":
    unittest.main()
