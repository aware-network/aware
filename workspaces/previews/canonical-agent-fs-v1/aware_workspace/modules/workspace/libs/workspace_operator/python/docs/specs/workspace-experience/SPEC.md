# Workspace Operator — SPEC

Status: in progress
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`

## Goal

Define `workspace-operator` as the canonical owner of workspace profiles, seed/layout materialization, workspace-root descriptor evolution, and the later canonical workspace operator layer, while keeping Structure workspace service as the separate owner of workspace topology plus operator-facing setup/compile/test/diagnostic orchestration.

## Canonical Direction

Non-negotiable invariants:

- `workspace-operator` owns workspace profile and shape policy, including FS-first seed/layout and the later move toward canonical workspace `.aware` experiences.
- `workspace-operator` owns full workspace filesystem evolution for workspace-authoritative surfaces, including follow-on root descriptor mutation after module/package creation.
- Structure workspace service remains the owner of normalized workspace topology, operator-facing setup/compile/test/diagnostic features, and workspace-owned receipts/status.
- The dependency arrow is provider-style, not package-coupled:
  `workspace-operator` emits stable artifacts/contracts that Structure workspace service consumes;
  Structure must not import `aware_workspace_operator` internals as its semantic source of truth.
- `aware-cli workspace bootstrap` is compatibility transport today, but the canonical target is thin transport over Workspace service; CLI parsing is not the owner of workspace seed semantics.
- `aware-cli module create` must also stay thin transport. The full module-create transaction is workspace-owned even when lower-level scaffold work is delegated downward.
- FS-first workspace scaffold is Phase 01, not the final destination. The long-term owner surface includes canonical workspace `.aware` experience rails under the workspace root.
- Workspace seed/layout must stay explicit and profile-driven. No phase in this spec may "guess" starter modules or silently invent workspace roots outside the declared profile contract.
- Package-first code ownership is the lower rail. `CodePackage` is the raw code/package truth, while `CodeModule` is a semantic bundle of package surfaces. Workspace-experience must therefore consume package-oriented scaffold outputs when evolving workspace-root descriptors.

## Current Truth (Repo State)

What exists today:

- `libs/workspace-operator/aware_workspace_operator/pipeline/` already owns real workspace bootstrap orchestration, report assembly, and scaffold writing.
- `libs/workspace-operator/aware_workspace_operator/models.py` already defines typed bootstrap/quality/commit request and outcome models.
- `libs/workspace-operator/aware_workspace_operator/assets/` already carries grammar docs, seed bundles, and software/rules content that are experience-owned rather than Structure workspace-service-owned.
- `libs/workspace-operator/aware_workspace_operator/bridge/` already defines remote/operator adapters over external services.
- `environments/robotics/workspace/` now exists as a real CLI-bootstrapped workspace root with `aware.environment.toml`, `pyproject.toml`, manifests, and contracts.
- `modules/structure/docs/specs/workspace/` already locks Structure workspace service as the KING owner for module-first topology and workspace service rails.
- `tools/cli/aware_cli/commands/workspace.py` still routes bootstrap directly into `workspace-operator`, so the single-boundary `CLI -> Workspace service` direction is not implemented yet.
- `tools/cli/aware_cli/commands/module.py` still routes `module create` into an env-artifacts compatibility shim that re-exports the grammar-owned scaffold helper, so there is no canonical workspace-owned descriptor evolution step after module creation.
- `aware_code.module_manifest.scaffold` owns the lower-level module-local scaffold rails, including module runtime and service package `pyproject.toml` generation.
- `aware_code.module_manifest.scaffold` is the correct lower rail for module-local/package-local scaffold semantics, but its output is not yet rich enough to serve as the canonical workspace root evolution contract.
- The workspace root `pyproject.toml` written by `workspace-operator` is still bootstrap-owned static text; it does not yet evolve from typed package registration truth.

What is not locked yet:

- The dedicated `workspace-operator` spec package exists, but its implementation phases are not yet fully aligned to the latest Workspace-service setup-boundary direction.
- Existing `libs/workspace-operator/docs/*.md` text still overstates the package as the owner of "workspace compilation rails".
- The operator-facing setup boundary is not yet frozen as `CLI -> Workspace service -> workspace-operator backend`.
- The canonical workspace root placeholder contract for `modules/`, `apis/`, `services/`, `experiences/`, and future profiles is not frozen.
- There is no explicit machine-readable provider contract stating what Structure workspace service is allowed to consume from workspace-operator outputs.
- Canonical workspace `.aware` experience ownership is still only directional and not yet phase-locked.
- The canonical module-create orchestration boundary is not yet frozen.
- There is no structured package registration contract between grammar-owned module scaffold and workspace-owned root descriptor evolution.
- The package-first direction from `docs/conversations/2026-03-17-CODE-OWNER-2.md` is not yet fully reflected in the workspace-operator implementation contract for module evolution.

## Scope

In scope:

- owner boundary for workspace profiles and seed/layout materialization
- FS-first workspace scaffold direction
- canonical workspace root placeholder and profile contract direction
- module-create orchestration boundary and workspace-owned root descriptor evolution
- service-consumption boundary between workspace-operator and Structure workspace service
- later evolution toward canonical workspace `.aware` experiences

Out of scope:

- Structure workspace-service implementation details
- compile/test/diagnostic backend semantics
- module scaffold semantics owned by grammar or env-artifacts
- remote transport or DTO freeze for Structure workspace service
- specific robotics workspace implementation beyond its use as a proof target for owner direction

## Integration Contract

Where this plugs into the system:

- `libs/workspace-operator/aware_workspace_operator/bootstrap.py` is the compatibility facade for workspace-operator entrypoints.
- `libs/workspace-operator/aware_workspace_operator/pipeline/` owns profile-driven planning, scaffold writing, and report generation for workspace seed/layout.
- `libs/workspace-operator/aware_workspace_operator/assets/` owns experience-side bundles such as grammar docs, software/rules content, and seed assets.
- `modules/structure/runtime/aware_structure/workspace/features/` owns the service-side workspace capabilities after workspace roots exist.
- `modules/structure/docs/specs/workspace/` is the separate Structure-owned spec package for topology plus setup/compile/test/diagnostic orchestration.

Boundary rules:

1. `workspace-operator` may emit workspace root files, manifests, contracts, placeholder directories, and later `.aware` experience assets.
2. Structure workspace service may consume those emitted artifacts/contracts and later invoke `workspace-operator` through a backend/provider seam for setup, but it must not take semantic ownership of how workspace-operator profiles or seeds them.
3. Experience-owned bundles such as operator guidance, grammar docs, rules bundles, and later `.aware` workspace operators stay on this side of the boundary even when Structure consumes adjacent workspace topology contracts.
4. Setup is exposed to operators through Workspace service even when backend FS evolution semantics remain in `workspace-operator`.
5. Compile/test/diagnostic planning and execution stay Structure-owned even when workspace-operator initiates or wraps those flows.
6. `aware-cli` is transport only. Canonical workspace feature orchestration should converge on Workspace service, while business logic for workspace FS evolution and experience bundles remains in `workspace-operator`.
7. `aware-grammar` owns lower-level module-local scaffold semantics, not workspace-root descriptor mutation.

## Canonical Owner Surfaces

The owner surfaces under this spec are:

- workspace profiles and profile identifiers
- workspace seed/layout planning
- workspace root placeholder policy
- experience-side asset bundles and seed bundles
- bootstrap reporting that explains what was materialized at the workspace root
- workspace-root descriptor adapters such as `pyproject.toml` and later additive root descriptors
- workspace-owned application of package registration truth after module evolution
- the long-term transition from FS-first workspace layout into canonical `.aware` workspace operators

The following are adjacent but not owned here:

- Structure workspace topology resolution
- Structure setup/compile/test/diagnostic features
- env-artifacts compile/materialization internals
- grammar-owned module/environment source contracts
- CLI argument parsing and terminal transport

## Module Bootstrap And Root Descriptor Evolution

The canonical module-create flow is:

- `aware-cli` parses the request and calls one typed Workspace service entrypoint.
- Workspace service owns the operator-facing workspace setup/module-evolution transaction boundary.
- Workspace service invokes the `workspace-operator` backend for the full workspace FS evolution transaction.
- `workspace-operator` invokes the grammar-owned module scaffold engine.
- `aware-grammar` performs the lower-level module-local and package-local scaffold writes and returns structured package registration output.
- `workspace-operator` consumes that structured output and mutates workspace-root descriptors deterministically.

Contract rules:

- `aware-cli` must not orchestrate grammar writes plus root-descriptor writes itself or bypass Workspace service for canonical workspace features.
- Workspace service owns operator-facing setup orchestration, but it must delegate backend filesystem/profile semantics to `workspace-operator`.
- Grammar scaffold helpers must not mutate workspace-root descriptors such as the root `pyproject.toml`.
- Workspace-root descriptor evolution is workspace-operator-owned.
- Workspace-root descriptor evolution must be driven by package truth, not module-path heuristics.
- The first required root descriptor adapter is `pyproject.toml`; later root descriptors may be added additively.
- Root descriptor mutation must be non-manual and derived from structured scaffold output, not from scraping `planned_paths` or guessing package layout.

### Structured package registration contract

Grammar-owned scaffold output must be rich enough for workspace-operator to evolve root descriptors honestly.

The contract must support package-oriented registration, not only module-oriented registration, because package-first semantics are the canonical lower rail:

- `CodePackage` is the only raw code owner.
- `CodeModule` is a semantic bundle of packages.
- Module bootstrap may therefore expose multiple package registrations inside one module evolution operation.
- Workspace-experience must treat module creation as one workspace transaction that applies all emitted package registrations atomically at the workspace root.

At minimum, the structured package registration surface must preserve:

- package-relative path
- package kind/surface
- language/runtime manager
- distribution/project name when applicable
- import root when applicable
- owner module id

Contract rules:

- Grammar may speak in package terms inside one module because packages are the installable/materializable lower rail.
- Workspace-experience is responsible for translating those package registrations into workspace-root descriptor mutations.
- Structure workspace service later consumes the resulting workspace artifacts/contracts; it does not become the owner of how module-local package truth updates workspace-root descriptors.

### Root descriptor adapters

Workspace-experience owns root descriptor adapters that consume structured package registrations.

Rules:

- `pyproject.toml` is the first required adapter.
- Later adapters, such as other language ecosystem root descriptors like `pubspec.yaml`, are additive and stay under workspace-operator ownership.
- Descriptor adapters must be deterministic and idempotent.
- Manual edits are not the canonical evolution rail for generated workspace descriptor entries.

## Canonical FS-First Root Contract

Phase 01 freezes the first honest workspace-operator root layout into three tiers:

### Tier 1 — mandatory root metadata

These files/directories are required for an honest bootstrapped workspace root:

- `aware.environment.toml`
- `pyproject.toml`
- revision-bound test inventory and receipts owned by Code and Workspace
- `configs/contracts/`
- `.github/workflows/`

This tier establishes a workspace root as a real Aware-controlled surface, even before any module/API/service/experience content exists.

### Tier 2 — canonical placeholder roots

The first-class placeholder roots are:

- `modules/`
- `apis/`
- `services/`
- `experiences/`

Contract rules:

- These roots are part of the workspace layout contract, not optional content bundles.
- They prepare the workspace for later explicit authoring; bootstrap must not guess starter contents under them.
- Placeholder ownership docs inside these roots are part of the intended Phase 01 implementation surface, but the directories themselves are the contract truth.

### Tier 3 — optional experience bundles

These surfaces are optional bundles layered over the root contract:

- `AGENTS.md` and `skills/`
- `docs/feed/**` and `docs/issues/**`
- `docs/aware/grammar/**`
- `docs/rules/SOFTWARE/**`
- `configs/seeds/**`

Contract rules:

- Optional bundles are experience-side assists, not the definition of the workspace root shape.
- A workspace may intentionally skip these bundles and still satisfy the FS-first root contract.

### Later Layers

- `profiles/` is not a mandatory Phase 01 root.
- Profile semantics are frozen later in Phase 02 as contract truth, and may later materialize explicit profile-owned surfaces if the contract requires them.
- Canonical workspace `.aware` experience surfaces are Phase 04 work and must remain additive over the FS-first root contract rather than replacing it.

## Data / Identity / Mutation Rules

Fail-closed rules:

- Workspace seed/layout must come from an explicit profile or declared default profile, never from ad-hoc filesystem heuristics.
- Workspace roots and placeholder surfaces must be explicit outputs of the profile contract. If a root such as `modules/`, `apis/`, `services/`, `experiences/`, or future profiles is materialized, the profile must declare it.
- Phase 01 freeze names `modules/`, `apis/`, `services/`, and `experiences/` as the mandatory placeholder roots. Additional roots such as `profiles/` require a later explicit contract freeze.
- `aware-cli` must not own workspace FS evolution semantics beyond transport.
- Canonical workspace feature entrypoints must not bypass Workspace service once the setup service seam is frozen.
- Module-create follow-on mutations to workspace-root descriptors must go through workspace-operator, not directly through CLI or grammar helpers.
- Grammar scaffold output must be structured enough for root descriptor adapters; scraping created paths is not an honest long-term contract.
- Root descriptor mutation must be package-oriented where package truth exists.
- Module create is a workspace-owned filesystem evolution transaction over package truth, not a CLI-owned sequence of ad-hoc file edits.
- `workspace-operator` must never claim ownership of setup orchestration or compile/test/diagnostic orchestration semantics that are already owned by Structure workspace service.
- Structure workspace service must not rely on importing `aware_workspace_operator` internals as a runtime dependency for canonical workspace semantics; the interop surface is emitted artifacts/contracts only.
- Bootstrap must not guess starter modules, starter APIs, or starter services. Those are explicit follow-on actions.
- Future canonical workspace `.aware` experience rails must remain additive over the workspace root, not a second competing owner of topology/service truth.

## Evidence And Testing Contract

Required proofs for implementation iterations:

- Unit and integration tests:
  - `uv run pytest -q libs/workspace-operator/tests`
- Static checks:
  - `uv run flake8 libs/workspace-operator/aware_workspace_operator libs/workspace-operator/tests`
  - `uv run mypy --follow-imports=silent libs/workspace-operator/aware_workspace_operator libs/workspace-operator/tests`
  - `uv run basedpyright --level warning libs/workspace-operator/aware_workspace_operator libs/workspace-operator/tests`
- Workspace shape proofs are phase-specific and must be declared in the relevant iteration artifacts.

## Work Governance

- Phases ledger: `PHASES.md`
- Shared iteration contract: `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`
- Phase directories: `phases/<phase_order>-<phase_slug>/README.md`
- Active iteration artifacts: `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md`
