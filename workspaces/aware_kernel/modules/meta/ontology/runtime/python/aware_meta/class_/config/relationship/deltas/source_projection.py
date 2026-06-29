from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Any, cast

from aware_meta.materialization.deltas.code_dto import (
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


FEATURE_KEY = "relationship_config"
RELATIONSHIP_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON = (
    "meta_source_projection_relationship_config_requires_renderer_segment_policy"
)
RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_READY_REASON = (
    "meta_source_projection_relationship_config_load_policy_annotation_delta_ready"
)
RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_BLOCKED_REASON = (
    "meta_source_projection_relationship_config_load_policy_requires_renderable_annotation"
)
RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_REQUIRED_FIELDS = (
    "single_source_ref",
    "source_class_name",
    "relationship_key",
    "renderable_load_policy_args",
)
META_SOURCE_PROJECTION_PROVIDER_KEY = "aware_meta"


def source_projection_feature_results_from_relationship_config_typed_operation(
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> tuple[MetaProviderDeltaSourceProjectionFeatureResult, ...]:
    event_refs = (
        meta_provider_delta_world_change_event_key(operation=operation),
    )
    entry = _code_section_delta_entry_from_relationship_load_policy_operation(
        operation=operation,
        context=context,
    )
    if entry is not None:
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.from_projected(
                feature_key=FEATURE_KEY,
                operation=operation,
                entries=(entry,),
                reason=RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_READY_REASON,
                required_evidence_fields=(
                    RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
            ),
        )
    if _relationship_load_policy_changed(operation=operation):
        return (
            MetaProviderDeltaSourceProjectionFeatureResult.from_blocked(
                feature_key=FEATURE_KEY,
                operation=operation,
                reason=RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_BLOCKED_REASON,
                event_refs=event_refs,
                required_evidence_fields=(
                    RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_REQUIRED_FIELDS
                ),
                missing_evidence_fields=(
                    _missing_load_policy_projection_fields(operation=operation)
                ),
            ),
        )
    return (
        MetaProviderDeltaSourceProjectionFeatureResult.skipped(
            feature_key=FEATURE_KEY,
            operation=operation,
            reason=RELATIONSHIP_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON,
            event_refs=event_refs,
        ),
    )


def _code_section_delta_entry_from_relationship_load_policy_operation(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
) -> CodeSectionDeltaEntry | None:
    if not _relationship_load_policy_changed(operation=operation):
        return None
    relative_path = _single_source_ref(operation.source_refs)
    class_name = _source_class_name(operation=operation)
    relationship_key = _relationship_key(operation=operation)
    current_args = _current_load_policy_args(operation=operation)
    if (
        relative_path is None
        or class_name is None
        or relationship_key is None
        or current_args is None
    ):
        return None
    baseline_args = _baseline_load_policy_args(operation=operation)
    annotation_path = _annotation_path(
        relative_path=relative_path,
        class_name=class_name,
        relationship_key=relationship_key,
    )
    current_line = _annotation_line(
        annotation_path=annotation_path,
        load_args=current_args,
    )
    if baseline_args is None:
        return _insert_load_policy_annotation_entry(
            operation=operation,
            context=context,
            relative_path=relative_path,
            class_name=class_name,
            relationship_key=relationship_key,
            current_line=current_line,
        )
    return _replace_load_policy_annotation_args_entry(
        operation=operation,
        context=context,
        relative_path=relative_path,
        class_name=class_name,
        relationship_key=relationship_key,
        annotation_path=annotation_path,
        baseline_args=baseline_args,
        current_args=current_args,
    )


def _insert_load_policy_annotation_entry(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
    relative_path: str,
    class_name: str,
    relationship_key: str,
    current_line: str,
) -> CodeSectionDeltaEntry:
    content_text = f"\n{current_line}"
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.insert_after_section,
        section_ref=CodeSectionRef(
            package_name=context.package_name,
            relative_path=relative_path,
            language=context.target_language,
            section_type="class",
            qualname=class_name,
            semantic_key=operation.semantic_key,
            source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "relationship_load_policy_class_section_ref"
                    ),
                    "operation_key": operation.operation_key,
                    "class_name": class_name,
                    "relationship_key": relationship_key,
                }
            ),
        ),
        segment_ref=None,
        content_text=content_text,
        before_hash=None,
        after_hash=_sha256_digest(content_text),
        event_ref=meta_provider_delta_world_change_event_key(operation=operation),
        semantic_key=operation.semantic_key,
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "relationship_load_policy_annotation_insert_delta"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "class_name": class_name,
                "relationship_key": relationship_key,
            }
        ),
    )


def _replace_load_policy_annotation_args_entry(
    *,
    operation: MetaProviderDeltaTypedOperation,
    context: MetaProviderDeltaSourceProjectionContext,
    relative_path: str,
    class_name: str,
    relationship_key: str,
    annotation_path: str,
    baseline_args: tuple[str, ...],
    current_args: tuple[str, ...],
) -> CodeSectionDeltaEntry:
    baseline_text = " ".join(baseline_args)
    content_text = " ".join(current_args)
    baseline_line = _annotation_line(
        annotation_path=annotation_path,
        load_args=baseline_args,
    )
    return CodeSectionDeltaEntry(
        operation=CodeSectionDeltaOperationKind.replace_segment,
        section_ref=CodeSectionRef(
            package_name=context.package_name,
            relative_path=relative_path,
            language=context.target_language,
            section_type="annotation",
            qualname=f"ann:{baseline_line}",
            semantic_key=operation.semantic_key,
            source_refs=list(_sorted_unique((*operation.source_refs, relative_path))),
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "relationship_load_policy_annotation_section_ref"
                    ),
                    "operation_key": operation.operation_key,
                    "class_name": class_name,
                    "relationship_key": relationship_key,
                }
            ),
        ),
        segment_ref=CodeSegmentRef(
            segment_name="args",
            before_segment_hash=_sha256_digest(baseline_text),
            metadata=_json_object(
                {
                    "source": (
                        "aware_meta.provider_delta."
                        "relationship_load_policy_annotation_args_segment_ref"
                    ),
                    "relationship_key": relationship_key,
                }
            ),
        ),
        content_text=content_text,
        before_hash=None,
        after_hash=_sha256_digest(content_text),
        event_ref=meta_provider_delta_world_change_event_key(operation=operation),
        semantic_key=operation.semantic_key,
        provider_key=META_SOURCE_PROJECTION_PROVIDER_KEY,
        metadata=_json_object(
            {
                "source": (
                    "aware_meta.provider_delta."
                    "relationship_load_policy_annotation_args_delta"
                ),
                "operation_key": operation.operation_key,
                "operation_family": operation.operation_family,
                "provider_operation_type": operation.provider_operation_type,
                "ontology_subject_kind": operation.ontology_subject_kind,
                "class_name": class_name,
                "relationship_key": relationship_key,
            }
        ),
    )


def _relationship_load_policy_changed(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if (
        operation.ontology_subject_kind != "relationship"
        or operation.operation_family != "update"
    ):
        return False
    return _current_load_policy_args(operation=operation) != (
        _baseline_load_policy_args(operation=operation)
    )


def _missing_load_policy_projection_fields(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...]:
    missing: list[str] = []
    if _single_source_ref(operation.source_refs) is None:
        missing.append("single_source_ref")
    if _source_class_name(operation=operation) is None:
        missing.append("source_class_name")
    if _relationship_key(operation=operation) is None:
        missing.append("relationship_key")
    if _current_load_policy_args(operation=operation) is None:
        missing.append("renderable_load_policy_args")
    return tuple(missing)


def _current_load_policy_args(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...] | None:
    return _load_policy_args(
        payload=operation.current,
        signature=_relationship_signature(payload=operation.current),
    )


def _baseline_load_policy_args(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> tuple[str, ...] | None:
    return _load_policy_args(
        payload=operation.baseline,
        signature=_relationship_signature(payload=operation.baseline),
    )


def _load_policy_args(
    *,
    payload: Mapping[str, object],
    signature: Mapping[str, object],
) -> tuple[str, ...] | None:
    forward = _loading_strategy_text(
        payload.get("forward_loading_strategy")
        or signature.get("forward_loading_strategy")
    )
    reverse = _loading_strategy_text(
        payload.get("reverse_loading_strategy")
        or signature.get("reverse_loading_strategy")
    )
    args: list[str] = []
    if forward is not None:
        args.extend(("forward", forward))
    if reverse is not None:
        args.extend(("reverse", reverse))
    return tuple(args) if args else None


def _loading_strategy_text(value: object) -> str | None:
    text = optional_text(value)
    if text is None:
        return None
    normalized = text.rsplit(".", maxsplit=1)[-1].lower()
    if normalized in {"eager", "lazy"}:
        return normalized
    return None


def _relationship_signature(
    *,
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    signature = mapping_value(payload.get("relationship_signature"))
    if signature:
        return signature
    object_payload = mapping_value(payload.get("object"))
    signature = mapping_value(object_payload.get("relationship_signature"))
    if signature:
        return signature
    baseline_object = mapping_value(payload.get("baseline_object"))
    return mapping_value(baseline_object.get("relationship_signature"))


def _relationship_key(*, operation: MetaProviderDeltaTypedOperation) -> str | None:
    current_signature = _relationship_signature(payload=operation.current)
    baseline_signature = _relationship_signature(payload=operation.baseline)
    return (
        optional_text(operation.current.get("relationship_key"))
        or optional_text(current_signature.get("relationship_key"))
        or optional_text(operation.baseline.get("relationship_key"))
        or optional_text(baseline_signature.get("relationship_key"))
        or _relationship_key_from_semantic_key(operation.semantic_key)
    )


def _source_class_name(
    *,
    operation: MetaProviderDeltaTypedOperation,
) -> str | None:
    current_signature = _relationship_signature(payload=operation.current)
    baseline_signature = _relationship_signature(payload=operation.baseline)
    class_fqn = (
        optional_text(operation.current.get("source_class_fqn"))
        or optional_text(current_signature.get("source_class_fqn"))
        or optional_text(operation.baseline.get("source_class_fqn"))
        or optional_text(baseline_signature.get("source_class_fqn"))
    )
    if class_fqn is not None:
        return class_fqn.rsplit(".", maxsplit=1)[-1]
    owner_key = (
        optional_text(operation.current.get("owner_semantic_key"))
        or optional_text(operation.current.get("parent_semantic_key"))
        or _owner_key_from_semantic_key(operation.semantic_key)
    )
    if owner_key is None:
        return None
    return owner_key.rsplit(".", maxsplit=1)[-1]


def _owner_key_from_semantic_key(semantic_key: str) -> str | None:
    marker = "/node:"
    if marker not in semantic_key:
        return None
    node_key = semantic_key.split(marker, maxsplit=1)[-1]
    if ":" not in node_key:
        return node_key
    return node_key.split(":", maxsplit=1)[0]


def _relationship_key_from_semantic_key(semantic_key: str) -> str | None:
    owner_key = _owner_key_from_semantic_key(semantic_key)
    if owner_key is None:
        return None
    suffix = semantic_key.split(f"/node:{owner_key}", maxsplit=1)[-1]
    parts = [part for part in suffix.split(":") if part]
    return parts[0] if parts else None


def _annotation_path(
    *,
    relative_path: str,
    class_name: str,
    relationship_key: str,
) -> str:
    path = PurePosixPath(relative_path)
    namespace = ".".join(
        part for part in path.parent.parts if part not in {".", "aware"}
    )
    if namespace:
        return f"{namespace}.{class_name}::{relationship_key}"
    return f"{class_name}::{relationship_key}"


def _annotation_line(
    *,
    annotation_path: str,
    load_args: Sequence[str],
) -> str:
    return f"ann {annotation_path} load {' '.join(load_args)}"


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
    "RELATIONSHIP_CONFIG_SOURCE_PROJECTION_SKIPPED_REASON",
    "RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_BLOCKED_REASON",
    "RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_READY_REASON",
    "RELATIONSHIP_LOAD_POLICY_SOURCE_PROJECTION_REQUIRED_FIELDS",
    "source_projection_feature_results_from_relationship_config_typed_operation",
]
