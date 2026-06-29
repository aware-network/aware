from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.semantic_scope_closure import (
    MetaOcgSemanticScopeClosureEvidence,
    SCOPE_GATE_STATUS_BLOCKED,
    SCOPE_GATE_STATUS_READY,
    meta_ocg_class_fqn_scope_closure_gate,
)


RELATIONSHIP_CONFIG_SUBJECT_KIND = "relationship"
RELATIONSHIP_CONFIG_SUBJECT_TYPE = "aware_meta.ClassConfigRelationship"


def relationship_config_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)

    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    current_signature = _relationship_current_signature(entry=entry)
    baseline_signature = _relationship_baseline_signature(entry=entry)
    source_semantic_key = _relationship_source_semantic_key(semantic_key)
    source_class_fqn = _first_text(
        entry.get("source_class_fqn"),
        payload.get("source_class_fqn"),
        current_signature.get("source_class_fqn"),
        baseline_object.get("source_class_fqn"),
        baseline_payload.get("source_class_fqn"),
        baseline_signature.get("source_class_fqn"),
        _relationship_source_class_fqn(semantic_key),
    )
    target_class_fqn = _first_text(
        entry.get("target_class_fqn"),
        payload.get("target_class_fqn"),
        current_signature.get("target_class_fqn"),
        baseline_object.get("target_class_fqn"),
        baseline_payload.get("target_class_fqn"),
        baseline_signature.get("target_class_fqn"),
        _relationship_target_class_fqn(semantic_key),
    )
    relationship_key = _first_text(
        entry.get("relationship_key"),
        payload.get("relationship_key"),
        current_signature.get("relationship_key"),
        baseline_object.get("relationship_key"),
        baseline_payload.get("relationship_key"),
        baseline_signature.get("relationship_key"),
        _relationship_key_from_semantic_key(semantic_key),
    )
    relationship_type = _first_text(
        entry.get("relationship_type"),
        payload.get("relationship_type"),
        current_signature.get("relationship_type"),
        baseline_object.get("relationship_type"),
        baseline_payload.get("relationship_type"),
        baseline_signature.get("relationship_type"),
        _relationship_type_from_semantic_key(semantic_key),
    )
    source_class_config_id = _first_text(
        entry.get("source_class_config_id"),
        payload.get("source_class_config_id"),
        current_signature.get("source_class_config_id"),
        entry.get("class_config_id"),
        payload.get("class_config_id"),
        current_signature.get("class_config_id"),
        baseline_object.get("source_class_config_id"),
        baseline_payload.get("source_class_config_id"),
        baseline_signature.get("source_class_config_id"),
    )
    target_class_config_id = _first_text(
        entry.get("target_class_config_id"),
        payload.get("target_class_config_id"),
        current_signature.get("target_class_config_id"),
        baseline_object.get("target_class_config_id"),
        baseline_payload.get("target_class_config_id"),
        baseline_signature.get("target_class_config_id"),
    )
    relationship_config_id = _first_text(
        entry.get("relationship_config_id"),
        entry.get("class_config_relationship_id"),
        entry.get("entity_id"),
        payload.get("relationship_config_id"),
        payload.get("class_config_relationship_id"),
        payload.get("entity_id"),
        baseline_object.get("relationship_config_id"),
        baseline_object.get("class_config_relationship_id"),
        baseline_object.get("entity_id"),
        baseline_object.get("object_id"),
        baseline_payload.get("relationship_config_id"),
        baseline_payload.get("class_config_relationship_id"),
        baseline_payload.get("entity_id"),
    )
    resolved_signature = {
        **current_signature,
        "source_class_config_id": source_class_config_id,
        "source_class_fqn": source_class_fqn,
        "target_class_config_id": target_class_config_id,
        "target_class_fqn": target_class_fqn,
        "relationship_key": relationship_key,
        "relationship_type": relationship_type,
    }
    operation_family = _operation_family(entry=entry)
    scope_evidence = _relationship_scope_closure_fields(
        source_semantic_key=source_semantic_key,
        source_class_fqn=source_class_fqn,
        target_class_fqn=target_class_fqn,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure")
            or payload.get("semantic_scope_closure")
        ),
    )
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": (
                f"meta_ocg.relationship.{operation_family}:{semantic_key}"
            ),
            "provider_operation_type": (
                f"meta_ocg.relationship.{operation_family}"
            ),
            "semantic_subject_type": RELATIONSHIP_CONFIG_SUBJECT_TYPE,
            "ontology_subject_kind": RELATIONSHIP_CONFIG_SUBJECT_KIND,
            "owner_semantic_key": source_semantic_key,
            "parent_semantic_key": source_semantic_key,
            "source_class_semantic_key": source_semantic_key,
            "source_class_fqn": source_class_fqn,
            "target_class_fqn": target_class_fqn,
            "source_class_config_id": source_class_config_id,
            "target_class_config_id": target_class_config_id,
            "class_config_id": source_class_config_id,
            "relationship_config_id": relationship_config_id,
            "class_config_relationship_id": relationship_config_id,
            "entity_id": relationship_config_id,
            "relationship_key": relationship_key,
            "relationship_type": relationship_type,
            "relationship_signature": resolved_signature,
            **scope_evidence,
        }
    )
    return (normalized,)


def _relationship_scope_closure_fields(
    *,
    source_semantic_key: str | None,
    source_class_fqn: str | None,
    target_class_fqn: str | None,
    semantic_scope_closure: object,
) -> dict[str, object]:
    if semantic_scope_closure is None:
        return {}

    gates: list[dict[str, object]] = []
    blockers: list[str] = []
    package_fqn_prefix = _relationship_package_fqn_prefix(
        source_semantic_key=source_semantic_key,
        source_class_fqn=source_class_fqn,
    )
    if source_class_fqn is None:
        blockers.append(
            "semantic_scope_closure_relationship_source_class_fqn_missing"
        )
    else:
        gates.append(
            meta_ocg_class_fqn_scope_closure_gate(
                package_fqn_prefix=package_fqn_prefix,
                class_fqn=source_class_fqn,
                semantic_scope_closure=_scope_closure_value(
                    semantic_scope_closure,
                ),
            )
        )
    if target_class_fqn is not None:
        gates.append(
            meta_ocg_class_fqn_scope_closure_gate(
                package_fqn_prefix=package_fqn_prefix,
                class_fqn=target_class_fqn,
                semantic_scope_closure=_scope_closure_value(
                    semantic_scope_closure,
                ),
            )
        )

    for gate in gates:
        blockers.extend(_tuple_text(gate.get("blockers")))
    stable_blockers = tuple(dict.fromkeys(blockers))
    ready = not stable_blockers
    return {
        "semantic_scope_closure_consumed": True,
        "semantic_scope_closure_ready": ready,
        "semantic_scope_closure_blocked": not ready,
        "semantic_scope_closure_status": _first_text(
            *(gate.get("semantic_scope_closure_status") for gate in gates)
        ),
        "semantic_scope_closure_gate_status": (
            SCOPE_GATE_STATUS_READY if ready else SCOPE_GATE_STATUS_BLOCKED
        ),
        "semantic_scope_closure_blockers": stable_blockers,
        "semantic_scope_closure_gate": gates[0] if gates else {},
        "semantic_scope_closure_gates": tuple(gates),
    }


def _relationship_current_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = _mapping_value(entry.get("payload"))
    return _mapping_value(
        entry.get("relationship_signature")
        or payload.get("relationship_signature")
    )


def _relationship_baseline_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    return _mapping_value(
        entry.get("baseline_relationship_signature")
        or baseline_object.get("relationship_signature")
        or baseline_payload.get("relationship_signature")
    )


def _scope_closure_value(
    value: object,
) -> MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None:
    if isinstance(value, MetaOcgSemanticScopeClosureEvidence):
        return value
    if isinstance(value, Mapping):
        return value
    return None


def _relationship_package_fqn_prefix(
    *,
    source_semantic_key: str | None,
    source_class_fqn: str | None,
) -> str:
    if source_semantic_key is not None and source_semantic_key.startswith("ocg:"):
        prefix = source_semantic_key.removeprefix("ocg:").split("/", 1)[0].strip()
        if prefix:
            return prefix
    if source_class_fqn is not None:
        return source_class_fqn.split(".", maxsplit=1)[0]
    return ""


def _relationship_source_semantic_key(value: str) -> str | None:
    if "/relationship:" in value:
        return _optional_text(value.split("/relationship:", 1)[0])
    graph_key, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    source_fqn = node_key.split(":", 1)[0].strip()
    if not source_fqn:
        return None
    return f"{graph_key}/node:{source_fqn}"


def _relationship_source_class_fqn(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    if "/relationship:" in node_key:
        return _optional_text(node_key.split("/relationship:", 1)[0])
    return _optional_text(node_key.split(":", 1)[0])


def _relationship_target_class_fqn(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    parts = node_key.split(":")
    if len(parts) < 4:
        return None
    return _optional_text(parts[3])


def _relationship_key_from_semantic_key(value: str) -> str | None:
    if "/relationship:" in value:
        return _optional_text(value.rsplit("/relationship:", 1)[-1])
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    parts = node_key.split(":")
    if len(parts) < 2:
        return None
    return _optional_text(parts[1])


def _relationship_type_from_semantic_key(value: str) -> str | None:
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    parts = node_key.split(":")
    if len(parts) < 3:
        return None
    return _optional_text(parts[2])


def _operation_family(*, entry: Mapping[str, object]) -> str:
    operation = _first_text(
        entry.get("baseline_compare_operation"),
        entry.get("dirty_operation"),
    )
    if operation is None:
        return "unknown"
    normalized = operation.strip().lower()
    if normalized == "create" or normalized.endswith("_create"):
        return "create"
    if normalized == "update" or normalized.endswith("_update"):
        return "update"
    if normalized == "delete" or normalized.endswith("_delete"):
        return "delete"
    return normalized


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = _optional_text(value)
        return (text,) if text is not None else ()
    if isinstance(value, (tuple, list)):
        return tuple(text for item in value if (text := _optional_text(item)) is not None)
    return ()


__all__ = [
    "RELATIONSHIP_CONFIG_SUBJECT_KIND",
    "RELATIONSHIP_CONFIG_SUBJECT_TYPE",
    "relationship_config_dirty_entry",
]
