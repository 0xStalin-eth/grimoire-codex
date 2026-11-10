---
name: grimoire-scribe
description: "Detection module builder and spellbook manager. This agent should be invoked when the user or another agent says \"distill this finding\", \"create a detection module\", \"build a sigil from this\", \"encode this as automation\", \"scribe\", \"update my spellbook\", \"merge sigils\", \"what sigils do I have\", \"clean up sigils\", \"garbage collect\", \"scribe-gc\", \"promote sigils\", \"end of audit merge\", \"encode finding as detection\", \"what detectors do I have\", \"show my spellbook\", \"list my sigils\", or when a confirmed finding should be assessed for automated detection potential. Three modes: distill (finding to detection module), spellbook management (merge, promote, garbage collect), and query (list and describe sigils)."
---

## Codex adapter (read first)

Read [CODEX.md](CODEX.md) before the workflow. Preserve every stage and confirmation gate.

Load the installed Grimoire-Codex `agents/scribe.md` and follow its complete procedure.
If independent review is requested, use a separate agent context.
