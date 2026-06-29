# Aware Meta Python Runtime

This package is the Python runtime for the Meta graph protocol. The public
module story is in [`../../../README.md`](../../../README.md); this file is the
implementer and auditor map for the code behind it.

Meta runtime code should be read as a pipeline:

```text
semantic provider request
  -> provider-delta planning
  -> typed operation plan
  -> ontology FunctionCall resolution/execution
  -> OIG commit/head move
  -> runtime index patch
  -> generated materialization output
  -> receipt
```

## Runtime Boundary

The runtime package is declared by
[`../../aware.ontology.toml`](../../aware.ontology.toml) with project name
`aware-meta` and import root `aware_meta`.

Public consumers should normally use Workspace, aware-dev, Meta SDK/service API,
or proof runners. Direct imports from `aware_meta.runtime`,
`aware_meta.materialization`, generated handlers, or handler executor internals
are contributor/auditor surfaces, not the first consumer API.

## Directory Map

**Graph configuration (`OCG`)**

- [`aware_meta/graph/config`](aware_meta/graph/config) builds and indexes
  ObjectConfigGraph truth: classes, attributes, enums, functions,
  relationships, packages, stable IDs, and runtime derivation.

**Graph projection (`OPG`)**

- [`aware_meta/graph/projection`](aware_meta/graph/projection) compiles
  projection declarations, portal identity, projection hashes, and projection
  materialization support.

**Graph instance (`OIG`)**

- [`aware_meta/graph/instance`](aware_meta/graph/instance) builds, validates,
  hashes, diffs, hydrates, and projects ObjectInstanceGraph state.

**Commit rail**

- [`aware_meta/graph/instance/commit`](aware_meta/graph/instance/commit) owns
  lane commits, commit storage, payload refs, materialization cache, state
  index, OCG-delta extraction from OIG commits, and validation.
- [`aware_meta/graph/instance/commit/committer.py`](aware_meta/graph/instance/commit/committer.py)
  is the durability boundary for canonical OIG commits.
- [`aware_meta/graph/instance/commit/fs_store.py`](aware_meta/graph/instance/commit/fs_store.py)
  persists lane heads, commit envelopes, sidecars, and health indexes under the
  configured Aware root.

**Provider-delta materialization**

- [`aware_meta/materialization/deltas`](aware_meta/materialization/deltas)
  contains the Meta provider-delta lifecycle: dirty diff, typed operations,
  mutation plans, ontology execution plans, generated materialization, receipts,
  readiness, and result envelopes.
- [`aware_meta/materialization/deltas/service.py`](aware_meta/materialization/deltas/service.py)
  is the main provider-delta pipeline.
- [`aware_meta/materialization/deltas/typed_operations.py`](aware_meta/materialization/deltas/typed_operations.py)
  exposes semantic dirty entries as typed Meta operations.
- [`aware_meta/materialization/deltas/result.py`](aware_meta/materialization/deltas/result.py)
  assembles consumer-facing provider-delta result and commit-ref evidence.

**Semantic FunctionCalls**

- [`aware_meta/materialization/semantic_function_call_resolution.py`](aware_meta/materialization/semantic_function_call_resolution.py)
  resolves semantic FunctionCall plans against current and planned graph truth.
- [`aware_meta/materialization/semantic_function_call_execution.py`](aware_meta/materialization/semantic_function_call_execution.py)
  adapts resolved Meta FunctionCalls to the semantic graph invocation backend.
- [`aware_meta/runtime/function_call_builder.py`](aware_meta/runtime/function_call_builder.py)
  builds deterministic Meta FunctionCall envelopes from runtime graph indexes.

**Runtime invocation and handlers**

- [`aware_meta/runtime/graph_commit_invocation_backend.py`](aware_meta/runtime/graph_commit_invocation_backend.py)
  is the canonical FunctionCall -> FunctionCallResponse -> OIG commit backend.
- [`aware_meta/runtime/handler_executor`](aware_meta/runtime/handler_executor)
  resolves function targets, builds execution plans, enforces mutation
  boundaries, records session changes, and dispatches generated/authored
  implementation code.
- [`aware_meta/handlers/impl`](aware_meta/handlers/impl) contains authored
  handler implementation sections.
- [`aware_meta/handlers/_generated`](aware_meta/handlers/_generated) contains
  generated handler routing and must not be treated as hand-authored authority.

**Language materialization**

- [`aware_meta/materialization/language_service.py`](aware_meta/materialization/language_service.py)
  drives language-plugin materialization for ObjectConfigGraph packages.
- [`aware_meta/language_plugin.py`](aware_meta/language_plugin.py) and
  [`aware_meta/language_plugin_registry.py`](aware_meta/language_plugin_registry.py)
  expose the plugin boundary for generated language targets.
- [`aware_meta/materialization/workspace_provider.py`](aware_meta/materialization/workspace_provider.py)
  adapts Meta materialization output to Workspace semantic materialization
  contracts.

**Receipts and testing**

- [`aware_meta/receipts`](aware_meta/receipts) carries receipt buses and relays.
- [`aware_meta/runtime/testing`](aware_meta/runtime/testing) contains the Meta
  runtime proof helpers used by module and public proofs.
- [`tests/provider_delta`](tests/provider_delta) is the focused provider-delta
  suite.

## Provider-Delta Stage Order

The main pipeline in
[`aware_meta/materialization/deltas/service.py`](aware_meta/materialization/deltas/service.py)
records named stage timings. The public README can use these as the stable
mental model:

1. `request_identity`
2. `provider_contract_check`
3. `execution_context_preflight`
4. `baseline_dirty_preflight`
5. `execution_baseline_gate`
6. `manifest_resolution`
7. `code_delta_normalization`
8. `semantic_analysis`
9. `function_call_plan`
10. `empty_lane_genesis_preflight`
11. `semantic_dirty_diff`
12. `head_move_plan_initial`
13. `typed_operation_plan`
14. `semantic_change_report`
15. `source_projection`
16. `generated_materialization`
17. `mutation_plan`
18. `ontology_execution_plan`
19. `functioncall_capability_matrix`
20. `execute_flag_preflight`
21. `operation_plan`
22. `oig_commit_receipt`
23. `head_move_applied_receipt`
24. `runtime_package_index_patch`
25. `semantic_commit_evidence`
26. `output_materialization`
27. `operation_plan_receipts`
28. `operation_execution_detail`
29. `result_assembly`

That order matters: generated outputs and runtime index patches are only
valuable after commit/head evidence exists or the receipt says why execution is
blocked.

## Key Tests And Proofs

Focused runtime tests live beside this package:

- [`tests/test_meta_workspace_provider_delta.py`](tests/test_meta_workspace_provider_delta.py)
- [`tests/test_meta_provider_delta_result_envelope_contracts.py`](tests/test_meta_provider_delta_result_envelope_contracts.py)
- [`tests/test_meta_provider_delta_dirty_diff_contracts.py`](tests/test_meta_provider_delta_dirty_diff_contracts.py)
- [`tests/provider_delta`](tests/provider_delta)
- [`tests/test_function_call_handlers.py`](tests/test_function_call_handlers.py)
- [`tests/test_function_invocation_plan_builder.py`](tests/test_function_invocation_plan_builder.py)
- [`tests/test_fs_commit_store.py`](tests/test_fs_commit_store.py)

The public kernel proof index is
[`../../../../../docs/proofs/proofs.json`](../../../../../docs/proofs/proofs.json).
The public proof package wrappers live under
[`../../../../../docs/proofs/aware_kernel_proofs`](../../../../../docs/proofs/aware_kernel_proofs).

## Source Of Truth

- `.aware` graph protocol sources live under
  [`../../structure/aware`](../../structure/aware).
- Runtime implementation lives under [`aware_meta`](aware_meta).
- Generated/materialized outputs under ontology structure language directories
  are not hand-authored authority.
- Handler logic belongs in explicit authored implementation sections under
  [`aware_meta/handlers/impl`](aware_meta/handlers/impl).
