# Issue: Integrate exact reviewed-workflow whole-envelope tree without selection

- Slug: canonical-reviewed-workflow-public-integration-v0
- Tag: fb/2026-10-17/canonical-reviewed-workflow-public-integration-v0
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-17
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `README.md`
- `docs/alignment/CURRENT.md`
- `docs/issues/2026/10/17/fb-2026-10-17-canonical-reviewed-workflow-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `protocols/workspace/README.md`
- `protocols/workspace/REVIEWED-SETUP.md`
- `releases/README.md`
- `releases/canonical-reviewed-workflow-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-reviewed-workflow-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-reviewed-workflow-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-reviewed-workflow-fs-v1/LICENSE`
- `releases/canonical-reviewed-workflow-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-reviewed-workflow-fs-v1/NOTICE`
- `releases/canonical-reviewed-workflow-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-reviewed-workflow-fs-v1/README.md`
- `releases/canonical-reviewed-workflow-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-reviewed-workflow-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-reviewed-workflow-fs-v1/SOURCE-MAP.json`
- `releases/canonical-reviewed-workflow-fs-v1/archive_verifier.py`
- `releases/canonical-reviewed-workflow-fs-v1/canonical-reviewed-workflow-source-notice-review-v1.tar.gz`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/LICENSE`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/NOTICE`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/README.md`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/SECURITY.md`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-reviewed-workflow-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-reviewed-workflow-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/main.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/workspace_review.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_composition.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_review.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_setup.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/local_files.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/tests/test_issue_sdk_local_files.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/CHANGELOG.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/README.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/confined_mutation.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/private_directory.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/retained_file_sequence.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/pyproject.toml`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_private_directory.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/architecture_setup_a1_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/architecture_setup_a1_command_values.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/architecture_setup_a1_presentation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/materialize_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/architecture_setup_a1_driver.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/change_evidence_codec.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/declaration_product_membership.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/declaration_scope_admission.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/dependency_fulfillment.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/dependency_resolution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_demands.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_planning.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_selected_host.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_command_composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_graph_host_composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_graph_planner.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/package_checkout.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_delta.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_tree_preparation_copy.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_tree_projection.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_workflow.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/materialization_latency_report.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/product_supplier_fixture.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_a1_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_a1_metadata.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_a1_presentation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_change_evidence_optimization.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_declaration_product_membership.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_delta_path_optimization.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_dependency_fulfillment.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_dependency_resolution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_dependency_planning.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_participant_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_candidates.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_retained_graph.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_product_performance.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_materialization_latency_report.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_original_supplier_fulfillment.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_product_dependency_inventory.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_tree_projection_journal.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_source_membership_optimization.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_tree_preparation_copy_optimization.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_usability_successor_metadata.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_delta_retention.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_delta_store.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_index_journal.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_mutation_store.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_source_projection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_delta_store_journal.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_mutation_store_journal.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_repository_delta_store.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_repository_index_journal.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/_tree_native.c`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/_tree_native.pyi`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/_tree_native_binding.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_command_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_delta_retention.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/hatch_build.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup_review_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_index_delta_native.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_tree_projection_contract.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_tree_projection_native.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_tree_projection_optimization.py`





## Problem
1. Accepted reviewed-workflow layout is not yet integrated against the exact incoming public revision.






## Goal
1. Project the reviewed 127-path delta with complete source/notice carriage, preserving contributor governance and predecessor selection.






## Acceptance Checklist
- [ ] Exact 131-path scope, accepted layout bytes and executable modes, original receipts and actual commit delta; no reconciliation debt.
- [ ] Fresh offline hidden-checkout 42-package installation with supported help, missing-identity and reuse refusals.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.






## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Exact 127-path reviewed-workflow layout projected against unchanged incoming 001457643287. Public scope is 131 paths including four evidence extras. 28 original/successor controls and eight integrated-tree cases pass, no skips. Fresh offline checkout-hidden installation verifies all 42 locked packages, dependency integrity, no editable/direct URL, installed help and identity/reuse refusals. Initial stale maintainer wording assertion retained; accepted customer guidance unchanged. Complete source/legal carriage, all modes, predecessor selection and contributor a6 preserved. Independent review next; no selection, freeze, push, unassisted evaluation, broad matrix or CPython work. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Local implementation f895e45c38848c1595b4a6108914da7789d146c4 applied exact 131-path scope; original publication git:f895e45c38848c1595b4a6108914da7789d146c4. CAS/index applied, no reconciliation debt; actual paths and original Issue guard match. Checkout/index clean after apply. Raw baseline-to-implementation whitespace diagnostic passes with empty stdout; no normalization. Report preserves final/initial replay distinctions and exact hashes. This two-path handoff is submitted for independent bounded integration review. Issue remains In Progress; no selection/freeze/push/CPython work. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Human supplied independent bounded PASS for producer b56327edea9c/0b366b890991 and public f895e45c3884/5af3a8334bd7. Independent 28 controls and eight integration checks pass, including fresh offline hidden-checkout 42-package installation. Exact original public scope/guards/receipts, CAS/index and committed deltas match. Producer captures remain explicitly truncated; actual producer commits checked separately, public original receipts intact. Record acceptance and close bounded integration; next separately governed selection/instruction alignment. No matrix or unassisted replay, software change, selection/freeze/push/GC or CPython action. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
