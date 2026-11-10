#!/usr/bin/env bash
# isolated-workspace.sh — a private copy of the workspace for patching and testing, proven byte-for-byte identical.
#
# Everything stays INSIDE the git workspace this runs from. Nothing is read from or written to any other workspace,
# sibling checkouts of the same repo included: dependency links and symlinks that lead outside are refused, and no
# write may leave the copy. The copy lives in <workspace>/.isolated/<name>/, which a `.gitignore` of `*` keeps out of
# `git status` and out of other sessions' copies. Nothing is written above the workspace root (no system temp dir,
# no `git worktree` metadata in the shared git dir); git is only read.
#
# Every copy belongs to ONE session. Copies and work folders live under <workspace>/.isolated/<session-id>/, where the
# session id is $CLAUDE_CODE_SESSION_ID (kept by `claude --resume`; `--fork-session` starts a new id). Names resolve
# only inside the current session's folder, so a session cannot name, sync or remove another session's copy, and the
# script refuses to run at all without a session id. `remove` additionally checks the folder's .owner file. Copies are
# kept until the user closes the lead they serve; nothing here removes a copy on its own.
#
# The copy holds every tracked and untracked, non-ignored file of the workspace; dependency folders (lib,
# node_modules) are symlinks to the workspace's own. After every create and sync, `verify` compares the two byte for
# byte (sha256 of every file, plus the symlink targets) and exits 1 on any difference.
#
# Uncommitted edits to TRACKED files in the workspace may be your own intended changes or another session's
# temporary patch. The script never guesses: create/sync refuse and list them. Pass --with-modified only after
# confirming they are code you want to test against.
#
# Usage (run from inside the workspace):
#   isolated-workspace.sh create <name> [--with-modified] [--ref <commit>] [--link <path>]...
#   isolated-workspace.sh sync   <name>     # mirror the workspace again (DISCARDS edits made in the copy), verify
#   isolated-workspace.sh verify <name> [--except <path>]...
#   isolated-workspace.sh path   <name>     # print the copy's absolute path
#   isolated-workspace.sh remove <name>     # only when the user has closed the lead (accepted or discarded)
#   isolated-workspace.sh work   <name>     # create and print this session's work folder for <name> (a/, b/, diffs)
#   isolated-workspace.sh session           # print this session's folder
#   isolated-workspace.sh list              # read-only: every session folder, its copies, age and size
#
#   --with-modified  accept uncommitted edits to tracked files and copy them as they are
#   --ref            build the copy from another commit (mitigation reviews); the comparison is skipped and says so
#   --link           folder to symlink to the workspace's own (default: lib and node_modules, when present)
#   --except         path to leave out of the comparison (e.g. a file you patched on purpose)
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
exec python3 -I - "$root" "$@" <<'PY'
import hashlib, os, shutil, subprocess, sys, json

import re, time
root, args = os.path.realpath(sys.argv[1]), sys.argv[2:]
USAGE = "usage: isolated-workspace.sh create|sync|verify|path|remove|work <name> [options] | session | list"
if not args:
    sys.exit(USAGE)
base = os.path.join(root, ".isolated")
STATE = ".isolated-state.json"
OWNER = ".owner"

sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{7,63}", sid):
    sys.exit("REFUSED: no session id ($CLAUDE_CODE_SESSION_ID is unset or malformed). Isolated copies are per session;"
             " run this from the Claude Code session that owns the copy.")
sbase = os.path.join(base, sid)

def human(n):
    for u in ("B", "K", "M", "G"):
        if n < 1024: return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.0f}T"

def tree_size(path):
    total = 0
    for d, dirs, files in os.walk(path):
        dirs[:] = [x for x in dirs if not os.path.islink(os.path.join(d, x))]
        for f in files:
            fp = os.path.join(d, f)
            if not os.path.islink(fp):
                try: total += os.path.getsize(fp)
                except OSError: pass
    return total

if args[0] == "list":
    if not os.path.isdir(base):
        sys.exit(print("no isolated copies in this workspace") or 0)
    for entry in sorted(os.listdir(base)):
        d = os.path.join(base, entry)
        if entry.startswith(".") or not os.path.isdir(d) or os.path.islink(d):
            continue
        owner_file = os.path.join(d, OWNER)
        if os.path.exists(owner_file):
            try: o = json.load(open(owner_file))
            except Exception: o = {}
            tag = " (THIS SESSION)" if entry == sid else ""
            print(f"session {entry}{tag}  created {o.get('created', '?')}")
            for c in sorted(os.listdir(d)):
                cp = os.path.join(d, c)
                if c.startswith(".") or not os.path.isdir(cp): continue
                age = (time.time() - os.path.getmtime(cp)) / 86400
                kind = "work folders" if c == "work" else "copy"
                print(f"  {c:<24} {kind:<12} {human(tree_size(cp)):>6}  modified {age:.1f}d ago")
        else:
            kind = "legacy copy, no owner" if os.path.exists(os.path.join(d, STATE)) else "folder, no owner"
            print(f"{entry}  ({kind}; created before per-session folders, never touched by this script)")
    sys.exit(0)

if args[0] == "session":
    print(sbase)
    sys.exit(0)

if len(args) < 2:
    sys.exit(USAGE)
cmd, name, rest = args[0], args[1], args[2:]
if not name or "/" in name or name.startswith(".") or name == "work" or ".." in name:
    sys.exit(f"invalid name {name!r}: use a plain folder name, e.g. i68 ('work' is reserved for patched copies)")
iso = os.path.join(sbase, name)

def check_owner(create=False):
    """The session folder must be ours: its .owner names this session id."""
    if os.path.islink(base) or os.path.islink(sbase):
        sys.exit(f"REFUSED: {base} or {sbase} is a symlink")
    owner_file = os.path.join(sbase, OWNER)
    if not os.path.exists(owner_file):
        if not create:
            sys.exit(f"REFUSED: {sbase} has no {OWNER} file; nothing here belongs to session {sid}")
        os.makedirs(sbase, exist_ok=True)
        with open(owner_file, "w") as f:
            json.dump({"session": sid, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "workspace": root}, f)
        return
    try: o = json.load(open(owner_file))
    except Exception: sys.exit(f"REFUSED: {owner_file} is unreadable")
    if o.get("session") != sid:
        sys.exit(f"REFUSED: {sbase} is owned by session {o.get('session')!r}, not {sid}")

def inside(path):
    p = os.path.realpath(path)
    return p == root or p.startswith(root + os.sep)
if os.path.islink(iso):
    if cmd == "remove":
        os.remove(iso)                    # drop the link itself, never what it points to
        print(f"removed the link {iso} (its target was not touched)")
        sys.exit(0)
    sys.exit(f"REFUSED: {iso} is a symlink to {os.path.realpath(iso)}; remove it first")
if not inside(iso) or os.path.realpath(iso) == root:
    sys.exit(f"REFUSED: {iso} resolves to {os.path.realpath(iso)}, outside the workspace (is .isolated a symlink?)")
if os.path.dirname(os.path.realpath(iso)) != os.path.realpath(sbase) and os.path.exists(sbase):
    sys.exit(f"REFUSED: {iso} does not resolve to a folder directly inside this session's {sbase}")

opts = {"links": [], "excepts": [], "with_modified": False, "ref": "HEAD"}
i = 0
while i < len(rest):
    a = rest[i]
    if a == "--with-modified": opts["with_modified"] = True; i += 1
    elif a in ("--ref", "--link", "--except") and i + 1 < len(rest):
        if a == "--ref": opts["ref"] = rest[i + 1]
        elif a == "--link": opts["links"].append(rest[i + 1].strip("/"))
        else: opts["excepts"].append(rest[i + 1].strip("/"))
        i += 2
    else: sys.exit(f"unknown argument: {a}")

def outside(path):
    """True when path, with symlinks followed, leads out of the workspace (e.g. into a sibling workspace)."""
    return not inside(path)

def check_boundaries(links, files):
    """Refuse dependency links or workspace symlinks that lead outside the workspace."""
    bad = [f"  dependency folder {l} -> {os.path.realpath(os.path.join(root, l))}" for l in links
           if outside(os.path.join(root, l))]
    bad += [f"  symlink {p} -> {os.path.realpath(os.path.join(root, p))}" for p in files
            if os.path.islink(os.path.join(root, p)) and outside(os.path.join(root, p))]
    if bad:
        sys.exit("REFUSED: these lead outside the workspace (another workspace or folder):\n" + "\n".join(bad))

def git(*a, inp=None):
    return subprocess.run(["git", "-C", root, *a], input=inp, capture_output=True, check=True).stdout

def under(p, prefixes):
    return any(p == x or p.startswith(x + "/") for x in prefixes)

def load_state():
    with open(os.path.join(iso, STATE)) as f:
        return json.load(f)

def workspace_files(links):
    out = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted({p.decode() for p in out.split(b"\0") if p and not under(p.decode(), links + [".isolated"])})

def copy_files(files):
    for p in files:
        src, dst = os.path.join(root, p), os.path.join(iso, p)
        if os.path.isdir(src) and not os.path.islink(src):
            continue                      # submodule outside the linked folders; reported by verify
        if not os.path.lexists(src):
            continue                      # deleted in the workspace
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.realpath(os.path.dirname(dst)).startswith(os.path.realpath(iso) + os.sep) \
                and os.path.realpath(os.path.dirname(dst)) != os.path.realpath(iso):
            sys.exit(f"REFUSED: writing {p} would leave the isolated copy")
        if os.path.lexists(dst) or os.path.islink(dst):
            os.remove(dst)
        shutil.copy2(src, dst, follow_symlinks=False)

def modified():
    return [l for l in git("status", "--porcelain", "--untracked-files=no").decode().splitlines()
            if not under(l[3:].strip(), [".isolated"])]

def iso_files(links, excepts):
    found = []
    for d, dirs, files in os.walk(iso):
        rel_d = os.path.relpath(d, iso)
        rel_d = "" if rel_d == "." else rel_d + "/"
        dirs[:] = [x for x in dirs if not os.path.islink(os.path.join(d, x))]
        found += [rel_d + f for f in files]
        found += [rel_d + x for x in os.listdir(d) if os.path.islink(os.path.join(d, x)) and os.path.isdir(os.path.join(d, x))]
    found = [p for p in found if p != STATE and not under(p, links)]
    if found:   # drop what the workspace's ignore rules ignore (build output, caches)
        ign = subprocess.run(["git", "-C", root, "check-ignore", "--no-index", "-z", "--stdin"],
                             input="\0".join(found).encode() + b"\0", capture_output=True).stdout
        ignored = {p.decode() for p in ign.split(b"\0") if p}
        found = [p for p in found if p not in ignored]
    return set(found)

def digest(path):
    if os.path.islink(path):
        return "link:" + os.readlink(path)
    if os.path.isdir(path):
        return "dir"
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def verify(links, excepts):
    problems, submodules, compared = [], [], 0
    for p in sorted(set(workspace_files(links)) | iso_files(links, excepts)):
        if under(p, excepts):
            continue
        a, b = digest(os.path.join(root, p)), digest(os.path.join(iso, p))
        if a == "dir" or b == "dir":
            submodules.append(p); continue
        compared += 1
        if a != b:
            why = "missing in the copy" if b is None else "missing in the workspace" if a is None else "content differs"
            problems.append(f"  {why}: {p}")
    for l in links:
        w = os.path.join(iso, l)
        if not (os.path.islink(w) and os.path.realpath(w) == os.path.realpath(os.path.join(root, l))):
            problems.append(f"  not linked to the workspace folder: {l}")
    print(f"compared {compared} files byte for byte; linked: {', '.join(links) or 'none'}"
          + (f"; excluded: {', '.join(excepts)}" if excepts else ""))
    for s in submodules:
        print(f"  NOT compared (submodule outside the linked folders): {s}")
    if problems:
        print("DIFFERENT from the workspace:\n" + "\n".join(problems))
        return False
    print("IDENTICAL to the workspace")
    return True

def refuse_if_modified(with_modified):
    mods = modified()
    if mods and not with_modified:
        print("REFUSED: tracked files have uncommitted changes in the workspace:", file=sys.stderr)
        print("\n".join("  " + m for m in mods), file=sys.stderr)
        print("If they are code you want to test against, re-run with --with-modified.\n"
              "If they are another session's temporary patch, wait until the workspace is back at HEAD.", file=sys.stderr)
        sys.exit(1)

def ensure_base():
    os.makedirs(base, exist_ok=True)
    gi = os.path.join(base, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w") as f:
            f.write("*\n")
    check_owner(create=True)

def make_links(links):
    for l in links:
        dst = os.path.join(iso, l)
        if os.path.islink(dst) or os.path.isfile(dst): os.remove(dst)
        elif os.path.isdir(dst): shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.symlink(os.path.join(root, l), dst)

if cmd != "create" and cmd != "work":
    check_owner()

if cmd == "create":
    if os.path.lexists(iso):
        sys.exit(f"{iso} already exists; remove it first or use sync")
    links = opts["links"] or [d for d in ("lib", "node_modules") if os.path.exists(os.path.join(root, d))]
    head = git("rev-parse", "HEAD").decode().strip()
    ref = git("rev-parse", opts["ref"] + "^{commit}").decode().strip()
    ensure_base()
    if ref != head:
        check_boundaries(links, [])
        os.makedirs(iso)
        tar = subprocess.run(["git", "-C", root, "archive", "--format=tar", ref], capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", iso], input=tar, check=True)
        others = git("ls-files", "-z", "--others", "--exclude-standard")
        copy_files([p.decode() for p in others.split(b"\0") if p and not under(p.decode(), links + [".isolated"])])
    else:
        refuse_if_modified(opts["with_modified"])
        check_boundaries(links, workspace_files(links))
        os.makedirs(iso)
        copy_files(workspace_files(links))
    make_links(links)
    with open(os.path.join(iso, STATE), "w") as f:
        json.dump({"links": links, "with_modified": opts["with_modified"], "ref": ref}, f)
    print(f"isolated copy at {iso} ({ref[:7]}); linked: {', '.join(links) or 'none'}")
    if ref != head:
        print(f"NOT compared: --ref {opts['ref']} is not the workspace's HEAD, so the code differs on purpose")
    elif not verify(links, []):
        shutil.rmtree(iso)
        sys.exit("removed the copy because it does not match the workspace")
    print("first build compiles from scratch, so expect it to be slower")

elif cmd == "sync":
    st = load_state()
    links = st["links"]
    head = git("rev-parse", "HEAD").decode().strip()
    if st["ref"] != head:
        others = git("ls-files", "-z", "--others", "--exclude-standard")
        copy_files([p.decode() for p in others.split(b"\0") if p and not under(p.decode(), links + [".isolated"])])
        print(f"synced untracked files; NOT compared (copy built from {st['ref'][:7]}, workspace HEAD is {head[:7]})")
        sys.exit(0)
    refuse_if_modified(st["with_modified"])
    want = workspace_files(links)
    check_boundaries(links, want)
    for p in sorted(iso_files(links, []) - set(want)):
        os.remove(os.path.join(iso, p))
    copy_files(want)
    make_links(links)
    print(f"synced {iso}")
    sys.exit(0 if verify(links, []) else 1)

elif cmd == "verify":
    links = load_state()["links"] if os.path.exists(os.path.join(iso, STATE)) else \
        [d for d in ("lib", "node_modules") if os.path.exists(os.path.join(root, d))]
    sys.exit(0 if verify(links, opts["excepts"]) else 1)

elif cmd == "path":
    print(iso)

elif cmd == "remove":
    if not os.path.lexists(iso):
        sys.exit(f"nothing to remove: {iso} does not exist")
    if not os.path.exists(os.path.join(iso, STATE)):
        sys.exit(f"REFUSED: {iso} has no {STATE}; it is not an isolated copy made by this script")
    shutil.rmtree(iso)
    print(f"removed {iso} (session {sid})")

elif cmd == "work":
    ensure_base()
    w = os.path.join(sbase, "work", name)
    os.makedirs(w, exist_ok=True)
    print(w)

else:
    sys.exit(f"unknown command: {cmd}")
PY
