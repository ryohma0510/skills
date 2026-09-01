#!/usr/bin/env python3
"""skills/ または .apm/ を変更したら marketplace.json の version が上がっているかを検査する (V01-V03)。

check_skills.py が拾えない「バージョン更新の漏れ」を、base ref との差分から決定論的に検出する。
CI でもローカルでも同じ判定になるよう、比較対象は merge-base に固定する。

    python3 scripts/check_version_bump.py               # base は origin/main (または GITHUB_BASE_REF)
    python3 scripts/check_version_bump.py --base main
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = ".claude-plugin/marketplace.json"
README_PATH = "README.md"
SKILLS_PREFIX = "skills/"
APM_PREFIX = ".apm/"

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} に失敗しました: {result.stderr.strip()}")
    return result.stdout


def default_base():
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        return f"origin/{base_ref}"
    return "origin/main"


def resolve_merge_base(base):
    """base と HEAD の merge-base を返す。base が無ければ候補にフォールバックする。"""
    candidates = [base]
    if base.startswith("origin/"):
        candidates.append(base[len("origin/") :])
    else:
        candidates.append(f"origin/{base}")

    for candidate in candidates:
        try:
            return git("merge-base", candidate, "HEAD").strip(), candidate
        except RuntimeError:
            continue
    raise RuntimeError(f"base ref '{base}' を解決できませんでした (fetch されていない可能性があります)")


def changed_files(merge_base):
    output = git("diff", "--name-only", merge_base, "HEAD")
    return [line for line in output.splitlines() if line]


def read_version(ref, path):
    """ref 時点の marketplace.json から metadata.version を読む。無ければ None。"""
    if ref is None:
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
    else:
        try:
            text = git("show", f"{ref}:{path}")
        except RuntimeError:
            return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path} のパースに失敗しました ({ref or 'working tree'}): {exc}")
    return data.get("metadata", {}).get("version")


def parse_semver(version, label):
    if not isinstance(version, str):
        raise RuntimeError(f"{label} の version が文字列ではありません: {version!r}")
    match = SEMVER_RE.match(version.strip())
    if not match:
        raise RuntimeError(f"{label} の version '{version}' が semver (x.y.z) 形式ではありません")
    return tuple(int(part) for part in match.groups())


def skill_description_changed(merge_base, files):
    """SKILL.md の frontmatter description 行が変わったスキルの一覧を返す。"""
    changed = []
    for path in files:
        if not (path.startswith(SKILLS_PREFIX) and path.endswith("/SKILL.md")):
            continue
        diff = git("diff", "-U0", merge_base, "HEAD", "--", path)
        for line in diff.splitlines():
            if line.startswith(("+++", "---")):
                continue
            if line.startswith(("+", "-")) and line[1:].lstrip().startswith("description:"):
                changed.append(path.split("/")[1])
                break
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=default_base(), help="比較対象の ref (既定: origin/main)")
    args = parser.parse_args()

    try:
        merge_base, resolved_base = resolve_merge_base(args.base)
        files = changed_files(merge_base)
        touched_skills = sorted(
            {path.split("/")[1] for path in files if path.startswith(SKILLS_PREFIX) and "/" in path[len(SKILLS_PREFIX) :]}
        )
        touched_apm = any(path.startswith(APM_PREFIX) for path in files)

        if not touched_skills and not touched_apm:
            print(f"base: {resolved_base} ({merge_base[:9]})")
            print("skills/ と .apm/ に変更がないため version チェックはスキップします")
            return 0

        head_version = read_version(None, MARKETPLACE_PATH)
        base_version = read_version(merge_base, MARKETPLACE_PATH)

        errors = []
        warnings = []

        if head_version is None:
            errors.append(("V01", f"{MARKETPLACE_PATH} に metadata.version がありません"))
            head_tuple = None
        else:
            head_tuple = parse_semver(head_version, "HEAD")

        if base_version is None:
            base_tuple = None
        else:
            base_tuple = parse_semver(base_version, resolved_base)

        if head_tuple is not None and base_tuple is not None:
            if head_tuple == base_tuple:
                changed = []
                if touched_skills:
                    changed.append(f"スキル: {', '.join(touched_skills)}")
                if touched_apm:
                    changed.append(".apm/")
                errors.append(
                    (
                        "V01",
                        "パッケージ内容を変更しているのに version が "
                        f"{base_version} のまま据え置かれています "
                        f"(変更: {', '.join(changed)})",
                    )
                )
            elif head_tuple < base_tuple:
                errors.append(("V02", f"version が base より小さくなっています: {base_version} -> {head_version}"))

        description_changed = skill_description_changed(merge_base, files)
        if description_changed and README_PATH not in files:
            warnings.append(
                (
                    "V03",
                    f"SKILL.md の description が変わったのに {README_PATH} が未更新です "
                    f"(対象: {', '.join(description_changed)})",
                )
            )
    except RuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    print(f"base: {resolved_base} ({merge_base[:9]})")
    if touched_skills:
        print(f"変更されたスキル: {', '.join(touched_skills)}")
    if touched_apm:
        print("変更された .apm/: yes")
    print(f"version: {base_version} -> {head_version}")
    for check_id, message in errors:
        print(f"  [{check_id}] error: {message}")
    for check_id, message in warnings:
        print(f"  [{check_id}] warn: {message}")
    if not errors and not warnings:
        print("  OK")
    print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
