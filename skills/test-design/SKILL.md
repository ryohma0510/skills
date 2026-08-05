---
name: test-design
description: seam（公開インターフェース）でテストを設計し、DRY ではなく DAMP に倒す。テストを新しく書くとき、既存テストの良し悪しを判断するとき、モックの是非を決めるとき、統合テストを求められたときに使う。他のスキルがテスト設計の判断を必要とするときにも参照する。
---
<!--
source: https://github.com/mattpocock/skills/tree/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/tdd
imported_at: 2026-08-02
note: 元スキルを手順(tdd)とテスト設計(test-design)に分割
note: DAMP・should/when 命名・Given-When-Then は『Googleのソフトウェアエンジニアリング』に基づき追加
-->

# テスト設計

残す価値のあるテストの基準を定める——何が良いテストか、テストをどこに置くか、避けるべきアンチパターン。テストを書く前と最中に参照すること、後ではない。

## 良いテストとは

テストは実装の詳細ではなく、公開インターフェースを通じて振る舞いを検証する。コードは丸ごと変わりうるが、テストは変わらないべきである。良いテストは仕様のように読める——"should confirm the order when the cart has items" と書いてあれば、どんな能力が存在するのかが正確にわかる——そして内部構造に依存しないためリファクタを生き延びる。

**DAMP——テストは重複してよい。** プロダクションコードは DRY に、テストは DAMP（Descriptive And Meaningful Phrases）に倒す。値の生成をビルダーやファクトリに逃がすのは構わない。ただしそのテストの結果を左右する値は、必ずテスト本体に書く——ビルダーの既定値に埋めるのではなく、テストの中で明示的に渡すこと。

例は [references/tests.md](references/tests.md)、モックの指針は [references/mocking.md](references/mocking.md) を参照。

## テストの形

**名前**——英語で `should <期待される振る舞い>` と書き、条件が振る舞いを分岐させるときだけ `when <条件>` を続ける。分岐がなければ `should` 節だけで終える。

- `should return 401 when the token is missing`
- `should create an empty cart`

`should` 節にも `when` 節にも、観測できる結果と、それを引き起こす具体的な入力を書く。判定: **名前だけを読んで、その条件を満たす入力を1つ書き出せるか。** `correct` / `correctly` / `valid` / `invalid` / `proper` / `properly` / `appropriate` / `expected` / `as expected` / `right` / `good` / `bad` / `works` / `successfully` / `gracefully` / `handles` といった判断を名指しする語は、これを満たせない——何が有効で何が正しいのかを名前から消してしまうからである。成功パスも同じ扱いで、そこを満たす具体的な条件に置き換えること。

- `should reject invalid tokens` → `should return 401 when the token has expired`
- `should handle empty input` → `should return 0 when the cart is empty`
- `should calculate the total correctly` → `should sum price times quantity across all line items`
- `should return 200 when the token is valid` → `should return 200 with the session when the token has not expired`

**ボディ**——`// Given` `// When` `// Then` の3つのコメントで区切る。行数にかかわらず、すべてのテストに3つとも書く。前提を持たないテストでも `// Given` は置き、その下は空行のまま `// When` へ進む。DAMP に倒すとボディは長くなるため、この3つの印がフェーズの境界を保つ。

**分岐なし**——テスト本体に `if` / `else` / `switch` / 三項演算子 / `&&`・`||` による短絡を書かない。分岐を書いた瞬間、そのテストは「どの枝を通ったか」を自分では保証できなくなり、テストの実装が正しいことを別の何かで証明する必要が出てくる——テストは検証される側ではなく、検証する側でなければならない。分岐したくなったらシナリオが2つあるということなので、テストを2つに割ること。入力ごとに期待値が違うだけならパラメタライズドにし、期待値はテーブルにリテラルで並べる。同じ理由でループと `try`/`catch` による分岐も避け、値を書き並べるか、フレームワークの例外アサーション（`expect(...).toThrow()` など）を使う。

**パラメタライズド**——シナリオが同一で入力と期待値だけが違う場合に限り `test.each` / table-driven を使う。各ケースに名前をつけ、その名前も `should ... when ...` にする。

**検査**——テストを書き終えたら、この `SKILL.md` と同じディレクトリにある `scripts/check_test_style.py` を実行し、報告された違反を直す。テストファイルでもディレクトリでも渡せる。

```
python3 <このスキルのディレクトリ>/scripts/check_test_style.py path/to/foo.test.ts
```

名前（T01/T02）、Given-When-Then（T03）、アサーション内での期待値の計算（T04）、テスト本体の条件分岐（T05）を決定的に検査する。DAMP・seam の選び方・モックの是非は意味の判断であり、この検査には含まれない——下のアンチパターンで自分で確かめること。

## Seam——テストを置く場所

**seam** とは、テストを行う公開境界のことである: 内部に手を伸ばすことなく振る舞いを観測できるインターフェース。テストは seam に置く。

**事前に合意した seam でのみテストする。** すべてをテストすることはできない——どの seam をテストするかを先に合意することが、テストの労力をあらゆるエッジケースではなくクリティカルパスと複雑なロジックに向ける方法である。

## アンチパターン

- **実装結合（implementation-coupled）**——内部の協力オブジェクトをモックする、プライベートメソッドをテストする、あるいは側路を通じて検証する（インターフェースを使わずデータベースを直接クエリする）。見分け方: 振る舞いは変わっていないのに、リファクタするとテストが壊れる。振る舞いは公開インターフェース経由で観測すること。
- **過剰共有（over-DRY）**——セットアップやアサーションを共有ヘルパーに畳み込み、テスト本体から意味が抜けている。見分け方: そのテストが通る/落ちる理由を、テスト本体だけを読んで説明できるか。説明にヘルパーの中身が要るなら、その値をテスト本体に戻すこと。
- **トートロジー（tautological）**——期待値を、コードが計算するのと同じやり方で計算してしまっているもの（`expect(add(a, b)).toBe(a + b)`、手で同じ手順から導出したスナップショット、それ自身と等しいと表明された定数）。構造上必ず通ってしまい、コードと食い違うことが原理的にありえない。期待値は独立した真実の源——仕様、既知の正しい値、手で計算した結果——から取る。計算はテストを書く前に済ませ、アサーションにはその結果をリテラルで書くこと（`toBe(15)`）。
