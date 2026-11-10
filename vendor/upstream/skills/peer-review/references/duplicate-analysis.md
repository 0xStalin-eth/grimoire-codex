# Duplicate Analysis

## The test

Two findings are **duplicates** when both hold:
1. **Same root cause**: the same wrong assumption or missing step, not merely the same function.
2. **Same fix**: one change closes both.

**A symptom of another finding's root cause is a duplicate too**, even when its impact, trigger or
affected state differs. If the finding under review only shows a consequence of the bug the other
finding already names (the other finding's fix removes it because it removes the cause), it is a
duplicate of that finding. Keep the finding that names the root; move the symptom's extra impact into
an additional-impact comment on it. A finding whose bug survives the other fix, even in a smaller
form, is not a symptom: test it by applying the other fix and running this finding's PoC.

Everything else is **related**: same function, same symptom, same theme, opposite directions of the
same tracker, or two bugs whose fixes touch the same lines. Related findings get a cross-reference,
and often a note that their fixes must land together.

## How to check

For each candidate (from the duplicates index, a grep of the mirror for the same `file:line`, and the
findings that mention the same state variables):

1. Write each root cause in one sentence. If the sentences differ in *what is wrong*, not just *where*,
   they are probably distinct.
2. Ask what each fix does to the other finding's PoC. When cheap, run it: apply fix A, run PoC B.
3. Check direction. A tracker that is wrong **too high** in one finding and **too low** in the other is
   two bugs, even on the same variable.
4. Check triggers. "Fee or loss writes down X" and "price path writes down X" are different triggers;
   if the fixes differ, they are different findings.

## Symptom vs root

A finding is a **symptom** of another when it is a consequence of the other's root cause, so the
other's fix removes it. Symptoms are duplicates (see the test above). Example pattern: a protected
bucket that never absorbs losses can show up as a revert in one state, an inflated claim in another, a
blocked price update in a third, and a failing payout in a fourth. One change (writing the bucket down
when nothing backs it) closes all four. Present those as a cluster:

| Condition | Symptom | Finding |
|---|---|---|
| state A | revert | #a |
| state B | inflated claim | #b |
| ... | ... | ... |

Then name the single fix and say which local fixes become defence in depth.

## Resolved by another finding's fix

Always consider this verdict, even when no candidate passes the duplicate test. A finding is
**resolved by another finding's fix** when that fix removes its precondition or impact, even if the
roots differ and the fixes close in one direction only. Example pattern: finding B says "path X
ignores the reservation that path Y applies", and finding A's fix makes that reservation always zero.
B's own fix would not close A, but after A's fix B has nothing left to bypass.

Being resolved by another fix is not a reason to close the issue. A finding with its own root stays
open as its own report entry, and the resolution points at the shared fix ("fixed in <commit>, the fix
for #A"). Close an issue only when it is a duplicate: same root and one fix closes both, or a symptom of the
other finding's root cause.

1. For each related finding, find its fix. Prefer the client's actual commit (linked in the issue's
   comments, or the "Client: Proposed Fix" label) over the finding's suggested diff.
2. Apply it to the audited code in an isolated copy inside the workspace, always
   (`scripts/verify-fix.sh`, or `scripts/isolated-workspace.sh` for manual runs; see
   `parallel-sessions.md`). When hunks don't apply because the trees diverged, adapt them and say which.
3. Run the reviewed finding's PoC and the regression suite before and after. Note which assertion
   now fails; it shows *where* the scenario breaks.
4. Check in code that the precondition cannot come back (every path that creates it is now covered),
   not only that this PoC stops.
5. If both hold and the roots differ, recommend keeping the issue open with a comment that the other
   finding's fix also resolves it: name the commit, give the PoC result with it applied, and say why
   the precondition is gone. Recommend closing only for a duplicate, symptoms included (above).
   Either way, say what is left of the scenario and where it is tracked (another finding, a documented
   runbook), and which neighbours stay open.

Report the strict duplicate result separately, and present the outcome as a suggestion with the
evidence. If the other fix is only proposed, not merged, say the resolution depends on it landing as
tested.

## The user's own findings

Always check whether the finding under review duplicates something the user filed, drafted, or is
about to submit:
- **The user filed later with the same root**: the user's issue will be closed as a duplicate. Move
  its extra impact (a stronger scenario, a cross-instance effect) into an additional-impact comment on
  the earlier issue, close the user's issue, and add the user as co-assignee.
- **The user has an unsubmitted draft**: don't submit it separately. Use it to rewrite or extend the
  filed finding, and justify the co-assignment by what it adds.
- **The user's rewrite of a finding**: it is a rewrite, not a new finding, even if the PoC and numbers
  differ. Keep the source link.

## When a judge might merge broader

Mention it when a broad framing could swallow several findings ("trackers don't keep a cost basis"),
and argue for or against the merge using the fix test. Keep groups the project's duplicates index
already separates unless a fix test shows otherwise.
