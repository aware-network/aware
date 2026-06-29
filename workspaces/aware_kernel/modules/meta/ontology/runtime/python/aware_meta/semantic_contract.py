from __future__ import annotations

from collections.abc import Mapping, Sequence

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticGrammarRuleDescriptor,
    ModuleSemanticGrammarRuleFieldDescriptor,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
    ModuleSemanticMaterializationExecutionContextDescriptor,
    ModuleSemanticMaterializationInputDescriptor,
    ModuleSemanticLanguageMaterializationProfileDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
)
from aware_code.semantic_capability import SEMANTIC_ANALYSIS_CAPABILITY
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS,
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY,
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY,
    SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY,
    SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY,
    SemanticProjectionPortalPolicy,
    SemanticProjectionPortalPolicyPortal,
    SemanticProjectionPortalPolicyProjection,
    SemanticPackageMaterializationRequest,
)
from aware_code.semantic_contract import CODE_MATERIALIZATION_REQUIRED_PROJECTIONS
from aware_code.semantic_package.schemas import (
    CapabilityBundleDescriptor,
    CapabilityParticipationDescriptor,
    CapabilityProfileDescriptor,
)
from aware_meta.semantic_operation_resolution import (
    ATTRIBUTE_CONFIG_UPDATE_CLASS_FUNCTION_REF,
    ATTRIBUTE_CONFIG_UPDATE_ENUM_FUNCTION_REF,
    ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF,
    CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF,
    CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
    META_ATTRIBUTE_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION,
    META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION,
    META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
    META_FUNCTION_SIGNATURE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
    META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION,
)
from aware_meta.semantic_projection_mutation_scope import (
    META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY,
    MetaSemanticProjectionMutationScopeDescriptor,
)

META_TYPE_MIRROR_OWNER = "aware_meta.type_mirror"
META_PROVIDER_OWNER = "aware_meta.provider"
META_PROJECTION_OWNER = "aware_meta.projection"
META_DEFAULTS_OWNER = "aware_meta.defaults"
META_ANNOTATION_OWNER = "aware_meta.annotation"
META_IDENTITY_OWNER = "aware_meta.identity"
META_OBJECT_CONFIG_GRAPH_OWNER = "aware_meta.object_config_graph"
META_OBJECT_CONFIG_GRAPH_CLASS_IDENTITY_RENAME_OPERATION = (
    "aware_meta.object_config_graph.class.identity.rename"
)
META_OBJECT_CONFIG_GRAPH_ENUM_IDENTITY_RENAME_OPERATION = (
    "aware_meta.object_config_graph.enum.identity.rename"
)
META_SEMANTIC_SOURCE_MEANING_CAPABILITY = "semantic_source_meaning"
META_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    *CODE_MATERIALIZATION_REQUIRED_PROJECTIONS,
    "ObjectConfigGraphPackage",
    "ObjectConfigGraph",
    "ObjectInstanceGraphIdentity",
    "ObjectProjectionGraphIdentity",
)
META_OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_INPUT_KEY = (
    "aware_meta.object_config_graph_package_manifest"
)
META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY = (
    "aware_meta.object_config_graph.language_materialization"
)
META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY = "generated_language_files"
META_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_DELTAS_OUTPUT_KEY = (
    "generated_language_code_package_deltas"
)
META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY = "language_package"
META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY = (
    "language_materialization_lifecycle_receipt"
)
META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_FILENAME = (
    "ocg.language_materialization.lifecycle.json"
)
META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY = "ocg_language_materialization"
META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_REQUIRED_FOR = (
    "workspace_revision",
    "runtime_index",
    "environment_config",
)
META_OCG_MIGRATION_ARTIFACT_FAMILY = "ocg_migration"
META_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY = "aware_meta"
META_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY = "aware_meta.ocg_migration_artifacts.v0"
META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION = (
    "aware.meta.ocg_migration_artifacts.v0"
)
META_OCG_MIGRATION_ARTIFACT_MEDIA_TYPE = "application/vnd.aware.meta.ocg-migration+json"
META_OCG_MIGRATION_ARTIFACT_REQUIRED_FOR = (
    "workspace_revision",
    "sdk_local_state",
    "service_local_state",
)
META_OCG_MIGRATION_LANE_INDEX_OUTPUT_KEY = "ocg_migration_lane_index"
META_OCG_MIGRATION_DELTA_OUTPUT_KEY = "ocg_migration_delta"
META_OCG_MIGRATION_DIALECT_OUTPUT_KEY = "ocg_migration_dialect"
META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = (
    "storage-ontology",
    "content-ontology",
    "code-ontology",
    "history-ontology",
    "meta-ontology",
)
META_GRAPH_RUNTIME_CONTEXT_KEY = "aware_meta.graph_runtime_context"
META_OCG_GENESIS_OPERATION_FAMILY = "ocg_genesis"
META_OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PORTAL_POLICY_KEY = (
    "aware_meta.ocg_genesis.object_projection_graphs"
)
META_OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PROJECTION_NAME = "ObjectProjectionGraph"

META_SEMANTIC_SCOPE_KEYS: tuple[str, ...] = (
    META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY,
)


def _meta_ocg_delta_product_readiness_payload() -> dict[str, object]:
    from aware_meta.materialization.deltas.coverage_matrix import (
        meta_ocg_delta_product_readiness_payload,
    )

    return meta_ocg_delta_product_readiness_payload()


META_DIAGNOSTICS_OWNER_SEQUENCE = (
    META_TYPE_MIRROR_OWNER,
    META_PROJECTION_OWNER,
    META_DEFAULTS_OWNER,
    META_ANNOTATION_OWNER,
)

META_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    META_PROJECTION_OWNER,
    META_IDENTITY_OWNER,
    META_ANNOTATION_OWNER,
)

META_SEMANTIC_ANALYSIS_OWNER_SEQUENCE = (META_OBJECT_CONFIG_GRAPH_OWNER,)

META_MATERIALIZATION_OWNER_SEQUENCE = (META_OBJECT_CONFIG_GRAPH_OWNER,)

META_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in META_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT: dict[str, object] = {
    "contract_version": "aware.code.semantic-source-meaning-binding.v1",
    "provider_key": "aware_meta",
    "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
    "grammar_profile_key": "code.grammar_profile.aware_kernel",
    "supported_languages": ["aware"],
    "bindings": [
        {
            "binding_key": "aware_meta.object_config_graph.attribute.type",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "attr_def",
            "anchor_field_path": "type",
            "anchor_role": "graph_attribute_value",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "ClassConfigAttributeConfig",
            "semantic_key_template": ("meta.attribute:{class_name}.{attribute_name}"),
            "semantic_field": "type",
            "value_domain": "aware_type_descriptor",
            "event_type": "semantic_change",
            "condition_keys": ["aware_meta.object_config_graph.attribute.type.changed"],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_attribute_type",
                "coverage": "partial",
                "excluded_template_values": ["relationship_key"],
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.attribute.type:"
                            "{class_name}.{attribute_name}:update"
                        ),
                        "event_verbs": ["update"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "ClassConfigAttributeConfig",
                        "field_path": "type",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": ("ontology_semantic_operation"),
                            "preview_only": True,
                        },
                    },
                ],
                "action_bindings": [
                    {
                        "action_key_template": (
                            "aware_meta.object_config_graph.attribute.type:"
                            "{class_name}.{attribute_name}:update_primitive"
                        ),
                        "event_verbs": ["update"],
                        "action_type": "function_call",
                        "description": (
                            "Preview the ontology FunctionCall that updates an "
                            "existing primitive AttributeConfig type."
                        ),
                        "function_call_binding": {
                            "binding_key": (
                                "aware_meta.object_config_graph.attribute.type."
                                "update_primitive"
                            ),
                            "function_ref": (
                                "aware_meta_ontology.attribute.attribute_config."
                                "AttributeConfig.update_primitive"
                            ),
                            "receiver_semantic_key_template": "semantic_key",
                            "argument_bindings": {
                                "primitive_base_type": "payload.after"
                            },
                            "metadata": {
                                "preview_only": True,
                                "semantic_apply_boundary": ("ontology_function_call"),
                                "requires_baseline_object_identity": True,
                                "source": "aware_meta.semantic_contract",
                            },
                        },
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_plan": "preview",
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.attribute.default_value",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "attr_def",
            "anchor_field_path": "default",
            "anchor_role": "graph_attribute_value",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "ClassConfigAttributeConfig",
            "semantic_key_template": ("meta.attribute:{class_name}.{attribute_name}"),
            "semantic_field": "default_value",
            "value_domain": "aware_default_value",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.attribute.default_value.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_attribute_default_value",
                "coverage": "partial",
                "excluded_template_values": ["relationship_key"],
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.attribute.default_value:"
                            "{class_name}.{attribute_name}:update"
                        ),
                        "event_verbs": ["update"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "ClassConfigAttributeConfig",
                        "field_path": "default_value",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": ("ontology_semantic_operation"),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": (
                "aware_meta.object_config_graph.attribute.membership.identity_key"
            ),
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "attr_def",
            "anchor_field_path": "__node__",
            "anchor_role": "graph_attribute_membership_identity_key",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.ClassConfigAttributeConfig",
            "semantic_key_template": (
                "meta.attribute:{class_name}.{attribute_name}"
                "/membership:class_config"
            ),
            "semantic_field": "is_identity_key",
            "value_domain": "aware_attribute_membership_identity_key",
            "event_type": "semantic_change",
            "condition_keys": [
                (
                    "aware_meta.object_config_graph.attribute.membership."
                    "identity_key.changed"
                )
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_attribute_membership_identity_key",
                "coverage": "partial",
                "change_detection_template_fields": ["is_identity_key"],
                "excluded_template_values": ["relationship_key"],
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.attribute."
                            "membership.identity_key:"
                            "{class_name}.{attribute_name}:update"
                        ),
                        "event_verbs": ["update"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": (
                            "aware_meta.ClassConfigAttributeConfig"
                        ),
                        "field_path": "is_identity_key",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.attribute.identity",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "attr_def",
            "anchor_field_path": "name",
            "anchor_role": "graph_attribute_identity",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
                "subject_kind": "attribute",
                "subject_type": "aware_meta.AttributeConfig",
            },
            "semantic_subject_type": "aware_meta.AttributeConfig",
            "semantic_key_template": "meta.attribute:{class_name}.{attribute_name}",
            "semantic_field": "name",
            "value_domain": "aware_attribute_name",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.attribute.identity.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_attribute_identity",
                "coverage": "fallback",
                "include_template_values_in_payload": True,
                "excluded_template_values": ["relationship_key"],
                "identity_rename_policy": "explicit_fallback_required",
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.attribute.identity:"
                            "{class_name}.{attribute_name}:rename"
                        ),
                        "event_verbs": ["rename"],
                        "operation_family": "rename",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.AttributeConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "fallback_required": True,
                            "fallback_reason": (
                                "meta_attribute_identity_rename_requires_"
                                "explicit_replacement_policy"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.attribute.structural",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "attr_def",
            "anchor_field_path": "__node__",
            "anchor_role": "graph_attribute_definition",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.AttributeConfig",
            "semantic_key_template": "meta.attribute:{class_name}.{attribute_name}",
            "semantic_field": "definition",
            "value_domain": "aware_attribute_definition",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.attribute.structural.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_attribute_structural",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "excluded_template_values": ["relationship_key"],
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.attribute:"
                            "{class_name}.{attribute_name}:create"
                        ),
                        "event_verbs": ["upsert"],
                        "operation_family": "create",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.AttributeConfig",
                        "field_path": "definition",
                        "requires_baseline_object_identity": False,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                            "generated_materialization_intent": {
                                "intent_kind": (
                                    "meta_attribute_create_generated_materialization_intent"
                                ),
                                "contract_version": (
                                    META_ATTRIBUTE_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                                ),
                                "generated_materialization_provider_key": (
                                    "aware_meta"
                                ),
                                "renderer_key": "python.orm.attribute.field",
                                "policy_key": (
                                    "aware_meta.python_orm.attribute.create"
                                ),
                                "materialization_target": (
                                    "python_orm_attribute_field"
                                ),
                            },
                        },
                    },
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.attribute:"
                            "{class_name}.{attribute_name}:delete"
                        ),
                        "event_verbs": ["delete"],
                        "operation_family": "delete",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.AttributeConfig",
                        "field_path": "definition",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                            "generated_materialization_intent": {
                                "intent_kind": (
                                    "meta_attribute_delete_generated_materialization_intent"
                                ),
                                "contract_version": (
                                    META_ATTRIBUTE_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                                ),
                                "generated_materialization_provider_key": (
                                    "aware_meta"
                                ),
                                "renderer_key": "python.orm.attribute.field",
                                "policy_key": (
                                    "aware_meta.python_orm.attribute.delete"
                                ),
                                "materialization_target": (
                                    "python_orm_attribute_field"
                                ),
                            },
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.function.create",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "fn_def",
            "anchor_field_path": "name",
            "anchor_role": "graph_function_name",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.FunctionConfig",
            "semantic_key_template": "meta.function:{class_name}.{function_name}",
            "semantic_field": "name",
            "value_domain": "aware_function_name",
            "event_type": "semantic_change",
            "condition_keys": ["aware_meta.object_config_graph.function.created"],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_function_create",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.function:"
                            "{class_name}.{function_name}:create"
                        ),
                        "event_verbs": ["upsert"],
                        "operation_family": "create",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.FunctionConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": False,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": ("ontology_semantic_operation"),
                            "preview_only": False,
                        },
                    },
                ],
                "action_bindings": [
                    {
                        "action_key_template": (
                            "aware_meta.object_config_graph.function:"
                            "{class_name}.{function_name}:create_function_config"
                        ),
                        "event_verbs": ["upsert"],
                        "action_type": "function_call",
                        "description": (
                            "Preview the ontology FunctionCall that creates a "
                            "FunctionConfig on an existing ClassConfig."
                        ),
                        "function_call_binding": {
                            "binding_key": (
                                "aware_meta.object_config_graph.function.create"
                            ),
                            "function_ref": (
                                "aware_meta_ontology.class_.class_config."
                                "ClassConfig.create_function_config"
                            ),
                            "receiver_semantic_key_template": (
                                "meta.class:{class_name}"
                            ),
                            "argument_bindings": {
                                "name": "payload.after.name",
                                "description": ("payload.after.function_description"),
                            },
                            "constant_arguments": {
                                "kind": "instance",
                                "is_public": True,
                                "is_constructor": False,
                            },
                            "result_semantic_key_template": "semantic_key",
                            "metadata": {
                                "preview_only": False,
                                "semantic_apply_boundary": ("ontology_function_call"),
                                "requires_baseline_object_identity": True,
                                "source": "aware_meta.semantic_contract",
                            },
                        },
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_plan": "preview",
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.function.structural",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "fn_def",
            "anchor_field_path": "__node__",
            "anchor_role": "graph_function_definition",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.FunctionConfig",
            "semantic_key_template": "meta.function:{class_name}.{function_name}",
            "semantic_field": "definition",
            "value_domain": "aware_function_definition",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.function.structural.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_function_structural",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.function:"
                            "{class_name}.{function_name}:delete"
                        ),
                        "event_verbs": ["delete"],
                        "operation_family": "delete",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.FunctionConfig",
                        "field_path": "definition",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                            "generated_materialization_intent": {
                                "intent_kind": (
                                    "meta_function_delete_generated_materialization_intent"
                                ),
                                "contract_version": (
                                    META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                                ),
                                "generated_materialization_provider_key": (
                                    "aware_meta"
                                ),
                                "renderer_key": "python.orm.function",
                                "policy_key": ("aware_meta.python_orm.function.delete"),
                                "materialization_target": ("python_orm_function"),
                            },
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.class.identity",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "class_def",
            "anchor_field_path": "name",
            "anchor_role": "graph_class_identity",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
                "subject_kind": "class",
                "subject_type": "aware_meta.ClassConfig",
            },
            "semantic_subject_type": "aware_meta.ClassConfig",
            "semantic_key_template": "meta.class:{class_name}",
            "semantic_field": "name",
            "value_domain": "aware_class_name",
            "event_type": "semantic_change",
            "condition_keys": ["aware_meta.object_config_graph.class.identity.changed"],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_class_identity",
                "coverage": "fallback",
                "include_template_values_in_payload": True,
                "identity_rename_policy": "explicit_fallback_required",
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.class.identity:"
                            "{class_name}:create"
                        ),
                        "event_verbs": ["upsert"],
                        "operation_family": "create",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.ClassConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": False,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": ("ontology_semantic_operation"),
                            "preview_only": True,
                        },
                    },
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.class.identity:"
                            "{class_name}:rename"
                        ),
                        "event_verbs": ["rename"],
                        "operation_family": "rename",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_CLASS_IDENTITY_RENAME_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.ClassConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "fallback_required": True,
                            "fallback_reason": (
                                "meta_class_identity_rename_requires_explicit_policy"
                            ),
                            "preview_only": True,
                        },
                    },
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.class.identity:"
                            "{class_name}:delete"
                        ),
                        "event_verbs": ["delete"],
                        "operation_family": "delete",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.ClassConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                            "generated_materialization_intent": {
                                "intent_kind": (
                                    "meta_class_delete_generated_materialization_intent"
                                ),
                                "contract_version": (
                                    META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                                ),
                                "generated_materialization_provider_key": (
                                    "aware_meta"
                                ),
                                "renderer_key": "python.orm.class",
                                "policy_key": ("aware_meta.python_orm.class.delete"),
                                "materialization_target": "python_orm_class",
                            },
                        },
                    },
                ],
                "generated_materialization_intent": {
                    "intent_kind": "meta_class_create_generated_materialization_intent",
                    "contract_version": (
                        META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                    ),
                    "generated_materialization_provider_key": "aware_meta",
                    "renderer_key": "python.orm.class",
                    "policy_key": "aware_meta.python_orm.class.create",
                    "materialization_target": "python_orm_class",
                },
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.class.description",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "class_def",
            "anchor_field_path": "description_comment",
            "anchor_role": "graph_class_description",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.ClassConfig",
            "semantic_key_template": "meta.class:{class_name}",
            "semantic_field": "description",
            "value_domain": "aware_doc_comment",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.class.description.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_class_description",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.class.description:"
                            "{class_name}:update"
                        ),
                        "event_verbs": ["update", "upsert"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.ClassConfig",
                        "field_path": "description",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
                "generated_materialization_intent": {
                    "intent_kind": (
                        "meta_class_description_generated_materialization_intent"
                    ),
                    "contract_version": (
                        META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                    ),
                    "generated_materialization_provider_key": "aware_meta",
                },
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.function_impl.body",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "fn_def",
            "anchor_field_path": "body",
            "anchor_role": "graph_function_impl_body",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.FunctionImpl",
            "semantic_key_template": (
                "meta.function_impl:{class_name}.{function_name}:default"
            ),
            "semantic_field": "body_text",
            "value_domain": "aware_function_impl_body",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.function_impl.body.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_function_impl_body",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.function_impl.body:"
                            "{class_name}.{function_name}:update"
                        ),
                        "event_verbs": ["update", "upsert"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.FunctionImpl",
                        "field_path": "body_text",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.enum.identity",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "enum_def",
            "anchor_field_path": "name",
            "anchor_role": "graph_enum_identity",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
                "subject_kind": "enum",
                "subject_type": "aware_meta.EnumConfig",
            },
            "semantic_subject_type": "aware_meta.EnumConfig",
            "semantic_key_template": "meta.enum:{enum_name}",
            "semantic_field": "name",
            "value_domain": "aware_enum_name",
            "event_type": "semantic_change",
            "condition_keys": ["aware_meta.object_config_graph.enum.identity.changed"],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_enum_identity",
                "coverage": "fallback",
                "include_template_values_in_payload": True,
                "identity_rename_policy": "explicit_fallback_required",
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.enum.identity:"
                            "{enum_name}:create"
                        ),
                        "event_verbs": ["upsert"],
                        "operation_family": "create",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.EnumConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": False,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "fallback_required": True,
                            "preview_only": True,
                        },
                    },
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.enum.identity:"
                            "{enum_name}:rename"
                        ),
                        "event_verbs": ["rename"],
                        "operation_family": "rename",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ENUM_IDENTITY_RENAME_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.EnumConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "fallback_required": True,
                            "fallback_reason": (
                                "meta_enum_identity_rename_requires_explicit_policy"
                            ),
                            "preview_only": True,
                        },
                    },
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.enum.identity:"
                            "{enum_name}:delete"
                        ),
                        "event_verbs": ["delete"],
                        "operation_family": "delete",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.EnumConfig",
                        "field_path": "name",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "fallback_required": True,
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.enum.description",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "enum_def",
            "anchor_field_path": "description_comment",
            "anchor_role": "graph_enum_description",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.EnumConfig",
            "semantic_key_template": "meta.enum:{enum_name}",
            "semantic_field": "description",
            "value_domain": "aware_doc_comment",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.enum.description.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_enum_description",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.enum.description:"
                            "{enum_name}:update"
                        ),
                        "event_verbs": ["update", "upsert"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.EnumConfig",
                        "field_path": "description",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.enum_option.value",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "enum_value_def",
            "anchor_field_path": "name",
            "anchor_role": "graph_enum_option_value",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
                "subject_kind": "enum_option",
                "subject_type": "aware_meta.EnumOption",
            },
            "semantic_subject_type": "aware_meta.EnumOption",
            "semantic_key_template": (
                "meta.enum:{enum_name}/option:{enum_option_value}"
            ),
            "semantic_field": "value",
            "value_domain": "aware_enum_option_value",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.enum_option.value.created"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_enum_option_value",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.enum_option.value:"
                            "{enum_name}.{enum_option_value}:create"
                        ),
                        "event_verbs": ["upsert"],
                        "operation_family": "create",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.EnumOption",
                        "field_path": "value",
                        "requires_baseline_object_identity": False,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.enum_option.value:"
                            "{enum_name}.{enum_option_value}:delete"
                        ),
                        "event_verbs": ["delete"],
                        "operation_family": "delete",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.EnumOption",
                        "field_path": "value",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "fallback_required": True,
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.enum_option.position",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "enum_value_def",
            "anchor_field_path": "name",
            "anchor_role": "graph_enum_option_position",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
                "subject_kind": "enum_option",
                "subject_type": "aware_meta.EnumOption",
            },
            "semantic_subject_type": "aware_meta.EnumOption",
            "semantic_key_template": (
                "meta.enum:{enum_name}/option:{enum_option_value}"
            ),
            "semantic_field": "position",
            "value_domain": "aware_enum_option_position",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.enum_option.position.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_enum_option_position",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "change_detection_template_fields": ["position"],
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.enum_option.position:"
                            "{enum_name}.{enum_option_value}:update"
                        ),
                        "event_verbs": ["update"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.EnumOption",
                        "field_path": "position",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "fallback_required": True,
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.relationship.structural",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "attr_def",
            "anchor_field_path": "__node__",
            "anchor_role": "graph_relationship_definition",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.ClassConfigRelationship",
            "semantic_key_template": (
                "meta.relationship:{class_name}.{relationship_key}"
            ),
            "semantic_field": "definition",
            "value_domain": "aware_relationship_definition",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.relationship.structural.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_relationship_structural",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "required_template_values": [
                    "relationship_key",
                    "target_class_name",
                    "relationship_type",
                ],
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.relationship:"
                            "{class_name}.{relationship_key}:create"
                        ),
                        "event_verbs": ["upsert"],
                        "operation_family": "create",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION
                        ),
                        "semantic_subject_type": ("aware_meta.ClassConfigRelationship"),
                        "field_path": "definition",
                        "requires_baseline_object_identity": False,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                            "generated_materialization_intent": {
                                "intent_kind": (
                                    "meta_relationship_create_generated_materialization_intent"
                                ),
                                "contract_version": (
                                    META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                                ),
                                "generated_materialization_provider_key": (
                                    "aware_meta"
                                ),
                                "renderer_key": ("python.orm.relationship.load_policy"),
                                "policy_key": (
                                    "aware_meta.python_orm.relationship.create"
                                ),
                                "materialization_target": (
                                    "python_orm_relationship_field"
                                ),
                            },
                        },
                    },
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.relationship:"
                            "{class_name}.{relationship_key}:delete"
                        ),
                        "event_verbs": ["delete"],
                        "operation_family": "delete",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION
                        ),
                        "semantic_subject_type": ("aware_meta.ClassConfigRelationship"),
                        "field_path": "definition",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                            "generated_materialization_intent": {
                                "intent_kind": (
                                    "meta_relationship_delete_generated_materialization_intent"
                                ),
                                "contract_version": (
                                    META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
                                ),
                                "generated_materialization_provider_key": (
                                    "aware_meta"
                                ),
                                "renderer_key": ("python.orm.relationship.load_policy"),
                                "policy_key": (
                                    "aware_meta.python_orm.relationship.delete"
                                ),
                                "materialization_target": (
                                    "python_orm_relationship_field"
                                ),
                            },
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.relationship.load_policy",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "ann_def",
            "anchor_field_path": "args",
            "anchor_role": "graph_relationship_load_policy_args",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.ClassConfigRelationship",
            "semantic_key_template": (
                "meta.relationship:{class_name}.{relationship_key}"
            ),
            "semantic_field": "load_policy_args",
            "value_domain": "aware_relationship_load_policy_args",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.relationship.load_policy.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_relationship_load_policy",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.relationship."
                            "load_policy:{class_name}.{relationship_key}:update"
                        ),
                        "event_verbs": ["update", "upsert"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": ("aware_meta.ClassConfigRelationship"),
                        "field_path": "load_policy_args",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": "aware_meta.object_config_graph.function.signature",
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "fn_def",
            "anchor_field_path": "sig",
            "anchor_role": "graph_function_signature",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.FunctionConfig",
            "semantic_key_template": "meta.function:{class_name}.{function_name}",
            "semantic_field": "signature",
            "value_domain": "aware_function_signature",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.function.signature.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_function_signature",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.function.signature:"
                            "{class_name}.{function_name}:update"
                        ),
                        "event_verbs": ["update", "upsert"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.FunctionConfig",
                        "field_path": "signature",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
        {
            "binding_key": (
                "aware_meta.object_config_graph.function.membership.constructor"
            ),
            "language": "aware",
            "grammar_profile_key": "code.grammar_profile.aware_kernel",
            "grammar_rule_name": "fn_def",
            "anchor_field_path": "verb",
            "anchor_role": "graph_function_membership_constructor",
            "graph_selector": {
                "provider_key": "aware_meta",
                "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
            },
            "semantic_subject_type": "aware_meta.FunctionConfig",
            "semantic_key_template": "meta.function:{class_name}.{function_name}",
            "semantic_field": "is_constructor",
            "value_domain": "aware_function_membership_constructor",
            "event_type": "semantic_change",
            "condition_keys": [
                "aware_meta.object_config_graph.function.membership.changed"
            ],
            "required": False,
            "metadata": {
                "meaning": "object_config_graph_function_membership_constructor",
                "coverage": "partial",
                "include_template_values_in_payload": True,
                "typed_operation_bindings": [
                    {
                        "operation_key_template": (
                            "aware_meta.object_config_graph.function.membership."
                            "constructor:{class_name}.{function_name}:update"
                        ),
                        "event_verbs": ["update", "upsert"],
                        "operation_family": "update",
                        "semantic_operation_type": (
                            META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION
                        ),
                        "semantic_subject_type": "aware_meta.FunctionConfig",
                        "field_path": "is_constructor",
                        "requires_baseline_object_identity": True,
                        "metadata": {
                            "source": "aware_meta.semantic_contract",
                            "semantic_apply_boundary": (
                                "provider_delta_ontology_operation_executor"
                            ),
                            "preview_only": True,
                        },
                    },
                ],
            },
        },
    ],
    "metadata": {
        "coverage": "partial",
        "fallback_when_no_changed_bindings": True,
        "source": "aware_meta.semantic_contract",
        "supported_meaning": [
            "object_config_graph.attribute.type",
            "object_config_graph.class.identity",
            "object_config_graph.class.description",
            "object_config_graph.enum.description",
            "object_config_graph.enum.identity",
            "object_config_graph.enum_option.position",
            "object_config_graph.enum_option.value",
            "object_config_graph.function.create",
            "object_config_graph.function.structural",
            "object_config_graph.function.signature",
            "object_config_graph.function.membership.constructor",
            "object_config_graph.function_impl.body",
            "object_config_graph.relationship.load_policy",
        ],
    },
}

META_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA: dict[str, object] = {
    "source_meaning_contract": META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT,
    "coverage": "partial",
}


def _source_meaning_binding_keys(
    contract: Mapping[str, object],
) -> tuple[str, ...]:
    return tuple(
        binding_key
        for binding in _source_meaning_bindings(contract)
        for binding_key in (_optional_text(binding.get("binding_key")),)
        if binding_key is not None
    )


def _source_meaning_semantic_operation_types(
    contract: Mapping[str, object],
) -> tuple[str, ...]:
    operation_types: list[str] = []
    for binding in _source_meaning_bindings(contract):
        metadata = binding.get("metadata")
        if not isinstance(metadata, Mapping):
            continue
        for operation_binding in _mapping_sequence(
            metadata.get("typed_operation_bindings")
        ):
            operation_type = _optional_text(
                operation_binding.get("semantic_operation_type")
            )
            if operation_type is not None:
                operation_types.append(operation_type)
    return tuple(dict.fromkeys(operation_types))


def _source_meaning_function_call_binding_refs(
    contract: Mapping[str, object],
) -> tuple[str, ...]:
    binding_refs: list[str] = []
    for action_binding in _source_meaning_action_bindings(contract):
        function_call_binding = action_binding.get("function_call_binding")
        if not isinstance(function_call_binding, Mapping):
            continue
        binding_key = _optional_text(function_call_binding.get("binding_key"))
        if binding_key is not None:
            binding_refs.append(binding_key)
    return tuple(dict.fromkeys(binding_refs))


def _source_meaning_ontology_function_refs(
    contract: Mapping[str, object],
) -> tuple[str, ...]:
    function_refs: list[str] = []
    for action_binding in _source_meaning_action_bindings(contract):
        function_call_binding = action_binding.get("function_call_binding")
        if not isinstance(function_call_binding, Mapping):
            continue
        function_ref = _optional_text(function_call_binding.get("function_ref"))
        if function_ref is not None:
            function_refs.append(function_ref)
    return tuple(dict.fromkeys(function_refs))


def _source_meaning_action_bindings(
    contract: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    action_bindings: list[Mapping[str, object]] = []
    for binding in _source_meaning_bindings(contract):
        metadata = binding.get("metadata")
        if not isinstance(metadata, Mapping):
            continue
        action_bindings.extend(_mapping_sequence(metadata.get("action_bindings")))
    return tuple(action_bindings)


def _source_meaning_bindings(
    contract: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    return _mapping_sequence(contract.get("bindings"))


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _optional_text(value: object) -> str | None:
    text = value.strip() if isinstance(value, str) else ""
    return text or None


META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES = (
    _source_meaning_semantic_operation_types(
        META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT
    )
)
META_OBJECT_CONFIG_GRAPH_FUNCTION_CALL_BINDING_REFS = (
    _source_meaning_function_call_binding_refs(
        META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT
    )
)
META_OBJECT_CONFIG_GRAPH_ONTOLOGY_FUNCTION_REFS = (
    _source_meaning_ontology_function_refs(
        META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT
    )
)
META_OBJECT_CONFIG_GRAPH_SOURCE_BINDING_REFS = _source_meaning_binding_keys(
    META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT
)
META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES = (
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
)
META_OBJECT_CONFIG_GRAPH_GENERATED_MATERIALIZATION_INTENT_REFS = (
    META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ATTRIBUTE_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_FUNCTION_SIGNATURE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
    META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
)
META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE = (
    MetaSemanticProjectionMutationScopeDescriptor(
        scope_key=META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY,
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        projection_name="ObjectConfigGraphPackage",
        projection_refs=(
            "ObjectConfigGraphPackage",
            "ObjectConfigGraph",
            "ObjectProjectionGraph",
            "ObjectProjectionGraphIdentity",
            "ObjectInstanceGraph",
            "ObjectInstanceGraphIdentity",
        ),
        projection_node_refs=(
            "ObjectProjectionGraphNode",
            "ObjectProjectionGraphEdge",
            "ObjectProjectionGraphRelationship",
            "ObjectProjectionGraphConstructor",
        ),
        projection_node_key_refs=("ObjectProjectionGraphNodeKey",),
        object_graph_refs=(
            "ObjectConfigGraph",
            "ObjectProjectionGraph",
            "ObjectInstanceGraph",
        ),
        operation_family_refs=(
            "create",
            "delete",
            "rename",
            "update",
            META_OCG_GENESIS_OPERATION_FAMILY,
        ),
        semantic_operation_type_refs=META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES,
        function_call_binding_refs=META_OBJECT_CONFIG_GRAPH_FUNCTION_CALL_BINDING_REFS,
        ontology_function_refs=(
            *META_OBJECT_CONFIG_GRAPH_ONTOLOGY_FUNCTION_REFS,
            ATTRIBUTE_CONFIG_UPDATE_PRIMITIVE_FUNCTION_REF,
            ATTRIBUTE_CONFIG_UPDATE_ENUM_FUNCTION_REF,
            ATTRIBUTE_CONFIG_UPDATE_CLASS_FUNCTION_REF,
            CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF,
            CLASS_CONFIG_UPDATE_CONFIG_FUNCTION_REF,
        ),
        source_binding_refs=META_OBJECT_CONFIG_GRAPH_SOURCE_BINDING_REFS,
        generated_materialization_intent_refs=(
            META_OBJECT_CONFIG_GRAPH_GENERATED_MATERIALIZATION_INTENT_REFS
        ),
        expected_proof_refs=(
            "meta.function_call.plan_preview",
            "meta.function_call.execution_result",
            "meta.provider_delta.ontology_mutation_proof",
            "meta.provider_delta.semantic_scope_closure",
        ),
        expected_receipt_refs=(
            "provider_delta_typed_operation_plan",
            "provider_delta_ontology_execution_plan",
            "provider_delta_oig_commit_receipt",
            "provider_delta_head_move_applied_receipt",
        ),
        package_selectors={
            "manifest_kind": "aware_toml",
            "package_kind": "ontology",
            "semantic_kind": "object_config_graph_package",
        },
        provider_payload={
            "source": "aware_meta.semantic_contract",
            "owner": "meta",
            "closure_truth": "ontology_projection_nodes",
            "execution_boundary": "ontology_function_call",
            "supported_function_call_operation_types": (
                META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES
            ),
        },
    )
)
META_SEMANTIC_PROJECTION_MUTATION_SCOPES = (
    META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE,
)
META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS = tuple(
    scope.evidence_payload() for scope in META_SEMANTIC_PROJECTION_MUTATION_SCOPES
)
META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA: dict[
    str,
    object,
] = {
    "contract_version": (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
    ),
    "callable_module": "aware_meta.semantic_operation_resolution",
    "callable_name": "resolve_meta_semantic_operation_function_call_plan_previews",
    "supported_semantic_operation_types": (
        META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES
    ),
    "semantic_operation_type_refs": META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY: (
        META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS
    ),
    "semantic_apply_boundary": "ontology_function_call",
    "mutates": False,
    "execution_status": "not_requested",
    "provider_contract": (
        "Meta owns ObjectConfigGraph semantic operation FunctionCall "
        "resolution. Consumers may reach this through the Ontology provider "
        "bridge, but OCG operation vocabulary and FunctionCall refs are "
        "Meta-owned."
    ),
}

META_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability=META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        metadata=META_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA,
    ),
)
META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability=META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        metadata=META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
    ),
)

META_OCG_GENESIS_PROJECTION_PORTAL_POLICY: dict[str, object] = (
    SemanticProjectionPortalPolicy(
        provider_key="aware_meta",
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        operation_family=META_OCG_GENESIS_OPERATION_FAMILY,
        primary_projection="ObjectConfigGraphPackage",
        projections=(
            SemanticProjectionPortalPolicyProjection(
                projection_name="ObjectConfigGraphPackage",
                participation="required",
            ),
            SemanticProjectionPortalPolicyProjection(
                projection_name="ObjectConfigGraph",
                participation="required",
            ),
            SemanticProjectionPortalPolicyProjection(
                projection_name=(
                    META_OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PROJECTION_NAME
                ),
                participation="created_in_plan",
            ),
        ),
        portals=(
            SemanticProjectionPortalPolicyPortal(
                policy_key=(META_OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PORTAL_POLICY_KEY),
                source_projection="ObjectConfigGraph",
                source_path="ObjectConfigGraph.object_projection_graphs",
                target_projection=(
                    META_OCG_GENESIS_OBJECT_PROJECTION_GRAPH_PROJECTION_NAME
                ),
                hydration="created_in_plan",
                operation_scope=(META_OCG_GENESIS_OPERATION_FAMILY,),
            ),
        ),
        metadata={
            "source": "aware_meta.semantic_contract",
            "purpose": "empty_lane_ocg_genesis",
        },
    ).model_dump(mode="json")
)

META_MATERIALIZATION_DELTA_ADAPTER_METADATA: dict[str, object] = {
    "callable_module": "aware_meta.materialization.workspace_provider",
    "callable_name": SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY: True,
    "request_contract_version": (
        "aware.workspace.semantic-materialization.provider-delta-request.v1"
    ),
    "result_contract_version": (
        "aware.workspace.semantic-materialization.provider-delta-result.v1"
    ),
    SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY: (
        "ObjectConfigGraphPackage"
    ),
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY: (
        _meta_ocg_delta_product_readiness_payload()
    ),
    "semantic_projection_portal_policy": (META_OCG_GENESIS_PROJECTION_PORTAL_POLICY),
    "semantic_projection_portal_policies": (META_OCG_GENESIS_PROJECTION_PORTAL_POLICY,),
    "semantic_projection_mutation_scope_keys": META_SEMANTIC_SCOPE_KEYS,
    META_SEMANTIC_PROJECTION_MUTATION_SCOPES_METADATA_KEY: (
        META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS
    ),
    SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY: (
        {
            "context_key": META_GRAPH_RUNTIME_CONTEXT_KEY,
            "callable_module": "aware_meta.runtime.graph_context",
            "callable_name": (
                "build_meta_graph_runtime_context_for_semantic_materialization"
            ),
            "required": False,
            "provider_payload": {
                "contract": (
                    "Meta-owned OCG/OPG runtime context for provider-delta "
                    "materialization"
                ),
            },
        },
    ),
}
META_MATERIALIZATION_CAPABILITY_METADATA: dict[str, object] = {
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: (
        META_MATERIALIZATION_DELTA_ADAPTER_METADATA
    ),
}

META_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        metadata=META_MATERIALIZATION_CAPABILITY_METADATA,
    )
    for semantic_owner in META_MATERIALIZATION_OWNER_SEQUENCE
)

META_DIAGNOSTICS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in META_DIAGNOSTICS_OWNER_SEQUENCE
)

META_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in META_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

META_CAPABILITY_PARTICIPATION = (
    *META_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION,
    *META_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION,
    *META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
    *META_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    *META_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    *META_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)

_META_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER = {
    META_OBJECT_CONFIG_GRAPH_OWNER: 15,
}

_META_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER = {
    META_OBJECT_CONFIG_GRAPH_OWNER: "_meta_object_config_graph_analysis_provider",
}

_META_MATERIALIZATION_PRIORITY_BY_OWNER = {
    META_OBJECT_CONFIG_GRAPH_OWNER: 15,
}

_META_MATERIALIZATION_CALLABLE_NAME_BY_OWNER = {
    META_OBJECT_CONFIG_GRAPH_OWNER: "_meta_object_config_graph_materialize_provider",
}

_META_DIAGNOSTICS_PRIORITY_BY_OWNER = {
    META_TYPE_MIRROR_OWNER: 10,
    META_PROJECTION_OWNER: 20,
    META_DEFAULTS_OWNER: 90,
    META_ANNOTATION_OWNER: 100,
}

_META_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER = {
    META_TYPE_MIRROR_OWNER: "_type_mirror_provider",
    META_PROJECTION_OWNER: "_projection_provider",
    META_DEFAULTS_OWNER: "_defaults_provider",
    META_ANNOTATION_OWNER: "_annotations_provider",
}

_META_SEMANTIC_TOKENS_PRIORITY_BY_OWNER = {
    META_PROJECTION_OWNER: 20,
    META_IDENTITY_OWNER: 120,
    META_ANNOTATION_OWNER: 140,
}

_META_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER = {
    META_PROJECTION_OWNER: "_meta_projection_tokens_provider",
    META_IDENTITY_OWNER: "_meta_identity_tokens_provider",
    META_ANNOTATION_OWNER: "_annotation_path_tokens_provider",
}

META_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
        callable_name=_META_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=META_SEMANTIC_SCOPE_KEYS,
        priority=_META_DIAGNOSTICS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in META_DIAGNOSTICS_OWNER_SEQUENCE
)

META_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
        callable_name=_META_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        priority=_META_SEMANTIC_TOKENS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in META_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

META_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_name=_META_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=META_SEMANTIC_SCOPE_KEYS,
        priority=_META_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in META_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

META_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_name=_META_MATERIALIZATION_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=META_SEMANTIC_SCOPE_KEYS,
        priority=_META_MATERIALIZATION_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in META_MATERIALIZATION_OWNER_SEQUENCE
)

META_CAPABILITY_EXECUTION_POLICY = (
    *META_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY,
    *META_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    *META_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY,
    *META_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY,
)

_META_DIAGNOSTICS_PROFILE_OWNERS = (
    ("module.aware_meta.annotation", (META_ANNOTATION_OWNER,)),
    ("module.aware_meta.defaults", (META_DEFAULTS_OWNER,)),
    ("module.aware_meta.projection", (META_PROJECTION_OWNER,)),
    ("module.aware_meta.type_mirror", (META_TYPE_MIRROR_OWNER,)),
)

_META_SEMANTIC_TOKENS_PROFILE_OWNERS = (
    ("module.aware_meta.annotation", (META_ANNOTATION_OWNER,)),
    ("module.aware_meta.identity", (META_IDENTITY_OWNER,)),
    ("module.aware_meta.projection", (META_PROJECTION_OWNER,)),
)

META_DIAGNOSTICS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _META_DIAGNOSTICS_PROFILE_OWNERS
)

META_SEMANTIC_TOKENS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _META_SEMANTIC_TOKENS_PROFILE_OWNERS
)

META_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_meta",
        semantic_owners=(
            META_ANNOTATION_OWNER,
            META_DEFAULTS_OWNER,
            META_PROJECTION_OWNER,
            META_TYPE_MIRROR_OWNER,
        ),
        default_selected=True,
    ),
    *META_DIAGNOSTICS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_meta",
        semantic_owners=(
            META_ANNOTATION_OWNER,
            META_IDENTITY_OWNER,
            META_PROJECTION_OWNER,
        ),
        default_selected=True,
    ),
    *META_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

META_CAPABILITY_BUNDLES = (
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.authoring",
        profile_names=("module.aware_meta",),
    ),
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.projection",
        profile_names=("module.aware_meta.projection",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.authoring",
        profile_names=("module.aware_meta",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.projection",
        profile_names=("module.aware_meta.projection",),
    ),
)

META_SYNTAX_LANES = (
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_meta.type_mirror",
        semantic_owner=META_TYPE_MIRROR_OWNER,
        compiler_owner=META_TYPE_MIRROR_OWNER,
        grammar_rules=("mirror_stmt",),
        semantic_token_types=("keyword", "type"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_meta.projection",
        semantic_owner=META_PROJECTION_OWNER,
        compiler_owner=META_PROJECTION_OWNER,
        grammar_rules=(
            "projection_def",
            "projection_root",
            "projection_edge",
            "projection_view_group",
            "projection_view_def",
        ),
        semantic_token_types=("keyword", "class", "type", "property"),
        semantic_token_modifiers=("projection",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_meta.defaults",
        semantic_owner=META_DEFAULTS_OWNER,
        compiler_owner=META_DEFAULTS_OWNER,
        grammar_rules=(
            "attr_def",
            "input_attr",
            "default_value",
            "default_call",
            "json_object",
            "json_array",
            "json_pair",
        ),
        semantic_token_types=("property", "parameter", "string", "number", "keyword"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_meta.annotation",
        semantic_owner=META_ANNOTATION_OWNER,
        compiler_owner=META_ANNOTATION_OWNER,
        semantic_token_types=(
            "class",
            "enum",
            "enumMember",
            "property",
            "method",
            "keyword",
        ),
        semantic_token_modifiers=("identity",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_meta.identity",
        semantic_owner=META_IDENTITY_OWNER,
        compiler_owner=META_IDENTITY_OWNER,
        grammar_rules=("attr_def", "input_attr"),
        semantic_token_types=("keyword",),
        semantic_token_modifiers=("identity",),
    ),
)

META_GRAMMAR_RULE_DECLARATIONS = (
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        rule_name="ann_def",
        top_level=True,
        section_type="annotation",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="args",
                field_role="annotation_arguments",
                value_kind="aware_annotation_args",
            ),
        ),
        source_anchor_fields=("__node__",),
        child_rule_refs=("json_object", "json_array"),
    ),
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        rule_name="attr_def",
        top_level=False,
        section_type="attribute",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="name",
                field_role="semantic_identity",
                value_kind="identifier",
                required=True,
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="type",
                field_role="graph_attribute_value",
                value_kind="aware_type_descriptor",
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="identity_key",
                field_role="graph_attribute_membership_identity_key",
                value_kind="aware_attribute_membership_identity_key",
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="default",
                field_role="graph_attribute_value",
                value_kind="aware_default_value",
            ),
        ),
        source_anchor_fields=("__node__",),
        child_rule_refs=("default_value", "default_call"),
    ),
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        rule_name="class_def",
        top_level=True,
        section_type="class",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="name",
                field_role="semantic_identity",
                value_kind="identifier",
                required=True,
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="description_comment",
                field_role="semantic_description",
                value_kind="comment_text",
            ),
        ),
        source_anchor_fields=("__node__",),
        child_rule_refs=("ann_def", "attr_def", "edge_def", "fn_def"),
    ),
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        rule_name="enum_def",
        top_level=True,
        section_type="enum",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="name",
                field_role="semantic_identity",
                value_kind="identifier",
                required=True,
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="description_comment",
                field_role="semantic_description",
                value_kind="comment_text",
            ),
        ),
        source_anchor_fields=("__node__",),
        child_rule_refs=("ann_def", "enum_value_def"),
    ),
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        rule_name="enum_value_def",
        top_level=False,
        section_type="enum_value",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="name",
                field_role="semantic_identity",
                value_kind="identifier",
                required=True,
            ),
        ),
        source_anchor_fields=("__node__",),
    ),
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        rule_name="fn_def",
        top_level=False,
        section_type="function",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="name",
                field_role="semantic_identity",
                value_kind="identifier",
                required=True,
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="sig",
                field_role="function_signature",
                value_kind="aware_function_signature",
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="verb",
                field_role="function_membership_constructor",
                value_kind="aware_function_membership_constructor",
            ),
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="body",
                field_role="function_body",
                value_kind="aware_function_body",
            ),
        ),
        source_anchor_fields=("__node__",),
        child_rule_refs=("input_attr", "output_attr"),
    ),
)

META_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=META_PROVIDER_OWNER,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            SEMANTIC_ANALYSIS_CAPABILITY,
            META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
            META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
            "diagnostics",
            "semantic_tokens",
            SEMANTIC_MATERIALIZATION_CAPABILITY,
        ),
        owns_manifest_kinds=("aware_toml",),
    ),
)

META_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=META_PROVIDER_OWNER,
        manifest_kind="aware_toml",
        filename="aware.toml",
        contract="aware.package",
        loader_module="aware_meta.manifest.loader",
        loader_name="load_aware_toml_spec",
        workspace_manifest_kind="module_package",
        package_role=META_PROVIDER_OWNER,
        semantic_package_family="meta",
        semantic_package_kind="object_config_graph_package",
        semantic_projection_name="ObjectConfigGraphPackage",
        semantic_root_kind="object_config_graph",
        code_package_surface_by_package_kind={
            "api": "api",
            "object_config_graph_package": "structure",
            "ontology": "structure",
            "state": "structure",
        },
        semantic_package_metadata={
            "package_section_name": "package",
        },
        workspace_materialization_order=50,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=False,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        priority=50,
    ),
)

META_MATERIALIZATION_ARTIFACT_OUTPUTS = (
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        output_key=META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY,
        artifact_family=META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        artifact_role="source_code",
        output_kind="generated_file",
        artifact_path_pattern="{output_root}/**/*",
        runtime_contract_version="aware.meta.language_materialization.v1",
        required_for=(
            "workspace_revision",
            "dependency_import_resolution",
        ),
        provider_payload={
            "receipt_field": "generated_files",
            "target_language": "plugin",
        },
    ),
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        output_key=META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
        artifact_family=META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        artifact_role="package",
        output_kind="package_output",
        package_output_key=META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
        artifact_relpath=".",
        runtime_contract_version="aware.meta.language_materialization.v1",
        required_for=(
            "workspace_revision",
            "runtime_index",
            "environment_config",
            "dependency_import_resolution",
        ),
        provider_payload={
            "receipt_field": "package_outputs",
            "target_language": "plugin",
        },
    ),
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        output_key=META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        artifact_family=META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        artifact_role="lifecycle_receipt",
        output_kind="materialization_lifecycle_receipt",
        package_output_key=META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
        artifact_path_pattern="{materialization_root}/lifecycle_receipts/**/"
        + META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_FILENAME,
        media_type="application/json",
        runtime_contract_version=(
            "aware.meta.language_materialization.lifecycle_receipt.v1"
        ),
        required_for=META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_REQUIRED_FOR,
        provider_payload={
            "receipt_field": "lifecycle_receipts",
            "target_language": "plugin",
        },
    ),
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        output_key=META_OCG_MIGRATION_LANE_INDEX_OUTPUT_KEY,
        artifact_family=META_OCG_MIGRATION_ARTIFACT_FAMILY,
        producer_provider_key=META_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY,
        artifact_role="lane_index",
        output_kind="ocg_migration_lane_index",
        artifact_path_pattern="{materialization_root}/ocg_migration/**/*.json",
        media_type=META_OCG_MIGRATION_ARTIFACT_MEDIA_TYPE,
        runtime_contract_version=(META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION),
        required_for=META_OCG_MIGRATION_ARTIFACT_REQUIRED_FOR,
        provider_payload={
            "artifact_role": "lane_index",
            "migration_artifact_contract": (
                META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION
            ),
        },
    ),
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        output_key=META_OCG_MIGRATION_DELTA_OUTPUT_KEY,
        artifact_family=META_OCG_MIGRATION_ARTIFACT_FAMILY,
        producer_provider_key=META_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY,
        artifact_role="ocg_delta",
        output_kind="object_config_graph_delta",
        artifact_path_pattern="{materialization_root}/ocg_migration/**/*.json",
        media_type=META_OCG_MIGRATION_ARTIFACT_MEDIA_TYPE,
        runtime_contract_version=(META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION),
        required_for=META_OCG_MIGRATION_ARTIFACT_REQUIRED_FOR,
        provider_payload={
            "artifact_role": "ocg_delta",
            "migration_artifact_contract": (
                META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION
            ),
        },
    ),
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY,
        output_key=META_OCG_MIGRATION_DIALECT_OUTPUT_KEY,
        artifact_family=META_OCG_MIGRATION_ARTIFACT_FAMILY,
        producer_provider_key=META_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY,
        artifact_role="dialect_migration",
        output_kind="dialect_migration",
        artifact_path_pattern="{materialization_root}/ocg_migration/**/*.json",
        media_type=META_OCG_MIGRATION_ARTIFACT_MEDIA_TYPE,
        runtime_contract_version=(META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION),
        required_for=META_OCG_MIGRATION_ARTIFACT_REQUIRED_FOR,
        provider_payload={
            "artifact_role": "dialect_migration",
            "migration_artifact_contract": (
                META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION
            ),
        },
    ),
)

META_MATERIALIZATION_LANGUAGE_PROFILES = (
    ModuleSemanticLanguageMaterializationProfileDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        profile_key="aware_meta.object_config_graph.default_language_materialization",
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        artifact_family=META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        code_package_languages=("aware",),
        semantic_package_metadata_matches={
            "package_kind": (
                "interface_db",
                "ontology",
                "state",
            ),
        },
        include_sqlite_target=True,
        sqlite_renderer_profile_metadata_key="package_kind",
        sqlite_renderer_profile_by_metadata_value={
            "state": "orm_models",
        },
        required_for=("workspace_revision",),
        provider_payload={
            "contract": (
                "Meta ObjectConfigGraph packages declare default language "
                "materialization policy; Workspace evaluates this descriptor "
                "without owning package-kind branches."
            ),
        },
        priority=20,
    ),
)

META_MATERIALIZATION_CODE_PACKAGE_DELTA_OUTPUTS = (
    ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        producer_key=META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        output_key=META_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_DELTAS_OUTPUT_KEY,
        package_output_key=META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY,
        runtime_contract_version=(
            "aware.meta.language_materialization.code_package_delta.v1"
        ),
        required_for=(
            "workspace_revision",
            "local_checkout",
            "dependency_import_resolution",
        ),
        provider_payload={
            "receipt_field": "generated_code_package_deltas",
            "target_language": "plugin",
        },
    ),
)

META_MATERIALIZATION_INPUTS = (
    ModuleSemanticMaterializationInputDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        input_key=META_OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_INPUT_KEY,
        input_kind="manifest",
        artifact_family="aware_toml_manifest",
        artifact_role="manifest",
        package_family="meta",
        semantic_kind="object_config_graph_package",
        runtime_contract_version="aware.meta.object_config_graph_package_manifest.v1",
        callable_module="aware_meta.materialization.workspace_provider",
        callable_name="materialize",
        required=True,
        priority=15,
        provider_payload={
            "contract": (
                "Meta OCG package manifest input accepted for generated "
                "ObjectConfigGraph package materialization"
            ),
        },
    ),
)

META_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        runtime_ontology_package_names=(
            META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="ObjectConfigGraphPackage",
        required_projection_names=META_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="meta-ontology",
                projection_names=(
                    "ObjectConfigGraphPackage",
                    "ObjectConfigGraph",
                    "ObjectInstanceGraphIdentity",
                    "ObjectProjectionGraphIdentity",
                ),
            ),
        ),
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=False,
        priority=15,
    ),
)

META_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        callable_module="aware_meta.runtime.graph_context",
        callable_name="build_meta_workspace_materialization_runtime_context",
        required=True,
        priority=15,
        provider_payload={
            "contract": "Meta-owned Workspace semantic materialization runtime context",
            "runtime_ontology_package_names": (
                META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
            SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY: (
                SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS
            ),
        },
    ),
)

META_MATERIALIZATION_EXECUTION_CONTEXT = (
    ModuleSemanticMaterializationExecutionContextDescriptor(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
        context_key=META_GRAPH_RUNTIME_CONTEXT_KEY,
        callable_module="aware_meta.runtime.graph_context",
        callable_name="build_meta_graph_runtime_context_for_semantic_materialization",
        required=False,
        priority=15,
        provider_payload={
            "contract": "Meta-owned OCG/OPG runtime context for semantic materialization"
        },
    ),
)

AWARE_META_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_meta",
    semantic_scope_keys=META_SEMANTIC_SCOPE_KEYS,
    capability_participation=META_CAPABILITY_PARTICIPATION,
    capability_execution_policy=META_CAPABILITY_EXECUTION_POLICY,
    capability_profiles=META_CAPABILITY_PROFILES,
    capability_bundles=META_CAPABILITY_BUNDLES,
    syntax_lanes=META_SYNTAX_LANES,
    grammar_rule_declarations=META_GRAMMAR_RULE_DECLARATIONS,
    package_roles=META_PACKAGE_ROLES,
    manifest_resolution=META_MANIFEST_RESOLUTION,
    materialization_artifact_outputs=META_MATERIALIZATION_ARTIFACT_OUTPUTS,
    materialization_language_profiles=META_MATERIALIZATION_LANGUAGE_PROFILES,
    materialization_code_package_delta_outputs=(
        META_MATERIALIZATION_CODE_PACKAGE_DELTA_OUTPUTS
    ),
    materialization_inputs=META_MATERIALIZATION_INPUTS,
    materialization_runtime=META_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=META_MATERIALIZATION_RUNTIME_CONTEXT,
    materialization_execution_context=META_MATERIALIZATION_EXECUTION_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_META_SEMANTIC_CONTRACT


async def _meta_object_config_graph_materialize_provider(
    request: SemanticPackageMaterializationRequest,
) -> object:
    from aware_meta.materialization.workspace_provider import materialize

    return await materialize(request)


__all__ = [
    "AWARE_META_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "META_ANNOTATION_OWNER",
    "META_CAPABILITY_PARTICIPATION",
    "META_CAPABILITY_BUNDLES",
    "META_CAPABILITY_EXECUTION_POLICY",
    "META_CAPABILITY_PROFILES",
    "META_DEFAULTS_OWNER",
    "META_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "META_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY",
    "META_DIAGNOSTICS_CAPABILITY_PROFILES",
    "META_DIAGNOSTICS_OWNER_SEQUENCE",
    "META_IDENTITY_OWNER",
    "META_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "META_MATERIALIZATION_CAPABILITY_METADATA",
    "META_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "META_MATERIALIZATION_DELTA_ADAPTER_METADATA",
    "META_MATERIALIZATION_ARTIFACT_OUTPUTS",
    "META_MATERIALIZATION_CODE_PACKAGE_DELTA_OUTPUTS",
    "META_MATERIALIZATION_INPUTS",
    "META_MATERIALIZATION_LANGUAGE_PROFILES",
    "META_MATERIALIZATION_RUNTIME",
    "META_MATERIALIZATION_RUNTIME_CONTEXT",
    "META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "META_MATERIALIZATION_OWNER_SEQUENCE",
    "META_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "META_OBJECT_CONFIG_GRAPH_OWNER",
    "META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE",
    "META_OBJECT_CONFIG_GRAPH_PROJECTION_MUTATION_SCOPE_KEY",
    "META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT",
    "META_OBJECT_CONFIG_GRAPH_SEMANTIC_OPERATION_TYPES",
    "META_OBJECT_CONFIG_GRAPH_SUPPORTED_FUNCTION_CALL_OPERATION_TYPES",
    "META_OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_INPUT_KEY",
    "META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY",
    "META_LANGUAGE_MATERIALIZATION_CODE_PACKAGE_DELTAS_OUTPUT_KEY",
    "META_LANGUAGE_MATERIALIZATION_GENERATED_FILES_OUTPUT_KEY",
    "META_LANGUAGE_MATERIALIZATION_PACKAGE_OUTPUT_KEY",
    "META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY",
    "META_OCG_MIGRATION_ARTIFACT_FAMILY",
    "META_OCG_MIGRATION_ARTIFACT_MEDIA_TYPE",
    "META_OCG_MIGRATION_ARTIFACT_PRODUCER_KEY",
    "META_OCG_MIGRATION_ARTIFACT_PRODUCER_PROVIDER_KEY",
    "META_OCG_MIGRATION_ARTIFACT_REQUIRED_FOR",
    "META_OCG_MIGRATION_ARTIFACT_RUNTIME_CONTRACT_VERSION",
    "META_OCG_MIGRATION_DELTA_OUTPUT_KEY",
    "META_OCG_MIGRATION_DIALECT_OUTPUT_KEY",
    "META_OCG_MIGRATION_LANE_INDEX_OUTPUT_KEY",
    "META_GRAPH_RUNTIME_CONTEXT_KEY",
    "META_GRAMMAR_RULE_DECLARATIONS",
    "META_MATERIALIZATION_EXECUTION_CONTEXT",
    "META_PACKAGE_ROLES",
    "META_MANIFEST_RESOLUTION",
    "META_PROJECTION_OWNER",
    "META_PROVIDER_OWNER",
    "META_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION",
    "META_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY",
    "META_SEMANTIC_ANALYSIS_OWNER_SEQUENCE",
    "META_SEMANTIC_PROJECTION_MUTATION_SCOPE_PAYLOADS",
    "META_SEMANTIC_PROJECTION_MUTATION_SCOPES",
    "META_SEMANTIC_SCOPE_KEYS",
    "META_SEMANTIC_SOURCE_MEANING_CAPABILITY",
    "META_SEMANTIC_SOURCE_MEANING_CAPABILITY_METADATA",
    "META_SEMANTIC_SOURCE_MEANING_CAPABILITY_PARTICIPATION",
    "META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY",
    "META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA",
    "META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION",
    "META_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "META_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY",
    "META_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "META_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "META_SYNTAX_LANES",
    "META_TYPE_MIRROR_OWNER",
]
