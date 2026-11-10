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
| Audit folder | Contains the target checkout (or is the checkout itself), existing Claude research and Codex's private output. Start Codex here. |

Use your existing audit folder, either the target Git checkout itself or a folder containing the
scoped checkout and Claude's research. Codex identifies the target from your request and existing
scope; it asks only if several repositories remain ambiguous. Review helpers run from the selected
target's Git root, which must remain inside the original launch folder. Use an existing suitable
checkout or clone a new one, for example:

```sh
mkdir -p "$HOME/audits"
git clone "REPLACE_WITH_TARGET_REPOSITORY_URL" "$HOME/audits/example-review"
```

Replace the URL before running that example. It is the repository being audited, not either
Grimoire toolkit repository. If you already have a dedicated review checkout, skip the clone.

Codex handles the checkout inspection: it detects the Git root, current commit and uncommitted
changes, and preserves existing work. You do not need a `GRIMOIRE_REVIEW_DIR` variable or manual
Git checks. Tell it which finding or fix you want reviewed; it can read commit references from
the supplied scope and finding, asking only when the intended audited/fix commit is unclear.
The current HEAD is detected automatically; it is not assumed to be the audited commit.

Keep input reports and findings inside the audit folder. Claude's root context and `grimoire/`
research are discovered automatically as read-only references. If a helper needs a checkout-local
input, Codex makes its own attributed copy under its private run, preserving the source.

## 5. Launch Codex normally

Open a terminal in the audit checkout and start Codex:

```sh
cd "/path/to/your/audit-checkout"
codex
```

For an explicit workspace sandbox, you can use
`codex --sandbox workspace-write --ask-for-approval on-request` instead.

When you request the first Grimoire skill, Codex automatically:

1. Records the original launch directory as the fixed audit boundary.
2. Inspects the checkout, HEAD and uncommitted work without changing them.
3. Discovers Claude's existing context and research as read-only inputs.
4. Creates a fresh UUID and private report/PoC directories for this chat.
5. Saves `grimoire-codex/<run-id>/session.json` and passes the required environment to its helpers.

There are **no per-session exports, path variables or IDs for you to generate or paste**. Each
parallel Codex chat gets its own run, even when both start in the same audit checkout or inherit
old terminal variables. The session record stays inside that run; there is no shared `.env` or
"latest session" file. Skill entry performs setup; simply opening an idle Codex chat creates no
Grimoire artifacts.

All audit work, copies and scratch files remain inside the original launch directory. The UUID is
an **operator run ID**, not a Codex chat ID. Codex records and manages it for you.

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

Inside Codex, invoke:

```text
$summon
```

The skill handles session setup, checkout inspection, private paths and context building. It uses
the local code by default, reads existing Claude `GRIMOIRE.md` and relevant `grimoire/tomes/`
research, and writes its own context, notes and PoCs. You do not need to paste setup instructions
or grant read access to those audit-local references each time. Bounty acquisition runs only when
you supply a program URL/slug; a Sigil swarm still needs explicit approval.

On resume, Codex automatically reloads its own session/context. On a new run, it creates its own
context and cites useful shared research instead of adopting another run. Existing Claude context,
tomes, indexes, links and logs remain unchanged. Corrections and new conclusions go into Codex's
private run. Scope, repository and commit questions appear only when available sources leave an
input missing, conflicting or ambiguous.

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
        ├── session.json       # automatic run setup and original checkout evidence
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

The examples below are **Codex messages**. Replace the example target with yours. Setup, read-only
research discovery, private output paths and review stages are already embedded in the skills.
You can invoke a review directly without first invoking summon; Codex creates missing private
context itself. Existing evidence and publication confirmation points remain in place.

### Review a finding from a peer or another agent

```text
$peer-review #12
```

Codex resolves the findings repository and scope from this chat or the existing audit context.
If repository identity is missing or ambiguous, it asks once; a full issue URL also provides it.
You can supply a local finding file instead. The skill reproduces the claim, checks severity,
scope and duplicates, verifies the proposed fix, and presents its verdict before publication.
GitHub-backed workflows require authenticated `gh`; Codex checks access and reports missing login.

Expect test/proof output and a review verdict. Session copies go under
`.isolated-codex/<run-id>/` in the checkout. Keep them until you close the lead; follow-up questions may
reuse them. A missing test environment is a verification gap, not proof that the finding is invalid.

### Review the client's mitigation

Use a checkout containing the fix commits, then invoke:

```text
$mitigation-review M-1
```

Codex finds the report, repository, audited/fix commits and relevant research from available
context, asking only for unresolved inputs. It fetches its own findings mirror, verifies the fix
with pre/post/residual evidence, and saves a verdict and report write-up privately. Client reports
remain read-only inputs. The workflow tracks whether the review is in progress, waiting on the
client or closed. Reading a diff alone does not establish that the mitigation works.

### Draft a finding from your evidence

```text
$finding-draft
```

The skill uses the bug and evidence already discussed; you can also name an observation or file.
It consults relevant shared research read-only, handles private output paths, and asks for missing
details. Familiar triage and the title, severity and draft-content review stages still apply.

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

Each skill resolves the installed toolkit, runs setup, supplies the returned environment to its
helpers, and uses the guarded writer and private PoC runner. These are built-in workflow defaults.

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
Include this session's record path so this chat can reload its own run later.
```

To continue the same logical session later, open the same audit checkout and use Codex's resume
picker:

```sh
cd "/path/to/the/same/review-checkout"
codex resume
```

Choose the actual previous Codex chat. It reloads its own recorded run with `session.py resume`
and checks the current checkout; you do not need to restore exports. If its run cannot be safely
identified from that chat's context, it creates a fresh one and leaves earlier output alone.
A new independent review always gets a fresh ID and separate working copies. Codex never picks
the newest folder or another session's ID to decide which run to resume.

The everyday pattern, after registration, is:

1. Open a terminal in the audit checkout.
2. Start `codex`, or use `codex resume` for an existing chat.
3. Ask for peer review or mitigation review and supply the finding/scope information.
4. Inspect the evidence and saved artifacts before accepting its conclusions.

## 10. Common first-time questions

| Question / problem | What to do |
|---|---|
| Do I pass a Claude-style `--plugin-dir` flag each time? | This guide uses Codex's skill discovery directories. After registration, start `codex` in the review checkout. |
| Do I install the skills again for each target? | User-level registration is reusable. Each target still needs its own engagement context and review inputs. |
| The skills do not appear in `/skills`. | Restart Codex and check `ls -l "$HOME/.agents/skills/peer-review/SKILL.md"` in your terminal. A moved toolkit folder breaks the links. |
| A skill appears twice. | You may have both user-level and project-level registration. Choose one installation scope; Codex can discover both. |
| Do parallel sessions need different exports? | No. Each chat's first Grimoire skill creates its own run and manages helper variables. |
| Do I paste the setup/safety prompt every time? | No. Invoke the skill and name its target; session setup, write boundaries, private paths and read-only research are embedded. |
| Do I need to run summon before peer/mitigation review? | No. The review skill bootstraps missing private context from available sources and asks only for unresolved inputs. |
| Can Codex read Claude's tomes without asking every time? | Yes. Audit-local Claude context and relevant `grimoire/tomes/` files are automatically available read-only. |
| A helper says the audit root is missing. | Ask Codex to load its own session record and pass the returned environment to the helper. A new chat runs automatic setup. |
| The Git root is above/outside my launch directory. | The helper refuses before creating copies. Keep the boundary; use a suitable checkout inside it, or explicitly start a new session at the intended repository root. |
| A helper refuses a report or PoC destination. | Use paths returned by `review_artifacts.py init`. Claude’s directories, other run IDs, unmarked folders and symlinks are not writable destinations. |
| A helper says the run ID is missing or malformed. | Ask Codex to reload its own session record or initialize a new run; it should pass the returned ID itself. |
| A helper refuses an outside-workspace path. | Codex should preserve the guard and make an attributed private copy of an audit-local input when needed. Inputs outside the audit folder must be supplied inside it. |
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
