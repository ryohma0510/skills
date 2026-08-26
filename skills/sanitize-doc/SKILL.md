---
name: sanitize-doc
description: 文章を完成品として仕上げ直す。装飾文言と会話の名残の両方をまとめて削る。文章の最終仕上げ・サニタイズが必要なとき、他のスキルが仕上げ工程として必要とするときに使う。
---

# sanitize-doc

対象ファイルに対して、次の2つのスキルをこの順で Skill ツールで発動する。

1. `trim-ai-smell` — 装飾文言を削る
2. `trim-session-context` — 会話の名残(production residue)を削る

完了条件: 両方のスキルを適用し終えている。
