# Codex execution adapter

Read this before following the workflow. Keep the original stages, evidence standards, safety rules,
confirmation points and output schemas. Treat `/skill-name` as a request to use `$skill-name`;
maintenance commands use `$grimoire-<command>`. These are workflow references, not shell commands.

- Determine the installed Grimoire-Codex root from this skill's real path (follow symlinks).
  `skills/...` and `agents/...` resource paths are relative to that root, not the audit target.
  Resolve them to absolute paths before invoking scripts. `references/`, `scripts/`, `examples/`
  and `../other-skill/` refer to the current skill's directory. Keep each script's documented
  working directory (usually the engagement or target repo root), so output stays with the audit.
- At entry, read the engagement's `GRIMOIRE.md` if it exists. For workspace initialization run
  `python3 <installed-root>/scripts/bootstrap.py` explicitly; Codex does not execute the archived
  Claude lifecycle hooks. Bootstrap is idempotent and only initializes the personal store.
- Before session-aware work, set `GRIMOIRE_SESSION_ID` in every shell invocation. Use a verified
  Codex thread ID when available; otherwise create a UUID once and keep it as an explicit run ID.
  Record the distinction in the engagement log. A run ID is not a resumable chat ID. Reuse it only
  for the same logical session; a new independent agent needs a new ID. Resume a chat only with a
  verified runtime chat ID. Never infer a chat ID from an isolated-copy folder or guess an ID.
- For a named role, load `<installed-root>/agents/<role>.md`, or use `$grimoire-<role>`.
  When the workflow delegates, spawn a Codex subagent with that procedure, scope, evidence inputs,
  output path and permissions. Use bounded batches within the runtime's available concurrency.
  Keep the upstream role's intended access restrictions in the prompt; these are instructions,
  not a security sandbox. A role skill alone does not create a separate execution context.
- Mandatory independent Familiar/Hag reviews require a separate agent context. Give reviewers the
  claim and raw evidence without the author's verdict. If subagents are unavailable, stop that
  stage and request a separate fresh Codex session; save a handoff. Do not label same-context
  self-review independent, skip triage, or declare an unreviewed finding confirmed.
- After EVERY Sigil result, explicitly dispatch Familiar triage before presenting findings,
  except where the engagement explicitly opted out via `.grimoire/no-auto-triage`. This replaces
  the PostToolUse hook and also applies to checks or variant hunts outside summon. Wait for the
  verdict. Preserve confirmed/uncertain findings, dismissal counts and verification limitations.
- Translate file read/search/edit/shell and web research instructions to available Codex tools.
  Discover MCP tools by service and operation; do not assume a Claude namespace or tool allowlist.
  Prefer configured Context7 documentation and claudit findings operations, with cited web/file
  fallback as the Librarian procedure specifies. Missing tools reduce coverage: report the gap.
- Do not expose secrets or confidential findings in this public toolkit. Audit artifacts belong in
  an authorized engagement workspace. Never publish a finding, issue comment or report without
  explicit user authorization. No production execution without explicit authorization.
