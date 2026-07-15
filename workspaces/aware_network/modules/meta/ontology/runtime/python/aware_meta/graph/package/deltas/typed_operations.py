from __future__ import annotations

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND = "object_config_graph_package"
OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_TYPE = "aware_meta.ObjectConfigGraphPackage"
OBJECT_CONFIG_GRAPH_PACKAGE_BUILD_FUNCTION = "ObjectConfigGraphPackage.build"
OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_FUNCTION = (
    "ObjectConfigGraphPackage.attach_object_config_graph"
)


def object_config_graph_package_create_typed_operation(
    *,
    package_name: str,
    fqn_prefix: str,
    package_id: str,
    semantic_key: str,
    source_refs: tuple[str, ...],
    title: str | None = None,
    description: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    return _operation(
        operation_key=(
            f"meta_ocg.object_config_graph_package.create:{semantic_key}"
        ),
        operation_family="create",
        provider_operation_type="meta_ocg.object_config_graph_package.create",
        semantic_key=semantic_key,
        source_refs=source_refs,
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND,
            "entity_id": package_id,
            "package_name": package_name,
            "fqn_prefix": fqn_prefix,
            "title": title,
            "description": description,
            "required_ontology_function": OBJECT_CONFIG_GRAPH_PACKAGE_BUILD_FUNCTION,
            "payload": {
                "entity_id": package_id,
                "package_name": package_name,
                "fqn_prefix": fqn_prefix,
                "title": title,
                "description": description,
            },
        },
    )


def object_config_graph_package_attach_graph_typed_operation(
    *,
    package_name: str,
    package_id: str,
    object_config_graph_id: str,
    semantic_key: str,
    source_refs: tuple[str, ...],
    title: str | None = None,
    description: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    return _operation(
        operation_key=(
            "meta_ocg.object_config_graph_package.update.attach_graph:"
            f"{semantic_key}"
        ),
        operation_family="update",
        provider_operation_type="meta_ocg.object_config_graph_package.update",
        semantic_key=semantic_key,
        source_refs=source_refs,
        baseline={"object_id": package_id},
        current={
            "semantic_key": semantic_key,
            "object_kind": OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND,
            "entity_id": package_id,
            "object_config_graph_id": object_config_graph_id,
            "title": title,
            "description": description,
            "required_ontology_function": (
                OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_FUNCTION
            ),
            "payload": {
                "entity_id": package_id,
                "object_config_graph_id": object_config_graph_id,
                "title": title,
                "description": description,
            },
        },
    )


def _operation(
    *,
    operation_key: str,
    operation_family: str,
    provider_operation_type: str,
    semantic_key: str,
    source_refs: tuple[str, ...],
    current: dict[str, object],
    baseline: dict[str, object] | None = None,
) -> MetaProviderDeltaTypedOperation:
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=operation_key,
        operation_family=operation_family,
        provider_operation_type=provider_operation_type,
        semantic_key=semantic_key,
        ontology_subject_kind=OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND,
        semantic_subject_type=OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline=baseline or {},
        current=current,
        would_execute=True,
        would_persist=True,
    )


__all__ = [
    "OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_FUNCTION",
    "OBJECT_CONFIG_GRAPH_PACKAGE_BUILD_FUNCTION",
    "OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_KIND",
    "OBJECT_CONFIG_GRAPH_PACKAGE_SUBJECT_TYPE",
    "object_config_graph_package_attach_graph_typed_operation",
    "object_config_graph_package_create_typed_operation",
]
