"""Concrete evidence intake from Protocol-admitted Git.

No callback, caller evidence mapping, path inventory or claimed currentness can
issue this snapshot. Carrier Gate claims and external holds still refuse.
"""

from __future__ import annotations

# Exact adapter composition shares retained source and publication primitives.
# pyright: reportPrivateUsage=false

import weakref
from dataclasses import dataclass
from typing import cast, override

from aware_goal_operational_runtime import (
    GoalNativeLaneIntroductionPublicationReceiptV1, GoalPhaseNativeDocumentV4,
    decode_goal_native_lane_introduction_receipt, derive_goal_native_lane_semantic_closure,
)
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_native_lane_evidence import (
    GoalNativeLaneEvidenceIssuerV2, GoalNativeLaneEvidenceSnapshotV2, GoalNativeLaneQualifiedHoldV2,
    GoalNativeLaneQualifiedGateV2,
    _register_native_lane_evidence_issuer, native_lane_incident_declarations,
    require_native_lane_evidence_for_document,
)
from aware_goal_operational_runtime.phase_runtime_checks_review import (
    PROFILE as GATE_PROFILE, RuntimeChecksArtifactV2, evaluate_runtime_checks_review_v2,
    runtime_checks_selected_work,
)
from .native_lane_hold import GitNativeLaneHoldAuthorityVerifier, PROFILE, require_verified_native_lane_hold
from .runtime_checks_review import GitRuntimeChecksReviewAuthorityVerifier
from .phase_operation import _require_native_resolver


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GitNativeLaneEvidenceIssuerV2(GoalNativeLaneEvidenceIssuerV2):
    @override
    def require_snapshot(self, value: GoalNativeLaneEvidenceSnapshotV2) -> None:
        issued = _ISSUED.get(self)
        if issued is None or issued[0]() is not value:
            raise ValueError("native_lane_evidence_unissued_or_mutated")
        try:
            valid = issued[1] == fingerprint(value.to_wire())
        except (ValueError, TypeError, AttributeError, KeyError) as error:
            raise ValueError("native_lane_evidence_unissued_or_mutated") from error
        if not valid:
            raise ValueError("native_lane_evidence_unissued_or_mutated")


_ISSUED: weakref.WeakKeyDictionary[
    GitNativeLaneEvidenceIssuerV2, tuple[weakref.ReferenceType[GoalNativeLaneEvidenceSnapshotV2], str],
] = weakref.WeakKeyDictionary()
_register_native_lane_evidence_issuer(GitNativeLaneEvidenceIssuerV2)


class GitNativeLaneEvidenceVerifier:
    def __init__(self, *, resolver_capability: object) -> None:
        self._holds: GitNativeLaneHoldAuthorityVerifier = GitNativeLaneHoldAuthorityVerifier(resolver_capability=resolver_capability)
        self._checks: GitRuntimeChecksReviewAuthorityVerifier = GitRuntimeChecksReviewAuthorityVerifier(resolver_capability=resolver_capability)

    def qualify_runtime_checks(
        self, *, request_publication: RuntimeChecksArtifactV2,
        proof_publication: RuntimeChecksArtifactV2, review_publication: RuntimeChecksArtifactV2,
    ) -> GoalNativeLaneEvidenceSnapshotV2:
        """Fresh evaluator-to-snapshot join, NOT lane-publication qualification.

        Only independently resolved publication claims enter. An old or caller
        evaluation cannot be used as a substitute for current verification.
        Direction/eligibility composition and carrier Gate intake stay held.
        """
        qualified = self._checks.verify(request_publication=request_publication,
            proof_publication=proof_publication, review_publication=review_publication)
        evaluation = evaluate_runtime_checks_review_v2(qualified)
        gate = GoalNativeLaneQualifiedGateV2(qualified, evaluation)
        source = self._checks._source
        request = cast(dict[str, object], qualified.to_wire()["request"])
        verified = cast(dict[str, object], qualified.to_wire()["source_verification"])
        head = cast(str, verified["observed_source_revision_ref"])
        goal_path = cast(str, request["goal_path"])
        document, _, payload, blob = source._snapshot(head, goal_path)
        if type(document) is not GoalPhaseNativeDocumentV4 or document.document_ref != verified["observed_document_ref"]:
            raise ValueError("native_lane_gate_snapshot_document_mismatch")
        _ = runtime_checks_selected_work(document, request)
        lane_key = cast(str, cast(dict[str, object], request["coordinate"])["lane_key"])
        binding = "goal-native-lane-source:" + fingerprint({
            "document_ref": document.document_ref, "source_revision_ref": head,
            "source_blob_ref": "repository-blob:" + blob, "goal_sha256": source._sha(payload),
        })
        inventory = (
            {"profile": GATE_PROFILE, "authority": qualified.to_wire()},
            {"profile": "committed_goal_v1", "goal_tag": document.goal_tag, "path": goal_path,
                "source_revision_ref": head, "document_ref": document.document_ref,
                "blob_ref": "repository-blob:" + blob, "sha256": source._sha(payload)},
        )
        evidence = GitNativeLaneEvidenceIssuerV2()
        result = GoalNativeLaneEvidenceSnapshotV2(
            goal_tag=document.goal_tag, lane_key=lane_key, document_ref=document.document_ref,
            source_revision_ref=head, source_binding_ref=binding,
            incident_declarations=native_lane_incident_declarations(document, lane_key),
            gate_observations=(gate,), holds=(), authority_inventory=inventory, source_evidence=evidence,
        )
        # Include every verified authority target, not a caller-selected subset.
        resolver = _require_native_resolver(source._capability)
        resolver.revalidate()
        paths = {goal_path, *(cast(str, item["path"]) for item in
            cast(list[dict[str, object]], verified["authority_inventory"]))}
        for path in sorted(paths):
            if resolver.match_goal_path(path) is not None:
                _ = resolver.resolve_goal_path(path)
            if source._issues.match_issue_path(path):
                source._issues.resolve_issue_path(path)
            self._checks._target(path)
        if source._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        # No provider I/O follows terminal HEAD. Registry is identity/full-value
        # and output-lifetime bound, just as for accepted introduction holds.
        _ISSUED[evidence] = (weakref.ref(result), fingerprint(result.to_wire()))
        try:
            _ = require_native_lane_evidence_for_document(result, document=document, lane_key=lane_key)
        except (ValueError, TypeError):
            _ = _ISSUED.pop(evidence, None)
            raise
        return result

    def qualify(self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1) -> GoalNativeLaneEvidenceSnapshotV2:
        if type(receipt) is not GoalNativeLaneIntroductionPublicationReceiptV1:
            raise TypeError("receipt type must be exact")
        receipt = decode_goal_native_lane_introduction_receipt(receipt.to_wire())
        proof = require_verified_native_lane_hold(self._holds.verify(receipt))
        source = self._holds._source
        head = proof.observed_head
        document, projection, payload, blob = source._snapshot(head, receipt.goal_path)
        if type(document) is not GoalPhaseNativeDocumentV4:
            raise ValueError("native_lane_authority_absent")
        dependencies, dependency_paths, epochs = source._dependency_sources(head, document, receipt)
        issue_authorities: dict[str, dict[str, object]] = {}
        for phase in document.operational_bundle.phases:
            if phase.coordinate.lane_key != receipt.lane_key:
                continue
            if phase.gate_observations:
                raise ValueError("native_lane_gate_authority_unavailable")
            for work in phase.work_associations:
                if work.association_ref == proof.decision.current_work_association_ref:
                    path = source._projector._resolve_issue_path(
                        revision=head, goal_path=receipt.goal_path, issue_ref=work.issue_ref,
                    )
                    issue_authorities[work.issue_ref] = source._issue(head, path)
        proof_wire = proof.to_wire()
        binding = "goal-native-lane-source:" + fingerprint({
            "document_ref": document.document_ref, "source_revision_ref": head,
            "source_blob_ref": "repository-blob:" + blob, "goal_sha256": source._sha(payload),
        })
        hold = GoalNativeLaneQualifiedHoldV2(
            decision=proof.decision, verifier_profile=PROFILE, issuance_authority=proof_wire,
            evidence_source_revision_ref=proof.decision.source_revision_ref,
            observed_source_revision_ref=head, currentness_ref=cast(str, proof_wire["verification_ref"]),
        )
        paths = set(proof.protected_paths) | dependency_paths
        inventory: list[dict[str, object]] = [
            {"profile": PROFILE, "authority": proof_wire},
            {"profile": "committed_goal_v1", "goal_tag": document.goal_tag, "path": receipt.goal_path,
                "source_revision_ref": head, "document_ref": document.document_ref,
                "blob_ref": "repository-blob:" + blob, "sha256": source._sha(payload)},
        ]
        inventory.extend({"profile": "committed_goal_v1", "goal_tag": tag, "path": path,
            "source_revision_ref": revision, "document_ref": ref,
            "blob_ref": "repository-blob:" + oid, "sha256": digest}
            for revision, tag, path, ref, oid, digest in epochs if path != receipt.goal_path)
        for path in sorted(paths - {receipt.goal_path, *(epoch[2] for epoch in epochs)}):
            issue = source._issue(head, path)
            inventory.append({"profile": "committed_issue_v1", "source_revision_ref": head,
                "authority": {**issue, "scope": list(cast(tuple[str, ...], issue["scope"]))}})
        evidence = GitNativeLaneEvidenceIssuerV2()
        result = GoalNativeLaneEvidenceSnapshotV2(
            goal_tag=document.goal_tag, lane_key=receipt.lane_key, document_ref=document.document_ref,
            source_revision_ref=head, source_binding_ref=binding,
            incident_declarations=native_lane_incident_declarations(document, receipt.lane_key),
            gate_observations=(), holds=(hold,), authority_inventory=tuple(inventory), source_evidence=evidence,
        )
        resolver = _require_native_resolver(source._capability)
        resolver.revalidate()
        for path in sorted({receipt.goal_path, *(epoch[2] for epoch in epochs)}):
            _ = resolver.resolve_goal_path(path)
        for path in sorted(paths):
            if source._issues.match_issue_path(path):
                source._issues.resolve_issue_path(path)
        if source._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        # No provider I/O after terminal freshness, no plain-mapping sealer.
        _ISSUED[evidence] = (weakref.ref(result), fingerprint(result.to_wire()))
        try:
            _ = require_native_lane_evidence_for_document(result, document=document, lane_key=receipt.lane_key)
            _ = derive_goal_native_lane_semantic_closure(
                document=document, lane_key=receipt.lane_key, global_authority=projection.global_authority,
                issue_authorities=issue_authorities, dependency_sources=dependencies, evidence_snapshot=result,
            )
        except (ValueError, TypeError):
            _ = _ISSUED.pop(evidence, None)
            raise
        return result
