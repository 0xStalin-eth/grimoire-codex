# Independent Claude versus Codex comparisons

This is a small **collection and comparison CLI**, not an agent launcher, sandbox, automatic
vulnerability judge or controlled model benchmark. It launches neither runtime and requires no
Claude installation to collect/compare Codex results. Each agent runs independently using its own
runtime and skills. An evaluator compares only after both runs are complete.

## Try the complete collection pipeline

From the downstream checkout:

```sh
python3 benchmark/demo.py --output /tmp/grimoire-comparison-demo
```

Use a fresh output path. This runs init → capture → compare through the CLI, preserves synthetic
raw reports and writes `comparison/comparison.md` plus `comparison.json`. **It executes no model,
contract or security test. Its illustrative findings are not benchmark results.**

## Prepare a real first comparison

1. Choose an authorized target, an exact audited commit, one workflow and a bounded scope. Prepare
   two clean, independent target clones at that same commit. Keep each target inside a separate
   engagement directory. Do not use either Grimoire toolkit repository as the audit workspace.
2. Pin the Claude skill source to the same upstream SHA recorded in downstream `sync-state.json`.
   Use a separate read-only source copy for the Claude runtime, never the original local checkout
   as a writable workspace. Pin Codex to a clean downstream commit. Record both exact skill commits.
3. Create a single `task.txt` and `scope.txt`. Copy identical bytes into both isolated environments.
   Task text must name the objective, authorized actions, time/token limits, expected artifacts,
   verification standard and stopping condition. Scope should name the same target-relative files,
   exclusions, threat model, ground rules and any fork block/fixture seed. Keep ground truth private
   from both agents. Do not include either model's findings in either task.
4. Provide equivalent dependencies and tools where possible; freeze any personal spellbook/library
   **before both runs**. Do not allow one run's findings or distilled detectors into the other run's
   knowledge store. Helpers normally use `~/.grimoire`; use separate OS users/containers for strict
   isolation. `GRIMOIRE_HOME` currently controls bootstrap only, not every inherited helper path.
5. Fill one environment JSON per run from `benchmark/examples/environment.json`. Include actual
   runtime/model versions, reasoning settings, sandbox/network policy, MCP services, tool versions,
   compiler/lockfiles, resource budgets and personal-knowledge snapshot. Record unavailable values
   explicitly. Do not store keys, RPC secrets, source code or confidential outputs in this toolkit.

The collector checks a clean target and records its actual HEAD, task/scope hashes and supplied
skill/model/runtime provenance. Skill/model/runtime versions are operator-supplied: verify them
against the actual checkout and runtime. It does not attest that a model used those settings.

For each Codex execution, automatic skill-entry setup records its launch directory and generates
a distinct run ID, as in [HOW-TO-USE.md](HOW-TO-USE.md). Capture its reports and PoCs from
`<target-git-root>/grimoire-codex/<run-id>/`, including raw evidence under `runs/`; working copies
remain in `.isolated-codex/<run-id>/`. Keep run collection, scratch and cache paths inside that
execution's audit folder. Supply existing Claude artifacts only to the evaluator after both runs.

For example, substitute your paths, exact commits and versions below. Both `--workflow` values
must be the same upstream workflow name, such as `peer-review`:

```sh
python3 scripts/benchmark.py init \
  --output /path/to/private-runs/claude \
  --agent claude --target /path/to/claude-engagement/target \
  --instructions /path/to/task.txt --scope /path/to/scope.txt \
  --environment /path/to/claude-environment.json \
  --skill-version <exact-upstream-commit> --upstream-sha <exact-upstream-commit> \
  --model <actual-claude-model> --runtime claude-code --runtime-version <actual-version> \
  --workflow peer-review

python3 scripts/benchmark.py init \
  --output /path/to/private-runs/codex \
  --agent codex --target /path/to/codex-engagement/target \
  --instructions /path/to/task.txt --scope /path/to/scope.txt \
  --environment /path/to/codex-environment.json \
  --skill-version <exact-downstream-commit> --upstream-sha <same-upstream-commit> \
  --model <actual-codex-model> --runtime codex-cli --runtime-version <actual-version> \
  --workflow peer-review
```

Get a source revision with `git -C /path/to/toolkit rev-parse HEAD`; inspect
`git -C /path/to/toolkit status --porcelain` to ensure it is clean. `codex --version` reports the
installed CLI version. Do not confuse downstream skill commit, canonical upstream commit and audited
target commit: all three are recorded separately.

## Execute and capture independently

Install the Codex skills with `python3 scripts/install.py --project /path/to/codex-engagement` and
start `codex --cd /path/to/codex-engagement`. Invoke `$peer-review` (or your selected skill) with
the shared task and scope. Start Claude in its own isolated engagement with the read-only pinned
Claude plugin source, following upstream installation guidance. Use its equivalent workflow.
Neither runtime is called by or required by the other.

Keep all original stages and approval gates. Record each operator intervention, approval, supplied
answer and resumed session; supply equivalent information to the other run where possible. Record
unequal assistance as a confound. Preserve available transcripts, report files, commands, PoCs,
execution logs and test output in a private raw-output directory per agent. Measure elapsed task
time (including/excluding operator waits consistently and state which). Capture token/cost metrics
only if the runtime exposes reliable values. Leave unavailable metrics null, not zero.

The CLI checks completion/integrity but cannot prevent one process reading a sibling directory on
the same machine. Strict blinding requires separate filesystem access boundaries or machines.
Do not mount either run's artifacts into the other environment. Keep the evaluator outside both
agents. Comparison artifacts are created only after both executions end.

## Normalize without judging

Transcribe each agent's findings into [the JSON schema](benchmark/findings.schema.json), using
[the example](benchmark/examples/findings.json) as structure only. Keep all raw reports intact.
Use one normalized finding per evidence-supported root cause **within that run**; a human may group
true duplicates while retaining raw IDs in an optional `aliases` field. Do not merge merely similar
reports. Severity is the agent's classification, not the evaluator's verdict. Provide exact
locations, root cause, impact, evidence references and reproduction status/command/result. For
unexecuted proofs, use `not_tested` and explain why; never fabricate successful test output.

An empty result is `{"schema_version":1,"findings":[]}`. Finding IDs must be unique within a run.
Normalized paths are target-relative; raw evidence references point to captured artifacts. The
collector validates structure; the reviewer must actually inspect cited code/proofs and artifacts.
It does not infer validity from the supplied status or automatically parse reports with an LLM.

Capture each completed run, using measured values (the example 120 seconds is illustrative):

```sh
python3 scripts/benchmark.py complete --run /path/to/private-runs/claude \
  --findings /path/to/claude-normalized.json --raw /path/to/claude-raw \
  --elapsed-seconds 120
python3 scripts/benchmark.py complete --run /path/to/private-runs/codex \
  --findings /path/to/codex-normalized.json --raw /path/to/codex-raw \
  --elapsed-seconds 120
```

Optional flags: `--input-tokens N --output-tokens N --estimated-cost-usd N`. Costs are operator
estimates, not automatically priced. Zero is meaningful; omit unavailable metrics. The command
copies explicitly selected raw files and seals hashes of inputs, normalized results and run metadata.
It refuses re-completion. These hashes detect accidental edits, not malicious re-sealing or leaked
information. Keep actual unredacted credentials out of captured logs from the start.

## Adjudicate and compare

Copy `benchmark/examples/review.json` into a **private** `review.json`. Set the exact run IDs from
each `run.json`, identify the independent reviewer and describe the evidence inspected. Create one
adjudication for every normalized ID: `valid`, `false_positive` or `uncertain`, with evidence.
Optional manual 1–5 quality scores cover reasoning, evidence and reproducibility: 1 means unsupported
or unusable; 3 means partly justified/reproducible with material gaps; 5 means source-grounded,
complete and independently reproduced. Keep unassessed scores null.

Add cross-run matches **only** when code location, causal mechanism, preconditions and proof support
the same root cause. Each match needs `left`, `right`, `root_cause` and `evidence`. Matching is
one-to-one after within-run deduplication. Ambiguous pairs stay unmatched. Set `matching_complete`
to true only after reviewing all valid unmatched candidates; otherwise the report calls them
candidates, not unique vulnerabilities. It never uses textual similarity to establish overlap.

Optional reliable ground truth:

```json
{
  "reliable": true,
  "items": [
    {"id": "GT-1", "evidence": "Private oracle / confirmed root cause / independently verified proof"}
  ]
}
```

Place that object in `ground_truth`; link confirmed coverage through each valid adjudication's
`ground_truth_ids`. Missed IDs are false negatives **against that supplied ground truth only**.
Without reliable ground truth, false negatives remain unavailable. Unknown bugs are not measurable
misses. The evaluator is responsible for the ground truth's scope and reliability.

```sh
python3 scripts/benchmark.py compare \
  /path/to/private-runs/claude /path/to/private-runs/codex \
  --review /path/to/private-runs/review.json \
  --output /path/to/private-runs/comparison
```

Both runs must be completed and have matching target commit, upstream commit, task bytes, scope
bytes and workflow. Reports include adjudicated validity/false positives/uncertainty, manually
confirmed overlap, uniqueness only after complete matching, severity differences, quality scores,
reproduction evidence, execution time and optional token/cost metrics. All detailed provenance and
the full adjudication ledger are in `comparison.json`; `comparison.md` is a concise overview.

Skill adaptations, tools/MCP availability, runtime configuration and environment differences are
listed as confounds. The model labels are recorded separately. Even with no recorded differences,
unmeasured effects can remain. Do not attribute the observed gap entirely to the underlying models.
This repository contains no actual Claude-vs-Codex security outcome or performance claim.
