---
name: pr-create
description: PR を作るときに使う。「PR を作って」「プルリク出して」と言われたとき、他のスキルが PR 作成を必要とするときにも使う。
argument-hint: "base ブランチ（省略時は自動推定）"
---

# Push & PR 作成

変更を push し、draft PR を作成する。タイトルと description の生成・既存 PR の本文更新は `pr-description` に任せる。

## 1. push

未コミットの変更を確認する。

```bash
git status --porcelain
```

出力があれば、コミットしてから進めるか現状のまま push するかをユーザーに聞く。

push 先は追跡先のリモートを優先し、無ければ `origin` にする。

```bash
BRANCH=$(git branch --show-current)
git push -u "$(git config --get "branch.${BRANCH}.remote" || echo origin)" "$BRANCH"
```

ここで使ったリモート名は、以降のステップで base を修飾するのに使う。

完了条件: リモートのブランチが、PR に含めたいコミットをすべて含んでいて、使ったリモート名が分かっている。

## 2. 既存 PR の確認

このブランチに PR が既にあるかを見る。

```bash
gh pr view --json number,url,baseRefName,isDraft
```

- PR がある → Skill ツールで `pr-description` を発動し、本文とタイトルを最新の差分に合わせる。このスキルの残りのステップは行わない。完了条件は `pr-description` の報告（PR URL・base・タイトル）が得られていること。
- `no pull requests found` で失敗する → **新規作成**。次のステップへ進む。
- それ以外の理由で失敗する（未認証、ネットワーク断、リポジトリ解決不能など） → モードを決められないため、エラー内容をユーザーに伝えて中断する。新規として進めると、既存 PR がある場合にステップ5で衝突する。

完了条件: 既存 PR なら `pr-description` まで済ませている。新規なら次のステップへ進める状態である。

## 3. base ブランチの決定

引数で base が指定されていれば、ステップ1のリモート名を冠して修飾つき ref を組み立て、このステップを終える。

指定がなければ、このスキルに同梱したスクリプトで直接の親ブランチを推定する。スキルの読み込み時に提示されるベースディレクトリ（このスキルのフォルダの絶対パス）配下の scripts/detect-base.sh を実行する。

```bash
bash "$SKILL_BASE_DIR/scripts/detect-base.sh"   # $SKILL_BASE_DIR は上記ベースディレクトリに置き換える
```

スクリプトは `origin/develop/a` のようにリモート修飾つきの ref を1行返す。この値を diff の取得に使い、PR 作成時にはリモート名の部分を除いたブランチ名を渡す。

出力された候補をユーザーに提示して確認する: 「base ブランチは `<候補>` でよいですか？ 別のブランチを指定する場合は入力してください」

完了条件: base が1つに確定し、その修飾つき ref とブランチ名の両方が分かっている。

## 4. タイトルと description の生成

確定した base を渡して Skill ツールで `pr-description` を発動する。既存 PR は無い前提なので、`pr-description` は本文のみ（一時ファイル）を返す。

完了条件: `pr-description` の報告から、タイトルと本文ファイルの実パスが分かっている。

## 5. PR の作成

draft で作成する。タイトルと `--body-file` にはステップ4の値を使う。

```bash
gh pr create --draft --base <リモート名を除いた base> --title "<title>" --body-file <本文ファイルの実パス> --assignee @me
```

完了条件: PR が作成され、その URL が得られている。

## 6. 結果の報告

PR URL、base ブランチ、タイトルを報告する。
