from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
    MetaProviderDeltaTypedOperationPlan,
)

_CONTRACT_VERSION = "aware.meta.provider-delta.language-target-impact-plan.v1"
_RENDER_ALL_POLICY = "render_all"
_FUNCTION_IMPL_POLICY = "function_impl_runtime_handlers_only"
_STRUCTURAL_POLICY = "structural_language_targets_only"
_SUPPORTED_UNION_POLICY = "supported_operation_target_union"
_RUNTIME_HANDLERS_SOURCE = "runtime_handlers"
_ANCHOR_OPERATION_FAMILY = "anchor"
_ANCHOR_PROVIDER_OPERATION_SUFFIX = ".anchor"
_FUNCTION_IMPL_SUBJECT_KIND = "function_impl"
_FUNCTION_SUBJECT_KIND = "function"
_FUNCTION_MEMBERSHIP_SUBJECT_KIND = "function_membership"
_RUNTIME_TARGET_GROUP = "runtime_handlers"
_STRUCTURAL_TARGET_GROUP = "structural"
_STRUCTURAL_SUBJECT_KINDS = frozenset(
    {
        "attribute",
        "attribute_membership",
        "class",
        "relationship",
    }
)


def provider_delta_language_target_impact_plan(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object] | None,
    target_payloads: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    targets = tuple(dict(target) for target in target_payloads)
    if provider_delta_typed_operation_plan is None:
        return _render_all_plan(
            reason="typed_operation_plan_missing",
            targets=targets,
            operations=(),
        )

    typed_plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    operations = _impactful_operations(operations=typed_plan.typed_operations)
    if typed_plan.status != "typed_operation_plan_ready":
        return _render_all_plan(
            reason="typed_operation_plan_not_ready",
            targets=targets,
            operations=operations,
            typed_operation_plan_status=typed_plan.status,
        )
    if not operations:
        return _render_all_plan(
            reason="typed_operations_missing",
            targets=targets,
            operations=operations,
            typed_operation_plan_status=typed_plan.status,
        )
    if any(operation.blocked for operation in operations):
        return _render_all_plan(
            reason="typed_operations_blocked",
            targets=targets,
            operations=operations,
            typed_operation_plan_status=typed_plan.status,
        )

    operation_target_groups = tuple(
        _operation_required_target_groups(operation) for operation in operations
    )
    if any(target_groups is None for target_groups in operation_target_groups):
        return _render_all_plan(
            reason="mixed_or_unsupported_operation_subjects",
            targets=targets,
            operations=operations,
            typed_operation_plan_status=typed_plan.status,
        )
    required_target_groups = frozenset(
        target_group
        for operation_groups in operation_target_groups
        if operation_groups is not None
        for target_group in operation_groups
    )

    if required_target_groups == frozenset({_RUNTIME_TARGET_GROUP}):
        return _select_plan(
            impact_policy=_FUNCTION_IMPL_POLICY,
            reason="function_impl_operations_target_runtime_handlers",
            targets=targets,
            operations=operations,
            typed_operation_plan_status=typed_plan.status,
            include_target=lambda target: _target_materialization_source(target)
            == _RUNTIME_HANDLERS_SOURCE,
            skip_reason="function_impl_operations_do_not_require_structural_targets",
            required_target_groups=required_target_groups,
        )
    if required_target_groups == frozenset({_STRUCTURAL_TARGET_GROUP}):
        return _select_plan(
            impact_policy=_STRUCTURAL_POLICY,
            reason="structural_operations_skip_runtime_handlers",
            targets=targets,
            operations=operations,
            typed_operation_plan_status=typed_plan.status,
            include_target=lambda target: _target_materialization_source(target)
            != _RUNTIME_HANDLERS_SOURCE,
            skip_reason="structural_operations_do_not_require_runtime_handlers",
            required_target_groups=required_target_groups,
        )
    return _select_plan(
        impact_policy=_SUPPORTED_UNION_POLICY,
        reason="supported_operation_target_union",
        targets=targets,
        operations=operations,
        typed_operation_plan_status=typed_plan.status,
        include_target=lambda target: _target_group(target) in required_target_groups,
        skip_reason="target_group_not_required_by_typed_operations",
        required_target_groups=required_target_groups,
    )


def _impactful_operations(
    *,
    operations: Sequence[MetaProviderDeltaTypedOperation],
) -> tuple[MetaProviderDeltaTypedOperation, ...]:
    return tuple(operation for operation in operations if not _is_anchor_operation(operation))


def _is_anchor_operation(operation: MetaProviderDeltaTypedOperation) -> bool:
    if operation.operation_family == _ANCHOR_OPERATION_FAMILY:
        return True
    return operation.provider_operation_type.endswith(
        _ANCHOR_PROVIDER_OPERATION_SUFFIX
    )


def _operation_required_target_groups(
    operation: MetaProviderDeltaTypedOperation,
) -> frozenset[str] | None:
    subject_kind = operation.ontology_subject_kind
    if subject_kind == _FUNCTION_IMPL_SUBJECT_KIND:
        return frozenset({_RUNTIME_TARGET_GROUP})
    if (
        subject_kind in _STRUCTURAL_SUBJECT_KINDS
        or subject_kind == _FUNCTION_MEMBERSHIP_SUBJECT_KIND
    ):
        return frozenset({_STRUCTURAL_TARGET_GROUP})
    if subject_kind == _FUNCTION_SUBJECT_KIND:
        if _function_update_is_description_only(operation):
            return frozenset({_STRUCTURAL_TARGET_GROUP})
        return frozenset({_RUNTIME_TARGET_GROUP, _STRUCTURAL_TARGET_GROUP})
    return None


def _function_update_is_description_only(
    operation: MetaProviderDeltaTypedOperation,
) -> bool:
    if operation.operation_family != "update":
        return False
    baseline_signature = _function_signature(operation.baseline)
    current_signature = _function_signature(operation.current)
    if baseline_signature is None or current_signature is None:
        return False
    baseline_without_description = _signature_without_description(
        baseline_signature
    )
    current_without_description = _signature_without_description(current_signature)
    if baseline_without_description != current_without_description:
        return False
    return _normalized_signature_value(baseline_signature.get("description")) != (
        _normalized_signature_value(current_signature.get("description"))
    )


def _function_signature(payload: Mapping[str, object]) -> Mapping[str, object] | None:
    direct = payload.get("function_signature")
    if isinstance(direct, Mapping):
        return direct
    object_payload = payload.get("object")
    if isinstance(object_payload, Mapping):
        nested = object_payload.get("function_signature")
        if isinstance(nested, Mapping):
            return nested
    return None


def _signature_without_description(
    signature: Mapping[str, object],
) -> dict[str, object]:
    return {
        str(key): _normalized_signature_value(value)
        for key, value in signature.items()
        if str(key) != "description"
    }


def _normalized_signature_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _normalized_signature_value(nested)
            for key, nested in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return tuple(_normalized_signature_value(item) for item in value)
    return value


def _select_plan(
    *,
    impact_policy: str,
    reason: str,
    targets: tuple[dict[str, object], ...],
    operations: Sequence[MetaProviderDeltaTypedOperation],
    typed_operation_plan_status: str | None,
    include_target: Callable[[Mapping[str, object]], bool],
    skip_reason: str,
    required_target_groups: frozenset[str],
) -> dict[str, object]:
    selected_targets: list[dict[str, object]] = []
    skipped_targets: list[dict[str, object]] = []
    for target in targets:
        if include_target(target):
            selected_targets.append(dict(target))
        else:
            skipped_targets.append({**dict(target), "skip_reason": skip_reason})
    if not selected_targets:
        return _render_all_plan(
            reason="target_impact_no_matching_targets",
            targets=targets,
            operations=operations,
            typed_operation_plan_status=typed_operation_plan_status,
        )
    return _plan_payload(
        impact_policy=impact_policy,
        reason=reason,
        render_all=False,
        targets=targets,
        selected_targets=tuple(selected_targets),
        skipped_targets=tuple(skipped_targets),
        operations=operations,
        typed_operation_plan_status=typed_operation_plan_status,
        required_target_groups=required_target_groups,
    )


def _render_all_plan(
    *,
    reason: str,
    targets: tuple[dict[str, object], ...],
    operations: Sequence[MetaProviderDeltaTypedOperation],
    typed_operation_plan_status: str | None = None,
) -> dict[str, object]:
    return _plan_payload(
        impact_policy=_RENDER_ALL_POLICY,
        reason=reason,
        render_all=True,
        targets=targets,
        selected_targets=targets,
        skipped_targets=(),
        operations=operations,
        typed_operation_plan_status=typed_operation_plan_status,
        required_target_groups=frozenset(),
    )


def _plan_payload(
    *,
    impact_policy: str,
    reason: str,
    render_all: bool,
    targets: tuple[dict[str, object], ...],
    selected_targets: tuple[dict[str, object], ...],
    skipped_targets: tuple[dict[str, object], ...],
    operations: Sequence[MetaProviderDeltaTypedOperation],
    typed_operation_plan_status: str | None,
    required_target_groups: frozenset[str],
) -> dict[str, object]:
    return {
        "receipt_kind": "meta_provider_delta_language_target_impact_plan",
        "contract_version": _CONTRACT_VERSION,
        "status": "language_target_impact_plan_ready",
        "reason": reason,
        "available": True,
        "blocked": False,
        "impact_policy": impact_policy,
        "render_all": render_all,
        "typed_operation_plan_status": typed_operation_plan_status,
        "required_target_groups": tuple(sorted(required_target_groups)),
        "target_count": len(targets),
        "selected_target_count": len(selected_targets),
        "skipped_target_count": len(skipped_targets),
        "selected_target_indexes": _target_indexes(targets=selected_targets),
        "skipped_target_indexes": _target_indexes(targets=skipped_targets),
        "selected_targets": tuple(dict(target) for target in selected_targets),
        "skipped_targets": tuple(dict(target) for target in skipped_targets),
        "operation_count": len(operations),
        "operation_type_counts": _operation_counts(
            operations=operations,
            field_name="provider_operation_type",
        ),
        "operation_family_counts": _operation_counts(
            operations=operations,
            field_name="operation_family",
        ),
        "ontology_subject_kind_counts": _operation_counts(
            operations=operations,
            field_name="ontology_subject_kind",
        ),
    }


def _operation_counts(
    *,
    operations: Sequence[MetaProviderDeltaTypedOperation],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for operation in operations:
        value = str(getattr(operation, field_name) or "")
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return counts


def _target_indexes(
    *,
    targets: Sequence[Mapping[str, object]],
) -> tuple[int, ...]:
    indexes: list[int] = []
    for target in targets:
        value = target.get("target_index")
        if isinstance(value, int):
            indexes.append(value)
    return tuple(indexes)


def _target_materialization_source(target: Mapping[str, object]) -> str:
    return str(target.get("materialization_source") or "")


def _target_group(target: Mapping[str, object]) -> str:
    if _target_materialization_source(target) == _RUNTIME_HANDLERS_SOURCE:
        return _RUNTIME_TARGET_GROUP
    return _STRUCTURAL_TARGET_GROUP


__all__ = ["provider_delta_language_target_impact_plan"]
