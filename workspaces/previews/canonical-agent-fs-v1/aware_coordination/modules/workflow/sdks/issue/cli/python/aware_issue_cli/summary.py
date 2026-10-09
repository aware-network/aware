"""Opt-in presentation of SDK results; no source reads, decisions or mutations."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping


def validate_presentation_input(payload):
    """Validate data, not domain authority; never skip omitted-field checks."""
    if not isinstance(payload, Mapping):
        raise TypeError("operation_result_object_required")
    pending = [payload]
    while pending:
        value = pending.pop()
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite_json")
        if isinstance(value, Mapping):
            pending.extend(value.values())
        elif isinstance(value, (list, tuple)):
            pending.extend(value)
    # Only these fields are recursively interpreted as operation summaries.
    results = [payload]
    while results:
        result = results.pop()
        if "receipts" in result:
            receipts = result["receipts"]
            if not isinstance(receipts, list) or any(
                not isinstance(receipt, Mapping) for receipt in receipts
            ):
                raise ValueError("nested_receipts_must_be_objects")
            results.extend(receipts)
        if "observation" in result and result["observation"] is not None:
            if not isinstance(result["observation"], Mapping):
                raise ValueError("nested_observation_must_be_object")
            results.append(result["observation"])


def _historical_evidence_view(value, source):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return {
        "omitted": True,
        "count": len(value) if isinstance(value, list) else None,
        "encoding": "json_sort_keys_compact_ascii_utf8",
        "sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
        "size_bytes": len(encoded),
        "source": source,
        "access": "full_json_or_saved_full_receipt",
        "availability": "not_retained_by_this_renderer",
    }


def summarize_result(payload: Mapping[str, object]) -> dict[str, object]:
    """Keep exact SDK coordinates and warnings, never infer index/acceptance state."""
    validate_presentation_input(payload)
    summary: dict[str, object] = {
        "view": "aware.issue.cli-summary.v2",
        "outcome": payload.get("outcome"),
        "operation_ref": payload.get("operation_ref"),
        "issue_ref": payload.get("issue_ref"),
        "provider_ref": payload.get("provider_ref"),
        "provider_distribution": payload.get("provider_distribution"),
        "provider_version": payload.get("provider_version"),
        "result_contract": payload.get("contract"),
        "operator_ref": payload.get("operator_ref"),
        "transaction_mode": payload.get("transaction_mode"),
        "reference_update": payload.get("reference_update"),
        "diagnostics": payload.get("diagnostics", []),
        "evidence": payload.get("evidence", []),
        "publication_receipt_ref": payload.get("publication_receipt_ref"),
        "closeout_publication_receipt_ref": payload.get(
            "closeout_publication_receipt_ref"
        ),
        "source_sha256_before": payload.get("source_sha256_before"),
        "source_sha256_after": payload.get("source_sha256_after"),
        "commit_hash": payload.get("commit_hash"),
        "currentness": payload.get("currentness"),
        "next_action": {
            "kind": "read_only_review",
            "issue_ref": payload.get("issue_ref"),
            "instruction": "Inspect full current-operation publication/failure evidence and durable Issue records; obtain fresh admission before any new effect.",
            "authorizes_retry": False,
            "restores_custody": False,
        },
        "index_result": {
            "scope": "this_operation_result_only_not_current_git_status",
            "shared_index_projection": payload.get("shared_index_projection")
            or "unknown",
            "shared_index_projection_error": payload.get(
                "shared_index_projection_error"
            ),
            "index_reconciliation_pending": (
                payload.get("index_reconciliation_pending")
                if payload.get("index_reconciliation_pending") is not None
                else "unknown"
            ),
        },
    }
    # Preserve explicit current-operation effects and cleanup, never derive them
    # from success, historical Issue evidence, or a presentation digest.
    for field in (
        "code",
        "phase",
        "provider_invoked",
        "effect",
        "provider_result",
        "provider_report_grade",
        "capture_diagnostics",
        "authorizes_retry",
        "publication_outcome",
        "effects",
        "cleanup",
        "input_cleanup",
        "input_custody",
    ):
        if field in payload:
            summary[field] = payload[field]
    projection = payload.get("projection")
    if isinstance(projection, Mapping):
        identity = projection.get("identity", {})
        content = projection.get("content", {})
        source = projection.get("source", {})
        summary["identity"] = identity
        summary["source"] = source
        if isinstance(content, Mapping):
            acceptance = content.get("acceptance_items", [])
            summary["problem"] = content.get("problem_items", [])
            summary["objective"] = content.get("goal_items", [])
            summary["scope"] = content.get("ownership_scope", [])
            summary["acceptance"] = (
                [
                    {"text": item.get("text"), "checked": item.get("checked")}
                    for item in acceptance
                    if isinstance(item, Mapping)
                ]
                if isinstance(acceptance, list)
                else []
            )
        summary["resolution"] = projection.get("resolution")
        activities = projection.get("activity", [])
        summary["latest_activity"] = (
            activities[-1] if isinstance(activities, list) and activities else None
        )
        summary["recorded_evidence"] = _historical_evidence_view(
            projection.get("evidence", []), source
        )
    if "target_paths" in payload:
        summary["scope"] = payload["target_paths"]
    if "receipts" in payload:
        receipts = payload["receipts"]
        summary["receipts"] = (
            [summarize_result(item) for item in receipts]
            if isinstance(receipts, list)
            else []
        )
        summary["atomic"] = payload.get("atomic")
    if "observation" in payload and isinstance(payload["observation"], Mapping):
        summary["observation"] = summarize_result(payload["observation"])
    return summary
