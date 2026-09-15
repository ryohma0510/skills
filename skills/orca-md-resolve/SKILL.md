---
name: orca-md-resolve
description: Orca の Markdown レビューコメント（File / Lines / Excerpt）から、作業ツリー上の正しい行を特定する。reported lines がズレているとき、「行を特定して」「どこか教えて」と言われたとき、ペイロードを貼ってローカルで直すとき、他のスキルが行特定を必要とするときに使う。
trigger: /orca-md-resolve
argument-hint: "Orca のペイロード"
---

# Orca Markdown → resolved lines

`excerpt` が source of truth。`reported lines` は hint。結果は `file:start[-end]` の行特定であり、PR への投稿はしない。

ペイロード例とマッチの具体形が要るときに [examples.md](examples.md) を読む。

## 1. パース

ユーザーが貼った文面を、次のスクリプトでコメントの配列にする。複数件を最初から扱う。

```bash
python3 <このスキルのディレクトリ>/scripts/resolve-excerpt-lines.py parse
```

標準入力にペイロードを渡す。各要素の `hint_start` / `hint_end` が reported lines。`excerpt` は引用記号を外した選択テキスト。`user_comment` があれば保持する（行特定には使わない）。

完了条件: コメント配列があり、各件に `file` と `excerpt` がある。

## 2. resolved line

対象は作業ツリーの `file`。呼び出し元が本文を一時ファイルに置いているときは、そのパスを `--file` に渡し、報告上の `file` はペイロードのパスのままにする。

```bash
python3 <このスキルのディレクトリ>/scripts/resolve-excerpt-lines.py resolve \
  --file <path> --excerpt <excerpt> --hint-start <hint_start> --hint-end <hint_end>
```

行特定はこのスクリプトに任せる。

- `status=resolved` → `start_line` / `end_line` を採用する。1行なら両方同じ。
- `status=ambiguous` → `candidates` を出して選ばせる。
- `status=not_found` → 理由を残す。

完了条件: 全件が resolved / ambiguous / not_found のいずれかに分かれている。採用する行はスクリプトの `start_line` / `end_line` である。

## 3. 報告

件ごとに次を出す。以降の指示・修正・引用は、ここ出た resolved 行を使う。

```
[n] {file}:{resolved_line}
    reported lines: {hint_start}-{hint_end}  →  resolved: {start}[-{end}]
    excerpt: ...
    user comment: ...   # あれば
    status: resolved | ambiguous | not_found
```

完了条件: 全件に status があり、resolved の件は `file:line`（複数行なら範囲）が書かれている。
