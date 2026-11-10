---
name: grimoire-assess-process-improvements
description: "Assess operator feedback on the current maintenance session and propose confirmed downstream process improvements."
---

## Codex adapter (read first)

Read [CODEX.md](CODEX.md) before the workflow. Preserve every stage and confirmation gate.


# Downstream maintenance boundary

Apply this adapter before the preserved maintenance procedure.

Verify the current repository is Grimoire-Codex using its `codex/project.json` marker and remotes.
Never operate on an upstream checkout. In the procedure, specifications mean
`vendor/upstream/grimoire/`; upstream implementations for comparison mean
`vendor/upstream/skills/` and `vendor/upstream/agents/`. Both are read-only.
Implementation changes go in `codex/` adapters/patches, `scripts/`, tests and downstream docs.
`skills/`, `agents/` and `.agents/skills/` are generated: change the adapter, then regenerate.
`CLAUDE.md` guidance maps to downstream `AGENTS.md`; command changes belong in downstream
maintenance adapters. Plugin configuration maps to the downstream Codex execution adapter.
Keep `IMPLEMENTATION_PLAN.md` downstream only.

Use Codex subagents with inherited model settings in place of Opus/Sonnet or a named
`skill-reviewer` type. Preserve separate spec-study, design, build, skill-review and compliance
stages. Batch catalog/analysis work within available concurrency; the 250-agent fanout is not a
Codex requirement. Give agents their procedure and required read/search capabilities rather than
attempting to grant Claude tool names. If independent review is unavailable, save the pending
review handoff rather than claiming completion.

For commit, replace the inherited pnpm checks with this repository's actual checks:
`python3 scripts/validate.py` and `python3 -m unittest discover -s tests -v`.
Review the diff and stage explicit authorized paths; never automatically stage audit targets,
secrets or unrelated user work. Do not bypass checks to make a commit pass. Never push as part of
these maintenance procedures. Persist durable process lessons in downstream `AGENTS.md` or
`codex/` instructions, not Claude memory or an upstream file.


# Assess Process Improvements

Study the conversation history to find every instance where the user corrected,
redirected, or refined Codex's work during the most recent gap-analysis or
execute-plan run. Then propose concrete changes to commands, skills, or
conventions so those corrections become unnecessary.

## Important Constraints

- This command operates on the current conversation context. It must be run in
  the same session as the gap-analysis or execute-plan run being assessed.
- Proposed changes target the process (commands, skills, AGENTS.md, conventions),
  not the plugin implementation itself.
- The specification in `vendor/upstream/grimoire/` is read-only. Never propose changes there.
- Use subagents for analysis to keep context clean.

## Subagent Tools

- **Step 1 subagent** (extract feedback): none needed (works from conversation context)
- **Step 2 subagent** (classify, Codex): `Read`, `Glob`
- **Step 3 subagent** (propose fixes, Codex): `Read`, `Glob`, `Grep`

## Workflow

### 1. Extract Feedback Events

Scan the full conversation history for the most recent `/gap-analysis` or
`/execute-plan` invocation and everything that followed it. Identify every
instance where the user:

- **Corrected** an output (e.g. "that's wrong", "no, it should be X")
- **Redirected** the approach (e.g. "don't do it that way", "use Y instead")
- **Added missing context** that Codex should have known or discovered
  (e.g. "you missed Z", "check the spec for W")
- **Refined quality** (e.g. "make this more detailed", "this is too verbose",
  "wrong format")
- **Repeated themselves** — gave the same feedback they've given before, meaning
  a prior improvement wasn't captured

For each event, record:
- **trigger** — what Codex did or produced that prompted the feedback
- **feedback** — what the user said (quote or close paraphrase)
- **resolution** — what Codex did in response
- **phase** — which step of the command workflow this occurred in

Present the extracted events to the user as a numbered list for confirmation
before proceeding. The user may add events that were missed or remove ones that
aren't worth addressing.

### 2. Classify Root Causes

For each confirmed feedback event, use an **Codex subagent** to determine the
root cause. The subagent should read the relevant command file(s) and classify
each event into one or more categories:

- **instruction_gap** — the command doesn't instruct this behavior; Codex had
  to be told. Fix: add explicit instruction to the command.
- **instruction_ambiguity** — the command says something but it's unclear or
  easily misinterpreted. Fix: clarify the instruction.
- **missing_convention** — the project has an unwritten convention that Codex
  violated. Fix: document the convention in AGENTS.md or the relevant command.
- **missing_context** — Codex lacked information it needed and didn't know to
  look for it. Fix: add a search/read step to the command workflow.
- **quality_bar** — Codex's output met the letter of the instructions but not
  the user's quality expectations. Fix: add quality criteria or examples.
- **wrong_default** — Codex made a reasonable choice but the user prefers a
  different default. Fix: encode the preference.
- **tool_misuse** — Codex used the wrong tool or used a tool incorrectly.
  Fix: add tool guidance to the command.
- **scope_creep** — Codex did more or less than was asked. Fix: tighten scope
  boundaries in the command.

Present the classification to the user for confirmation.

### 3. Propose Process Changes

For each classified root cause, use an **Codex subagent** to draft a specific,
minimal change to the appropriate file. The subagent reads the target file and
proposes:

- **target_file** — which file to change (e.g. `codex/patches.json`,
  `AGENTS.md`, a skill's `SKILL.md`)
- **change_type** — one of: `add_instruction`, `clarify_instruction`,
  `add_workflow_step`, `add_convention`, `add_quality_criteria`, `add_example`
- **location** — where in the file the change belongs (section name or after
  which line)
- **content** — the exact text to add or the before/after for a clarification
- **rationale** — one sentence explaining what feedback this prevents

Guidelines for proposals:
- Prefer the smallest change that prevents the feedback. Don't restructure
  entire commands to fix one issue.
- If multiple feedback events share a root cause, propose one change that
  addresses all of them.
- If a change would make a command significantly longer, consider whether a
  convention in AGENTS.md would be better.
- Changes must be consistent with existing command style and conventions.

### 4. Present and Prioritize

Show the user:

1. **Feedback summary** — table with columns: #, Phase, Trigger (brief),
   Root Cause, Proposed Fix (brief)
2. **Proposed changes** — grouped by target file, each with full content and
   rationale
3. **Impact estimate** — for each change, how many feedback events it would
   have prevented

Sort proposals by impact (most feedback events prevented first).

### 5. Apply Approved Changes

Wait for the user to approve, modify, or reject each proposal. Then apply
all approved changes:

- Use `Edit` for modifications to existing files
- Use `Write` only for new files
- After applying, re-read each modified file to verify the change fits
  naturally in context

### 6. Update Memory

If any approved changes reveal stable patterns or preferences that apply
beyond a single command, note them in the auto memory directory so they
persist across sessions. Only record durable insights — not session-specific
fixes.

### 7. Commit

Stage all changes with `git add -A` and commit with a message like:
`process: incorporate feedback from [gap-analysis|execute-plan] session`

Don't push.
