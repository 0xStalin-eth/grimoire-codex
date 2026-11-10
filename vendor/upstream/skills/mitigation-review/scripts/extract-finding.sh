#!/usr/bin/env bash
# extract-finding.sh — print one finding's full section from a Cyfrin-style report.
#
# Usage: extract-finding.sh <report.md> <ID | title-substring>
#   ID:               H-2, L-5, I-10 ... (derived by index-report.sh)
#   title-substring:  any case-insensitive fragment of the `###` heading (e.g. an issue title)
#
# Prints from the finding heading up to (not including) the next `###` or `##` heading.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
report="${1:?usage: extract-finding.sh <report.md> <ID|title-substring>}"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_workspace-guard.sh"
require_inside "the report" "$report"
key="${2:?usage: extract-finding.sh <report.md> <ID|title-substring>}"

if [[ "$key" =~ ^[CHMLIG]-[0-9]+$ ]]; then
  line="$("$here/index-report.sh" "$report" | awk -F'\t' -v k="$key" '$1 == k { print $2 }')"
else
  matches="$("$here/index-report.sh" "$report" | awk -F'\t' -v k="$key" 'index(tolower($3), tolower(k)) { print }')"
  count="$(printf '%s' "$matches" | grep -c . || true)"
  if [ "$count" -gt 1 ]; then
    echo "error: '$key' matches $count findings:" >&2
    printf '%s\n' "$matches" | cut -f1,3 >&2
    exit 1
  fi
  line="$(printf '%s' "$matches" | cut -f2)"
  [ -n "$line" ] && echo "# $(printf '%s' "$matches" | cut -f1) (report line $line)" >&2
fi

[ -n "${line:-}" ] || { echo "error: no finding matches '$key'" >&2; exit 1; }

awk -v start="$line" 'NR == start { print; next } NR > start && /^##/ { exit } NR > start { print }' "$report"
