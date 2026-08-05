#!/usr/bin/env python3
"""test-design の規約に対する決定的な検査 (T01-T05)。stdlib のみ。

    python3 check_test_style.py src/cart.test.ts
    python3 check_test_style.py src/            # ディレクトリは再帰的に走査する

検査するのは、機械が確実に見分けられる5つだけである。

    T01  テスト名が should で始まっていない
    T02  テスト名に判断を名指しする語が入っている (correct / valid / ...)
    T03  Given-When-Then のコメントが3つ揃っていない
    T04  期待値がアサーションの中で計算されている (トートロジー)
    T05  テスト本体に条件分岐がある (if / switch / 三項演算子)

DAMP——決定的な値がヘルパーに隠れていないか——は意味の判断であり、ここでは見ない。
seam の選び方、モックの是非、実装結合も同様に人が判断する領域である。

パースは正規表現とブレースの対応付けによる近似であり、文字列とコメントは除外するが
JavaScript の構文を完全に解釈するわけではない。
"""

import argparse
import re
import sys
from collections import namedtuple
from pathlib import Path

TEST_FILE_SUFFIXES = (".test.ts", ".test.tsx", ".test.js", ".test.jsx",
                      ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx")

JUDGMENT_WORDS = (
    "correct", "correctly", "valid", "invalid", "proper", "properly",
    "appropriate", "appropriately", "expected", "right", "good", "bad",
    "work", "works", "successfully", "gracefully", "handle", "handles",
)
JUDGMENT_RE = re.compile(r"\b(" + "|".join(JUDGMENT_WORDS) + r")\b", re.I)

# printf 形式のテンプレート名 ("%s" など) は each の行から実名を取るため名前検査から外す。
TEMPLATE_NAME_RE = re.compile(r"[%$]\w|[%$]\{")

TEST_CALL_RE = re.compile(r"(?<![\w.$])(?:test|it)(?![\w$])")
GWT_RES = (("Given", re.compile(r"//\s*Given\b")),
           ("When", re.compile(r"//\s*When\b")),
           ("Then", re.compile(r"//\s*Then\b")))

MATCHER_RE = re.compile(r"\.(?:toBe|toEqual|toStrictEqual|toBeCloseTo|toHaveLength)\s*\(")
BINARY_OP_RE = re.compile(r"(?<=[\w)\]])\s*[-+*/%]\s*(?=[\w(\[])")
DERIVED_RE = re.compile(r"\.(?:reduce|map|filter|flatMap)\s*\(")
EXPECTED_VAR_RE = re.compile(r"\b(?:const|let|var)\s+\w*(?:expected|want)\w*\s*=\s*([^;\n]+)", re.I)

# 三項は「空白 + ?」だけを見る。TS の省略可能マーカー (x?: T / x?.y) と ?? は空白を挟まない。
BRANCH_RES = (
    (re.compile(r"\bif\s*\("), "if"),
    (re.compile(r"\bswitch\s*\("), "switch"),
    (re.compile(r"\s\?(?![.?:=])"), "三項演算子"),
)

Finding = namedtuple("Finding", ["path", "line", "check_id", "message"])


def mask_strings_and_comments(text):
    """文字列とコメントの中身を空白に潰した、同じ長さのテキストを返す。

    引用符やコメント記号そのものは残すので、位置は元テキストと1対1で対応する。
    """
    out = list(text)
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'`":
            quote = ch
            i += 1
            while i < n:
                if text[i] == "\\":
                    out[i] = " "
                    if i + 1 < n:
                        out[i + 1] = " "
                    i += 2
                    continue
                if text[i] == quote:
                    break
                if text[i] != "\n":
                    out[i] = " "
                i += 1
            i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            out[i + 1] = " "
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                if text[i] != "\n":
                    out[i] = " "
                i += 1
            i += 2
        else:
            i += 1
    return "".join(out)


def match_bracket(masked, open_idx):
    """masked[open_idx] の括弧に対応する閉じ括弧の位置を返す。見つからなければ None。"""
    pairs = {"(": ")", "[": "]", "{": "}"}
    opener = masked[open_idx]
    closer = pairs[opener]
    depth = 0
    for i in range(open_idx, len(masked)):
        if masked[i] == opener:
            depth += 1
        elif masked[i] == closer:
            depth -= 1
            if depth == 0:
                return i
    return None


def read_string_literal(text, masked, start):
    """start 以降の最初の文字列リテラルを (値, 開始位置) で返す。手前に他の字句があれば None。"""
    i = start
    while i < len(masked) and masked[i].isspace():
        i += 1
    if i >= len(masked) or text[i] not in "\"'`":
        return None
    quote = text[i]
    end = text.find(quote, i + 1)
    while end != -1 and text[end - 1] == "\\":
        end = text.find(quote, end + 1)
    if end == -1:
        return None
    return text[i + 1:end], i


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def collect_test_names(text, masked):
    """(名前, 位置) の一覧と、各テスト本体の (開始, 終了, 位置) の一覧を返す。"""
    names = []
    bodies = []

    for call in TEST_CALL_RE.finditer(masked):
        cursor = call.end()

        each_open = None
        rest = masked[cursor:cursor + 8]
        if rest.lstrip().startswith(".each"):
            each_at = masked.index(".each", cursor)
            paren = masked.find("(", each_at)
            if paren == -1:
                continue
            close = match_bracket(masked, paren)
            if close is None:
                continue
            each_open = (paren, close)
            cursor = close + 1

        while cursor < len(masked) and masked[cursor].isspace():
            cursor += 1
        if cursor >= len(masked) or masked[cursor] != "(":
            continue
        args_close = match_bracket(masked, cursor)
        if args_close is None:
            continue

        literal = read_string_literal(text, masked, cursor + 1)
        if literal is not None:
            name, at = literal
            if not TEMPLATE_NAME_RE.search(name):
                names.append((name, at))

        if each_open is not None:
            names.extend(collect_each_names(text, masked, *each_open))

        body_open = masked.find("{", cursor, args_close)
        if body_open != -1:
            body_close = match_bracket(masked, body_open)
            if body_close is not None:
                bodies.append((body_open, body_close, call.start()))

    return names, bodies


def collect_each_names(text, masked, paren_open, paren_close):
    """test.each([...]) の各行から、先頭の文字列リテラルを取り出す。"""
    names = []
    array_open = masked.find("[", paren_open, paren_close)
    if array_open == -1:
        return names
    array_close = match_bracket(masked, array_open)
    if array_close is None:
        return names

    depth = 0
    for i in range(array_open, array_close):
        ch = masked[i]
        if ch in "([{":
            depth += 1
            if depth == 2 and ch == "[":
                literal = read_string_literal(text, masked, i + 1)
                if literal is not None and not TEMPLATE_NAME_RE.search(literal[0]):
                    names.append(literal)
        elif ch in ")]}":
            depth -= 1
    return names


def check_names(path, text, names, findings):
    for name, at in names:
        line = line_of(text, at)
        if not name.strip().lower().startswith("should"):
            findings.append(Finding(path, line, "T01", f"テスト名が should で始まっていません: 「{name}」"))
        hit = JUDGMENT_RE.search(name)
        if hit:
            findings.append(
                Finding(path, line, "T02",
                        f"テスト名に判断を名指しする語 '{hit.group(1)}' があります: 「{name}」"
                        "——観測できる結果と、それを引き起こす具体的な入力に書き換えること")
            )


def check_gwt(path, text, masked, bodies, findings):
    for body_open, body_close, call_at in bodies:
        region = text[body_open:body_close]
        missing = [label for label, pattern in GWT_RES if not pattern.search(region)]
        if missing:
            findings.append(
                Finding(path, line_of(text, call_at), "T03",
                        f"Given-When-Then のコメントが揃っていません (不足: {' / '.join(missing)})")
            )


def check_tautology(path, text, masked, bodies, findings):
    for body_open, body_close, _ in bodies:
        for matcher in MATCHER_RE.finditer(masked, body_open, body_close):
            arg_open = matcher.end() - 1
            arg_close = match_bracket(masked, arg_open)
            if arg_close is None:
                continue
            arg = masked[arg_open + 1:arg_close]
            if BINARY_OP_RE.search(arg) or DERIVED_RE.search(arg):
                findings.append(
                    Finding(path, line_of(text, arg_open), "T04",
                            f"期待値をアサーションの中で計算しています: 「{text[arg_open + 1:arg_close].strip()}」"
                            "——計算は書く前に済ませ、結果をリテラルで書くこと")
                )

        for assign in EXPECTED_VAR_RE.finditer(masked, body_open, body_close):
            rhs = assign.group(1)
            if BINARY_OP_RE.search(rhs) or DERIVED_RE.search(rhs):
                findings.append(
                    Finding(path, line_of(text, assign.start()), "T04",
                            "期待値を実装と同じ手順で導出しています"
                            "——独立した真実の源から取り、結果をリテラルで書くこと")
                )


def check_branching(path, text, masked, bodies, findings):
    for body_open, body_close, _ in bodies:
        for pattern, label in BRANCH_RES:
            for hit in pattern.finditer(masked, body_open, body_close):
                findings.append(
                    Finding(path, line_of(text, hit.start()), "T05",
                            f"テスト本体に条件分岐 ({label}) があります"
                            "——一本道になるよう、シナリオごとにテストを割ること")
                )


def check_file(path):
    text = Path(path).read_text(encoding="utf-8")
    masked = mask_strings_and_comments(text)
    names, bodies = collect_test_names(text, masked)

    findings = []
    check_names(path, text, names, findings)
    check_gwt(path, text, masked, bodies, findings)
    check_tautology(path, text, masked, bodies, findings)
    check_branching(path, text, masked, bodies, findings)
    return sorted(findings, key=lambda f: (f.line, f.check_id))


def resolve_targets(paths):
    targets = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            targets.extend(sorted(p for p in path.rglob("*")
                                  if p.name.endswith(TEST_FILE_SUFFIXES)))
        elif path.exists():
            targets.append(path)
        else:
            print(f"[error] {path} が見つかりません", file=sys.stderr)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", help="テストファイル、またはそれを含むディレクトリ")
    args = parser.parse_args()

    targets = resolve_targets(args.paths)
    if not targets:
        print("検査対象のテストファイルが見つかりません")
        return 0

    total = 0
    for target in targets:
        findings = check_file(target)
        print(f"=== {target} ===")
        if not findings:
            print("  OK")
        for finding in findings:
            print(f"  L{finding.line} [{finding.check_id}] {finding.message}")
            total += 1
        print()

    print(f"{len(targets)} file(s) checked: {total} violation(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
