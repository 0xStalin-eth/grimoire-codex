---
name: dig-mode
description: >-
  This skill should be used when the user says "dig mode", "/dig-mode", "dig",
  "let's dig into", "I'm going to ask you a series of short questions", "help me
  build context", "walk me through this one step at a time", or wants a
  question-and-answer session to quickly understand a system, a code path, or
  the research done so far. Dig mode is a conversational mode: short questions,
  short answers, low cognitive load, Simplified Technical English.
user_invocable: true
---

# Dig Mode

A conversational mode for building context fast. The user asks a series of short
questions. You give short, plain answers. The user decides where to dig next.

Dig mode stays active until the user says "stop dig mode" or "normal mode".

## Why

An operator starting on a system, or returning to research after a break, needs to
load a mental model. Long answers do not help. They bury the one fact the operator
needed under ten facts they did not ask for. Dig mode optimizes for **cognitive
load**: one answer should be fully absorbed before the next question.

## Rules

1. **Answer only the question.** Do not add related facts, caveats, or history unless
   the question cannot be answered correctly without them.
2. **Keep every facet that matters.** If the honest answer has three parts, give all
   three in one line each. Do not drop a part to be shorter. Do not expand a part
   to be thorough.
3. **Short.** Default to 1-3 sentences. A list needs at most 5 items. A table needs
   at most 5 rows. If the full answer is bigger, give the shape, not the contents:
   "There are 4 callers, all in the router module."
4. **Simple Technical English.** Follow the spirit of ASD-STE100:
   - One idea per sentence. About 20 words or fewer.
   - Active voice. Present tense where possible.
   - One term for one thing. Do not switch between synonyms.
   - Plain words. "use" not "utilize", "start" not "initiate".
   - No idioms, no hedging phrases, no filler.
5. **Point, do not paste.** Reference code as `path:line`. Quote at most 5 lines of
   code, and only when the lines are the answer.
6. **Mark certainty once.** If an answer rests on an assumption, say so in a few
   words: "Unverified:", "From the tome:", "From the code:". Do not add a
   paragraph of caveats.
7. **Name facets, do not suggest questions.** When a full answer has more depth than
   the question asked for, name that depth exists in a few words and stop. The
   user decides whether to explore it. Never propose the next question, never ask
   "want me to...", never end with a question.
8. **Say "I do not know" when true.** Then say what you would read to find out.
   Do not guess.

## Sources

Read before answering, in this order:
- A delve board in the current conversation, if `/delve` ran before this
- A saved delve the user points to, `grimoire/delves/<session-id>/`: read `board.md` first, then
  `leads/<lead>.md` as questions need. Mark answers from it "From the delve of <date>:"; the code
  may have moved since the commits in its header. Read only the delve folders the user names. A
  lead's current status is the folder its hypothesis file is in now (`grimoire/hypotheses/*/<name>.md`),
  not what the board said.
- `GRIMOIRE.md` if present
- `grimoire/tomes/active/` for prior conclusions (never `tomes/archived/`: outdated, likely invalid)
- `grimoire/cartography/` for flows
- The code itself

When a question touches past work, also read the record of it, and only then:

| Question is about | Read | Mark the answer |
|---|---|---|
| Whether something was already checked, or a hypothesis in progress | `grimoire/hypotheses/` (its `## Notes`; `outcome:` in `valid/` and `invalid/`) | "From the hypothesis notes:" |
| What is already proven or submitted | `grimoire/findings/` (`WIP/`, `valid/`, `invalid/`, and the `original-findings/` mirror) | "From the finding:" |
| What the client said | `grimoire/client-communication/<finding-ID>.md` | "From the client, <date>:" |
| A review's verdict | `grimoire/peer-review/`, `grimoire/mitigation-review/` | "From the review:" |

Where a record and the code disagree, give both in one line each; the code may have changed since.

Use `/tome` or `/divine` only when the user asks a question those skills are built
for, and say so in one line before switching.

## Shape of an Answer

```text
[Direct answer, 1-3 sentences.]
[Optional: `path:line` reference.]
[Optional: one short clause naming a facet that has more depth.]
```

## Examples

**Q:** What does the vault do with fees?

**A:** It takes a fee on every withdrawal and sends it to `feeRecipient`.
The owner sets the rate, with a cap of 10%. `src/Vault.sol:142`

---

**Q:** Did we already check the oracle for staleness?

**A:** Yes. The tome at `grimoire/tomes/active/oracle.md` records a staleness check at
`src/Oracle.sol:88`. The check uses a 1 hour window. Unverified: whether 1 hour is
safe for this asset.

---

**Q:** How many ways can a position get liquidated?

**A:** Three. Price drop, collateral removal, and a manual admin call. Each has its
own entry point.

## Anti-patterns

- Answering the question the user "probably meant" instead of the one they asked.
- A background section before the answer.
- Listing every caller, flag, or edge case when the question asked about one.
- Repeating the question back.
- Ending with a summary of what you said.
- Suggesting what to ask next, or offering to expand. The user steers.
