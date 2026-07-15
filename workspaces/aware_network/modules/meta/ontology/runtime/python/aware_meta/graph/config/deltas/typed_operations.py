from __future__ import annotations

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


OBJECT_CONFIG_GRAPH_SUBJECT_KIND = "object_config_graph"
OBJECT_CONFIG_GRAPH_SUBJECT_TYPE = "aware_meta.ObjectConfigGraph"
OBJECT_CONFIG_GRAPH_BUILD_FUNCTION = "ObjectConfigGraph.build"
OBJECT_CONFIG_GRAPH_IDENTITY_SUBJECT_KIND = "object_config_graph_identity"
OBJECT_CONFIG_GRAPH_IDENTITY_SUBJECT_TYPE = "aware_meta.ObjectConfigGraphIdentity"
OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_FUNCTION = "ObjectConfigGraphIdentity.create"


def object_config_graph_identity_create_typed_operation(
    *,
    semantic_key: str,
    object_config_graph_identity_id: str,
    key: str,
    source_refs: tuple[str, ...],
    label: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.object_config_graph_identity.create:{semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.object_config_graph_identity.create",
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_CONFIG_GRAPH_IDENTITY_SUBJECT_KIND,
        semantic_subject_type=OBJECT_CONFIG_GRAPH_IDENTITY_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_CONFIG_GRAPH_IDENTITY_SUBJECT_KIND,
            "entity_id": object_config_graph_identity_id,
            "key": key,
            "label": label,
            "required_ontology_function": (
                OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_FUNCTION
            ),
            "payload": {
                "entity_id": object_config_graph_identity_id,
                "key": key,
                "label": label,
            },
        },
        would_execute=True,
        would_persist=True,
    )


def object_config_graph_create_typed_operation(
    *,
    fqn_prefix: str,
    semantic_key: str,
    object_config_graph_id: str,
    name: str,
    source_refs: tuple[str, ...],
    graph_hash: str = "",
    layout_hash: str | None = None,
    language: str = "aware",
    description: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.object_config_graph.create:{semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.object_config_graph.create",
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_CONFIG_GRAPH_SUBJECT_KIND,
        semantic_subject_type=OBJECT_CONFIG_GRAPH_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_CONFIG_GRAPH_SUBJECT_KIND,
            "entity_id": object_config_graph_id,
            "name": name,
            "hash": graph_hash,
            "layout_hash": layout_hash,
            "fqn_prefix": fqn_prefix,
            "language": language,
            "description": description,
            "required_ontology_function": OBJECT_CONFIG_GRAPH_BUILD_FUNCTION,
            "payload": {
                "entity_id": object_config_graph_id,
                "name": name,
                "hash": graph_hash,
                "layout_hash": layout_hash,
                "fqn_prefix": fqn_prefix,
                "language": language,
                "description": description,
            },
        },
        would_execute=True,
        would_persist=True,
    )


__all__ = [
    "OBJECT_CONFIG_GRAPH_BUILD_FUNCTION",
    "OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_FUNCTION",
    "OBJECT_CONFIG_GRAPH_IDENTITY_SUBJECT_KIND",
    "OBJECT_CONFIG_GRAPH_IDENTITY_SUBJECT_TYPE",
    "OBJECT_CONFIG_GRAPH_SUBJECT_KIND",
    "OBJECT_CONFIG_GRAPH_SUBJECT_TYPE",
    "object_config_graph_identity_create_typed_operation",
    "object_config_graph_create_typed_operation",
]
