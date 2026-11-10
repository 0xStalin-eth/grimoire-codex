---
name: divine
description: >-
  This skill should be used when the user says "divine", "/divine", "why",
  "/why", "why does this exist", "why does this work this way", "why was this
  chosen", "what motivated this code", "explain the rationale", "trace this decision",
  "reason about intent", or wants to understand the forces that shaped a
  security-relevant design choice, defensive check, threshold, invariant, trust
  boundary, or regression. Produces a confidence-calibrated, source-backed read
  on rationale, tradeoffs, gaps, and follow-up hypotheses.
user_invocable: true
---

# Divine

Investigate the motivation and intent behind security-relevant code or design.

`divine` is also invocable as `/why`. It is the Grimoire version of a "why"
archaeology skill. It complements:
- `cartography`, which maps where things are.
- `tome`, which preserves durable source-backed conclusions.
- `finding`, which reports verified vulnerabilities.

Divine answers what forces likely led to the current shape. It does not treat code
mechanics as proof of intent.

## Philosophy

It can often help to understand why something has the shape it does. Strange code is
not automatically vulnerable, but it may reveal a historical incident, customer
constraint, protocol invariant, integration boundary, threat model assumption, or
forgotten workaround.

Operate as a careful, cautious investigator. Be honest about what is known, what is
inferred, what is speculative, and what remains unknown. A boring cited answer is
better than a confident story.

Never claim "this exists because..." unless a source says so directly or several
independent sources strongly converge. Code shows what happens; commits, PRs,
issues, docs, comments, tests, incidents, and prior tomes are where rationale may
live.

## Confidence Tiers

Every important claim must sit in one tier:

| Tier | Meaning | Phrasing |
|------|---------|----------|
| Direct | A source explicitly states the rationale | "This exists because..." with citation |
| Supported | Multiple indirect sources converge | "The evidence points to..." with citations |
| Inferred | Reasonable interpretation from context | "It appears", "likely", "suggests" |
| Speculative | Plausible but thin evidence | "One possibility is..." |
| Unknown | Searched but not found | "We searched X and found no rationale" |

Do not upgrade a claim by repeating it. Do not use Direct phrasing for Inferred
claims. If the user proposes a hypothesis, treat it as one candidate, not a
conclusion to validate.

## Workflow

When this skill is activated, create a todo list from the following steps. Mark each
task in_progress before starting it and completed when done.

```
- [ ] 1. Understand the target and question
- [ ] 2. Establish the code or artifact anchor
- [ ] 3. Build an evidence coverage map
- [ ] 4. Investigate available evidence sources
- [ ] 5. Synthesize rationale and competing hypotheses
- [ ] 6. Translate security implications
- [ ] 7. Record durable conclusions
- [ ] 8. Present confidence-calibrated answer
```

### 1. Understand The Target And Question

Parse what the user is asking.

The target is usually:
- A code path, function, class, contract, module, or config value
- A pattern, threshold, fallback, guard, check, or special case
- A design decision, trust boundary, invariant, or privilege assignment
- A behavior described in `GRIMOIRE.md`, a tome, cartography, or finding

The question is usually:
- Why does this exist?
- What forced this design?
- What tradeoff was made?
- Is this dead code, defensive code, or a workaround?
- What incident, audit note, integration, or invariant might explain it?
- What should be preserved, changed, or avoided if we touch it?

If the target is vague, make the best interpretation from conversation context and
state it briefly before proceeding.

### 2. Establish The Code Or Artifact Anchor

Before investigating intent, anchor the question in concrete material.

Collect:
- Relevant file paths and line ranges
- Key symbols, constants, roles, events, endpoints, or storage fields
- Surrounding tests and documentation
- Related cartography, tomes, findings, and sigil findings
- Recent commits touching the target
- Older commits where the target was introduced or materially changed
- PR numbers, issue IDs, or ticket references found in commits

Useful commands:

```bash
git blame -L <start>,<end> <file>
git log --follow -p -- <file>
git log --oneline -20 -- <file>
git log -1 --format=%B <commit>
rg -n "<symbol|constant|error|event|issue-id>" .
```

If `gh` is available and the commit history references PRs, inspect substantive PRs:

```bash
gh pr view <number> --json title,body,author,createdAt,mergedAt,labels,closingIssuesReferences,comments,reviews
```

Do not assume the newest commit is authoritative. Current behavior is often the
accumulation of several older choices.

### 3. Build An Evidence Coverage Map

Document the evidence categories that are available and unavailable. Search broadly
first, then narrow.

Evidence categories:

| Category | Examples | What it reveals |
|----------|----------|-----------------|
| Grimoire artifacts | `GRIMOIRE.md`, tomes, cartography, findings, sigil findings | Prior research, local conclusions, known gaps |
| Source control | Git history, PRs, reviews, code comments, tests | Implementation-time rationale |
| Issues and tickets | GitHub Issues, Linear, Jira, Plane, Shortcut | Product, customer, audit, or business pressure |
| Long-form docs | Design docs, specs, ADRs, Notion, Confluence, docs | Planned architecture and rejected alternatives |
| Communication records | Slack, Discord, Teams, email, meeting notes | Decisions that never reached formal docs |
| Runtime evidence | logs, metrics, traces, deployed config, dashboards | Operational pressure behind defensive behavior |
| Error tracking | Sentry, Rollbar, Bugsnag, incident reports | Exceptions or regressions that motivated fixes |
| Product or protocol data | analytics, on-chain events, governance posts | Real-world usage, governance, or economic constraints |

If a category is unavailable, record that as a gap. Do not silently skip it. Only mark
a category irrelevant when it is provably unrelated to the target.

### 4. Investigate Available Evidence Sources

For each available source, gather evidence rather than writing a story.

Record:
- What you searched
- Exact queries, files, commits, PRs, issues, docs, dashboards, or logs
- Direct evidence that explicitly answers the rationale question
- Indirect evidence that bears on the question
- Contradictions
- Gaps and null results
- Additional leads for other sources

Read full PRs, issues, docs, or threads when they are relevant. Important rationale is
often buried in comments, review discussion, subtasks, or follow-up commits.

For defensive-looking code, search for incidents and regressions:
- Null checks
- Retry logic
- Timeout handling
- Rate limiting
- Circuit breakers
- Feature flags
- Egress guards
- Input clamps
- Emergency admin paths
- OOM or resource exhaustion handling

Do not chase active production systems or externally visible tests without explicit
authorization.

### 5. Synthesize Rationale And Competing Hypotheses

Weigh the evidence using the confidence tiers.

Separate:
- Explicit rationale
- Strongly supported rationale
- Reasonable inference
- Competing hypotheses
- Contradictions
- Unknowns

When evidence contradicts, surface both sides with citations. Do not pick the tidier
story unless stronger matching evidence resolves the conflict.

Ask:
- Would I expect to see this evidence if my current interpretation were wrong?
- Is this source about intent, implementation, deployment, or a different time?
- Does the evidence apply to this version, fork, network, config, or scope?
- Am I using code as evidence for its own intent?

### 6. Translate Security Implications

After rationale is calibrated, translate it into security research guidance.

Produce a Preserve / Change / Avoid / Risk set when the user may modify or audit the
target:

```markdown
## Constraints For Future Work

- Preserve: [properties or compatibility requirements that evidence supports]
- Change: [parts that appear accidental, stale, or weakly supported]
- Avoid: [edits that would break an invariant, scope assumption, or operational guard]
- Risk: [security questions or attack hypotheses still unresolved]
```

If the rationale suggests a vulnerability, do not file it as fact. Create a concrete
hypothesis:

```markdown
If [attacker capability or system condition], then [mechanism] may cause
[security impact], unless [mitigating condition].
```

Route follow-up work:
- Use `/finding-draft` for a verified vulnerability.
- Use `/tome` for durable rationale, negative results, or unresolved questions.
- Use `/scribe-distill` if the pattern should become a reusable detection.
- Use `/cartography` if the investigation revealed missing navigation.

### 7. Record Durable Conclusions

If the investigation changes understanding, write or update a tome.

Record:
- The original question
- The code or artifact anchor
- Sources searched, including gaps
- Direct and supported evidence
- Inferences and competing hypotheses
- Contradictions
- Security implications
- Follow-up checks

For thin or unresolved questions, update `grimoire/tomes/notes/hypotheses.md`,
`grimoire/tomes/notes/unverified-claims.md`, or
`grimoire/tomes/notes/contradictions.md` when those files exist or are useful.

Preserve useful negative results so future agents do not repeat the same search.

### 8. Present Confidence-Calibrated Answer

Use this structure:

```markdown
## The Question

[Restate the target and why-question.]

## The Anchor

[Files, line ranges, symbols, commits, PRs, tomes, findings, or other artifacts.]

## What We Found

- [Direct] [Claim with citation.]
- [Supported] [Claim with multiple pieces of evidence.]

## What We Can Reasonably Infer

- [Inferred] [Hedged claim with the inference chain.]

## Competing Hypotheses

- Hypothesis: [One possible explanation.]
  Evidence for: [Specific evidence.]
  Evidence against or missing: [Specific gap.]

## Security Implications

- Preserve: [What should remain true.]
- Change: [What can likely change.]
- Avoid: [Dangerous edits or assumptions.]
- Risk: [Open security hypothesis.]

## What We Don't Know

- [Specific unanswered question and sources searched.]

## Sources Consulted

- Grimoire artifacts: [paths searched or not available]
- Source control: [commits, PRs, files searched]
- Issues and tickets: [queries or unavailable]
- Long-form docs: [docs or unavailable]
- Communication records: [queries or unavailable]
- Runtime evidence: [logs/metrics/config or unavailable]
- Error tracking: [issues/incidents or unavailable]
- Product/protocol data: [queries or unavailable]

## Confidence Summary

[One or two sentences summarizing the strength and limits of the answer.]
```

Skip empty sections only when they genuinely do not apply, but keep `What We Don't
Know`, `Sources Consulted`, and `Confidence Summary`.

## Quality Check

Before finalizing:
- Every Direct or Supported claim has a citation.
- Inferred and Speculative claims use hedged language.
- Code is not cited as evidence for its own intent.
- Contradictions are surfaced, not flattened.
- Null searches and unavailable sources are recorded.
- The user's embedded hypothesis, if any, was checked independently.
- The answer says what changed in the repository, if a tome was updated.

## Common Failure Modes

- Recency bias: assuming the latest commit explains the original reason.
- Rationalization: inventing a clean rationale because the code currently makes sense.
- Sycophancy: confirming the user's guess without checking evidence.
- Mechanics-as-motivation: treating code behavior as proof of why it was written.
- Hidden gaps: omitting sources that were unavailable or searched unsuccessfully.
- Scope drift: using evidence from a different version, deployment, fork, or network.
