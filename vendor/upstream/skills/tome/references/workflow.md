# Tome Workflow

Use this procedure when answering from, creating, or updating durable research notes.

## Operating Model

Tome has two modes:

1. **Base workflow** — orient, restate the question, and answer from existing tomes when
   the wiki already contains enough evidence.
2. **Research workflow** — when the wiki is insufficient, identify the evidence gap,
   study related source material, update the wiki with supported conclusions, and note
   unverified claims.

The base workflow can use efficient, speed-oriented models. The research workflow should
always be executed by the most competent model possible.

## Base Workflow

When this skill is activated and when answering a question, create a todo list from these
steps. Mark each task in_progress before starting it and completed when done.

```
- [ ] 1. Orient to the existing grimoire
- [ ] 2. Define the research question in your own words
- [ ] 3. Answer the question using evidence from tomes if possible
- [ ] 4. If the wiki is insufficient, run the research workflow
```

### 1. Orient To The Existing Grimoire

Read `GRIMOIRE.md` if it exists. Then inspect relevant files in:
- `grimoire/tomes/`
- `grimoire/findings/`
- `grimoire/sigil-findings/`
- `grimoire/cartography/`
- `grimoire/spells/`

Search before creating a new page. For larger collections, search all markdown files
for target names, subsystem names, symbols, prior claims, and related pages.

Completion criterion: you can state the target, in-scope versions, existing coverage,
and current unanswered questions.

### 2. Define The Research Question

Restate the user's question in your own words. Capture:
- The target or topic
- The kind of answer needed
- The version, deployment, or scope if known
- The evidence that would be sufficient to answer

If active testing might be required, record the safety scope before testing:
- Exact target and environment
- Included and excluded versions or deployments
- Authorized test methods
- Prohibited or high-impact actions

For active testing, stop when scope or authorization is missing. Ask the user before a
destructive, persistent, or externally visible test.

Completion criterion: the question is testable, scoped, and clear enough to search for.

### 3. Answer From Existing Tomes If Possible

Use existing tomes and related grimoire artifacts first. Distinguish:
- Established facts
- Observations
- Supported interpretations
- Hypotheses
- Contradictions
- Unknowns
- Version or deployment limits

Cite the relevant tome paths and source references. If existing tomes are enough, answer
the user and stop. Do not perform fresh research just to make the answer feel fuller.

Completion criterion: the answer is supported by existing durable notes and its
confidence is calibrated to those notes.

### 4. Escalate To Research Workflow When Needed

Run the research workflow when:
- Existing tomes do not answer the question.
- The answer depends on unverified claims.
- Existing tomes contradict each other or conflict with code, tests, docs, or findings.
- The user explicitly asks to update or extend the wiki.
- The task would create durable value for future research.

State the evidence gap before starting research.

## Research Workflow

Use this workflow when the wiki is insufficient.

```
- [ ] 1. Formulate the evidence gap
- [ ] 2. Locate and study related source material
- [ ] 3. Verify and classify claims
- [ ] 4. Track hypotheses, contradictions, and unverified claims
- [ ] 5. Write or update tomes
- [ ] 6. Cross-link navigation and history
- [ ] 7. Answer with scoped confidence
```

### 1. Formulate The Evidence Gap

Write down what the existing tomes cannot answer and what evidence would resolve it.

If the question is not yet page-worthy, record it in
`grimoire/tomes/notes/hypotheses.md`.

Completion criterion: the missing evidence is specific enough to guide source review.

### 2. Locate And Study Related Source Material

Prefer existing local evidence first: code, tests, docs, traces, prior tomes,
cartography, findings, and artifacts. If new external evidence is needed, preserve the
source or record why it could not be preserved.

For every important source, record:
- Title or origin
- Local path or URL
- Source type
- Retrieval or observation date
- Version, tag, commit, deployment, or block number when applicable
- Subsystem coverage
- Completeness and fetch problems
- Freshness and known limitations
- Questions the source can and cannot answer

Do not store credentials, session tokens, private keys, or unrelated personal data.
If redaction is necessary, record that the snapshot is redacted.

Completion criterion: each important source has a usable reference or a recorded gap.

### 3. Verify And Classify Claims

Before writing conclusions, classify important claims using `evidence-model.md`.

If a claim is plausible but unverified, label it as an open question or hypothesis
instead of a conclusion. Add unresolved security-critical claims to
`grimoire/tomes/notes/unverified-claims.md`.

Completion criterion: every material statement has provenance, scope, support, state,
and suitable confidence.

### 4. Track Hypotheses, Contradictions, And Unverified Claims

Put plausible but unsupported ideas in `grimoire/tomes/notes/hypotheses.md`. Put source
disagreements in `grimoire/tomes/notes/contradictions.md`.

For each contradiction, record:
- Conflicting statements
- Exact sources and versions
- Whether the conflict concerns intent, implementation, deployment, or time
- Evidence needed to resolve it
- Current effect on conclusions

Do not bury an unresolved contradiction inside a confident summary.

Completion criterion: uncertainty remains visible and is not accidentally promoted to
fact elsewhere.

### 5. Write Or Update Tomes

Follow `tome-format.md` and the relevant template in `page-templates.md`.

Route new pages into the typed directory that best matches the page's primary purpose:
actors, components, contracts, flows, mechanisms, trust boundaries, risks, or open
questions. If a page could fit multiple directories, choose the one a human would most
likely browse first and add cross-links to the other relevant pages. Use `notes/` for
durable context that does not cleanly fit a stricter category yet.

**Shared topics.** If `grimoire/tomes/LINKS.md` exists, look up every section you are about to change
(see `links.md`):
- Before writing, note whether the section is the **owner** or a **copy** of its topic.
- If the change alters a claim, update the owner first, then every copy listed, in the same pass, and
  bump `Synced`.
- If you are adding a claim to a **copy** that its owner lacks, choose **push up** (write it into the
  owner too; default when the topic is background for this tome) or **transfer** (this section becomes
  the owner; default when the topic is this tome's subject). Follow the transfer steps in `links.md`
  and tell the user which you chose.
- If an owner and a copy disagree and it isn't clear which is right, ask the user.
- If a new tome or section repeats a topic another tome already covers, add it to that row's copies;
  it owns nothing yet. For a topic with no row, pick the owner by subject, then by the fullest current
  claims, and say which you picked. Create `LINKS.md` if this is the first topic shared between two
  tomes.

Completion criterion: the page saves future readers time without hiding evidence,
limits, or uncertainty, and no copy listed in `LINKS.md` now contradicts its owner.

### 6. Cross-Link Navigation And History

Use Obsidian-style links when referencing tomes:

```markdown
[[tomes/flows/auth-flow]]
```

Add links from `GRIMOIRE.md` only when the tome contains important context future
agents should discover early. Do not bloat `GRIMOIRE.md` with details that belong in
the tome.

If `grimoire/tomes/index.md` exists, add every new page under the correct directory or
type with one factual summary. If a log file exists, append one task entry listing
every created, updated, archived, or deleted tome.

List every copy you synced in the answer and in the log entry, and name the owner. Drift you saw but
did not fix goes under `Open drift` in `LINKS.md`.

Completion criterion: every changed research artifact is discoverable from an index,
log, `GRIMOIRE.md`, or a related page.

### 7. Answer With Scoped Confidence

The final response must distinguish:
- Established facts
- Observations
- Supported interpretations
- Hypotheses
- Contradictions
- Unknowns
- Version or deployment limits

Cite the relevant tome paths and source references. If evidence is insufficient,
complete the task with an evidence-gap report rather than a confident answer.

Completion criterion: the durable repository and the response give the same scoped
conclusion and confidence level.
