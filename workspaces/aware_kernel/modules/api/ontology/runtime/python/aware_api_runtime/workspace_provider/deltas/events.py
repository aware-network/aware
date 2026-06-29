from __future__ import annotations

from collections.abc import Mapping, Sequence

from aware_api_runtime.workspace_provider.deltas.typed_operations import (
    api_delta_operation_count_by_field,
)


API_MATERIALIZATION_EVENT_REPORT_CONTRACT_VERSION = (
    "aware.api.provider-delta-materialization-event-report.v1"
)
API_MATERIALIZATION_EVENT_CONTRACT_VERSION = (
    "aware.api.provider-delta-materialization-event.v1"
)
API_MATERIALIZATION_EVENT_CHAIN_CONTRACT_VERSION = (
    "aware.api.provider-delta-materialization-event-chain.v1"
)
API_WORKSPACE_AGGREGATE_PROVIDER_EVIDENCE_CONTRACT_VERSION = (
    "aware.api.provider-delta-workspace-aggregate-provider-evidence.v1"
)
API_PROVIDER_KEY = "aware_api"


def api_delta_materialization_event_report(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    runtime_artifact_delta_plan: Mapping[str, object],
) -> dict[str, object]:
    dirty_status = _optional_text(semantic_dirty_diff.get("status"))
    typed_status = _optional_text(provider_delta_typed_operation_plan.get("status"))
    runtime_status = _optional_text(runtime_artifact_delta_plan.get("status"))
    candidate_plan = _mapping_payload(
        runtime_artifact_delta_plan.get("generated_path_candidate_plan")
    )
    fragment_plan = _mapping_payload(
        runtime_artifact_delta_plan.get("runtime_artifact_fragment_plan")
    )
    candidate_status = _optional_text(candidate_plan.get("status"))
    fragment_status = _optional_text(fragment_plan.get("status"))
    blockers = _materialization_event_report_blockers(
        dirty_status=dirty_status,
        typed_status=typed_status,
        runtime_status=runtime_status,
        candidate_plan=candidate_plan,
        candidate_status=candidate_status,
    )
    typed_operations = tuple(
        _mapping_payload(operation)
        for operation in _tuple_evidence(
            provider_delta_typed_operation_plan.get("typed_operations")
        )
        if isinstance(operation, Mapping)
    )
    candidates = tuple(
        _mapping_payload(candidate)
        for candidate in _tuple_evidence(candidate_plan.get("candidates"))
        if isinstance(candidate, Mapping)
    )
    candidate_by_semantic_key = _candidate_by_semantic_key(candidates=candidates)
    materialization_events = (
        ()
        if blockers
        else tuple(
            _materialization_event_from_typed_operation(
                typed_operation=operation,
                runtime_artifact_delta_plan=runtime_artifact_delta_plan,
                generated_path_candidates=candidate_by_semantic_key.get(
                    _optional_text(operation.get("semantic_key")) or "",
                    (),
                ),
            )
            for operation in typed_operations
            if _optional_text(operation.get("operation_family"))
            in {"create", "update", "delete"}
        )
    )
    event_candidate_gaps = tuple(
        event
        for event in materialization_events
        if not _tuple_mapping_payloads(event.get("generated_path_candidates"))
    )
    if event_candidate_gaps:
        blockers = (
            *blockers,
            "materialization_event_generated_path_candidates_missing",
        )
        materialization_events = ()
    available = not blockers
    readable_event_chain = _readable_materialization_event_chain(
        available=available,
        blockers=blockers,
        materialization_events=materialization_events,
    )
    return {
        "report_kind": "api_provider_delta_materialization_event_report",
        "contract_version": API_MATERIALIZATION_EVENT_REPORT_CONTRACT_VERSION,
        "event_contract_version": API_MATERIALIZATION_EVENT_CONTRACT_VERSION,
        "readable_event_chain_contract_version": (
            API_MATERIALIZATION_EVENT_CHAIN_CONTRACT_VERSION
        ),
        "status": (
            "api_materialization_event_report_ready"
            if available
            else "api_materialization_event_report_blocked"
        ),
        "reason": (
            "api_provider_delta_materialization_events_ready"
            if available
            else "api_provider_delta_materialization_event_report_blocked"
        ),
        "source": "aware_api.provider_delta.typed_operations",
        "provider_key": API_PROVIDER_KEY,
        "semantic_dirty_diff_status": dirty_status,
        "provider_delta_typed_operation_status": typed_status,
        "runtime_artifact_delta_plan_status": runtime_status,
        "runtime_artifact_fragment_plan_status": fragment_status,
        "runtime_artifact_fragment_ready": (
            fragment_plan.get("fragment_ready") is True
        ),
        "runtime_artifact_fragment_operation_count": _int_value(
            fragment_plan.get("fragment_operation_count")
        ),
        "generated_path_candidate_plan_status": candidate_status,
        "generated_path_candidate_filter_ready": (
            candidate_plan.get("candidate_filter_ready") is True
        ),
        "current_delta_fingerprint": _optional_text(
            runtime_artifact_delta_plan.get("current_delta_fingerprint")
        ),
        "head_refs": _head_refs(
            runtime_artifact_delta_plan=runtime_artifact_delta_plan
        ),
        "baseline_refs": _baseline_refs(semantic_dirty_diff=semantic_dirty_diff),
        "semantic_dirty_entry_count": _int_value(
            semantic_dirty_diff.get("dirty_entry_count")
        ),
        "typed_operation_count": len(typed_operations),
        "generated_path_candidate_count": len(candidates),
        "materialization_event_count": len(materialization_events),
        "semantic_world_change_event_count": len(materialization_events),
        "events": materialization_events,
        "materialization_events": materialization_events,
        "semantic_world_change_events": materialization_events,
        "readable_materialization_event_chain": readable_event_chain,
        "readable_semantic_event_chain": readable_event_chain,
        "minimal_readable_semantic_event_chain": readable_event_chain,
        "readable_materialization_event_chain_markdown": (
            readable_event_chain["markdown"]
        ),
        "readable_semantic_event_chain_markdown": readable_event_chain["markdown"],
        "readable_materialization_event_chain_lines": readable_event_chain["lines"],
        "readable_semantic_event_chain_lines": readable_event_chain["lines"],
        "natural_language_summaries": tuple(
            _optional_text(event.get("summary")) or ""
            for event in materialization_events
        ),
        "event_type_counts": api_delta_operation_count_by_field(
            operations=materialization_events,
            field_name="event_type",
        ),
        "event_key_counts": api_delta_operation_count_by_field(
            operations=materialization_events,
            field_name="event_key",
        ),
        "operation_family_counts": api_delta_operation_count_by_field(
            operations=materialization_events,
            field_name="verb",
        ),
        "artifact_target_counts": _artifact_target_counts(
            materialization_events=materialization_events,
        ),
        "language_delta_driver_ready": available,
        "language_delta_driver_status": (
            "language_delta_driver_event_targets_ready"
            if available
            else "language_delta_driver_event_targets_blocked"
        ),
        "available": available,
        "blocked": not available,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "would_dispatch": False,
        "did_dispatch": False,
        "event_dispatch_wired": False,
        "reactivity_dispatch_status": "dispatch_unwired",
        "reactivity_dispatch_reason": (
            "api_materialization_event_preview_dispatch_unwired"
        ),
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def api_delta_materialization_event_report_with_workspace_aggregate_evidence(
    *,
    materialization_event_report: Mapping[str, object],
    api_client_service_protocol_delta_patch: Mapping[str, object],
) -> dict[str, object]:
    report = _mapping_payload(materialization_event_report)
    aggregate_evidence = _workspace_aggregate_provider_evidence(
        materialization_event_report=report,
        api_client_service_protocol_delta_patch=(
            api_client_service_protocol_delta_patch
        ),
    )
    return {
        **report,
        "workspace_aggregate_provider_evidence": aggregate_evidence,
        "workspace_aggregate_provider_evidence_status": (
            aggregate_evidence["status"]
        ),
        "workspace_aggregate_provider_evidence_contract_version": (
            API_WORKSPACE_AGGREGATE_PROVIDER_EVIDENCE_CONTRACT_VERSION
        ),
        "durable_provider_evidence_available": aggregate_evidence[
            "available"
        ],
    }


def _workspace_aggregate_provider_evidence(
    *,
    materialization_event_report: Mapping[str, object],
    api_client_service_protocol_delta_patch: Mapping[str, object],
) -> dict[str, object]:
    artifact_driver = _mapping_payload(
        api_client_service_protocol_delta_patch.get(
            "materialization_event_artifact_driver"
        )
    )
    file_patch = _mapping_payload(
        api_client_service_protocol_delta_patch.get("generated_artifact_file_patch")
    )
    service_protocol_section_apply = _mapping_payload(
        file_patch.get("service_protocol_section_apply")
    )
    service_protocol_section_render_execution = _mapping_payload(
        file_patch.get("service_protocol_section_render_execution")
    )
    renderer_scope = _mapping_payload(
        api_client_service_protocol_delta_patch.get(
            "generated_artifact_renderer_candidate_scope"
        )
    )
    language_delta_apply = _mapping_payload(
        api_client_service_protocol_delta_patch.get("language_artifact_delta_apply")
    )
    report_status = _optional_text(materialization_event_report.get("status"))
    patch_status = _optional_text(api_client_service_protocol_delta_patch.get("status"))
    artifact_driver_status = _optional_text(artifact_driver.get("status"))
    blockers: list[str] = []
    if report_status != "api_materialization_event_report_ready":
        blockers.append(f"materialization_event_report_not_ready:{report_status}")
    if patch_status not in {
        "api_client_service_protocol_patch_applied",
        "api_client_service_protocol_patch_noop",
    }:
        blockers.append(f"api_client_service_protocol_patch_not_ready:{patch_status}")
    if artifact_driver_status != "materialization_event_artifact_driver_ready":
        blockers.append(
            "materialization_event_artifact_driver_not_ready:"
            f"{artifact_driver_status}"
        )
    language_delta_apply_status = _optional_text(language_delta_apply.get("status"))
    if language_delta_apply_status not in {
        "api_language_artifact_delta_apply_applied",
        "api_language_artifact_delta_apply_noop",
    }:
        blockers.append(
            "language_artifact_delta_apply_not_ready:"
            f"{language_delta_apply_status}"
        )
    available = not blockers
    return {
        "evidence_kind": "api_provider_delta_workspace_aggregate_provider_evidence",
        "contract_version": (
            API_WORKSPACE_AGGREGATE_PROVIDER_EVIDENCE_CONTRACT_VERSION
        ),
        "provider_key": API_PROVIDER_KEY,
        "status": (
            "api_workspace_aggregate_provider_evidence_ready"
            if available
            else "api_workspace_aggregate_provider_evidence_blocked"
        ),
        "reason": (
            "api_provider_delta_workspace_aggregate_evidence_ready"
            if available
            else "api_provider_delta_workspace_aggregate_evidence_blocked"
        ),
        "source": "aware_api.provider_delta.materialization_event_report",
        "available": available,
        "blocked": not available,
        "blockers": tuple(blockers),
        "blocker_count": len(blockers),
        "provider_event_report_status": report_status,
        "semantic_world_change_event_count": _int_value(
            materialization_event_report.get("semantic_world_change_event_count")
        ),
        "readable_semantic_event_chain_status": _optional_text(
            _mapping_payload(
                materialization_event_report.get("readable_semantic_event_chain")
            ).get("status")
        ),
        "api_client_service_protocol_patch_status": patch_status,
        "api_client_service_protocol_patch_did_patch": (
            api_client_service_protocol_delta_patch.get("did_patch") is True
        ),
        "materialization_event_artifact_driver_status": artifact_driver_status,
        "materialization_event_artifact_driver_source": _optional_text(
            artifact_driver.get("source")
        ),
        "artifact_driver_target_candidate_counts": _mapping_payload(
            artifact_driver.get("target_candidate_counts")
        ),
        "artifact_patch_targets": _tuple_text(
            api_client_service_protocol_delta_patch.get("patch_targets")
        ),
        "generated_artifact_file_patch_status": _optional_text(
            file_patch.get("status")
        ),
        "generated_artifact_changed_file_count": _int_value(
            file_patch.get("changed_file_count")
        ),
        "generated_artifact_upserted_file_count": _int_value(
            file_patch.get("upserted_file_count")
        ),
        "generated_artifact_deleted_file_count": _int_value(
            file_patch.get("deleted_file_count")
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
        ),
        "service_protocol_section_operation_count": _int_value(
            service_protocol_section_render_execution.get("section_operation_count")
        ),
        "renderer_candidate_scope_status": _optional_text(
            renderer_scope.get("status")
        ),
        "renderer_candidate_path_count": _int_value(
            renderer_scope.get("renderer_candidate_path_count")
        ),
        "language_artifact_delta_apply_status": language_delta_apply_status,
        "language_artifact_delta_apply_event_driven": (
            language_delta_apply.get("event_driven") is True
        ),
        "language_artifact_delta_apply_operation_count": _int_value(
            language_delta_apply.get("operation_count")
        ),
        "language_artifact_delta_apply_changed_operation_count": _int_value(
            language_delta_apply.get("changed_operation_count")
        ),
        "language_artifact_delta_apply_deleted_operation_count": _int_value(
            language_delta_apply.get("deleted_operation_count")
        ),
        "language_artifact_delta_apply_noop_operation_count": _int_value(
            language_delta_apply.get("noop_operation_count")
        ),
        "language_artifact_delta_apply_target_operation_counts": _mapping_payload(
            language_delta_apply.get("target_operation_counts")
        ),
        "workspace_envelope_retains_provider_report_payload": True,
        "workspace_aggregate_consumes_provider_envelope": True,
        "event_dispatch_wired": False,
        "would_dispatch": False,
        "did_dispatch": False,
    }


def _materialization_event_report_blockers(
    *,
    dirty_status: str | None,
    typed_status: str | None,
    runtime_status: str | None,
    candidate_plan: Mapping[str, object],
    candidate_status: str | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if dirty_status != "semantic_dirty_diff_ready":
        blockers.append(f"semantic_dirty_diff_not_ready:{dirty_status or 'unknown'}")
    if typed_status != "typed_operation_plan_ready":
        blockers.append(f"typed_operation_plan_not_ready:{typed_status or 'unknown'}")
    if runtime_status != "api_product_runtime_delta_plan_ready":
        blockers.append(
            f"runtime_artifact_delta_plan_not_ready:{runtime_status or 'unknown'}"
        )
    if candidate_status != "generated_path_candidate_plan_ready":
        blockers.append(
            f"generated_path_candidate_plan_not_ready:{candidate_status or 'unknown'}"
        )
    if candidate_plan.get("candidate_filter_ready") is not True:
        blockers.append("generated_path_candidate_filter_not_ready")
    return tuple(dict.fromkeys(blockers))


def _materialization_event_from_typed_operation(
    *,
    typed_operation: Mapping[str, object],
    runtime_artifact_delta_plan: Mapping[str, object],
    generated_path_candidates: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    current = _mapping_payload(typed_operation.get("current"))
    baseline = _mapping_payload(typed_operation.get("baseline"))
    projection = _mapping_payload(typed_operation.get("semantic_event_projection"))
    api_operation = _mapping_payload(typed_operation.get("api_operation"))
    operation_family = _optional_text(typed_operation.get("operation_family")) or (
        "unknown"
    )
    subject_kind = _optional_text(typed_operation.get("ontology_subject_kind")) or (
        "api_semantic_object"
    )
    semantic_key = _optional_text(typed_operation.get("semantic_key"))
    event_key = (
        _optional_text(projection.get("event_key"))
        or f"aware_api.materialization.{subject_kind}.{operation_family}"
    ).replace("aware_api.provider_delta.", "aware_api.materialization.")
    candidate_payloads = tuple(
        _generated_path_candidate_payload(candidate=candidate)
        for candidate in generated_path_candidates
    )
    artifact_targets = tuple(
        sorted(
            {
                target
                for target in (
                    _optional_text(candidate.get("target"))
                    for candidate in candidate_payloads
                )
                if target is not None
            }
        )
    )
    summary = _materialization_event_summary(
        operation_family=operation_family,
        subject_kind=subject_kind,
        current=current,
        artifact_targets=artifact_targets,
    )
    return {
        "event_kind": "api_provider_delta_materialization_event",
        "contract_version": API_MATERIALIZATION_EVENT_CONTRACT_VERSION,
        "event_key": event_key,
        "event_type": "api_materialization_event_preview",
        "summary": summary,
        "narrative": summary,
        "semantic_key": semantic_key,
        "verb": operation_family,
        "subject_type": _optional_text(
            typed_operation.get("semantic_subject_type")
        ),
        "ontology_subject_kind": subject_kind,
        "subject_label": _subject_label(
            subject_kind=subject_kind,
            current=current,
            semantic_key=semantic_key,
        ),
        "provider_operation_type": _optional_text(
            typed_operation.get("provider_operation_type")
        ),
        "source": "aware_api.provider_delta.typed_operations",
        "source_refs": _tuple_text(typed_operation.get("source_refs")),
        "delta_keys": _tuple_text(projection.get("delta_keys")),
        "condition_keys": tuple(
            dict.fromkeys(
                (
                    *_tuple_text(projection.get("condition_keys")),
                    "api.provider_delta.semantic_dirty_diff_ready",
                    "api.provider_delta.typed_operation_plan_ready",
                    "api.provider_delta.runtime_artifact_delta_plan_ready",
                    "api.provider_delta.runtime_artifact_fragment_plan_ready",
                    "api.provider_delta.generated_path_candidates_ready",
                    f"api.provider_delta.operation_family.{operation_family}",
                    f"api.provider_delta.subject_kind.{subject_kind}",
                )
            )
        ),
        "baseline": baseline,
        "current": current,
        "api_operation": api_operation,
        "head_refs": _head_refs(runtime_artifact_delta_plan=runtime_artifact_delta_plan),
        "current_delta_fingerprint": _optional_text(
            runtime_artifact_delta_plan.get("current_delta_fingerprint")
        ),
        "runtime_package_dir": _optional_text(
            runtime_artifact_delta_plan.get("runtime_package_dir")
        ),
        "generated_path_candidates": candidate_payloads,
        "generated_path_candidate_count": len(candidate_payloads),
        "artifact_targets": artifact_targets,
        "artifact_target_counts": _candidate_counts_by_field(
            candidates=candidate_payloads,
            field_name="target",
        ),
        "language_delta_driver_ready": bool(candidate_payloads),
        "language_delta_driver_status": (
            "language_delta_driver_event_targets_ready"
            if candidate_payloads
            else "language_delta_driver_event_targets_missing"
        ),
        "would_dispatch": False,
        "did_dispatch": False,
        "event_dispatch_wired": False,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
    }


def _generated_path_candidate_payload(
    *,
    candidate: Mapping[str, object],
) -> dict[str, object]:
    render_section_refs = tuple(
        dict(ref)
        for ref in _tuple_mapping_payloads(candidate.get("render_section_refs"))
    )
    payload: dict[str, object] = {
        "candidate_kind": "api_materialization_event_generated_path_candidate",
        "semantic_key": _optional_text(candidate.get("semantic_key")),
        "target": _optional_text(candidate.get("target")),
        "artifact_role": _optional_text(candidate.get("artifact_role")),
        "generated_path_kind": _optional_text(candidate.get("generated_path_kind")),
        "generated_path": _optional_text(candidate.get("generated_path")),
        "runtime_package_relpath": _optional_text(
            candidate.get("runtime_package_relpath")
        ),
        "class_ref": _optional_text(candidate.get("class_ref")),
        "api_semantic_key": _optional_text(candidate.get("api_semantic_key")),
        "capability_semantic_key": _optional_text(
            candidate.get("capability_semantic_key")
        ),
        "endpoint_semantic_key": _optional_text(candidate.get("endpoint_semantic_key")),
        "source_refs": _tuple_text(candidate.get("source_refs")),
    }
    if render_section_refs:
        payload["render_section_refs"] = render_section_refs
        payload["render_section_ref_count"] = (
            _int_value(candidate.get("render_section_ref_count"))
            or len(render_section_refs)
        )
    return payload


def _readable_materialization_event_chain(
    *,
    available: bool,
    blockers: tuple[str, ...],
    materialization_events: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    lines = (
        tuple(
            _readable_materialization_event_chain_line(
                event=event,
                index=index,
            )
            for index, event in enumerate(materialization_events, start=1)
        )
        if available
        else ()
    )
    return {
        "chain_kind": "api_provider_delta_materialization_event_chain",
        "contract_version": API_MATERIALIZATION_EVENT_CHAIN_CONTRACT_VERSION,
        "status": (
            "api_materialization_event_chain_ready"
            if available
            else "api_materialization_event_chain_blocked"
        ),
        "reason": (
            "api_provider_delta_materialization_event_chain_ready"
            if available
            else "api_provider_delta_materialization_event_chain_blocked"
        ),
        "source": "aware_api.provider_delta.materialization_event_report",
        "provider_key": API_PROVIDER_KEY,
        "event_count": len(materialization_events),
        "line_count": len(lines),
        "lines": lines,
        "markdown": _readable_materialization_event_chain_markdown(lines=lines),
        "plain_text": "\n".join(lines),
        "available": available,
        "blocked": not available,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "would_dispatch": False,
        "did_dispatch": False,
        "event_dispatch_wired": False,
    }


def _readable_materialization_event_chain_line(
    *,
    event: Mapping[str, object],
    index: int,
) -> str:
    operation = _optional_text(event.get("verb")) or "change"
    subject_label = _optional_text(event.get("subject_label")) or (
        _optional_text(event.get("semantic_key")) or "semantic object"
    )
    targets = ", ".join(_tuple_text(event.get("artifact_targets")))
    suffix = f" -> {targets}" if targets else ""
    return f"{index}. {_readable_operation_label(operation)} {subject_label}{suffix}."


def _readable_operation_label(operation: str) -> str:
    if operation == "create":
        return "Add"
    if operation == "update":
        return "Update"
    if operation == "delete":
        return "Remove"
    return operation.replace("_", " ").capitalize()


def _readable_materialization_event_chain_markdown(
    *,
    lines: tuple[str, ...],
) -> str:
    if not lines:
        return "No API materialization events are ready."
    return "\n".join(lines)


def _materialization_event_summary(
    *,
    operation_family: str,
    subject_kind: str,
    current: Mapping[str, object],
    artifact_targets: tuple[str, ...],
) -> str:
    subject_label = _subject_label(
        subject_kind=subject_kind,
        current=current,
        semantic_key=_optional_text(current.get("semantic_key")),
    )
    targets = ", ".join(artifact_targets) if artifact_targets else "no artifacts"
    return (
        "API materialization will "
        f"{_summary_operation_label(operation_family)} "
        f"{_summary_subject_kind_label(subject_kind)} `{subject_label}` "
        f"for {targets}."
    )


def _summary_operation_label(operation: str) -> str:
    if operation == "create":
        return "add"
    if operation == "update":
        return "update"
    if operation == "delete":
        return "remove"
    return operation.replace("_", " ")


def _summary_subject_kind_label(subject_kind: str) -> str:
    return {
        "api": "API",
        "api_capability": "API capability",
        "api_capability_endpoint": "API endpoint",
    }.get(subject_kind, "API semantic object")


def _subject_label(
    *,
    subject_kind: str,
    current: Mapping[str, object],
    semantic_key: str | None,
) -> str:
    payload = _mapping_payload(current.get("payload"))
    if subject_kind == "api":
        return _optional_text(payload.get("name")) or semantic_key or "api"
    if subject_kind == "api_capability":
        api_name = _optional_text(payload.get("api_name"))
        name = _optional_text(payload.get("name"))
        if api_name is not None and name is not None:
            return f"{api_name}.{name}"
        return name or semantic_key or "api capability"
    if subject_kind == "api_capability_endpoint":
        api_name = _optional_text(payload.get("api_name"))
        capability_name = _optional_text(payload.get("capability_name"))
        name = _optional_text(payload.get("name"))
        parts = tuple(part for part in (api_name, capability_name, name) if part)
        if parts:
            return ".".join(parts)
        return semantic_key or "api endpoint"
    return semantic_key or "api semantic object"


def _candidate_by_semantic_key(
    *,
    candidates: tuple[Mapping[str, object], ...],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for candidate in candidates:
        semantic_key = _optional_text(candidate.get("semantic_key"))
        if semantic_key is None:
            continue
        grouped.setdefault(semantic_key, []).append(candidate)
    return {key: tuple(value) for key, value in grouped.items()}


def _artifact_target_counts(
    *,
    materialization_events: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in materialization_events:
        for target in _tuple_text(event.get("artifact_targets")):
            counts[target] = counts.get(target, 0) + 1
    return dict(sorted(counts.items()))


def _candidate_counts_by_field(
    *,
    candidates: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        value = _optional_text(candidate.get(field_name))
        if value is None:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _head_refs(
    *,
    runtime_artifact_delta_plan: Mapping[str, object],
) -> dict[str, str]:
    head_refs = _mapping_payload(runtime_artifact_delta_plan.get("head_refs"))
    if head_refs:
        return {
            key: value
            for key, value in (
                (str(field_name), _optional_text(field_value))
                for field_name, field_value in head_refs.items()
            )
            if value is not None
        }
    return {
        field_name: field_value
        for field_name, field_value in (
            (field_name, _optional_text(runtime_artifact_delta_plan.get(field_name)))
            for field_name in (
                "source_code_package_id",
                "source_object_instance_graph_commit_id",
                "semantic_package_id",
                "semantic_branch_id",
                "semantic_head_commit_id",
                "semantic_object_instance_graph_commit_id",
            )
        )
        if field_value is not None
    }


def _baseline_refs(
    *,
    semantic_dirty_diff: Mapping[str, object],
) -> dict[str, str]:
    return {
        field_name: field_value
        for field_name, field_value in (
            (field_name, _optional_text(semantic_dirty_diff.get(field_name)))
            for field_name in (
                "baseline_branch_id",
                "baseline_projection_name",
                "baseline_semantic_package_id",
                "baseline_semantic_package_commit_id",
                "baseline_semantic_object_instance_graph_commit_id",
                "baseline_semantic_root_object_instance_graph_commit_id",
            )
        )
        if field_value is not None
    }


def _tuple_mapping_payloads(value: object) -> tuple[Mapping[str, object], ...]:
    return tuple(item for item in _tuple_evidence(value) if isinstance(item, Mapping))


def _mapping_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _tuple_text(value: object) -> tuple[str, ...]:
    return tuple(
        text
        for text in (_optional_text(item) for item in _tuple_evidence(value))
        if text is not None
    )


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
    "API_MATERIALIZATION_EVENT_CHAIN_CONTRACT_VERSION",
    "API_MATERIALIZATION_EVENT_CONTRACT_VERSION",
    "API_MATERIALIZATION_EVENT_REPORT_CONTRACT_VERSION",
    "API_WORKSPACE_AGGREGATE_PROVIDER_EVIDENCE_CONTRACT_VERSION",
    "api_delta_materialization_event_report",
    "api_delta_materialization_event_report_with_workspace_aggregate_evidence",
]
