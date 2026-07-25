---
name: token-diet
description: Claude Code のシステムプロンプトを軽量化する設定を ~/.claude/settings.json に適用し、削減量を実測する。
disable-model-invocation: true
---

# token-diet

Claude Code は毎リクエスト、ツール定義・スキルカタログ・機能別のシステム指示を送る。使っていない機能の分も一緒に送られ、毎ターン課金される。設定でこれを削る。

削るかどうかは**実測**で決める。効きそうに見える設定の大半は誤差の範囲で、実測せずに足した設定は、失う機能の分だけ損になる。

## 適用する

### 1. 適用先を決める

| 置き場所 | 効く範囲 | git |
| --- | --- | --- |
| `~/.claude/settings.json` | 全プロジェクト | 対象外 |
| `<repo>/.claude/settings.json` | そのリポジトリのみ | コミットされ、クローンした全員に効く |
| `<repo>/.claude/settings.local.json` | そのリポジトリの自分だけ | `.gitignore` に入れる |

削減量はどこに置いても変わらない。全体を軽くしたいならグローバルを選ぶ。

リポジトリに置く場合、そこで働く人全員が同じ機能を失う。組み込みスキルに依存する作業をするリポジトリでは、グローバルか `settings.local.json` を選ぶ。

**完了条件**: 適用先のパスを1つに確定した。

### 2. ベースラインを実測する

`scripts/measure.sh` を実行し、出力されたトークン数を控える。プロジェクトに置く場合は、そのディレクトリで `scripts/measure.sh --here` を使う。素の `measure.sh` は空ディレクトリで走るためプロジェクト設定を拾わない。

**完了条件**: 変更前の数値を記録した。

### 3. 現在の設定を退避する

適用先のファイルがあれば `.bak` を付けてコピーする。無ければ新規作成になる旨をユーザーに伝える。

**完了条件**: 既存ファイルの有無を確かめ、あればバックアップを取った。

### 4. プリセットを適用する

以下を適用先にマージする。既存のキーは残し、衝突するキーだけ上書きする。`permissions.deny` に要素があれば置き換えず追記する。

```json
{
  "permissions": {
    "deny": ["AskUserQuestion"]
  },
  "disableWorkflows": true,
  "disableArtifact": true,
  "disableBundledSkills": true,
  "disableClaudeAiConnectors": true,
  "skillOverrides": {
    "docx": "user-invocable-only",
    "xlsx": "user-invocable-only",
    "pptx": "user-invocable-only",
    "pdf": "user-invocable-only"
  }
}
```

`skillOverrides` のキーは `~/.claude/skills/` に実際に入っているスキル名に合わせる。並んでいる4つはファイルを触るときに自分から呼ぶ種類なので、`user-invocable-only` にしても `/docx` のように名前で呼べる。存在しない名前を書いても無視されるだけで害はない。

**完了条件**: マージ後の JSON が妥当で、元々あった設定が1つも消えていない。

### 5. 再起動する

設定は起動時に読み込まれる。書き込んだだけでは効かない。ユーザーに Claude Code の再起動を促す。

**完了条件**: 再起動が必要であることを伝えた。

### 6. 再計測する

再起動後、手順2と同じ measure.sh の呼び方で測り直し、2つの数値を並べて差分を示す。セッション内なら `/context` でも内訳を確認できる。

**完了条件**: 削減量を数値で示した。

## 何を失うか

| 設定 | 失うもの |
| --- | --- |
| `disableBundledSkills` | バイナリに同梱されたスキル全て（dataviz / update-config / security-review など）。スラッシュコマンドは打てる状態で残る。`~/.claude/skills/` に自分で入れたスキルは消えず、カタログ分のトークンも残る |
| `disableArtifact` | Artifact の公開。Artifact を前提にしたスキルも動かなくなる |
| `disableWorkflows` | 動的ワークフロー |
| `disableClaudeAiConnectors` | claude.ai コネクタ |
| `deny: AskUserQuestion` | 選択肢UI。質問はテキストで届く |
| `skillOverrides` | 挙げたスキルを Claude が自発的に思いつかなくなる。`/名前` で呼べば従来どおり動く |

## 元に戻す

手順3で取った `.bak` を書き戻して再起動する。バックアップが無い場合は手順4で足したキーを削除する。

## プリセットを組み替えるとき

キー名も削減量も Claude Code のバージョンで変わる。バージョンが上がったとき、別の機能も削りたいとき、削減量が期待に届かないときは、[`references/measurements.md`](references/measurements.md) の手順で測り直してからプリセットを書き換える。
