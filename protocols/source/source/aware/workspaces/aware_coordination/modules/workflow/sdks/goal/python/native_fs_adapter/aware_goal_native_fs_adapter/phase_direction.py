"""Protocol-admitted Git provider for read-only Phase direction receipts.

V1 receipts bind the entire committed Goal document. This provider never
substitutes Phase semantic-scope advancement for document currentness.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from typing import cast

from aware_goal_operational_runtime import (
    GoalPhaseCoordinate,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseRevisionLineageV1,
    GoalPhaseSourceBindingV1,
    decode_goal_phase_pursuit,
    issue_goal_phase_pursuit,
    verify_goal_phase_pursuit_currentness,
)
from aware_goal_sdk.phase_direction import (
    GoalPhaseDirectionCurrentnessRequestV1,
    GoalPhaseDirectionObserveRequestV1,
)

from .compatibility_source import GoalNativeScopeSourceError
from .phase_operation import NativeGitGoalPhaseOperationProvider


class NativeGitGoalPhaseDirectionProvider(NativeGitGoalPhaseOperationProvider):
    """Only a live Protocol-issued resolver capability may construct this provider."""

    def _committed_source(self, revision: str, path: str, tag: str):
        self._validate_goal_path(path, expected_goal_tag=tag)
        blob = self._regular_goal_blob(revision, path)
        source_bytes = self._git_bytes("show", f"{revision}:{path}")
        sha = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
        try:
            document, authority = self._projector.project_committed(
                revision_ref=revision,
                goal_path=path,
                expected_goal_sha256=sha,
                expected_goal_blob_oid=blob,
            )
        except GoalNativeScopeSourceError as error:
            raise ValueError(error.code) from error
        if type(document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}:
            raise ValueError("native_phase_v2_or_v3_required")
        if document.goal_tag != tag or not self._is_unique_goal_source(revision, tag, path):
            raise ValueError("native_goal_identity_mismatch_or_ambiguous")
        binding = GoalPhaseSourceBindingV1(
            repository_revision_ref=revision, goal_sha256=sha, goal_blob_oid=blob
        )
        return document, authority, binding

    def observe_phase_direction(
        self, request: GoalPhaseDirectionObserveRequestV1
    ) -> dict[str, object]:
        request.__post_init__()
        head = self._git_text("rev-parse", "--verify", "HEAD^{commit}")
        document, authority, binding = self._committed_source(
            head, request.goal_path, request.goal_tag
        )
        if not any(lane.lane_key == request.lane_key for lane in authority.lane_authorities):
            raise ValueError("lane_authority_absent")
        receipt = issue_goal_phase_pursuit(
            document=document,
            coordinate=GoalPhaseCoordinate(
                request.goal_tag, request.lane_key, request.phase_key
            ),
            source=binding,
            expected_document_ref=document.document_ref,
        )
        self._before_success()
        if self._git_text("rev-parse", "--verify", "HEAD^{commit}") != head:
            raise ValueError("repository_head_advanced")
        return receipt.to_wire()

    def verify_phase_direction_currentness(
        self, request: GoalPhaseDirectionCurrentnessRequestV1
    ) -> dict[str, object]:
        request.__post_init__()
        supplied = request.expected_receipt
        if type(supplied) is not dict:
            raise ValueError("phase_direction_receipt_invalid")
        raw = cast(dict[str, object], supplied)
        if type(raw.get("source")) is not dict:
            raise ValueError("phase_direction_receipt_invalid")
        source = cast(dict[str, object], raw["source"])
        revision = source.get("repository_revision_ref")
        coordinate_value = raw.get("coordinate")
        if (
            type(revision) is not str
            or re.fullmatch(r"[0-9a-f]{40}", revision) is None
            or type(coordinate_value) is not dict
        ):
            raise ValueError("phase_direction_receipt_invalid")
        if self._git_text("rev-parse", "--verify", revision + "^{commit}") != revision:
            raise ValueError("historical_revision_unavailable")
        coordinate = cast(dict[str, object], coordinate_value)
        tag = coordinate.get("goal_tag")
        if type(tag) is not str:
            raise ValueError("phase_direction_receipt_invalid")
        # Independently reconstruct the retained receipt from its historical
        # committed source. A re-digested caller object is not authority.
        historical, _, historical_binding = self._committed_source(
            revision, request.goal_path, tag
        )
        expected = decode_goal_phase_pursuit(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode(),
            document=historical,
            source=historical_binding,
        )
        head = self._git_text("rev-parse", "--verify", "HEAD^{commit}")
        observed, _, observed_binding = self._committed_source(
            head, request.goal_path, tag
        )
        if revision == head:
            relation = "equal"
        else:
            ancestry = subprocess.run(
                ("git", "merge-base", "--is-ancestor", revision, head),
                cwd=self._root, capture_output=True, check=False,
            )
            if ancestry.returncode not in {0, 1}:
                raise ValueError("repository_lineage_unavailable")
            relation = "descendant" if ancestry.returncode == 0 else "unproven"
        lineage = GoalPhaseRevisionLineageV1(
            expected_revision_ref=revision,
            observed_revision_ref=head,
            relation=relation,
        )
        result = verify_goal_phase_pursuit_currentness(
            expected=expected,
            observed_document=observed,
            observed_source=observed_binding,
            revision_lineage=lineage,
        )
        self._before_success()
        if self._git_text("rev-parse", "--verify", "HEAD^{commit}") != head:
            raise ValueError("repository_head_advanced")
        return result.to_wire()
