#!/usr/bin/env bash
# commit-links.sh — render fix commits as markdown links to the client's GitHub repo, for the
# client-response line above the Cyfrin write-up.
#
# Usage: commit-links.sh <remote> <ref>...
#   remote:  git remote pointing at the client's repo (e.g. the one the PRs were merged into)
#   ref:     a fix commit (short or full sha), or a PR as `#N`, `pr:N`, or a PR URL.
#            PRs are resolved to their MERGE commit via `gh` — the write-up always links commits,
#            never PRs. An unmerged PR is an error.
#
# Output: [abc1234](https://github.com/<org>/<repo>/commit/<full-sha>) && [def5678](...)
set -euo pipefail

remote="${1:?usage: commit-links.sh <remote> <ref>...}"
shift
[ "$#" -gt 0 ] || { echo "usage: commit-links.sh <remote> <ref>..." >&2; exit 1; }

url="$(git remote get-url "$remote")"
url="${url%.git}"
url="${url/git@github.com:/https://github.com/}"
slug="${url#https://github.com/}"
# The report links the client's own repo; the Cyfrin audit repo is internal and readers can't open it.
case "$(printf '%s' "$slug" | tr '[:upper:]' '[:lower:]')" in
  cyfrin/*) echo "error: remote '$remote' is the Cyfrin repo $slug; use a remote for the client's own repo" >&2; exit 1 ;;
esac

resolve() {
  local ref="$1" pr=""
  case "$ref" in
    \#*) pr="${ref#\#}" ;;
    pr:*) pr="${ref#pr:}" ;;
    https://github.com/*/pull/*) pr="$(printf '%s' "$ref" | sed -E 's#.*/pull/([0-9]+).*#\1#')" ;;
  esac
  if [ -n "$pr" ]; then
    local sha
    sha="$(gh pr view "$pr" --repo "$slug" --json mergeCommit -q '.mergeCommit.oid // empty')"
    [ -n "$sha" ] || { echo "error: PR #$pr in $slug is not merged (no merge commit)" >&2; exit 1; }
    echo "$sha"
  else
    git rev-parse --verify "$ref^{commit}"
  fi
}

links=()
for r in "$@"; do
  full="$(resolve "$r")"
  links+=("[${full:0:7}]($url/commit/$full)")
done

out="${links[0]}"
for l in "${links[@]:1}"; do out="$out && $l"; done
echo "$out"
