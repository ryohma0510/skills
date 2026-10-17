---
name: ponytail-help
description: "ponytail のレベル・スキル・コマンドのクイックリファレンス。一回限りの表示。/ponytail-help、「ponytail help」「how do I use ponytail」のとき"
---
<!--
source: https://github.com/DietrichGebert/ponytail/tree/main/skills/ponytail-help
imported_at: 2026-10-17
upstream_commit: 16352ac229eb08a9598dcae48fe9f2b342567d86
license: MIT (LICENSE)
-->

# Ponytail Help

呼び出されたらこのリファレンスカードを表示する。一回限り。モード変更・フラグファイル・永続化はしない。

## レベル

| レベル | トリガー | 変更の内容 |
|-------|---------|-------------|
| **Lite** | `/ponytail lite` | 依頼どおり作り、より小さい選択肢を1行で示す。 |
| **Full** | `/ponytail` | 最小の完結した変更、ロジックに要る箇所のチェック、省略とリスクを述べた返答。既定。 |
| **Ultra** | `/ponytail ultra` | 依頼を疑い、作る前に押し返す。 |

レベルは変更またはセッション終了まで維持。

## スキル

| スキル | トリガー | 内容 |
|-------|---------|------|
| **ponytail** | `/ponytail` | 怠けモード本体。新コード最小、省略とリスクを明示した返答。 |
| **ponytail-review** | `/ponytail-review` | diff の品質レビュー: バグ、セキュリティ、負荷、テスト不足、速度、削れるもの。各指摘に何が起きるかと直し方。 |
| **ponytail-audit** | `/ponytail-audit` | リポジトリ全体への同品質レビュー。優先度付き。 |
| **ponytail-debt** | `/ponytail-debt` | `shortcut:` コメントを台帳として収集。 |
| **ponytail-gain** | `/ponytail-gain` | ベンチマークに基づく削減効果（コード・コスト・速度）のスコアボード。 |
| **ponytail-help** | `/ponytail-help` | このカード。 |

Codex CLI と IDE 拡張では `$ponytail:ponytail`、`$ponytail:ponytail-review`、`$ponytail:ponytail-help` で呼ぶ。Claude Code と OpenCode は上記スラッシュコマンド（OpenCode は6つすべてスラッシュコマンド）。

## 解除

「stop ponytail」または「normal mode」。`/ponytail` で再開。`/ponytail off` も可。

## Band（Claude Code）

`/ponytail band` でプロンプト上のバンド表示の on/off。`/ponytail band on` / `off` で直接指定。レベルは維持。`/ponytail band import` で過去の Claude Code セッション（コスト、エージェント時間、トークン）をボードに取り込む。

## 既定モードの設定

既定 = `full`、毎セッション自動有効。変更方法:

**環境変数**（最優先）:
```bash
export PONYTAIL_DEFAULT_MODE=ultra
```

**設定ファイル**（`~/.config/ponytail/config.json`、Windows: `%APPDATA%\ponytail\config.json`）:
```json
{ "defaultMode": "lite" }
```

`"off"` にするとセッション開始時の自動有効化を止め、必要なとき `/ponytail` で手動有効化。

解決順: 環境変数 > 設定ファイル > `full`。

## 更新

自動更新: `/plugin` → Marketplaces → ponytail → Enable auto-update。Claude Code は起動時に新版を取得（プロンプト時は `/reload-plugins`）。手動: `/plugin marketplace update ponytail` のあと `/reload-plugins`。

`/plugin` が無い場合は Claude Code が古い。更新して再起動（`npm install -g @anthropic-ai/claude-code@latest` または `brew upgrade claude-code`）。他ホストは各々の更新手順。

## 詳細

ドキュメントと例: https://github.com/DietrichGebert/ponytail
