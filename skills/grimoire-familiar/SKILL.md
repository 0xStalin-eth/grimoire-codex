---
name: grimoire-familiar
description: "QA gatekeeper and triage partner. This agent should be invoked when the user or another agent says \"triage this finding\", \"verify this vulnerability\", \"check if this is real\", \"is this a false positive\", \"validate this hypothesis\", \"review these sigil results\", \"triage findings\", \"familiar\", \"run triage\", \"double check this\", \"sanity check\", \"quality check this finding\", \"review this PoC\", \"evaluate this finding\", \"triage all findings\", \"batch triage\", \"process sigil output\", \"check this PoC\", \"is this PoC correct\", or when sigil agents produce findings that need validation before presenting to the user. Three modes: finding triage (validate a single finding or hypothesis), batch triage (process multiple sigil findings), and PoC review (evaluate proof-of-concept quality and completeness)."
---

## Codex adapter (read first)

Read [CODEX.md](CODEX.md) before the workflow. Preserve every stage and confirmation gate.

Load the installed Grimoire-Codex `agents/familiar.md` and follow its complete procedure.
If independent review is requested, use a separate agent context.
