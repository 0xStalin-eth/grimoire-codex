---
name: findings-sync
description: >-
  This skill should be used when the user says "pull findings", "pull new findings", "pull issue <N>",
  "fetch the findings repo", "update finding <N>", "refresh findings", "sync findings", "which findings
  changed", "/findings-sync", or wants the local mirror of the engagement's findings repo brought up to
  date. Pulls issues that are not mirrored yet, and updates mirrored ones by first preserving the current
  copy (the original write-up is kept forever, every replaced version is kept in history) and then
  writing the newest version under the same file name. Not for reviewing findings (use /peer-review) or
  drafting them (use /finding-draft).
user_invocable: true
---

# Findings Sync

Keep a local, greppable mirror of the findings repo, without ever losing what a finding said before it
was edited.

## Philosophy

- **Pull and update are different operations.** Pulling only adds issues that aren't mirrored yet; it
  never touches an existing file. Updating always preserves the current copy first, then writes the
  newest version.
- **The original write-up is permanent.** The first version ever mirrored goes to `originals/` once and
  is never overwritten. Every version an update replaces goes to `history/`, stamped with its
  `updated` time.
- **File names are stable.** A file is named when the issue is first pulled and keeps that name on every
  update, even if the title changes, so notes, tomes and other skills that reference it stay valid.
- **One file per issue in the mirror root.** Preserved copies live in subfolders so that
  `<mirror>/issue<N>-*.md` always matches exactly one file (other skills rely on that).
- **Show before writing.** Run `status` first and confirm with the user what will be pulled or updated.
- **Only the mirror is touched.** The script reads and writes inside the mirror folder alone (its top
  level, `CLOSED/`, `originals/`, `history/`). The project's own findings (drafts, submissions, comments,
  rewrites) and tomes are never read or written: only the user or the skill that owns them changes them.
  The script refuses a `--mirror` that looks like the project's own findings folder.

## Mirror layout

```
<mirror>/
  issue<N>-<slug>.md                      latest version, open issues
  CLOSED/issue<N>-<slug>.md               latest version, closed issues (moved here when an issue closes)
  originals/issue<N>-<slug>.md            first version ever mirrored (written once)
  history/issue<N>-<slug>@<updated>.md    each version replaced by an update
```

Each file is YAML front matter (`title`, `source`, `author`, `labels`, `state`, `created`, `updated`, and
`closed` for closed issues), a blank line, the issue body verbatim, and, when the issue has comments, a
`---` separator, `## Comments`, and one `### <author> — <createdAt>` section per comment.

## Inputs

| Input | Where it comes from |
|---|---|
| Findings repo (`owner/repo`) | GRIMOIRE.md header, or ask once and record it there |
| Mirror directory | Default `grimoire/findings/original-repo-findings`; use the project's existing mirror if it differs |

Requires `gh`, authenticated with access to the findings repo (`gh auth status`). The script is
`scripts/findings_sync.py`; run it from the repo root.

---

## Workflow

Create a todo list from these steps.

```
- [ ] 1. Check access and inputs
- [ ] 2. Show what is new and what changed
- [ ] 3. Confirm the operation with the user          [confirm]
- [ ] 4. Pull and/or update
- [ ] 5. Report what changed and suggest follow-ups
```

### 1. Check access and inputs

```bash
gh auth status
python3 <skill>/scripts/findings_sync.py --repo <owner/repo> --mirror <mirror> status
```

If `status` warns that an issue has **more than one mirrored file**, a legacy copy is sitting in the
mirror root (for example a hand-made `issue<N>-original.md` / `issue<N>-latest.md` pair). Resolve it
before updating; see *Legacy copies* below.

### 2. Show what is new and what changed

`status` prints two lists: issues upstream that aren't mirrored (**pull**), and mirrored issues whose
`updated` time differs upstream (**update**). For the update list, a dry run shows the size of each
change without writing anything:

```bash
python3 <skill>/scripts/findings_sync.py --repo <owner/repo> --dry-run update --all
```

Each issue prints `changes: body +<added>/-<removed> lines, <±n> comments, state <STATE>`. Point out
large body rewrites, state changes (OPEN → CLOSED) and new comments.

### 3. Confirm **[confirm]**

Ask which to run: pull the new ones (all, or specific numbers), update the changed ones (all, or
specific numbers), or both. Updating is safe (nothing is lost), but it changes the files other notes
point at, so the user decides.

### 4. Pull and/or update

```bash
# new issues only; existing files are never touched
python3 <skill>/scripts/findings_sync.py --repo <owner/repo> --mirror <mirror> pull 102 103
python3 <skill>/scripts/findings_sync.py --repo <owner/repo> --mirror <mirror> pull --new

# preserve, then refresh
python3 <skill>/scripts/findings_sync.py --repo <owner/repo> --mirror <mirror> update 7 15
python3 <skill>/scripts/findings_sync.py --repo <owner/repo> --mirror <mirror> update --all
```

`pull` skips issues that are already mirrored (and says to use `update`). `update` skips issues that
aren't mirrored (and says to use `pull`), and reports "up to date" when nothing changed upstream.
Running either twice is harmless.

### 5. Report and suggest follow-ups

Summarize: issues pulled, issues updated (with their change sizes), issues that moved to `CLOSED/`, and
titles that changed upstream (the file kept its name). Then suggest:
- **Re-review** updated issues that already have a peer-review verdict, session marker or tome entry:
  `grep -rl "#<N>\b" grimoire/` finds them. A large body change can change the verdict (`/peer-review`).
- **Diff against the original** when the user wants to see how a finding evolved:
  `diff <mirror>/originals/issue<N>-*.md <mirror>/issue<N>-*.md`.
- **Update the duplicates index** (if the project keeps one) for newly pulled issues.
- **Move submitted drafts.** For each newly pulled issue, look for a local draft in
  `grimoire/findings/WIP/` with the same title (or a front-matter line naming the issue). If one
  matches, the draft was submitted: ask the user to confirm, then apply the "Finding submitted" rule in
  `/summon` Step 2 (move it to `findings/valid/`, update links and logs, record the issue number).

## Legacy copies

Mirrors created by hand may hold preserved versions in the root (`issue<N>-original.md`,
`issue<N>-latest.md`, `issue<N>-v1.md`). They break the one-file-per-issue rule. With the user's
confirmation:
1. move the oldest copy to `originals/issue<N>-<slug>.md` (keep it byte for byte, even if its format
   differs from the script's);
2. move any intermediate copies to `history/issue<N>-<slug>@<their updated time>.md`;
3. remove the remaining root copies and run `update <N>` to write the newest version under
   `issue<N>-<slug>.md`, using the slug of the first mirrored file if one exists.

## Conventions

- **Never edit mirrored files by hand.** They are overwritten on update. Put notes, rewrites and
  comments in the project's own folders (comments, drafts, submissions).
- **Never edit `originals/` or `history/`.** They are the audit trail of what each finding said.
- **Slugs** are the title in lowercase, every run of non-alphanumeric characters replaced by `-`, cut to
  80 characters, with trailing `-` removed.
