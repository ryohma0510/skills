#!/usr/bin/env python3
"""resolve-excerpt-lines.py の公開関数に対するテスト。"""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "resolve-excerpt-lines.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("resolve_excerpt_lines", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ResolveExcerptLinesTest(unittest.TestCase):
    def test_should_resolve_truncated_excerpt_to_the_single_containing_line_when_reported_lines_span_a_block(self):
        # Given
        mod = load_mod()
        lines = [f"前文{i}" for i in range(1, 160)]
        lines.append("- 節タイトル")
        lines.extend([f"ブロック行{i}" for i in range(161, 162)])
        lines.append(
            "- [ ] **AC-026** 明示的な保存操作により、入力項目順序設定がテナント単位で"
            " 1 セット保存されることを確認できる（注記）"
        )
        lines.extend([f"ブロック行{i}" for i in range(163, 173)])
        source = "\n".join(lines) + "\n"
        excerpt = (
            "明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で"
        )

        # When
        result = mod.resolve_excerpt(source, excerpt, hint_start=160, hint_end=172)

        # Then
        self.assertEqual("resolved", result["status"])
        self.assertEqual(162, result["start_line"])
        self.assertEqual(162, result["end_line"])

    def test_should_resolve_visible_text_when_markdown_markers_split_the_raw_line(self):
        # Given
        mod = load_mod()
        source = (
            "導入\n"
            "- [ ] **AC-026** hello **world** を確認できる（注記）\n"
            "末尾\n"
        )
        excerpt = "AC-026 hello world を確認できる"

        # When
        result = mod.resolve_excerpt(source, excerpt, hint_start=1, hint_end=3)

        # Then
        self.assertEqual("resolved", result["status"])
        self.assertEqual(2, result["start_line"])
        self.assertEqual(2, result["end_line"])

    def test_should_ignore_quote_prefixes_in_the_excerpt_when_matching_file_text(self):
        # Given
        mod = load_mod()
        source = "対象の本文です。\n"
        excerpt = "> 対象の本文です。"

        # When
        result = mod.resolve_excerpt(source, excerpt)

        # Then
        self.assertEqual("resolved", result["status"])
        self.assertEqual(1, result["start_line"])
        self.assertEqual(1, result["end_line"])

    def test_should_return_ambiguous_when_the_excerpt_matches_two_lines_and_no_hint_is_given(self):
        # Given
        mod = load_mod()
        source = "同じ文がここにある。\n間\n同じ文がここにある。\n"

        # When
        result = mod.resolve_excerpt(source, "同じ文がここにある。")

        # Then
        self.assertEqual("ambiguous", result["status"])
        self.assertEqual(2, len(result["candidates"]))
        self.assertNotIn("start_line", result)

    def test_should_resolve_the_hit_inside_reported_lines_when_the_excerpt_matches_twice(self):
        # Given
        mod = load_mod()
        source = "同じ文がここにある。\n間\n同じ文がここにある。\n"

        # When
        result = mod.resolve_excerpt(source, "同じ文がここにある。", hint_start=3, hint_end=3)

        # Then
        self.assertEqual("resolved", result["status"])
        self.assertEqual(3, result["start_line"])
        self.assertEqual(3, result["end_line"])
        self.assertEqual("medium", result["confidence"])

    def test_should_parse_multiple_orca_payloads_and_keep_lines_as_hints(self):
        # Given
        mod = load_mod()
        payload = """
File: docs/spec.md
Source: markdown

Lines 160-172
Excerpt:
│ 明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で
User comment: "ここを直してほしい"

File: docs/other.md
Lines 10
Excerpt:
> 別の選択
User comment: 誤字を直す
"""

        # When
        comments = mod.parse_payloads(payload)

        # Then
        self.assertEqual(2, len(comments))
        self.assertEqual("docs/spec.md", comments[0]["file"])
        self.assertEqual("markdown", comments[0]["source"])
        self.assertEqual(160, comments[0]["hint_start"])
        self.assertEqual(172, comments[0]["hint_end"])
        self.assertEqual(
            "明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で",
            comments[0]["excerpt"],
        )
        self.assertEqual("ここを直してほしい", comments[0]["user_comment"])
        self.assertEqual("docs/other.md", comments[1]["file"])
        self.assertEqual(10, comments[1]["hint_start"])
        self.assertEqual(10, comments[1]["hint_end"])
        self.assertEqual("別の選択", comments[1]["excerpt"])
        self.assertEqual("誤字を直す", comments[1]["user_comment"])

    def test_should_return_not_found_when_the_excerpt_is_absent_from_the_file(self):
        # Given
        mod = load_mod()

        # When
        result = mod.resolve_excerpt("存在する行\n", "ファイルに無い選択")

        # Then
        self.assertEqual("not_found", result["status"])
        self.assertEqual([], result["candidates"])

    def test_should_resolve_a_two_line_span_when_the_excerpt_joins_consecutive_lines(self):
        # Given
        mod = load_mod()
        source = "これは前半\nそして後半の続き\n別段落\n"
        excerpt = "これは前半\nそして後半の続き"

        # When
        result = mod.resolve_excerpt(source, excerpt)

        # Then
        self.assertEqual("resolved", result["status"])
        self.assertEqual(1, result["start_line"])
        self.assertEqual(2, result["end_line"])


if __name__ == "__main__":
    unittest.main()
