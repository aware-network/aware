from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
    CodeGrammarAnchorBinding,
    CodeGrammarAnchorBindingDirection,
    CodeGrammarAnchorRenderReplacement,
    CodeGrammarAnchorRenderSemanticValue,
    CodeGrammarAnchorRenderSemanticValueKind,
    CodeGrammarAnchorRenderSource,
    CodeGrammarAnchorRenderTypeRefValue,
    CodeGraphAttributeSelector,
    CodeLanguage,
)
from aware_meta.materialization.deltas.coercion import (
    mapping_value,
    optional_text,
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
    "meta_source_projection_attribute_config_type_grammar_anchor_ready"
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
    "meta_source_projection_attribute_config_default_value_grammar_anchor_ready"
)
ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_BLOCKED_REASON = "meta_source_projection_attribute_config_default_value_requires_renderable_default_value"
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


def source_projection_feature_results_from_attribute_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    _ = context
    event_refs = (meta_provider_delta_world_change_event_key(operation=operation),)
    results: list[MetaProviderDeltaSourceProjectionFeatureResult] = []
    if _attribute_type_changed(operation=operation):
        bindings, sources, replacements = (
            _grammar_anchor_render_delta_from_attribute_type_operation(
                operation=operation,
            )
        )
        if replacements:
            results.append(
                MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                    feature_key=FEATURE_KEY,
                    operation=operation,
                    entries=(),
                    grammar_anchor_bindings=bindings,
                    grammar_anchor_sources=sources,
                    grammar_anchor_replacements=replacements,
                    reason=ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_READY_REASON,
                    required_evidence_fields=(
                        ATTRIBUTE_CONFIG_TYPE_SOURCE_PROJECTION_REQUIRED_FIELDS
                    ),
                ),
            )
        else:
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
    if _attribute_default_value_changed(operation=operation):
        bindings, sources, replacements = (
            _grammar_anchor_render_delta_from_attribute_default_value_operation(
                operation=operation,
            )
        )
        if replacements:
            results.append(
                MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                    feature_key=FEATURE_KEY,
                    operation=operation,
                    entries=(),
                    grammar_anchor_bindings=bindings,
                    grammar_anchor_sources=sources,
                    grammar_anchor_replacements=replacements,
                    reason=(
                        ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_READY_REASON
                    ),
                    required_evidence_fields=(
                        ATTRIBUTE_CONFIG_DEFAULT_VALUE_SOURCE_PROJECTION_REQUIRED_FIELDS
                    ),
                ),
            )
        else:
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
        semantic_value=_current_type_semantic_value(operation=operation),
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
        semantic_value=_current_default_value_semantic_value(operation=operation),
        render_policy_key="aware_meta.attribute_config.default_value",
        compatibility_segment_name="default_value",
    )


def _grammar_anchor_render_delta_from_attribute_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    field_key: str,
    anchor_field_path: str,
    value_domain: str,
    semantic_value: CodeGrammarAnchorRenderSemanticValue | None,
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
        or semantic_value is None
    ):
        return (), (), ()

    binding_key = f"aware_meta.attribute_config.{operation.operation_key}.{field_key}"
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
        language=CodeLanguage.aware,
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
        semantic_value=semantic_value,
        before_text_hash=None,
        event_ref=event_ref,
        semantic_key=operation.semantic_key,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.attribute_config_grammar_anchor_replacement",
                "operation_key": operation.operation_key,
                "field_key": field_key,
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
    current_value = _current_type_semantic_value(operation=operation)
    baseline_value = _type_semantic_value_from_signature(
        _attribute_signature(payload=operation.baseline)
    )
    if current_value is None:
        current_signature = _attribute_signature(payload=operation.current)
        current_descriptor = mapping_value(current_signature.get("type_descriptor"))
        return bool(current_descriptor)
    return current_value != baseline_value


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
    if _current_type_semantic_value(operation=operation) is None:
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
    if _current_default_value_semantic_value(operation=operation) is None:
        missing.append("renderable_default_value")
    return tuple(missing)


def _current_type_semantic_value(
    *, operation: MetaProviderDeltaTypedOperation
) -> CodeGrammarAnchorRenderSemanticValue | None:
    return _type_semantic_value_from_signature(
        _attribute_signature(payload=operation.current)
    )


def _type_semantic_value_from_signature(
    signature: Mapping[str, object],
) -> CodeGrammarAnchorRenderSemanticValue | None:
    descriptor = mapping_value(signature.get("type_descriptor"))
    if not descriptor:
        return None
    if optional_text(descriptor.get("kind")) != "primitive":
        return None
    primitive_type = optional_text(descriptor.get("primitive_base_type"))
    if primitive_type is None:
        return None
    return CodeGrammarAnchorRenderSemanticValue(
        kind=CodeGrammarAnchorRenderSemanticValueKind.type_ref,
        type_ref_value=CodeGrammarAnchorRenderTypeRefValue(
            type_name=primitive_type,
            nullable=signature.get("is_required") is False,
        ),
    )


def _current_default_value_semantic_value(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> CodeGrammarAnchorRenderSemanticValue | None:
    return _default_value_semantic_value_from_signature(
        _attribute_signature(payload=operation.current)
    )


def _default_value_payload(*, signature: Mapping[str, object]) -> object:
    if "default_value" not in signature:
        return _DEFAULT_VALUE_MISSING
    return signature["default_value"]


def _default_value_semantic_value_from_signature(
    signature: Mapping[str, object],
) -> CodeGrammarAnchorRenderSemanticValue | None:
    default_value = _default_value_payload(signature=signature)
    if default_value is _DEFAULT_VALUE_MISSING or default_value is None:
        return None
    if not isinstance(default_value, str):
        return None
    try:
        parsed_value = json.loads(default_value)
    except json.JSONDecodeError:
        return None
    if parsed_value is None:
        return CodeGrammarAnchorRenderSemanticValue(
            kind=CodeGrammarAnchorRenderSemanticValueKind.null,
        )
    if isinstance(parsed_value, bool):
        return CodeGrammarAnchorRenderSemanticValue(
            kind=CodeGrammarAnchorRenderSemanticValueKind.boolean,
            boolean_value=parsed_value,
        )
    if isinstance(parsed_value, int):
        return CodeGrammarAnchorRenderSemanticValue(
            kind=CodeGrammarAnchorRenderSemanticValueKind.integer,
            integer_value=parsed_value,
        )
    if isinstance(parsed_value, float):
        return CodeGrammarAnchorRenderSemanticValue(
            kind=CodeGrammarAnchorRenderSemanticValueKind.float,
            float_value=parsed_value,
        )
    if isinstance(parsed_value, str):
        return CodeGrammarAnchorRenderSemanticValue(
            kind=CodeGrammarAnchorRenderSemanticValueKind.string,
            string_value=parsed_value,
        )
    return CodeGrammarAnchorRenderSemanticValue(
        kind=CodeGrammarAnchorRenderSemanticValueKind.json,
        json_value=cast(Any, parsed_value),
    )


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
        or optional_text(
            _attribute_signature(payload=operation.current).get("owner_key")
        )
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
    refs = tuple(sorted({ref.strip() for ref in source_refs if ref.strip()}))
    return refs[0] if len(refs) == 1 else None


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
