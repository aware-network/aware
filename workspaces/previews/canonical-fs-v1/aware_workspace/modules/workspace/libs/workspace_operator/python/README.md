# aware-workspace-operator

Canonical bootstrap/operator wrapper for workspace setup and delivery-contract scaffolding.

Version 0.4 consumes the neutral Issue operational runtime 0.3 source-scope
policy. Publication retains its existing owner/status/path diagnostics, parser,
source-digest checks and Git effect boundary. The policy is not a write permit;
Protocol setup admission and source effects remain separate. Dependency bounds
and authored local sources are declared; installed/lock qualification is not
implied by source adoption.

## Boundary

- Owns opinionated workspace setup behavior (empty-root bootstrap, contracts, docs, manifests, CI rails).
- Owns bootstrap reporting (`status`, `next_required_actions`) for human-agent flows.
- Does not own canonical workspace environment experience policy (delegated to product-owned `experiences/aware-workspace` on top of core Experience contracts).
- Does not own compile/materialization semantics (delegated to Workspace materialize / Meta-owned runtime artifact rails).
- Does not own module scaffold semantics (delegated to grammar-owned module scaffold helpers and Workspace-owned package-manager projection).

## Day-1 Ownership and Deterministic Automation

- Human-owned:
  - `aware-cli workspace bootstrap` (explicit workspace initialization and operator policy entrypoint).
- AI-owned deterministic rails:
  - `aware-cli module create --repo-root <repo_root> --module-id <module_id>`
  - `aware-cli compile module <module_id>`
  - `aware-cli workspace quality-gates --path <target>`
  - module proof / pane registrar / IPC validation when present
- Required gate order:
  1. module create
  2. compile (must pass)
  3. quality gates
  4. module proof and runtime checks
- `configs/seeds/**/*` and seed secret provisioning are explicitly day-1 excluded.
- All Workspace Operator entrypoints require an explicit `--repo-root` or an
  explicit repo-root environment variable; they do not discover a checkout root.

## Design Intent

- Keep `aware-cli` as a thin command transport.
- Keep module creation explicit (no guessed starter modules).
- Keep bootstrap profile explicit: `remote-managed` by default, `full-local` as opt-in strict mode.
- Support a two-loop contract: Workspace Config Loop first, Workspace Instantiation Loop second.
- Provide one canonical quality gate command (`aware-cli workspace quality-gates`) so agents do not guess lint/type tooling.
- Bundle grammar docs into each bootstrapped workspace so agents can author `.aware`
  without monorepo source access.
- Bundle software rules into each bootstrapped workspace by composing the
  revision-owned package template + profile contracts into `docs/rules/SOFTWARE/*`.
- Bundle seed artifacts into bootstrapped workspace under `configs/seeds/*` only when
  the automation phase is set to `phase-2`.
- Lock module standard rails for generated workspaces:
  - `structure/` (ontology + module API contracts)
  - `runtime/` (core semantics only)
  - `services/` (app-surface adapters)
  - `providers/` (external connectors)
  - `representation/`, `experience/`, `docs/`
- Keep API profile authoring explicit (`api projection` / `*.apis.aware`) as contract rails separate from service/provider implementation.

## Program/Profile Contract (Next Canonical Rail)

Workspace automation must stay orchestration-only and reusable across tenants.

1. Module responsibility:
- Each module owns its deterministic program assets in `modules/<module>/programs/**/*.aware`.
- Each module declares exported refs and symbol contract in `modules/<module>/programs/aware.programs.toml`.
- Stable ids stay module-canonical (no workspace-level ad-hoc id derivation).
- Modules own service/provider rails under module scope; workspace bootstrap must not centralize service ownership in app wrappers.

2. Operator/workspace responsibility:
- Operator rollup source lives in revision-owned package `aware_workspace_operator/assets/seeds/`; bootstrap materializes it to external workspace `configs/seeds/` only for phase 2.
- Seed/rollup programs compose module refs via `plan.apply_program_ref(...)`; they do not duplicate module business logic.
- Workspace profile inputs provide symbol values (for example org/agent/service selections) without changing program source.

3. Composition responsibility (Workspace materialize / Meta runtime):
- Resolve `aware.programs.toml` contracts into Workspace-owned materialization receipts and Meta-owned runtime artifact sets.
- Validate ref uniqueness, dependency closure, and symbol declarations at materialization time.
- Emit deterministic registry metadata consumed by runtime/execution tooling.

4. Runtime responsibility:
- Execute program refs from manifest `program_registry` (fail closed when registry-required policy is enabled).
- Enforce `required_symbols` before execution (top-level and nested program refs).
- Convert program steps to canonical FunctionCall invocations and commit outcomes.

This separation keeps bootstrap flows reproducible while allowing profile-level customization for non-Aware deployments (for example different organization/agent presets) through symbolized composition, not Python/TOML/markdown reimplementation drift.

Future direction:

- `libs/workspace-operator` remains the bootstrap/operator layer.
- Product-owned Workspace experience policy should converge under `experiences/aware-workspace/`.
- Core process/thread/projection primitives remain owned by `modules/experience/docs/specs/`.

## Repository commit and index reconciliation

Repository publication and shared Git index projection are separate effects.
The publisher uses an isolated index and a branch-ref CAS; it never commits
another participant's staged files. Its receipt names its own candidate commit,
not a later observation of shared HEAD.

Short native index-lock contention is retried three times (50 ms between
attempts). A held native lock is never removed and a foreign staged postimage
is never overwritten. If projection remains incomplete, the library retains
the published commit receipt with `index_reconciliation_pending=true` and the
exact `shared_index_projection_error`. Library success means publication; it
does not imply shared-index reconciliation. The selected `aware-cli commit`
returns **exit 3**, emits an explicit publication-success/index-pending warning,
and supplies the recovery instruction. Exit 0 means the CLI operation completed
or its dry-run was planned; exit 2 means a refused/failed operation.

Recover through the same active Issue and exact owned paths:

```sh
aware-cli commit --repo-root <repo> --issue <issue-path> --issue-tag <tag> \
  --path <exact-path> --message "Reconcile published index" \
  --reconcile-index <published-commit> --dry-run --json
```

After a successful plan, repeat without `--dry-run`. This is not a second
publication: it creates no commit, changes no ref or worktree file, and cannot
expand the original publication's path scope. It checks current Issue owner,
lifecycle and scope; original commit Issue/path trailers; commit reachability;
unchanged per-path HEAD postimages; and current index entries or durable
eligible projection-debt preimages. It preserves unrelated staging and refuses
foreign staged target content. Unrelated HEAD advancement is allowed when the
owned published images are unchanged; movement after validation fails closed.
Do not close the Issue before reconciliation completes. Do not retry a plain
publication, force a reset, delete a native lock, or clear debt manually.

## Docs

- Architecture: `docs/ARCHITECTURE.md`
- Bridge backbone: `docs/BRIDGE_BACKBONE.md`
- Stage model: `docs/STAGES.md`
- Functional behavior: `docs/FUNCTIONALITY.md`
