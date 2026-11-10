#!/usr/bin/env bash
# prefix-snapshot.sh — copy a contract as it was BEFORE a fix, renamed and with imports
# re-pointed, so a PoC can swap it in with `deployCodeTo` and reproduce the original bug.
#
# Usage: prefix-snapshot.sh <src-file> <fix-commit> <out-dir> <ID> [--no-check]
#   e.g. prefix-snapshot.sh src/Router.sol a1b2c3d test/mitigation H-1
#
# Produces <out-dir>/<Name>PreFix<Id>.sol where contract <Name> is renamed <Name>PreFix<Id> (<Id> is the
# finding ID with non-alphanumerics dropped, e.g. H-1 -> H1) and every relative import is rewritten
# relative to <out-dir>. The ID keeps snapshots from different findings, and from parallel sessions
# reviewing fixes to the same contract, from overwriting each other. The PoC must IMPORT this file so
# the artifact exists for `deployCodeTo("<Name>PreFix<Id>.sol:<Name>PreFix<Id>", args, address(target))`.
#
# The snapshot lands in the shared test folder, so it is compiled by every session's build. After
# writing it, the script compiles it; if the old code no longer compiles against today's dependencies,
# the file is removed again (use an isolated copy at <fix-commit>^ instead). --no-check skips this.
#
# Caveat: only valid when the pre-fix contract keeps the same storage layout and constructor as the
# deployed one (immutables are re-created from the constructor args). Diff it before relying on it.
set -euo pipefail

usage="usage: prefix-snapshot.sh <src-file> <fix-commit> <out-dir> <ID> [--no-check]"
src="${1:?$usage}"
commit="${2:?$usage}"
out="${3:?$usage}"
id="$(printf '%s' "${4:?$usage}" | tr -cd 'A-Za-z0-9')"
check=1
[[ "${5:-}" == "--no-check" ]] && check=0
[[ -n "$id" ]] || { echo "the finding ID must contain letters or digits" >&2; exit 2; }

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_workspace-guard.sh"
require_inside "the output folder" "$out"

name="$(basename "$src" .sol)"
pre="${name}PreFix${id}"
dest="$out/${pre}.sol"
if [[ -e "$dest" ]]; then
  echo "$dest already exists; remove it first if it is yours (another session may own it)" >&2
  exit 1
fi
mkdir -p "$out"

git show "$commit^:$src" > "$dest.tmp"

python3 -I - "$dest.tmp" "$dest" "$src" "$out" "$name" "$pre" <<'PY'
import os, re, sys
tmp, dest, src, out, name, pre = sys.argv[1:]
code = open(tmp).read()
src_dir = os.path.dirname(src)

def fix(m):
    path = m.group(2)
    if not path.startswith("."):
        return m.group(0)  # remapped import (lib/, @openzeppelin/...), leave it
    target = os.path.normpath(os.path.join(src_dir, path))
    rel = os.path.relpath(target, out)
    if not rel.startswith("."):
        rel = "./" + rel
    return f'{m.group(1)}"{rel}"'

code = re.sub(r'(import\s+(?:[^"\']*?\s+from\s+)?)"([^"]+)"', fix, code)
code = re.sub(rf'\b(contract|abstract contract)\s+{name}\b', rf'\1 {pre}', code, count=1)
open(dest, "w").write(code)
os.remove(tmp)
PY

if [[ $check -eq 1 ]] && command -v forge >/dev/null; then
  if ! forge build "$dest" >/dev/null 2>&1; then
    rm -f "$dest"
    echo "REMOVED $dest: the pre-fix code does not compile against the current tree, and a broken file in" >&2
    echo "the shared test folder breaks every session's build. Reproduce in an isolated copy at <fix-commit>^:" >&2
    echo "  isolated-workspace.sh create prefix-$id --ref $commit^" >&2
    exit 1
  fi
fi

echo "wrote $dest (contract ${pre}, from $commit^)"
echo "diff vs head:"
git diff --no-index --stat "$src" "$dest" || true
