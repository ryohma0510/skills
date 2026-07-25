---
name: token-diet
description: Claude Code のシステムプロンプトを軽量化する設定を ~/.claude/settings.json に適用し、削減量を実測する。
disable-model-invocation: true
---

# token-diet

Claude Code は毎リクエスト、ツール定義・スキルカタログ・機能別のシステム指示を送る。使っていない機能の分も一緒に送られ、毎ターン課金される。設定でこれを削る。

削るかどうかは**実測**で決める。効きそうに見える設定の大半は誤差の範囲で、実測せずに足した設定は、失う機能の分だけ損になる。

## 適用する

### 1. ベースラインを実測する

`scripts/measure.sh` を実行し、出力されたトークン数を控える。

**完了条件**: 変更前の数値を記録した。

### 2. 現在の設定を退避する

`~/.claude/settings.json` があれば `~/.claude/settings.json.bak` にコピーする。無ければ新規作成になる旨をユーザーに伝える。

**完了条件**: 既存ファイルの有無を確かめ、あればバックアップを取った。

### 3. プリセットを適用する

以下を `~/.claude/settings.json` にマージする。既存のキーは残し、衝突するキーだけ上書きする。`permissions.deny` に要素があれば置き換えず追記する。

```json
{
  "permissions": {
    "deny": ["AskUserQuestion"]
  },
  "disableWorkflows": true,
  "disableArtifact": true,
  "disableBundledSkills": true,
  "disableClaudeAiConnectors": true
}
```

**完了条件**: マージ後の JSON が妥当で、元々あった設定が1つも消えていない。

### 4. 再起動する

設定は起動時に読み込まれる。書き込んだだけでは効かない。ユーザーに Claude Code の再起動を促す。

**完了条件**: 再起動が必要であることを伝えた。

### 5. 再計測する

再起動後に `scripts/measure.sh` を再実行し、手順1の値と並べて差分を示す。セッション内なら `/context` でも内訳を確認できる。

**完了条件**: 削減量を数値で示した。

## 何を失うか

| 設定 | 失うもの |
| --- | --- |
| `disableBundledSkills` | 組み込みスキル全て（pdf / xlsx / docx / pptx / dataviz / skill-creator / update-config / security-review など）。スラッシュコマンドは打てる状態で残る |
| `disableArtifact` | Artifact の公開。Artifact を前提にしたスキルも動かなくなる |
| `disableWorkflows` | 動的ワークフロー |
| `disableClaudeAiConnectors` | claude.ai コネクタ |
| `deny: AskUserQuestion` | 選択肢UI。質問はテキストで届く |

## 元に戻す

`~/.claude/settings.json.bak` を書き戻して再起動する。バックアップが無い場合は手順3で足したキーを削除する。

## プリセットを組み替えるとき

キー名も削減量も Claude Code のバージョンで変わる。バージョンが上がったとき、別の機能も削りたいとき、削減量が期待に届かないときは、[`references/measurements.md`](references/measurements.md) の手順で測り直してからプリセットを書き換える。
