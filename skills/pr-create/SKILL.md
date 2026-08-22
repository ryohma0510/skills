---
name: pr-create
description: PR を作るときに使う。「PR を作って」「プルリク出して」と言われたとき、他のスキルが PR 作成を必要とするときにも使う。
argument-hint: "base ブランチ（省略時は自動推定）"
---

# Push & PR 作成

変更を push し、diff から日本語のタイトルと description を生成して draft PR を作成する。

## 1. push

未コミットの変更を確認する。

```bash
git status --porcelain
```

出力があれば、コミットしてから進めるか現状のまま push するかをユーザーに聞く。

```bash
git push -u origin $(git branch --show-current)
```

リモート名が `origin` でないリポジトリでは、`git remote` の出力に合わせて読み替える。

完了条件: リモートのブランチが、PR に含めたいコミットをすべて含んでいる。

## 2. 既存 PR の確認

このブランチに PR が既にあるかを見る。

```bash
gh pr view --json number,url,baseRefName,isDraft
```

- PR がある → **更新モード**。base は既存 PR の `baseRefName` を使い、次のステップを飛ばす。最後は本文の差し替えになる。
- `no pull requests found` で失敗する → **新規モード**。次のステップへ進む。
- それ以外の理由で失敗する（未認証、ネットワーク断、リポジトリ解決不能など） → モードを決められないため、エラー内容をユーザーに伝えて中断する。新規モードとして進めると、既存 PR がある場合にステップ9で衝突する。

完了条件: 更新モードか新規モードかが決まり、更新モードなら対象の PR 番号を控えている。

## 3. base ブランチの決定

新規モードでのみ行う。引数で base が指定されていればそれを使い、このステップを終える。

指定がなければ、このスキルに同梱したスクリプトで直接の親ブランチを推定する。スキルの読み込み時に提示されるベースディレクトリ（このスキルのフォルダの絶対パス）配下の scripts/detect-base.sh を実行する。

```bash
bash "$SKILL_BASE_DIR/scripts/detect-base.sh"   # $SKILL_BASE_DIR は上記ベースディレクトリに置き換える
```

スクリプトは `origin/develop/a` のようにリモート修飾つきの ref を1行返す。この値を diff の取得に使い、PR 作成時にはリモート名の部分を除いたブランチ名を渡す。

出力された候補をユーザーに提示して確認する: 「base ブランチは `<候補>` でよいですか？ 別のブランチを指定する場合は入力してください」

完了条件: base が1つに確定し、その修飾つき ref とブランチ名の両方が分かっている。

## 4. 関連 PR の把握

同じスタックに積まれた PR があるかを見る。

```bash
gh pr list --state all --limit 50 --json number,title,url,headRefName,baseRefName,state,isDraft
```

このブランチの base が別 PR の head なら、その PR がスタックの1つ下。その PR の base をさらにたどって根まで並べる。逆に、このブランチを base にしている PR があればスタックの1つ上で、そこからも同様にたどる。

完了条件: スタックに属さないと判断したか、属する場合は根から先端までの PR を列挙できている。

## 5. diff の取得

base のローカルブランチが無くても解決できるよう、リモート追跡参照を使う。更新モードでは既存 PR の `baseRefName` に、ステップ1で push したリモート名を冠したものが対象になる。

```bash
git log <remote>/<base>...HEAD --oneline
git diff <remote>/<base>...HEAD --stat
git diff <remote>/<base>...HEAD
```

完了条件: 全変更ファイルの diff を読み終えている。

## 6. タイトルの生成

diff の内容から日本語で生成する。50文字以内を目安に、変更の目的と内容を端的に表す。

## 7. テンプレートの選択

リポジトリの PR テンプレートを探す。

カレントディレクトリではなくリポジトリのルートを基準に探す。

```bash
find "$(git rev-parse --show-toplevel)" -maxdepth 3 \
  -ipath '*pull_request_template*' -not -path '*/.git/*'
```

見つかったテンプレートをすべて読み、どれを使うかを1回だけユーザーに聞く。選択肢は、見つかったテンプレート各ファイル（`.github/PULL_REQUEST_TEMPLATE/` に複数ある場合はファイル別に並べる）と、このスキルのテンプレート。

リポジトリのテンプレートを選んだ場合は、その見出し構成を骨格にして各セクションを diff の内容で埋める。テンプレートが記入方法を明示している項目はその指示に従い、指示のない部分だけ次のステップのガイドラインを適用する。図解と末尾の `🤖 Generated with AI` 行は、どちらのテンプレートでも入れる。

完了条件: 使うテンプレートが1つに決まっている。

## 8. Description の生成

diff を分析し、日本語の description を書く。設計判断や背景の「なぜ」を軸にし、コードの羅列ではなく意図が伝わる記述にする。テンプレートと各セクションの書き方は [`references/description.md`](references/description.md) を読んでから書く。リポジトリのテンプレートを選んだ場合は、そちらの見出しを骨格にし、ガイドラインはテンプレートの指示がない部分にだけ適用する。

description を書き上げたら、リポジトリ外の一時ファイルに保存する（`git status` を汚さないため）。

```bash
mktemp -d
```

出力されたディレクトリ配下に pr-body.md として本文を書き出す。シェル変数はコマンド間で引き継がれないため、以降のステップでは書き出した実パスをそのまま書く。

保存したパスを渡して Skill ツールで `doc-trim` を発動する。以降のステップは、このファイルの内容を PR 本文として扱う。

完了条件: テンプレートの各セクションが埋まっているか意図的に省略されていて、その本文がファイルに保存され、`doc-trim` を適用済みである。

## 9. PR の作成 / 更新

新規モードでは draft で作成する。

```bash
gh pr create --draft --base <リモート名を除いた base> --title "<title>" --body-file <本文ファイルの実パス> --assignee @me
```

更新モードでは既存 PR のタイトルと本文を差し替える。

```bash
gh pr edit <PR番号> --title "<title>" --body-file <本文ファイルの実パス>
```

完了条件: PR が作成または更新され、その URL が得られている。

## 10. 結果の報告

PR URL、base ブランチ、タイトル、新規作成か更新かを報告する。
