# skills

自分が開発した Claude Skills を整理・管理するためのリポジトリ。

[apm (Agent Package Manager)](https://github.com/microsoft/apm) および Claude Code のプラグイン機構の両方から利用できるように構成している。

## インストール方法

### apm を使う場合

```bash
# リポジトリ内の全スキルを .claude/skills/ に配置する
apm install ryohma0510/skills --target claude

# 個別のスキルだけ入れる場合
apm install ryohma0510/skills/tdd --target claude
```

apm 自体のインストールは [apm の README](https://github.com/microsoft/apm#installation) を参照。

#### 共通ルールを `~/.claude/CLAUDE.md` として配る

`.apm/instructions/` に置いた instruction のうち `applyTo` を持たないものは、
user scope でインストールすると `~/.claude/CLAUDE.md` (または `$CLAUDE_CONFIG_DIR/CLAUDE.md`) に展開される。
全セッションのコンテキストに載るため、会話の返答にも適用される。

```bash
apm install ryohma0510/skills --target claude --global
```

生成されたファイルには APM のマーカーが入り、次回以降の install で上書きされる。
マーカーのない手書きの `CLAUDE.md` が既にある場合は `skipped-hand-authored` となり上書きされないので、
このリポジトリで管理するなら手書きの `CLAUDE.md` は置かない。

### Claude Code のプラグインとして使う場合

```
/plugin marketplace add ryohma0510/skills
/plugin install ryohma0510-skills@ryohma0510-skills
```

配布単位は apm パッケージと 1:1 で、プラグインは 1 つだけ。apm 側に複数プラグインへ分割する概念がないため、
Claude Code 側もリポジトリ全体を 1 プラグインとして配る。

## ディレクトリ構成

```
skills/
├── README.md
├── .gitignore
├── apm.yml                # apm パッケージのマニフェスト
├── .apm/
│   └── instructions/      # 常時適用のルール。applyTo なしで ~/.claude/CLAUDE.md に展開される
├── .claude-plugin/
│   └── marketplace.json   # Claude Code プラグインとして配布するためのマニフェスト
└── skills/
    └── <skill-name>/
        ├── SKILL.md        # 必須。YAML frontmatter (name, description) + 本文
        ├── scripts/        # 任意。決定的・反復的な処理を行う実行可能コード
        ├── references/      # 任意。必要に応じて読み込むドキュメント
        └── assets/          # 任意。出力に使うテンプレート・アイコン等
```

- `SKILL.md` の `description` には、いつ使うか(トリガー条件)と何をするかを具体的に書く。
- `SKILL.md` 本体は 500 行程度に収め、肥大化する場合は `references/` に分割する。
- 新しいスキルを `skills/` 配下に追加したら、`.claude-plugin/marketplace.json` の `plugins[0].skills` 配列にも `./skills/<skill-name>` を追記する(Claude plugin 側はこのマニフェストで明示する必要がある)。
- `.apm/instructions/*.instructions.md` の frontmatter は `description` のみ。`applyTo` を書くと `.claude/rules/<name>.md` への path 限定ルールになり、CLAUDE.md には載らない。
- `apm.yml` の `version` と `marketplace.json` の `metadata.version` は同じ値に揃える(`scripts/check_skills.py` の S18 が検査する)。

## スキル一覧

| スキル名 | 概要 |
| --- | --- |
| [code-comments](skills/code-comments/SKILL.md) | コメント・ドキュメンテーションコメントに何を書き何を書かないかの原則。アンチパターンの検出とラベル付けも行う |
| [copy-skill](skills/copy-skill/SKILL.md) | GitHub上に公開されたスキルフォルダを取得し、外国語なら内容を変えずに日本語へ翻訳して取り込む |
| [doc-trim](skills/doc-trim/SKILL.md) | Markdown から装飾文言(煽り・脅し、唯一の記述への強調、意味を変えない強度副詞など)を削る。新規執筆時にも常に適用する |
| [grilling](skills/grilling/SKILL.md) | ユーザーの計画・決定・アイデアを容赦なく問い詰め、共通理解に達するまで一問一答で深掘りする |
| [handoff](skills/handoff/SKILL.md) | 会話を要約し、次のエージェント/セッションが引き継げるドキュメントにする |
| [implement](skills/implement/SKILL.md) | 実装作業の入り口。`tdd` でテストファーストに進め、`code-comments` でコメント品質を確認し、完了後に `pr-create` と `review-loop` を実行する |
| [pr-create](skills/pr-create/SKILL.md) | 変更を push し、base ブランチの推定と日本語タイトル/description の生成を経て draft PR を作成する |
| [reply-review](skills/reply-review/SKILL.md) | PR のレビューコメントに対応する。対応要否の判断・同種箇所への横展開・返信・自分と Bot のスレッドの resolve まで行う |
| [review](skills/review/SKILL.md) | 変更差分をレビューし、バグや改善点を深刻度順に整形して表示する |
| [review-loop](skills/review-loop/SKILL.md) | サブエージェントに `review` を実行させ、確信度の高い指摘を自分で修正するループを指定回数(既定2周)回す |
| [skill-design-principles](skills/skill-design-principles/SKILL.md) | Predictable なスキルを書くための語彙と原則。スキルの作成・編集・診断時に参照する |
| [tdd](skills/tdd/SKILL.md) | red → green のループを回す手順。seam の確定・red・green の各ステップと vertical slice |
| [test-design](skills/test-design/SKILL.md) | 良いテストの設計。seam でのテスト、DAMP、should/when 命名と Given-When-Then、アンチパターン、モックの境界。規約違反を検出する lint スクリプトを同梱 |

## 開発フロー

新しいスキルの作成・改善には `skill-creator` スキルの利用を推奨する(ドラフト作成 → テストケース実行 → 評価 → 改善のループ)。
