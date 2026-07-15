from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from aware_code.package.schemas import CodePackageInfo
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS,
    SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY,
)
from aware_meta import semantic_package as meta_semantic_package
from aware_meta.semantic_contract import (
    AWARE_META_SEMANTIC_CONTRACT,
    META_OBJECT_CONFIG_GRAPH_OWNER,
    META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT,
    META_MANIFEST_RESOLUTION,
    META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
    META_PROVIDER_OWNER,
    META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
)
from aware_code_service_dto.code.features.semantic_source_meaning import (
    CodeSemanticSourceMeaningContract as DtoCodeSemanticSourceMeaningContract,
)

_NON_META_MANIFEST_KINDS = frozenset(
    {
        "aware_api_toml",
        "aware_economy_toml",
        "aware_experience_toml",
        "aware_interface_toml",
        "aware_pane_toml",
        "aware_service_toml",
    }
)


def test_meta_materialization_runtime_declares_ontology_package_dependencies() -> None:
    descriptors = AWARE_META_SEMANTIC_CONTRACT.materialization_runtime_for(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
    )

    assert len(descriptors) == 1
    assert (
        descriptors[0].runtime_ontology_package_names
        == META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert descriptors[0].include_package_dependency_closure is False


def test_meta_dialect_migrations_declare_append_only_artifact_scope() -> None:
    descriptors = {
        descriptor.output_key: descriptor
        for descriptor in AWARE_META_SEMANTIC_CONTRACT.materialization_artifact_outputs
    }

    assert descriptors["ocg_migration_dialect"].artifact_scope_policy == ("append_only")


def test_meta_object_config_graph_manifest_contract_is_public_facade() -> None:
    from aware_meta.graph.package.manifest_contract import (
        OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND,
        OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME,
        OBJECT_CONFIG_GRAPH_PACKAGE_SEMANTIC_KIND,
        object_config_graph_package_manifest_contract,
    )

    contract = object_config_graph_package_manifest_contract()

    assert contract.provider_key == AWARE_META_SEMANTIC_CONTRACT.provider_key
    assert contract.semantic_owner == META_PROVIDER_OWNER
    assert contract.manifest_kind == OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND
    assert OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND == "aware_toml"
    assert contract.filename == "aware.toml"
    assert contract.semantic_package_kind == OBJECT_CONFIG_GRAPH_PACKAGE_SEMANTIC_KIND
    assert OBJECT_CONFIG_GRAPH_PACKAGE_SEMANTIC_KIND == "object_config_graph_package"
    assert contract.semantic_projection_name == (
        OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME
    )
    assert OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME == "ObjectConfigGraphPackage"
    assert contract.code_package_surface_for_package_kind("api") == "api"
    assert contract.code_package_surface_for_package_kind("ontology") == "structure"


def test_meta_ocg_materialization_input_declares_lane_identity() -> None:
    [descriptor] = AWARE_META_SEMANTIC_CONTRACT.materialization_inputs

    assert descriptor.semantic_projection_name == "ObjectConfigGraphPackage"
    assert descriptor.semantic_root_kind == "object_config_graph"


def test_meta_generated_materialization_intent_metadata_is_shared_contract() -> None:
    from aware_meta.materialization.deltas.generated_materialization_dispatch import (
        generated_materialization_intent_target_metadata as dispatch_metadata,
    )
    from aware_meta.generated_materialization_contract import (
        generated_materialization_intent_target_metadata as shared_metadata,
    )
    from aware_meta.generated_materialization_contract import (
        ORM_RUNTIME_TARGET_PROFILE,
    )
    from aware_meta.semantic_contract import (
        generated_materialization_intent_target_metadata as semantic_metadata,
    )

    kwargs = {
        "policy_key": "aware_meta.test_policy",
        "materialization_target": "aware_meta.test_target",
    }

    expected = {
        "policy_key": "aware_meta.test_policy",
        "materialization_target": "aware_meta.test_target",
        "target_profile": ORM_RUNTIME_TARGET_PROFILE.descriptor_key,
        "renderer_profile": ORM_RUNTIME_TARGET_PROFILE.renderer_profile,
        "materialization_source": ORM_RUNTIME_TARGET_PROFILE.materialization_source,
        "product_intent": "orm_runtime",
    }
    assert shared_metadata(**kwargs) == expected
    assert semantic_metadata(**kwargs) == expected
    assert dispatch_metadata(**kwargs) == expected


def test_api_and_ontology_do_not_claim_meta_aware_toml_manifest_kind() -> None:
    from aware_api_runtime.semantic_contract import AWARE_API_SEMANTIC_CONTRACT
    from aware_ontology.semantic_contract import AWARE_ONTOLOGY_SEMANTIC_CONTRACT
    from aware_meta.graph.package.manifest_contract import (
        OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND,
    )

    api_manifest_kinds = {
        descriptor.manifest_kind
        for descriptor in AWARE_API_SEMANTIC_CONTRACT.manifest_resolution
    }
    ontology_manifest_kinds = {
        descriptor.manifest_kind
        for descriptor in AWARE_ONTOLOGY_SEMANTIC_CONTRACT.manifest_resolution
    }
    api_owned_manifest_kinds = {
        manifest_kind
        for role in AWARE_API_SEMANTIC_CONTRACT.package_roles
        for manifest_kind in role.owns_manifest_kinds
    }
    ontology_owned_manifest_kinds = {
        manifest_kind
        for role in AWARE_ONTOLOGY_SEMANTIC_CONTRACT.package_roles
        for manifest_kind in role.owns_manifest_kinds
    }

    assert OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND == "aware_toml"
    assert api_manifest_kinds == {"aware_api_toml"}
    assert ontology_manifest_kinds == {"aware_ontology_toml"}
    assert OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND not in api_owned_manifest_kinds
    assert (
        OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND not in ontology_owned_manifest_kinds
    )


def test_meta_materialization_runtime_context_payload_omits_module_ids() -> None:
    descriptors = AWARE_META_SEMANTIC_CONTRACT.materialization_runtime_context_for(
        semantic_owner=META_OBJECT_CONFIG_GRAPH_OWNER,
    )

    assert len(descriptors) == 1
    provider_payload = descriptors[0].provider_payload
    assert provider_payload is not None
    assert (
        provider_payload["runtime_ontology_package_names"]
        == META_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert (
        provider_payload[SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY]
        == SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS
    )


def test_meta_declares_generic_ocg_semantic_source_meaning_binding() -> None:
    [participation] = AWARE_META_SEMANTIC_CONTRACT.capability_participation_for(
        capability=META_SEMANTIC_SOURCE_MEANING_CAPABILITY,
    )

    assert participation.semantic_owner == META_OBJECT_CONFIG_GRAPH_OWNER
    contract_payload = participation.metadata["source_meaning_contract"]
    assert contract_payload == META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT
    contract = DtoCodeSemanticSourceMeaningContract.model_validate(contract_payload)
    assert contract.provider_key == "aware_meta"
    assert contract.semantic_owner == META_OBJECT_CONFIG_GRAPH_OWNER
    assert contract.metadata is not None
    assert contract.metadata["coverage"] == "partial"
    assert contract.metadata["fallback_when_no_changed_bindings"] is True

    bindings = {binding.binding_key: binding for binding in contract.bindings}
    binding = bindings["aware_meta.object_config_graph.attribute.type"]
    attribute_membership_binding = bindings[
        "aware_meta.object_config_graph.attribute.membership.identity_key"
    ]
    attribute_identity_binding = bindings[
        "aware_meta.object_config_graph.attribute.identity"
    ]
    function_binding = bindings["aware_meta.object_config_graph.function.create"]
    function_structural_binding = bindings[
        "aware_meta.object_config_graph.function.structural"
    ]
    enum_identity_binding = bindings["aware_meta.object_config_graph.enum.identity"]
    enum_description_binding = bindings[
        "aware_meta.object_config_graph.enum.description"
    ]
    enum_option_binding = bindings["aware_meta.object_config_graph.enum_option.value"]
    enum_option_position_binding = bindings[
        "aware_meta.object_config_graph.enum_option.position"
    ]
    function_signature_binding = bindings[
        "aware_meta.object_config_graph.function.signature"
    ]
    function_membership_constructor_binding = bindings[
        "aware_meta.object_config_graph.function.membership.constructor"
    ]
    assert binding.grammar_rule_name == "attr_def"
    assert binding.anchor_field_path == "type"
    assert binding.semantic_subject_type == "ClassConfigAttributeConfig"
    assert (
        binding.semantic_key_template == "meta.attribute:{class_name}.{attribute_name}"
    )
    assert binding.semantic_field == "type"
    assert binding.required is False
    assert binding.graph_selector.class_name is None
    assert binding.graph_selector.attribute_name is None
    assert binding.graph_selector.attribute_path is None
    assert attribute_membership_binding.grammar_rule_name == "attr_def"
    assert attribute_membership_binding.anchor_field_path == "__node__"
    assert attribute_membership_binding.anchor_role == (
        "graph_attribute_membership_identity_key"
    )
    assert attribute_membership_binding.semantic_subject_type == (
        "aware_meta.ClassConfigAttributeConfig"
    )
    assert attribute_membership_binding.semantic_key_template == (
        "meta.attribute:{class_name}.{attribute_name}/membership:class_config"
    )
    assert attribute_membership_binding.semantic_field == "is_identity_key"
    assert attribute_membership_binding.value_domain == (
        "aware_attribute_membership_identity_key"
    )
    assert attribute_membership_binding.metadata is not None
    assert attribute_membership_binding.metadata[
        "change_detection_template_fields"
    ] == ["is_identity_key"]
    attribute_membership_typed_operation_bindings = (
        attribute_membership_binding.typed_operation_bindings
    )
    [attribute_membership_typed_operation_binding] = (
        attribute_membership_typed_operation_bindings
    )
    assert attribute_membership_typed_operation_binding.semantic_operation_type == (
        "aware_meta.object_config_graph.attribute.membership.update"
    )
    assert attribute_membership_typed_operation_binding.field_path == (
        "is_identity_key"
    )
    assert attribute_identity_binding.grammar_rule_name == "attr_def"
    assert attribute_identity_binding.anchor_field_path == "name"
    assert attribute_identity_binding.anchor_role == "graph_attribute_identity"
    assert attribute_identity_binding.semantic_subject_type == (
        "aware_meta.AttributeConfig"
    )
    assert attribute_identity_binding.semantic_key_template == (
        "meta.attribute:{class_name}.{attribute_name}"
    )
    assert attribute_identity_binding.semantic_field == "name"
    assert attribute_identity_binding.value_domain == "aware_attribute_name"
    assert attribute_identity_binding.metadata is not None
    assert attribute_identity_binding.metadata["identity_rename_policy"] == (
        "explicit_fallback_required"
    )
    attribute_identity_typed_operation_bindings = (
        attribute_identity_binding.typed_operation_bindings
    )
    [attribute_identity_typed_operation_binding] = (
        attribute_identity_typed_operation_bindings
    )
    assert attribute_identity_typed_operation_binding.semantic_operation_type == (
        "aware_meta.object_config_graph.attribute.identity.rename"
    )
    assert attribute_identity_typed_operation_binding.operation_family == "rename"
    assert attribute_identity_typed_operation_binding.field_path == "name"
    assert attribute_identity_typed_operation_binding.contract_source == (
        "aware_meta.semantic_contract"
    )
    assert attribute_identity_typed_operation_binding.semantic_apply_boundary == (
        "provider_delta_ontology_operation_executor"
    )
    assert attribute_identity_typed_operation_binding.fallback_required is True
    assert attribute_identity_typed_operation_binding.fallback_reason == (
        "meta_attribute_identity_rename_requires_explicit_replacement_policy"
    )
    assert attribute_identity_typed_operation_binding.preview_only is True
    assert function_binding.grammar_rule_name == "fn_def"
    assert function_binding.anchor_field_path == "name"
    assert function_binding.semantic_subject_type == "aware_meta.FunctionConfig"
    assert (
        function_binding.semantic_key_template
        == "meta.function:{class_name}.{function_name}"
    )
    assert function_binding.semantic_field == "name"
    assert function_binding.required is False
    assert function_binding.metadata is not None
    assert function_binding.metadata["include_template_values_in_payload"] is True
    assert function_structural_binding.grammar_rule_name == "fn_def"
    assert function_structural_binding.anchor_field_path == "__node__"
    assert function_structural_binding.semantic_subject_type == (
        "aware_meta.FunctionConfig"
    )
    assert function_structural_binding.semantic_key_template == (
        "meta.function:{class_name}.{function_name}"
    )
    assert function_structural_binding.semantic_field == "definition"
    assert function_structural_binding.required is False
    assert function_structural_binding.metadata is not None
    assert (
        function_structural_binding.metadata["include_template_values_in_payload"]
        is True
    )
    function_structural_typed_operation_bindings = (
        function_structural_binding.typed_operation_bindings
    )
    [function_structural_typed_operation_binding] = (
        function_structural_typed_operation_bindings
    )
    assert function_structural_typed_operation_binding.semantic_operation_type == (
        "aware_meta.object_config_graph.function.delete"
    )
    assert function_structural_typed_operation_binding.operation_family == "delete"
    assert function_structural_typed_operation_binding.field_path == "definition"
    assert enum_identity_binding.grammar_rule_name == "enum_def"
    assert enum_identity_binding.anchor_field_path == "name"
    assert enum_identity_binding.semantic_subject_type == "aware_meta.EnumConfig"
    assert enum_identity_binding.semantic_key_template == "meta.enum:{enum_name}"
    assert enum_identity_binding.semantic_field == "name"
    assert enum_identity_binding.required is False
    assert enum_identity_binding.metadata is not None
    assert enum_identity_binding.metadata["include_template_values_in_payload"] is True
    enum_identity_typed_operation_bindings = (
        enum_identity_binding.typed_operation_bindings
    )
    assert len(enum_identity_typed_operation_bindings) >= 2
    assert enum_identity_typed_operation_bindings[0].semantic_operation_type == (
        "aware_meta.object_config_graph.enum.create"
    )
    assert enum_identity_typed_operation_bindings[0].operation_family == "create"
    assert enum_identity_typed_operation_bindings[0].field_path == "name"
    assert enum_identity_typed_operation_bindings[0].contract_source == (
        "aware_meta.semantic_contract"
    )
    assert enum_identity_typed_operation_bindings[0].semantic_apply_boundary == (
        "provider_delta_ontology_operation_executor"
    )
    assert enum_identity_typed_operation_bindings[0].fallback_required is True
    assert enum_identity_typed_operation_bindings[0].preview_only is True
    enum_delete_typed_operation_binding = next(
        item
        for item in enum_identity_typed_operation_bindings
        if item.semantic_operation_type == "aware_meta.object_config_graph.enum.delete"
    )
    assert enum_delete_typed_operation_binding.operation_family == "delete"
    assert enum_delete_typed_operation_binding.field_path == "name"
    assert enum_description_binding.grammar_rule_name == "enum_def"
    assert enum_description_binding.anchor_field_path == "description_comment"
    assert enum_description_binding.semantic_subject_type == "aware_meta.EnumConfig"
    assert enum_description_binding.semantic_key_template == "meta.enum:{enum_name}"
    assert enum_description_binding.semantic_field == "description"
    assert enum_description_binding.required is False
    assert enum_description_binding.metadata is not None
    assert (
        enum_description_binding.metadata["include_template_values_in_payload"] is True
    )
    enum_typed_operation_bindings = enum_description_binding.typed_operation_bindings
    [enum_typed_operation_binding] = enum_typed_operation_bindings
    assert enum_typed_operation_binding.semantic_operation_type == (
        "aware_meta.object_config_graph.enum.description.update"
    )
    assert enum_typed_operation_binding.field_path == "description"
    assert enum_option_binding.grammar_rule_name == "enum_value_def"
    assert enum_option_binding.anchor_field_path == "name"
    assert enum_option_binding.semantic_subject_type == "aware_meta.EnumOption"
    assert enum_option_binding.semantic_key_template == (
        "meta.enum:{enum_name}/option:{enum_option_value}"
    )
    assert enum_option_binding.semantic_field == "value"
    assert enum_option_binding.required is False
    assert enum_option_binding.metadata is not None
    assert enum_option_binding.metadata["include_template_values_in_payload"] is True
    enum_option_typed_operation_bindings = enum_option_binding.typed_operation_bindings
    assert len(enum_option_typed_operation_bindings) == 2
    assert enum_option_typed_operation_bindings[0].semantic_operation_type == (
        "aware_meta.object_config_graph.enum_option.create"
    )
    assert enum_option_typed_operation_bindings[0].operation_family == "create"
    assert enum_option_typed_operation_bindings[0].field_path == "value"
    assert enum_option_typed_operation_bindings[1].semantic_operation_type == (
        "aware_meta.object_config_graph.enum_option.delete"
    )
    assert enum_option_typed_operation_bindings[1].operation_family == "delete"
    assert enum_option_typed_operation_bindings[1].field_path == "value"
    assert enum_option_position_binding.grammar_rule_name == "enum_value_def"
    assert enum_option_position_binding.anchor_field_path == "name"
    assert enum_option_position_binding.semantic_subject_type == (
        "aware_meta.EnumOption"
    )
    assert enum_option_position_binding.semantic_field == "position"
    assert enum_option_position_binding.metadata is not None
    assert enum_option_position_binding.metadata[
        "change_detection_template_fields"
    ] == ["position"]
    enum_option_position_typed_operation_bindings = (
        enum_option_position_binding.typed_operation_bindings
    )
    [position_typed_operation_binding] = enum_option_position_typed_operation_bindings
    assert position_typed_operation_binding.semantic_operation_type == (
        "aware_meta.object_config_graph.enum_option.position.update"
    )
    assert position_typed_operation_binding.operation_family == "update"
    assert position_typed_operation_binding.field_path == "position"
    assert function_signature_binding.grammar_rule_name == "fn_def"
    assert function_signature_binding.anchor_field_path == "sig"
    assert function_signature_binding.semantic_subject_type == (
        "aware_meta.FunctionConfig"
    )
    assert function_signature_binding.semantic_key_template == (
        "meta.function:{class_name}.{function_name}"
    )
    assert function_signature_binding.semantic_field == "signature"
    assert function_signature_binding.required is False
    assert function_signature_binding.metadata is not None
    assert (
        function_signature_binding.metadata["include_template_values_in_payload"]
        is True
    )
    typed_operation_bindings = function_signature_binding.typed_operation_bindings
    [typed_operation_binding] = typed_operation_bindings
    assert typed_operation_binding.semantic_operation_type == (
        "aware_meta.object_config_graph.function.signature.update"
    )
    assert typed_operation_binding.field_path == "signature"
    assert function_membership_constructor_binding.grammar_rule_name == "fn_def"
    assert function_membership_constructor_binding.anchor_field_path == "verb"
    assert function_membership_constructor_binding.anchor_role == (
        "graph_function_membership_constructor"
    )
    assert function_membership_constructor_binding.semantic_subject_type == (
        "aware_meta.FunctionConfig"
    )
    assert function_membership_constructor_binding.semantic_field == ("is_constructor")
    assert function_membership_constructor_binding.value_domain == (
        "aware_function_membership_constructor"
    )
    assert function_membership_constructor_binding.metadata is not None
    function_membership_typed_operation_bindings = (
        function_membership_constructor_binding.typed_operation_bindings
    )
    [function_membership_typed_operation_binding] = (
        function_membership_typed_operation_bindings
    )
    assert function_membership_typed_operation_binding.semantic_operation_type == (
        "aware_meta.object_config_graph.function.signature.update"
    )
    assert function_membership_typed_operation_binding.field_path == ("is_constructor")
    assert function_membership_typed_operation_binding.contract_source == (
        "aware_meta.semantic_contract"
    )
    assert function_membership_typed_operation_binding.semantic_apply_boundary == (
        "provider_delta_ontology_operation_executor"
    )
    assert function_membership_typed_operation_binding.preview_only is True


def test_meta_signature_source_meaning_contract_resolves_code_delta() -> None:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        CodeSemanticSourceMeaningBinding as RuntimeSourceMeaningBinding,
        CodeSemanticSourceMeaningContract as RuntimeSourceMeaningContract,
        resolve_code_semantic_source_meaning,
    )
    from aware_code.source_index import (  # noqa: WPS433
        CodeGrammarGraphSelector,
    )

    raw_bindings = cast(
        Sequence[Mapping[str, object]],
        META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["bindings"],
    )
    runtime_contract = RuntimeSourceMeaningContract(
        provider_key=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["provider_key"]
        ),
        semantic_owner=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["semantic_owner"]
        ),
        grammar_profile_key=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["grammar_profile_key"]
        ),
        bindings=tuple(
            RuntimeSourceMeaningBinding(
                binding_key=str(binding["binding_key"]),
                language=str(binding["language"]),
                grammar_profile_key=str(binding["grammar_profile_key"]),
                grammar_rule_name=str(binding["grammar_rule_name"]),
                anchor_field_path=str(binding["anchor_field_path"]),
                anchor_role=cast(str | None, binding.get("anchor_role")),
                graph_selector=CodeGrammarGraphSelector(
                    **cast(
                        Mapping[str, str],
                        binding["graph_selector"],
                    )
                ),
                semantic_subject_type=str(binding["semantic_subject_type"]),
                semantic_key_template=str(binding["semantic_key_template"]),
                semantic_field=str(binding["semantic_field"]),
                value_domain=cast(str | None, binding.get("value_domain")),
                event_type=str(binding["event_type"]),
                condition_keys=tuple(
                    str(item)
                    for item in cast(
                        Sequence[object],
                        binding.get("condition_keys", ()),
                    )
                ),
                typed_operation_bindings=_runtime_typed_operation_bindings(binding),
                required=binding.get("required") is not False,
                metadata=cast(Mapping[str, object], binding.get("metadata", {})),
            )
            for binding in raw_bindings
        ),
        metadata=cast(
            Mapping[str, object],
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["metadata"],
        ),
    )
    baseline = _source_index(
        "class TvChannel {\n"
        "    name String\n"
        "    fn rename(display_name String) -> TvChannel {\n"
        "    }\n"
        "}\n"
    )
    current = _source_index(
        "class TvChannel {\n"
        "    name String\n"
        "    fn rename(label String) -> TvChannel {\n"
        "    }\n"
        "}\n"
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    signature_operations = tuple(
        operation
        for operation in resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.function.signature.update"
    )
    assert resolution.resolved is True
    assert len(signature_operations) == 1
    [operation] = signature_operations
    assert operation.semantic_key == "meta.function:TvChannel.rename"
    assert operation.semantic_subject_type == "aware_meta.FunctionConfig"
    assert operation.field_path == "signature"
    assert operation.before_payload is not None
    assert operation.after_payload is not None
    assert operation.before_payload["signature"] == (
        "(display_name String) -> TvChannel"
    )
    assert operation.after_payload["signature"] == "(label String) -> TvChannel"


def test_meta_function_source_meaning_contract_resolves_delete_delta() -> None:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        resolve_code_semantic_source_meaning,
    )

    runtime_contract = _runtime_source_meaning_contract()
    baseline = _source_index(
        "class TvChannel {\n"
        "    name String\n"
        "    fn rename(display_name String) -> TvChannel {\n"
        "    }\n"
        "}\n"
    )
    current = _source_index("class TvChannel {\n" "    name String\n" "}\n")

    resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    function_delete_operations = tuple(
        operation
        for operation in resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.function.delete"
    )
    assert resolution.resolved is True
    assert len(function_delete_operations) == 1
    [operation] = function_delete_operations
    assert operation.operation_family == "delete"
    assert operation.semantic_key == "meta.function:TvChannel.rename"
    assert operation.semantic_subject_type == "aware_meta.FunctionConfig"
    assert operation.field_path == "definition"
    assert operation.before_payload is not None
    assert operation.after_payload is None
    assert operation.before_payload["function_name"] == "rename"
    assert operation.before_payload["class_name"] == "TvChannel"
    assert operation.before_payload["definition"] == (
        "fn rename(display_name String) -> TvChannel {\n    }"
    )


def test_meta_enum_description_source_meaning_contract_resolves_code_delta() -> None:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        CodeSemanticSourceMeaningBinding as RuntimeSourceMeaningBinding,
        CodeSemanticSourceMeaningContract as RuntimeSourceMeaningContract,
        resolve_code_semantic_source_meaning,
    )
    from aware_code.source_index import (  # noqa: WPS433
        CodeGrammarGraphSelector,
    )

    raw_bindings = cast(
        Sequence[Mapping[str, object]],
        META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["bindings"],
    )
    runtime_contract = RuntimeSourceMeaningContract(
        provider_key=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["provider_key"]
        ),
        semantic_owner=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["semantic_owner"]
        ),
        grammar_profile_key=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["grammar_profile_key"]
        ),
        bindings=tuple(
            RuntimeSourceMeaningBinding(
                binding_key=str(binding["binding_key"]),
                language=str(binding["language"]),
                grammar_profile_key=str(binding["grammar_profile_key"]),
                grammar_rule_name=str(binding["grammar_rule_name"]),
                anchor_field_path=str(binding["anchor_field_path"]),
                anchor_role=cast(str | None, binding.get("anchor_role")),
                graph_selector=CodeGrammarGraphSelector(
                    **cast(
                        Mapping[str, str],
                        binding["graph_selector"],
                    )
                ),
                semantic_subject_type=str(binding["semantic_subject_type"]),
                semantic_key_template=str(binding["semantic_key_template"]),
                semantic_field=str(binding["semantic_field"]),
                value_domain=cast(str | None, binding.get("value_domain")),
                event_type=str(binding["event_type"]),
                condition_keys=tuple(
                    str(item)
                    for item in cast(
                        Sequence[object],
                        binding.get("condition_keys", ()),
                    )
                ),
                typed_operation_bindings=_runtime_typed_operation_bindings(binding),
                required=binding.get("required") is not False,
                metadata=cast(Mapping[str, object], binding.get("metadata", {})),
            )
            for binding in raw_bindings
        ),
        metadata=cast(
            Mapping[str, object],
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["metadata"],
        ),
    )
    baseline = _source_index(
        "/// Playback state.\n"
        "enum PlaybackState {\n"
        "    paused\n"
        "    playing\n"
        "}\n"
    )
    current = _source_index(
        "/// Playback state visible to assistants.\n"
        "enum PlaybackState {\n"
        "    paused\n"
        "    playing\n"
        "}\n"
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    enum_operations = tuple(
        operation
        for operation in resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.enum.description.update"
    )
    assert resolution.resolved is True
    assert len(enum_operations) == 1
    [operation] = enum_operations
    assert operation.semantic_key == "meta.enum:PlaybackState"
    assert operation.semantic_subject_type == "aware_meta.EnumConfig"
    assert operation.field_path == "description"
    assert operation.before_payload is not None
    assert operation.after_payload is not None
    assert operation.before_payload["description"] == "Playback state."
    assert operation.after_payload["description"] == (
        "Playback state visible to assistants."
    )
    assert operation.after_payload["enum_name"] == "PlaybackState"


def test_meta_enum_source_meaning_contract_resolves_structural_create_delete() -> None:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        resolve_code_semantic_source_meaning,
    )

    runtime_contract = _runtime_source_meaning_contract()
    baseline = _source_index("")
    current = _source_index("enum PlaybackState {\n}\n")

    create_resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    enum_create_operations = tuple(
        operation
        for operation in create_resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.enum.create"
    )
    assert create_resolution.resolved is True
    assert len(enum_create_operations) == 1
    [create_operation] = enum_create_operations
    assert create_operation.operation_family == "create"
    assert create_operation.semantic_key == "meta.enum:PlaybackState"
    assert create_operation.semantic_subject_type == "aware_meta.EnumConfig"
    assert create_operation.field_path == "name"
    assert create_operation.before_payload is None
    assert create_operation.after_payload is not None
    assert create_operation.after_payload["name"] == "PlaybackState"
    assert create_operation.after_payload["enum_name"] == "PlaybackState"

    delete_resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=current,
        current_source_index=baseline,
    )

    enum_delete_operations = tuple(
        operation
        for operation in delete_resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.enum.delete"
    )
    assert delete_resolution.resolved is True
    assert len(enum_delete_operations) == 1
    [delete_operation] = enum_delete_operations
    assert delete_operation.operation_family == "delete"
    assert delete_operation.semantic_key == "meta.enum:PlaybackState"
    assert delete_operation.field_path == "name"
    assert delete_operation.before_payload is not None
    assert delete_operation.after_payload is None
    assert delete_operation.before_payload["name"] == "PlaybackState"


def test_meta_enum_source_meaning_contract_resolves_identity_rename_explicitly() -> (
    None
):
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        resolve_code_semantic_source_meaning,
    )

    runtime_contract = _runtime_source_meaning_contract()
    baseline = _source_index("enum PlaybackState {\n}\n")
    current = _source_index("enum PlaybackMode {\n}\n")

    resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    rename_operations = tuple(
        operation
        for operation in resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.enum.identity.rename"
    )
    assert resolution.resolved is True
    assert len(rename_operations) == 1
    [rename_operation] = rename_operations
    assert rename_operation.operation_family == "rename"
    assert rename_operation.semantic_key == "meta.enum:PlaybackMode"
    assert rename_operation.before_payload is not None
    assert rename_operation.after_payload is not None
    assert rename_operation.before_payload["name"] == "PlaybackState"
    assert rename_operation.after_payload["name"] == "PlaybackMode"
    assert rename_operation.metadata["fallback_required"] is True
    assert rename_operation.metadata["fallback_reason"] == (
        "meta_enum_identity_rename_requires_explicit_policy"
    )
    assert rename_operation.metadata["preview_only"] is True


def test_meta_enum_option_source_meaning_contract_resolves_create_delta() -> None:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        resolve_code_semantic_source_meaning,
    )

    runtime_contract = _runtime_source_meaning_contract()
    baseline = _source_index(
        "enum PlaybackState {\n" "    paused\n" "    playing\n" "}\n"
    )
    current = _source_index(
        "enum PlaybackState {\n" "    paused\n" "    playing\n" "    buffering\n" "}\n"
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    enum_option_operations = tuple(
        operation
        for operation in resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.enum_option.create"
    )
    assert resolution.resolved is True
    assert len(enum_option_operations) == 1
    [operation] = enum_option_operations
    assert operation.operation_family == "create"
    assert operation.semantic_key == "meta.enum:PlaybackState/option:buffering"
    assert operation.semantic_subject_type == "aware_meta.EnumOption"
    assert operation.field_path == "value"
    assert operation.before_payload is None
    assert operation.after_payload is not None
    assert operation.after_payload["value"] == "buffering"
    assert operation.after_payload["enum_name"] == "PlaybackState"
    assert operation.after_payload["enum_option_value"] == "buffering"
    assert operation.after_payload["position"] == "2"


def test_meta_enum_option_source_meaning_contract_resolves_reorder_delta() -> None:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        resolve_code_semantic_source_meaning,
    )

    runtime_contract = _runtime_source_meaning_contract()
    baseline = _source_index(
        "enum PlaybackState {\n" "    paused\n" "    playing\n" "    buffering\n" "}\n"
    )
    current = _source_index(
        "enum PlaybackState {\n" "    paused\n" "    buffering\n" "    playing\n" "}\n"
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    enum_option_operations = tuple(
        operation
        for operation in resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.enum_option.position.update"
    )
    assert resolution.resolved is True
    assert len(enum_option_operations) == 2
    operations_by_key = {
        operation.semantic_key: operation for operation in enum_option_operations
    }
    playing_operation = operations_by_key["meta.enum:PlaybackState/option:playing"]
    buffering_operation = operations_by_key["meta.enum:PlaybackState/option:buffering"]
    assert playing_operation.operation_family == "update"
    assert playing_operation.field_path == "position"
    assert playing_operation.before_payload is not None
    assert playing_operation.after_payload is not None
    assert playing_operation.before_payload["position"] == "1"
    assert playing_operation.after_payload["position"] == "2"
    assert buffering_operation.before_payload is not None
    assert buffering_operation.after_payload is not None
    assert buffering_operation.before_payload["position"] == "2"
    assert buffering_operation.after_payload["position"] == "1"


def test_meta_enum_option_source_meaning_contract_resolves_delete_delta() -> None:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        resolve_code_semantic_source_meaning,
    )

    runtime_contract = _runtime_source_meaning_contract()
    baseline = _source_index(
        "enum PlaybackState {\n" "    paused\n" "    playing\n" "    buffering\n" "}\n"
    )
    current = _source_index(
        "enum PlaybackState {\n" "    paused\n" "    playing\n" "}\n"
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=runtime_contract,
        baseline_source_index=baseline,
        current_source_index=current,
    )

    enum_option_operations = tuple(
        operation
        for operation in resolution.typed_operations
        if operation.semantic_operation_type
        == "aware_meta.object_config_graph.enum_option.delete"
    )
    assert resolution.resolved is True
    assert len(enum_option_operations) == 1
    [operation] = enum_option_operations
    assert operation.operation_family == "delete"
    assert operation.semantic_key == "meta.enum:PlaybackState/option:buffering"
    assert operation.field_path == "value"
    assert operation.before_payload is not None
    assert operation.after_payload is None
    assert operation.before_payload["value"] == "buffering"
    assert operation.before_payload["enum_name"] == "PlaybackState"
    assert operation.before_payload["position"] == "2"


def _runtime_source_meaning_contract() -> Any:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        CodeSemanticSourceMeaningBinding as RuntimeSourceMeaningBinding,
        CodeSemanticSourceMeaningContract as RuntimeSourceMeaningContract,
    )
    from aware_code.source_index import (  # noqa: WPS433
        CodeGrammarGraphSelector,
    )

    raw_bindings = cast(
        Sequence[Mapping[str, object]],
        META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["bindings"],
    )
    return RuntimeSourceMeaningContract(
        provider_key=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["provider_key"]
        ),
        semantic_owner=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["semantic_owner"]
        ),
        grammar_profile_key=str(
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["grammar_profile_key"]
        ),
        bindings=tuple(
            RuntimeSourceMeaningBinding(
                binding_key=str(binding["binding_key"]),
                language=str(binding["language"]),
                grammar_profile_key=str(binding["grammar_profile_key"]),
                grammar_rule_name=str(binding["grammar_rule_name"]),
                anchor_field_path=str(binding["anchor_field_path"]),
                anchor_role=cast(str | None, binding.get("anchor_role")),
                graph_selector=CodeGrammarGraphSelector(
                    **cast(
                        Mapping[str, str],
                        binding["graph_selector"],
                    )
                ),
                semantic_subject_type=str(binding["semantic_subject_type"]),
                semantic_key_template=str(binding["semantic_key_template"]),
                semantic_field=str(binding["semantic_field"]),
                value_domain=cast(str | None, binding.get("value_domain")),
                event_type=str(binding["event_type"]),
                condition_keys=tuple(
                    str(item)
                    for item in cast(
                        Sequence[object],
                        binding.get("condition_keys", ()),
                    )
                ),
                typed_operation_bindings=_runtime_typed_operation_bindings(binding),
                required=binding.get("required") is not False,
                metadata=cast(Mapping[str, object], binding.get("metadata", {})),
            )
            for binding in raw_bindings
        ),
        metadata=cast(
            Mapping[str, object],
            META_OBJECT_CONFIG_GRAPH_SOURCE_MEANING_CONTRACT["metadata"],
        ),
    )


def _runtime_typed_operation_bindings(
    binding: Mapping[str, object],
) -> tuple[Any, ...]:
    from aware_code.semantic_source_meaning import (  # noqa: WPS433
        CodeSemanticSourceMeaningTypedOperationBinding,
    )

    operation_bindings = cast(
        Sequence[Mapping[str, object]],
        binding.get("typed_operation_bindings", ()),
    )
    return tuple(
        CodeSemanticSourceMeaningTypedOperationBinding(
            operation_key_template=cast(
                str | None,
                operation_binding.get("operation_key_template"),
            ),
            event_verbs=cast(
                Any,
                tuple(
                    str(item)
                    for item in cast(
                        Sequence[object],
                        operation_binding.get("event_verbs", ()),
                    )
                ),
            ),
            operation_family=cast(
                Any,
                operation_binding.get("operation_family"),
            ),
            semantic_operation_type=str(operation_binding["semantic_operation_type"]),
            semantic_subject_type=cast(
                str | None,
                operation_binding.get("semantic_subject_type"),
            ),
            field_path=cast(
                str | None,
                operation_binding.get("field_path"),
            ),
            requires_baseline_object_identity=(
                operation_binding.get("requires_baseline_object_identity") is True
            ),
            contract_source=cast(
                str | None,
                operation_binding.get("contract_source"),
            ),
            semantic_apply_boundary=cast(
                str | None,
                operation_binding.get("semantic_apply_boundary"),
            ),
            preview_only=operation_binding.get("preview_only") is not False,
            fallback_required=(operation_binding.get("fallback_required") is True),
            fallback_reason=cast(
                str | None,
                operation_binding.get("fallback_reason"),
            ),
            generated_materialization_intent=cast(
                Mapping[str, object] | None,
                operation_binding.get("generated_materialization_intent"),
            ),
        )
        for operation_binding in operation_bindings
    )


def _source_index(source_text: str) -> Any:
    from aware_code.source_index import (  # noqa: WPS433
        CodeGrammarSource,
        CodeGrammarSourceIndex,
    )

    return CodeGrammarSourceIndex.from_sources(
        (
            CodeGrammarSource(
                source_key="home/tv_channel.aware",
                source_text=source_text,
                relative_path="home/tv_channel.aware",
            ),
        )
    )


def test_meta_provider_role_advertises_semantic_source_meaning() -> None:
    role = AWARE_META_SEMANTIC_CONTRACT.package_role_for(role=META_PROVIDER_OWNER)

    assert role is not None
    assert META_SEMANTIC_SOURCE_MEANING_CAPABILITY in role.capabilities


def test_meta_provider_role_owns_only_aware_toml_manifest() -> None:
    role = AWARE_META_SEMANTIC_CONTRACT.package_role_for(role=META_PROVIDER_OWNER)

    assert role is not None
    assert role.owns_manifest_kinds == ("aware_toml",)
    manifest_kinds = {item.manifest_kind for item in META_MANIFEST_RESOLUTION}
    assert manifest_kinds == {"aware_toml"}
    assert manifest_kinds.isdisjoint(_NON_META_MANIFEST_KINDS)


def test_meta_semantic_package_provider_resolves_only_aware_toml() -> None:
    provider = meta_semantic_package._PROVIDER  # noqa: SLF001

    for manifest_kind in _NON_META_MANIFEST_KINDS:
        assert provider.resolve(_code_package(manifest_kind=manifest_kind)) == ()

    assert (
        provider.resolve(_code_package(manifest_kind="aware_toml", package_kind="api"))
        == ()
    )
    [descriptor] = provider.resolve(_code_package(manifest_kind="aware_toml"))
    assert descriptor.provider_key == "aware_meta"
    assert descriptor.family == "meta"
    assert descriptor.semantic_kind == "object_config_graph_package"
    assert descriptor.metadata["manifest_kind"] == "aware_toml"
    assert descriptor.metadata["semantic_projection_name"] == "ObjectConfigGraphPackage"
    assert descriptor.metadata["semantic_root_kind"] == "object_config_graph"


def _code_package(
    *,
    manifest_kind: str,
    package_kind: str = "ontology",
) -> CodePackageInfo:
    package_root = Path("modules/demo/structure/ontology")
    return CodePackageInfo(
        name="demo-ontology",
        root_path=package_root,
        manifest_path=package_root / "aware.toml",
        language=CodeLanguage.aware,
        metadata={
            "fqn_prefix": "aware_demo",
            "manifest_kind": manifest_kind,
            "package_kind": package_kind,
        },
    )
