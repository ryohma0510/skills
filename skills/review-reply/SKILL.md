---
name: review-reply
description: PR に付いたレビューコメントに対応するときに使う。「レビューコメントに対応して」「指摘を直して」と言われたとき、他のスキルがレビューコメントへの対応を必要とするときにも使う。対応要否の判断・同種箇所への横展開・返信・resolve まで行う。
---

# レビューコメント対応

PR の未 resolve なレビュースレッドを集め、1件ずつ対応要否を判断し、直し、返信し、resolve する。

## 1. 対象 PR とスレッドの取得

対象 PR が指定されていなければ、現在のブランチの PR を使う。

```bash
gh pr view --json number,url,headRefName
gh repo view --json owner,name
gh api user --jq .login
```

`gh pr view` が `no pull requests found` で失敗したら、対象 PR が特定できないためユーザーに聞いて中断する。取得した自分の login は、ステップ6の resolve 判定に使う。

レビュースレッドを resolve 状態つきで取得する。

```bash
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100){
        nodes{
          id isResolved isOutdated path line
          comments(first:20){nodes{author{login,__typename} body url createdAt}}
        }
      }
    }
  }
}' -F owner=<owner> -F repo=<repo> -F pr=<number>
```

`isResolved: true` のスレッドは対象外。残ったスレッドを対応対象のリストにする。

スレッドに紐づかないレビュー本文や PR コメントも指摘を含むことがある。次で拾い、対象に加える。

```bash
gh pr view <number> --json reviews,comments
```

これらは thread ID を持たないため resolve できない。返信のみを行う（ステップ5参照）。

完了条件: 未 resolve なスレッドと、スレッド外のコメントが列挙でき、それぞれの ID・ファイル・行・本文・投稿者が分かっている。

## 2. 対応要否の判断

指摘を鵜呑みにしない。1件ずつ、該当箇所のコードとその周辺を実際に読み、次のどれかに分類する。

| 分類 | 条件 | やること |
| --- | --- | --- |
| 対応する | 指摘のとおり壊れている・規約から外れていると自分で確認できた | 直して返信し、ステップ6の条件を満たせば resolve |
| 対応しない | 誤読・既に対応済み・仕様上そうしている、と根拠を示せる | 直さず、理由を返信する |
| 判断を仰ぐ | 設計方針の変更を伴う、影響範囲が PR を超える、指摘者の意図が読めない | 直さず、ユーザーに判断を求める |

「対応しない」に分類するには、コード上の根拠（該当行、既存の規約、テストの存在など）が要る。根拠を示せないものは「判断を仰ぐ」に倒す。

完了条件: 全件がいずれかに分類され、「対応する」「対応しない」それぞれの根拠が言える。

## 3. 同種箇所の洗い出し

「対応する」に分類した指摘ごとに、同じ指摘が当てはまる箇所が他にないかを探す。1箇所だけ直すと、同じ指摘が次のレビューで再び付く。

探す順序は次のとおり。

1. 同じファイルの他の箇所
2. この PR の差分に含まれる他のファイル（`git diff <remote>/<base>...HEAD`）
3. リポジトリ全体

指摘の性質に応じて検索の手がかりを変える。命名やAPI誤用なら識別子で grep、パターンの誤りなら同じ構文の出現箇所、抜けている処理なら対になる処理の呼び出し箇所を探す。

見つかった箇所の扱いは範囲で分ける。

- この PR の差分の中 → 一緒に直す。
- 差分の外 → 直さない。PR の範囲が広がるため、返信と最終報告で「同じ問題が <path:line> にもある」と挙げるにとどめる。ユーザーが直すと決めたら直す。

完了条件: 「対応する」各件について、同種箇所を探した結果（差分内で見つかった件数、差分外で見つかった件数、いずれもゼロならその旨）が分かっている。

## 4. 修正

分類が「対応する」の指摘と、ステップ3で差分内に見つかった同種箇所を直す。

指摘された箇所の周辺に既存のテストがあれば、修正後に走らせて壊していないことを確認する。テストの追加が要る修正なら `tdd` スキルを使う。コメントを書く・直すときは `code-comments` スキルを使う。

修正できたらコミットして push する。

完了条件: 修正が push 済みで、テストがあるなら通っている。

## 5. 返信

スレッドごとに返信を書く。内容は次の3点に絞る。

- どう対応したか（対応しない場合はその理由と根拠）
- 差分外に同種箇所が見つかった場合はその場所
- 判断を仰ぐ場合は、ユーザーに聞いた結果

返信本文はリポジトリ外の一時ファイルに書き出す（`git status` を汚さないため）。

```bash
mktemp -d
```

出力されたディレクトリ配下に返信ごとのファイルを書き出す。シェル変数はコマンド間で引き継がれないため、以降のコマンドには実パスをそのまま書く。

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

完了条件: 対応対象の各スレッドに返信が付き、その本文は `doc-trim` を適用済みである。

## 6. resolve

返信済みのスレッドのうち、次の条件を満たすものを resolve する。

- スレッドの最初のコメントの投稿者が自分（ステップ1で取得した login）である。
- または投稿者が Bot である（`author.__typename` が `Bot`、もしくは login が `[bot]` で終わる）。

```bash
gh api graphql -f query='
mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{isResolved}}}
' -f threadId=<thread id>
```

分類が「対応しない」でも、上の条件を満たすスレッドは返信したうえで resolve する。判断を仰ぎ中で結論が出ていないスレッドは resolve しない。

自分でも Bot でもない投稿者のスレッドは resolve しない。対応できたかどうかの判断は指摘者に委ねる。

完了条件: 自分・Bot のスレッドが resolve 済みで、他者のスレッドが未 resolve のまま残っている。

## 7. 結果の報告

次を報告する。

- PR の URL と、対応したスレッド件数（対応した / 対応しない / 判断を仰ぐ の内訳）
- 修正内容と、差分内で一緒に直した同種箇所
- 差分外に見つかった同種箇所（直していないもの）
- resolve したスレッド件数と、他者のスレッドとして残した件数
