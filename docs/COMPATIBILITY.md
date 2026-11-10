# Discovery and compatibility assessment

Inspected before implementation: upstream `0xStalin-eth/grimoire`, default branch `master`, commit
`4cfded991acfe02375335e5bc8f9bd3a52c5df38`. Inspection used a separate temporary clone.
The existing Claude checkout was read only (including Git metadata); its remote `origin` points at
JoranHonig while `fork` points at 0xStalin-eth. It was clean at the same commit.

## Inventory

30 implemented skills (all inventoried below), six implemented agents (`familiar`, `gnome`, `hag`,
`librarian`, `scribe`, `sigil`), four maintenance commands (`commit`, `gap-analysis`, `execute-plan`,
`assess-process-improvements`), three hook commands (personal store init, GRIMOIRE context load,
sigil-return triage), one Claude plugin manifest with optional claudit/Context7 MCP servers, and a
Pi footer extension. No upstream GitHub Actions workflows or conventional test runner. The init hook
has a shell integration test. Human specifications are in `grimoire/` and contain Obsidian links.
Machine-readable per-skill stages and resources: [inventory.json](inventory.json).

| Skill | Compatibility and expected artifacts |
|---|---|
| `annotation` | Discovery script → JSON/table; Python Fire required; optional tree-sitter. |
| `cartography` | Shared methodology → grimoire/cartography/*.md and index. |
| `checks` | Shared checks format + delegated detection → spells/checks and triaged findings. |
| `delve` | Session adapter → delves/<session-id>/board.md, leads and hypotheses. |
| `dig-mode` | Shared conversational workflow → concise source-backed answers. |
| `divine` | Shared rationale investigation → calibrated answer and durable tomes. |
| `finding` | Shared schema, severity, examples and validators → finding guidance. |
| `finding-dedup` | Shared root-cause review → user-approved merge/archive actions. |
| `finding-draft` | Shared stages + validator → findings/WIP/*.md. |
| `finding-review` | Shared quality review → review and approved revisions. |
| `findings-sync` | GitHub CLI read access → originals and versioned local issue mirror. |
| `gc-cartography` | Shared overlap/merge scripts → approved consolidated flows. |
| `grimoire-mode` | Six agent procedures + shared principles → research orchestration. |
| `hunt-summary` | Visible session context only → hunt-summary-<datetime>.md. |
| `librarian-clean-cache` | Shared user-confirmed cache maintenance → reclaimed cache space. |
| `librarian-index` | uv + Fire, PyYAML, Qdrant/FastEmbed → local vector index. |
| `librarian-library-search` | Same embedding environment → cited JSON search results. |
| `mitigation-review` | Session + agent adapters; gh, git, project test runner → pre/post-fix proofs and verdict. |
| `modify-library` | Shared library registry operations → libraries.yaml and local clones/links. |
| `peer-review` | Session-isolated copies + project test runner → proof and review verdict. |
| `review-cartography` | Shared scripts → verified flows, overlap report. |
| `scribe-distill` | Gnome/Scribe procedures → checks or knowledge artifacts; static module types remain limited upstream. |
| `scribe-gc` | Shared user-approved merges → deduplicated spellbook. |
| `scribe-utilities` | Shared read-only queries → detector inventory. |
| `summon` | Explicit bootstrap/context/triage replacing hooks + session adapter → full workspace and GRIMOIRE.md. |
| `tome` | Shared evidence model → tomes, provenance, owner/copy links. |
| `tome-sync` | Session adapter → approved drift repairs and session history. |
| `validate-hypothesis` | Session adapter + independent Familiar → PoC, verdict and confirmed filing. |
| `write-hypothesis` | Session adapter → hypotheses/WIP/*.md and status row. |
| `write-poc` | Shared numbered workflow → reproducible benign PoC and validation. |

## Blockers and adaptation decisions

- No assumption that Claude tool allowlists, slash commands, hooks or plugin manifests are executable
  in Codex. Remove Claude-only frontmatter; keep name/description. Slash invocations become `$skill`
  examples. Keep every workflow stage and confirmation gate.
- Claude's session environment variable is unavailable. Use an explicit `GRIMOIRE_SESSION_ID`,
  preferably the verified Codex thread ID; an operator-created UUID is allowed as a run identifier
  but must never be represented as a resumable Codex chat. No fabricated thread IDs.
- Preserve isolated-copy containment and ownership checks. Native delegation uses Codex subagents
  when available. Independent review must stop if no independent execution context is available;
  a same-context self-review is not equivalent. No 250-agent fanout: bounded batches preserve work.
- Hook init becomes an explicit local bootstrap; GRIMOIRE is read at skill entry; sigil triage is an
  explicit mandatory handoff. This is instruction-enforced, not a harness lifecycle guarantee.
- Optional MCP services must be configured separately in Codex; discover actual exposed tools by
  capability rather than retaining Claude's namespace. Fall back to cited web/file research and
  disclose missing coverage. No Claude CLI or plugin installation required.
- Shared bash/Python helpers remain intact unless an explicit reviewed patch is necessary. `uv` is
  not guaranteed; annotation needs Fire; semantic search may download a model. Foundry, Semgrep,
  Slither and other project tools are optional and cannot be inferred from structural checks.
- Pi footer is a Pi runtime UI extension, not a security workflow; retain as archival upstream
  content only. Super Sigil and complete Semgrep/Slither/CodeQL integrations were already unimplemented.
- Maintenance commands must operate on the downstream only. Canonical snapshots/specifications are
  read-only. Replace upstream implementation paths with downstream ownership boundaries.

## Chosen architecture

`vendor/upstream/`: exact tracked upstream files and modes, inert archive (no upstream hooks run).
`skills/` and `agents/`: reproducibly generated Codex runtime files.
`.agents/skills/<name>`: native discovery symlinks to generated skills.
`codex/`: owned adapters, exact per-file patches and reviewed source hashes.
`scripts/`, `.github/`, docs and benchmark tooling: downstream owned.
A content manifest detects edits in managed trees before sync. Unknown platform-specific changes,
new entrypoints and modified patched sources fail with file-specific conflicts before writes.
Plain shared assets synchronize automatically. A downstream schedule polls upstream and opens or
updates one PR; it never merges or writes upstream. No arbitrary prompt-based rewriting.

## Official specifications checked

- [Skills and discovery](https://learn.chatgpt.com/docs/build-skills): required name/description,
  `.agents/skills/`, `$skill` CLI invocation and supported symlinked skill folders.
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md): project instructions,
  discovery precedence and limits.
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): delegation is
  capability dependent; custom agents and permissions differ by client/version.
- [GitHub token permissions](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).

Checked 2026-11-09. These establish packaging and adaptation choices, not successful model execution.
