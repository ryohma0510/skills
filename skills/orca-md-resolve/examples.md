# 例

行特定の手順は `scripts/resolve-excerpt-lines.py` が正本。ここは入出力の形だけを示す。

## ペイロード

```
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

報告は `docs/spec.md:162`。以降の修正指示もこの行を使う。

## スクリプト

```bash
python3 scripts/resolve-excerpt-lines.py parse < payload.txt
python3 scripts/resolve-excerpt-lines.py resolve \
  --file docs/spec.md \
  --excerpt '明示的な保存操作により、入力項目順序設定がテナント単位で 1 セット保存されることを確認で' \
  --hint-start 160 --hint-end 172
```
