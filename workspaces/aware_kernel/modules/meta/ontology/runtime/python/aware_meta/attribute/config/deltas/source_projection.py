from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
import json
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingDirection,
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSource,
    CodeGraphAttributeSelector,
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionRef,
    CodeSegmentRef,
)
from aware_meta.materialization.deltas.coercion import (
    mapping_value,
    optional_text,
    tuple_text,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaSourceProjectionContext,
    MetaProviderDeltaSourceProjectionFeatureResult,
    meta_provider_delta_world_change_event_key,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_types import JsonObject


FEATURE_KEY = "attribute_config"
ATTRIBUTE_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON = (
    "meta_source_projection_attribute_config_requires_renderer_segment_policy"
)
ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_attribute_config_type_segment_delta_ready"
)
ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_attribute_config_type_requires_renderable_type_descriptor"
)
ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "single_source_ref",
    "attribute_name",
    "owner_key",
    "renderable_primitive_type_descriptor",
)
ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_attribute_config_default_value_segment_delta_ready"
)
ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_attribute_config_default_value_requires_renderable_default_value"
)
ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "single_source_ref",
    "attribute_name",
    "owner_key",
    "renderable_default_value",
)
ATTRIBUTE_MEMBERSHIP_SOURCE_PROJECTION_SKIPPED_REASON = (
    "meta_source_projection_attribute_membership_requires_renderer_segment_policy"
)
_DEFAULT_VALUE_MISSING = object()
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


def source_projection_feature_results_from_attribute_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    event_refs = (
        meta_provider_delta_world_change_event_key(operation=operation),
    )
    results: list[MetaProviderDeltaSourceProjectionFeatureResult] = []
    entry = _code_section_delta_entry_from_attribute_type_operation(
        operation=operation,
        context=context,
    )
    if entry is not None:
        grammar_anchor_bindings, grammar_anchor_sources, grammar_anchor_replacements = (
            _grammar_anchor_render_delta_from_attribute_type_operation(
                operation=operation,
            )
        )
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key=FEATURE_KEY,
                operation=operation,
                entries=(entry,),
                grammar_anchor_bindings=grammar_anchor_bindings,
                grammar_anchor_sources=grammar_anchor_sources,
                grammar_anchor_replacements=grammar_anchor_replacements,
                reason=ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_READY_REASON,
                required_evidence_fields=(
                    ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    elif _attribute_type_changed(operation=operation):
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason=ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_BLOCKED_REASON,
                event_refs=event_refs,
                required_evidence_fields=(
                    ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
                missing_evidence_fields=_missing_type_projection_fields(
                    operation=operation,
                ),
            ),
        )
    entry = _code_section_delta_entry_from_attribute_default_value_operation(
        operation=operation,
        context=context,
    )
    if entry is not None:
        grammar_anchor_bindings, grammar_anchor_sources, grammar_anchor_replacements = (
            _grammar_anchor_render_delta_from_attribute_default_value_operation(
                operation=operation,
            )
        )
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key=FEATURE_KEY,
                operation=operation,
                entries=(entry,),
                grammar_anchor_bindings=grammar_anchor_bindings,
                grammar_anchor_sources=grammar_anchor_sources,
                grammar_anchor_replacements=grammar_anchor_replacements,
                reason=(
                    ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_READY_REASON
                ),
                required_evidence_fields=(
                    ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    elif _attribute_default_value_changed(operation=operation):
        results.append(
            MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason=(
                    ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_BLOCKED_REASON
                ),
                event_refs=event_refs,
                required_evidence_fields=(
                    ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
                missing_evidence_fields=(
                    _missing_default_value_projection_fields(operation=operation)
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
    if operation.ontology_subject_kind == "attribute_membership":
        return ATTRIBUTE_MEMBERSHIP_SOURCE_PROJECTION_SKIPPED_REASON
    return ATTRIBUTE_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON


def _code_section_delta_entry_from_attribute_type_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> CodeSectionDeltaEntry | None:
    if not _attribute_type_changed(operation=operation):
        return None
    relative_path = _single_source_ref(operation.source_refs)
    attribute_name = _attribute_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    content_text = _current_type_text(operation=operation)
    if (
        relative_path is None
        or attribute_name is None
        or owner_name is None
        or content_text is None
    ):
        return None
    baseline_text = _baseline_type_text(operation=operation)
    section_ref = CodeSectionRef(
        package_name=context.package_name,
        relative_path=relative_path,
        language=context.target_language,
        section_type="attribute",
        qualname=f"{owner_name}.{attribute_name}",
        semantic_key=operation.semantic_key,
        source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.attribute_type_section_ref",
                "operation_key": operation.operation_key,
                "attribute_name": attribute_name,
                "owner_key": _owner_key(operation=operation),
            }
        ),
    )
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.replace_segment,
        section_ref=section_ref,
        segment_ref=CodeSegmentRef(
            segment_name="type",
            before_segment_hash=(
                _sha256_digest(baseline_text)
                if baseline_text is not None
                else None
            ),
            metadata=_json_object(
                {
                    "source": "aware_meta.provider_delta.attribute_type_segment_ref",
                    "attribute_name": attribute_name,
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
                "source": "aware_meta.provider_delta.attribute_type_section_delta",
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "attribute_name": attribute_name,
                "owner_key": _owner_key(operation=operation),
            }
        ),
    )


def _code_section_delta_entry_from_attribute_default_value_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> CodeSectionDeltaEntry | None:
    if not _attribute_default_value_changed(operation=operation):
        return None
    relative_path = _single_source_ref(operation.source_refs)
    attribute_name = _attribute_name(operation=operation)
    owner_name = _owner_name(operation=operation)
    content_text = _current_default_value_text(operation=operation)
    if (
        relative_path is None
        or attribute_name is None
        or owner_name is None
        or content_text is None
    ):
        return None
    baseline_text = _baseline_default_value_text(operation=operation)
    section_ref = CodeSectionRef(
        package_name=context.package_name,
        relative_path=relative_path,
        language=context.target_language,
        section_type="attribute",
        qualname=f"{owner_name}.{attribute_name}",
        semantic_key=operation.semantic_key,
        source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "attribute_default_value_section_ref"
                ),
                "operation_key": operation.operation_key,
                "attribute_name": attribute_name,
                "owner_key": _owner_key(operation=operation),
            }
        ),
    )
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.replace_segment,
        section_ref=section_ref,
        segment_ref=CodeSegmentRef(
            segment_name="default_value",
            before_segment_hash=(
                _sha256_digest(baseline_text)
                if baseline_text is not None
                else None
            ),
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "attribute_default_value_segment_ref"
                    ),
                    "attribute_name": attribute_name,
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
                    "attribute_default_value_section_delta"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "attribute_name": attribute_name,
                "owner_key": _owner_key(operation=operation),
            }
        ),
    )


def _grammar_anchor_render_delta_from_attribute_type_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[
    tuple[CodeGrammarAnchorBinding, ...],
    tuple[CodeGrammarAnchorRenderSource, ...],
    tuple[CodeGrammarAnchorRenderReplacement, ...],
]:
    return _grammar_anchor_render_delta_from_attribute_operation(
        operation=operation,
        field_key="type",
        anchor_field_path="type",
        value_domain="aware_type_ref",
        replacement_text=_current_type_text(operation=operation),
        baseline_text=_baseline_type_text(operation=operation),
        render_policy_key="aware_meta.attribute_config.type",
        compatibility_segment_name="type",
    )


def _grammar_anchor_render_delta_from_attribute_default_value_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[
    tuple[CodeGrammarAnchorBinding, ...],
    tuple[CodeGrammarAnchorRenderSource, ...],
    tuple[CodeGrammarAnchorRenderReplacement, ...],
]:
    return _grammar_anchor_render_delta_from_attribute_operation(
        operation=operation,
        field_key="default_value",
        anchor_field_path="default",
        value_domain="aware_default_value",
        replacement_text=_current_default_value_text(operation=operation),
        baseline_text=_baseline_default_value_text(operation=operation),
        render_policy_key="aware_meta.attribute_config.default_value",
        compatibility_segment_name="default_value",
    )


def _grammar_anchor_render_delta_from_attribute_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    field_key: str,
    anchor_field_path: str,
    value_domain: str,
    replacement_text: str | None,
    baseline_text: str | None,
    render_policy_key: str,
    compatibility_segment_name: str,
) -> tuple[
    tuple[CodeGrammarAnchorBinding, ...],
    tuple[CodeGrammarAnchorRenderSource, ...],
    tuple[CodeGrammarAnchorRenderReplacement, ...],
]:
    relative_path = _single_source_ref(operation.source_refs)
    attribute_name = _attribute_name(operation=operation)
    owner_key = _owner_key(operation=operation)
    owner_name = _owner_name(operation=operation)
    if (
        relative_path is None
        or attribute_name is None
        or owner_name is None
        or replacement_text is None
    ):
        return (), (), ()

    binding_key = (
        f"aware_meta.attribute_config.{operation.operation_key}.{field_key}"
    )
    event_ref = meta_provider_delta_world_change_event_key(operation=operation)
    binding = CodeGrammarAnchorBinding(
        binding_key=binding_key,
        language="aware",
        grammar_profile_key="aware",
        provider_key="aware_meta",
        lane_key="meta_ocg_source_projection",
        grammar_rule_name="attr_def",
        anchor_field_path=anchor_field_path,
        graph_selector=CodeGraphAttributeSelector(
            provider_key="aware_meta",
            semantic_owner="aware_meta.ocg",
            class_fqn=owner_key,
            class_name=owner_name,
            attribute_name=attribute_name,
            attribute_path=f"{owner_name}.{attribute_name}.{field_key}",
            metadata=_json_object(
                {
                    "source": "aware_meta.provider_delta.attribute_config_graph_selector",
                    "operation_key": operation.operation_key,
                    "semantic_key": operation.semantic_key,
                    "ocg_field_key": field_key,
                    "owner_key": owner_key,
                }
            ),
        ),
        value_domain=value_domain,
        direction=CodeGrammarAnchorBindingDirection.graph_to_source,
        renderer_key="aware.grammar_anchor",
        render_policy_key=render_policy_key,
        compatibility_section_type="attribute",
        compatibility_segment_name=compatibility_segment_name,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.attribute_config_grammar_anchor_binding",
                "operation_key": operation.operation_key,
                "semantic_key": operation.semantic_key,
                "attribute_name": attribute_name,
                "owner_key": owner_key,
                "field_key": field_key,
            }
        ),
    )
    source = CodeGrammarAnchorRenderSource(
        source_key=relative_path,
        language="aware",
        relative_path=relative_path,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.attribute_config_grammar_anchor_source",
                "operation_key": operation.operation_key,
            }
        ),
    )
    replacement = CodeGrammarAnchorRenderReplacement(
        replacement_key=f"{binding_key}.replace",
        binding_key=binding_key,
        source_key=relative_path,
        replacement_text=replacement_text,
        before_text_hash=None,
        event_ref=event_ref,
        semantic_key=operation.semantic_key,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.attribute_config_grammar_anchor_replacement",
                "operation_key": operation.operation_key,
                "field_key": field_key,
                "semantic_baseline_text": baseline_text,
                "semantic_baseline_text_hash": (
                    _sha256_digest(baseline_text)
                    if baseline_text is not None
                    else None
                ),
                "source_context_before_text_hash": None,
            }
        ),
    )
    return (binding,), (source,), (replacement,)


def _attribute_type_changed(*, operation: MetaProviderDeltaTypedOperation) -> bool:
    if (
        operation.ontology_subject_kind != "attribute"
        or operation.operation_family != "update"
    ):
        return False
    current_text = _current_type_text(operation=operation)
    baseline_text = _baseline_type_text(operation=operation)
    if current_text is None:
        current_signature = _attribute_signature(payload=operation.current)
        current_descriptor = mapping_value(current_signature.get("type_descriptor"))
        return bool(current_descriptor)
    return current_text != baseline_text


def _missing_type_projection_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs) is None:
        missing.append("single_source_ref")
    if _attribute_name(operation=operation) is None:
        missing.append("attribute_name")
    if _owner_name(operation=operation) is None:
        missing.append("owner_key")
    if _current_type_text(operation=operation) is None:
        missing.append("renderable_primitive_type_descriptor")
    return tuple(missing)


def _attribute_default_value_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "attribute"
        or operation.operation_family != "update"
    ):
        return False
    current_default = _default_value_payload(
        signature=_attribute_signature(payload=operation.current)
    )
    baseline_default = _default_value_payload(
        signature=_attribute_signature(payload=operation.baseline)
    )
    if current_default is _DEFAULT_VALUE_MISSING:
        return False
    return current_default != baseline_default


def _missing_default_value_projection_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs) is None:
        missing.append("single_source_ref")
    if _attribute_name(operation=operation) is None:
        missing.append("attribute_name")
    if _owner_name(operation=operation) is None:
        missing.append("owner_key")
    if _current_default_value_text(operation=operation) is None:
        missing.append("renderable_default_value")
    return tuple(missing)


def _current_type_text(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return _type_text_from_signature(_attribute_signature(payload=operation.current))


def _baseline_type_text(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return _type_text_from_signature(_attribute_signature(payload=operation.baseline))


def _type_text_from_signature(signature: Mapping[str, object]) -> str | None:
    descriptor = mapping_value(signature.get("type_descriptor"))
    if not descriptor:
        return None
    if optional_text(descriptor.get("kind")) != "primitive":
        return None
    primitive_text = _primitive_type_text(descriptor.get("primitive_base_type"))
    if primitive_text is None:
        return None
    if signature.get("is_required") is False:
        return f"{primitive_text}?"
    return primitive_text


def _primitive_type_text(value: object) -> str | None:
    raw_value = optional_text(value)
    if raw_value is None:
        return None
    key = raw_value.rsplit(".", maxsplit=1)[-1].lower()
    return _PRIMITIVE_TYPE_TEXT.get(key)


def _current_default_value_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    return _default_value_text_from_signature(
        _attribute_signature(payload=operation.current)
    )


def _baseline_default_value_text(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    return _default_value_text_from_signature(
        _attribute_signature(payload=operation.baseline)
    )


def _default_value_payload(*, signature: Mapping[str, object]) -> object:
    if "default_value" not in signature:
        return _DEFAULT_VALUE_MISSING
    return signature["default_value"]


def _default_value_text_from_signature(
    signature: Mapping[str, object],
) -> str | None:
    default_value = _default_value_payload(signature=signature)
    if default_value is _DEFAULT_VALUE_MISSING or default_value is None:
        return None
    if not isinstance(default_value, str):
        return None
    descriptor = mapping_value(signature.get("type_descriptor"))
    if optional_text(descriptor.get("kind")) != "primitive":
        return None
    try:
        parsed_value = json.loads(default_value)
    except json.JSONDecodeError:
        return None
    return _primitive_default_value_text(
        parsed_value=parsed_value,
        primitive_base_type=descriptor.get("primitive_base_type"),
    )


def _primitive_default_value_text(
    *,
    parsed_value: object,
    primitive_base_type: object,
) -> str | None:
    raw_type = optional_text(primitive_base_type)
    if raw_type is None:
        return None
    primitive_key = raw_type.rsplit(".", maxsplit=1)[-1].lower()
    if parsed_value is None:
        return "null"
    if primitive_key in {"string", "uuid", "datetime", "date_time"}:
        if not isinstance(parsed_value, str):
            return None
        return json.dumps(parsed_value)
    if primitive_key in {"boolean", "bool"}:
        if not isinstance(parsed_value, bool):
            return None
        return "true" if parsed_value else "false"
    if primitive_key in {"integer", "int"}:
        if isinstance(parsed_value, bool) or not isinstance(parsed_value, int):
            return None
        return str(parsed_value)
    if primitive_key == "float":
        if isinstance(parsed_value, bool) or not isinstance(parsed_value, (int, float)):
            return None
        return str(parsed_value)
    if primitive_key in {"json", "any"}:
        return json.dumps(parsed_value, separators=(",", ":"), sort_keys=True)
    return None


def _attribute_signature(*, payload: Mapping[str, object]) -> Mapping[str, object]:
    signature = mapping_value(payload.get("attribute_signature"))
    if signature:
        return signature
    nested_payload = mapping_value(payload.get("payload"))
    signature = mapping_value(nested_payload.get("attribute_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("attribute_signature"))
    if signature:
        return signature
    baseline_object = mapping_value(payload.get("baseline_object"))
    return mapping_value(baseline_object.get("attribute_signature"))


def _attribute_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("attribute_name"))
        or optional_text(_attribute_signature(payload=operation.current).get("name"))
        or _attribute_name_from_semantic_key(operation.semantic_key)
    )


def _attribute_name_from_semantic_key(semantic_key: str) -> str | None:
    marker = "/attribute:"
    if marker not in semantic_key:
        return None
    raw_attribute = semantic_key.rsplit(marker, maxsplit=1)[-1]
    return raw_attribute.rsplit("/", maxsplit=1)[-1].rsplit(":", maxsplit=1)[-1]


def _owner_key(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    return (
        optional_text(operation.current.get("owner_key"))
        or optional_text(operation.current.get("owner_semantic_key"))
        or optional_text(_attribute_signature(payload=operation.current).get("owner_key"))
        or _owner_key_from_semantic_key(operation.semantic_key)
    )


def _owner_name(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    owner_key = _owner_key(operation=operation)
    if owner_key is None:
        return None
    return owner_key.rsplit(".", maxsplit=1)[-1]


def _owner_key_from_semantic_key(semantic_key: str) -> str | None:
    node_marker = "/node:"
    attribute_marker = "/attribute:"
    if node_marker not in semantic_key or attribute_marker not in semantic_key:
        return None
    return semantic_key.split(node_marker, maxsplit=1)[-1].split(
        attribute_marker,
        maxsplit=1,
    )[0]


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
    "ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_BLOCKED_REASON",
    "ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_READY_REASON",
    "ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "ATTRIBUTE_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON",
    "ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_BLOCKED_REASON",
    "ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_READY_REASON",
    "ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "ATTRIBUTE_MEMBERSHIP_SOURCE_PROJECTION_SKIPPED_REASON",
    "source_projection_feature_results_from_attribute_config_typed_operation",
]
