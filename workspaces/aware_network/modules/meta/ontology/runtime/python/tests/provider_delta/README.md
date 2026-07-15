# Meta Provider Delta Tests

This directory is the target namespace for splitting
`modules/meta/runtime/tests/test_meta_workspace_provider_delta.py`.

The current monolith is intentionally not moved in this prep slice because
parallel agents are actively adding typed-operation planner coverage there.
Future slices should move focused clusters here one at a time, keeping each
commit small enough to review and easy to rebase against active delta work.

## Target Layout

- `fixtures.py`: shared test builders only. Keep it small and split it again
  when a helper is clearly owned by one domain. Current helpers cover
  deterministic provider-delta UUIDs, a minimal `.aware` package fixture,
  baseline refs, and provider-delta request construction.
- `test_workspace_adapter.py`: Workspace request/bundle/adapter contract tests.
- `test_baseline_preflight.py`: baseline refs, hydrator blocks, unresolved
  projection, and missing baseline guardrails.
- `test_baseline_index.py`: committed OIG to semantic-object index hydration.
- `test_dirty_diff.py`: runtime-delta dirty comparison, stale/delete semantics,
  source-ref guardrails, and request hydrator dirty diff cases.
- `test_typed_operations.py`: typed-operation plan assembly,
  semantic-object anchors, and subject-specific planner fanout. FunctionImpl
  noop-anchor, function-membership, and class attribute-membership split
  coverage live here.
- `test_mutation_plan.py`: typed-operation to mutation-step conversion,
  receiver resolution, descriptor resolution, and FunctionCall plan readiness.
  FunctionImpl anchor/head-move mutation-plan coverage lives here.
- `test_ontology_execution_attribute.py`: direct attribute create/update/delete,
  attribute-membership update/replacement/blocking, and collection
  missing-function ontology execution plus capability matrix cases.
- `test_ontology_execution_function.py`: direct function update and
  identity-change blocking ontology execution plus capability matrix cases.
- `test_ontology_execution_function_membership.py`: direct function-membership
  update and identity-change blocking ontology execution plus capability
  matrix cases.
- `test_ontology_execution_function_impl.py`: direct FunctionImpl instruction
  creation, assignment/value-source replacement, stale removal, reorder, and
  capability matrix ontology execution cases.
- `test_ontology_execution_relationship.py`: direct relationship
  create/update/delete and identity-change blocking ontology execution plus
  capability matrix cases.
- `runtime_execution/`: execute-flag preflight/guardrails and runtime commit
  E2E coverage split by execution concern. Keep provider-level readiness and
  blocked-state policy in `test_preflight.py`, subject-specific runtime
  invocation in subject files such as `test_attribute.py`, and retired
  append-ready payload absence coverage in `test_append_ready_commit.py`.
- `test_receipts.py`: direct OIG/head context receipts, FunctionCall execution
  receipt contracts, and runtime package-index patch receipts. Broader execute-flag
  materialization E2E cases stay with their subject split until the dirty-diff
  and planner clusters move.
- `test_events.py`: dirty semantic event reports and committed semantic event
  translation.
- `test_handler_boundaries.py`: direct handler mutation-boundary proofs.

## Current Cluster Map

Approximate line ranges in the current monolith:

- `1-968`: imports and shared builders.
- `969-1234`: Workspace adapter, bundle, context, and code-owned request
  contracts.
- `1235-1872`: baseline dirty preflight and blocked hydrator states.
- `1873-2819`: committed OIG semantic index hydration plus hydrated dirty diff,
  typed-operation, and mutation-plan readiness.
- `2822-3645`: mutation-plan receiver/descriptor helper behavior.
- `3646-4552`: path-hint guardrails, simple dirty diff, stale attributes,
  request hydrator, and delete-delta dirty diff behavior.
- `4520-6590`: execute-flag durable runtime execution for attribute,
  relationship, function, and function-membership operations.
- `6591-6596`: `_FakeEvidence` helper still used by monolith event payload
  tests.

## Fixture Boundary

The first migration slice should create `fixtures.py` with only the builders
needed by the moved cluster. Avoid a new mega-helper file.

Allowed shared fixture categories:

- request builders: provider-delta request and baseline refs;
- source fixtures: temporary `.aware` package deltas;
- baseline fixtures: semantic-object index and committed OIG shapes;
- runtime fixtures: recording ontology runtime and invocation context;
- tiny evidence helpers: `_FakeEvidence` style payload wrappers.

Do not move subject-specific typed-operation payload builders into
`fixtures.py`. Put them in the test module that owns the subject, or in a
small subject helper next to that module.

## Migration Order

1. Move leaf direct-unit clusters first:
   `test_events.py` owns provider-delta dirty event report/readable-chain plus
   semantic event translation tests. `test_handler_boundaries.py` owns direct
   invoked-object handler mutation-boundary tests. `test_receipts.py` owns
   direct receipt/package-index patch tests.
2. Move direct ontology execution planners by subject:
   FunctionImpl execution planners live in
   `test_ontology_execution_function_impl.py`; attribute execution planners live in
   `test_ontology_execution_attribute.py`; function execution planners live in
   `test_ontology_execution_function.py`; function-membership execution
   planners live in `test_ontology_execution_function_membership.py`;
   relationship execution planners live in
   `test_ontology_execution_relationship.py`.
3. Move typed-operation planner tests by subject. FunctionImpl noop-anchor,
   function-membership fanout, and class attribute-membership fanout coverage
   live in `test_typed_operations.py`; remaining mixed tests that also assert
   ontology execution live with their execution subject.
4. Move mutation-plan clusters. FunctionImpl mutation-plan coverage lives in
   `test_mutation_plan.py`; remaining receiver/descriptor helpers should move
   in later slices.
5. Move baseline/dirty-diff clusters.
6. Move Workspace adapter/provider E2E clusters last.
7. Delete or shrink the monolith only after `pytest --collect-only` proves no
   tests were lost and focused suites are passing.

## Runtime Execution Package Boundary

`runtime_execution/` is intentionally a package, not a single runtime E2E file.
Each file should model one reason the provider crosses from read-only delta
planning into execution:

- `test_preflight.py`: execute-flag policy, active execution rail selection,
  missing baseline blocks, and baseline-present fallback states.
- `test_attribute.py`: attribute and attribute-membership invocations through
  the Meta ontology FunctionCall rail.
- `test_relationship.py`: relationship create/update/delete runtime execution.
- `test_function.py`: function and function-membership runtime execution.
- `test_append_ready_commit.py`: retired append-ready payload absence and
  FunctionCall-only runtime receipt coverage.
- `fixtures.py`: tiny runtime-only fakes and OIG head-context writers. Do not
  add typed-operation builders here; those stay with the subject test that owns
  the payload.

## Validation

For each move:

```bash
uv run pytest --collect-only -q modules/meta/runtime/tests/test_meta_workspace_provider_delta.py modules/meta/runtime/tests/provider_delta
uv run pytest -q modules/meta/runtime/tests/provider_delta/<moved_file>.py
uv run pytest -q modules/meta/runtime/tests/test_meta_workspace_provider_delta.py -k '<moved_keyword>'
.venv/bin/flake8 --select F,E9 modules/meta/runtime/tests/provider_delta/<moved_file>.py
uvx basedpyright --level error modules/meta/runtime/tests/provider_delta/<moved_file>.py
```

The old monolith `-k` check should return either the moved tests before
deletion or zero selected after deletion. Do not leave duplicates unless the
issue explicitly says the step is a temporary copy-only staging commit.

## Rules

- New provider-delta tests should land in this namespace, not in the monolith.
- Keep each test file aligned with one runtime module or one semantic subject.
- Keep public payload assertions close to the module that owns the contract.
- Do not hide execution semantics behind fixtures; fixtures build data,
  tests assert behavior.
- Avoid broad imports from the monolith. Move helpers into `fixtures.py` or
  small subject-owned helper modules before importing them.
