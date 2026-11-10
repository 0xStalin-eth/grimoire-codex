# Parallel Sessions on One Repo

**These rules apply on every review, even when you are the only session.** Another session can start
in the same checkout at any time, and you can't see it coming. Working the same way every time is also
what makes a single-session review safe to run alongside the next one.

Several sessions often review findings side by side in the same checkout: one per issue, each
reproducing, probing and verifying fixes. A file one session swaps in for a fix run is live for every
other session's `forge test` in that window. A run that overlaps someone else's swap measures their
patch, not the original code, and a restore can wipe out their patch or put back a stale file.

## Rules

0. **Stay inside the workspace.** Every file a review reads or writes, and every command it runs, stays
   inside the git workspace the session runs in. That covers inputs, copies, patched files, builds and
   scratch output. **Other workspaces are off limits even when they belong to the same engagement**, such
   as sibling checkouts that share one git directory (a manual-audit checkout, a fixes checkout, a report
   checkout). Nothing goes in a parent folder, the system temp folder, or a `git worktree`, which
   registers itself in the git directory, often above the workspace. The scripts enforce this with
   `_workspace-guard.sh`:
   - every path they read or write is resolved with symlinks followed and refused unless it lands inside
     the workspace;
   - the isolated copy refuses dependency folders or symlinks that lead outside, and writes only inside
     `<workspace>/.isolated/<session-id>/`.

   If an input lives in another checkout (a report, a finding mirror), copy it into this workspace first.
   git itself reads the shared object store, and only for this workspace's commits.
1. **The shared checkout is read-mostly.** Write only new, untracked files there: your PoCs, probes,
   write-ups. Never swap or edit tracked source files in it, not even briefly and not even when you think
   you are alone.
2. **Patch and verify in your own isolated copy.** `verify-fix.sh` always does this. For manual patch
   probes, create one with `scripts/isolated-workspace.sh create i<N>` and work in the folder that
   `isolated-workspace.sh path i<N>` prints (`.isolated/<session-id>/i<N>/`). It holds every tracked and
   untracked file of the workspace, so your PoCs are present. Keep it until the user closes the lead
   (rule 9).
   - **Prove the copy is identical before using it.** `create` and `sync` compare the copy and the
     workspace byte for byte: every tracked and untracked, non-ignored file, plus the dependency
     symlinks. Any difference stops the run. `create` then removes the copy and lists the cause, and
     `verify-fix.sh` runs the same comparison again at the end to show whether the workspace changed
     mid-run. Run `isolated-workspace.sh verify i<N>` yourself before quoting any figure from a manual
     probe. A baseline that differs from the workspace's code is not a baseline.
3. **Take write-up output from a clean run.** PoC output embedded in a write-up must come from a
   run on unmodified code: the isolated copy, or the workspace after confirming that `git status`
   shows no tracked changes under the source folders and no other `forge` process is running.
4. **Check before you trust a run in the workspace itself.** Before and after it, run
   `git status --short` on the source folders and `pgrep -fl 'forge (test|build)'`. If tracked files
   changed during the run, or another forge process overlapped it, run it again in your isolated copy.
5. **Never revert what isn't yours.** If you find tracked source files modified in the workspace and
   you didn't change them, leave them. Say so to the user, and report your results from your isolated
   copy. Restoring them can destroy another session's work in progress.
6. **Tell the other session when you touched a shared file.** If you swapped a shared file, even briefly,
   message the sessions that may have run tests in that window (`ListAgents`, then `SendMessage`).
   Say which files changed and for how long, and that the files are back at HEAD. When you receive such a
   message, check its claims (`git status`, compare with HEAD), re-run anything that overlapped, and reply
   saying what you re-ran and whether results changed.
7. **One work folder per finding, inside your session folder.** Use `isolated-workspace.sh work i<N>`,
   which creates and prints `.isolated/<session-id>/work/i<N>/`:
   - `a/` for the originals and `b/` for the patched copies;
   - the diff;
   - a backup of any PoC you rewrite.

   Probes that compile only against a patch go in that work folder, not the PoC folder. In the shared
   PoC folder they break every other session's build.
8. **Never use `git stash` in a shared repo.** The stash stack is shared across checkouts. To set work
   aside, copy the files into your work folder.
9. **One session, one folder; never touch another session's.** Copies and work folders live under
   `.isolated/$CLAUDE_CODE_SESSION_ID/`, and the scripts refuse to run without that id. `claude --resume`
   keeps the id, so a resumed session finds its copies; `--fork-session` starts a new id and an empty
   folder. Never read results from, run in, or remove another session's folder, even one that looks
   abandoned: list them with `isolated-workspace.sh list` and leave the clean-up to the user.
   Keep your own copies until the user explicitly closes the lead they serve (accepted or discarded); only
   then run `isolated-workspace.sh remove <name>`.

## Isolated copy notes

- **Location:** `<workspace>/.isolated/<session-id>/<name>/`, with an `.owner` file naming the session.
  Names resolve only inside the current session's folder (no `/` or `..`), and `remove` also checks
  `.owner` and that the target is a copy the script made. The script writes `.isolated/.gitignore` with
  `*`, so the folder never shows in `git status`, is never copied into another session's copy, and is
  outside the folders forge and Hardhat compile from the workspace root. `work` is a reserved name for
  the work folders. Copies made before per-session folders (`.isolated/<name>/`) show in `list` as
  legacy and are never touched by the script.
- **Dependencies:** `lib/` and `node_modules/` are symlinks to the workspace's own folders. Copying them
  is slow, and they are compared by checking where the links point. `remove` deletes the links, never
  what they point to.
- **Untracked files:** all untracked, non-ignored files are copied, not only the PoC files. PoCs import
  helpers (`utils/`, mocks) that are also untracked, and a missing helper fails the whole build.
- **Uncommitted edits to tracked files** in the workspace stop `create` and `sync`. Find out whose they
  are. If they are code you mean to test against (your own intended edits), re-run with
  `--with-modified`, which copies them as they are and proves the copy identical. If they are another
  session's temporary patch, wait until the workspace is back at HEAD. Never guess.
- **Refresh, don't recreate.** After editing a PoC in the workspace, run `sync`. It mirrors the
  workspace again (deleting extra files and discarding edits made in the copy) and re-verifies.
  Recreating the copy costs a full rebuild.
- **Other commits** (mitigation reviews): `create <name> --ref <commit>` extracts that commit's files with
  `git archive` into the copy, then adds the untracked files. The comparison is skipped and says so.
- **What the comparison skips:** files the workspace ignores (build output, caches) and anything under the
  symlinked dependency folders. It reports any submodule outside them as not compared.
- **Clean up:** `isolated-workspace.sh remove <name>`, only once the user has closed the lead. See what
  is alive, per session, with `isolated-workspace.sh list`.

## Comparing results

- **Key every result by suite and test** (`forge test --json`). Text output repeats failing tests in a
  summary at the end. Tests with the same name in different suites also merge when you sort text lines.
- **Record the baseline failure count.** Old probes that fail on purpose show up as failures in both
  runs; only *changes* matter.
- **Separate infrastructure failures from results.** Fork suites can fail on one run and pass on the
  next ("block not found", RPC timeouts). Re-run them, or exclude fork suites, before calling a change a
  regression.
- **Spot-check one run in the workspace itself.** Run the PoC once there on clean code and compare figures
  and gas with the isolated run. If they are identical, the two environments agree.
