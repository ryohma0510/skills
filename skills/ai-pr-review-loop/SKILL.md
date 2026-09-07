---
name: ai-pr-review-loop
description: Copilot と Codex に GitHub PR レビューを依頼し、指摘対応と再依頼をループする。
disable-model-invocation: true
argument-hint: "PR 番号または owner/repo#number（複数可、省略時は現在ブランチの PR）"
---

# Copilot と Codex のレビューループ

Copilot と Codex にレビューを依頼し、到着を待ち、指摘対応し、修正があれば再依頼する。この 1 循環を **周** と呼ぶ。周の上限は 5。

指摘の分類・修正・返信・resolve は Skill ツールで `reply-review` を発動して行う。

依頼と到着待ちのコマンドは [references/github.md](references/github.md) にある。実行するステップの直前に、該当節を読む。

## 1. 対象 PR を確定する

引数を空白区切りで読む。

| 引数 | 意味 |
| --- | --- |
| `274` | 現在のリポジトリの PR 274 |
| `owner/repo#274` | そのリポジトリの PR 274 |
| PR の URL | その URL の PR |
| （省略） | 現在のブランチの PR |

番号だけのときは `gh pr view <number> --json number,url,baseRefName,headRefName`。省略時は番号なしで同じフィールドを取る。

```bash
gh pr view --json number,url,baseRefName,headRefName
```

`owner` / `repo` は PR の URL から取る。

`gh pr view` が `no pull requests found` で失敗したら、対象 PR をユーザーに聞いて中断する。

各 PR について `owner` / `repo` / `number` / `url` / head を控える。以降の `gh` には `--repo owner/repo` を付ける。コードを触るステップは、その PR の head が入った working tree で行う。別リポジトリなら、その working tree に移る（未 clone なら clone する）。

完了条件: 対象 PR が 1 件以上あり、各件の owner・repo・number・url・head が分かっている。

## 2. 周を回す

ステップ1の対象を、上限 5 周、または対象が空になるまで繰り返す。

各周は依頼 → 到着待ち → 指摘対応 → 継続判定の順。対象が複数ある周では、依頼を全件やってから到着待ちを全件やり、指摘対応は 1 件ずつ working tree を移しながら行う。

### 2.1 依頼

対象の各 PR について、head がリモートに push 済みであることを確認してから依頼する。

1. [references/github.md](references/github.md) の「ベースライン」で、Copilot と Codex それぞれの直近 `submitted_at` を取る（未提出なら null）。
2. 同ファイルの「Copilot の依頼」を実行し、「Copilot の検証」で `requested_reviewers` に `Copilot` が載っていることを確認する。mutation の成功ログだけでは未完了。載っていなければ同ファイルの「GitHub Enterprise Server」または「トラブルシュート」へ進む。
3. 同ファイルの「Codex の依頼」を実行する。本文は `@codex review` の 1 行だけ。自動レビューが既に走っていて未提出の Codex review がある初回は、この投稿を省略する。再依頼の周では push 後に毎回投稿する。

`gh pr edit --add-reviewer` は Bot では silent fail するため、Copilot の依頼には使わない。

完了条件: 各 PR について、Copilot が `requested_reviewers` に載っている（検証済み）か、検証失敗を報告してその PR の Copilot をこの周の対象外にした。Codex は投稿したコメントの URL があるか、自動レビュー中のため省略した旨が言える。各 bot のベースライン `submitted_at` が分かっている。

### 2.2 到着待ち

間隔は `sleep 30`、最大 20 回。各回で [references/github.md](references/github.md) の「到着待ち」を実行する（スレッドの GraphQL、reviews の `submitted_at`、`requested_reviewers`）。author の対応は同節の表で判定する。

各 bot の完了シグナル:

- ベースラインより新しい `submitted_at` の review がある
- その bot 起点の未 resolve スレッドが、ベースライン以降に 1 件以上ある
- Copilot のみ: `requested_reviewers` から `Copilot` が消えた

ポーリングを止めるのは次のいずれか。

- Copilot と Codex の両方に完了シグナルがある
- 20 回に達した

20 回に達した時点でシグナルが無い bot は、この周は欠席として報告し、届いている側だけで次へ進む。

完了条件: 各 PR について、止めた理由（両方のシグナル / 打ち切り）と、届いた bot・欠席した bot が言える。

### 2.3 指摘対応

対象の各 PR について、その PR の head を checkout してから、Skill ツールで `reply-review` を発動する。引数にその PR を渡す。

完了条件: 各 PR について `reply-review` が終わっており、分類の内訳・resolve 件数・この周で作ったコミットの有無が分かっている。

### 2.4 継続判定

各 PR を次のどちらかに振り分ける。

- この周で修正コミットがある → head がリモートに push 済みであることを確認し、次の周の対象に残す
- この周で修正コミットが無い → 終了。次の周の対象から外す

5 周目の継続判定のあと、対象を空にする。

完了条件: 次の周の対象一覧が確定している。空ならステップ3へ進む。

## 3. 最終報告

- 対象にした PR の URL
- 回した周回数
- 各 PR の、各周の対応件数 / 対応しない件数 / resolve 件数 / 残したスレッド
- 打ち切り（上限・欠席した bot）があればその理由。5 周目で修正コミットを出して終えた場合は、その修正に対する再依頼はしていない旨も書く

完了条件: ステップ1で対象にした全 PR について、上の項目が揃っている。
