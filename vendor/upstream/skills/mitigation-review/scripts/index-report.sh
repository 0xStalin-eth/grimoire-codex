#!/usr/bin/env bash
# index-report.sh — list every finding in a Cyfrin-style markdown report with a derived ID.
#
# Usage: index-report.sh <report.md>
#
# Findings are `### <title>` headings under `## <Severity> Risk` / `## Informational` / `## Gas`
# sections. Cyfrin reports do not print IDs, so they are derived from order within the section
# (C-1, H-1, M-1, L-1, I-1, G-1). Output (TSV): ID  line  title
set -euo pipefail

report="${1:?usage: index-report.sh <report.md>}"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_workspace-guard.sh"
require_inside "the report" "$report"
[ -f "$report" ] || { echo "error: $report not found" >&2; exit 1; }

awk '
  /^## / {
    s = tolower($0)
    if (s ~ /critical/) p = "C"
    else if (s ~ /high/) p = "H"
    else if (s ~ /medium/) p = "M"
    else if (s ~ /low/) p = "L"
    else if (s ~ /informational/) p = "I"
    else if (s ~ /gas/) p = "G"
    else p = ""
    next
  }
  /^### / && p != "" {
    n[p]++
    t = substr($0, 5)
    printf "%s-%d\t%d\t%s\n", p, n[p], NR, t
  }
' "$report"
