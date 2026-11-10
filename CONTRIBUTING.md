# Contributing

This project and its automation must **never modify the original Claude repository**, locally or
remotely. No upstream files, Git metadata, branches, commits, tags, PRs, workflows, settings, Apps
or secrets may be changed by this project's tools. Verify the current directory and remotes before
repository operations. Use a separate temporary clone for read-only inspection.

The repository owner may separately choose to maintain shared methodology in the canonical project;
that independent owner activity is outside this downstream project's authorization. Propose shared
methodology improvements to the owner as text. Do not implement or submit them upstream here.

- Shared workflow logic, evidence standards, security methodology, references and deterministic
  helpers originate upstream and are mirrored into `vendor/upstream/`.
- Codex execution rules and platform differences belong in `codex/runtime.md` or
  `codex/maintenance.md`. Minimal required source edits belong in `codex/patches.json` with exact
  reviewed source hashes/counts. Keep confirmation gates and independent verification.
- Downstream tooling, CI, tests, benchmarking and documentation are maintained here.
- Do not edit generated `skills/`, `agents/`, discovery links or the vendor snapshot by hand.
  Add a new Codex-only skill through the downstream generator/adapter with a test and a distinct
  name; never hide an upstream skill by colliding with a generated name.

For upstream revisions that change an adapted file, inspect its full old/new diff first. Update the
patch deliberately, retain its rationale, regenerate and run:

```sh
python3 scripts/sync.py --source /path/to/separate/upstream-clone
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Do not treat structural passing results as proof of model behavior. State the tested workflow,
fixture, runtime, tool availability and limits. Run live services or paid model evaluations only
within the authorized scope. No benchmark target codebases, confidential findings or credentials
belong in this repository. Use synthetic examples and keep real runs outside the checkout.

A PR should explain the concrete compatibility problem, resulting behavior, verification performed
and material behavioral differences. Publish downstream code and change remote settings only after
explicit user confirmation. Never auto-merge synchronization PRs.
