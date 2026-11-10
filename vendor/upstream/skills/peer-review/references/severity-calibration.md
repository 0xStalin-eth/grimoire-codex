# Severity Calibration

Rate impact and likelihood separately, then combine. Write down the strongest argument on each side;
the user (or the judge) decides between close calls, so give them both.

## 1. Preconditions and minimum actor

List every condition that must hold, in order, and name the cheapest actor who can make them hold.

| Actor | Typical effect on likelihood |
|---|---|
| Anyone, permissionless, repeatable | High |
| Any user, but only in a rare protocol state | Medium to low; depends on how rare the state is |
| Operator role without timelock, doing its normal job | The finding stands: the operator is not "misusing" anything |
| Timelocked owner / governance making a mistake | Usually Low or Informational (trusted, slow, visible) |
| Only reachable through a mock or test setter | Not a finding against the real code |

**Before calling a step "privileged misuse", check that it isn't a supported flow.** Look in the
project's own tests, specs and runbooks: if they exercise the step (reopening a paused action, funding
promptly, rotating a component), it is normal operation and the finding should be judged as such.

## 2. Magnitude

Quantify, don't describe:
- **Size-dependent bugs** (overflow, rounding, dust, thresholds): sweep the inputs in a short script and
  report the boundary ("overflows above ~X tokens at Y decimals", "1.1% of random states overshoot by
  one unit").
- **Value transfers**: give the amount moved and who pays and who gains, in tokens and in USD at the
  relevant price.
- **Bounded effects**: state the bound and what sets it (a fee bucket, a dust floor, a claim size).
  When the bound depends on an operational cadence (how often a fee is paid out), say so; that is a
  mitigation the project controls.
- **Parameter sensitivity**: if a parameter moves the result across the threshold (a premium, an
  exponent), show both sides.

## 3. Recovery

| Recovery | Pulls severity |
|---|---|
| Self-heals in normal operation (yield, the next push, the next flow) | Down |
| Permissionless and cheap (donate a small gap, call a public function) | Down |
| Operator action without timelock | Down slightly |
| Owner action behind a long timelock | Up: the freeze lasts at least that long |
| Only an upgrade | Up |
| Recovery costs about as much as the value it unlocks | Up: nobody will do it |
| Waiting makes it worse (accumulators keep growing) | Up |

## 4. Persistence

- **Transient**: lasts until the next routine update.
- **Sticky**: persists until someone acts (recovery above).
- **Virtual until acted on**: effective values that are recomputed on read. The transfer becomes real
  only when someone exits, deposits, or a payout is booked during the window; if everyone waits, it
  resets. State this explicitly; it is often the deciding factor between Low and Medium.

## 5. Configuration and deployment

- Features shipped **disabled by default** (a rate seeded at 0, an optional module): the bug is dormant
  until enabled. Rate for the enabled case and note the default.
- **Reference deployment**: how many instances share the component, which implementations are wired.
  A cross-instance bug with one instance deployed is latent; say when it becomes live.
- **Who owns what**: the owner of an oracle or registry sets how fast a broken dependency can be fixed.

## 6. Scope interaction

- **New in the delta**: rate normally.
- **Pre-existing, copied into a new file**: in scope through the new copy; note that the root is older.
- **Pre-existing, untouched**: in scope only if the in-scope list includes the file; argue the
  delta-specific angle if there is one (a new victim, a wider trigger, a new revert surface).
- **Out-of-scope component as trigger**: fine, as long as the root cause is in scope.

## Common down-arguments

- Needs a near-total loss or an extreme price (state the threshold as a percentage).
- Only the protected or privileged party is affected, and only by its own setting.
- The protocol is already "abandoned" or wiped at that point.
- Dust-bounded, or bounded by a parameter the project controls.
- Documented design choice (code comments, specs). Then the finding is a spec mismatch at most.

## Common up-arguments

- A protected party (the user or position the system promises to shield) pays.
- Cross-component blast radius: one instance's state blocks or starves others.
- Funds outside the faulty component are frozen (a vault blocked by a strategy-side revert).
- Recovery is slow, expensive, or absent.
- The trigger is the system's normal operation or a common market path.
