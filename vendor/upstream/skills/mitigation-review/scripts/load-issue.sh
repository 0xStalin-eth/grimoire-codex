#!/usr/bin/env bash
# load-issue.sh — dump a findings-repo issue with its full comment thread, then list every
# PR / commit reference found in it (the client usually links the fix there).
#
# Usage: load-issue.sh <issue-number> <owner/repo>
# Requires: gh (authenticated)
set -euo pipefail

n="${1:?usage: load-issue.sh <issue-number> <owner/repo>}"
repo="${2:?usage: load-issue.sh <issue-number> <owner/repo>}"

thread="$(gh issue view "$n" --repo "$repo" --comments)"
printf '%s\n' "$thread"

echo
echo "=== References found in thread ==="
printf '%s\n' "$thread" | grep -oE 'github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(pull|commit)/[0-9a-f]+' | sort -u || true
printf '%s\n' "$thread" | grep -oE '(PR|pull request) ?#[0-9]+' | sort -u || true
printf '%s\n' "$thread" | grep -oE '\b[0-9a-f]{7,40}\b' | grep -E '[a-f]' | sort -u | head -20 || true
