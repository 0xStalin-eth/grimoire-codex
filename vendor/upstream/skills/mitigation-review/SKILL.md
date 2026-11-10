---
name: mitigation-review
description: >-
  This skill should be used when the user says "mitigation review", "review the mitigation",
  "review the fix", "verify the fix", "fix review", "check the remediation", "/mitigation-review",
  or shares a finding (ID, title, or issue URL) and asks whether the client's fix resolves it.
  Maps an audit report to the client's fix commits and findings-repo issues, reviews each fix
  against its finding and thread, verifies it with pre-fix / post-fix / residual PoCs, records a
  verdict, and drafts the short "Cyfrin:" write-up for the report. Not for finding new bugs in
  unchanged code (use sigils / cartography) or drafting new findings (use /finding-draft).
user_invocable: true
---

# Mitigation Review

Judge whether each client fix closes its finding, prove it with PoCs, and produce a short write-up
for the report's `**Cyfrin:**` field.

## Philosophy

- **The fix is guilty until a PoC says otherwise.** Reading the diff is not verification. Every fix that
  changes behaviour gets a test that reproduces the bug before the fix and passes after it. Only renames
  and docs-only changes skip PoCs, and the review says so.
- **The thread binds the verdict.** Agreements reached in the issue thread (accepted behaviour,
  severity, design limits) are context, not something to re-litigate.
- **Realism before severity.** Before raising a residual, ask who triggers it, what they control, and
  how many uncontrollable events it needs. Unrealistic residuals become footnotes, not findings.
- **Short and plain.** Write-ups are 1–3 sentences in simple words. Detail lives in the review file.
  Never use one-letter placeholders for a quantity, a time or any other value (`T`, `t`, `X`, `x`),
  even after defining them once: write the contract's name (`effectiveAt`) or a plain phrase.
- **Don't touch `src/`.** PoCs go in `test/mitigation/`. Pre-fix code is swapped in at test time.

## Inputs

| Input | Example | Where it's stored |
|---|---|---|
| Report | `2026-09-17-cyfrin-<client>-v0.0.md`, inside this workspace (copy it in if it lives in another checkout; the scripts refuse paths outside) | GRIMOIRE.md header |
| Findings repo | `Cyfrin/audit-2026-09-<client>` | GRIMOIRE.md header |
| Baseline (audited) commit | `37f06bb` | GRIMOIRE.md header |
| Mitigation commit | `be70792` | GRIMOIRE.md header |
| In-scope paths | `src/vault-v2 src/risk-engines` | GRIMOIRE.md Scope |
| Client name + git remote of the client's own external repo (not the Cyfrin audit repo) | `Acme`, remote `client` | GRIMOIRE.md header |

If GRIMOIRE.md doesn't exist, run `/summon` first. If any input is missing from GRIMOIRE.md, ask
once, then record it there.

Scripts live in this skill's `scripts/` directory (`$S` below) and in the peer-review skill's
`scripts/` directory (`$P` below: `isolated-workspace.sh`, `verify-fix.sh`). Both are Grimoire paths, not
paths inside the reviewed repo; run every script from the repo root.

---

## Phase A — Setup (once per engagement; skip steps already done)

```
- [ ] A1. Confirm inputs, record them in GRIMOIRE.md, and fresh-pull the findings mirror
- [ ] A2. Build the findings → issue → fix index
- [ ] A3. Add the status table to GRIMOIRE.md
```

### A1. Confirm inputs

Run the review from the checkout that has the fix commits (often a separate checkout used only for
fixes). The scripts are confined to the workspace they start in: its HEAD, its files, and this
session's `.isolated/<session-id>/` copies. Every other checkout of the repo, including the one used for the audit itself, is
off limits. So the report and GRIMOIRE.md must be in this checkout too. Copy them in, or run
`/summon` here.

Check `git log -1 <mitigation-commit>` and `git log -1 <baseline>` resolve, `gh auth status` works,
and the report file exists. Note fork-test env vars the repo uses (`grep -r "vm.envString\|rpc_endpoints" test foundry.toml`).

**Findings mirror: always a fresh pull.** Peer review and mitigation review happen in different
workspaces, and each one keeps its own mirror. Never copy the mirror from the audit or peer-review
checkout. If this checkout has no `grimoire/` tree yet, create it first with the layout from
`/summon` Step 2 (never overwriting existing folders or files). Then pull with `/findings-sync` into
this checkout's `grimoire/findings/original-findings`
(`findings_sync.py --repo <owner/repo> --mirror grimoire/findings/original-findings pull --new`). If
this checkout already has a mirror, run `status` and `pull --new` for any issues it is missing.

### A2. Build the index

```bash
$S/index-report.sh   <report>                       # ID, line, title (IDs derived per severity section)
$S/link-issues.sh    <report> <owner/repo>          # ID → issue # by title
$S/map-fixes.sh      <baseline> <head> <scope...>   # PR → issue refs, commits, files ([*] in scope)
```

Join the three into `grimoire/tomes/findings-index.md`:

| ID | Report line | Finding (short) | Issue # | PR / commits | Mitigation type |

PRs without issue references (e.g. `fix/<client>-adapters`) are mapped by content: compare the diff
to the finding's recommendation. Mark findings with no matching PR `none found` and list them at the
bottom as "confirm with the client whether acknowledged". Also flag PRs in the range that map to no
finding: they are unreviewed changes, so skim them for regressions.

### A3. Status table

Add a `### Finding → mitigation status` table to GRIMOIRE.md (`| Finding | PR | Verdict |`, all
`pending`) and a short **Mitigation Diff Map** (one row per PR) if not already present.

---

## Phase B — Per finding (the user names the finding: ID, title, issue number, or issue URL)

```
- [ ] B0. Refresh the issue in the findings mirror
- [ ] B1. Load finding, thread, and fix diff
- [ ] B2. Review the fix
- [ ] B3. Verify with PoCs
- [ ] B4. Decide the verdict
- [ ] B5. Record (review file + GRIMOIRE status)
- [ ] B6. Present + Cyfrin write-up
- [ ] B7. Move the review file (`PENDINGS/` when waiting on the client, `done/` when closed)
```

### B0. Refresh

Before every review, check the issue on GitHub for edits and new comments since it was mirrored:

```bash
python3 <findings-sync>/scripts/findings_sync.py --repo <owner/repo> --mirror <mirror> update <N>
```

The update keeps the replaced version in `history/` and reports "up to date" when nothing changed. If
the issue isn't mirrored yet, `pull <N>` it. Tell the user what changed (body lines, new comments,
state) before reviewing. A new client comment can link a different fix, or an agreement that changes
the verdict.

### B1. Load

Run these in parallel:

```bash
$S/extract-finding.sh <report> <ID | title fragment>
$S/load-issue.sh      <N> <owner/repo>                 # full thread + PR/commit links in it
$S/fix-diff.sh        <N> <baseline> <head> src        # the fix commits + their diff
```

If `fix-diff.sh` finds nothing, use the PR/commit links from the thread or the index row, then
`git show <sha>`. If the user's pasted title doesn't match the issue they linked, say so and review
the issue.

Summarise for yourself: root cause (one sentence), the recommendation, what the thread agreed, and
what the diff changes.

### B2. Review

Work through `references/review-checklist.md`: root cause, every instance and path (siblings,
constructor vs setter, defaults), regressions (new reverts, params, casts, privileged powers,
layout/ABI, EIP-170), bypasses of the new defence, reliance on out-of-scope code, thread
consistency, stale docs/invariants. Cite `file:line` for every claim.

For a large or cross-contract fix, spawn a `grimoire:sigil` (variant mode) on the fixed pattern to
check for unfixed siblings, and the `grimoire:familiar` to challenge any residual before you rate it.

### B3. Verify with PoCs

Follow `references/poc-patterns.md`. The minimum is:

1. **Pre-fix reproduces.** Config fixes: the report's inputs now revert. Logic fixes:
   `$S/prefix-snapshot.sh <src-file> <fix-commit> test/mitigation <ID>`, then `deployCodeTo` it. The
   snapshot is named after the finding (`<Name>PreFix<Id>.sol`), so parallel sessions never overwrite each
   other's, and it is removed again if the old code does not compile against the current tree. Layout
   changes, or a snapshot that does not compile: use an isolated copy at `<fix-commit>^` (below).
2. **Post-fix passes** with the report's own figures.
3. **Residual / bypass probes** for every concern raised in B2.
4. **The client's regression test** for the fix (from the fix commits) also passes.

Always, even when you are the only session, keep the shared checkout free of other commits and
swapped source files. Do any step that needs them in an isolated copy inside the workspace:
`bash $P/isolated-workspace.sh create <ID> --ref <commit>`. It is created at
`.isolated/<session-id>/<ID>/`, owned by this session, and nothing goes above the workspace root. Keep it
until the user closes the finding's review; never use or remove another session's copies
(the peer-review skill's `references/parallel-sessions.md`, rule 9). A copy at the workspace's HEAD is proven
byte-for-byte identical before use; with `--ref` the code differs on purpose, and the script says the
comparison was skipped. The new test files stay untracked in the workspace and are copied into the
isolated copy, so only the source under test changes.

Put the tests in `test/mitigation/<ID>MitigationReview.t.sol` (template:
`examples/MitigationReview.t.sol.template`), scoped with `--match-path`. If a fork test needs an RPC
the shell lacks, ask the user to export it (never echo the URL). If a PoC fails, report the failure
and its output; don't call the fix verified.

**When you propose a code change** (a residual fix, a hardening, a corrected version of the client's
fix), verify it the way peer reviews do, never by editing `src/` in the workspace. Copy the files into
this session's work folder (`bash $P/isolated-workspace.sh work <ID>` prints it; `a/` original, `b/`
patched) and run:

```bash
bash $P/verify-fix.sh --name <ID> \
  --patch <src/path/File.sol>=.isolated/<session-id>/work/<ID>/b/File.sol \
  --suite 'test/mitigation/<ID>*' --suite '<regression glob>'
```

It proves its isolated copy byte-identical to the workspace, runs the suites before and after the patch,
and prints every result that changed. Expect the residual PoC to flip and nothing else; investigate any
other change. Quote only a verified diff in the write-up, and keep the work folder until the user closes
the finding's review.

Skip PoCs only for renames and docs-only changes. For those, grep that no stale reference is left and
state "no behaviour change, no PoC".

### B4. Verdict

Pick one from `references/verdict-taxonomy.md`. Rate each residual as **new finding**, **note (Info)**,
or **footnote (not reported)**. Before calling a residual a finding, show the user the realism
reasoning; if the user disagrees, downgrade it.

### B5. Record

- Write `grimoire/mitigation-review/WIP/<ID>-mitigation-review.md` from
  `examples/mitigation-review-template.md`. Every new review file starts in `WIP/`.
  Include the PoC table, the run command, the thread context, and the final write-up.
- Update the finding's row in the GRIMOIRE.md status table (format in `verdict-taxonomy.md`).
- Don't edit the report file unless the user asks.

### B6. Present

Reply in this order, briefly:

1. One sentence: the verdict and the reason.
2. **What changed** — 2–4 bullets with `file:line`.
3. **PoCs** — the table (test → result) and the pass count, or why there are none.
4. **Notes** — numbered residuals with their rating, if any.
5. The write-up, following `references/writeup-format.md`: first the client line with the fix commit links
   (`$S/commit-links.sh <client-remote> <sha | #PR | PR-URL>...`; PRs resolve to their merge commit, never link a PR;
   links point to the client's external repo named in the client's comment, never to the Cyfrin audit repo), then `**Cyfrin:**` on its own line and the text as
   **one single unwrapped line**, no blockquote:

   **<Client>:**
   Fixed at commitHash [abc1234](…/commit/<full>) && [def5678](…/commit/<full>).

   **Cyfrin:**
   Verified. …

6. One line: where the review was saved and which finding is next by the index (pending, report
   order).

Expect follow-ups: "shorter", "simpler wording", "in md format", "write the recommendation as if it
led to this mitigation", "propose hardening to the client", "justify X". Their shapes are in
`references/writeup-format.md`. Update the review file's write-up section whenever the user settles
on a new version.

### B7. Close

Review files live in `grimoire/mitigation-review/` and move between its subfolders (create any that
are missing) only when the user says so:

| Folder | When the file goes there |
|---|---|
| `WIP/` | Every new review (B5), and a review taken back up from `PENDINGS/` once the client answers |
| `PENDINGS/` | The user moves on from a **Partially fixed** or **Not fixed** review, waiting on the client's answers |
| `done/` | The user closes the review |
| `archived/` | The review is discarded or invalidated |

On every move, update that finding's GRIMOIRE.md status link to
`[[mitigation-review/<folder>/<ID>-mitigation-review]]`, and any other link to the file (`grep -rl
"<ID>-mitigation-review" grimoire/ GRIMOIRE.md`). Only when the file reaches `done/` or `archived/`,
remove this session's isolated copies for the finding (`isolated-workspace.sh remove <name>`); a
review in `PENDINGS/` keeps them for when it resumes.

**Session status.** `grimoire/mitigation-review/SESSIONS.md` is a snapshot of where every review
stands now: one row per review, never a history. Every time a review file is created (B5) or moved
between these folders, replace its row with the summon skill's script, so the review can be resumed
in the last session that worked on it, which holds its context and isolated copies (`claude --resume
<session-id>`):

```bash
<summon>/scripts/session-status.sh grimoire/mitigation-review/SESSIONS.md <ID>-mitigation-review.md \
  PENDINGS "Partially fixed; asked the client Q2 in [[client-communication/<ID>]]"
```

The script reads the session ID from `$CLAUDE_CODE_SESSION_ID` and refuses without it; never edit
the table by hand. For a move into `PENDINGS/`, first add the questions to
`grimoire/client-communication/<ID>.md` (format in
`/summon` Step 2) with the answer `pending`, and point the note at them. When the client answers,
fill in the answer and outcome there before taking the review back to `WIP/`.

---

## Phase C — Wrap-up (when the user says the review is done or asks what's left)

- List the pending rows. Group docs-only acknowledgements (they can be reviewed together in one pass:
  check that the doc text is accurate and placed where the affected party will see it).
- List findings with no fix PR, with their issue numbers, for client confirmation.
- List PRs in the range that map to no finding, and whether they were skimmed for regressions.
- Offer to fill the `**Cyfrin:**` fields in the report from the saved write-ups. Do this only when
  asked.
- Offer `/scribe-distill` for any new finding a mitigation introduced.

## Guidelines

- Before the first finding, read GRIMOIRE.md's Scope and accepted-behaviour notes. Don't report
  anything listed as accepted.
- When the user corrects a claim (e.g. how a library function behaves), fix it in the review file and
  the write-up straight away, and say it was corrected.
- Keep every PoC passing. Re-run the mitigation suite before Phase C:
  `forge test --match-path 'test/mitigation/*'` (fork suites with the RPC set).
- Don't commit unless asked.
- **Isolation, always:** apply these rules on every review, even in a single session, because another
  session can start in the same checkout at any time. Follow
  the peer-review skill's `references/parallel-sessions.md`:
  - patch and probe only in an isolated copy inside the workspace;
  - take PoC output for write-ups from a clean run;
  - check `git status` and running `forge` processes before trusting a shared-checkout run;
  - never revert changes you didn't make;
  - message the other sessions if you touched a shared file.
