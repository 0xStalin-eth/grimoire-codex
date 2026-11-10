# Grimoire for Codex

Independent Codex execution of [Grimoire](https://github.com/0xStalin-eth/grimoire) security research
workflows. Grimoire remains the canonical source. This downstream repository owns all Codex
adaptation and polling automation. **The original repository requires zero changes and is never
written by this project's tools.** Upstream MIT attribution is retained in [LICENSE.md](LICENSE.md).

Initial port baseline: `4cfded991acfe02375335e5bc8f9bd3a52c5df38` (`master`). The current authoritative
revision and content hashes are in [sync-state.json](sync-state.json).

## Start using the skills

New to Codex agents and skills? Start with [HOW-TO-USE.md](HOW-TO-USE.md), a terminal walkthrough
covering setup, skill discovery, peer review, mitigation review and finding drafts.

Requires Python 3.10+, Git and Bash. No Claude runtime or CLI is needed. Optional dependencies are
listed by `python3 scripts/doctor.py`. GitHub issue workflows need `gh`/`jq`; annotations use `uv`
and Fire; semantic library search uses `uv`, Qdrant/FastEmbed and an initial model download.
Smart-contract proofs need the target's compiler, dependencies and test runner (often Foundry).

From a checkout of this downstream repository:

```sh
export GRIMOIRE_CODEX_ROOT="$(pwd -P)"
python3 scripts/validate.py
python3 scripts/install.py --project "$HOME"
cd /path/to/audit/target-checkout
export GRIMOIRE_AUDIT_ROOT="$(pwd -P)"
export GRIMOIRE_SESSION_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
python3 "$GRIMOIRE_CODEX_ROOT/scripts/review_artifacts.py" init
codex --sandbox workspace-write --ask-for-approval on-request
```

The target checkout must already exist and have its Git root at the launch directory. This review
setup links all 40 skill folders into `~/.agents/skills/`, so they are available when Codex starts
in an audit checkout. Existing unrelated skills are never overwritten. Project-level registration
is also available via `--project /path/to/engagement`; see the walkthrough's note about external
skill symlinks in source snapshots. Keep this toolkit checkout at a stable path. For
container/hosted sessions, copy the complete downstream checkout into the environment and install
there; links to your laptop cannot work remotely. Restart Codex if the skills do not appear.

In Codex, use `$summon`, `$cartography`, `$write-poc`, `$peer-review` or another skill below.
For example: **`Use $summon on the local in_scope_repo. Skip bounty acquisition.`**
Natural-language discovery remains enabled. Claude slash-command spellings in shared prose map to
`$skill-name`; they are not shell commands. Each skill first loads its Codex adapter and this
run's `grimoire-codex/<run-id>/GRIMOIRE.md`. Helpers use their installed absolute paths while retaining the
engagement/target working directory, as directed in `CODEX.md`.

For review work, pass `GRIMOIRE_AUDIT_ROOT` (the absolute Codex launch directory) and a stable
`GRIMOIRE_SESSION_ID` to helpers in each shell invocation. The audit root must never be broadened
after changing directories. Peer/mitigation copies and scratch files live in
`<target-git-root>/.isolated-codex/<run-id>/`, inside that launch directory. Claude keeps its separate
`.isolated/` tree; Codex excludes both trees from snapshots and requires matching runtime/run/root
ownership before reuse or cleanup. Global-store writes are unavailable during a confined audit.
Reports, findings mirrors, context and logs use `<target-git-root>/grimoire-codex/<run-id>/`;
PoCs use its `pocs/` subdirectory, outside shared test discovery. The guarded writer refuses
Claude's paths, other runs, symlinks and accidental file replacement. Private Foundry execution
uses owned copies, local build/cache/persistence paths, no automatic compiler installation and no
shared RPC cache. Raw evidence stays under the run's `runs/` directory. Existing Claude
`GRIMOIRE.md`, `grimoire/`, test files and working copies are left untouched.
Use a verified Codex thread ID when exposed, or generate a UUID once (`python3 -c 'import uuid; print(uuid.uuid4())'`)
and label it **run ID, not resumable chat ID**. Preserve it only for that logical session. Missing or
malformed IDs are refused by isolated-copy/status helpers. Do not fabricate a Codex chat ID.

Peer/mitigation review does not require personal-store bootstrap. Optional library/detector setup
with `scripts/bootstrap.py` belongs before an audit session; the default `~/.grimoire/` store may
already be shared with Claude. See the walkthrough before enabling those workflows.

A skills-only [Codex plugin manifest](.codex-plugin/plugin.json) is also supplied for environments
supporting local plugins; archive the **whole repository**, including `agents/` and `scripts/`.
Local CLI linking is the validated installation path. Hosted plugin upload/installation was not tested.
Do not install the archived Claude manifest or hooks from `vendor/`.

## Available skills

| Area | Skills |
|---|---|
| Engagement and research | `summon`, `grimoire-mode`, `cartography`, `review-cartography`, `gc-cartography`, `divine`, `delve`, `dig-mode`, `hunt-summary`, `annotation` |
| Hypotheses and findings | `write-hypothesis`, `validate-hypothesis`, `finding`, `finding-draft`, `finding-review`, `finding-dedup`, `findings-sync` |
| Proof and review | `write-poc`, `peer-review`, `mitigation-review` |
| Research wiki | `tome`, `tome-sync` |
| Detectors | `checks`, `scribe-distill`, `scribe-gc`, `scribe-utilities` |
| Libraries | `modify-library`, `librarian-index`, `librarian-library-search`, `librarian-clean-cache` |
| Agent procedures | `grimoire-familiar`, `grimoire-gnome`, `grimoire-hag`, `grimoire-librarian`, `grimoire-scribe`, `grimoire-sigil` |
| Downstream maintenance | `grimoire-gap-analysis`, `grimoire-execute-plan`, `grimoire-assess-process-improvements`, `grimoire-commit` |

All 30 upstream skills retain their workflow bodies, stages, references, scripts and output
conventions except for explicit compatibility patches. The additional ten entrypoints expose six
agent procedures and four maintenance commands. See the [compatibility assessment](docs/COMPATIBILITY.md)
and [inventory](docs/inventory.json) for inputs, outputs, stages and dependencies.

## Layout and ownership

```text
vendor/upstream/       exact tracked upstream snapshot; inert archive
skills/                generated Codex skill bodies and shared resources
agents/                generated Codex role procedures
.agents/skills/        native discovery links into skills/
codex/                 downstream-owned runtime/maintenance adapters and exact patches
scripts/               sync, validation, installation, PR and benchmark tools
.github/workflows/     downstream CI and scheduled/manual synchronization
benchmark/             schema, synthetic examples and collection demo
```

## Limits and verification

Claude lifecycle hooks become explicit bootstrap/context-load/triage instructions, not harness
hooks. Role skills are procedures; delegation must use real Codex subagents or a fresh session.
Mandatory independent review stops when no independent context is available. No self-review is
presented as an independent check. Role access lists are not Codex permission sandboxes.

Optional Context7/claudit MCP services must be configured separately in Codex. An inert
[configuration example](codex/mcp.example.toml) forwards environment keys without storing them;
merge it into an authorized Codex config and enable only the desired servers. This follows the
[official MCP configuration format](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). Node/npx
and service access are optional; the example was parsed but no live MCP server was started.
Tools are discovered
by service capability instead of assuming Claude namespaces. Without them, the Librarian uses
cited web/file fallback and reports coverage gaps. No service or key is installed automatically.

Pi's footer is archived only. Super Sigil and complete Semgrep/Slither/CodeQL workflows were already
unfinished upstream. Optional vector search, live bounty websites, MCP services and full model-driven
audits have not been end-to-end verified. Structural checks alone do not establish equivalence.

[SYNC.md](SYNC.md) covers one-way polling and PRs. [BENCHMARKING.md](BENCHMARKING.md) gives the first
comparison commands and independence controls. [CONTRIBUTING.md](CONTRIBUTING.md) defines ownership.
[docs/DELIVERY.md](docs/DELIVERY.md) records completed checks and remaining setup.
