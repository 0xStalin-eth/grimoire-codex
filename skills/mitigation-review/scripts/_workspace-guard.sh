# _workspace-guard.sh — sourced by the other scripts in this folder.
#
# A script may only read and write inside the git workspace it is started from (`git rev-parse --show-toplevel`).
# Sibling workspaces of the same repo (other checkouts that share its git directory) count as outside, and so does
# any symlink that leads out of the workspace. Every path is resolved with symlinks followed before it is checked.

# Git inspection must not refresh metadata outside a linked audit checkout.
export GIT_OPTIONAL_LOCKS=0

ws_root() {
  local repo_root
  repo_root="$(git rev-parse --show-toplevel)" || return 2
  python3 -I - "$repo_root" <<'ROOT_PY'
import os, sys
root = os.path.realpath(sys.argv[1])
launch = os.environ.get("GRIMOIRE_AUDIT_ROOT", "")
if not launch or not os.path.isabs(launch) or not os.path.isdir(launch):
    sys.exit("REFUSED: GRIMOIRE_AUDIT_ROOT must be the absolute Codex launch directory")
launch = os.path.realpath(launch)
if root != launch and not root.startswith(launch + os.sep):
    sys.exit(f"REFUSED: git root {root} is above or outside Codex launch directory {launch}")
import re, subprocess
remotes = subprocess.run(["git", "-C", root, "remote", "-v"], capture_output=True, text=True, check=True).stdout
if re.search(r"github\.com[:/]0xStalin-eth/grimoire(?:\.git)?(?:\s|$)", remotes, re.I):
    sys.exit("REFUSED: canonical Claude Grimoire is strictly read-only")
print(root)
ROOT_PY
}
# Refuse a broader root at source time, before the caller creates scratch/output files.
ws_root >/dev/null || return 2

_codex_artifact_tool="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/scripts/review_artifacts.py"
codex_artifacts() { python3 "$_codex_artifact_tool" "$@"; }
require_codex_output() { codex_artifacts guard-output "$@"; }

# require_inside <what> <path>... : exit 2 unless every path resolves inside the workspace
require_inside() {
  local what="$1"; shift
  python3 -I - "$(ws_root)" "$what" "$@" <<'PY'
import os, sys
root, what, paths = os.path.realpath(sys.argv[1]), sys.argv[2], sys.argv[3:]
bad = [f"{p} -> {os.path.realpath(p)}" for p in paths
       if not (os.path.realpath(p) == root or os.path.realpath(p).startswith(root + os.sep))]
if bad:
    sys.exit(f"refusing {what} outside the workspace {root}:\n  " + "\n  ".join(bad))
PY
}
