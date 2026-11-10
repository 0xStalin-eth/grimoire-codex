#!/usr/bin/env bash
# session-status.sh — Set one file's row in a status-snapshot SESSIONS.md (hypotheses/, peer-review/,
# mitigation-review/). The table holds one row per file with its CURRENT status only; this replaces the
# file's row, or adds it if missing. Safe for parallel sessions: the update runs under a lock and the
# new table replaces the old one in a single rename, so no session's row is lost.
# Usage: session-status.sh <SESSIONS.md> <file-name> <status> [note]
#   <status>  the folder the file is in now (WIP, valid, invalid, done, archived, PENDINGS)
#   [note]    short note: verdict, claim, what the client was asked (no '|' characters)
# The session ID is read from $CLAUDE_CODE_SESSION_ID; the script refuses to run without it.
# Example: session-status.sh grimoire/mitigation-review/SESSIONS.md M-3-mitigation-review.md PENDINGS \
#            "Partially fixed; asked the client Q2 in [[client-communication/M-3]]"

set -euo pipefail

log="${1:?usage: session-status.sh <SESSIONS.md> <file-name> <status> [note]}"
name="${2:?file name required}"
status="${3:?status required}"
note="${4:-}"
sid="${CLAUDE_CODE_SESSION_ID:-}"

[ -n "$sid" ] || { echo "REFUSED: \$CLAUDE_CODE_SESSION_ID is unset; never guess a session ID" >&2; exit 1; }
case "$name$status$note" in *'|'*) echo "REFUSED: '|' would break the table" >&2; exit 1 ;; esac

header='| File | Status | Session ID | Updated | Notes |'
divider='|---|---|---|---|---|'
row="| $name | $status | $sid | $(date '+%Y-%m-%d %H:%M') | $note |"

lock="$log.lock"
for _ in $(seq 1 100); do
  mkdir "$lock" 2>/dev/null && break
  sleep 0.1
done
[ -d "$lock" ] || { echo "REFUSED: $lock is held; another session is updating the log" >&2; exit 1; }
trap 'rmdir "$lock"' EXIT

tmp="$(mktemp "$log.XXXXXX")"
{
  echo "$header"
  echo "$divider"
  if [ -f "$log" ]; then
    # keep every other file's row; drop the header, the divider and this file's old row
    awk -F'|' -v n="$name" 'NR > 2 && NF > 1 { f = $2; gsub(/^ +| +$/, "", f); if (f != n) print }' "$log"
  fi
  echo "$row"
} > "$tmp"
mv "$tmp" "$log"
echo "$row"
