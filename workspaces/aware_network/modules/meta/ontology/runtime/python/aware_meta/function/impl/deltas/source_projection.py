from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
from typing import Any, cast
from uuid import UUID

from aware_meta.materialization.deltas.code_dto import (
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionRef,
    CodeSegmentRef,
)
from aware_meta.materialization.deltas.coercion import optional_text, tuple_text
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaSourceProjectionContext,
    MetaProviderDeltaSourceProjectionFeatureResult,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_types import JsonObject


META_SOURCE_PROJECTION_PROVIDER_KEY = "aware_meta"
DEFAULT_SECTION_TYPE = "function"
DEFAULT_SEGMENT_NAME = "body"
DEFAULT_OPERATION_KIND = CodeSectionDeltaOperationKind.replace_segment
FUNCTION_IMPL_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "relative_path",
    "content_text",
    "segment_name",
    "section_identity",
)


def code_section_delta_entries_from_function_impl_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[CodeSectionDeltaEntry, ...]:
    return tuple(
        entry
        for result in source_projection_feature_results_from_function_impl_typed_operation(
            operation,
            context,
        )
        for entry in result.entries
    )


def source_projection_feature_results_from_function_impl_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    entry = code_section_delta_entry_from_function_impl_typed_operation(
        operation=operation,
        context=context,
    )
    if entry is not None:
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key="function_impl",
                operation=operation,
                entries=(entry,),
                reason="meta_source_projection_function_impl_section_delta_ready",
                required_evidence_fields=(
                    FUNCTION_IMPL_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    return (
        MetaProviderDeltaSourceProjectionFeatureResult.skipped(
            feature_key="function_impl",
            operation=operation,
            reason="meta_source_projection_function_impl_requires_explicit_section_evidence",
            event_refs=(_world_change_event_key(operation=operation),),
            required_evidence_fields=FUNCTION_IMPL_SOURCE_PROJECTION_REQUIRED_FIELDS,
            missing_evidence_fields=_missing_function_impl_source_projection_fields(
                operation=operation,
            ),
        ),
    )


def code_section_delta_entry_from_function_impl_typed_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> CodeSectionDeltaEntry | None:
    projection = _function_impl_source_projection_evidence(operation=operation)
    relative_path = optional_text(
        projection.get("relative_path")
    ) or _single_source_ref(operation.source_refs)
    content_text = optional_text(projection.get("content_text"))
    segment_name = optional_text(projection.get("segment_name"))
    section_identity = _section_identity_available(projection=projection)
    if (
        relative_path is None
        or content_text is None
        or segment_name is None
        or not section_identity
    ):
        return None
    operation_kind = _section_delta_operation_kind(projection.get("operation"))
    if operation_kind is not CodeSectionDeltaOperationKind.replace_segment:
        return None
    section_ref = CodeSectionRef(
        package_name=(
            optional_text(projection.get("package_name")) or context.package_name
        ),
        relative_path=relative_path,
        language=(optional_text(projection.get("language")) or context.target_language),
        section_type=(
            optional_text(projection.get("section_type")) or DEFAULT_SECTION_TYPE
        ),
        section_id=_uuid_or_none(projection.get("section_id")),
        qualname=optional_text(projection.get("qualname")),
        identity_hash=optional_text(projection.get("identity_hash")),
        semantic_key=operation.semantic_key,
        source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.function_impl_section_ref",
                "operation_key": operation.operation_key,
                "function_semantic_key": optional_text(
                    operation.current.get("function_semantic_key")
                ),
                "function_name": optional_text(operation.current.get("function_name")),
                "function_impl_key": optional_text(
                    operation.current.get("function_impl_key")
                ),
            }
        ),
    )
    segment_ref = CodeSegmentRef(
        segment_name=segment_name,
        before_segment_hash=optional_text(projection.get("before_segment_hash")),
        byte_start=_int_or_none(projection.get("byte_start")),
        byte_end=_int_or_none(projection.get("byte_end")),
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.function_impl_segment_ref",
                "function_impl_kind": optional_text(
                    operation.current.get("function_impl_kind")
                ),
            }
        ),
    )
    return CodeSectionDeltaEntry(
        operation=operation_kind,
        section_ref=section_ref,
        segment_ref=segment_ref,
        content_text=content_text,
        before_hash=optional_text(projection.get("before_hash")),
        after_hash=(
            optional_text(projection.get("after_hash")) or _sha256_digest(content_text)
        ),
        event_ref=(
            optional_text(projection.get("event_ref"))
            or _world_change_event_key(operation=operation)
        ),
        semantic_key=operation.semantic_key,
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
        metadata=_json_object(
            {
                "source": "aware_meta.provider_delta.function_impl_section_delta",
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "function_semantic_key": optional_text(
                    operation.current.get("function_semantic_key")
                ),
                "function_name": optional_text(operation.current.get("function_name")),
                "function_impl_key": optional_text(
                    operation.current.get("function_impl_key")
                ),
                "function_impl_kind": optional_text(
                    operation.current.get("function_impl_kind")
                ),
            }
        ),
    )


def _function_impl_source_projection_evidence(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> Mapping[str, object]:
    for candidate in (
        operation.current.get("source_projection"),
        operation.current.get("code_section_delta"),
        (
            operation.semantic_change_projection.get("source_projection")
            if operation.semantic_change_projection is not None
            else None
        ),
    ):
        if isinstance(candidate, Mapping):
            return {str(key): value for key, value in candidate.items()}
    return {}


def _section_delta_operation_kind(value: object) -> CodeSectionDeltaOperationKind:
    raw_value = optional_text(value)
    if raw_value is None:
        return DEFAULT_OPERATION_KIND
    try:
        return CodeSectionDeltaOperationKind(raw_value)
    except ValueError:
        return DEFAULT_OPERATION_KIND


def _section_identity_available(*, projection: Mapping[str, object]) -> bool:
    return any(
        optional_text(projection.get(key)) is not None
        for key in ("qualname", "identity_hash", "section_id")
    )


def _missing_function_impl_source_projection_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...]:
    projection = _function_impl_source_projection_evidence(operation=operation)
    missing: list[str] = []
    if (
        optional_text(projection.get("relative_path"))
        or _single_source_ref(operation.source_refs)
    ) is None:
        missing.append("relative_path")
    if optional_text(projection.get("content_text")) is None:
        missing.append("content_text")
    if optional_text(projection.get("segment_name")) is None:
        missing.append("segment_name")
    if not _section_identity_available(projection=projection):
        missing.append("section_identity")
    return tuple(missing)


def _single_source_ref(source_refs: Sequence[str]) -> str | None:
    refs = _sorted_unique(source_refs)
    return refs[0] if len(refs) == 1 else None


def _uuid_or_none(value: object) -> UUID | None:
    raw_value = optional_text(value)
    if raw_value is None:
        return None
    try:
        return UUID(raw_value)
    except ValueError:
        return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    raw_value = optional_text(value)
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except ValueError:
        return None


def _world_change_event_key(*, operation: MetaProviderDeltaTypedOperation) -> str:
    return (
        "aware_meta.provider_delta.world_change."
        f"{operation.ontology_subject_kind}.{operation.operation_family}"
    )


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _sorted_unique(values: Iterable[str | object]) -> tuple[str, ...]:
    return tuple(sorted({text for item in values for text in tuple_text(item)}))


def _json_object(payload: Mapping[str, object]) -> JsonObject:
    return JsonObject(cast(Any, dict(payload)))


__all__ = [
    "FUNCTION_IMPL_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "META_SOURCE_PROJECTION_PROVIDER_KEY",
    "code_section_delta_entries_from_function_impl_typed_operation",
    "code_section_delta_entry_from_function_impl_typed_operation",
    "source_projection_feature_results_from_function_impl_typed_operation",
]
