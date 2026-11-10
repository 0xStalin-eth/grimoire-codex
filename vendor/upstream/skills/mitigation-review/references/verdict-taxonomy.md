# Verdicts

Use exactly one of these as the first word(s) of the review verdict and of the `Cyfrin:` write-up.

| Verdict | When | Write-up opens with |
|---|---|---|
| **Fixed** | Root cause closed on every instance and path; PoC reproduces pre-fix and passes post-fix. | `Verified.` |
| **Fixed, with notes** | As above, but there are Info-level residuals, doc gaps, or hardening suggestions that don't reopen the finding. | `Verified.` + a short second paragraph |
| **Partially fixed** | The main vector is closed but an instance, a path, or a default still reproduces the finding (or a lower-impact form of it). | `Partially fixed.` |
| **Fixed for X** | The finding named several components; some were deliberately left as-is and documented. | `Verified for X:` … |
| **Acknowledged** | No code change, or docs only; the client accepts the behaviour. | `Acknowledged.` |
| **Not fixed** | The change does not stop the finding, or introduces an equal/worse issue. | `Not fixed.` |

## Residual severity

Rate residuals independently of the original finding, using the realism questions in
`review-checklist.md` §8:

- **New finding** (Low+): exploitable by an unprivileged actor with a concrete impact. Recommend
  filing it as a new issue, not burying it in the write-up.
- **Note (Info)**: hardening, defence-in-depth, doc gaps, owner-config footguns.
- **Footnote (not reported)**: theoretical, needs several uncontrollable events, or impact is strictly
  smaller than the original. Keep it in the review file only.

## Status line for GRIMOIRE.md

`**<Verdict>** (<≤12-word reason>) — [[mitigation-review/WIP/<ID>-mitigation-review]]`

When the file moves (SKILL.md B7), the link follows it: `[[mitigation-review/PENDINGS/…]]`,
`[[mitigation-review/done/…]]` or `[[mitigation-review/archived/…]]`.

Examples:
- `**Fixed** (untracked priority entries skipped) — [[mitigation-review/done/L-5-mitigation-review]]`
- `**Partially fixed** (1-day setter floor; zero deploy default still steps NAV) — [[mitigation-review/PENDINGS/L-6-mitigation-review]]`
- `**Acknowledged** (docs; fail-closed by design) — [[mitigation-review/done/L-2-mitigation-review]]`
