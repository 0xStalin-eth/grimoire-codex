---
name: finding-draft
description: >-
  This skill should be used when the user says "draft a finding", "write a finding",
  "create a finding", "document a vulnerability", "write up this bug", "finding template",
  "report a vulnerability", "/finding-draft", or wants to construct a new structured
  security finding from a vulnerability observation. This skill is NOT for reviewing
  existing findings (use /finding-review) or deduplicating findings (use /finding-dedup).
user_invocable: true
---

# Finding Draft

Draft structured security findings from vulnerability observations.

## Prerequisites

Before starting, read `skills/finding/SKILL.md` to understand finding structure, best
practices, and conventions. That skill defines the format, frontmatter schema, severity
scale, and key principles that this workflow applies.

## Workflow

When this skill is activated, create a todo list from the following steps. Mark each task
in_progress before starting it and completed when done.

```
- [ ] 0. Load finding knowledge (read skills/finding/SKILL.md)
- [ ] 1. Gather context
- [ ] 2. Construct title
- [ ] 3. Estimate severity and classify type
- [ ] 4. Draft sections
- [ ] 5. Write finding file
- [ ] 6. Suggest follow-ups
```

---

### 0. Load Finding Knowledge

Read `skills/finding/SKILL.md` to internalize finding structure, best practices, and
conventions. This is required before proceeding — the base skill defines the format you
will produce.

### 1. Gather Context

Verify the workspace:
- Check for `GRIMOIRE.md` in the project root. If absent, suggest running [[summon]] first.
- Check whether `grimoire/findings/` exists. Create it if not.

Gather vulnerability context:
- If triage context exists from the familiar agent, use it. Otherwise invoke the familiar
  in finding triage mode (Mode 1) on the vulnerability context. The familiar produces:
  - an **Impact** statement (use it to calibrate severity — step 3),
  - a **Feasibility** analysis with an attacker class and prerequisite predicate (use it
    to populate the finding's preconditions — step 4),
  - a **Design Intent** verdict (if `Possibly By Design`, surface the familiar's
    yes/no question to the user before drafting — the answer may change whether there
    is a finding to draft at all),
  - a **Scope Cross-Reference** (if a capability clause forecloses the attack path,
    reconsider whether to proceed; if it downgrades severity, carry that through).
- Ask the user to describe: **what component** is affected, **what goes wrong**, and
  **what the impact is** — even with familiar context, the user's framing is the source
  of truth for the finding's voice.
- Search for existing PoC artifacts that relate to this vulnerability. If found, note the
  path for later `@reference`.

Check in with the user before continuing.

### 2. Construct Title

Build the title following the **where / how / what** rule from the finding skill.

Present the candidate title to the user for confirmation.

### 3. Estimate Severity and Classify Type

**Severity** — propose one of: Critical, High, Medium, Low, Informational. Provide a
one-sentence justification. Use the severity scale from the finding skill. If the
familiar produced an Adjusted Severity, use that as your starting point and only deviate
with explicit justification.

**Type** — classify the flaw. Consult `skills/finding/references/finding-format.md` for the
recommended type taxonomy.

**Context** — list the affected source files with optional line numbers for the `context`
frontmatter field.

Present severity, type, and context to the user for confirmation.

### 4. Draft Sections

Write each section following the format from the finding skill and the detailed guidelines
in `skills/finding/references/finding-best-practices.md`. Read that file before drafting. These style
rules are mandatory in every section; re-check the draft against them before presenting it:

- **Topic sentences:** each explanatory paragraph opens with a declarative sentence stating its main
  point. No run-in bold headings ("**How X works.** ...") and no question-then-answer framing.
- **Function references:** `Contract::functionName` in prose, never `contract.function()` or a bare
  `function()`.
- **Code snippets:** headed by `// ContractName`, wrapped in the enclosing function signature, with `...`
  around the referenced lines and the closing brace. Functions of the same contract share one heading;
  another contract gets its own.
- **Other findings:** linked as `[issue-N](<url of that issue>)`, never a bare `#N`.
- **PoC references:** a figure or result cited from a PoC names the test it comes from ("In
  `test_PoC_<Name>`, ..."), never a bare "the PoC"; give the PoC file path at least once. Every
  test cited must be embedded, with its output, in the same write-up file: no figure may point to
  a test that lives only in another file or another comment.
- **No collapsible blocks:** never wrap a PoC (or any code) in `<details>` / `<summary>` tags.
  The code block follows its introducing sentence directly ("Save it as `<path>`:").
- **No one-letter shorthand:** never stand a letter in for a quantity, a time, an address or any other
  value (`P`, `R`, `D`, `x`, `p`, `Δ`, `T`, `t`, `X`), even after defining it once. Write the contract
  variable (`srtPnLProjected`, `valuationPrice`, `effectiveAt`) or a plain phrase ("the realized-loss
  claim", "the split being re-applied") at every occurrence, formulas and call examples included
  (`setUIMultiplier(1e18, effectiveAt)`, not `setUIMultiplier(1e18, T)`). Before finishing, grep the
  prose for backticked single letters and single-letter call arguments. Test code embedded verbatim
  is exempt.

**## Description** (mandatory) — 2-4 self-contained paragraphs covering component, flaw,
preconditions, and impact. If the familiar produced a feasibility predicate or
prerequisite table, the finding's preconditions should match it (or explicitly differ,
with reasoning). The minimum attacker class from the familiar's Feasibility section
should be stated here verbatim.

**## Details** (optional) — only when the mechanism is non-obvious or multi-step.

**## Proof of Concept** — `@path/to/poc-file` if one exists, placeholder otherwise.

**## Recommendation** (mandatory) — objective fix direction. Never non-trivial code changes.
It always comes after the Proof of Concept; only References may follow it.
When it includes a code diff, put this disclosure line directly above the diff block:
"The next code snippet shall be taken as a general guidance to visualize the changes the mitigation may require. This is not to be used as the exact changes that are implemented."

**## References** (optional) — numbered citations. Use the librarian agent to discover
relevant references — prior audit findings, specification clauses, and vulnerability
database entries related to the flaw.

Consult `skills/finding/examples/reentrancy-finding.md` for a complete finding and
`skills/finding/examples/access-control-finding.md` for a minimal valid finding.

Present the drafted content to the user for review before writing the file.

### 5. Write Finding File

Determine the target directory:
- `grimoire/findings/` for manual audit research (default)
- `grimoire/sigil-findings/` for automated tooling or sigil agents

Generate the filename per the filing conventions in the finding skill.

Write the complete finding file with frontmatter and all sections.

Validate by running:
```bash
bash skills/finding/scripts/validate-finding.sh <path-to-finding>
```

If validation fails, fix the issues and re-validate.

### 6. Suggest Follow-ups

Based on the finding:
- If no PoC exists: suggest [[write-poc]]
- If related findings may exist: suggest `/finding-dedup`
- If cartography is missing for affected flows: suggest [[cartography]]
- If the pattern could be generalized into a check: suggest [[checks]]
- If the finding represents an automatable pattern: suggest [[scribe-distill]] to distill
  it into a reusable detection module

When the user later confirms the finding was submitted, move it from `findings/WIP/` to
`findings/valid/` in the same turn and update its links and logs: the "Finding submitted" rule in
`/summon` Step 2.
