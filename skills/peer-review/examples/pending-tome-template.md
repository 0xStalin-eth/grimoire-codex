# Pending peer reviews: leads to come back to

> Source: peer-review session `<session-id>`, <date>. Each entry lists where the review stands, what is
> already proven, and the leads still worth exploring. Search the session transcript for `FINDING #<n>`.

## Start here

### <Lead title, phrased as a hypothesis>

- **Origin:** found while reviewing #<N>. Not verified, no PoC yet.
- **The hypothesis:** <what might be wrong, with `file:line` for each side>.
- **Why it might break:** <the scenarios, both directions if there are two>.
- **Leads:**
  1. **<First check, the one that can kill the hypothesis cheaply.>**
  2. **<Quantify the effect or the threshold.>**
  3. **<Write a PoC, starting from <existing PoC path>.>**
  4. **<Duplicate check against #X, #Y.>**

## Parked reviews

### #<N> — <title>

- **Issue:** <URL> (<author>, filed <Rating>)
- **Status:** preliminary verdict **<valid/invalid>, <Rating>**, <scope>. Parked: <why>.
- **Mechanism:** <two sentences with `file:line`>.
- **Proven:** <PoC paths and the figures they log>.
- **Related, not duplicates:** <#X (difference)>, …
- **Leads:**
  1. **<…>**

## Other open items

- **#<N> — <title>** (verdict: <…>)
  - **Action:** <post comment X | close #Y as duplicate | apply full fix and re-run>.
