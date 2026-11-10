#!/usr/bin/env bash
# verify-fix.sh — test a candidate fix without touching the workspace's own files.
#
# Everything runs INSIDE the git workspace this is started from: the comparison uses this session's private copy in
# <workspace>/.isolated/<session-id>/<name>/ (scripts/isolated-workspace.sh) and keeps its scratch files in
# <workspace>/.isolated/<session-id>/.verify-<name>/. The copy is KEPT after the run (it is reused by the next run with
# the same --name); remove it with `isolated-workspace.sh remove <name>` only once the user has closed the lead.
# Nothing is read or written outside the workspace: patched files must be inside
# it too (e.g. .isolated/work/i<N>/b/), and sibling workspaces of the same repo are refused.
#
# Before the baseline run the copy is proven byte-for-byte identical to the workspace; if it is not (uncommitted edits
# to tracked files), the script stops and lists them. The suites run on the original code, the patched files are
# copied in, the suites run again, and every test whose result changed is printed, keyed by suite. At the end the
# comparison runs again, to show whether the workspace changed during the run.
#
# Usage: verify-fix.sh --patch <repo/File.sol>=<patched/File.sol> [--patch ...] --suite '<glob>' [--suite ...]
#                      --name <name> [--with-modified]
#   --patch     a repo file and the patched copy to swap in for the "after" run (repeatable)
#   --suite     a forge --match-path glob (repeatable), e.g. 'test/pocs/Issue12*.t.sol' 'test/unit/**'
#   --name      name of this session's isolated copy (required, e.g. i12); an existing one is synced and reused
#   --keep      accepted for compatibility; copies are always kept
#   --with-modified  include the workspace's uncommitted edits to tracked files in the baseline (only after
#               confirming they are code you want to test against, not another session's temporary patch)
# Env: FORGE_ARGS  extra arguments for forge test (e.g. "--no-match-path 'test/fork/**'")
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
iso_sh="$here/isolated-workspace.sh"
# shellcheck source=_workspace-guard.sh
source "$here/_workspace-guard.sh"
patches=(); suites=(); name=""; create_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --patch) patches+=("$2"); shift 2 ;;
    --suite) suites+=("$2"); shift 2 ;;
    --name) name="$2"; shift 2 ;;
    --keep) shift ;;
    --with-modified) create_args+=(--with-modified); shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[[ ${#patches[@]} -gt 0 && ${#suites[@]} -gt 0 ]] || { echo "need at least one --patch and one --suite" >&2; exit 2; }
[[ -n "$name" ]] || { echo "need --name <name> (this session's isolated copy, e.g. i12)" >&2; exit 2; }
case "$name" in ""|.*|*/*) echo "invalid --name: $name" >&2; exit 2 ;; esac

root="$(git rev-parse --show-toplevel)"
cd "$root"
session_dir="$(bash "$iso_sh" session)" || exit 2
work="$session_dir/.verify-$name"

for p in "${patches[@]}"; do
  target="${p%%=*}"; patched="${p#*=}"
  case "$target" in /*|*..*) echo "--patch target must be a relative path inside the workspace: $target" >&2; exit 2 ;; esac
  [[ -f "$root/$target" && -f "$patched" ]] || { echo "missing file in --patch $p" >&2; exit 2; }
  require_inside "a --patch target" "$root/$target"
  require_inside "a --patched file" "$patched"
done
rm -rf "$work"; mkdir -p "$work"
require_inside "the scratch folder" "$work"

for p in "${patches[@]}"; do
  target="${p%%=*}"; patched="${p#*=}"
  patched_abs="$(cd "$(dirname "$patched")" && pwd)/$(basename "$patched")"
  echo "$target=$patched_abs" >> "$work/patches"
done

echo ">>> preparing the isolated copy and proving it matches the workspace"
if [[ -e "$session_dir/$name" ]]; then
  bash "$iso_sh" sync "$name"
else
  bash "$iso_sh" create "$name" ${create_args[@]+"${create_args[@]}"}
fi
run_dir="$(bash "$iso_sh" path "$name")"

mkdir -p "$work/orig"
while IFS='=' read -r target _; do
  mkdir -p "$work/orig/$(dirname "$target")"
  cp "$run_dir/$target" "$work/orig/$target"
done < "$work/patches"

restore() {
  while IFS='=' read -r target _; do
    [[ -f "$work/orig/$target" ]] && cp "$work/orig/$target" "$run_dir/$target"
  done < "$work/patches"
}
cleanup() {
  restore
  rm -rf "$work"
}
trap cleanup EXIT INT TERM

results() {
  local out="$1" i=0
  for s in "${suites[@]}"; do
    i=$((i + 1))
    # shellcheck disable=SC2086
    (cd "$run_dir" && forge test --match-path "$s" --json ${FORGE_ARGS:-} 2>/dev/null) > "$out.$i.json" || true
  done
  python3 -I - "$out".*.json <<'PY' | sort -u > "$out"
import json, sys
for f in sys.argv[1:]:
    try:
        data = json.load(open(f))
    except Exception:
        print(f"COMPILE-OR-RUN-ERROR {f}")
        continue
    for suite, v in data.items():
        for test, r in v.get("test_results", {}).items():
            reason = (r.get("reason") or "").replace("\n", " ")[:120]
            print(f"{suite} {test} {r['status']} {reason}".rstrip())
PY
}

echo ">>> running suites on the original code (in $run_dir)"
results "$work/before"
while IFS='=' read -r target patched; do cp "$patched" "$run_dir/$target"; done < "$work/patches"
echo ">>> running suites with the patch applied"
results "$work/after"

echo
echo "tests: before=$(wc -l < "$work/before" | tr -d ' ')  after=$(wc -l < "$work/after" | tr -d ' ')"
echo "failing before: $(grep -c ' Failure' "$work/before" || true)"
echo "=== results that changed (< original, > patched)"
diff "$work/before" "$work/after" || true
grep -h 'COMPILE-OR-RUN-ERROR' "$work/before" "$work/after" && echo "(a suite produced no results; check it compiles)" || true

restore
echo
echo "=== end-of-run check: isolated copy (patch removed) vs workspace"
if bash "$iso_sh" verify "$name"; then
  echo "the workspace did not change during the run"
else
  echo "WARNING: the workspace changed during the run (it matched at the start). The results above are"
  echo "for the code as it was at the start; re-run if the change is meant to be part of the baseline."
fi
