# Current Alignment - Public

- Status: Current public coordination snapshot
- Last updated: 2026-07-10

Aware is alignment-first. Work starts by sharing semantic coordinates before
execution.

Alignment is not planning. Alignment is the shared semantic coordinate system
that lets humans, agents, services, interfaces, and workspaces act without
drifting.

The public product surface is being consolidated around one external entry:
`aware-sdk` and Interface-facing SDK/API contracts. Developer and agent
workflows use that same direction through `aware-dev` and local-first SDK
adapters, then route to service-backed execution as canonical services become
available.

Some implementation evidence still lives in the private development repo while
public packages and integration proofs are materialized. Public receipts are
added when a protocol, SDK, API, or service boundary is ready to be cited
without private issue/feed context.

## Public Invariants

- Aware is a protocol-driven network.
- Before execution, actors align on semantic coordinates.
- Issues, goals, specs, skills, services, SDKs, and commits move the system
  after alignment.
- Every meaningful action must eventually leave a receipt.
- Public docs cite public protocol, SDK, API, and service surfaces first.
  Private issue/feed paths are not public evidence.
- Local-first behavior must use the same API-shaped DTOs and SDK boundaries
  that remote services will use later.

## Alignment Center

The public alignment center is the stable entrypoint for contributors and
agents:

- `AGENTS.md` bootstraps identity, issue, FEED, commit, and alignment rules.
- `docs/alignment/README.md` indexes durable invariants.
- `docs/alignment/CURRENT.md` is the public-safe current synthesis.
- Protocol docs define how issues, FEED, goals, specs, skills, services, SDKs,
  and commits leave receipts.

Contributors should not fork current direction into local instruction files.
They should use the alignment center, then move work through issue/service/SDK
receipts. As public packages mature, `aware-dev` should route agent and human
contribution through service-backed SDK/API boundaries rather than direct
workspace internals.

## Current Direction

`aware-sdk-entry`

- `aware-sdk` is the public entrypoint for external usage and Interface-facing
  control. Its canonical source is Interface-owned and depends on
  `interface-sdk`; Flutter and other renderers use that same shared SDK rail.
- AX=UX means shared semantic app, session, attention, action, and receipt
  coordinates while presentation may vary by renderer and actor lens.
- Interface panes consume SDK/API/service view rails and do not reconstruct
  service internals.

`aware-dev-contribution`

- `aware-dev` is the developer and agent contribution rail over Workspace,
  Code, FileSystem, and local status.
- Local repository observation belongs behind SDK/API-shaped contracts so the
  same workflows can later route through services without changing callers.

`workspace-revision-deployment`

- WorkspaceRevision is producer-side committed artifact truth.
- Runtime consumers should receive generated deployment artifacts, publication
  locks, topology evidence, and lifecycle receipts.
- Workspace deployment validation remains the active proving lane for clean
  node/service boot and revision-root execution.

`api-owned-dtos`

- Service APIs own DTO contracts at the public boundary.
- SDKs consume API-owned DTOs and service protocols instead of importing module
  ontology/runtime internals.
- Local-first SDK adapters are allowed when they preserve the API boundary and
  can be replaced by service routing later.

`agent-execution`

- Agents are actors with stable provider-backed execution identities today.
- Agent product evolution belongs in its own execution workspace, not inside
  Coordination.
- Agent SDK work should provide actor/session/process-thread ergonomics while
  staying compatible with Identity, Goal, Reactivity, and future Agent service
  routes.

`coordination-aggregation`

- Coordination is the receipt aggregation, alignment, prioritization, and
  handoff layer.
- Coordination must not become the source authority for Agent, Workspace,
  Code, FileSystem, Identity, or service-specific DTO truth.
- The near-term coordination product is clean issue/feed/alignment aggregation
  over committed filesystem evidence.

`workspace-content-materialization`

- Shared checkout should eventually include coordination content that agents
  need to align, starting with selected active Goal content.
- Goal, Issue, Feed, and Alignment services remain the provider truth. Files in
  the workspace are readable projections for shared participation, not separate
  authorities.
- Goal content is not code and should not be treated as a CodePackage.

## Durable Categories

`actor-identity`

- Humans, agents, services, interfaces, and process threads act as actors with
  explicit roles.
- Active automated work uses stable provider-backed execution identities.

`interface-door`

- Interface is the human door to Aware.
- Interface experiences consume SDK/API/service contracts and present actor
  admission, control, and feedback without private repo coupling.

`service-api-sdk-automation`

- Capabilities move through generated APIs, service protocols, root services,
  SDKs, and skills.
- Protocols become executable through skills and service surfaces.

`commit-driven-reads`

- Ontology exposes action/mutation contracts, not a second public query model.
- Services expose view DTOs from committed/materialized state or service-owned
  read models.

`goal-promise-exec`

- RUN -> GOAL -> EXEC starts from a goal promise before agent execution.
- Execution attempts should return or emit receipts.

`public-aware-facade`

- Public Aware starts from the SDK/API facade under the alignment contract.
- The public facade must not require private history, private runtime state, or
  private service internals.

`coordination-receipts`

- Issues, FEED, goals, specs, alignment, skills, services, SDKs, and commits
  are distinct coordination surfaces.
- Receipts are the provenance layer for humans, agents, services, workspaces,
  and UI panes.

## Public Refs

- `AGENTS.md`
- `docs/alignment/PROTOCOL.md`
- `docs/alignment/README.md`
- `docs/issues/PROTOCOL.md`
- `docs/feed/PROTOCOL.md`
- `docs/goals/PROTOCOL.md`
- `docs/specs/PROTOCOL.md`
- `workspaces/aware_network/modules/interface/sdks/aware/README.md`
- `workspaces/aware_network/modules/interface/sdks/interface/aware/interface_sdk.aware`
