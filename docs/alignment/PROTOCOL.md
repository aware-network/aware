# Protocol - Alignment

Purpose: keep humans, agents, services, and interfaces on shared semantic
coordinates before execution. Alignment is the CEO rail for durable direction,
not a replacement for issues, FEED, goals, specs, skills, services, or commits.

Alignment is not planning. Alignment is the shared semantic coordinate system
that lets humans, agents, services, and interfaces act without drifting.

## Authority Boundary

- Issues are the ownership and commit rail: `docs/issues/PROTOCOL.md`.
- FEED is the live coordination pulse: `docs/feed/PROTOCOL.md`.
- Goals are product targets spanning issues: `docs/goals/PROTOCOL.md`.
- Specs define long-lived implementation contracts: `docs/specs/PROTOCOL.md`.
- Alignment states durable invariants and current direction locks.
- Daily alignment tracks aggregate fresh receipt movement.
- Skills and services are the automation path for protocols.

Alignment must answer two questions:

1. Which coordinates must a worker share before motion?
2. Which issue-derived invariants are stable enough to cite?

Alignment must not track per-issue status, duplicate FEED, or become an
unowned planning notebook.

## Alignment Center

The alignment center is the maintained synthesis/index over protocol, issue,
goal, FEED, spec, service, and receipt evidence. It is not a new authority and
not a replacement for the source surfaces.

- `docs/alignment/README.md` is the global invariant index and entrypoint.
- `docs/alignment/CURRENT.md` is the private current synthesis for this
  workspace.
- `docs/alignment/PUBLIC.md` is the public-safe synthesis for public checkouts.
- `docs/alignment/daily/YYYY/MM/DD.md` is the append-only receipt aggregation
  track that lets maintainers or future services promote stable coordinates.

Agents maintain the alignment center by:

1. working through one active issue;
2. citing the issue, actor, surface, environment, receipt, and goal coordinate;
3. appending daily alignment receipt movement when shared direction changes;
4. promoting only issue-derived, receipt-backed statements into the index or
   current synthesis;
5. keeping `AGENTS.md` as bootstrap only;
6. updating public-safe source docs and checkout profiles instead of manually
   patching generated public checkout targets.

The long-term service path is: Issue/Goal/FEED/Spec receipts -> Alignment
service synthesis -> public/current alignment views -> aware-dev and external
agent contribution surfaces.

## Files

- `docs/alignment/PROTOCOL.md`: this protocol.
- `docs/alignment/README.md`: global invariant index and alignment-center
  entrypoint.
- `docs/alignment/CURRENT.md`: mutable present-tense topic board for this
  workspace.
- `docs/alignment/PUBLIC.md`: public-safe current alignment surface for the
  `aware-network/aware` facade.
- `docs/alignment/daily/YYYY/MM/DD.md`: append-only alignment receipt
  aggregation for the day.
- `docs/issues/YYYY/MM/DD/issues-YYYY-MM-DD.md`: daily issue input.
- `docs/issues/YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md`: issue evidence.
- `docs/feed/YYYY/MM/DD.md`: scoped movement receipts.
- `docs/goals/LATEST.md`: active product target pointers.
- `AGENTS.md`: bootstrap contract that points agents here.

## Alignment Coordinate

An alignment coordinate is citeable only when it has these fields:

- `issue`: one issue tag and path, or a narrow set of issue refs for a broad
  invariant study.
- `actor`: a stable provider-backed execution id for the active worker.
- `surface`: the protocol, spec, goal, or alignment file being interpreted.
- `environment`: the workspace, revision, deployment, node, service, or API
  boundary affected, when applicable.
- `receipt`: a commit, test, materialization, service response, issue update,
  or FEED line proving the movement.
- `goal`: a goal tag or `TBD` when the work is not yet under a product goal.

If a direction cannot be expressed with these coordinates, keep it as a
question or study finding. Do not elevate it into an invariant.

## Public And Private Evidence Split

The public repo must publish stable doctrine and public contribution rules
without private issue/feed paths that do not exist there.

- Public alignment protocol: stable doctrine, categories, contribution loop,
  and public refs.
- Private alignment evidence: internal issue/feed/goal/conversation refs in
  this development repo.
- Public receipts become citeable only after public issues, proofs, packages, or
  integration receipts are published.

Until public receipts exist, public docs may say:

> Some implementation evidence currently lives in the private development repo
> while the public SDK/API facade is being materialized. Public receipts will be
> added as packages and integration proofs are published.

## Required Loop

1. Publish the active provider-backed execution id.
2. Read `AGENTS.md`, this protocol, `docs/alignment/CURRENT.md`,
   `docs/issues/PROTOCOL.md`, `docs/feed/PROTOCOL.md`, and
   `docs/goals/LATEST.md` before broad alignment work.
3. Map the request to exactly one active issue. If no issue exists, create one
   before editing.
4. For current-direction work, read today's issue index. For invariant work,
   also read the current week's issue headings and the key issue files that
   repeat the direction.
5. Categorize the work using the stable alignment categories below.
6. Execute only through the owning issue scope.
7. Leave receipts in the issue and daily FEED. Use `aware-cli commit` for any
   Git mutation, with `--dry-run` first.
8. Append a short daily alignment entry when the work changes shared
   coordinates.
9. Update `CURRENT.md` only when the invariant is issue-derived, current, and
   useful as a shared citation.

## Promotion Rule

Promote a statement into `docs/alignment/README.md`, `CURRENT.md`, or
`PUBLIC.md` only when at least one is true:

- Luis explicitly locks the direction.
- Multiple issues from the current week rely on the same boundary.
- A closed issue produced a durable proof or protocol surface.
- A live P0 issue needs a cross-agent invariant to prevent drift.
- A public contribution rule must be stable before public code lands.

Every promoted statement must cite issue/protocol/spec/SDK refs. Do not promote
chat-only phrasing without a repo coordinate.

## Stable Categories

These categories are public-safe lenses. Internal current evidence belongs in
`docs/alignment/CURRENT.md` and `docs/alignment/daily/**`.

`coordination-receipts`

- Issues, FEED, goals, alignment, conversations, specs, skills, services, and
  commits are separate surfaces.
- Every meaningful action leaves a receipt.
- `services/issue`, `services/feed`, `services/goal`, and `services/skill` are
  the service/API automation path for these protocols.
- Public refs: `docs/issues/PROTOCOL.md`, `docs/feed/PROTOCOL.md`,
  `docs/goals/PROTOCOL.md`, `docs/specs/PROTOCOL.md`.

`alignment-center-evolution`

- The alignment center is a maintained synthesis/index over receipts, not an
  execution queue.
- Agents contribute by issue-first daily alignment receipts; maintainers or
  future services aggregate durable coordinates into current/public views.
- `AGENTS.md` stays bootstrap-only so generated checkouts do not drift through
  duplicated invariant prose.
- Public refs: `docs/alignment/README.md`, `docs/alignment/PROTOCOL.md`,
  `docs/alignment/PUBLIC.md`, `AGENTS.md`.

`workspace-content-materialization`

- Coordination content such as goals, issues, FEED, and alignment can be
  materialized into shared Workspace files for checkout without becoming code.
- Services remain provider truth; filesystem content is a readable projection
  for agents, humans, and external contributors.
- SDK/local SDK and service routes own writes and refreshes as they mature.
- Public refs: `docs/goals/PROTOCOL.md`, `docs/issues/PROTOCOL.md`,
  `docs/alignment/README.md`.

`public-aware-facade`

- Public Aware starts alignment-first from the SDK/API monorepo facade.
- Public consumers must not require private history, private service internals,
  or private workspace state.
- Public refs: `README.md`, `AGENTS.md`, `docs/alignment/README.md`.

`workspace-revision-deployment`

- WorkspaceRevision remains producer-side committed truth.
- Public/runtime consumers should receive generated deployment artifact DTOs,
  Hub locks, Network first-contact evidence, and Node lifecycle receipts rather
  than WorkspaceRevision internals.
- Public refs: `docs/alignment/README.md`, `docs/specs/PROTOCOL.md`.

`actor-identity`

- Active work uses provider-backed execution ids.
- Product actor history belongs to Identity through Actor, ActorRole,
  ActorCommit, ActorSubscription, and Actor Thread surfaces.
- Public refs: `AGENTS.md`, `docs/issues/PROTOCOL.md`.

`commit-driven-reads`

- Ontology exposes mutation/action contracts, not public read/query functions.
- Services read committed/materialized state or service-owned read models and
  expose view DTOs.
- Environment committed DTO verification is the trust path for proving service
  claims against commit coordinates.
- Public refs: `docs/alignment/README.md`, `docs/specs/PROTOCOL.md`.

`meta-provider-delta`

- Meta remains the FunctionCall/OIG commit authority.
- Provider deltas can patch runtime indexes and API artifacts only after durable
  commit/head-move evidence. Planner and dry-run paths must emit blocked
  receipts instead of mutating hidden state.
- Public refs: `docs/specs/PROTOCOL.md`.

`interface-door`

- Interface is the human door to Aware.
- Interface, panes, and shells consume SDK/API/service view rails. They must not
  reconstruct Workspace, Environment, Node, or service internals.
- Pane/rendering work stays non-guessing and follows declared views.
- Public refs: `README.md`, `docs/alignment/README.md`.

`service-api-sdk-automation`

- Product capabilities move through generated API, service protocol, root
  service, SDK, and skill automation rails.
- Module service shims and direct local shortcuts are migration debt unless a
  current issue explicitly owns them.
- Public refs: `docs/specs/PROTOCOL.md`, `docs/goals/PROTOCOL.md`.

`goal-promise-exec`

- RUN -> GOAL -> EXEC starts with a Workflow Goal promise before Agent/Codex
  execution attempts.
- Agent providers are bounded behind AgentProvider/GoalRunner contracts and use
  generated API/SDK rails.
- Public refs: `docs/goals/PROTOCOL.md`, `docs/issues/PROTOCOL.md`.

`one-wallet-actor-economy`

- Humans and AIs are the same actor shape: Identity -> FinanceEntity -> one
  Wallet. AGENT = IDENTITY = FINANCE ENTITY -> 1 WALLET; AI models act as
  Actors under that Identity.
- Wallet funding is the sole capital ingress; per-action settlement is the
  sole metering; payout/distribution receipts are the sole egress. No
  service, app, or surface ships its own payment path — a side-rail capital
  channel is a trap and a double rail.
- Paid execution requires a wallet-backed `SmartContractPermit` spend
  envelope. An agent's process threads collaborate by allocating capital from
  the shared agent wallet through permits.
- Direction (locked, later implementation): self-funding agents — agents
  register their own Event-Action subscriptions and allocate capital for
  their own runs, moving activation from "human triggers AI" to "AI ensures
  its own allocation" over the same reactive rail.
- Public refs: `docs/goals/PROTOCOL.md`, `docs/alignment/README.md`.

## Daily Alignment Track

Daily alignment entries extract and aggregate receipts into shared coordinate
movement. They are not a second issue system.

Use `docs/alignment/daily/YYYY/MM/DD.md` when an issue, goal, spec, service, or
public proof changes a stable category or current invariant. Each entry should
include:

- UTC timestamp.
- Recorder execution id.
- Category.
- Source receipt refs.
- The coordinate change in one or two bullets.

Maintainers or a future Alignment service aggregate daily entries into
`CURRENT.md`. Future service automation may aggregate from Issue, Goal, FEED,
Spec, commit, and conversation receipts.

## Conflict Rule

If an alignment statement conflicts with an issue, FEED entry, goal, spec, or
implementation proof:

1. Stop widening the invariant.
2. Log the conflict in the owning issue update and daily FEED.
3. Cite both refs.
4. Continue only after the owner or maintainer resolves the coordinate.

## AGENTS.md Rule

`AGENTS.md` is the bootstrap contract. It may summarize identity, issue, FEED,
commit, and alignment requirements, but it must point to this protocol for the
full alignment loop. Do not turn `AGENTS.md` into the weekly invariant ledger.
