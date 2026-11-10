# Mitigation Review Checklist

Run every item for each finding. Most broken mitigations fail on one of the first five.

## 1. Does the fix hit the root cause?

- Restate the root cause from the finding in one sentence, then point at the line that now prevents it.
- A fix that blocks the PoC but not the cause (e.g. a guard on one entry point, a magic-number check)
  is **Partially fixed**.
- If the client chose a different approach from the recommendation, judge the approach, not the match.

## 2. Every instance, every path

- **Siblings:** the finding often names several contracts or functions (e.g. two adapters). Grep for
  the same pattern across the scope. A fix applied to one sibling only is partial unless the thread
  documents why.
- **Every write path:** constructor *and* setter *and* initializer *and* factory/deploy script. A bound
  enforced only in the setter leaves the deploy default unchecked.
- **Defaults:** what happens at the zero/default value? (A floor on the setter doesn't help if the
  default is 0 and the bug triggers at 0.)
- **All callers** of a changed internal function — did the change alter behaviour for a caller the
  finding didn't mention?

## 3. Regressions introduced by the fix

- New revert paths: can a user flow, liquidation, or accrual now be bricked?
- New parameters: unbounded, unvalidated, immutable with no setter, unsafe casts (`uint64(...)`).
- New privileged powers or escape hatches (owner clears, exemptions): who holds them, can they be abused?
- Storage layout / ABI changes: upgrade safety, other contracts reading raw slots, engines/periphery
  that must be upgraded in lockstep.
- Size limits (EIP-170) when bytecode grew: `forge build --sizes`.
- Rounding direction and overflow on new math (check what the math library actually does — e.g. Solady
  `mulDiv` reverts when `x*y` overflows; only `fullMulDiv` is 512-bit).

## 4. Bypasses of the new defence

- If the fix gates one action (e.g. `repay`), list every other way to reach the same end state
  (liquidate, withdraw, transfer, a second account, a flash loan, a different market or pool).
- If the fix keys exemptions or state on an address, check whether a position-keyed attacker can route
  around it (`onBehalf`, helper contracts).
- Timing: does the defence hold across blocks, or only atomically?

## 5. Scope and reliance

- Does the mitigation live in, or rely on, out-of-scope code? Review it anyway, and say so in the
  review ("reviewed as the mitigation, out of this review's file scope").
- Docs-only / acknowledged fixes: confirm the doc text is accurate, is placed where the affected party
  (curator, integrator, operator) will see it, and that the code still behaves as documented.

## 6. Consistency with the thread

- Read the whole issue thread. Agreements reached there (accepted behaviour, chosen severity, design
  constraints) bind the verdict. Do not re-open them; note them as context.
- If the thread promised something (an event, a doc update, a test) that isn't in the diff, note it.

## 7. Stale artefacts

- Invariant docs, NatSpec, `docs/`, Certora specs that describe the old behaviour.
- Client tests that pin the old behaviour and were deleted rather than updated.

## 8. Residual severity — assess realism before rating

For each residual, answer: who triggers it, what do they control, how many uncontrollable events are
needed, and what is the impact relative to the original finding? A residual that needs several
independent market crashes, or only reduces a recovery ceiling, is a footnote, not a finding.
