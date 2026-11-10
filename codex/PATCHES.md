# Reviewed patch rationale

`patches.json` is executable configuration: each key identifies an exact upstream file, its
SHA-256 and counted literal edits. It is intentionally small and inspectable. The generator adds
shared adapters and normalizes metadata separately; it does not run a free-form conversion model.

| Files | Compatibility reason |
|---|---|
| Session-aware skill bodies, parallel-session reference, isolated-workspace and status helpers | Replace the unavailable Claude environment ID with explicit `GRIMOIRE_SESSION_ID`; distinguish run IDs from verified resumable Codex thread IDs. Preserve copy ownership, containment and refusal rules. |
| `summon/scripts/session-status.sh` | Fix inherited lock ownership: an existing directory is not evidence this process acquired the lock. Validate run ID format to prevent malformed log rows. |
| `annotation/scripts/find-annotations.py` | Declare Python Fire via PEP 723 so the documented `uv run` entrypoint can install its required dependency in an isolated script environment. Tree-sitter stays optional. |
| Librarian procedure and semantic-search skill text | Resolve tools by configured service capability, remove Claude namespaces, explicitly require optional `uv`, and state the initial embedding-model download. Codex exposes the search skill explicitly as well as through the Librarian. |
| Summon and bounty-platform reference | Use available Codex web retrieval instead of Claude-specific tool names; missing web access still requires supplied scope, never invented scope. |
| Mitigation-review and hypothesis-validation bodies | Route role names through Codex procedures and make cross-skill references unambiguous. All independent review and pre/post-fix verification stages remain. |
| Four maintenance commands | Replace Claude product/model/path references, cap fanout through the maintenance adapter and bind every mutation to downstream ownership. Preserve catalog, study, design, build, review, confirmation and commit stages. The maintenance adapter replaces inherited pnpm checks with the actual Python checks and prevents broad staging. |

Unknown metadata, newly added/removed entrypoints, incompatible platform instructions, source-hash
changes in patched files and collisions fail rather than being guessed. Review the upstream diff
before changing any source hash. No shared security standard was weakened or workflow stage removed.
