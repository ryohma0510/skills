---
name: review-reply
description: PR に付いたレビューコメントに対応するときに使う。「レビューコメントに対応して」「指摘を直して」と言われたとき、他のスキルがレビューコメントへの対応を必要とするときにも使う。
---

# レビューコメント対応

PR の未対応なレビュースレッドを集め、1件ずつ対応要否を判断し、直し、返信し、resolve する。

## 1. 対象 PR とスレッドの取得

対象 PR が指定されていなければ、現在のブランチの PR を使う。

```bash
gh pr view --json number,url,baseRefName
gh repo view --json owner,name --jq '.owner.login, .name'
gh api user --jq .login
```

`gh pr view` が `no pull requests found` で失敗したら、対象 PR をユーザーに聞いて中断する。取得した自分の login はステップ6の resolve 判定に、baseRefName はステップ3の diff に使う。

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
            nodes{author{login,__typename} body url createdAt}
          }
        }
      }
    }
  }
}' -F owner=<owner> -F repo=<repo> -F pr=<number>
```

スレッドは最初のコメントだけを指摘として扱わない。`comments.nodes` に並ぶ返信まで含めて1件の指摘であり、指摘の結論は後続の返信にあることがある（指摘者が自分で撤回している、条件を足している、別の箇所を追加で挙げている）。

`hasNextPage` が true なら `endCursor` を `after` に渡して続きを取る。スレッド側（`reviewThreads`）とコメント側（`comments`）のどちらにもあり、両方を最後まで辿る。コメント側の取りこぼしは、そのまま指摘の読み違いになる。

次のスレッドは対象外にする。

- `isResolved` が true
- `comments.nodes` の最後が自分の返信であるもの。前回の実行で対応済みで、指摘者からの反応がまだない。

スレッドに紐づかないレビュー本文や PR コメントも指摘を含むことがある。次で拾い、自分の返信より後に投稿されたものを対象に加える。

```bash
gh pr view <number> --json reviews,comments
```

これらは thread ID を持たないため、返信のみを行う（ステップ5参照）。

完了条件: 対象のスレッドとスレッド外のコメントが列挙でき、それぞれの ID・ファイル・行・投稿者と、スレッド内の全コメントの本文が分かっている。除外したスレッドは、除外の理由（resolve 済み / 返信済み）が言える。

## 2. 分類

1件ずつ、スレッド内の全コメントと、該当箇所のコードとその周辺を実際に読み、次のどれかに分類する。分類の対象は最後の返信まで踏まえた指摘の現在の内容とする。`isOutdated` が true のスレッドは指摘後にその箇所が変わっているため、指摘時点ではなく現在のコードを読んで分類する。

| 分類 | 条件 |
| --- | --- |
| 対応する | 指摘のとおり壊れている・規約から外れていると自分で確認できた |
| 対応しない | 誤読・既に対応済み・仕様上そうしている、と根拠を示せる |
| 判断を仰ぐ | 設計方針の変更を伴う、影響範囲が PR を超える、指摘者の意図が読めない |

「対応しない」に分類するには、コード上の根拠（該当行、既存の規約、テストの存在など）が要る。根拠を示せないものは「判断を仰ぐ」に倒す。

全件を分類し終えたら、「判断を仰ぐ」の件をまとめてユーザーに提示する。指摘の内容・該当箇所・自分の見立てを添えて聞き、回答を「対応する」「対応しない」のどちらかに反映してから先へ進む。1件ずつ都度聞くと、ユーザーの応答待ちで作業が細切れになる。

完了条件: 全件が「対応する」「対応しない」のどちらかに落ち着き、それぞれの根拠（ユーザーに聞いたものはその回答）が言える。

## 3. 横展開

「対応する」に分類した指摘ごとに、同じ指摘が当てはまる箇所を他からも探す。1箇所だけ直すと、同じ指摘が次のレビューで再び付く。

探す順序は、同じファイルの他の箇所 → この PR の差分に含まれる他のファイル → リポジトリ全体。差分はステップ1の baseRefName を、追跡先のリモート（無ければ `origin`）で修飾して取る。

```bash
REMOTE=$(git config --get "branch.$(git branch --show-current).remote" || echo origin)
git diff "$REMOTE/<baseRefName>...HEAD"
```

検索の手がかりは指摘の性質に合わせる。命名やAPI誤用なら識別子で grep、パターンの誤りなら同じ構文の出現箇所、抜けている処理なら対になる処理の呼び出し箇所を探す。

見つかった箇所の扱いは範囲で分ける。

- この PR の差分の中 → 一緒に直す。
- 差分の外 → 返信と最終報告で「同じ問題が <path:line> にもある」と挙げるにとどめる（PR の範囲が広がるため）。ユーザーが直すと決めたら直す。

完了条件: 「対応する」各件について、横展開の結果（差分内で見つかった件数、差分外で見つかった件数、いずれもゼロならその旨）が分かっている。

## 4. 修正

分類が「対応する」の指摘と、横展開で差分内に見つかった箇所を直す。

指摘された箇所の周辺に既存のテストがあれば、修正後に走らせて壊していないことを確認する。テストの追加が要る修正なら `tdd` スキルを使う。コメントを書く・直すときは `code-comments` スキルを使う。

修正できたらコミットして push する。修正で設計判断や動作確認の内容が変わったなら、Skill ツールで `pr-create` を発動し、更新モードで PR 本文を最新の差分に合わせる。

完了条件: 修正が push 済みで、テストがあるなら通っている。

## 5. 返信

スレッドごとに返信を書く。内容は次の3点に絞る。

- どう対応したか（対応しない場合はその理由と根拠）
- 差分外に同種箇所が見つかった場合はその場所
- ユーザーに判断を仰いだ場合はその結果

返信本文はリポジトリ外の一時ファイルに書き出す（`git status` を汚さないため）。

```bash
mktemp -d
```

出力されたディレクトリ配下に返信ごとのファイルを書き出す。シェル変数はコマンド間で引き継がれないため、以降のコマンドには書き出した実パスをそのまま書く。

書き出したパスを渡して Skill ツールで `doc-trim` を発動する。整形後のファイルの内容を返信本文として使う。

スレッドへの返信:

```bash
gh api graphql -f query='
mutation($threadId:ID!,$body:String!){
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId,body:$body}){comment{url}}
}' -f threadId=<thread id> -f body="$(cat <返信ファイルの実パス>)"
```

スレッド外のレビュー本文・PR コメントへの返信:

```bash
gh pr comment <number> --body-file <返信ファイルの実パス>
```

完了条件: ステップ1で対象にしたスレッドとスレッド外のコメントのすべてに返信が付き、その本文は `doc-trim` を適用済みである。

## 6. resolve

返信済みのスレッドのうち、`comments.nodes` の先頭（指摘を起票したコメント）の投稿者が次のいずれかのものを resolve する。

- 自分（ステップ1で取得した login）
- Bot（`author.__typename` が `Bot`、もしくは login が `[bot]` で終わる）

```bash
gh api graphql -f query='
mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{isResolved}}}
' -f threadId=<thread id>
```

分類が「対応しない」でも、上の条件を満たすスレッドは返信したうえで resolve する。

それ以外の投稿者のスレッドは、対応できたかどうかの判断ごと指摘者に委ね、未 resolve のまま残す。

完了条件: 条件を満たすスレッドをすべて resolve し、残したスレッドについては残した理由が言える。

## 7. 結果の報告

- PR の URL と、分類の内訳（対応した / 対応しない）
- 修正内容と、横展開で一緒に直した箇所
- 差分外に見つかった同種箇所
- resolve した件数と、他者のスレッドとして残した件数
