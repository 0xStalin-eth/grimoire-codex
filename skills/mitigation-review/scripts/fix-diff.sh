#!/usr/bin/env bash
# fix-diff.sh — show the commits that mitigate one issue and their combined diff.
#
# Usage: fix-diff.sh <issue-number> <baseline> <head> [pathspec...]
#
# Finds commits in baseline..head whose message (or the merge that brought them in) references
# the issue (`#N`, `followup-N`, `follow-up #N`), prints them, then the combined diff of the
# non-merge commits, oldest first. Pass pathspecs to drop test/doc noise.
set -euo pipefail

n="${1:?usage: fix-diff.sh <issue-number> <baseline> <head> [pathspec...]}"
base="${2:?}"
head="${3:?}"
shift 3

pat="(follow-?up[-_ /#]*|cyfrin[^0-9]*#|issue[-_ /#]*)$n([^0-9]|\$)"

declare -a shas=()
# Commits whose own message references the issue.
while IFS= read -r c; do [ -n "$c" ] && shas+=("$c"); done < <(git log --format=%H -E -i --grep="$pat" "$base..$head")
# Commits brought in by a merge whose message references the issue (branch name fix/...-N).
for m in $(git log --merges --format=%H -E -i --grep="$pat" "$base..$head"); do
  while IFS= read -r c; do [ -n "$c" ] && shas+=("$c"); done < <(git rev-list --no-merges "$m^1..$m")
done

[ "${#shas[@]}" -gt 0 ] || { echo "no commits reference issue #$n in $base..$head" >&2; exit 1; }

uniq_shas="$(printf '%s\n' "${shas[@]}" | awk '!seen[$0]++')"
ordered="$(git rev-list --reverse --no-merges "$base..$head" | grep -Fx -f <(printf '%s\n' "$uniq_shas") || true)"

echo "=== Commits for issue #$n ==="
for c in $ordered; do git log -1 --format='%h %ad %s' --date=short "$c"; done
echo
for c in $ordered; do
  echo "=================== $(git log -1 --format='%h %s' "$c") ==================="
  git show --stat --format= "$c" -- "$@"
  git show --format= "$c" -- "$@"
done
