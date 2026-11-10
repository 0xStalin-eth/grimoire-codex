# Grimoire: How-To-Use Manual

## What Is Grimoire?

Grimoire is a Claude Code plugin that structures your security research workflow — from initial codebase exploration through hypotheses, validation, finding write-ups, PoCs, peer and mitigation reviews, and building a personal library of reusable detection patterns.

**Install:** `claude --plugin-dir /path/to/grimoire`

---

## The Research Workflow

Every idea starts as a **hypothesis** and ends either as a **finding** or as a recorded **dead end**. Grimoire's skills move it along, and the folder a file sits in is its status.

```
                    research (you reading code, sigil agents, agent runs)
                         │                                   │
     manual idea / /write-hypothesis                      /delve
                         │                    writes delves/<session-id>/
                         │                       board.md + leads/<lead>.md
                         ▼                                   │
                 hypotheses/WIP/<name>.md  ◄─────────────────┘  (1 lead = 1 hypothesis,
                 (source: manual | delve lead)                   source: links back)
                         │
          /dig-mode ─────┤  your questions; reads delves, hypothesis notes,
          (anytime)      │  findings, client answers, reviews, tomes, code
                         ▼
               /validate-hypothesis
          explore → intent (/divine) → PoC (/write-poc) → familiar triage
                         │
                 verdict [you confirm] ── dig-mode to question it
        ┌────────────────┼──────────────────────┬──────────────────────┐
     Valid            Invalid           Expected behavior        Inconclusive
        │                │                      │                      │
 hypotheses/valid/   hypotheses/invalid/   hypotheses/invalid/    stays in WIP/
 outcome: promoted   outcome: invalid      outcome: expected      question →
        │                                                         client-communication/
        ▼                                                         <name>.md
 /finding-draft → findings/WIP/<name>.md   (hypothesis: link back)
        │
   polish, hag red-team, submit            ← manual for now
        ▼
 findings/valid/   (or findings/invalid/ if rejected later —
                    its hypothesis moves back to hypotheses/invalid/ with it)


 Next /delve reads hypotheses/ back: WIP → still a lead · valid → Guardrails (finding)
                                     invalid → Guardrails (dead end, with reason)
```

Findings written by others (peers, AI agents) and the client's fixes follow their own track:

```
 findings repo (GitHub) ──/findings-sync──► findings/original-findings/
                                                   │ (pulled automatically if empty)
               ┌───────────────────────────────────┴──────────────────────┐
         /peer-review                                            /mitigation-review
   peer-review/WIP → done | archived                 mitigation-review/WIP → PENDINGS → WIP …
                                                                    → done | archived
                                                     questions → client-communication/<ID>.md
```

---

## The Workspace Layout

`/summon` creates this next to the in-scope repositories:

```
grimoire/
    findings/               SESSIONS.md, WIP/, valid/, invalid/
        original-findings/  mirror of the findings repo (/findings-sync): CLOSED/, originals/, history/
    hypotheses/             SESSIONS.md, WIP/, valid/, invalid/
    delves/                 one <session-id>/ per /delve run: board.md, leads/
    peer-review/            SESSIONS.md, WIP/, done/, archived/
    mitigation-review/      SESSIONS.md, WIP/, PENDINGS/, done/, archived/
    client-communication/   SESSIONS.md, kickoff-questions.md, one <finding-ID>.md per finding
    tomes/                  SESSIONS.md, LINKS.md, active/, archived/
    report-deliverables/    protocol-summary.md, executive-summary.md
    sigil-findings/, spells/, tmp/
GRIMOIRE.md
```

**File lifecycle.** Every new file lands in `WIP/`. It moves to `valid/` or `done/` when it is valid or submitted, and to `invalid/` or `archived/` when it is discarded, closed or invalidated. A mitigation review waiting on the client goes to `PENDINGS/` and comes back to `WIP/` when the client answers.

**Session logs.** Each top-level folder has a `SESSIONS.md`, so you can pick up old work where it was left: find the file's row and run `claude --resume <session-id>`.
- In `hypotheses/`, `peer-review/` and `mitigation-review/` it is a **status snapshot**: one row per file with its current folder, the last session that worked on it, the date and a note. Every update replaces the row.
- In `findings/`, `tomes/` and `client-communication/` it is a **history log**: every create or move adds a row, and rows are never deleted.

**Hypotheses ⇄ findings ⇄ delves stay in sync.** A hypothesis file records where it came from (`source:`) and how it ended (`outcome:`). A promoted finding links back to its hypothesis. If the finding is rejected later, the hypothesis moves to `invalid/` too. Delve never stores a lead's status itself; it reads it from the hypothesis's folder.

**Tomes stay in sync through `tomes/LINKS.md`.** Tomes are meant to be read on their own, so a topic is often written in several of them. `LINKS.md` names one **owner** section per shared topic and lists its **copies**. Ownership is per topic: a tome built from others starts as a copy of everything it pulls in, and takes ownership of a topic once it becomes the place that topic is worked on in depth. When `/tome` changes a claim in a section, it updates the owner and every copy in the same pass (owner → copies), and adds rows when a new tome is spun off an old one. `/tome-sync` is the safety net: it sweeps for copies that drifted anyway (hand edits, other sessions, other skills), reports them, and fixes only what you approve.

**`tomes/archived/` is never read.** It keeps a record of old work; its conclusions are outdated and likely invalid. Every skill reads `tomes/active/` only.

---

## Stage 1: Initialize a New Codebase (automatic — you confirm the layout and scope)

### `/summon`

Run this first on any new codebase. It creates your `GRIMOIRE.md` — the living contextual map that all other skills use as their foundation.

**What it does:**
- Creates the workspace layout above
- Maps the architecture and identifies crown jewels (high-value targets)
- Writes `GRIMOIRE.md` — a structured summary of the protocol
- Writes `client-communication/kickoff-questions.md` — questions for the client kickoff call: spec ↔ code gaps, unusual mechanisms, unclear concepts, roles and invariants, each with its evidence
- Surfaces automation opportunities
- Can spawn a sigil swarm for initial vulnerability hunting
- With a bug-bounty program URL, first fetches the scope and clones the in-scope repositories

**When to use:** Once per engagement, at the start. Also in a separate fix checkout before `/mitigation-review` (that skill creates the layout itself if it is missing).

---

## Stage 2: Map Code Flows (automatic)

### `/cartography`

Explore and document specific code paths you want to understand deeply. Creates indexed YAML-frontmatter files that act as pointers to code (not explanations).

**Seeded:** Point it at a specific function/flow
**Unseeded:** Let it discover flows via subagent swarms

**Output format:** `path/to/file:symbol` notation — designed to be machine-readable for other skills.

### `/review-cartography`

Verify and update existing cartography files when code changes. Extends missing pieces, adds conditional execution paths, cross-references related flows.

### `/gc-cartography`

When you accumulate many flows, this detects overlaps (>40% component overlap triggers a flag) and merges duplicates. Keeps the flow library clean.

---

## Stage 3: Discover Leads (both — agents hunt and delve, you add your own hypotheses and dig)

### `/annotation`

Scans the codebase for `@audit` tags left by auditors or developers. Returns structured JSON with file, line, tag, content, and surrounding context.

**Use early** to catch already-flagged concerns.

### `/checks`

Create and apply vulnerability pattern checks against the codebase. Each check is a simple, targeted query.

**Philosophy:** "Many simple checks beat one complex check."

**Modes:**
- **Create** — define a new check for a pattern you've identified
- **Apply** — run existing checks against the codebase
- **Manage** — organize your check library

### Manual hypotheses

When something looks off while you read code, record it as `hypotheses/WIP/<name>.md`. `/write-hypothesis` does this for you from an idea or from the part of the conversation that explored it: it writes the file, narrows the possible outcomes into ruled out / open / confirmed using what was already established, logs it, and stops without investigating. (`/validate-hypothesis` also records an idea you give it, but then goes on to settle it.) Hypothesis files use one format: `source:` and `outcome:` front matter, a testable description with `path:line`, and dated `## Notes`.

### `/delve`

After autonomous research (sigil agents, long agent runs), `/delve` shows you what the agents found odd: near-misses, unexplained mechanisms, fragile assumptions. It ranks 3–7 leads on a board and lists known findings and dead ends separately, so you don't re-open them.

- Saves each run to `delves/<session-id>/` (`board.md` + one file per lead), so parallel delves never collide and any session can read them later
- Records every lead as a hypothesis in `hypotheses/WIP/` (or adds itself as a source of the existing one)
- Never picks a lead for you, never investigates, never moves a hypothesis

### `/dig-mode`

A question-and-answer mode for building context fast: you ask short questions, it gives short, plain answers with `path:line` references. Use it to learn a system, to understand the leads on a delve board, or to question a verdict before you confirm it.

- Point it at a saved delve (`delves/<session-id>/`) to work from another session
- Reads hypotheses, findings, client answers and reviews when a question touches past work, and labels each source ("From the hypothesis notes:", "From the client, <date>:")
- Stays on until you say "stop dig mode"

---

## Stage 4: Validate Hypotheses (automatic — you confirm the verdict and the filing)

### `/validate-hypothesis`

Settles one hypothesis from `hypotheses/WIP/`:

1. **Load** — reads the hypothesis and its delve leads; stops if a finding or dead end already covers it
2. **Explore** — traces the path in code and checks every sibling implementation (can use a `sigil` agent or the `librarian`)
3. **Check intent** — docs, tests, client answers, `/divine`
4. **Prove it** — `/write-poc`; a test showing the attack fails also counts
5. **Independent triage** — the `familiar` agent gets the evidence, not the verdict
6. **Verdict** [you confirm] — Valid, Invalid, Expected behavior, or Inconclusive
7. **File it** [you confirm] — Valid: hypothesis → `valid/`, draft → `findings/WIP/`. Invalid / Expected behavior: → `invalid/` with the reason. Inconclusive: stays in `WIP/`, question → `client-communication/`

Every check is written to the hypothesis's `## Notes` as it happens, so an unfinished validation can be resumed from the file alone.

---

## Stage 5: Document Findings (both — drafting is automatic, polishing and submitting are manual)

### `/finding-draft`

When a vulnerability is proven, use this to create a properly structured finding (`/validate-hypothesis` calls it for you on a Valid verdict and saves to `findings/WIP/`). It handles:
- Title construction (where/how/what rule)
- Severity estimation
- Vulnerability type classification
- All standard sections (description, impact, recommendation, PoC reference)

### `/finding-review`

Review an existing finding against best practices. Invokes a familiar agent for triage and a librarian for reference validation. Use before finalizing findings.

### `/finding-dedup`

When findings pile up, this identifies duplicates and similar issues. Classifies pairs as:
- **Duplicate** → delete one
- **Similar** → merge or cross-reference
- **Distinct** → keep both

### `hag` agent

Before you submit, ask the hag to red-team the finding from a bug-bounty host's perspective. It assumes the finding is overstated and rules for it only when the evidence forces it.

**Submitting:** moving a finding from `findings/WIP/` to `valid/` (or `invalid/` if it is rejected later) is manual for now. Log the move in `findings/SESSIONS.md`, and move its hypothesis with it when it is rejected.

---

## Stage 6: Write Proof-of-Concept (automatic)

### `/write-poc`

6-phase workflow for writing exploit code:

1. Gather vulnerability details
2. Define the exploit flow
3. Determine PoC approach
4. Write the PoC (via gnome agent)
5. Review (via familiar agent)

**Core principles:**
- **Minimum viable proof** — demonstrate the issue exists, nothing beyond that
- **Benign payloads only** — `alert(1)`, `sleep()`, `id` — never destructive
- **Parameterized targets** — localhost + variables, never hardcoded production URLs

Integrates with `forge-poc-templates` (Immunefi's Solidity PoC library, included as a submodule).

---

## Stage 7: Review Others' Findings and the Client's Fixes (automatic — you confirm verdicts and file moves)

### `/findings-sync`

Mirrors the engagement's findings repo into `findings/original-findings/`. Pulls new issues and updates changed ones, keeping the first version of each write-up in `originals/` and every replaced version in `history/`. Closed issues move to `CLOSED/`.

### `/peer-review`

Validates a finding written by a peer or an AI agent: reproduces it with a PoC, checks the mechanism, scope, severity and duplicates, verifies the proposed fix in an isolated copy, and gives a verdict. Pulls the findings mirror first if it is empty.

Files: `peer-review/WIP/` → `done/` (valid or submitted) or `archived/` (discarded or invalidated).

### `/mitigation-review`

After the audit, reviews the client's fix for each finding: maps report → issue → fix commits, runs pre-fix and post-fix PoCs, records a verdict, and drafts the write-up for the report. Runs in the checkout that has the fix commits, with its own fresh pull of the findings mirror.

Files: `mitigation-review/WIP/` → `done/` when closed, `archived/` when discarded. A **Partially fixed** or **Not fixed** review you move on from goes to `PENDINGS/`, its questions go to `client-communication/<ID>.md`, and the session that did the work is logged so you can resume it when the client answers.

### Client communication

`client-communication/<finding-ID>.md` keeps every question asked to the client about a finding, numbered in order, with the answer (or `pending`) and what it changed. Questions are never rewritten; a follow-up is a new question.

`client-communication/kickoff-questions.md` holds the protocol-level questions `/summon` prepares for the kickoff call. After the call, fill in the answers and fold what they change into `GRIMOIRE.md`.

---

## Stage 8: Build Your Detection Library (automatic)

### `/scribe-distill`

Transforms a finding into a reusable detection module. Extracts the generalizable vulnerability pattern so you can find the same class of bug in future codebases automatically.

**Output:** A `checks` file or knowledge artifact added to your spellbook.

### `/scribe-gc`

Deduplicates your sigil library when detection modules start overlapping.

### `/scribe-utilities`

Query your spellbook: list, describe, get stats, or search across your accumulated detection modules.

---

## Typical Engagement Flow

```
Day 1 — Orientation
  /summon                    → workspace layout + GRIMOIRE.md
  /annotation                → catch flagged code immediately
  /cartography               → map the core flows (e.g., deposit/withdraw, price calculation)

Day 2–N — Research
  /checks, sigil agents      → automated hunting
  /delve                     → what the agents found odd → hypotheses/WIP/
  manual reading             → your own ideas → hypotheses/WIP/
  /write-hypothesis          → turn an idea or a conversation into a hypothesis (writes, then stops)
  /dig-mode                  → build context on a lead or a system
  /validate-hypothesis       → settle each hypothesis → findings/WIP/ or hypotheses/invalid/
  /write-poc                 → (called by validate-hypothesis, or on its own)
  /tome-sync                 → now and then: find and fix tomes whose copies drifted from their owner

Before Submitting
  /finding-review, hag       → quality and red-team each draft in findings/WIP/
  /finding-dedup             → clean up duplicates
  submit                     → findings/WIP/ → findings/valid/

Report Phase
  /findings-sync             → mirror the findings repo
  /peer-review               → validate peers' and agents' findings
  report-deliverables/       → protocol summary and executive summary

Mitigation Phase (fix checkout)
  /mitigation-review         → per finding; PENDINGS/ while waiting on the client

Post-Engagement
  /scribe-distill            → turn your best findings into detection modules
  /gc-cartography            → clean up flow library
  /scribe-gc                 → deduplicate your sigil library
```

---

## Key Concepts to Internalize

**Trivial verifiability** — Every finding needs a concrete artifact proving it exists. If you can't prove it, it's a hypothesis, not a finding.

**The folder is the status** — A file's folder (`WIP/`, `valid/`, `invalid/`, `done/`, `archived/`, `PENDINGS/`) says where it stands. Nothing copies the status elsewhere, so nothing drifts.

**Dead ends are results** — A hypothesis closed as invalid or expected behavior, with its reason, keeps the next delve and the next session from re-opening it.

**Every file can be traced to its session** — `SESSIONS.md` logs let you resume the exact conversation that worked on a file.

**GRIMOIRE.md is your anchor** — Most skills read this file for context. Keep it updated if the codebase changes significantly mid-engagement.

**Cartography files are code pointers, not explanations** — They use `file:symbol` notation so agents can navigate precisely, not prose descriptions.

**Checks compound over time** — Each `/scribe-distill` run makes your future engagements faster. The library grows with every audit.
