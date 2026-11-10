---
name: grimoire-execute-plan
description: "Implement the highest-priority downstream plan item with spec study, independent review and validation."
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


# Execute Plan

Implement the highest-priority item from the implementation plan by studying the
specification, learning from existing implementation patterns, building it completely,
and validating the result.

## Important Constraints

- The specification lives in the `vendor/upstream/grimoire/` directory. These files are written by a
  human and are the source of truth. NEVER modify them.
- The implementation lives in everything else at the repo root (`skills/`, `marker-groups/`,
  `codex/`, `README.md`, etc.) — everything outside `vendor/upstream/grimoire/`.
- The solution is NEVER to change the specification. Always extend or update the plugin.
- Never assume something isn't implemented. Always search first.
- Implement completely. No placeholders, stubs, or TODOs. Doing work twice wastes effort.
- Keep `IMPLEMENTATION_PLAN.md` current — update it with findings as you go.
- Use subagents heavily for reads and searches. Use Codex subagents for complex reasoning.

## Subagent Tools

All subagents spawned during this workflow need the following tools to function:
- **Step 1a subagents** (spec study): `Read`, `Glob`
- **Step 1b subagents** (pattern learning): `Read`, `Glob`
- **Step 1c subagents** (confirm non-existence): `Read`, `Glob`, `Grep`
- **Step 2 subagent** (plan design, Codex): `Read`, `Glob`, `Grep`
- **Step 3** (implement): uses `Write`, `Edit`, `Read`, `Glob`, `Grep` directly (not a subagent)
- **Step 4a** (skill review): uses a separate Codex reviewer context
- **Step 4b subagent** (spec compliance, Codex): `Read`, `Glob`, `Grep`
- **Step 5** (update plan): uses `Read`, `Edit` or `Write` directly (not a subagent)
- **Step 6** (commit): uses `Bash` directly (not a subagent)

When spawning subagents, explicitly grant them these tools so they can read spec files and
search the implementation.

## Paths

Anchor all file references to the repo root at `grimoire/` (the git repository root, NOT
`vendor/upstream/grimoire/`).

- **Spec directory:** `vendor/upstream/grimoire/` — contains subdirectories `skills/`, `agents/`,
  `concepts/`, and files like `README.md`, `notes.md`
- **Implementation root:** `grimoire/` — contains `skills/`, `marker-groups/`,
  `codex/project.json`, `README.md`
- **Implemented skills:** `skills/*/SKILL.md` (each skill has its own directory)
- **Implementation plan:** `grimoire/IMPLEMENTATION_PLAN.md`

These two trees are completely separate. Do not confuse `vendor/upstream/skills/` (spec)
with `skills/` (implementation).

## Workflow

### 0. Read the Plan

Read `IMPLEMENTATION_PLAN.md` at the repo root. Understand the full priority queue.

Select the **single most important item** from the Priority Queue section. This is the
top item — the one with the highest leverage, fewest blockers, and clearest spec. If the
top item has unmet dependencies that are also in the queue, implement the dependency first.

Only select from the Priority Queue — these are implementable items (skills, agents,
infrastructure). The Cross-Cutting Adoption section contains concepts and flows which are
not standalone work items; their recommendations are folded into the tasks of implementable
items they touch.

Announce the selected item and briefly explain why it's the right choice before proceeding.

### 1. Deep Study Phase

Launch these subagent groups **in parallel**:

#### 1a. Study the Specification (up to 10 Codex subagents)

For the selected item, spawn subagents to read ALL spec files listed in its
IMPLEMENTATION_PLAN.md entry, plus any related spec files. Each subagent reads one file
and extracts:

- Exact behaviors and capabilities described
- Interactions with other components
- Any constraints, principles, or design decisions
- Open questions or ambiguities

Merge these into a **spec summary** — a complete picture of what needs to be built.

#### 1b. Learn Implementation Patterns (2-3 Codex subagents)

Study the 2-3 most mature implemented skills (pick the ones with the most files/structure
in `skills/`). Each subagent reads an entire skill directory and reports:

- Directory structure (references/, examples/, scripts/)
- SKILL.md conventions (frontmatter fields, section structure, instruction style)
- How references support the skill workflow
- How examples demonstrate usage
- Any scripts and what they automate

Merge into a **pattern profile** describing what a well-built component looks like here.

#### 1c. Confirm Non-Existence (up to 10 Codex subagents)

Before building anything, **verify the item isn't already implemented** somewhere
unexpected. Spawn subagents to search:

- `skills/*/SKILL.md` for keywords from the spec
- `skills/*/references/` for related reference material
- `codex/` for relevant configuration
- Any other plausible locations

Each subagent reports what it found (or confirmed absent). If substantial implementation
already exists, STOP and reassess — the item may need updating rather than building from
scratch. Update IMPLEMENTATION_PLAN.md accordingly.

### 2. Plan the Implementation

Using the spec summary, pattern profile, and search results, use an **Codex subagent** to
design the implementation. The subagent should produce:

- **File list** — every file that needs to be created or modified, with purpose
- **Structure** — how the new component fits the established patterns
- **Content outline** — for each file, what sections/content it needs
- **Spec compliance** — how each spec requirement maps to an implementation element
- **Edge cases** — anything the spec is ambiguous about, with proposed resolution

Present this plan to the user briefly, then **proceed immediately** to implementation.
Do not wait for confirmation — the user trusts the process.

### 3. Implement

Build the component completely, following the plan from step 2 and the patterns from
step 1b.

Guidelines:
- Match the conventions of peer skills exactly (frontmatter format, section naming,
  instruction style, directory layout)
- Every spec requirement must map to something concrete in the implementation
- References should provide depth — not repeat what's in SKILL.md
- Examples should be realistic and demonstrate actual usage
- Scripts should automate repetitive parts of the workflow
- Single source of truth — don't duplicate content across files

Use Codex subagents for file reads/searches during implementation. Do the actual writing
yourself (not via subagent) so you maintain full context of what's been built.

### 4. Validate

After implementation is complete, run two validation passes:

#### 4a. Skill Review

Invoke the **skill-reviewer** subagent against the newly built component. This reviews
quality, triggering effectiveness, and best practices compliance.

#### 4b. Spec Compliance Check

Spawn an **Codex subagent** to compare the implementation against the original spec files.
The subagent should:

1. Re-read every spec file for the item
2. Read every implementation file just created
3. Produce a checklist: each spec requirement marked as covered or missing
4. Flag any implementation that goes beyond or contradicts the spec

#### 4c. Evaluate and Apply

Review the skill-reviewer recommendations and the spec compliance results together.

For each skill-reviewer recommendation:
- If it aligns with the specification and improves the implementation: **apply it**
- If it contradicts the specification: **reject it** (spec is source of truth)
- If it's about something the spec doesn't address: **apply it** only if it follows
  patterns established by peer skills

Apply all valid recommendations. Document any rejected recommendations and why.

### 5. Update the Plan

Update `IMPLEMENTATION_PLAN.md`:

1. Move the completed item from Priority Queue to the Completed section
2. Note what was built and any decisions made
3. If you discovered new gaps, issues, or debt during implementation, add them to the
   appropriate section (Priority Queue, Implementation Debt, or Needs Spec Work)
4. If you learned something about how the project works that future work depends on,
   capture it

### 6. Commit

Stage all changes with `git add -A` and commit with a descriptive message summarizing
what was implemented. The message should name the item and briefly describe what was built.

Don't push!
