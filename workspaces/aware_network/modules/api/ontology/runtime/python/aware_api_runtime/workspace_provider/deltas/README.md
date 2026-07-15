# API Provider Deltas

This package owns the API provider-delta implementation.

`aware_api_runtime.workspace_provider.materialize_delta` is the public Workspace
provider entrypoint. New provider-delta implementation should land under this
package instead of expanding the provider entrypoint module.

## Current Modules

- `service.py` owns provider-delta orchestration while the existing implementation
  is extracted from the provider entrypoint module.
- `transport.py` owns provider request normalization, transported
  `CodePackageDelta` validation, changed-path hint normalization, and fail-closed
  delta guards.
- `semantic_analysis.py` owns current API semantic analysis from transported
  authored `.aware` source upserts plus current semantic-delta index evidence.
- `baseline.py` owns baseline ref/commit-ref normalization, durable execution
  input preflight, and current-head semantic-object context extraction.
- `dirty_diff.py` owns API semantic dirty diff construction and baseline-index
  comparison evidence.
- `typed_operations.py` owns API typed operation plan construction, typed
  operation payloads, semantic-event projection, and operation counts.
- `execution.py` owns API typed operation execution preflight,
  payload-completeness checks, typed apply/upsert execution through semantic
  graph invocations, and typed execution-block evidence.
- `source_package.py` owns API source `CodePackageDelta` filtering and source
  package apply payloads.
- `artifact_plan.py` owns the api-client/service-protocol runtime-artifact delta
  plan. It emits updated API runtime artifacts from the current provider-delta
  semantic analysis only when the delta covers the full API source set and the
  render inputs are available. It now prefers Meta semantic context
  ObjectConfigGraphs as current render inputs, then falls back to existing
  runtime accessible-dependency artifacts; otherwise it blocks before renderer
  execution. Ready plans also expose a generated-path candidate plan derived
  from API semantic dirty entries plus current API ownership, covering
  api-client model/client/binding paths and service-protocol `protocols.py`
  paths as evidence for later renderer-invocation pruning.
- `artifact_patch.py` owns the post-execution api-client/service-protocol delta
  patch receipt. It blocks unless typed execution, source package delta apply,
  commit/head refs, and a freshness-proven runtime-artifact delta plan are
  ready. When that plan is present, it executes only the requested
  api-client/service-protocol patch targets, compares requested generated files
  before/after refresh, returns ownership receipts only for changed generated
  files, records no-op target evidence, consumes generated-path candidate plans
  to scope file comparison, receipt propagation, and Meta renderer invocation
  candidates when the candidate plan is filter-ready, emits generated-file
  pruning metrics, exposes a normalized event-driven language artifact delta
  apply payload for api-client/service-protocol file create/update/delete/no-op
  operations, and never runs full API compile as a hidden fallback.

## Extraction Order

1. `transport.py`: provider request normalization, transported
   `CodePackageDelta` validation, and fail-closed delta guards.
2. `semantic_analysis.py`: transported authored `.aware` source analysis and
   current semantic-delta index evidence.
3. `baseline.py`: baseline hydration preflight, baseline ref normalization, and
   committed API semantic-object index normalization.
4. `dirty_diff.py`: API semantic dirty diff and baseline-index comparison.
5. `head_move.py`: shared Workspace provider-delta head-move request/plan
   normalization.
6. `typed_operations.py`: API typed operation payloads for Api,
   ApiCapability, ApiCapabilityEndpoint, and future graph/contract shapes.
7. `execution.py`: typed operation execution preflight, payload-completeness
   checks, typed apply/upsert execution through canonical semantic graph
   invocations, durable refs, and head-move-applied receipts.
8. `source_package.py`: source CodePackage delta commit/update receipt handling.
9. `artifact_plan.py`: api-client/service-protocol runtime-artifact delta plan
   emission from current delta analysis, blocked on partial source-set deltas or
   missing render dependency graph inputs, with semantic dirty-entry to
   generated-path candidate planning.
10. `artifact_patch.py`: post-commit api-client/service-protocol patch receipts
   gated by real delta execution/head refs and runtime-artifact delta-plan
   freshness, with planner/dry-run paths blocked.
11. `result.py`: final provider-delta result envelope and compatibility payloads.
12. `utils.py` and `constants.py`: shared coercion helpers and contract ids once
   enough modules need them.

The current pruning boundary is generated-file propagation pruning: unchanged
api-client/service-protocol files are detected by before/after digest and
excluded from changed-file receipts while target-level pruning metrics remain
visible. Runtime-artifact plans now carry generated-path candidates, but those
candidates are now translated into renderer-output-relative paths for Meta
renderer candidate scope when the candidate plan is filter-ready. Candidate
scope prunes renderer file invocation and generated-file receipt propagation;
provider deltas still never run full API compile to manufacture
api-client/service-protocol ownership receipts. The next normalized boundary is
`language_artifact_delta_apply`: it records the concrete api-client and
service-protocol file operations derived from materialization-event candidates
plus generated-file patch evidence, while dispatch remains explicitly unwired.
