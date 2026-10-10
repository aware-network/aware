# Workspace SDK Feature Packages

Workspace SDK feature packages organize public caller workflows. They are not a
mirror of Workspace runtime `features/*`.

## Boundary

- Feature packages own typed SDK request/result contracts, lifecycle profiles,
  receipt parsing, blocker normalization, and local caller ergonomics.
- Feature packages call service/API/transport facades; they do not import
  Workspace runtime implementation internals.
- Root `client.py` is the SDK facade; package-root `__init__.py` and
  package-level feature/state `__init__.py` files are markers, not export
  barrels. The session facade lives under
  `features/session/facade.py`. New workflow implementation should live in
  feature packages first and callers should use direct feature paths unless they
  are importing `WorkspaceSdkClient` from `aware_workspace_sdk.client`.
- Do not add new package-root or package-level compatibility modules for
  feature migrations; move callers to the direct owner path.

## Current Packages

- `semantic`: semantic status/plan/apply/source-projection lifecycle contracts
  and pure receipt parsing.
- `materialization`: materialize/apply/verify lifecycle result contracts,
  provider-delta feedback parsing, direct materialize API/apply-output/local-state
  workflows, semantic baseline establishment, generated-materialization stage
  helpers, and receipt verification utilities/workflows.
- `revision`: checkout, publish, CAS/lease, branch-head, and revision
  publication caller contracts, helpers, and direct workflow-family modules
  (`checkout_workflows`, `local_head_workflows`, `publication_workflows`,
  `git_mirror_workflows`, `test_api`).
- `operations`: SDK operation catalog dispatch, runtime binding metadata, and
  CLI-oriented local-state payload readers.
- `session`: shared session/status state contracts, checkout-sync,
  checkout-sync workflow delegation, session updates, typed local-only evidence
  builders, prepare/build/commit API request workflows, semantic workflow option
  contracts and workflow orchestration, publish-candidate readiness/commit-stage
  contracts, merge/rebase workflow contracts, direct merge/rebase workflow
  family modules, session facade, delta bundle, and local-state coordination.
- `source_delta`: local source delta collection, local FS-code status, remote
  status orchestration, and CodePackageDelta shaping.
- `transport`: protocol contracts for generated Workspace and Code API clients.

## Planned Packages
