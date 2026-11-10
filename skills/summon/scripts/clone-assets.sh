#!/usr/bin/env bash
# clone-assets.sh — Shallow-clone in-scope bug-bounty repositories at pinned refs.
# Used by the summon skill's "Acquire Target" step (Step 0) after the user approves
# the asset list. Clones each repo into the current directory (the project root).
#
# Usage:
#   clone-assets.sh <entry> [<entry> ...]
#   clone-assets.sh --from-file <path>     # one entry per line; blank lines and # comments ignored
#
# Each entry is:  <repo_url>[@<ref>]
#   - <repo_url> is any git-cloneable URL (https or ssh).
#   - <ref> (optional) is a branch, tag, or full/short commit SHA to pin to.
#
# Examples:
#   clone-assets.sh https://github.com/org/repo@a1b2c3d
#   clone-assets.sh https://github.com/org/repo@v1.2.0 https://github.com/org/other
#   clone-assets.sh --from-file assets.txt
#
# Behavior:
#   - Destination dir name is derived from the repo (basename, ".git" stripped).
#   - Existing destination dirs are SKIPPED (idempotent — never overwrites).
#   - A SHA-looking ref is fetched explicitly (git clone --branch rejects SHAs).
#   - Individual failures do not abort the batch; a summary is printed at the end.
# Exit code: 0 if every entry cloned or was skipped; 1 if any entry failed.

set -uo pipefail

print_usage() {
  echo "Usage: clone-assets.sh <repo_url[@ref]> [...]   |   clone-assets.sh --from-file <path>" >&2
}

# Collect entries from args or a file.
declare -a entries=()
if [ "${1:-}" = "--from-file" ]; then
  file="${2:-}"
  if [ -z "$file" ] || [ ! -f "$file" ]; then
    echo "Error: --from-file requires a readable file path" >&2
    print_usage
    exit 1
  fi
  while IFS= read -r line || [ -n "$line" ]; do
    # Strip leading/trailing whitespace
    line="$(printf '%s' "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    entries+=("$line")
  done < "$file"
else
  if [ "$#" -eq 0 ]; then
    print_usage
    exit 1
  fi
  entries=("$@")
fi

if [ "${#entries[@]}" -eq 0 ]; then
  echo "Error: no entries to clone" >&2
  exit 1
fi

declare -a cloned=()
declare -a skipped=()
declare -a failed=()

# A ref looks like a commit SHA if it is 7-40 hex chars.
is_sha() {
  printf '%s' "$1" | grep -Eq '^[0-9a-fA-F]{7,40}$'
}

for entry in "${entries[@]}"; do
  # Split <repo_url>@<ref> on the LAST '@' so ssh URLs (git@host:...) survive.
  if printf '%s' "$entry" | grep -q '@'; then
    ref="${entry##*@}"
    url="${entry%@*}"
    # Guard against splitting an ssh "git@host" prefix when no ref was given:
    # if url has no host/path separator left, treat the whole thing as the url.
    case "$url" in
      *[:/]*) : ;;             # looks like a real url, keep the split
      *) url="$entry"; ref="" ;;
    esac
  else
    url="$entry"
    ref=""
  fi

  dest="$(basename "$url")"
  dest="${dest%.git}"

  if [ -z "$dest" ]; then
    echo "  ✗ could not derive directory name from: $entry" >&2
    failed+=("$entry")
    continue
  fi

  if [ -e "$dest" ]; then
    echo "  • skip (exists): $dest"
    skipped+=("$dest")
    continue
  fi

  echo "  → cloning $url${ref:+ @ $ref} -> $dest/"

  if [ -z "$ref" ]; then
    if git clone --depth 1 "$url" "$dest" >/dev/null 2>&1; then
      cloned+=("$dest")
    else
      echo "  ✗ clone failed: $url" >&2
      failed+=("$entry")
      rm -rf "$dest" 2>/dev/null || true
    fi
  elif is_sha "$ref"; then
    # Commit pins: init + shallow fetch the exact ref, then checkout.
    if git init -q "$dest" >/dev/null 2>&1 \
      && git -C "$dest" remote add origin "$url" >/dev/null 2>&1 \
      && git -C "$dest" fetch --depth 1 origin "$ref" >/dev/null 2>&1 \
      && git -C "$dest" checkout -q FETCH_HEAD >/dev/null 2>&1; then
      cloned+=("$dest")
    else
      echo "  ✗ fetch/checkout failed for commit $ref: $url" >&2
      failed+=("$entry")
      rm -rf "$dest" 2>/dev/null || true
    fi
  else
    # Branch or tag.
    if git clone --depth 1 --branch "$ref" "$url" "$dest" >/dev/null 2>&1; then
      cloned+=("$dest")
    else
      echo "  ✗ clone failed for ref $ref: $url" >&2
      failed+=("$entry")
      rm -rf "$dest" 2>/dev/null || true
    fi
  fi
done

echo ""
echo "Clone summary: ${#cloned[@]} cloned, ${#skipped[@]} skipped, ${#failed[@]} failed"
if [ "${#failed[@]}" -gt 0 ]; then
  printf '  failed: %s\n' "${failed[@]}" >&2
  exit 1
fi
exit 0
