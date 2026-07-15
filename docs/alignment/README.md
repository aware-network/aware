# Alignment

`docs/alignment` is the durable citation surface for current Aware invariants.
It exists so concurrent agents and humans can reference the same present-tense
direction while issues, FEED, goals, skills, and SDK work move in parallel.

## Boundary

Alignment docs are not the execution rail.

- Issues remain the ownership and commit rail: `docs/issues/PROTOCOL.md`.
- FEED remains the live coordination snapshot: `docs/feed/PROTOCOL.md`.
- Goals remain product targets across issues: `docs/goals/PROTOCOL.md`.
- Conversations remain long-form mental-model capture: `docs/conversations`.
- Skills are the procedural automation layer: `skills/README.md`.
- Public product usage starts at the SDK rail: `workspaces/aware_network/modules/interface/sdks/aware/README.md`.

Alignment docs should state durable invariants and current topic locks. They
should not duplicate issue updates, test logs, or implementation details that
belong in issue files.

Real-time reviews use alignment as their lock source. A review may inspect an
active issue's dirty worktree evidence and flag drift against cited
conversation, goal, issue, or alignment locks, but it must not take ownership of
the target implementation issue or edit target implementation files unless the
issue is explicitly handed off.

## Current Surface

- [PROTOCOL.md](PROTOCOL.md) is the required alignment loop for shared
  coordinates and invariant promotion.
- [CURRENT.md](CURRENT.md) is the mutable private current-topic synthesis for
  this workspace.
- [PUBLIC.md](PUBLIC.md) is the public-safe current synthesis used by the
  `aware-network/aware` facade.
- `daily/YYYY/MM/DD.md` entries aggregate receipt movement before maintainers
  promote it into `CURRENT.md`.
- Topic statements should cite issue/protocol/SDK refs where possible.
- If an invariant changes, update `CURRENT.md` through an issue-first workflow
  and append the reason in that issue's `Updates`.

## Alignment Center Contract

The alignment center is this index plus the current/public/daily alignment
surfaces. It synthesizes where the system is going; it does not own execution.

- Issues own work, status, ownership, and commit scope.
- FEED owns live coordination pulses.
- Goals own product target lanes and issue rows.
- Specs own long-lived implementation contracts.
- Alignment owns durable shared coordinates and current synthesis.

Agents keep the center alive by appending issue-derived daily alignment
receipts and promoting only receipt-backed coordinates into this index,
`CURRENT.md`, or `PUBLIC.md`. `AGENTS.md` remains the bootstrap contract that
points agents here.

## Global Invariants

`A-001`: Issues, FEED, goals, alignment, conversations, and skills are distinct
coordination surfaces. Do not collapse them into one document or invent a new
ontology first.

`A-002`: Protocols become executable through skills. The near-term path is
protocol docs -> canonical skill packs -> service/API automation, not ad hoc
agent memory.

`A-003`: The durable product rail is Interface-SDK-first:
`aware-sdk -> interface-sdk -> Interface -> Experience -> API/Services`, while
Flutter/platform renderers consume the same `interface-sdk` boundary directly.
Product workflows must not bypass
`workspaces/aware_network/modules/interface/sdks/aware` into domain SDKs,
service internals, or a separate agent-only door.

`A-004`: Every meaningful action should leave a receipt. Receipts are the
provenance surface for agents, humans, services, and later UI panes.

`A-005`: Ontology functions are mutation/action contracts. Authored ontology
`read` functions and callable `opg_read` rails are retired because they create a
second query model.

`A-006`: Reads are commit-driven. Services read committed/materialized state or
service-owned DB/read models, then expose service/view DTOs.

`A-007`: Environment committed DTO verification is the trust layer for proving
branch/projection state as Ontology DTOs. It complements service views without
making ontology expose reads again.

`A-008`: Identity owns actor personal history through `ActorCommit` and
`resolve_actor_commits`. Do not replace it with raw commit-author reverse
lookups.

`A-009`: Meta remains the function-call and OIG commit authority. Service
actions should route through API/service/runtime contracts down to Meta commits.

`A-010`: Alignment coordinates are issue-derived and receipt-backed. Broad
direction must cite issue/protocol/goal/alignment refs before it becomes a
durable invariant.

`A-011`: WorkspaceRevision can be producer-side committed truth, but public and
runtime consumers should move through generated DTOs, SDKs, Hub, Network, and
Node receipts instead of requiring Workspace internals.

`A-012`: `AGENTS.md` is the bootstrap contract. The full alignment loop lives in
`docs/alignment/PROTOCOL.md`.

`A-013`: Public protocol docs must not cite private issue/feed paths that are
absent from the public facade. Public receipts are added only after public
issues, packages, or integration proofs exist.

`A-014`: `CURRENT.md` is mutable aggregate truth. Daily alignment tracks collect
fresh receipt movement so later maintainers or services can promote stable
current coordinates.

`A-015`: Real-time review is alignment-derived. Review findings must cite the
active issue, the lock source, and the observed evidence. A review flag is not a
replacement for the target issue owner, implementation receipt, or commit rail.

`A-016`: Attribution receipts must distinguish ownership from observation. Until
the agent harness emits edit-event receipts, local dirty-delta or watcher output
is observer evidence only; it cannot prove which Codex session wrote a file.

`A-017`: The alignment center is maintained by receipt-backed synthesis, not by
copying current direction into `AGENTS.md` or generated checkout targets.

`A-018`: External and common-agent contribution should converge on
`aware-dev`/service-backed SDK/API rails while alignment remains the shared
semantic coordinate surface.

## Update Rules

1. Work issue-first.
2. Follow `docs/alignment/PROTOCOL.md` for current-direction and invariant
   promotion work.
3. Keep statements short, current, and citeable.
4. Prefer updating `CURRENT.md` over spreading new invariant prose into random
   issue updates.
5. Preserve older conversations and issue history as historical evidence; do
   not rewrite them to match new alignment.
