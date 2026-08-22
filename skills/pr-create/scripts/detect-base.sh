#!/usr/bin/env bash
# 現在のブランチの直接の親とみなせるブランチ名を1行で出力する。
# 候補は develop/ topic/ release/ のプレフィックス付きと、develop / master / main。
# merge-base から HEAD までのコミット数が最小の候補を親とみなす。候補がなければ main。
set -euo pipefail

git fetch --prune --quiet || true

current=$(git branch --show-current)
head_sha=$(git rev-parse HEAD)
best=""
best_count=""

# 候補ゼロのとき grep が非ゼロで終わるため、失敗を握りつぶして main へフォールバックさせる
candidates=$(git branch -r --format='%(refname:short)' \
  | sed 's|^origin/||' \
  | { grep -E '^(develop|topic|release)/|^(develop|master|main)$' || true; } \
  | { grep -v "^${current}$" || true; } \
  | sort -u)

for candidate in $candidates; do
  merge_base=$(git merge-base "$head_sha" "origin/${candidate}" 2>/dev/null) || continue
  # HEAD が候補の祖先なら、その候補は親ではなく子孫
  [ "$merge_base" = "$head_sha" ] && continue
  count=$(git rev-list --count "${merge_base}..${head_sha}")
  if [ -z "$best_count" ] || [ "$count" -lt "$best_count" ]; then
    best=$candidate
    best_count=$count
  fi
done

echo "${best:-main}"
