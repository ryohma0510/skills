---
name: reply-review
description: PR に付いたレビューコメントへ返信するときに使う。「レビューコメントに返信して」と言われたとき、他のスキルがレビューへの返信を必要とするときにも使う。
argument-hint: "対象 PR（省略時は現在のブランチの PR）"
---

# レビューコメントへの返信

PR の未対応なレビュースレッドを集め、1件ずつ返信を書き、投稿する。コードは直さない。

## 1. 対象 PR とスレッドの取得

対象 PR が指定されていなければ、現在のブランチの PR を使う。

```bash
gh pr view --json number,url
gh repo view --json owner,name --jq '.owner.login, .name'
gh api user --jq .login
```

`gh pr view` が `no pull requests found` で失敗したら、対象 PR をユーザーに聞いて中断する。取得した自分の login は、末尾が自分の返信であるスレッドの除外に使う。

レビュースレッドを resolve 状態つきで取得する。

```bash
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){
        pageInfo{hasNextPage endCursor}
        nodes{
          id isResolved isOutdated path line
          comments(first:100){
            pageInfo{hasNextPage endCursor}
            nodes{author{login} body url createdAt}
          }
        }
      }
    }
  }
}' -F owner=<owner> -F repo=<repo> -F pr=<number>
```

`comments.nodes` 全体で1件の指摘として扱う。指摘の結論は後続の返信にあることがある（指摘者が自分で撤回している、条件を足している、別の箇所を追加で挙げている）。

スレッド側の `hasNextPage` が true なら、`endCursor` を `reviewThreads(first:100, after:$cursor)` に渡して続きを取る。

コメント側のカーソルはスレッドごとに異なるため、外側のクエリでは辿れない。`comments.pageInfo.hasNextPage` が true のスレッドは、その thread ID を指定して個別に続きを取る。

```bash
gh api graphql -f query='
query($threadId:ID!,$cursor:String!){
  node(id:$threadId){
    ... on PullRequestReviewThread{
      comments(first:100, after:$cursor){
        pageInfo{hasNextPage endCursor}
        nodes{author{login} body url createdAt}
      }
    }
  }
}' -f threadId=<thread id> -f cursor=<endCursor>
```

次のスレッドは対象外にする。

- `isResolved` が true
- `comments.nodes` の最後が自分の返信であるもの。前回の実行で返信済みで、指摘者からの反応がまだない。

スレッドに紐づかないレビュー本文や PR コメントも指摘を含むことがある。次で拾う。

```bash
gh pr view <number> --json reviews,comments
```

対象にするのは、本文が指摘を含むもののうち、自分の直近の返信より後に投稿されたもの。時刻は `reviews` が `submittedAt`、`comments` が `createdAt` を見る。自分の返信がまだ無ければ全件が対象になる。本文が空のレビュー（APPROVED だけのものなど）と、CI・通知の投稿は除く。

これらは thread ID を持たないため、ステップ3で `gh pr comment` により返信する。

対象がスレッド・スレッド外ともに0件なら、ステップ4の報告だけを行って終える。

完了条件: 対象が列挙できている。スレッドは ID・ファイル・行・投稿者と全コメントの本文が、スレッド外のコメントは投稿者・本文・投稿時刻が分かっている。除外したスレッドは、除外の理由（resolve 済み / 返信済み）が言える。

## 2. 返信の下書きと整形

ステップ1で対象にしたスレッドとスレッド外のコメントのそれぞれに、日本語で返信を書く。1件ずつ、スレッド内の全コメントと、該当箇所のコードとその周辺を読む。`isOutdated` が true のスレッドは指摘後にその箇所が変わっているため、現在のコードを読む。

返信の内容は指摘への返答に絞る。同意、現状の説明、既に満たしていること、意図の確認など。コードやテストは変更しない。コミットもしない。

返信本文は、`mktemp -d` が出力したディレクトリ配下に返信先ごとのファイルとして書き出す（リポジトリ内に置くと `git status` を汚すため）。シェル変数はコマンド間で引き継がれないため、以降のコマンドには実パスをそのまま書く。

対象の全件を書き出してから、そのファイルの実パスを列挙して渡し、Skill ツールで `sanitize-doc` を発動する。整形はファイルを上書きするため、ステップ3が投稿するのは整形後の内容になる。

完了条件: 対象の全件について返信本文がファイルとして存在し、そのすべてに `sanitize-doc` を適用し終えている。

## 3. 投稿

ステップ2で整形したファイルを本文として投稿する。

スレッドへの返信は1件ずつ投稿し、公開を確認してから次の mutation を実行する。複数件を同時に投げると、先頭以外が GraphQL 上は `COMMENTED` でも REST から見えず Pending のまま残ることがある。公開の判定は REST 取得の終了コードが 0 であること。`pullRequestReview.state` や `submittedAt` だけでは判定しない。

```bash
gh api graphql -f query='
mutation($threadId:ID!,$body:String!){
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId,body:$body}){
    comment{
      id
      databaseId
      url
    }
  }
}' -f threadId=<thread id> -f body="$(cat <返信ファイルの実パス>)"
```

mutation の結果から `comment.id` と `comment.databaseId` を取る。直後に REST で公開を確認する。

```bash
gh api repos/<owner>/<repo>/pulls/comments/<databaseId> --silent
```

REST が 404 なら、そのコメントは未公開である。`comment.id` を渡して削除し、同じ本文をもう一度投稿して REST を取り直す。1件あたり再試行は3回まで。3回とも 404 ならその件は失敗として残し、次の件へ進む。

```bash
gh api graphql -f query='
mutation($id:ID!){
  deletePullRequestReviewComment(input:{id:$id}){pullRequestReviewComment{id}}
}' -f id=<comment id>
```

スレッド外のレビュー本文・PR コメントへの返信:

```bash
gh pr comment <number> --body-file <返信ファイルの実パス>
```

完了条件: ステップ1の対象それぞれについて、スレッド返信は REST 取得が成功した URL があるか失敗理由があり、スレッド外は返信が付いている。

## 4. 結果の報告

- PR の URL
- 返信した件数と、各返信の URL
- 失敗した件とその理由
