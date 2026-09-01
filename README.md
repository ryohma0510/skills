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

#### 共通ルールを user scope のルートコンテキストに配る

`.apm/instructions/` に置いた instruction のうち `applyTo` を持たないものは、
グローバルインストールのあと `apm compile --global` でルートコンテキストに展開される。

- Claude Code: `~/.claude/CLAUDE.md`（または `$CLAUDE_CONFIG_DIR/CLAUDE.md`）
- Cursor: `~/.cursor/AGENTS.md`

```bash
apm install ryohma0510/skills --target claude,cursor --global
apm compile --global
```

`apm install -g` だけではルートコンテキストは書かれない。instruction を載せるには `apm compile --global` が要る。

生成されたファイルには APM のマーカーが入り、次回以降の compile で上書きされる。
マーカーのない手書きの `CLAUDE.md` / `AGENTS.md` が既にある場合は上書きされないので、
このリポジトリで管理するなら手書きのルートコンテキストは置かない。

いま入っている常時適用ルール:

- `plain-text-questions` — 質問はチャット本文にプレーンテキストで書く。Claude Code の `AskUserQuestion` と Cursor の `AskQuestion`（Question UI）は使わない。

Claude Code では、同じ内容を PreToolUse フックでも遮断する。`apm install --target claude --global` が `~/.claude/settings.json` にマージし、`AskUserQuestion` の呼び出しを拒否してチャット本文へ誘導する。Cursor の Question UI にはフックが発火しないので、無効化は instruction に頼る。

### Claude Code のプラグインとして使う場合

```
/plugin marketplace add ryohma0510/skills
/plugin install ryohma0510-skills@ryohma0510-skills
```

配布単位は apm パッケージと 1:1 で、プラグインは 1 つだけ。apm 側に複数プラグインへ分割する概念がないため、
Claude Code 側もリポジトリ全体を 1 プラグインとして配る。
プラグイン経路はスキルだけを配る。instruction とフックは apm 経由で入れる。

## ディレクトリ構成

```
skills/
├── README.md
├── .gitignore
├── apm.yml                # apm パッケージのマニフェスト
├── .apm/
│   ├── instructions/      # 常時適用のルール。applyTo なし。apm compile --global でルートコンテキストへ
│   └── hooks/             # Claude Code の PreToolUse。apm install が settings.json にマージする
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
- `.apm/instructions/*.instructions.md` の frontmatter は `description` のみ。`applyTo` を書くと path 限定ルールになり、ルートコンテキストには載らない(`scripts/check_skills.py` の S19 が検査する)。
- `.apm/hooks/*.json` の command が指すスクリプトは同ディレクトリに置く(`scripts/check_skills.py` の S20 が検査する)。
- `apm.yml` の `version` と `marketplace.json` の `metadata.version` は同じ値に揃える(`scripts/check_skills.py` の S18 が検査する)。skills/ または .apm/ を変えたら version を上げる。

## スキル一覧

| スキル名 | 概要 |
| --- | --- |
| [code-comments](skills/code-comments/SKILL.md) | コメント・ドキュメンテーションコメントに何を書き何を書かないかの原則。アンチパターンの検出とラベル付けも行う |
| [copy-skill](skills/copy-skill/SKILL.md) | GitHub上に公開されたスキルフォルダを取得し、外国語なら内容を変えずに日本語へ翻訳して取り込む |
| [grilling](skills/grilling/SKILL.md) | ユーザーの計画・決定・アイデアを容赦なく問い詰め、共通理解に達するまで一問一答で深掘りする |
| [handoff](skills/handoff/SKILL.md) | 会話を要約し、次のエージェント/セッションが引き継げるドキュメントにする |
| [implement](skills/implement/SKILL.md) | 実装作業の入り口。`tdd` でテストファーストに進め、`code-comments` でコメント品質を確認し、完了後に `pr-create` と `review-loop` を実行する |
| [pr-create](skills/pr-create/SKILL.md) | 変更を push し、base ブランチの推定と日本語タイトル/description の生成を経て draft PR を作成する |
| [reply-review](skills/reply-review/SKILL.md) | PR のレビューコメントに対応する。対応要否の判断・同種箇所への横展開・返信・自分と Bot のスレッドの resolve まで行う |
| [review](skills/review/SKILL.md) | 変更差分をレビューし、バグや改善点を深刻度順に整形して表示する |
| [review-loop](skills/review-loop/SKILL.md) | サブエージェントに `review` を実行させ、確信度の高い指摘を自分で修正するループを指定回数(既定2周)回す |
| [sanitize-doc](skills/sanitize-doc/SKILL.md) | 文章を完成品として仕上げ直す。装飾文言と会話の名残の両方をまとめて削る |
| [skill-design-principles](skills/skill-design-principles/SKILL.md) | Predictable なスキルを書くための語彙と原則。スキルの作成・編集・診断時に参照する |
| [tdd](skills/tdd/SKILL.md) | red → green のループを回す手順。seam の確定・red・green の各ステップと vertical slice |
| [test-design](skills/test-design/SKILL.md) | 良いテストの設計。seam でのテスト、DAMP、should/when 命名と Given-When-Then、アンチパターン、モックの境界。規約違反を検出する lint スクリプトを同梱 |
| [trim-ai-smell](skills/trim-ai-smell/SKILL.md) | Markdown から装飾文言(煽り・脅し、唯一の記述への強調、意味を変えない強度副詞など)を削る。新規執筆時にも常に適用する |
| [trim-session-context](skills/trim-session-context/SKILL.md) | セッション中に作った成果物から会話の名残(production residue)を削り、単独で読める完成品に仕上げ直す |

## 開発フロー

新しいスキルの作成・改善には `skill-creator` スキルの利用を推奨する(ドラフト作成 → テストケース実行 → 評価 → 改善のループ)。
