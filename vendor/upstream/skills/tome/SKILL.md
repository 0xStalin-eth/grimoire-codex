---
name: tome
description: >-
  This skill should be used when the user says "tome", "/tome", "write a tome",
  "update a tome", "document this learning", "save this research note", "compact
  this context", "build a security wiki", "source-backed note", "track claims",
  "track contradictions", or wants to create or maintain durable security research
  notes in grimoire/tomes/. Tomes store verified conclusions, nuanced analysis,
  unresolved questions, and reusable context that is too detailed for GRIMOIRE.md
  but not necessarily a finding.
user_invocable: true
---

# Tome

Build and maintain a source-backed security research wiki inside `grimoire/tomes/`.
The durable artifact is the repository, not the chat response.

## Philosophy

`GRIMOIRE.md` is the concise map loaded into future context. Tomes are the library:
focused pages that preserve evidence, claims, uncertainty, contradictions, and
reasoning that would otherwise be lost during compaction.

Cartography tells future agents where things are. A tome tells them what has been
learned, why it is believed, what version or scope it applies to, and what remains
unknown. Before adding a claim to a tome, cross-check it against code, tests,
documentation, traces, deployments, or prior artifacts.

Do not convert inference into fact through repeated summaries. Do not hide
contradictions by choosing the most convenient source. If evidence is insufficient,
write the evidence gap clearly.

## Key Principles

- Keep `GRIMOIRE.md` concise and link outward to tomes.
- Tomes contain supported conclusions and reasoning; cartography contains navigation.
- Prefer updating existing tomes over creating near-duplicates.
- Keep shared topics in sync. `grimoire/tomes/LINKS.md` names one owner section per topic shared
  across tomes, plus its copies. Before editing a section, look it up there. If the edit changes a
  claim, update the owner and every copy in the same pass (owner → copies). A tome spun off or built
  from others starts as a copy of every topic it pulls in; when it goes deeper on its own subject,
  ownership of that topic transfers to it. See `references/links.md` (how owners are chosen, push up
  vs transfer); `/tome-sync` sweeps for drift that slipped past.
- Preserve useful negative results when they prevent repeated work.
- Mark uncertain material as open questions, not facts.
- Do not change evidence to match a conclusion.
- Documentation describes intent; matching code or observation describes behavior.
- Write full meanings, never one-letter placeholders for a quantity, a time or any other value (`T`,
  `t`, `X`, `x`), even after defining them once. Use the contract's name (`effectiveAt`,
  `newMultiplier`) or a plain phrase ("the split being re-applied", "the holder"), formulas and call
  examples included (`setUIMultiplier(1e18, effectiveAt)`, not `setUIMultiplier(1e18, t)`). Tome
  text is often pasted into reports and notes, so it follows the same rule as findings.

## Relationship To Grimoire

Use the existing project layout:

```text
project/
  GRIMOIRE.md
  grimoire/
    tomes/
    findings/
    sigil-findings/
    cartography/
    spells/
    tmp/
```

Tomes live in `grimoire/tomes/`. They may link to findings, cartography, PoCs, tests,
and source files. Do not create a separate `security-wiki/` repository unless the user
explicitly asks for one.

When a research task needs more structure, create these files under `grimoire/tomes/`:

```text
grimoire/tomes/
  index.md
  actors/
  components/
  contracts/
  flows/
  mechanisms/
  trust-boundaries/
  risks/
  open-questions/
  notes/
    unverified-claims.md
    contradictions.md
    hypotheses.md
```

Create only the directories and files that are useful for the task. If they already
exist, update them. Prefer the typed directories for human navigation over a flat pile
of pages. Use `notes/` for durable context that does not cleanly fit a stricter
category yet.

## Workflow

When this skill is activated and when you're answering a question, follow these steps.

### Base

```text
- [ ] 1. Orient to the existing grimoire
- [ ] 2. Define the research question in your own words
- [ ] 3. Answer the question using evidence from tomes if possible
- [ ] 4. Run the research workflow if the wiki is insufficient
```

### Research

```text
- [ ] 1. Identify where tomes lack evidence and what evidence is needed
- [ ] 2. Study related source material to acquire evidence
- [ ] 3. Update the wiki with new evidence-supported conclusions
- [ ] 4. Note unverified claims
```

The base workflow can use efficient, speed-oriented models. The research workflow should
always be executed by the most competent model possible.

Read `references/workflow.md` for the full procedure and completion criteria.

## Reference Files

- `references/evidence-model.md` — source precedence, support/state/confidence, claim
  blocks, and provenance.
- `references/tome-format.md` — `grimoire/tomes/` structure, frontmatter, page types,
  and routing.
- `references/page-templates.md` — templates for general, mechanism, flow, component,
  risk, and finding-candidate pages.
- `references/workflow.md` — base and research workflows with completion criteria.
- `references/health-check.md` — lint, review, and completion checklist for tome
  repositories.
- `references/links.md` — `LINKS.md`: owner and copies of each shared topic, editing rules,
  open drift.

Read only the references needed for the task, but always read `evidence-model.md` before
writing or changing claims, and `links.md` before editing a tome when `grimoire/tomes/LINKS.md`
exists.
