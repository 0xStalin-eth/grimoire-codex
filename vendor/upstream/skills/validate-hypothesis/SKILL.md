---
name: validate-hypothesis
description: >-
  This skill should be used when the user says "validate hypothesis", "validate this hypothesis",
  "/validate-hypothesis", "is this lead real", "explore this lead", "prove or disprove this", "check
  this hypothesis", "work on hypothesis <name>", "promote this hypothesis", or points at a file in
  grimoire/hypotheses/WIP/ (created by hand or by /delve) and wants it explored and settled. Traces the
  mechanism in code, checks whether the behavior is intended, proves it with a PoC, gets an independent
  triage, and records the outcome: promoted to a finding draft in findings/WIP/, or closed in
  hypotheses/invalid/ as invalid or expected behavior. Not for only writing a hypothesis down (use
  /write-hypothesis), surfacing leads (use /delve), building
  context through questions (use /dig-mode), reviewing someone else's finding (use /peer-review), or
  writing up an already-proven bug (use /finding-draft).
user_invocable: true
---

# Validate Hypothesis

Take one hypothesis from `grimoire/hypotheses/WIP/` and settle it: explore it, prove or disprove it,
and file the result where the rest of Grimoire can see it. A hypothesis comes from the user's own
reading or from `/delve`; both use the hypothesis format from `/summon` Step 2.

## Philosophy

- **Prove, don't argue.** A hypothesis is valid only when a test shows it. Numbers in the verdict come
  from test output, not from reasoning about the code.
- **Disproving is a result.** A hypothesis closed as `invalid` or `expected behavior`, with the reason,
  keeps the next delve and the next session from re-opening it. Write the reason so it convinces a
  reader who was not here.
- **Validity, intent and severity are separate questions.** The code can do what the hypothesis says
  and still be working as designed. Answer each one on its own.
- **Write as you go.** Every check goes into the hypothesis file's `## Notes` with the date, so a
  hypothesis left in `WIP/` can be resumed from the file alone.
- **The user moves the file.** Nothing leaves `WIP/` without the user confirming the verdict.

## Inputs

| Input | Where it comes from |
|---|---|
| Hypothesis | A file in `grimoire/hypotheses/WIP/`, or an idea the user states (step 1 records it) |
| Source leads | The file's `source:` lines (`grimoire/delves/<session-id>/leads/<lead>.md`) |
| Context | `GRIMOIRE.md` (scope, trust assumptions, crown jewels), `grimoire/tomes/active/` (never `tomes/archived/`) |
| PoC directory | The project's existing PoC folder; never create a new one silently |

If GRIMOIRE.md doesn't exist, run `/summon` first. The peer-review skill's `scripts/` directory is `$P`
below (`isolated-workspace.sh`, `verify-fix.sh`); its `references/severity-calibration.md` and
`references/parallel-sessions.md` apply here too.

## Parallel Sessions

Several sessions can validate different hypotheses in the same workspace at once. On top of the
peer-review rules above:
- **One session per hypothesis.** A session works only on a hypothesis it has claimed (step 1).
- **Status rows go through the script.** `hypotheses/SESSIONS.md` is a snapshot, one row per
  hypothesis with its current state. Write it only with the summon skill's
  `scripts/session-status.sh`, which replaces the row under a lock, so concurrent updates are never
  lost. `findings/SESSIONS.md` is a history log: add rows with a shell append (`>>`) only.
- **Never overwrite on create.** Before writing a new hypothesis, finding draft or PoC, check the name
  is free (`set -o noclobber` or `[ ! -e <file> ]`). On a clash, add a short suffix.

---

## Workflow

Create a todo list from these steps. Steps marked **[confirm]** pause for the user.

```
- [ ] 1. Load the hypothesis and check what is already known
- [ ] 2. Explore the mechanism
- [ ] 3. Check intent
- [ ] 4. Prove it
- [ ] 5. Independent triage
- [ ] 6. Present the verdict              [confirm]
- [ ] 7. File the outcome                 [confirm]
```

### 1. Load

Read the hypothesis file and every lead in its `source:`. If the user gave an idea instead of a file,
create `grimoire/hypotheses/WIP/<name>.md` in the `/summon` format (`source: manual`) and append a
row for it to `grimoire/hypotheses/SESSIONS.md` 
(`session-status.sh … <name>.md WIP "created, manual"`).

**Claim it.** If `claimed-by:` is empty, set it to this session's ID and update its row in
`grimoire/hypotheses/SESSIONS.md` (`session-status.sh … <name>.md WIP "claimed, validating"`). Re-read the file right after: if another ID won, back off. If it
already names another session, stop: tell the user which session holds it (`claude --resume
<session-id>`), and continue only if they explicitly take it over (note `taken over from <id>`
in its row).
A resumed session keeps its ID, so it finds its own claim.

Restate the hypothesis as one testable sentence: who does what, through which path, and what breaks.

Then check whether it is already settled. Search `grimoire/findings/` (all folders, and the
`original-findings/` mirror) and `grimoire/hypotheses/valid/` and `invalid/` for the same mechanism at
the same `path:line`. If a match exists, stop and tell the user: it is a duplicate of a finding, or a
known dead end with its recorded reason.

### 2. Explore

Trace the path in code and quote the responsible lines (`file:line`):
- Is the vulnerable path reachable from an entry point the attacker can call? Walk it end to end.
- Which checks stand in the way, and can each one be satisfied?
- Check every sibling (other variants, adapters, implementations) with one grep. Say which are
  affected and why the others are not.

For a wide search across the codebase, spawn a `sigil` agent (variant mode) on the pattern. When the
hypothesis rests on a spec or external protocol claim, ask the `librarian` agent; don't rely on memory.
Append each check to `## Notes` as you go.

### 3. Check intent

Look for evidence that the behavior is by design: the spec and docs, a docstring describing this exact
behavior, an intent-named test, the client's answers in `grimoire/client-communication/`. When the
reason for the code is unclear, run `/divine` on it. Land on *not by design*, *by design*, or *needs the
client* (then draft the question for `client-communication/`; don't send it).

### 4. Prove it

Use `/write-poc` to write the smallest test that shows the claim. Name it after the hypothesis
(`Hyp<Name>.t.sol`, or the project's equivalent) so parallel sessions never pick the same file. Draft
it in this session's work folder (`$P/isolated-workspace.sh work hyp-<name>`) and move it into the
project's PoC directory only once it compiles: a broken file in the shared PoC folder breaks every
other session's build. Prefer the hypothesis's own scenario on the full stack, reusing existing fixtures. Record the exact
figures the test logs. When a code change is needed to probe the behavior, make it only in this
session's isolated copy (`$P/isolated-workspace.sh`), never in the workspace.

A test that shows the attack does **not** work is also proof: keep it, and cite it in the verdict.

### 5. Independent triage

Spawn the `familiar` agent (Mode 1) on the hypothesis file and the PoC path. Give it the claim and the
evidence, not your verdict, so its read is not anchored on yours. Where it disagrees with you, look
again before going on, and report the disagreement in the verdict.

### 6. Present the verdict [confirm]

One of:

| Verdict | When |
|---|---|
| **Valid** | The PoC shows the impact, the path is reachable by the stated actor, and it is not by design |
| **Invalid** | The attack does not work; name the check or condition that stops it |
| **Expected behavior** | It works, but as designed; cite the evidence of intent |
| **Inconclusive** | Something only the client or more work can answer; say exactly what |

Reply briefly: the verdict and the reason in one sentence; the key `file:line`; the PoC result; the
familiar's verdict; and for **Valid**, a severity estimate walked through the peer-review skill's
`references/severity-calibration.md`, with the strongest argument on each side. Wait for the user
to confirm or correct it.

Before confirming, the user may question the verdict with `/dig-mode`. Make sure the hypothesis
file's `## Notes` hold everything found so far before pausing; dig-mode reads them, also from
another session.

### 7. File the outcome [confirm]

On the user's confirmation (they may question the filing with `/dig-mode` first), finish the
hypothesis file's `## Notes` with the verdict and clear `claimed-by:` (an Inconclusive hypothesis keeps
it only if this session will resume it), then:

| Verdict | Hypothesis file | Also |
|---|---|---|
| **Valid** | Move to `hypotheses/valid/`, `outcome: promoted: findings/WIP/<name>.md` | Run `/finding-draft` and save the draft as `grimoire/findings/WIP/<name>.md` (not the skill's default folder), with a `hypothesis: hypotheses/valid/<name>.md` line in its front matter and the PoC in its proof section |
| **Invalid** | Move to `hypotheses/invalid/`, `outcome: invalid: <why>` | |
| **Expected behavior** | Move to `hypotheses/invalid/`, `outcome: expected behavior: <why>` | |
| **Inconclusive** | Stays in `WIP/` | Notes say what is missing; if it waits on the client, add the question to `grimoire/client-communication/<name>.md` |

Update the hypothesis's row in `grimoire/hypotheses/SESSIONS.md` to its new folder, with the verdict
as the note (`session-status.sh … <name>.md valid "Valid; promoted to findings/WIP/<name>.md"`), and
append a `created in WIP` row to `grimoire/findings/SESSIONS.md` for a new draft.

From here on, the finding and the hypothesis move together: if the finding is later rejected, its
hypothesis goes back to `invalid/` (rule in `/summon` Step 2, "Findings and hypotheses stay in sync").
When the user confirms the draft was submitted, move it to `findings/valid/` and update the
hypothesis's `outcome:` link and both logs in the same turn (rule in `/summon` Step 2, "Finding
submitted").

Never edit the delve folders. A lead's status is read from its hypothesis's folder, so moving the
hypothesis is all the sync a delve needs.

End with one line: where the hypothesis went, and the draft's path if one was created.
