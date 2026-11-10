#!/usr/bin/env python3
"""findings_sync.py — mirror a findings repo's issues as local markdown files, preserving earlier versions.

Mirror layout (one file per issue, closed issues in CLOSED/):

    <mirror>/issue<N>-<slug>.md          latest version of an open issue
    <mirror>/CLOSED/issue<N>-<slug>.md   latest version of a closed issue
    <mirror>/originals/issue<N>-<slug>.md          the first version ever mirrored (written once, never overwritten)
    <mirror>/history/issue<N>-<slug>@<updated>.md  every version replaced by an update

The file name is fixed when an issue is first pulled and kept on later updates, even if the title changes,
so references to it stay valid. Preserved copies live in subfolders so that `<mirror>/issue<N>-*.md` always
matches exactly one file.

Commands:
    status                     list mirrored issues that are new upstream or changed since the last pull
    pull   <N> [<N> ...]       mirror issues not yet in the mirror (refuses existing ones; use update)
    pull   --new               mirror every upstream issue not yet in the mirror
    update <N> [<N> ...]       preserve the current copy, then replace it with the newest version
    update --all               the same for every mirrored issue that changed upstream

Options:  --repo <owner/repo>  (required)   --mirror <dir>  (default: grimoire/findings/original-repo-findings)
          --dry-run            print what would happen without writing anything
Requires: gh (authenticated).
"""
import argparse, difflib, glob, json, os, re, shutil, subprocess, sys

FIELDS = "number,title,body,author,labels,state,createdAt,updatedAt,closedAt,comments,url"
SLUG_MAX = 80


def gh_json(args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed:\n{out.stderr.strip()}")
    return json.loads(out.stdout)


def fetch(repo, n):
    return gh_json(["issue", "view", str(n), "--repo", repo, "--json", FIELDS])


def list_upstream(repo):
    return gh_json(["issue", "list", "--repo", repo, "--state", "all", "--limit", "1000",
                    "--json", "number,title,state,updatedAt"])


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:SLUG_MAX].rstrip("-")


def render(issue):
    """Front matter + verbatim body + comments, in the mirror's format."""
    title = issue["title"].replace("\\", "\\\\").replace('"', '\\"')
    labels = ", ".join(l["name"] for l in issue.get("labels", []))
    author = (issue.get("author") or {}).get("login", "")
    lines = [
        "---",
        f'title: "{title}"',
        f"source: {issue['url']}",
        f"author: {author}",
        f"labels: [{labels}]",
        f"state: {issue['state']}",
        f"created: {issue['createdAt']}",
        f"updated: {issue['updatedAt']}",
    ]
    if issue["state"] == "CLOSED" and issue.get("closedAt"):
        lines.append(f"closed: {issue['closedAt']}")
    lines += [
        "---",
        "",
        (issue.get("body") or "").replace("\r\n", "\n").rstrip("\n"),
    ]
    comments = issue.get("comments") or []
    if comments:
        lines += ["", "---", "", "## Comments"]
        for c in comments:
            who = (c.get("author") or {}).get("login", "")
            lines += ["", f"### {who} — {c['createdAt']}", "", (c.get("body") or "").replace("\r\n", "\n").rstrip("\n")]
    return "\n".join(lines) + "\n"


def front(path):
    """updated timestamp and comment count of a mirrored file."""
    text = open(path).read()
    m = re.search(r"^updated: (\S+)$", text, re.M)
    return (m.group(1) if m else None), len(re.findall(r"^### .+ — \S+$", text, re.M))


def mirrored(mirror):
    """{N: path} for every mirrored issue (open or CLOSED), ignoring preserved copies."""
    found = {}
    for d in (mirror, os.path.join(mirror, "CLOSED")):
        for p in glob.glob(os.path.join(d, "issue*-*.md")):
            m = re.match(r"issue(\d+)-", os.path.basename(p))
            if not m:
                continue
            n = int(m.group(1))
            if n in found:
                print(f"warning: #{n} has more than one mirrored file ({found[n]}, {p}); using the first", file=sys.stderr)
                continue
            found[n] = p
    return found


def target_path(mirror, name, state):
    return os.path.join(mirror, "CLOSED", name) if state == "CLOSED" else os.path.join(mirror, name)


def write(path, text, dry):
    print(f"  write {path}")
    if not dry:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)


def copy(src, dst, dry):
    print(f"  preserve {src} -> {dst}")
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def cmd_status(args):
    have = mirrored(args.mirror)
    new, changed = [], []
    for it in list_upstream(args.repo):
        n = it["number"]
        if n not in have:
            new.append(n)
        elif front(have[n])[0] != it["updatedAt"]:
            changed.append(n)
    print("new upstream (pull):   ", " ".join(f"#{n}" for n in sorted(new)) or "none")
    print("changed upstream (update):", " ".join(f"#{n}" for n in sorted(changed)) or "none")


def cmd_pull(args):
    have = mirrored(args.mirror)
    if args.new:
        nums = sorted(it["number"] for it in list_upstream(args.repo) if it["number"] not in have)
    else:
        nums = args.numbers
    if not nums:
        print("nothing to pull")
    for n in nums:
        if n in have:
            print(f"#{n}: already mirrored at {have[n]}; skipped (use update to refresh it)")
            continue
        issue = fetch(args.repo, n)
        print(f"#{n}: pulled ({issue['state']}, updated {issue['updatedAt']})")
        write(target_path(args.mirror, f"issue{n}-{slug(issue['title'])}.md", issue["state"]), render(issue), args.dry_run)


def cmd_update(args):
    have = mirrored(args.mirror)
    if args.all:
        upstream = {it["number"]: it for it in list_upstream(args.repo)}
        nums = sorted(n for n in have if n in upstream and front(have[n])[0] != upstream[n]["updatedAt"])
    else:
        nums = args.numbers
    if not nums:
        print("everything is up to date")
    for n in nums:
        if n not in have:
            print(f"#{n}: not mirrored yet; skipped (use pull)")
            continue
        current = have[n]
        issue = fetch(args.repo, n)
        local_updated, local_comments = front(current)
        if local_updated == issue["updatedAt"] and local_comments == len(issue.get("comments") or []):
            print(f"#{n}: up to date ({local_updated})")
            continue
        name = os.path.basename(current)
        print(f"#{n}: {local_updated} -> {issue['updatedAt']}")
        original = os.path.join(args.mirror, "originals", name)
        if not os.path.exists(original):
            copy(current, original, args.dry_run)
        stamp = (local_updated or "unknown").replace(":", "")
        copy(current, os.path.join(args.mirror, "history", name[:-3] + f"@{stamp}.md"), args.dry_run)
        new_text = render(issue)
        old_text = open(current).read()
        old_body, new_body = old_text.split("\n## Comments\n")[0], new_text.split("\n## Comments\n")[0]
        diff = [l for l in difflib.unified_diff(old_body.splitlines(), new_body.splitlines(), lineterm="", n=0)
                if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        added = sum(1 for l in diff if l.startswith("+")); removed = len(diff) - added
        new_comments = len(issue.get("comments") or []) - local_comments
        print(f"  changes: body +{added}/-{removed} lines, {new_comments:+d} comments, state {issue['state']}")
        dest = target_path(args.mirror, name, issue["state"])
        if dest != current:
            print(f"  state changed: moving {current} -> {dest}")
            if not args.dry_run:
                os.remove(current)
        write(dest, new_text, args.dry_run)
        if slug(issue["title"]) != name[len(f"issue{n}-"):-3]:
            print(f"  note: the title changed upstream; the file keeps its original name ({name})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--mirror", default="grimoire/findings/original-repo-findings")
    ap.add_argument("--dry-run", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p = sub.add_parser("pull")
    p.add_argument("numbers", nargs="*", type=int)
    p.add_argument("--new", action="store_true")
    u = sub.add_parser("update")
    u.add_argument("numbers", nargs="*", type=int)
    u.add_argument("--all", action="store_true")
    args = ap.parse_args()
    # Only the mirror is ever written. Refuse a mirror that holds the user's own findings work.
    own = [d for d in ("Submitted", "comments", "drafts") if os.path.isdir(os.path.join(args.mirror, d))]
    if own or os.path.basename(os.path.normpath(args.mirror)) == "findings":
        ap.error(f"--mirror {args.mirror} looks like the project's own findings folder ({', '.join(own) or 'findings/'}); "
                 "point it at the dedicated mirror folder, e.g. grimoire/findings/original-repo-findings")
    if args.cmd == "pull" and not (args.numbers or args.new):
        ap.error("pull needs issue numbers or --new")
    if args.cmd == "update" and not (args.numbers or args.all):
        ap.error("update needs issue numbers or --all")
    {"status": cmd_status, "pull": cmd_pull, "update": cmd_update}[args.cmd](args)


if __name__ == "__main__":
    main()
