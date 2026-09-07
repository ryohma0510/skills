# 依頼と到着待ち

`SKILL.md` のステップ 2.1 と 2.2 から読む。`<owner>` `<repo>` `<number>` は対象 PR のものに置き換える。

## ベースライン

再レビュー判定の比較元にする。依頼の直前に取る。

```bash
gh api repos/<owner>/<repo>/pulls/<number>/reviews \
  --jq '[.[]|select(.user.login=="copilot-pull-request-reviewer[bot]")|.submitted_at]|sort|last'

gh api repos/<owner>/<repo>/pulls/<number>/reviews \
  --jq '[.[]|select(.user.login=="chatgpt-codex-connector[bot]")|.submitted_at]|sort|last'
```

該当 review が無ければ null。

## Copilot の依頼

```bash
PR_NODE_ID=$(gh pr view <number> --repo <owner>/<repo> --json id --jq '.id')

gh api graphql -f query='
mutation($prId: ID!) {
  requestReviews(input: {
    pullRequestId: $prId,
    botIds: ["BOT_kgDOCnlnWA"],
    union: true
  }) {
    pullRequest { number }
  }
}' -f prId="$PR_NODE_ID"
```

`BOT_kgDOCnlnWA` は GitHub.com の `copilot-pull-request-reviewer[bot]` の node_id。`union: true` は既存の reviewer を残したまま追加する。

## Copilot の検証

```bash
gh api repos/<owner>/<repo>/pulls/<number>/requested_reviewers
```

`users` の `login` に `Copilot` が含まれていれば依頼は届いている。含まれていなければ未完了なので、「GitHub Enterprise Server」または「トラブルシュート」へ進む。

## GitHub Enterprise Server

```bash
gh api "users/copilot-pull-request-reviewer[bot]" --jq .node_id
```

得られた値を `botIds` に入れて「Copilot の依頼」を実行し、検証する。

## Codex の依頼

```bash
gh pr comment <number> --repo <owner>/<repo> --body "@codex review"
```

本文は `@codex review` と完全一致させる。別文言は Codex の cloud task になり、コードレビューではない。

リポジトリで Codex cloud と Code review が有効である前提。Security 版をユーザーが指定したときだけ本文を `@codex security review` にする。

## 到着待ち

```bash
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){
        pageInfo{hasNextPage endCursor}
        nodes{id isResolved path line
          comments(first:100){
            pageInfo{hasNextPage endCursor}
            nodes{author{login __typename} body createdAt}
          }
        }
      }
    }
  }
}' -F owner=<owner> -F repo=<repo> -F pr=<number>
```

`reviewThreads.pageInfo.hasNextPage` が true なら、同じクエリの `reviewThreads(first:100)` を `reviewThreads(first:100, after:$cursor)` にして `endCursor` を渡す。`comments.pageInfo.hasNextPage` が true のスレッドは、thread ID を指定してコメント側を辿る。

各回でベースラインと同じ reviews 取得と、Copilot の検証と同じ `requested_reviewers` も取る。完了シグナルの `submitted_at` と Copilot の離脱はこちらで見る。

```bash
gh api graphql -f query='
query($threadId:ID!,$cursor:String!){
  node(id:$threadId){
    ... on PullRequestReviewThread{
      comments(first:100, after:$cursor){
        pageInfo{hasNextPage endCursor}
        nodes{author{login __typename} body createdAt}
      }
    }
  }
}' -f threadId=<thread id> -f cursor=<endCursor>
```

bot 起点のスレッドとは、先頭コメントの author が下表の inline comment であるもの。`author.__typename` は `Bot`。

| 場所 | Copilot | Codex |
| --- | --- | --- |
| inline comment `user.login` / GraphQL `author.login` | `Copilot` | `chatgpt-codex-connector[bot]` |
| `GET /pulls/N/reviews` の `user.login` | `copilot-pull-request-reviewer[bot]` | `chatgpt-codex-connector[bot]` |
| `requested_reviewers` の `login` | `Copilot` | （コメントトリガーのため、通常は載らない） |

到着待ち中に見る review の `submitted_at` は `GET /pulls/N/reviews` 側の login でフィルタする。

スレッドの `id`（`PRRT_...`）は GraphQL の reply / resolve 用。reply と resolve は `reply-review` がこの id で行う。

Copilot の review state `COMMENTED` は拒否ではない。本文の「human review recommended」は finding ではない。finding は bot 起点の未 resolve スレッドとして数える。

## トラブルシュート

検証で `Copilot` が載らない: node_id を `gh api "users/copilot-pull-request-reviewer[bot]" --jq .node_id` で取り、`botIds` を差し替えて依頼をやり直す。それでも載らなければ、その PR のこの周は Copilot を欠席にし、Codex 側だけで進める。

Codex の review が来ない: リポジトリで Codex cloud と Code review が有効かを確認する。無効ならその PR の以降の周も Codex 投稿を省略し、Copilot だけで回す。

自動レビュー ON: 初回 push で Codex が既に動き出していることがある。未提出の Codex review があるあいだは `@codex review` を重ねない。push 後の再レビューでは投稿する。
