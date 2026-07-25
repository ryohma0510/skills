# 実測手順と計測結果

## 測り方

`scripts/measure.sh` は `claude -p` を1回走らせ、`--output-format json` が返す `modelUsage` から `inputTokens + cacheCreationInputTokens + cacheReadInputTokens` を合計して出す。プロンプトキャッシュが効くと `cacheCreationInputTokens` だけを見た値は途中から 0 に落ちるため、3つを必ず足す。

レバーを1つずつ評価するときは、候補を1個だけ書いた設定ファイルを `--bare` 付きで測り、同じく `--bare` で測ったベースラインとの差を取る。

```bash
./scripts/measure.sh --bare                    # ベースライン
echo '{"disableWorkflows": true}' > /tmp/one.json
./scripts/measure.sh --bare /tmp/one.json      # 候補1個
```

### 実行ディレクトリで数値が変わる

| 呼び方 | 読み込むもの |
| --- | --- |
| `--bare` | 何も読まない。ハーネスの下限 |
| 既定 | ユーザー設定とユーザースキル。空の一時ディレクトリで走る |
| `--here` | 上記に加えてカレントディレクトリの `CLAUDE.md`・MCP サーバ・プロジェクトスキル・`.claude/settings.json` |

プロジェクトの `.claude/settings.json` を評価できるのは `--here` だけである。適用前後は同じ呼び方で測って比べる。

同一環境での実測例（2.1.220 / Sonnet 5）:

| 呼び方 | プリセットなし | プリセットあり |
| --- | --- | --- |
| `--bare` | 33,906 | 20,089 |
| 既定 | 35,780 | 22,113 |
| `--here`（プロジェクト設定として配置） | 35,851 | 22,149 |

`--bare` と既定の差 1,945 は `~/.claude/skills/` に置いたユーザースキルのカタログ分である。`disableBundledSkills` が消すのはバイナリ同梱のスキルだけなので、この分は削減後も残る。

## 計測結果（Claude Code 2.1.220 / Sonnet 5 / ベースライン 33,906）

| 順位 | レバー | 削減 | 割合 |
| --- | --- | --- | --- |
| 1 | `disableWorkflows` | 7,900 | 23.3% |
| 2 | `disableArtifact` | 4,144 | 12.2% |
| 3 | `disableBundledSkills` | 1,890 | 5.6% |
| 4 | `deny: ScheduleWakeup` | 1,403 | 4.1% |
| 5 | `deny: ReportFindings` | 821 | 2.4% |
| 6 | `env: CLAUDE_CODE_DISABLE_CRON` | 148 | 0.44% |
| 7 | `deny: NotebookEdit` | 8 | 0.02% |
| 8 | `deny: DesignSync` / `SendMessage` / `PushNotification` / `CronCreate` / `CronDelete` | 各 6 | 各 0.02% |
| 13 | `deny: Monitor` | 5 | 0.01% |
| 14 | `deny: CronList` | 4 | 0.01% |
| 15 | `disableRemoteControl` | 0 | 0% |
| 15 | `disableClaudeAiConnectors` | 0 | 0% |
| 15 | `deny: RemoteTrigger` | 0 | 0% |

`deny: AskUserQuestion` `deny: EnterPlanMode` `deny: ExitPlanMode` は対話モード専用ツールで `-p` にロードされないため、この方法では測れない。対話セッションでは存在するので `/context` で確認する。

`disableRemoteControl` と `disableClaudeAiConnectors` の 0 は計測環境の事情による。クラウドセッションはリモートコントロールが元から利用不可で、コネクタも未設定だった。ローカルでコネクタを繋いでいれば、そのツールスキーマ分が削れる。

`deny: RemoteTrigger` が 0 なのは、この版に該当ツールがロードされないため。

## 個別ツールの deny がほとんど効かない理由

`tengu_non_deferrable_builtins` に載っているツールだけがスキーマを常時展開し、それ以外は ToolSearch によって名前だけの遅延ロードになる。遅延ロード対象を deny しても消えるのは名前分の 5〜6 トークンだけで、上の表で4位と5位だけが突出しているのはこの2つが非遅延ビルトインだからである。

ToolSearch の有効判定は `qYr()` が返すモードで決まり、環境変数 `ENABLE_TOOL_SEARCH` 未設定・first-party ホスト・対応モデルなら既定で有効になる。

## ロギングプロキシで測るときの落とし穴

`ANTHROPIC_BASE_URL` を自前のプロキシに向けると、Claude Code は「プロキシが `tool_reference` ブロックを転送しない可能性がある」と判断して ToolSearch を自動的に無効化する。全ツールのスキーマが展開された状態のペイロードが観測されるため、個別ツールが実際よりはるかに大きく見える。

プロキシ経由で得たツール別ランキングを、そのまま通常セッションの削減見込みとして使わないこと。プロキシで測るなら `ENABLE_TOOL_SEARCH=true` を明示して条件を揃える。

## 出典

Matt Pocock, "How To Kill The Bloat In Claude Code's System Prompt" (AI Hero)
<https://www.aihero.dev/how-to-kill-the-bloat-in-claude-codes-system-prompt>

記事は `/context` とロギングプロキシで測る手順を示し、著者の環境で削るに値した設定を列挙している。記事自身が "Treat it as a menu, not a prescription." と断っているとおり、列挙されたリストは環境ごとに測り直して取捨する前提のものである。
