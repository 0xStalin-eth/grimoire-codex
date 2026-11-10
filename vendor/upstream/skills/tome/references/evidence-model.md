# Evidence Model

Use this reference before writing or changing claims in `grimoire/tomes/`.

## Source Precedence

Prefer evidence in this order:

1. Observed deployed state, runtime behavior, configuration, or bytecode for the target version.
2. Source code and tests that match the deployed or in-scope version.
3. Official specifications and technical documentation for intended behavior.
4. Standards, research papers, and formal analyses.
5. Security audits, advisories, and incident reports.
6. Official issues, discussions, release notes, and engineering posts.
7. Independent technical explanations and other external sources.
8. Marketing material and unattributed claims.

Not all evidence constitutes proof. Code and deployed state demonstrate behavior, while
artifacts like documentation, papers, and reports demonstrate intent.

Never invent a line number, commit, deployment, test result, hash, or source path.

## Claim Model

Classify each important claim on three dimensions:

| Dimension | Values |
|-----------|--------|
| Support | `observed`, `test`, `code`, `docs`, `audit`, `inferred` |
| State | `current`, `uncertain`, `stale`, `contradicted` |
| Confidence | `high`, `medium`, `low` |

Do not use `high` confidence for a single weak source. Do not treat a trust
assumption as a mitigation unless the scope explicitly says that capability is out
of bounds.

Never overclaim confidence.

Use a claim block for security-critical, disputed, or non-obvious statements:

```markdown
> Claim: A precise, testable statement.
> Scope: Version, deployment, configuration, or date.
> Support: code
> State: current
> Confidence: medium
> Sources: `src/Vault.sol:40-58`, `test/Vault.t.sol`
> Limits: Missing evidence or conditions that can change the result.
```

Use short inline provenance markers for routine supported statements:

```markdown
The withdrawal path updates balances before the external call. ^[`src/Vault.sol:40-58`]
```

## Claim Support Requirements

| Claim type | Required support |
|------------|------------------|
| Code behavior | Source reference and, when useful, test or trace |
| Protocol intent | Documentation, comments, scope notes, or repeated implementation pattern |
| Runtime behavior | Observation, deployment config, trace, reproduced test, or explicit limitation |
| Security implication | Mechanism plus affected asset or invariant |
| Negative result | Search performed and reason the path is not viable |

If a claim is plausible but unverified, label it as an open question or hypothesis
instead of a conclusion. Add unresolved security-critical claims to
`grimoire/tomes/notes/unverified-claims.md`.
