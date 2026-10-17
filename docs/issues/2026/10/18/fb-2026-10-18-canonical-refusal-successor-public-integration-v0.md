# Issue: Integrate exact refusal-successor whole-envelope tree without selection

- Slug: canonical-refusal-successor-public-integration-v0
- Tag: fb/2026-10-18/canonical-refusal-successor-public-integration-v0
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-18
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `AGENTS.md`
- `README.md`
- `docs/alignment/CURRENT.md`
- `docs/issues/2026/10/18/fb-2026-10-18-canonical-refusal-successor-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `protocols/workspace/README.md`
- `protocols/workspace/REVIEWED-SETUP.md`
- `releases/README.md`
- `releases/canonical-refusal-successor-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-refusal-successor-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-refusal-successor-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-refusal-successor-fs-v1/LICENSE`
- `releases/canonical-refusal-successor-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-refusal-successor-fs-v1/NOTICE`
- `releases/canonical-refusal-successor-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-refusal-successor-fs-v1/README.md`
- `releases/canonical-refusal-successor-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-refusal-successor-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-refusal-successor-fs-v1/SOURCE-MAP.json`
- `releases/canonical-refusal-successor-fs-v1/archive_verifier.py`
- `releases/canonical-refusal-successor-fs-v1/canonical-refusal-successor-source-notice-review-v1.tar.gz`
- `releases/canonical-refusal-successor-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-refusal-successor-fs-v1/source-history/LICENSE`
- `releases/canonical-refusal-successor-fs-v1/source-history/NOTICE`
- `releases/canonical-refusal-successor-fs-v1/source-history/README.md`
- `releases/canonical-refusal-successor-fs-v1/source-history/SECURITY.md`
- `releases/canonical-refusal-successor-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-refusal-successor-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-refusal-successor-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-refusal-successor-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-refusal-successor-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/main.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/workspace_review.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_composition.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_review.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_setup.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/declaration_scope_admission.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/dependency_fulfillment.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_planning.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_command_composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/initial_authoring.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_operation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/semantic_issuer_factory.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/semantic_materialization_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/source_observation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_a1_metadata.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_consumer_declaration_observation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_dependency_input_carriage.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_participant_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_product_performance.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_materialization_operation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_original_upstream_fulfillment.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_product_input_context.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_product_inventory_validation_window.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_reviewed_refusal_successor_metadata.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_selected_input_read_node.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_usability_successor_metadata.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/initial_authoring.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_publication.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/_tree_native.c`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/_tree_native.pyi`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/_tree_native_binding.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_review_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/__init__.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/authority.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/initial_authoring/values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_preparation/authority.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_publication/authority.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup_review.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup_review_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_initial_authoring.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_tree_projection_native.py`




## Problem
1. Accepted refusal-successor layout is not yet integrated against the exact incoming public revision.





## Goal
1. Project the reviewed 88-path delta with complete source/notice carriage, preserving contributor governance and predecessor selection.





## Acceptance Checklist
- [ ] Exact 92-path scope, accepted layout bytes and executable modes, original receipts and actual commit delta; no reconciliation debt.
- [ ] Fresh offline hidden-checkout 42-package installation with supported help, missing-identity and reuse refusals.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.





## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Exact reviewed 88-path layout projected after original Issue admitted all 92 paths. 28 original/successor projection guards pass. Fresh offline checkout-hidden 42-package install succeeded. First integration suite has seven passes and one inherited wording assertion failure; accepted README says six detached-wheel gaps. Corrected only maintainer assertion; initial environment/XML retained, fresh final replay runs separately. Accepted layout/software, original contributor selection and delivered predecessor are unchanged; no selection, freeze or push. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- 28 guard cases and eight final integration cases pass with zero skips. Fresh offline checkout-hidden 42-package installation verifies exact lock, no editables/direct URLs, complete retained envelope, dependency checks, fifteen help entrances, no-identity and no-reuse refusals. Initial seven-pass/one inherited wording-assertion failure and first successful installation remain retained; only maintainer assertion corrected. Exact accepted layout/software unchanged. Ready for observed-guard dry-run then identical 92-path local apply, not selection/freeze/push; independent integration review remains next. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
