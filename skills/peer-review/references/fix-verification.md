# Fix Verification

## The loop

1. **Copy** the files you'll change into this session's work folder (`isolated-workspace.sh work <id>`):
   `.isolated/<session-id>/work/<id>/a/` (original) and `.../b/` (patched). Check the repo copy equals `a/` before you start.
2. **Patch** `b/` with exact string replacements (assert each pattern matches exactly once).
3. **Run** `scripts/verify-fix.sh` with the PoC and the regression suites. It always runs in an
   isolated copy inside the workspace, so the workspace's own files and other sessions' runs are never
   affected:
   - the PoC's **bug assertions should now fail** (that is the bug being gone);
   - the PoC's control tests should still pass;
   - every other test should keep its result.
4. **Read** the changed-results list. Explain every unexpected change before claiming the fix works.
5. **Restore** (the script removes the copy) and confirm the workspace's touched paths still match
   HEAD. If they don't, another session changed them: leave them and say so.
6. **Show** the diff (from `a/` to `b/`) with clean `a/` and `b/` path prefixes.

When a PoC asserts the buggy state *before* measuring the outcome, a fixed run fails early and hides
the end result. Re-run a copy with that one assertion removed (back up and restore the PoC file).

## Interpreting changes

| Change | Meaning |
|---|---|
| PoC bug assertion now fails with the expected "correct" values | Fix works |
| PoC panics in its own arithmetic (`expected - actual` underflow) | Usually the fixed value landed on the other side of the expected one; print the values |
| An unrelated suite changes | Regression, or the suite encoded the buggy behaviour; read it |
| A suite fails only through a mock setter or a path the real code can't reach | Not a regression, but the fix relies on an invariant; document it |
| Fork suites fail before and after | Missing RPC env vars; exclude them from the comparison |
| Fork suites fail in only one run ("block not found", timeouts) | RPC flakiness, not the fix; re-run them |
| Many unrelated changes at once | Another session's patch leaked into one run; re-run in an isolated copy |

## Recurring fix patterns

- **Destructive cap → non-destructive cap.** If a value is overwritten with `min(stored, f(price))` on
  every update, a recovery followed by a drop loses information. Keep the stored value (the cost basis)
  and apply the cap where it is read.
- **Tracking in-flight state as if it were final.** A counter for "collected but not yet settled" is not a
  record of what was collected. Track the backed amount separately, reduce it only when the underlying
  obligation settles, and keep it in the unit the obligation is denominated in.
- **Mutate-then-checkpoint.** If an admin push sizes something from stored values, settle pending
  accounting first (call the regular update at the start of the setter).
- **Re-quote dependent amounts.** When a base amount is reduced (part paid from elsewhere), recompute
  every amount derived from it (token quantities, shares) before passing it on, rounding in favour of
  the protocol.
- **Same unit for both sides.** When a value is funded at one price and paid at another, record the
  funded amount at funding time and pay out pro rata to what was funded.
- **Cap at the source, not at the subtraction.** Saturating the final subtraction hides inconsistent
  state. Cap the quantity where it is computed, and say what happens to the remainder.
- **Validate on the same basis you enforce.** A setter that validates against a live value while the
  trigger uses a stored value needs one shared helper.

## Documenting a fix

- State the **invariant** the fix relies on (for example "every increase of X happens together with Y
  in the same transaction") and where it holds in the code today.
- Name the **other variants or implementations** that need the same change.
- Note **interactions**: fixes that must land together, and fixes that make another finding's local
  fix redundant.
- Prefer a separate mapping over adding a field to a struct exposed by a public getter (tests and
  integrators destructure the getter). Append new state after existing variables (proxy layout).
