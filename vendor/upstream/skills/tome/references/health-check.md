# Tome Health Check

Use this reference when asked to review tomes, audit the research wiki, or check that a
tome task is complete.

## Lint And Review

Check:

1. Broken wikilinks.
2. Pages missing from `grimoire/tomes/index.md` when that index exists.
3. Missing or invalid frontmatter fields.
4. Source references that do not resolve to preserved or inspectable evidence.
5. Claims without scope or provenance.
6. `high` confidence claims with weak or single-source support.
7. Pages whose versions do not match the current research target.
8. Pages marked `contested`, `contradicted`, `stale`, or `confidence: low`.
9. Unresolved claims and hypotheses that appear as facts elsewhere.
10. Contradictions missing from `grimoire/tomes/notes/contradictions.md`.
11. Finding candidates without reproduction evidence or clear uncertainty.
12. Pages over about 200 lines.
13. Potential secrets in research files. Report file paths and field names, never secret values.
14. Active-test records without authorization or scope references.
15. Copies that contradict their owner in `grimoire/tomes/LINKS.md`, topics repeated across tomes
    with no `LINKS.md` row, and stale `Open drift` entries. `/tome-sync` runs this check in full.

Group issues by severity:
- Unsafe scope or exposed secrets
- Invalid evidence or broken provenance
- Contradicted security conclusions
- Missing target or version alignment
- Broken navigation and coverage gaps
- Stale content and style problems

Do not silently repair a security conclusion that needs human judgment.

## Completion Checklist

A tome task is complete only when all applicable checks pass:

- [ ] The target, version, deployment, and authorization are explicit.
- [ ] Important evidence is preserved, inspectable, or recorded as missing.
- [ ] Source coverage reflects the available evidence.
- [ ] Important claims have support, state, confidence, scope, and provenance.
- [ ] Contradictions and unknowns remain visible.
- [ ] Active tests are safe, reproducible, and linked to authorization.
- [ ] Tome pages use valid types, frontmatter, and links.
- [ ] New pages are discoverable from `GRIMOIRE.md`, an index, log, or related page.
- [ ] Every claim changed in an owner section is also changed in its copies (`LINKS.md`), and new
      shared topics have a row.
- [ ] The final answer separates facts, interpretations, hypotheses, and unknowns.
- [ ] No secret value appears in the output.
- [ ] The user receives a list of every file created or updated.
