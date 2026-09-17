---
name: sanitize-doc
description: 文章を完成品として仕上げ直す。語彙の平易化、装飾文言、会話の名残をまとめて直す。文章の最終仕上げ・サニタイズが必要なとき、他のスキルが仕上げ工程として必要とするときに使う。
---

# sanitize-doc

対象ファイルに対して、次の3つのスキルをこの順で Skill ツールで発動する。

1. `plain-vocab` — 語彙を平易にする（硬語・外来語・日英混在）
2. `trim-ai-smell` — 装飾文言を削る
3. `trim-session-context` — 会話の名残(production residue)を削る

完了条件: 3つのスキルを適用し終えている。
