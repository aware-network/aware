from __future__ import annotations

from typing import Mapping, cast

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticArtifactLeafOwnershipDescriptor,
    ModuleSemanticContract,
    ModuleSemanticGrammarRuleDescriptor,
    ModuleSemanticGrammarRuleFieldDescriptor,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
    ModuleSemanticMaterializationExecutionContextDescriptor,
    ModuleSemanticMaterializationInputDescriptor,
    ModuleSemanticMaterializationPackageOutputDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
    ModuleSemanticWorkflowDescriptor,
    ModuleSemanticWorkflowInstructionDescriptor,
)
from aware_code.package_surface import normalize_code_package_surface
from aware_code.semantic_package.schemas import (
    CapabilityBundleDescriptor,
    CapabilityParticipationDescriptor,
    CapabilityProfileDescriptor,
)
from aware_code_sdk.dto import (
    CodeCapabilityBundleDescriptor,
    CodeCapabilityExecutionPolicyDescriptor,
    CodeCapabilityParticipationDescriptor,
    CodeCapabilityProfileDescriptor,
    CodeSemanticArtifactLeafOwnershipDescriptor,
    CodeSemanticContract,
    CodeSemanticGrammarRuleDescriptor,
    CodeSemanticGrammarRuleFieldDescriptor,
    CodeSemanticManifestResolutionDescriptor,
    CodeSemanticMaterializationArtifactOutputDescriptor,
    CodeSemanticMaterializationCodePackageDeltaOutputDescriptor,
    CodeSemanticMaterializationExecutionContextDescriptor,
    CodeSemanticMaterializationInputDescriptor,
    CodeSemanticMaterializationPackageOutputDescriptor,
    CodeSemanticMaterializationRuntimeContextDescriptor,
    CodeSemanticMaterializationRuntimeDescriptor,
    CodeSemanticPackageRoleDescriptor,
    CodeSemanticProviderBinding,
    CodeSemanticRuntimeProjectionPackageDescriptor,
    CodeSemanticSyntaxLaneDescriptor,
    CodeSemanticWorkflowDescriptor,
    CodeSemanticWorkflowInstructionDescriptor,
)
from aware_types import JsonObject, JsonValue


def code_semantic_contract_from_module_contract(
    contract: ModuleSemanticContract,
) -> CodeSemanticContract:
    """Adapt runtime provider contract truth into the API-owned DTO."""

    return CodeSemanticContract(
        provider_key=contract.provider_key,
        semantic_scope_keys=list(contract.semantic_scope_keys),
        capability_participation=[
            CodeCapabilityParticipationDescriptor(
                capability=item.capability,
                semantic_owner=item.semantic_owner,
                metadata=_json_object_or_none(item.metadata),
            )
            for item in contract.capability_participation
        ],
        capability_execution_policy=[
            CodeCapabilityExecutionPolicyDescriptor(
                capability=item.capability,
                semantic_owner=item.semantic_owner,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required_semantic_scope_keys=list(item.required_semantic_scope_keys),
                priority=item.priority,
                applies_when=item.applies_when,
            )
            for item in contract.capability_execution_policy
        ],
        capability_profiles=[
            CodeCapabilityProfileDescriptor(
                capability=item.capability,
                name=item.name,
                semantic_owners=list(item.semantic_owners),
                metadata=_json_object_or_none(item.metadata),
            )
            for item in contract.capability_profiles
        ],
        capability_bundles=[
            CodeCapabilityBundleDescriptor(
                capability=item.capability,
                name=item.name,
                capabilities=list(item.profile_names),
                semantic_owners=[],
                metadata=_json_object_or_none(item.metadata),
            )
            for item in contract.capability_bundles
        ],
        syntax_lanes=[
            CodeSemanticSyntaxLaneDescriptor(
                lane_key=item.lane_key,
                semantic_owner=item.semantic_owner,
                compiler_owner=item.compiler_owner,
                grammar_rules=list(item.grammar_rules),
                semantic_token_types=list(item.semantic_token_types),
                semantic_token_modifiers=list(item.semantic_token_modifiers),
            )
            for item in contract.syntax_lanes
        ],
        grammar_rule_declarations=[
            CodeSemanticGrammarRuleDescriptor(
                semantic_owner=item.semantic_owner,
                rule_name=item.rule_name,
                language=item.language,
                grammar_backend=item.grammar_backend,
                top_level=item.top_level,
                section_type=item.section_type,
                fields=[
                    CodeSemanticGrammarRuleFieldDescriptor(
                        field_path=field.field_path,
                        field_role=field.field_role,
                        value_kind=field.value_kind,
                        required=field.required,
                        child_rule_refs=list(field.child_rule_refs),
                        token_literals=list(field.token_literals),
                        provider_payload=_json_object_or_none(field.provider_payload),
                    )
                    for field in item.fields
                ],
                child_rule_refs=list(item.child_rule_refs),
                literal_tokens=list(item.literal_tokens),
                source_anchor_fields=list(item.source_anchor_fields),
                generation_status=item.generation_status,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.grammar_rule_declarations
        ],
        package_roles=[
            CodeSemanticPackageRoleDescriptor(
                role=item.role,
                contract=item.contract,
                package_kind=item.package_kind,
                capabilities=list(item.capabilities),
                owns_manifest_kinds=list(item.owns_manifest_kinds),
            )
            for item in contract.package_roles
        ],
        semantic_workflows=[
            CodeSemanticWorkflowDescriptor(
                workflow_key=item.workflow_key,
                semantic_owner=item.semantic_owner,
                stage_keys=list(item.stage_keys),
                instructions=[
                    CodeSemanticWorkflowInstructionDescriptor(
                        instruction_key=instruction.instruction_key,
                        title=instruction.title,
                        body=instruction.body,
                        instruction_kind=instruction.instruction_kind,
                        audience=instruction.audience,
                        stage_keys=list(instruction.stage_keys),
                        required=instruction.required,
                        source_refs=list(instruction.source_refs),
                        metadata=_json_object_or_none(instruction.metadata),
                    )
                    for instruction in item.instructions
                ],
                description=item.description,
                instruction_refs=list(item.instruction_refs),
                capability_refs=list(item.capability_refs),
                capability_profile_refs=list(item.capability_profile_refs),
                grammar_profile_refs=list(item.grammar_profile_refs),
                source_meaning_refs=list(item.source_meaning_refs),
                ontology_feature_refs=list(item.ontology_feature_refs),
                graph_binding_refs=list(item.graph_binding_refs),
                expected_artifact_refs=list(item.expected_artifact_refs),
                expected_proof_refs=list(item.expected_proof_refs),
                expected_receipt_refs=list(item.expected_receipt_refs),
                diagnostic_refs=list(item.diagnostic_refs),
                policy_refs=list(item.policy_refs),
                required=item.required,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.semantic_workflows
        ],
        artifact_leaf_ownership=[
            CodeSemanticArtifactLeafOwnershipDescriptor(
                semantic_owner=item.semantic_owner,
                owner_manifest_kinds=list(item.owner_manifest_kinds),
                artifact_manifest_kinds=list(item.artifact_manifest_kinds),
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                priority=item.priority,
                ownership_role=item.ownership_role,
            )
            for item in contract.artifact_leaf_ownership
        ],
        materialization_artifact_outputs=[
            CodeSemanticMaterializationArtifactOutputDescriptor(
                semantic_owner=item.semantic_owner,
                producer_key=item.producer_key,
                output_key=item.output_key,
                artifact_family=item.artifact_family,
                producer_provider_key=getattr(item, "producer_provider_key", None),
                artifact_role=item.artifact_role,
                output_kind=item.output_kind,
                package_output_key=item.package_output_key,
                artifact_relpath=item.artifact_relpath,
                artifact_path_pattern=item.artifact_path_pattern,
                manifest_relpath=item.manifest_relpath,
                media_type=item.media_type,
                runtime_contract_version=item.runtime_contract_version,
                required_for=list(item.required_for),
                required=item.required,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.materialization_artifact_outputs
        ],
        materialization_code_package_delta_outputs=[
            CodeSemanticMaterializationCodePackageDeltaOutputDescriptor(
                semantic_owner=item.semantic_owner,
                producer_key=item.producer_key,
                output_key=item.output_key,
                producer_provider_key=item.producer_provider_key,
                authority_kind=item.authority_kind,
                package_output_key=item.package_output_key,
                runtime_contract_version=item.runtime_contract_version,
                required_for=list(item.required_for),
                required=item.required,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.materialization_code_package_delta_outputs
        ],
        materialization_inputs=[
            CodeSemanticMaterializationInputDescriptor(
                semantic_owner=item.semantic_owner,
                input_key=item.input_key,
                input_kind=item.input_kind,
                artifact_family=item.artifact_family,
                artifact_role=item.artifact_role,
                package_family=item.package_family,
                semantic_kind=item.semantic_kind,
                runtime_contract_version=item.runtime_contract_version,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required=item.required,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.materialization_inputs
        ],
        materialization_package_outputs=[
            CodeSemanticMaterializationPackageOutputDescriptor(
                semantic_owner=item.semantic_owner,
                producer_key=item.producer_key,
                output_key=item.output_key,
                target_provider_key=item.target_provider_key,
                target_input_key=item.target_input_key,
                target_semantic_owner=item.target_semantic_owner,
                target_package_family=item.target_package_family,
                target_semantic_kind=item.target_semantic_kind,
                input_artifact_producer_key=item.input_artifact_producer_key,
                input_artifact_output_key=item.input_artifact_output_key,
                input_artifact_family=item.input_artifact_family,
                runtime_contract_version=item.runtime_contract_version,
                required_for=list(item.required_for),
                required=item.required,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.materialization_package_outputs
        ],
        materialization_runtime=[
            CodeSemanticMaterializationRuntimeDescriptor(
                semantic_owner=item.semantic_owner,
                runtime_ontology_package_names=list(
                    item.runtime_ontology_package_names
                ),
                lane_projection_name=item.lane_projection_name,
                required_projection_names=list(item.required_projection_names),
                runtime_projection_packages=[
                    CodeSemanticRuntimeProjectionPackageDescriptor(
                        package_name=runtime_package.package_name,
                        projection_names=list(runtime_package.projection_names),
                    )
                    for runtime_package in item.runtime_projection_packages
                ],
                environment_handle=item.environment_handle,
                include_package_dependency_closure=item.include_package_dependency_closure,
                priority=item.priority,
            )
            for item in contract.materialization_runtime
        ],
        materialization_runtime_context=[
            CodeSemanticMaterializationRuntimeContextDescriptor(
                semantic_owner=item.semantic_owner,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required=item.required,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.materialization_runtime_context
        ],
        materialization_execution_context=[
            CodeSemanticMaterializationExecutionContextDescriptor(
                semantic_owner=item.semantic_owner,
                context_key=item.context_key,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required=item.required,
                priority=item.priority,
                provider_payload=_json_object_or_none(item.provider_payload),
            )
            for item in contract.materialization_execution_context
        ],
        manifest_resolution=[
            CodeSemanticManifestResolutionDescriptor(
                semantic_owner=item.semantic_owner,
                manifest_kind=item.manifest_kind,
                filename=item.filename,
                contract=item.contract,
                loader_module=item.loader_module,
                loader_name=item.loader_name,
                workspace_manifest_kind=item.workspace_manifest_kind,
                package_role=item.package_role,
                semantic_package_family=item.semantic_package_family,
                semantic_package_kind=item.semantic_package_kind,
                semantic_projection_name=item.semantic_projection_name,
                semantic_root_kind=item.semantic_root_kind,
                code_package_surface=item.code_package_surface,
                code_package_surface_by_package_kind=_json_object_or_none(
                    item.code_package_surface_by_package_kind
                ),
                workspace_materialization_order=item.workspace_materialization_order,
                workspace_materialization_branch=item.workspace_materialization_branch,
                workspace_materialization_commit=item.workspace_materialization_commit,
                workspace_materialization_primary=(
                    item.workspace_materialization_primary
                ),
                copy_code_package_metadata_keys=list(
                    item.copy_code_package_metadata_keys
                ),
                semantic_package_metadata=_json_object_or_none(
                    item.semantic_package_metadata
                ),
                priority=item.priority,
            )
            for item in contract.manifest_resolution
        ],
        metadata=JsonObject({"source": "aware_code.runtime.semantic_contract"}),
    )


def module_semantic_contract_from_code_semantic_contract(
    contract: CodeSemanticContract,
) -> ModuleSemanticContract:
    """Adapt an API DTO into the current runtime-compatible contract shape."""

    diagnostics = validate_code_semantic_contract(
        contract,
        require_runtime_compatible=True,
    )
    if diagnostics:
        joined = "; ".join(diagnostics)
        raise ValueError(f"CodeSemanticContract is not runtime-compatible: {joined}")

    return ModuleSemanticContract(
        provider_key=contract.provider_key,
        semantic_scope_keys=tuple(contract.semantic_scope_keys),
        capability_participation=tuple(
            CapabilityParticipationDescriptor(
                capability=item.capability,
                semantic_owner=item.semantic_owner,
                metadata=_dict_or_empty(item.metadata),
            )
            for item in contract.capability_participation
        ),
        capability_execution_policy=tuple(
            ModuleCapabilityExecutionPolicyDescriptor(
                capability=item.capability,
                semantic_owner=item.semantic_owner,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required_semantic_scope_keys=tuple(item.required_semantic_scope_keys),
                priority=item.priority,
                applies_when=item.applies_when,
            )
            for item in contract.capability_execution_policy
        ),
        capability_profiles=tuple(
            CapabilityProfileDescriptor(
                capability=item.capability,
                name=item.name,
                semantic_owners=tuple(item.semantic_owners),
                metadata=_dict_or_empty(item.metadata),
            )
            for item in contract.capability_profiles
        ),
        capability_bundles=tuple(
            CapabilityBundleDescriptor(
                capability=item.capability,
                name=item.name,
                profile_names=tuple(item.capabilities),
                metadata=_dict_or_empty(item.metadata),
            )
            for item in contract.capability_bundles
        ),
        syntax_lanes=tuple(
            ModuleSemanticSyntaxLaneDescriptor(
                lane_key=item.lane_key,
                semantic_owner=item.semantic_owner,
                compiler_owner=item.compiler_owner,
                grammar_rules=tuple(item.grammar_rules),
                semantic_token_types=tuple(item.semantic_token_types),
                semantic_token_modifiers=tuple(item.semantic_token_modifiers),
            )
            for item in contract.syntax_lanes
        ),
        grammar_rule_declarations=tuple(
            ModuleSemanticGrammarRuleDescriptor(
                semantic_owner=item.semantic_owner,
                rule_name=item.rule_name,
                language=item.language,
                grammar_backend=item.grammar_backend,
                top_level=item.top_level,
                section_type=item.section_type,
                fields=tuple(
                    ModuleSemanticGrammarRuleFieldDescriptor(
                        field_path=field.field_path,
                        field_role=field.field_role,
                        value_kind=field.value_kind,
                        required=field.required,
                        child_rule_refs=tuple(field.child_rule_refs),
                        token_literals=tuple(field.token_literals),
                        provider_payload=_dict_or_none(field.provider_payload),
                    )
                    for field in item.fields
                ),
                child_rule_refs=tuple(item.child_rule_refs),
                literal_tokens=tuple(item.literal_tokens),
                source_anchor_fields=tuple(item.source_anchor_fields),
                generation_status=item.generation_status,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.grammar_rule_declarations
        ),
        package_roles=tuple(
            ModuleSemanticPackageRoleDescriptor(
                role=item.role,
                contract=item.contract,
                package_kind=item.package_kind,
                capabilities=tuple(item.capabilities),
                owns_manifest_kinds=tuple(item.owns_manifest_kinds),
            )
            for item in contract.package_roles
        ),
        semantic_workflows=tuple(
            ModuleSemanticWorkflowDescriptor(
                workflow_key=item.workflow_key,
                semantic_owner=item.semantic_owner,
                stage_keys=tuple(item.stage_keys),
                instructions=tuple(
                    ModuleSemanticWorkflowInstructionDescriptor(
                        instruction_key=instruction.instruction_key,
                        title=instruction.title,
                        body=instruction.body,
                        instruction_kind=instruction.instruction_kind,
                        audience=instruction.audience,
                        stage_keys=tuple(instruction.stage_keys),
                        required=instruction.required,
                        source_refs=tuple(instruction.source_refs),
                        metadata=_dict_or_none(instruction.metadata),
                    )
                    for instruction in item.instructions
                ),
                description=item.description,
                instruction_refs=tuple(item.instruction_refs),
                capability_refs=tuple(item.capability_refs),
                capability_profile_refs=tuple(item.capability_profile_refs),
                grammar_profile_refs=tuple(item.grammar_profile_refs),
                source_meaning_refs=tuple(item.source_meaning_refs),
                ontology_feature_refs=tuple(item.ontology_feature_refs),
                graph_binding_refs=tuple(item.graph_binding_refs),
                expected_artifact_refs=tuple(item.expected_artifact_refs),
                expected_proof_refs=tuple(item.expected_proof_refs),
                expected_receipt_refs=tuple(item.expected_receipt_refs),
                diagnostic_refs=tuple(item.diagnostic_refs),
                policy_refs=tuple(item.policy_refs),
                required=item.required,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.semantic_workflows
        ),
        artifact_leaf_ownership=tuple(
            ModuleSemanticArtifactLeafOwnershipDescriptor(
                semantic_owner=item.semantic_owner,
                owner_manifest_kinds=tuple(item.owner_manifest_kinds),
                artifact_manifest_kinds=tuple(item.artifact_manifest_kinds),
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                priority=item.priority,
                ownership_role=item.ownership_role,
            )
            for item in contract.artifact_leaf_ownership
        ),
        materialization_artifact_outputs=tuple(
            ModuleSemanticMaterializationArtifactOutputDescriptor(
                semantic_owner=item.semantic_owner,
                producer_key=item.producer_key,
                output_key=item.output_key,
                artifact_family=item.artifact_family,
                producer_provider_key=item.producer_provider_key,
                artifact_role=item.artifact_role,
                output_kind=item.output_kind,
                package_output_key=item.package_output_key,
                artifact_relpath=item.artifact_relpath,
                artifact_path_pattern=item.artifact_path_pattern,
                manifest_relpath=item.manifest_relpath,
                media_type=item.media_type,
                runtime_contract_version=item.runtime_contract_version,
                required_for=tuple(item.required_for),
                required=item.required,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.materialization_artifact_outputs
        ),
        materialization_code_package_delta_outputs=tuple(
            ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor(
                semantic_owner=item.semantic_owner,
                producer_key=item.producer_key,
                output_key=item.output_key,
                producer_provider_key=item.producer_provider_key,
                authority_kind=item.authority_kind,
                package_output_key=item.package_output_key,
                runtime_contract_version=item.runtime_contract_version,
                required_for=tuple(item.required_for),
                required=item.required,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.materialization_code_package_delta_outputs
        ),
        materialization_inputs=tuple(
            ModuleSemanticMaterializationInputDescriptor(
                semantic_owner=item.semantic_owner,
                input_key=item.input_key,
                input_kind=item.input_kind,
                artifact_family=item.artifact_family,
                artifact_role=item.artifact_role,
                package_family=item.package_family,
                semantic_kind=item.semantic_kind,
                runtime_contract_version=item.runtime_contract_version,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required=item.required,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.materialization_inputs
        ),
        materialization_package_outputs=tuple(
            ModuleSemanticMaterializationPackageOutputDescriptor(
                semantic_owner=item.semantic_owner,
                producer_key=item.producer_key,
                output_key=item.output_key,
                target_provider_key=item.target_provider_key,
                target_input_key=item.target_input_key,
                target_semantic_owner=item.target_semantic_owner,
                target_package_family=item.target_package_family,
                target_semantic_kind=item.target_semantic_kind,
                input_artifact_producer_key=item.input_artifact_producer_key,
                input_artifact_output_key=item.input_artifact_output_key,
                input_artifact_family=item.input_artifact_family,
                runtime_contract_version=item.runtime_contract_version,
                required_for=tuple(item.required_for),
                required=item.required,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.materialization_package_outputs
        ),
        materialization_runtime=tuple(
            ModuleSemanticMaterializationRuntimeDescriptor(
                semantic_owner=item.semantic_owner,
                runtime_ontology_package_names=tuple(
                    item.runtime_ontology_package_names
                ),
                lane_projection_name=item.lane_projection_name,
                required_projection_names=tuple(item.required_projection_names),
                runtime_projection_packages=tuple(
                    ModuleSemanticRuntimeProjectionPackageDescriptor(
                        package_name=runtime_package.package_name,
                        projection_names=tuple(runtime_package.projection_names),
                    )
                    for runtime_package in item.runtime_projection_packages
                ),
                environment_handle=item.environment_handle,
                include_package_dependency_closure=item.include_package_dependency_closure,
                priority=item.priority,
            )
            for item in contract.materialization_runtime
        ),
        materialization_runtime_context=tuple(
            ModuleSemanticMaterializationRuntimeContextDescriptor(
                semantic_owner=item.semantic_owner,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required=item.required,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.materialization_runtime_context
        ),
        materialization_execution_context=tuple(
            ModuleSemanticMaterializationExecutionContextDescriptor(
                semantic_owner=item.semantic_owner,
                context_key=item.context_key,
                callable_module=item.callable_module,
                callable_name=item.callable_name,
                required=item.required,
                priority=item.priority,
                provider_payload=_dict_or_none(item.provider_payload),
            )
            for item in contract.materialization_execution_context
        ),
        manifest_resolution=tuple(
            ModuleSemanticManifestResolutionDescriptor(
                semantic_owner=item.semantic_owner,
                manifest_kind=item.manifest_kind,
                filename=item.filename,
                contract=item.contract,
                loader_module=item.loader_module,
                loader_name=item.loader_name,
                workspace_manifest_kind=item.workspace_manifest_kind,
                package_role=item.package_role,
                semantic_package_family=item.semantic_package_family,
                semantic_package_kind=item.semantic_package_kind,
                semantic_projection_name=item.semantic_projection_name,
                semantic_root_kind=item.semantic_root_kind,
                code_package_surface=item.code_package_surface,
                code_package_surface_by_package_kind=_string_dict_or_none(
                    item.code_package_surface_by_package_kind
                ),
                workspace_materialization_order=item.workspace_materialization_order,
                workspace_materialization_branch=item.workspace_materialization_branch,
                workspace_materialization_commit=item.workspace_materialization_commit,
                workspace_materialization_primary=(
                    item.workspace_materialization_primary
                ),
                copy_code_package_metadata_keys=tuple(
                    item.copy_code_package_metadata_keys
                ),
                semantic_package_metadata=_dict_or_none(item.semantic_package_metadata),
                priority=item.priority,
            )
            for item in contract.manifest_resolution
        ),
    )


def normalize_code_semantic_contract(
    contract: CodeSemanticContract,
) -> CodeSemanticContract:
    return CodeSemanticContract.model_validate(contract.model_dump(mode="json"))


def code_semantic_provider_binding_from_module_contract(
    contract: ModuleSemanticContract,
    *,
    package_name: str | None = None,
    package_fqn: str | None = None,
    provider_name: str = "Aware Code Runtime",
    provider_module: str = "aware_code.semantic_contract",
    manifest_relative_path: str = "workspaces/aware_kernel/modules/code/ontology/runtime/python/aware_code/semantic_contract.py",
) -> CodeSemanticProviderBinding:
    return CodeSemanticProviderBinding(
        provider_key=contract.provider_key,
        provider_role="runtime_semantic_contract",
        provider_name=provider_name,
        provider_module=provider_module,
        package_fqn=package_fqn or package_name,
        manifest_kind="code_semantic_contract",
        manifest_relative_path=manifest_relative_path,
        semantic_package_metadata=JsonObject(
            {"contract_source": "AWARE_CODE_SEMANTIC_CONTRACT"}
        ),
    )


def validate_code_semantic_contract(
    contract: CodeSemanticContract,
    *,
    require_runtime_compatible: bool = False,
) -> list[str]:
    diagnostics: list[str] = []
    if not contract.provider_key.strip():
        diagnostics.append("provider_key is required.")

    diagnostics.extend(
        _required_text_sequence_diagnostics(
            "semantic_scope_keys",
            contract.semantic_scope_keys,
        )
    )
    diagnostics.extend(_validate_capability_participation(contract))
    diagnostics.extend(_validate_capability_execution_policy(contract))
    diagnostics.extend(_validate_capability_profiles(contract))
    diagnostics.extend(
        _validate_capability_bundles(
            contract,
            require_runtime_compatible=require_runtime_compatible,
        )
    )
    diagnostics.extend(_validate_syntax_lanes(contract))
    diagnostics.extend(_validate_grammar_rule_declarations(contract))
    diagnostics.extend(_validate_package_roles(contract))
    diagnostics.extend(_validate_semantic_workflows(contract))
    diagnostics.extend(_validate_artifact_leaf_ownership(contract))
    diagnostics.extend(_validate_materialization_inputs(contract))
    diagnostics.extend(_validate_materialization_artifact_outputs(contract))
    diagnostics.extend(_validate_materialization_code_package_delta_outputs(contract))
    diagnostics.extend(_validate_materialization_package_outputs(contract))
    diagnostics.extend(_validate_materialization_runtime(contract))
    diagnostics.extend(_validate_materialization_runtime_context(contract))
    diagnostics.extend(_validate_materialization_execution_context(contract))
    diagnostics.extend(_validate_manifest_resolution(contract))
    return diagnostics


def _validate_capability_participation(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contract.capability_participation):
        diagnostics.extend(
            _required_text_fields(
                f"capability_participation[{index}]",
                {
                    "capability": item.capability,
                    "semantic_owner": item.semantic_owner,
                },
            )
        )
        key = (item.capability, item.semantic_owner)
        if key in seen:
            diagnostics.append(
                f"duplicate capability participation: {item.capability}/{item.semantic_owner}"
            )
        seen.add(key)
    return diagnostics


def _validate_capability_execution_policy(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str, str | None, str | None]] = set()
    for index, item in enumerate(contract.capability_execution_policy):
        diagnostics.extend(
            _required_text_fields(
                f"capability_execution_policy[{index}]",
                {
                    "capability": item.capability,
                    "semantic_owner": item.semantic_owner,
                    "applies_when": item.applies_when,
                },
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"capability_execution_policy[{index}].required_semantic_scope_keys",
                item.required_semantic_scope_keys,
            )
        )
        key = (
            item.capability,
            item.semantic_owner,
            item.callable_module,
            item.callable_name,
        )
        if key in seen:
            diagnostics.append(
                "duplicate capability execution policy: "
                f"{item.capability}/{item.semantic_owner}/"
                f"{item.callable_module or ''}/{item.callable_name or ''}"
            )
        seen.add(key)
    return diagnostics


def _validate_capability_profiles(contract: CodeSemanticContract) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contract.capability_profiles):
        diagnostics.extend(
            _required_text_fields(
                f"capability_profiles[{index}]",
                {"capability": item.capability, "name": item.name},
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"capability_profiles[{index}].semantic_owners",
                item.semantic_owners,
            )
        )
        key = (item.capability, item.name)
        if key in seen:
            diagnostics.append(
                f"duplicate capability profile: {item.capability}/{item.name}"
            )
        seen.add(key)
    return diagnostics


def _validate_capability_bundles(
    contract: CodeSemanticContract,
    *,
    require_runtime_compatible: bool,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contract.capability_bundles):
        diagnostics.extend(
            _required_text_fields(
                f"capability_bundles[{index}]",
                {"capability": item.capability, "name": item.name},
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"capability_bundles[{index}].capabilities",
                item.capabilities,
            )
        )
        key = (item.capability, item.name)
        if key in seen:
            diagnostics.append(
                f"duplicate capability bundle: {item.capability}/{item.name}"
            )
        seen.add(key)
        if require_runtime_compatible and item.semantic_owners:
            diagnostics.append(
                f"capability_bundles[{index}].semantic_owners is API-only "
                "and cannot be converted to ModuleSemanticContract."
            )
    return diagnostics


def _validate_syntax_lanes(contract: CodeSemanticContract) -> list[str]:
    diagnostics: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(contract.syntax_lanes):
        diagnostics.extend(
            _required_text_fields(
                f"syntax_lanes[{index}]",
                {
                    "lane_key": item.lane_key,
                    "semantic_owner": item.semantic_owner,
                    "compiler_owner": item.compiler_owner,
                },
            )
        )
        if item.lane_key in seen:
            diagnostics.append(f"duplicate syntax lane: {item.lane_key}")
        seen.add(item.lane_key)
    return diagnostics


def _validate_grammar_rule_declarations(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contract.grammar_rule_declarations):
        prefix = f"grammar_rule_declarations[{index}]"
        diagnostics.extend(
            _required_text_fields(
                prefix,
                {
                    "semantic_owner": item.semantic_owner,
                    "rule_name": item.rule_name,
                    "language": item.language,
                    "grammar_backend": item.grammar_backend,
                    "generation_status": item.generation_status,
                },
            )
        )
        for field_index, field in enumerate(item.fields):
            field_prefix = f"{prefix}.fields[{field_index}]"
            diagnostics.extend(
                _required_text_fields(
                    field_prefix,
                    {"field_path": field.field_path},
                )
            )
            diagnostics.extend(
                _required_text_sequence_diagnostics(
                    f"{field_prefix}.child_rule_refs",
                    field.child_rule_refs,
                )
            )
            diagnostics.extend(
                _required_text_sequence_diagnostics(
                    f"{field_prefix}.token_literals",
                    field.token_literals,
                )
            )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"{prefix}.child_rule_refs",
                item.child_rule_refs,
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"{prefix}.literal_tokens",
                item.literal_tokens,
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"{prefix}.source_anchor_fields",
                item.source_anchor_fields,
            )
        )
        key = (item.semantic_owner, item.rule_name)
        if key in seen:
            diagnostics.append(
                f"duplicate grammar rule declaration: "
                f"{item.semantic_owner}/{item.rule_name}"
            )
        seen.add(key)
    return diagnostics


def _validate_package_roles(contract: CodeSemanticContract) -> list[str]:
    diagnostics: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(contract.package_roles):
        diagnostics.extend(
            _required_text_fields(
                f"package_roles[{index}]",
                {"role": item.role, "contract": item.contract},
            )
        )
        if item.role in seen:
            diagnostics.append(f"duplicate package role: {item.role}")
        seen.add(item.role)
    return diagnostics


def _validate_semantic_workflows(contract: CodeSemanticContract) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contract.semantic_workflows):
        prefix = f"semantic_workflows[{index}]"
        diagnostics.extend(
            _required_text_fields(
                prefix,
                {
                    "workflow_key": item.workflow_key,
                    "semantic_owner": item.semantic_owner,
                },
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"{prefix}.stage_keys",
                item.stage_keys,
                require_non_empty=True,
            )
        )
        if not item.instructions and not item.instruction_refs:
            diagnostics.append(
                f"{prefix} must include instructions or instruction_refs."
            )
        for instruction_index, instruction in enumerate(item.instructions):
            instruction_prefix = f"{prefix}.instructions[{instruction_index}]"
            diagnostics.extend(
                _required_text_fields(
                    instruction_prefix,
                    {
                        "instruction_key": instruction.instruction_key,
                        "title": instruction.title,
                        "body": instruction.body,
                        "instruction_kind": instruction.instruction_kind,
                        "audience": instruction.audience,
                    },
                )
            )
            diagnostics.extend(
                _required_text_sequence_diagnostics(
                    f"{instruction_prefix}.stage_keys",
                    instruction.stage_keys,
                )
            )
        key = (item.semantic_owner, item.workflow_key)
        if key in seen:
            diagnostics.append(
                f"duplicate semantic workflow: {item.semantic_owner}/{item.workflow_key}"
            )
        seen.add(key)
    return diagnostics


def _validate_artifact_leaf_ownership(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(contract.artifact_leaf_ownership):
        diagnostics.extend(
            _required_text_fields(
                f"artifact_leaf_ownership[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "callable_module": item.callable_module,
                    "callable_name": item.callable_name,
                    "ownership_role": item.ownership_role,
                },
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"artifact_leaf_ownership[{index}].owner_manifest_kinds",
                item.owner_manifest_kinds,
                require_non_empty=True,
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"artifact_leaf_ownership[{index}].artifact_manifest_kinds",
                item.artifact_manifest_kinds,
                require_non_empty=True,
            )
        )
        key = (item.semantic_owner, item.callable_module, item.callable_name)
        if key in seen:
            diagnostics.append(
                "duplicate artifact leaf ownership: "
                f"{item.semantic_owner}/{item.callable_module}/{item.callable_name}"
            )
        seen.add(key)
    return diagnostics


def _validate_materialization_inputs(contract: CodeSemanticContract) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contract.materialization_inputs):
        diagnostics.extend(
            _required_text_fields(
                f"materialization_inputs[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "input_key": item.input_key,
                    "input_kind": item.input_kind,
                },
            )
        )
        key = (item.semantic_owner, item.input_key)
        if key in seen:
            diagnostics.append(
                f"duplicate materialization input: {item.semantic_owner}/{item.input_key}"
            )
        seen.add(key)
    return diagnostics


def _validate_materialization_artifact_outputs(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(contract.materialization_artifact_outputs):
        diagnostics.extend(
            _required_text_fields(
                f"materialization_artifact_outputs[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "producer_key": item.producer_key,
                    "output_key": item.output_key,
                    "artifact_family": item.artifact_family,
                    "artifact_role": item.artifact_role,
                    "output_kind": item.output_kind,
                },
            )
        )
        key = (item.semantic_owner, item.producer_key, item.output_key)
        if key in seen:
            diagnostics.append(
                "duplicate materialization artifact output: "
                f"{item.semantic_owner}/{item.producer_key}/{item.output_key}"
            )
        seen.add(key)
    return diagnostics


def _validate_materialization_code_package_delta_outputs(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(contract.materialization_code_package_delta_outputs):
        diagnostics.extend(
            _required_text_fields(
                f"materialization_code_package_delta_outputs[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "producer_key": item.producer_key,
                    "output_key": item.output_key,
                    "authority_kind": item.authority_kind,
                },
            )
        )
        key = (item.semantic_owner, item.producer_key, item.output_key)
        if key in seen:
            diagnostics.append(
                "duplicate materialization CodePackageDelta output: "
                f"{item.semantic_owner}/{item.producer_key}/{item.output_key}"
            )
        seen.add(key)
    return diagnostics


def _validate_materialization_package_outputs(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(contract.materialization_package_outputs):
        diagnostics.extend(
            _required_text_fields(
                f"materialization_package_outputs[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "producer_key": item.producer_key,
                    "output_key": item.output_key,
                    "target_provider_key": item.target_provider_key,
                    "target_input_key": item.target_input_key,
                },
            )
        )
        key = (item.semantic_owner, item.producer_key, item.output_key)
        if key in seen:
            diagnostics.append(
                "duplicate materialization package output: "
                f"{item.semantic_owner}/{item.producer_key}/{item.output_key}"
            )
        seen.add(key)
    return diagnostics


def _validate_materialization_runtime(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(contract.materialization_runtime):
        diagnostics.extend(
            _required_text_fields(
                f"materialization_runtime[{index}]",
                {"semantic_owner": item.semantic_owner},
            )
        )
        diagnostics.extend(
            _required_text_sequence_diagnostics(
                f"materialization_runtime[{index}].runtime_ontology_package_names",
                item.runtime_ontology_package_names,
            )
        )
        for package_index, runtime_package in enumerate(
            item.runtime_projection_packages
        ):
            diagnostics.extend(
                _required_text_fields(
                    "materialization_runtime"
                    f"[{index}].runtime_projection_packages[{package_index}]",
                    {"package_name": runtime_package.package_name},
                )
            )
            diagnostics.extend(
                _required_text_sequence_diagnostics(
                    "materialization_runtime"
                    f"[{index}].runtime_projection_packages"
                    f"[{package_index}].projection_names",
                    runtime_package.projection_names,
                )
            )
        if item.semantic_owner in seen:
            diagnostics.append(
                f"duplicate materialization runtime: {item.semantic_owner}"
            )
        seen.add(item.semantic_owner)
    return diagnostics


def _validate_materialization_runtime_context(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for index, item in enumerate(contract.materialization_runtime_context):
        diagnostics.extend(
            _required_text_fields(
                f"materialization_runtime_context[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "callable_module": item.callable_module,
                    "callable_name": item.callable_name,
                },
            )
        )
        key = (item.semantic_owner, item.callable_module, item.callable_name)
        if key in seen:
            diagnostics.append(
                "duplicate materialization runtime context: "
                f"{item.semantic_owner}/{item.callable_module}/{item.callable_name}"
            )
        seen.add(key)
    return diagnostics


def _validate_materialization_execution_context(
    contract: CodeSemanticContract,
) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contract.materialization_execution_context):
        diagnostics.extend(
            _required_text_fields(
                f"materialization_execution_context[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "context_key": item.context_key,
                    "callable_module": item.callable_module,
                    "callable_name": item.callable_name,
                },
            )
        )
        key = (item.semantic_owner, item.context_key)
        if key in seen:
            diagnostics.append(
                "duplicate materialization execution context: "
                f"{item.semantic_owner}/{item.context_key}"
            )
        seen.add(key)
    return diagnostics


def _validate_manifest_resolution(contract: CodeSemanticContract) -> list[str]:
    diagnostics: list[str] = []
    seen: set[tuple[str, str, str, str | None]] = set()
    for index, item in enumerate(contract.manifest_resolution):
        diagnostics.extend(
            _required_text_fields(
                f"manifest_resolution[{index}]",
                {
                    "semantic_owner": item.semantic_owner,
                    "manifest_kind": item.manifest_kind,
                    "filename": item.filename,
                    "contract": item.contract,
                    "loader_module": item.loader_module,
                    "loader_name": item.loader_name,
                },
            )
        )
        if (
            not _has_text(item.code_package_surface)
            and not item.code_package_surface_by_package_kind
        ):
            diagnostics.append(
                f"manifest_resolution[{index}] must declare code_package_surface "
                "or code_package_surface_by_package_kind."
            )
        if (
            item.code_package_surface is not None
            and item.code_package_surface.strip()
            and normalize_code_package_surface(item.code_package_surface)
            != item.code_package_surface.strip()
        ):
            diagnostics.append(
                f"manifest_resolution[{index}].code_package_surface is not a "
                f"valid CodePackageSurface: {item.code_package_surface!r}."
            )
        diagnostics.extend(
            _validate_code_package_surface_by_package_kind(
                index=index,
                value=item.code_package_surface_by_package_kind,
            )
        )
        key = (
            item.semantic_owner,
            item.manifest_kind,
            item.filename,
            item.workspace_manifest_kind,
        )
        if key in seen:
            diagnostics.append(
                "duplicate manifest resolution: "
                f"{item.semantic_owner}/{item.manifest_kind}/"
                f"{item.filename}/{item.workspace_manifest_kind or ''}"
            )
        seen.add(key)
    return diagnostics


def _required_text_fields(
    prefix: str,
    values: Mapping[str, str | None],
) -> list[str]:
    return [
        f"{prefix}.{name} is required."
        for name, value in values.items()
        if value is None or not value.strip()
    ]


def _has_text(value: str | None) -> bool:
    return value is not None and bool(value.strip())


def _validate_code_package_surface_by_package_kind(
    *,
    index: int,
    value: Mapping[str, object] | None,
) -> list[str]:
    if value is None:
        return []
    diagnostics: list[str] = []
    for key, surface in sorted(value.items()):
        if not key.strip():
            diagnostics.append(
                "manifest_resolution"
                f"[{index}].code_package_surface_by_package_kind key is required."
            )
            continue
        if not isinstance(surface, str) or not surface.strip():
            diagnostics.append(
                "manifest_resolution"
                f"[{index}].code_package_surface_by_package_kind[{key!r}] "
                "must be a non-empty string."
            )
            continue
        if normalize_code_package_surface(surface) != surface.strip():
            diagnostics.append(
                "manifest_resolution"
                f"[{index}].code_package_surface_by_package_kind[{key!r}] "
                f"is not a valid CodePackageSurface: {surface!r}."
            )
    return diagnostics


def _required_text_sequence_diagnostics(
    prefix: str,
    values: list[str],
    *,
    require_non_empty: bool = False,
) -> list[str]:
    diagnostics: list[str] = []
    if require_non_empty and not values:
        diagnostics.append(f"{prefix} must include at least one value.")
    for index, value in enumerate(values):
        if not value.strip():
            diagnostics.append(f"{prefix}[{index}] is required.")
    return diagnostics


def _json_object_or_none(value: Mapping[str, object] | None) -> JsonObject | None:
    if value is None:
        return None
    payload = dict(value)
    if not payload:
        return None
    return JsonObject(cast(dict[str, JsonValue], payload))


def _dict_or_none(value: Mapping[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    return dict(value)


def _string_dict_or_none(
    value: Mapping[str, object] | None,
) -> dict[str, str] | None:
    if value is None:
        return None
    payload = {
        key: item
        for key, item in value.items()
        if isinstance(key, str) and isinstance(item, str)
    }
    return payload or None


def _dict_or_empty(value: Mapping[str, object] | None) -> dict[str, object]:
    if value is None:
        return {}
    return dict(value)


__all__ = [
    "code_semantic_contract_from_module_contract",
    "code_semantic_provider_binding_from_module_contract",
    "module_semantic_contract_from_code_semantic_contract",
    "normalize_code_semantic_contract",
    "validate_code_semantic_contract",
]
