## Finding #<N>: <valid | partly valid | invalid>. <Rating> (filed <Rating>)

"<Title>", filed by <author> as <Rating>. <PoC: the finding's own, extracted to `<path>` | none, new one at `<path>`>, <K> tests pass.

**The bug** (`<File>:<lines>`; same in `<OtherVariant>:<lines>`, …). <Two or three plain sentences: what the
code assumes, what actually happens, and the consequence.>

```solidity
<the 2-6 responsible lines, with one-line comments pointing at the wrong step>
```

**Reproduction** (<setup in one line>):

| | <Control / expected> | <Bug path> |
|---|---|---|
| <metric> | <value> | **<value>** |

**Scope.** <New in the delta | pre-existing (base `<commit>:<line>`), copied into <new file> | pre-existing and untouched>. <Delta-specific angle, if any.>

**Severity: <Rating>.**
- **For:** <strongest argument, quantified>.
- **Against:** <strongest argument: preconditions, recovery, bound, configuration>.
- <What to ask the project, if the rating hinges on an unverifiable fact.>

**Duplicates:** <none | duplicate of #X (same root, same fix) | related: #Y (<one-line difference>)>.
<If another finding's fix resolves this one: "Resolved by #Z's fix (<commit or diff>): <PoC result with it applied>; <why the precondition cannot recur>. Keep open and comment that #Z's fix resolves it (close only if it is a duplicate, including a symptom of #Z's root cause).">.
<Cluster table if this is one symptom of a broader root.>

**Mitigation.** <Is the recommendation right? What is missing?> <Verified diff, or "not verified".>

**Open items:** <tests not run, facts to confirm, leads.>
