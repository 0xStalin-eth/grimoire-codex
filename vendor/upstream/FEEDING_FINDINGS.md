# Feeding Pre-Grimoire Findings into Grimoire

This guide explains how to bring findings from audits conducted before you started using
grimoire into the knowledge base, so future engagements benefit from that accumulated
experience.

---

## Overview

Grimoire has two complementary mechanisms for storing and using past knowledge:

| Mechanism | What it does | When it helps |
|-----------|-------------|---------------|
| **Librarian** | Stores findings as searchable reference material | When you or grimoire actively query for prior art |
| **Scribe sigils** | Encodes repeatable vulnerability patterns as automated detectors | Automatically, on every future `/summon` |

The recommended approach is to do both: register all your past findings as a library for
broad searchability, then distill the structurally repeatable ones into sigils for
automated detection.

---

## Step 1 — Organise your past findings

Your findings do not need to be in grimoire's native format for the librarian to index
them. Any readable format works: markdown, plain text, PDF-derived text, or your own
report structure. However, the closer they are to structured markdown the better the
semantic search quality will be.

If your findings are scattered across various formats, consider consolidating them into
a single directory organised by audit or vulnerability class before proceeding. A
flat directory of markdown files is sufficient.

### File granularity

The right level of granularity depends on what you want to do with the findings:

| Goal | File structure |
|------|---------------|
| Librarian search only | One file per engagement is fine — the indexer chunks by heading, so each finding section becomes its own searchable chunk |
| Scribe distillation | One file per finding — the distill workflow reads a single finding file and expects its frontmatter to describe one vulnerability |

The practical approach: register your existing engagement files as-is for immediate
library coverage. Only split into individual files for the specific findings you decide
to distill. You do not need to convert everything upfront.

### Grimoire's native finding format

This format is recommended for files you plan to distill, as it maps cleanly onto what
the scribe needs to extract:

```markdown
---
title: <where> / <how> / <what> — e.g. "Theft of deposited funds via reentrancy in Vault.withdraw()"
severity: Critical | High | Medium | Low | Informational
type: reentrancy | access-control | dos | arithmetic | logic | ...
context:
  - src/ContractName.sol:142-158
---

## Description

What is wrong and what is the impact.

## Details

Technical deep-dive for complex mechanisms (optional).

## Recommendation

What needs to change (not how to rewrite the code).

## References

- [1] Link or citation (optional)
```

A good title follows the **where / how / what** rule: component, mechanism, impact.

---

## Step 2 — Register the findings directory as a library

Run `/modify-library` or instruct grimoire directly:

**Local directory (most common):**

```
add a local library called past-findings at /absolute/path/to/your/findings/
```

**Git repository:**

```
add a git library called past-findings from git@github.com:you/audit-findings.git
```

Grimoire validates that the path or URL is reachable before writing anything. The entry
is recorded in:

```
~/.grimoire/librarian/library/libraries.yaml
```

Git libraries are cloned into:

```
~/.grimoire/librarian/library/<library-name>/
```

Symlink libraries are read directly from their source path.

---

## Step 3 — Index the library for semantic search

After registering, build the search index:

```
/librarian-index
```

This runs a local embedding pipeline (no API key, no network after the first model
download of ~80 MB) that chunks your finding files and stores them in a local Qdrant
vector database at `~/.grimoire/librarian/qdrant/`.

The index is idempotent — re-running it after adding or updating libraries is safe and
will not create duplicates.

From this point the librarian can retrieve relevant findings from your history when you
or grimoire search for prior art during an engagement.

> Re-run `/librarian-index` any time you add new findings to the library directory or
> register a new library with `/modify-library`.

---

## Step 4 — Distill repeatable findings into sigils

The librarian stores knowledge passively — it only helps when queried. Sigils go further:
they become automated detectors that run on every future codebase before you start manual
review.

Not every finding can or should become a sigil. The Scribe evaluates each finding and
classifies it as:

- **Static-feasible** — identifiable by searching for specific strings, function calls,
  or code shapes. Becomes a runnable check.
- **Agentic-feasible** — identifiable by grep but requires reading surrounding context
  to confirm. Becomes an agentic check with assessment criteria.
- **Not automatable** — requires deep business logic reasoning. Becomes a knowledge
  artifact (structured reference note) or is left as a library entry only.

### Which findings are worth distilling?

Prioritise findings that:

- You have seen recur across multiple protocols or codebases
- Have a clear structural code shape (missing check, wrong order of operations,
  unchecked return value, missing state update)
- Do not depend heavily on project-specific economics or off-chain context

Leave in the library only (do not distill) findings that:

- Were one-off logic errors tied to a specific protocol's business rules
- Required deep knowledge of an external system or oracle to identify
- Were highly context-dependent (e.g. "admin set a parameter too high for this protocol")

### Format requirements for distillation

The scribe distill workflow is agent-driven — it reads the finding file and extracts
information rather than parsing a strict schema. It can work with reasonable format
variations, as long as the finding contains enough information to extract:

- What the vulnerability is and what its impact is
- Where it is (file and ideally line references)
- How severe it is

**What works without issues:** The native grimoire format, or any structured markdown
with clear headings and a severity label.

**What causes friction:**

- No file/line references — the scribe cannot populate location info, which reduces
  the quality of the generalised pattern
- No clear severity label — the scribe needs this to set the sigil's default severity
- Unstructured prose with no headings or labels — harder to extract reliably and more
  likely to require back-and-forth clarification

If you are converting findings specifically for distillation, the native format is worth
using. For findings only going into the library, format matters much less.

### How to distill

You need a grimoire workspace to distill — `/summon` must have been run on some project.
You can use any project as the vehicle; it does not need to be a new engagement.

For each finding you want to distill:

1. Ensure the finding exists as its own individual file (one finding per file is required
   for distillation). It can live inside the library directory you registered, or be
   copied into the current project's `grimoire/findings/` directory.

2. Run:

   ```
   /scribe-distill
   ```

   Point the scribe at the finding file. It will:
   - Extract the generalizable vulnerability pattern (stripping project-specific details)
   - Assess automation feasibility
   - Create the detection module in `grimoire/spells/checks/` (for checks) or
     `grimoire/spells/knowledge/` (for knowledge artifacts)
   - Validate the output

3. After distilling a batch of findings, merge the generalizable sigils into your
   personal grimoire so they persist across all future engagements. There is no
   dedicated slash command for this — trigger it through natural language:

   ```
   merge sigils into personal grimoire
   ```

   or equivalently:

   ```
   promote generalizable sigils to the personal grimoire
   ```

   The scribe reviews each project-local sigil before merging, filters out anything
   too project-specific, and copies the generalizable ones to `~/.grimoire/sigils/`.
   Expect some back-and-forth during this step — it is not as automated as a named
   skill. Sigils only become available to future `/summon` runs after this merge
   completes.

### Bulk distillation tips

- Work in batches grouped by vulnerability class (all your reentrancy findings together,
  all your access-control findings together). This makes it easier to spot when the scribe
  is producing overlapping sigils.
- After each batch, run `/scribe-gc` to deduplicate and merge any overlapping detectors
  before continuing.
- You do not need to distill every finding in one session. The library is always there as
  a fallback; distillation is an ongoing process.

---

## Step 5 — Ongoing maintenance

| Task | When | Command |
|------|------|---------|
| Add a new findings directory or repo | After each audit, or when consolidating old work | `/modify-library` |
| Rebuild the search index | After adding or updating a library | `/librarian-index` |
| Distill new confirmed findings | At the end of each engagement | `/scribe-distill` then "merge sigils into personal grimoire" |
| Deduplicate the personal grimoire | Periodically, or when the sigil list feels cluttered | `/scribe-gc` |

---

## Summary

```
past findings directory
        │
        ├─── /modify-library ──────► ~/.grimoire/librarian/library/
        │                                       │
        │                            /librarian-index
        │                                       │
        │                            searchable via librarian
        │
        └─── /scribe-distill ──────► grimoire/spells/checks/  (per-project)
                                                │
                                     merge into personal grimoire
                                                │
                                     ~/.grimoire/sigils/  (runs on every /summon)
```

The library is the safety net — all knowledge is preserved and searchable. Sigils are
the compounding asset — they raise the detection baseline automatically on every future
engagement.
