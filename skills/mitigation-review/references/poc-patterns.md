# Mitigation PoC Patterns (Foundry)

A mitigation PoC answers three questions. Write one test per question; name them so the table in the
review reads naturally.

| Test name | Question | Expected |
|---|---|---|
| `test_<ID>_preFix_<scenario>` | Does the original bug reproduce on the old code? | Reproduces (revert / wrong value) |
| `test_<ID>_postFix_<scenario>` | Does the same scenario pass on the mitigated code? | Passes |
| `test_<ID>_residual_<scenario>` / `_bypass_` | Does the fix leave a path, default, or sibling open? | Documents the residual (passes by asserting the residual behaviour) |

Also run the client's own regression test for the fix (find it with `fix-diff.sh` — test files in the
fix commits). Report it as PASS/FAIL alongside yours.

Location: `test/mitigation/<ID>MitigationReview.t.sol`. Contract `<ID>MitigationReview` (strip the
dash: `L5MitigationReview`). One NatSpec `@notice` with the finding ID, issue number, PR, and the
one-line bug. Reuse the repo's existing test bases (`BaseTest`, unit/integration fixtures) — inherit,
don't rebuild setup.

## Reproducing pre-fix behaviour

Pick the cheapest that works:

1. **Parameter/config fixes** (bounds, setters): no old code needed — the pre-fix value now reverts.
   `vm.expectRevert(Err.selector)` on the report's exact inputs, plus boundary ±1.
2. **Swap in the old code at the same address** (logic fixes in a contract):
   ```bash
   prefix-snapshot.sh <src-file> <fix-commit> test/mitigation <ID>
   ```
   It writes `<Name>PreFix<Id>.sol` (finding ID without punctuation, e.g. `H-1` -> `H1`), so snapshots
   of the same contract for different findings, or from parallel sessions, never overwrite each other.
   It refuses to overwrite an existing snapshot, and it compiles the new one and removes it if the old
   code no longer builds against the current tree (a broken file in the shared test folder breaks every
   session's build); then use option 3. Then in the test:
   ```solidity
   // Imported so the artifact is compiled for `deployCodeTo`.
   import {XPreFixH1} from "./XPreFixH1.sol";
   ...
   deployCodeTo("XPreFixH1.sol:XPreFixH1", abi.encode(<constructor args>), address(x));
   ```
   Immutables are rebuilt from the constructor args; storage stays. Only valid if the storage layout
   and constructor didn't change in the fix — check the snapshot's diff.
3. **Layout/ABI changes** (storage re-pack, type widening): can't swap. Reproduce in an isolated copy
   of the pre-fix code inside the workspace, and run the test there:
   `bash $P/isolated-workspace.sh create prefix-<ID> --ref <fix-commit>^` (`$P` is the peer-review
   skill's `scripts/` folder). The copy lives in `.isolated/<session-id>/` and is kept until the review closes.
   Or rely on the client's pre-fix PoC from the original report. Never `git checkout` in the review
   workspace, and never create anything above its root.

## Gotchas

- **`via_ir` caches `block.timestamp`** across `vm.warp` in the same function. Use absolute warps:
  `uint256 t0 = vm.getBlockTimestamp(); vm.warp(t0 + 1 days);` — never `block.timestamp + x` twice.
- **`vm.getCode: no matching artifact`** → the pre-fix contract isn't imported anywhere; import it.
- **`--match-test` is case-sensitive** ("No tests found" usually means `sweep` vs `Sweep`).
- **Revert selectors from external libs**: `vm.expectRevert(bytes4(keccak256("MulDivFailed()")))`.
- **`expectRevert` + internal call**: the revert must come from an external call. Wrap helpers as
  `function doX(...) external { require(msg.sender == address(this)); ... }` and call `this.doX(...)`.
- **Fork tests**: need an RPC env var (e.g. `MAINNET_RPC_URL`). Never echo or write the URL. If unset,
  ask the user to run `! export MAINNET_RPC_URL=...` or pass it inline for one command; if they paste a
  keyed URL in chat, suggest rotating it.
- **Slow `via_ir` builds**: don't edit `src/`. Use `--match-path test/mitigation/<file>` to keep runs
  scoped. Build once, then iterate on tests only.
- **Submodule clone noise** (`forge` trying to `git clone` libs that already exist) is harmless.

## Figures

Use the report's own numbers (amounts, prices, timings) so the review can say "the report's scenario
now …". Log key values with `emit log_named_uint` and put them in the review's PoC table.

## Run command (put it in the review)

```
forge test --match-path test/mitigation/<ID>MitigationReview.t.sol -vv
MAINNET_RPC_URL=... forge test --match-path test/mitigation/<ID>MitigationReview.t.sol   # fork
```
