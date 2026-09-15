---
name: orca-md-pr-comments
description: Orca の Markdown レビューコメント（File / Lines / Excerpt / User comment）を GitHub PR の inline comment として投稿する。「レビューコメントして」「PR に投稿して」など投稿を明示的に指示されたとき、または /orca-md-pr-comments のときにだけ使う。ペイロードを貼っただけでは使わない。
trigger: /orca-md-pr-comments
argument-hint: "Orca のペイロード。対象 PR は省略可"
---

# Orca Markdown → PR inline comment

投稿先はファイル行に付く inline comment。行の決め方は `orca-md-resolve` が正本。

投稿本文の整え方の例は、具体形が要るときに [examples.md](examples.md) を読む。

## 1. 投稿意図

次のいずれかがあるときだけこのスキルを進める。

- ユーザーの文に「レビューコメントして」「PR に投稿して」「inline comment で投稿して」など、GitHub への投稿を明示的に指示する表現がある
- `/orca-md-pr-comments`

`File` / `Lines` / `Excerpt` / `User comment` のペイロードがあるだけでは進めない。投稿を指示する文がなければここで終える。行特定も投稿もしない。

完了条件: 投稿意図があると言えた。無ければこのスキルを終えている。

## 2. 対象 PR

URL または番号があればそれを使う。省略時は現在ブランチの PR。

```bash
gh pr view --json number,url,headRefOid
gh pr list --head "$(git branch --show-current)" --json number,url,headRefOid
```

0件または2件以上なら、URL を出してもらい中断する。repo 省略時はカレント。

完了条件: owner / repo / PR 番号 / head SHA が1組に決まっている。

## 3. 行特定

行特定の対象は `commit_id` と同じ PR head のファイル。`git rev-parse HEAD` がその SHA と一致し、作業ツリーにファイルがあるならそれを使う。それ以外は PR head から取り、一時ファイルに書く。

```bash
gh api "repos/{owner}/{repo}/contents/{path}?ref={HEAD_SHA}" --jq .content \
  | python3 -c "import sys,base64; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read()))"
```

ペイロードと、一時ファイルを使った件のパス対応を渡して Skill ツールで `orca-md-resolve` を発動する。投稿に使う行は、その結果の `start_line` / `end_line` である。

完了条件: `orca-md-resolve` が終わり、全件が resolved / ambiguous / not_found のいずれかに分かれている。

## 4. 投稿本文

`user_comment` を、指示として読める文に整える。対象は excerpt から補う。新しい指摘・理由・装飾・会話の名残は足さない。excerpt は引用しない。

音声入力の欠け（助詞、句読点、対象の抜け）を埋めるところまで。

完了条件: 各 resolved かつ `user_comment` がある件に、元の `user_comment` と投稿本文の両方がある。

## 5. 投稿

resolved かつ `user_comment` がある件を、同一ターンで GitHub の review comment として投稿する。

head SHA を `commit_id` にする。`side` は `RIGHT`。1行なら `line` だけ。複数行なら `start_line` / `line`（最終行）と `start_side=RIGHT` を付ける。

1行:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  -f commit_id="{HEAD_SHA}" \
  -f path="{file}" \
  -f body="{投稿本文}" \
  -F line={resolved_end_line} \
  -f side=RIGHT
```

複数行:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  -f commit_id="{HEAD_SHA}" \
  -f path="{file}" \
  -f body="{投稿本文}" \
  -F start_line={resolved_start_line} \
  -f start_side=RIGHT \
  -F line={resolved_end_line} \
  -f side=RIGHT
```

複数件は review 一括:

```bash
jq -n --arg commit "$HEAD_SHA" --argjson comments "$COMMENTS" \
  '{commit_id:$commit, event:"COMMENT", comments:$comments}' \
| gh api repos/{owner}/{repo}/pulls/{pr}/reviews --input -
```

`comments` の各要素は `path` / `body` / `line` / `side`。複数行は `start_line` と `start_side` を足す。

API が diff 外を理由に失敗したら、その失敗を返す。近い変更行へ付け替えない。

完了条件: resolved の各件について、コメント URL があるか、失敗理由がある。

## 6. 報告

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
