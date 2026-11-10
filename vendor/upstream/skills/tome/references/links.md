# Tome Links (`grimoire/tomes/LINKS.md`)

Tomes are written to be read on their own, so a topic often appears in several of them: a new tome is
spun off a section of an older one, or a short summary of a mechanism is repeated where a reader needs
it. Without a record of where each topic lives, new understanding lands in one tome and the others
quietly go stale. `LINKS.md` is that record.

## Model

- **Owner:** the one section that holds the full, current version of a topic.
- **Copies:** shorter versions in other tomes, written for their own reader. A copy may carry extra
  local detail (code references, a different example), but it must not contradict the owner.
- **Direction:** owner → copies. New understanding goes into the owner first, then out to the copies.
  When the newer understanding is being built in a copy, ownership can move there (see "Choosing the
  owner").

Don't merge tomes to remove duplication, and don't rewrite copies mechanically from the owner. A copy
is a summary written for its own tome, so updating it takes judgment.

## Format

```markdown
# Tome links — which section owns each shared topic

<one paragraph: what this file is>

**Rules**
<the editing rules below, copied in so a reader of the file sees them>

**ID families**
<every ID prefix used across the grimoire, e.g. K = kickoff question, FQ = follow-up question,
I = idea, L = lead, R = research, and any protocol invariant IDs. Note prefixes that collide.>

## <Area>

| Topic | Owner | Copies | Synced | Status |
|---|---|---|---|---|
| <the claim, in a few words> | <tome> › <section> | <tome> › <section> · <tome> › <section> | YYYY-MM-DD | in sync / **drift D<n>** |

## Open drift

| # | Where | What is out of date |
|---|---|---|
| D1 | <tome> › <section> | <what the copy says vs what the owner says> |
```

- Name tomes without `tomes/active/` and `.md`. Name sections by their heading, so a search finds them.
- Group rows by area (rate and tokens, flows, liquidity, books, termination, ...), whatever the
  engagement's tomes are organised around.
- `Topic` names the **claim** that must stay consistent, not just the subject.
- `Open drift` IDs are never reused. A fixed row is struck through (`~~D3~~`) with what was done and
  when; a partly fixed one says what is still open.

## Choosing the owner

Ownership is per **topic**, not per tome. One tome can own the topics it goes deep on and be a copy for
the topics it only borrows for context.

**A new row:**
1. **Subject first.** The owner is the tome whose subject the topic is: a tome about swaps owns swap
   mechanics, a glossary owns definitions, an architecture tome owns the component tables.
2. **Tie-break: the fullest current explanation of the claims.** When two tomes have an equal claim to
   the subject, pick the section that states the claims most completely and most recently. Extra code
   references, line numbers or examples in a section don't make it fuller; claims do.
3. **Say which owner you picked** when you add a row. The user can override any owner.

**A new tome built from existing tomes** starts as a **copy** for every topic it pulls in, even when it
gathers several of them into one place. Add it to each topic's copy list; the owners don't change.

**Push up or transfer.** The first time an edit adds a claim to a copy that the owner doesn't have,
choose:
- **Push up:** write the new claim into the owner as well, then sync the other copies. The owner stays.
  Default when the topic is background for the tome being edited.
- **Transfer:** the edited section becomes the owner. Default when the topic is the tome's subject, i.e.
  the tome exists to go deep on it. Without transfers, a deep-dive tome keeps feeding its findings back
  into thinner parent sections, and the parents stay "owners" of a topic they no longer cover best.

**To transfer ownership:**
1. Move the row's owner to the new section and add `owner moved from <old tome › section> on
   YYYY-MM-DD` in the row (in the Topic cell or a note under the table).
2. The old owner becomes a copy: it keeps its summary, gains the new claim in short form, and ends with
   a `Source:` line pointing to the new owner.
3. Sync the other copies from the new owner.
4. Tell the user, so they can override.

Never transfer silently, and never transfer because a section is longer. Transfer because it is where
the topic is now being worked on.

## Editing rules (apply on every tome edit)

1. **Before editing a section, look it up in `LINKS.md`.** Search for the tome and section name.
2. **If the edit changes a claim** (a mechanism, a number, a status, an ID), update the owner and every
   copy in the same pass, and bump `Synced`. Wording, formatting or extra local detail in a copy needs
   no sync.
3. **If an edit adds a claim to a copy that the owner doesn't have,** decide whether to **push it up**
   or **transfer ownership** (see "Choosing the owner"), and say which you chose.
4. **If an owner and a copy disagree** and it isn't obvious which is right, ask the user. Don't assume
   the owner wins.
5. **Say which section is the owner** before fixing drift, especially when a stale copy sits inside a
   tome that owns other topics.
6. **When a tome or section is spun off another one,** add it to the copy list of each topic it pulls
   in, in the same pass. It owns nothing yet; ownership moves later, by transfer.
7. **Copies end with a source pointer:** `Source: [[tomes/active/<owner-tome>]] §<section>.`
8. **Drift found but not fixed** goes under `Open drift`, and its rows are marked `**drift D<n>**`.
   Fix drift only after the user OKs it.
9. Log every tome change in `tomes/SESSIONS.md` as usual, and log `LINKS.md` changes there too.

The owner is trusted as written: propagation copies its claims, it does not re-verify them. If an
owner looks wrong, raise it before pushing it out to every copy.

## When there is no `LINKS.md` yet

Create it the first time a topic is written into a second tome, or when `/tome-sync` is run. Start
with the topics actually shared; don't map single-tome topics.
