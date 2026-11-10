#!/usr/bin/env bash
# load-finding.sh — print a finding and every local artifact that already mentions it.
#
# Reads the finding from a local mirror (<mirror>/issue<N>-*.md) when present, otherwise from the findings
# repo with gh. Then lists: duplicates-index lines mentioning it, other findings citing "#<N>", local
# drafts / submissions / comments that cite it, and PoC files whose name contains Issue<N>.
#
# Usage: load-finding.sh <N> [--mirror <dir>] [--repo <owner/repo>] [--findings <dir>] [--tests <dir>]
#   --mirror    local mirror of the findings repo (default: grimoire/findings/original-repo-findings)
#   --repo      owner/repo of the findings repo (used when the mirror has no file for <N>)
#   --findings  root of the user's local findings work (default: grimoire/findings)
#   --tests     where PoCs live (default: test)
# Run from the repository root. Requires gh only when falling back to the remote repo.
set -euo pipefail

n="${1:?usage: load-finding.sh <N> [--mirror <dir>] [--repo <owner/repo>] [--findings <dir>] [--tests <dir>]}"
shift
mirror="grimoire/findings/original-repo-findings"
repo=""
findings="grimoire/findings"
tests="test"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mirror)   mirror="$2"; shift 2 ;;
    --repo)     repo="$2"; shift 2 ;;
    --findings) findings="$2"; shift 2 ;;
    --tests)    tests="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_workspace-guard.sh"
require_inside "--mirror" "$mirror"
require_inside "--findings" "$findings"
require_inside "--tests" "$tests"

file="$(ls "$mirror"/issue"$n"-*.md 2>/dev/null | head -1 || true)"
echo "=== Finding #$n"
if [[ -n "$file" ]]; then
  require_inside "the mirrored finding" "$file"
  echo "(local mirror: $file)"
  cat "$file"
elif [[ -n "$repo" ]]; then
  gh issue view "$n" --repo "$repo" --comments
else
  echo "not in $mirror and no --repo given" >&2
  exit 1
fi

echo
echo "=== Duplicates index lines mentioning #$n"
grep -n -E "#$n([^0-9]|$)" "$mirror"/DUPLICATES.md 2>/dev/null || echo "(none)"

echo
echo "=== Other mirrored findings citing #$n"
grep -l -E "#$n([^0-9]|$)" "$mirror"/*.md 2>/dev/null | grep -v -E "/issue$n-|DUPLICATES.md" || echo "(none)"

echo
echo "=== Local work citing #$n (drafts, submissions, comments, tomes)"
grep -rl -E "#$n([^0-9]|$)|issue$n[^0-9]|issues/$n([^0-9]|$)" "$findings" grimoire/tomes 2>/dev/null \
  | grep -v "^$mirror/" || echo "(none)"

echo
echo "=== PoC files named after #$n"
find "$tests" -iname "*issue${n}[^0-9]*" -o -iname "*issue${n}.t.sol" 2>/dev/null | sort || true
