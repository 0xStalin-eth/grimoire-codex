# _workspace-guard.sh — sourced by the other scripts in this folder.
#
# A script may only read and write inside the git workspace it is started from (`git rev-parse --show-toplevel`).
# Sibling workspaces of the same repo (other checkouts that share its git directory) count as outside, and so does
# any symlink that leads out of the workspace. Every path is resolved with symlinks followed before it is checked.

ws_root() { git rev-parse --show-toplevel; }

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
