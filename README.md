# skills

自分が開発した Claude Skills を整理・管理するためのリポジトリ。

## ディレクトリ構成

各スキルはリポジトリ直下に1フォルダとして配置する。

```
skills/
├── README.md
├── .gitignore
└── <skill-name>/
    ├── SKILL.md        # 必須。YAML frontmatter (name, description) + 本文
    ├── scripts/        # 任意。決定的・反復的な処理を行う実行可能コード
    ├── references/      # 任意。必要に応じて読み込むドキュメント
    └── assets/          # 任意。出力に使うテンプレート・アイコン等
```

- `SKILL.md` の `description` には、いつ使うか(トリガー条件)と何をするかを具体的に書く。
- `SKILL.md` 本体は 500 行程度に収め、肥大化する場合は `references/` に分割する。

## スキル一覧

| スキル名 | 概要 |
| --- | --- |
| _(まだなし)_ | |

## 開発フロー

新しいスキルの作成・改善には `skill-creator` スキルの利用を推奨する(ドラフト作成 → テストケース実行 → 評価 → 改善のループ)。
