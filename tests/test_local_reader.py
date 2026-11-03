"""The local reader's prompt assembly and output filter. None of it needs MLX."""

import importlib.util
import os
import tempfile
import unittest

from tools import local_reader

HAS_MLX = importlib.util.find_spec("mlx_lm") is not None


class FakeTokenizer:
    """Renders turns as [role] content, like a chat template would."""

    def __init__(self, allow_system=True):
        self.allow_system = allow_system

    def apply_chat_template(self, messages, add_generation_prompt=False, tokenize=True, **kwargs):
        self.kwargs = kwargs
        if not self.allow_system and any(m["role"] == "system" for m in messages):
            raise ValueError("System role not supported")
        out = "".join(f"[{m['role']}] {m['content']}\n" for m in messages)
        return out + ("[model] " if add_generation_prompt else "")


class Prompt(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.paths = []
        for name, text in (("a.md", "First brief.\n"), ("b.md", "\nSecond brief.\n\n")):
            p = os.path.join(self.d, name)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            self.paths.append(p)

    def test_briefs_join_in_the_order_given(self):
        self.assertEqual(local_reader.read_briefs(self.paths), "First brief.\n\nSecond brief.\n")
        self.assertTrue(local_reader.read_briefs(self.paths[::-1]).startswith("Second"))

    def test_blind_lines_carry_their_own_numbers(self):
        self.assertEqual(local_reader.number_lines("# Blind test\n\n{x | y} A line.\n"),
                         "1\t# Blind test\n2\t\n3\t{x | y} A line.")

    def test_messages_put_brief_in_system_and_blind_in_user(self):
        msgs = local_reader.build_messages("BRIEF", "head\nitem")
        self.assertEqual([m["role"] for m in msgs], ["system", "user"])
        self.assertEqual(msgs[0]["content"], "BRIEF")
        self.assertIn("1\thead\n2\titem", msgs[1]["content"])

    def test_chat_template_renders_both_turns(self):
        p = local_reader.render_prompt(FakeTokenizer(), local_reader.build_messages("BRIEF", "item"))
        self.assertTrue(p.startswith("[system] BRIEF"))
        self.assertTrue(p.endswith("[model] "))

    def test_thinking_switch_reaches_the_template_only_when_set(self):
        tok, msgs = FakeTokenizer(), local_reader.build_messages("BRIEF", "item")
        local_reader.render_prompt(tok, msgs)
        self.assertEqual(tok.kwargs, {})
        local_reader.render_prompt(tok, msgs, thinking="off")
        self.assertEqual(tok.kwargs, {"enable_thinking": False})
        local_reader.render_prompt(tok, msgs, thinking="on")
        self.assertEqual(tok.kwargs, {"enable_thinking": True})

    def test_template_without_system_turn_gets_brief_in_user_turn(self):
        p = local_reader.render_prompt(FakeTokenizer(allow_system=False), local_reader.build_messages("BRIEF", "item"))
        self.assertNotIn("[system]", p)
        self.assertTrue(p.startswith("[user] BRIEF"))
        self.assertIn("1\titem", p)


class Filter(unittest.TestCase):
    REPLY = "\n".join([
        "Here are my flags:",
        "```",
        "L5 | the memory dissolved | poem | image doing a plain beat's job",
        "- L12 | a phrase here | essay | states the lesson",
        "  `L30 | another phrase | scripted | too tidy`",
        "L7 is fine, no flag.",
        "L9 |",
        "Line 14 | phrase | essay | wrong prefix",
        "```",
        "TALLY: 3 flags, 48 lines read",
    ])

    def test_keeps_well_formed_flags_and_drops_chatter(self):
        kept = local_reader.keep_flags(self.REPLY)
        self.assertEqual(kept, ["L5 | the memory dissolved | poem | image doing a plain beat's job",
                                "L12 | a phrase here | essay | states the lesson",
                                "L30 | another phrase | scripted | too tidy"])

    def test_line_numbers_are_parsed(self):
        self.assertEqual(local_reader.line_numbers(local_reader.keep_flags(self.REPLY)), [5, 12, 30])

    def test_flags_inside_thinking_blocks_do_not_count(self):
        reply = "<think>L3 | draft | poem | maybe</think>\nL8 | real one | essay | thesis"
        self.assertEqual(local_reader.line_numbers(local_reader.keep_flags(reply)), [8])
        reply = "<|channel>thought\nL3 | draft | poem | maybe<channel|>L8 | real one | essay | thesis"
        self.assertEqual(local_reader.line_numbers(local_reader.keep_flags(reply)), [8])

    def test_an_unclosed_thinking_block_drops_the_rest(self):
        self.assertEqual(local_reader.keep_flags("L2 | kept | essay | x\n<think>L3 | cut | poem | y"),
                         ["L2 | kept | essay | x"])

    def test_output_is_readable_by_eval_stats(self):
        from tools import eval_stats
        d = tempfile.mkdtemp()
        p = os.path.join(d, "run1.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(local_reader.keep_flags(self.REPLY)) + "\n")
        self.assertEqual(eval_stats.flagged_lines(p), {5, 12, 30})


class Cli(unittest.TestCase):
    def test_module_imports_without_mlx(self):
        self.assertTrue(callable(local_reader.run))

    @unittest.skipUnless(HAS_MLX, "mlx_lm isn't installed (it only runs on Apple Silicon)")
    def test_mlx_sampler_builds(self):
        from mlx_lm.sample_utils import make_sampler
        self.assertTrue(callable(make_sampler(temp=0.7)))


if __name__ == "__main__":
    unittest.main()
