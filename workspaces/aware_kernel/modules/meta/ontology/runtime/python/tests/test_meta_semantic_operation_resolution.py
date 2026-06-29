from __future__ import annotations

from types import SimpleNamespace
from typing import Mapping, Sequence, cast

import pytest

from _meta_runtime_test_paths import CODE_RUNTIME_ROOT, META_RUNTIME_ROOT


def _prepend_runtime_roots(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for runtime_root in (CODE_RUNTIME_ROOT, META_RUNTIME_ROOT):
        monkeypatch.syspath_prepend(str(runtime_root))


def test_function_config_semantic_operation_resolution_is_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.function.config.deltas.provider import (
        FUNCTION_CONFIG_DELTA_FEATURE_PROVIDER,
    )
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
    )

    operation_types = {
        META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
    }
    registrations = semantic_operation_resolver_registrations()
    function_registration = next(
        registration
        for registration in registrations
        if registration.handler_key
        == "function_config.semantic_operation_resolution"
    )

    assert set(function_registration.semantic_operation_types) == operation_types
    assert (
        function_registration
        in FUNCTION_CONFIG_DELTA_FEATURE_PROVIDER.semantic_operation_resolver_registrations
    )
    for operation_type in operation_types:
        resolver = semantic_operation_resolver_for_type(operation_type)
        assert resolver is function_registration.resolver


def test_attribute_config_semantic_operation_resolution_is_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.attribute.config.deltas.provider import (
        ATTRIBUTE_CONFIG_DELTA_FEATURE_PROVIDER,
    )
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
    )

    operation_types = {
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION,
    }
    registrations = semantic_operation_resolver_registrations()
    attribute_registration = next(
        registration
        for registration in registrations
        if registration.handler_key
        == "attribute_config.semantic_operation_resolution"
    )

    assert set(attribute_registration.semantic_operation_types) == operation_types
    assert (
        attribute_registration
        in ATTRIBUTE_CONFIG_DELTA_FEATURE_PROVIDER.semantic_operation_resolver_registrations
    )
    for operation_type in operation_types:
        resolver = semantic_operation_resolver_for_type(operation_type)
        assert resolver is attribute_registration.resolver


def test_class_config_semantic_operation_resolution_is_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.class_.config.deltas.provider import (
        CLASS_CONFIG_DELTA_FEATURE_PROVIDER,
    )
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION,
    )

    operation_types = {
        META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION,
    }
    registrations = semantic_operation_resolver_registrations()
    class_registration = next(
        registration
        for registration in registrations
        if registration.handler_key == "class_config.semantic_operation_resolution"
    )

    assert set(class_registration.semantic_operation_types) == operation_types
    assert (
        class_registration
        in CLASS_CONFIG_DELTA_FEATURE_PROVIDER.semantic_operation_resolver_registrations
    )
    for operation_type in operation_types:
        resolver = semantic_operation_resolver_for_type(operation_type)
        assert resolver is class_registration.resolver


def test_enum_config_semantic_operation_resolution_is_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.enum.config.deltas.provider import (
        ENUM_CONFIG_DELTA_FEATURE_PROVIDER,
    )
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION,
    )

    operation_types = {
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION,
    }
    registrations = semantic_operation_resolver_registrations()
    enum_registration = next(
        registration
        for registration in registrations
        if registration.handler_key == "enum_config.semantic_operation_resolution"
    )

    assert set(enum_registration.semantic_operation_types) == operation_types
    assert (
        enum_registration
        in ENUM_CONFIG_DELTA_FEATURE_PROVIDER.semantic_operation_resolver_registrations
    )
    for operation_type in operation_types:
        resolver = semantic_operation_resolver_for_type(operation_type)
        assert resolver is enum_registration.resolver


def test_enum_option_semantic_operation_resolution_is_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.enum.config.deltas.provider import (
        ENUM_CONFIG_DELTA_FEATURE_PROVIDER,
    )
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION,
    )

    operation_types = {
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION,
    }
    registrations = semantic_operation_resolver_registrations()
    enum_option_registration = next(
        registration
        for registration in registrations
        if registration.handler_key
        == "enum_option.semantic_operation_resolution"
    )

    assert set(enum_option_registration.semantic_operation_types) == operation_types
    assert (
        enum_option_registration
        in ENUM_CONFIG_DELTA_FEATURE_PROVIDER.semantic_operation_resolver_registrations
    )
    for operation_type in operation_types:
        resolver = semantic_operation_resolver_for_type(operation_type)
        assert resolver is enum_option_registration.resolver


def test_relationship_config_semantic_operation_resolution_is_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.class_.config.relationship.deltas.provider import (
        RELATIONSHIP_CONFIG_DELTA_FEATURE_PROVIDER,
    )
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
    )

    operation_types = {
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
    }
    registrations = semantic_operation_resolver_registrations()
    relationship_registration = next(
        registration
        for registration in registrations
        if registration.handler_key
        == "relationship_config.semantic_operation_resolution"
    )

    assert set(relationship_registration.semantic_operation_types) == operation_types
    assert (
        relationship_registration
        in RELATIONSHIP_CONFIG_DELTA_FEATURE_PROVIDER.semantic_operation_resolver_registrations
    )
    for operation_type in operation_types:
        resolver = semantic_operation_resolver_for_type(operation_type)
        assert resolver is relationship_registration.resolver


def test_function_impl_semantic_operation_resolution_is_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.function.impl.deltas.provider import (
        FUNCTION_IMPL_DELTA_FEATURE_PROVIDER,
    )
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION,
    )

    operation_types = {
        META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION,
    }
    registrations = semantic_operation_resolver_registrations()
    function_impl_registration = next(
        registration
        for registration in registrations
        if registration.handler_key == "function_impl.semantic_operation_resolution"
    )

    assert set(function_impl_registration.semantic_operation_types) == operation_types
    assert (
        function_impl_registration
        in FUNCTION_IMPL_DELTA_FEATURE_PROVIDER.semantic_operation_resolver_registrations
    )
    for operation_type in operation_types:
        resolver = semantic_operation_resolver_for_type(operation_type)
        assert resolver is function_impl_registration.resolver


def test_exported_meta_ocg_semantic_operations_are_feature_registered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta import semantic_operation_resolution
    from aware_meta.materialization.deltas.feature_registry import (
        semantic_operation_resolver_for_type,
        semantic_operation_resolver_registrations,
    )

    exported_operation_names = tuple(
        name
        for name in semantic_operation_resolution.__all__
        if name.startswith("META_OBJECT_CONFIG_GRAPH_")
        and name.endswith("_OPERATION")
    )
    exported_operation_types = {
        getattr(semantic_operation_resolution, name)
        for name in exported_operation_names
    }
    registrations = semantic_operation_resolver_registrations()
    registered_operation_types = {
        operation_type
        for registration in registrations
        for operation_type in registration.semantic_operation_types
    }

    assert exported_operation_names
    assert exported_operation_types == registered_operation_types
    for operation_type in sorted(exported_operation_types):
        matching_registrations = tuple(
            registration
            for registration in registrations
            if registration.handles_operation_type(operation_type)
        )
        assert len(matching_registrations) == 1
        assert (
            semantic_operation_resolver_for_type(operation_type)
            is matching_registrations[0].resolver
        )


def test_resolves_primitive_attribute_type_update_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code.semantic_capability import SemanticCapabilityTypedOperation
    from aware_meta.semantic_operation_resolution import (
        META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            SemanticCapabilityTypedOperation(
                operation_key=(
                    "aware_meta.object_config_graph.attribute.type:"
                    "TvChannel.number:update"
                ),
                operation_family="update",
                semantic_operation_type=(
                    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION
                ),
                semantic_key="meta.attribute:TvChannel.number",
                semantic_subject_type="ClassConfigAttributeConfig",
                field_path="type",
                event_key="meta.attribute:TvChannel.number:type:update",
                source_refs=("home/tv_channel.aware",),
                before_payload={"type": "Int"},
                after_payload={"type": "String"},
                requires_baseline_object_identity=True,
            ),
        ),
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.ready is False
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_attribute_type_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "attribute.scalar_function_calls"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.attribute.update"
    )
    assert resolution.metadata["requires_baseline_object_identity"] is True
    assert resolution.metadata["execution_ready"] is False
    assert resolution.metadata["execution_preconditions"] == (
        "provider_delta_ontology_operation_executor",
    )
    assert resolution.metadata["provider_delta_typed_operation_status"] == (
        "provider_delta_typed_operation_ready"
    )
    assert resolution.metadata["provider_delta_typed_operation_reason"] == (
        "attribute_type_provider_delta_operation_ready"
    )
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    assert len(typed_operations) == 1
    typed_operation = _mapping(typed_operations[0])
    assert typed_operation["provider_operation_type"] == ("meta_ocg.attribute.update")
    assert typed_operation["ontology_subject_kind"] == "attribute"
    assert typed_operation["operation_family"] == "update"
    assert typed_operation["semantic_key"] == ("meta.attribute:TvChannel.number")
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_attribute_type_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_ATTRIBUTE_TYPE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    assert generated_intent["reason"] == (
        "attribute_type_generated_materialization_intent_ready"
    )
    assert generated_intent["generated_materialization_provider_key"] == "aware_meta"
    assert generated_intent["blockers"] == ()
    assert (
        resolution.metadata[
            "provider_delta_generated_materialization_typed_operation_plan"
        ]
        == typed_plan
    )
    payload = resolution.evidence_payload()
    assert payload["mutates"] is False
    assert payload["execution_status"] == "not_requested"
    assert payload["would_execute"] is False
    assert "function_call_plan" not in payload
    assert "provider_delta_attribute_update_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_attribute_default_value_update_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_code.semantic_capability import SemanticCapabilityTypedOperation
    from aware_meta.semantic_operation_resolution import (
        META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            SemanticCapabilityTypedOperation(
                operation_key=(
                    "aware_meta.object_config_graph.attribute.default_value:"
                    "TvChannel.number:update"
                ),
                operation_family="update",
                semantic_operation_type=(
                    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DEFAULT_VALUE_UPDATE_OPERATION
                ),
                semantic_key="meta.attribute:TvChannel.number",
                semantic_subject_type="ClassConfigAttributeConfig",
                field_path="default_value",
                event_key="meta.attribute:TvChannel.number:default_value:update",
                source_refs=("home/tv_channel.aware",),
                before_payload={"default_value": "7"},
                after_payload={"default_value": "11"},
                requires_baseline_object_identity=True,
            ),
        ),
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.ready is False
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_attribute_default_value_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "attribute.scalar_function_calls"
    )
    assert resolution.metadata["provider_delta_typed_operation_status"] == (
        "provider_delta_typed_operation_ready"
    )
    assert resolution.metadata["provider_delta_typed_operation_reason"] == (
        "attribute_default_value_provider_delta_operation_ready"
    )
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    assert len(typed_operations) == 1
    typed_operation = _mapping(typed_operations[0])
    assert typed_operation["provider_operation_type"] == ("meta_ocg.attribute.update")
    assert typed_operation["ontology_subject_kind"] == "attribute"
    current = _mapping(typed_operation["current"])
    signature = _mapping(current["attribute_signature"])
    assert signature["default_value"] == "11"
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_attribute_default_value_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_ATTRIBUTE_DEFAULT_VALUE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    assert generated_intent["reason"] == (
        "attribute_default_value_generated_materialization_intent_ready"
    )
    assert generated_intent["blockers"] == ()
    assert (
        resolution.metadata[
            "provider_delta_generated_materialization_typed_operation_plan"
        ]
        == typed_plan
    )
    assert "provider_delta_attribute_update_operation_executor_required" in (
        resolution.blockers
    )


def test_blocks_attribute_identity_rename_as_explicit_replacement_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.attribute.identity:"
                    "ContentLayout.slug:rename"
                ),
                "operation_family": "rename",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_IDENTITY_RENAME_OPERATION
                ),
                "semantic_key": "meta.attribute:ContentLayout.slug",
                "semantic_subject_type": "aware_meta.AttributeConfig",
                "field_path": "name",
                "event_key": "meta.attribute:ContentLayout.slug:name:rename",
                "source_refs": ("content/content_layout.aware",),
                "before_payload": {
                    "class_name": "ContentLayout",
                    "attribute_name": "title",
                    "name": "title",
                },
                "after_payload": {
                    "class_name": "ContentLayout",
                    "attribute_name": "slug",
                    "name": "slug",
                },
                "requires_baseline_object_identity": True,
                "metadata": {
                    "fallback_required": True,
                    "fallback_reason": (
                        "meta_attribute_identity_rename_requires_explicit_"
                        "replacement_policy"
                    ),
                },
            },
        ),
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.ready is False
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_attribute_identity_rename_requires_explicit_replacement_policy"
    )
    assert "attribute_identity_rename_is_not_mutable_update" in resolution.blockers
    assert (
        "attribute_identity_replacement_requires_explicit_delete_create_or_migration"
        in resolution.blockers
    )
    assert resolution.metadata["replacement_policy"] == "explicit_fallback_required"
    assert resolution.metadata["fallback_required"] is True
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.attribute.identity.rename"
    )
    assert resolution.metadata["before_semantic_key"] == (
        "meta.attribute:ContentLayout.title"
    )
    assert resolution.metadata["after_semantic_key"] == (
        "meta.attribute:ContentLayout.slug"
    )
    assert resolution.metadata["allowed_replacement_operations"] == (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_DELETE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
    )
    assert "provider_delta_typed_operation_plan" not in resolution.metadata


def test_records_hydrated_receiver_object_id_without_executing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": "op:update",
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION
                ),
                "semantic_key": "meta.attribute:TvChannel.number",
                "semantic_subject_type": "ClassConfigAttributeConfig",
                "field_path": "type",
                "after_payload": {
                    "type_descriptor": {
                        "descriptor_kind": "primitive",
                        "primitive_base_type": "String",
                    },
                },
            },
        ),
        current_semantic_object_ids={
            "meta.attribute:TvChannel.number": "attribute-object-id",
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.metadata["receiver_object_id"] == "attribute-object-id"
    assert resolution.metadata["execution_ready"] is True
    assert resolution.metadata["execution_preconditions"] == (
        "provider_delta_ontology_operation_executor",
    )
    assert resolution.evidence_payload()["execution_status"] == "not_requested"


def test_resolves_function_create_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.function:" "TvChannel.rename:create"
                ),
                "operation_family": "create",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION
                ),
                "semantic_key": "meta.function:TvChannel.rename",
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "field_path": "name",
                "event_key": "meta.function:TvChannel.rename:name:upsert",
                "source_refs": ("home/tv_channel.aware",),
                "after_payload": {
                    "name": "rename",
                    "class_name": "TvChannel",
                    "function_name": "rename",
                    "function_description": (
                        "Rename the channel display label for humans and " "assistants."
                    ),
                },
            },
        ),
        current_semantic_object_ids={"meta.class:TvChannel": "class-object-id"},
    )

    assert resolution.status == "function_call_plan_ready"
    assert resolution.ready is True
    assert resolution.reason == "meta_ocg_function_create_function_call_plan_ready"
    plan = resolution.function_call_plan
    assert plan is not None
    assert plan.function_ref == CLASS_CONFIG_CREATE_FUNCTION_CONFIG_FUNCTION_REF
    assert plan.receiver_semantic_key == "meta.class:TvChannel"
    assert plan.receiver_object_id == "class-object-id"
    assert plan.result_semantic_key == "meta.function:TvChannel.rename"
    assert plan.arguments["name"] == "rename"
    assert plan.arguments["description"] == (
        "Rename the channel display label for humans and assistants."
    )
    assert plan.arguments["kind"] == "instance"
    assert plan.metadata["execution_ready"] is True
    assert plan.metadata["requires_baseline_object_identity"] is True


def test_resolves_class_description_update_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.class.description:"
                    "TvChannel:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_CLASS_DESCRIPTION_UPDATE_OPERATION
                ),
                "semantic_key": "meta.class:TvChannel",
                "semantic_subject_type": "aware_meta.ClassConfig",
                "field_path": "description",
                "event_key": "meta.class:TvChannel:description:upsert",
                "source_refs": ("home/tv_channel.aware",),
                "before_payload": {},
                "after_payload": {
                    "class_name": "TvChannel",
                    "description": "A media channel.",
                },
                "requires_baseline_object_identity": True,
            },
        ),
        current_semantic_object_ids={
            "ocg:aware_demo/node:aware_demo.default.home.TvChannel": (
                "class-object-id"
            ),
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_class_description_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "class.object_config_graph_node_function_calls"
    )
    assert resolution.metadata["provider_operation_type"] == "meta_ocg.class.update"
    assert resolution.metadata["receiver_object_id"] == "class-object-id"
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    assert len(typed_operations) == 1
    typed_operation = _mapping(typed_operations[0])
    assert typed_operation["ontology_subject_kind"] == "class"
    assert typed_operation["provider_operation_type"] == "meta_ocg.class.update"
    current = _mapping(typed_operation["current"])
    assert current["class_config_id"] == "class-object-id"
    assert current["description"] == "A media channel."
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_class_description_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_CLASS_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    assert (
        resolution.metadata[
            "provider_delta_generated_materialization_typed_operation_plan"
        ]
        == typed_plan
    )
    assert "provider_delta_class_update_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_class_structural_create_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    graph_id = "00000000-0000-0000-0000-000000000501"
    graph_semantic_key = "ocg:aware_content"
    class_fqn = "aware_content.default.content.ContentPlacement"

    from aware_meta.graph.config.stable_ids import (
        stable_class_config_id,
        stable_object_config_graph_node_id,
    )
    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )
    from uuid import UUID

    expected_node_id = str(
        stable_object_config_graph_node_id(
            object_config_graph_id=UUID(graph_id),
            type="class",
            node_key=class_fqn,
        )
    )
    expected_class_config_id = str(
        stable_class_config_id(
            object_config_graph_node_id=UUID(expected_node_id),
            class_fqn=class_fqn,
        )
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.class.identity:"
                    "ContentPlacement:create"
                ),
                "operation_family": "create",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION
                ),
                "semantic_key": "meta.class:ContentPlacement",
                "semantic_subject_type": "aware_meta.ClassConfig",
                "field_path": "name",
                "event_key": "meta.class:ContentPlacement:name:upsert",
                "source_refs": ("content/content_layout.aware",),
                "before_payload": None,
                "after_payload": {
                    "name": "ContentPlacement",
                    "class_name": "ContentPlacement",
                    "class_fqn": class_fqn,
                    "graph_semantic_key": graph_semantic_key,
                    "description": (
                        "Content placement hints for generated layout tests."
                    ),
                },
            },
        ),
        current_semantic_object_ids={
            graph_semantic_key: graph_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_class_create_requires_provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == "meta_ocg.class.create"
    assert resolution.metadata["receiver_semantic_key"] == graph_semantic_key
    assert resolution.metadata["receiver_object_id"] == graph_id
    assert resolution.metadata["result_object_id"] == expected_class_config_id
    assert resolution.metadata["object_config_graph_node_id"] == expected_node_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    anchors = _sequence(typed_plan["semantic_object_anchors"])
    assert len(typed_operations) == 1
    assert len(anchors) == 1
    typed_operation = _mapping(typed_operations[0])
    current = _mapping(typed_operation["current"])
    assert typed_operation["provider_operation_type"] == "meta_ocg.class.create"
    assert typed_operation["ontology_subject_kind"] == "class"
    assert current["graph_semantic_key"] == graph_semantic_key
    assert current["object_config_graph_node_id"] == expected_node_id
    assert current["class_config_id"] == expected_class_config_id
    assert current["class_fqn"] == class_fqn
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_class_create_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_CLASS_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    assert generated_intent["policy_key"] == "aware_meta.python_orm.class.create"
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 2
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    create_node_intent, create_class_intent = intents
    assert create_node_intent["function_name"] == "create_node"
    assert create_node_intent["target_object_id"] == graph_id
    assert create_node_intent["expected_result_object_id"] == expected_node_id
    assert create_class_intent["function_name"] == "create_class"
    assert create_class_intent["target_object_id"] == expected_node_id
    assert create_class_intent["expected_result_object_id"] == (
        expected_class_config_id
    )
    assert "provider_delta_class_create_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_class_structural_delete_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    graph_id = "00000000-0000-0000-0000-000000000511"
    node_id = "00000000-0000-0000-0000-000000000512"
    class_config_id = "00000000-0000-0000-0000-000000000513"
    graph_semantic_key = "ocg:aware_content"
    class_fqn = "aware_content.default.content.ContentPlacement"

    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.materialization.semantic_function_call_resolution import (
        META_OCG_DELETE_NODE_FUNCTION_REF,
    )
    from aware_meta.semantic_operation_resolution import (
        META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.class.identity:"
                    "ContentPlacement:delete"
                ),
                "operation_family": "delete",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_CLASS_DELETE_OPERATION
                ),
                "semantic_key": "meta.class:ContentPlacement",
                "semantic_subject_type": "aware_meta.ClassConfig",
                "field_path": "name",
                "event_key": "meta.class:ContentPlacement:name:delete",
                "source_refs": ("content/content_layout.aware",),
                "before_payload": {
                    "name": "ContentPlacement",
                    "class_name": "ContentPlacement",
                    "class_fqn": class_fqn,
                    "graph_semantic_key": graph_semantic_key,
                    "object_config_graph_node_id": node_id,
                    "class_config_id": class_config_id,
                    "description": "Content placement config.",
                },
                "after_payload": None,
            },
        ),
        current_semantic_object_ids={
            graph_semantic_key: graph_id,
            "meta.class:ContentPlacement": class_config_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_class_delete_requires_provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == "meta_ocg.class.delete"
    assert resolution.metadata["receiver_semantic_key"] == graph_semantic_key
    assert resolution.metadata["receiver_object_id"] == graph_id
    assert resolution.metadata["result_object_id"] == node_id
    assert resolution.metadata["object_config_graph_node_id"] == node_id
    assert resolution.metadata["class_config_id"] == class_config_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    anchors = _sequence(typed_plan["semantic_object_anchors"])
    assert len(typed_operations) == 1
    assert len(anchors) == 1
    typed_operation = _mapping(typed_operations[0])
    current = _mapping(typed_operation["current"])
    assert typed_operation["provider_operation_type"] == "meta_ocg.class.delete"
    assert typed_operation["semantic_subject_type"] == "aware_meta.ObjectConfigGraph"
    assert typed_operation["ontology_subject_kind"] == "class"
    assert current["graph_semantic_key"] == graph_semantic_key
    assert current["object_config_graph_node_id"] == node_id
    assert current["class_config_id"] == class_config_id
    assert current["class_fqn"] == class_fqn
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_class_delete_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_CLASS_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    assert generated_intent["policy_key"] == "aware_meta.python_orm.class.delete"
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    [delete_node_intent] = intents
    assert delete_node_intent["function_name"] == "delete_node"
    assert delete_node_intent["target_object_id"] == graph_id
    assert delete_node_intent["expected_result_object_id"] == node_id
    assert delete_node_intent["function_ref"] == META_OCG_DELETE_NODE_FUNCTION_REF
    assert "provider_delta_class_delete_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_enum_description_update_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    enum_config_id = "00000000-0000-0000-0000-000000000301"

    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_ENUM_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.enum.description:"
                    "PlaybackState:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION
                ),
                "semantic_key": "meta.enum:PlaybackState",
                "semantic_subject_type": "aware_meta.EnumConfig",
                "field_path": "description",
                "event_key": "meta.enum:PlaybackState:description:update",
                "source_refs": ("home/playback_state.aware",),
                "before_payload": {
                    "enum_name": "PlaybackState",
                    "description": "Playback state.",
                },
                "after_payload": {
                    "enum_name": "PlaybackState",
                    "description": "Playback state visible to assistants.",
                },
                "requires_baseline_object_identity": True,
            },
        ),
        current_semantic_object_ids={
            "ocg:aware_demo/node:aware_demo.home.PlaybackState": enum_config_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_enum_description_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "enum.object_config_graph_node_function_calls"
    )
    assert resolution.metadata["provider_operation_type"] == "meta_ocg.enum.update"
    assert resolution.metadata["receiver_object_id"] == enum_config_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    assert len(typed_operations) == 1
    typed_operation = _mapping(typed_operations[0])
    assert typed_operation["ontology_subject_kind"] == "enum"
    assert typed_operation["provider_operation_type"] == "meta_ocg.enum.update"
    current = _mapping(typed_operation["current"])
    assert current["enum_config_id"] == enum_config_id
    assert current["description"] == "Playback state visible to assistants."
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_enum_description_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_ENUM_DESCRIPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    assert generated_intent["reason"] == (
        "enum_description_generated_materialization_intent_ready"
    )
    assert generated_intent["renderer_key"] == "python.orm.enum"
    assert generated_intent["policy_key"] == "aware_meta.python_orm.enum.description"
    assert generated_intent["materialization_target"] == "python_enum_docstring"
    assert resolution.metadata["generated_materialization_intent_blockers"] == ()
    assert (
        resolution.metadata[
            "provider_delta_generated_materialization_typed_operation_plan"
        ]
        == typed_plan
    )
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert intents[0]["function_name"] == "update_config"
    assert intents[0]["target_object_id"] == enum_config_id
    assert intents[0]["kwargs"] == {
        "description": "Playback state visible to assistants.",
    }
    assert "provider_delta_enum_update_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_enum_option_create_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    enum_config_id = "00000000-0000-0000-0000-000000000301"

    from aware_meta.graph.config.stable_ids import stable_enum_option_id
    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )
    from uuid import UUID

    expected_enum_option_id = str(
        stable_enum_option_id(
            enum_config_id=UUID(enum_config_id),
            value="assistant",
        )
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.enum_option.value:"
                    "ContentSource.assistant:create"
                ),
                "operation_family": "create",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION
                ),
                "semantic_key": "meta.enum:ContentSource/option:assistant",
                "semantic_subject_type": "aware_meta.EnumOption",
                "field_path": "value",
                "event_key": ("meta.enum:ContentSource/option:assistant:value:upsert"),
                "source_refs": ("content/content_enums.aware",),
                "before_payload": None,
                "after_payload": {
                    "enum_name": "ContentSource",
                    "value": "assistant",
                    "enum_option_value": "assistant",
                    "position": "6",
                },
            },
        ),
        current_semantic_object_ids={
            "meta.enum:ContentSource": enum_config_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_enum_option_create_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "enum.object_config_graph_node_function_calls"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.enum_option.create"
    )
    assert resolution.metadata["receiver_object_id"] == enum_config_id
    assert resolution.metadata["result_object_id"] == expected_enum_option_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    assert len(typed_operations) == 1
    typed_operation = _mapping(typed_operations[0])
    assert typed_operation["ontology_subject_kind"] == "enum_option"
    assert typed_operation["provider_operation_type"] == ("meta_ocg.enum_option.create")
    current = _mapping(typed_operation["current"])
    assert current["enum_config_id"] == enum_config_id
    assert current["enum_option_id"] == expected_enum_option_id
    assert current["value"] == "assistant"
    assert current["position"] == 6
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_enum_option_create_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_ENUM_OPTION_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    assert generated_intent["reason"] == (
        "enum_option_create_generated_materialization_intent_ready"
    )
    assert generated_intent["renderer_key"] == "python.orm.enum"
    assert generated_intent["policy_key"] == "aware_meta.python_orm.enum.option_line"
    assert generated_intent["materialization_target"] == "python_enum_option_line"
    assert resolution.metadata["generated_materialization_intent_blockers"] == ()
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert intents[0]["function_name"] == "create_enum_option"
    assert intents[0]["target_object_id"] == enum_config_id
    assert intents[0]["expected_result_object_id"] == expected_enum_option_id
    assert intents[0]["kwargs"] == {
        "value": "assistant",
        "label": None,
        "description": None,
        "position": 6,
    }
    receiver_typed_operation = dict(typed_operation)
    receiver_current = dict(current)
    receiver_payload = dict(_mapping(receiver_current["payload"]))
    receiver_current["receiver_object_id"] = "enum-executable-object-id"
    receiver_payload["receiver_object_id"] = "enum-executable-object-id"
    receiver_current["payload"] = receiver_payload
    receiver_typed_operation["current"] = receiver_current
    receiver_plan = {
        **typed_plan,
        "typed_operations": (receiver_typed_operation,),
    }
    receiver_ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=receiver_plan,
    )
    receiver_intents = cast(
        Sequence[Mapping[str, object]],
        receiver_ontology_plan["invocation_intents"],
    )
    assert receiver_intents[0]["target_object_id"] == "enum-executable-object-id"
    assert receiver_intents[0]["expected_result_object_id"] == expected_enum_option_id
    assert "provider_delta_enum_option_create_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_enum_structural_create_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    graph_id = "00000000-0000-0000-0000-000000000401"
    graph_semantic_key = "ocg:aware_content"
    enum_fqn = "aware_content.default.content.ContentSource"

    from aware_meta.graph.config.stable_ids import (
        stable_enum_config_id,
        stable_object_config_graph_node_id,
    )
    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )
    from uuid import UUID

    expected_node_id = str(
        stable_object_config_graph_node_id(
            object_config_graph_id=UUID(graph_id),
            type="enum",
            node_key=enum_fqn,
        )
    )
    expected_enum_config_id = str(
        stable_enum_config_id(
            object_config_graph_node_id=UUID(expected_node_id),
            enum_fqn=enum_fqn,
        )
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.enum.identity:"
                    "ContentSource:create"
                ),
                "operation_family": "create",
                "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
                "semantic_key": "meta.enum:ContentSource",
                "semantic_subject_type": "aware_meta.EnumConfig",
                "field_path": "name",
                "event_key": "meta.enum:ContentSource:name:upsert",
                "source_refs": ("content/content_enums.aware",),
                "before_payload": None,
                "after_payload": {
                    "name": "ContentSource",
                    "enum_name": "ContentSource",
                    "enum_fqn": enum_fqn,
                    "graph_semantic_key": graph_semantic_key,
                    "values": ("text", "image"),
                },
            },
        ),
        current_semantic_object_ids={
            graph_semantic_key: graph_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_enum_create_requires_provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == "meta_ocg.enum.create"
    assert resolution.metadata["receiver_semantic_key"] == graph_semantic_key
    assert resolution.metadata["receiver_object_id"] == graph_id
    assert resolution.metadata["result_object_id"] == expected_enum_config_id
    assert resolution.metadata["object_config_graph_node_id"] == expected_node_id
    assert resolution.metadata["execution_ready"] is True
    assert resolution.metadata["provider_delta_typed_operation_status"] == (
        "provider_delta_typed_operation_ready"
    )
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operations = _sequence(typed_plan["typed_operations"])
    anchors = _sequence(typed_plan["semantic_object_anchors"])
    assert len(typed_operations) == 1
    assert len(anchors) == 1
    typed_operation = _mapping(typed_operations[0])
    current = _mapping(typed_operation["current"])
    assert typed_operation["provider_operation_type"] == "meta_ocg.enum.create"
    assert typed_operation["ontology_subject_kind"] == "enum"
    assert current["graph_semantic_key"] == graph_semantic_key
    assert current["object_config_graph_node_id"] == expected_node_id
    assert current["enum_config_id"] == expected_enum_config_id
    assert current["values"] == ("text", "image")
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_enum_create_generated_materialization_intent"
    )
    assert resolution.metadata["generated_materialization_intent_status"] == (
        "generated_materialization_intent_ready"
    )
    assert resolution.metadata["generated_materialization_intent_reason"] == (
        "enum_create_generated_materialization_intent_ready"
    )
    assert generated_intent["policy_key"] == "aware_meta.python_orm.enum.create"
    assert generated_intent["materialization_target"] == "python_enum_class"
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 2
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    create_node_intent, create_enum_intent = intents
    assert create_node_intent["function_name"] == "create_node"
    assert create_node_intent["target_object_id"] == graph_id
    assert create_node_intent["expected_result_object_id"] == expected_node_id
    assert create_enum_intent["function_name"] == "create_enum"
    assert create_enum_intent["target_object_id"] == expected_node_id
    assert create_enum_intent["expected_result_object_id"] == expected_enum_config_id
    create_enum_kwargs = _mapping(create_enum_intent["kwargs"])
    assert create_enum_kwargs["values"] == ["text", "image"]
    assert "provider_delta_enum_create_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_enum_structural_create_graph_from_package_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    graph_receiver_id = "00000000-0000-0000-0000-000000000401"
    graph_source_id = "00000000-0000-0000-0000-000000000402"
    graph_semantic_key = "ocg:aware_content"
    enum_fqn = "aware_content.default.content.ContentAudience"

    from uuid import UUID

    from aware_meta.graph.config.stable_ids import (
        stable_enum_config_id,
        stable_object_config_graph_node_id,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    expected_node_id = str(
        stable_object_config_graph_node_id(
            object_config_graph_id=UUID(graph_source_id),
            type="enum",
            node_key=enum_fqn,
        )
    )
    expected_enum_config_id = str(
        stable_enum_config_id(
            object_config_graph_node_id=UUID(expected_node_id),
            enum_fqn=enum_fqn,
        )
    )
    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.enum.identity:"
                    "ContentAudience:create"
                ),
                "operation_family": "create",
                "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
                "semantic_key": "meta.enum:ContentAudience",
                "semantic_subject_type": "aware_meta.EnumConfig",
                "field_path": "name",
                "event_key": "meta.enum:ContentAudience:name:upsert",
                "source_refs": ("content/content_enums.aware",),
                "package_name": "content-ontology",
                "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                "before_payload": None,
                "after_payload": {
                    "name": "ContentAudience",
                    "enum_name": "ContentAudience",
                    "enum_fqn": enum_fqn,
                    "values": ("internal", "public"),
                },
            },
        ),
        current_semantic_object_ids={
            graph_semantic_key: graph_receiver_id,
        },
        baseline_semantic_object_identities={
            graph_semantic_key: {
                "semantic_key": graph_semantic_key,
                "object_kind": "object_config_graph",
                "object_id": graph_source_id,
                "semantic_apply_receiver_object_id": graph_receiver_id,
            },
        },
    )

    assert resolution.metadata["receiver_semantic_key"] == graph_semantic_key
    assert resolution.metadata["receiver_object_id"] == graph_source_id
    assert resolution.metadata["semantic_apply_receiver_object_id"] == graph_receiver_id
    assert resolution.metadata["semantic_source_object_id"] == graph_source_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    typed_operation = _mapping(_sequence(typed_plan["typed_operations"])[0])
    anchor = _mapping(_sequence(typed_plan["semantic_object_anchors"])[0])
    current = _mapping(typed_operation["current"])
    assert current["graph_semantic_key"] == graph_semantic_key
    assert current["graph_object_id"] == graph_source_id
    assert current["object_config_graph_node_id"] == expected_node_id
    assert current["enum_config_id"] == expected_enum_config_id
    assert current["values"] == ("internal", "public")
    assert _mapping(anchor["current"])["object_id"] == graph_source_id


def test_resolves_same_delta_enum_sibling_operations_from_package_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    graph_receiver_id = "00000000-0000-0000-0000-000000000401"
    graph_source_id = "00000000-0000-0000-0000-000000000402"
    graph_semantic_key = "ocg:aware_content"
    enum_fqn = "aware_content.default.content.ContentAudience"

    from uuid import UUID

    from aware_meta.graph.config.stable_ids import (
        stable_enum_config_id,
        stable_enum_option_id,
        stable_object_config_graph_node_id,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    expected_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=UUID(graph_source_id),
        type="enum",
        node_key=enum_fqn,
    )
    expected_enum_config_id = str(
        stable_enum_config_id(
            object_config_graph_node_id=expected_node_id,
            enum_fqn=enum_fqn,
        )
    )
    expected_public_option_id = str(
        stable_enum_option_id(
            enum_config_id=UUID(expected_enum_config_id),
            value="public",
        )
    )
    common_payload = {
        "enum_name": "ContentAudience",
    }
    [enum_create, description, option_create, option_update] = (
        resolve_meta_semantic_operation_function_call_plan_previews(
            typed_operations=(
                {
                    "operation_key": (
                        "aware_meta.object_config_graph.enum.identity:"
                        "ContentAudience:create"
                    ),
                    "operation_family": "create",
                    "semantic_operation_type": (
                        META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION
                    ),
                    "semantic_key": "meta.enum:ContentAudience",
                    "semantic_subject_type": "aware_meta.EnumConfig",
                    "field_path": "name",
                    "package_name": "content-ontology",
                    "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                    "source_refs": ("aware/content/content_enums.aware",),
                    "before_payload": None,
                    "after_payload": {
                        **common_payload,
                    },
                },
                {
                    "operation_key": (
                        "aware_meta.object_config_graph.enum.description:"
                        "ContentAudience:update"
                    ),
                    "operation_family": "update",
                    "semantic_operation_type": (
                        META_OBJECT_CONFIG_GRAPH_ENUM_DESCRIPTION_UPDATE_OPERATION
                    ),
                    "semantic_key": "meta.enum:ContentAudience",
                    "semantic_subject_type": "aware_meta.EnumConfig",
                    "field_path": "description",
                    "package_name": "content-ontology",
                    "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                    "source_refs": ("aware/content/content_enums.aware",),
                    "after_payload": {
                        **common_payload,
                        "description": (
                            "Audience role for generated content dispatch."
                        ),
                    },
                },
                {
                    "operation_key": (
                        "aware_meta.object_config_graph.enum.option:"
                        "ContentAudience.public:create"
                    ),
                    "operation_family": "create",
                    "semantic_operation_type": (
                        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION
                    ),
                    "semantic_key": "meta.enum:ContentAudience/option:public",
                    "semantic_subject_type": "aware_meta.EnumOption",
                    "field_path": "value",
                    "package_name": "content-ontology",
                    "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                    "source_refs": ("aware/content/content_enums.aware",),
                    "after_payload": {
                        **common_payload,
                        "value": "public",
                    },
                },
                {
                    "operation_key": (
                        "aware_meta.object_config_graph.enum.option.position:"
                        "ContentAudience.public:update"
                    ),
                    "operation_family": "update",
                    "semantic_operation_type": (
                        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION
                    ),
                    "semantic_key": "meta.enum:ContentAudience/option:public",
                    "semantic_subject_type": "aware_meta.EnumOption",
                    "field_path": "position",
                    "package_name": "content-ontology",
                    "package_root": "workspaces/aware_kernel/modules/content/ontology/structure",
                    "source_refs": ("aware/content/content_enums.aware",),
                    "after_payload": {
                        **common_payload,
                        "value": "public",
                        "position": 1,
                    },
                },
            ),
            current_semantic_object_ids={
                graph_semantic_key: graph_receiver_id,
            },
            baseline_semantic_object_identities={
                graph_semantic_key: {
                    "semantic_key": graph_semantic_key,
                    "object_kind": "object_config_graph",
                    "object_id": graph_source_id,
                    "semantic_apply_receiver_object_id": graph_receiver_id,
                },
            },
        )
    )

    create_typed_plan = _mapping(
        enum_create.metadata["provider_delta_typed_operation_plan"]
    )
    create_operation = _mapping(_sequence(create_typed_plan["typed_operations"])[0])
    create_current = _mapping(create_operation["current"])
    assert create_current["enum_fqn"] == enum_fqn
    assert create_current["node_key"] == enum_fqn
    assert create_current["object_config_graph_node_id"] == str(expected_node_id)
    assert create_current["enum_config_id"] == expected_enum_config_id
    assert create_current["description"] == (
        "Audience role for generated content dispatch."
    )
    assert create_current["values"] == ("public",)
    assert enum_create.metadata["generated_materialization_intent_status"] == (
        "generated_materialization_intent_ready"
    )

    for resolution in (description, option_create, option_update):
        assert resolution.status == "function_call_plan_blocked"
        assert "missing_enum_config_id" not in resolution.blockers
        assert resolution.metadata["receiver_object_id"] == expected_enum_config_id

    assert option_create.metadata["result_object_id"] == expected_public_option_id
    assert option_update.metadata["result_object_id"] == expected_public_option_id
    assert "missing_enum_option_id" not in option_update.blockers


def test_resolves_enum_structural_delete_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        META_ENUM_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    graph_id = "00000000-0000-0000-0000-000000000401"
    node_id = "00000000-0000-0000-0000-000000000402"
    enum_config_id = "00000000-0000-0000-0000-000000000403"
    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.enum.identity:"
                    "ContentSource:delete"
                ),
                "operation_family": "delete",
                "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_ENUM_DELETE_OPERATION,
                "semantic_key": "meta.enum:ContentSource",
                "semantic_subject_type": "aware_meta.EnumConfig",
                "field_path": "name",
                "event_key": "meta.enum:ContentSource:name:delete",
                "source_refs": ("content/content_enums.aware",),
                "before_payload": {
                    "name": "ContentSource",
                    "enum_name": "ContentSource",
                    "enum_fqn": "aware_content.default.content.ContentSource",
                    "graph_semantic_key": "ocg:aware_content",
                    "object_config_graph_node_id": node_id,
                    "enum_config_id": enum_config_id,
                },
                "after_payload": None,
            },
        ),
        current_semantic_object_ids={
            "ocg:aware_content": graph_id,
            "meta.enum:ContentSource": enum_config_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_enum_delete_requires_provider_delta_" "ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == "meta_ocg.enum.delete"
    assert resolution.metadata["execution_ready"] is True
    assert resolution.metadata["receiver_object_id"] == graph_id
    assert resolution.metadata["result_object_id"] == node_id
    assert resolution.metadata["enum_config_id"] == enum_config_id
    assert resolution.metadata["object_config_graph_node_id"] == node_id
    assert resolution.metadata["execution_preconditions"] == (
        "provider_delta_ontology_operation_executor",
    )
    assert resolution.metadata["generated_materialization_intent_status"] == (
        "generated_materialization_intent_ready"
    )
    intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert intent["contract_version"] == (
        META_ENUM_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert intent["policy_key"] == "aware_meta.python_orm.enum.delete"
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    [typed_operation_raw] = _sequence(typed_plan["typed_operations"])
    typed_operation = _mapping(typed_operation_raw)
    current = _mapping(typed_operation["current"])
    assert typed_operation["provider_operation_type"] == "meta_ocg.enum.delete"
    assert typed_operation["semantic_subject_type"] == "aware_meta.ObjectConfigGraph"
    assert current["graph_semantic_key"] == "ocg:aware_content"
    assert current["object_config_graph_node_id"] == node_id
    assert current["enum_config_id"] == enum_config_id
    assert "provider_delta_enum_delete_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_enum_option_reorder_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    enum_config_id = "00000000-0000-0000-0000-000000000301"
    enum_option_id = "00000000-0000-0000-0000-000000000302"

    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.enum_option.position:"
                    "ContentSource.assistant:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_POSITION_UPDATE_OPERATION
                ),
                "semantic_key": "meta.enum:ContentSource/option:assistant",
                "semantic_subject_type": "aware_meta.EnumOption",
                "field_path": "position",
                "event_key": (
                    "meta.enum:ContentSource/option:assistant:position:update"
                ),
                "source_refs": ("content/content_enums.aware",),
                "before_payload": {
                    "enum_name": "ContentSource",
                    "value": "assistant",
                    "position": "6",
                },
                "after_payload": {
                    "enum_name": "ContentSource",
                    "value": "assistant",
                    "position": "1",
                },
            },
        ),
        current_semantic_object_ids={
            "meta.enum:ContentSource": enum_config_id,
            "meta.enum:ContentSource/option:assistant": enum_option_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_enum_option_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.enum_option.update"
    )
    assert resolution.metadata["receiver_object_id"] == enum_config_id
    assert resolution.metadata["result_object_id"] == enum_option_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    [typed_operation_raw] = _sequence(typed_plan["typed_operations"])
    typed_operation = _mapping(typed_operation_raw)
    assert typed_operation["provider_operation_type"] == "meta_ocg.enum_option.update"
    current = _mapping(typed_operation["current"])
    baseline = _mapping(typed_operation["baseline"])
    baseline_object = _mapping(baseline["object"])
    assert current["enum_config_id"] == enum_config_id
    assert current["enum_option_id"] == enum_option_id
    assert current["position"] == 1
    assert baseline_object["position"] == 6
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_enum_option_update_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert intents[0]["function_name"] == "update_config"
    assert intents[0]["target_object_id"] == enum_option_id
    assert intents[0]["kwargs"] == {
        "label": None,
        "description": None,
        "position": 1,
    }
    assert "provider_delta_enum_option_update_operation_executor_required" in (
        resolution.blockers
    )


def test_resolves_enum_option_delete_to_provider_delta_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    enum_config_id = "00000000-0000-0000-0000-000000000301"
    enum_option_id = "00000000-0000-0000-0000-000000000302"

    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.enum_option.value:"
                    "ContentSource.assistant:delete"
                ),
                "operation_family": "delete",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_DELETE_OPERATION
                ),
                "semantic_key": "meta.enum:ContentSource/option:assistant",
                "semantic_subject_type": "aware_meta.EnumOption",
                "field_path": "value",
                "event_key": ("meta.enum:ContentSource/option:assistant:value:delete"),
                "source_refs": ("content/content_enums.aware",),
                "before_payload": {
                    "enum_name": "ContentSource",
                    "value": "assistant",
                    "position": "6",
                },
                "after_payload": None,
            },
        ),
        current_semantic_object_ids={
            "meta.enum:ContentSource": enum_config_id,
            "meta.enum:ContentSource/option:assistant": enum_option_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_enum_option_delete_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.enum_option.delete"
    )
    assert resolution.metadata["receiver_object_id"] == enum_config_id
    assert resolution.metadata["result_object_id"] == enum_option_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    [typed_operation_raw] = _sequence(typed_plan["typed_operations"])
    typed_operation = _mapping(typed_operation_raw)
    assert typed_operation["provider_operation_type"] == "meta_ocg.enum_option.delete"
    current = _mapping(typed_operation["current"])
    baseline = _mapping(typed_operation["baseline"])
    baseline_object = _mapping(baseline["object"])
    assert current["enum_config_id"] == enum_config_id
    assert current["enum_option_id"] == enum_option_id
    assert current["value"] == "assistant"
    assert baseline_object["enum_option_id"] == enum_option_id
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_enum_option_delete_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_ENUM_OPTION_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert intents[0]["function_name"] == "delete_enum_option"
    assert intents[0]["target_object_id"] == enum_config_id
    assert intents[0]["expected_result_object_id"] == enum_option_id
    assert intents[0]["kwargs"] == {
        "value": "assistant",
        "enum_option_id": enum_option_id,
    }
    assert "provider_delta_enum_option_delete_operation_executor_required" in (
        resolution.blockers
    )


def test_blocks_class_attribute_type_update_without_target_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": "op:update",
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_TYPE_UPDATE_OPERATION
                ),
                "semantic_key": "meta.attribute:TvChannel.device",
                "semantic_subject_type": "ClassConfigAttributeConfig",
                "field_path": "type",
                "after_payload": {"type": "Device"},
            },
        ),
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_attribute_type_update_requires_target_ref_for_class"
    )
    assert resolution.blockers == ("missing_class_target_ref",)
    assert resolution.evidence_payload()["would_execute"] is False


def test_unsupported_semantic_operation_is_not_mapped_to_function_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": "class:name:update",
                "operation_family": "update",
                "semantic_operation_type": (
                    "aware_meta.object_config_graph.class.name.update"
                ),
                "semantic_key": "meta.class:TvChannel",
                "semantic_subject_type": "ClassConfig",
                "field_path": "name",
                "after_payload": {"name": "Channel"},
            },
        ),
    )

    assert resolution.status == "unsupported_operation"
    assert resolution.function_call_plan is None
    assert resolution.blockers == (
        "unsupported_operation_type:"
        "aware_meta.object_config_graph.class.name.update",
    )


def test_meta_semantic_contract_advertises_operation_resolution_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_contract import (
        AWARE_META_SEMANTIC_CONTRACT,
        META_OBJECT_CONFIG_GRAPH_OWNER,
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA,
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
    )
    from aware_meta.semantic_operation_resolution import (
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
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION,
    )

    provider_role = AWARE_META_SEMANTIC_CONTRACT.package_role_for(
        role="aware_meta.provider"
    )
    assert provider_role is not None
    assert (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY
        in provider_role.capabilities
    )

    [participation] = (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION
    )
    assert participation.capability == (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY
    )
    assert participation.semantic_owner == META_OBJECT_CONFIG_GRAPH_OWNER
    assert participation.metadata == (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA
    )
    assert participation.metadata["contract_version"] == (
        META_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
    )
    assert participation.metadata["callable_module"] == (
        "aware_meta.semantic_operation_resolution"
    )
    assert participation.metadata["callable_name"] == (
        "resolve_meta_semantic_operation_function_call_plan_previews"
    )
    assert participation.metadata["supported_semantic_operation_types"] == (
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


def test_function_signature_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    function_config_id = "00000000-0000-0000-0000-000000000101"

    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )
    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.function.signature:"
                    "TvChannel.rename:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION
                ),
                "semantic_key": "meta.function:TvChannel.rename",
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "field_path": "signature",
                "after_payload": {
                    "class_name": "TvChannel",
                    "function_name": "rename",
                    "signature": "(label String) -> TvChannel",
                },
            },
        ),
        current_semantic_object_ids={
            "meta.function:TvChannel.rename": function_config_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_function_signature_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "function_config.update_config"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.function.update"
    )
    assert resolution.metadata["execution_ready"] is True
    assert resolution.metadata["receiver_object_id"] == function_config_id
    typed_operation_plan = resolution.metadata["provider_delta_typed_operation_plan"]
    assert isinstance(typed_operation_plan, Mapping)
    assert resolution.metadata["generated_materialization_intent_status"] == (
        "generated_materialization_intent_ready"
    )
    assert resolution.metadata["generated_materialization_intent_reason"] == (
        "function_signature_generated_materialization_intent_ready"
    )
    generated_intent = resolution.metadata["generated_materialization_intent"]
    assert isinstance(generated_intent, Mapping)
    assert generated_intent["intent_kind"] == (
        "meta_function_signature_generated_materialization_intent"
    )
    assert generated_intent["generated_materialization_provider_key"] == "aware_meta"
    assert generated_intent["provider_delta_typed_operation_plan"] == (
        typed_operation_plan
    )
    assert (
        resolution.metadata[
            "provider_delta_generated_materialization_typed_operation_plan"
        ]
        == typed_operation_plan
    )
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 2
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert intents[0]["function_name"] == "update_config"
    assert intents[0]["target_object_id"] == function_config_id
    assert intents[1]["function_name"] == "add_primitive_attribute_config"
    assert intents[1]["target_object_id"] == function_config_id
    assert intents[1]["kwargs"] == {
        "name": "label",
        "primitive_base_type": "string",
        "description": None,
        "default_value": None,
        "is_primary": False,
        "is_public": True,
        "is_required": True,
        "is_unique": False,
        "is_virtual": False,
        "type": "input",
        "position": 0,
        "is_identity_key": False,
    }
    assert "provider_delta_function_update_operation_executor_required" in (
        resolution.blockers
    )


def test_function_membership_constructor_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    function_config_id = "00000000-0000-0000-0000-000000000111"
    class_config_id = "00000000-0000-0000-0000-000000000112"
    edge_id = "00000000-0000-0000-0000-000000000113"
    graph_function_key = (
        "ocg:aware_content/node:aware_content.default.content.ContentLayout"
        "/function:rename"
    )

    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.function.membership:"
                    "ContentLayout.rename:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_FUNCTION_SIGNATURE_UPDATE_OPERATION
                ),
                "semantic_key": "meta.function:ContentLayout.rename",
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "field_path": "is_constructor",
                "package_name": "content-ontology",
                "package_root": "modules/content/ontology/structure",
                "source_refs": ("content/content_layout.aware",),
                "before_payload": {
                    "class_name": "ContentLayout",
                    "function_name": "rename",
                    "is_constructor": False,
                    "function_membership_signature": {
                        "is_public": True,
                        "is_constructor": False,
                        "position": 0,
                    },
                },
                "after_payload": {
                    "class_name": "ContentLayout",
                    "function_name": "rename",
                    "is_constructor": True,
                    "function_membership_signature": {
                        "is_public": True,
                        "is_constructor": True,
                        "position": 0,
                    },
                },
            },
        ),
        current_semantic_object_ids={
            "meta.class:ContentLayout": class_config_id,
        },
        baseline_semantic_object_identities={
            graph_function_key: {
                "object_id": function_config_id,
                "class_config_id": class_config_id,
                "class_config_function_config_id": edge_id,
                "function_config_id": function_config_id,
                "function_membership_semantic_key": (
                    "meta.function:ContentLayout.rename/membership:class_config"
                ),
                "function_membership_signature": {
                    "class_config_id": class_config_id,
                    "function_config_id": function_config_id,
                    "is_public": True,
                    "is_constructor": False,
                    "position": 0,
                },
                "owner_semantic_key": "meta.class:ContentLayout",
            },
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_function_signature_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["receiver_semantic_key"] == (
        "meta.class:ContentLayout"
    )
    assert resolution.metadata["receiver_object_id"] == class_config_id
    assert resolution.metadata["result_object_id"] == edge_id
    typed_operation = resolution.metadata["provider_delta_typed_operation"]
    assert isinstance(typed_operation, Mapping)
    assert typed_operation["provider_operation_type"] == (
        "meta_ocg.function_membership.update"
    )
    assert typed_operation["ontology_subject_kind"] == "function_membership"
    assert typed_operation["semantic_key"] == (
        "meta.function:ContentLayout.rename/membership:class_config"
    )
    current = cast(Mapping[str, object], typed_operation["current"])
    assert current["class_config_function_config_id"] == edge_id
    assert "entity_id" not in current
    assert current["function_config_id"] == function_config_id
    membership_signature = cast(
        Mapping[str, object],
        current["function_membership_signature"],
    )
    assert membership_signature["class_config_id"] == class_config_id
    assert membership_signature["function_config_id"] == function_config_id
    assert membership_signature["is_constructor"] is True
    assert "provider_delta_function_update_operation_executor_required" in (
        resolution.blockers
    )


def test_attribute_membership_identity_key_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    class_config_id = "00000000-0000-0000-0000-000000000121"
    attribute_config_id = "00000000-0000-0000-0000-000000000122"
    edge_id = "00000000-0000-0000-0000-000000000123"

    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.attribute.membership."
                    "identity_key:ContentLayout.name:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_MEMBERSHIP_UPDATE_OPERATION
                ),
                "semantic_key": (
                    "meta.attribute:ContentLayout.name/membership:class_config"
                ),
                "semantic_subject_type": (
                    "aware_meta.ClassConfigAttributeConfig"
                ),
                "field_path": "is_identity_key",
                "package_name": "content-ontology",
                "package_root": "modules/content/ontology/structure",
                "source_refs": ("content/content_layout.aware",),
                "before_payload": {
                    "class_name": "ContentLayout",
                    "attribute_name": "name",
                    "is_identity_key": False,
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "is_identity_key": False,
                    },
                },
                "after_payload": {
                    "class_name": "ContentLayout",
                    "attribute_name": "name",
                    "is_identity_key": True,
                    "attribute_membership_signature": {
                        "owner_kind": "class",
                        "is_identity_key": True,
                    },
                },
            },
        ),
        current_semantic_object_ids={
            "meta.class:ContentLayout": class_config_id,
            "meta.attribute:ContentLayout.name": attribute_config_id,
            "meta.class_attribute_edge:ContentLayout.name": edge_id,
        },
        baseline_semantic_object_identities={
            "meta.class_attribute_edge:ContentLayout.name": {
                "object_id": edge_id,
                "object_kind": "class_attribute_edge",
                "class_config_id": class_config_id,
                "class_config_attribute_config_id": edge_id,
                "attribute_config_id": attribute_config_id,
                "attribute_membership_signature": {
                    "owner_kind": "class",
                    "class_config_id": class_config_id,
                    "attribute_config_id": attribute_config_id,
                    "position": 0,
                    "is_identity_key": False,
                },
                "owner_semantic_key": "meta.class:ContentLayout",
            },
            "meta.attribute:ContentLayout.name": {
                "object_id": attribute_config_id,
                "class_config_id": class_config_id,
                "class_config_attribute_config_id": edge_id,
                "attribute_config_id": attribute_config_id,
                "attribute_membership_signature": {
                    "owner_kind": "class",
                    "class_config_id": class_config_id,
                    "attribute_config_id": attribute_config_id,
                    "position": 0,
                    "is_identity_key": False,
                },
                "owner_semantic_key": "meta.class:ContentLayout",
            },
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_attribute_membership_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.attribute_membership.update"
    )
    assert resolution.metadata["receiver_semantic_key"] == (
        "meta.class_attribute_edge:ContentLayout.name"
    )
    assert resolution.metadata["receiver_object_id"] == edge_id
    typed_operation = resolution.metadata["provider_delta_typed_operation"]
    assert isinstance(typed_operation, Mapping)
    assert typed_operation["provider_operation_type"] == (
        "meta_ocg.attribute_membership.update"
    )
    assert typed_operation["ontology_subject_kind"] == "attribute_membership"
    current = cast(Mapping[str, object], typed_operation["current"])
    assert current["class_config_attribute_config_id"] == edge_id
    signature = cast(
        Mapping[str, object],
        current["attribute_membership_signature"],
    )
    assert signature["class_config_id"] == class_config_id
    assert signature["attribute_config_id"] == attribute_config_id
    assert signature["is_identity_key"] is True
    assert "provider_delta_attribute_membership_update_operation_executor_required" in (
        resolution.blockers
    )


def test_function_delete_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    class_config_id = "00000000-0000-0000-0000-000000000201"
    class_source_object_id = "00000000-0000-0000-0000-000000000211"
    function_config_id = "00000000-0000-0000-0000-000000000202"
    executable_function_id = "00000000-0000-0000-0000-000000000212"

    from aware_meta.semantic_operation_resolution import (
        META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )
    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.function:"
                    "ContentLayout.render:delete"
                ),
                "operation_family": "delete",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_FUNCTION_DELETE_OPERATION
                ),
                "semantic_key": "meta.function:ContentLayout.render",
                "semantic_subject_type": "aware_meta.FunctionConfig",
                "field_path": "definition",
                "event_key": "meta.function:ContentLayout.render:definition:delete",
                "source_refs": ("content/content_layout.aware",),
                "before_payload": {
                    "class_name": "ContentLayout",
                    "class_fqn": "aware_content.default.content.ContentLayout",
                    "function_name": "render",
                    "name": "render",
                    "kind": "instance",
                    "definition": "fn render() -> String {\n    }",
                },
                "after_payload": None,
            },
        ),
        current_semantic_object_ids={
            "meta.class:ContentLayout": class_config_id,
            "meta.function:ContentLayout.render": executable_function_id,
        },
        baseline_semantic_object_identities={
            "meta.class:ContentLayout": {
                "semantic_source_object_id": class_source_object_id,
                "semantic_apply_receiver_object_id": class_config_id,
            },
            "meta.function:ContentLayout.render": {
                "semantic_source_object_id": function_config_id,
                "semantic_apply_receiver_object_id": executable_function_id,
                "generated_materialization": {
                    "python_orm": {
                        "relative_path": "aware_content_ontology/content/content_layout.py",
                    },
                },
            },
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_function_delete_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "function.object_config_graph_function_calls"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.function.delete"
    )
    assert resolution.metadata["execution_ready"] is True
    assert resolution.metadata["receiver_object_id"] == class_config_id
    assert resolution.metadata["result_object_id"] == function_config_id
    assert (
        resolution.metadata["semantic_apply_receiver_object_id"]
        == executable_function_id
    )
    assert resolution.metadata["semantic_source_object_id"] == function_config_id
    assert resolution.metadata["provider_delta_typed_operation_status"] == (
        "provider_delta_typed_operation_ready"
    )
    typed_operation_plan = resolution.metadata["provider_delta_typed_operation_plan"]
    assert isinstance(typed_operation_plan, Mapping)
    typed_operations = cast(
        Sequence[Mapping[str, object]],
        typed_operation_plan["typed_operations"],
    )
    [typed_operation] = typed_operations
    assert typed_operation["provider_operation_type"] == "meta_ocg.function.delete"
    current = cast(Mapping[str, object], typed_operation["current"])
    current_signature = cast(Mapping[str, object], current["function_signature"])
    current_membership = cast(
        Mapping[str, object],
        current["function_membership_signature"],
    )
    baseline = cast(Mapping[str, object], typed_operation["baseline"])
    baseline_object = cast(Mapping[str, object], baseline["object"])
    assert current["class_config_id"] == class_config_id
    assert current["function_config_id"] == function_config_id
    assert current["semantic_source_object_id"] == function_config_id
    assert current["semantic_apply_receiver_object_id"] == executable_function_id
    assert current["generated_materialization"] == {
        "python_orm": {
            "relative_path": "aware_content_ontology/content/content_layout.py",
        },
    }
    assert current_signature["owner_key"] == (
        "aware_content.default.content.ContentLayout"
    )
    assert current_signature["name"] == "render"
    assert current_signature["kind"] == "instance"
    assert current_membership["class_config_id"] == class_config_id
    assert current_membership["function_config_id"] == function_config_id
    assert baseline["object_id"] == function_config_id
    assert baseline["semantic_source_object_id"] == function_config_id
    assert baseline_object["class_config_id"] == class_config_id
    assert baseline_object["function_config_id"] == function_config_id
    assert baseline_object["semantic_source_object_id"] == function_config_id
    assert resolution.metadata["generated_materialization_intent_status"] == (
        "generated_materialization_intent_ready"
    )
    generated_intent = resolution.metadata["generated_materialization_intent"]
    assert isinstance(generated_intent, Mapping)
    assert generated_intent["intent_kind"] == (
        "meta_function_delete_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_FUNCTION_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["renderer_key"] == "python.orm.function"
    assert generated_intent["policy_key"] == "aware_meta.python_orm.function.delete"
    assert (
        generated_intent["provider_delta_typed_operation_plan"]
        == typed_operation_plan
    )

    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    [intent] = intents
    assert intent["function_name"] == "remove_function_config"
    assert intent["target_object_id"] == class_config_id
    assert intent["expected_result_object_id"] == function_config_id
    assert intent["kwargs"] == {
        "name": "render",
        "function_config_id": function_config_id,
    }
    assert "provider_delta_function_delete_operation_executor_required" in (
        resolution.blockers
    )


def test_function_impl_body_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.function_impl.body:"
                    "TvChannel.rename:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION
                ),
                "semantic_key": "meta.function_impl:TvChannel.rename:default",
                "semantic_subject_type": "aware_meta.FunctionImpl",
                "field_path": "body_text",
                "after_payload": {
                    "class_name": "TvChannel",
                    "function_name": "rename",
                    "body_text": "{\n    set name = display_name\n}\n",
                },
            },
        ),
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "function_impl.additive_instruction_body"
    )
    assert resolution.metadata["requires_multi_invocation_ontology_operation"] is True
    assert resolution.metadata["provider_delta_typed_operation_status"] == (
        "provider_delta_typed_operation_blocked"
    )
    raw_blockers = resolution.metadata["provider_delta_typed_operation_blockers"]
    assert isinstance(raw_blockers, Sequence)
    assert "function_impl_object_id_unavailable" in tuple(
        str(item) for item in raw_blockers
    )
    assert "provider_delta_function_impl_operation_executor_required" in (
        resolution.blockers
    )


def test_relationship_load_policy_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    relationship_config_id = "00000000-0000-0000-0000-000000000201"

    from aware_meta.semantic_operation_resolution import (
        META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )
    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.relationship.load_policy:"
                    "RemoteControl.selected_channel:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_LOAD_POLICY_UPDATE_OPERATION
                ),
                "semantic_key": ("meta.relationship:RemoteControl.selected_channel"),
                "semantic_subject_type": ("aware_meta.ClassConfigRelationship"),
                "field_path": "load_policy_args",
                "event_key": (
                    "meta.relationship:RemoteControl.selected_channel:"
                    "load_policy_args:upsert"
                ),
                "source_refs": ("home/tv_channel.aware",),
                "after_payload": {
                    "load_policy_args": "forward eager",
                    "class_fqn": "home.RemoteControl",
                    "class_name": "RemoteControl",
                    "relationship_key": "selected_channel",
                    "relationship_type": "many_to_one",
                    "target_class_fqn": "home.TvChannel",
                },
                "requires_baseline_object_identity": True,
            },
        ),
        current_semantic_object_ids={
            "meta.relationship:RemoteControl.selected_channel": (
                relationship_config_id
            ),
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.function_call_plan is None
    assert resolution.reason == (
        "meta_ocg_relationship_load_policy_update_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["semantic_apply_boundary"] == (
        "provider_delta_ontology_operation_executor"
    )
    assert resolution.metadata["provider_delta_handler_key"] == (
        "relationship.class_config_function_calls"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.relationship.update"
    )
    assert resolution.metadata["execution_ready"] is True
    assert resolution.metadata["receiver_object_id"] == relationship_config_id
    assert resolution.metadata["provider_delta_typed_operation_status"] == (
        "provider_delta_typed_operation_ready"
    )
    typed_operation_plan = resolution.metadata["provider_delta_typed_operation_plan"]
    assert isinstance(typed_operation_plan, Mapping)
    typed_operations = _sequence(typed_operation_plan["typed_operations"])
    typed_operation = _mapping(typed_operations[0])
    assert typed_operation["ontology_subject_kind"] == "relationship"
    assert typed_operation["provider_operation_type"] == (
        "meta_ocg.relationship.update"
    )
    current = _mapping(typed_operation["current"])
    assert current["class_config_relationship_id"] == relationship_config_id
    assert current["relationship_type"] == "many_to_one"
    assert current["forward_loading_strategy"] == "eager"
    assert resolution.metadata["generated_materialization_intent_status"] == (
        "generated_materialization_intent_ready"
    )
    assert resolution.metadata["generated_materialization_intent_reason"] == (
        "relationship_load_policy_generated_materialization_intent_ready"
    )
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_relationship_load_policy_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_RELATIONSHIP_LOAD_POLICY_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["generated_materialization_provider_key"] == ("aware_meta")
    assert (
        resolution.metadata[
            "provider_delta_generated_materialization_typed_operation_plan"
        ]
        == typed_operation_plan
    )

    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 1
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert intents[0]["function_name"] == "update_config"
    assert intents[0]["target_object_id"] == relationship_config_id
    kwargs = _mapping(intents[0]["kwargs"])
    assert kwargs["relationship_type"] == "many_to_one"
    assert kwargs["forward_loading_strategy"] == "eager"
    assert "provider_delta_relationship_update_operation_executor_required" in (
        resolution.blockers
    )


def test_relationship_create_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    source_class_id = "00000000-0000-0000-0000-000000000301"
    target_class_id = "00000000-0000-0000-0000-000000000302"

    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.relationship:"
                    "ContentLayout.placements:create"
                ),
                "operation_family": "create",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION
                ),
                "semantic_key": "meta.relationship:ContentLayout.placements",
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "field_path": "definition",
                "event_key": (
                    "meta.relationship:ContentLayout.placements:definition:upsert"
                ),
                "source_refs": ("content/content_layout.aware",),
                "after_payload": {
                    "definition": "placements ContentPlacement[]",
                    "class_name": "ContentLayout",
                    "class_fqn": "content.ContentLayout",
                    "relationship_key": "placements",
                    "relationship_type": "one_to_many",
                    "target_class_name": "ContentPlacement",
                    "target_class_fqn": "content.ContentPlacement",
                },
                "requires_baseline_object_identity": False,
            },
        ),
        current_semantic_object_ids={
            "meta.class:ContentLayout": source_class_id,
            "meta.class:ContentPlacement": target_class_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_relationship_create_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.relationship.create"
    )
    assert resolution.metadata["receiver_object_id"] == source_class_id
    assert resolution.metadata["execution_ready"] is True
    relationship_id = resolution.metadata["result_object_id"]
    assert isinstance(relationship_id, str)
    assert relationship_id
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    [typed_operation_raw] = _sequence(typed_plan["typed_operations"])
    typed_operation = _mapping(typed_operation_raw)
    assert typed_operation["provider_operation_type"] == "meta_ocg.relationship.create"
    current = _mapping(typed_operation["current"])
    assert current["relationship_config_id"] == relationship_id
    assert current["source_class_config_id"] == source_class_id
    assert current["target_class_config_id"] == target_class_id
    assert current["relationship_key"] == "placements"
    assert current["relationship_type"] == "one_to_many"
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_relationship_create_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_RELATIONSHIP_CREATE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert intents[0]["function_name"] == "create_relationship"
    assert intents[0]["target_object_id"] == source_class_id
    assert intents[0]["expected_result_object_id"] == relationship_id
    kwargs = _mapping(intents[0]["kwargs"])
    assert kwargs["target_class_config_id"] == target_class_id
    assert kwargs["relationship_key"] == "placements"
    assert kwargs["relationship_type"] == "one_to_many"
    assert "provider_delta_relationship_create_operation_executor_required" in (
        resolution.blockers
    )


def test_relationship_delete_resolution_requests_provider_delta_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)
    source_class_id = "00000000-0000-0000-0000-000000000401"
    relationship_id = "00000000-0000-0000-0000-000000000402"

    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION,
        META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.relationship:"
                    "ContentLayout.placements:delete"
                ),
                "operation_family": "delete",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_DELETE_OPERATION
                ),
                "semantic_key": "meta.relationship:ContentLayout.placements",
                "semantic_subject_type": "aware_meta.ClassConfigRelationship",
                "field_path": "definition",
                "event_key": (
                    "meta.relationship:ContentLayout.placements:definition:delete"
                ),
                "source_refs": ("content/content_layout.aware",),
                "before_payload": {
                    "definition": "placements ContentPlacement[]",
                    "class_name": "ContentLayout",
                    "class_fqn": "content.ContentLayout",
                    "relationship_key": "placements",
                    "relationship_type": "one_to_many",
                    "target_class_name": "ContentPlacement",
                    "target_class_fqn": "content.ContentPlacement",
                },
                "after_payload": None,
                "requires_baseline_object_identity": True,
            },
        ),
        current_semantic_object_ids={
            "meta.class:ContentLayout": source_class_id,
            "meta.relationship:ContentLayout.placements": relationship_id,
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.reason == (
        "meta_ocg_relationship_delete_requires_provider_delta_"
        "ontology_operation_executor"
    )
    assert resolution.metadata["provider_operation_type"] == (
        "meta_ocg.relationship.delete"
    )
    assert resolution.metadata["receiver_object_id"] == source_class_id
    assert resolution.metadata["result_object_id"] == relationship_id
    assert resolution.metadata["execution_ready"] is True
    typed_plan = _mapping(resolution.metadata["provider_delta_typed_operation_plan"])
    [typed_operation_raw] = _sequence(typed_plan["typed_operations"])
    typed_operation = _mapping(typed_operation_raw)
    assert typed_operation["provider_operation_type"] == "meta_ocg.relationship.delete"
    current = _mapping(typed_operation["current"])
    baseline = _mapping(typed_operation["baseline"])
    baseline_object = _mapping(baseline["object"])
    assert current["source_class_config_id"] == source_class_id
    assert current["relationship_config_id"] == relationship_id
    assert baseline_object["relationship_config_id"] == relationship_id
    generated_intent = _mapping(resolution.metadata["generated_materialization_intent"])
    assert generated_intent["intent_kind"] == (
        "meta_relationship_delete_generated_materialization_intent"
    )
    assert generated_intent["contract_version"] == (
        META_RELATIONSHIP_DELETE_GENERATED_MATERIALIZATION_INTENT_CONTRACT_VERSION
    )
    assert generated_intent["status"] == "generated_materialization_intent_ready"
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_plan,
    )
    intents = cast(Sequence[Mapping[str, object]], ontology_plan["invocation_intents"])
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert intents[0]["function_name"] == "remove_relationship_config"
    assert intents[0]["target_object_id"] == source_class_id
    assert intents[0]["expected_result_object_id"] == relationship_id
    assert intents[0]["kwargs"] == {
        "relationship_key": "placements",
        "relationship_config_id": relationship_id,
    }
    assert "provider_delta_relationship_delete_operation_executor_required" in (
        resolution.blockers
    )


def test_function_impl_body_resolution_normalizes_provider_delta_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_meta.materialization.deltas.ontology_execution.service import (
        build_provider_delta_ontology_execution_plan,
    )
    from aware_meta.semantic_operation_resolution import (
        META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION,
        resolve_meta_semantic_operation_function_call_plan_previews,
    )

    function_impl_id = "00000000-0000-0000-0000-000000000101"
    target_edge_id = "00000000-0000-0000-0000-000000000102"
    source_input_id = "00000000-0000-0000-0000-000000000103"
    function_config_id = "00000000-0000-0000-0000-000000000104"
    [resolution] = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            {
                "operation_key": (
                    "aware_meta.object_config_graph.function_impl.body:"
                    "TvChannel.rename:update"
                ),
                "operation_family": "update",
                "semantic_operation_type": (
                    META_OBJECT_CONFIG_GRAPH_FUNCTION_IMPL_BODY_UPDATE_OPERATION
                ),
                "semantic_key": "meta.function_impl:TvChannel.rename:default",
                "semantic_subject_type": "aware_meta.FunctionImpl",
                "field_path": "body_text",
                "source_refs": ("home/tv_channel.aware",),
                "before_payload": {
                    "class_name": "TvChannel",
                    "function_name": "rename",
                    "function_description": (
                        "Rename the channel display label for humans and " "assistants."
                    ),
                    "body_text": (
                        "{\n"
                        '    """\n'
                        "    Rename the channel display label for humans and "
                        "assistants.\n"
                        '    """\n'
                        "}\n"
                    ),
                },
                "after_payload": {
                    "class_name": "TvChannel",
                    "function_name": "rename",
                    "function_description": (
                        "Rename the channel display label for humans and " "assistants."
                    ),
                    "body_text": "{\n    set name = display_name\n}\n",
                },
            },
        ),
        current_semantic_object_ids={
            "meta.function_impl:TvChannel.rename:default": function_impl_id,
            "meta.function:TvChannel.rename": function_config_id,
            "meta.class_attribute_edge:TvChannel.name": target_edge_id,
            "meta.function_input_edge:TvChannel.rename.display_name": (source_input_id),
        },
    )

    assert resolution.status == "function_call_plan_blocked"
    assert resolution.metadata["provider_delta_typed_operation_status"] == (
        "provider_delta_typed_operation_ready"
    )
    assert resolution.metadata["execution_ready"] is True
    typed_operation = resolution.metadata["provider_delta_typed_operation"]
    assert isinstance(typed_operation, Mapping)
    assert typed_operation["ontology_subject_kind"] == "function_impl"
    assert typed_operation["provider_operation_type"] == (
        "meta_ocg.function_impl.update"
    )
    current = typed_operation["current"]
    assert isinstance(current, Mapping)
    signature = current["function_impl_signature"]
    assert isinstance(signature, Mapping)
    assert signature["instruction_count"] == 1
    instructions = cast(Sequence[object], signature["instructions"])
    [instruction] = instructions
    assert isinstance(instruction, Mapping)
    assert instruction["type"] == "set"
    set_payload = instruction["set"]
    assert isinstance(set_payload, Mapping)
    assert set_payload["target_class_config_attribute_config_id"] == target_edge_id
    value_source = set_payload["value_source"]
    assert isinstance(value_source, Mapping)
    assert value_source["source_function_config_attribute_config_id"] == source_input_id

    typed_operation_plan = resolution.metadata["provider_delta_typed_operation_plan"]
    assert isinstance(typed_operation_plan, Mapping)
    ontology_plan = build_provider_delta_ontology_execution_plan(
        request=SimpleNamespace(),
        provider_delta_typed_operation_plan=typed_operation_plan,
    )
    assert ontology_plan["status"] == "ontology_execution_plan_ready"
    assert ontology_plan["invocation_intent_count"] == 3

    assert resolution.metadata["generated_materialization_intent_status"] == (
        "generated_materialization_intent_ready"
    )
    generated_plan = resolution.metadata[
        "provider_delta_generated_materialization_typed_operation_plan"
    ]
    assert isinstance(generated_plan, Mapping)
    assert generated_plan["status"] == "typed_operation_plan_ready"
    [generated_operation] = cast(
        Sequence[Mapping[str, object]],
        generated_plan["typed_operations"],
    )
    assert generated_operation["ontology_subject_kind"] == "function_invocation"
    assert generated_operation["operation_family"] == "create"
    assert generated_operation["would_execute"] is False
    assert generated_operation["would_persist"] is False
    assert generated_operation["intent_only"] is True
    assert generated_operation["semantic_key"] == (
        "meta.function:TvChannel.rename/invocation:function_impl_body"
    )
    current_generated = generated_operation["current"]
    assert isinstance(current_generated, Mapping)
    assert current_generated["function_config_id"] == function_config_id
    generated_materialization = current_generated["generated_materialization"]
    assert isinstance(generated_materialization, Mapping)
    python_orm = generated_materialization["python_orm"]
    assert isinstance(python_orm, Mapping)
    assert python_orm["baseline_body_text"] == (
        '"""Rename the channel display label for humans and assistants."""\n'
        "        raise NotImplementedError"
    )
    assert python_orm["body_text"] == (
        "self.name = display_name\n" "        return self"
    )


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping)
    return value


def _sequence(value: object) -> Sequence[object]:
    assert isinstance(value, Sequence)
    assert not isinstance(value, (str, bytes))
    return value
