#!/usr/bin/env bash
# extract-poc.sh — extract the Solidity PoC embedded in a finding and re-root its relative imports so it
# compiles from a new location.
#
# The PoC's original location is read from the finding's run command ("forge test --match-path <path>"),
# or given with --src-dir. Every relative import ("./x", "../x") is resolved against that original
# directory and rewritten relative to the destination directory.
#
# Usage: extract-poc.sh <finding.md> <dest.t.sol> [--src-dir <dir>] [--block <n>]
#   --src-dir  directory the PoC was written for (repo-relative), e.g. test/pocs
#   --block    which ```solidity block to extract when there are several (1-based, default 1)
# Run from the repository root.
set -euo pipefail

finding="${1:?usage: extract-poc.sh <finding.md> <dest.t.sol> [--src-dir <dir>] [--block <n>]}"
dest="${2:?usage: extract-poc.sh <finding.md> <dest.t.sol> [--src-dir <dir>] [--block <n>]}"
shift 2
src_dir=""
block=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --src-dir) src_dir="$2"; shift 2 ;;
    --block)   block="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_workspace-guard.sh"
require_inside "the finding file" "$finding"
require_inside "the destination" "$dest"
[[ -z "$src_dir" ]] || require_inside "--src-dir" "$src_dir"

python3 - "$finding" "$dest" "$src_dir" "$block" <<'PY'
import os, re, sys
finding, dest, src_dir, block = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
text = open(finding).read()
blocks = re.findall(r"```solidity\n(.*?)```", text, re.S)
if not blocks:
    sys.exit(f"no ```solidity block in {finding}")
if block > len(blocks):
    sys.exit(f"{finding} has {len(blocks)} solidity block(s); --block {block} is out of range")
code = blocks[block - 1]

if not src_dir:
    m = re.search(r"--match-path\s+['\"]?([^\s'\"]+\.t\.sol)", text)
    if not m:
        sys.exit("could not find the PoC's original path in a 'forge test --match-path' command; pass --src-dir")
    src_dir = os.path.dirname(m.group(1))

dest_dir = os.path.dirname(dest) or "."

def reroot(match):
    quote, path = match.group(1), match.group(2)
    if not path.startswith("."):
        return match.group(0)            # remappings / library imports stay as they are
    target = os.path.normpath(os.path.join(src_dir, path))
    new = os.path.relpath(target, dest_dir)
    if not new.startswith("."):
        new = "./" + new
    return f"{quote}{new}{quote}"

code = re.sub(r"""(["'])(\.{1,2}/[^"']+)\1""", reroot, code)
os.makedirs(dest_dir, exist_ok=True)
if os.path.exists(dest):
    sys.exit(f"{dest} already exists; refusing to overwrite")
open(dest, "w").write(code)
print(f"wrote {dest} (block {block}/{len(blocks)}, imports re-rooted from {src_dir} to {dest_dir})")
PY
