"""Transport consistency is not repository/Issue authentication."""
from dataclasses import replace
import json

import pytest
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_native_lane_reconciliation import (
    GoalNativeLaneProjectionReconciliationV1, decode_goal_native_lane_projection_reconciliation,
)
from test_phase_native_lane_authority import _transition


def _result(*, current=True):
    _, _, publication = _transition()
    return GoalNativeLaneProjectionReconciliationV1(publication_receipt=publication,
        observed_head=publication.repository_commit_ref,
        reconciliation_issue_path="customer/issues/2026/10/01/fb-2026-10-01-reconcile.md",
        reconciliation_issue_blob_oid="1" * 40,
        reconciliation_execution_id="codex-proof", reconciliation_issue_scope_digest="sha256:" + "2" * 64,
        protocol_manifest_sha256="sha256:" + "3" * 64, index_blob_oid=publication.after_goal_blob_oid,
        worktree_sha256=publication.after_goal_sha256 if current else publication.before_goal_sha256,
        disposition="current" if current else "planned", dry_run=not current)


@pytest.mark.parametrize("current", [False, True])
def test_transport_round_trip_retains_complete_publication(current):
    result = _result(current=current)
    decoded = decode_goal_native_lane_projection_reconciliation(json.dumps(result.to_wire()).encode())
    assert decoded == result
    assert decoded.to_wire()["publication_receipt"] == result.publication_receipt.to_wire()


@pytest.mark.parametrize("change", ["false_current", "foreign_index", "extra", "unknown", "bool", "digest", "publication"])
def test_redigested_contradictions_refuse(change):
    result = _result()
    wire = result.to_wire()
    if change == "false_current": wire["worktree_sha256"] = result.publication_receipt.before_goal_sha256
    elif change == "foreign_index": wire["index_blob_oid"] = "e" * 40
    elif change == "extra": wire["extra"] = True
    elif change == "unknown": wire["disposition"] = "running"
    elif change == "bool": wire["dry_run"] = 1
    elif change == "publication": wire["publication_receipt"] = {**result.publication_receipt.to_wire(), "lane_key": "foreign"}
    else: wire["observed_head"] = "c" * 40
    if change != "digest":
        wire["receipt_ref"] = "goal-native-lane-projection-reconciliation:" + fingerprint({k: v for k, v in wire.items() if k != "receipt_ref"})
    with pytest.raises((TypeError, ValueError)):
        decode_goal_native_lane_projection_reconciliation(wire)


def test_stale_non_dry_result_and_constructor_laws():
    result = _result(current=False)
    assert replace(result, disposition="reconciliation_required", dry_run=False).disposition == "reconciliation_required"
    with pytest.raises(ValueError):
        replace(result, dry_run=False)
    wire = json.dumps(_result().to_wire())
    with pytest.raises(ValueError, match="duplicate"):
        decode_goal_native_lane_projection_reconciliation(wire.replace('"dry_run": false', '"dry_run": false, "dry_run": false').encode())
