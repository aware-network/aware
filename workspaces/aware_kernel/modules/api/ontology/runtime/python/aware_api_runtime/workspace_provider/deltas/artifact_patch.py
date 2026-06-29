from __future__ import annotations

import ast
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, cast


API_CLIENT_SERVICE_PROTOCOL_PATCH_CONTRACT_VERSION = (
    "aware.api.provider-delta-api-client-service-protocol-patch.v1"
)
GENERATED_ARTIFACT_FILE_PATCH_CONTRACT_VERSION = (
    "aware.api.generated-artifact-file-patch.v1"
)
API_LANGUAGE_ARTIFACT_DELTA_APPLY_CONTRACT_VERSION = (
    "aware.api.language-artifact-delta-apply.v1"
)
API_MATERIALIZATION_EVENT_ARTIFACT_DRIVER_CONTRACT_VERSION = (
    "aware.api.materialization-event-artifact-driver.v1"
)
API_RENDERER_FRAGMENT_EXECUTION_CONTRACT_VERSION = (
    "aware.api.renderer-fragment-execution.v1"
)
API_RENDER_INPUT_PRUNING_CONTRACT_VERSION = (
    "aware.api.render-input-pruning.v1"
)
API_SERVICE_PROTOCOL_SECTION_APPLY_CONTRACT_VERSION = (
    "aware.api.service-protocol-section-apply.v1"
)
API_SERVICE_PROTOCOL_SECTION_RENDER_EXECUTION_CONTRACT_VERSION = (
    "aware.api.service-protocol-section-render-execution.v1"
)
API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION = (
    "aware.api.service-protocol-section-text-manifest.v1"
)
API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME = (
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON"
)

_REQUIRED_BUNDLE_HEAD_REF_FIELDS = (
    "source_code_package_id",
    "source_object_instance_graph_commit_id",
    "semantic_package_id",
    "semantic_branch_id",
    "semantic_head_commit_id",
    "semantic_object_instance_graph_commit_id",
)
_SUPPORTED_PATCH_TARGETS = ("api_client", "service_protocol")
_PATCH_TARGET_ARTIFACT_ROLES = {
    "api_client": ("public_package_file",),
    "service_protocol": ("service_protocol_package_file",),
}
_PATCH_TARGET_ARTIFACT_ROOT_SEGMENTS = {
    "api_client": ("public_package", "python", "package"),
    "service_protocol": ("service_protocol", "python", "package"),
}


@dataclass(frozen=True, slots=True)
class ApiClientServiceProtocolPatchRenderResult:
    artifact_ownership_receipts: tuple[dict[str, object], ...]
    generated_artifact_file_patch: Mapping[str, object] | None = None


def api_delta_api_client_service_protocol_patch_receipt(
    *,
    manifest_path: Path,
    package_name: str,
    current_delta_fingerprint: str,
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    operation_execution: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    commit_ref_payload: Mapping[str, object],
    runtime_artifact_delta_plan: Mapping[str, object] | None = None,
    materialization_event_report: Mapping[str, object] | None = None,
    workspace_root: Path | None = None,
    renderer: Callable[..., object] | None = None,
) -> dict[str, object]:
    bundle_package = _mapping_payload(commit_ref_payload.get("bundle_package"))
    head_refs: dict[str, str] = {}
    for field_name in _REQUIRED_BUNDLE_HEAD_REF_FIELDS:
        field_value = _optional_text(bundle_package.get(field_name))
        if field_value is not None:
            head_refs[field_name] = field_value
    missing_head_ref_fields = tuple(
        field_name
        for field_name in _REQUIRED_BUNDLE_HEAD_REF_FIELDS
        if field_name not in head_refs
    )
    blockers = _api_client_service_protocol_patch_blockers(
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        operation_execution=operation_execution,
        package_source_execution=package_source_execution,
        missing_head_ref_fields=missing_head_ref_fields,
    )
    readiness_status = (
        "api_client_service_protocol_patch_ready"
        if not blockers
        else "api_client_service_protocol_patch_not_ready"
    )
    plan_payload = _mapping_payload(runtime_artifact_delta_plan)
    plan_blockers = (
        ()
        if blockers
        else _runtime_artifact_delta_plan_blockers(
            runtime_artifact_delta_plan=plan_payload,
            head_refs=head_refs,
            current_delta_fingerprint=current_delta_fingerprint,
        )
    )
    patch_targets = _runtime_artifact_delta_patch_targets(
        runtime_artifact_delta_plan=plan_payload,
    )
    event_report_payload = _mapping_payload(materialization_event_report)
    event_driver_payload = _materialization_event_artifact_driver_payload(
        materialization_event_report=event_report_payload,
        patch_targets=patch_targets,
    )
    event_driver_blockers = (
        ()
        if blockers or plan_blockers
        else _materialization_event_artifact_driver_blockers(
            materialization_event_driver=event_driver_payload,
        )
    )
    if blockers or plan_blockers or event_driver_blockers:
        return _api_client_service_protocol_patch_payload(
            status="api_client_service_protocol_patch_blocked",
            reason=(
                "api_provider_delta_api_client_service_protocol_patch_blocked"
                if blockers
                else (
                    "api_provider_delta_api_client_service_protocol_patch_requires_runtime_artifact_delta_plan"
                    if plan_blockers
                    else "api_provider_delta_api_client_service_protocol_patch_requires_materialization_events"
                )
            ),
            blocked=True,
            blockers=(*blockers, *plan_blockers, *event_driver_blockers),
            readiness_status=readiness_status,
            executor_ready=not plan_blockers and not blockers and not event_driver_blockers,
            would_patch=False,
            did_patch=False,
            manifest_path=manifest_path,
            package_name=package_name,
            current_delta_fingerprint=current_delta_fingerprint,
            head_refs=head_refs,
            missing_head_ref_fields=missing_head_ref_fields,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
            runtime_artifact_delta_plan=plan_payload,
            materialization_event_report=event_report_payload,
            materialization_event_artifact_driver=event_driver_payload,
            patch_targets=patch_targets,
            artifact_ownership_receipts=(),
        )

    patch_renderer = renderer or _render_api_client_service_protocol_patch
    try:
        render_result = patch_renderer(
            manifest_path=manifest_path,
            workspace_root=workspace_root,
            package_name=package_name,
            head_refs=head_refs,
            runtime_artifact_delta_plan=plan_payload,
            materialization_event_report=event_report_payload,
            patch_targets=patch_targets,
        )
    except Exception as exc:
        return _api_client_service_protocol_patch_payload(
            status="api_client_service_protocol_patch_failed",
            reason="api_provider_delta_api_client_service_protocol_patch_failed",
            blocked=True,
            blockers=(f"renderer_failed:{type(exc).__name__}: {exc}",),
            readiness_status=readiness_status,
            executor_ready=True,
            would_patch=True,
            did_patch=False,
            manifest_path=manifest_path,
            package_name=package_name,
            current_delta_fingerprint=current_delta_fingerprint,
            head_refs=head_refs,
            missing_head_ref_fields=missing_head_ref_fields,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
            runtime_artifact_delta_plan=plan_payload,
            materialization_event_report=event_report_payload,
            materialization_event_artifact_driver=event_driver_payload,
            patch_targets=patch_targets,
            artifact_ownership_receipts=(),
        )
    artifact_ownership_receipts, generated_artifact_file_patch = (
        _normalize_patch_renderer_result(render_result=render_result)
    )
    artifact_ownership_receipts = _filter_artifact_ownership_receipts_for_targets(
        artifact_ownership_receipts=artifact_ownership_receipts,
        patch_targets=patch_targets,
    )
    if not artifact_ownership_receipts:
        if _generated_artifact_file_patch_covers_targets(
            generated_artifact_file_patch=generated_artifact_file_patch,
            patch_targets=patch_targets,
        ):
            file_patch_status = _optional_text(
                _mapping_payload(generated_artifact_file_patch).get("status")
            )
            return _api_client_service_protocol_patch_payload(
                status=(
                    "api_client_service_protocol_patch_noop"
                    if file_patch_status == "generated_artifact_file_patch_noop"
                    else "api_client_service_protocol_patch_applied"
                ),
                reason=(
                    "api_provider_delta_api_client_service_protocol_patch_noop"
                    if file_patch_status == "generated_artifact_file_patch_noop"
                    else "api_provider_delta_api_client_service_protocol_patch_applied"
                ),
                blocked=False,
                blockers=(),
                readiness_status=readiness_status,
                executor_ready=True,
                would_patch=True,
                did_patch=True,
                manifest_path=manifest_path,
                package_name=package_name,
                current_delta_fingerprint=current_delta_fingerprint,
                head_refs=head_refs,
                missing_head_ref_fields=missing_head_ref_fields,
                provider_delta_head_move_plan=provider_delta_head_move_plan,
                provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
                operation_execution=operation_execution,
                package_source_execution=package_source_execution,
                runtime_artifact_delta_plan=plan_payload,
                materialization_event_report=event_report_payload,
                materialization_event_artifact_driver=event_driver_payload,
                patch_targets=patch_targets,
                artifact_ownership_receipts=(),
                generated_artifact_file_patch=generated_artifact_file_patch,
            )
        return _api_client_service_protocol_patch_payload(
            status="api_client_service_protocol_patch_blocked",
            reason="api_provider_delta_api_client_service_protocol_patch_missing_artifact_receipts",
            blocked=True,
            blockers=("artifact_ownership_receipts_missing",),
            readiness_status=readiness_status,
            executor_ready=True,
            would_patch=True,
            did_patch=False,
            manifest_path=manifest_path,
            package_name=package_name,
            current_delta_fingerprint=current_delta_fingerprint,
            head_refs=head_refs,
            missing_head_ref_fields=missing_head_ref_fields,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
            runtime_artifact_delta_plan=plan_payload,
            materialization_event_report=event_report_payload,
            materialization_event_artifact_driver=event_driver_payload,
            patch_targets=patch_targets,
            artifact_ownership_receipts=(),
            generated_artifact_file_patch=generated_artifact_file_patch,
        )
    missing_target_receipt_blockers = _missing_target_artifact_receipt_blockers(
        artifact_ownership_receipts=artifact_ownership_receipts,
        patch_targets=patch_targets,
    )
    if missing_target_receipt_blockers and not _generated_artifact_file_patch_covers_targets(
        generated_artifact_file_patch=generated_artifact_file_patch,
        patch_targets=patch_targets,
    ):
        return _api_client_service_protocol_patch_payload(
            status="api_client_service_protocol_patch_blocked",
            reason="api_provider_delta_api_client_service_protocol_patch_missing_target_artifact_receipts",
            blocked=True,
            blockers=missing_target_receipt_blockers,
            readiness_status=readiness_status,
            executor_ready=True,
            would_patch=True,
            did_patch=False,
            manifest_path=manifest_path,
            package_name=package_name,
            current_delta_fingerprint=current_delta_fingerprint,
            head_refs=head_refs,
            missing_head_ref_fields=missing_head_ref_fields,
            provider_delta_head_move_plan=provider_delta_head_move_plan,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            operation_execution=operation_execution,
            package_source_execution=package_source_execution,
            runtime_artifact_delta_plan=plan_payload,
            materialization_event_report=event_report_payload,
            materialization_event_artifact_driver=event_driver_payload,
            patch_targets=patch_targets,
            artifact_ownership_receipts=artifact_ownership_receipts,
            generated_artifact_file_patch=generated_artifact_file_patch,
        )

    return _api_client_service_protocol_patch_payload(
        status="api_client_service_protocol_patch_applied",
        reason="api_provider_delta_api_client_service_protocol_patch_applied",
        blocked=False,
        blockers=(),
        readiness_status=readiness_status,
        executor_ready=True,
        would_patch=True,
        did_patch=True,
        manifest_path=manifest_path,
        package_name=package_name,
        current_delta_fingerprint=current_delta_fingerprint,
        head_refs=head_refs,
        missing_head_ref_fields=missing_head_ref_fields,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        operation_execution=operation_execution,
        package_source_execution=package_source_execution,
        runtime_artifact_delta_plan=plan_payload,
        materialization_event_report=event_report_payload,
        materialization_event_artifact_driver=event_driver_payload,
        patch_targets=patch_targets,
        artifact_ownership_receipts=artifact_ownership_receipts,
        generated_artifact_file_patch=generated_artifact_file_patch,
    )


def _api_client_service_protocol_patch_payload(
    *,
    status: str,
    reason: str,
    blocked: bool,
    blockers: tuple[str, ...],
    readiness_status: str,
    executor_ready: bool,
    would_patch: bool,
    did_patch: bool,
    manifest_path: Path,
    package_name: str,
    current_delta_fingerprint: str,
    head_refs: Mapping[str, str],
    missing_head_ref_fields: tuple[str, ...],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    operation_execution: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    runtime_artifact_delta_plan: Mapping[str, object],
    materialization_event_report: Mapping[str, object],
    materialization_event_artifact_driver: Mapping[str, object],
    patch_targets: tuple[str, ...],
    artifact_ownership_receipts: tuple[dict[str, object], ...],
    generated_artifact_file_patch: Mapping[str, object] | None = None,
) -> dict[str, object]:
    file_patch_payload = _generated_artifact_file_patch_payload(
        generated_artifact_file_patch=generated_artifact_file_patch,
        patch_targets=patch_targets,
        would_patch=would_patch,
        did_patch=did_patch,
    )
    renderer_pruning_payload = _generated_artifact_renderer_pruning_payload(
        generated_artifact_file_patch=file_patch_payload,
        patch_targets=patch_targets,
        did_patch=did_patch,
    )
    renderer_candidate_scope_payload = _mapping_payload(
        file_patch_payload.get("generated_artifact_renderer_candidate_scope")
    )
    renderer_fragment_execution_payload = _mapping_payload(
        file_patch_payload.get("generated_artifact_renderer_fragment_execution")
    )
    render_input_pruning_payload = _generated_artifact_render_input_pruning_payload(
        generated_artifact_file_patch=file_patch_payload,
        patch_targets=patch_targets,
        did_patch=did_patch,
    )
    language_artifact_delta_apply_payload = _language_artifact_delta_apply_payload(
        patch_targets=patch_targets,
        would_patch=would_patch,
        did_patch=did_patch,
        generated_artifact_file_patch=file_patch_payload,
        materialization_event_report=materialization_event_report,
        materialization_event_artifact_driver=materialization_event_artifact_driver,
        renderer_candidate_scope=renderer_candidate_scope_payload,
    )
    target_executions = _target_patch_executions(
        patch_targets=patch_targets,
        artifact_ownership_receipts=artifact_ownership_receipts,
        did_patch=did_patch,
        generated_artifact_file_patch=file_patch_payload,
    )
    return {
        "contract_version": API_CLIENT_SERVICE_PROTOCOL_PATCH_CONTRACT_VERSION,
        "receipt_kind": "api_provider_delta_api_client_service_protocol_patch",
        "provider_key": "aware_api",
        "semantic_owner": "aware_api.provider",
        "producer_key": "aware_api.api_client_service_protocol",
        "replacement_target": "aware-cli compile api",
        "patch_targets": patch_targets,
        "status": status,
        "reason": reason,
        "blocked": blocked,
        "blockers": blockers,
        "readiness_status": readiness_status,
        "executor_ready": executor_ready,
        "would_patch": would_patch,
        "did_patch": did_patch,
        "runtime_artifact_delta_plan": dict(runtime_artifact_delta_plan),
        "runtime_artifact_delta_plan_available": bool(runtime_artifact_delta_plan),
        "runtime_artifact_delta_plan_status": _optional_text(
            runtime_artifact_delta_plan.get("status")
        ),
        "materialization_event_report": dict(materialization_event_report),
        "materialization_event_report_available": bool(materialization_event_report),
        "materialization_event_report_status": _optional_text(
            materialization_event_report.get("status")
        ),
        "materialization_event_artifact_driver": dict(
            materialization_event_artifact_driver
        ),
        "materialization_event_artifact_driver_status": _optional_text(
            materialization_event_artifact_driver.get("status")
        ),
        "artifact_ownership_receipts": artifact_ownership_receipts,
        "artifact_ownership_receipt_count": len(artifact_ownership_receipts),
        "artifact_role_counts": _artifact_role_counts(
            artifact_ownership_receipts=artifact_ownership_receipts,
        ),
        "generated_artifact_file_patch": file_patch_payload,
        "generated_artifact_file_patch_status": _optional_text(
            file_patch_payload.get("status")
        ),
        "generated_artifact_renderer_pruning": renderer_pruning_payload,
        "generated_artifact_renderer_pruning_status": _optional_text(
            renderer_pruning_payload.get("status")
        ),
        "generated_artifact_renderer_candidate_scope": (
            renderer_candidate_scope_payload
        ),
        "generated_artifact_renderer_candidate_scope_status": _optional_text(
            renderer_candidate_scope_payload.get("status")
        ),
        "generated_artifact_renderer_fragment_execution": (
            renderer_fragment_execution_payload
        ),
        "generated_artifact_renderer_fragment_execution_status": _optional_text(
            renderer_fragment_execution_payload.get("status")
        ),
        "generated_artifact_render_input_pruning": render_input_pruning_payload,
        "generated_artifact_render_input_pruning_status": _optional_text(
            render_input_pruning_payload.get("status")
        ),
        "language_artifact_delta_apply": language_artifact_delta_apply_payload,
        "language_artifact_delta_apply_status": _optional_text(
            language_artifact_delta_apply_payload.get("status")
        ),
        "language_artifact_delta_apply_operation_count": _int_value(
            language_artifact_delta_apply_payload.get("operation_count")
        ),
        "language_artifact_delta_apply_event_driven": (
            language_artifact_delta_apply_payload.get("event_driven") is True
        ),
        "target_patch_executions": target_executions,
        "target_patch_status_counts": _target_patch_status_counts(
            target_patch_executions=target_executions,
        ),
        "manifest_path": manifest_path.as_posix(),
        "package_name": package_name,
        "current_delta_fingerprint": current_delta_fingerprint,
        "head_refs": head_refs,
        "missing_head_ref_fields": missing_head_ref_fields,
        "provider_delta_head_move_status": _optional_text(
            provider_delta_head_move_plan.get("status")
        ),
        "provider_delta_head_move_reason": _optional_text(
            provider_delta_head_move_plan.get("reason")
        ),
        "provider_delta_typed_operation_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "provider_delta_typed_operation_count": _int_value(
            provider_delta_typed_operation_plan.get("typed_operation_count")
        ),
        "operation_execution_status": _optional_text(
            operation_execution.get("status")
        ),
        "package_source_execution_status": _optional_text(
            package_source_execution.get("status")
        ),
        "source_update_strategy": _optional_text(
            package_source_execution.get("source_update_strategy")
        ),
        "source_delta_path_count": _int_value(
            package_source_execution.get("source_delta_path_count")
        ),
    }


def _api_client_service_protocol_patch_blockers(
    *,
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    operation_execution: Mapping[str, object],
    package_source_execution: Mapping[str, object],
    missing_head_ref_fields: tuple[str, ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if provider_delta_head_move_plan.get("status") != "head_move_plan_ready":
        blockers.append(
            "head_move_plan_not_ready:"
            f"{_optional_text(provider_delta_head_move_plan.get('status')) or 'unknown'}"
        )
    if provider_delta_typed_operation_plan.get("status") != "typed_operation_plan_ready":
        blockers.append(
            "typed_operation_plan_not_ready:"
            f"{_optional_text(provider_delta_typed_operation_plan.get('status')) or 'unknown'}"
        )
    if operation_execution.get("status") != "executed":
        blockers.append(
            "operation_execution_not_applied:"
            f"{_optional_text(operation_execution.get('status')) or 'unknown'}"
        )
    if package_source_execution.get("status") != "executed":
        blockers.append(
            "package_source_execution_not_applied:"
            f"{_optional_text(package_source_execution.get('status')) or 'unknown'}"
        )
    if package_source_execution.get("source_update_strategy") != "code_package_delta":
        blockers.append(
            "source_update_strategy_not_delta:"
            f"{_optional_text(package_source_execution.get('source_update_strategy')) or 'unknown'}"
        )
    for field_name in missing_head_ref_fields:
        blockers.append(f"head_ref_missing:{field_name}")
    return tuple(dict.fromkeys(blockers))


def _runtime_artifact_delta_plan_blockers(
    *,
    runtime_artifact_delta_plan: Mapping[str, object],
    head_refs: Mapping[str, str],
    current_delta_fingerprint: str,
) -> tuple[str, ...]:
    if not runtime_artifact_delta_plan:
        return ("runtime_artifact_delta_plan_missing",)

    blockers: list[str] = []
    status = _optional_text(runtime_artifact_delta_plan.get("status"))
    if status not in {
        "runtime_artifact_delta_plan_ready",
        "api_product_runtime_delta_plan_ready",
    }:
        blockers.append(f"runtime_artifact_delta_plan_not_ready:{status or 'unknown'}")
    if runtime_artifact_delta_plan.get("runtime_artifacts_current") is not True:
        blockers.append("runtime_artifacts_current_false")
    if runtime_artifact_delta_plan.get("allow_runtime_artifact_refresh") is not True:
        blockers.append("runtime_artifact_refresh_not_allowed")
    patch_targets = _runtime_artifact_delta_patch_targets(
        runtime_artifact_delta_plan=runtime_artifact_delta_plan,
    )
    if not patch_targets:
        blockers.append("patch_targets_missing")
    for target in patch_targets:
        if target not in _SUPPORTED_PATCH_TARGETS:
            blockers.append(f"patch_target_unsupported:{target}")

    plan_fingerprint = _optional_text(
        runtime_artifact_delta_plan.get("current_delta_fingerprint")
    )
    if plan_fingerprint is None:
        blockers.append("current_delta_fingerprint_missing")
    elif plan_fingerprint != current_delta_fingerprint:
        blockers.append("current_delta_fingerprint_mismatch")

    for field_name, head_value in head_refs.items():
        plan_value = _optional_text(runtime_artifact_delta_plan.get(field_name))
        if plan_value is None:
            blockers.append(f"runtime_artifact_delta_plan_ref_missing:{field_name}")
        elif plan_value != head_value:
            blockers.append(f"head_ref_mismatch:{field_name}")
    return tuple(dict.fromkeys(blockers))


def _render_api_client_service_protocol_patch(
    *,
    manifest_path: Path,
    workspace_root: Path | None,
    package_name: str,
    head_refs: Mapping[str, str],
    runtime_artifact_delta_plan: Mapping[str, object],
    materialization_event_report: Mapping[str, object] | None = None,
    patch_targets: tuple[str, ...],
) -> ApiClientServiceProtocolPatchRenderResult:
    from aware_api_runtime.build import (  # noqa: WPS433
        api_product_runtime_artifact_ownership_receipts,
    )
    from aware_api_runtime.compile import (  # noqa: WPS433
        refresh_api_workspace_from_runtime_artifacts,
    )

    before_runtime_package_dir = _runtime_package_dir_from_patch_inputs(
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        package_name=package_name,
    )
    fragment_candidate_file_scope = _runtime_artifact_fragment_candidate_file_scope(
        runtime_artifact_delta_plan=runtime_artifact_delta_plan,
        runtime_package_dir=before_runtime_package_dir,
        patch_targets=patch_targets,
    )
    event_candidate_file_scope = _materialization_event_candidate_file_scope(
        materialization_event_report=_mapping_payload(materialization_event_report),
        runtime_package_dir=before_runtime_package_dir,
        patch_targets=patch_targets,
    )
    generated_path_candidate_file_scope = (
        fragment_candidate_file_scope
        if fragment_candidate_file_scope.get("status")
        == "generated_path_candidate_file_scope_applied"
        else (
            event_candidate_file_scope
            if event_candidate_file_scope.get("status")
            == "generated_path_candidate_file_scope_applied"
            else _generated_path_candidate_file_scope(
                runtime_artifact_delta_plan=runtime_artifact_delta_plan,
                runtime_package_dir=before_runtime_package_dir,
                patch_targets=patch_targets,
            )
        )
    )
    candidate_file_keys = _candidate_file_keys_from_scope(
        generated_path_candidate_file_scope=generated_path_candidate_file_scope,
    )
    before_all_file_records = _snapshot_patch_target_artifact_files(
        runtime_package_dir=before_runtime_package_dir,
        workspace_root=workspace_root,
        patch_targets=patch_targets,
    )
    before_file_records = _snapshot_patch_target_artifact_files(
        runtime_package_dir=before_runtime_package_dir,
        workspace_root=workspace_root,
        patch_targets=patch_targets,
        candidate_file_keys=candidate_file_keys,
    )
    public_package_candidate_paths = _renderer_candidate_paths_from_scope(
        generated_path_candidate_file_scope=generated_path_candidate_file_scope,
        target="api_client",
    )
    service_protocol_candidate_paths = _renderer_candidate_paths_from_scope(
        generated_path_candidate_file_scope=generated_path_candidate_file_scope,
        target="service_protocol",
    )
    renderer_candidate_scope = _generated_artifact_renderer_candidate_scope_payload(
        generated_path_candidate_file_scope=generated_path_candidate_file_scope,
        before_all_file_records=before_all_file_records,
        candidate_file_keys=candidate_file_keys,
        patch_targets=patch_targets,
        public_package_candidate_paths=public_package_candidate_paths,
        service_protocol_candidate_paths=service_protocol_candidate_paths,
    )
    renderer_fragment_execution = _renderer_fragment_execution_payload(
        runtime_artifact_delta_plan=runtime_artifact_delta_plan,
        fragment_candidate_file_scope=fragment_candidate_file_scope,
        selected_candidate_file_scope=generated_path_candidate_file_scope,
        renderer_candidate_scope=renderer_candidate_scope,
        public_package_candidate_paths=public_package_candidate_paths,
        service_protocol_candidate_paths=service_protocol_candidate_paths,
    )
    render_input_pruning_plan = _render_input_pruning_plan_payload(
        selected_candidate_file_scope=generated_path_candidate_file_scope,
        renderer_candidate_scope=renderer_candidate_scope,
        public_package_candidate_paths=public_package_candidate_paths,
        service_protocol_candidate_paths=service_protocol_candidate_paths,
        patch_targets=patch_targets,
    )
    public_package_render_input_class_refs = (
        tuple(
            _tuple_text(
                render_input_pruning_plan.get(
                    "public_package_render_input_class_refs"
                )
            )
        )
        if render_input_pruning_plan.get("public_package_graph_input_pruned") is True
        else None
    )
    refresh_result = refresh_api_workspace_from_runtime_artifacts(
        toml_path=manifest_path,
        repo_root=workspace_root,
        refresh_public_package="api_client" in patch_targets
        and "service_protocol" not in patch_targets,
        refresh_service_protocol="service_protocol" in patch_targets,
        public_package_candidate_paths=public_package_candidate_paths,
        service_protocol_candidate_paths=service_protocol_candidate_paths,
        public_package_render_input_class_refs=public_package_render_input_class_refs,
    )
    runtime_package_dir = None
    if refresh_result.service_protocol_materialization is not None:
        runtime_package_dir = (
            refresh_result.service_protocol_materialization.runtime_package_dir
        )
    elif refresh_result.public_package_materialization is not None:
        runtime_package_dir = refresh_result.public_package_materialization.runtime_package_dir
    if runtime_package_dir is None:
        raise RuntimeError("API target runtime artifact refresh unavailable.")
    snapshot = refresh_result.snapshot
    receipts = api_product_runtime_artifact_ownership_receipts(
        package_name=package_name,
        workspace_root=snapshot.repo_root,
        runtime_package_dir=runtime_package_dir,
        source_code_package_id=cast(Any, head_refs.get("source_code_package_id")),
        source_object_instance_graph_commit_id=cast(
            Any,
            head_refs.get("source_object_instance_graph_commit_id"),
        ),
    )
    target_receipts = _filter_artifact_ownership_receipts_for_targets(
        artifact_ownership_receipts=receipts,
        patch_targets=patch_targets,
        candidate_file_keys=candidate_file_keys,
    )
    render_input_pruning = _render_input_pruning_execution_payload(
        render_input_pruning_plan=render_input_pruning_plan,
        refresh_result=refresh_result,
    )
    return _file_level_patch_render_result(
        runtime_package_dir=runtime_package_dir,
        workspace_root=snapshot.repo_root,
        patch_targets=patch_targets,
        artifact_ownership_receipts=target_receipts,
        before_file_records=before_file_records,
        generated_path_candidate_file_scope=generated_path_candidate_file_scope,
        renderer_candidate_scope=renderer_candidate_scope,
        renderer_fragment_execution=renderer_fragment_execution,
        render_input_pruning=render_input_pruning,
    )


def _runtime_artifact_delta_patch_targets(
    *,
    runtime_artifact_delta_plan: Mapping[str, object],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            target
            for target in _tuple_text(runtime_artifact_delta_plan.get("patch_targets"))
            if target
        )
    )


def _materialization_event_artifact_driver_payload(
    *,
    materialization_event_report: Mapping[str, object],
    patch_targets: tuple[str, ...],
) -> dict[str, object]:
    if not materialization_event_report:
        return {
            "contract_version": (
                API_MATERIALIZATION_EVENT_ARTIFACT_DRIVER_CONTRACT_VERSION
            ),
            "status": "materialization_event_artifact_driver_not_provided",
            "reason": "api_materialization_event_report_not_provided",
            "source": None,
            "required": False,
            "available": False,
            "blocked": False,
            "blockers": (),
            "event_count": 0,
            "generated_path_candidate_count": 0,
            "target_candidate_counts": {},
            "missing_patch_targets": (),
            "language_delta_driver_ready": False,
        }
    report_status = _optional_text(materialization_event_report.get("status"))
    language_delta_driver_ready = (
        materialization_event_report.get("language_delta_driver_ready") is True
    )
    events = _materialization_event_report_events(
        materialization_event_report=materialization_event_report
    )
    candidates = tuple(
        candidate
        for event in events
        for candidate in _tuple_mapping_payloads(
            event.get("generated_path_candidates")
        )
    )
    target_candidate_counts = _candidate_counts_by_target(
        candidates=candidates,
        patch_targets=patch_targets,
    )
    missing_patch_targets = tuple(
        target for target in patch_targets if target not in target_candidate_counts
    )
    blockers: list[str] = []
    if report_status != "api_materialization_event_report_ready":
        blockers.append(
            "materialization_event_report_not_ready:"
            f"{report_status or 'unknown'}"
        )
    if not language_delta_driver_ready:
        blockers.append("language_delta_driver_not_ready")
    for target in missing_patch_targets:
        blockers.append(f"materialization_event_target_missing:{target}")
    blocked = bool(blockers)
    return {
        "contract_version": API_MATERIALIZATION_EVENT_ARTIFACT_DRIVER_CONTRACT_VERSION,
        "status": (
            "materialization_event_artifact_driver_ready"
            if not blocked
            else "materialization_event_artifact_driver_blocked"
        ),
        "reason": (
            "api_materialization_events_drive_artifact_targets"
            if not blocked
            else "api_materialization_events_cannot_drive_artifact_targets"
        ),
        "source": "api_materialization_event_report",
        "required": True,
        "available": not blocked,
        "blocked": blocked,
        "blockers": tuple(blockers),
        "event_count": len(events),
        "generated_path_candidate_count": len(candidates),
        "target_candidate_counts": target_candidate_counts,
        "missing_patch_targets": missing_patch_targets,
        "language_delta_driver_ready": language_delta_driver_ready,
    }


def _materialization_event_artifact_driver_blockers(
    *,
    materialization_event_driver: Mapping[str, object],
) -> tuple[str, ...]:
    if materialization_event_driver.get("required") is not True:
        return ()
    if materialization_event_driver.get("status") == (
        "materialization_event_artifact_driver_ready"
    ):
        return ()
    blockers = _tuple_text(materialization_event_driver.get("blockers"))
    return blockers or ("materialization_event_artifact_driver_not_ready",)


def _filter_artifact_ownership_receipts_for_targets(
    *,
    artifact_ownership_receipts: tuple[dict[str, object], ...],
    patch_targets: tuple[str, ...],
    candidate_file_keys: frozenset[str] | None = None,
) -> tuple[dict[str, object], ...]:
    requested_roles = {
        role
        for target in patch_targets
        for role in _PATCH_TARGET_ARTIFACT_ROLES.get(target, ())
    }
    if not requested_roles:
        return ()
    filtered: list[dict[str, object]] = []
    for receipt in artifact_ownership_receipts:
        if _optional_text(receipt.get("artifact_role")) not in requested_roles:
            continue
        if candidate_file_keys is not None:
            file_key = _receipt_file_key(receipt=receipt)
            if file_key not in candidate_file_keys:
                continue
        filtered.append(receipt)
    return tuple(filtered)


def _normalize_patch_renderer_result(
    *,
    render_result: object,
) -> tuple[tuple[dict[str, object], ...], Mapping[str, object] | None]:
    if isinstance(render_result, ApiClientServiceProtocolPatchRenderResult):
        return (
            render_result.artifact_ownership_receipts,
            render_result.generated_artifact_file_patch,
        )
    if isinstance(render_result, tuple):
        return cast(tuple[dict[str, object], ...], render_result), None
    if isinstance(render_result, list):
        return tuple(cast(list[dict[str, object]], render_result)), None
    raise TypeError(
        "API provider-delta artifact patch renderer must return receipt tuple "
        "or ApiClientServiceProtocolPatchRenderResult"
    )


def _runtime_package_dir_from_patch_inputs(
    *,
    manifest_path: Path,
    workspace_root: Path | None,
    package_name: str,
) -> Path:
    if workspace_root is not None:
        repo_root = workspace_root
    else:
        try:
            from aware_api_runtime.workspace import APIWorkspace  # noqa: WPS433

            repo_root = APIWorkspace.from_toml(
                toml_path=manifest_path,
                repo_root=None,
            ).build_snapshot().repo_root
        except Exception:
            repo_root = manifest_path.parent
    return (repo_root / ".aware" / "api" / "runtime" / package_name).resolve()


def _generated_path_candidate_file_scope(
    *,
    runtime_artifact_delta_plan: Mapping[str, object],
    runtime_package_dir: Path,
    patch_targets: tuple[str, ...],
) -> dict[str, object]:
    candidate_plan = _mapping_payload(
        runtime_artifact_delta_plan.get("generated_path_candidate_plan")
    )
    candidate_plan_status = _optional_text(candidate_plan.get("status"))
    if candidate_plan.get("candidate_filter_ready") is not True:
        return _generated_path_candidate_file_scope_payload(
            status="generated_path_candidate_file_scope_not_available",
            reason="generated_path_candidate_plan_not_filter_ready",
            source="runtime_artifact_delta_plan",
            candidate_plan_status=candidate_plan_status,
            candidate_file_keys=(),
            candidate_runtime_package_relpaths=(),
            candidate_class_refs=(),
            target_candidate_class_refs={},
            target_candidate_render_section_refs={},
            target_candidate_file_counts={},
            missing_patch_targets=(),
        )

    candidate_file_keys: set[str] = set()
    candidate_runtime_package_relpaths: set[str] = set()
    candidate_class_refs: set[str] = set()
    target_candidate_class_refs: dict[str, set[str]] = {}
    target_candidate_render_section_refs: dict[str, dict[str, dict[str, object]]] = {}
    target_candidate_file_counts: dict[str, int] = {}
    requested_targets = set(patch_targets)
    for candidate in _tuple_mapping_payloads(candidate_plan.get("candidates")):
        target = _optional_text(candidate.get("target"))
        if target not in requested_targets:
            continue
        artifact_role = _optional_text(candidate.get("artifact_role"))
        if artifact_role not in _PATCH_TARGET_ARTIFACT_ROLES.get(target, ()):
            continue
        relpath = _optional_text(candidate.get("runtime_package_relpath"))
        if relpath is None:
            continue
        relpath_path = Path(relpath)
        if relpath_path.is_absolute():
            continue
        candidate_file_keys.add(
            (runtime_package_dir / relpath_path).resolve().as_posix()
        )
        candidate_runtime_package_relpaths.add(relpath_path.as_posix())
        target_candidate_file_counts[target] = (
            target_candidate_file_counts.get(target, 0) + 1
        )
        class_ref = _optional_text(candidate.get("class_ref"))
        if class_ref is not None:
            candidate_class_refs.add(class_ref)
            target_candidate_class_refs.setdefault(target, set()).add(class_ref)
        for section_ref in _tuple_mapping_payloads(candidate.get("render_section_refs")):
            section_key = _optional_text(section_ref.get("section_key"))
            if section_key is None:
                continue
            target_candidate_render_section_refs.setdefault(target, {})[
                section_key
            ] = dict(section_ref)

    missing_patch_targets = tuple(
        target
        for target in patch_targets
        if target not in target_candidate_file_counts
    )
    if not candidate_file_keys or missing_patch_targets:
        return _generated_path_candidate_file_scope_payload(
            status="generated_path_candidate_file_scope_incomplete",
            reason="generated_path_candidate_scope_missing_requested_target",
            source="runtime_artifact_delta_plan",
            candidate_plan_status=candidate_plan_status,
            candidate_file_keys=tuple(sorted(candidate_file_keys)),
            candidate_runtime_package_relpaths=tuple(
                sorted(candidate_runtime_package_relpaths)
            ),
            candidate_class_refs=tuple(sorted(candidate_class_refs, key=str.casefold)),
            target_candidate_class_refs={
                target: tuple(sorted(refs, key=str.casefold))
                for target, refs in target_candidate_class_refs.items()
            },
            target_candidate_render_section_refs={
                target: _sorted_render_section_refs(refs.values())
                for target, refs in target_candidate_render_section_refs.items()
            },
            target_candidate_file_counts=target_candidate_file_counts,
            missing_patch_targets=missing_patch_targets,
        )

    return _generated_path_candidate_file_scope_payload(
        status="generated_path_candidate_file_scope_applied",
        reason="api_provider_delta_generated_path_candidate_file_scope_applied",
        source="runtime_artifact_delta_plan",
        candidate_plan_status=candidate_plan_status,
        candidate_file_keys=tuple(sorted(candidate_file_keys)),
        candidate_runtime_package_relpaths=tuple(
            sorted(candidate_runtime_package_relpaths)
        ),
        candidate_class_refs=tuple(sorted(candidate_class_refs, key=str.casefold)),
        target_candidate_class_refs={
            target: tuple(sorted(refs, key=str.casefold))
            for target, refs in target_candidate_class_refs.items()
        },
        target_candidate_render_section_refs={
            target: _sorted_render_section_refs(refs.values())
            for target, refs in target_candidate_render_section_refs.items()
        },
        target_candidate_file_counts=target_candidate_file_counts,
        missing_patch_targets=(),
    )


def _materialization_event_candidate_file_scope(
    *,
    materialization_event_report: Mapping[str, object],
    runtime_package_dir: Path,
    patch_targets: tuple[str, ...],
) -> dict[str, object]:
    if not materialization_event_report:
        return _generated_path_candidate_file_scope_payload(
            status="generated_path_candidate_file_scope_not_available",
            reason="materialization_event_report_not_provided",
            source="api_materialization_event_report",
            candidate_plan_status=None,
            candidate_file_keys=(),
            candidate_runtime_package_relpaths=(),
            candidate_class_refs=(),
            target_candidate_class_refs={},
            target_candidate_render_section_refs={},
            target_candidate_file_counts={},
            missing_patch_targets=(),
        )
    report_status = _optional_text(materialization_event_report.get("status"))
    if report_status != "api_materialization_event_report_ready":
        return _generated_path_candidate_file_scope_payload(
            status="generated_path_candidate_file_scope_not_available",
            reason="materialization_event_report_not_ready",
            source="api_materialization_event_report",
            candidate_plan_status=report_status,
            candidate_file_keys=(),
            candidate_runtime_package_relpaths=(),
            candidate_class_refs=(),
            target_candidate_class_refs={},
            target_candidate_render_section_refs={},
            target_candidate_file_counts={},
            missing_patch_targets=(),
        )
    candidates = tuple(
        candidate
        for event in _materialization_event_report_events(
            materialization_event_report=materialization_event_report
        )
        for candidate in _tuple_mapping_payloads(
            event.get("generated_path_candidates")
        )
    )
    return _candidate_file_scope_from_candidates(
        candidates=candidates,
        runtime_package_dir=runtime_package_dir,
        patch_targets=patch_targets,
        candidate_plan_status=report_status,
        source="api_materialization_event_report",
    )


def _runtime_artifact_fragment_candidate_file_scope(
    *,
    runtime_artifact_delta_plan: Mapping[str, object],
    runtime_package_dir: Path,
    patch_targets: tuple[str, ...],
) -> dict[str, object]:
    fragment_plan = _mapping_payload(
        runtime_artifact_delta_plan.get("runtime_artifact_fragment_plan")
    )
    fragment_status = _optional_text(fragment_plan.get("status"))
    if (
        fragment_status != "api_runtime_artifact_fragment_plan_ready"
        or fragment_plan.get("fragment_ready") is not True
    ):
        return _generated_path_candidate_file_scope_payload(
            status="generated_path_candidate_file_scope_not_available",
            reason="runtime_artifact_fragment_plan_not_ready",
            source="api_runtime_artifact_fragment_plan",
            candidate_plan_status=fragment_status,
            candidate_file_keys=(),
            candidate_runtime_package_relpaths=(),
            candidate_class_refs=(),
            target_candidate_class_refs={},
            target_candidate_render_section_refs={},
            target_candidate_file_counts={},
            missing_patch_targets=(),
        )
    fragment_operations = tuple(
        operation
        for operation in _tuple_mapping_payloads(
            fragment_plan.get("fragment_operations")
        )
        if operation.get("fragment_ready") is True
    )
    candidates = tuple(
        candidate
        for operation in fragment_operations
        for candidate in _tuple_mapping_payloads(
            operation.get("generated_path_candidates")
        )
    )
    return _candidate_file_scope_from_candidates(
        candidates=candidates,
        runtime_package_dir=runtime_package_dir,
        patch_targets=patch_targets,
        candidate_plan_status=fragment_status,
        source="api_runtime_artifact_fragment_plan",
    )


def _candidate_file_scope_from_candidates(
    *,
    candidates: tuple[Mapping[str, object], ...],
    runtime_package_dir: Path,
    patch_targets: tuple[str, ...],
    candidate_plan_status: str | None,
    source: str,
) -> dict[str, object]:
    candidate_file_keys: set[str] = set()
    candidate_runtime_package_relpaths: set[str] = set()
    candidate_class_refs: set[str] = set()
    target_candidate_class_refs: dict[str, set[str]] = {}
    target_candidate_render_section_refs: dict[str, dict[str, dict[str, object]]] = {}
    target_candidate_file_counts: dict[str, int] = {}
    requested_targets = set(patch_targets)
    for candidate in candidates:
        target = _optional_text(candidate.get("target"))
        if target not in requested_targets:
            continue
        artifact_role = _optional_text(candidate.get("artifact_role"))
        if artifact_role not in _PATCH_TARGET_ARTIFACT_ROLES.get(target, ()):
            continue
        relpath = _optional_text(candidate.get("runtime_package_relpath"))
        if relpath is None:
            continue
        relpath_path = Path(relpath)
        if relpath_path.is_absolute():
            continue
        candidate_file_keys.add(
            (runtime_package_dir / relpath_path).resolve().as_posix()
        )
        candidate_runtime_package_relpaths.add(relpath_path.as_posix())
        target_candidate_file_counts[target] = (
            target_candidate_file_counts.get(target, 0) + 1
        )
        class_ref = _optional_text(candidate.get("class_ref"))
        if class_ref is not None:
            candidate_class_refs.add(class_ref)
            target_candidate_class_refs.setdefault(target, set()).add(class_ref)
        for section_ref in _tuple_mapping_payloads(candidate.get("render_section_refs")):
            section_key = _optional_text(section_ref.get("section_key"))
            if section_key is None:
                continue
            target_candidate_render_section_refs.setdefault(target, {})[
                section_key
            ] = dict(section_ref)

    missing_patch_targets = tuple(
        target
        for target in patch_targets
        if target not in target_candidate_file_counts
    )
    if not candidate_file_keys or missing_patch_targets:
        return _generated_path_candidate_file_scope_payload(
            status="generated_path_candidate_file_scope_incomplete",
            reason="generated_path_candidate_scope_missing_requested_target",
            source=source,
            candidate_plan_status=candidate_plan_status,
            candidate_file_keys=tuple(sorted(candidate_file_keys)),
            candidate_runtime_package_relpaths=tuple(
                sorted(candidate_runtime_package_relpaths)
            ),
            candidate_class_refs=tuple(sorted(candidate_class_refs, key=str.casefold)),
            target_candidate_class_refs={
                target: tuple(sorted(refs, key=str.casefold))
                for target, refs in target_candidate_class_refs.items()
            },
            target_candidate_render_section_refs={
                target: _sorted_render_section_refs(refs.values())
                for target, refs in target_candidate_render_section_refs.items()
            },
            target_candidate_file_counts=target_candidate_file_counts,
            missing_patch_targets=missing_patch_targets,
        )

    return _generated_path_candidate_file_scope_payload(
        status="generated_path_candidate_file_scope_applied",
        reason="api_provider_delta_generated_path_candidate_file_scope_applied",
        source=source,
        candidate_plan_status=candidate_plan_status,
        candidate_file_keys=tuple(sorted(candidate_file_keys)),
        candidate_runtime_package_relpaths=tuple(
            sorted(candidate_runtime_package_relpaths)
        ),
        candidate_class_refs=tuple(sorted(candidate_class_refs, key=str.casefold)),
        target_candidate_class_refs={
            target: tuple(sorted(refs, key=str.casefold))
            for target, refs in target_candidate_class_refs.items()
        },
        target_candidate_render_section_refs={
            target: _sorted_render_section_refs(refs.values())
            for target, refs in target_candidate_render_section_refs.items()
        },
        target_candidate_file_counts=target_candidate_file_counts,
        missing_patch_targets=(),
    )


def _sorted_render_section_refs(
    refs: object,
) -> tuple[dict[str, object], ...]:
    if isinstance(refs, Mapping):
        raw_refs = (refs,)
    elif isinstance(refs, (str, bytes)) or refs is None:
        raw_refs = ()
    elif isinstance(refs, Iterable):
        raw_refs = tuple(refs)
    else:
        raw_refs = ()
    return tuple(
        dict(ref)
        for ref in sorted(
            (ref for ref in raw_refs if isinstance(ref, Mapping) and ref.get("section_key")),
            key=lambda item: (
                _optional_text(item.get("runtime_package_relpath")) or "",
                _optional_text(item.get("section_key")) or "",
            ),
        )
    )


def _generated_path_candidate_file_scope_payload(
    *,
    status: str,
    reason: str,
    source: str,
    candidate_plan_status: str | None,
    candidate_file_keys: tuple[str, ...],
    candidate_runtime_package_relpaths: tuple[str, ...],
    candidate_class_refs: tuple[str, ...],
    target_candidate_class_refs: Mapping[str, tuple[str, ...]],
    target_candidate_render_section_refs: Mapping[
        str, tuple[Mapping[str, object], ...]
    ],
    target_candidate_file_counts: Mapping[str, int],
    missing_patch_targets: tuple[str, ...],
) -> dict[str, object]:
    candidate_render_section_refs = _sorted_render_section_refs(
        ref
        for refs in target_candidate_render_section_refs.values()
        for ref in refs
    )
    return {
        "contract_version": "aware.api.generated-path-candidate-file-scope.v1",
        "status": status,
        "reason": reason,
        "source": source,
        "candidate_plan_status": candidate_plan_status,
        "candidate_file_count": len(candidate_file_keys),
        "candidate_file_keys": candidate_file_keys,
        "candidate_runtime_package_relpaths": candidate_runtime_package_relpaths,
        "candidate_class_refs": candidate_class_refs,
        "candidate_class_ref_count": len(candidate_class_refs),
        "target_candidate_class_refs": {
            target: tuple(refs)
            for target, refs in target_candidate_class_refs.items()
        },
        "candidate_render_section_refs": candidate_render_section_refs,
        "candidate_render_section_ref_count": len(candidate_render_section_refs),
        "target_candidate_render_section_refs": {
            target: tuple(dict(ref) for ref in refs)
            for target, refs in target_candidate_render_section_refs.items()
        },
        "target_candidate_render_section_ref_counts": {
            target: len(refs)
            for target, refs in target_candidate_render_section_refs.items()
        },
        "target_candidate_file_counts": dict(target_candidate_file_counts),
        "missing_patch_targets": missing_patch_targets,
        "filter_applied": status == "generated_path_candidate_file_scope_applied",
    }


def _candidate_file_keys_from_scope(
    *,
    generated_path_candidate_file_scope: Mapping[str, object],
) -> frozenset[str] | None:
    if (
        generated_path_candidate_file_scope.get("status")
        != "generated_path_candidate_file_scope_applied"
    ):
        return None
    return frozenset(
        str(item)
        for item in _tuple_evidence(
            generated_path_candidate_file_scope.get("candidate_file_keys")
        )
        if _optional_text(item) is not None
    )


def _renderer_candidate_paths_from_scope(
    *,
    generated_path_candidate_file_scope: Mapping[str, object],
    target: str,
) -> tuple[Path, ...]:
    if (
        generated_path_candidate_file_scope.get("status")
        != "generated_path_candidate_file_scope_applied"
    ):
        return ()
    root_segments = _PATCH_TARGET_ARTIFACT_ROOT_SEGMENTS.get(target)
    if root_segments is None:
        return ()
    renderer_paths: list[Path] = []
    seen: set[str] = set()
    for relpath in _tuple_text(
        generated_path_candidate_file_scope.get(
            "candidate_runtime_package_relpaths"
        )
    ):
        parts = Path(relpath).parts
        if len(parts) <= len(root_segments):
            continue
        if tuple(parts[:len(root_segments)]) != root_segments:
            continue
        # Runtime package relpaths include the import root after
        # public_package/python/package or service_protocol/python/package.
        renderer_parts = parts[len(root_segments) + 1:]
        if not renderer_parts:
            continue
        renderer_path = Path(*renderer_parts)
        renderer_key = renderer_path.as_posix()
        if renderer_key in seen:
            continue
        seen.add(renderer_key)
        renderer_paths.append(renderer_path)
    return tuple(renderer_paths)


def _generated_artifact_renderer_candidate_scope_payload(
    *,
    generated_path_candidate_file_scope: Mapping[str, object],
    before_all_file_records: Mapping[str, Mapping[str, object]],
    candidate_file_keys: frozenset[str] | None,
    patch_targets: tuple[str, ...],
    public_package_candidate_paths: tuple[Path, ...],
    service_protocol_candidate_paths: tuple[Path, ...],
) -> dict[str, object]:
    file_scope_status = _optional_text(
        generated_path_candidate_file_scope.get("status")
    )
    filter_applied = file_scope_status == "generated_path_candidate_file_scope_applied"
    target_full_file_counts = {
        target: sum(
            1
            for record in before_all_file_records.values()
            if _optional_text(record.get("target")) == target
        )
        for target in patch_targets
    }
    full_target_file_count = sum(target_full_file_counts.values())
    candidate_file_count = len(candidate_file_keys or ())
    renderer_candidate_path_count = (
        len(public_package_candidate_paths) + len(service_protocol_candidate_paths)
    )
    service_protocol_render_section_refs = _target_candidate_render_section_refs_from_scope(
        candidate_file_scope=generated_path_candidate_file_scope,
        target="service_protocol",
    )
    return {
        "contract_version": "aware.api.generated-artifact-renderer-candidate-scope.v1",
        "status": (
            "generated_artifact_renderer_candidate_scope_applied"
            if filter_applied
            else "generated_artifact_renderer_candidate_scope_not_available"
        ),
        "reason": (
            "api_provider_delta_renderer_candidate_scope_applied"
            if filter_applied
            else "api_provider_delta_renderer_candidate_scope_requires_file_scope"
        ),
        "source_file_scope_source": _optional_text(
            generated_path_candidate_file_scope.get("source")
        ),
        "source_file_scope_status": file_scope_status,
        "filter_applied": filter_applied,
        "requested_patch_targets": patch_targets,
        "target_full_file_counts": target_full_file_counts,
        "full_target_file_count": full_target_file_count,
        "candidate_file_count": candidate_file_count,
        "candidate_runtime_package_relpaths": tuple(
            _tuple_text(
                generated_path_candidate_file_scope.get(
                    "candidate_runtime_package_relpaths"
                )
            )
        ),
        "public_package_candidate_paths": tuple(
            path.as_posix() for path in public_package_candidate_paths
        ),
        "service_protocol_candidate_paths": tuple(
            path.as_posix() for path in service_protocol_candidate_paths
        ),
        "service_protocol_render_section_refs": service_protocol_render_section_refs,
        "service_protocol_render_section_ref_count": len(
            service_protocol_render_section_refs
        ),
        "renderer_candidate_path_count": renderer_candidate_path_count,
        "estimated_renderer_file_invocation_pruned_count": (
            max(full_target_file_count - candidate_file_count, 0)
            if filter_applied
            else 0
        ),
    }


def _renderer_fragment_execution_payload(
    *,
    runtime_artifact_delta_plan: Mapping[str, object],
    fragment_candidate_file_scope: Mapping[str, object],
    selected_candidate_file_scope: Mapping[str, object],
    renderer_candidate_scope: Mapping[str, object],
    public_package_candidate_paths: tuple[Path, ...],
    service_protocol_candidate_paths: tuple[Path, ...],
) -> dict[str, object]:
    fragment_plan = _mapping_payload(
        runtime_artifact_delta_plan.get("runtime_artifact_fragment_plan")
    )
    fragment_scope_status = _optional_text(fragment_candidate_file_scope.get("status"))
    selected_scope_source = _optional_text(selected_candidate_file_scope.get("source"))
    renderer_scope_status = _optional_text(renderer_candidate_scope.get("status"))
    applied = (
        selected_scope_source == "api_runtime_artifact_fragment_plan"
        and renderer_scope_status == "generated_artifact_renderer_candidate_scope_applied"
    )
    service_protocol_render_section_refs = _target_candidate_render_section_refs_from_scope(
        candidate_file_scope=selected_candidate_file_scope,
        target="service_protocol",
    )
    return {
        "contract_version": API_RENDERER_FRAGMENT_EXECUTION_CONTRACT_VERSION,
        "execution_kind": "api_renderer_fragment_execution",
        "status": (
            "api_renderer_fragment_execution_applied"
            if applied
            else "api_renderer_fragment_execution_not_applied"
        ),
        "reason": (
            "api_renderer_fragment_execution_used_runtime_artifact_fragments"
            if applied
            else "api_renderer_fragment_execution_requires_fragment_file_scope"
        ),
        "source": "api_runtime_artifact_fragment_plan",
        "selected_file_scope_source": selected_scope_source,
        "fragment_file_scope_status": fragment_scope_status,
        "renderer_candidate_scope_status": renderer_scope_status,
        "fragment_plan_status": _optional_text(fragment_plan.get("status")),
        "fragment_ready": fragment_plan.get("fragment_ready") is True,
        "fragment_operation_count": _int_value(
            fragment_plan.get("fragment_operation_count")
        ),
        "filter_applied": applied,
        "candidate_file_count": _int_value(
            selected_candidate_file_scope.get("candidate_file_count")
        ),
        "renderer_candidate_path_count": (
            len(public_package_candidate_paths) + len(service_protocol_candidate_paths)
        ),
        "public_package_candidate_paths": tuple(
            path.as_posix() for path in public_package_candidate_paths
        ),
        "service_protocol_candidate_paths": tuple(
            path.as_posix() for path in service_protocol_candidate_paths
        ),
        "service_protocol_render_section_ref_count": len(
            service_protocol_render_section_refs
        ),
        "service_protocol_section_render_execution_wired": False,
        "event_dispatch_wired": False,
        "would_dispatch": False,
        "did_dispatch": False,
    }


def _render_input_pruning_plan_payload(
    *,
    selected_candidate_file_scope: Mapping[str, object],
    renderer_candidate_scope: Mapping[str, object],
    public_package_candidate_paths: tuple[Path, ...],
    service_protocol_candidate_paths: tuple[Path, ...],
    patch_targets: tuple[str, ...],
) -> dict[str, object]:
    selected_scope_source = _optional_text(selected_candidate_file_scope.get("source"))
    file_scope_status = _optional_text(selected_candidate_file_scope.get("status"))
    renderer_scope_status = _optional_text(renderer_candidate_scope.get("status"))
    fragment_scope_applied = (
        selected_scope_source == "api_runtime_artifact_fragment_plan"
        and file_scope_status == "generated_path_candidate_file_scope_applied"
        and renderer_scope_status == "generated_artifact_renderer_candidate_scope_applied"
    )
    public_target_requested = "api_client" in patch_targets
    service_protocol_target_requested = "service_protocol" in patch_targets
    public_class_refs = _target_candidate_class_refs_from_scope(
        candidate_file_scope=selected_candidate_file_scope,
        target="api_client",
    )
    service_protocol_render_section_refs = (
        _target_candidate_render_section_refs_from_scope(
            candidate_file_scope=selected_candidate_file_scope,
            target="service_protocol",
        )
    )
    public_model_candidate_paths = tuple(
        path for path in public_package_candidate_paths if path.parts[:1] == ("models",)
    )
    public_global_candidate_paths = tuple(
        path for path in public_package_candidate_paths if path.parts[:1] != ("models",)
    )
    public_package_graph_input_pruned = False
    public_package_input_strategy: str | None = None
    public_package_blockers: tuple[str, ...] = ()

    if not public_target_requested:
        public_package_input_strategy = "not_requested"
    elif not fragment_scope_applied:
        public_package_input_strategy = "full_graph_required"
        public_package_blockers = ("runtime_fragment_file_scope_not_applied",)
    elif public_class_refs:
        public_package_graph_input_pruned = True
        public_package_input_strategy = "fragment_class_ref_subset"
    elif public_package_candidate_paths and not public_model_candidate_paths:
        public_package_graph_input_pruned = True
        public_package_input_strategy = "fragment_global_renderer_empty_graph"
    elif public_model_candidate_paths:
        public_package_input_strategy = "full_graph_required"
        public_package_blockers = ("model_candidate_class_refs_missing",)
    else:
        public_package_input_strategy = "full_graph_required"
        public_package_blockers = ("public_package_candidate_paths_missing",)

    service_protocol_full_input_required = (
        service_protocol_target_requested and bool(service_protocol_candidate_paths)
    )
    service_protocol_section_plan_ready = (
        service_protocol_target_requested
        and bool(service_protocol_render_section_refs)
        and bool(service_protocol_candidate_paths)
    )
    service_protocol_section_render_execution_wired = (
        service_protocol_section_plan_ready
        and _render_section_refs_wired(refs=service_protocol_render_section_refs)
    )
    if service_protocol_full_input_required:
        service_protocol_input_strategy = (
            "full_graph_required_global_protocol_renderer"
        )
    elif service_protocol_target_requested:
        service_protocol_input_strategy = "full_graph_required"
    else:
        service_protocol_input_strategy = "not_requested"

    if public_package_graph_input_pruned and service_protocol_full_input_required:
        status = "api_render_input_pruning_partially_applied"
    elif public_package_graph_input_pruned:
        status = "api_render_input_pruning_applied"
    elif service_protocol_full_input_required:
        status = "api_render_input_pruning_full_input_required"
    else:
        status = "api_render_input_pruning_not_available"

    return {
        "contract_version": API_RENDER_INPUT_PRUNING_CONTRACT_VERSION,
        "pruning_kind": "api_delta_runtime_fragment_render_input_pruning",
        "status": status,
        "reason": _render_input_pruning_reason(status=status),
        "source": "api_runtime_artifact_fragment_plan",
        "selected_file_scope_source": selected_scope_source,
        "selected_file_scope_status": file_scope_status,
        "renderer_candidate_scope_status": renderer_scope_status,
        "fragment_scope_applied": fragment_scope_applied,
        "requested_patch_targets": patch_targets,
        "public_package_input_strategy": public_package_input_strategy,
        "public_package_graph_input_pruned": public_package_graph_input_pruned,
        "public_package_render_input_class_refs": public_class_refs,
        "public_package_render_input_class_ref_count": len(public_class_refs),
        "public_package_model_candidate_paths": tuple(
            path.as_posix() for path in public_model_candidate_paths
        ),
        "public_package_global_candidate_paths": tuple(
            path.as_posix() for path in public_global_candidate_paths
        ),
        "public_package_blockers": public_package_blockers,
        "service_protocol_input_strategy": service_protocol_input_strategy,
        "service_protocol_full_input_required": service_protocol_full_input_required,
        "service_protocol_section_plan_status": (
            "api_service_protocol_render_section_plan_ready"
            if service_protocol_section_plan_ready
            else (
                "api_service_protocol_render_section_plan_missing"
                if service_protocol_target_requested
                else "not_requested"
            )
        ),
        "service_protocol_section_input_strategy": (
            "declarative_sections_ready_renderer_full_graph_required"
            if service_protocol_section_plan_ready
            else service_protocol_input_strategy
        ),
        "service_protocol_render_section_refs": (
            service_protocol_render_section_refs
        ),
        "service_protocol_render_section_ref_count": len(
            service_protocol_render_section_refs
        ),
        "service_protocol_section_render_execution_wired": (
            service_protocol_section_render_execution_wired
        ),
        "service_protocol_section_patch_wired": False,
        "service_protocol_section_apply_strategy": (
            "local_full_file_refresh_with_section_ref_resolution"
            if service_protocol_section_render_execution_wired
            else None
        ),
        "service_protocol_candidate_paths": tuple(
            path.as_posix() for path in service_protocol_candidate_paths
        ),
        "actual_public_package_graph_node_count": None,
        "actual_public_package_graph_ref": None,
    }


def _render_input_pruning_execution_payload(
    *,
    render_input_pruning_plan: Mapping[str, object],
    refresh_result: object,
) -> dict[str, object]:
    payload = dict(render_input_pruning_plan)
    public_package_materialization = getattr(
        refresh_result,
        "public_package_materialization",
        None,
    )
    dto_graph = getattr(public_package_materialization, "dto_graph", None)
    if dto_graph is not None:
        payload["actual_public_package_graph_node_count"] = len(
            getattr(dto_graph, "object_config_graph_nodes", ())
        )
        payload["actual_public_package_graph_ref"] = (
            _optional_text(getattr(dto_graph, "hash", None))
            or _optional_text(getattr(dto_graph, "id", None))
        )
    return payload


def _target_candidate_class_refs_from_scope(
    *,
    candidate_file_scope: Mapping[str, object],
    target: str,
) -> tuple[str, ...]:
    target_refs = _mapping_payload(
        candidate_file_scope.get("target_candidate_class_refs")
    )
    return tuple(
        sorted(
            {
                class_ref
                for class_ref in _tuple_text(target_refs.get(target))
                if class_ref
            },
            key=str.casefold,
        )
    )


def _target_candidate_render_section_refs_from_scope(
    *,
    candidate_file_scope: Mapping[str, object],
    target: str,
) -> tuple[dict[str, object], ...]:
    target_refs = _mapping_payload(
        candidate_file_scope.get("target_candidate_render_section_refs")
    )
    return _sorted_render_section_refs(target_refs.get(target))


def _render_section_refs_wired(
    *,
    refs: tuple[Mapping[str, object], ...],
) -> bool:
    return bool(refs) and all(ref.get("section_render_wired") is True for ref in refs)


def _render_input_pruning_reason(*, status: str) -> str:
    return {
        "api_render_input_pruning_applied": (
            "api_provider_delta_render_input_pruning_applied"
        ),
        "api_render_input_pruning_partially_applied": (
            "api_provider_delta_render_input_pruning_partially_applied"
        ),
        "api_render_input_pruning_full_input_required": (
            "api_provider_delta_render_input_pruning_full_input_required"
        ),
        "api_render_input_pruning_not_available": (
            "api_provider_delta_render_input_pruning_not_available"
        ),
    }[status]


def _snapshot_patch_target_artifact_files(
    *,
    runtime_package_dir: Path,
    workspace_root: Path | None,
    patch_targets: tuple[str, ...],
    candidate_file_keys: frozenset[str] | None = None,
) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for target, artifact_role, root in _patch_target_artifact_roots(
        runtime_package_dir=runtime_package_dir,
        patch_targets=patch_targets,
    ):
        if not root.is_dir():
            continue
        for path in _iter_patch_target_files(root=root):
            resolved_path = path.resolve()
            file_key = resolved_path.as_posix()
            if candidate_file_keys is not None and file_key not in candidate_file_keys:
                continue
            records[resolved_path.as_posix()] = {
                "target": target,
                "artifact_role": artifact_role,
                "path": file_key,
                "manifest_path": _workspace_relative_or_absolute_path(
                    path=resolved_path,
                    workspace_root=workspace_root,
                ),
                "digest": sha256(resolved_path.read_bytes()).hexdigest(),
            }
    return records


def _file_level_patch_render_result(
    *,
    runtime_package_dir: Path,
    workspace_root: Path,
    patch_targets: tuple[str, ...],
    artifact_ownership_receipts: tuple[dict[str, object], ...],
    before_file_records: Mapping[str, Mapping[str, object]],
    generated_path_candidate_file_scope: Mapping[str, object],
    renderer_candidate_scope: Mapping[str, object],
    renderer_fragment_execution: Mapping[str, object],
    render_input_pruning: Mapping[str, object],
) -> ApiClientServiceProtocolPatchRenderResult:
    render_section_refs_by_relpath = (
        _service_protocol_render_section_refs_by_runtime_relpath(
            candidate_file_scope=generated_path_candidate_file_scope,
        )
    )
    role_to_target = {
        role: target
        for target, roles in _PATCH_TARGET_ARTIFACT_ROLES.items()
        for role in roles
    }
    target_counts = {
        target: {
            "target": target,
            "artifact_roles": _PATCH_TARGET_ARTIFACT_ROLES.get(target, ()),
            "scanned_file_count": 0,
            "upserted_file_count": 0,
            "deleted_file_count": 0,
            "unchanged_file_count": 0,
        }
        for target in patch_targets
    }
    comparable_receipt_count = 0
    after_file_keys: set[str] = set()
    changed_files: list[dict[str, object]] = []
    unchanged_files: list[dict[str, object]] = []
    changed_receipts: list[dict[str, object]] = []

    for receipt in artifact_ownership_receipts:
        artifact_role = _optional_text(receipt.get("artifact_role"))
        if artifact_role is None:
            continue
        target = role_to_target.get(artifact_role)
        file_key = _receipt_file_key(receipt=receipt)
        digest = _receipt_digest(receipt=receipt)
        if target is None or file_key is None or digest is None:
            continue
        comparable_receipt_count += 1
        after_file_keys.add(file_key)
        target_counts[target]["scanned_file_count"] = cast(
            int,
            target_counts[target]["scanned_file_count"],
        ) + 1
        before_record = before_file_records.get(file_key)
        previous_digest = (
            _optional_text(before_record.get("digest"))
            if before_record is not None
            else None
        )
        render_section_refs = _service_protocol_render_section_refs_for_file(
            path_text=_optional_text(receipt.get("path")),
            manifest_path_text=_optional_text(receipt.get("manifest_path")),
            refs_by_runtime_relpath=render_section_refs_by_relpath,
        )
        section_text_manifest_entries = (
            _service_protocol_section_text_manifest_entries_for_file(
                path_text=_optional_text(receipt.get("path")),
                render_section_refs=render_section_refs,
            )
        )
        if before_record is None:
            change_kind = "create"
        elif previous_digest != digest:
            change_kind = "update"
        else:
            target_counts[target]["unchanged_file_count"] = cast(
                int,
                target_counts[target]["unchanged_file_count"],
            ) + 1
            unchanged_files.append(
                _file_patch_file_payload(
                    target=target,
                    artifact_role=artifact_role,
                    receipt=receipt,
                    change_kind="unchanged",
                    previous_digest=previous_digest,
                    current_digest=digest,
                    render_section_refs=render_section_refs,
                    section_text_manifest_entries=section_text_manifest_entries,
                )
            )
            continue

        target_counts[target]["upserted_file_count"] = cast(
            int,
            target_counts[target]["upserted_file_count"],
        ) + 1
        file_payload = _file_patch_file_payload(
            target=target,
            artifact_role=artifact_role,
            receipt=receipt,
            change_kind=change_kind,
            previous_digest=previous_digest,
            current_digest=digest,
            render_section_refs=render_section_refs,
            section_text_manifest_entries=section_text_manifest_entries,
        )
        changed_files.append(file_payload)
        changed_receipt = dict(receipt)
        changed_receipt["generated_artifact_file_patch_strategy"] = (
            "before_after_digest"
        )
        changed_receipt["generated_artifact_file_patch_change_kind"] = change_kind
        changed_receipt["previous_digest"] = previous_digest
        changed_receipts.append(changed_receipt)

    deleted_files: list[dict[str, object]] = []
    requested_targets = set(patch_targets)
    for file_key, before_record in before_file_records.items():
        target = _optional_text(before_record.get("target"))
        if target not in requested_targets or file_key in after_file_keys:
            continue
        artifact_role = _optional_text(before_record.get("artifact_role"))
        if artifact_role is None:
            continue
        render_section_refs = _service_protocol_render_section_refs_for_file(
            path_text=_optional_text(before_record.get("path")),
            manifest_path_text=_optional_text(before_record.get("manifest_path")),
            refs_by_runtime_relpath=render_section_refs_by_relpath,
        )
        target_counts[target]["deleted_file_count"] = cast(
            int,
            target_counts[target]["deleted_file_count"],
        ) + 1
        deleted_files.append(
            _file_patch_file_payload_from_record(
                target=target,
                artifact_role=artifact_role,
                record=before_record,
                change_kind="delete",
                current_digest=None,
                render_section_refs=render_section_refs,
            )
        )

    changed_file_count = len(changed_files) + len(deleted_files)
    if comparable_receipt_count == 0 and not before_file_records:
        status = "generated_artifact_file_patch_unavailable"
        receipt_scope = "target_receipts"
        returned_receipts = artifact_ownership_receipts
    else:
        status = (
            "generated_artifact_file_patch_applied"
            if changed_file_count > 0
            else "generated_artifact_file_patch_noop"
        )
        receipt_scope = "changed_files"
        returned_receipts = tuple(changed_receipts)

    service_protocol_section_render_execution = (
        _service_protocol_section_render_execution_payload(
            patch_targets=patch_targets,
            generated_path_candidate_file_scope=generated_path_candidate_file_scope,
            render_input_pruning=render_input_pruning,
            changed_files=tuple(changed_files),
            deleted_files=tuple(deleted_files),
            unchanged_files=tuple(unchanged_files),
        )
    )
    service_protocol_section_apply = _service_protocol_section_apply_payload(
        patch_targets=patch_targets,
        generated_path_candidate_file_scope=generated_path_candidate_file_scope,
        render_input_pruning=render_input_pruning,
        section_render_execution=service_protocol_section_render_execution,
        changed_files=tuple(changed_files),
        deleted_files=tuple(deleted_files),
        unchanged_files=tuple(unchanged_files),
    )
    generated_artifact_file_patch = {
        "contract_version": GENERATED_ARTIFACT_FILE_PATCH_CONTRACT_VERSION,
        "status": status,
        "strategy": "before_after_digest",
        "receipt_scope": receipt_scope,
        "requested_patch_targets": patch_targets,
        "runtime_package_dir": runtime_package_dir.as_posix(),
        "changed_file_count": changed_file_count,
        "upserted_file_count": len(changed_files),
        "deleted_file_count": len(deleted_files),
        "unchanged_file_count": len(unchanged_files),
        "changed_files": tuple(changed_files),
        "deleted_files": tuple(deleted_files),
        "unchanged_files": tuple(unchanged_files),
        "target_file_patch_counts": tuple(
            dict(target_counts[target]) for target in patch_targets
        ),
        "generated_path_candidate_file_scope": dict(
            generated_path_candidate_file_scope
        ),
        "generated_path_candidate_file_scope_status": _optional_text(
            generated_path_candidate_file_scope.get("status")
        ),
        "generated_artifact_renderer_candidate_scope": dict(
            renderer_candidate_scope
        ),
        "generated_artifact_renderer_candidate_scope_status": _optional_text(
            renderer_candidate_scope.get("status")
        ),
        "generated_artifact_renderer_fragment_execution": dict(
            renderer_fragment_execution
        ),
        "generated_artifact_renderer_fragment_execution_status": _optional_text(
            renderer_fragment_execution.get("status")
        ),
        "generated_artifact_render_input_pruning": dict(render_input_pruning),
        "generated_artifact_render_input_pruning_status": _optional_text(
            render_input_pruning.get("status")
        ),
        "service_protocol_section_render_execution": (
            service_protocol_section_render_execution
        ),
        "service_protocol_section_render_execution_status": _optional_text(
            service_protocol_section_render_execution.get("status")
        ),
        "service_protocol_section_apply": service_protocol_section_apply,
        "service_protocol_section_apply_status": _optional_text(
            service_protocol_section_apply.get("status")
        ),
        "workspace_root": workspace_root.as_posix(),
    }
    return ApiClientServiceProtocolPatchRenderResult(
        artifact_ownership_receipts=returned_receipts,
        generated_artifact_file_patch=generated_artifact_file_patch,
    )


def _patch_target_artifact_roots(
    *,
    runtime_package_dir: Path,
    patch_targets: tuple[str, ...],
) -> tuple[tuple[str, str, Path], ...]:
    roots: list[tuple[str, str, Path]] = []
    for target in patch_targets:
        roles = _PATCH_TARGET_ARTIFACT_ROLES.get(target, ())
        segments = _PATCH_TARGET_ARTIFACT_ROOT_SEGMENTS.get(target)
        if not roles or segments is None:
            continue
        roots.append((target, roles[0], runtime_package_dir.joinpath(*segments)))
    return tuple(roots)


def _iter_patch_target_files(*, root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        files.append(path)
    return tuple(sorted(files, key=lambda item: item.as_posix()))


def _receipt_file_key(*, receipt: Mapping[str, object]) -> str | None:
    path_text = _optional_text(receipt.get("path"))
    if path_text is None:
        return None
    return Path(path_text).resolve().as_posix()


def _receipt_digest(*, receipt: Mapping[str, object]) -> str | None:
    digest = _optional_text(receipt.get("digest"))
    if digest is not None:
        return digest
    path_text = _optional_text(receipt.get("path"))
    if path_text is None:
        return None
    path = Path(path_text)
    if not path.is_file():
        return None
    return sha256(path.read_bytes()).hexdigest()


def _file_patch_file_payload(
    *,
    target: str,
    artifact_role: str,
    receipt: Mapping[str, object],
    change_kind: str,
    previous_digest: str | None,
    current_digest: str | None,
    render_section_refs: tuple[dict[str, object], ...] = (),
    section_text_manifest_entries: tuple[dict[str, object], ...] = (),
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target": target,
        "artifact_role": artifact_role,
        "path": _optional_text(receipt.get("path")),
        "manifest_path": _optional_text(receipt.get("manifest_path")),
        "change_kind": change_kind,
        "previous_digest": previous_digest,
        "current_digest": current_digest,
    }
    if render_section_refs:
        payload["service_protocol_render_section_refs"] = render_section_refs
        payload["service_protocol_render_section_ref_count"] = len(
            render_section_refs
        )
        payload["service_protocol_section_render_execution_wired"] = (
            _render_section_refs_wired(refs=render_section_refs)
        )
        payload["service_protocol_section_text_manifest_entries"] = (
            section_text_manifest_entries
        )
        payload["service_protocol_section_text_manifest_entry_count"] = len(
            section_text_manifest_entries
        )
    return payload


def _file_patch_file_payload_from_record(
    *,
    target: str,
    artifact_role: str,
    record: Mapping[str, object],
    change_kind: str,
    current_digest: str | None,
    render_section_refs: tuple[dict[str, object], ...] = (),
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target": target,
        "artifact_role": artifact_role,
        "path": _optional_text(record.get("path")),
        "manifest_path": _optional_text(record.get("manifest_path")),
        "change_kind": change_kind,
        "previous_digest": _optional_text(record.get("digest")),
        "current_digest": current_digest,
    }
    if render_section_refs:
        payload["service_protocol_render_section_refs"] = render_section_refs
        payload["service_protocol_render_section_ref_count"] = len(
            render_section_refs
        )
        payload["service_protocol_section_render_execution_wired"] = (
            _render_section_refs_wired(refs=render_section_refs)
        )
    return payload


def _workspace_relative_or_absolute_path(
    *,
    path: Path,
    workspace_root: Path | None,
) -> str:
    if workspace_root is None:
        return path.as_posix()
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _service_protocol_render_section_refs_by_runtime_relpath(
    *,
    candidate_file_scope: Mapping[str, object],
) -> dict[str, tuple[dict[str, object], ...]]:
    refs_by_relpath: dict[str, dict[str, dict[str, object]]] = {}
    for ref in _target_candidate_render_section_refs_from_scope(
        candidate_file_scope=candidate_file_scope,
        target="service_protocol",
    ):
        relpath = _optional_text(ref.get("runtime_package_relpath"))
        section_key = _optional_text(ref.get("section_key"))
        if relpath is None or section_key is None:
            continue
        refs_by_relpath.setdefault(relpath, {})[section_key] = dict(ref)
    return {
        relpath: _sorted_render_section_refs(refs.values())
        for relpath, refs in sorted(refs_by_relpath.items())
    }


def _service_protocol_render_section_refs_for_file(
    *,
    path_text: str | None,
    manifest_path_text: str | None,
    refs_by_runtime_relpath: Mapping[str, tuple[dict[str, object], ...]],
) -> tuple[dict[str, object], ...]:
    matched_refs: dict[str, dict[str, object]] = {}
    path_candidates = tuple(
        candidate
        for candidate in (path_text, manifest_path_text)
        if candidate is not None
    )
    for runtime_relpath, refs in refs_by_runtime_relpath.items():
        if not any(candidate.endswith(runtime_relpath) for candidate in path_candidates):
            continue
        for ref in refs:
            section_key = _optional_text(ref.get("section_key"))
            if section_key is None:
                continue
            matched_refs[section_key] = dict(ref)
    return _sorted_render_section_refs(matched_refs.values())


def _service_protocol_section_text_manifest_entries_for_file(
    *,
    path_text: str | None,
    render_section_refs: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    if path_text is None or not render_section_refs:
        return ()
    manifest = _service_protocol_section_text_manifest_for_file(path=Path(path_text))
    if manifest is None:
        return ()
    contract_version = _optional_text(manifest.get("contract_version"))
    if contract_version != API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_CONTRACT_VERSION:
        return ()
    text_digest_algorithm = _optional_text(manifest.get("text_digest_algorithm"))
    target_relpath = _optional_text(manifest.get("target_relpath"))
    refs_by_section_key = {
        section_key
        for section_key in (
            _optional_text(ref.get("section_key")) for ref in render_section_refs
        )
        if section_key is not None
    }
    entries: list[dict[str, object]] = []
    for raw_entry in _tuple_mapping_payloads(manifest.get("sections")):
        section_key = _optional_text(raw_entry.get("section_key"))
        if section_key is None or section_key not in refs_by_section_key:
            continue
        rendered_text_digest = _optional_text(raw_entry.get("rendered_text_digest"))
        if rendered_text_digest is None:
            continue
        entries.append(
            {
                "contract_version": contract_version,
                "section_key": section_key,
                "section_kind": _optional_text(raw_entry.get("section_kind")),
                "section_order": _int_value(raw_entry.get("section_order")),
                "line_count": _int_value(raw_entry.get("line_count")),
                "target_relpath": target_relpath,
                "text_digest_algorithm": text_digest_algorithm,
                "rendered_text_digest": rendered_text_digest,
            }
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                _int_value(item.get("section_order")) or 0,
                str(item.get("section_key") or ""),
            ),
        )
    )


def _service_protocol_section_text_manifest_for_file(
    *,
    path: Path,
) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    for node in tree.body:
        value_node: ast.expr | None = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME:
                value_node = node.value
        elif isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name)
                and target.id == API_SERVICE_PROTOCOL_SECTION_TEXT_MANIFEST_JSON_NAME
                for target in node.targets
            ):
                value_node = node.value
        if value_node is None:
            continue
        try:
            manifest_json = ast.literal_eval(value_node)
        except (SyntaxError, TypeError, ValueError):
            return None
        if not isinstance(manifest_json, str):
            return None
        try:
            manifest = json.loads(manifest_json)
        except json.JSONDecodeError:
            return None
        if isinstance(manifest, dict):
            return cast(dict[str, object], manifest)
        return None
    return None


def _service_protocol_section_render_execution_payload(
    *,
    patch_targets: tuple[str, ...],
    generated_path_candidate_file_scope: Mapping[str, object],
    render_input_pruning: Mapping[str, object],
    changed_files: tuple[Mapping[str, object], ...],
    deleted_files: tuple[Mapping[str, object], ...],
    unchanged_files: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    if "service_protocol" not in patch_targets:
        return {
            "contract_version": (
                API_SERVICE_PROTOCOL_SECTION_RENDER_EXECUTION_CONTRACT_VERSION
            ),
            "status": "api_service_protocol_section_render_execution_not_requested",
            "reason": "service_protocol_patch_target_not_requested",
            "source": "aware_api.provider_delta.generated_artifact_file_patch",
            "strategy": None,
            "available": False,
            "blocked": False,
            "blockers": (),
            "render_section_refs": (),
            "render_section_ref_count": 0,
            "section_operation_count": 0,
            "changed_section_operation_count": 0,
            "noop_section_operation_count": 0,
            "section_operations": (),
            "rendered_text_digest_available": False,
            "section_patch_wired": False,
            "filesystem_apply_wired": False,
        }

    section_refs = _target_candidate_render_section_refs_from_scope(
        candidate_file_scope=generated_path_candidate_file_scope,
        target="service_protocol",
    )
    render_input_status = _optional_text(render_input_pruning.get("status"))
    section_plan_status = _optional_text(
        render_input_pruning.get("service_protocol_section_plan_status")
    )
    section_render_wired = (
        render_input_pruning.get("service_protocol_section_render_execution_wired")
        is True
    )
    service_file_payloads = tuple(
        file_payload
        for file_payload in (*changed_files, *deleted_files, *unchanged_files)
        if _optional_text(file_payload.get("target")) == "service_protocol"
    )
    blockers: list[str] = []
    if section_plan_status != "api_service_protocol_render_section_plan_ready":
        blockers.append(
            "service_protocol_section_plan_not_ready:"
            f"{section_plan_status or 'unknown'}"
        )
    if not section_refs:
        blockers.append("service_protocol_render_section_refs_missing")
    if not section_render_wired:
        blockers.append("service_protocol_section_render_execution_not_wired")
    if not service_file_payloads:
        blockers.append("service_protocol_file_patch_payload_missing")

    section_operations = tuple(
        operation
        for file_payload in service_file_payloads
        for operation in _service_protocol_section_render_operations_for_file(
            file_payload=file_payload,
        )
    )
    missing_required_text_digest_count = sum(
        1
        for operation in section_operations
        if _optional_text(operation.get("operation_family")) != "delete"
        and operation.get("rendered_text_digest_available") is not True
    )
    if missing_required_text_digest_count:
        blockers.append("service_protocol_section_text_manifest_missing")
    blocked = bool(blockers)
    changed_section_operation_count = sum(
        1
        for operation in section_operations
        if _optional_text(operation.get("operation_family")) != "noop"
    )
    noop_section_operation_count = len(section_operations) - changed_section_operation_count
    rendered_text_digest_available = (
        bool(section_operations)
        and missing_required_text_digest_count == 0
        and any(
            operation.get("rendered_text_digest_available") is True
            for operation in section_operations
        )
    )
    if blocked:
        status = "api_service_protocol_section_render_execution_blocked"
        reason = "api_service_protocol_section_render_execution_requires_resolved_sections"
    elif changed_section_operation_count:
        status = "api_service_protocol_section_render_execution_applied"
        reason = "api_service_protocol_section_render_execution_applied"
    else:
        status = "api_service_protocol_section_render_execution_noop"
        reason = "api_service_protocol_section_render_execution_noop"

    return {
        "contract_version": (
            API_SERVICE_PROTOCOL_SECTION_RENDER_EXECUTION_CONTRACT_VERSION
        ),
        "status": status,
        "reason": reason,
        "source": "aware_api.provider_delta.generated_artifact_file_patch",
        "strategy": "section_ref_resolved_full_file_refresh_execution",
        "available": not blocked,
        "blocked": blocked,
        "blockers": tuple(dict.fromkeys(blockers)),
        "render_input_pruning_status": render_input_status,
        "section_plan_status": section_plan_status,
        "section_render_execution_wired": section_render_wired,
        "render_section_refs": section_refs,
        "render_section_ref_count": len(section_refs),
        "section_operation_count": len(section_operations),
        "changed_section_operation_count": changed_section_operation_count,
        "noop_section_operation_count": noop_section_operation_count,
        "section_operation_family_counts": _operation_counts_by_field(
            operations=section_operations,
            field_name="operation_family",
        ),
        "section_kind_counts": _operation_counts_by_field(
            operations=section_operations,
            field_name="section_kind",
        ),
        "section_operations": section_operations,
        "rendered_text_digest_available": rendered_text_digest_available,
        "rendered_text_digest_missing_operation_count": (
            missing_required_text_digest_count
        ),
        "rendered_text_digest_unavailable_reason": (
            None
            if rendered_text_digest_available
            else "renderer_section_text_manifest_missing"
        ),
        "section_patch_wired": False,
        "filesystem_apply_wired": False,
        "event_dispatch_wired": False,
    }


def _service_protocol_section_render_operations_for_file(
    *,
    file_payload: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    render_section_refs = _sorted_render_section_refs(
        file_payload.get("service_protocol_render_section_refs")
    )
    if not render_section_refs:
        return ()
    change_kind = _optional_text(file_payload.get("change_kind")) or "unknown"
    operation_family = "noop" if change_kind == "unchanged" else change_kind
    previous_digest = _optional_text(file_payload.get("previous_digest"))
    current_digest = _optional_text(file_payload.get("current_digest"))
    manifest_path = _optional_text(file_payload.get("manifest_path"))
    path = _optional_text(file_payload.get("path"))
    text_entries_by_section_key: dict[str, Mapping[str, object]] = {}
    for entry in _tuple_mapping_payloads(
        file_payload.get("service_protocol_section_text_manifest_entries")
    ):
        section_key = _optional_text(entry.get("section_key"))
        if section_key is not None:
            text_entries_by_section_key[section_key] = entry
    operations: list[dict[str, object]] = []
    for ref in render_section_refs:
        section_key = _optional_text(ref.get("section_key"))
        if section_key is None:
            continue
        text_entry = text_entries_by_section_key.get(section_key)
        rendered_text_digest = (
            _optional_text(text_entry.get("rendered_text_digest"))
            if text_entry is not None
            else None
        )
        rendered_text_digest_available = rendered_text_digest is not None
        rendered_text_digest_unavailable_reason = (
            None
            if rendered_text_digest_available
            else (
                "deleted_file_no_current_rendered_text"
                if operation_family == "delete"
                else "renderer_section_text_manifest_missing"
            )
        )
        payload_basis = {
            "section_key": section_key,
            "section_kind": _optional_text(ref.get("section_kind")),
            "semantic_key": _optional_text(ref.get("semantic_key")),
            "runtime_package_relpath": _optional_text(
                ref.get("runtime_package_relpath")
            ),
            "change_kind": change_kind,
            "previous_file_digest": previous_digest,
            "current_file_digest": current_digest,
            "rendered_text_digest": rendered_text_digest,
        }
        operations.append(
            {
                "operation_kind": "api_service_protocol_section_render_operation",
                "operation_family": operation_family,
                "change_kind": change_kind,
                "section_key": section_key,
                "section_kind": _optional_text(ref.get("section_kind")),
                "semantic_key": _optional_text(ref.get("semantic_key")),
                "runtime_package_relpath": _optional_text(
                    ref.get("runtime_package_relpath")
                ),
                "api_name": _optional_text(ref.get("api_name")),
                "capability_name": _optional_text(ref.get("capability_name")),
                "endpoint_name": _optional_text(ref.get("endpoint_name")),
                "target": _optional_text(file_payload.get("target")),
                "artifact_role": _optional_text(file_payload.get("artifact_role")),
                "manifest_path": manifest_path,
                "path": path,
                "previous_file_digest": previous_digest,
                "current_file_digest": current_digest,
                "section_payload_digest": _stable_payload_digest(payload_basis),
                "section_text_manifest_contract_version": (
                    _optional_text(text_entry.get("contract_version"))
                    if text_entry is not None
                    else None
                ),
                "section_text_manifest_target_relpath": (
                    _optional_text(text_entry.get("target_relpath"))
                    if text_entry is not None
                    else None
                ),
                "rendered_text_line_count": (
                    _int_value(text_entry.get("line_count"))
                    if text_entry is not None
                    else None
                ),
                "rendered_text_digest": rendered_text_digest,
                "rendered_text_digest_available": (
                    rendered_text_digest_available
                ),
                "rendered_text_digest_unavailable_reason": (
                    rendered_text_digest_unavailable_reason
                ),
                "section_render_wired": ref.get("section_render_wired") is True,
                "section_patch_wired": False,
                "filesystem_apply_wired": False,
                "event_dispatch_wired": False,
            }
        )
    return tuple(operations)


def _service_protocol_section_apply_payload(
    *,
    patch_targets: tuple[str, ...],
    generated_path_candidate_file_scope: Mapping[str, object],
    render_input_pruning: Mapping[str, object],
    section_render_execution: Mapping[str, object],
    changed_files: tuple[Mapping[str, object], ...],
    deleted_files: tuple[Mapping[str, object], ...],
    unchanged_files: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    if "service_protocol" not in patch_targets:
        return {
            "contract_version": API_SERVICE_PROTOCOL_SECTION_APPLY_CONTRACT_VERSION,
            "status": "api_service_protocol_section_apply_not_requested",
            "reason": "service_protocol_patch_target_not_requested",
            "source": "aware_api.provider_delta.generated_artifact_file_patch",
            "strategy": None,
            "available": False,
            "blocked": False,
            "blockers": (),
            "render_section_refs": (),
            "render_section_ref_count": 0,
            "section_patch_wired": False,
            "shared_filesystem_delta_apply_wired": False,
        }

    section_refs = _target_candidate_render_section_refs_from_scope(
        candidate_file_scope=generated_path_candidate_file_scope,
        target="service_protocol",
    )
    render_input_status = _optional_text(render_input_pruning.get("status"))
    section_render_execution_status = _optional_text(
        section_render_execution.get("status")
    )
    section_plan_status = _optional_text(
        render_input_pruning.get("service_protocol_section_plan_status")
    )
    section_render_wired = (
        render_input_pruning.get("service_protocol_section_render_execution_wired")
        is True
    )
    service_file_payloads = tuple(
        file_payload
        for file_payload in (*changed_files, *deleted_files, *unchanged_files)
        if _optional_text(file_payload.get("target")) == "service_protocol"
    )
    changed_service_file_payloads = tuple(
        file_payload
        for file_payload in (*changed_files, *deleted_files)
        if _optional_text(file_payload.get("target")) == "service_protocol"
    )
    blockers: list[str] = []
    if section_plan_status != "api_service_protocol_render_section_plan_ready":
        blockers.append(
            "service_protocol_section_plan_not_ready:"
            f"{section_plan_status or 'unknown'}"
        )
    if not section_refs:
        blockers.append("service_protocol_render_section_refs_missing")
    if not section_render_wired:
        blockers.append("service_protocol_section_render_execution_not_wired")
    if section_render_execution_status not in {
        "api_service_protocol_section_render_execution_applied",
        "api_service_protocol_section_render_execution_noop",
    }:
        blockers.append(
            "service_protocol_section_render_execution_not_ready:"
            f"{section_render_execution_status or 'unknown'}"
        )
    if not service_file_payloads:
        blockers.append("service_protocol_file_patch_payload_missing")

    blocked = bool(blockers)
    if blocked:
        status = "api_service_protocol_section_apply_blocked"
        reason = "api_service_protocol_section_apply_requires_resolved_sections"
    elif changed_service_file_payloads:
        status = "api_service_protocol_section_apply_applied"
        reason = "api_service_protocol_section_apply_resolved_via_full_file_refresh"
    else:
        status = "api_service_protocol_section_apply_noop"
        reason = "api_service_protocol_section_apply_resolved_no_changed_sections"

    file_payload_summaries = tuple(
        {
            "manifest_path": _optional_text(file_payload.get("manifest_path")),
            "change_kind": _optional_text(file_payload.get("change_kind")),
            "render_section_ref_count": _int_value(
                file_payload.get("service_protocol_render_section_ref_count")
            )
            or 0,
        }
        for file_payload in service_file_payloads
    )
    return {
        "contract_version": API_SERVICE_PROTOCOL_SECTION_APPLY_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "source": "aware_api.provider_delta.generated_artifact_file_patch",
        "strategy": "local_full_file_refresh_with_section_ref_resolution",
        "available": not blocked,
        "blocked": blocked,
        "blockers": tuple(dict.fromkeys(blockers)),
        "render_input_pruning_status": render_input_status,
        "section_render_execution_status": section_render_execution_status,
        "section_plan_status": section_plan_status,
        "section_render_execution_wired": section_render_wired,
        "render_section_refs": section_refs,
        "render_section_ref_count": len(section_refs),
        "section_operation_count": _int_value(
            section_render_execution.get("section_operation_count")
        )
        or 0,
        "resolved_file_count": len(service_file_payloads),
        "changed_file_count": len(changed_service_file_payloads),
        "file_payloads": file_payload_summaries,
        "section_patch_wired": False,
        "shared_filesystem_delta_apply_wired": False,
        "future_shared_apply_contract": "filesystem.service_operation.apply_delta",
    }


def _target_patch_executions(
    *,
    patch_targets: tuple[str, ...],
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    did_patch: bool,
    generated_artifact_file_patch: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    role_counts = _artifact_role_counts(
        artifact_ownership_receipts=artifact_ownership_receipts,
    )
    file_patch_target_counts = _generated_artifact_file_patch_target_counts(
        generated_artifact_file_patch=generated_artifact_file_patch,
    )
    executions: list[dict[str, object]] = []
    for target in patch_targets:
        roles = _PATCH_TARGET_ARTIFACT_ROLES.get(target, ())
        receipt_count = sum(role_counts.get(role, 0) for role in roles)
        file_counts = file_patch_target_counts.get(target, {})
        upserted_file_count = _int_value(file_counts.get("upserted_file_count")) or 0
        deleted_file_count = _int_value(file_counts.get("deleted_file_count")) or 0
        unchanged_file_count = _int_value(file_counts.get("unchanged_file_count")) or 0
        changed_file_count = upserted_file_count + deleted_file_count
        executions.append(
            {
                "target": target,
                "status": (
                    "patched"
                    if did_patch and (receipt_count > 0 or changed_file_count > 0)
                    else (
                        "no_changed_files"
                        if did_patch and target in file_patch_target_counts
                        else "not_patched"
                    )
                ),
                "artifact_roles": roles,
                "artifact_ownership_receipt_count": receipt_count,
                "generated_artifact_upserted_file_count": upserted_file_count,
                "generated_artifact_deleted_file_count": deleted_file_count,
                "generated_artifact_changed_file_count": changed_file_count,
                "generated_artifact_unchanged_file_count": unchanged_file_count,
            }
        )
    return tuple(executions)


def _missing_target_artifact_receipt_blockers(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
    patch_targets: tuple[str, ...],
) -> tuple[str, ...]:
    role_counts = _artifact_role_counts(
        artifact_ownership_receipts=artifact_ownership_receipts,
    )
    blockers: list[str] = []
    for target in patch_targets:
        roles = _PATCH_TARGET_ARTIFACT_ROLES.get(target, ())
        if not any(role_counts.get(role, 0) > 0 for role in roles):
            blockers.append(f"target_artifact_receipts_missing:{target}")
    return tuple(blockers)


def _target_patch_status_counts(
    *,
    target_patch_executions: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for execution in target_patch_executions:
        status = _optional_text(execution.get("status"))
        if status is None:
            continue
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _generated_artifact_file_patch_payload(
    *,
    generated_artifact_file_patch: Mapping[str, object] | None,
    patch_targets: tuple[str, ...],
    would_patch: bool,
    did_patch: bool,
) -> dict[str, object]:
    if generated_artifact_file_patch is not None:
        return _mapping_payload(generated_artifact_file_patch)
    return {
        "contract_version": GENERATED_ARTIFACT_FILE_PATCH_CONTRACT_VERSION,
        "status": (
            "generated_artifact_file_patch_not_declared"
            if would_patch or did_patch
            else "generated_artifact_file_patch_not_attempted"
        ),
        "strategy": None,
        "receipt_scope": None,
        "requested_patch_targets": patch_targets,
        "changed_file_count": 0,
        "upserted_file_count": 0,
        "deleted_file_count": 0,
        "unchanged_file_count": 0,
        "target_file_patch_counts": (),
    }


def _generated_artifact_file_patch_covers_targets(
    *,
    generated_artifact_file_patch: Mapping[str, object] | None,
    patch_targets: tuple[str, ...],
) -> bool:
    payload = _mapping_payload(generated_artifact_file_patch)
    status = _optional_text(payload.get("status"))
    if status not in {
        "generated_artifact_file_patch_applied",
        "generated_artifact_file_patch_noop",
    }:
        return False
    target_counts = _generated_artifact_file_patch_target_counts(
        generated_artifact_file_patch=payload,
    )
    return all(target in target_counts for target in patch_targets)


def _generated_artifact_file_patch_target_counts(
    *,
    generated_artifact_file_patch: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    counts: dict[str, dict[str, object]] = {}
    raw_counts = generated_artifact_file_patch.get("target_file_patch_counts")
    if not isinstance(raw_counts, (list, tuple)):
        return counts
    for item in raw_counts:
        payload = _mapping_payload(item)
        target = _optional_text(payload.get("target"))
        if target is None:
            continue
        counts[target] = payload
    return counts


def _generated_artifact_renderer_pruning_payload(
    *,
    generated_artifact_file_patch: Mapping[str, object],
    patch_targets: tuple[str, ...],
    did_patch: bool,
) -> dict[str, object]:
    file_patch_status = _optional_text(generated_artifact_file_patch.get("status"))
    pruning_available = file_patch_status in {
        "generated_artifact_file_patch_applied",
        "generated_artifact_file_patch_noop",
    }
    target_counts = _generated_artifact_file_patch_target_counts(
        generated_artifact_file_patch=generated_artifact_file_patch,
    )
    target_pruning_counts: list[dict[str, object]] = []
    for target in patch_targets:
        file_counts = target_counts.get(target, {})
        upserted_file_count = _int_value(file_counts.get("upserted_file_count")) or 0
        deleted_file_count = _int_value(file_counts.get("deleted_file_count")) or 0
        unchanged_file_count = _int_value(file_counts.get("unchanged_file_count")) or 0
        target_pruning_counts.append(
            {
                "target": target,
                "artifact_roles": _PATCH_TARGET_ARTIFACT_ROLES.get(target, ()),
                "emitted_changed_file_count": (
                    upserted_file_count + deleted_file_count
                ),
                "pruned_unchanged_file_count": unchanged_file_count,
            }
        )
    emitted_changed_file_count = sum(
        _int_value(item.get("emitted_changed_file_count")) or 0
        for item in target_pruning_counts
    )
    pruned_unchanged_file_count = sum(
        _int_value(item.get("pruned_unchanged_file_count")) or 0
        for item in target_pruning_counts
    )
    return {
        "contract_version": "aware.api.generated-artifact-renderer-pruning.v1",
        "status": (
            "generated_artifact_renderer_pruning_applied"
            if did_patch and pruning_available
            else "generated_artifact_renderer_pruning_not_available"
        ),
        "strategy": (
            "before_after_digest_changed_file_propagation"
            if pruning_available
            else None
        ),
        "source_file_patch_status": file_patch_status,
        "requested_patch_targets": patch_targets,
        "emitted_changed_file_count": emitted_changed_file_count,
        "pruned_unchanged_file_count": pruned_unchanged_file_count,
        "target_pruning_counts": tuple(target_pruning_counts),
    }


def _generated_artifact_render_input_pruning_payload(
    *,
    generated_artifact_file_patch: Mapping[str, object],
    patch_targets: tuple[str, ...],
    did_patch: bool,
) -> dict[str, object]:
    payload = _mapping_payload(
        generated_artifact_file_patch.get("generated_artifact_render_input_pruning")
    )
    if payload:
        return payload
    return {
        "contract_version": API_RENDER_INPUT_PRUNING_CONTRACT_VERSION,
        "pruning_kind": "api_delta_runtime_fragment_render_input_pruning",
        "status": (
            "api_render_input_pruning_not_declared"
            if did_patch
            else "api_render_input_pruning_not_attempted"
        ),
        "reason": "api_provider_delta_render_input_pruning_not_declared",
        "requested_patch_targets": patch_targets,
        "public_package_graph_input_pruned": False,
        "public_package_render_input_class_refs": (),
        "public_package_render_input_class_ref_count": 0,
        "service_protocol_full_input_required": False,
    }


def _language_artifact_delta_apply_payload(
    *,
    patch_targets: tuple[str, ...],
    would_patch: bool,
    did_patch: bool,
    generated_artifact_file_patch: Mapping[str, object],
    materialization_event_report: Mapping[str, object],
    materialization_event_artifact_driver: Mapping[str, object],
    renderer_candidate_scope: Mapping[str, object],
) -> dict[str, object]:
    file_patch_status = _optional_text(generated_artifact_file_patch.get("status"))
    file_scope = _mapping_payload(
        generated_artifact_file_patch.get("generated_path_candidate_file_scope")
    )
    file_scope_source = _optional_text(file_scope.get("source"))
    event_driver_status = _optional_text(
        materialization_event_artifact_driver.get("status")
    )
    renderer_scope_status = _optional_text(renderer_candidate_scope.get("status"))
    event_refs_by_relpath = _materialization_event_refs_by_runtime_package_relpath(
        materialization_event_report=materialization_event_report
    )
    changed_operations = tuple(
        _language_artifact_delta_operation_payload(
            file_payload=_mapping_payload(item),
            operation_source="generated_artifact_file_patch.changed_files",
            event_refs_by_relpath=event_refs_by_relpath,
        )
        for item in _tuple_mapping_payloads(
            generated_artifact_file_patch.get("changed_files")
        )
    )
    deleted_operations = tuple(
        _language_artifact_delta_operation_payload(
            file_payload=_mapping_payload(item),
            operation_source="generated_artifact_file_patch.deleted_files",
            event_refs_by_relpath=event_refs_by_relpath,
        )
        for item in _tuple_mapping_payloads(
            generated_artifact_file_patch.get("deleted_files")
        )
    )
    noop_operations = tuple(
        _language_artifact_delta_operation_payload(
            file_payload=_mapping_payload(item),
            operation_source="generated_artifact_file_patch.unchanged_files",
            event_refs_by_relpath=event_refs_by_relpath,
        )
        for item in _tuple_mapping_payloads(
            generated_artifact_file_patch.get("unchanged_files")
        )
    )
    operations = (*changed_operations, *deleted_operations)
    service_protocol_section_apply = _mapping_payload(
        generated_artifact_file_patch.get("service_protocol_section_apply")
    )
    service_protocol_section_render_execution = _mapping_payload(
        generated_artifact_file_patch.get("service_protocol_section_render_execution")
    )
    file_patch_ready = file_patch_status in {
        "generated_artifact_file_patch_applied",
        "generated_artifact_file_patch_noop",
    }
    event_driven = (
        event_driver_status == "materialization_event_artifact_driver_ready"
        and bool(event_refs_by_relpath)
    )
    fragment_guided = (
        file_scope_source == "api_runtime_artifact_fragment_plan"
    )
    blockers: list[str] = []
    if would_patch and not file_patch_ready:
        blockers.append(f"generated_artifact_file_patch_not_ready:{file_patch_status}")
    if would_patch and event_driver_status != "materialization_event_artifact_driver_ready":
        blockers.append(
            "materialization_event_artifact_driver_not_ready:"
            f"{event_driver_status}"
        )
    if would_patch and file_scope_source not in {
        "api_materialization_event_report",
        "api_runtime_artifact_fragment_plan",
    }:
        blockers.append(
            "language_artifact_delta_apply_scope_not_supported:"
            f"{file_scope_source}"
        )
    if would_patch and renderer_scope_status != (
        "generated_artifact_renderer_candidate_scope_applied"
    ):
        blockers.append(
            "renderer_candidate_scope_not_applied:"
            f"{renderer_scope_status}"
        )
    available = did_patch and file_patch_ready and event_driven and not blockers
    if not would_patch:
        status = "api_language_artifact_delta_apply_not_attempted"
        reason = "api_language_artifact_delta_apply_not_attempted"
    elif not available:
        status = "api_language_artifact_delta_apply_blocked"
        reason = "api_language_artifact_delta_apply_requires_event_driven_file_patch"
    elif operations:
        status = "api_language_artifact_delta_apply_applied"
        reason = "api_language_artifact_delta_apply_applied"
    else:
        status = "api_language_artifact_delta_apply_noop"
        reason = "api_language_artifact_delta_apply_noop"
    return {
        "contract_version": API_LANGUAGE_ARTIFACT_DELTA_APPLY_CONTRACT_VERSION,
        "apply_kind": "api_client_service_protocol_language_artifact_delta_apply",
        "provider_key": "aware_api",
        "semantic_owner": "aware_api.provider",
        "producer_key": "aware_api.api_client_service_protocol",
        "status": status,
        "reason": reason,
        "source": "aware_api.provider_delta.generated_artifact_file_patch",
        "strategy": (
            "fragment_guided_event_backed_generated_artifact_file_delta"
            if fragment_guided
            else "event_driven_generated_artifact_file_delta"
        ),
        "available": available,
        "blocked": bool(blockers),
        "blockers": tuple(dict.fromkeys(blockers)),
        "blocker_count": len(tuple(dict.fromkeys(blockers))),
        "would_apply": would_patch,
        "did_apply": did_patch and available,
        "event_driven": event_driven,
        "fragment_guided": fragment_guided,
        "event_driver_status": event_driver_status,
        "source_event_report_status": _optional_text(
            materialization_event_report.get("status")
        ),
        "source_file_patch_status": file_patch_status,
        "candidate_file_scope_status": _optional_text(file_scope.get("status")),
        "candidate_file_scope_source": file_scope_source,
        "renderer_candidate_scope_status": renderer_scope_status,
        "requested_patch_targets": patch_targets,
        "operation_count": len(operations),
        "changed_operation_count": len(changed_operations),
        "deleted_operation_count": len(deleted_operations),
        "noop_operation_count": len(noop_operations),
        "operation_family_counts": _operation_counts_by_field(
            operations=(*operations, *noop_operations),
            field_name="operation_family",
        ),
        "target_operation_counts": _operation_counts_by_field(
            operations=operations,
            field_name="target",
        ),
        "noop_target_counts": _operation_counts_by_field(
            operations=noop_operations,
            field_name="target",
        ),
        "service_protocol_section_apply_status": _optional_text(
            service_protocol_section_apply.get("status")
        ),
        "service_protocol_section_apply_available": (
            service_protocol_section_apply.get("available") is True
        ),
        "service_protocol_section_render_execution_status": _optional_text(
            service_protocol_section_render_execution.get("status")
        ),
        "service_protocol_section_render_execution_available": (
            service_protocol_section_render_execution.get("available") is True
        ),
        "service_protocol_render_section_ref_count": _int_value(
            service_protocol_section_apply.get("render_section_ref_count")
        )
        or 0,
        "service_protocol_section_operation_count": _int_value(
            service_protocol_section_render_execution.get("section_operation_count")
        )
        or 0,
        "operations": operations,
        "noop_operations": noop_operations,
        "event_ref_count": sum(
            len(_tuple_mapping_payloads(operation.get("semantic_event_refs")))
            for operation in operations
        ),
        "would_dispatch": False,
        "did_dispatch": False,
        "event_dispatch_wired": False,
    }


def _language_artifact_delta_operation_payload(
    *,
    file_payload: Mapping[str, object],
    operation_source: str,
    event_refs_by_relpath: Mapping[str, tuple[dict[str, object], ...]],
) -> dict[str, object]:
    change_kind = _optional_text(file_payload.get("change_kind")) or "unknown"
    operation_family = "noop" if change_kind == "unchanged" else change_kind
    semantic_event_refs = _semantic_event_refs_for_file_payload(
        file_payload=file_payload,
        event_refs_by_relpath=event_refs_by_relpath,
    )
    render_section_refs = _sorted_render_section_refs(
        file_payload.get("service_protocol_render_section_refs")
    )
    payload: dict[str, object] = {
        "operation_kind": "api_language_artifact_delta_operation",
        "operation_family": operation_family,
        "change_kind": change_kind,
        "target": _optional_text(file_payload.get("target")),
        "artifact_role": _optional_text(file_payload.get("artifact_role")),
        "language": _language_from_file_payload(file_payload=file_payload),
        "manifest_path": _optional_text(file_payload.get("manifest_path")),
        "path": _optional_text(file_payload.get("path")),
        "previous_digest": _optional_text(file_payload.get("previous_digest")),
        "current_digest": _optional_text(file_payload.get("current_digest")),
        "source": operation_source,
        "semantic_event_refs": semantic_event_refs,
        "semantic_event_ref_count": len(semantic_event_refs),
        "event_driven": bool(semantic_event_refs),
        "would_apply": operation_family != "noop",
        "did_apply": operation_family != "noop",
    }
    if render_section_refs:
        payload["service_protocol_render_section_refs"] = render_section_refs
        payload["service_protocol_render_section_ref_count"] = len(
            render_section_refs
        )
        payload["service_protocol_section_render_execution_wired"] = (
            _render_section_refs_wired(refs=render_section_refs)
        )
    return payload


def _materialization_event_refs_by_runtime_package_relpath(
    *,
    materialization_event_report: Mapping[str, object],
) -> dict[str, tuple[dict[str, object], ...]]:
    refs_by_relpath: dict[str, list[dict[str, object]]] = {}
    for event in _materialization_event_report_events(
        materialization_event_report=materialization_event_report,
    ):
        event_ref = {
            "event_key": _optional_text(event.get("event_key")),
            "semantic_key": _optional_text(event.get("semantic_key")),
            "verb": _optional_text(event.get("verb")),
            "ontology_subject_kind": _optional_text(
                event.get("ontology_subject_kind")
            ),
            "subject_label": _optional_text(event.get("subject_label")),
        }
        for candidate in _tuple_mapping_payloads(
            event.get("generated_path_candidates")
        ):
            relpath = _optional_text(candidate.get("runtime_package_relpath"))
            if relpath is None:
                continue
            refs_by_relpath.setdefault(relpath, []).append(
                {
                    **event_ref,
                    "target": _optional_text(candidate.get("target")),
                    "artifact_role": _optional_text(candidate.get("artifact_role")),
                    "generated_path_kind": _optional_text(
                        candidate.get("generated_path_kind")
                    ),
                    "runtime_package_relpath": relpath,
                }
            )
    return {
        relpath: tuple(refs)
        for relpath, refs in sorted(refs_by_relpath.items())
    }


def _semantic_event_refs_for_file_payload(
    *,
    file_payload: Mapping[str, object],
    event_refs_by_relpath: Mapping[str, tuple[dict[str, object], ...]],
) -> tuple[dict[str, object], ...]:
    manifest_path = _optional_text(file_payload.get("manifest_path")) or ""
    path = _optional_text(file_payload.get("path")) or ""
    refs: list[dict[str, object]] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for runtime_relpath, event_refs in event_refs_by_relpath.items():
        if not (
            manifest_path.endswith(runtime_relpath)
            or path.endswith(runtime_relpath)
        ):
            continue
        for ref in event_refs:
            key = (
                _optional_text(ref.get("event_key")),
                _optional_text(ref.get("semantic_key")),
                _optional_text(ref.get("target")),
                _optional_text(ref.get("runtime_package_relpath")),
            )
            if key in seen:
                continue
            seen.add(key)
            refs.append(dict(ref))
    return tuple(refs)


def _language_from_file_payload(*, file_payload: Mapping[str, object]) -> str | None:
    for field_name in ("manifest_path", "path"):
        text = _optional_text(file_payload.get(field_name))
        if text is None:
            continue
        path = Path(text)
        parts = path.parts
        for index, part in enumerate(parts):
            if part in {"public_package", "service_protocol"} and index + 1 < len(parts):
                return parts[index + 1]
    return None


def _operation_counts_by_field(
    *,
    operations: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for operation in operations:
        field_value = _optional_text(operation.get(field_name))
        if field_value is None:
            continue
        counts[field_value] = counts.get(field_value, 0) + 1
    return dict(sorted(counts.items()))


def _materialization_event_report_events(
    *,
    materialization_event_report: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    raw_events = materialization_event_report.get("semantic_world_change_events")
    if not isinstance(raw_events, (list, tuple)):
        raw_events = materialization_event_report.get("materialization_events")
    if not isinstance(raw_events, (list, tuple)):
        raw_events = materialization_event_report.get("events")
    return tuple(item for item in _tuple_evidence(raw_events) if isinstance(item, Mapping))


def _candidate_counts_by_target(
    *,
    candidates: tuple[Mapping[str, object], ...],
    patch_targets: tuple[str, ...],
) -> dict[str, int]:
    requested_targets = set(patch_targets)
    counts: dict[str, int] = {}
    for candidate in candidates:
        target = _optional_text(candidate.get("target"))
        if target not in requested_targets:
            continue
        artifact_role = _optional_text(candidate.get("artifact_role"))
        if artifact_role not in _PATCH_TARGET_ARTIFACT_ROLES.get(target, ()):
            continue
        relpath = _optional_text(candidate.get("runtime_package_relpath"))
        if relpath is None:
            continue
        counts[target] = counts.get(target, 0) + 1
    return dict(sorted(counts.items()))


def _mapping_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return {}


def _stable_payload_digest(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        _json_safe_payload(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256(canonical).hexdigest()}"


def _json_safe_payload(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe_payload(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple):
        return [_json_safe_payload(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_payload(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if value is None:
        return ()
    return (value,)


def _tuple_mapping_payloads(value: object) -> tuple[Mapping[str, object], ...]:
    return tuple(item for item in _tuple_evidence(value) if isinstance(item, Mapping))


def _tuple_text(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text
        for text in (_optional_text(item) for item in value)
        if text is not None
    )


def _artifact_role_counts(
    *,
    artifact_ownership_receipts: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for receipt in artifact_ownership_receipts:
        role = _optional_text(receipt.get("artifact_role"))
        if role is None:
            continue
        counts[role] = counts.get(role, 0) + 1
    return dict(sorted(counts.items()))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if value is None:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


__all__ = [
    "API_CLIENT_SERVICE_PROTOCOL_PATCH_CONTRACT_VERSION",
    "API_LANGUAGE_ARTIFACT_DELTA_APPLY_CONTRACT_VERSION",
    "API_MATERIALIZATION_EVENT_ARTIFACT_DRIVER_CONTRACT_VERSION",
    "api_delta_api_client_service_protocol_patch_receipt",
]
