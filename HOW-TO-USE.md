# How to use Grimoire with Codex

You can work much as you already do with Claude: launch an interactive session in a terminal,
describe your task, and let the assistant use the appropriate skills. With this setup, you register
the skills once, then start **`codex`** in the checkout where you want to work.

This walkthrough starts with your usual workflows: peer review, mitigation review and finding drafts.
It uses the existing local Grimoire-Codex folder; publishing it to GitHub is not required.

## 1. Understand the three pieces

| Term | What it means here |
|---|---|
| Codex / main agent | The assistant you talk to in your terminal. It reads files, runs tools and follows your requests. |
| Skill | A workflow the assistant can read and follow, such as `peer-review`. It is stored in a `SKILL.md` file with supporting resources. |
| Subagent | A separate agent context used for delegated work, such as an independent Familiar review. Starting a skill does not itself create a subagent. |

Codex discovers skill names and descriptions. It reads the full instructions when it selects a
skill. You can request a skill explicitly or let Codex choose one from your request.
This is supported by the [official skill documentation](https://learn.chatgpt.com/docs/build-skills).

In this guide, **`sh` blocks are terminal commands**. **`text` blocks are messages to paste into
Codex after it has started**. In particular, `$peer-review` belongs in a Codex message; typing it
alone at a shell prompt will not start the workflow.

## 2. Check the command-line tools and sign in

In a terminal, run:

```sh
codex --version
python3 --version
git --version
```

You need Codex CLI, Python 3.10 or later, Git and Bash. If `codex` is not found, follow the
[official CLI installation instructions](https://learn.chatgpt.com/docs/codex/cli) and then retry.
Having the desktop app available does not necessarily mean your terminal can find the CLI.

For your first CLI session, sign in:

```sh
codex login
```

Follow the sign-in prompts. You can check the result with `codex login status`. Codex has its own
authentication; your Claude login does not sign you into Codex.

## 3. Register the Grimoire skills once

Open the local **Grimoire-Codex** folder in your terminal. Replace the example path below with the
location of that folder on your computer:

```sh
cd "/path/to/Grimoire-Codex"
export GRIMOIRE_CODEX_ROOT="$(pwd)"
python3 "$GRIMOIRE_CODEX_ROOT/scripts/validate.py"
python3 "$GRIMOIRE_CODEX_ROOT/scripts/doctor.py"
```

`validate.py` checks the toolkit. `doctor.py` lists available tools; an unavailable optional tool
does not prevent you from starting Codex. For example, GitHub issue workflows use `gh` and `jq`,
while Solidity proofs need your target project's compiler, dependencies and test runner.

Now register the skills for your user account:

```sh
python3 "$GRIMOIRE_CODEX_ROOT/scripts/install.py" --project "$HOME"
```

The installer's argument is named `--project`. Passing your home directory makes it create links
in **`~/.agents/skills/`**, the user-level Codex skill directory. Expect:

```text
Installed 40 Codex skills. Restart Codex if they are not visible.
```

These links point to this toolkit folder. Keep the folder at a stable location. Existing unrelated
skills are not overwritten; a collision stops installation and names the conflicting path.
Registration makes the workflows available to your Codex sessions; it does not execute them.

We use user-level registration for this walkthrough because the review helpers reject unignored
symlinks that leave the target repository. Installing skill links inside that repository can trigger
that check. Keeping them under your home directory avoids adding those links to the audited code.

For peer review and mitigation review, **skip personal-store setup**. The review helpers initialize
their own audit-local directories in step 5.

If you later need personal libraries or detectors, the optional setup command is:

```sh
python3 "$GRIMOIRE_CODEX_ROOT/scripts/bootstrap.py"
```

Run it only as a separate setup step before an audit session. By default it prepares `~/.grimoire/`
for libraries, caches and detectors, preserving an existing library registry. Your Claude setup may
already use that store. Leave it alone for your review workflows. For independent benchmarks, use the
separate environments described in [BENCHMARKING.md](BENCHMARKING.md).

## 4. Choose the checkout where the review will happen

Keep these two locations separate:

| Location | Purpose |
|---|---|
| Grimoire-Codex folder | Stores the skills and helper scripts. |
| Dedicated target checkout | Stores the code you are reviewing and Codex's private `grimoire-codex/<run-id>/` outputs. Start Codex here. |

For peer review and mitigation review, use a dedicated checkout of the **target codebase**, with
its own `.git` directory. These helpers run from that checkout's Git root and keep their working
copies inside it. Use an existing suitable checkout or clone a new one, for example:

```sh
mkdir -p "$HOME/audits"
git clone "REPLACE_WITH_TARGET_REPOSITORY_URL" "$HOME/audits/example-review"
```

Replace the URL before running that example. It is the repository being audited, not either
Grimoire toolkit repository. If you already have a dedicated review checkout, skip the clone.

Set a convenient variable to its absolute path, then check its root and current commit:

```sh
export GRIMOIRE_REVIEW_DIR="$HOME/audits/example-review"
git -C "$GRIMOIRE_REVIEW_DIR" rev-parse --show-toplevel
git -C "$GRIMOIRE_REVIEW_DIR" rev-parse HEAD
git -C "$GRIMOIRE_REVIEW_DIR" status --short
```

Confirm the checkout contains the commit you intend to review. Tell Codex about any existing
uncommitted work; it must preserve that work. Keep input reports and findings inside this checkout,
too. The review helpers refuse input paths that resolve outside it.

## 5. Give this session a run ID and launch Codex

Some helpers need an ID to keep one session's temporary copies separate from another's. Before
starting a **new logical session**, generate an ID:

```sh
cd "$GRIMOIRE_REVIEW_DIR"
export GRIMOIRE_AUDIT_ROOT="$(pwd -P)"
export GRIMOIRE_SESSION_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
printf 'Audit root: %s\nRun ID: %s\n' "$GRIMOIRE_AUDIT_ROOT" "$GRIMOIRE_SESSION_ID"
python3 "$GRIMOIRE_CODEX_ROOT/scripts/review_artifacts.py" init
codex --sandbox workspace-write --ask-for-approval on-request
```

The initializer prints the private report, context and PoC paths for this run; it leaves Claude's
existing files untouched. All are inside your audit directory.

Keep both printed values in your private session notes. The root is the immutable directory where
you launch Codex: all audit work, copies and scratch files must remain inside it. The UUID is an
**operator run ID**, not a Codex chat ID. It cannot identify a chat for `codex resume`.

The terminal now contains an interactive Codex session. You can converse with it as you do with
Claude. If asked to trust a folder, check that it is the intended review checkout.

## 6. Confirm that Codex can see the skills

Inside Codex, type:

```text
/skills
```

Look for `peer-review`, `mitigation-review` and `finding-draft`. You can also type `$` and select a
skill. The `/skills` selector and `$skill-name` syntax are documented in the
[official skill guide](https://learn.chatgpt.com/docs/build-skills).

You do not need to start a separate terminal process for each skill. You can use several workflows
in one conversation, retaining the context you have already discussed.

## 7. Initialize the review workspace with summon

If you are resuming the same run, ask Codex to read its own
`grimoire-codex/<run-id>/GRIMOIRE.md` and confirm the scope and commits. A new run gets its own
context, notes and PoCs. A root `GRIMOIRE.md` or `grimoire/` directory may belong to Claude; Codex
must not update those files. You may explicitly supply them as read-only inputs when appropriate.

Otherwise, paste this into Codex. Replace `PASTE_RUN_ID_HERE` and
`PASTE_AUDIT_ROOT_HERE` with the values printed in step 5:

```text
Use $summon to initialize this dedicated review checkout.

Use the run-owned paths returned by review_artifacts.py init:
context and reports under grimoire-codex/<my-run-id>/, and PoCs under
its pocs/ directory. Keep Claude’s GRIMOIRE.md, grimoire/, and test
folders untouched. Use the guarded writer and private PoC runner.
Ask me for the audited commit, in-scope paths and findings repository.
Use the local code; skip bug-bounty acquisition.

My audit root is PASTE_AUDIT_ROOT_HERE. All work, including isolated
copies, scratch files and caches, must stay inside that directory.
Never broaden that root after changing directories.
My operator run ID is PASTE_RUN_ID_HERE. Explicitly pass
GRIMOIRE_AUDIT_ROOT and GRIMOIRE_SESSION_ID to helpers that need them,
even if the shell environment does not inherit them. Record that the
run ID is not a chat ID. Give independent subagents their own run IDs
while retaining the same audit root.

Preserve tracked source files. Ask before running a Sigil swarm.
```

The review layout keeps all Codex output in the audit checkout, under this run’s own directory.
If a client report is elsewhere, provide a local copy as a read-only input; ask Codex to save any
proposed edits as its own derivative report rather than replacing that input.

Codex should ask for missing context and prepare the workspace, including:

```text
example-review/
├── .git/
├── src/                       # target's existing source; actual layout varies
├── GRIMOIRE.md                # existing Claude context; unchanged
├── grimoire/                  # existing Claude output; unchanged
├── test/                      # existing project/Claude tests; unchanged
└── grimoire-codex/
    └── <run-id>/
        ├── .owner             # Codex/run/workspace/launch-root ownership
        ├── GRIMOIRE.md         # this Codex run's context
        ├── findings/
        ├── peer-review/
        ├── mitigation-review/
        ├── pocs/
        │   ├── peer-review/
        │   └── mitigation-review/
        ├── runs/              # raw compiler/test evidence
        └── tomes/
```

The context and reports above belong to one Codex run. The existing root `GRIMOIRE.md`,
`grimoire/` and shared test folders are not Codex output destinations. Neither output tree is the
Grimoire-Codex toolkit itself. Keep these audit artifacts private unless you have
authorization to publish them.

## 8. Use your usual workflows

The examples below are **Codex messages**. Replace the example issue, paths and commit references
with your real inputs. Codex will ask for missing information and pause at workflow confirmation
points.

### Review a finding from a peer or another agent

```text
Use $peer-review on issue #12 in OWNER/FINDINGS-REPOSITORY.
Read this run’s grimoire-codex/<my-run-id>/GRIMOIRE.md for scope and the audited commit.
Reproduce the claim, assess severity and duplicates, and verify the proposed fix.
Keep temporary patches in this session's isolated copy.
Present the verdict before taking any follow-up publishing action.
```

You can point it at a local finding file instead of an issue URL. Supply the relevant scope, issue
context and duplicate information, too. For GitHub-backed workflows, check `gh auth status` in a
terminal; use `gh auth login` if access still needs setup.

Expect test/proof output and a review verdict. Session copies go under
`.isolated-codex/<run-id>/` in the checkout. Keep them until you close the lead; follow-up questions may
reuse them. A missing test environment is a verification gap, not proof that the finding is invalid.

### Review the client's mitigation

Use a separate review checkout containing the fix commits. Launch Codex there using step 5 with
a **new** run ID. Skill registration is already done. Keep its own context, derivative reports and findings mirror under
`grimoire-codex/<new-run-id>/`. Let it fetch its own mirror rather than copying another review’s
mirror. Existing client reports are read-only inputs; Codex writes proposed report edits to its
own run directory.

```text
Use $mitigation-review for finding M-1.
The report is scope/audit-report.md inside this checkout.
The findings repository is OWNER/FINDINGS-REPOSITORY.
The audited commit is AUDITED_COMMIT and the fix commit is FIX_COMMIT.
Confirm the in-scope paths with me, then verify the fix with pre-fix and post-fix PoCs.
```

Provide the new session's run ID as in step 7. Expect a per-finding verdict, evidence and a report
write-up. The workflow records whether a review is still in progress, waiting on the client or
closed. Reading a diff alone does not establish that the mitigation works.

### Draft a finding from your evidence

```text
Use $finding-draft to document the issue we just reproduced.
Use the source locations and PoC output from this conversation.
Save the draft under this run’s grimoire-codex/<my-run-id>/findings/WIP/.
Do not write to Claude’s grimoire/ or shared test folders.
Ask me for any missing information before making a claim.
```

Then, in the same conversation:

```text
Use $finding-review on the draft you just created.
Check its wording, evidence references, severity and recommendations.
```

`finding-review` evaluates the write-up's quality. `peer-review` evaluates the underlying finding,
including reproduction. Drafting a report does not itself verify the vulnerability.

### Let Codex select the skill automatically

Once you are comfortable, ordinary requests work too:

```text
Review whether the client's fix resolves M-1.
```

```text
Draft a finding for the issue we just proved.
```

Codex can choose a matching skill from its description. Explicit `$skill-name` requests make your
intended workflow clear while you are learning; you can ask which skill it selected if unsure.

### Keep Claude and Codex output separate

Both runtimes can use the same audit checkout with separate output and working-copy namespaces:

```text
your-audit/
├── GRIMOIRE.md                       # Claude's existing context; unchanged
├── grimoire/                         # Claude's existing reports; unchanged
├── test/mitigation/                  # Claude/project PoCs; unchanged
├── grimoire-codex/
│   ├── run-id-A/                     # Codex context, reports, logs, mirrors and PoCs
│   └── run-id-B/                     # another Codex run's independent output
├── .isolated/                        # Claude's existing copies; unchanged
└── .isolated-codex/
    ├── run-id-A/
    │   ├── .owner
    │   ├── i12/                     # source + this run's PoCs for execution
    │   └── work/                    # compiler cache, output, temporary files and probes
    └── run-id-B/
        └── i12/                     # same issue name, different run
```

Codex never adopts or cleans Claude's `.isolated/` copies. Its source snapshots exclude both
isolation trees, including when building a pre-fix copy from another commit. A matching issue
name or even a matching Claude session ID therefore cannot select Claude's copy. New Codex
sessions need distinct run IDs; deliberately reusing an ID means resuming the same logical run.
The owner marker must match the runtime, run ID, Git root and original launch directory.
Unmarked legacy Codex copies in `.isolated/` are also left untouched; no automatic migration occurs.

Reports, session logs, finding mirrors and PoCs are now separated too. Run IDs make identical
issue IDs and filenames safe across Claude and Codex and across independent Codex runs. Existing
Claude/legacy Codex output is not automatically migrated or adopted. The guarded writer, mover,
extraction/snapshot helpers and status/mirror helpers reject Claude’s paths, other runs and symlink
redirects. Updates to an existing file in your own run require an intentional `--replace` when using
the writer; filing moves refuse an existing destination.

For example, a Codex agent resolves the installed toolkit root and uses these helpers (replace
`/path/to/Grimoire-Codex` with that path; run from the audit Git root with the two launch variables):

```sh
python3 "/path/to/Grimoire-Codex/scripts/review_artifacts.py" init
python3 "/path/to/Grimoire-Codex/scripts/review_artifacts.py" path reports
python3 "/path/to/Grimoire-Codex/scripts/review_artifacts.py" path poc-relative
```

Let Codex use those returned paths. Its messages can say:

```text
Write the review and PoC through review_artifacts.py into this run’s directories.
Keep the source report read-only. Execute the PoC with the private runner,
and include the saved raw test evidence in the review.
```

The runner uses `test --name <copy-name> --suite <poc-relative>/<pattern>` and optional
`--ref <commit>` for pre-fix tests. It explicitly sets Foundry’s test directory to your run’s PoCs
inside your owned copy. Your project’s `foundry.toml` and shared test directories are unchanged.
Compiler output/cache/tmp are run-local; raw stdout/stderr is retained under your run’s `runs/`.
Build information, snapshots and fuzz/invariant persistence also stay in that run's work folder.
Automatic compiler installation and shared RPC caching are disabled. Use an available compiler,
or prepare one inside the audit folder. A missing compiler is a setup gap to resolve locally.
No matched tests or zero executed tests is reported as a verification failure, not success. For
regression suites, the fix-verification helper retains the normal project test configuration in
the isolated copy. Other test frameworks need the equivalent private-discovery setup.

Only this run’s PoCs are added to its source snapshots, including when audit output is Git-ignored.
Reports and other Codex runs’ PoCs are excluded. Byte-for-byte source and PoC verification stays
in place. Ordinary project source is still shared read-only input: neither model should patch the
shared source checkout while the other is reviewing it.

## 9. Stop, continue later, or begin another review

Before ending a session, you can ask:

```text
Use $hunt-summary to record the evidence, decisions, open questions and next steps.
Include this session's operator run ID so I can restore it later.
```

To continue the same logical session later, restore its **old** run ID in your terminal and use
Codex's resume picker:

```sh
cd "/path/to/the/same/review-checkout"
export GRIMOIRE_AUDIT_ROOT="$(pwd -P)"
export GRIMOIRE_SESSION_ID="PASTE_THE_PREVIOUS_RUN_ID_HERE"
codex resume --sandbox workspace-write --ask-for-approval on-request
```

Choose the actual previous Codex chat. Remind it of the run ID if needed. A new independent review
gets a new run ID and separate working copies. Do not use another session's ID to access its copies.

The everyday pattern, after registration, is:

1. Choose the correct review checkout and confirm its commit.
2. Set the audit root to your launch directory; export a new run ID, or restore the old one when resuming.
3. Start `codex --cd ...`, or resume the existing chat.
4. Request the workflow, supply its inputs and answer confirmation prompts.
5. Inspect the evidence and saved artifacts before accepting its conclusions.

## 10. Common first-time questions

| Question / problem | What to do |
|---|---|
| Do I pass a Claude-style `--plugin-dir` flag each time? | This guide uses Codex's skill discovery directories. After registration, start `codex` in the review checkout. |
| Do I install the skills again for each target? | User-level registration is reusable. Each target still needs its own engagement context and review inputs. |
| The skills do not appear in `/skills`. | Restart Codex and check `ls -l "$HOME/.agents/skills/peer-review/SKILL.md"` in your terminal. A moved toolkit folder breaks the links. |
| A skill appears twice. | You may have both user-level and project-level registration. Choose one installation scope; Codex can discover both. |
| A helper says the audit root is missing. | Pass the original absolute launch directory as `GRIMOIRE_AUDIT_ROOT`. Never substitute a broader Git root. |
| The Git root is above/outside my launch directory. | The helper refuses before creating copies. Keep the boundary; use a suitable checkout inside it, or explicitly start a new session at the intended repository root. |
| A helper refuses a report or PoC destination. | Use paths returned by `review_artifacts.py init`. Claude’s directories, other run IDs, unmarked folders and symlinks are not writable destinations. |
| A helper says the run ID is missing or malformed. | Give Codex the UUID from step 5 and ask it to pass `GRIMOIRE_SESSION_ID` explicitly to that command. |
| A helper refuses an outside-workspace path. | Place the required report/input in the dedicated review checkout. Preserve the containment check. Skill definitions remain in the installed toolkit. |
| An isolated copy rejects a skill symlink. | Check for project-local `.agents/skills/` links in the target. This walkthrough uses user-level links outside it; discuss removal or local exclusion of existing links before changing them. |
| It asks for an independent Familiar or Hag review. | Let it use a separate Codex subagent context. If delegation is unavailable, it should save a handoff for a fresh session and report the pending review. |
| Do I need Solodit or Context7 keys to start? | Those integrations are optional. Available tools and supplied evidence determine coverage; see [the MCP example](codex/mcp.example.toml) when you need them. |
| Can I use this in the desktop app? | Open the same local review checkout in Codex. User-level filesystem skills are supported; this walkthrough specifically verifies CLI commands. Remote sessions need the toolkit installed on their own machine. |

For a general audit with several repositories, keep the target repositories inside the chosen
audit launch directory. Codex’s context and output still use its private per-run namespace. Start Codex in that
engagement directory. [README.md](README.md) also describes project-level registration via
`install.py --project /path/to/engagement`; choose that instead of user-level registration when you
want the skills confined to one engagement. For peer/mitigation review, retain the checkout-local
input and isolation rules described above.

Reviewed against the local helpers and official Codex documentation; review-isolation updates
and artifact-separation updates verified on 2026-11-10, including a real local Foundry/Solidity
smoke test. Full multi-agent
security audits and live integrations still need runtime validation; see the
[delivery report](docs/DELIVERY.md) for exactly what has been tested.
