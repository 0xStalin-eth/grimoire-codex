# <ID> Mitigation Review — <short finding title> (issue #<N>)

Report `<report.md>:<line>`. PR #<PR> (`<sha>`, `<sha>`). <If the fix lives outside the review's file
scope: "Fix is in `<file>` (out of this review's file scope, reviewed as the mitigation).">

## Verdict

**<Fixed | Fixed, with notes | Partially fixed | Fixed for X | Acknowledged | Not fixed>.** <One or two
sentences: what is closed, what (if anything) is left, and whether it matches the report's recommendation.>

## Change

- `<Contract>::<function>` (`:<line>`): <what changed, in one line>.
- <Every other touched path: constructor / setter / sibling contract / docs.>
- <What was NOT changed that the finding or the recommendation mentioned.>

## Checks

- **<Root cause closed>:** <why the new code prevents the root cause, with the invariant it relies on>.
- **<Every instance / path>:** <siblings, constructor vs setter, defaults>.
- **<Regressions>:** <new reverts, params, casts, privileged powers — or "none found">.
- **<Bypasses>:** <other routes to the same end state, and why they're closed or not>.

## PoCs — `test/mitigation/<ID>MitigationReview.t.sol` (<N>/<N> PASS; <fork?>)

| PoC | Result |
|---|---|
| `test_<ID>_preFix_<scenario>` | <Bug reproduced on pre-fix code: exact revert / figure> |
| `test_<ID>_postFix_<scenario>` | <Same scenario passes at the mitigation commit> |
| `test_<ID>_residual_<scenario>` | <Residual behaviour, if any> |
| Client `<test name>` | PASS |

Run: `forge test --match-path test/mitigation/<ID>MitigationReview.t.sol -vv`

## Thread context

- <Agreements from the issue thread that bind the verdict: accepted behaviour, severity, design limits.>

## Notes

1. **<Note title> (Info):** <one or two sentences + suggested action>.

## Footnote (not reported)

- <Theoretical residuals judged unrealistic, with the reason (e.g. needs N uncontrollable events).>

## Cyfrin write-up

**<Client>:**
Fixed at commitHash [<short>](https://github.com/<org>/<repo>/commit/<full>) && [<short>](...).

**Cyfrin:**
Verified. <single unwrapped line, no blockquote>
