from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.semantic_scope_closure import (
    meta_ocg_class_fqn_scope_closure_gate,
    MetaOcgSemanticScopeClosureEvidence,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


CLASS_CONFIG_SUBJECT_KIND = "class"
CLASS_CONFIG_CREATE_SUBJECT_TYPE = "aware_meta.ObjectConfigGraphNode"
CLASS_CONFIG_DELETE_SUBJECT_TYPE = "aware_meta.ObjectConfigGraph"


def class_config_create_typed_operation(
    *,
    semantic_key: str,
    graph_semantic_key: str,
    object_config_graph_node_id: str,
    class_config_id: str,
    node_key: str,
    class_fqn: str,
    class_name: str,
    source_refs: tuple[str, ...],
    description: str | None = None,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ) = None,
) -> MetaProviderDeltaTypedOperation:
    scope_evidence = _class_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        class_fqn=class_fqn,
        semantic_scope_closure=semantic_scope_closure,
    )
    scope_blocked = scope_evidence.get("semantic_scope_closure_ready") is False
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.class.create:{semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.class.create",
        semantic_key=semantic_key,
        ontology_subject_kind=CLASS_CONFIG_SUBJECT_KIND,
        semantic_subject_type=CLASS_CONFIG_CREATE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": CLASS_CONFIG_SUBJECT_KIND,
            "graph_semantic_key": graph_semantic_key,
            "node_id": object_config_graph_node_id,
            "node_key": node_key,
            "node_type": CLASS_CONFIG_SUBJECT_KIND,
            "entity_id": class_config_id,
            "entity_name": class_name,
            "class_fqn": class_fqn,
            "description": description,
            "is_base": True,
            "is_edge": False,
            "value_mode": "graph_ref",
            "payload": {
                "graph_semantic_key": graph_semantic_key,
                "node_id": object_config_graph_node_id,
                "node_key": node_key,
                "node_type": CLASS_CONFIG_SUBJECT_KIND,
                "entity_id": class_config_id,
                "entity_name": class_name,
                "class_fqn": class_fqn,
                "description": description,
            },
        },
        blocked=scope_blocked,
        blocked_reason=(
            "meta_ocg_class_scope_closure_blocked" if scope_blocked else None
        ),
        would_execute=not scope_blocked,
        would_persist=not scope_blocked,
        extra=scope_evidence,
        include_operation_evidence=scope_blocked,
    )


def class_config_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    class_fqn = _first_text(
        entry.get("class_fqn"),
        payload.get("class_fqn"),
        entry.get("node_key"),
        payload.get("node_key"),
    )
    class_name = _first_text(
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("name"),
        payload.get("entity_name"),
        _class_name_from_fqn(class_fqn),
    )
    normalized = dict(entry)
    scope_evidence = _class_scope_closure_fields(
        graph_semantic_key=_first_text(
            entry.get("graph_semantic_key"),
            payload.get("graph_semantic_key"),
        ),
        class_fqn=class_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure")
            or payload.get("semantic_scope_closure")
        ),
    )
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.class.create:{semantic_key}",
            "provider_operation_type": "meta_ocg.class.create",
            "semantic_subject_type": CLASS_CONFIG_CREATE_SUBJECT_TYPE,
            "ontology_subject_kind": CLASS_CONFIG_SUBJECT_KIND,
            "class_fqn": class_fqn,
            "name": class_name,
            "entity_name": class_name,
            "node_key": _first_text(
                entry.get("node_key"),
                payload.get("node_key"),
                class_fqn,
            ),
            "node_type": "class",
            "graph_semantic_key": _first_text(
                entry.get("graph_semantic_key"),
                payload.get("graph_semantic_key"),
            ),
            "class_config_id": _first_text(
                entry.get("class_config_id"),
                entry.get("entity_id"),
                payload.get("class_config_id"),
                payload.get("entity_id"),
            ),
            "object_config_graph_node_id": _first_text(
                entry.get("object_config_graph_node_id"),
                entry.get("node_id"),
                payload.get("object_config_graph_node_id"),
                payload.get("node_id"),
            ),
            "description": _first_text(
                entry.get("description"),
                payload.get("description"),
            ),
            **scope_evidence,
        }
    )
    return (normalized,)


def class_config_delete_typed_operation(
    *,
    semantic_key: str,
    graph_semantic_key: str,
    object_config_graph_node_id: str,
    class_config_id: str | None,
    node_key: str,
    class_fqn: str,
    class_name: str,
    source_refs: tuple[str, ...],
    description: str | None = None,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ) = None,
) -> MetaProviderDeltaTypedOperation:
    scope_evidence = _class_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        class_fqn=class_fqn,
        semantic_scope_closure=semantic_scope_closure,
    )
    scope_blocked = scope_evidence.get("semantic_scope_closure_ready") is False
    baseline_object = {
        "semantic_key": semantic_key,
        "object_kind": CLASS_CONFIG_SUBJECT_KIND,
        "graph_semantic_key": graph_semantic_key,
        "object_config_graph_node_id": object_config_graph_node_id,
        "node_id": object_config_graph_node_id,
        "class_config_id": class_config_id,
        "entity_id": class_config_id,
        "node_key": node_key,
        "node_type": CLASS_CONFIG_SUBJECT_KIND,
        "class_fqn": class_fqn,
        "name": class_name,
        "entity_name": class_name,
        "description": description,
    }
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.class.delete:{semantic_key}",
        operation_family="delete",
        provider_operation_type="meta_ocg.class.delete",
        semantic_key=semantic_key,
        ontology_subject_kind=CLASS_CONFIG_SUBJECT_KIND,
        semantic_subject_type=CLASS_CONFIG_DELETE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={"object": {**baseline_object, "payload": baseline_object}},
        current={**baseline_object, "payload": baseline_object},
        blocked=scope_blocked,
        blocked_reason=(
            "meta_ocg_class_scope_closure_blocked" if scope_blocked else None
        ),
        would_execute=not scope_blocked,
        would_persist=not scope_blocked,
        extra=scope_evidence,
        include_operation_evidence=scope_blocked,
    )


def class_config_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    class_fqn = _first_text(
        entry.get("class_fqn"),
        payload.get("class_fqn"),
        baseline_object.get("class_fqn"),
        baseline_payload.get("class_fqn"),
        entry.get("node_key"),
        payload.get("node_key"),
        baseline_object.get("node_key"),
        baseline_payload.get("node_key"),
        _class_fqn_from_semantic_key(semantic_key),
    )
    class_name = _first_text(
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("name"),
        payload.get("entity_name"),
        baseline_object.get("name"),
        baseline_object.get("entity_name"),
        baseline_payload.get("name"),
        baseline_payload.get("entity_name"),
        _class_name_from_fqn(class_fqn),
    )
    graph_semantic_key = _first_text(
        entry.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        baseline_object.get("graph_semantic_key"),
        baseline_payload.get("graph_semantic_key"),
        _graph_semantic_key_from_class_semantic_key(semantic_key),
    )
    scope_evidence = _class_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        class_fqn=class_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure")
            or payload.get("semantic_scope_closure")
        ),
    )
    class_config_id = _first_text(
        entry.get("class_config_id"),
        entry.get("entity_id"),
        payload.get("class_config_id"),
        payload.get("entity_id"),
        baseline_object.get("class_config_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("class_config_id"),
        baseline_payload.get("entity_id"),
        entry.get("baseline_object_id"),
    )
    object_config_graph_node_id = _first_text(
        entry.get("object_config_graph_node_id"),
        entry.get("node_id"),
        payload.get("object_config_graph_node_id"),
        payload.get("node_id"),
        baseline_object.get("object_config_graph_node_id"),
        baseline_object.get("node_id"),
        baseline_payload.get("object_config_graph_node_id"),
        baseline_payload.get("node_id"),
    )
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.class.delete:{semantic_key}",
            "provider_operation_type": "meta_ocg.class.delete",
            "semantic_subject_type": CLASS_CONFIG_DELETE_SUBJECT_TYPE,
            "ontology_subject_kind": CLASS_CONFIG_SUBJECT_KIND,
            "class_fqn": class_fqn,
            "name": class_name,
            "entity_name": class_name,
            "node_key": _first_text(
                entry.get("node_key"),
                payload.get("node_key"),
                baseline_object.get("node_key"),
                baseline_payload.get("node_key"),
                class_fqn,
            ),
            "node_type": CLASS_CONFIG_SUBJECT_KIND,
            "graph_semantic_key": graph_semantic_key,
            "class_config_id": class_config_id,
            "entity_id": class_config_id,
            "object_config_graph_node_id": object_config_graph_node_id,
            "node_id": object_config_graph_node_id,
            "description": _first_text(
                entry.get("description"),
                payload.get("description"),
                baseline_object.get("description"),
                baseline_payload.get("description"),
            ),
            **scope_evidence,
        }
    )
    return (normalized,)


def class_config_update_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    class_fqn = _first_text(
        entry.get("class_fqn"),
        payload.get("class_fqn"),
        baseline_object.get("class_fqn"),
        baseline_payload.get("class_fqn"),
        _class_fqn_from_semantic_key(semantic_key),
    )
    class_name = _first_text(
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("name"),
        payload.get("entity_name"),
        baseline_object.get("name"),
        baseline_object.get("entity_name"),
        baseline_payload.get("name"),
        baseline_payload.get("entity_name"),
        _class_name_from_fqn(class_fqn),
    )
    normalized = dict(entry)
    scope_evidence = _class_scope_closure_fields(
        graph_semantic_key=_first_text(
            entry.get("graph_semantic_key"),
            payload.get("graph_semantic_key"),
            _graph_semantic_key_from_class_semantic_key(semantic_key),
        ),
        class_fqn=class_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure")
            or payload.get("semantic_scope_closure")
        ),
    )
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.class.update:{semantic_key}",
            "provider_operation_type": "meta_ocg.class.update",
            "semantic_subject_type": CLASS_CONFIG_CREATE_SUBJECT_TYPE,
            "ontology_subject_kind": CLASS_CONFIG_SUBJECT_KIND,
            "class_fqn": class_fqn,
            "name": class_name,
            "entity_name": class_name,
            "node_key": _first_text(
                entry.get("node_key"),
                payload.get("node_key"),
                class_fqn,
            ),
            "node_type": "class",
            "graph_semantic_key": _first_text(
                entry.get("graph_semantic_key"),
                payload.get("graph_semantic_key"),
                _graph_semantic_key_from_class_semantic_key(semantic_key),
            ),
            "class_config_id": _first_text(
                entry.get("class_config_id"),
                entry.get("entity_id"),
                payload.get("class_config_id"),
                payload.get("entity_id"),
                baseline_object.get("class_config_id"),
                baseline_object.get("entity_id"),
                baseline_payload.get("class_config_id"),
                baseline_payload.get("entity_id"),
            ),
            "object_config_graph_node_id": _first_text(
                entry.get("object_config_graph_node_id"),
                entry.get("node_id"),
                payload.get("object_config_graph_node_id"),
                payload.get("node_id"),
                baseline_object.get("object_config_graph_node_id"),
                baseline_object.get("node_id"),
                baseline_payload.get("object_config_graph_node_id"),
                baseline_payload.get("node_id"),
            ),
            "description": _first_text(
                entry.get("description"),
                payload.get("description"),
            ),
            **scope_evidence,
        }
    )
    return (normalized,)


def _class_scope_closure_fields(
    *,
    graph_semantic_key: str | None,
    class_fqn: str | None,
    semantic_scope_closure: object,
) -> dict[str, object]:
    if semantic_scope_closure is None:
        return {}
    resolved_class_fqn = _optional_text(class_fqn)
    if resolved_class_fqn is None:
        return {
            "semantic_scope_closure_consumed": True,
            "semantic_scope_closure_ready": False,
            "semantic_scope_closure_blocked": True,
            "semantic_scope_closure_blockers": (
                "semantic_scope_closure_class_fqn_missing",
            ),
        }
    gate = meta_ocg_class_fqn_scope_closure_gate(
        package_fqn_prefix=_class_package_fqn_prefix(
            graph_semantic_key=graph_semantic_key,
            class_fqn=resolved_class_fqn,
        ),
        class_fqn=resolved_class_fqn,
        semantic_scope_closure=(
            semantic_scope_closure
            if isinstance(semantic_scope_closure, Mapping)
            or isinstance(semantic_scope_closure, MetaOcgSemanticScopeClosureEvidence)
            else None
        ),
    )
    return {
        "semantic_scope_closure_consumed": gate["consumed"],
        "semantic_scope_closure_ready": gate["ready"],
        "semantic_scope_closure_blocked": gate["ready"] is not True,
        "semantic_scope_closure_status": gate["semantic_scope_closure_status"],
        "semantic_scope_closure_gate_status": gate["status"],
        "semantic_scope_closure_blockers": gate["blockers"],
        "semantic_scope_closure_gate": gate,
    }


def _class_package_fqn_prefix(
    *,
    graph_semantic_key: str | None,
    class_fqn: str,
) -> str:
    if graph_semantic_key is not None and graph_semantic_key.startswith("ocg:"):
        prefix = graph_semantic_key.removeprefix("ocg:").strip()
        if prefix:
            return prefix
    return class_fqn.split(".", maxsplit=1)[0]


def _class_name_from_fqn(value: str | None) -> str | None:
    if value is None:
        return None
    return value.rsplit(".", maxsplit=1)[-1] or None


def _class_fqn_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    return _optional_text(node_key.split("/", maxsplit=1)[0])


def _graph_semantic_key_from_class_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return _optional_text(graph_key)


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "CLASS_CONFIG_CREATE_SUBJECT_TYPE",
    "CLASS_CONFIG_DELETE_SUBJECT_TYPE",
    "CLASS_CONFIG_SUBJECT_KIND",
    "class_config_create_dirty_entry",
    "class_config_create_typed_operation",
    "class_config_delete_dirty_entry",
    "class_config_delete_typed_operation",
    "class_config_update_dirty_entry",
]
