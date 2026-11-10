---
name: tome-sync
description: >-
  This skill should be used when the user says "tome sync", "/tome-sync", "sync
  the tomes", "fix drift", "check tome drift", "are the tomes up to date", "which
  tomes are stale", "update the copies", "link the tomes", "map shared topics", or
  wants to find and fix tome sections that drifted from the section that owns
  their topic. It sweeps grimoire/tomes/active/ against grimoire/tomes/LINKS.md,
  maps topics shared across tomes that have no row yet, reports the drift, and
  fixes only what the user approves, owner → copies.
user_invocable: true
---

# Tome Sync

Find tome copies that drifted from their owner section, and bring them back in line. This is the safety
net behind the `tome` skill's editing rule: that rule keeps copies in sync when a tome is edited through
`/tome`, and this sweep catches what slipped past it (hand edits, other sessions, other skills, copies
that disagreed from the start).

## Philosophy

**Tomes are self-contained on purpose, so topics repeat.** A tome spun off a section of an older tome
carries a short version of that section. When new understanding lands in one place, the others go
stale silently. `grimoire/tomes/LINKS.md` names one **owner** per shared topic and lists its
**copies**. Read `../tome/references/links.md` before starting: it defines the file and the rules.

**Owner → copies.** The owner holds the full, current version; copies are summaries for their own
reader. Fix a copy from its owner, never the other way round, unless the newer understanding is in the
copy or the two disagree in a way that needs judgment (ask the user).

**Ownership is per topic, and it moves.** A tome built from several others starts as a copy of each
topic it pulls in. When it goes deeper on its own subject, ownership of that topic should transfer to
it; otherwise its findings keep flowing back into thinner parent sections. How owners are chosen, and
when to push up vs transfer, is in `../tome/references/links.md` › "Choosing the owner". Never transfer
silently: propose it in the report.

**Report first, fix on approval.** Drift is a disagreement between notes, and sometimes the stale one is
the owner. Never rewrite a security conclusion without the user's OK. Never merge tomes and never
rewrite copies mechanically: a copy is written for its own tome.

## Workflow

When this skill is activated, create a todo list from the following steps. Mark each task in_progress
before starting it and completed when done.

```
- [ ] 1. Load the map — read LINKS.md (create it if missing) and list every tome in tomes/active/
- [ ] 2. Check mapped topics — compare each owner with each copy
- [ ] 3. Find unmapped shared topics — topics repeated across tomes with no row
- [ ] 4. Check IDs and pointers — colliding ID families, stale IDs, missing Source lines
- [ ] 5. Report — open-drift table + new rows, owner named for each [user approves]
- [ ] 6. Fix approved drift — owner → copies, one topic at a time
- [ ] 7. Update LINKS.md and logs — statuses, Synced dates, SESSIONS.md rows
```

---

### 1. Load The Map

- Read `GRIMOIRE.md` for context, then `grimoire/tomes/LINKS.md`.
- If `LINKS.md` doesn't exist, say so and build it in steps 2–3 from scratch, using the format in
  `../tome/references/links.md`.
- List every file in `grimoire/tomes/active/` with its section headings (`grep -n '^#'`). Never read
  `grimoire/tomes/archived/`.
- Note which tomes were changed since the last sweep: the `tomes/SESSIONS.md` rows after the last
  `LINKS.md` row show what to check first.

Completion criterion: you know every active tome, its sections, and every row in `LINKS.md`.

### 2. Check Mapped Topics

For each row, read the owner section and every copy, then compare **claims**, not wording:
- mechanisms and their order of steps;
- numbers, worked-example values, formulas;
- statuses (open / likely invalid / confirmed), verdicts and conclusions;
- IDs and cross-references (question IDs, idea IDs, finding IDs);
- what is said to be unknown or pending.

A copy that omits detail is fine. A copy that says something the owner no longer says, or contradicts
it, is drift.

A copy that has **outgrown** its owner (newer claims, deeper treatment, and the topic is the copy's
tome's subject) is a **transfer candidate**, not drift to be pushed back up. Propose the transfer:
name the current owner, the proposed owner, and the claims that are only in the copy. If the owner itself is internally inconsistent (a heading says "resolved", the body still
argues the opposite), that is drift in the owner.

Also check that each listed section still exists under that heading. A renamed or removed section is
drift in the map.

Completion criterion: each row is marked in sync or has a drift entry with the exact sections.

### 3. Find Unmapped Shared Topics

Look for topics written in two or more tomes with no row:
- the same worked example or numbers in several tomes;
- the same mechanism explained in several places (glossary entry, flow, focused tome);
- the same lead, idea or question referenced from several tomes;
- sections whose text points to another tome ("see …", "Source: …", "ties into …").

For each, propose an owner using `../tome/references/links.md` › "Choosing the owner": first the tome
whose subject the topic is, then, on a tie, the section with the fullest current claims (extra code
references don't count). A tome that only gathers topics from other tomes is a copy of each, not the
owner.

Completion criterion: every topic found in more than one tome has a row or a reason not to have one.

### 4. Check IDs And Pointers

- **ID collisions.** List every ID family used across the grimoire (questions, ideas, leads, research
  items, findings, the protocol's own invariant or requirement IDs). Flag families that use the same
  prefix for different things, and every place an ambiguous ID appears without its family named.
- **Stale IDs.** An ID quoted for something it no longer names (a question renumbered, an idea split
  in two, a "candidate" ID later used for another question).
- **Unfiled actions.** A tome says "ask the client …" or "candidate question" with no matching entry in
  `grimoire/client-communication/`. Report it; filing a client question is the user's decision.
- **Source pointers.** Copies without a `Source:` line to their owner.

Completion criterion: every collision, stale ID, unfiled action and missing pointer is listed.

### 5. Report

Present, in this order:
1. **Open drift**, one row per item: `D<n>` (continue the numbering in `LINKS.md`), where, what is out
   of date, **which section is the owner**, and the proposed fix.
2. **Owner questions:** rows where owner and copy disagree and it isn't clear which is right.
3. **Ownership transfers** proposed from step 2: current owner → proposed owner, and why.
4. **New rows** proposed from step 3, with the owner picked for each.
5. **ID and pointer issues** from step 4.

Write the drift entries and new rows into `LINKS.md` now, marked as open, so the findings survive even
if nothing is fixed this session. Then ask the user which items to fix.

Completion criterion: the user has the full report and has chosen what to fix.

### 6. Fix Approved Drift

For each approved item:
- Name the owner, then update the owner first if the drift is in it, then each copy.
- Keep each copy written for its own reader: same claims as the owner, its own length and context.
  Follow the tome skill's writing rules (full meanings, no one-letter placeholders, and any
  engagement-specific style rules in memory or `GRIMOIRE.md`, such as glossing every symbol).
- End each touched copy with `Source: [[tomes/active/<owner-tome>]] §<section>` if it has none.
- For an approved transfer, follow the transfer steps in `../tome/references/links.md`: move the
  owner, note `owner moved from … on <date>` in the row, turn the old owner into a copy with a
  `Source:` line, then sync the other copies from the new owner.
- If fixing reveals that the owner is wrong against the code, stop and report it. Don't propagate it.

Completion criterion: each approved item is fixed in the owner and every copy listed for it.

### 7. Update LINKS.md And Logs

- Mark fixed rows `in sync` with today's date in `Synced`. Strike fixed drift entries (`~~D<n>~~`) with
  what was done and the date; note what is still open on a partial fix.
- Append one row per changed tome to `grimoire/tomes/SESSIONS.md`, and one for `LINKS.md`, with a shell
  append (`>>`) and the session ID from `$CLAUDE_CODE_SESSION_ID`.
- List every file changed in the final answer, with the owner named for each topic synced.

Completion criterion: `LINKS.md`, the tomes and `SESSIONS.md` agree on what was fixed and what is open.
