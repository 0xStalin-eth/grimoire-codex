---
name: grimoire-sigil
description: "Single-context vulnerability hunter. This agent should be invoked when the user or another agent says \"hunt for bugs\", \"find vulnerabilities\", \"run a sigil\", \"variant analysis\", \"scan for a pattern\", \"check the code for issues\", \"security scan\", \"look for reentrancy\", \"audit this contract\", \"find bugs in this function\", \"spawn a sigil\", \"run a variant sigil\", \"security review\", or when another agent needs focused vulnerability detection on a specific pattern or code area. Two modes: single-target hypothesis-driven hunting (one vector per invocation with evidence-backed findings) and variant analysis (scanning the full codebase for recurrences of a confirmed bug pattern)."
---

## Codex adapter (read first)

Read [CODEX.md](CODEX.md) before the workflow. Preserve every stage and confirmation gate.

Load the installed Grimoire-Codex `agents/sigil.md` and follow its complete procedure.
If independent review is requested, use a separate agent context.
