# Downstream maintenance boundary

Apply this adapter before the preserved maintenance procedure.

Verify the current repository is Grimoire-Codex using its `codex/project.json` marker and remotes.
Never operate on an upstream checkout. In the procedure, specifications mean
`vendor/upstream/grimoire/`; upstream implementations for comparison mean
`vendor/upstream/skills/` and `vendor/upstream/agents/`. Both are read-only.
Implementation changes go in `codex/` adapters/patches, `scripts/`, tests and downstream docs.
`skills/`, `agents/` and `.agents/skills/` are generated: change the adapter, then regenerate.
`CLAUDE.md` guidance maps to downstream `AGENTS.md`; command changes belong in downstream
maintenance adapters. Plugin configuration maps to the downstream Codex execution adapter.
Keep `IMPLEMENTATION_PLAN.md` downstream only.

Use Codex subagents with inherited model settings in place of Opus/Sonnet or a named
`skill-reviewer` type. Preserve separate spec-study, design, build, skill-review and compliance
stages. Batch catalog/analysis work within available concurrency; the 250-agent fanout is not a
Codex requirement. Give agents their procedure and required read/search capabilities rather than
attempting to grant Claude tool names. If independent review is unavailable, save the pending
review handoff rather than claiming completion.

For commit, replace the inherited pnpm checks with this repository's actual checks:
`python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v`.
Review the diff and stage explicit authorized paths; never automatically stage audit targets,
secrets or unrelated user work. Do not bypass checks to make a commit pass. Never push as part of
these maintenance procedures. Persist durable process lessons in downstream `AGENTS.md` or
`codex/` instructions, not Claude memory or an upstream file.
