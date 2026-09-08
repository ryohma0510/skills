---
name: orca-md-pr-comments
description: Orca の Markdown レビューコメント（File / Lines / Excerpt / User comment）を GitHub PR の inline comment として投稿する。excerpt から resolved line を決め、レビューコメントとして載せるとき、または /orca-md-pr-comments のときに使う。
trigger: /orca-md-pr-comments
argument-hint: "Orca のペイロード。対象 PR は省略可"
---

# Orca Markdown → PR inline comment

`excerpt` が source of truth。`reported lines` は hint。投稿先はファイル行に付く inline comment。

ペイロード例と行特定例は、パースやマッチの具体形が要るときに [examples.md](examples.md) を読む。

## 1. 投稿意図

次のいずれかがあるときだけこのスキルを進める。

- 「レビューコメント」「inline comment」「PR に投稿」など、GitHub へ載せることを指す語
- `/orca-md-pr-comments`

`File` / `Lines` / `Excerpt` / `User comment` を実装中の修正指示として貼っただけなら、ここで終える。行特定も投稿もしない。

完了条件: 投稿意図があると言えた。無ければこのスキルを終えている。

## 2. パース

ユーザーが貼った文面を、次のスクリプトでコメントの配列にする。複数件を最初から扱う。

```bash
python3 <このスキルのディレクトリ>/scripts/resolve-excerpt-lines.py parse
```

標準入力にペイロードを渡す。各要素の `hint_start` / `hint_end` が reported lines。`excerpt` は引用記号を外した選択テキスト。`user_comment` は投稿の種。

完了条件: コメント配列があり、各件に `file` と `excerpt` と `user_comment` がある。

## 3. 対象 PR

URL または番号があればそれを使う。省略時は現在ブランチの PR。

```bash
gh pr view --json number,url,headRefOid
gh pr list --head "$(git branch --show-current)" --json number,url,headRefOid
```

0件または2件以上なら、URL を出してもらい中断する。repo 省略時はカレント。

完了条件: owner / repo / PR 番号 / head SHA が1組に決まっている。

## 4. resolved line

各コメントについて、作業ツリーの `file` を読む。無ければ PR head から取る。

```bash
python3 <このスキルのディレクトリ>/scripts/resolve-excerpt-lines.py resolve \
  --file <path> --excerpt <excerpt> --hint-start <hint_start> --hint-end <hint_end>
```

行特定はこのスクリプトに任せる。

- `status=resolved` → `start_line` / `end_line` を採用する。1行なら両方同じ。
- `status=ambiguous` → 投稿せず、`candidates` を出して選ばせる。
- `status=not_found` → 投稿せず、理由を残す。

完了条件: 全件が resolved / ambiguous / not_found のいずれかに分かれている。投稿に使う行はスクリプトの `start_line` / `end_line` である。

## 5. 投稿本文

`user_comment` を、指示として読める文に整える。対象は excerpt から補う。新しい指摘・理由・装飾・会話の名残は足さない。excerpt は引用しない。

音声入力の欠け（助詞、句読点、対象の抜け）を埋めるところまで。

完了条件: 各 resolved 件に、元の `user_comment` と投稿本文の両方がある。

## 6. 投稿

resolved の件を、同一ターンで GitHub の review comment として投稿する。

head SHA を `commit_id` にする。`side` は `RIGHT`。1行なら `line` だけ。excerpt が複数行のときだけ `start_line` と `line`（最終行）を付ける。

1件:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  -f commit_id="{HEAD_SHA}" \
  -f path="{file}" \
  -f body="{投稿本文}" \
  -F line={resolved_end_line} \
  -f side=RIGHT
```

複数件は review 一括:

```bash
jq -n --arg commit "$HEAD_SHA" --argjson comments "$COMMENTS" \
  '{commit_id:$commit, event:"COMMENT", comments:$comments}' \
| gh api repos/{owner}/{repo}/pulls/{pr}/reviews --input -
```

`comments` の各要素は `path` / `body` / `line` / `side`。複数行だけ `start_line` を足す。

API が diff 外を理由に失敗したら、その失敗を返す。近い変更行へ付け替えない。

完了条件: resolved の各件について、コメント URL があるか、失敗理由がある。

## 7. 報告

件ごとに次を出す。

```
[n] {file}:{resolved_line}
    reported lines: {hint_start}-{hint_end}  →  resolved: {start}[-{end}]
    excerpt: ...
    user comment: ...
    posted body: ...
    url: ...  / skipped: {理由}
```

完了条件: 全件が posted か skipped で、skipped には理由がある。
