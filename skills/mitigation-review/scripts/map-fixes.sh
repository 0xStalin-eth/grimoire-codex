#!/usr/bin/env bash
# map-fixes.sh — map the mitigation range to PRs, issue references and touched files.
#
# Usage: map-fixes.sh <baseline> <head> [path-filter...]
#   baseline:     audited commit
#   head:         mitigation commit
#   path-filter:  optional path prefixes to flag in-scope files (e.g. src/vault-v2 src/risk-engines)
#
# Output, per "Merge pull request" merge (or per commit when the range has no PR merges):
#   <sha> <subject>
#     issues: findings-repo issue numbers parsed from the branch name and the PR's commit messages
#             (followup-N, follow-up #N, "Cyfrin ... #N", issue N). PR numbers are not included.
#     commits: the PR's non-merge commits
#     files:  files the PR changed; [*] = matches a path filter (in scope)
set -euo pipefail

base="${1:?usage: map-fixes.sh <baseline> <head> [path-filter...]}"
head="${2:?usage: map-fixes.sh <baseline> <head> [path-filter...]}"
shift 2
filters=("$@")

issue_refs() {
  grep -oiE '(follow-?up[-_ /#]*|cyfrin[^0-9#]*#|issue[-_ /#]*)[0-9]+' \
    | grep -oE '[0-9]+$' | sort -un | sed 's/^/#/' | tr '\n' ' ' || true
}

print_files() {
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    mark=" "
    for p in ${filters[@]+"${filters[@]}"}; do
      [[ "$f" == "$p"* ]] && mark="*"
    done
    echo "    [$mark] $f"
  done
}

prs="$(git log --merges --format=%H -E --grep='^Merge pull request #[0-9]+' "$base..$head")"

if [ -n "$prs" ]; then
  for m in $(git rev-list --reverse $prs --no-walk); do
    subj="$(git log -1 --format=%s "$m")"
    # Commits unique to the PR branch (second parent side).
    commits="$(git rev-list --no-merges "$m^1..$m^2")"
    issues="$( { echo "$subj"; [ -n "$commits" ] && git log --no-walk --format='%s %b' $commits; } | issue_refs)"
    echo "$(git rev-parse --short "$m") $subj"
    echo "  issues: ${issues:-none}"
    echo "  commits:"
    for c in $commits; do echo "    $(git log -1 --format='%h %s' "$c")"; done
    echo "  files:"
    git diff --name-only "$m^1...$m^2" | print_files
    echo
  done
else
  for c in $(git rev-list --reverse --no-merges "$base..$head"); do
    echo "$(git log -1 --format='%h %s' "$c")"
    echo "  issues: $(git log -1 --format='%s %b' "$c" | issue_refs)"
    echo "  files:"
    git show --name-only --format= "$c" | print_files
    echo
  done
fi

echo "=== Range diffstat ($base..$head${filters[*]:+, filtered}) ==="
git diff --stat "$base" "$head" -- ${filters[@]+"${filters[@]}"} | tail -40
