# One-way synchronization

Everything runs in **grimoire-codex**. The upstream repository, its local working tree and Git
metadata, GitHub settings and history are never modified. It requires no workflow, webhook,
secret, App, token, configuration or knowledge of this downstream repository.

## Ownership and transformations

| Paths | Owner | Sync behavior |
|---|---|---|
| `vendor/upstream/**` | upstream snapshot | Exact tracked Git blobs, modes and safe internal resource links |
| `skills/**`, `agents/**`, `.agents/skills/*` | generated | Derived from snapshot + explicit downstream adapters |
| `codex/**` | downstream | Preserved; runtime instructions, maintenance boundary, reviewed inventory and exact patches |
| scripts, tests, workflows, docs, benchmark | downstream | Preserved |
| `sync-state.json` | generated | Upstream SHA and complete hash/mode manifest |

The reader uses `git ls-tree` and `git cat-file` against the committed revision, never an upstream
working tree or Git attributes export filters. It never runs upstream hooks, installers or workflows.
A fresh temporary clone is used for network synchronization. All generation occurs downstream.
New/removed/renamed skill or command entrypoints require explicit inventory review. Ordinary asset
additions, deletions and renames propagate, including removing obsolete generated copies.

Metadata conversion only parses the known frontmatter shape and emits Codex `name`/`description`.
Placeholder angle brackets are removed from descriptions to satisfy the skill validator; workflow
bodies retain their placeholders. New metadata fails instead of guessing its meaning. Per-file edits in `codex/patches.json`
contain the exact source SHA-256, literal old/new text and required occurrence count. This is an
explicit reviewed patch set, not a general Markdown rewrite engine. Each skill gets the shared
Codex execution adapter. Six roles and four maintenance commands become additional skill entrypoints.

Before any write, compare all managed files and discovery links to the previous manifest.
Hand edits, extra files, missing files, changed permissions or altered symlinks cause a conflict.
Keep custom instructions in `codex/`; a changed runtime adapter regenerates its copies without being
overwritten. Generated files are not customization points. The manifest is an integrity/drift check,
not a signature against a malicious maintainer changing both content and hashes.

## Run locally

From the downstream checkout:

```sh
python3 scripts/sync.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Or use a separate existing upstream clone, read-only at its tracked `HEAD`:

```sh
python3 scripts/sync.py --source /path/to/separate/upstream-clone
python3 scripts/sync.py --source /path/to/separate/upstream-clone --check
```

The source must not be nested in or contain the downstream directory. No local fetch or checkout
is performed in an existing source clone, and uncommitted source files are not imported.
`--check` verifies the pinned generated result without writes. A normal no-op run leaves the
manifest and generated file contents untouched. The local `.sync.lock/` prevents competing runs.
A summary can be saved with `--summary sync-summary.json` inside a downstream-owned path; keep it
untracked or remove it before publication. The regular JSON stdout also identifies changed/deleted
paths and both upstream revisions.

## GitHub Actions

[Sync workflow](.github/workflows/sync.yml) polls every six hours at minute 23 UTC and supports
`workflow_dispatch`. It always starts from the downstream default branch. It retrieves the current
upstream default branch, generates, validates and runs tests. If successful and changed, it opens
or updates **one** PR from `automation/sync-upstream` to the downstream default branch.
It never merges the PR. The commit and PR identify the exact upstream SHA and changed-file summary.
Concurrent scheduled/manual runs are serialized. GitHub schedules are best-effort; this is polling,
not an immediate push trigger. Public repository schedules can be disabled after inactivity.

Manual trigger after publishing the downstream:

```sh
gh workflow run sync.yml --repo 0xStalin-eth/grimoire-codex
gh run list --repo 0xStalin-eth/grimoire-codex --workflow sync.yml
```

The publication script hardcodes and verifies the downstream repository and origin. It refuses
non-managed working-tree changes. It will not overwrite human commits or non-managed changes on
the sync branch. Updating the bot-only branch uses an exact `--force-with-lease` to detect remote
changes; no other branch is rewritten. A default-branch change during generation requires a retry.
An existing PR with the same generated tree is left unchanged.

## Permissions and initial configuration

Only the downstream owner needs to:

1. Publish this checkout into `0xStalin-eth/grimoire-codex` and enable Actions there.
2. Allow GitHub Actions to create pull requests in that repository (organization policy may also
   govern this). The normal CI has `contents: read`. The sync job requests only `contents: write`
   and `pull-requests: write`; checkout does not persist credentials.
3. Decide how to trigger checks on bot-created PRs. By default, publication uses the repository's
   `GITHUB_TOKEN`, which needs no secret and has no upstream write permission. GitHub suppresses push-triggered workflows from this token; current GitHub documentation says
   opened/synchronize/reopened PR checks enter an approval-required state. Approve those workflows
   in the PR merge-box banner. The sync job also runs validation/tests **before** publication.
   An alternative manual check is:

   ```sh
   gh workflow run ci.yml --repo 0xStalin-eth/grimoire-codex --ref automation/sync-upstream
   ```

   For automatic PR-triggered CI, set the optional downstream secret `SYNC_PR_TOKEN` to a
   fine-grained token restricted to **grimoire-codex only**, with Contents and Pull requests
   read/write (Metadata read is implicit). No upstream access is needed. A GitHub App installation
   token with the same downstream-only permissions is an alternative if provisioned externally.
   This project does not install an App. Organization restrictions may still apply.
4. Optionally require the `Validate / validate` check and a human review before merge. This project
   does not change branch protection, repository settings or auto-merge configuration.

Do not place tokens in files, logs or PR bodies. For private upstream forks, read access would need
separate downstream-side authentication; this implementation targets the supplied public upstream.
No secret is sent to it. The upstream fetch uses no write credential.

## Conflicts and failures

- **Managed content conflict:** inspect your local change. Move intentional Codex customization
  into an adapter, or explicitly restore the generated file from the reviewed downstream commit.
  Never reset unrelated work or “fix” this by editing the manifest alone.
- **Adaptation conflict:** sync fails before modifying managed content and names the changed
  patched source. Inspect the upstream diff in a temporary clone, revise literal patches and their
  source hashes, run sync and all checks, and submit a downstream PR. Never update review hashes
  blindly. The changed upstream commit remains available; it is not discarded or overwritten.
- **New/removed skill or unknown metadata:** review compatibility and update `codex/reviewed.json`
  deliberately. Removal of a patched file also requires removing/replacing its obsolete patch.
- **Unresolved platform instruction/broken resource:** adapt it downstream and add a regression
  test. Failed generation/validation does not open a normal sync PR or push an incompatible tree;
  the failed Actions run is the conflict report requiring manual resolution. A PR cannot silently
  bypass local generation or CI validation.
- **Stale `.sync.lock/`:** verify no sync process is active before removing only that lock directory.
- **PR denied:** check downstream Actions PR policy/token permissions. Local generation is still
  usable. **Human work on bot branch:** preserve it in a manual branch/PR before retrying.
- **No scheduled runs:** workflow must be on the default branch and enabled; check inactivity,
  account limits and GitHub scheduling delays.

Publication and GitHub-hosted execution are pending until the owner approves publishing and configures
the downstream. No live PR or hosted CI result is claimed by the local tests.

Official behavior: [GitHub token authentication](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token),
[triggering workflows](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow),
[inactive schedules](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows).
