# Deliverables

Produce these only when asked. Save files where the project keeps them (look for an existing comments
or findings folder) and show the text in the reply as well.

The Recommended Mitigation section always goes last, after the Proof of Concept; only the project/auditor response stubs (and a References list, if any) may follow it.

In every deliverable meant for the tracker or the report, reference other findings as
`[issue-N](<url of that issue>)`, never a bare `#N` (see `finding-best-practices.md`).
When citing a PoC result, name the test function it comes from ("In `test_PoC_<Name>`, ..."),
not just "the PoC". Every test a deliverable cites must be embedded, with its output, in that
same deliverable file. Do not split a comment and its supporting PoC into separate files, and do
not cite tests that exist only in the repo's PoC file or in another deliverable.
Never wrap a PoC (or any code) in `<details>` / `<summary>` collapsible tags; the code block
follows its introducing sentence directly ("Save it as `<path>`:").
Probe tests (written to answer a question or to check a fix's side effects) stay out of the
write-up and its PoC. Move a probe test in only when the user asks to add a claim that probe
validated; rename it `test_PoC_<Name>` and cite it. The same applies to tests written to explore an
idea or a possible new impact: nothing enters the write-up until it is validated and requested.
Probe files may stay on disk, but a write-up must not keep stale references: once an idea is
ruled out or left out of the final write-up, remove every mention, citation and snippet of its
tests from the deliverables. Do not delete probe files unless the user asks.

## Introductory paragraph

For readers new to the bug. Markdown, ready to paste above the finding's Description.
- Open with a declarative topic sentence that states the main point; no run-in bold headings (see
  `skills/finding/references/finding-best-practices.md`).
- Explain the normal behaviour first, then the case that breaks it.
- Use one small table or worked example with numbers from the PoC.
- End with the consequence in one sentence.
- No one-letter shorthand, even if defined once: write the variable name or a plain phrase at
  every occurrence, formulas and call examples included (`srtPnLProjected / valuationPrice`, not
  `P / price`; `setUIMultiplier(1e18, effectiveAt)` … "after that `effectiveAt`", not
  `setUIMultiplier(1e18, T)` … "after `T`").

## Comment (downgrade, Informational, recovery runbook)

One paragraph, small and concise, starting with a bold verdict ("**Suggest Informational.**").
Include only the decisive arguments: preconditions, recovery path and its cost, bound, scope. If the
user may close the report with it, phrase the recovery as a runbook step.

## Full rewrite

Follow the format of the finding the user names (or the project's submitted findings):
- front matter (`title`, `severity`, `type`, `context` with `file:line` ranges) if the project uses it;
- Description that explains the mechanism before the bug, in paragraphs that each open with a
  declarative topic sentence (no run-in bold headings);
- Preconditions and attacker class, Impact bullets, a Severity paragraph;
- a worked example with a table;
- an embedded or `@`-referenced PoC that is standalone and passes, with the run command;
- a verified mitigation diff, labelled as guidance if that is the project's convention, with the
  invariant it relies on and the variants that need it;
- References.

Remove the source issue link only if the user asks (for example when submitting it as a new finding),
and warn if the rewrite is a duplicate of the source issue.

## Co-assignee note

Two to four sentences: "Adding myself as co-assignee." Then what the user added that the original
lacks (a new impact, a PoC, a verified fix), with one concrete number. If the user found it
independently, mention the draft date. Focus on the strongest addition when asked.

## Session marker

A block that a later search can find (use the template in `examples/session-marker-template.md`):
finding number and title, author, role of this session, verdict, the artifacts created (paths),
open items, date. Write a corrected marker if a later turn changes the verdict.

## Pending-reviews tome entry

For parked findings and new leads (template in `examples/pending-tome-template.md`): status, mechanism
with `file:line`, what is already proven (PoC paths and figures), related findings, and numbered leads
from most to least promising. New leads go at the top when the user says they'll start there.

## Mitigation diff

Show the verified diff with clean paths. Directly above the diff block, add the disclosure line:
"The next code snippet shall be taken as a general guidance to visualize the changes the mitigation may require. This is not to be used as the exact changes that are implemented."
Say what was verified (PoC results, regression comparison),
what the other variants need, and any invariant or caveat. If the user asks for a design without
implementation, label it a sketch and compare it with the tested option.
