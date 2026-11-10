#!/usr/bin/env bash
# link-issues.sh — match findings-repo issues to report findings by title.
#
# Usage: link-issues.sh <report.md> <owner/repo>
# Requires: gh (authenticated)
#
# Output (TSV): ID  report-line  issue#  title
# Issue titles normally equal the report's `###` headings; matching ignores case, backticks and
# punctuation, then falls back to "one title is a prefix of the other". Unmatched findings get
# issue "?" — map those by content or ask the user.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
report="${1:?usage: link-issues.sh <report.md> <owner/repo>}"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_workspace-guard.sh"
require_inside "the report" "$report"
repo="${2:?usage: link-issues.sh <report.md> <owner/repo>}"

issues="$(gh issue list --repo "$repo" --state all --limit 500 --json number,title \
  --jq '.[] | "\(.number)\t\(.title)"')"

python3 -I - <("$here/index-report.sh" "$report") <(printf '%s\n' "$issues") <<'PY'
import re, sys

def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

findings = [l.rstrip("\n").split("\t", 2) for l in open(sys.argv[1]) if l.strip()]
issues = [l.rstrip("\n").split("\t", 1) for l in open(sys.argv[2]) if "\t" in l]
by_title = {norm(t): n for n, t in issues}

for fid, line, title in findings:
    t = norm(title)
    n = by_title.get(t)
    if n is None:
        cands = [num for it, num in by_title.items() if it and (t.startswith(it) or it.startswith(t))]
        n = cands[0] if len(cands) == 1 else "?"
    print(f"{fid}\t{line}\t#{n}\t{title[:100]}" if n != "?" else f"{fid}\t{line}\t?\t{title[:100]}")
PY
