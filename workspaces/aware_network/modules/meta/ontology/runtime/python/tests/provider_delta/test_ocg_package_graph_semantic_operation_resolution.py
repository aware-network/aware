from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.feature_registry import (
    semantic_operation_resolver_for_type,
)
from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
    resolve_meta_semantic_operation_function_call_plan_previews,
)
from aware_meta.graph.config.stable_ids import (
    stable_class_config_id,
    stable_object_config_graph_id,
    stable_object_config_graph_identity_id,
    stable_object_config_graph_node_id,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id


PACKAGE_NAME = "content-ontology"
FQN_PREFIX = "aware_content"
GRAPH_SEMANTIC_KEY = f"ocg:{FQN_PREFIX}"
GRAPH_IDENTITY_SEMANTIC_KEY = f"{GRAPH_SEMANTIC_KEY}/identity"
PACKAGE_SEMANTIC_KEY = f"ocg_package:{PACKAGE_NAME}"
CLASS_NAME = "DeltaReadyContent"
CLASS_FQN = f"{FQN_PREFIX}.content.{CLASS_NAME}"
CLASS_SEMANTIC_KEY = f"{GRAPH_SEMANTIC_KEY}/node:{CLASS_FQN}"
FUNCTION_NAME = "rename"
FUNCTION_SEMANTIC_KEY = f"{CLASS_SEMANTIC_KEY}/function:{FUNCTION_NAME}"


def test_package_graph_semantic_operation_resolvers_are_registered() -> None:
    assert (
        semantic_operation_resolver_for_type(
            META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
        )
        is not None
    )
    assert (
        semantic_operation_resolver_for_type(META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION)
        is not None
    )
    assert (
        semantic_operation_resolver_for_type(
            META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
        )
        is not None
    )
    assert (
        semantic_operation_resolver_for_type(
            META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
        )
        is not None
    )


def test_package_graph_chain_resolves_provider_delta_typed_operations() -> None:
    graph_id = str(
        stable_object_config_graph_id(fqn_prefix=FQN_PREFIX, language="aware")
    )
    package_id = str(
        stable_object_config_graph_package_id(
            package_name=PACKAGE_NAME,
            fqn_prefix=FQN_PREFIX,
        )
    )
    graph_identity_id = str(
        stable_object_config_graph_identity_id(key=f"{FQN_PREFIX}:aware")
    )

    resolutions = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            _package_create_operation(package_id=package_id),
            _graph_identity_create_operation(graph_identity_id=graph_identity_id),
            _graph_create_operation(graph_id=graph_id),
            _package_attach_graph_operation(
                package_id=package_id,
                graph_id=graph_id,
            ),
        ),
    )

    provider_operation_types = tuple(
        _provider_delta_operation_type(resolution.metadata)
        for resolution in resolutions
    )
    assert provider_operation_types == (
        "meta_ocg.object_config_graph_package.create",
        "meta_ocg.object_config_graph_identity.create",
        "meta_ocg.object_config_graph.create",
        "meta_ocg.object_config_graph_package.update",
    )
    for resolution in resolutions:
        assert resolution.status == "function_call_plan_blocked"
        assert (
            resolution.metadata.get("semantic_apply_boundary")
            == "provider_delta_ontology_operation_executor"
        )
        assert (
            resolution.metadata.get("provider_delta_typed_operation_status")
            == "provider_delta_typed_operation_ready"
        )
        typed_plan = _mapping(
            resolution.metadata.get("provider_delta_typed_operation_plan")
        )
        assert typed_plan.get("status") == "typed_operation_plan_ready"
        assert typed_plan.get("typed_operation_count") == 1


def test_same_batch_function_create_uses_provider_delta_when_owner_is_new() -> None:
    graph_id = str(
        stable_object_config_graph_id(fqn_prefix=FQN_PREFIX, language="aware")
    )
    class_node_id = str(
        stable_object_config_graph_node_id(
            object_config_graph_id=stable_object_config_graph_id(
                fqn_prefix=FQN_PREFIX,
                language="aware",
            ),
            type=ObjectConfigGraphNodeType.class_.value,
            node_key=CLASS_FQN,
        )
    )
    class_config_id = str(
        stable_class_config_id(
            object_config_graph_node_id=stable_object_config_graph_node_id(
                object_config_graph_id=stable_object_config_graph_id(
                    fqn_prefix=FQN_PREFIX,
                    language="aware",
                ),
                type=ObjectConfigGraphNodeType.class_.value,
                node_key=CLASS_FQN,
            ),
            class_fqn=CLASS_FQN,
        )
    )

    (resolution,) = resolve_meta_semantic_operation_function_call_plan_previews(
        typed_operations=(
            _function_create_operation(
                graph_id=graph_id,
                class_node_id=class_node_id,
                class_config_id=class_config_id,
            ),
        ),
    )

    assert resolution.status == "function_call_plan_blocked"
    assert (
        resolution.reason
        == "meta_ocg_function_create_requires_provider_delta_ontology_operation_executor"
    )
    assert resolution.function_call_plan is None
    assert (
        resolution.metadata.get("provider_delta_handler_key")
        == "function.scalar_function_calls"
    )
    assert (
        resolution.metadata.get("provider_delta_typed_operation_status")
        == "provider_delta_typed_operation_ready"
    )
    assert (
        resolution.metadata.get("generated_materialization_intent_status")
        == "generated_materialization_intent_ready"
    )
    typed_plan = _mapping(resolution.metadata.get("provider_delta_typed_operation_plan"))
    assert typed_plan.get("status") == "typed_operation_plan_ready"
    typed_operations = _sequence(typed_plan.get("typed_operations"))
    assert len(typed_operations) == 1
    typed_operation = _mapping(typed_operations[0])
    assert typed_operation.get("provider_operation_type") == "meta_ocg.function.create"


def _package_create_operation(*, package_id: str) -> dict[str, object]:
    return {
        "operation_key": "proof.package.create",
        "operation_family": "create",
        "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphPackage",
        "semantic_key": PACKAGE_SEMANTIC_KEY,
        "package_name": PACKAGE_NAME,
        "fqn_prefix": FQN_PREFIX,
        "source_refs": ("content/content_delta_ready.aware",),
        "before_payload": {},
        "after_payload": {
            "package_name": PACKAGE_NAME,
            "fqn_prefix": FQN_PREFIX,
            "object_config_graph_package_id": package_id,
            "title": "Content ontology",
            "description": "Content ontology package.",
        },
    }


def _graph_create_operation(*, graph_id: str) -> dict[str, object]:
    return {
        "operation_key": "proof.graph.create",
        "operation_family": "create",
        "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION,
        "semantic_subject_type": "aware_meta.ObjectConfigGraph",
        "semantic_key": GRAPH_SEMANTIC_KEY,
        "package_name": PACKAGE_NAME,
        "fqn_prefix": FQN_PREFIX,
        "source_refs": ("content/content_delta_ready.aware",),
        "before_payload": {},
        "after_payload": {
            "name": "content",
            "fqn_prefix": FQN_PREFIX,
            "language": "aware",
            "hash": "sha256:content-delta-ready",
            "object_config_graph_id": graph_id,
            "description": "Content OCG.",
        },
    }


def _graph_identity_create_operation(*, graph_identity_id: str) -> dict[str, object]:
    return {
        "operation_key": "proof.graph_identity.create",
        "operation_family": "create",
        "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphIdentity",
        "semantic_key": GRAPH_IDENTITY_SEMANTIC_KEY,
        "package_name": PACKAGE_NAME,
        "fqn_prefix": FQN_PREFIX,
        "source_refs": ("content/content_delta_ready.aware",),
        "before_payload": {},
        "after_payload": {
            "key": f"{FQN_PREFIX}:aware",
            "fqn_prefix": FQN_PREFIX,
            "language": "aware",
            "object_config_graph_identity_id": graph_identity_id,
            "label": "Content OCG identity",
        },
    }


def _package_attach_graph_operation(
    *,
    package_id: str,
    graph_id: str,
) -> dict[str, object]:
    return {
        "operation_key": "proof.package.attach_graph",
        "operation_family": "update",
        "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphPackage",
        "semantic_key": PACKAGE_SEMANTIC_KEY,
        "package_name": PACKAGE_NAME,
        "fqn_prefix": FQN_PREFIX,
        "graph_semantic_key": GRAPH_SEMANTIC_KEY,
        "source_refs": ("content/content_delta_ready.aware",),
        "before_payload": {
            "package_name": PACKAGE_NAME,
            "fqn_prefix": FQN_PREFIX,
            "object_config_graph_package_id": package_id,
        },
        "after_payload": {
            "package_name": PACKAGE_NAME,
            "fqn_prefix": FQN_PREFIX,
            "object_config_graph_package_id": package_id,
            "graph_semantic_key": GRAPH_SEMANTIC_KEY,
            "object_config_graph_id": graph_id,
        },
    }


def _function_create_operation(
    *,
    graph_id: str,
    class_node_id: str,
    class_config_id: str,
) -> dict[str, object]:
    return {
        "operation_key": "proof.function.create",
        "operation_family": "create",
        "semantic_operation_type": META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "semantic_key": FUNCTION_SEMANTIC_KEY,
        "package_name": PACKAGE_NAME,
        "fqn_prefix": FQN_PREFIX,
        "source_refs": ("content/content_delta_ready.aware",),
        "before_payload": {},
        "after_payload": {
            "class_name": CLASS_NAME,
            "class_fqn": CLASS_FQN,
            "owner_key": CLASS_FQN,
            "owner_semantic_key": CLASS_SEMANTIC_KEY,
            "object_config_graph_id": graph_id,
            "object_config_graph_node_id": class_node_id,
            "class_config_id": class_config_id,
            "function_name": FUNCTION_NAME,
            "name": FUNCTION_NAME,
            "description": "Rename content.",
            "kind": "instance",
            "is_public": True,
            "is_constructor": False,
            "position": 0,
            "generated_materialization": {
                "python_orm": {"relative_path": "content/content_delta_ready.py"},
            },
        },
    }


def _provider_delta_operation_type(metadata: Mapping[str, object]) -> str | None:
    typed_operation = _mapping(metadata.get("provider_delta_typed_operation"))
    return typed_operation.get("provider_operation_type") if typed_operation else None


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()
