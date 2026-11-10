# Delivery report

## Result

Complete local downstream contents are prepared for `0xStalin-eth/grimoire-codex`, based on
canonical upstream commit `4cfded991acfe02375335e5bc8f9bd3a52c5df38` on `master`.
The owner supplied the public downstream repository on 2026-11-10. Read-only GitHub checks confirm
it is empty, its default branch is `main`, and the authenticated account has admin access.
No code, live synchronization PR, hosted CI run, secret or remote setting has been published by this
project. Publication awaits the owner's explicit approval, as required by the request.

All **30 upstream skills** have been inventoried and adapted. Six agent procedures and four
maintenance commands add ten native Codex skill entrypoints (**40 total**). None is intentionally
omitted. The [compatibility assessment](COMPATIBILITY.md) lists every skill and its output, and
[inventory.json](inventory.json) records stages and supporting files. [Patch rationale](../codex/PATCHES.md)
explains the exact compatibility edits; security methodology and confirmation gates are preserved.

```text
.agents/skills/          40 native discovery links
skills/                 generated Codex entrypoints + shared scripts/references/examples
agents/                 six generated role procedures
vendor/upstream/        196 tracked canonical files, preserved as an inert snapshot
codex/                  owned adapters, patches, inventory/config and optional MCP example
scripts/                generation, validation, install, bootstrap, PR and benchmark CLI
.github/workflows/      CI plus six-hour/manual upstream polling
benchmark/              normalized findings schema, examples, synthetic CLI demo
README.md, SYNC.md, BENCHMARKING.md, CONTRIBUTING.md
```

## Verification executed

| Check | Result |
|---|---|
| Downstream structural/ownership/reference/reproducibility validator | PASS: 40 skills, 30 Bash syntax checks, 14 Python syntax checks |
| Bundled skill-creator `quick_validate.py` | PASS: all 40 entrypoints |
| Python unittest suite | PASS: 79 tests |
| Read-only network retrieval via `sync.py --check` | PASS: pinned upstream, zero changed/deleted files |
| Repeated synchronization from separate local source | PASS: idempotent, no managed file changes |
| Local Git PR-publication integration | PASS: temporary bare remote, bot branch/commit, create/update requests via stubbed GitHub API; human commits preserved; default branch unchanged |
| Installed annotation CLI on synthetic Solidity fixture | PASS: JSON discovery, tag filtering; installed symlink entrypoint; grep fallback reports context `unknown` |
| Findings/check validators on upstream examples | PASS: two finding examples and all five check examples |
| Isolated-copy helper | PASS: byte verification, drift detection and session separation on synthetic repository |
| Per-run reports/PoCs and guarded execution | PASS: 15 dedicated tests for collisions, output ownership, private discovery, raw evidence, mirrors and Claude preservation |
| Automatic session setup | PASS: seven tests for checkout detection, dirty-work preservation, simultaneous starts, owned read-only resume and boundary/refusal checks |
| Shared Claude research inputs | PASS: four tests for automatic discovery, exact read-only content/hash retrieval, parent-audit references, symlink/escape refusal and exclusion of other Codex runs |
| Actual Foundry/Solidity execution | PASS: one synthetic private PoC, Forge 1.5.1 and local solc 0.8.25; invalid shared Claude draft excluded; shared configuration/files unchanged |
| Status helper | PASS: concurrent updates, malformed/missing IDs refused, held lock not stolen |
| Bootstrap/installation | PASS: idempotent, registry preserved, collision and Claude-toolkit destination refused |
| Benchmark init → capture → compare CLI demo | PASS with synthetic reports only; raw reports preserved |
| Benchmark integrity/adjudication | PASS: incomplete runs, modified artifacts/metadata, mismatched inputs, unsupported matches and invalid metrics rejected |
| Workflow YAML / plugin JSON / optional MCP TOML | Parsed locally; no hosted execution or live service connection |
| Original local Claude checkout + Git metadata | 823 before/after file-content hashes matched; clean status and same HEAD |

Synchronization tests also cover additions, deletions, renames, directory-to-file transitions,
source working-tree exclusion, exact blob retrieval despite export attributes, safe resource links,
escaping links, overlay preservation, review conflicts, unknown metadata, new/removed entrypoints,
platform instruction rejection, broken references and script syntax failures.

The annotation test installed only Fire and its dependency in a temporary `uv` cache. It did not
install anything in the original repository or global Python environment. Initial-delivery test repositories and synthetic run artifacts used temporary directories.
For the follow-up review-isolation verification, `TMPDIR` kept all fixtures and scratch outputs
under the ignored `.review-test-tmp/` directory inside this downstream checkout. No test writes to the original
Claude checkout. No model-driven security outcome or performance score was produced.

## Review isolation follow-up — 2026-11-10

Codex review copies now use `.isolated-codex/<run-id>/`, separately from Claude's `.isolated/`.
Runtime/run/Git-root/launch-root ownership checks prevent adopting foreign or unmarked copies;
legacy copies are not migrated. Both trees are excluded from Codex snapshots. Review/status helpers
require `GRIMOIRE_AUDIT_ROOT`, reject a broader Git root and block escaping output paths. Optional
Git metadata refreshes are disabled to avoid writes to shared metadata of linked checkouts.

Twelve dedicated regression tests cover identical Claude/Codex IDs and names using the actual
archived Claude helper, simultaneous Codex runs, cleanup preservation, foreign markers, symlinks,
pinned-commit snapshots, missing/relative launch roots, nested launch boundaries, external status
logs, linked-checkout metadata and fix-verification scratch paths. Fix orchestration uses a fake
Forge process; it does not establish Solidity or vulnerability correctness. These 12 tests remain
part of the expanded suite. The original-Claude checkout remains unchanged.

## Reports and PoCs follow-up — 2026-11-10

All Codex context, reports, findings mirrors, session logs and PoCs now use an owned
`grimoire-codex/<run-id>/` tree inside the audit launch boundary. PoCs use its `pocs/` directory,
outside shared test discovery. The writer, mover and adapted helpers refuse Claude's output paths,
other runs, unmarked roots, ownership-marker changes and symlink redirects. Existing report files
are created exclusively unless an intentional own-run update is requested. Client reports and
explicitly supplied Claude artifacts remain read-only inputs; legacy output is not migrated.

The private runner explicitly includes only this run's PoCs in owned source copies, even when
Git-ignored, and retains raw stdout/stderr under the run's `runs/`. Fix verification retains its
before/after evidence and uses normal project discovery for regression suites. Build/cache/tmp,
build information, snapshots and fuzz/invariant persistence stay run-local. Foundry compiler
auto-installation and shared RPC caching are disabled. The guide documents the layout and launch
sequence; personal-store setup is optional and unnecessary for peer/mitigation review.

Fifteen dedicated artifact tests cover simultaneous same-name outputs, exclusive writes, guarded
moves, Claude/other-run/symlink refusals, canonical-source protection, private mirror history,
extraction/import paths, ignored PoCs, stale-PoC pruning, empty/failing evidence, private snapshot
compilation and PoC/regression discovery. The full suite passes 68 tests.

A real Foundry smoke used a synthetic contract and private PoC with relative imports. An existing
solc 0.8.25 binary was copied into the fixture's owned work directory; no compiler was downloaded.
Forge 1.5.1 executed one passing test while an intentionally invalid Claude-owned shared draft
was excluded. Shared context, Claude draft and `foundry.toml` hashes stayed unchanged; no shared
root `out/` or `cache/` appeared. The fixture and compiler copy were cleaned. This demonstrates
private test routing and compilation, not a model-driven audit or a security finding's validity.

## Automatic session setup follow-up — 2026-11-10

The first audit skill now instructs Codex to run `scripts/session.py start` itself using the
original runtime launch directory. The helper inspects Git root, HEAD and uncommitted changes
read-only, creates a fresh UUID, initializes private artifacts and writes that run's `session.json`.
Its JSON result supplies the environment for later helper calls. The operator starts normal
`codex` in the audit checkout; no repeated path variables, exports, Git checks or copied IDs are
required. The current HEAD remains checkout evidence, not an assumption about the audited commit.

New starts ignore inherited run/root variables; simultaneous starts receive independent outputs
and working copies. A resumed chat must identify its own recorded run explicitly. Resume validates
ownership and saved paths, rereads current Git evidence, and leaves the original run record intact.
No shared environment file or latest-run pointer is created. Seven synthetic integration tests
exercise these behaviors and refusal paths. The full suite passes 75 tests. This validates the
helper and generated instructions; it is not a model-driven CLI startup or resume test.

## Short invocations and shared research follow-up — 2026-11-10

The four core entrypoints now embed their invocation defaults: `$summon`, `$peer-review #12`,
`$mitigation-review M-1` and `$finding-draft` handle setup and output paths without a pasted prompt.
Reviews bootstrap missing private context from the request, checkout and available research instead
of requiring a separate operator summon step. Summon accepts the current target checkout or a
scoped checkout inside the launch folder; it never suggests moving above the audit boundary.
Missing/ambiguous findings-repository identity, scope or commit evidence still requires a question.
Reproduction, Familiar triage, finding-content checkpoints and publication gates are preserved.

Session setup discovers existing root GRIMOIRE.md and grimoire/ research at the launch and target
roots. All skills may consult relevant Claude tomes and indexes automatically as read-only inputs.
The reference reader returns contained Markdown and its SHA-256 without changing any source file,
and refuses symlinks, outside paths and other Codex runs. New conclusions and corrections stay
private to Codex, with source pointers; shared research is never adopted as independently verified
evidence. Four additional synthetic integration tests cover these behaviors. The full suite now
passes 79 tests; no model-driven security review or automatic input-inference result is claimed.

## Behavioral differences and manual attention

- Codex uses optional pre-audit personal-store setup, reads its own GRIMOIRE at skill entry and dispatches
  Familiar after Sigil. These are instructions, not Claude lifecycle-hook guarantees.
- Six role skills expose full procedures; independent execution requires a real Codex subagent or
  fresh session. When unavailable, mandatory independent review pauses with a saved handoff.
- Automatic skill-entry setup captures `GRIMOIRE_AUDIT_ROOT` and generates `GRIMOIRE_SESSION_ID`;
  Codex supplies both to helpers. Working copies use `.isolated-codex/`, separately from Claude’s
  `.isolated/`; runtime/run/Git-root/launch-root ownership and exclusions protect reuse and cleanup. Operator run IDs are distinguished from verified
  resumable chat IDs. Copy ownership and containment checks remain enforced.
- Context7/claudit setup is optional and manual; actual tool namespaces are discovered dynamically.
  Live MCP access, vector indexing/search and embedding-model downloads were not tested.
- The Pi footer is archived only. Super Sigil and full static-analyzer integrations were already
  unfinished upstream. The downstream does not claim to implement those missing upstream features.
- No real target, complete multi-agent audit, live bounty acquisition, issue synchronization or
  client-fix review was executed. The synthetic Foundry/Solidity smoke verifies private execution;
  it does not establish audit equivalence or real vulnerability correctness.
- Hosted plugin installation and GitHub PR API publication remain untested. Local publication tests
  used real temporary Git remotes and stubbed only GitHub interactions.

No skill currently has an unresolved structural compatibility error. Adapted-source changes,
missing runtime tools, independent-review availability and optional services can require manual
attention. The full audit-equivalence requirement remains an empirical validation task on an
explicitly authorized target.

## Start using Codex

From this downstream checkout, with a pre-existing target Git checkout for the review:

```sh
python3 scripts/validate.py
python3 scripts/install.py --project "$HOME"
cd /path/to/audit/target-checkout
codex
```

Invoke `$summon` on the local target, then the desired workflow. Codex initializes the session and
supplies helper variables itself; independent chats get distinct runs automatically.
[README](../README.md) covers paths, dependencies and available skills.

## First comparison

For the runnable, non-model demonstration:

```sh
python3 benchmark/demo.py --output /tmp/grimoire-comparison-demo
```

For a real comparison, follow [BENCHMARKING.md](../BENCHMARKING.md): create two clean target clones
at one commit, freeze shared scope/task/knowledge, collect provenance with `benchmark.py init`,
execute the workflows in separate environments, capture raw outputs with `complete`, manually
adjudicate root causes and validity, then `compare` the two finished directories. Preserve tool,
adapter and runtime differences as confounds. No agent should see the other's findings.

## Remaining GitHub setup

The owner has created [0xStalin-eth/grimoire-codex](https://github.com/0xStalin-eth/grimoire-codex)
as a public repository. After explicit authorization, publish **only this downstream** checkout
from its root (no local remote is configured yet):

```sh
git remote add origin https://github.com/0xStalin-eth/grimoire-codex.git
git push -u origin main
gh workflow run ci.yml --repo 0xStalin-eth/grimoire-codex
gh workflow run sync.yml --repo 0xStalin-eth/grimoire-codex
```

Push/settings changes have not been executed. Read-only checks show Actions has read-only default
workflow permissions and its create/approve-PR toggle is disabled. Enabling that downstream-only
toggle also requires explicit approval; keep the default token permissions read-only. The sync
job requests its own narrow write permissions. The default token needs no secret and
requests Contents/Pull requests write only in the sync job. Approve bot-created PR workflow runs
when GitHub requires it, or configure the optional downstream-only `SYNC_PR_TOKEN` for automatic
PR checks. Branch protection/review rules are optional owner settings. See [SYNC.md](../SYNC.md)
for permissions, authentication, exact triggers and troubleshooting.

The default branch is never automatically updated from upstream: changes go through a reviewable
bot PR. Patched-source conflicts fail with file-specific diagnostics and require a downstream
manual compatibility update. Upstream requires **zero** modifications or configuration.

## Upstream safety verification

The original local Claude checkout and its parent plugin directory were hashed before development
and again at delivery: **823 file-content hashes, zero additions, deletions or content changes**,
including Git metadata. Its HEAD remains the pinned upstream SHA and its working tree remains
clean. Original-repository operations were read-only; all cloning/generation/testing occurred in
this downstream or temporary directories. No upstream push, commit, branch, tag, PR, setting,
workflow, App or secret mutation was performed.
