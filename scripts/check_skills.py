#!/usr/bin/env python3
"""Deterministic checks for skills/*/SKILL.md (S01-S15). Stdlib only, manual invocation."""

import json
import re
import sys
from collections import Counter, namedtuple
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
CLAUDE_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
README_MD = REPO_ROOT / "README.md"

MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
MAX_BODY_LINES = 500
MAX_REFERENCE_DEPTH = 1
RESERVED_WORDS = ("anthropic", "claude")
MIN_DUPLICATE_BLOCK_LEN = 80
USER_INVOKED_DESCRIPTION_MAX_LEN = 200

Finding = namedtuple("Finding", ["check_id", "severity", "message"])

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BACKTICK_RE = re.compile(r"`([^`]+)`")
FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def parse_frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, text

    fm_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :])
    data = {}
    i = 0
    while i < len(fm_lines):
        match = FRONTMATTER_KEY_RE.match(fm_lines[i])
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()

        if value in (">-", ">", "|", "|-", "|+", ""):
            block_lines = []
            base_indent = None
            j = i + 1
            while j < len(fm_lines):
                line = fm_lines[j]
                if line.strip() == "":
                    j += 1
                    continue
                indent = len(line) - len(line.lstrip(" "))
                if base_indent is None:
                    if indent == 0:
                        break
                    base_indent = indent
                if indent < base_indent:
                    break
                block_lines.append(line.strip())
                j += 1
            value = " ".join(block_lines) if value in (">-", ">", "") else "\n".join(block_lines)
            i = j
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            i += 1

        data[key] = value

    return data, body


def strip_anchor(target):
    if "#" in target:
        target = target.split("#", 1)[0]
    return target


def is_local_path(target):
    return bool(target) and not target.startswith(("http://", "https://", "mailto:", "#"))


def extract_links(body):
    results = []
    for lineno, line in enumerate(body.split("\n"), start=1):
        for match in LINK_RE.finditer(line):
            results.append((match.group(2).strip(), lineno))
    return results


# Any backtick span ending in a word character + ".md" (excludes a bare ".md" extension mention).
BACKTICK_MD_MENTION_RE = re.compile(r"^\S*[A-Za-z0-9_]\.md$")
# Stricter: only path-safe characters, used to decide whether an existence check (S10) makes sense.
REAL_PATH_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\-./]*\.md$")


def extract_backtick_md_paths(body):
    results = []
    for lineno, line in enumerate(body.split("\n"), start=1):
        for match in BACKTICK_RE.finditer(line):
            content = match.group(1).strip()
            if BACKTICK_MD_MENTION_RE.match(content):
                results.append((content, lineno))
    return results


def extract_blocks(text):
    blocks = []
    for para in re.split(r"\n\s*\n", text):
        lines = [l for l in para.split("\n") if l.strip()]
        bullet_lines = [l.strip() for l in lines if l.strip().startswith(("- ", "* "))]
        if bullet_lines and len(bullet_lines) == len(lines):
            blocks.extend(bullet_lines)
        else:
            block = " ".join(l.strip() for l in lines)
            if block:
                blocks.append(block)
    return blocks


def check_name(frontmatter, findings):
    name = frontmatter.get("name", "")
    if not name:
        findings.append(Finding("S01", "error", "frontmatterに name がありません"))
        return
    if not re.fullmatch(r"[a-z0-9-]+", name) or len(name) > MAX_NAME_LEN:
        findings.append(
            Finding(
                "S01",
                "error",
                f"name '{name}' は小文字+数字+ハイフンのみ・{MAX_NAME_LEN}文字以内である必要があります",
            )
        )
    lowered = name.lower()
    for word in RESERVED_WORDS:
        if word in lowered:
            findings.append(Finding("S02", "error", f"name '{name}' に予約語 '{word}' が含まれています"))


def check_description(frontmatter, findings):
    description = frontmatter.get("description", "")
    if not description.strip():
        findings.append(Finding("S03", "error", "frontmatterに description がないか空です"))
        return
    if len(description) > MAX_DESCRIPTION_LEN:
        findings.append(
            Finding(
                "S03",
                "error",
                f"description が{len(description)}文字あります（上限{MAX_DESCRIPTION_LEN}文字）",
            )
        )


def check_body_length(body, findings):
    line_count = len(body.strip("\n").split("\n")) if body.strip("\n") else 0
    if line_count > MAX_BODY_LINES:
        findings.append(
            Finding(
                "S04",
                "warn",
                f"SKILL.md本文が{line_count}行あります（推奨上限{MAX_BODY_LINES}行）",
            )
        )


def check_references(skill_dir, body, findings):
    links = extract_links(body)
    backticks = extract_backtick_md_paths(body)
    local_link_targets = [(strip_anchor(t), ln) for t, ln in links if is_local_path(t)]

    referenced_paths = set()
    for target, lineno in local_link_targets + backticks:
        referenced_paths.add(target)

        if target.count("/") > MAX_REFERENCE_DEPTH:
            findings.append(
                Finding("S05", "warn", f"L{lineno}: 参照パス '{target}' がSKILL.mdから2階層以上深い位置を指しています")
            )
        if "\\" in target:
            findings.append(Finding("S06", "error", f"L{lineno}: 参照パス '{target}' にWindowsパス区切り(\\)が含まれています"))
        if ".." in target.split("/"):
            findings.append(Finding("S09", "warn", f"L{lineno}: 参照パス '{target}' に親方向traversal(..)が含まれています"))

    for target, lineno in local_link_targets:
        if not (skill_dir / target).exists():
            findings.append(Finding("S08", "error", f"L{lineno}: リンク先 '{target}' が存在しません"))

    for target, lineno in backticks:
        if REAL_PATH_RE.match(target) and not (skill_dir / target).exists():
            findings.append(Finding("S10", "warn", f"L{lineno}: バッククォート内のパス '{target}' が存在しません"))

    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        for md_file in sorted(references_dir.rglob("*.md")):
            rel = md_file.relative_to(skill_dir).as_posix()
            if rel not in referenced_paths:
                findings.append(Finding("S07", "warn", f"'{rel}' はSKILL.mdのどこからも参照されていません"))


def check_symlink(name, findings):
    link_path = CLAUDE_SKILLS_DIR / name
    target_path = SKILLS_DIR / name
    if link_path.is_symlink():
        if link_path.resolve() != target_path.resolve():
            findings.append(
                Finding("S11", "error", f".claude/skills/{name} のリンク先が skills/{name} と一致しません")
            )
    elif link_path.exists():
        findings.append(Finding("S11", "error", f".claude/skills/{name} がシンボリックリンクではありません"))
    else:
        findings.append(Finding("S11", "error", f".claude/skills/{name} が存在しません"))


def check_marketplace(name, findings):
    if not MARKETPLACE_JSON.exists():
        findings.append(Finding("S12", "error", "marketplace.jsonが見つかりません"))
        return
    try:
        data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(Finding("S12", "error", f"marketplace.jsonのパースに失敗しました: {exc}"))
        return

    expected = f"./skills/{name}"
    for plugin in data.get("plugins", []):
        entries = {s.rstrip("/") for s in plugin.get("skills", [])}
        if expected in entries or f"skills/{name}" in {e.lstrip("./") for e in entries}:
            return
    findings.append(Finding("S12", "error", f"marketplace.jsonのplugins[].skillsに '{expected}' がありません"))


def check_readme(name, findings):
    if not README_MD.exists():
        findings.append(Finding("S13", "warn", "README.mdが見つかりません"))
        return
    text = README_MD.read_text(encoding="utf-8")
    if f"skills/{name}/SKILL.md" not in text:
        findings.append(Finding("S13", "warn", f"README.mdのスキル一覧表に '{name}' の行がありません"))


def check_duplicate_blocks(skill_dir, body, findings):
    texts = [body]
    referenced_md_targets = set()
    for target, _ in extract_links(body):
        target = strip_anchor(target)
        if is_local_path(target) and target.endswith(".md"):
            referenced_md_targets.add(target)
    for target, _ in extract_backtick_md_paths(body):
        referenced_md_targets.add(target)

    skill_md_path = (skill_dir / "SKILL.md").resolve()
    for target in referenced_md_targets:
        candidate = skill_dir / target
        if candidate.exists() and candidate.resolve() != skill_md_path:
            texts.append(candidate.read_text(encoding="utf-8"))

    all_blocks = []
    for text in texts:
        all_blocks.extend(extract_blocks(text))

    counts = Counter(b for b in all_blocks if len(b) >= MIN_DUPLICATE_BLOCK_LEN)
    for block, count in counts.items():
        if count >= 2:
            preview = block[:60] + ("…" if len(block) > 60 else "")
            findings.append(Finding("S14", "warn", f"同一の文/段落が{count}回出現しています: 「{preview}」"))


def check_user_invoked_description(frontmatter, findings):
    disable_flag = str(frontmatter.get("disable-model-invocation", "")).strip().lower()
    if disable_flag != "true":
        return
    description = frontmatter.get("description", "")
    if "\n" in description:
        findings.append(Finding("S15", "warn", "disable-model-invocation:trueですがdescriptionが複数行です（1行の要約が推奨）"))
    elif len(description) > USER_INVOKED_DESCRIPTION_MAX_LEN:
        findings.append(
            Finding(
                "S15",
                "warn",
                f"disable-model-invocation:trueですがdescriptionが{len(description)}文字あります"
                f"（{USER_INVOKED_DESCRIPTION_MAX_LEN}文字以内の一行要約が推奨）",
            )
        )


def check_skill(skill_dir):
    findings = []
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)

    check_name(frontmatter, findings)
    check_description(frontmatter, findings)
    check_body_length(body, findings)
    check_references(skill_dir, body, findings)
    check_symlink(name, findings)
    check_marketplace(name, findings)
    check_readme(name, findings)
    check_duplicate_blocks(skill_dir, body, findings)
    check_user_invoked_description(frontmatter, findings)

    return findings


def main():
    skill_dirs = sorted(p.parent for p in SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_dirs:
        print(f"{SKILLS_DIR} 配下に SKILL.md が見つかりません")
        return 0

    total_errors = 0
    total_warnings = 0

    for skill_dir in skill_dirs:
        findings = check_skill(skill_dir)
        print(f"=== {skill_dir.name} ===")
        if not findings:
            print("  OK")
        for finding in findings:
            print(f"  [{finding.check_id}] {finding.severity}: {finding.message}")
            if finding.severity == "error":
                total_errors += 1
            else:
                total_warnings += 1
        print()

    print(f"{len(skill_dirs)} skill(s) checked: {total_errors} error(s), {total_warnings} warning(s)")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
