# API Runtime Architecture

The API runtime is organized by product feature, not by generic execution phase.

## Feature Boundaries

- `manifest/` owns `aware.api.toml` loading and typed manifest specs.
- `source/` owns authored API `.aware` source parsing, ownership loading, and
  semantic capability analysis. The retired root `compiler.py` and
  `semantic_analysis.py` facades are deleted; all consumers must import through
  `aware_api_runtime.source`.
- `dependencies/` owns dependency runtime artifact and accessible graph
  resolution. The retired root `runtime_resolution.py` facade is deleted; all
  consumers must import through `aware_api_runtime.dependencies.runtime_resolution`.
- `ir/` owns the API intermediate representation. `APICompilePlan` is the
  canonical IR produced from manifest/source/dependencies and consumed by
  ontology graph, package, and invocation outputs. The retired root `builder.py`
  facade is deleted; all consumers must import through `aware_api_runtime.ir`.
- `ontology_graph/` owns lowering the API IR into API ontology graph operation
  plans and graph materialization steps. The retired `graph/` package is
  deleted; API runtime internals and downstream consumers must import through
  `aware_api_runtime.ontology_graph`.
- `packages/` owns generated package outputs: public API package, service
  protocol package, and DTO package surfaces. The retired `products/` package
  is deleted; all consumers must import through `aware_api_runtime.packages`.
- `compile_materialization/` owns API package compile/materialization
  orchestration: compile-plan payload loading, dependency graph preparation,
  package materialization specs, and the `materialize_api_compile_plan_ontology`
  deployable runtime entrypoint. The retired
  `aware_api_runtime.materialization.service` path is deleted; consumers must
  import through `aware_api_runtime.compile_materialization`.
- API compile dependency graph authority is runtime-first. Production
  `compile_api_workspace` accepts only `meta_runtime` dependency graph mode; when
  Workspace semantic provider context passes explicit accessible graphs, runtime
  manifests record `semantic_contract`. The retired compat/authored dependency
  graph mode is not a product rail.
- `runtime_context/` owns API's Workspace semantic materialization runtime
  context callable. This is the semantic provider hook used by Workspace to
  build API-owned runtime context through Meta.
- `semantic_functions/` owns API semantic provider function-call preview
  resolution and execution helpers used by provider-delta materialization.
- `snapshots/` owns commit-backed API reference and package manifest snapshots.
- `invocation/` owns API invocation IR, dispatch, ingress, and committed API call
  runtime materialization. `invocation/materialization/` owns `ApiCall` and
  `ApiCallOutcome` commit-backed receipt materialization. The retired
  `ontology/` package is deleted; API invocation materialization must not be
  reached through `aware_api_runtime.ontology`.
- `workspace_provider/` owns the Workspace semantic provider entrypoint and
  provider-delta bridge. `workspace_provider/provider.py` exposes the provider
  callable implementation; `workspace_provider/deltas/` owns provider-delta
  planning, execution, event, and artifact patch logic.
- `handlers/` remains generated handlers plus handwritten impl sections only.

## Compatibility

Root compatibility facades are retired. Use feature-boundary imports only:
`aware_api_runtime.ir`, `aware_api_runtime.source`,
`aware_api_runtime.invocation`, `aware_api_runtime.compile_materialization`, and
`aware_api_runtime.dependencies.runtime_resolution`,
`aware_api_runtime.runtime_context`, `aware_api_runtime.semantic_functions`, and
`aware_api_runtime.snapshots`.

The retired `aware_api_runtime.materialization` package is deleted. API
materialization responsibilities are split across the explicit feature
boundaries above.

The stable operation name `api_product_build` is not Product A/B language; it is
the graph operation/producer key used by provider-delta receipts.
