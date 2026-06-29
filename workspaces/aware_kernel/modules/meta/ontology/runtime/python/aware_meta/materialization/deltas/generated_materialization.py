from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from aware_meta.class_.config.deltas.operation_normalization import (
    coalesced_class_create_update_typed_operations,
)
from aware_meta.function.config.deltas.operation_normalization import (
    coalesced_function_signature_child_attribute_typed_operations,
)
from aware_meta.materialization.deltas.coercion import (
    mapping_value,
    optional_text,
)
from aware_meta.materialization.deltas.change_evidence_contracts import (
    MetaProviderDeltaSemanticChangeReport,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
    MetaProviderDeltaGeneratedMaterializationExpectation,
    MetaProviderDeltaGeneratedMaterializationFeatureResult,
)
from aware_meta.materialization.deltas.feature_registry import (
    generated_materialization_feature_results_from_typed_operation,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperationPlan,
)


META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-generated-materialization.v1"
)
META_GENERATED_MATERIALIZATION_PROVIDER_KEY = "aware_meta"


def provider_delta_generated_materialization_stage(
    *,
    package_payload: Mapping[str, object],
    manifest_path: Path,
    current_delta_fingerprint: str,
    provider_delta_semantic_change_report: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    code_package_delta: object | None = None,
) -> dict[str, object]:
    """Build provider-native generated-materialization evidence for Workspace."""

    report = MetaProviderDeltaSemanticChangeReport.from_payload(
        provider_delta_semantic_change_report
    )
    typed_plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    if not report.ready:
        return _provider_delta_generated_materialization_blocked_stage(
            reason="meta_generated_materialization_semantic_change_report_not_ready",
            current_delta_fingerprint=current_delta_fingerprint,
            report=report,
            typed_plan=typed_plan,
        )
    if typed_plan.status != "typed_operation_plan_ready":
        return _provider_delta_generated_materialization_blocked_stage(
            reason="meta_generated_materialization_typed_operation_plan_not_ready",
            current_delta_fingerprint=current_delta_fingerprint,
            report=report,
            typed_plan=typed_plan,
        )
    typed_operations = coalesced_function_signature_child_attribute_typed_operations(
        operations=coalesced_class_create_update_typed_operations(
            operations=typed_plan.typed_operations,
        ),
    )

    context = MetaProviderDeltaGeneratedMaterializationContext(
        package_name=_generated_materialization_package_name(
            package_payload=package_payload,
            code_package_delta=code_package_delta,
        ),
        package_root=_generated_materialization_package_root(
            package_payload=package_payload,
            manifest_path=manifest_path,
            code_package_delta=code_package_delta,
        ),
        sources_root=_generated_materialization_sources_root(
            code_package_delta=code_package_delta,
        ),
    )
    feature_results = tuple(
        result
        for operation in typed_operations
        for result in generated_materialization_feature_results_from_typed_operation(
            operation=operation,
            context=context,
        )
    )
    expectations = tuple(
        MetaProviderDeltaGeneratedMaterializationExpectation.from_feature_result(
            feature_result
        )
        for feature_result in feature_results
    )
    target_count = sum(item.target_count for item in feature_results)
    entry_count = sum(item.entry_count for item in feature_results)
    renderer_operation_count = sum(
        item.renderer_operation_count for item in feature_results
    )
    skipped_target_count = sum(item.skipped_target_count for item in feature_results)
    blocked_count = sum(1 for item in feature_results if item.blocked)
    skipped_count = sum(
        1
        for item in feature_results
        if item.status == "generated_materialization_skipped"
    )
    expected_generated_output_count = sum(1 for item in expectations if item.required)
    fulfilled_generated_output_count = sum(
        1 for item in expectations if item.required and item.fulfilled
    )
    missing_generated_output_count = sum(1 for item in expectations if item.missing)
    unsupported_generated_output_count = sum(
        1 for item in expectations if item.unsupported
    )
    deferred_generated_output_count = sum(1 for item in expectations if item.deferred)
    not_required_generated_output_count = sum(
        1 for item in expectations if item.not_required
    )
    blocking_missing_generated_output_count = sum(
        1 for item in expectations if item.required and item.missing
    )
    blocking_unsupported_generated_output_count = sum(
        1 for item in expectations if item.required and item.unsupported
    )
    blocking_deferred_generated_output_count = sum(
        1 for item in expectations if item.required and item.deferred
    )
    status, reason = _provider_delta_generated_materialization_status_and_reason(
        feature_result_count=len(feature_results),
        renderer_operation_count=renderer_operation_count,
        blocked_count=blocked_count,
        skipped_count=skipped_count,
        missing_generated_output_count=blocking_missing_generated_output_count,
        unsupported_generated_output_count=(
            blocking_unsupported_generated_output_count
        ),
        deferred_generated_output_count=blocking_deferred_generated_output_count,
    )
    return {
        "stage_kind": "meta_ocg_provider_delta_generated_materialization",
        "contract_version": (
            META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "available": True,
        "ready": status == "generated_materialization_ready",
        "blocked": status == "generated_materialization_blocked",
        "projected": renderer_operation_count > 0,
        "provider_key": META_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        "current_delta_fingerprint": current_delta_fingerprint,
        "change_count": report.semantic_world_change_count,
        "typed_operation_count": len(typed_operations),
        "feature_result_count": len(feature_results),
        "target_count": target_count,
        "entry_count": entry_count,
        "renderer_operation_count": renderer_operation_count,
        "skipped_target_count": skipped_target_count,
        "generated_materialization_expectation_count": len(expectations),
        "expected_generated_output_count": expected_generated_output_count,
        "fulfilled_generated_output_count": fulfilled_generated_output_count,
        "missing_generated_output_count": missing_generated_output_count,
        "unsupported_generated_output_count": unsupported_generated_output_count,
        "deferred_generated_output_count": deferred_generated_output_count,
        "not_required_generated_output_count": not_required_generated_output_count,
        "blocking_missing_generated_output_count": (
            blocking_missing_generated_output_count
        ),
        "blocking_unsupported_generated_output_count": (
            blocking_unsupported_generated_output_count
        ),
        "blocking_deferred_generated_output_count": (
            blocking_deferred_generated_output_count
        ),
        "blocked_feature_result_count": blocked_count,
        "skipped_feature_result_count": skipped_count,
        "diagnostics": _generated_materialization_feature_diagnostics(
            feature_results,
            expectations=expectations,
        ),
        "expectations": tuple(item.evidence_payload() for item in expectations),
        "delta_requests": tuple(
            item.delta_request.model_dump(mode="json")
            for item in feature_results
            if item.delta_request is not None
        ),
        "results": tuple(
            item.result.model_dump(mode="json")
            for item in feature_results
            if item.result is not None
        ),
        "feature_results": tuple(item.evidence_payload() for item in feature_results),
    }


def _provider_delta_generated_materialization_blocked_stage(
    *,
    reason: str,
    current_delta_fingerprint: str,
    report: MetaProviderDeltaSemanticChangeReport,
    typed_plan: MetaProviderDeltaTypedOperationPlan,
) -> dict[str, object]:
    return {
        "stage_kind": "meta_ocg_provider_delta_generated_materialization",
        "contract_version": (
            META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_CONTRACT_VERSION
        ),
        "status": "generated_materialization_blocked",
        "reason": reason,
        "available": True,
        "ready": False,
        "blocked": True,
        "projected": False,
        "provider_key": META_GENERATED_MATERIALIZATION_PROVIDER_KEY,
        "current_delta_fingerprint": current_delta_fingerprint,
        "change_count": report.semantic_world_change_count,
        "typed_operation_count": len(typed_plan.typed_operations),
        "feature_result_count": 0,
        "target_count": 0,
        "entry_count": 0,
        "renderer_operation_count": 0,
        "skipped_target_count": 0,
        "generated_materialization_expectation_count": 0,
        "expected_generated_output_count": 0,
        "fulfilled_generated_output_count": 0,
        "missing_generated_output_count": 0,
        "unsupported_generated_output_count": 0,
        "deferred_generated_output_count": 0,
        "not_required_generated_output_count": 0,
        "blocking_missing_generated_output_count": 0,
        "blocking_unsupported_generated_output_count": 0,
        "blocking_deferred_generated_output_count": 0,
        "blocked_feature_result_count": 0,
        "skipped_feature_result_count": 0,
        "diagnostics": (reason,),
        "expectations": (),
        "delta_requests": (),
        "results": (),
        "feature_results": (),
    }


def _provider_delta_generated_materialization_status_and_reason(
    *,
    feature_result_count: int,
    renderer_operation_count: int,
    blocked_count: int,
    skipped_count: int,
    missing_generated_output_count: int,
    unsupported_generated_output_count: int,
    deferred_generated_output_count: int,
) -> tuple[str, str]:
    if missing_generated_output_count:
        return (
            "generated_materialization_blocked",
            "meta_generated_materialization_expected_output_missing",
        )
    if unsupported_generated_output_count:
        return (
            "generated_materialization_blocked",
            "meta_generated_materialization_expectation_unsupported",
        )
    if deferred_generated_output_count:
        return (
            "generated_materialization_blocked",
            "meta_generated_materialization_expectation_deferred",
        )
    if renderer_operation_count > 0:
        return (
            "generated_materialization_ready",
            "meta_generated_materialization_renderer_operation_evidence_ready",
        )
    if blocked_count:
        return (
            "generated_materialization_blocked",
            "meta_generated_materialization_feature_blocked",
        )
    if feature_result_count == 0 or skipped_count == feature_result_count:
        return (
            "generated_materialization_not_required",
            "meta_generated_materialization_not_required",
        )
    return (
        "generated_materialization_not_required",
        "meta_generated_materialization_no_renderer_operations",
    )


def _generated_materialization_feature_diagnostics(
    feature_results: tuple[MetaProviderDeltaGeneratedMaterializationFeatureResult, ...],
    *,
    expectations: tuple[MetaProviderDeltaGeneratedMaterializationExpectation, ...],
) -> tuple[str, ...]:
    diagnostics = [
        diagnostic for item in feature_results for diagnostic in item.diagnostics
    ]
    diagnostics.extend(
        item.reason
        for item in expectations
        if item.missing or item.unsupported or item.deferred
    )
    return tuple(dict.fromkeys(diagnostics))


def _generated_materialization_package_name(
    *,
    package_payload: Mapping[str, object],
    code_package_delta: object | None,
) -> str | None:
    return _object_text_attribute(code_package_delta, "package_name") or optional_text(
        package_payload.get("package_name")
    )


def _generated_materialization_package_root(
    *,
    package_payload: Mapping[str, object],
    manifest_path: Path,
    code_package_delta: object | None,
) -> str | None:
    raw_package_root = _object_text_attribute(
        code_package_delta, "package_root"
    ) or optional_text(mapping_value(code_package_delta).get("package_root"))
    if raw_package_root is None:
        return manifest_path.expanduser().resolve().parent.as_posix()
    package_root_path = Path(raw_package_root).expanduser()
    if package_root_path.is_absolute():
        return package_root_path.resolve().as_posix()
    workspace_root = _workspace_root_for_package_manifest(
        fallback_package_root=package_root_path,
        package_payload=package_payload,
        manifest_path=manifest_path,
    )
    package_payload_root = (
        _relative_package_root(package_payload=package_payload) or package_root_path
    )
    if workspace_root is not None and _relative_path_has_prefix(
        path=package_root_path,
        prefix=package_payload_root,
    ):
        manifest_parent = manifest_path.expanduser().resolve().parent
        if package_root_path == package_payload_root and _path_has_suffix(
            path=manifest_parent,
            suffix=package_payload_root / "structure",
        ):
            return manifest_parent.as_posix()
        return (workspace_root / package_root_path).resolve().as_posix()
    return (
        (manifest_path.expanduser().resolve().parent / package_root_path)
        .resolve()
        .as_posix()
    )


def _workspace_root_for_package_manifest(
    *,
    fallback_package_root: Path | None = None,
    package_payload: Mapping[str, object],
    manifest_path: Path,
) -> Path | None:
    package_root = (
        _relative_package_root(package_payload=package_payload) or fallback_package_root
    )
    if package_root is None:
        return None
    manifest_parent = manifest_path.expanduser().resolve().parent
    for candidate_root in (package_root, package_root / "structure"):
        package_parts = candidate_root.parts
        if not package_parts:
            continue
        if manifest_parent.parts[-len(package_parts) :] != package_parts:
            continue
        workspace_parts = manifest_parent.parts[: -len(package_parts)]
        if not workspace_parts:
            continue
        return Path(*workspace_parts)
    return None


def _relative_package_root(
    *,
    package_payload: Mapping[str, object],
) -> Path | None:
    raw_package_root = optional_text(package_payload.get("package_root"))
    if raw_package_root is None:
        return None
    package_root = Path(raw_package_root).expanduser()
    if package_root.is_absolute():
        return None
    return package_root


def _relative_path_has_prefix(*, path: Path, prefix: Path) -> bool:
    prefix_parts = prefix.parts
    if not prefix_parts:
        return False
    return path.parts[: len(prefix_parts)] == prefix_parts


def _path_has_suffix(*, path: Path, suffix: Path) -> bool:
    suffix_parts = suffix.parts
    if not suffix_parts:
        return False
    return path.parts[-len(suffix_parts) :] == suffix_parts


def _generated_materialization_sources_root(
    *,
    code_package_delta: object | None,
) -> str | None:
    code_package_delta_payload = mapping_value(code_package_delta)
    raw_sources_root = (
        _object_text_attribute(code_package_delta, "sources_root")
        or optional_text(code_package_delta_payload.get("stage_sources_root"))
        or optional_text(code_package_delta_payload.get("workspace_sources_root"))
        or optional_text(code_package_delta_payload.get("sources_root"))
    )
    if raw_sources_root is None:
        return None
    if Path(raw_sources_root).parts[-1:] == ("aware",):
        return "aware"
    return raw_sources_root


def _object_text_attribute(value: object, attribute_name: str) -> str | None:
    if value is None or isinstance(value, Mapping):
        return None
    return optional_text(getattr(value, attribute_name, None))


__all__ = [
    "META_GENERATED_MATERIALIZATION_PROVIDER_KEY",
    "META_PROVIDER_DELTA_GENERATED_MATERIALIZATION_CONTRACT_VERSION",
    "provider_delta_generated_materialization_stage",
]
