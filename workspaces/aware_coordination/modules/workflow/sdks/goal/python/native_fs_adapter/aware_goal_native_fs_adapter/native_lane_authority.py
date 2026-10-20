"""Concrete, Protocol-admitted Git proof of native lane publication/history.

This is source authentication, not an eligibility reducer. No caller callbacks,
claimed HEAD, path inventory, or currentness booleans enter this verifier.
"""

from __future__ import annotations

# Adapter modules share these internal Protocol/projector primitives; they are
# not public callback or authority construction entrances.
# pyright: reportPrivateUsage=false

import weakref
from dataclasses import dataclass
from typing import cast, override

from aware_goal_operational_runtime import (
    GoalLanePhaseWorkDisposition,
    GoalNativeLaneIntroductionPublicationReceiptV1,
    GoalNativeLaneDirectionAuthorityV1,
    GoalPhaseNativeDocumentV4,
    decode_goal_native_lane_introduction_receipt,
    derive_goal_native_lane_semantic_closure,
    reduce_goal_native_lane_scope_history,
)
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_native_lane_evidence import (
    GoalNativeLaneEvidenceSnapshotV2, require_native_lane_evidence_for_document,
    require_native_lane_gate_issue_effect,
)
from aware_goal_operational_runtime.phase_runtime_checks_review import RuntimeChecksArtifactV2
from aware_goal_operational_runtime.phase_native_lane_authority import (
    GoalNativeLaneDirectionEvidenceV1, GoalNativeLanePublicationError,
    _direction_fingerprint, _register_goal_native_lane_evidence_type,
    _validate_goal_native_lane_direction,
)

from .compatibility_source import _compatibility_relation
from .phase_operation import _require_native_resolver
from .native_lane_source import NativeGitLaneSource

PROJECTOR = "aware.goal.git-native-lane-authority/v1"


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GitNativeLaneVerificationV1:
    """Provider observation; only an issued, unmodified instance is verified."""

    goal_tag: str
    lane_key: str
    publication_ref: str
    introduction_commit: str
    observed_head: str
    document_ref: str
    goal_blob_oid: str
    goal_sha256: str
    origin_closure_ref: str
    current_closure_ref: str
    protected_paths: tuple[str, ...]
    history_edges: tuple[tuple[str, str, str, str], ...]
    status: str
    projection_currentness: str
    replay_disposition: str
    reasons: tuple[str, ...]
    dependency_source_epochs: tuple[tuple[str, str, str, str, str, str], ...]
    evidence_snapshot_ref: str | None = None
    qualified_issue_effects: tuple[tuple[str, str, str, str, str, str], ...] = ()

    def to_wire(self) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": ("aware.goal.git-native-lane-verification.v1" if self.evidence_snapshot_ref is None
                else "aware.goal.git-native-lane-verification.v2"),
            "projector_ref": PROJECTOR,
            "goal_tag": self.goal_tag, "lane_key": self.lane_key,
            "publication_ref": self.publication_ref,
            "introduction_commit": self.introduction_commit,
            "observed_head": self.observed_head,
            "document_ref": self.document_ref,
            "goal_blob_oid": self.goal_blob_oid, "goal_sha256": self.goal_sha256,
            "origin_closure_ref": self.origin_closure_ref,
            "current_closure_ref": self.current_closure_ref,
            "protected_paths": list(self.protected_paths),
            "history_edges": [list(edge) for edge in self.history_edges],
            "status": self.status,
            "projection_currentness": self.projection_currentness,
            "replay_disposition": self.replay_disposition,
            "reasons": list(self.reasons),
            "dependency_source_epochs": [list(epoch) for epoch in self.dependency_source_epochs],
        }
        if self.evidence_snapshot_ref is not None:
            body["evidence_snapshot_ref"] = self.evidence_snapshot_ref
        if self.qualified_issue_effects:
            body["qualified_issue_effects"] = [list(effect) for effect in self.qualified_issue_effects]
        return body

    @property
    def verification_ref(self) -> str:
        return "goal-git-native-lane-verification:" + fingerprint(self.to_wire())


# Lifetime follows the actual output object; fingerprints cannot be recomputed
# by mutating its fields. There is deliberately no public registration entrance.
_VERIFIED: weakref.WeakKeyDictionary[GitNativeLaneVerificationV1, str] = (
    weakref.WeakKeyDictionary()
)


def require_verified_git_native_lane(
    value: GitNativeLaneVerificationV1,
) -> GitNativeLaneVerificationV1:
    if type(value) is not GitNativeLaneVerificationV1 or (
        _VERIFIED.get(value) != fingerprint(value.to_wire())
    ):
        raise ValueError("native_lane_verification_unissued_or_mutated")
    return value


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GitNativeLaneDirectionEvidenceV1(GoalNativeLaneDirectionEvidenceV1):
    """Opaque issuance witness; constructor/copy does not enter the registry."""

    verification_ref: str

    @override
    def require_direction(self, value: GoalNativeLaneDirectionAuthorityV1) -> None:
        issued = _DIRECTION_ISSUED.get(self)
        if issued is None or issued[0]() is not value or self.verification_ref != value.scope_currentness_ref:
            raise GoalNativeLanePublicationError("native_lane_direction_unissued_or_mutated")
        try:
            current = _direction_fingerprint(value)
        except (ValueError, TypeError, AttributeError, StopIteration, KeyError) as error:
            raise GoalNativeLanePublicationError("native_lane_direction_unissued_or_mutated") from error
        if issued[1] != current:
            raise GoalNativeLanePublicationError("native_lane_direction_unissued_or_mutated")


_DIRECTION_ISSUED: weakref.WeakKeyDictionary[
    GitNativeLaneDirectionEvidenceV1, tuple[weakref.ReferenceType[GoalNativeLaneDirectionAuthorityV1], str],
] = weakref.WeakKeyDictionary()
_register_goal_native_lane_evidence_type(GitNativeLaneDirectionEvidenceV1)


class NativeGitLaneAuthorityVerifier(NativeGitLaneSource):
    """Joined publication/HEAD/history verification from retained Protocol authority."""


    def verify(
        self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
    ) -> GitNativeLaneVerificationV1:
        """Authenticate origin, then reproject every intervening repository edge."""
        return self._verify(receipt, self._qualify_evidence(receipt))

    def _qualify_evidence(self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1) -> GoalNativeLaneEvidenceSnapshotV2 | None:
        if type(receipt) is not GoalNativeLaneIntroductionPublicationReceiptV1:
            raise TypeError("receipt type must be exact")
        receipt = decode_goal_native_lane_introduction_receipt(receipt.to_wire())
        document, _, _, _ = self._snapshot(receipt.repository_commit_ref, receipt.goal_path)
        if type(document) is GoalPhaseNativeDocumentV4:
            lane = next((r for r in document.native_lane_authorities if r.lane_key == receipt.lane_key), None)
            if lane is not None and lane.hold_authority_refs:
                # Concrete provider-owned source verification, not a callback
                # mapping or a caller-supplied hold. Import avoids composition
                # cycles with the introduction-hold verifier's shared sources.
                from .native_lane_evidence import GitNativeLaneEvidenceVerifier
                return GitNativeLaneEvidenceVerifier(resolver_capability=self._capability).qualify(receipt)
        return None

    def _verify(
        self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
        evidence_snapshot: GoalNativeLaneEvidenceSnapshotV2 | None,
    ) -> GitNativeLaneVerificationV1:

        if type(receipt) is not GoalNativeLaneIntroductionPublicationReceiptV1:
            raise TypeError("receipt type must be exact")
        # A mutated object's stale derived identity must not be repaired in place.
        receipt = decode_goal_native_lane_introduction_receipt(receipt.to_wire())
        resolver = _require_native_resolver(self._capability)
        head = self._commit("HEAD")
        if evidence_snapshot is not None and evidence_snapshot.source_revision_ref != head:
            raise ValueError("repository_head_advanced")
        commit = self._authenticate_introduction(receipt)
        issue_effects = self._verify_gate_issue_effects(commit, head, evidence_snapshot)
        origin, origin_paths, origin_epochs = self._closure(commit, receipt, evidence_snapshot)
        if evidence_snapshot is not None:
            # Complete issued authority inventory, not caller-selected paths.
            for item in evidence_snapshot.authority_inventory:
                if item.get("profile") == "committed_issue_v1":
                    origin_paths.add(cast(str, cast(dict[str, object], item["authority"])["path"]))
            for gate in evidence_snapshot.gate_observations:
                inputs = gate.evaluator_input.to_wire()
                request = cast(dict[str, object], inputs["request"])
                if request["goal_path"] != receipt.goal_path:
                    raise ValueError("native_lane_gate_goal_path_mismatch")
                verified = cast(dict[str, object], inputs["source_verification"])
                for item in cast(list[dict[str, object]], verified["authority_inventory"]):
                    origin_paths.add(cast(str, item["path"]))
        current_document, _, current_bytes, current_blob = self._snapshot(head, receipt.goal_path)
        if evidence_snapshot is not None and evidence_snapshot.gate_observations:
            if type(current_document) is not GoalPhaseNativeDocumentV4:
                raise ValueError("native_lane_authority_absent")
            _ = require_native_lane_evidence_for_document(evidence_snapshot,
                document=current_document, lane_key=receipt.lane_key)
            if evidence_snapshot.source_binding_ref != "goal-native-lane-source:" + fingerprint({
                "document_ref": current_document.document_ref, "source_revision_ref": head,
                "source_blob_ref": "repository-blob:" + current_blob, "goal_sha256": self._sha(current_bytes),
            }):
                raise ValueError("native_lane_gate_source_binding_mismatch")
        origin_ref = "goal-native-lane-semantic-closure:" + fingerprint(origin)
        edges: list[tuple[str, str, str, str]] = []
        paths = set(origin_paths)
        source_epochs = set(origin_epochs)
        relations: list[str] = []
        current_ref = origin_ref
        lineage = "unproven"
        if self._ancestor(commit, head):
            lineage = "equal" if commit == head else "descendant"
            current, current_paths, current_epochs = self._closure(head, receipt, evidence_snapshot)
            source_epochs.update(current_epochs)
            current_ref = "goal-native-lane-semantic-closure:" + fingerprint(current)
            paths.update(current_paths)
            for left, right in self._history_edges(commit, head):
                a, a_paths, a_epochs = self._closure(left, receipt, evidence_snapshot)
                b, b_paths, b_epochs = self._closure(right, receipt, evidence_snapshot)
                source_epochs.update(a_epochs)
                source_epochs.update(b_epochs)
                paths.update(a_paths)
                paths.update(b_paths)
                a_ref = "goal-native-lane-semantic-closure:" + fingerprint(a)
                b_ref = "goal-native-lane-semantic-closure:" + fingerprint(b)
                edges.append((left, right, a_ref, b_ref))
                # Classify every participating Goal, not just the dependent
                # carrier. An unknown external compatibility delta is also
                # ambiguous, even when both endpoint digests can be read.
                goal_paths = {receipt.goal_path, *(epoch[2] for epoch in (*a_epochs, *b_epochs))}
                edge_relations: set[str] = set()
                for path in sorted(goal_paths):
                    _, pa, _, _ = self._snapshot(left, path)
                    _, pb, _, _ = self._snapshot(right, path)
                    edge_relations.add(_compatibility_relation(pa, pb).value)
                relations.append(next(r for r in (
                    "unknown", "decoded_authority_change", "allowlisted_append", "exact",
                ) if r in edge_relations))
        status, projection, replay, reasons = reduce_goal_native_lane_scope_history(
            lineage=lineage, origin_closure_ref=origin_ref, current_closure_ref=current_ref,
            effect_closure_pairs=tuple((e[2], e[3]) for e in edges),
            compatibility_relations=tuple(relations),
        )
        resolver.revalidate()
        if self._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        # Committed bytes do not qualify the concrete source target. Recheck
        # every participating Goal, including sources only seen earlier in
        # history, after the terminal repository observation and before seal.
        for goal_path in sorted({receipt.goal_path, *(epoch[2] for epoch in source_epochs)}):
            _ = resolver.resolve_goal_path(goal_path)
        self._recheck_evidence_targets(evidence_snapshot, paths)
        # Target resolution itself performs provider I/O. Do not seal the old
        # source epoch if HEAD advanced while those terminal checks ran.
        if self._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        result = GitNativeLaneVerificationV1(
            goal_tag=receipt.goal_tag, lane_key=receipt.lane_key,
            publication_ref=receipt.receipt_ref, introduction_commit=commit,
            observed_head=head, document_ref=current_document.document_ref,
            goal_blob_oid=current_blob, goal_sha256=self._sha(current_bytes),
            origin_closure_ref=origin_ref, current_closure_ref=current_ref,
            protected_paths=tuple(sorted(paths)), history_edges=tuple(edges),
            status=status, projection_currentness=projection,
            replay_disposition=replay, reasons=reasons,
            dependency_source_epochs=tuple(sorted(source_epochs)),
            evidence_snapshot_ref=None if evidence_snapshot is None else cast(str, evidence_snapshot.to_wire()["snapshot_ref"]),
            qualified_issue_effects=issue_effects,
        )
        _VERIFIED[result] = fingerprint(result.to_wire())
        return result

    def _verify_gate_issue_effects(
        self, introduction: str, head: str, snapshot: GoalNativeLaneEvidenceSnapshotV2 | None,
    ) -> tuple[tuple[str, str, str, str, str, str], ...]:
        if snapshot is None or not snapshot.gate_observations:
            return ()
        paths = {cast(str, cast(dict[str, object], cast(dict[str, object], gate.evaluator_input.to_wire()["request"])["implementation_publication"])["governing_issue_path"])
            for gate in snapshot.gate_observations}
        effects: list[tuple[str, str, str, str, str, str]] = []
        # Include every merge parent; no first-parent or endpoint-only shortcut.
        for parent, child in self._history_edges(introduction, head):
            for path in sorted(paths):
                if not self._git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", parent, child, "--", path):
                    continue
                _, before = self._regular_file(parent, path)
                _, after = self._regular_file(child, path)
                if self._parents(child) != (parent,):
                    raise ValueError("native_lane_gate_issue_effect_unqualified")
                authority_ref = require_native_lane_gate_issue_effect(snapshot, issue_path=path,
                    parent_ref=parent, commit_ref=child, before_blob_ref=before, after_blob_ref=after)
                effects.append((path, parent, child, before, after, authority_ref))
        return tuple(effects)


    def qualify_direction(
        self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
    ) -> GoalNativeLaneDirectionAuthorityV1:
        """Fresh joined source/provenance entrance; no eligibility interpretation.

        The accepted verifier covers every scope edge. Restored input facts are
        rejoined to that exact verified output before the final target/HEAD check
        and neutral handoff. A retained verification alone is not currentness.
        """
        if type(receipt) is not GoalNativeLaneIntroductionPublicationReceiptV1:
            raise TypeError("receipt type must be exact")
        receipt = decode_goal_native_lane_introduction_receipt(receipt.to_wire())
        evidence_snapshot = self._qualify_evidence(receipt)
        return self._qualify_direction(receipt, evidence_snapshot)

    def qualify_runtime_checks_direction(
        self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1, *,
        request_publication: RuntimeChecksArtifactV2,
        proof_publication: RuntimeChecksArtifactV2,
        review_publication: RuntimeChecksArtifactV2,
    ) -> GoalNativeLaneDirectionAuthorityV1:
        """Fresh concrete source verification; never accepts a transported snapshot."""
        from .native_lane_evidence import GitNativeLaneEvidenceVerifier
        snapshot = GitNativeLaneEvidenceVerifier(resolver_capability=self._capability).qualify_runtime_checks(
            request_publication=request_publication, proof_publication=proof_publication,
            review_publication=review_publication,
        )
        return self._qualify_direction(receipt, snapshot)

    def _recheck_evidence_targets(
        self, snapshot: GoalNativeLaneEvidenceSnapshotV2 | None, paths: set[str],
    ) -> None:
        if snapshot is not None and snapshot.gate_observations:
            from .runtime_checks_review import GitRuntimeChecksReviewAuthorityVerifier
            verifier = GitRuntimeChecksReviewAuthorityVerifier(resolver_capability=self._capability)
            for path in sorted(paths):
                verifier._target(path)

    def _qualify_direction(
        self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
        evidence_snapshot: GoalNativeLaneEvidenceSnapshotV2 | None,
    ) -> GoalNativeLaneDirectionAuthorityV1:
        verification = require_verified_git_native_lane(self._verify(receipt, evidence_snapshot))
        if verification.status != "current":
            raise ValueError("native_lane_scope_not_current")
        head = verification.observed_head
        document, projection, payload, blob = self._snapshot(head, receipt.goal_path)
        if type(document) is not GoalPhaseNativeDocumentV4:
            raise ValueError("native_lane_authority_absent")
        issue_authorities: dict[str, dict[str, object]] = {}
        for phase in document.operational_bundle.phases:
            if phase.coordinate.lane_key != receipt.lane_key:
                continue
            for work in phase.work_associations:
                if work.disposition is GoalLanePhaseWorkDisposition.CURRENT:
                    path = self._projector._resolve_issue_path(
                        revision=head, goal_path=receipt.goal_path, issue_ref=work.issue_ref,
                    )
                    issue_authorities[work.issue_ref] = self._issue(head, path)
        dependencies, _, epochs = self._dependency_sources(head, document, receipt)
        closure = derive_goal_native_lane_semantic_closure(
            document=document, lane_key=receipt.lane_key, global_authority=projection.global_authority,
            issue_authorities=issue_authorities, dependency_sources=dependencies,
            evidence_snapshot=evidence_snapshot,
        )
        if (
            document.document_ref != verification.document_ref
            or blob != verification.goal_blob_oid
            or self._sha(payload) != verification.goal_sha256
            or "goal-native-lane-semantic-closure:" + fingerprint(closure) != verification.current_closure_ref
            or any(epoch not in verification.dependency_source_epochs for epoch in epochs)
        ):
            raise ValueError("native_lane_verified_snapshot_mismatch")
        resolver = _require_native_resolver(self._capability)
        resolver.revalidate()
        for goal_path in sorted({receipt.goal_path, *(epoch[2] for epoch in verification.dependency_source_epochs)}):
            _ = resolver.resolve_goal_path(goal_path)
        for path in sorted({receipt.publication_issue_path, *verification.protected_paths}):
            if self._issues.match_issue_path(path):
                self._issues.resolve_issue_path(path)
        self._recheck_evidence_targets(evidence_snapshot, set(verification.protected_paths))
        if self._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        # No provider I/O follows the final HEAD check. Neutral validation is
        # pure; only this concrete provider registers the issued snapshot.
        evidence = GitNativeLaneDirectionEvidenceV1(verification.verification_ref)
        result = GoalNativeLaneDirectionAuthorityV1(
            document=document, global_authority=projection.global_authority, lane_key=receipt.lane_key,
            issue_authorities=issue_authorities, dependency_sources=dependencies,
            source_blob_ref="repository-blob:" + blob, goal_sha256=self._sha(payload),
            publication_ref=verification.publication_ref, scope_currentness_ref=verification.verification_ref,
            semantic_closure_ref=verification.current_closure_ref, projector_ref=PROJECTOR,
            source_evidence=evidence,
            evidence_snapshot=evidence_snapshot,
        )
        _validate_goal_native_lane_direction(result)
        _DIRECTION_ISSUED[evidence] = (weakref.ref(result), _direction_fingerprint(result))
        return result

    def _closure(
        self, revision: str, receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
        evidence_snapshot: GoalNativeLaneEvidenceSnapshotV2 | None = None,
    ) -> tuple[dict[str, object], set[str], tuple[tuple[str, str, str, str, str, str], ...]]:
        document, projected, _, _ = self._snapshot(revision, receipt.goal_path)
        if type(document) is not GoalPhaseNativeDocumentV4:
            raise ValueError("native_lane_authority_absent")
        paths = {receipt.goal_path}
        issue_authorities: dict[str, dict[str, object]] = {}
        for phase in document.operational_bundle.phases:
            if phase.coordinate.lane_key != receipt.lane_key:
                continue
            for work in phase.work_associations:
                if work.disposition is not GoalLanePhaseWorkDisposition.CURRENT:
                    continue
                path = self._projector._resolve_issue_path(
                    revision=revision, goal_path=receipt.goal_path, issue_ref=work.issue_ref,
                )
                issue = self._issue(revision, path)
                paths.add(path)
                issue_authorities[work.issue_ref] = issue
        dependency_sources, dependency_paths, source_epochs = self._dependency_sources(
            revision, document, receipt,
        )
        paths.update(dependency_paths)
        return derive_goal_native_lane_semantic_closure(
            document=document, lane_key=receipt.lane_key,
            global_authority=projected.global_authority,
            issue_authorities=issue_authorities,
            dependency_sources=dependency_sources,
            evidence_snapshot=(evidence_snapshot if evidence_snapshot is None or not evidence_snapshot.gate_observations else None),
            gate_history_evidence=(evidence_snapshot if evidence_snapshot is not None and evidence_snapshot.gate_observations else None),
        ), paths, source_epochs
