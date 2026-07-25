#!/usr/bin/env bash
# Report the per-request input-token cost of a Claude Code configuration.
#
#   ./measure.sh                 # user + global settings, isolated from any project
#   ./measure.sh preset.json     # the same, with preset.json layered on top
#   ./measure.sh --here          # the current directory as it really is
#   ./measure.sh --bare          # no settings sources at all (harness floor)
#   ./measure.sh --bare p.json   # preset.json alone, nothing else
#
# By default the run happens in an empty directory, so project CLAUDE.md, MCP
# servers, project skills and project settings stay out of the number. Pass
# --here to measure a project as configured, which is the only mode that picks
# up a project-level .claude/settings.json. Compare runs taken the same way.
set -euo pipefail

command -v claude >/dev/null || { echo "claude not found in PATH" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found in PATH" >&2; exit 1; }

args=(-p "Reply with exactly: ok" --output-format json)
here=""

while true; do
  case "${1-}" in
    --bare) args+=(--setting-sources ''); shift ;;
    --here) here=1; shift ;;
    *) break ;;
  esac
done

if [ $# -gt 0 ]; then
  [ -f "$1" ] || { echo "settings file not found: $1" >&2; exit 1; }
  args+=(--settings "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")")
fi

if [ -z "$here" ]; then
  workdir=$(mktemp -d)
  trap 'rm -rf "$workdir"' EXIT
  cd "$workdir"
fi

claude "${args[@]}" | python3 -c '
import json, re, sys

raw = sys.stdin.read()
match = re.search(r"\"modelUsage\":(\{.*\}\}),\"permission_denials\"", raw)
if not match:
    sys.exit("could not parse modelUsage from claude output")

usage = json.loads(match.group(1))
print(max(
    entry.get("inputTokens", 0)
    + entry.get("cacheCreationInputTokens", 0)
    + entry.get("cacheReadInputTokens", 0)
    for entry in usage.values()
))
'
