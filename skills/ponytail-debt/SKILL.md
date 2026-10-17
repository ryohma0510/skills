---
name: ponytail-debt
description: "すべての `shortcut:` コメント（旧 `ponytail:` 含む）を負債台帳として一覧。一回限りのレポート、コードは変更しない。「ponytail debt」「what did ponytail defer」「list the shortcuts」、/ponytail-debt"
---
<!--
source: https://github.com/DietrichGebert/ponytail/tree/main/skills/ponytail-debt
imported_at: 2026-10-17
upstream_commit: 16352ac229eb08a9598dcae48fe9f2b342567d86
license: MIT (LICENSE)
-->

意図的な ponytail の近道は `shortcut:` コメントで上限とアップグレード経路を名指しする（旧コードは `ponytail:` のこともある）。これらを1つの台帳に集め、先延ばしが黙って恒久化するのを防ぐ。

## スキャン

リポジトリ全体を grep する。`.git` と `.gitignore` で無視されるもの（依存、ビルド出力、キャッシュなど）はスキップ:

`git grep --no-index --exclude-standard -nE '(#|//|/[*]) ?(shortcut|ponytail):'`（スタックに応じて他のコメント接頭辞を追加）

ユーザーが独自マーカー語を指定した場合（`/ponytail-debt TODO`）はその語で grep。

ヒット1件 = 台帳1行。コメント接頭辞により、慣習に言及しているだけの散文は除外。キーボードショートカットのメモなど、延期でないヒットはスキップ。

## 出力

マーカー1件1行、ファイルごとにグループ:

`<file>:<line>, <何を簡略化したか>. ceiling: <コメントが名指した限界>. upgrade: <見直しトリガー>.`

慣習は `shortcut: <ceiling>, <upgrade path>`。ceiling とトリガーはコメントからそのまま取り出す。行ごとの担当者が要るなら `git blame -L<line>,<line>`。

腐敗リスク: アップグレード経路やトリガーを名指していないマーカーに `no-trigger` タグ。黙って腐る候補。

末尾: `<N> markers, <M> with no trigger.` 無ければ `No shortcut debt. Clean ledger.`

## 境界

読み取りと報告のみ、変更しない。永続化はユーザーが依頼したときだけ（例: `PONYTAIL-DEBT.md` に書き出し）。一回限り。
