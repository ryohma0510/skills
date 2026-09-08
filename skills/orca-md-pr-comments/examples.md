# 例

行特定の手順は `scripts/resolve-excerpt-lines.py` が正本。ここは入出力の形だけを示す。

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

`reported lines` は 160-172。本文の該当は次の1行（例では162行目）。

```
- [ ] **AC-026** 明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認できる（注記）
```

resolve の結果:

```json
{"status":"resolved","start_line":162,"end_line":162,"confidence":"high","match_method":"substring"}
```

投稿は `line=162` のみ。`start_line` は付けない。

投稿本文の例: `AC-026 の「テナント単位で 1 セット保存されること」を直してほしい。`

元の user comment は「ここを直してほしい」。対象を excerpt から補い、指摘や理由は足していない。

## このスキルを進めないペイロード

実装中に同じ形を貼っただけなら、行特定も投稿もしない。

```
File: docs/spec.md
Lines 160-172
Excerpt:
│ 明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で
User comment: "ここを直してほしい"
```

## スクリプト

```bash
python3 scripts/resolve-excerpt-lines.py parse < payload.txt
python3 scripts/resolve-excerpt-lines.py resolve \
  --file docs/spec.md \
  --excerpt '明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で' \
  --hint-start 160 --hint-end 172
```
