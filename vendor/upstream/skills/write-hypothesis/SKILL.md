---
name: write-hypothesis
description: >-
  This skill should be used when the user says "write a hypothesis", "write up a hypothesis",
  "/write-hypothesis", "create a hypothesis", "turn this into a hypothesis", "make a hypothesis out of
  this", "record this as a hypothesis", "save this idea as a hypothesis", "hypothesis from this
  conversation", "log this lead", or wants an idea, a suspicion, or a portion of the current
  conversation written into grimoire/hypotheses/WIP/ for later exploration. Distills what was already
  discussed into the hypothesis format from /summon Step 2, narrows the possible outcomes into ruled
  out / open / confirmed using only evidence already gathered, logs it, and stops. Not for exploring
  or proving a hypothesis (use /validate-hypothesis), surfacing leads from agent research (use
  /delve), or writing up a proven bug (use /finding-draft).
user_invocable: true
---

# Write Hypothesis

Turn an idea, or the part of the conversation that explored it, into one hypothesis file in
`grimoire/hypotheses/WIP/`, ready for `/validate-hypothesis` or a later session to pick up cold.

This skill **writes and stops**. It does not trace new code paths, run tests, or decide whether the
hypothesis is valid. Its value is that the reasoning done in conversation is not lost, and that the
next session starts from a narrowed set of outcomes instead of from zero.

## Philosophy

- **Capture, don't investigate.** Use what the conversation already established. A quick look at a
  `file:line` to confirm a citation or a line number is fine; new exploration is not. If a gap needs
  real work, write it down as an open outcome.
- **Narrow the outcomes.** A good hypothesis says not only "this might be a bug" but which ways it could
  go wrong, which of those are already ruled out (and by what check), and which are still open. That
  outcome tree is what saves the next session the most time.
- **Facts and guesses stay apart.** Things checked in code are facts, with `file:line`. Things inferred
  or assumed are marked as such. Never present an unchecked guess as established.
- **Corrections win.** If the conversation corrected an earlier claim, write the corrected version
  only. The file must not repeat a mistake the conversation already fixed.
- **Readable cold.** Someone who wasn't in the conversation must understand the file alone. Explain
  each domain term or symbol where it is first used, and never refer to "what we said above".

## Inputs

| Input | Where it comes from |
|---|---|
| The idea | The user's request, plus the part of the conversation it points at ("this", "what we explored", "the last few answers"). If the scope is unclear, take the most recent thread on the topic and say which part you used |
| Context | `GRIMOIRE.md` (scope, actors, trust assumptions), `grimoire/tomes/active/`, `grimoire/client-communication/` |
| Existing work | `grimoire/hypotheses/` (all folders), `grimoire/findings/` (all folders, including `original-findings/`), `grimoire/tomes/active/` idea or lead lists |

If GRIMOIRE.md or `grimoire/hypotheses/` doesn't exist, run `/summon` first.

---

## Workflow

Create a todo list from these steps. Steps marked **[confirm]** pause for the user.

```
- [ ] 1. Gather what the conversation established
- [ ] 2. Check it isn't already recorded
- [ ] 3. Build the outcome tree
- [ ] 4. Write the file
- [ ] 5. Log it and report
```

### 1. Gather

From the conversation, collect:
- **The claim.** One testable sentence: who does what, through which path, and what could break.
- **The facts.** Every behavior that was checked in code, with its `file:line`. Re-open a cited line
  only to confirm the citation is still right.
- **The corrections.** Any earlier claim the conversation retracted, so it is left out.
- **The open questions.** What was suspected but not checked.
- **Links.** Related tomes, ideas, client questions, delve leads, or findings that were mentioned.

### 2. Check it isn't already recorded

Search `grimoire/hypotheses/` (WIP, valid, invalid) and `grimoire/findings/` for the same mechanism at
the same `path:line`:
- **Same hypothesis in `WIP/`:** don't create another. Append the new evidence to its `## Notes`
  (dated), widen its outcome tree if needed, and update its row (step 5).
- **Already closed** (`valid/`, `invalid/`, or a finding): stop and tell the user what it was closed
  as and why. Write a new file only if the user confirms the new angle is different.

### 3. Build the outcome tree

List the concrete ways the hypothesis could turn into impact. Give each one a status, with the reason:

| Status | Meaning |
|---|---|
| **Ruled out** | A check already seen in code stops it; cite the check |
| **Ruled out (to confirm)** | Very likely stopped, but one listed thing is still unchecked; name it |
| **Open** | Not yet checked, or checked and still possible; say what would settle it |
| **Confirmed** | Already shown to happen (by a test or an unambiguous code path); say the impact level it was shown at |
| **Known** | Already recorded elsewhere (an idea, a finding, a client answer); link it |

Then add:
- **What to explore next.** A short, ordered list aimed at the open outcomes only.
- **A PoC sketch**, if the open outcomes are clear enough to test. Use placeholders, and keep it short.
- **A severity expectation** per group of outcomes, labelled as an expectation, not a verdict.

### 4. Write the file

Pick a short kebab-case name for the mechanism (`<component>-<behavior>.md`). Check the name is free
(`[ ! -e grimoire/hypotheses/WIP/<name>.md ]`); on a clash, add a short suffix. Never overwrite.

Use the hypothesis format from `/summon` Step 2 exactly, with the body laid out like this:

```markdown
---
source: manual
outcome:
claimed-by:
---
# <hypothesis title: the behavior and the condition, in one line>

<one paragraph: the behavior, where it is (`path:line`), why it may matter, what would confirm or refute it>

**Code:**
- `<path:line>` (<what is there>)

**Related:** <tomes, ideas, client questions, findings, delve leads, or "none">

## What is established
<numbered facts, each with `path:line`; corrections already applied>

## Outcomes
| # | Possible outcome | Status | Why |
|---|---|---|---|

## What to explore next
<ordered list, open outcomes only>

## PoC sketch
<optional>

## Severity expectation
<per group of outcomes; an expectation, not a verdict>

## Notes
- <YYYY-MM-DD>: written from a conversation with /write-hypothesis. <what was checked, in one or two sentences>
```

Rules:
- `source:` is `manual` unless the idea came from a delve lead file; then list that file instead
  (one per line), as `/delve` does.
- `outcome:` and `claimed-by:` stay empty. Writing a hypothesis does not claim it.
- If the project has a rule about how terms are explained (for example, in `GRIMOIRE.md` or the user's
  memory), follow it in the file.

### 5. Log it and report

Set the hypothesis's row in `grimoire/hypotheses/SESSIONS.md` with the summon skill's
`scripts/session-status.sh` (never edit the table by hand; it reads the session ID from
`$CLAUDE_CODE_SESSION_ID` and refuses to guess one):

```bash
<summon>/scripts/session-status.sh grimoire/hypotheses/SESSIONS.md <name>.md WIP "manual. <claim in a few words>; open: <open outcome ids>"
```

Notes may not contain `|`.

Then reply briefly:
- the file path;
- the claim in one sentence;
- the outcome tree as a compact table (outcome, status);
- one line offering `/validate-hypothesis <name>` to explore it.

Do not start validating.
