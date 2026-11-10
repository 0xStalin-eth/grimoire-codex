# Grimoire-Codex

The canonical repository `https://github.com/0xStalin-eth/grimoire` and any local Claude checkout
are strictly read-only. Never write files, Git metadata, branches, commits, tags, PRs, settings,
workflows or credentials there. Verify the directory and remotes before repository operations.
Retrieve changes only into a separate temporary clone. Never push upstream.

Edit downstream adapters in `codex/`, tooling in `scripts/`, tests and documentation.
`vendor/upstream/`, `skills/`, `agents/` and `.agents/skills/` are managed by `scripts/sync.py`;
never hand-edit them. The upstream human specifications are also immutable.
For an adapted source change, inspect the full diff and update exact reviewed patches explicitly;
do not regenerate source hashes without review or weaken verification to pass synchronization.

Run `python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v` after substantive
changes. Structural checks do not prove runtime compatibility. Report exactly what executed.
Keep examples protocol-agnostic. Never put target checkouts, real audit findings or secrets here.
Audit skills write into the engagement workspace; follow each skill's `CODEX.md` execution adapter.
Publishing code or changing remote settings requires explicit user confirmation.
