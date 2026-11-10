# Bug Bounty Platform Reference

How summon's "Acquire Target" step (Step 0) fetches scope from a bug-bounty program URL,
resolves the in-scope source repositories, and prepares the workspace. Consult this when summon
is invoked with a program URL or slug (e.g. `/summon immunefi.com/bug-bounty/<program>`).

The goal of Step 0 is narrow: turn a program URL into (1) cloned in-scope repos at their pinned
commits and (2) a `scope/bounty-program.md` capturing assets, impacts, and rules. The rest of the
summon workflow then runs as usual, with Crown Jewels (Step 5) and Scope Constraints (Step 5b)
pre-seeded from the program data.

## Argument Normalization & Platform Detection

Accept the argument in any of these shapes and reduce it to a canonical program URL:

- Full URL — `https://immunefi.com/bug-bounty/compound/`
- Host + path — `immunefi.com/bug-bounty/compound`
- Bare host + slug words — `immunefi compound` (rare; treat last token as the slug)

Identify the platform by host:

| Host substring | Platform | Handler |
|----------------|----------|---------|
| `immunefi.com` | Immunefi | tuned (below) |
| `cantina.xyz`  | Cantina  | tuned (below) |
| anything else  | —        | generic fallback |

If the argument is not a URL/slug at all (e.g. it's a local path), Step 0 does not apply — fall
through to the normal summon Step 1.

## Fetching

Use `WebFetch` (load it via ToolSearch if not already available) against the platform's scope and
rules pages with a targeted extraction prompt. Ask the fetch to return, as structured text:

- **Program name**
- **Assets in scope** — for each: identifier/URL, type (`smart_contract` | `web` | `repo` |
  `blockchain` | `other`), pinned ref (commit/branch) and subpath if shown, reward tier/severity
- **Impacts in scope** — grouped by severity (Critical/High/Medium/Low). These seed Crown Jewels.
- **Out-of-scope** — assets and impacts explicitly excluded
- **Rules / prohibited actions / KYC** — these seed Scope Constraints (Step 5b)
- **Reward tiers**
- **Source URL + the date fetched**

These pages are JavaScript-rendered single-page apps. WebFetch's text conversion usually still
contains the asset/impact tables. If it does not (Cloudflare challenge, login wall, or empty/JS
shell), **do not invent scope** — fall back: ask the user to paste the scope page text, or to
provide the in-scope repo URLs (and commits) directly. Record whatever the user provides into
`scope/bounty-program.md` and proceed.

## Immunefi

- Program root: `https://immunefi.com/bug-bounty/<slug>/`
- Scope/assets: `https://immunefi.com/bug-bounty/<slug>/scope/`
- Rules/program info: `https://immunefi.com/bug-bounty/<slug>/information/`

Fetch both `scope/` and `information/`. The **Assets in Scope** table lists each asset with a type
(Smart Contract / Websites and Applications / Blockchain) and a target — for source-code assets
this is typically a GitHub URL, often pinned to a commit via a `/tree/<commit>/<path>` or
`/blob/<commit>/...` form. The **Impacts in Scope** section is organized by severity and maps
directly onto Crown Jewels. The **information** page carries prohibited actions, KYC requirements,
and out-of-scope impacts → Scope Constraints.

Note: many Immunefi smart-contract assets are **deployed contract addresses** (e.g.
`0x…` on a named chain), not repos. These are non-cloneable — record them (address + chain) and
note that local source must be obtained separately (e.g. from the project's own repo if one is
also listed, or a verified-source explorer). Do not attempt to clone an address.

## Cantina

- Hosts competitions and ongoing bounties at `https://cantina.xyz/competitions/<id>` and
  `https://cantina.xyz/bounties/<id>` (also surfaced under organization pages).
- Each scope entry generally names a **repository and a commit hash** plus the in-scope file
  globs. Extract the repo URL + commit for cloning, and keep the file globs as in-scope paths for
  the Scope section.
- Rules, severity matrix, and out-of-scope items appear on the same competition/bounty page.

## Generic Fallback (any other host)

For unrecognized hosts (HackerOne, Sherlock, Code4rena, HackenProof, a project's own page, etc.):

1. WebFetch the given URL with the same extraction prompt.
2. Pull out anything that looks like an in-scope **GitHub/GitLab repo URL** with an optional
   commit/branch, plus impacts and rules text.
3. If the page yields no usable repo URLs, fall back to asking the user (paste scope / give repo
   URLs). Many web/infra programs (HackerOne, HackenProof) have **no source repos at all** —
   their assets are domains/hosts; in that case there is nothing to clone. Record the in-scope
   domains as assets and proceed; the codebase-exploration steps will be light or N/A.

## Asset → Repository Resolution

Turn the fetched asset list into a clone plan:

- **Normalize GitHub/GitLab URLs.** From `github.com/<org>/<repo>/tree/<ref>/<subpath>` or
  `.../blob/<ref>/<file>`, extract `repo_url = https://github.com/<org>/<repo>`, `ref = <ref>`,
  and `subpath` (kept for the Scope section's in-scope paths, not for cloning — we clone the whole
  repo at the ref).
- **Dedupe** by `(repo_url, ref)`. Multiple file-level assets in the same repo+commit collapse to
  one clone.
- **Separate cloneable from non-cloneable.** Cloneable = a git repo URL. Non-cloneable = deployed
  contract addresses, live web/infra targets, or assets with no source link. Non-cloneable assets
  are recorded in `scope/bounty-program.md` but never passed to the cloner.

Pass the cloneable entries to `scripts/clone-assets.sh` as `<repo_url>@<ref>` tokens (omit `@<ref>`
when no commit/branch was specified — it will clone the default branch HEAD). The script clones
into the current directory (the project root), skips dirs that already exist, and pins commit-SHA
refs via an explicit fetch + checkout.

## Failure Handling — Never Fabricate

If at any point the scope cannot be retrieved with confidence:

- Do not guess repo URLs, commits, or impacts from memory of the program.
- State clearly what could not be fetched.
- Ask the user to paste the scope text or supply the repo URLs + commits.
- Record exactly what was provided, and cite the source URL + fetch date in
  `scope/bounty-program.md` so downstream triage knows the provenance.
