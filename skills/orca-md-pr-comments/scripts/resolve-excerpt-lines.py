#!/usr/bin/env python3
"""Orca の excerpt から、Markdown 本文上の行番号を決める。

reported lines は hint であり、excerpt が source of truth。
エージェントは本文を自分で検索せず、このスクリプトの JSON を使う。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def resolve_excerpt(
    source: str,
    excerpt: str,
    hint_start: int | None = None,
    hint_end: int | None = None,
) -> dict[str, Any]:
    """excerpt が含まれる行範囲を返す。

    source は対象ファイルの全文。行番号は 1 始まり。
    hint_start / hint_end は reported lines。複数ヒットのときだけ優先に使う。
    """
    needle = _normalize_excerpt(excerpt)
    if not needle:
        return _result("not_found", candidates=[])

    lines = source.splitlines()
    strategies = (
        ("substring", lambda: _find_substring_on_single_lines(lines, needle)),
        ("joined_lines", lambda: _find_joined_lines(lines, needle)),
        ("prefix", lambda: _find_prefix(lines, needle)),
        ("visible_text", lambda: _find_visible_text(lines, needle)),
        ("whitespace_normalized", lambda: _find_whitespace_normalized(lines, needle)),
    )
    last_empty: dict[str, Any] | None = None
    for method, finder in strategies:
        matches = finder()
        result = _pick_result(matches, lines, hint_start, hint_end, method=method)
        if result["status"] == "resolved":
            return result
        if result["status"] == "ambiguous":
            return result
        last_empty = result
    return last_empty or _result("not_found", candidates=[])


def _normalize_excerpt(excerpt: str) -> str:
    cleaned = []
    for raw in excerpt.splitlines():
        line = raw.strip()
        line = re.sub(r"^[>|│┃]+", "", line).strip()
        if line:
            cleaned.append(line)
    return "\n".join(cleaned).strip()


FILE_RE = re.compile(r"^File:\s*(.+?)\s*$", re.I)
SOURCE_RE = re.compile(r"^Source:\s*(.+?)\s*$", re.I)
LINES_RE = re.compile(r"^Lines?\s+(\d+)(?:\s*[-–—〜~]\s*(\d+))?\s*$", re.I)
USER_COMMENT_RE = re.compile(r"^User comment:\s*(.*)$", re.I)


def parse_payloads(text: str) -> list[dict[str, Any]]:
    """Orca のペースト文面をコメント辞書のリストにする。

    Lines は hint_start / hint_end として保持する。
    """
    comments = []
    current: dict[str, Any] | None = None
    mode = None
    excerpt_lines: list[str] = []
    comment_lines: list[str] = []

    def flush():
        nonlocal current, mode, excerpt_lines, comment_lines
        if current is None:
            excerpt_lines = []
            comment_lines = []
            mode = None
            return
        current["excerpt"] = _normalize_excerpt("\n".join(excerpt_lines))
        current["user_comment"] = _normalize_user_comment("\n".join(comment_lines))
        if current.get("file") and current["excerpt"]:
            comments.append(current)
        current = None
        excerpt_lines = []
        comment_lines = []
        mode = None

    for raw in text.splitlines():
        line = raw.rstrip()
        file_match = FILE_RE.match(line)
        if file_match:
            flush()
            current = {
                "file": file_match.group(1).strip(),
                "source": None,
                "hint_start": None,
                "hint_end": None,
            }
            mode = None
            continue
        if current is None:
            continue
        source_match = SOURCE_RE.match(line)
        if source_match:
            current["source"] = source_match.group(1).strip()
            continue
        lines_match = LINES_RE.match(line.strip())
        if lines_match:
            start = int(lines_match.group(1))
            end = int(lines_match.group(2)) if lines_match.group(2) else start
            current["hint_start"] = start
            current["hint_end"] = end
            continue
        comment_match = USER_COMMENT_RE.match(line)
        if comment_match:
            mode = "comment"
            comment_lines.append(comment_match.group(1))
            continue
        if re.match(r"^Excerpt:\s*$", line, re.I):
            mode = "excerpt"
            continue
        excerpt_inline = re.match(r"^Excerpt:\s*(.+)$", line, re.I)
        if excerpt_inline:
            mode = "excerpt"
            excerpt_lines.append(excerpt_inline.group(1))
            continue
        if mode == "excerpt":
            excerpt_lines.append(line)
        elif mode == "comment":
            comment_lines.append(line)

    flush()
    return comments


def _normalize_user_comment(text: str) -> str:
    stripped = text.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "\"'「」":
        return stripped[1:-1].strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        return stripped[1:-1].strip()
    if stripped.startswith("「") and stripped.endswith("」"):
        return stripped[1:-1].strip()
    return stripped


def _find_substring_on_single_lines(lines: list[str], needle: str) -> list[tuple[int, int]]:
    if "\n" in needle:
        return []
    found = []
    for index, line in enumerate(lines, start=1):
        if needle in line:
            found.append((index, index))
    return found


def _find_joined_lines(lines: list[str], needle: str) -> list[tuple[int, int]]:
    found = []
    compact = needle.replace("\n", "")
    max_span = min(len(lines), 8)
    for start in range(len(lines)):
        parts = []
        for end in range(start, min(start + max_span, len(lines))):
            parts.append(lines[end])
            joined_newline = "\n".join(parts)
            joined_flat = "".join(parts)
            if needle in joined_newline or compact in joined_flat:
                span = (start + 1, end + 1)
                if span not in found:
                    found.append(span)
    return found


def _find_prefix(lines: list[str], needle: str) -> list[tuple[int, int]]:
    if "\n" in needle:
        return []
    found = []
    for index, line in enumerate(lines, start=1):
        visible = _visible_text(line)
        if visible.startswith(needle) or line.lstrip().startswith(needle):
            found.append((index, index))
    return found


def _find_visible_text(lines: list[str], needle: str) -> list[tuple[int, int]]:
    visible_needle = _visible_text(needle.replace("\n", ""))
    if not visible_needle:
        return []
    found = []
    for index, line in enumerate(lines, start=1):
        visible = _visible_text(line)
        if visible_needle in visible:
            found.append((index, index))
        else:
            span = _visible_span(lines, index - 1, visible_needle)
            if span and span not in found:
                found.append(span)
    return found


def _visible_span(lines: list[str], start_index: int, visible_needle: str) -> tuple[int, int] | None:
    parts = []
    for end in range(start_index, min(start_index + 8, len(lines))):
        parts.append(_visible_text(lines[end]))
        if visible_needle in "".join(parts) or visible_needle in "\n".join(parts) or _normalize_ws(visible_needle) in _normalize_ws("\n".join(parts)):
            return (start_index + 1, end + 1)
    return None


def _find_whitespace_normalized(lines: list[str], needle: str) -> list[tuple[int, int]]:
    compact = _normalize_ws(_visible_text(needle))
    if not compact:
        return []
    found = []
    for index, line in enumerate(lines, start=1):
        if compact in _normalize_ws(_visible_text(line)):
            found.append((index, index))
    if found:
        return found
    for start in range(len(lines)):
        parts = []
        for end in range(start, min(start + 8, len(lines))):
            parts.append(_visible_text(lines[end]))
            if compact in _normalize_ws("\n".join(parts)):
                span = (start + 1, end + 1)
                if span not in found:
                    found.append(span)
    return found


def _visible_text(text: str) -> str:
    out = text
    out = re.sub(r"^\s{0,3}#{1,6}\s+", "", out)
    out = re.sub(r"^\s*[-*+]\s+\[[ xX]\]\s+", "", out)
    out = re.sub(r"^\s*[-*+]\s+", "", out)
    out = re.sub(r"^\s*\d+\.\s+", "", out)
    out = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", out)
    out = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", out)
    out = out.replace("**", "").replace("__", "")
    out = re.sub(r"(?<!\w)[*_](.+?)[*_](?!\w)", r"\1", out)
    out = out.replace("`", "")
    return out


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _pick_result(
    matches: list[tuple[int, int]],
    lines: list[str],
    hint_start: int | None,
    hint_end: int | None,
    method: str,
) -> dict[str, Any]:
    matches = _tighten(list(dict.fromkeys(matches)))
    candidates = [_candidate(start, end, lines) for start, end in matches]
    if not matches:
        return _result("not_found", candidates=[], method=method)
    if len(matches) == 1:
        start, end = matches[0]
        return _result("resolved", start, end, "high", method, candidates)
    narrowed = _prefer_hint(matches, hint_start, hint_end)
    if len(narrowed) == 1:
        start, end = narrowed[0]
        return _result(
            "resolved",
            start,
            end,
            "medium",
            method,
            [_candidate(s, e, lines) for s, e in matches],
        )
    return _result("ambiguous", candidates=candidates, method=method)


def _tighten(matches: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """他のヒットを内包する広い span を捨て、内側の行を残す。"""
    kept = []
    for match in matches:
        contains_other = any(
            other != match and other[0] >= match[0] and other[1] <= match[1]
            for other in matches
        )
        if not contains_other:
            kept.append(match)
    return kept


def _prefer_hint(
    matches: list[tuple[int, int]],
    hint_start: int | None,
    hint_end: int | None,
) -> list[tuple[int, int]]:
    if hint_start is None and hint_end is None:
        return matches
    start = hint_start if hint_start is not None else hint_end
    end = hint_end if hint_end is not None else hint_start
    if start is None or end is None:
        return matches
    lo, hi = min(start, end), max(start, end)
    inside = [m for m in matches if _overlaps(m, lo, hi)]
    if inside:
        return inside
    pad = max(20, hi - lo)
    near = [m for m in matches if _overlaps(m, lo - pad, hi + pad)]
    return near if near else matches


def _overlaps(match: tuple[int, int], lo: int, hi: int) -> bool:
    return match[0] <= hi and match[1] >= lo


def _candidate(start: int, end: int, lines: list[str]) -> dict[str, Any]:
    text = "\n".join(lines[start - 1 : end])
    return {"start_line": start, "end_line": end, "text": text}


def _result(
    status: str,
    start_line: int | None = None,
    end_line: int | None = None,
    confidence: str | None = None,
    method: str | None = None,
    candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status, "candidates": candidates or []}
    if start_line is not None:
        payload["start_line"] = start_line
    if end_line is not None:
        payload["end_line"] = end_line
    if confidence is not None:
        payload["confidence"] = confidence
    if method is not None:
        payload["match_method"] = method
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    resolve_p = sub.add_parser("resolve", help="excerpt から行番号を決める")
    resolve_p.add_argument("--file", required=True, help="対象 Markdown ファイル")
    resolve_p.add_argument("--excerpt", required=True)
    resolve_p.add_argument("--hint-start", type=int)
    resolve_p.add_argument("--hint-end", type=int)

    parse_p = sub.add_parser("parse", help="Orca ペイロードを JSON 配列にする")
    parse_p.add_argument(
        "--payload-file",
        help="省略時は標準入力",
    )

    args = parser.parse_args(argv)
    if args.command == "resolve":
        source = _read_file(args.file)
        result = resolve_excerpt(source, args.excerpt, args.hint_start, args.hint_end)
        json.dump(result, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0 if result["status"] == "resolved" else 1
    if args.command == "parse":
        text = _read_file(args.payload_file) if args.payload_file else sys.stdin.read()
        json.dump(parse_payloads(text), sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0
    return 2


def _read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
