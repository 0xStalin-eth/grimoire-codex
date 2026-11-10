# Page Templates

Use these templates with the frontmatter described in `tome-format.md`.

## General

```markdown
# [Title]

## Summary

## Scope And Versions

## Source Coverage

## Known Claims

## Unknowns

## Security Relevance

## Related Pages

## Source References
```

## Mechanism

```markdown
# [Mechanism Name]

## Summary

## Scope And Versions

## Actors

## Assets

## Preconditions

## State Machine

## Happy Path

## Failure Paths

## Trust Assumptions

## Security Properties And Invariants

## Privileged Operations

## External Dependencies

## Open Questions

## Related Pages

## Source References
```

## Flow

```markdown
# [Flow Name]

## Goal

## Entry Points

## Participants

## Preconditions

## State Transitions

## Calls And Data Movement

## Authorization Checks

## Failure And Rollback Behavior

## Trust Boundary Crossings

## Security Invariants

## Open Questions

## Source References
```

## Component Or Contract

```markdown
# [Component Name]

## Purpose

## Scope And Versions

## Entry Points

## State And Storage

## Roles And Permissions

## Upgrade And Administration Paths

## External Calls And Dependencies

## Critical Invariants

## Dangerous Assumptions

## Known Risks

## Tests And Observed Behavior

## Open Questions

## Source References
```

## Risk

```markdown
# [Risk Title]

## Risk Statement

## Evidence Status

## Affected Assets And Components

## Threat Actor And Required Capability

## Preconditions

## Failure Mode

## Attack Path

## Impact

## Likelihood Factors

## Existing Mitigations

## Mitigation Limits

## Residual Risk

## Detection Opportunities

## Questions To Verify

## Source References
```

## Finding Candidate

Use `grimoire/tomes/` for finding notes only when they are research support. Use
`grimoire/findings/` for report-ready vulnerabilities and `/finding-draft` for the
finding format.

```markdown
# [Finding Candidate Title]

## Status

candidate | reproduced | confirmed | rejected | fixed | accepted-risk

## Scope And Affected Versions

## Summary

## Security Property Violated

## Preconditions

## Reproduction Evidence

## Root Cause

## Attack Scenario

## Impact

## Existing Controls

## Recommended Remediation

## Regression Test

## Uncertainties

## Source References
```

Do not call a hypothesis a vulnerability before the evidence supports that conclusion.
Keep early ideas in `grimoire/tomes/notes/hypotheses.md` or use `/divine`.
