# Protocol — Specs (SPEC / INVARIANTS / PHASES / ITERATIONS / AUDIT)

Goal: keep spec work declarative, execution-safe, and low-noise.

This protocol defines the canonical spec package shape under
`docs/specs/<spec_slug>/`.

## When To Use Specs

Use specs when work:

- spans multiple commits or multiple agents
- has non-trivial invariants (fail-closed rules, migrations, compatibility constraints)
- needs explicit proofs and sign-off per step

If the work is small and can be safely executed as one issue without drift, do not introduce a spec package.

## Where Spec Packages Live (Ownership)

Spec packages must be owned by the code they govern:

- `modules/<module>/docs/specs/<spec_slug>/`
- `libs/<lib>/docs/specs/<spec_slug>/`
- Self-contained workspaces/samples (owned by a workspace root):
  - `<workspace_root>/docs/specs/<spec_slug>/` (example: `modules/**/runtime/samples/**/<workspace>/docs/specs/<spec_slug>/`)

Avoid creating code-owned spec packages under root `docs/**` unless the spec is truly cross-cutting and not owned by a single module/lib.

## Cross-Cutting Module Extraction Rule

When introducing a new canonical module by extracting shared semantics out of an existing module/domain rail, the target module must start spec-first.

Examples:

- extracting generic `Service` semantics out of `economy` into a future `modules/service`
- extracting a cross-cutting substrate out of a domain-owned runtime rail into a new `libs/<lib>` or `modules/<module>`

Rules:

1. Create the target module spec package before moving ontology/code truth.
2. The spec package lives under the target owner, not under the source rail being broken apart.
3. The opening `SPEC.md` must state:
   - what semantics are becoming canonical in the new owner
   - what remains with the source owner
   - compatibility/non-goals during extraction
4. Source and target issues must stay explicit about shared-file overlap and handoff boundaries.

This keeps extractions honest and prevents "new module via ad-hoc file moves" drift.

## Canonical Shape

A spec package is a directory. Inside it:

- `SPEC.md`
  - the root declarative contract
- `invariants/README.md`
  - the invariant index for the spec package
- `invariants/<invariant_order>-<invariant_slug>/README.md`
  - one first-class invariant contract unit
- `PHASES.md`
  - the execution gate ledger
- `phases/<phase_order>-<phase_slug>/README.md`
  - the phase gate artifact
- `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md`
  - the signed autonomous loop artifact
- `audit/README.md`
  - optional spec-local historical audit index
- `audit/<audit_slug>.md`
  - optional audit note anchored on invariant refs

Shared iteration contract:

- `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`

Rules:

1. `SPEC.md` is the only spec-package root entrypoint.
2. Invariant folders are the declarative SSOT for must-hold contract units.
3. Audit belongs under the owning spec package when evidence exists; do not create parallel code-owned `docs/audit/**` trees outside the spec package.
4. Do not add a spec-package root `README.md`.
5. Do not add a spec-local `iterations/PROTOCOL.md`.
6. Do not create flat root `iterations/<iter>/...` for new or migrated canonical specs.
7. Do not invent alternative local invariant layouts.
8. Historical pre-cleanup root `iterations/**` receipts may remain append-only until explicitly migrated; do not create new ones.

## Canonical File Layout (Required)

Every new or declaratively upgraded spec package must contain:

1. `SPEC.md`
2. `invariants/README.md`
3. `invariants/<invariant_order>-<invariant_slug>/README.md` (at least one once the contract is declared)
4. `PHASES.md`
5. `phases/<phase_order>-<phase_slug>/README.md` (at least one once work starts)
6. `phases/<phase_order>-<phase_slug>/iterations/<iter_order>-<YYYY-MM-DD>-<iter_slug>/README.md` (at least one approved iteration once work starts)

Existing legacy specs may migrate incrementally, but when a spec adopts invariants it must use this layout and not invent a parallel variant.

Optional, evidence-driven:

1. `audit/README.md`
2. `audit/<audit_slug>.md`

If audit content exists for a spec, it must live here rather than in a sibling or root-level `docs/audit/` tree.

### Naming Rules (recommended)

- `spec_slug`: kebab-case, stable, and **unversioned**.
  - Do not suffix `-v0` / `-v1`; spec evolution is carried by phases + signed iterations.
- `invariant_order`: numeric and monotonic (`00`, `01`, `02`, ...). Zero-pad.
- `invariant_slug`: kebab-case, stable, and scoped to one must-hold contract unit.
- `phase_order`: numeric and monotonic (`00`, `01`, `02`, ...). Zero-pad to keep lexicographic sorting stable.
- `iter_order`: numeric and monotonic within the phase (`00`, `01`, `02`, ...). Zero-pad.
- `<YYYY-MM-DD>`: UTC capture date.
- `<phase_slug>` / `<iter_slug>`: kebab-case.

## Invariant Folder Contract

- `invariants/README.md` is the spec-local invariant index.
- Each invariant lives in exactly one folder:
  - `invariants/<invariant_order>-<invariant_slug>/README.md`

Rules:

1. The invariant folder `README.md` is the invariant entrypoint and SSOT.
2. `SPEC.md` may summarize direction, but it must not become the only home of first-class invariants once folders exist.
3. Invariant folders may point to docs/code/tests/proofs, but they must not duplicate phase ledgers or iteration history.
4. Add extra files inside an invariant folder only after repeated need proves the shape; keep the first version lean.

## Semantic Model: SPEC vs INVARIANT vs PHASE vs ITERATION vs AUDIT

- **SPEC.md**: the spec-package entrypoint (what is being built, scope, boundaries, architecture, evidence contract).
- **Invariant folder** (`invariants/<...>/README.md`): one declarative must-hold contract unit with proof anchors and phase alignment.
- **PHASES.md**: the execution roadmap, including a phase ledger mapping phases -> iterations -> commit evidence.
- **Phase directory** (`phases/<...>/`): phase-local locks, acceptance, and pointers to its iterations.
- **Iteration artifact** (`phases/<...>/iterations/<...>/README.md`): exactly one autonomous execution loop (scope lock -> implement -> proofs -> exit checks -> sign-off).
- **Audit directory** (`audit/**`): historical observations against invariant refs (`holds`, `drift`, `debt`, `deprecation`); audit is evidence, not declarative truth or execution history.
- **Shared iteration contract** (`docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`): the global loop contract; reference it, do not copy it.

## Phase vs Iteration (Gate vs Loop)

This is the critical semantic split (avoid drift and "phase per iteration" confusion):

- **Phase == gate**:
  - a milestone with explicit acceptance criteria
  - can span days/weeks
  - usually contains multiple iterations
  - should be few and stable (phases are not a daily log)
- **Iteration == loop**:
  - one autonomous execution cycle owned by one agent (via one issue)
  - carries proofs + exit checks + sign-off + commit receipts
  - many iterations per phase is normal

### Default Rule: Iterate, Don’t Phase

Create a **new iteration** when:

- you are still working toward the same phase gate
- the previous iteration is signed-off but the gate is not yet satisfied
- you need to correct/extend prior work (corrections must be a new iteration, not edits to signed artifacts)
- you are handing off to another agent (new owner == new iteration)

Create a **new phase** only when:

- the gate changes (new acceptance criteria/invariants), or
- the prior gate is satisfied and you are starting the next milestone

It is OK for a phase to end up with a single iteration if the gate was completed in one loop. It is not OK to create phases just to create a place to put the next loop.

## Declarative vs Execution Rail

- `SPEC.md` + `invariants/**` is the declarative rail.
- `PHASES.md` + `phases/**/iterations/**` is the execution rail.
- `audit/**` is the historical observation rail.

The orchestrator should be able to target invariant truth without treating phase order as the contract itself.

## Issue / Commit Integration (Administrative Rail)

Issues remain the canonical administrative rail:

- ownership (`Owner`)
- state (`Status`)
- allowed mutation scope (`Ownership Scope`)
- commit evidence (`aware-cli commit`)

For spec-driven work:

1. Every code-change iteration MUST map to exactly one issue file.
2. Spec/phase/iteration `Owner` fields should use the same stable provider-backed execution identity standard as the issue/feed rail: `<provider>-<provider_session_id>`.
3. Future canonical actor ids (`apt_id`, `aware_id`) may be recorded separately, but they do not replace execution identity in spec ownership/sign-off fields.
4. Issue SHOULD include pointers:
   - `Spec: <path/to/spec-package/SPEC.md>`
   - `Invariant: <path/to/spec-package/invariants/<...>/README.md>` (repeat as needed)
   - `Audit: <path/to/spec-package/audit/<...>.md>` (for audit-driven work)
   - `Phase: <path/to/spec-package/phases/<...>/README.md>` (optional but recommended)
   - `Iteration: <path/to/spec-package/phases/<...>/iterations/<...>/README.md>`
5. Issue `Ownership Scope` MUST include:
   - the iteration artifact README
   - any spec docs changed (`SPEC.md`, `PHASES.md`, phase README)
   - shared protocol/template docs when this lane changes them
   - the exact code paths being mutated
6. Commit evidence MUST be recorded in three places:
   - issue `Updates`
   - iteration artifact `Sign-Off`
   - `PHASES.md` phase ledger (phase -> iteration -> commit hash)

Issues are SSOT for "who did what/when/what changed". The spec package is SSOT for "what we are building and how we prove it".

## FEED + GOALS Linking (Coordination Rail)

- Goals (`docs/goals/**`) may link to spec packages as execution plans for product targets.
- FEED (`docs/feed/YYYY/MM/DD.md`) records:
  - claim (issue + iteration pointer)
  - commit (issue tag + commit hash)
  - resolved (issue closed)

## Update Rules (No Drift)

- `phases/**/iterations/**` is append-only evidence:
  - do not rewrite iteration artifacts after sign-off
  - open a new iteration folder for the next loop
- `invariants/**` is declarative contract:
  - keep invariant folder slugs stable
  - update the invariant when the contract changes
  - if an invariant is retired, mark it explicitly rather than silently deleting contract history
- `PHASES.md` is the roadmap ledger:
  - may evolve, but must keep phase->iteration->commit evidence honest
- `audit/**` is the historical observation ledger:
  - anchor findings on invariant refs
  - prefer additive note growth or new audit notes over free-floating rewrites
  - audit findings must link issues/spec work when action is required
- `SPEC.md` may evolve:
  - must remain fail-closed and explicit
  - avoid speculative claims; label "planned" sections clearly
- `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md` is global:
  - update it once
  - do not materialize spec-local copies

## Templates

Use these templates when creating new spec packages:

- `docs/specs/TEMPLATE_SPEC.md`
- `docs/specs/TEMPLATE_INVARIANT.md`
- `docs/specs/TEMPLATE_PHASES.md`
- `docs/specs/TEMPLATE_PHASE.md`
- `docs/specs/TEMPLATE_ITERATION.md`

Shared iteration contract:

- `docs/specs/TEMPLATE_ITERATIONS_PROTOCOL.md`

## Example (Reference Implementation)

Workspace spec package (phase-owned iteration layout):

- `modules/structure/docs/specs/workspace/SPEC.md`
- `modules/structure/docs/specs/workspace/invariants/README.md`
- `modules/structure/docs/specs/workspace/invariants/00-module-first-topology/README.md`
- `modules/structure/docs/specs/workspace/PHASES.md`
- `modules/structure/docs/specs/workspace/phases/00-spec-gate/README.md`
- `modules/structure/docs/specs/workspace/phases/00-spec-gate/iterations/00-2026-03-15-workspace-spec-bootstrap/README.md`

Runtime error spec package (spec-local audit layout):

- `libs/runtime/docs/specs/error/SPEC.md`
- `libs/runtime/docs/specs/error/invariants/README.md`
- `libs/runtime/docs/specs/error/PHASES.md`
- `libs/runtime/docs/specs/error/audit/README.md`
