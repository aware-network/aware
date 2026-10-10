# Aware

**One reality that humans and their AI agents evolve together.**
*A shared map. Sovereign territories. Receipts for every step.*

Aware is a place before it is a technology: humans and AI agents inhabiting the
same world model — seeing the same state, acting under the same contracts,
remembered by the same history.

The mechanism that makes this possible is a **semantic codec for information
distribution**: a meta-configuration we all share to decode evolution through
graph structures. Git proved the pattern for text — one canonical history, replay the commits, everyone rebuilds
the same code. Aware extends that contract past the text, to the *things the
text means*:

```text
Git    replays  commits   over  files       ->  the same code
Aware  replays  commits   over  objects     ->  the same reality
```

You share one **map** (`ObjectConfigGraph` — classes, attributes, relationships,
functions). You claim a **membership** of it (`ObjectProjectionGraph` — the
slice a territory cares about). You evolve a **territory**
(`ObjectInstanceGraph` branches) by committing typed mutations. Anyone holding
the map and the commits replays them and arrives at the *same branch state* —
attribute by attribute, relationship by relationship. No globally privileged
database is required for canonical truth — nodes keep their own persistence and
projections, but truth derives from replayable graph lineage, never from access
to one authoritative store. And no re-describing the world in an ORM, an IDL,
an API schema, and docs that each drift apart. That replay contract is the decentralization
base, and everything else in this repository is built on it.

Four layers make this concrete:

| Layer | Object | Role |
| --- | --- | --- |
| Map | `ObjectConfigGraph` (OCG) | the shared configuration — knowledge as object classes **with functional behavior** |
| Membership | `ObjectProjectionGraph` (OPG) | which part of the map a territory projects |
| Territory | `ObjectInstanceGraph` (OIG) branches | lived state, evolved only by commits |
| Evolution | commits + replay | typed mutations anyone can replay to the same state |

## One public repository, two workspaces

The repo declares its workspaces in [`aware.repo.toml`](aware.repo.toml): each
workspace is a semantic territory with its own packages, materialization, and
receipts.

| Workspace | What it is |
| --- | --- |
| [`aware_kernel`](workspaces/aware_kernel) | the reactive graph OS — the shared infrastructure everything else runs on: Storage, Content, Code, History, Meta, Ontology, Reactivity, API/SDK |
| [`aware_network`](workspaces/aware_network) | the inhabited world: Identity, Experience, Attention, Services, Economy, Interface, Node |

The public checkout is an immutable `RepositoryRevision` projection that pins
one exact `WorkspaceRevision` for Kernel and one for Network. Producer
development repositories may aggregate additional Workspaces, but those are not
members of this public repository revision. Git is only the publication adapter
over that repository-level receipt.

## The kernel: a reactive graph OS

The kernel is the shared infrastructure the network builds on. It holds the
world model and keeps it **pure — no world side-effects**:

From the outside in — the door, the contract, the knowledge, the life:

- **SDK** — the door: consumer ergonomics over the API. Typed clients in your
  language that can keep a local working view of your state and sync it
  through contract calls — you build against a library, not a platform.
- **API** — the operational contract *over* the ontology: capabilities,
  endpoints, typed request/response/stream schemas, and readable `ApiView`
  state. The ontology is the coordinates everyone shares; the API is what you
  may *do and see* at those coordinates.
- **Ontology** — the base of knowledge: object configuration with functional
  behavior. Mutations happen only through canonical `Object.function` calls
  that emit graph commits. State is lineage, never a snapshot.
- **Reactivity** — semantic events: policies evaluated over graph commits.
  Events are not messages someone sent; they are *meaning derived from what
  actually changed*, and they carry the action lifecycle
  (`intent -> attempts -> receipts`) that routes every reaction through an API
  contract.

Read the kernel story: [`workspaces/aware_kernel/README.md`](workspaces/aware_kernel/README.md).

## The network: the inhabited world

The network turns the graph OS into a place:

1. **Identity** — humans and AI agents are the *same actor shape*: an Identity
   with roles, sessions, subscriptions, and history. Both act; both are
   attributable.
2. **Experience & Attention** — Experience binds graph truth to meaning
   (*graph bindings*: "front_door" names a worldline; scenarios declare what
   they watch and what they act on). Attention makes looking shareable:
   layouts, sections, and focus over one graph state — humans and agents
   literally attending the same thing.
3. **Services** — the fulfillment layer. Services fulfill API contracts: ontology
   services coordinate over the graph; world services perform real
   side-effects behind typed endpoints, returning stream receipts — companies
   participate at *actions*, never needing ontology internals.
4. **Economy** — the value layer. Identities evolve into Finance Entities with
   Wallets. Wallet funding is the sole capital ingress; services declare
   pricing on their contracts; every priced action settles through Economy;
   distribution flows back by receipt. Money is compiled the way ontology is
   compiled — as graph truth.
5. **Nodes & Interfaces** — workspace revisions deploy to nodes that run the
   services; interfaces render declared views (`ApiView -> Experience ->
   panes/screens`) so what you see is a projection of committed truth, never a
   reconstruction of it.

That is the closed loop: a **Semantic Network** — declaratively evolved,
contract-fulfilled, receipt-settled, shared by humans and AI as equals.

## The arrow to remember

```text
SDK -> API -> Service -> Ontology            (the door, inward)
Experience ->  graph bindings                (meaning, sideways)
commits -> events -> actions -> receipts     (life, forward)
```

Every meaningful action leaves a receipt: who acted, through which contract,
with what feedback, visible where. Every priced action settles through Economy.
Trust here is not assumed or moderated — it is constructed.

## Enter

- **Read** — the kernel promise: [`workspaces/aware_kernel/README.md`](workspaces/aware_kernel/README.md)
- **Explore the inhabited network** — start at
  [`workspaces/aware_network`](workspaces/aware_network).
- **Agents working this repo** — start at [`AGENTS.md`](AGENTS.md)
  (identity, issue-first, no raw git), then
  [`docs/issues/PROTOCOL.md`](docs/issues/PROTOCOL.md) and
  [`docs/alignment/PROTOCOL.md`](docs/alignment/PROTOCOL.md).

```bash
uv sync
```

## Canonical invariants

- `.aware` is SSOT. Generated artifacts are produced only by Workspace
  materialization — never hand-edited.
- The ontology plane is platonic: no world side-effects. Side-effects cross
  only through typed API contracts with stream receipts.
- One capital ingress, one metering (priced-action settlement), one egress
  (payout receipts). No side-rail payment paths.
- Coordination is issue-first (`docs/issues/**` is SSOT); every meaningful
  action leaves a receipt.

---

*Aware 4 Humanity.*
