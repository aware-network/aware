# Issue: Integrate exact Workspace A1 whole-envelope tree without selection

- Slug: canonical-workspace-a1-public-integration-v0
- Tag: fb/2026-10-16/canonical-workspace-a1-public-integration-v0
- Status: Closed
- Owner: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Priority: P1
- Goal: TBD
- Captured: 2026-10-16
- Recorder: codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6
- Source: Customer-directed work through aware issue open

## Ownership Scope
- `README.md`
- `docs/alignment/CURRENT.md`
- `docs/issues/2026/10/16/fb-2026-10-16-canonical-workspace-a1-public-integration-v0.md`
- `protocols/WORKFLOW.md`
- `protocols/install.py`
- `protocols/workspace/README.md`
- `releases/README.md`
- `releases/canonical-workspace-a1-fs-v1/CONTENT-AUDIT.json`
- `releases/canonical-workspace-a1-fs-v1/DELIVERY-MAP.json`
- `releases/canonical-workspace-a1-fs-v1/LAYOUT-REVIEW.json`
- `releases/canonical-workspace-a1-fs-v1/LICENSE`
- `releases/canonical-workspace-a1-fs-v1/LOCAL-INTEGRATION.md`
- `releases/canonical-workspace-a1-fs-v1/NOTICE`
- `releases/canonical-workspace-a1-fs-v1/NOTICE-BINDINGS.json`
- `releases/canonical-workspace-a1-fs-v1/README.md`
- `releases/canonical-workspace-a1-fs-v1/REVIEW-STATUS.md`
- `releases/canonical-workspace-a1-fs-v1/SOURCE-INDEX.json`
- `releases/canonical-workspace-a1-fs-v1/SOURCE-MAP.json`
- `releases/canonical-workspace-a1-fs-v1/archive_verifier.py`
- `releases/canonical-workspace-a1-fs-v1/canonical-workspace-a1-source-notice-review-v1.tar.gz`
- `releases/canonical-workspace-a1-fs-v1/source-history/CONTRIBUTING.md`
- `releases/canonical-workspace-a1-fs-v1/source-history/LICENSE`
- `releases/canonical-workspace-a1-fs-v1/source-history/NOTICE`
- `releases/canonical-workspace-a1-fs-v1/source-history/README.md`
- `releases/canonical-workspace-a1-fs-v1/source-history/SECURITY.md`
- `releases/canonical-workspace-a1-fs-v1/source-history/THIRD_PARTY_NOTICES.md`
- `releases/canonical-workspace-a1-fs-v1/source-history/docs/legal/ARTIFACT_PROVENANCE.toml`
- `releases/canonical-workspace-a1-fs-v1/source-history/docs/legal/GENERATED_OUTPUT_POLICY.md`
- `releases/canonical-workspace-a1-fs-v1/source-history/docs/legal/OPEN_SOURCE_POLICY.md`
- `releases/canonical-workspace-a1-fs-v1/test_local_integration.py`
- `workspaces/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/README.md`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/aware_agent_cli/main.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/pyproject.toml`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_composition.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_initialization.py`
- `workspaces/aware_agent/modules/agent/libs/agent_cli/python/tests/test_workspace_setup.py`
- `workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/aware_issue_operational_runtime/source_projection.py`
- `workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/aware_issue_operational_runtime/source_scope_policy.py`
- `workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/aware_issue_operational_runtime/workspace_setup_admission.py`
- `workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/libs/issue_operational_runtime/tests/test_source_scope_policy.py`
- `workspaces/aware_coordination/modules/workflow/libs/issue_runtime/aware_issue_runtime/parser.py`
- `workspaces/aware_coordination/modules/workflow/libs/issue_runtime/tests/test_identity_header.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/README.md`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/provider.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/source_projection.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/aware_issue_fs_adapter/workspace_setup_admission.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/tests/test_provider.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/tests/test_repository_tree_projection_authority.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python/tests/test_rich_reading.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/repository_tree_projection_codec.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/repository_tree_projection_values.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/source_projection.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/workspace_setup_admission.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/workspace_setup_admission_codec.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/aware_issue_sdk/workspace_setup_admission_values.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/pyproject.toml`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/tests/test_repository_tree_projection_admission.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/tests/test_repository_tree_projection_codec.py`
- `workspaces/aware_coordination/modules/workflow/sdks/issue/python/tests/test_workspace_setup_admission_codec.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/README.md`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/__init__.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/grammar_contribution_output.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/grammar_factory.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/grammar_profile_composition.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/grammar_profile_source.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/grammar_source_operands.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/grammar_syntax_composition.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/parser.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/profile_codec.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/profile_models.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/profile_parser.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/v2_codec.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/aware_code_module_manifest_contract_runtime/v2_parser.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_contribution_output.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_factory.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_group_dependency_binding.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_local_dependency_binding.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_planner_product_identity.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_profile_composition.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_profile_source.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_source_operands.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_grammar_syntax_composition.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_profile_manifest_v2.py`
- `workspaces/aware_kernel/modules/code/libs/module_manifest_contract_runtime/tests/test_v3_declarations.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/README.md`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/declaration_host.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/declaration_product_projection.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/direct_epoch_tracking.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/direct_host.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/grammar_profile_role.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/grammar_role_attachment.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/grammar_role_cleanup.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/grammar_role_composition.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/grammar_role_epoch.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/grammar_syntax_role.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/planning_source_composition.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/product_execution.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/product_execution_inputs.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/product_planning_source.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/product_runtime_retention.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/profile_membership.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/selected_catalog_eligibility.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/selected_participant_calculation.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/aware_code_retained_registry_policy_runtime/selected_root_intent.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/pyproject.toml`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_declaration_product_projection.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_contribution_production.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_group_dependency_role.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_local_dependency_role.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_original_planning_target.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_original_source_execution.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_original_workspace_host.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_profile_role.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_role_attachment.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_role_cleanup.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_role_composition.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_role_disposal.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_role_epoch.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_grammar_syntax_role.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_product_execution_inputs.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_product_planning_source.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_product_runtime_retention.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_profile_exposure_v2.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_selected_catalog_eligibility.py`
- `workspaces/aware_kernel/modules/code/libs/retained_registry_policy_runtime/tests/test_single_product_declaration_host.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/README.md`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/__init__.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/direct_origin_interfaces.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_contribution_contract.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_input_codecs.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_product_contracts.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_profile_codec.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_profile_contract.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/grammar_profile_join.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/installed_provider_factory.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/product_contribution.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/product_execution_input_plan.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/retained_declaration_scope_codec.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/retained_declaration_scope_validation.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/selected_provider.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/aware_code_semantic_contract_runtime/stage_contribution.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/pyproject.toml`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_declaration_scope_context_ref.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_direct_origin_interfaces.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_contextual_codecs.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_declaration_context.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_declaration_workspace_join.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_input_context_codecs.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_product_contracts.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_profile_codec.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_grammar_profile_contract.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_installed_provider_factory.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_product_contribution.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_product_execution_input_plan.py`
- `workspaces/aware_kernel/modules/code/libs/semantic_contract_runtime/python/tests/test_retained_declaration_scope_validation.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/README.md`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/__init__.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/confined_mutation.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/retained_file_sequence.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/retained_mutation.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/retained_tree_projection.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/pyproject.toml`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_confined_mutation.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_confined_observation_cleanup.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_retained_file_sequence.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_retained_tree_projection.py`
- `workspaces/aware_kernel/modules/filesystem/libs/file_system/python/tests/test_tree_projection_values.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/README.md`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/aware_specification_cli/read_commands.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/aware_specification_cli/receipt_commands.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/pyproject.toml`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/tests/test_read_commands.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/tests/test_receipt_commands.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/README.md`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/aware_specification_fs_sdk_adapter/__init__.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/aware_specification_fs_sdk_adapter/saved_receipt.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/pyproject.toml`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_issue_storage_successor.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_package_catalog.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_provider.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_saved_receipt.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/README.md`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/aware_specification_sdk/__init__.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/aware_specification_sdk/saved_receipt.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/aware_specification_sdk/wire.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/pyproject.toml`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_authored_closure.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_draft_evidence.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_operation.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_saved_receipt.py`
- `workspaces/aware_kernel/modules/specification/sdks/specification/python/public/tests/test_saved_receipt_codec.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/README.md`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/architecture_setup_a1_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/architecture_setup_a1_command_values.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/architecture_setup_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_command/materialize_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/change_evidence_codec.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/declaration_product_membership.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/declaration_scope_admission.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_planning.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_product_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_cli_selected_host.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/direct_command_composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/local_service.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_graph_coordinator.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_graph_host_composition.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_graph_planner.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_operation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/materialization_session.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/operational_validation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/package_checkout.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_delta_retention.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_mutation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_tree_capacity.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_tree_projection.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/repository_workflow.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/semantic_catalog_host.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/semantic_dependency_graph.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/semantic_dependency_graph_codec.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/semantic_materialization_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/source_observation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/aware_workspace_runtime/source_observation_io.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/benchmarks/materialization_latency.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/qualification/installed_a1_proof.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/materialization_latency_report.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_a1_command.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_a1_command_values.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_a1_metadata.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_architecture_setup_admission.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_change_evidence_codec.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_declaration_product_membership.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_execution.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_planning.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_product_publication.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_cli_selected_host.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_live_profile_selection.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_direct_product_performance.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_local_service.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_materialization_latency_report.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_materialization_wire_performance.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_operational_validation.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_package_checkout.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_tree_capacity.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_tree_projection.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_repository_workflow.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_retained_body_batch.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_selected_source_storage_process_handoff.py`
- `workspaces/aware_workspace/modules/workspace/libs/workspace_runtime/tests/test_single_product_command_composition.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_delta_store.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_mutation_store.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/aware_workspace_fs_adapter/repository_source_projection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_mutation_store_serialization.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_repository_delta_store.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/filesystem_adapter/python/tests/test_repository_tree_projection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/README.md`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_admission.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_admission_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/architecture_setup_admission_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_delta_retention.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_workflow.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_workflow_source_codec.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_workflow_source_values.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/pyproject.toml`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_architecture_setup_admission.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_tree_projection_contract.py`
- `workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/tests/test_repository_workflow_source_contract.py`






## Problem
1. Accepted Workspace A1 layout is not yet integrated against the exact incoming public revision.







## Goal
1. Project the reviewed 275-path delta with complete source/notice carriage, preserving contributor governance and predecessor selection.







## Acceptance Checklist
- [ ] Exact 279-path scope, accepted layout bytes and executable modes, original receipts and actual commit delta; no reconciliation debt.
- [ ] Fresh offline hidden-checkout 42-package installation with supported help, missing-identity and reuse refusals.
- [ ] Independent review before closeout; instructions remain draft and successor unselected; no push or unassisted-onboarding claim.







## Verified-by
- Independent PASS supplied by Luis; /tmp/aware-a1-integration-review.OaE65poE/integration.xml SHA256 6da299ed70c5efcdb1917272d246ec3db04e2eb7b2bc86f13dc63bb64f4e5af6. Recording and closeout rerun no tests, installation or software changes.
- git:4da4e03a77cf8fe8efc137eecf44a4870a03e08c

## Updates (append-only)
- Ensured through `issue_sdk.ensure_issue_snapshot`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.start_issue_progress`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Projected exact 275-path accepted delta under genuine 279-path scope. Restored original pinned contributor a6 separately after explicit Luis authorization. 28 producer guards and 8 integration checks pass, including fresh offline checkout-hidden 42-package installation, full envelope/source bindings, 14 help entrances, missing identity and reuse refusals. Initial wrong maintainer help vector failure retained; corrected smoke used new environment and unchanged software. Whole-envelope and prepared A1 limits remain; no governed A1/domain matrix/U replay, selection, freeze or push. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Integrated locally at 1872a6e20a5502749aa34acffdcb9e06c611eb07: exact 279-path implementation matches original receipt; CAS/shared-index applied without debt. 28 guards and 8 integration checks pass. Whole accepted envelope/source/modes and predecessor/contributor selection preserved. Full implementation-range whitespace check clean. Independent bounded review next; Issue remains In Progress. No selection, instruction freeze, remote push, full domain/governed A1 replay or unassisted evaluation. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Luis supplied independent bounded PASS for 1872a6e20a55 / 1b2bb517fc3a. 28 guards and 8 integration checks pass, zero skipped; exact 279-path implementation/two-path handoff and original guards/receipts match with CAS/index completed without debt. Fresh offline hidden-checkout 42 locked packages; restored contributor 0.1.0a6 contract 1.2.1 hash-bound. Independent XML /tmp/aware-a1-integration-review.OaE65poE/integration.xml SHA256 6da299ed70c5efcdb1917272d246ec3db04e2eb7b2bc86f13dc63bb64f4e5af6. No tests/installation rerun recording acceptance. Whole-envelope/A1 limits remain; selection/freeze/push separate. (outcome: info) (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)
- Applied `issue_sdk.close_issue`. (recorder: `codex-01a0e2c0-e9cd-7c83-969b-d9ab031d0ec6`)

## Resolution
Bounded local integration accepted independently: exact 279-path implementation, two-path handoff and original receipts match; 28 guards + 8 fresh offline checkout-hidden integration checks pass, 42 locked packages, preserved bytes/modes/source/notices and contributor governance; restored pinned contributor separate. Whole-envelope required; governed A1 execution, A2/tree completion and unassisted onboarding unestablished. Selection, instruction freeze and push remain separate.
