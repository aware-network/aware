# Protocol — Issues (simple, single-file)

Goal: each issue is tracked in **one** Markdown file with a stable tag so we can close the feedback loop.

## Create an issue

1) Pick a descriptive `slug` (kebab-case).
2) Create a file:
   - `docs/issues/YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md`
3) Add a `Tag` derived from the slug:
   - `fb/YYYY-MM-DD/<slug>`

## Daily entrypoint (required for active work)

- Use `docs/issues/YYYY/MM/DD/issues-YYYY-MM-DD.md` as the day’s index/capture log.
- Keep a `## Priorities (recommended for shipping)` section in the daily index.
- Agent coordination feed lives in:
- `docs/feed/PROTOCOL.md`
- `docs/feed/FEED.md`
- `docs/feed/YYYY/MM/DD.md`
- If issue status changes or ownership moves, append to the issue + day index same cycle; then mirror the movement in `docs/feed/YYYY/MM/DD.md`.

## Feed alignment ownership

- Working agents update `docs/feed/YYYY/MM/DD.md` for scoped, day-level movements:
  - state transitions
  - blockers
  - handoffs
  - owner/repo-path evidence
- Maintainer owns `docs/feed/FEED.md` refresh and global alignment checks.

## Issue-state sync into agent feed (recommended)

Use this loop whenever the maintainer pings for status:

1) Read current issue headers (`Status`, `Owner`, `Priority`) for active issue files and latest entries in `docs/feed/YYYY/MM/DD.md`.
2) Refresh `docs/feed/FEED.md` as a point-in-time snapshot.
3) Update:
   - `Last updated` (UTC timestamp)
   - `Shipping now (P0 / In Progress)`
   - `Needs owner now (P0 / Open)`
   - `Recently closed (today)`
   - `Alignment checks` (drift between FEED lines and issue file headers)
4) Append one bullet in:
   - `docs/feed/FEED.md` → `Pulse log (append-only)`
   - `docs/feed/YYYY/MM/DD.md` (daily append-only entries)
   with timestamp + recorder id + what was refreshed.

Rules:

- Keep FEED bullets short and path-first.
- Per-issue files remain SSOT; agent FEED is the coordination snapshot.
- If mismatch exists, do not hide it: list it under `Alignment checks` and resolve on next pulse.

## Required header fields (top of file)

- `Slug`
- `Tag`
- `Status` (`Open` | `In Progress` | `Closed` | `Blocked`)
- `Owner` (agent id / person)
- `Priority` (`P0` | `P1` | `P2` | `TBD`)
- `Captured` (date)
- `Recorder` (agent id)
- `Source`
- `Ownership Scope` (required when using `aware-cli commit`)

## Recommended header fields (top of file)

- `Goal` (recommended: `goal/YYYY-MM-DD/<goal-slug>` or `TBD`; goals are product-level pointers, issues remain the commit rail)
- `Spec` (recommended: repo-relative path to `SPEC.md` for spec-driven work; see `docs/specs/PROTOCOL.md`)
- `Phase` (recommended: repo-relative path to the phase README for spec-driven work; see `docs/specs/PROTOCOL.md`)
- `Iteration` (recommended: repo-relative path to the iteration README for spec-driven work; use `phases/<phase>/iterations/<iter>/README.md`)

Identity rule:

- `Owner` and `Recorder` must use the stable provider-backed execution identity format (`<provider>-<provider_session_id>`) for active ownership.
- `provider` must be lowercase snake_case and identify the harness/session owner (for example `codex`, `claude_code`), not the model family or vendor.
- If stable execution identity is unknown, use `Owner: Unassigned`.
- Do not continue implementation with alias identity ownership; mark issue `Blocked` until remapped.
- Future canonical actor ids (`apt_id`, `aware_id`) are additive and do not replace the active execution identity in issue ownership fields.

Ownership scope rule (commit rail):

- `Ownership Scope` must list explicit repo-relative paths owned by the issue.
- Wildcards are not allowed (`*`, `?`).
- Absolute paths are not allowed.
- Recommended format:
  - header list: ``- Ownership Scope: `path/a`, `path/b`, `path/c` ``
  - or dedicated section:
    - `## Ownership Scope`
    - one `- <repo-relative-path>` entry per line.

Canonical commit governance rule:

- Agent mutation is `aware-cli commit` only (no raw `git add`/`git commit`).
- Required preflight for every mutation:
  - issue `Status: In Progress`
  - stable owner identity (`<provider>-<provider_session_id>`)
  - explicit owned `--path` entries
  - `aware-cli commit ... --dry-run` success before non-dry-run
- Fast-eyes override is allowed only with explicit Luis approval and still uses `aware-cli commit` one-shot.
- `Closed` issues are not commit-eligible. The canonical order is:
  - implementation commit(s) while the issue is still `In Progress`
  - final receipt/closeout commit that records prior implementation evidence and flips the issue doc to `Closed`
  - no further commits on that issue unless Luis explicitly approves an override or the lane is intentionally reopened
- Commit evidence must be appended in issue `Updates` with:
  - approval context (if override)
  - commit hash
  - committed path list

## Editing rules (parallel-safe)

- Header fields are **modifiable**.
- `Updates` is **append-only** (add a dated bullet; do not rewrite history).
- To claim work: set `Owner` + set `Status: In Progress` + append an update with date + owner.
- To close: prepare the receipt/closeout update while the issue still counts as `In Progress`, then in that final canonical commit set `Status: Closed`, fill `Resolution` + `Verified-by` (or `Needs Verification`), and append the final update.

## Recommended CLI lifecycle rail

- Prefer lifecycle-first commands over hand-editing status fields when the local CLI rail is available:
  - `aware-cli issue open`
  - `aware-cli issue claim`
  - `aware-cli issue block`
  - `aware-cli issue resume`
  - `aware-cli issue reopen`
  - `aware-cli issue note`
  - `aware-cli issue sync`
  - `aware-cli issue finalize`
- Treat the older low-level commands (`set-status`, `set-owner`, `bind-scope`, `append-update`, `append-evidence`, `materialize`) as backend primitives and migration rails, not the primary operator workflow.
- `finalize` must preserve canonical commit ordering:
  - prior implementation commit already exists
  - finalize prepares the closing issue/day-index/feed docs
  - finalize runs the closeout `aware-cli commit`
  - the post-commit issue-state sync then makes the issue locally `Closed`

## Priority meaning (recommended)

- `P0` — ship blocker (crash, data loss, forced restart, severe perf/battery, cannot complete core flow).
- `P1` — major UX friction (core flow works but feels broken/slow/confusing).
- `P2` — improvement / feature (valuable, but not blocking a release).
- `TBD` — not triaged yet.
