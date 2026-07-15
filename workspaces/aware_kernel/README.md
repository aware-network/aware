# Aware Kernel

**Aware turns code changes into canonical graph reality.**
*One shared truth for humans and their AI agents.*

Humans and AI agents already build software together through Git — and Git works
because everyone agrees on one canonical history: a commit head you replay to
rebuild the exact code. That contract stops at the text. Past it, every layer
keeps its own version of what the system is — an ORM bridges database and
runtime, an IDL translates the wire, an API draws a boundary, the database holds
the latest snapshot — each owns a slice, none owns the whole. Noise, drift, and
duplication are the symptom; the missing end-to-end contract is the root.

Aware gives software that contract: an ontology graph. You write semantic source
in `.aware`; Aware translates each text change into ontology-graph mutations and
records them as commits. Like Git, any system replays the commits to reconstruct
state — but the state is structured graph reality, not text. Runtime, database
projections, APIs, services, and interfaces all derive from or fulfill one
canonical model; humans and their agents build on it instead of re-describing it
by hand.

The payoff is immediate: instead of making an ORM, an IDL, an API, and docs each
carry their own version of truth, you write `.aware` — and you and your agents
coordinate over one shared reality, ontology-graph commits, rather than chasing
scattered artifacts.

The public value is not "more generated code." The value is a consumer contract:
source changes become typed operations, graph commits, generated API/SDK
surfaces, and receipts that agents and services can use without importing
kernel internals.

`aware_kernel` is the smallest substrate that makes this possible: Storage,
Content, Code, History, Meta, Ontology, Reactivity, and the API/SDK boundaries
that expose them.

## What this gives you

- **No-reset evolution** — truth is commit lineage, not the latest snapshot, so
  upgrades and migrations are replayable and auditable.
- **Network-native** — systems and peers converge by replaying commits, with no
  shared database.
- **One model, many surfaces** — the same graph drives runtime, storage, APIs,
  and interface projections instead of being re-described in each.
- **API/SDK from truth** — generated API clients, DTOs, service protocols, and
  SDK facades are produced from the same committed model instead of being a
  parallel hand-written contract.
- **Receipts for agents** — consumers can inspect provider-delta readiness,
  generated `CodePackageDelta` output, blockers, and next actions without
  reading Meta runtime internals.

## The consumer boundary: API and SDK

The kernel is useful when a consumer can do something with the graph without
becoming a kernel contributor. That boundary is API/SDK.

```text
consumer / agent / tool
  -> SDK facade
  -> generated API client + DTOs
  -> service API ingress
  -> service operation
  -> Meta / Ontology FunctionCalls and graph commits
  -> typed response + receipt
```

The SDK is the ergonomic caller surface. The generated API client and DTO
packages are the stable wire and operation contract. Services may host those
operations later, but the caller should still see typed requests, typed
responses, and receipts rather than runtime internals.

What ships in this checkout:

- Shared API invocation: [`modules/api/libs/api/python/aware_api`](modules/api/libs/api/python/aware_api).
- API service client/DTO/protocol packages:
  [`modules/api/apis/api/python`](modules/api/apis/api/python).
- Kernel module API packages:
  [`modules/code/apis/code`](modules/code/apis/code),
  [`modules/filesystem/apis/filesystem`](modules/filesystem/apis/filesystem),
  [`modules/meta/apis/meta`](modules/meta/apis/meta),
  [`modules/ontology/apis/ontology`](modules/ontology/apis/ontology),
  [`modules/reactivity/apis/reactivity`](modules/reactivity/apis/reactivity),
  and [`modules/storage/apis/storage`](modules/storage/apis/storage).
- Shared SDK core:
  [`modules/sdk/libs/sdk/python`](modules/sdk/libs/sdk/python).
- Kernel SDK facades:
  [`modules/code/sdks/code/python`](modules/code/sdks/code/python),
  [`modules/filesystem/sdks/filesystem/python`](modules/filesystem/sdks/filesystem/python),
  [`modules/meta/sdks/meta/python`](modules/meta/sdks/meta/python),
  [`modules/ontology/sdks/ontology/python`](modules/ontology/sdks/ontology/python),
  [`modules/reactivity/sdks/reactivity/python`](modules/reactivity/sdks/reactivity/python),
  and [`modules/storage/sdks/storage/python`](modules/storage/sdks/storage/python).

Why this matters:

- Agents can call named operations and receive readiness receipts instead of
  scraping generated files.
- Product services can expose API capability endpoints while keeping ontology
  knowledge behind the service boundary.
- Companies can fulfill actions through API/service operations; they should not
  need to learn OCG/OPG/OIG before participating.
- Generated materialization is a consumable delta and receipt path, not an
  opaque render-all fallback.

## The engine: Meta

Meta is the package that lets Aware describe and change itself. It owns the three
views every graph has — Configuration (what may exist), Projection (the lens you
observe and select through), and Instance (the live state) — and, at runtime,
evolves the Instance as branches advancing through commits.

That branch-and-commit mechanism is the whole codec: **Meta is the graph-commit
protocol — the codec for Configuration / Projection / Instance (OCG / OPG / OIG)
state.** The mechanism in depth lives in Meta's own module README.

## The spine: Code → Graph → Ontology

The kernel is six modules in four moves.

**Substrate — the durable ground the graph rests on.**
- **Storage** — immutable bytes, addressed by their content.
- **Content** — structured, branchable content over those bytes.
- **History** — lineage: how branches and commits are identified and ordered.

**Semantic source — human-readable meaning.**
- **Code** — source that describes graph meaning: code packages and their
  deltas.

**Graph engine — meaning becomes mutation.**
- **Meta** — the Configuration/Projection/Instance engine; evolves the Instance
  as branches via commits.

**Consumer boundary — typed operations and receipts.**
- **API** — generated clients, DTOs, bindings, and service protocols for typed
  operation ingress.
- **SDK** — public facades over generated APIs and DTOs; local where safe,
  service-backed when hosted.

**First modeled semantic world — the protocol, applied.**
- **Ontology** — the self-describing schema catalog that runtime builds and runs
  from.

**Kernel event semantics — reactions over graph commits.**
- **Reactivity** — consumer-agnostic Condition/Event/Action semantics over
  commit-backed graph state. Identity, Attention, Environment, Service, and
  Experience use Reactivity; they do not define the kernel event substrate.

## What the kernel is

`aware_kernel` is that codec proven on its first real targets. The kernel uses
the graph mechanism to model **Ontology** — the self-describing schema layer —
and **Reactivity** — the shared event/reaction substrate over graph commits.
It draws its boundary at the smallest system that can carry semantic source,
hold lineage, evolve self-describing ontologies, expose typed API/SDK contracts,
and react to canonical graph changes without importing network or product
identity semantics.

Everything above this line is the *same mechanism applied to other domains* —
Workspace collaboration, Hub distribution, Network participation, Identity,
Attention, Interface/Pane/Renderer, and managed Node/services. Those layers live
above the kernel and are out of scope for this checkout; they are named here
only to show the kernel is the floor they stand on. API/SDK is different: this
checkout includes the kernel API/SDK contracts because they are how consumers
touch the floor.

## Proof path

Start with the kernel proofs:
[`docs/proofs/proofs.json`](docs/proofs/proofs.json).

The API/SDK value lane is visible in these public proof families:

- `kernel-api-provider-delta-functioncall-public-proof` — API source delta
  becomes provider-delta typed operations and graph FunctionCalls.
- `kernel-api-generated-materialization-delta-required-proof` — API provider
  output becomes guarded generated `CodePackageDelta` output without render-all
  fallback.
- `kernel-api-generated-delta-workspace-sdk-consumer-proof` — Workspace public
  payload and SDK consumer receipt report generated-output readiness, blockers,
  and next action.
- `workspace-sdk-kernel-*` proofs — Workspace SDK drives kernel semantic
  changes through ServiceHost, FunctionCalls, generated deltas, and receipts.

When `aware_home` is checked out beside the kernel, it is the public demo route:
[`../aware_home/docs/proofs/README.md`](../aware_home/docs/proofs/README.md).
Home is the release gate where this stops being an engine story and becomes
product evidence:
source deltas, generated API ingress, strict semantic meaning, no generic
fallback, no source/render/persist mutation during read-only preview, and
receipts a user or agent can inspect.

## Launch posture

Read this repository in four layers:

1. Kernel proves canonical graph truth: `.aware` source -> typed operation ->
   FunctionCall -> OIG commit.
2. API/SDK turns that truth into a consumer contract: typed operation ingress,
   DTOs, SDK calls, and receipts.
3. Aware Home is the consumer release gate: the same contract in a real
   workspace without asking users to touch ontology internals first.
4. aware-dev, Workspace, Hub, and Network are the paid/product surfaces that
   make the same contract collaborative, distributed, and operational.

## Navigate

- Each module tells its link in the spine: `modules/<module>/README.md` —
  Storage, Content, Code, History, Meta, Ontology.
- The engine in depth: `modules/meta/README.md`.
- Public proof index: `docs/proofs/proofs.json`.
- API/SDK entry points: `modules/api`, `modules/sdk`, and each module's
  `apis/` and `sdks/` directories.
- This checkout's boundary and rules: `docs/WORKSPACE.md`.
