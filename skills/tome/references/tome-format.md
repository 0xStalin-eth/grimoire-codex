# Tome Format

Use this reference when creating, updating, or routing tome pages.

## File Layout

Create tomes as markdown files under typed directories:

```text
grimoire/tomes/
    index.md
    actors/
        <slug>.md
    components/
        <slug>.md
    contracts/
        <slug>.md
    flows/
        <slug>.md
    mechanisms/
        <slug>.md
    trust-boundaries/
        <slug>.md
    risks/
        <slug>.md
    open-questions/
        <slug>.md
    notes/
        <slug>.md
```

Use kebab-case filenames. Keep one page focused on one security-relevant concept,
mechanism, actor, flow, component, contract, trust boundary, risk, open question, or
resolved research thread. Use `notes/` for durable context that does not cleanly fit
one of the stricter categories.

Use directories to make the wiki easy to browse as a human. The page `type` field and
the directory should agree.

| Page type | Directory |
|-----------|-----------|
| `actor` | `grimoire/tomes/actors/` |
| `component` | `grimoire/tomes/components/` |
| `contract` | `grimoire/tomes/contracts/` |
| `flow` | `grimoire/tomes/flows/` |
| `mechanism` | `grimoire/tomes/mechanisms/` |
| `trust-boundary` | `grimoire/tomes/trust-boundaries/` |
| `risk` | `grimoire/tomes/risks/` |
| `open-question` | `grimoire/tomes/open-questions/` |
| `note` | `grimoire/tomes/notes/` |
| `concept` | Choose the most relevant typed directory, usually `mechanisms/` or `components/` |
| `finding` | Prefer `grimoire/findings/`; use `risks/` or `open-questions/` for supporting research notes |

Supporting index files may live alongside tomes:

```text
grimoire/tomes/index.md
grimoire/tomes/notes/unverified-claims.md
grimoire/tomes/notes/contradictions.md
grimoire/tomes/notes/hypotheses.md
```

Create only the directories and files that are useful for the task. If they already
exist, update them.

## Frontmatter

Every tome uses YAML frontmatter:

```yaml
---
title: Human-readable title
created: 2026-10-01
updated: 2026-10-01
type: concept
topic: auth-flow
status: draft
targets:
  - project-name
versions:
  - commit-or-release
confidence: medium
sources:
  - src/Auth.sol:42-91
  - docs/auth.md
contested: false
contradictions: []
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | yes | Short descriptive title |
| `created` | yes | Creation date, `YYYY-MM-DD` |
| `updated` | yes | Last material update date, `YYYY-MM-DD` |
| `type` | yes | `concept`, `mechanism`, `actor`, `flow`, `component`, `contract`, `trust-boundary`, `risk`, `finding`, `open-question`, or `note` |
| `topic` | yes | Stable kebab-case topic identifier |
| `status` | yes | `draft`, `verified`, `stale`, or `contested` |
| `targets` | yes | Project, deployment, or subsystem names |
| `versions` | yes | Commit, tag, release, deployment, date, or `unknown` |
| `confidence` | yes | `high`, `medium`, or `low` |
| `sources` | yes | Files, docs, tests, traces, findings, or artifacts supporting the page |
| `contested` | yes | `true` when unresolved contradictions materially affect conclusions |
| `contradictions` | yes | Related contradiction IDs or links |

## Create Or Update

Create a new tome when:
- The topic has no existing durable note.
- The new material would make an existing tome unfocused.
- The research question is distinct enough to be linked independently.

Update an existing tome when:
- New evidence refines or corrects the same conclusion.
- The old note is stale but still the right home.
- You are compacting a conversation that continued the same research thread.

Create a page only when the topic is central to one strong source or supported by
multiple sources. Do not create one page per symbol. Split pages that exceed about
200 lines.

## Links

Use Obsidian-style links when referencing tomes:

```markdown
[[tomes/flows/auth-flow]]
```

Add links from `GRIMOIRE.md` only when the tome contains important context future
agents should discover early. Do not bloat `GRIMOIRE.md` with details that belong in
the tome.
