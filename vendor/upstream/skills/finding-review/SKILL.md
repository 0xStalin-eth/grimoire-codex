---
name: finding-review
description: >-
  This skill should be used when the user says "review finding", "review my finding",
  "check my finding", "fact check finding", "improve finding", "/finding-review", or
  provides a path to an existing finding file and wants it evaluated for quality. Reviews
  findings against best practices for title clarity, description completeness, recommendation
  objectivity, severity accuracy, and reference validity. This skill is NOT for drafting
  new findings (use /finding-draft) or deduplicating findings (use /finding-dedup).
user_invocable: true
---

# Finding Review

Review and harden existing security findings against best practices.

## Prerequisites

Before starting, read `skills/finding/SKILL.md` to understand finding structure, best
practices, and conventions. That skill defines the format, quality standards, and principles
that this workflow evaluates against.

## Workflow

When this skill is activated, create a todo list from the following steps. Mark each task
in_progress before starting it and completed when done.

```
- [ ] 0. Load finding knowledge (read skills/finding/SKILL.md)
- [ ] 1. Load and validate finding
- [ ] 2. Analyze content
- [ ] 3. Present review and offer updates
```

---

### 0. Load Finding Knowledge

Read `skills/finding/SKILL.md` to internalize finding structure, best practices, and
conventions. This is required before proceeding — the base skill defines the standards you
will evaluate against.

### 1. Load and Validate Finding

Read the target finding file. Parse frontmatter and sections.

Run structural validation:
```bash
bash skills/finding/scripts/validate-finding.sh <path-to-finding>
```

Report any schema violations — missing frontmatter fields, missing required sections,
invalid severity values.

### 2. Analyze Content

Evaluate the finding against the guidelines in the finding skill and
`skills/finding/references/finding-best-practices.md`:

**Title** — does it satisfy the where/how/what rule? If not, propose an improved title.

**Description** — is it self-contained? Could a reader unfamiliar with the codebase
understand the vulnerability from this section alone? Is impact clearly stated?

**Details** — if present, does it add value beyond the description? If absent, should it
be added?

**Recommendation** — is it the last section, after the PoC? Is it objective? Does it avoid non-trivial code suggestions? Is it
actionable by a project maintainer? If it shows a code diff, is the guidance disclosure
("The next code snippet shall be taken as a general guidance ...") directly above it?

**Severity** — is the estimate reasonable given the described impact, exploitability,
and preconditions?

**Preconditions & attacker class** — does the finding enumerate every prerequisite
needed to exploit, and name the minimum attacker class (any user, privileged role,
governance majority, etc.)? Missing or vague preconditions are a review failure — they
are what the reader uses to decide whether the finding applies to their deployment.

**Style rules** — flag every violation of these mandatory rules (details in
`finding-best-practices.md`), quoting the offending text and giving the corrected version:

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

**PoC reference** — does the `@`-referenced file exist? Is it correctly formatted?

**References** — are all cited references real and relevant? Are claims fact-checked?

**Familiar agent check** — Invoke the familiar agent in finding triage mode (Mode 1) on
the finding being reviewed. The familiar produces a triangulated assessment across
Impact, Feasibility (with an attacker class and prerequisite predicate), Design Intent,
and Scope Cross-Reference. Include the familiar's verdict (Confirmed, Severity Adjusted,
Uncertain, Possibly By Design, or Dismissed) and each of these four sections in the
review output. Compare the familiar's feasibility analysis against the finding's stated
preconditions — discrepancies are the review's most important signal.

**Librarian agent check** — Use the librarian agent to verify cited references exist and
are accurate. Ask the librarian to search for additional relevant references (prior findings
for similar flaws, specification clauses, security advisories) that could strengthen the
finding.

### 3. Present Review and Offer Updates

Present the review in structured sections:

- **Passes** — what the finding does well
- **Warnings** — non-critical issues worth addressing
- **Failures** — violations of required guidelines
- **Recommendations** — specific suggested improvements

Each item should cite the guideline it checks against.

Ask the user: *"Apply recommended changes? [y/n]"*

If yes, apply edits to the finding file. Re-run validation. Present the updated finding.

Suggest follow-ups:
- `/finding-dedup` if the project has multiple findings
- [[write-poc]] if the PoC section has a placeholder
