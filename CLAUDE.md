# CLAUDE.md

このリポジトリは Claude Skills のコレクション。`npx skills` と Claude Code プラグインの両方から配布する。

## スキルを追加・変更・削除したら必ずやること

スキル本体(`skills/<name>/`)を触ったら、**同じコミット内で**以下を最後まで確認する。特に忘れやすいのは 1 と 2。

1. **バージョンを上げる** — `.claude-plugin/marketplace.json` の `metadata.version` を semver で更新する。
   - スキルの追加・削除、既存スキルの挙動が変わる変更 → minor (`1.1.0` → `1.2.0`)
   - 誤字修正・言い回しの調整など挙動が変わらない変更 → patch (`1.1.0` → `1.1.1`)
   - `plugins[]` の構成が壊れる変更(プラグイン名変更など) → major
2. **README.md を更新する** — 「スキル一覧」表に行を追加・修正・削除する。リンクは `skills/<name>/SKILL.md`。概要は `SKILL.md` の `description` と食い違わせない。
3. **marketplace.json の `plugins[].skills` に登録する**(新規追加・削除時) — `./skills/<name>`。エンジニアリング系は `engineering`、それ以外は `productivity`。
4. **`.claude/skills/<name>` のシンボリックリンク**(新規追加・削除時) — `ln -s ../../skills/<name> .claude/skills/<name>`。削除したスキルのリンクは消す。
5. **チェックスクリプトを通す** — 下の 2 本を error 0 で通す。

コミット前のセルフチェック:

```bash
python3 scripts/check_skills.py                          # S01-S15: SKILL.md 単体 + 3・4・READMEの行
python3 scripts/check_version_bump.py --base origin/main  # V01-V03: versionの更新漏れ
```

- `check_skills.py` — 3 の漏れ(S12)、4 の漏れ(S11)、README の行の欠落(S13)を検出する。
- `check_version_bump.py` — base ref との merge-base を取り、`skills/` に変更があるのに `metadata.version` が据え置き(V01)/後退(V02)していないかを見る。`SKILL.md` の `description` が変わったのに README.md が未更新なら warn(V03)。
- CI(`.github/workflows/check-skills.yml`)は PR で両方を実行する。`check_version_bump.py` は PR のみ(base ref が必要なため)。

## スキルの書き方

- `SKILL.md` の frontmatter は `name` と `description` が必須。`description` には「いつ使うか(トリガー条件)」と「何をするか」を具体的に書く。
- ユーザーが明示的に呼ぶスキル(`disable-model-invocation: true`)の `description` は 1 行・200 文字以内に収める。
- 本文は 500 行以内。超えるなら `references/` に分割する。
- 外部から取り込んだスキルは、frontmatter 直後の HTML コメントに `source:` と `imported_at:` を残す。
- 書き方の原則は `skills/skill-design-principles/SKILL.md` を参照。
