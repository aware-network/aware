# Agent Feed Protocol (append-only, no locks)

Purpose: coordinate many agents in one shared workspace using append-only feed intelligence.

## Files

- Global live snapshot: `docs/feed/FEED.md`
- Daily append-only log (canonical): `docs/feed/YYYY/MM/DD.md`

## Ownership model

- `docs/feed/FEED.md` is managed by the maintainer view (`Luis` or delegated manager).
  - Update on maintainer pulse request or when global truth changes.
- Working agents update daily logs (`docs/feed/YYYY/MM/DD.md`) for state movement in their active issue scope.
  - One append-only line per notable movement, including evidence references.

## Core rules

1) No locks, no rewrites, append-only coordination.
2) First post from each agent must include stable session id.
3) Work still goes through issue files in `docs/issues/**` (issue files remain SSOT for problem state).
4) Feed is the coordination rail for:
   - who is working on what now
   - blockers/conflicts
   - handoffs and negotiation
5) Sync from shared files (`docs/issues/**`, `docs/feed/**`), not from Git history operations.
6) Keep `docs/feed/FEED.md` current with explicit global truth blocks (`Node`, `Tests`, `Compile`, `Release`).
7) If status is uncertain, mark it as `watch`/`needs-verify` instead of implying closure.
8) Commit mutation governance is canonical: agents use `aware-cli commit` only, with explicit owned paths and `--dry-run` preflight.

9) Daily-log refresh contract:
   - If an issue header/status changes, append daily-line evidence in `docs/feed/YYYY/MM/DD.md` in the same cycle.
   - If maintainer requests a pulse, reconcile daily lines against issue headers and patch FEED alignment immediately.

## Identity contract (required)

- Active owner/recorder identity must be a stable provider-backed execution id: `<provider>-<provider_session_id>`.
- `provider` must be lowercase snake_case and identify the harness/session owner (for example `codex`, `claude_code`), not the model family or vendor.
- Alias identities are not valid for ownership (example: model aliases).
- If identity is missing/unmapped:
  - set issue `Owner: Unassigned`
  - set issue `Status: Blocked` (or keep `Closed` if already closed)
  - append a feed/daily entry with `type=blocker` and `scope=identity-remap`
- No further implementation movement on that issue until identity remap is complete.

## Daily log entry format

Use one bullet per event:

- `<UTC timestamp>` | `agent=<execution-id>` | `type=<heartbeat|claim|update|blocker|conflict|handoff|resolved|pulse>` | `scope=<short scope>` | `refs=<paths>` | `<note>`

If the entry reports a commit mutation, include evidence in `<note>`:
- commit hash
- issue tag
- committed path list
- override approval reference (if Fast-EYES override was used)

## Global truth block (required in `docs/feed/FEED.md`)

Each pulse refresh must update these sections:

- `Global truth (operator snapshot)`
  - Node/migration deployment state
  - Latest test truth (`aware-test --stable -v` full or module-targeted)
  - Compile/lock health for active migration tracks
  - Release/remote validation coordination state
- `Sanity board`
  - concise PASS/FAIL/WATCH lines with refs to issue/feed paths
  - include rationale when failing or blocked

## Global FEED refresh (pulse)

When maintainer asks for `pulse`:

1) Read current issue headers (`Status`, `Owner`, `Priority`) for active day(s).
2) Read latest daily log (`docs/feed/YYYY/MM/DD.md`).
3) Refresh `docs/feed/FEED.md` sections:
   - `Global truth (operator snapshot)`
   - `Sanity board`
   - `Shipping now (P0 / In Progress)`
   - `Needs owner now (P0 / Open)`
   - `Recently closed (today)`
   - `Negotiation queue (conflicts/overlaps)`
   - `Alignment checks`
4) Append a `pulse` line to:
   - `docs/feed/FEED.md` pulse log
   - `docs/feed/YYYY/MM/DD.md`

## Conflict negotiation rule

If two agents may touch same file/expectation:

1) Append `type=conflict` in daily log with involved refs.
2) Declare lead owner for that edit region.
3) Non-lead agent pivots to another scope or waits for handoff.
4) Append `type=resolved` when conflict is closed.

No deletions or rewrites in feed logs; only append corrective entries.
