---
name: pr-description
description: PR の description（本文）やタイトルを書く・更新するときに使う。「description を更新して」「PR 本文を書き直して」と言われたとき、他のスキルが PR 本文の生成や更新を必要とするときにも使う。
argument-hint: "base ブランチ（PR が無く本文だけ書くとき。省略時は既存 PR の base）"
---

# PR Description の生成と適用

diff から日本語のタイトルと description を生成する。既存 PR があればタイトルと本文を差し替え、無ければ本文を一時ファイルに書いて呼び出し元へ渡す。

## 1. リモートと base の確定

```bash
BRANCH=$(git branch --show-current)
REMOTE=$(git config --get "branch.${BRANCH}.remote" || echo origin)
```

このブランチに PR があるかを見る。

```bash
gh pr view --json number,url,baseRefName,title
```

- PR がある → base は既存 PR の `baseRefName`。修飾つき ref は `$REMOTE/<baseRefName>`。PR 番号を控える。**適用は更新**（後で `gh pr edit`）。
- PR が無く、呼び出し時に base が渡されている → その base を使う。引数が `origin/develop` のように修飾つきなら、リモート名を除いたブランチ名と修飾つき ref の両方を揃える。修飾が無ければ `$REMOTE/<base>` を修飾つき ref とする。**適用は本文のみ**（ファイルに書き、PR は触らない）。
- PR が無く base も無い → base を特定できないため、エラー内容をユーザーに伝えて中断する。PR の作成は `pr-create` の責務。
- `gh pr view` が「PR が無い」以外の理由で失敗する（未認証、ネットワーク断など） → 適用先を決められないため、エラー内容をユーザーに伝えて中断する。

完了条件: 適用が「更新」か「本文のみ」かが決まり、修飾つき ref とブランチ名の両方が分かっている。更新なら対象の PR 番号も控えている。

## 2. 関連 PR の把握

同じスタックに積まれた PR があるかを見る。

```bash
gh pr list --state all --limit 50 --json number,title,url,headRefName,baseRefName,state,isDraft
```

このブランチの base が別 PR の head なら、その PR がスタックの1つ下。その PR の base をさらにたどって根まで並べる。逆に、このブランチを base にしている PR があればスタックの1つ上で、そこからも同様にたどる。

完了条件: スタックに属さないと判断したか、属する場合は根から先端までの PR を列挙できている。

## 3. diff の取得

```bash
git log <remote>/<base>...HEAD --oneline
git diff <remote>/<base>...HEAD --stat
git diff <remote>/<base>...HEAD
```

完了条件: 全変更ファイルの diff を読み終えている。

## 4. タイトルの生成

diff の内容から日本語で生成する。50文字以内を目安に、変更の目的と内容を端的に表す。

## 5. テンプレートの選択

デフォルトはこのスキルのテンプレート（[`references/description.md`](references/description.md)）。リポジトリの PR テンプレートを使うのは、ユーザーが明示的に指示した場合のみ。

ユーザーからリポジトリのテンプレートを使う指示があった場合だけ、カレントディレクトリではなくリポジトリのルートを基準に探す。

```bash
find "$(git rev-parse --show-toplevel)" -maxdepth 3 -type f \
  -ipath '*pull_request_template*' -not -path '*/.git/*'
```

見つかったテンプレートが複数あれば（`.github/PULL_REQUEST_TEMPLATE/` に複数ある場合など）、すべて読み、どれを使うかを1回だけユーザーに聞く。見つからなければユーザーにその旨を伝え、このスキルのテンプレートを使う。

リポジトリのテンプレートを使う場合は、その見出し構成を骨格にして各セクションを diff の内容で埋める。テンプレートが記入方法を明示している項目はその指示に従い、指示のない部分だけ次のステップのガイドラインを適用する。図解、ELI5 の `<details>`、末尾の `🤖 Generated with AI` 行は、どちらのテンプレートでも入れる。

完了条件: 使うテンプレートが1つに決まっている。

## 6. Description の生成

diff を分析し、日本語の description を書く。設計判断や背景の「なぜ」を軸にし、コードの羅列ではなく意図が伝わる記述にする。テンプレートと各セクションの書き方は [`references/description.md`](references/description.md) を読んでから書く。リポジトリのテンプレートを選んだ場合は、そちらの見出しを骨格にし、ガイドラインはテンプレートの指示がない部分にだけ適用する。

description を書き上げたら、リポジトリ外の一時ファイルに保存する（`git status` を汚さないため）。

```bash
mktemp -d
```

出力されたディレクトリ配下に pr-body.md として本文を書き出す。シェル変数はコマンド間で引き継がれないため、以降のステップでは書き出した実パスをそのまま書く。

保存したパスを渡して Skill ツールで `sanitize-doc` を発動する。

今回の変更を対象に Skill ツールで `eli5` を発動する。得た説明を、保存したファイルの ELI5 の `<details>` に書き込む。ブロックが無ければ、[`references/description.md`](references/description.md) の `<details>` と同じマークアップを、背景の自然文の直後（関連 PR リストがあればその直後。背景が無ければ本文先頭）へ追加してから書き込む。

以降のステップは、このファイルの内容を PR 本文として扱う。

完了条件: テンプレートの各セクションが埋まっているか意図的に省略されていて、その本文がファイルに保存され、`sanitize-doc` を適用済みであり、その後に発動した `eli5` の出力が、保存したファイルの ELI5 の `<details>` に入っている。

## 7. 適用

更新では既存 PR のタイトルと本文を差し替える。

```bash
gh pr edit <PR番号> --title "<title>" --body-file <本文ファイルの実パス>
```

本文のみでは PR を作成も更新もしない。タイトルと本文ファイルの実パスを次のステップの報告用に控える。

完了条件: 更新なら PR のタイトルと本文が差し替わり URL が得られている。本文のみならタイトルと本文ファイルの実パスが控えてある。

## 8. 結果の報告

- 更新: PR URL、base ブランチ、タイトルを報告する。
- 本文のみ: タイトル、本文ファイルの実パス、base ブランチを報告する（呼び出し元が PR 作成に使う）。
