from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionRef,
    CodeSegmentRef,
)
from aware_meta.materialization.deltas.coercion import mapping_value
from aware_meta.materialization.deltas.coercion import optional_text
from aware_meta.materialization.deltas.coercion import tuple_mappings
from aware_meta.materialization.deltas.coercion import tuple_text
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaSourceProjectionContext,
    MetaProviderDeltaSourceProjectionFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_types import JsonObject


FEATURE_KEY = "function_config"
FUNCTION_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON = (
    "meta_source_projection_function_config_requires_renderer_segment_policy"
)
FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_function_config_description_segment_delta_ready"
)
FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_function_config_description_requires_renderable_segment"
)
FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "single_source_ref",
    "function_name",
    "owner_key",
    "renderable_description_text",
)
FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_function_config_signature_segment_delta_ready"
)
FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_function_config_signature_requires_renderable_signature"
)
FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "single_source_ref",
    "function_name",
    "owner_key",
    "renderable_signature_text",
)
FUNCTION_MEMBERSHIP_SOURCE_PROJECTION_SKIPPED_REASON = (
    "meta_source_projection_function_membership_requires_renderer_segment_policy"
)
_MISSING = object()
_PRIMITIVE_TYPE_TEXT = {
    "any": "Any",
    "boolean": "Bool",
    "bool": "Bool",
    "bytes": "Bytes",
    "datetime": "DateTime",
    "date_time": "DateTime",
    "float": "Float",
    "integer": "Int",
    "int": "Int",
    "json": "Json",
    "string": "String",
    "uuid": "UUID",
    "vector": "Vector",
}


def source_projection_feature_results_from_function_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    event_refs = (
        meta_provider_delta_world_change_event_key(operation=operation),
    )
    results: list[MetaProviderDeltaSourceProjectionFeatureResult] = []
    entry = _code_section_delta_entry_from_function_description_operation(
        operation=operation,
        context=context,
    )
    if entry is not None:
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key=FEATURE_KEY,
                operation=operation,
                entries=(entry,),
                reason=(
                    FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_READY_REASON
                ),
                required_evidence_fields=(
                    FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    elif _function_description_changed(operation=operation):
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason=(
                    FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_BLOCKED_REASON
                ),
                event_refs=event_refs,
                required_evidence_fields=(
                    FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
                missing_evidence_fields=(
                    _missing_description_projection_fields(operation=operation)
                ),
            ),
        )
    entry = _code_section_delta_entry_from_function_signature_operation(
        operation=operation,
        context=context,
    )
    if entry is not None:
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key=FEATURE_KEY,
                operation=operation,
                entries=(entry,),
                reason=FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_READY_REASON,
                required_evidence_fields=(
                    FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    elif _function_signature_shape_changed(operation=operation):
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason=FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_BLOCKED_REASON,
                event_refs=event_refs,
                required_evidence_fields=(
                    FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
                missing_evidence_fields=(
                    _missing_signature_projection_fields(operation=operation)
                ),
            ),
        )
    if results:
        return tuple(results)
    return (
        MetaProviderDeltaSourceProjectionFeatureResult.skipped(
            feature_key=FEATURE_KEY,
            operation=operation,
            reason=_skipped_reason(operation=operation),
            event_refs=event_refs,
        ),
    )


def _skipped_reason(*, operation: MetaProviderDeltaTypedOperation) -> str:
    if operation.ontology_subject_kind == "function_membership":
        return FUNCTION_MEMBERSHIP_SOURCE_PROJECTION_SKIPPED_REASON
    return FUNCTION_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON


def _code_section_delta_entry_from_function_description_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> CodeSectionDeltaEntry | None:
    if not _function_description_changed(operation=operation):
        return None
    relative_path = _single_source_ref(operation.source_refs)
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    content_text = _current_description_text(operation=operation)
    if (
        relative_path is None
        or function_name is None
        or owner_name is None
        or content_text is None
    ):
        return None
    baseline_text = _baseline_description_text(operation=operation)
    owner_key = _owner_key(operation=operation)
    section_ref = CodeSectionRef(
        package_name=context.package_name,
        relative_path=relative_path,
        language=context.target_language,
        section_type="function",
        qualname=f"{owner_name}.{function_name}",
        semantic_key=operation.semantic_key,
        source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.function_description_section_ref"
                ),
                "operation_key": operation.operation_key,
                "function_name": function_name,
                "owner_key": owner_key,
            }
        ),
    )
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.replace_segment,
        section_ref=section_ref,
        segment_ref=CodeSegmentRef(
            segment_name="description_comment",
            before_segment_hash=(
                _sha256_digest(baseline_text)
                if baseline_text is not None
                else None
            ),
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "function_description_segment_ref"
                    ),
                    "function_name": function_name,
                }
            ),
        ),
        content_text=content_text,
        before_hash=None,
        after_hash=_sha256_digest(content_text),
        event_ref=meta_provider_delta_world_change_event_key(operation=operation),
        semantic_key=operation.semantic_key,
        provider_key="aware_meta",
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "function_description_section_delta"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "function_name": function_name,
                "owner_key": owner_key,
            }
        ),
    )


def _code_section_delta_entry_from_function_signature_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> CodeSectionDeltaEntry | None:
    if not _function_signature_shape_changed(operation=operation):
        return None
    relative_path = _single_source_ref(operation.source_refs)
    function_name = _function_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    content_text = _current_signature_text(operation=operation)
    if (
        relative_path is None
        or function_name is None
        or owner_name is None
        or content_text is None
    ):
        return None
    baseline_text = _baseline_signature_text(operation=operation)
    owner_key = _owner_key(operation=operation)
    section_ref = CodeSectionRef(
        package_name=context.package_name,
        relative_path=relative_path,
        language=context.target_language,
        section_type="function",
        qualname=f"{owner_name}.{function_name}",
        semantic_key=operation.semantic_key,
        source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.function_signature_section_ref"
                ),
                "operation_key": operation.operation_key,
                "function_name": function_name,
                "owner_key": owner_key,
            }
        ),
    )
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.replace_segment,
        section_ref=section_ref,
        segment_ref=CodeSegmentRef(
            segment_name="signature",
            before_segment_hash=(
                _sha256_digest(baseline_text)
                if baseline_text is not None
                else None
            ),
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta.function_signature_segment_ref"
                    ),
                    "function_name": function_name,
                }
            ),
        ),
        content_text=content_text,
        before_hash=None,
        after_hash=_sha256_digest(content_text),
        event_ref=meta_provider_delta_world_change_event_key(operation=operation),
        semantic_key=operation.semantic_key,
        provider_key="aware_meta",
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta.function_signature_section_delta"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "function_name": function_name,
                "owner_key": owner_key,
            }
        ),
    )


def _function_description_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "function"
        or operation.operation_family != "update"
    ):
        return False
    current_description = _description_value(
        payload=_function_signature(payload=operation.current)
    )
    baseline_description = _description_value(
        payload=_function_signature(payload=operation.baseline)
    )
    if current_description is _MISSING:
        return False
    return current_description != baseline_description


def _function_signature_shape_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "function"
        or operation.operation_family != "update"
    ):
        return False
    current_signature = _function_signature(payload=operation.current)
    current_shape = _function_signature_shape_payload(signature=current_signature)
    if current_shape is None:
        return False
    baseline_shape = _function_signature_shape_payload(
        signature=_function_signature(payload=operation.baseline)
    )
    return current_shape != baseline_shape


def _missing_description_projection_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs) is None:
        missing.append("single_source_ref")
    if _function_name(operation=operation) is None:
        missing.append("function_name")
    if _owner_name(operation=operation) is None:
        missing.append("owner_key")
    if _current_description_text(operation=operation) is None:
        missing.append("renderable_description_text")
    return tuple(missing)


def _missing_signature_projection_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs) is None:
        missing.append("single_source_ref")
    if _function_name(operation=operation) is None:
        missing.append("function_name")
    if _owner_name(operation=operation) is None:
        missing.append("owner_key")
    if _current_signature_text(operation=operation) is None:
        missing.append("renderable_signature_text")
    return tuple(missing)


def _current_description_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    value = _description_value(payload=_function_signature(payload=operation.current))
    if not isinstance(value, str):
        return None
    return value


def _baseline_description_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    value = _description_value(payload=_function_signature(payload=operation.baseline))
    if not isinstance(value, str):
        return None
    return value


def _current_signature_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    return _signature_text_from_signature(
        _function_signature(payload=operation.current)
    )


def _baseline_signature_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    return _signature_text_from_signature(
        _function_signature(payload=operation.baseline)
    )


def _signature_text_from_signature(
    signature: Mapping[str, object],
) -> str | None:
    inputs = tuple_mappings(signature.get("inputs"))
    outputs = tuple_mappings(signature.get("outputs"))
    if "inputs" not in signature or "outputs" not in signature:
        return None
    input_texts: list[str] = []
    for input_signature in sorted(inputs, key=_function_attribute_sort_key):
        input_text = _function_input_text(input_signature)
        if input_text is None:
            return None
        input_texts.append(input_text)
    return_text = _function_return_text(outputs)
    if return_text is None:
        return None
    return f"({', '.join(input_texts)}) -> {return_text}"


def _function_signature_shape_payload(
    *,
    signature: Mapping[str, object],
) -> tuple[tuple[tuple[str, object], ...], ...] | None:
    if "inputs" not in signature and "outputs" not in signature:
        return None
    inputs = tuple(
        _function_attribute_shape_payload(item)
        for item in sorted(
            tuple_mappings(signature.get("inputs")),
            key=_function_attribute_sort_key,
        )
    )
    outputs = tuple(
        _function_attribute_shape_payload(item)
        for item in sorted(
            tuple_mappings(signature.get("outputs")),
            key=_function_attribute_sort_key,
        )
    )
    return (
        (("kind", "inputs"), ("items", inputs)),
        (("kind", "outputs"), ("items", outputs)),
    )


def _function_attribute_shape_payload(
    signature: Mapping[str, object],
) -> tuple[tuple[str, object], ...]:
    descriptor = mapping_value(signature.get("type_descriptor"))
    return (
        ("name", optional_text(signature.get("name")) or ""),
        ("type", _json_safe_mapping(descriptor)),
        ("is_required", signature.get("is_required")),
        ("position", signature.get("position")),
    )


def _function_attribute_sort_key(
    signature: Mapping[str, object],
) -> tuple[int, str]:
    position = signature.get("position")
    resolved_position = position if isinstance(position, int) else 0
    return (resolved_position, optional_text(signature.get("name")) or "")


def _function_input_text(signature: Mapping[str, object]) -> str | None:
    name = optional_text(signature.get("name"))
    type_text = _type_text_from_signature(signature)
    if name is None or type_text is None:
        return None
    return f"{name} {type_text}"


def _function_return_text(
    outputs: tuple[dict[str, object], ...],
) -> str | None:
    if not outputs:
        return None
    sorted_outputs = tuple(sorted(outputs, key=_function_attribute_sort_key))
    if len(sorted_outputs) == 1:
        return _type_text_from_signature(sorted_outputs[0])
    output_texts: list[str] = []
    for output_signature in sorted_outputs:
        output_text = _function_input_text(output_signature)
        if output_text is None:
            return None
        output_texts.append(output_text)
    return f"({', '.join(output_texts)})"


def _type_text_from_signature(signature: Mapping[str, object]) -> str | None:
    descriptor = mapping_value(signature.get("type_descriptor"))
    if not descriptor:
        descriptor = mapping_value(signature)
    base_text = _type_text_from_descriptor(descriptor)
    if base_text is None:
        return None
    if signature.get("is_required") is False:
        return f"{base_text}?"
    return base_text


def _type_text_from_descriptor(descriptor: Mapping[str, object]) -> str | None:
    descriptor_kind = optional_text(descriptor.get("kind"))
    if descriptor_kind == "primitive":
        return _primitive_type_text(descriptor.get("primitive_base_type"))
    if descriptor_kind == "class":
        return _fqn_leaf(descriptor.get("class_fqn"))
    if descriptor_kind == "enum":
        return _fqn_leaf(descriptor.get("enum_fqn"))
    if descriptor_kind == "collection":
        child_text = _first_child_type_text(descriptor=descriptor)
        if child_text is None:
            return None
        return f"{child_text}[]"
    if descriptor_kind == "union":
        child_text = _single_non_null_child_type_text(descriptor=descriptor)
        if child_text is None:
            return None
        return child_text
    return None


def _primitive_type_text(value: object) -> str | None:
    raw_value = optional_text(value)
    if raw_value is None:
        return None
    key = raw_value.rsplit(".", maxsplit=1)[-1].lower()
    return _PRIMITIVE_TYPE_TEXT.get(key)


def _first_child_type_text(*, descriptor: Mapping[str, object]) -> str | None:
    child_links = tuple_mappings(descriptor.get("child_links"))
    if not child_links:
        return None
    child = mapping_value(child_links[0].get("child"))
    return _type_text_from_descriptor(child)


def _single_non_null_child_type_text(*, descriptor: Mapping[str, object]) -> str | None:
    child_links = tuple_mappings(descriptor.get("child_links"))
    child_texts = tuple(
        text
        for link in child_links
        for child in (mapping_value(link.get("child")),)
        if optional_text(child.get("primitive_base_type")) != "null"
        for text in (_type_text_from_descriptor(child),)
        if text is not None
    )
    if len(child_texts) != 1:
        return None
    return child_texts[0]


def _fqn_leaf(value: object) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    return text.rsplit(".", maxsplit=1)[-1]


def _json_safe_mapping(value: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    return tuple(
        sorted(
            (str(key), _json_safe_value(item))
            for key, item in value.items()
        )
    )


def _json_safe_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, tuple):
        return tuple(_json_safe_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_json_safe_value(item) for item in value)
    return value


def _function_signature(*, payload: Mapping[str, object]) -> Mapping[str, object]:
    signature = mapping_value(payload.get("function_signature"))
    if signature:
        return signature
    nested_payload = mapping_value(payload.get("payload"))
    signature = mapping_value(nested_payload.get("function_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("function_signature"))
    if signature:
        return signature
    baseline_object = mapping_value(payload.get("baseline_object"))
    return mapping_value(baseline_object.get("function_signature"))


def _function_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("function_name"))
        or optional_text(_function_signature(payload=operation.current).get("name"))
        or _function_name_from_semantic_key(operation.semantic_key)
    )


def _function_name_from_semantic_key(semantic_key: str) -> str | None:
    raw_name = semantic_key.rsplit("/", maxsplit=1)[-1].rsplit(".", maxsplit=1)[-1]
    if not raw_name or ":" in raw_name:
        return None
    return raw_name


def _owner_key(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("owner_key"))
        or optional_text(operation.current.get("owner_semantic_key"))
        or optional_text(_function_signature(payload=operation.current).get("owner_key"))
        or _owner_key_from_semantic_key(operation.semantic_key)
    )


def _owner_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    owner_key = _owner_key(operation=operation)
    if owner_key is None:
        return None
    return owner_key.rsplit(".", maxsplit=1)[-1]


def _owner_key_from_semantic_key(semantic_key: str) -> str | None:
    node_marker = "/node:"
    if node_marker not in semantic_key:
        return None
    node_key = semantic_key.split(node_marker, maxsplit=1)[-1]
    return node_key.rsplit(".", maxsplit=1)[0]


def _description_value(*, payload: Mapping[str, object]) -> object:
    if "description" not in payload:
        return _MISSING
    return payload["description"]


def _single_source_ref(source_refs: Sequence[str]) -> str | None:
    refs = _sorted_unique(source_refs)
    return refs[0] if len(refs) == 1 else None


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _sorted_unique(values: Iterable[str | object]) -> tuple[str, ...]:
    return tuple(sorted({text for item in values for text in tuple_text(item)}))


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_BLOCKED_REASON",
    "FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_READY_REASON",
    "FUNCTION_CONFIG_DESCRIPTION_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_BLOCKED_REASON",
    "FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_READY_REASON",
    "FUNCTION_CONFIG_SIGNATURE_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "FUNCTION_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON",
    "FUNCTION_MEMBERSHIP_SOURCE_PROJECTION_SKIPPED_REASON",
    "source_projection_feature_results_from_function_config_typed_operation",
]
