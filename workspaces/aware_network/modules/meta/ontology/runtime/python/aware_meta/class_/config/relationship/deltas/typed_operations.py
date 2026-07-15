from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.semantic_scope_closure import (
    MetaOcgSemanticScopeClosureEvidence,
    SCOPE_GATE_STATUS_BLOCKED,
    SCOPE_GATE_STATUS_READY,
    meta_ocg_class_fqn_scope_closure_gate,
    meta_ocg_scope_closure_committed_ref_fields,
)


RELATIONSHIP_CONFIG_SUBJECT_KIND = "relationship"
RELATIONSHIP_CONFIG_SUBJECT_TYPE = "aware_meta.ClassConfigRelationship"
RELATIONSHIP_ASSOCIATION_SUBJECT_TYPE = "aware_meta.ClassConfigRelationshipAssociation"
RELATIONSHIP_ATTRIBUTE_SUBJECT_TYPE = "aware_meta.ClassConfigRelationshipAttribute"
RELATIONSHIP_ASSOCIATION_CREATE_PROVIDER_OPERATION_TYPE = (
    "meta_ocg.relationship.association.create"
)
RELATIONSHIP_ATTRIBUTE_CREATE_PROVIDER_OPERATION_TYPE = (
    "meta_ocg.relationship.attribute.create"
)
RELATIONSHIP_LOAD_POLICY_ANNOTATION_UPDATE_PROVIDER_OPERATION_TYPE = (
    "meta_ocg.relationship.annotation.load_policy.update"
)
RELATIONSHIP_LOAD_POLICY_SEMANTIC_OPERATION_TYPE = (
    "aware_meta.object_config_graph.relationship.load_policy.update"
)
ANNOTATION_EFFECT_TYPED_OPERATION_CONTRACT_VERSION = (
    "aware.meta.annotation-effect-typed-operation.v0"
)


def relationship_config_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)

    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    derived_edge_kind = _relationship_derived_edge_kind(entry=entry, payload=payload)
    if derived_edge_kind == "association":
        return (
            _relationship_association_create_dirty_entry(
                entry=entry,
                payload=payload,
                semantic_key=semantic_key,
            ),
        )
    if derived_edge_kind == "attribute":
        return (
            _relationship_attribute_create_dirty_entry(
                entry=entry,
                payload=payload,
                semantic_key=semantic_key,
            ),
        )
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
            entry.get("semantic_scope_closure") or payload.get("semantic_scope_closure")
        ),
    )
    normalized = dict(entry)
    annotation_effect_fields = _relationship_annotation_effect_fields(
        entry=entry,
        payload=payload,
    )
    normalized.update(
        {
            "typed_operation_key": (
                f"meta_ocg.relationship.{operation_family}:{semantic_key}"
            ),
            "provider_operation_type": _relationship_provider_operation_type(
                operation_family=operation_family,
                annotation_effect_fields=annotation_effect_fields,
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
            **annotation_effect_fields,
            **scope_evidence,
        }
    )
    return (normalized,)


def _relationship_association_create_dirty_entry(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    semantic_key: str,
) -> dict[str, object]:
    association_signature = _mapping_value(
        entry.get("relationship_association_signature")
        or entry.get("association_signature")
        or payload.get("relationship_association_signature")
        or payload.get("association_signature")
    )
    relationship_semantic_key = _first_text(
        entry.get("relationship_semantic_key"),
        payload.get("relationship_semantic_key"),
        association_signature.get("relationship_semantic_key"),
        _relationship_parent_semantic_key(semantic_key),
    )
    relationship_config_id = _first_text(
        entry.get("relationship_config_id"),
        entry.get("class_config_relationship_id"),
        payload.get("relationship_config_id"),
        payload.get("class_config_relationship_id"),
        association_signature.get("relationship_config_id"),
        association_signature.get("class_config_relationship_id"),
    )
    association_class_config_id = _first_text(
        entry.get("association_class_config_id"),
        entry.get("class_config_id"),
        payload.get("association_class_config_id"),
        payload.get("class_config_id"),
        association_signature.get("association_class_config_id"),
        association_signature.get("class_config_id"),
    )
    association_id = _first_text(
        entry.get("relationship_association_id"),
        entry.get("association_edge_id"),
        entry.get("entity_id"),
        payload.get("relationship_association_id"),
        payload.get("association_edge_id"),
        payload.get("entity_id"),
        association_signature.get("relationship_association_id"),
        association_signature.get("association_edge_id"),
    )
    resolved_signature = {
        **association_signature,
        "relationship_config_id": relationship_config_id,
        "class_config_relationship_id": relationship_config_id,
        "association_class_config_id": association_class_config_id,
        "class_config_id": association_class_config_id,
    }
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": (
                "meta_ocg.relationship.association.create:" f"{semantic_key}"
            ),
            "provider_operation_type": (
                RELATIONSHIP_ASSOCIATION_CREATE_PROVIDER_OPERATION_TYPE
            ),
            "operation_family": "create",
            "semantic_subject_type": RELATIONSHIP_ASSOCIATION_SUBJECT_TYPE,
            "ontology_subject_kind": RELATIONSHIP_CONFIG_SUBJECT_KIND,
            "owner_semantic_key": relationship_semantic_key,
            "parent_semantic_key": relationship_semantic_key,
            "relationship_semantic_key": relationship_semantic_key,
            "relationship_config_id": relationship_config_id,
            "class_config_relationship_id": relationship_config_id,
            "association_class_config_id": association_class_config_id,
            "class_config_id": association_class_config_id,
            "relationship_association_id": association_id,
            "association_edge_id": association_id,
            "entity_id": association_id,
            "relationship_association_signature": resolved_signature,
        }
    )
    return normalized


def _relationship_attribute_create_dirty_entry(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
    semantic_key: str,
) -> dict[str, object]:
    attribute_signature = _mapping_value(
        entry.get("relationship_attribute_signature")
        or entry.get("attribute_signature")
        or payload.get("relationship_attribute_signature")
        or payload.get("attribute_signature")
    )
    relationship_semantic_key = _first_text(
        entry.get("relationship_semantic_key"),
        payload.get("relationship_semantic_key"),
        attribute_signature.get("relationship_semantic_key"),
        _relationship_parent_semantic_key(semantic_key),
    )
    relationship_config_id = _first_text(
        entry.get("relationship_config_id"),
        entry.get("class_config_relationship_id"),
        payload.get("relationship_config_id"),
        payload.get("class_config_relationship_id"),
        attribute_signature.get("relationship_config_id"),
        attribute_signature.get("class_config_relationship_id"),
    )
    attribute_config_id = _first_text(
        entry.get("attribute_config_id"),
        payload.get("attribute_config_id"),
        attribute_signature.get("attribute_config_id"),
    )
    direction = _first_text(
        entry.get("direction"),
        payload.get("direction"),
        attribute_signature.get("direction"),
    )
    role = _first_text(
        entry.get("role"),
        payload.get("role"),
        attribute_signature.get("role"),
    )
    relationship_attribute_id = _first_text(
        entry.get("relationship_attribute_id"),
        entry.get("relationship_attribute_config_id"),
        entry.get("entity_id"),
        payload.get("relationship_attribute_id"),
        payload.get("relationship_attribute_config_id"),
        payload.get("entity_id"),
        attribute_signature.get("relationship_attribute_id"),
        attribute_signature.get("relationship_attribute_config_id"),
    )
    resolved_signature = {
        **attribute_signature,
        "relationship_config_id": relationship_config_id,
        "class_config_relationship_id": relationship_config_id,
        "attribute_config_id": attribute_config_id,
        "direction": direction,
        "role": role,
    }
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": (
                "meta_ocg.relationship.attribute.create:" f"{semantic_key}"
            ),
            "provider_operation_type": (
                RELATIONSHIP_ATTRIBUTE_CREATE_PROVIDER_OPERATION_TYPE
            ),
            "operation_family": "create",
            "semantic_subject_type": RELATIONSHIP_ATTRIBUTE_SUBJECT_TYPE,
            "ontology_subject_kind": RELATIONSHIP_CONFIG_SUBJECT_KIND,
            "owner_semantic_key": relationship_semantic_key,
            "parent_semantic_key": relationship_semantic_key,
            "relationship_semantic_key": relationship_semantic_key,
            "relationship_config_id": relationship_config_id,
            "class_config_relationship_id": relationship_config_id,
            "attribute_config_id": attribute_config_id,
            "direction": direction,
            "role": role,
            "relationship_attribute_id": relationship_attribute_id,
            "relationship_attribute_config_id": relationship_attribute_id,
            "entity_id": relationship_attribute_id,
            "relationship_attribute_signature": resolved_signature,
        }
    )
    return normalized


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
        blockers.append("semantic_scope_closure_relationship_source_class_fqn_missing")
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
        **meta_ocg_scope_closure_committed_ref_fields(gates=gates),
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
        entry.get("relationship_signature") or payload.get("relationship_signature")
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


def _relationship_derived_edge_kind(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
) -> str | None:
    provider_operation_type = _first_text(
        entry.get("provider_operation_type"),
        payload.get("provider_operation_type"),
    )
    object_kind = _first_text(
        entry.get("relationship_derived_edge_kind"),
        payload.get("relationship_derived_edge_kind"),
        entry.get("object_kind"),
        payload.get("object_kind"),
        entry.get("ontology_subject_kind"),
        payload.get("ontology_subject_kind"),
    )
    if (
        provider_operation_type
        == RELATIONSHIP_ASSOCIATION_CREATE_PROVIDER_OPERATION_TYPE
    ):
        return "association"
    if provider_operation_type == RELATIONSHIP_ATTRIBUTE_CREATE_PROVIDER_OPERATION_TYPE:
        return "attribute"
    if object_kind in {
        "relationship_association",
        "class_config_relationship_association",
        "association",
    }:
        return "association"
    if object_kind in {
        "relationship_attribute",
        "class_config_relationship_attribute",
        "attribute",
    }:
        return "attribute"
    return None


def _relationship_provider_operation_type(
    *,
    operation_family: str,
    annotation_effect_fields: Mapping[str, object],
) -> str:
    if annotation_effect_fields.get("annotation_effect_kind") == (
        "relationship_load_policy"
    ):
        return RELATIONSHIP_LOAD_POLICY_ANNOTATION_UPDATE_PROVIDER_OPERATION_TYPE
    return f"meta_ocg.relationship.{operation_family}"


def _relationship_annotation_effect_fields(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
) -> dict[str, object]:
    if not _is_relationship_load_policy_annotation_effect(
        entry=entry,
        payload=payload,
    ):
        return {}
    return {
        "annotation_semantics_consumed": True,
        "annotation_semantics_contract_version": (
            ANNOTATION_EFFECT_TYPED_OPERATION_CONTRACT_VERSION
        ),
        "annotation_effect_kind": "relationship_load_policy",
        "annotation_to_relationship_mutation_policy": (
            "class_config_relationship.update_config"
        ),
        "annotation_source_field_path": _first_text(
            entry.get("field_path"),
            payload.get("field_path"),
            "load_policy_args",
        ),
    }


def _is_relationship_load_policy_annotation_effect(
    *,
    entry: Mapping[str, object],
    payload: Mapping[str, object],
) -> bool:
    semantic_operation_type = _first_text(
        entry.get("semantic_operation_type"),
        payload.get("semantic_operation_type"),
    )
    if semantic_operation_type == RELATIONSHIP_LOAD_POLICY_SEMANTIC_OPERATION_TYPE:
        return True
    provider_operation_type = _first_text(
        entry.get("provider_operation_type"),
        payload.get("provider_operation_type"),
    )
    if (
        provider_operation_type
        == RELATIONSHIP_LOAD_POLICY_ANNOTATION_UPDATE_PROVIDER_OPERATION_TYPE
    ):
        return True
    field_path = _first_text(entry.get("field_path"), payload.get("field_path"))
    return field_path in {
        "load_policy_args",
        "load_policy",
        "forward_loading_strategy",
        "reverse_loading_strategy",
    }


def _relationship_parent_semantic_key(value: str) -> str | None:
    for marker in ("/association:", "/attribute:"):
        if marker in value:
            return _optional_text(value.split(marker, maxsplit=1)[0])
    return None


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
        return tuple(
            text for item in value if (text := _optional_text(item)) is not None
        )
    return ()


__all__ = [
    "ANNOTATION_EFFECT_TYPED_OPERATION_CONTRACT_VERSION",
    "RELATIONSHIP_ASSOCIATION_CREATE_PROVIDER_OPERATION_TYPE",
    "RELATIONSHIP_ASSOCIATION_SUBJECT_TYPE",
    "RELATIONSHIP_ATTRIBUTE_CREATE_PROVIDER_OPERATION_TYPE",
    "RELATIONSHIP_ATTRIBUTE_SUBJECT_TYPE",
    "RELATIONSHIP_CONFIG_SUBJECT_KIND",
    "RELATIONSHIP_CONFIG_SUBJECT_TYPE",
    "RELATIONSHIP_LOAD_POLICY_ANNOTATION_UPDATE_PROVIDER_OPERATION_TYPE",
    "relationship_config_dirty_entry",
]
