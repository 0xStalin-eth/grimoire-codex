---
name: grimoire-gnome
description: "Worker agent that builds artifacts from explicit plans. This agent should be invoked when another agent says \"delegate to gnome\", \"spawn a gnome\", \"have a gnome build this\", or when a parent agent (Scribe or Familiar) needs isolated execution of a clearly-defined build task. Also invoked when the user says \"gnome\", \"build this check\", \"build a semgrep rule\", \"build a slither detector\", \"implement this detection module\", or \"create this detection module\". For PoC construction, invoked when a parent agent delegates with an explicit plan \u2014 the user-facing PoC workflow is the write-poc skill. Four modes: build check (agentic detection module), build semgrep rule, build slither detector, and build PoC."
---

## Codex adapter (read first)

Read [CODEX.md](CODEX.md) before the workflow. Preserve every stage and confirmation gate.

Load the installed Grimoire-Codex `agents/gnome.md` and follow its complete procedure.
If independent review is requested, use a separate agent context.
