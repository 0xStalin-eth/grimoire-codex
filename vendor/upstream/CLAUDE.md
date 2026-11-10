# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Grimoire is a Claude Code plugin — a security research toolkit that transforms vulnerability discovery into structured proof-of-concept code for responsible disclosure. It's a collection of markdown-driven skills, reference documents, and (planned) agents. There is no traditional build system, runtime, or compiled code.

**Install:** `claude --plugin-dir /path/to/grimoire`

## Architecture

### Specification vs Implementation (Critical)

The codebase has a strict separation:

- **`grimoire/`** — Human-written specifications (source of truth). **Read-only.** Never modify these files. They are an Obsidian vault containing agent specs, concept docs, skill specs, and the project roadmap (`notes.md`).
- **`skills/`** — Implementation of those specs as Claude Code skills. This is where development happens.
- **`.claude/commands/gap-analysis.md`** — Command that compares specs against implementation to identify what needs building.

### Plugin Structure

```
.claude-plugin/plugin.json    # Manifest (v0.1.0, auto-discovers skills)
skills/                       # Implemented skills (each is a directory)
  <skill-name>/
    SKILL.md                  # Skill instructions (frontmatter + workflow)
    references/               # Deep-dive docs the skill can reference
    examples/                 # Worked examples
    scripts/                  # Automation (bash)
grimoire/                     # Specs — DO NOT MODIFY
forge-poc-templates/          # Git submodule: Immunefi's Solidity PoC library
```

### Implemented Skills

| Skill | Purpose |
|-------|---------|
| `write-poc` | Write proof-of-concept exploits (6-phase workflow, 10 reference docs covering 20+ vuln classes) |
| `mitigation-review` | Review client fixes per finding: report/issue/fix-commit mapping, pre/post-fix PoCs, verdict, report write-up |
| `peer-review` | Validate findings written by peers or AI agents: reproduce with a PoC, check validity, scope, severity and duplicates, verify the fix, produce the verdict and follow-up write-ups |
| `findings-sync` | Mirror the findings repo locally: pull new issues, and update existing ones after preserving the original write-up and every replaced version |
| `validate-hypothesis` | Settle a hypothesis from `hypotheses/WIP/` (manual or from delve): explore, check intent, prove with a PoC, independent triage, then promote to a finding draft or close as invalid / expected behavior |
| `write-hypothesis` | Turn an idea or a part of the conversation into a `hypotheses/WIP/` file in the summon format, with outcomes narrowed to ruled out / open / confirmed; writes and stops |
| `summon` | Initialize a grimoire workspace on a new codebase (creates GRIMOIRE.md, maps architecture) |
| `cartography` | Map and document code flows with indexed YAML-frontmatter cartography files |
| `review-cartography` | Verify and refine existing cartography flows |
| `gc-cartography` | Detect overlapping flows, merge/deduplicate cartography |
| `tome-sync` | Sweep tomes for copies that drifted from their owner section (`tomes/LINKS.md`), map unlinked shared topics, fix only what the user approves |

### Specified but Not Yet Implemented

**Skills:** Semgrep rules, Slither detectors, CodeQL integration

Use `/gap-analysis` to get a current prioritized view of what's spec'd vs built.

## Skill Development Conventions

- Each skill lives in `skills/<name>/` with a `SKILL.md` containing YAML frontmatter (name, description, triggers, `user_invocable: true`)
- **Skill names must be lowercase and hyphenated** (e.g. `write-poc`, `gc-cartography`) — no spaces, no capitals. The `name` field in SKILL.md frontmatter and the directory name must both follow this format. This matches the Claude Code skill spec: only lowercase letters, numbers, and hyphens are allowed (max 64 characters).
- Skills use numbered-step workflows with explicit human confirmation points
- Supporting material goes in `references/` and `examples/` subdirectories
- All skills produce concrete artifacts (GRIMOIRE.md, cartography files, PoC scripts)
- Skills auto-load via `"skills": "auto"` in plugin.json — no manifest changes needed
- **Skills and agents must be protocol-agnostic.** They have to work for any research engagement. Never
  include anything specific to a client or protocol: no names, contract/function identifiers, addresses,
  commit hashes, repo URLs, report excerpts, or figures from a real engagement. This applies to SKILL.md,
  `references/`, `examples/`, script comments and agent specs. When a skill is distilled from a real
  engagement, generalize its examples into placeholders (`<ID>`, `Router::_withdraw`, `AdapterA`) or
  templates, and don't copy that engagement's files in. This repo is public, so engagement content in it
  would also leak confidential audit material. Before finishing a skill, grep it for the source
  engagement's identifiers.

## Key Principles

- **Trivial verifiability**: Every finding must be provable with a concrete artifact
- **Minimum viable proof**: Demonstrate the issue exists, nothing beyond that
- **Benign payloads only**: `alert(1)`, `sleep()`, `id` — never destructive commands
- **Parameterized targets**: localhost and variables, never hardcoded production URLs
- **Authorized contexts only**: pentesting, bug bounty, coordinated disclosure, CTF
