---
name: summon
description: >-
  This skill should be used when the user says "summon", "summon grimoire",
  "/summon", "initialize grimoire", "start an audit", "begin security review",
  "set up audit workspace", "kick off security research", "scope a codebase",
  "map a codebase for security", "prepare for an audit", or wants to initialize
  Grimoire on a new codebase. Also use it when invoked with a bug-bounty program
  URL or slug (e.g. "/summon immunefi.com/bug-bounty/<program>", "summon from a
  bug bounty program", "set up from an Immunefi/Cantina program", "fetch the
  scope and clone the repos") — in that case it first fetches the program scope
  and clones the in-scope repositories before initializing. This is the first
  skill run on a new engagement. It builds initial context, creates the audit
  workspace structure, and produces GRIMOIRE.md — the living contextual map that
  primes all future agent interactions for security research.
user_invocable: true
---

# Summon

Initialize Grimoire on a new codebase. Build context, create the audit workspace, and produce
`GRIMOIRE.md` — the living contextual map for this security engagement.

## Philosophy

**Build context first.** Top researchers always establish contextual understanding before hunting
for bugs. Summon explores the target, builds a map, and gives you and future agents the context
needed to do meaningful work. Keep GRIMOIRE.md concise — it is loaded into every agent context.
Detailed notes belong in `grimoire/tomes/`.

## Workflow

When this skill is activated, create a todo list from the following steps. Mark each task
in_progress before starting it and completed when done.

```
- [ ] 0. Acquire target from bug bounty program — fetch scope, resolve & clone in-scope repos  (ONLY if invoked with a program URL/slug)
- [ ] 1. Verify workspace layout — confirm directory structure, identify in-scope repo(s)
- [ ] 2. Create audit directory structure — set up grimoire/, findings/, hypotheses/, spells/, tomes/, report-deliverables/
- [ ] 3. Build initial context — language, tooling, frameworks, integrations, problem & approach
- [ ] 4. Map architecture and flows — identify structure, primary flows, key components
- [ ] 5. Identify crown jewels — determine high-impact targets and threat model
- [ ] 5b. Capture scope constraints — capability vs trust assumptions, out-of-scope, invariants
- [ ] 6. Write GRIMOIRE.md — assemble the contextual map
- [ ] 6b. Write kickoff questions — what to ask the client on the kickoff call
- [ ] 7. Review GRIMOIRE.md — kick off subagent to verify accuracy and trim bloat
- [ ] 8. Surface automation opportunities — check for spellbook modules to run
- [ ] 9. Spawn sigil swarm — run checks-based sigils against the codebase
```

---

### 0. Acquire Target from a Bug Bounty Program

**Run this step only when summon is invoked with a bug-bounty program URL or slug** (e.g.
`/summon immunefi.com/bug-bounty/<program>`). If invoked with no argument, or with a local path,
skip directly to Step 1.

The goal is narrow: turn a program URL into (1) the in-scope source repositories cloned at their
pinned commits and (2) a `scope/bounty-program.md` capturing assets, impacts, and rules. The rest
of the workflow then runs normally, with Crown Jewels (Step 5) and Scope Constraints (Step 5b)
pre-seeded from the program data.

Consult `references/bounty-platforms.md` for the host→handler map, per-platform scope locations
(Immunefi, Cantina), the generic fallback, and asset-resolution rules.

**0a. Detect platform.** Normalize the argument (full URL, `host/path`, or bare host + slug) to a
canonical program URL and identify the platform by host (Immunefi / Cantina / generic).

**0b. Fetch scope.** Use `WebFetch` against the platform's scope and rules pages with a targeted
extraction prompt. Extract: program name; **assets in scope** (each: identifier/URL, type, pinned
ref + subpath if shown, tier); **impacts in scope** by severity; **out-of-scope** assets/impacts;
**rules / prohibited actions / KYC**; reward tiers; source URL + fetch date. These pages are
JavaScript-rendered — if the fetch returns no usable scope (Cloudflare, login wall, empty shell),
**do not fabricate scope**: ask the user to paste the scope text or supply the in-scope repo URLs
and commits directly.

**0c. Establish project root.** If the current directory is not already a suitable project dir,
create `<program-slug>/` under cwd and treat it as the project root for everything that follows.
Warn if cwd appears to be inside an existing repo (same reasoning as Step 1).

**0d. Resolve assets → repos.** Parse asset URLs into `{repo_url, ref, subpath}` and dedupe by
`(repo_url, ref)`. Separate **cloneable** git repos from **non-cloneable** assets (deployed
contract addresses, live web/infra targets) — the latter are recorded but have no local source.

**0e. Confirm & clone.** Present the resolved asset list (cloneable repos with pinned refs, plus
non-cloneable assets). Cloning is a side-effecting operation — get explicit user approval, and let
the user deselect repos (bounty repos can be large). On approval, run `scripts/clone-assets.sh`
from the project root, passing approved entries as `<repo_url>@<ref>` tokens (or via
`--from-file`). Report what cloned, skipped, and failed.

**0f. Write scope materials.** Create the `scope/` directory and write `scope/bounty-program.md`
capturing the fetched data — assets (cloneable and non-cloneable), impacts by severity,
out-of-scope items, rules/prohibited actions, KYC, reward tiers, and the source URL + fetch date.
Steps 5 and 5b read this file.

After Step 0 completes, continue to Step 1. The workspace layout is now satisfied (project root
created, repos cloned, `scope/` populated), so Step 1 is largely a confirmation.

---

### 1. Verify Workspace Layout

> If Step 0 ran, the project root was created, the in-scope repos were cloned, and `scope/` was
> populated — this step is then just a confirmation that the cloned repos match the program scope.

Check the current working directory. The ideal layout is:

```
project/          <-- cwd
    in_scope_repo/
```

The project directory should contain the repository (or repositories) that are in scope. Grimoire
creates its own files and directories alongside (not inside) the scoped code.

**Verify:**
- Are we in a directory that contains one or more code repositories?
- Are we accidentally inside the repo itself? (If so, warn the user and suggest moving up)
- Is there a git repo at the current level that would conflict? (Grimoire artifacts should not
  pollute the scoped repo's git history)

If multiple repositories are in scope, identify each one. GRIMOIRE.md should cover all in-scope
repos in a single document, with architecture and flows sections clearly delineating per-repo
structure where they differ.

If the layout looks wrong, explain the expected structure to the user and ask them to confirm or
adjust before proceeding. Do not silently continue with a bad layout.

If the user has additional context available (meeting notes, scope documents, prior audit reports),
ask whether they'd like to point Grimoire at those directories.

### 2. Create Audit Directory Structure

Create the following directories if they don't already exist:

```
project/
    in_scope_repo/              # already present
    grimoire/
        findings/               # findings during this audit
            SESSIONS.md         # session log: history (see below)
            invalid/            # discarded, closed or invalidated
            valid/              # valid / submitted
            WIP/                # every new finding file lands here
            original-findings/  # findings-repo mirror kept by /findings-sync
                CLOSED/
                originals/
                history/
        peer-review/            # reviews of findings by peers or AI agents (/peer-review)
            SESSIONS.md
            archived/           # discarded, closed or invalidated
            done/               # valid / submitted
            WIP/                # every new peer-review file lands here
        mitigation-review/      # client-fix reviews (/mitigation-review)
            SESSIONS.md
            archived/           # discarded, closed or invalidated
            done/               # review closed
            PENDINGS/           # partially fixed / invalid mitigation, waiting on the client
            WIP/                # every new mitigation-review file lands here
        hypotheses/             # leads not yet proven or disproven
            SESSIONS.md
            invalid/            # discarded, closed or invalidated
            valid/              # promoted to a finding (its write-up starts in findings/WIP/)
            WIP/                # every new hypothesis file lands here
        sigil-findings/         # findings sourced from sigil agents
        spells/                 # scripts, PoCs, static analysis modules
        tomes/                  # documentation, detailed notes, learnings
            SESSIONS.md
            LINKS.md            # owner + copies of each topic shared across tomes (tome skill, references/links.md)
            active/
            archived/           # record of old work only; outdated, likely invalid, never read
        delves/                 # one <session-id>/ per /delve run (board.md, leads/); for /dig-mode
        client-communication/   # conversations with the client: one <finding-ID>.md per finding
            SESSIONS.md
            kickoff-questions.md  # questions for the kickoff call (created in step 6b)
        report-deliverables/
            protocol-summary.md
            executive-summary.md
        tmp/                    # temporary files and scripts
    GRIMOIRE.md                 # main contextual map (created in step 6)
```

Create `protocol-summary.md` and `executive-summary.md` as empty files; they are filled in later
in the engagement.

Create `tomes/LINKS.md` with the header and rules from the tome skill's `references/links.md` and no
rows yet. Rows are added as soon as a topic is written into a second tome.

**Session logs.** `findings/`, `hypotheses/`, `peer-review/`, `mitigation-review/`, `tomes/` and
`client-communication/` each get a `SESSIONS.md` at their root, so any file in them can be traced
back to the Claude Code session that worked on it and resumed there (`claude --resume <session-id>`).
The session ID is always read from `$CLAUDE_CODE_SESSION_ID`, never guessed. There are two kinds:

- **Status snapshots** — `hypotheses/`, `peer-review/` and `mitigation-review/`. One row per file,
  holding only its current state: the folder it is in now, the last session that worked on it, when,
  and a short note (verdict, claim, what the client was asked). Every create or move replaces the
  file's row; history is not kept here. Always write it with `scripts/session-status.sh` (this
  skill's), which replaces the row under a lock so parallel sessions never lose each other's
  updates; never edit the table by hand:

  ```bash
  <summon>/scripts/session-status.sh grimoire/<folder>/SESSIONS.md <file-name> <status> "<note>"
  ```

  It creates the file with this header if missing:

  ```markdown
  | File | Status | Session ID | Updated | Notes |
  |---|---|---|---|---|
  ```

- **History logs** — `findings/`, `tomes/` and `client-communication/`. Every create or move appends
  a row, and rows are never deleted; a file's rows are its history. Create each with this header:

  ```markdown
  | File | Session ID | Date | Event | Notes |
  |---|---|---|---|---|
  ```

  The event is `created in <subfolder>` (e.g. `WIP` or `tomes/active`; `created` for the flat
  `client-communication/`) or `moved <from> → <to>`. Add rows with a shell append (`>>`), never by
  reading and rewriting the file, so rows from parallel sessions are never lost.

The `original-findings/` mirror is not logged: `/findings-sync` writes it, not a research session.

**Hypothesis files.** Every `hypotheses/` file uses this format, wherever it was created (by hand or
by `/delve`), so a lead's outcome can always be read from the file and its folder:

```markdown
---
source: <delves/<session-id>/leads/<lead>.md, one per line, or `manual`>
outcome: <empty in WIP/ | promoted: findings/WIP/<file>.md | invalid: <why> | expected behavior: <why>>
claimed-by: <empty, or the session ID validating it now>
---
# <hypothesis title>

<the behavior, where it appears (`path:line`), why it may matter, what would confirm or refute it>

## Notes
<work log: what was checked, with dates>
```

Moving a file out of `WIP/` sets `outcome:`. Both `invalid` (the attack does not work) and
`expected behavior` (it works as designed) go to `invalid/`.

**Findings and hypotheses stay in sync.** A finding promoted from a hypothesis carries a
`hypothesis:` link in its front matter, and the hypothesis's `outcome:` points back at the finding.
Whenever such a finding moves between `valid/` and `invalid/`, move its hypothesis the same way in
the same step:
- **Finding rejected** (`findings/valid/` or `WIP/` → `findings/invalid/`): move the hypothesis
  `valid/` → `invalid/`, set `outcome: invalid: finding rejected — <why>`, and add a dated line to its
  `## Notes` saying which finding it was promoted to and why that finding was rejected.
- **Finding reinstated** (`findings/invalid/` → `valid/` or `WIP/`): move the hypothesis back to
  `valid/` and restore `outcome: promoted: <finding path>`, with a dated note.

Update the links in both files to the new paths, update the hypothesis's row in
`hypotheses/SESSIONS.md` (`session-status.sh`), and append the move to `findings/SESSIONS.md`. A
finding with no `hypothesis:` link moves alone.

**Finding submitted.** `findings/valid/` holds submitted findings. When the user says a finding in
`findings/WIP/` was submitted (posted to the findings repo, or sent in the report), act in the same
turn, without waiting to be asked:
1. Move the file `findings/WIP/<name>.md` → `findings/valid/<name>.md`. Never overwrite: check the
   name is free first.
2. Update every link to its old path: the hypothesis's `outcome: promoted: <path>`, and any tome,
   `tomes/LINKS.md` row or client question that names it (`grep -rl "findings/WIP/<name>.md" grimoire/`).
   The finding's own `hypothesis:` link does not change; the hypothesis stays in `hypotheses/valid/`.
3. Add a dated line to the hypothesis's `## Notes` ("finding submitted"), update its row in
   `hypotheses/SESSIONS.md` (`session-status.sh … valid "…; finding submitted, now findings/valid/<name>.md"`),
   and append a `submitted` row to `findings/SESSIONS.md` with the issue number if the user gave one.
4. Tell the user where the file went and which links changed.

If the user only says they are about to submit, or the submission is pending review, leave the file in
`WIP/`. If a submitted finding is later rejected, the "Finding rejected" rule above applies.

**Client communication.** One file per finding, `client-communication/<finding-ID>.md`, holds every
question asked to the client about that finding and its answer. Questions are numbered in the order
asked and never rewritten; a follow-up is a new question. Create the file with the first question:

```markdown
# <finding-ID> — <finding title>

## Q1 — <YYYY-MM-DD>
**Question:** <what was asked>
**Answer (<YYYY-MM-DD>):** <the client's answer, or `pending`>
**Outcome:** <what the answer changed: verdict, severity, scope, next step>
```

Documents in `grimoire/tomes/` are cross-linked from GRIMOIRE.md using Obsidian-style wiki links:
`[[tomes/auth-flow]]` links to `grimoire/tomes/auth-flow.md`.

Optionally create if the user indicates they have relevant materials:
```
    meeting_notes/              # context from client meetings
    scope/                      # scope documentation from client (Step 0 populates this
                                #   with bounty-program.md when summoned from a bounty URL)
```

Do not overwrite existing directories or files.

### 3. Build Initial Context

Explore the in-scope repository to answer these questions. Use subagents to parallelize exploration
where possible.

**Concrete details:**
- What programming language(s) are used?
- What build system / package manager is used?
- What test framework is used?
- What major frameworks or libraries does the project depend on?
- What external systems does the project integrate with? (databases, APIs, blockchains, message
  queues, cloud services)

**Problem and approach:**
- What problem is this project trying to solve?
- At a high level, what approach does this project use to solve it?
- Who are the users / actors in the system?

Start by reading documentation if available (README, docs/, wiki). Then scan the codebase
structure, dependency manifests, and configuration files. Documentation conveys intent; code
conveys reality. Cross-reference both.

**Collect kickoff questions (steps 3–5b).** While exploring, note anything worth asking the client
on the kickoff call: an unusual mechanism, a protocol-specific concept, a gap between the docs and
the code, or missing information needed to connect the two. Tell every exploration subagent to
return its candidate questions with its results, each with the evidence that raised it (`path:line`
and/or the doc passage). Before keeping a question, check that the code and docs can't answer it.
The questions are written to a file in step 6b.

### 4. Map Architecture and Flows

Dive deeper into the codebase to understand structure and behavior. Use subagents to explore
individual modules, components, or flows in parallel. Keep the main context focused on assembling
the map.

**Architecture (structure):**
- How is the codebase organized? (modules, packages, layers)
- What are the key components and how do they relate?
- Where are the system boundaries? (entry points, external interfaces)
- Are there implicit relationships that aren't obvious from call graphs? (e.g., input validated
  in one place, consumed in another; shared state; event-driven coupling)

**Primary flows (behavior):**
- What are the main activities / use cases?
- For each primary flow: what steps are involved, and how does execution flow through the system?
- Where does authentication and authorization happen?
- Where does data enter and leave the system?

Keep this high-level. The goal is a map for navigation, not a line-by-line audit. Detailed flow
analysis belongs in `grimoire/tomes/` and will happen during the actual research.

### 5. Identify Crown Jewels

Determine what matters most from a security perspective. In the end, we care about bugs that have
**impact**. Crown jewels are the assets and capabilities that attackers would target.

If Step 0 ran, seed this assessment from the program's **impacts in scope** (in
`scope/bounty-program.md`) — the bounty's severity-ranked impacts are an explicit statement of
what the program values most. Map each in-scope impact to the asset and code location it targets.

**Common crown jewels by domain:**
- **Smart contracts:** funds, governance control, oracle manipulation, protocol invariants
- **Web applications:** user accounts, authentication tokens, PII, payment data, admin access
- **Infrastructure:** RCE, privilege escalation, lateral movement, secrets/credentials
- **APIs:** data exfiltration, rate limiting bypass, authorization bypass

**For each crown jewel, note:**
- What is the asset?
- Where in the code is it handled?
- What are the likely attack vectors?
- What would successful exploitation look like?

Consult `references/domain-crown-jewels.md` for a comprehensive breakdown of assets, attack
vectors, and exploitation patterns by domain.

This is an initial assessment. The user will refine crown jewels as the engagement progresses.
GRIMOIRE.md is living memory.

### 5b. Capture Scope Constraints

Scope constraints are what the familiar agent uses to decide whether a finding is in or out
of bounds. Capture them structurally, not as prose. Read any materials the user pointed you
at (`scope/`, `meeting_notes/`, or client-provided docs) — including `scope/bounty-program.md`
when Step 0 ran — and extract:

- **Capability assumptions** — statements that bound what a privileged actor *can do*.
  These foreclose findings whose attack path falls strictly within the granted capability.
  Example: *"the pauser role can only pause and unpause"*, *"the oracle only updates
  prices, never arbitrary storage slots"*.
- **Trust assumptions** — statements that an actor will behave *honestly*. These do NOT
  foreclose findings; they only describe expected behavior. Example: *"admin is assumed
  to be honest"*, *"the sequencer will not censor transactions"*.
- **Out-of-scope components** — files, contracts, or flows the engagement explicitly
  excludes. Cite the source of the exclusion.
- **Protocol invariants** — properties the scope claims are maintained. These are useful
  targets: an exploit that breaks an invariant is a valid finding even when the attacker
  is nominally in scope.

When summoned from a bounty program, map the fetched fields onto this taxonomy: in-scope/
out-of-scope **assets and impacts** become the In-scope / Out-of-scope lists (cite the program as
source); **prohibited actions and program rules** become capability or trust constraints (a rule
that bounds what a privileged actor may do is a capability assumption; a rule describing expected
honest behavior is trust); record **KYC** requirements as a note in the Scope section.

When a clause is ambiguous, classify it as **trust** (the weaker claim). This errs toward
surfacing findings rather than silently dismissing them.

If no scope materials exist, say so explicitly in the Scope section rather than leaving
it empty — downstream triage needs to know the constraints are unknown, not assume none
exist.

### 6. Write GRIMOIRE.md

Assemble findings from steps 3-5 into `GRIMOIRE.md` at the project root. This file serves as:
- Initial context for the researcher
- Context primer for all future agent interactions
- A living document that evolves during the engagement

**Template:**

```markdown
# GRIMOIRE — [Project Name]

> Summoned: [date]

## Target

- **Language:** [languages]
- **Build/Test:** [build system, test framework]
- **Frameworks:** [key frameworks/libraries]
- **Integrations:** [external systems]
- **Bounty:** [platform + program URL + reward tiers — only if summoned from a bounty program]

## Problem & Approach

[2-3 sentences: what the project does and how]

## Scope

- **In-scope:** [paths / contracts / components covered by this engagement; for bounty programs,
  note the cloned repo(s) and pinned commit(s)]
- **Out-of-scope:** [explicit exclusions, with source]

### Capability assumptions (foreclose within granted capability)
- [role or actor]: can only [narrower capability]. Source: [scope doc / clause]

### Trust assumptions (context only; do not foreclose findings)
- [actor]: assumed to [act honestly / not behave adversarially]. Source: [scope doc / clause]

### Protocol invariants (claimed to hold)
- [invariant statement]. Source: [scope doc / clause]

[If no scope materials were provided: state "No scope materials available — constraints
unknown" so downstream triage is not silently uncalibrated.]

## Architecture

[High-level component map. Use a simple list or ASCII diagram. Keep it scannable.]

## Primary Flows

[List the main use cases / activities. For each: 1-2 line description of the flow path through
the system. More detail belongs in grimoire/tomes/.]

## Crown Jewels

[For each high-value target: asset, location, likely attack vectors. Bulleted list.]

## Attack Surface Notes

[Initial observations about security-relevant patterns, trust boundaries, areas that warrant
deeper investigation. Keep this brief — it will grow during the engagement.]

## Automation

[List any spellbook modules that were run or are available to run. Note results if applicable.]
```

**Important constraints:**
- Keep GRIMOIRE.md concise. It will be loaded into every agent context.
- Use `[[document-name]]` cross-linking to reference detailed notes in `grimoire/tomes/`.
- Do not include line-by-line code analysis. That belongs in tomes.
- Consult `examples/grimoire-md-example.md` for a concrete reference of what a completed
  GRIMOIRE.md looks like.

### 6b. Write Kickoff Questions

Write the questions collected in steps 3–5b to `grimoire/client-communication/kickoff-questions.md`.
This file is about the protocol as a whole; questions about a single finding go in that finding's
`<finding-ID>.md`. If the file already exists, add new questions after the last ID and do not
rewrite earlier ones. Append a `created` row to `client-communication/SESSIONS.md`.

**What to ask:**
- **Spec ↔ implementation gaps** — the docs say one thing and the code does another; code behavior
  with no spec; a documented feature not found in the code; a value, formula or threshold the docs
  do not explain.
- **Unusual mechanisms** — non-standard designs, custom math, odd ordering or state transitions,
  workarounds: why was it built this way, and what does it protect against?
- **Concepts** — protocol-specific terms, external dependencies or integrations whose intended
  semantics are unclear.
- **Scope, roles and deployment** — ambiguous clauses from step 5b, the intended capabilities of
  each privileged role, off-chain or out-of-repo components, deployment targets, configuration
  and parameter values, upgrade paths.
- **Invariants and edge cases** — what must always hold, and what should happen in an edge case the
  code handles in a surprising way (or not at all).

**Rules:**
- Ask only what the code and docs cannot answer. A question the reviewer can answer by reading is
  dropped.
- Every question cites its evidence, so the answer can be applied without re-exploring.
- Ask about intended behavior, not suspected bugs. If a question comes from a suspected bug, also
  open a hypothesis in `hypotheses/WIP/` and link it.
- Order each section by impact: questions that change scope, crown jewels or trust assumptions
  come first. List the most important 5–10 under **Priority** for a short call.

**Template:**

```markdown
# Kickoff questions — <Project Name>

> Prepared: <YYYY-MM-DD> · Call: <YYYY-MM-DD, or `not scheduled`>

## Priority
<5–10 question IDs to ask first if time is short, e.g. K3, K1, K7>

## Spec ↔ implementation gaps
### K1 — <short title>
**Question:** <what to ask the client>
**Why we ask:** <what the docs say (source) vs what the code does (`path:line`), or what is missing>
**What the answer changes:** <scope, a trust or capability assumption, a crown jewel, a hypothesis>
**Hypothesis:** <hypotheses/WIP/<file>.md, or `none`>
**Answer:** <`pending` until the call>

## Unusual mechanisms
## Concepts
## Scope, roles and deployment
## Invariants and edge cases
```

IDs (`K1`, `K2`, …) are unique across sections. Leave a section out if it has no questions.

**After the call:** fill each **Answer**, then fold what changes the map into GRIMOIRE.md (scope
constraints, invariants, crown jewels — cite `kickoff call <date>` as the source) and update any
linked hypothesis. A follow-up is a new question with a new ID.

When summoned from a bounty program there is usually no kickoff call. Write the file anyway, with
`Call: not scheduled`; it is the list for the program's support channel.

### 7. Review GRIMOIRE.md

After writing GRIMOIRE.md, kick off a subagent to review it. The subagent should read both
GRIMOIRE.md and the in-scope codebase independently to verify accuracy and flag bloat. Do not
skip this step — the main agent built context progressively and may have carried forward
assumptions or included too much detail.

**Subagent instructions:**

Give the subagent the following mandate. It should read GRIMOIRE.md and then independently spot-check
claims against the actual codebase:

1. **Accuracy check** — Verify factual claims against the codebase:
   - Are the listed languages, frameworks, and dependencies correct?
   - Do the described flows match what the code actually does?
   - Are referenced file paths and component names real?
   - Are crown jewel locations accurate?
   - Flag anything stated with confidence that the code contradicts.

2. **Bloat check** — GRIMOIRE.md is loaded into every agent context. Every unnecessary line
   degrades future agent performance. Flag:
   - Sections that repeat the same information in different words
   - Overly detailed flow descriptions that belong in `grimoire/tomes/`
   - Vague filler sentences that don't add navigational or security value
   - Content exceeding ~150 lines total (a strong signal of bloat)

3. **Completeness check** — Flag obvious gaps:
   - Major entry points or external interfaces not mentioned
   - Significant components missing from the architecture
   - Crown jewels that seem absent given the project domain

4. **Kickoff questions check** — Read `grimoire/client-communication/kickoff-questions.md`:
   - Drop questions the code or docs already answer (give the answer and its location).
   - Verify each cited `path:line` and doc passage.
   - Merge duplicates and flag questions phrased as accusations rather than about intent.
   - Flag gaps between docs and code it noticed that have no question.

The subagent should return a short list of specific corrections, cuts, and additions. Apply them
to GRIMOIRE.md and the kickoff questions before presenting the final version to the user. Show the user what the subagent
found and what was changed.

### 8. Surface Automation Opportunities

Check if the user has a spellbook (prior static analysis modules, detection scripts, or
research automation).

Look for:
- Existing `spells/` directory content from previous engagements
- Semgrep, CodeQL, or Slither rules
- Custom detection scripts

If automation modules exist:
- List what's available and briefly describe what each detects
- Ask the user which modules they'd like to run against the new codebase
- Run selected modules and provide an initial triage of results

If no spellbook exists yet:
- Note this in GRIMOIRE.md under Automation
- Note that automation modules can be built from findings as the engagement progresses

If the researcher has a personal grimoire (`~/.grimoire/sigils/`), list what's available and
suggest running the Scribe GC skill (`/scribe-gc` with scope "both") to check for duplicates
between personal and project-local sigils before applying them.

Note in GRIMOIRE.md under Automation that new detection modules can be distilled from findings
as the engagement progresses using the Scribe agent (`/scribe-distill`).

### 9. Spawn Sigil Swarm

After automation discovery, spawn sigil agents to hunt for known vulnerability patterns across
the codebase. Each sigil is a single-context agent that hunts one bug pattern using a check
from the spellbook.

Consult `references/sigil-spawning.md` for the subagent prompt template and detailed guidance.

**Index available checks.**

Run the `index-checks.sh` script from the checks skill's `scripts/` directory, passing
`grimoire/spells/checks/` as the target. If the directory does not exist or contains no
checks, note "No checks available — sigil swarm skipped" in GRIMOIRE.md under Automation
and skip this step. A fresh engagement with no prior checks is normal.

**Filter by language.**

Match each check's `languages` field against the languages identified in step 3 (the Target
section of GRIMOIRE.md). Only include checks whose language matches the target codebase.
Include checks with an empty or wildcard languages field regardless of target.

Run the `select-checks.sh` script from this skill's `scripts/` directory, passing
`grimoire/spells/checks/` and a comma-separated list of target languages from GRIMOIRE.md.
The script outputs only the checks that apply.

**Confirm with the user.**

Present the user with:
- How many applicable checks were found
- A brief list of check names and what they detect
- The estimated number of sigils to spawn

Ask whether to: **spawn all**, **select a subset**, or **skip**. Sigil spawning is the most
expensive operation in the workflow — the user must explicitly approve it.

If there are more than 20 applicable checks, warn about the time cost and suggest filtering
by tag or selecting a subset.

**Spawn sigils.**

For each approved check, spawn a subagent sigil. Process in batches of 5 to manage context
budget. For each check, give the subagent these instructions:

1. Read GRIMOIRE.md for engagement context
2. Read the check file at `<filepath>` for the vulnerability pattern
3. Hunt following the protocol in `references/sigil-spawning.md` — formulate a hypothesis from
   the check, search the codebase, evaluate evidence, produce a finding or dismiss
4. Write any findings to `grimoire/sigil-findings/<check-slug>.md` where `<check-slug>` is the
   check's filename without extension. If a check produces multiple findings, append a numeric
   suffix (e.g., `reentrancy-1.md`, `reentrancy-2.md`)
5. Return a hunt summary: check name, verdict (finding or dismissed), confidence, and file path
   if a finding was written

Wait for each batch of 5 to complete before spawning the next batch.

**Collect and present results.**

After all sigils complete, aggregate results. Present a summary:

```
## Sigil Swarm Results

Checks run: [N]  |  Findings: [N]  |  Dismissed: [N]

| Check | Verdict | Severity | Confidence | Finding |
|-------|---------|----------|------------|---------|
```

Group findings by severity (Critical/High first).

**Familiar Triage.** Invoke the familiar agent in batch triage mode (Mode 2) on
`grimoire/sigil-findings/`. The familiar will independently verify each finding, dismiss
false positives (moving them to `grimoire/sigil-findings/dismissed/`), and adjust severity
where warranted. Present the familiar's triage summary to the user instead of raw sigil
results.

**Update GRIMOIRE.md.**

Append to the Automation section:
- Number of checks run and findings produced
- Link to `grimoire/sigil-findings/` for details
- Note which checks were skipped (if any) and why

---

## Guidelines

- **Subagents for exploration.** Use subagents to parallelize codebase exploration. This keeps
  the main context clean and speeds up the process.
- **Cross-reference documentation and code.** Documentation describes intent; code describes
  reality. Discrepancies between the two are themselves interesting from a security perspective.
- **Ask, don't assume.** If something is ambiguous (scope, layout, priorities), ask the user.
- **Living document.** Remind the user that GRIMOIRE.md should be edited as they learn more.
  It's a starting point, not a final artifact.
- **Conciseness over completeness.** GRIMOIRE.md is a map, not an encyclopedia. Err on the side
  of too brief. Detailed notes go in `grimoire/tomes/`.
