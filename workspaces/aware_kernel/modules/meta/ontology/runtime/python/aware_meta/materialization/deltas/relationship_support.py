from __future__ import annotations

from collections.abc import Mapping


_RELATIONSHIP_ATTRIBUTE_ALLOWED_DIFF_FIELDS = frozenset(
    {
        "class_fqn",
        "default_value",
        "exclude_serialization",
        "is_required",
    }
)
_RELATIONSHIP_ATTRIBUTE_TYPE_DESCRIPTOR_ALLOWED_DIFF_FIELDS = frozenset(
    {
        "class_fqn",
    }
)


def relationship_update_support_attribute_index(
    *,
    dirty_entries: tuple[Mapping[str, object], ...],
) -> dict[str, str]:
    support_index: dict[str, str] = {}
    for entry in dirty_entries:
        if _optional_text(entry.get("baseline_compare_operation")) != "update":
            continue
        if _optional_text(entry.get("ontology_subject_kind")) != "relationship":
            continue
        relationship_semantic_key = _optional_text(entry.get("semantic_key"))
        if relationship_semantic_key is None:
            continue
        owner_semantic_key = _relationship_owner_semantic_key(
            relationship_semantic_key,
        )
        relationship_key = _relationship_key(
            entry=entry,
            relationship_semantic_key=relationship_semantic_key,
        )
        if owner_semantic_key is None or relationship_key is None:
            continue
        support_index[f"{owner_semantic_key}/attribute:{relationship_key}"] = (
            relationship_semantic_key
        )
        support_index[f"{owner_semantic_key}/attribute:{relationship_key}_id"] = (
            relationship_semantic_key
        )
    return support_index


def relationship_support_attribute_delta_only(
    *,
    entry: Mapping[str, object],
) -> bool:
    if _optional_text(entry.get("baseline_compare_operation")) != "update":
        return False
    if _optional_text(entry.get("ontology_subject_kind")) != "attribute":
        return False
    current_signature = _attribute_signature_from_entry(entry=entry)
    baseline_signature = _attribute_signature_from_baseline(entry=entry)
    if not current_signature or not baseline_signature:
        return False
    return _normalized_relationship_support_attribute_signature(
        current_signature,
    ) == _normalized_relationship_support_attribute_signature(baseline_signature)


def relationship_deferred_attribute_dirty_entry(
    *,
    entry: Mapping[str, object],
    relationship_semantic_key: str,
) -> dict[str, object]:
    updated = dict(entry)
    updated.update(
        {
            "dirty_operation": "attribute_noop",
            "baseline_compare_operation": "noop",
            "baseline_compare_status": (
                "relationship_support_attribute_deferred_to_relationship_update"
            ),
            "relationship_support_attribute_delta": True,
            "relationship_support_attribute_deferred_to": relationship_semantic_key,
        }
    )
    return updated


def _attribute_signature_from_entry(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = _mapping_value(entry.get("payload"))
    return _mapping_value(entry.get("attribute_signature") or payload.get("attribute_signature"))


def _attribute_signature_from_baseline(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    baseline = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline.get("payload"))
    return _mapping_value(
        entry.get("baseline_attribute_signature")
        or baseline.get("attribute_signature")
        or baseline_payload.get("attribute_signature")
    )


def _normalized_relationship_support_attribute_signature(
    signature: Mapping[str, object],
) -> tuple[tuple[str, object], ...]:
    return tuple(
        (str(key), _normalized_signature_value(key=str(key), value=value))
        for key, value in sorted(signature.items(), key=lambda item: str(item[0]))
        if str(key) not in _RELATIONSHIP_ATTRIBUTE_ALLOWED_DIFF_FIELDS
    )


def _normalized_signature_value(*, key: str, value: object) -> object:
    if key == "type_descriptor" and isinstance(value, Mapping):
        return tuple(
            (str(child_key), _normalized_signature_value(key=str(child_key), value=item))
            for child_key, item in sorted(value.items(), key=lambda item: str(item[0]))
            if str(child_key)
            not in _RELATIONSHIP_ATTRIBUTE_TYPE_DESCRIPTOR_ALLOWED_DIFF_FIELDS
        )
    if isinstance(value, Mapping):
        return tuple(
            (str(child_key), _normalized_signature_value(key=str(child_key), value=item))
            for child_key, item in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, (tuple, list)):
        return tuple(
            _normalized_signature_value(key=key, value=item)
            for item in value
        )
    if value == "null":
        return None
    return value


def _relationship_owner_semantic_key(value: str) -> str | None:
    node_marker = "/node:"
    if node_marker not in value:
        if "/relationship:" in value:
            return _optional_text(value.split("/relationship:", 1)[0])
        return None
    prefix, tail = value.split(node_marker, 1)
    parts = tail.split(":")
    if len(parts) < 2 or not parts[0]:
        return None
    return f"{prefix}{node_marker}{parts[0]}"


def _relationship_key(
    *,
    entry: Mapping[str, object],
    relationship_semantic_key: str,
) -> str | None:
    payload = _mapping_value(entry.get("payload"))
    signature = _mapping_value(
        entry.get("relationship_signature") or payload.get("relationship_signature")
    )
    relationship_key = _optional_text(
        entry.get("relationship_key")
        or payload.get("relationship_key")
        or signature.get("relationship_key")
    )
    if relationship_key is not None:
        return relationship_key
    if "/relationship:" in relationship_semantic_key:
        return _optional_text(relationship_semantic_key.rsplit("/relationship:", 1)[-1])
    node_marker = "/node:"
    if node_marker not in relationship_semantic_key:
        return None
    parts = relationship_semantic_key.split(node_marker, 1)[1].split(":")
    if len(parts) < 2:
        return None
    return _optional_text(parts[1])


def _mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
