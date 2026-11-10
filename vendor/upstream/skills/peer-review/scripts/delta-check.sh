#!/usr/bin/env bash
# delta-check.sh — decide whether code a finding blames is new in the audited delta or pre-existing.
#
# For <file>: reports whether it exists at <baseline> and at <audited>, and whether it changed between
# them. For each <symbol>: how many lines mention it at each commit, and any changed (+/-) lines that
# mention it in the diff.
#
# Usage: delta-check.sh <baseline> <audited> <file> [<symbol> ...]
# Run from the repository root.
set -euo pipefail

base="${1:?usage: delta-check.sh <baseline> <audited> <file> [<symbol> ...]}"
head="${2:?usage: delta-check.sh <baseline> <audited> <file> [<symbol> ...]}"
file="${3:?usage: delta-check.sh <baseline> <audited> <file> [<symbol> ...]}"
shift 3

exists() { git cat-file -e "$1:$2" 2>/dev/null && echo yes || echo no; }
echo "=== $file"
echo "exists at $base: $(exists "$base" "$file")    exists at $head: $(exists "$head" "$file")"
if [[ "$(exists "$base" "$file")" == "yes" ]]; then
  changed="$(git diff --stat "$base" "$head" -- "$file" | tail -1)"
  echo "changed in delta: ${changed:-no}"
else
  echo "new file in the delta"
fi

for sym in "$@"; do
  echo
  echo "--- $sym"
  b=0; h=0
  [[ "$(exists "$base" "$file")" == "yes" ]] && b="$(git show "$base:$file" | grep -c -- "$sym" || true)"
  [[ "$(exists "$head" "$file")" == "yes" ]] && h="$(git show "$head:$file" | grep -c -- "$sym" || true)"
  echo "lines mentioning it: baseline=$b audited=$h"
  git diff "$base" "$head" -- "$file" | grep -E '^[-+]' | grep -v -E '^(\+\+\+|---)' | grep -- "$sym" \
    || echo "(no changed lines mention it)"
done
