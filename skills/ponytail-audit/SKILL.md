---
name: ponytail-audit
description: "リポジトリ全体の品質監査: バグ、セキュリティ、実負荷での破綻、テストのないリスクコード、遅い経路、削除・統合・分割候補。優先度付き、各指摘を平易な言葉で。一回限り、変更なし。audit this codebase、review the whole repo、find bloat、what can I delete、/ponytail-audit"
---
<!--
source: https://github.com/DietrichGebert/ponytail/tree/main/skills/ponytail-audit
imported_at: 2026-10-17
upstream_commit: 16352ac229eb08a9598dcae48fe9f2b342567d86
license: MIT (LICENSE)
-->

引き継いだ直後に呼ばれるシニア開発者の視点でリポ全体を監査する。重要度: 正しさ、安全、負荷、テスト、速度、削ぎ。余分な1行は後で読まれテストされ直される。ユーザーが求めたレポートなので省略せず出す。

## 1. まず地図を作る

- ユーザーが名指した範囲: フォルダ、パッケージ、またはリポ全体。指定なし: リポ全体。
- README、デプロイ・ビルド設定、依存一覧、エントリポイント（main、routes、handlers、jobs、CLI）、テストを読む。
- 想定負荷: 1人のスクリプトか、多数ユーザー・同時プロセスか。それに照らして判断し、想定した負荷を明記。
- 主要フローを端から端まで: 入力、保存、出力。ユーザー入力、金銭、認証、書き込み、バックグラウンドジョブ、プロセス間共有に沿って深く読む。
- 大きいリポ: ミスが高コストな所を深く、ファイル順に総当たりしない。読まなかった部分を明記。

## 2. 探すもの

1. **バグ:** 誤結果、クラッシュ、エッジケース漏れ（空、ゼロ、最後、丸め、TZ）、呼び出し元と戻り値の不一致、同ルールの二重実装。
2. **リスク:** セキュリティ（インジェクション、弱乱数、秘密、入力未検証）、データ損失（エラー握りつぶし、書き順、トランザクションなし）。
3. **スケール:** 1ユーザーでは足りるが多数で破綻: 競合、全プロセス重複処理、増え続けるメモリ・リスト、件数クエリ、O(n^2)、共有すべき状態がローカル。
4. **テスト不足:** リスクロジック（分岐、パーサ、金銭、セキュリティ、書き込み）に壊れたとき失敗するテストがない。
5. **速度:** 大きな劣化は問題。小さな改善は提案程度。
6. **削ぎ:** 存在すべきでない、または小さくできるコード。
   - delete: デッドコード、未使用オプション・フラグ・設定、投機的機能
   - reuse: 同じことをする2ヘルパー（1つ残しパスを名指し）
   - stdlib / native: 標準・プラットフォームで足りる; 数行のための依存
   - yagni: 実装1つのインターフェース、製品1つのファクトリ、通過だけのラッパー
   - merge: 一緒に変える近似重複
   - split: 無関係な仕事を1関数・1クラスが抱える。仕事で分割。行数分割や短くするだけのヘルパーはしない。

## 3. 報告前の確認

- 指摘には具体例が要る。例なし指摘なし。
- 未使用と言う前にツリー全体を grep（テスト、フィクスチャ、設定、文字列・動的参照含む）。
- `shortcut:`（旧 `ponytail:`）で限界を名指した近道は、想定負荷が限界を超えない限り指摘ではなく判断。
- 最小の動く修正を提案。削除優先。不要な層・FW・設定は足さない。
- 好み、曖昧な consider、根拠のない心配は出さない。

## 4. 出力

平易な言葉: 短い文、日常語。専門語は初出で説明。

冒頭 `What this repo does:` を2〜3文と、想定した負荷。

指摘は3グループ、重要度順、空は省略:
- **Must fix:** バグ、セキュリティ、データ損失、想定負荷で破綻。
- **Should fix:** テストのないリスク、実スロー、重複、仕事混在、不要コード。
- **Nice to have:** 小さな高速化、短い形。

全グループ通し番号。最大20件。小さな指摘を省略したら件数を明記。
各指摘4要素、各1〜2短句:

2. **Orders land on the wrong day** (`billing/close_day.py:L40-52`)
   - **What this is:** At midnight this job closes the day and bills all orders of that day.
   - **Problem:** It takes "today" from the server clock, which runs in UTC. An order placed
     at 00:30 in Berlin is billed on the day before.
   - **Fix:** Compute the day once in the shop's time zone:
     `datetime.now(ZoneInfo("Europe/Berlin")).date()`. One line, nothing else changes.
   - **If we skip it:** Late orders show the wrong date, and accounting fixes them by hand.

末尾:
- `Verdict:` 1行: 健全、または最初に直すもの。
- 削ぎ指摘があるとき `Lean: -<N> lines, -<M> dependencies possible.`
- `Not checked:` 読めなかった・実行できなかった部分。

指摘なし: `What this repo does:` のあと `Healthy. Nothing to fix.` と確認内容1行。

一回限りのレポート、コードは変更しない。
