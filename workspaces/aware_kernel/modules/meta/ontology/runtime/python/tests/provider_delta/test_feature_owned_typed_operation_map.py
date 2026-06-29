from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from aware_meta.attribute.config.deltas.typed_operations import (
    attribute_config_create_typed_operation,
)
from aware_meta.class_.config.deltas.typed_operations import (
    class_config_create_typed_operation,
)
from aware_meta.function.config.deltas.typed_operations import (
    function_config_create_typed_operation,
    function_invocation_create_typed_operation,
)
from aware_meta.graph.config.deltas.typed_operations import (
    object_config_graph_create_typed_operation,
)
from aware_meta.graph.package.deltas.typed_operations import (
    object_config_graph_package_attach_graph_typed_operation,
    object_config_graph_package_create_typed_operation,
)
from aware_meta.graph.projection.deltas.typed_operations import (
    object_projection_graph_create_typed_operation,
    object_projection_graph_node_create_typed_operation,
)
from aware_meta.materialization.deltas.feature_registry import (
    registered_feature_providers,
)
from aware_meta.materialization.deltas.ocg_genesis import (
    OCG_GENESIS_COMPOSITION_KEY,
    MetaOcgGenesisSpec,
    ocg_genesis_typed_operation_plan,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)

from .fixtures import provider_delta_uuid


def test_ocg_genesis_composes_feature_owned_typed_operations() -> None:
    spec = _genesis_spec()
    plan = ocg_genesis_typed_operation_plan(spec=spec)
    operations = cast(Sequence[Mapping[str, object]], plan["typed_operations"])

    assert tuple(dict(operation) for operation in operations) == tuple(
        operation.evidence_payload() for operation in _genesis_operations(spec=spec)
    )


def test_feature_owned_genesis_helpers_return_typed_value_objects() -> None:
    spec = _genesis_spec()
    operations = _genesis_operations(spec=spec)
    operation_keys = tuple(operation.operation_key for operation in operations)

    assert all(
        isinstance(operation, MetaProviderDeltaTypedOperation)
        for operation in operations
    )
    assert all("genesis" not in operation_key for operation_key in operation_keys)
    assert operation_keys == (
        f"meta_ocg.object_config_graph_package.create:{spec.package_semantic_key}",
        f"meta_ocg.object_config_graph.create:{spec.graph_semantic_key}",
        (
            "meta_ocg.object_config_graph_package.update.attach_graph:"
            f"{spec.package_semantic_key}"
        ),
        f"meta_ocg.class.create:{spec.class_semantic_key}",
        f"meta_ocg.attribute.create:{spec.attribute_semantic_key}",
        (
            "meta_ocg.object_projection_graph.create:"
            f"{spec.object_projection_graph_semantic_key}"
        ),
        (
            "meta_ocg.object_projection_graph_node.create:"
            f"{spec.object_projection_graph_node_semantic_key}"
        ),
    )


def test_ocg_genesis_keeps_composition_context_at_plan_level() -> None:
    spec = _genesis_spec()
    plan = ocg_genesis_typed_operation_plan(spec=spec)
    composition = cast(Mapping[str, object], plan["operation_composition"])
    operations = cast(Sequence[Mapping[str, object]], plan["typed_operations"])

    assert composition == {
        "composition_key": OCG_GENESIS_COMPOSITION_KEY,
        "composition_kind": "meta_ocg_package_genesis",
        "package_semantic_key": spec.package_semantic_key,
        "graph_semantic_key": spec.graph_semantic_key,
    }
    assert all(
        "genesis" not in str(operation["operation_key"]) for operation in operations
    )


def test_class_create_typed_operation_identity_is_reusable_outside_genesis() -> None:
    spec = _genesis_spec()
    operation = class_config_create_typed_operation(
        semantic_key="ocg:aware_demo/node:aware_demo.NewClass",
        graph_semantic_key=spec.graph_semantic_key,
        object_config_graph_node_id=str(
            provider_delta_uuid("feature-owned-existing-graph-node")
        ),
        class_config_id=str(provider_delta_uuid("feature-owned-existing-graph-class")),
        node_key="aware_demo.NewClass",
        class_fqn="aware_demo.NewClass",
        class_name="NewClass",
        source_refs=(spec.source_ref,),
        description="A class added after genesis.",
    )

    assert isinstance(operation, MetaProviderDeltaTypedOperation)
    assert operation.operation_key == (
        "meta_ocg.class.create:ocg:aware_demo/node:aware_demo.NewClass"
    )
    assert "genesis" not in operation.operation_key


def test_function_create_typed_operation_identity_is_reusable_outside_genesis() -> None:
    spec = _genesis_spec()
    operation = function_config_create_typed_operation(
        semantic_key=f"{spec.class_semantic_key}/function:create_scene",
        owner_semantic_key=spec.class_semantic_key,
        class_config_id=spec.class_config_id,
        function_config_id=str(provider_delta_uuid("feature-owned-function-create")),
        function_name="create_scene",
        owner_key=spec.class_fqn,
        source_refs=(spec.source_ref,),
        description="Create a scene.",
        verb="create",
        is_async=True,
        kind="constructor",
        is_public=True,
        is_constructor=True,
        position=1,
    )

    assert isinstance(operation, MetaProviderDeltaTypedOperation)
    assert operation.operation_key == (
        f"meta_ocg.function.create:{spec.class_semantic_key}/function:create_scene"
    )
    assert operation.provider_operation_type == "meta_ocg.function.create"
    assert "genesis" not in operation.operation_key


def test_function_invocation_create_typed_operation_identity_is_reusable_outside_genesis() -> (
    None
):
    spec = _genesis_spec()
    target_function_config_id = str(
        provider_delta_uuid("feature-owned-function-invocation-target")
    )
    invocation_id = str(provider_delta_uuid("feature-owned-function-invocation"))
    operation = function_invocation_create_typed_operation(
        semantic_key=(f"{spec.class_semantic_key}/function:create_scene/invocation:0"),
        function_semantic_key=(f"{spec.class_semantic_key}/function:create_scene"),
        function_config_id=str(provider_delta_uuid("feature-owned-function-create")),
        function_config_invocation_id=invocation_id,
        position=0,
        kind="call",
        target_function_config_id=target_function_config_id,
        relationship_fingerprint="owner",
        source_refs=(spec.source_ref,),
    )

    assert isinstance(operation, MetaProviderDeltaTypedOperation)
    assert operation.operation_key == (
        "meta_ocg.function_invocation.create:"
        f"{spec.class_semantic_key}/function:create_scene/invocation:0"
    )
    assert operation.provider_operation_type == ("meta_ocg.function_invocation.create")
    assert operation.ontology_subject_kind == "function_invocation"
    assert "genesis" not in operation.operation_key


def test_feature_registry_includes_package_graph_and_function_handlers() -> None:
    providers = {
        provider.feature_key: provider for provider in registered_feature_providers()
    }

    package_provider = providers["object_config_graph_package"]
    graph_provider = providers["object_config_graph"]
    projection_provider = providers["object_projection_graph"]
    function_provider = providers["function_config"]
    relationship_provider = providers["relationship_config"]
    assert package_provider.ontology_subject_kinds == ("object_config_graph_package",)
    assert [
        registration.handler_key
        for registration in package_provider.ontology_operation_registrations
    ] == ["object_config_graph_package.function_calls"]
    assert package_provider.source_projection_builder is None
    assert graph_provider.ontology_subject_kinds == ("object_config_graph",)
    assert [
        registration.handler_key
        for registration in graph_provider.ontology_operation_registrations
    ] == ["object_config_graph.function_calls"]
    assert graph_provider.source_projection_builder is None
    assert projection_provider.ontology_subject_kinds == (
        "object_projection_graph",
        "object_projection_graph_node",
    )
    assert [
        registration.handler_key
        for registration in projection_provider.ontology_operation_registrations
    ] == [
        "object_projection_graph.function_calls",
        "object_projection_graph.function_calls",
    ]
    assert projection_provider.source_projection_builder is None
    assert function_provider.ontology_subject_kinds == (
        "function",
        "function_membership",
        "function_invocation",
    )
    assert [
        registration.handler_key
        for registration in function_provider.typed_operation_dirty_entry_planner_registrations
    ] == [
        "function.create.scope_closure",
        "function.update.scope_closure_and_split_membership",
        "function.invocation_plan.create",
    ]
    assert [
        registration.handler_key
        for registration in function_provider.ontology_operation_registrations
    ] == [
        "function.scalar_function_calls",
        "function_membership.class_config_function_config_calls",
        "function.invocation_plan_function_calls",
    ]
    assert function_provider.source_projection_builder is not None
    assert function_provider.generated_materialization_builder is not None
    assert relationship_provider.ontology_subject_kinds == ("relationship",)
    assert [
        registration.handler_key
        for registration in relationship_provider.typed_operation_dirty_entry_planner_registrations
    ] == ["relationship.scope_closure"]
    assert [
        registration.handler_key
        for registration in relationship_provider.ontology_operation_registrations
    ] == ["relationship.class_config_function_calls"]


def _genesis_operations(
    *,
    spec: MetaOcgGenesisSpec,
) -> tuple[MetaProviderDeltaTypedOperation, ...]:
    return (
        object_config_graph_package_create_typed_operation(
            package_name=spec.package_name,
            fqn_prefix=spec.fqn_prefix,
            package_id=spec.package_id,
            semantic_key=spec.package_semantic_key,
            source_refs=(spec.source_ref,),
            title=spec.package_title,
            description=spec.package_description,
        ),
        object_config_graph_create_typed_operation(
            fqn_prefix=spec.fqn_prefix,
            semantic_key=spec.graph_semantic_key,
            object_config_graph_id=spec.object_config_graph_id,
            name=spec.resolved_graph_name,
            source_refs=(spec.source_ref,),
            graph_hash=spec.graph_hash,
            layout_hash=spec.layout_hash,
            language=spec.language,
            description=spec.package_description,
        ),
        object_config_graph_package_attach_graph_typed_operation(
            package_name=spec.package_name,
            package_id=spec.package_id,
            object_config_graph_id=spec.object_config_graph_id,
            semantic_key=spec.package_semantic_key,
            source_refs=(spec.source_ref,),
            title=spec.package_title,
            description=spec.package_description,
        ),
        class_config_create_typed_operation(
            semantic_key=spec.class_semantic_key,
            graph_semantic_key=spec.graph_semantic_key,
            object_config_graph_node_id=spec.object_config_graph_node_id,
            class_config_id=spec.class_config_id,
            node_key=spec.class_fqn,
            class_fqn=spec.class_fqn,
            class_name=spec.class_name,
            source_refs=(spec.source_ref,),
            description=spec.class_description,
        ),
        attribute_config_create_typed_operation(
            semantic_key=spec.attribute_semantic_key,
            attribute_config_id=spec.attribute_config_id,
            owner_semantic_key=spec.class_semantic_key,
            attribute_name=spec.attribute_name,
            source_refs=(spec.source_ref,),
            primitive_base_type=spec.primitive_base_type,
            description=spec.attribute_description,
        ),
        object_projection_graph_create_typed_operation(
            semantic_key=spec.object_projection_graph_semantic_key,
            graph_semantic_key=spec.graph_semantic_key,
            object_config_graph_id=spec.object_config_graph_id,
            object_projection_graph_id=spec.object_projection_graph_id,
            name=spec.resolved_projection_name,
            projection_hash=spec.projection_hash,
            source_refs=(spec.source_ref,),
            language=spec.language,
            description=spec.projection_description,
            supports_virtual_build=spec.projection_supports_virtual_build,
        ),
        object_projection_graph_node_create_typed_operation(
            semantic_key=spec.object_projection_graph_node_semantic_key,
            object_projection_graph_semantic_key=(
                spec.object_projection_graph_semantic_key
            ),
            object_projection_graph_id=spec.object_projection_graph_id,
            object_projection_graph_node_id=(spec.object_projection_graph_node_id),
            class_config_id=spec.class_config_id,
            source_refs=(spec.source_ref,),
            is_root=True,
            required_for_validity=spec.projection_node_required_for_validity,
            selection=spec.projection_node_selection,
        ),
    )


def _genesis_spec() -> MetaOcgGenesisSpec:
    return MetaOcgGenesisSpec(
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        source_ref="aware/home/model.aware",
        package_id=str(provider_delta_uuid("feature-owned-genesis-package")),
        object_config_graph_id=str(provider_delta_uuid("feature-owned-genesis-graph")),
        object_config_graph_node_id=str(
            provider_delta_uuid("feature-owned-genesis-node")
        ),
        class_config_id=str(provider_delta_uuid("feature-owned-genesis-class")),
        attribute_config_id=str(provider_delta_uuid("feature-owned-genesis-attribute")),
        object_projection_graph_id=str(
            provider_delta_uuid("feature-owned-genesis-opg")
        ),
        object_projection_graph_node_id=str(
            provider_delta_uuid("feature-owned-genesis-opg-node")
        ),
        class_name="Room",
        attribute_name="name",
        graph_hash="sha256:ocg-genesis",
        layout_hash="sha256:layout",
        projection_name="Demo",
        projection_hash="sha256:opg-genesis",
        package_title="Demo ontology",
        package_description="Demo package.",
        class_description="Room in a demo home.",
        attribute_description="Human-readable room name.",
    )
