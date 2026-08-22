#!/usr/bin/env bash
# 現在のブランチの直接の親とみなせるブランチを、リモート修飾つきの ref で1行出力する（例: origin/develop/a）。
# 候補は develop/ topic/ release/ のプレフィックス付きと、develop / master / main。
# merge-base から HEAD までのコミット数が最小の候補を親とみなす。候補がなければ <remote>/main。
set -euo pipefail

current=$(git branch --show-current)

# リモート名は origin 固定にせず、追跡先 → origin → 最初のリモート の順に決める
remote=$(git config --get "branch.${current}.remote" 2>/dev/null || true)
if [ -z "$remote" ]; then
  if git remote | grep -qx origin; then
    remote=origin
  else
    remote=$(git remote | head -n 1)
  fi
fi
[ -n "$remote" ] || { echo "main"; exit 0; }

git fetch --prune --quiet "$remote" || true

head_sha=$(git rev-parse HEAD)
best=""
best_count=""

# 候補ゼロのとき grep が非ゼロで終わるため、失敗を握りつぶしてフォールバックに到達させる
candidates=$(git branch -r --format='%(refname:short)' \
  | sed "s|^${remote}/||" \
  | { grep -E '^(develop|topic|release)/|^(develop|master|main)$' || true; } \
  | { grep -v "^${current}$" || true; } \
  | sort -u)

for candidate in $candidates; do
  merge_base=$(git merge-base "$head_sha" "${remote}/${candidate}" 2>/dev/null) || continue
  # HEAD が候補の祖先なら、その候補は親ではなく子孫
  [ "$merge_base" = "$head_sha" ] && continue
  count=$(git rev-list --count "${merge_base}..${head_sha}")
  if [ -z "$best_count" ] || [ "$count" -lt "$best_count" ]; then
    best=$candidate
    best_count=$count
  fi
done

echo "${remote}/${best:-main}"
