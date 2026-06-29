from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.semantic_scope_closure import (
    meta_ocg_class_fqn_scope_closure_gate,
    MetaOcgSemanticScopeClosureEvidence,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)


_FUNCTION_SCALAR_SIGNATURE_FIELDS = (
    "owner_key",
    "name",
    "kind",
    "description",
    "verb",
    "is_async",
    "inputs",
    "outputs",
)
_FUNCTION_MEMBERSHIP_SIGNATURE_FIELDS = (
    "class_config_id",
    "function_config_id",
    "is_public",
    "is_constructor",
    "position",
)
_FUNCTION_INVOCATION_SIGNATURE_FIELDS = (
    "function_config_id",
    "position",
    "kind",
    "target_function_config_id",
    "relationship_fingerprint",
    "class_config_relationship_id",
    "root_invocation_id",
    "root_kind",
    "capture_name",
)
FUNCTION_CONFIG_SUBJECT_KIND = "function"
FUNCTION_CONFIG_CREATE_SUBJECT_TYPE = "aware_meta.FunctionConfig"
FUNCTION_INVOCATION_SUBJECT_KIND = "function_invocation"
FUNCTION_INVOCATION_CREATE_SUBJECT_TYPE = "aware_meta.FunctionConfigInvocation"


def function_config_create_typed_operation(
    *,
    semantic_key: str,
    owner_semantic_key: str,
    class_config_id: str,
    function_config_id: str,
    function_name: str,
    owner_key: str,
    source_refs: tuple[str, ...],
    description: str | None = None,
    verb: str | None = None,
    is_async: bool = False,
    kind: str = "instance",
    is_public: bool = True,
    is_constructor: bool = False,
    position: int = 0,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ) = None,
) -> MetaProviderDeltaTypedOperation:
    function_signature = {
        "owner_key": owner_key,
        "name": function_name,
        "kind": kind,
        "description": description,
        "verb": verb,
        "is_async": is_async,
    }
    membership_signature = {
        "class_config_id": class_config_id,
        "function_config_id": function_config_id,
        "is_public": is_public,
        "is_constructor": is_constructor,
        "position": position,
    }
    scope_evidence = _owner_class_scope_closure_fields(
        owner_semantic_key=owner_semantic_key,
        owner_key=owner_key,
        semantic_scope_closure=semantic_scope_closure,
    )
    scope_blocked = scope_evidence.get("semantic_scope_closure_ready") is False
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.function.create:{semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.function.create",
        semantic_key=semantic_key,
        ontology_subject_kind=FUNCTION_CONFIG_SUBJECT_KIND,
        semantic_subject_type=FUNCTION_CONFIG_CREATE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={
            "semantic_key": semantic_key,
            "object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "owner_semantic_key": owner_semantic_key,
            "class_config_id": class_config_id,
            "entity_id": function_config_id,
            "function_config_id": function_config_id,
            "entity_name": function_name,
            "function_name": function_name,
            "owner_key": owner_key,
            "kind": kind,
            "description": description,
            "verb": verb,
            "is_async": is_async,
            "is_public": is_public,
            "is_constructor": is_constructor,
            "position": position,
            "function_signature": function_signature,
            "function_membership_signature": membership_signature,
            "payload": {
                "semantic_key": semantic_key,
                "object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
                "owner_semantic_key": owner_semantic_key,
                "class_config_id": class_config_id,
                "entity_id": function_config_id,
                "function_config_id": function_config_id,
                "entity_name": function_name,
                "function_name": function_name,
                "owner_key": owner_key,
                "kind": kind,
                "description": description,
                "verb": verb,
                "is_async": is_async,
                "is_public": is_public,
                "is_constructor": is_constructor,
                "position": position,
                "function_signature": function_signature,
                "function_membership_signature": membership_signature,
            },
        },
        blocked=scope_blocked,
        blocked_reason=(
            "meta_ocg_function_owner_scope_closure_blocked"
            if scope_blocked
            else None
        ),
        would_execute=not scope_blocked,
        would_persist=not scope_blocked,
        extra=scope_evidence,
        include_operation_evidence=scope_blocked,
    )


def function_config_delete_typed_operation(
    *,
    semantic_key: str,
    owner_semantic_key: str,
    class_config_id: str,
    function_config_id: str,
    function_name: str,
    owner_key: str,
    source_refs: tuple[str, ...],
    kind: str = "instance",
    semantic_source_object_id: str | None = None,
    semantic_scope_closure: (
        MetaOcgSemanticScopeClosureEvidence | Mapping[str, object] | None
    ) = None,
) -> MetaProviderDeltaTypedOperation:
    source_object_id = semantic_source_object_id or function_config_id
    function_signature = {
        "owner_key": owner_key,
        "name": function_name,
        "kind": kind,
    }
    membership_signature = {
        "class_config_id": class_config_id,
        "function_config_id": function_config_id,
    }
    scope_evidence = _owner_class_scope_closure_fields(
        owner_semantic_key=owner_semantic_key,
        owner_key=owner_key,
        semantic_scope_closure=semantic_scope_closure,
    )
    scope_blocked = scope_evidence.get("semantic_scope_closure_ready") is False
    current = {
        "semantic_key": semantic_key,
        "object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
        "owner_semantic_key": owner_semantic_key,
        "parent_semantic_key": owner_semantic_key,
        "class_semantic_key": owner_semantic_key,
        "class_config_id": class_config_id,
        "semantic_source_object_id": source_object_id,
        "entity_id": function_config_id,
        "function_config_id": function_config_id,
        "entity_name": function_name,
        "function_name": function_name,
        "owner_key": owner_key,
        "kind": kind,
        "function_signature": function_signature,
        "function_membership_signature": membership_signature,
    }
    baseline_object = {
        "object_id": function_config_id,
        "object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
        "semantic_source_object_id": source_object_id,
        "entity_id": function_config_id,
        "function_config_id": function_config_id,
        "owner_semantic_key": owner_semantic_key,
        "class_config_id": class_config_id,
        "name": function_name,
        "function_name": function_name,
        "owner_key": owner_key,
        "kind": kind,
        "function_signature": function_signature,
        "function_membership_signature": membership_signature,
    }
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.function.delete:{semantic_key}",
        operation_family="delete",
        provider_operation_type="meta_ocg.function.delete",
        semantic_key=semantic_key,
        ontology_subject_kind=FUNCTION_CONFIG_SUBJECT_KIND,
        semantic_subject_type=FUNCTION_CONFIG_CREATE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={
            "object_id": function_config_id,
            "semantic_source_object_id": source_object_id,
            "object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "object": baseline_object,
        },
        current={**current, "payload": current},
        blocked=scope_blocked,
        blocked_reason=(
            "meta_ocg_function_owner_scope_closure_blocked"
            if scope_blocked
            else None
        ),
        would_execute=not scope_blocked,
        would_persist=not scope_blocked,
        extra=scope_evidence,
        include_operation_evidence=scope_blocked,
    )


def function_invocation_create_typed_operation(
    *,
    semantic_key: str,
    function_semantic_key: str,
    function_config_id: str,
    position: int,
    kind: str,
    target_function_config_id: str,
    source_refs: tuple[str, ...],
    function_config_invocation_id: str | None = None,
    relationship_fingerprint: str = "owner",
    class_config_relationship_id: str | None = None,
    root_invocation_id: str | None = None,
    root_kind: str = "owner",
    capture_name: str | None = None,
) -> MetaProviderDeltaTypedOperation:
    invocation_signature = {
        "function_config_id": function_config_id,
        "position": position,
        "kind": kind,
        "target_function_config_id": target_function_config_id,
        "relationship_fingerprint": relationship_fingerprint,
        "class_config_relationship_id": class_config_relationship_id,
        "root_invocation_id": root_invocation_id,
        "root_kind": root_kind,
        "capture_name": capture_name,
    }
    current = {
        "semantic_key": semantic_key,
        "object_kind": FUNCTION_INVOCATION_SUBJECT_KIND,
        "function_semantic_key": function_semantic_key,
        "parent_semantic_key": function_semantic_key,
        "entity_id": function_config_invocation_id,
        "function_config_invocation_id": function_config_invocation_id,
        "function_config_id": function_config_id,
        "position": position,
        "kind": kind,
        "target_function_config_id": target_function_config_id,
        "relationship_fingerprint": relationship_fingerprint,
        "class_config_relationship_id": class_config_relationship_id,
        "root_invocation_id": root_invocation_id,
        "root_kind": root_kind,
        "capture_name": capture_name,
        "function_invocation_signature": invocation_signature,
    }
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key=f"meta_ocg.function_invocation.create:{semantic_key}",
        operation_family="create",
        provider_operation_type="meta_ocg.function_invocation.create",
        semantic_key=semantic_key,
        ontology_subject_kind=FUNCTION_INVOCATION_SUBJECT_KIND,
        semantic_subject_type=FUNCTION_INVOCATION_CREATE_SUBJECT_TYPE,
        source_refs=source_refs,
        baseline={},
        current={**current, "payload": current},
        would_execute=True,
        would_persist=True,
    )


def function_invocation_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    signature = _function_invocation_current_signature(entry=entry)
    function_semantic_key = _first_text(
        entry.get("function_semantic_key"),
        entry.get("parent_semantic_key"),
        payload.get("function_semantic_key"),
        payload.get("parent_semantic_key"),
        signature.get("function_semantic_key"),
        _function_semantic_key_from_invocation_semantic_key(semantic_key),
    )
    function_config_id = _first_text(
        entry.get("function_config_id"),
        payload.get("function_config_id"),
        signature.get("function_config_id"),
    )
    function_config_invocation_id = _first_text(
        entry.get("function_config_invocation_id"),
        entry.get("entity_id"),
        entry.get("object_id"),
        payload.get("function_config_invocation_id"),
        payload.get("entity_id"),
        payload.get("object_id"),
        signature.get("function_config_invocation_id"),
        signature.get("entity_id"),
        signature.get("object_id"),
    )
    position = _int_value(
        _first_value(
            entry.get("position"),
            payload.get("position"),
            signature.get("position"),
        )
    )
    kind = _first_text(
        entry.get("kind"),
        payload.get("kind"),
        signature.get("kind"),
        "call",
    )
    target_function_config_id = _first_text(
        entry.get("target_function_config_id"),
        payload.get("target_function_config_id"),
        signature.get("target_function_config_id"),
    )
    relationship_fingerprint = _first_text(
        entry.get("relationship_fingerprint"),
        payload.get("relationship_fingerprint"),
        signature.get("relationship_fingerprint"),
        "owner",
    )
    class_config_relationship_id = _first_text(
        entry.get("class_config_relationship_id"),
        payload.get("class_config_relationship_id"),
        signature.get("class_config_relationship_id"),
    )
    root_invocation_id = _first_text(
        entry.get("root_invocation_id"),
        payload.get("root_invocation_id"),
        signature.get("root_invocation_id"),
    )
    root_kind = _first_text(
        entry.get("root_kind"),
        payload.get("root_kind"),
        signature.get("root_kind"),
        "owner",
    )
    capture_name = _first_text(
        entry.get("capture_name"),
        payload.get("capture_name"),
        signature.get("capture_name"),
    )
    resolved_signature = {
        "function_config_id": function_config_id,
        "position": position,
        "kind": kind,
        "target_function_config_id": target_function_config_id,
        "relationship_fingerprint": relationship_fingerprint,
        "class_config_relationship_id": class_config_relationship_id,
        "root_invocation_id": root_invocation_id,
        "root_kind": root_kind,
        "capture_name": capture_name,
    }
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": (
                f"meta_ocg.function_invocation.create:{semantic_key}"
            ),
            "provider_operation_type": "meta_ocg.function_invocation.create",
            "semantic_subject_type": FUNCTION_INVOCATION_CREATE_SUBJECT_TYPE,
            "ontology_subject_kind": FUNCTION_INVOCATION_SUBJECT_KIND,
            "object_kind": FUNCTION_INVOCATION_SUBJECT_KIND,
            "function_semantic_key": function_semantic_key,
            "parent_semantic_key": function_semantic_key,
            "entity_id": function_config_invocation_id,
            "function_config_invocation_id": function_config_invocation_id,
            "function_config_id": function_config_id,
            "position": position,
            "kind": kind,
            "target_function_config_id": target_function_config_id,
            "relationship_fingerprint": relationship_fingerprint,
            "class_config_relationship_id": class_config_relationship_id,
            "root_invocation_id": root_invocation_id,
            "root_kind": root_kind,
            "capture_name": capture_name,
            "function_invocation_signature": resolved_signature,
        }
    )
    return (normalized,)


def function_config_create_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    function_signature = _function_current_signature(entry=entry)
    membership_signature = _function_current_membership_signature(entry=entry)
    owner_semantic_key = _first_text(
        entry.get("owner_semantic_key"),
        entry.get("parent_semantic_key"),
        entry.get("class_semantic_key"),
        payload.get("owner_semantic_key"),
        payload.get("parent_semantic_key"),
        payload.get("class_semantic_key"),
    )
    owner_key = _first_text(
        entry.get("owner_key"),
        entry.get("class_fqn"),
        payload.get("owner_key"),
        payload.get("class_fqn"),
        function_signature.get("owner_key"),
        _owner_key_from_owner_semantic_key(owner_semantic_key),
    )
    function_name = _first_text(
        entry.get("function_name"),
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("function_name"),
        payload.get("name"),
        payload.get("entity_name"),
        function_signature.get("name"),
        _function_name_from_semantic_key(semantic_key),
    )
    class_config_id = _first_text(
        entry.get("class_config_id"),
        payload.get("class_config_id"),
        membership_signature.get("class_config_id"),
    )
    function_config_id = _first_text(
        entry.get("function_config_id"),
        entry.get("entity_id"),
        payload.get("function_config_id"),
        payload.get("entity_id"),
        membership_signature.get("function_config_id"),
    )
    scope_evidence = _owner_class_scope_closure_fields(
        owner_semantic_key=owner_semantic_key,
        owner_key=owner_key,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure")
            or payload.get("semantic_scope_closure")
        ),
    )
    kind = _first_text(
        entry.get("kind"),
        payload.get("kind"),
        function_signature.get("kind"),
        "instance",
    )
    description = _first_text(
        entry.get("description"),
        entry.get("function_description"),
        payload.get("description"),
        payload.get("function_description"),
        function_signature.get("description"),
    )
    verb = _first_text(
        entry.get("verb"),
        entry.get("function_verb"),
        payload.get("verb"),
        payload.get("function_verb"),
        function_signature.get("verb"),
    )
    is_async = _bool_value(
        _first_value(
            entry.get("is_async"),
            payload.get("is_async"),
            function_signature.get("is_async"),
            False,
        )
    )
    is_public = _bool_value(
        _first_value(
            entry.get("is_public"),
            payload.get("is_public"),
            membership_signature.get("is_public"),
            True,
        )
    )
    is_constructor = _bool_value(
        _first_value(
            entry.get("is_constructor"),
            payload.get("is_constructor"),
            membership_signature.get("is_constructor"),
            False,
        )
    )
    position = _int_value(
        _first_value(
            entry.get("position"),
            payload.get("position"),
            membership_signature.get("position"),
            0,
        )
    )
    normalized = dict(entry)
    resolved_function_signature = {
        "owner_key": owner_key,
        "name": function_name,
        "kind": kind,
        "description": description,
        "verb": verb,
        "is_async": is_async,
    }
    resolved_membership_signature = {
        "class_config_id": class_config_id,
        "function_config_id": function_config_id,
        "is_public": is_public,
        "is_constructor": is_constructor,
        "position": position,
    }
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.function.create:{semantic_key}",
            "provider_operation_type": "meta_ocg.function.create",
            "semantic_subject_type": FUNCTION_CONFIG_CREATE_SUBJECT_TYPE,
            "ontology_subject_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "owner_semantic_key": owner_semantic_key,
            "parent_semantic_key": owner_semantic_key,
            "class_semantic_key": owner_semantic_key,
            "class_config_id": class_config_id,
            "function_config_id": function_config_id,
            "entity_id": function_config_id,
            "function_name": function_name,
            "name": function_name,
            "entity_name": function_name,
            "owner_key": owner_key,
            "kind": kind,
            "description": description,
            "verb": verb,
            "is_async": is_async,
            "is_public": is_public,
            "is_constructor": is_constructor,
            "position": position,
            "function_signature": resolved_function_signature,
            "function_membership_signature": resolved_membership_signature,
            **scope_evidence,
        }
    )
    return (normalized,)


def function_config_delete_dirty_entry(
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return (dict(entry),)
    payload = _mapping_value(entry.get("payload"))
    baseline_object = dict(_mapping_value(entry.get("baseline_object")))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    function_signature = (
        _function_baseline_signature(entry=entry)
        or _function_current_signature(entry=entry)
    )
    membership_signature = (
        _function_baseline_membership_signature(entry=entry)
        or _function_current_membership_signature(entry=entry)
    )
    owner_semantic_key = _first_text(
        entry.get("owner_semantic_key"),
        entry.get("parent_semantic_key"),
        entry.get("class_semantic_key"),
        payload.get("owner_semantic_key"),
        payload.get("parent_semantic_key"),
        payload.get("class_semantic_key"),
        baseline_object.get("owner_semantic_key"),
        baseline_payload.get("owner_semantic_key"),
        baseline_object.get("parent_semantic_key"),
        baseline_payload.get("parent_semantic_key"),
        baseline_object.get("class_semantic_key"),
        baseline_payload.get("class_semantic_key"),
    )
    owner_key = _first_text(
        entry.get("owner_key"),
        entry.get("class_fqn"),
        payload.get("owner_key"),
        payload.get("class_fqn"),
        baseline_object.get("owner_key"),
        baseline_payload.get("owner_key"),
        baseline_object.get("class_fqn"),
        baseline_payload.get("class_fqn"),
        function_signature.get("owner_key"),
        _owner_key_from_owner_semantic_key(owner_semantic_key),
    )
    function_name = _first_text(
        entry.get("function_name"),
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("function_name"),
        payload.get("name"),
        payload.get("entity_name"),
        baseline_object.get("function_name"),
        baseline_object.get("name"),
        baseline_object.get("entity_name"),
        baseline_payload.get("function_name"),
        baseline_payload.get("name"),
        baseline_payload.get("entity_name"),
        function_signature.get("name"),
        _function_name_from_semantic_key(semantic_key),
    )
    class_config_id = _first_text(
        entry.get("class_config_id"),
        payload.get("class_config_id"),
        baseline_object.get("class_config_id"),
        baseline_payload.get("class_config_id"),
        membership_signature.get("class_config_id"),
    )
    function_config_id = _first_text(
        entry.get("function_config_id"),
        entry.get("entity_id"),
        payload.get("function_config_id"),
        payload.get("entity_id"),
        baseline_object.get("function_config_id"),
        baseline_object.get("entity_id"),
        baseline_object.get("object_id"),
        baseline_payload.get("function_config_id"),
        baseline_payload.get("entity_id"),
        baseline_payload.get("object_id"),
        membership_signature.get("function_config_id"),
        entry.get("baseline_object_id"),
    )
    kind = _first_text(
        entry.get("kind"),
        payload.get("kind"),
        baseline_object.get("kind"),
        baseline_payload.get("kind"),
        function_signature.get("kind"),
        "instance",
    )
    resolved_function_signature = {
        "owner_key": owner_key,
        "name": function_name,
        "kind": kind,
    }
    resolved_membership_signature = {
        "class_config_id": class_config_id,
        "function_config_id": function_config_id,
    }
    scope_evidence = _owner_class_scope_closure_fields(
        owner_semantic_key=owner_semantic_key,
        owner_key=owner_key,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure")
            or payload.get("semantic_scope_closure")
        ),
    )
    baseline_object.update(
        {
            "object_id": function_config_id,
            "object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "entity_id": function_config_id,
            "function_config_id": function_config_id,
            "owner_semantic_key": owner_semantic_key,
            "parent_semantic_key": owner_semantic_key,
            "class_semantic_key": owner_semantic_key,
            "class_config_id": class_config_id,
            "name": function_name,
            "function_name": function_name,
            "entity_name": function_name,
            "owner_key": owner_key,
            "kind": kind,
            "function_signature": resolved_function_signature,
            "function_membership_signature": resolved_membership_signature,
        }
    )
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.function.delete:{semantic_key}",
            "provider_operation_type": "meta_ocg.function.delete",
            "semantic_subject_type": FUNCTION_CONFIG_CREATE_SUBJECT_TYPE,
            "ontology_subject_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "owner_semantic_key": owner_semantic_key,
            "parent_semantic_key": owner_semantic_key,
            "class_semantic_key": owner_semantic_key,
            "class_config_id": class_config_id,
            "function_config_id": function_config_id,
            "entity_id": function_config_id,
            "function_name": function_name,
            "name": function_name,
            "entity_name": function_name,
            "owner_key": owner_key,
            "kind": kind,
            "function_signature": resolved_function_signature,
            "function_membership_signature": resolved_membership_signature,
            "baseline_object_id": function_config_id,
            "baseline_object_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "baseline_object": baseline_object,
            **scope_evidence,
        }
    )
    return (normalized,)


def split_function_update_entry(
    *,
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    return function_config_update_dirty_entry(entry=entry)


def function_config_update_dirty_entry(
    *,
    entry: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    membership_changed = _function_membership_signature_changed(entry=entry)
    scalar_changed = _function_scalar_signature_changed(entry=entry)
    entries: list[dict[str, object]] = []
    if scalar_changed or not membership_changed:
        entries.append(_function_scalar_update_dirty_entry(entry=entry))
    if membership_changed:
        entries.append(_function_membership_dirty_entry(entry=entry))
    return tuple(entries)


def _function_scalar_update_dirty_entry(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return dict(entry)
    payload = _mapping_value(entry.get("payload"))
    baseline_object = _mapping_value(entry.get("baseline_object"))
    baseline_payload = _mapping_value(baseline_object.get("payload"))
    function_signature = _function_current_signature(entry=entry)
    baseline_signature = _function_baseline_signature(entry=entry)
    membership_signature = _function_current_membership_signature(entry=entry)
    owner_semantic_key = _first_text(
        entry.get("owner_semantic_key"),
        entry.get("parent_semantic_key"),
        entry.get("class_semantic_key"),
        payload.get("owner_semantic_key"),
        payload.get("parent_semantic_key"),
        payload.get("class_semantic_key"),
    )
    owner_key = _first_text(
        entry.get("owner_key"),
        payload.get("owner_key"),
        function_signature.get("owner_key"),
        baseline_object.get("owner_key"),
        baseline_payload.get("owner_key"),
        baseline_signature.get("owner_key"),
        _owner_key_from_owner_semantic_key(owner_semantic_key),
    )
    function_name = _first_text(
        entry.get("function_name"),
        entry.get("name"),
        entry.get("entity_name"),
        payload.get("function_name"),
        payload.get("name"),
        payload.get("entity_name"),
        function_signature.get("name"),
        baseline_object.get("name"),
        baseline_object.get("entity_name"),
        baseline_payload.get("name"),
        baseline_payload.get("entity_name"),
        baseline_signature.get("name"),
        _function_name_from_semantic_key(semantic_key),
    )
    function_config_id = _first_text(
        entry.get("function_config_id"),
        entry.get("entity_id"),
        payload.get("function_config_id"),
        payload.get("entity_id"),
        baseline_object.get("function_config_id"),
        baseline_object.get("entity_id"),
        baseline_object.get("object_id"),
        baseline_payload.get("function_config_id"),
        baseline_payload.get("entity_id"),
        membership_signature.get("function_config_id"),
    )
    class_config_id = _first_text(
        entry.get("class_config_id"),
        payload.get("class_config_id"),
        baseline_object.get("class_config_id"),
        baseline_payload.get("class_config_id"),
        membership_signature.get("class_config_id"),
    )
    kind = _first_text(
        entry.get("kind"),
        payload.get("kind"),
        function_signature.get("kind"),
        baseline_object.get("kind"),
        baseline_payload.get("kind"),
        baseline_signature.get("kind"),
        "instance",
    )
    description = _first_text(
        entry.get("description"),
        entry.get("function_description"),
        payload.get("description"),
        payload.get("function_description"),
        function_signature.get("description"),
    )
    verb = _first_text(
        entry.get("verb"),
        entry.get("function_verb"),
        payload.get("verb"),
        payload.get("function_verb"),
        function_signature.get("verb"),
    )
    is_async = _bool_value(
        _first_value(
            entry.get("is_async"),
            payload.get("is_async"),
            function_signature.get("is_async"),
        )
    )
    scope_evidence = _owner_class_scope_closure_fields(
        owner_semantic_key=owner_semantic_key,
        owner_key=owner_key,
        semantic_scope_closure=(
            entry.get("semantic_scope_closure")
            or payload.get("semantic_scope_closure")
        ),
    )
    normalized = dict(entry)
    normalized.update(
        {
            "typed_operation_key": f"meta_ocg.function.update:{semantic_key}",
            "provider_operation_type": "meta_ocg.function.update",
            "semantic_subject_type": "aware_meta.FunctionConfig",
            "ontology_subject_kind": FUNCTION_CONFIG_SUBJECT_KIND,
            "owner_semantic_key": owner_semantic_key,
            "parent_semantic_key": owner_semantic_key,
            "class_semantic_key": owner_semantic_key,
            "class_config_id": class_config_id,
            "function_config_id": function_config_id,
            "entity_id": function_config_id,
            "function_name": function_name,
            "name": function_name,
            "entity_name": function_name,
            "owner_key": owner_key,
            "kind": kind,
            "description": description,
            "verb": verb,
            "is_async": is_async,
            "function_signature": {
                "owner_key": owner_key,
                "name": function_name,
                "kind": kind,
                "description": description,
                "verb": verb,
                "is_async": is_async,
            },
            **scope_evidence,
        }
    )
    return normalized


def _function_scalar_signature_changed(*, entry: Mapping[str, object]) -> bool:
    current_signature = _field_projection(
        _function_current_signature(entry=entry),
        fields=_FUNCTION_SCALAR_SIGNATURE_FIELDS,
    )
    baseline_signature = _field_projection(
        _function_baseline_signature(entry=entry),
        fields=_FUNCTION_SCALAR_SIGNATURE_FIELDS,
    )
    if not current_signature:
        return False
    return current_signature != baseline_signature


def _function_membership_signature_changed(*, entry: Mapping[str, object]) -> bool:
    current_signature = _field_projection(
        _function_current_membership_signature(entry=entry),
        fields=_FUNCTION_MEMBERSHIP_SIGNATURE_FIELDS,
    )
    baseline_signature = _field_projection(
        _function_baseline_membership_signature(entry=entry),
        fields=_FUNCTION_MEMBERSHIP_SIGNATURE_FIELDS,
    )
    if not current_signature or not baseline_signature:
        return False
    comparable_fields = tuple(
        field
        for field in _FUNCTION_MEMBERSHIP_SIGNATURE_FIELDS
        if (
            field in current_signature
            and field in baseline_signature
            and current_signature[field] is not None
            and baseline_signature[field] is not None
        )
    )
    if not comparable_fields:
        return False
    return any(
        current_signature[field] != baseline_signature[field]
        for field in comparable_fields
    )


def _function_membership_dirty_entry(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = dict(_mapping_value(entry.get("payload")))
    current_signature = _function_current_membership_signature(entry=entry)
    baseline_signature = _function_baseline_membership_signature(entry=entry)
    baseline_object = dict(_mapping_value(entry.get("baseline_object")))
    membership_semantic_key = _function_membership_semantic_key(entry=entry)
    membership_object_id = _first_text(
        baseline_object.get("class_config_function_config_id"),
        entry.get("class_config_function_config_id"),
        payload.get("class_config_function_config_id"),
    )
    membership_payload = dict(payload)
    membership_payload.update(
        {
            "semantic_key": membership_semantic_key,
            "object_kind": "function_membership",
            "ontology_subject_kind": "function_membership",
            "entity_id": membership_object_id,
            "class_config_function_config_id": membership_object_id,
            "class_config_id": _first_text(
                entry.get("class_config_id"),
                payload.get("class_config_id"),
                current_signature.get("class_config_id"),
            ),
            "function_config_id": _first_text(
                entry.get("function_config_id"),
                payload.get("function_config_id"),
                current_signature.get("function_config_id"),
            ),
            "function_semantic_key": _optional_text(entry.get("semantic_key")),
            "function_membership_semantic_key": membership_semantic_key,
            "function_membership_signature": current_signature,
        }
    )
    baseline_object.update(
        {
            "object_id": membership_object_id,
            "object_kind": "function_membership",
            "class_config_function_config_id": membership_object_id,
            "class_config_id": baseline_signature.get("class_config_id"),
            "function_config_id": baseline_signature.get("function_config_id"),
            "function_membership_semantic_key": membership_semantic_key,
            "function_membership_signature": baseline_signature,
        }
    )
    updated = dict(entry)
    updated.update(
        {
            "semantic_key": membership_semantic_key,
            "source_delta_key": (
                "aware_meta.runtime_delta.class_config_function_config:"
                f"{membership_semantic_key}"
            ),
            "semantic_subject_type": "aware_meta.ClassConfigFunctionConfig",
            "ontology_subject_kind": "function_membership",
            "object_kind": "function_membership",
            "node_type": "function_membership",
            "entity_id": membership_object_id,
            "class_config_function_config_id": membership_object_id,
            "class_config_id": membership_payload.get("class_config_id"),
            "function_config_id": membership_payload.get("function_config_id"),
            "function_semantic_key": _optional_text(entry.get("semantic_key")),
            "function_membership_semantic_key": membership_semantic_key,
            "function_membership_signature": current_signature,
            "payload": membership_payload,
            "baseline_object_id": membership_object_id,
            "baseline_object_kind": "function_membership",
            "baseline_object": baseline_object,
        }
    )
    return updated


def _function_current_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = _mapping_value(entry.get("payload"))
    return _mapping_value(
        entry.get("function_signature") or payload.get("function_signature")
    )


def _function_baseline_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    baseline_object = _mapping_value(entry.get("baseline_object"))
    return _mapping_value(
        entry.get("baseline_function_signature")
        or baseline_object.get("function_signature")
    )


def _function_current_membership_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = _mapping_value(entry.get("payload"))
    signature = _mapping_value(
        entry.get("function_membership_signature")
        or payload.get("function_membership_signature")
    )
    if signature:
        return signature
    function_signature = _function_current_signature(entry=entry)
    return _field_projection(
        {
            **function_signature,
            "class_config_id": _first_text(
                entry.get("class_config_id"),
                payload.get("class_config_id"),
                function_signature.get("class_config_id"),
            ),
            "function_config_id": _first_text(
                entry.get("function_config_id"),
                payload.get("function_config_id"),
                function_signature.get("function_config_id"),
            ),
        },
        fields=_FUNCTION_MEMBERSHIP_SIGNATURE_FIELDS,
    )


def _function_baseline_membership_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    baseline_object = _mapping_value(entry.get("baseline_object"))
    signature = _mapping_value(
        entry.get("baseline_function_membership_signature")
        or baseline_object.get("function_membership_signature")
    )
    if signature:
        return signature
    function_signature = _function_baseline_signature(entry=entry)
    return _field_projection(
        {
            **function_signature,
            "class_config_id": _first_text(
                baseline_object.get("class_config_id"),
                function_signature.get("class_config_id"),
            ),
            "function_config_id": _first_text(
                baseline_object.get("function_config_id"),
                function_signature.get("function_config_id"),
            ),
        },
        fields=_FUNCTION_MEMBERSHIP_SIGNATURE_FIELDS,
    )


def _function_invocation_current_signature(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = _mapping_value(entry.get("payload"))
    return _mapping_value(
        entry.get("function_invocation_signature")
        or payload.get("function_invocation_signature")
    )


def _function_membership_semantic_key(
    *,
    entry: Mapping[str, object],
) -> str:
    payload = _mapping_value(entry.get("payload"))
    semantic_key = _optional_text(
        entry.get("function_membership_semantic_key")
        or payload.get("function_membership_semantic_key")
    )
    if semantic_key is not None:
        return semantic_key
    return f"{_string_value(entry.get('semantic_key'))}/membership:class_config"


def _owner_class_scope_closure_fields(
    *,
    owner_semantic_key: str | None,
    owner_key: str | None,
    semantic_scope_closure: object,
) -> dict[str, object]:
    if semantic_scope_closure is None:
        return {}
    resolved_owner_key = _optional_text(owner_key)
    if resolved_owner_key is None:
        return {
            "semantic_scope_closure_consumed": True,
            "semantic_scope_closure_ready": False,
            "semantic_scope_closure_blocked": True,
            "semantic_scope_closure_blockers": (
                "semantic_scope_closure_function_owner_class_fqn_missing",
            ),
        }
    gate = meta_ocg_class_fqn_scope_closure_gate(
        package_fqn_prefix=_owner_package_fqn_prefix(
            owner_semantic_key=owner_semantic_key,
            owner_key=resolved_owner_key,
        ),
        class_fqn=resolved_owner_key,
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


def _owner_package_fqn_prefix(
    *,
    owner_semantic_key: str | None,
    owner_key: str,
) -> str:
    if owner_semantic_key is not None and owner_semantic_key.startswith("ocg:"):
        prefix = owner_semantic_key.removeprefix("ocg:").split("/", 1)[0].strip()
        if prefix:
            return prefix
    return owner_key.split(".", maxsplit=1)[0]


def _owner_key_from_owner_semantic_key(value: str | None) -> str | None:
    if value is None:
        return None
    _, separator, node_key = value.partition("/node:")
    if not separator:
        return None
    return _optional_text(node_key.split("/", 1)[0])


def _function_name_from_semantic_key(value: str) -> str | None:
    _, separator, tail = value.partition("/function:")
    if separator:
        return _optional_text(tail.split("/", 1)[0])
    if "." not in value:
        return None
    return _optional_text(value.rsplit(".", 1)[-1].split("/", 1)[0])


def _function_semantic_key_from_invocation_semantic_key(
    value: str,
) -> str | None:
    for separator in ("/invocation:", "/function_invocation:"):
        function_key, found, _tail = value.partition(separator)
        if found:
            return _optional_text(function_key)
    return None


def _field_projection(
    value: Mapping[str, object],
    *,
    fields: tuple[str, ...],
) -> dict[str, object]:
    return {field: value[field] for field in fields if field in value}


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


def _first_value(*values: object) -> object | None:
    for value in values:
        if value is not None:
            return value
    return None


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = _optional_text(value)
    if text is None:
        return False
    return text.casefold() in {"1", "true", "yes", "y", "on"}


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = _optional_text(value)
    if text is None:
        return 0
    return int(text)


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "FUNCTION_CONFIG_CREATE_SUBJECT_TYPE",
    "FUNCTION_CONFIG_SUBJECT_KIND",
    "FUNCTION_INVOCATION_CREATE_SUBJECT_TYPE",
    "FUNCTION_INVOCATION_SUBJECT_KIND",
    "function_config_create_dirty_entry",
    "function_config_create_typed_operation",
    "function_config_update_dirty_entry",
    "function_invocation_create_dirty_entry",
    "function_invocation_create_typed_operation",
    "split_function_update_entry",
]
