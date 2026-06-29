from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.semantic_scope_closure import (
    meta_ocg_enum_fqn_scope_closure_gate,
    MetaOcgSemanticScopeClosureEvidence,
)


ENUM_CONFIG_SUBJECT_KIND = "enum"
ENUM_CONFIG_CREATE_SUBJECT_TYPE = "aware_meta.ObjectConfigGraphNode"
ENUM_CONFIG_DELETE_SUBJECT_TYPE = "aware_meta.ObjectConfigGraph"
ENUM_CONFIG_UPDATE_SUBJECT_TYPE = "aware_meta.EnumConfig"
ENUM_OPTION_SUBJECT_KIND = "enum_option"
ENUM_OPTION_SUBJECT_TYPE = "aware_meta.EnumOption"


def enum_config_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    enum_fqn = _first_text(
        entry.get("enum_fqn"),
        payload.get("enum_fqn"),
        entry.get("node_key"),
        payload.get("node_key"),
        _enum_fqn_from_semantic_key(semantic_key),
    )
    enum_name = _first_text(
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("name"),
        payload.get("entity_name"),
        _enum_name_from_fqn(enum_fqn),
    )
    graph_semantic_key = _first_text(
        entry.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        _graph_semantic_key_from_enum_semantic_key(semantic_key),
    )
    scope_evidence = _enum_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        enum_fqn=enum_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
        ),
    )
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.enum.create:{semantic_key}",
            "provider_operation_type": "meta_ocg.enum.create",
            "semantic_subject_type": ENUM_CONFIG_CREATE_SUBJECT_TYPE,
            "ontology_subject_kind": ENUM_CONFIG_SUBJECT_KIND,
            "enum_fqn": enum_fqn,
            "name": enum_name,
            "entity_name": enum_name,
            "node_key": _first_text(
                entry.get("node_key"),
                payload.get("node_key"),
                enum_fqn,
            ),
            "node_type": ENUM_CONFIG_SUBJECT_KIND,
            "graph_semantic_key": graph_semantic_key,
            "enum_config_id": _first_text(
                entry.get("enum_config_id"),
                entry.get("entity_id"),
                payload.get("enum_config_id"),
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
            "values": _tuple_text(
                _first_value(
                    entry.get("values"),
                    payload.get("values"),
                    (),
                )
            ),
            **scope_evidence,
        }
    )
    return (normalized,)


def enum_config_update_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    enum_fqn = _first_text(
        entry.get("enum_fqn"),
        payload.get("enum_fqn"),
        baseline_object.get("enum_fqn"),
        baseline_payload.get("enum_fqn"),
        entry.get("node_key"),
        payload.get("node_key"),
        _enum_fqn_from_semantic_key(semantic_key),
    )
    enum_name = _first_text(
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("name"),
        payload.get("entity_name"),
        baseline_object.get("name"),
        baseline_object.get("entity_name"),
        baseline_payload.get("name"),
        baseline_payload.get("entity_name"),
        _enum_name_from_fqn(enum_fqn),
    )
    graph_semantic_key = _first_text(
        entry.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        baseline_object.get("graph_semantic_key"),
        baseline_payload.get("graph_semantic_key"),
        _graph_semantic_key_from_enum_semantic_key(semantic_key),
    )
    scope_evidence = _enum_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        enum_fqn=enum_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
        ),
    )
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.enum.update:{semantic_key}",
            "provider_operation_type": "meta_ocg.enum.update",
            "semantic_subject_type": ENUM_CONFIG_UPDATE_SUBJECT_TYPE,
            "ontology_subject_kind": ENUM_CONFIG_SUBJECT_KIND,
            "enum_fqn": enum_fqn,
            "name": enum_name,
            "entity_name": enum_name,
            "node_key": _first_text(
                entry.get("node_key"),
                payload.get("node_key"),
                baseline_object.get("node_key"),
                baseline_payload.get("node_key"),
                enum_fqn,
            ),
            "node_type": ENUM_CONFIG_SUBJECT_KIND,
            "graph_semantic_key": graph_semantic_key,
            "enum_config_id": _first_text(
                entry.get("enum_config_id"),
                entry.get("entity_id"),
                payload.get("enum_config_id"),
                payload.get("entity_id"),
                baseline_object.get("enum_config_id"),
                baseline_object.get("entity_id"),
                baseline_payload.get("enum_config_id"),
                baseline_payload.get("entity_id"),
                entry.get("baseline_object_id"),
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


def enum_config_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    enum_fqn = _first_text(
        entry.get("enum_fqn"),
        payload.get("enum_fqn"),
        baseline_object.get("enum_fqn"),
        baseline_payload.get("enum_fqn"),
        entry.get("node_key"),
        payload.get("node_key"),
        baseline_object.get("node_key"),
        baseline_payload.get("node_key"),
        _enum_fqn_from_semantic_key(semantic_key),
    )
    enum_name = _first_text(
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("name"),
        payload.get("entity_name"),
        baseline_object.get("name"),
        baseline_object.get("entity_name"),
        baseline_payload.get("name"),
        baseline_payload.get("entity_name"),
        _enum_name_from_fqn(enum_fqn),
    )
    graph_semantic_key = _first_text(
        entry.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        baseline_object.get("graph_semantic_key"),
        baseline_payload.get("graph_semantic_key"),
        _graph_semantic_key_from_enum_semantic_key(semantic_key),
    )
    scope_evidence = _enum_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        enum_fqn=enum_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
        ),
    )
    enum_config_id = _first_text(
        entry.get("enum_config_id"),
        entry.get("entity_id"),
        payload.get("enum_config_id"),
        payload.get("entity_id"),
        baseline_object.get("enum_config_id"),
        baseline_object.get("entity_id"),
        baseline_payload.get("enum_config_id"),
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
            "typed_operation_key": f"meta_ocg.enum.delete:{semantic_key}",
            "provider_operation_type": "meta_ocg.enum.delete",
            "semantic_subject_type": ENUM_CONFIG_DELETE_SUBJECT_TYPE,
            "ontology_subject_kind": ENUM_CONFIG_SUBJECT_KIND,
            "enum_fqn": enum_fqn,
            "name": enum_name,
            "entity_name": enum_name,
            "node_key": _first_text(
                entry.get("node_key"),
                payload.get("node_key"),
                baseline_object.get("node_key"),
                baseline_payload.get("node_key"),
                enum_fqn,
            ),
            "node_type": ENUM_CONFIG_SUBJECT_KIND,
            "graph_semantic_key": graph_semantic_key,
            "enum_config_id": enum_config_id,
            "entity_id": enum_config_id,
            "object_config_graph_node_id": object_config_graph_node_id,
            "node_id": object_config_graph_node_id,
            **scope_evidence,
        }
    )
    return (normalized,)


def enum_option_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return (_enum_option_dirty_entry(entry=entry, operation_family="create"),)


def enum_option_update_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return (_enum_option_dirty_entry(entry=entry, operation_family="update"),)


def enum_option_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return (_enum_option_dirty_entry(entry=entry, operation_family="delete"),)


def _enum_option_dirty_entry(
    *,
    entry: Mapping[str, object],
    operation_family: str,
) -> dict[str, object]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return dict(entry)
    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    enum_semantic_key = _first_text(
        entry.get("enum_semantic_key"),
        entry.get("parent_semantic_key"),
        payload.get("enum_semantic_key"),
        payload.get("parent_semantic_key"),
        baseline_object.get("enum_semantic_key"),
        baseline_object.get("parent_semantic_key"),
        baseline_payload.get("enum_semantic_key"),
        baseline_payload.get("parent_semantic_key"),
        _enum_semantic_key_from_option_semantic_key(semantic_key),
    )
    enum_fqn = _first_text(
        entry.get("enum_fqn"),
        payload.get("enum_fqn"),
        baseline_object.get("enum_fqn"),
        baseline_payload.get("enum_fqn"),
        _enum_fqn_from_semantic_key(enum_semantic_key or semantic_key),
    )
    value = _first_text(
        entry.get("value"),
        entry.get("option_value"),
        entry.get("entity_name"),
        payload.get("value"),
        payload.get("option_value"),
        payload.get("entity_name"),
        baseline_object.get("value"),
        baseline_object.get("option_value"),
        baseline_object.get("entity_name"),
        baseline_payload.get("value"),
        baseline_payload.get("option_value"),
        baseline_payload.get("entity_name"),
        _enum_option_value_from_semantic_key(semantic_key),
    )
    graph_semantic_key = _first_text(
        entry.get("graph_semantic_key"),
        payload.get("graph_semantic_key"),
        baseline_object.get("graph_semantic_key"),
        baseline_payload.get("graph_semantic_key"),
        _graph_semantic_key_from_enum_semantic_key(enum_semantic_key or semantic_key),
    )
    scope_evidence = _enum_scope_closure_fields(
        graph_semantic_key=graph_semantic_key,
        enum_fqn=enum_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
        ),
    )
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": (
                f"meta_ocg.enum_option.{operation_family}:{semantic_key}"
            ),
            "provider_operation_type": f"meta_ocg.enum_option.{operation_family}",
            "semantic_subject_type": ENUM_OPTION_SUBJECT_TYPE,
            "ontology_subject_kind": ENUM_OPTION_SUBJECT_KIND,
            "enum_semantic_key": enum_semantic_key,
            "parent_semantic_key": enum_semantic_key,
            "graph_semantic_key": graph_semantic_key,
            "enum_fqn": enum_fqn,
            "enum_config_id": _first_text(
                entry.get("enum_config_id"),
                payload.get("enum_config_id"),
                baseline_object.get("enum_config_id"),
                baseline_payload.get("enum_config_id"),
            ),
            "enum_option_id": _first_text(
                entry.get("enum_option_id"),
                entry.get("entity_id"),
                payload.get("enum_option_id"),
                payload.get("entity_id"),
                baseline_object.get("enum_option_id"),
                baseline_object.get("entity_id"),
                baseline_payload.get("enum_option_id"),
                baseline_payload.get("entity_id"),
                entry.get("baseline_object_id"),
            ),
            "entity_id": _first_text(
                entry.get("enum_option_id"),
                entry.get("entity_id"),
                payload.get("enum_option_id"),
                payload.get("entity_id"),
                baseline_object.get("enum_option_id"),
                baseline_object.get("entity_id"),
                baseline_payload.get("enum_option_id"),
                baseline_payload.get("entity_id"),
                entry.get("baseline_object_id"),
            ),
            "value": value,
            "entity_name": value,
            "label": _first_text(
                entry.get("label"),
                payload.get("label"),
            ),
            "description": _first_text(
                entry.get("description"),
                payload.get("description"),
            ),
            "position": _int_value(
                _first_value(
                    entry.get("position"),
                    payload.get("position"),
                    0,
                )
            ),
            **scope_evidence,
        }
    )
    return normalized


def _enum_scope_closure_fields(
    *,
    graph_semantic_key: str | None,
    enum_fqn: str | None,
    semantic_scope_closure: object,
) -> dict[str, object]:
    if semantic_scope_closure is None:
        return {}
    resolved_enum_fqn = _optional_text(enum_fqn)
    if resolved_enum_fqn is None:
        return {
            "semantic_scope_closure_consumed": True,
            "semantic_scope_closure_ready": False,
            "semantic_scope_closure_blocked": True,
            "semantic_scope_closure_blockers": (
                "semantic_scope_closure_enum_fqn_missing",
            ),
        }
    gate = meta_ocg_enum_fqn_scope_closure_gate(
        package_fqn_prefix=_enum_package_fqn_prefix(
            graph_semantic_key=graph_semantic_key,
            enum_fqn=resolved_enum_fqn,
        ),
        enum_fqn=resolved_enum_fqn,
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


def _enum_package_fqn_prefix(
    *,
    graph_semantic_key: str | None,
    enum_fqn: str,
) -> str:
    if graph_semantic_key is not None and graph_semantic_key.startswith("ocg:"):
        prefix = graph_semantic_key.removeprefix("ocg:").strip()
        if prefix:
            return prefix
    return enum_fqn.split(".", maxsplit=1)[0]


def _enum_name_from_fqn(value: str | None) -> str | None:
    if value is None:
        return None
    return value.rsplit(".", maxsplit=1)[-1] or None


def _enum_fqn_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    return _optional_text(node_key.split("/", maxsplit=1)[0])


def _graph_semantic_key_from_enum_semantic_key(value: str) -> str | None:
    graph_key, separator, _ = value.partition("/node:")
    if not separator:
        return None
    return _optional_text(graph_key)


def _enum_semantic_key_from_option_semantic_key(value: str) -> str | None:
    enum_key, separator, _ = value.partition("/option:")
    if not separator:
        return None
    return _optional_text(enum_key)


def _enum_option_value_from_semantic_key(value: str) -> str | None:
    _, separator, option_key = value.partition("/option:")
    if not separator:
        return None
    return _optional_text(option_key)


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _first_value(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
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
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 0
    return 0


__all__ = [
    "ENUM_CONFIG_CREATE_SUBJECT_TYPE",
    "ENUM_CONFIG_DELETE_SUBJECT_TYPE",
    "ENUM_CONFIG_SUBJECT_KIND",
    "ENUM_CONFIG_UPDATE_SUBJECT_TYPE",
    "enum_config_delete_dirty_entry",
    "ENUM_OPTION_SUBJECT_KIND",
    "ENUM_OPTION_SUBJECT_TYPE",
    "enum_config_create_dirty_entry",
    "enum_config_update_dirty_entry",
    "enum_option_create_dirty_entry",
    "enum_option_delete_dirty_entry",
    "enum_option_update_dirty_entry",
]
