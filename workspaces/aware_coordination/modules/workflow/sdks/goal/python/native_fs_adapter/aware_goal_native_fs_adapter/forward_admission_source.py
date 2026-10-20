"""Concrete Git/Protocol admission verification; no callback authority issuers."""
# pyright: reportPrivateUsage=false
from __future__ import annotations

import json
import weakref
from dataclasses import dataclass, replace
from typing import cast

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_contracts import GoalLanePhaseWorkDisposition, GoalPhaseCoordinate
from aware_goal_operational_runtime.phase_dependency_endpoint_context import (
    dependency_endpoint_scope_profile, derive_absent_lane_endpoint_context,
    derive_dependency_endpoint_context, validate_forward_admission_direction,
)
from aware_goal_operational_runtime.phase_forward_admission import (
    Document, GoalPhaseOperationalAdmissionPlanV2, GoalPhaseOperationalAdmissionRequestV2,
    GoalPhaseOperationalAdmissionPublicationV2, PUBLICATION_SCHEMA,
    checked_forward_document, decode_forward_admission_request, document_wire,
    decode_forward_admission_publication, forward_publication_intent,
    forward_plan_wire, plan_existing_definition_admission,
)
from aware_goal_operational_runtime.phase_document import attach_goal_phase_native_carrier, extract_goal_phase_native_carrier
from aware_goal_operational_runtime.phase_frontier import goal_phase_dependency_digest
from aware_goal_operational_runtime.phase_native_scope_advancement import GoalLaneDirectionAuthorityV1
from .native_lane_source import NativeGitLaneSource
from .phase_operation import _require_native_resolver


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class VerifiedForwardAdmissionV2:
    plan: GoalPhaseOperationalAdmissionPlanV2
    goal_path: str
    publication_issue_path: str
    publication_issue: dict[str, object]
    selected_issue: dict[str, object]
    source_head: str
    observed_head: str
    before_bytes: bytes
    before_blob: str
    dependency_contexts: tuple[dict[str, object], ...]
    protected_paths: tuple[str, ...]
    goal_paths: tuple[str, ...]
    issue_paths: tuple[str, ...]
    protocol_sha256: str

    def to_wire(self) -> dict[str, object]:
        return {"schema_id": "aware.goal.git-forward-admission-verification.v2",
            "plan": forward_plan_wire(self.plan), "goal_path": self.goal_path,
            "publication_issue_path": self.publication_issue_path,
            "publication_issue": {**self.publication_issue, "scope": list(cast(tuple[str, ...], self.publication_issue["scope"]))},
            "selected_issue": {**self.selected_issue, "scope": list(cast(tuple[str, ...], self.selected_issue["scope"]))},
            "source_head": self.source_head, "observed_head": self.observed_head,
            "before_sha256": NativeGitLaneSource._sha(self.before_bytes), "before_blob": self.before_blob,
            "scope_profile": dependency_endpoint_scope_profile(self.dependency_contexts), "dependency_contexts": list(self.dependency_contexts),
            "protected_paths": list(self.protected_paths), "goal_paths": list(self.goal_paths),
            "issue_paths": list(self.issue_paths), "protocol_sha256": self.protocol_sha256}


# Weak registration is identity/content-bound and dies with the issued object.
# There is deliberately no public or private mapping-to-seal entrance.
_ISSUED: weakref.WeakKeyDictionary[VerifiedForwardAdmissionV2, tuple[weakref.ReferenceType[NativeGitForwardAdmissionSource], str]] = weakref.WeakKeyDictionary()


class NativeGitForwardAdmissionSource(NativeGitLaneSource):
    def __init__(self, *, resolver_capability: object) -> None:
        super().__init__(resolver_capability=resolver_capability)
        resolver = _require_native_resolver(resolver_capability)
        # Capture before CAS. Receipt issuance must never revalidate mutable
        # Protocol/target topology after a successful repository effect.
        self._protocol_manifest_path: str = resolver.manifest_path.relative_to(self._root).as_posix()

    def _lane_context(self, *, revision: str, goal_path: str, document: object,
                      coordinate: GoalPhaseCoordinate) -> tuple[GoalLaneDirectionAuthorityV1, tuple[dict[str, object], ...]]:
        typed = checked_forward_document(cast(Document, document))
        _, projection, _, _ = self._snapshot(revision, goal_path)
        matches = tuple(l for l in projection.lane_authorities if l.lane_key == coordinate.lane_key)
        if len(matches) != 1:
            raise ValueError("forward_admission_lane_authority_absent")
        lane = matches[0]
        required: set[str] = {w.issue_ref for p in typed.operational_bundle.phases
            if p.coordinate.lane_key == coordinate.lane_key for w in p.work_associations
            if w.disposition is GoalLanePhaseWorkDisposition.CURRENT}
        if lane.current_issue_ref is not None and not lane.current_issue_ref.startswith("TBD:"):
            required.add(lane.current_issue_ref)
        issues: dict[str, dict[str, object]] = {}
        for reference in sorted(required):
            path = self._projector._resolve_issue_path(revision=revision, goal_path=goal_path, issue_ref=reference)
            # Work itself must use an exact canonical admitted location; a
            # compatibility link may resolve to that same location explicitly.
            issues[path] = self._issue(revision, path)
        selected = lane.current_issue_ref
        if selected is not None and not selected.startswith("TBD:"):
            selected = self._projector._resolve_issue_path(revision=revision, goal_path=goal_path, issue_ref=selected)
            lane = replace(lane, current_issue_ref=selected)
        return lane, tuple(issues[path] for path in sorted(issues))

    def verify(self, *, goal_path: str, publication_issue_path: str,
               request: GoalPhaseOperationalAdmissionRequestV2) -> VerifiedForwardAdmissionV2:
        """Authenticate source bytes, complete graph context and terminal epoch."""
        if type(request) is not GoalPhaseOperationalAdmissionRequestV2:
            raise TypeError("forward admission request must be exact")
        request = decode_forward_admission_request(request.to_wire())
        head = self._commit("HEAD")
        result = self._restore_request(goal_path=goal_path, publication_issue_path=publication_issue_path,
            request=request, head=head)
        self.terminal(result, expected_head=head)
        _ISSUED[result] = (weakref.ref(self), fingerprint(result.to_wire()))
        return result

    def _restore_request(self, *, goal_path: str, publication_issue_path: str,
        request: GoalPhaseOperationalAdmissionRequestV2, head: str) -> VerifiedForwardAdmissionV2:
        """Historical facts only; this method cannot register current authority."""
        request = decode_forward_admission_request(request.to_wire())
        origin = self._commit(request.expected_source_revision_ref)
        if origin != request.expected_source_revision_ref:
            raise ValueError("forward_admission_source_revision_not_exact")
        if not self._ancestor(origin, head):
            raise ValueError("forward_admission_source_lineage_unproven")
        document, projection, before, blob = self._snapshot(origin, goal_path)
        document = checked_forward_document(cast(Document, document))
        publication_issue = self._issue(origin, publication_issue_path)
        if (publication_issue["status"] != "in_progress"
            or projection.global_authority.owner_ref != publication_issue["owner"]
            or goal_path not in cast(tuple[str, ...], publication_issue["scope"])):
            raise ValueError("forward_admission_goal_owner_issue_required")
        lane, lane_issues = self._lane_context(revision=origin, goal_path=goal_path,
            document=document, coordinate=request.coordinate)
        self._issues.resolve_issue_path(request.issue_ref)
        selected_issue = self._issue(origin, request.issue_ref)
        validate_forward_admission_direction(coordinate=request.coordinate, issue_ref=request.issue_ref,
            global_authority=projection.global_authority, lane_authority=lane, selected_issue=selected_issue)
        plan = plan_existing_definition_admission(document=document, request=request)
        # The committed document, not the caller, selects the full incident set.
        incident = tuple(sorted((d for d in document.operational_bundle.dependencies
            if request.coordinate in (d.dependent, d.prerequisite)), key=lambda d: d.dependency_key))
        wires = cast(list[dict[str, object]], cast(dict[str, object], document_wire(document)["operational_bundle"])["dependencies"])
        declaration_by_key = {cast(str, d["dependency_key"]): d for d in wires}
        goal_paths = {goal_path}
        issue_paths = {publication_issue_path, request.issue_ref,
            *(cast(str, i["path"]) for i in lane_issues)}
        records: list[dict[str, object]] = []
        for declaration in incident:
            endpoints: list[dict[str, object]] = []
            for coordinate in (declaration.dependent, declaration.prerequisite):
                path = goal_path if coordinate.goal_tag == document.goal_tag else self._goal_path(origin, coordinate.goal_tag)
                endpoint, endpoint_projection, payload, endpoint_blob = self._snapshot(origin, path)
                endpoint = checked_forward_document(cast(Document, endpoint))
                goal_paths.add(path)
                matches = tuple(l for l in endpoint_projection.lane_authorities if l.lane_key == coordinate.lane_key)
                if matches:
                    # Shared lanes retain every existing qualification/agreement
                    # check. Ambiguity is never downgraded to absence.
                    endpoint_lane, endpoint_issues = self._lane_context(revision=origin, goal_path=path,
                        document=endpoint, coordinate=coordinate)
                    context = derive_dependency_endpoint_context(document=endpoint, coordinate=coordinate,
                        global_authority=endpoint_projection.global_authority, lane_authority=endpoint_lane,
                        issues=endpoint_issues, source_revision_ref=origin)
                else:
                    if coordinate == request.coordinate:
                        raise ValueError("forward_admission_lane_authority_absent")
                    # V2/V3 have no native lane authority. Resolve complete
                    # committed Work facts without inventing lane selection,
                    # owner, operational state, or qualified Gate evidence.
                    references = {w.issue_ref for p in endpoint.operational_bundle.phases
                        if p.coordinate.lane_key == coordinate.lane_key for w in p.work_associations
                        if w.disposition is GoalLanePhaseWorkDisposition.CURRENT}
                    endpoint_issues = tuple(self._issue(origin, reference) for reference in sorted(references))
                    context = derive_absent_lane_endpoint_context(document=endpoint, coordinate=coordinate,
                        global_authority=endpoint_projection.global_authority,
                        issues=endpoint_issues, source_revision_ref=origin)
                issue_paths.update(cast(str, i["path"]) for i in endpoint_issues)
                if coordinate == declaration.prerequisite:
                    definition = cast(dict[str, object], context["definition"])
                    if cast(dict[str, object], definition["gate"])["gate_digest"] != declaration.required_gate_digest:
                        raise ValueError("forward_admission_dependency_gate_mismatch")
                endpoints.append({"context": context, "goal_path": path,
                    "goal_sha256": self._sha(payload), "goal_blob_oid": endpoint_blob})
            records.append({"declaration": declaration_by_key[declaration.dependency_key],
                "declaration_digest": goal_phase_dependency_digest(declaration),
                "dependent": endpoints[0], "prerequisite": endpoints[1],
                "evaluation_profile": "source_context_only_non_authorizing"})
        for unresolved in document.unresolved_dependencies:
            if request.coordinate in (unresolved.dependent, unresolved.prerequisite):
                body = next(d for d in cast(list[dict[str, object]], document_wire(document)["unresolved_dependencies"])
                    if d["dependency_key"] == unresolved.dependency_key)
                records.append({"declaration": body, "declaration_digest": fingerprint(body),
                    "evaluation_profile": "unresolved_non_authorizing"})
        resolver = _require_native_resolver(self._capability)
        manifest = resolver.manifest_path.relative_to(self._root).as_posix()
        manifest_bytes, _ = self._regular_file(origin, manifest)
        if self._sha(manifest_bytes) != resolver.manifest_sha256:
            raise ValueError("forward_admission_protocol_source_mismatch")
        protected = tuple(sorted({manifest, *goal_paths, *issue_paths}))
        self.protected_history(origin, head, protected)
        # No caller-owned mapping survives into the registered provider result.
        result = VerifiedForwardAdmissionV2(plan, goal_path, publication_issue_path,
            dict(publication_issue), dict(selected_issue), origin, head, bytes(before), blob,
            tuple(cast(list[dict[str, object]], json.loads(json.dumps(records)))), protected,
            tuple(sorted(goal_paths)), tuple(sorted(issue_paths)), resolver.manifest_sha256)
        return result

    def candidate(self, verified: VerifiedForwardAdmissionV2) -> bytes:
        compatibility, _ = extract_goal_phase_native_carrier(verified.before_bytes)
        return attach_goal_phase_native_carrier(compatibility, verified.plan.after_document)

    def publication_receipt(self, verified: VerifiedForwardAdmissionV2, *, parent: str,
        commit: str, after_blob: str, repository_ref: str, request_fingerprint: str,
        commit_message: str, pending_projection_authority: dict[str, object] | None = None
        ) -> GoalPhaseOperationalAdmissionPublicationV2:
        """Build integrity evidence from already verified immutable effect inputs."""
        source_wire = verified.to_wire()
        source_wire["observed_head"] = parent
        after_document = document_wire(verified.plan.after_document)
        bundle = cast(dict[str, object], after_document["operational_bundle"])
        after_phase = cast(list[dict[str, object]], bundle["phases"])[-1]
        body: dict[str, object] = {
            "schema_id": PUBLICATION_SCHEMA, "provider_profile": "git_repository_cas_v1",
            "scope_profile": source_wire["scope_profile"], "source_verification": source_wire,
            "before_document": document_wire(verified.plan.before_document),
            "after_document": after_document, "before_phase": None, "after_phase": after_phase,
            "semantic_intent_ref": forward_publication_intent(source_wire, pending_projection_authority),
            "source_verification_ref": "goal-phase-forward-admission-source:" + fingerprint(source_wire),
            "after_sha256": self._sha(self.candidate(verified)), "after_blob": after_blob,
            "protocol_manifest_path": self._protocol_manifest_path,
            "repository_parent_ref": parent, "repository_commit_ref": commit,
            "repository_commit_receipt_ref": "repository-commit:" + commit,
            "repository_ref": repository_ref, "repository_request_fingerprint": request_fingerprint,
            "commit_message": commit_message,
        }
        if pending_projection_authority is not None:
            body["provider_profile"] = "git_repository_cas_pending_projection_v1"
            body["pending_projection_authority"] = pending_projection_authority
        return GoalPhaseOperationalAdmissionPublicationV2(body)

    def restore_publication_sources(self, supplied: GoalPhaseOperationalAdmissionPublicationV2
        ) -> tuple[GoalPhaseOperationalAdmissionPublicationV2, VerifiedForwardAdmissionV2, bytes]:
        """Independently reconstruct historical sources and the committed carrier effect.

        This unregistered result is not complete publication/currentness
        authority. The repository operation must independently rederive the
        shared repository request fingerprint, then observe HEAD, protected
        history and targets at each consuming boundary.
        """
        if type(supplied) is not GoalPhaseOperationalAdmissionPublicationV2:
            raise TypeError("forward publication receipt requires exact type")
        receipt = decode_forward_admission_publication(supplied.to_wire())
        body = receipt.body
        source_wire = cast(dict[str, object], body["source_verification"])
        request = decode_forward_admission_request(cast(dict[str, object], source_wire["plan"])["request"])
        commit = self._commit(cast(str, body["repository_commit_ref"]))
        parent = self._commit(cast(str, body["repository_parent_ref"]))
        if self._parents(commit) != (parent,):
            raise ValueError("forward_publication_parent_mismatch")
        path = cast(str, source_wire["goal_path"])
        if self._git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", parent, commit) != path.encode() + b"\0":
            raise ValueError("forward_publication_not_one_goal_path")
        restored = self._restore_request(goal_path=path,
            publication_issue_path=cast(str, source_wire["publication_issue_path"]), request=request, head=parent)
        if restored.to_wire() != source_wire:
            raise ValueError("forward_publication_source_authority_mismatch")
        before, before_blob = self._regular_file(parent, path)
        after, after_blob = self._regular_file(commit, path)
        if (before != restored.before_bytes or before_blob != restored.before_blob
            or after != self.candidate(restored)):
            raise ValueError("forward_publication_committed_delta_mismatch")
        if self._git("ls-tree", parent, "--", path).split(b" ", 1)[0] != self._git("ls-tree", commit, "--", path).split(b" ", 1)[0]:
            raise ValueError("forward_publication_mode_changed")
        expected = self.publication_receipt(restored, parent=parent, commit=commit, after_blob=after_blob,
            repository_ref=cast(str, body["repository_ref"]),
            request_fingerprint=cast(str, body["repository_request_fingerprint"]),
            commit_message=cast(str, body["commit_message"]),
            pending_projection_authority=cast(dict[str, object] | None, body.get("pending_projection_authority")))
        if expected.to_wire() != receipt.to_wire():
            raise ValueError("forward_publication_receipt_differs_from_authority")
        self._issue_effect_issuance(commit, restored.publication_issue_path,
            restored.publication_issue, (path,))
        message = self._git("show", "-s", "--format=%B", commit).decode()
        lines = message.splitlines()
        for name, value in (("Aware-Idempotency-Ref", request.idempotency_key),
                            ("Aware-Request-Fingerprint", body["repository_request_fingerprint"])):
            if [line for line in lines if line.startswith(name + ": ")] != [name + ": " + cast(str, value)]:
                raise ValueError("forward_publication_repository_receipt_mismatch")
        if not message.startswith(cast(str, body["commit_message"]) + "\n\n"):
            raise ValueError("forward_publication_commit_message_mismatch")
        return receipt, restored, after

    def protected_history(self, origin: str, head: str, paths: tuple[str, ...]) -> None:
        if not self._ancestor(origin, head):
            raise ValueError("forward_admission_source_lineage_unproven")
        if self._git("log", "--full-history", "--format=%H", f"{origin}..{head}", "--", *paths):
            raise ValueError("forward_admission_protected_history_advanced")

    def terminal(self, verified: VerifiedForwardAdmissionV2, *, expected_head: str) -> None:
        resolver = _require_native_resolver(self._capability)
        resolver.revalidate()
        for path in verified.goal_paths:
            _ = resolver.resolve_goal_path(path)
        for path in verified.issue_paths:
            self._issues.resolve_issue_path(path)
        resolver.revalidate()
        if self._commit("HEAD") != expected_head:
            raise ValueError("repository_head_advanced")

    def require_verified(self, verified: VerifiedForwardAdmissionV2) -> None:
        registered = _ISSUED.get(verified) if type(verified) is VerifiedForwardAdmissionV2 else None
        if registered is None or registered[0]() is not self or registered[1] != fingerprint(verified.to_wire()):
            raise ValueError("forward_admission_verification_unqualified_or_mutated")
        self.terminal(verified, expected_head=verified.observed_head)
