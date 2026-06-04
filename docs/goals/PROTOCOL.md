# Protocol - Goals (shared goals, lanes, issue rows)

Purpose: coordinate multi-agent work around shared **direction targets** without
bloating `docs/feed/FEED.md` or forcing a monolithic `GOALS.md`.

Goals are not a commit rail. Issues remain the unit of work, ownership,
mutation, validation, and closeout. A goal records the direction chain that
multiple issues are advancing. The canonical target bridge is:

`Goal -> GoalLane -> GoalLaneIssue -> Issue`

Do not add canonical lane-less issue rows. During migration, use a
default/migration lane so all future consumers learn only the lane model.

## Files

- Active pointer surface (bounded): `docs/goals/LATEST.md`
- Optional sparse global history (append-only): `docs/goals/HISTORY.md`
- Goal template: `docs/goals/TEMPLATE.md`
- Per-goal SSOT files:
  - `docs/goals/YYYY/MM/DD/goal-YYYY-MM-DD-<goal-slug>.md`
  - Existing or product-local filenames may remain stable, but new goals should
    use the `goal-YYYY-MM-DD-...` prefix unless a maintainer chooses otherwise.

The per-goal date path is a capture anchor, not a daily running-state index.
Long-lived goals stay in their original file. Active/running state comes from
goal status, goal lanes, lane issue rows, and linked issue headers, not from
moving goal files between daily folders.

## Ownership model

- Maintainer (or delegated scribe) owns:
  - `docs/goals/LATEST.md`
  - `docs/goals/HISTORY.md` (if used)
- A goal file has one `Owner` for stewardship.
- Goal lanes are visible coordination streams scoped to an owner/role.
- Any agent may propose edits, but only through an issue-first workflow whose
  ownership scope includes the goal file.

Lane ownership is an execution identity snapshot today. Future ontology may
attach lanes to identity `Actor`, `ActorRole`, and role/capability references.
Do not create a goal-specific actor type. Actor/role identity is a shared
identity concern.

## Goal status semantics

Use one:

- `Proposed` - captured but not active
- `Active` - currently shipping
- `Blocked` - active but cannot progress (explicit blocker + refs required)
- `Achieved` - Definition of Done met (evidence required)
- `Parked` - intentionally paused
- `Superseded` - replaced by another goal (ref required)

## Goal file template (SSOT)

Each goal file should contain:

- `Slug`
- `Tag` (recommended: `goal/YYYY-MM-DD/<goal-slug>`)
- `Status` (see above)
- `Stage` (recommended: `Meta` | `OS` | `Experience` | `Attention`)
- `StageDetail` (optional; free text)
- `Priority` (optional; `P0` | `P1` | `P2`)
- `Confidence` (optional; `Low` | `Medium` | `High`)
- `Owner`
- `Captured` (date)
- `Review-by` (optional; date to force a focus review without promising a deadline)
- `Source` (conversation refs / direction docs)
- `Tracking issue` (the issue that created or last materially reshaped the goal)

Sections (recommended):

- `## Why` (max 3 bullets)
- `## Definition of Done` (checkboxes; receipts/tests explicit)
- `## Locks (SSOT)` (the minimal invariants + links to conversations)
- `## Coordination Strategy` (how lanes synchronize on this goal)
- `## Lane Map` (current visible lanes, owners/roles, current issue, receipt)
- `## Forward Plan By Lane` (planned lane issues before they are opened)
- `## Issue Matrix` (lane-owned issue rows; see matrix contract below)
- `## Execution Map` (short refs to key issue clusters or supporting docs)
- `## Evidence` (links to tests/receipts/proofs; no vibes)
- `## Updates (append-only)` (only major transitions, not daily work logs)

Tip: copy `docs/goals/TEMPLATE.md` when creating a new goal file.

## LATEST.md rules (bounded pointer-only)

`docs/goals/LATEST.md` must stay readable:

- Max active goals: 1-3
- Pointer-only: goal file path + 3-10 key refs (issues/conversations/docs)
- No inline issue matrix. The bounded issue matrix lives in the goal file.

## SDK and view consumer contract

Operational consumers must use the Goal SDK contract as the interface:

- Source of truth for SDK/CLI/local-files behavior:
  `workspaces/aware_coordination/modules/workflow/sdks/goal/python/public/README.md`
- Agent and Aware-Dev consumers should not parse this protocol as an API
  contract. This protocol defines docs SSOT shape; the SDK README defines
  callable/parseable behavior.
- Goal CLI commands are shims over the Goal SDK only. They may route arguments,
  resolve repo paths, and print results, but they must not own separate goal
  filesystem mutation semantics.
- Local filesystem support belongs behind the local Goal SDK, similar to the
  Issue SDK local-files helper.
- Markdown goal files are filesystem view projections. The long-term target is
  that the Goal service resolves a Goal view model, the Goal SDK renders/syncs
  Markdown, and Codex/agents consume either the SDK or the projected filesystem
  view.

## How goals relate to issues

Issues are execution units; goals are product targets.

- **Issue -> Goal**: recommended header field in issue files:
  - `Goal: goal/YYYY-MM-DD/<goal-slug>` (or `Goal: TBD`)
- **Goal -> Lanes**: `GoalLane` rows list the visible actor/role-scoped streams
  advancing a shared goal.
- **Lane -> Issues**: `GoalLaneIssue` rows list the issue chain owned by that
  lane. The Markdown `Issue Matrix` is the docs projection until the SDK
  exposes the materialized row surface everywhere.

Rules:

- Do not duplicate issue updates inside goals.
- One active owner per issue. If work needs multiple owners, split rows into
  multiple issues or multiple lanes.
- A goal update should only happen when the goal state changes
  (Active/Blocked/Achieved/etc), when the DoD/locks change, or when the lane
  plan changes.
- A lane issue row may be updated when an issue is opened, claimed, blocked,
  closed, or materially changes its gate. The agent must be working through an
  issue whose ownership scope includes the goal file.

## Goal Lane contract

Every shared or parallel goal should include a `## Lane Map`.

Recommended columns:

| Lane | Role | Owner | Status | Current Issue | Since | Last Receipt | Scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `goal-coordination` | Protocol / planning | `<execution-id>` | Active | `docs/issues/...md` | `YYYY-MM-DDThh:mmZ` | Pending | Goal protocol and lane model |

Lane rules:

- `Lane` is a stable lane key within the goal.
- `Role` describes the work role, not a hardcoded ontology actor type.
- `Owner` is an execution identity snapshot today; future model may reference
  identity `Actor` / `ActorRole`.
- `Status` is `Active`, `Ready`, `Planned`, `Blocked`, or `Closed`.
- `Current Issue` is one linked issue path, `TBD:<slug>`, or `None`.
- `Since` is the lane activation/planning timestamp.
- `Last Receipt` is the latest lane receipt pointer.
- `Scope` keeps the lane boundary legible to parallel agents.

## Issue Matrix contract

Every Active goal should include `## Issue Matrix`.

Recommended columns:

| Row | Time | Lane | Tick | Issue | Gate | Status | Owner | Receipt |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `YYYY-MM-DDThh:mmZ` | `goal-coordination` | `[ ]` | `docs/issues/...md` or `TBD:<slug>` | One-line completion gate | Issue status or `Planned` | Owner or `Unassigned` | Evidence pointer |

This table maps to the target `GoalLaneIssue` surface:

- `Row` maps to the stable lane issue display row / receipt id.
- `Time` maps to the row's sync timestamp or latest major receipt timestamp.
- `Lane` maps to `GoalLane.lane_key`.
- `Tick` maps to `GoalLaneIssue.tick`.
- `Issue` maps to the optional linked `Issue` or planned issue tag.
- `Gate` maps to `GoalLaneIssue.gate`.
- `Status`, `Owner`, and `Receipt` are bounded snapshots only.

Tick semantics:

- `[ ]` - planned or open, no completion receipt yet.
- `[~]` - active/in progress.
- `[x]` - complete; linked issue is closed or has a recorded completion receipt.
- `[!]` - blocked; linked issue records the blocker.

Rules:

- Row number is a stable identity, not strict execution order.
- Cross-lane sync uses `Time`, `Lane`, and `Receipt`.
- Planned rows may use `TBD:<slug>` until the issue exists; replace with the
  issue path when opened. In the ontology/SDK surface, this is the transition
  from `planned_issue_tag` to linked `issue_id`.
- `Status` mirrors the linked issue at the last matrix touch. If it drifts, the
  issue wins.
- `Receipt` is a pointer only: issue update, commit id, test path, report path,
  or proof artifact. Do not paste daily logs into the goal.
- Agents tick rows through their active issue. If the goal file is not in the
  issue ownership scope, append an issue/feed note asking the goal owner or
  scribe to refresh the matrix.

## Interaction with FEED

- `docs/feed/YYYY/MM/DD.md` remains the daily append-only movement log.
- `docs/feed/FEED.md` remains the global snapshot.
- FEED should link to `docs/goals/LATEST.md` instead of restating goals.

## Ontology mapping

This layout maps to current and next canonical modeling:

- `issue.aware` (task execution + ownership scope)
- `task.aware` (work items / sub-issues)
- `goal.aware` (direction target and lane parent)
- `goal_lane.aware` (target visible lane stream under a Goal)
- `goal_lane_issue.aware` (target lane-owned Issue row)

The expected ontology path for goal sources is under coordination Workflow:

- `workspaces/aware_coordination/modules/workflow/ontology/structure/aware/goal/`

## View projection mapping

Markdown files under `docs/goals/**` are the current filesystem view projection.
The long-term target is:

1. Goal ontology owns state.
2. Goal service resolves view DTOs.
3. A small goal experience declares the view surface.
4. Goal SDK renders/syncs Markdown from the view model.
5. CLI and Aware-Dev route through SDKs, not ad hoc file parsers.
