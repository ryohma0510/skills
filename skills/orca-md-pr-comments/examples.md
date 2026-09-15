# 例

行特定は `orca-md-resolve` が正本。ここは投稿意図と投稿本文の形だけを示す。

## 投稿意図があるペイロード

```
このコメントを PR のレビューコメントとして投稿して

File: docs/spec.md
Source: markdown

Lines 160-172
Excerpt:
│ 明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で
User comment: "ここを直してほしい"
```

`orca-md-resolve` が `docs/spec.md:162` を返したとする。投稿は `line=162` のみ。`start_line` は付けない。

投稿本文の例: `AC-026 の「テナント単位で 1 セット保存されること」を直してほしい。`

元の user comment は「ここを直してほしい」。対象を excerpt から補い、指摘や理由は足していない。

## このスキルを進めないペイロード

実装中に同じ形を貼っただけなら、行特定も投稿もしない。行だけ知りたいときは `orca-md-resolve` を使う。

```
File: docs/spec.md
Lines 160-172
Excerpt:
│ 明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で
User comment: "ここを直してほしい"
```
