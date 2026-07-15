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
CLASS_CONFIG_UPDATE_PROVIDER_OPERATION_TYPE = "meta_ocg.class.update"
CLASS_CONFIG_PARENT_UPDATE_PROVIDER_OPERATION_TYPE = "meta_ocg.class.parent.update"


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
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
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
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
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
    parent_update = _class_parent_changed(
        entry=entry,
        payload=payload,
        baseline_object=baseline_object,
        baseline_payload=baseline_payload,
    )
    provider_operation_type = (
        CLASS_CONFIG_PARENT_UPDATE_PROVIDER_OPERATION_TYPE
        if parent_update
        else CLASS_CONFIG_UPDATE_PROVIDER_OPERATION_TYPE
    )
    typed_operation_key = (
        f"meta_ocg.class.parent.update:{semantic_key}"
        if parent_update
        else f"meta_ocg.class.update:{semantic_key}"
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
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
        ),
    )
    if parent_update:
        scope_evidence = _class_parent_scope_closure_fields(
            graph_semantic_key=_first_text(
                entry.get("graph_semantic_key"),
                payload.get("graph_semantic_key"),
                _graph_semantic_key_from_class_semantic_key(semantic_key),
            ),
            class_fqn=class_fqn,
            parent_class_fqn=_class_parent_fqn(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            parent_class_required=_class_current_parent_required(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            semantic_scope_closure=(
                entry.get("semantic_scope_closure")
                or payload.get("semantic_scope_closure")
            ),
        )
    normalized.update(
        {
            "typed_operation_key": typed_operation_key,
            "provider_operation_type": provider_operation_type,
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
            "parent_class_id": _class_parent_id(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            "parent_class_fqn": _class_parent_fqn(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            "parent_class_semantic_key": _class_parent_semantic_key(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            "previous_parent_class_id": _baseline_class_parent_id(
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            "previous_parent_class_fqn": _baseline_class_parent_fqn(
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            "previous_parent_class_semantic_key": (
                _baseline_class_parent_semantic_key(
                    baseline_object=baseline_object,
                    baseline_payload=baseline_payload,
                )
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
        "semantic_scope_closure_hash": gate["semantic_scope_closure_hash"],
        "semantic_scope_closure_ref_keys": gate["semantic_scope_closure_ref_keys"],
        "semantic_scope_closure_blockers": gate["blockers"],
        "semantic_scope_closure_gate": gate,
    }


def _class_parent_scope_closure_fields(
    *,
    graph_semantic_key: str | None,
    class_fqn: str | None,
    parent_class_fqn: str | None,
    parent_class_required: bool,
    semantic_scope_closure: object,
) -> dict[str, object]:
    child_evidence = _class_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        class_fqn=class_fqn,
        semantic_scope_closure=semantic_scope_closure,
    )
    parent_gate = None
    parent_blockers: tuple[str, ...] = ()
    if parent_class_required:
        resolved_parent_class_fqn = _optional_text(parent_class_fqn)
        if resolved_parent_class_fqn is None:
            parent_blockers = ("parent_class_fqn_missing",)
        else:
            parent_gate = meta_ocg_class_fqn_scope_closure_gate(
                package_fqn_prefix=_class_package_fqn_prefix(
                    graph_semantic_key=graph_semantic_key,
                    class_fqn=resolved_parent_class_fqn,
                ),
                class_fqn=resolved_parent_class_fqn,
                semantic_scope_closure=(
                    semantic_scope_closure
                    if isinstance(semantic_scope_closure, Mapping)
                    or isinstance(
                        semantic_scope_closure,
                        MetaOcgSemanticScopeClosureEvidence,
                    )
                    else None
                ),
            )
            parent_blockers = _tuple_text(parent_gate.get("blockers"))

    child_gate = _mapping_value(child_evidence.get("semantic_scope_closure_gate"))
    child_blockers = _tuple_text(child_evidence.get("semantic_scope_closure_blockers"))
    blockers = _unique_texts((*child_blockers, *parent_blockers))
    gates = tuple(
        gate for gate in (child_gate if child_gate else None, parent_gate) if gate
    )
    ready = not blockers
    closure_hash = _first_text(
        child_evidence.get("semantic_scope_closure_hash"),
        parent_gate.get("semantic_scope_closure_hash") if parent_gate else None,
    )
    closure_ref_keys = _unique_texts(
        (
            *_tuple_text(child_evidence.get("semantic_scope_closure_ref_keys")),
            *(
                _tuple_text(parent_gate.get("semantic_scope_closure_ref_keys"))
                if parent_gate
                else ()
            ),
        )
    )
    return {
        **child_evidence,
        "semantic_scope_closure_ready": ready,
        "semantic_scope_closure_blocked": not ready,
        "semantic_scope_closure_gate_status": (
            "semantic_scope_closure_gate_ready"
            if ready
            else "semantic_scope_closure_gate_blocked"
        ),
        "semantic_scope_closure_hash": closure_hash,
        "semantic_scope_closure_ref_keys": closure_ref_keys,
        "semantic_scope_closure_blockers": blockers,
        "semantic_scope_closure_gates": gates,
        "parent_semantic_scope_closure_gate": parent_gate or {},
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


def _class_parent_changed(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> bool:
    current = (
        _class_parent_id(
            entry=entry,
            payload=payload,
            baseline_object=baseline_object,
            baseline_payload=baseline_payload,
        ),
        _class_parent_fqn(
            entry=entry,
            payload=payload,
            baseline_object=baseline_object,
            baseline_payload=baseline_payload,
        ),
        _class_parent_semantic_key(
            entry=entry,
            payload=payload,
            baseline_object=baseline_object,
            baseline_payload=baseline_payload,
        ),
    )
    baseline = (
        _baseline_class_parent_id(
            baseline_object=baseline_object,
            baseline_payload=baseline_payload,
        ),
        _baseline_class_parent_fqn(
            baseline_object=baseline_object,
            baseline_payload=baseline_payload,
        ),
        _baseline_class_parent_semantic_key(
            baseline_object=baseline_object,
            baseline_payload=baseline_payload,
        ),
    )
    return any(value is not None for value in (*current, *baseline)) and (
        current != baseline
    )


def _class_current_parent_required(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> bool:
    return any(
        value is not None
        for value in (
            _class_parent_id(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            _class_parent_fqn(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
            _class_parent_semantic_key(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            ),
        )
    )


def _class_parent_id(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        entry.get("parent_class_id"),
        entry.get("parent_class_config_id"),
        payload.get("parent_class_id"),
        payload.get("parent_class_config_id"),
        _mapping_value(entry.get("class_signature")).get("parent_class_id"),
        _mapping_value(payload.get("class_signature")).get("parent_class_id"),
    )


def _baseline_class_parent_id(
    *,
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        baseline_object.get("parent_class_id"),
        baseline_object.get("parent_class_config_id"),
        baseline_payload.get("parent_class_id"),
        baseline_payload.get("parent_class_config_id"),
        _mapping_value(baseline_object.get("class_signature")).get("parent_class_id"),
        _mapping_value(baseline_payload.get("class_signature")).get("parent_class_id"),
    )


def _class_parent_fqn(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        entry.get("parent_class_fqn"),
        payload.get("parent_class_fqn"),
        _mapping_value(entry.get("class_signature")).get("parent_class_fqn"),
        _mapping_value(payload.get("class_signature")).get("parent_class_fqn"),
        _class_fqn_from_semantic_key(
            _class_parent_semantic_key(
                entry=entry,
                payload=payload,
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            )
            or ""
        ),
    )


def _baseline_class_parent_fqn(
    *,
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        baseline_object.get("parent_class_fqn"),
        baseline_payload.get("parent_class_fqn"),
        _mapping_value(baseline_object.get("class_signature")).get("parent_class_fqn"),
        _mapping_value(baseline_payload.get("class_signature")).get("parent_class_fqn"),
        _class_fqn_from_semantic_key(
            _baseline_class_parent_semantic_key(
                baseline_object=baseline_object,
                baseline_payload=baseline_payload,
            )
            or ""
        ),
    )


def _class_parent_semantic_key(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        entry.get("parent_class_semantic_key"),
        payload.get("parent_class_semantic_key"),
        _mapping_value(entry.get("class_signature")).get("parent_class_semantic_key"),
        _mapping_value(payload.get("class_signature")).get("parent_class_semantic_key"),
    )


def _baseline_class_parent_semantic_key(
    *,
    baseline_object: Mapping[str, object],
    baseline_payload: Mapping[str, object],
) -> str | None:
    return _first_text(
        baseline_object.get("parent_class_semantic_key"),
        baseline_payload.get("parent_class_semantic_key"),
        _mapping_value(baseline_object.get("class_signature")).get(
            "parent_class_semantic_key"
        ),
        _mapping_value(baseline_payload.get("class_signature")).get(
            "parent_class_semantic_key"
        ),
    )


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


def _tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = _optional_text(value)
        return (text,) if text is not None else ()
    if isinstance(value, (tuple, list, set, frozenset)):
        return tuple(
            text for item in value if (text := _optional_text(item)) is not None
        )
    return ()


def _unique_texts(values: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(text for value in values for text in _tuple_text(value)))


__all__ = [
    "CLASS_CONFIG_PARENT_UPDATE_PROVIDER_OPERATION_TYPE",
    "CLASS_CONFIG_CREATE_SUBJECT_TYPE",
    "CLASS_CONFIG_DELETE_SUBJECT_TYPE",
    "CLASS_CONFIG_SUBJECT_KIND",
    "class_config_create_dirty_entry",
    "class_config_create_typed_operation",
    "class_config_delete_dirty_entry",
    "class_config_delete_typed_operation",
    "class_config_update_dirty_entry",
]
