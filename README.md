# skills

自分が開発した Claude Skills を整理・管理するためのリポジトリ。

[`npx skills`](https://github.com/vercel-labs/skills) および Claude Code のプラグイン機構の両方から利用できるように構成している。

## インストール方法

### npx skills を使う場合

```bash
npx skills add ryohma0510/skills
```

### Claude Code のプラグインとして使う場合

```
/plugin marketplace add ryohma0510/skills
/plugin install productivity@ryohma0510-skills
/plugin install engineering@ryohma0510-skills
```

## ディレクトリ構成

```
skills/
├── README.md
├── .gitignore
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
- 新しいスキルを `skills/` 配下に追加したら、`.claude-plugin/marketplace.json` の `plugins[].skills` 配列にも `./skills/<skill-name>` を追記する(npx skills 側は `skills/` 配下を自動で認識するが、Claude plugin 側はこのマニフェストで明示する必要がある)。

## スキル一覧

| スキル名 | 概要 |
| --- | --- |
| [copy-skill](skills/copy-skill/SKILL.md) | GitHub上に公開されたスキルフォルダを取得し、外国語なら内容を変えずに日本語へ翻訳して取り込む |
| [grilling](skills/grilling/SKILL.md) | ユーザーの計画・決定・アイデアを容赦なく問い詰め、共通理解に達するまで一問一答で深掘りする |
| [handoff](skills/handoff/SKILL.md) | 現在の会話をハンドオフドキュメントにまとめ、他のエージェントが引き継げるようにする |
| [my-code-review](skills/my-code-review/SKILL.md) | diff や checkout 済みの他人の PR を設計品質の観点でレビューする |
| [skill-design-principles](skills/skill-design-principles/SKILL.md) | スキルをうまく書き・編集するためのリファレンス。スキルを予測可能にする語彙と原則 |

## 開発フロー

新しいスキルの作成・改善には `skill-creator` スキルの利用を推奨する(ドラフト作成 → テストケース実行 → 評価 → 改善のループ)。
