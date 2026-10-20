"""Concrete Goal-owner-issued introduction hold proof, not eligibility.

This primitive intentionally does not remove the direction verifier's Gate or
hold refusals. It reuses its publication/source entrance, never an echo resolver.
The initial profile conservatively refuses all post-introduction Goal touches;
semantic scope advancement and release are not supported by this primitive.
"""

from __future__ import annotations

# Exact provider composition shares internal source/publication primitives.
# pyright: reportPrivateUsage=false

import weakref
from dataclasses import dataclass
from typing import cast

from aware_goal_operational_runtime import (
    GoalLanePhaseWorkDisposition,
    GoalNativeLaneIntroductionPublicationReceiptV1,
    GoalPhaseNativeDocumentV4,
    decode_goal_native_lane_introduction_receipt,
)
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_native_lane_authority import _validated_current_issue
from aware_goal_operational_runtime.phase_native_lane_hold import (
    GoalNativeLaneHoldDecisionV1,
    exact_hold_wire,
    extract_goal_native_lane_hold_block,
)

from .native_lane_source import NativeGitLaneSource
from .phase_operation import _require_native_resolver

PROFILE = "aware.goal.git-native-lane-hold/introduction-v1"


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GitNativeLaneHoldVerificationV1:
    decision: GoalNativeLaneHoldDecisionV1
    introduction_receipt: GoalNativeLaneIntroductionPublicationReceiptV1
    decision_commit_ref: str
    decision_parent_ref: str
    decision_issue_authority: dict[str, object]
    source_goal_blob_oid: str
    source_goal_sha256: str
    selected_work_issue_source_authority: dict[str, object] | None
    selected_work_issue_authority: dict[str, object] | None
    selected_work_issue_permitted_effect_receipt_refs: tuple[str, ...]
    observed_head: str
    protected_paths: tuple[str, ...]

    def to_wire(self) -> dict[str, object]:
        def issue_wire(issue: dict[str, object] | None) -> object:
            return None if issue is None else {**issue, "scope": list(cast(tuple[str, ...], issue["scope"]))}

        body: dict[str, object] = {
            "schema_id": "aware.goal.git-native-lane-hold-verification.v1",
            "verifier_profile": PROFILE,
            "decision": self.decision.to_wire(),
            "introduction_receipt": self.introduction_receipt.to_wire(),
            "decision_commit_ref": self.decision_commit_ref,
            "decision_parent_ref": self.decision_parent_ref,
            "repository_commit_receipt_ref": "repository-commit:" + self.decision_commit_ref,
            "decision_issue_authority": issue_wire(self.decision_issue_authority),
            "source_goal_blob_oid": self.source_goal_blob_oid,
            "source_goal_sha256": self.source_goal_sha256,
            "selected_work_issue_source_authority": issue_wire(self.selected_work_issue_source_authority),
            "selected_work_issue_authority": issue_wire(self.selected_work_issue_authority),
            "selected_work_issue_permitted_effect_receipt_refs": list(self.selected_work_issue_permitted_effect_receipt_refs),
            "observed_head": self.observed_head,
            "protected_paths": list(self.protected_paths),
            "effect_profile": "read_only_non_authorizing",
            "event_effect": "none", "dispatch_effect": "none",
        }
        return {**body, "verification_ref": "goal-git-native-lane-hold-verification:" + fingerprint(body)}


_ISSUED: weakref.WeakKeyDictionary[GitNativeLaneHoldVerificationV1, str] = weakref.WeakKeyDictionary()


def require_verified_native_lane_hold(value: GitNativeLaneHoldVerificationV1) -> GitNativeLaneHoldVerificationV1:
    if type(value) is not GitNativeLaneHoldVerificationV1:
        raise ValueError("native_lane_hold_verification_unissued_or_mutated")
    try:
        valid = _ISSUED.get(value) == fingerprint(value.to_wire())
    except (ValueError, TypeError, AttributeError, KeyError) as error:
        raise ValueError("native_lane_hold_verification_unissued_or_mutated") from error
    if not valid:
        raise ValueError("native_lane_hold_verification_unissued_or_mutated")
    return value


def decode_native_lane_hold_verification(
    payload: object, *, qualified: GitNativeLaneHoldVerificationV1,
) -> GitNativeLaneHoldVerificationV1:
    qualified = require_verified_native_lane_hold(qualified)
    if not exact_hold_wire(payload, qualified.to_wire()):
        raise ValueError("native_lane_hold_transport_differs_from_authority")
    return qualified


class GitNativeLaneHoldAuthorityVerifier:
    def __init__(self, *, resolver_capability: object) -> None:
        self._source: NativeGitLaneSource = NativeGitLaneSource(
            resolver_capability=resolver_capability,
        )

    def verify(self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1) -> GitNativeLaneHoldVerificationV1:
        if type(receipt) is not GoalNativeLaneIntroductionPublicationReceiptV1:
            raise TypeError("receipt type must be exact")
        receipt = decode_goal_native_lane_introduction_receipt(receipt.to_wire())
        source = self._source
        head = source._commit("HEAD")
        commit = source._authenticate_introduction(receipt)
        if not source._ancestor(commit, head):
            raise ValueError("native_lane_hold_lineage_unproven")
        document, _, _, _ = source._snapshot(commit, receipt.goal_path)
        if type(document) is not GoalPhaseNativeDocumentV4:
            raise ValueError("lane_publication_postimage_not_v4")
        lane = next(r for r in document.native_lane_authorities if r.lane_key == receipt.lane_key)
        issue_path = receipt.publication_issue_path
        text, _ = source._regular_file(receipt.repository_parent_ref, issue_path)
        decision = extract_goal_native_lane_hold_block(text.decode("utf-8"))
        if (
            decision.goal_tag != receipt.goal_tag or decision.lane_key != receipt.lane_key
            or decision.source_document_ref != receipt.before_document_ref
            or decision.governing_issue_tag != source._issues.issue_tag_for_path(issue_path)
            or decision.owner_profile != lane.owner_profile or decision.owner_ref != lane.owner_ref
            or decision.target_state != lane.operational_state or decision.state_detail != lane.state_detail
            or decision.current_work_association_ref != lane.current_work_association_ref
            or lane.hold_authority_refs != (decision.decision_ref,)
        ):
            raise ValueError("native_lane_hold_decision_carrier_mismatch")
        revision = source._commit(decision.source_revision_ref)
        if revision != decision.source_revision_ref:
            raise ValueError("native_lane_hold_source_revision_not_exact")
        original, projected, original_bytes, original_blob = source._snapshot(revision, receipt.goal_path)
        if original.document_ref != decision.source_document_ref or original_blob != receipt.before_goal_blob_oid or source._sha(original_bytes) != receipt.before_goal_sha256:
            raise ValueError("native_lane_hold_source_mismatch")
        # Derive the actual Issue publication, never accept a relabeled commit.
        decision_commit = source._git("log", "--full-history", "-1", "--format=%H", receipt.repository_parent_ref, "--", issue_path).decode().strip()
        parents = source._parents(decision_commit)
        if len(parents) != 1 or not source._ancestor(revision, parents[0]):
            raise ValueError("native_lane_hold_decision_lineage_invalid")
        if not source._ancestor(decision_commit, receipt.repository_parent_ref):
            raise ValueError("native_lane_hold_decision_lineage_invalid")
        changed = source._git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", parents[0], decision_commit)
        if changed != issue_path.encode() + b"\0":
            raise ValueError("native_lane_hold_decision_effect_invalid")
        issue = source._issue(decision_commit, issue_path)
        previous_issue = source._issue(parents[0], issue_path)
        if any(issue[n] != previous_issue[n] for n in ("owner", "status", "scope_digest", "tag")) or (
            issue["owner"] != projected.global_authority.owner_ref
            or issue["owner"] != receipt.publication_issue_owner_execution_id
            or issue["status"] != "in_progress"
            or issue_path not in cast(tuple[str, ...], issue["scope"])
            or receipt.goal_path not in cast(tuple[str, ...], issue["scope"])
        ):
            raise ValueError("native_lane_hold_goal_owner_issuance_invalid")
        old_text, _ = source._regular_file(parents[0], issue_path)
        if "<!-- aware.goal.native-lane-hold-decision.v1:start -->" in old_text.decode("utf-8"):
            raise ValueError("native_lane_hold_decision_inherited_or_replaced")
        source._issue_effect_issuance(decision_commit, issue_path, issue, (issue_path,))
        paths = {receipt.goal_path, issue_path}
        selected_source: dict[str, object] | None = None
        selected: dict[str, object] | None = None
        permitted_effects: tuple[str, ...] = ()
        # Introduction authentication preserves the source's Phase/Work history.
        # Bind the selected Issue at that exact source epoch, not just after the
        # introduction; restored bytes cannot erase an intervening authority touch.
        for phase in original.operational_bundle.phases:
            if phase.coordinate.lane_key != lane.lane_key:
                continue
            for work in phase.work_associations:
                if work.disposition is not GoalLanePhaseWorkDisposition.CURRENT:
                    continue
                if work.association_ref != decision.current_work_association_ref:
                    raise ValueError("native_lane_hold_selected_work_source_mismatch")
                path = source._projector._resolve_issue_path(revision=revision, goal_path=receipt.goal_path, issue_ref=work.issue_ref)
                selected_source = _validated_current_issue(source._issue(revision, path), lane.owner_ref)
                if path == issue_path:
                    # The only permitted touch is this independently verified
                    # one-Issue hold decision. Protect both sides, and bind its
                    # exact pre/post Issue authority and repository receipt.
                    self._unchanged(revision, parents[0], (path,))
                    if selected_source != previous_issue:
                        raise ValueError("native_lane_hold_selected_work_source_mismatch")
                    permitted_effects = ("repository-commit:" + decision_commit,)
                else:
                    self._unchanged(revision, head, (path,))
                path = source._projector._resolve_issue_path(revision=commit, goal_path=receipt.goal_path, issue_ref=work.issue_ref)
                selected = _validated_current_issue(source._issue(commit, path), lane.owner_ref)
                if selected != (issue if permitted_effects else selected_source):
                    raise ValueError("native_lane_hold_selected_work_source_mismatch")
                paths.add(path)
        self._unchanged(revision, receipt.repository_parent_ref, (receipt.goal_path,))
        self._unchanged(decision_commit, head, (issue_path,))
        self._unchanged(commit, head, tuple(sorted(paths)))
        resolver = _require_native_resolver(source._capability)
        resolver.revalidate()
        _ = resolver.resolve_goal_path(receipt.goal_path)
        for path in sorted(paths - {receipt.goal_path}):
            source._issues.resolve_issue_path(path)
        if source._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        # No I/O or caller-provided mappings after the terminal HEAD check.
        result = GitNativeLaneHoldVerificationV1(
            decision=decision, introduction_receipt=receipt,
            decision_commit_ref=decision_commit, decision_parent_ref=parents[0],
            decision_issue_authority=issue, source_goal_blob_oid=original_blob,
            source_goal_sha256=source._sha(original_bytes),
            selected_work_issue_source_authority=selected_source,
            selected_work_issue_authority=selected, observed_head=head,
            selected_work_issue_permitted_effect_receipt_refs=permitted_effects,
            protected_paths=tuple(sorted(paths)),
        )
        _ISSUED[result] = fingerprint(result.to_wire())
        return result

    def _unchanged(self, before: str, after: str, paths: tuple[str, ...]) -> None:
        if self._source._git("log", "--full-history", "--format=%H", f"{before}..{after}", "--", *paths).strip():
            raise ValueError("native_lane_hold_protected_history_changed")
