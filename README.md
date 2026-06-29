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

`aware_kernel` is the smallest substrate that makes this possible: Storage,
Content, Code, History, Meta, Ontology, and Reactivity.

## What this gives you

- **No-reset evolution** — truth is commit lineage, not the latest snapshot, so
  upgrades and migrations are replayable and auditable.
- **Network-native** — systems and peers converge by replaying commits, with no
  shared database.
- **One model, many surfaces** — the same graph drives runtime, storage, APIs,
  and interface projections instead of being re-described in each.

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
hold lineage, evolve self-describing ontologies, and react to canonical graph
changes without importing network or product identity semantics.

Everything above this line is the *same mechanism applied to other domains* —
network dynamics such as SDK/API/Service, Identity, Attention,
Interface/Pane/Renderer, and Node/services. Those layers live above the kernel
and are out of scope for this checkout; they are named here only to show the
kernel is the floor they stand on.

## Navigate

- Each module tells its link in the spine: `modules/<module>/README.md` —
  Storage, Content, Code, History, Meta, Ontology.
- The engine in depth: `modules/meta/README.md`.
- This checkout's boundary and rules: `docs/WORKSPACE.md`.
