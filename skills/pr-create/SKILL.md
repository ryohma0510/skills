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

完了条件: リモートのブランチが、PR に含めたいコミットをすべて含んでいる。

## 2. base ブランチの決定

引数で base が指定されていればそれを使い、このステップを終える。

指定がなければ、リモートを最新化して直接の親ブランチを推定する。

```bash
git fetch --prune
```

候補を一覧する（自分自身は除外）。

```bash
git branch -r --format='%(refname:short)' | sed 's|origin/||' \
  | grep -E "^(develop|topic|release)/" | grep -v "^$(git branch --show-current)$"
```

各候補について merge-base から HEAD までのコミット数を数え、最小の候補を親とみなす。候補がなければ `main` をデフォルトにする。

```bash
git rev-list --count $(git merge-base HEAD origin/<candidate>)..HEAD
```

デフォルト候補をユーザーに提示して確認する: 「base ブランチは `<候補>` でよいですか？ 別のブランチを指定する場合は入力してください」

完了条件: ユーザーの回答で base が1つに確定している。

## 3. diff の取得

```bash
git log <base>...HEAD --oneline
git diff <base>...HEAD --stat
git diff <base>...HEAD
```

完了条件: 全変更ファイルの diff を読み終えている。

## 4. タイトルの生成

diff の内容から日本語で生成する。50文字以内を目安に、変更の目的と内容を端的に表す。

## 5. テンプレートの選択

リポジトリの PR テンプレートを探す。

```bash
ls .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE.md \
   PULL_REQUEST_TEMPLATE.md docs/pull_request_template.md \
   .github/PULL_REQUEST_TEMPLATE/ 2>/dev/null
```

見つかったテンプレートをすべて読み、どれを使うかを1回だけユーザーに聞く。選択肢は、見つかったテンプレート各ファイル（`.github/PULL_REQUEST_TEMPLATE/` に複数ある場合はファイル別に並べる）と、このスキルのテンプレート。

リポジトリのテンプレートを選んだ場合は、その見出し構成を骨格にして各セクションを diff の内容で埋める。テンプレートが記入方法を明示している項目はその指示に従い、指示のない部分だけ次のステップのガイドラインを適用する。図解と末尾の `🤖 Generated with AI` 行は、どちらのテンプレートでも入れる。

完了条件: 使うテンプレートが1つに決まっている。

## 6. Description の生成

diff を分析し、日本語の description を書く。設計判断や背景の「なぜ」を軸にし、コードの羅列ではなく意図が伝わる記述にする。テンプレートと各セクションの書き方は [`references/description.md`](references/description.md) を読んでから書く。リポジトリのテンプレートを選んだ場合は、そちらの見出しを骨格にし、ガイドラインはテンプレートの指示がない部分にだけ適用する。

description を書き上げたら、リポジトリ外の一時ファイルに保存する（`git status` を汚さないため）。

```bash
BODY="$(mktemp -d)/pr-body.md"
```

保存したパスを渡して Skill ツールで `doc-trim` を発動する。以降のステップは、このファイルの内容を PR 本文として扱う。

完了条件: テンプレートの各セクションが埋まっているか意図的に省略されていて、その本文が `$BODY` に保存され、`doc-trim` を適用済みである。

## 7. PR の作成

draft で作成する。

```bash
gh pr create --draft --base <base> --title "<title>" --body-file "$BODY" --assignee @me
```

## 8. 結果の報告

PR URL、base ブランチ、タイトルを報告する。
