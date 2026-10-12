# Issue: Integrate exact target-fit whole-envelope tree without selection

- Slug: canonical-target-fit-public-integration-v0
- Tag: fb/2026-10-12/canonical-target-fit-public-integration-v0
- Status: In Progress
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-12
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `README.md`
- `docs/alignment/CURRENT.md`
- `docs/issues/2026/10/12/fb-2026-10-12-canonical-target-fit-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `releases/README.md`
- `releases/canonical-target-fit-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-target-fit-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-target-fit-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-target-fit-fs-v1/LICENSE`
- `releases/canonical-target-fit-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-target-fit-fs-v1/NOTICE`
- `releases/canonical-target-fit-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-target-fit-fs-v1/README.md`
- `releases/canonical-target-fit-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-target-fit-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-target-fit-fs-v1/SOURCE-MAP.json`
- `releases/canonical-target-fit-fs-v1/archive_verifier.py`
- `releases/canonical-target-fit-fs-v1/canonical-target-fit-source-notice-review-v1.tar.gz`
- `releases/canonical-target-fit-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-target-fit-fs-v1/source-history/LICENSE`
- `releases/canonical-target-fit-fs-v1/source-history/NOTICE`
- `releases/canonical-target-fit-fs-v1/source-history/README.md`
- `releases/canonical-target-fit-fs-v1/source-history/SECURITY.md`
- `releases/canonical-target-fit-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-target-fit-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-target-fit-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-target-fit-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-target-fit-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/draft_preparation.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_composition.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_draft_preparation.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_initialization.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/cli/python/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/provider.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/tests/test_rich_reading.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/__init__.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/operation.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/reading_operation.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/tests/test_reading_operation.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/README.md`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/__init__.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/codec.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/models.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/parser.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/python_package_setup.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/syntax_declaration.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/pyproject.toml`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_module_manifest_contract.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_python_package_setup.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_syntax_declaration.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/pyproject.toml`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/README.md`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/__init__.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_profile_join.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_source_group.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/retained_declaration_scope_codec.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_declaration_scope_context_ref.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_profile_join.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_source_group.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/LICENSE`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/NOTICE`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/README.md`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/__init__.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/_origin_profile.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/codec.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/compatibility.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/composed_slice_advancement.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/composition.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/composition_codec.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/composition_transition.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/definition_fragment.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/diagnostics.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/encoding.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/local_read_model.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/migration.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/model.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/persistent_index.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/positive_reader.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/py.typed`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/type_schema_operation.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/aware_meta_type_schema/validation.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/pyproject.toml`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_codec.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_compatibility.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_composed_slice_advancement.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_composition.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_composition_codec.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_composition_transition.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_definition_fragment.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_encoding.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_local_read_model.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_migration.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_model.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_null_scalar.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_origin_profile.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_package_closure.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_persistent_index.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_positive_reader.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_slices.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_type_schema_operation.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/tests/test_validation.py`
- `workspaces/aware_kernel/modules/meta/libs/type_schema/python/uv.lock`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/README.md`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/aware_protocol_fs_adapter/__init__.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/aware_protocol_fs_adapter/specification_selection.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/aware_protocol_fs_adapter/specification_target_fit.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/pyproject.toml`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/tests/test_specification_selection.py`
- `workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python/tests/test_specification_target_fit.py`
- `workspaces/aware_kernel/modules/protocol/sdks/protocol/python/README.md`
- `workspaces/aware_kernel/modules/protocol/sdks/protocol/python/aware_protocol_sdk/__init__.py`
- `workspaces/aware_kernel/modules/protocol/sdks/protocol/python/aware_protocol_sdk/specification_target_fit.py`
- `workspaces/aware_kernel/modules/protocol/sdks/protocol/python/pyproject.toml`
- `workspaces/aware_kernel/modules/protocol/sdks/protocol/python/tests/test_bootstrap_contract.py`
- `workspaces/aware_kernel/modules/protocol/sdks/protocol/python/tests/test_specification_target_fit.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/LICENSE`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/NOTICE`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/README.md`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/__init__.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/codec.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/definition.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/definition_codec.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/definition_transition.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/manifest/__init__.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/manifest/codec.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/manifest/model.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/manifest/parser.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/model.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/py.typed`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/aware_sdk_contract_runtime/validation.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/pyproject.toml`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/tests/test_contract.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/tests/test_definition_codec.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/tests/test_definition_transition.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/tests/test_manifest.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/tests/test_manifest_profiles.py`
- `workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python/uv.lock`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/README.md`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/architecture_setup_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/pack.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/setup_registration.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/workspace_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/declaration_scope_admission.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/package_checkout.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/package_manager_toml.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_workflow.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_checkout_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_grouped_selected_source_input.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_package_checkout.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_workflow.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_setup_registration.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_workflow_evidence.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_repository_workflow_evidence.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_workflow.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_workflow_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_workflow_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_package_manager_contexts.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_workflow_contract.py`





## Problem
1. Accepted target-fit layout is not yet integrated against the exact incoming public revision.






## Goal
1. Project the reviewed 169-path delta with complete source/notice carriage, preserving contributor governance and predecessor selection.






## Acceptance Checklist
- [ ] Exact 173-path scope, accepted layout bytes and executable modes, original receipts and actual commit delta; no reconciliation debt.
- [ ] Fresh offline hidden-checkout 42-package installation with supported help, missing-identity and reuse refusals.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.






## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Reviewed169-path projection plus4governance extras matches accepted1332-file layout;28 producer guards and8 public maintainer checks pass,zero skips,fresh offline hidden-checkout42-package installation. Complete envelope/source/notice/mode mappings,predecessor selection and contributor a6 preserved. Missing identity,reuse and aware workspace refuse. No broad workflow/matrix,U,selection,freeze or push. Local publication dry-run/apply then independent integration review next. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Implementation8fb3710a4e310b8049ce92024b4132b0913a909a matches actual173-path admitted delta;original contributor dry-run/apply guard9bb110a9aa46 preserved,CAS/shared-index applied,no debt.28 guards+8 integration checks passed with fresh offline42-package install. Final two-path Issue/report handoff only;independent review remains before closeout. Successor unselected,instructions draft,contributor a6 and predecessor unchanged. No broadmatrix/workflow,U,selection,freeze or push. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Record supplied independent PASS8fb3710a4e31/a275a229cf17:28guards+8integration passes zero skips,fresh offline checkout-hidden42packages;actual173/two-path deltas,original guards,CAS/index no debt,exact sources/notices/modes/predecessor/contributor preserved. Receipt SHAff0b9003d0c386d74b0996715ae5e048e276b9e0db3c99a0ce4b16bb82693ce5. No validation rerun/artifact changes to record. Bounded closeout next through original owner;selection,freeze,push,U separate. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
