"""Opt-in presentation of SDK results; no source reads, decisions or mutations."""

from __future__ import annotations

from collections.abc import Mapping


def summarize_result(payload: Mapping[str, object]) -> dict[str, object]:
    """Keep exact SDK coordinates and warnings, never infer index/acceptance state."""
    summary: dict[str, object] = {
        "view": "aware.issue.cli-summary.v1",
        "outcome": payload.get("outcome"),
        "operation_ref": payload.get("operation_ref"),
        "issue_ref": payload.get("issue_ref"),
        "provider_ref": payload.get("provider_ref"),
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
        summary["recorded_evidence"] = projection.get("evidence", [])
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
