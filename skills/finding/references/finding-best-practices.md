# Finding Best Practices

Quality guidelines for drafting and reviewing security findings. Used by both draft mode
(to write well) and review mode (to evaluate quality).

## Title Guidelines

The title must convey **where**, **how**, and **what** (impact):

- **Where** — the affected component, route, function, or contract
- **How** — the mechanism or flaw type
- **What** — the impact or consequence

### Good Titles

| Title | Why it works |
|-------|-------------|
| "Theft of deposited funds via reentrancy in Vault.withdraw() due to state update after external call" | Where (Vault.withdraw), How (reentrancy + state after call), What (theft of funds) |
| "Account takeover enabled by lack of authentication in backend route UPDATE /user" | Where (UPDATE /user), How (no auth), What (account takeover) |
| "Denial of service in token transfer via unbounded loop over holder array" | Where (token transfer), How (unbounded loop), What (DoS) |

### Bad Titles

| Title | Problem |
|-------|---------|
| "Missing authentication" | No where, no what. Which route? What can an attacker do? |
| "Account takeover" | No where, no how. What component? What mechanism? |
| "Incorrect backend implementation" | Vague. Says nothing specific about the flaw. |
| "Reentrancy" | No where, no what. Which function? What is the impact? |
| "Bug in Vault.sol" | No how, no what. What kind of bug? What does it enable? |

### Common Anti-patterns

- **Too short** — missing one or more of where/how/what
- **Too long** — more than ~120 characters; move detail to Description
- **Impact-only** — states what happens but not where or how
- **Location-only** — states where but not what an attacker gains
- **Jargon without context** — assumes the reader knows project-specific terms

## Description Guidelines

The description is the most important section. Self-containment test: *Could someone who
has never opened this repo understand the vulnerability from this section alone?*

### Structure

1. **What is the component?** One sentence establishing context.
2. **What is the flaw?** The mechanism — what goes wrong and why.
3. **What are the preconditions?** Privileges required, timing, configuration needed.
4. **What is the impact?** What an attacker can achieve. Be specific.

### Tips

- Include code snippets when they clarify the mechanism. Keep them short, but always show where the
  lines live: a `// ContractName` comment heading the snippet, then the enclosing function's signature,
  `...` for omitted code, the referenced lines together with the `if`/`for` blocks they sit in, and the
  closing brace. Several functions of the same contract go under the same heading; a second contract gets
  its own `// ContractName` heading. Mitigation diffs follow the same shape.

  ```solidity
  // Router
  function withdraw(uint256 assets, address receiver) external {
      ...
      if (assets > available) {
          uint256 shortfall = assets - available;   // <- the line being discussed
          ...
      }
  }

  function _settle(uint256 shortfall) internal {
      ...
  }

  // Vault
  function pull(uint256 amount) external {
      ...
  }
  ```
- Write explanatory paragraphs as plain prose that opens with a declarative topic sentence: what
  happens, what the component does, or what the reader needs to know. The following sentences explain
  the mechanism, conditions and details. Do not use run-in headings (a bold label such as
  "**How withdrawals are processed.**" followed by the explanation), and do not frame a paragraph as a
  question followed by its answer.

  Avoid: "**How a withdrawal is settled.** When a user withdraws, `Router::withdraw` pulls the assets
  from `Vault::pull` and burns the shares."

  Prefer: "Withdrawals are settled in two steps. When a user withdraws, `Router::withdraw` pulls the
  assets from `Vault::pull` and burns the shares."
- Refer to functions in prose as `Contract::functionName`: the contract's name, no parentheses or
  arguments (`Router::withdraw`, not `router.withdraw()` or a bare `withdraw()`). When the code calls
  through an instance variable, name its contract type. If the arguments matter, say them in words.
  Statements (`require(a == b)`) stay as written, and code blocks keep real call syntax.
- State severity cues explicitly: "Any unauthenticated user can...", "An attacker with
  admin access could...", "Under specific timing conditions..."
- Each finding stands alone: never rely on another finding to explain this one. When a cross-reference
  is still useful (a related root cause, a shared fix, the same symptom through a different trigger),
  link it as `[issue-N](<url of that issue in the findings repo>)`, e.g.
  `[issue-72](https://github.com/<org>/<findings-repo>/issues/72)`, never a bare `#72`.
- When prose cites a PoC result ("in the PoC, ..."), name the test it comes from, e.g. "In
  `test_PoC_<Name>`, ...", and give the PoC file path at least once. A bare "the PoC"
  leaves the reader guessing which test produced the figure when the file has several.
- Every test the write-up cites must be in the write-up itself, embedded with its output. Do
  not cite a test that only exists in the repo, in another draft or in a separate comment: the
  reader of this write-up must be able to run every figure it quotes from what it contains.
- Never wrap a PoC (or any code) in `<details>` / `<summary>` collapsible tags. Put the code
  block directly after the sentence that introduces it ("Save it as `<path>`:").
- Never use one-letter shorthand for a quantity, a time, an address or any other value (`P`, `R`,
  `D`, `x`, `p`, `Δ`, `T`, `t`, `X`), even after defining it once ("an open projection `P`", "at time
  `T`"). Write the contract variable (`srtPnLProjected`, `valuationPrice`, `effectiveAt`) or a plain
  phrase ("the realized-loss claim", "the split being re-applied") at every occurrence, formulas and
  call examples included (`setUIMultiplier(1e18, effectiveAt)`, not `setUIMultiplier(1e18, T)`), so
  the reader never has to translate. Test code embedded verbatim is exempt.
- Keep it concise. If you need more than 4 paragraphs, move technical detail to the
  Details section.

## Details Guidelines

### When to Include

- The exploit involves multiple steps (e.g., flash loan + swap + withdrawal)
- The mechanism requires a code walkthrough to understand
- There are edge cases or timing windows that need explanation

### When to Omit

- The Description already covers the mechanism adequately
- The flaw is straightforward (e.g., missing authorization on one route)
- The PoC demonstrates the issue clearly enough on its own

### Tips

- Use numbered steps for multi-step exploits
- Reference specific code lines with `file:line` format
- Do not repeat content from the Description

## Recommendation Guidelines

### Principles

- **Always last.** The Recommended Mitigation section always goes last, after the Proof of Concept; only the project/auditor response stubs (and a References list, if any) may follow it. This holds for full findings, rewrites and comments that add impact.
- **Objective voice.** State what needs to change, not how you would rewrite the code.
- **One-sentence fixes preferred.** If you can express the fix in one sentence, do so.
- **Never suggest non-trivial code changes.** Security researchers are external, unbiased
  reviewers. Suggesting complex implementations introduces bias.
- **Acceptable suggestions:** Add a check, use a different function, add comments, reorder
  operations, add rate limiting, validate input.
- **Not acceptable:** Full reimplementations, architectural redesigns, multi-file refactors.

### The "Out of Scope" Escape Hatch

If the vulnerability has no simple fix, state:

> *"The design space for a solution to this flaw is out of scope for this report."*

This is honest and appropriate. Not every finding has a one-line fix.

### Tips

- Reference established patterns when applicable (e.g., "checks-effects-interactions",
  "principle of least privilege")
- If suggesting a function change, name the function but do not write the implementation
- When a recommendation does include a code diff (a verified mitigation diff, for example),
  put this disclosure line directly above the diff block, on its own:

  The next code snippet shall be taken as a general guidance to visualize the changes the mitigation may require. This is not to be used as the exact changes that are implemented.

  The diff illustrates the change; it is not the patch the project must apply.

## Severity Estimation

### Factors to Consider

| Factor | Higher severity | Lower severity |
|--------|----------------|----------------|
| **Exploitability** | No authentication needed, simple to trigger | Requires admin access, complex setup |
| **Impact scope** | All users, all funds, full compromise | Single user, limited data, partial |
| **Preconditions** | None or minimal | Specific config, timing, privilege |
| **Reversibility** | Irreversible (fund loss, data deletion) | Recoverable (temporary DoS) |
| **Likelihood** | Common scenario, easy to discover | Edge case, requires specific knowledge |

### Guidelines

- **Critical** — direct, unconditional path to maximum impact. No reasonable preconditions.
- **High** — significant impact with moderate preconditions or effort.
- **Medium** — real but conditional impact. Requires chaining, specific config, or elevated
  privileges.
- **Low** — minor or largely theoretical impact. Worth documenting for defense in depth.
- **Informational** — deviation from best practice. No direct exploitation path.

Severity is an estimate, not a formal CVSS score. Justify with one sentence in the finding.
Do not overstate confidence.

## References and Fact-Checking

- Every cited reference must be real and verifiable
- Never fabricate CVEs, SWC entries, blog posts, or documentation links
- When referencing a concept (e.g., reentrancy), provide background for readers who may
  not know the term — do not assume universal knowledge
- Prefer primary sources: official documentation, specification documents, registry entries
- Use the librarian agent for reference discovery — it searches external documentation,
  audit databases, and specifications to find citable sources for claims in findings

## Common Mistakes Checklist

Use this during review to catch frequent issues:

- [ ] Title missing impact (what)
- [ ] Title missing location (where)
- [ ] Description not self-contained — references external context
- [ ] Recommendation suggests non-trivial code changes
- [ ] Recommended Mitigation placed before the Proof of Concept instead of at the end
- [ ] A recommendation diff without the guidance disclosure line directly above it
- [ ] Severity estimate does not match described impact
- [ ] PoC reference points to nonexistent file
- [ ] References cite fabricated sources
- [ ] Code snippets included without file/line attribution
- [ ] Code snippet shows bare lines without the `// ContractName` heading, the enclosing function signature and `...`
- [ ] Functions referenced as `contract.function()` or bare `function()` instead of `Contract::functionName`
- [ ] Paragraph opens with a run-in bold heading or a question instead of a declarative topic sentence
- [ ] Another finding referenced as a bare `#N` instead of `[issue-N](link)`
- [ ] A PoC result cited as "the PoC" without naming the test function it comes from
- [ ] A cited test that is not embedded (with its output) in the write-up itself
- [ ] A PoC or code block wrapped in `<details>` / `<summary>` collapsible tags
- [ ] A quantity, time or other value written as a one-letter symbol (`P`, `x`, `R / price`, `T`, `setUIMultiplier(1e18, t)`), even if defined once
- [ ] Preconditions not stated (assumes the reader knows requirements)
- [ ] Uses project-specific jargon without explanation
