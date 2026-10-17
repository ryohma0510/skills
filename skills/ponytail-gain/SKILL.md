---
name: ponytail-gain
description: "ベンチマークに基づく ponytail の削減効果（コード・コスト・速度）スコアボード。一回限りの表示。/ponytail-gain、「what does ponytail save」「ponytail impact」"
---
<!--
source: https://github.com/DietrichGebert/ponytail/tree/main/skills/ponytail-gain
imported_at: 2026-10-17
upstream_commit: 16352ac229eb08a9598dcae48fe9f2b342567d86
license: MIT (LICENSE)
-->

# Ponytail Gain

呼び出されたらこのスコアボードを表示する。一回限り。モード変更・フラグファイル・永続化はしない。

数値は公開エージェントベンチマーク Ponytail 5 に基づく: ヘッドレス Claude Code（Opus 5.5、既定 effort）で39タスク（実 FastAPI + React リポの機能チケット、バグ修正、セキュリティ・プライバシー、小アプリ）、各5回、同エージェントでスキルなしと比較。18タスクに正しさ・安全性の隠しチェック。各数値はタスク別中央値の幾何平均。測定値であり、現在のリポから算出したものではない。
出典: `benchmarks/results/2026-10-07-agentic.md` と README。

## スコアボード

プレーン ASCII バー。バー長は no-skill 基準に対する ponytail の比率。ラベルに正確な数値:

```
  ponytail gain           benchmark · 39 tasks × 5 runs · Opus 5.5

  no-skill        ████████████████████  100%
  Lines of code   █████████···········   47%   ▼ 53%
  Output tokens   ███████████·········   55%   ▼ 45%
  Cost            ███████████████·····   74%   ▼ 26%
  Time            ████████████········   59%   ▼ 41%
  Hidden checks passed   97%  (no-skill 96%)
  Tests where the logic needs one   98%  (no-skill 68%)

  This repo:  /ponytail-debt  (shortcuts you deferred)
              /ponytail-audit (what's still cuttable)
```

## 正直さの境界

これらはベンチマーク平均であり、このリポの実測ではない。リポ単位の削減数（「ここで X 行/トークン節約」）は**絶対に出さない**: 書かなかった版は存在しないため、ライブリポに引く実 baseline がない。リポで実数が取れるのは `/ponytail-debt`（数えた台帳）のみ。このカードはそこを指す。

## 境界

一回限りの表示。編集なし、モード変更なし。
