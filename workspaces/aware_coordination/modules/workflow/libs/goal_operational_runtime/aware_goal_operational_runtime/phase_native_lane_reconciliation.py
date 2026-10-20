"""Strict projection-result transport, not publication or currentness authority.

Only a concrete repository operation can authenticate the retained receipt.
Decoding this value never qualifies a lane, Gate, actor or eligibility result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import cast

from .identity import fingerprint
from .phase_native_lane_authority import (
    GoalNativeLaneIntroductionPublicationReceiptV1,
    decode_goal_native_lane_introduction_receipt,
)

SCHEMA = "aware.goal.native-lane-projection-reconciliation.v1"
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class GoalNativeLaneProjectionReconciliationV1:
    publication_receipt: GoalNativeLaneIntroductionPublicationReceiptV1
    observed_head: str
    reconciliation_issue_path: str
    reconciliation_issue_blob_oid: str
    reconciliation_execution_id: str
    reconciliation_issue_scope_digest: str
    protocol_manifest_sha256: str
    index_blob_oid: str
    worktree_sha256: str
    disposition: str
    dry_run: bool
    receipt_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalNativeLaneProjectionReconciliationV1:
            raise TypeError("lane reconciliation type must be exact")
        if type(self.publication_receipt) is not GoalNativeLaneIntroductionPublicationReceiptV1:
            raise TypeError("lane reconciliation requires the complete publication receipt")
        retained = decode_goal_native_lane_introduction_receipt(self.publication_receipt.to_wire())
        for name in ("observed_head", "reconciliation_issue_blob_oid", "index_blob_oid"):
            value = getattr(self, name)
            if type(value) is not str or not _OID.fullmatch(value):
                raise ValueError("lane_reconciliation_oid_invalid")
        for name in ("reconciliation_issue_scope_digest", "protocol_manifest_sha256", "worktree_sha256"):
            value = getattr(self, name)
            if type(value) is not str or not _SHA.fullmatch(value):
                raise ValueError("lane_reconciliation_sha_invalid")
        path = self.reconciliation_issue_path
        if type(path) is not str or any(part in {"", ".", ".."} for part in path.split("/")) or ":" in path or "\\" in path or any(ord(c) < 32 for c in path):
            raise ValueError("lane_reconciliation_issue_path_invalid")
        actor = self.reconciliation_execution_id
        if type(actor) is not str or not actor or actor.strip() != actor or any(ord(c) < 32 for c in actor):
            raise ValueError("lane_reconciliation_execution_invalid")
        if type(self.dry_run) is not bool or type(self.disposition) is not str:
            raise TypeError("lane reconciliation wire types must be exact")
        if self.index_blob_oid != retained.after_goal_blob_oid:
            raise ValueError("lane_reconciliation_index_not_postimage")
        if self.disposition == "current":
            if self.worktree_sha256 != retained.after_goal_sha256:
                raise ValueError("lane_reconciliation_current_without_postimage")
        elif self.disposition in {"planned", "reconciliation_required"}:
            if self.worktree_sha256 != retained.before_goal_sha256 or (
                self.disposition == "planned" and not self.dry_run
            ) or (self.disposition == "reconciliation_required" and self.dry_run):
                raise ValueError("lane_reconciliation_stale_disposition_invalid")
        else:
            raise ValueError("lane_reconciliation_disposition_invalid")
        object.__setattr__(self, "receipt_ref", "goal-native-lane-projection-reconciliation:" + fingerprint(self.to_wire(include_ref=False)))

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {"schema_id": SCHEMA,
            "publication_receipt": self.publication_receipt.to_wire(),
            "observed_head": self.observed_head,
            "reconciliation_issue_path": self.reconciliation_issue_path,
            "reconciliation_issue_blob_oid": self.reconciliation_issue_blob_oid,
            "reconciliation_execution_id": self.reconciliation_execution_id,
            "reconciliation_issue_scope_digest": self.reconciliation_issue_scope_digest,
            "protocol_manifest_sha256": self.protocol_manifest_sha256,
            "index_blob_oid": self.index_blob_oid, "worktree_sha256": self.worktree_sha256,
            "disposition": self.disposition, "dry_run": self.dry_run}
        return {**body, "receipt_ref": self.receipt_ref} if include_ref else body


def decode_goal_native_lane_projection_reconciliation(payload: bytes | dict[str, object]) -> GoalNativeLaneProjectionReconciliationV1:
    """Strict structural decode; source authenticity must be independently verified."""
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("lane_reconciliation_duplicate_field")
            result[key] = value
        return result
    raw: object = json.loads(payload.decode("utf-8"), object_pairs_hook=unique) if type(payload) is bytes else payload
    names = {"publication_receipt", "observed_head", "reconciliation_issue_path",
        "reconciliation_issue_blob_oid", "reconciliation_execution_id",
        "reconciliation_issue_scope_digest", "protocol_manifest_sha256",
        "index_blob_oid", "worktree_sha256", "disposition", "dry_run"}
    if type(raw) is not dict:
        raise TypeError("lane reconciliation must be an exact object")
    body = cast(dict[str, object], raw)
    if set(body) != names | {"schema_id", "receipt_ref"} or body["schema_id"] != SCHEMA:
        raise ValueError("lane_reconciliation_fields_invalid")
    receipt = decode_goal_native_lane_introduction_receipt(cast(dict[str, object], body["publication_receipt"]))
    if any(type(body[k]) is not str for k in names - {"publication_receipt", "dry_run"}):
        raise TypeError("lane reconciliation strings must be exact")
    value = GoalNativeLaneProjectionReconciliationV1(publication_receipt=receipt,
        observed_head=cast(str, body["observed_head"]),
        reconciliation_issue_path=cast(str, body["reconciliation_issue_path"]),
        reconciliation_issue_blob_oid=cast(str, body["reconciliation_issue_blob_oid"]),
        reconciliation_execution_id=cast(str, body["reconciliation_execution_id"]),
        reconciliation_issue_scope_digest=cast(str, body["reconciliation_issue_scope_digest"]),
        protocol_manifest_sha256=cast(str, body["protocol_manifest_sha256"]),
        index_blob_oid=cast(str, body["index_blob_oid"]), worktree_sha256=cast(str, body["worktree_sha256"]),
        disposition=cast(str, body["disposition"]), dry_run=cast(bool, body["dry_run"]))
    if value.receipt_ref != body["receipt_ref"]:
        raise ValueError("lane_reconciliation_digest_invalid")
    return value
