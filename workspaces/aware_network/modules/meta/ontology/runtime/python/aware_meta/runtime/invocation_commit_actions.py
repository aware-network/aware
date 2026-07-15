from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_meta_ontology.stable_ids import stable_class_instance_identity_id


OPG_CONSTRUCTOR_CALL_TARGET = "opg_constructor"


@dataclass(frozen=True)
class MetaInvocationCommitAction:
    operation_label: str
    call_target: str
    function_id: UUID
    object_id: UUID | None
    class_instance_identity_id: UUID | None


def resolve_invocation_class_instance_identity_id(
    *,
    object_instance_graph_identity_id: UUID,
    class_instance_id: UUID | None,
) -> UUID | None:
    if class_instance_id is None:
        return None
    return stable_class_instance_identity_id(
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_id=class_instance_id,
    )


def build_constructor_commit_action(
    *,
    operation_label: str | None,
    function_id: UUID,
    root_object_id: UUID | None,
    object_instance_graph_identity_id: UUID,
    root_class_instance_id: UUID | None,
) -> MetaInvocationCommitAction:
    return MetaInvocationCommitAction(
        operation_label=_commit_operation_label(
            operation_label=operation_label,
            function_id=function_id,
        ),
        call_target=OPG_CONSTRUCTOR_CALL_TARGET,
        function_id=function_id,
        object_id=root_object_id,
        class_instance_identity_id=resolve_invocation_class_instance_identity_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_id=root_class_instance_id,
        ),
    )


def build_instance_commit_action(
    *,
    operation_label: str | None,
    call_target: str,
    function_id: UUID,
    object_id: UUID | None,
    object_instance_graph_identity_id: UUID,
    source_class_instance_id: UUID | None,
) -> MetaInvocationCommitAction:
    normalized_call_target = call_target.strip()
    if not normalized_call_target:
        raise ValueError("commit action call_target must be non-empty")
    return MetaInvocationCommitAction(
        operation_label=_commit_operation_label(
            operation_label=operation_label,
            function_id=function_id,
        ),
        call_target=normalized_call_target,
        function_id=function_id,
        object_id=object_id,
        class_instance_identity_id=resolve_invocation_class_instance_identity_id(
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            class_instance_id=source_class_instance_id,
        ),
    )


def _commit_operation_label(*, operation_label: str | None, function_id: UUID) -> str:
    if operation_label is not None:
        normalized_label = operation_label.strip()
        if normalized_label:
            return normalized_label
    return f"function:{function_id}"


__all__ = [
    "MetaInvocationCommitAction",
    "OPG_CONSTRUCTOR_CALL_TARGET",
    "build_constructor_commit_action",
    "build_instance_commit_action",
    "resolve_invocation_class_instance_identity_id",
]
