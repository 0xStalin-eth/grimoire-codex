# Reviewed patch rationale

`patches.json` is executable configuration: each key identifies an exact upstream file, its
SHA-256 and counted literal edits. Every adaptation is explicit and inspectable. The generator adds
shared adapters and normalizes metadata separately; it does not run a free-form conversion model.

| Files | Compatibility reason |
|---|---|
| Session-aware skill bodies, parallel-session reference, isolated-workspace and status helpers | Replace the unavailable Claude environment ID with explicit `GRIMOIRE_SESSION_ID`; distinguish run IDs from verified resumable Codex thread IDs. Preserve copy ownership, containment and refusal rules. |
| Peer-review isolation helper, both workspace guards and review references | Use `.isolated-codex/<run-id>/` separately from Claude; exclude both trees from copies, check runtime/run/Git-root/launch-root ownership, refuse symlinks and preserve unknown/legacy copies. Disable optional Git metadata refreshes (including in linked checkouts). Require `GRIMOIRE_AUDIT_ROOT` before review output/scratch writes; refuse a Git root above the launch directory. |
| Skill/role output paths, templates and context references | Route Codex reports, mirrors, logs, context and PoCs to `grimoire-codex/<run-id>/`. Shared Claude files are explicit read-only inputs. The common adapter requires the owned artifact writer/mover and private test runner; no migration or automatic overwrite is allowed. Personal-store paths remain separate and unavailable for audit writes. |
| Extraction, snapshot, mirror, status and fix-verification helpers | Apply output ownership checks before writing; refuse Claude paths, other runs, symlinks and canonical Claude repository remotes. Preserve existing reports and raw verification evidence. Private PoCs are included explicitly even when ignored by Git; reports and other runs' PoCs are excluded from copies. Foundry selects private PoCs while regression suites retain normal discovery, with local output/cache/persistence, offline compiler resolution and disabled shared RPC caching. |
| `summon/scripts/session-status.sh` | Fix inherited lock ownership: an existing directory is not evidence this process acquired the lock. Validate run ID format to prevent malformed log rows; logs must belong to this run's private report directory. |
| `annotation/scripts/find-annotations.py` | Declare Python Fire via PEP 723 so the documented `uv run` entrypoint can install its required dependency in an isolated script environment. Tree-sitter stays optional. |
| Librarian procedure and semantic-search skill text | Resolve tools by configured service capability, remove Claude namespaces, explicitly require optional `uv`, and state the initial embedding-model download. Codex exposes the search skill explicitly as well as through the Librarian. |
| Summon and bounty-platform reference | Use available Codex web retrieval instead of Claude-specific tool names; missing web access still requires supplied scope, never invented scope. |
| Mitigation-review and hypothesis-validation bodies | Route role names through Codex procedures and make cross-skill references unambiguous. All independent review and pre/post-fix verification stages remain. |
| Four maintenance commands | Replace Claude product/model/path references, cap fanout through the maintenance adapter and bind every mutation to downstream ownership. Preserve catalog, study, design, build, review, confirmation and commit stages. The maintenance adapter replaces inherited pnpm checks with the actual Python checks and prevents broad staging. |

Unknown metadata, newly added/removed entrypoints, incompatible platform instructions, source-hash
changes in patched files and collisions fail rather than being guessed. Review the upstream diff
before changing any source hash. No shared security standard was weakened or workflow stage removed.
