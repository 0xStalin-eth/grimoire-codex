# Grimoire for Codex

Independent Codex execution of [Grimoire](https://github.com/0xStalin-eth/grimoire) security research
workflows. Grimoire remains the canonical source. This downstream repository owns all Codex
adaptation and polling automation. **The original repository requires zero changes and is never
written by this project's tools.** Upstream MIT attribution is retained in [LICENSE.md](LICENSE.md).

Initial port baseline: `4cfded991acfe02375335e5bc8f9bd3a52c5df38` (`master`). The current authoritative
revision and content hashes are in [sync-state.json](sync-state.json).

## Start using the skills

Requires Python 3.10+, Git and Bash. No Claude runtime or CLI is needed. Optional dependencies are
listed by `python3 scripts/doctor.py`. GitHub issue workflows need `gh`/`jq`; annotations use `uv`
and Fire; semantic library search uses `uv`, Qdrant/FastEmbed and an initial model download.
Smart-contract proofs need the target's compiler, dependencies and test runner (often Foundry).

From a checkout of this downstream repository:

```sh
python3 scripts/validate.py
python3 scripts/install.py --project /path/to/engagement
python3 scripts/bootstrap.py
codex --cd /path/to/engagement
```

The engagement directory must already exist. Keep the scoped code repository inside it, as
`summon` expects. Installation links all 40 skill folders into `<engagement>/.agents/skills/`;
existing unrelated skills are never overwritten. Keep this checkout at a stable path. For
container/hosted sessions, copy the complete downstream checkout into the environment and install
there; links to your laptop cannot work remotely. Restart Codex if the skills do not appear.

In Codex, use `$summon`, `$cartography`, `$write-poc`, `$peer-review` or another skill below.
For example: **`Use $summon on the local in_scope_repo. Skip bounty acquisition.`**
Natural-language discovery remains enabled. Claude slash-command spellings in shared prose map to
`$skill-name`; they are not shell commands. Each skill first loads its Codex adapter and the
engagement's `GRIMOIRE.md`. Helpers use their installed absolute paths while retaining the
engagement/target working directory, as directed in `CODEX.md`.

For session-aware work set a stable `GRIMOIRE_SESSION_ID` in each shell invocation. Use a verified
Codex thread ID when exposed, or generate a UUID once (`python3 -c 'import uuid; print(uuid.uuid4())'`)
and label it **run ID, not resumable chat ID**. Preserve it only for that logical session. Missing or
malformed IDs are refused by isolated-copy/status helpers. Do not fabricate a Codex chat ID.

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
