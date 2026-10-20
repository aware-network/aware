"""Concrete Git/Protocol authority for the opt-in forward-looking Gate.

No callback/mapping resolver, test execution, eligibility reduction or writer.
Authored publication bindings are claims until every coordinate is restored.
"""
from __future__ import annotations

# Reuse the already governed source entrance, not a second Git authority rail.
# pyright: reportPrivateUsage=false

import re
import stat
import weakref
from datetime import UTC, datetime
from typing import cast
from typing_extensions import override

from aware_goal_operational_runtime import GoalPhaseNativeDocumentV4
from aware_goal_operational_runtime.phase_runtime_checks_review import (
    PROOF, PUBLICATION, REQUEST, REVIEW,
    VERIFICATION, RuntimeChecksArtifactV2, RuntimeChecksSourceIssuerV2, RuntimeChecksVerifiedInputV2,
    _register_runtime_checks_issuer, canonical_json, coordinate, decode_runtime_checks_artifact,
    digest, path, require_runtime_checks_dependency_profile, runtime_checks_selected_work,
    runtime_checks_semantic_scope, strict_json, text,
)
from .native_lane_source import NativeGitLaneSource
from .phase_operation import _require_native_resolver

_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


class _GitRuntimeChecksIssuer(RuntimeChecksSourceIssuerV2):
    @override
    def require_input(self, value: RuntimeChecksVerifiedInputV2) -> None:
        recorded = _ISSUED.get(self)
        if recorded is None or recorded[0]() is not value or recorded[1] != digest(value.to_wire()):
            raise ValueError("runtime_checks_input_unissued_or_mutated")


_ISSUED: weakref.WeakKeyDictionary[_GitRuntimeChecksIssuer, tuple[weakref.ReferenceType[RuntimeChecksVerifiedInputV2], str]] = weakref.WeakKeyDictionary()
_register_runtime_checks_issuer(_GitRuntimeChecksIssuer)


class GitRuntimeChecksReviewAuthorityVerifier:
    """The sole provider entrance; requires an issued retained Protocol capability."""

    def __init__(self, *, resolver_capability: object) -> None:
        self._source: NativeGitLaneSource = NativeGitLaneSource(resolver_capability=resolver_capability)

    def _commit(self, value: object) -> str:
        claimed = text(value)
        if not _OID.fullmatch(claimed) or self._source._commit(claimed) != claimed:
            raise ValueError("runtime_checks_commit_invalid")
        return claimed

    def _changed(self, parent: str, commit: str) -> list[str]:
        return sorted(self._source._git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", parent, commit).decode().strip("\0").split("\0"))

    def _issuance(self, commit: str, issue_path: str, issue: dict[str, object], paths: list[str]) -> None:
        # The repository writer retains command operand order in its footer;
        # that order is not the canonical changed-path inventory's semantics.
        message = self._source._git("show", "-s", "--format=%B", commit).decode()
        fields = cast(list[str], re.findall(r"(?m)^Owned-Paths: ([^\n]+)$", message))
        if len(fields) != 1:
            raise ValueError("runtime_checks_publication_effect_receipt")
        actual = tuple(path(p) for p in fields[0].split(","))
        if sorted(actual) != paths or len(set(actual)) != len(actual):
            raise ValueError("runtime_checks_publication_effect_receipt")
        self._source._issue_effect_issuance(commit, issue_path, issue, actual)

    def _target(self, name: str) -> None:
        """Artifacts/source/output paths are also concrete admitted regular targets."""
        name = path(name)
        target = self._source._root
        for index, part in enumerate(name.split("/")):
            target = target / part
            try:
                mode = target.lstat().st_mode
                if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) if index == len(name.split("/")) - 1 else stat.S_ISDIR(mode)):
                    raise ValueError("runtime_checks_target_unresolvable")
            except OSError as error:
                raise ValueError("runtime_checks_target_unresolvable") from error
        if not target.resolve().is_relative_to(self._source._root.resolve()):
            raise ValueError("runtime_checks_target_unresolvable")

    def _issue_binding(self, epoch: str, issue_path: str) -> dict[str, object]:
        issue = self._source._issue(epoch, issue_path)
        return {**issue, "scope": list(cast(tuple[str, ...], issue["scope"]))}

    def _publication(
        self, claim: RuntimeChecksArtifactV2, schema: str,
    ) -> tuple[dict[str, object], dict[str, object], str, dict[str, object], list[str]]:
        claim = decode_runtime_checks_artifact(claim.to_wire())
        pub = claim.to_wire()
        if pub["schema_id"] != PUBLICATION or pub["artifact_schema_id"] != schema:
            raise ValueError("runtime_checks_publication_variant")
        commit = self._commit(pub["repository_revision_ref"])
        parents = self._source._parents(commit)
        if len(parents) != 1 or pub["repository_commit_receipt_ref"] != "repository-commit:" + commit:
            raise ValueError("runtime_checks_publication_receipt")
        artifact_path = path(pub["artifact_path"])
        issue_path = path(pub["governing_issue_path"])
        self._target(artifact_path)
        data, blob = self._source._regular_file(commit, artifact_path)
        artifact = decode_runtime_checks_artifact(strict_json(data)).to_wire()
        ref_field = {REQUEST: "request_ref", PROOF: "proof_ref", REVIEW: "review_ref"}[schema]
        if artifact["schema_id"] != schema or artifact[ref_field] != pub["artifact_ref"] or pub["artifact_blob_ref"] != blob:
            raise ValueError("runtime_checks_artifact_publication_mismatch")
        issue = self._issue_binding(parents[0], issue_path)
        post = self._issue_binding(commit, issue_path)
        if pub["governing_issue_blob_ref"] != post["blob_oid"] or any(pub[k] != issue[v] for k, v in (
            ("owner_execution_id", "owner"),
            ("status", "status"), ("scope", "scope"), ("scope_digest", "scope_digest"),
        )) or any(post[k] != issue[k] for k in ("tag", "owner", "status", "scope", "scope_digest")):
            raise ValueError("runtime_checks_publication_issue_mismatch")
        paths = [artifact_path, issue_path]
        if schema == PROOF:
            paths.extend(path(cast(dict[str, object], c["output"])["path"]) for c in cast(list[dict[str, object]], artifact["checks"]))
        paths = sorted(paths)
        if len(set(paths)) != len(paths) or self._changed(parents[0], commit) != paths or not set(paths).issubset(cast(list[str], issue["scope"])):
            raise ValueError("runtime_checks_publication_effect")
        self._issuance(commit, issue_path, issue, paths)
        # An inherited blob cannot be relabeled as a publication effect.
        changed = self._source._git("diff", "--name-only", parents[0], commit, "--", artifact_path).decode().splitlines()
        if changed != [artifact_path]:
            raise ValueError("runtime_checks_inherited_artifact")
        if schema == PROOF:
            for check in cast(list[dict[str, object]], artifact["checks"]):
                output = cast(dict[str, object], check["output"])
                output_path = path(output["path"])
                self._target(output_path)
                content, oid = self._source._regular_file(commit, output_path)
                _ = content.decode("utf-8")
                if output["blob_ref"] != oid or output["sha256"] != self._source._sha(content):
                    raise ValueError("runtime_checks_output_binding")
                if self._source._git("ls-tree", "-z", parents[0], "--", output_path):
                    raise ValueError("runtime_checks_output_inherited")
        return pub, artifact, parents[0], issue, paths

    def _selection(self, revision: str, goal_path: str, request: dict[str, object]) -> tuple[GoalPhaseNativeDocumentV4, dict[str, object], dict[str, object]]:
        doc, _, _, _ = self._source._snapshot(revision, goal_path)
        if type(doc) is not GoalPhaseNativeDocumentV4:
            raise ValueError("runtime_checks_requires_v4")
        binding = runtime_checks_selected_work(doc, request)
        pub = cast(dict[str, object], request["implementation_publication"])
        issue_path = self._source._projector._resolve_issue_path(revision=revision, goal_path=goal_path, issue_ref=text(binding["issue_ref"]))
        issue = self._issue_binding(revision, issue_path)
        if binding != pub["selected_work_binding"] or pub["governing_issue_path"] != issue_path or pub["governing_issue_tag"] != issue["tag"]:
            raise ValueError("implementation_work_issue_mismatch")
        return doc, binding, issue

    def _closure(self, revision: str, goal_path: str, lane: str) -> tuple[dict[str, object], set[str]]:
        doc, projection, _, _ = self._source._snapshot(revision, goal_path)
        if type(doc) is not GoalPhaseNativeDocumentV4:
            raise ValueError("runtime_checks_requires_v4")
        dependencies, paths, _ = self._source._incident_sources(revision, doc, goal_path=goal_path, lane_key=lane)
        return runtime_checks_semantic_scope(doc, projection.global_authority, lane, dependencies, projection.lane_authorities), paths | {goal_path}

    def verify(
        self, *, request_publication: RuntimeChecksArtifactV2,
        proof_publication: RuntimeChecksArtifactV2, review_publication: RuntimeChecksArtifactV2,
    ) -> RuntimeChecksVerifiedInputV2:
        source = self._source
        head = source._commit("HEAD")
        request_pub, request, request_parent, request_issue, request_paths = self._publication(request_publication, REQUEST)
        proof_pub, proof, proof_parent, proof_issue, proof_paths = self._publication(proof_publication, PROOF)
        review_pub, review, review_parent, review_issue, review_paths = self._publication(review_publication, REVIEW)
        pubs = [request_pub, proof_pub, review_pub]
        commits = [text(p["repository_revision_ref"]) for p in pubs]
        origin = self._commit(request["source_revision_ref"])
        impl = cast(dict[str, object], request["implementation_publication"])
        implementation = self._commit(impl["repository_revision_ref"])
        impl_parent = self._commit(impl["repository_parent_ref"])
        if source._parents(implementation) != (impl_parent,) or impl["repository_commit_receipt_ref"] != "repository-commit:" + implementation:
            raise ValueError("runtime_checks_implementation_parent_receipt")
        ordered = [implementation, origin, *commits, head]
        if any(not source._ancestor(a, b) for a, b in zip(ordered, ordered[1:])) or any(a == b for a, b in zip([origin, *commits], commits)):
            raise ValueError("runtime_checks_publication_order")
        goal_path = path(request["goal_path"])
        lane_key = coordinate(request["coordinate"]).lane_key
        doc, work, source_issue = self._selection(origin, goal_path, request)
        _, parent_work, impl_issue = self._selection(impl_parent, goal_path, request)
        observed_doc, observed_work, _ = self._selection(head, goal_path, request)
        if work != parent_work or work != observed_work or doc.document_ref != request["source_document_ref"]:
            raise ValueError("implementation_work_issue_mismatch")
        changed = self._changed(impl_parent, implementation)
        if changed != impl["changed_paths"] or impl["changed_paths_ref"] != "goal-runtime-checks-changed-paths:" + digest(changed):
            raise ValueError("runtime_checks_implementation_path_set")
        for k, name in (("governing_issue_blob_ref", "blob_oid"), ("owner_execution_id", "owner"), ("status", "status"), ("scope", "scope"), ("scope_digest", "scope_digest")):
            if impl[k] != impl_issue[name]:
                raise ValueError("runtime_checks_implementation_parent_authority")
        if impl_issue["status"] != "in_progress" or not set(changed).issubset(cast(list[str], impl_issue["scope"])):
            raise ValueError("runtime_checks_implementation_parent_authority")
        if any(source_issue[k] != impl_issue[k] for k in ("tag", "owner", "status", "scope", "scope_digest")):
            raise ValueError("runtime_checks_implementation_source_authority")
        self._issuance(implementation, path(impl["governing_issue_path"]), impl_issue, changed)
        for epoch in (origin, commits[0], head):
            _, projection, _, _ = source._snapshot(epoch, goal_path)
            if projection.global_authority.owner_ref != request["requested_by_execution_id"]:
                raise ValueError("runtime_checks_request_goal_owner")
        if request_issue["owner"] != request["requested_by_execution_id"] or proof_issue["owner"] != proof["publisher_execution_id"] or proof_issue["owner"] != impl_issue["owner"]:
            raise ValueError("runtime_checks_publisher_identity")
        if review_issue["owner"] != review["reviewer_execution_id"] or review_issue["owner"] in {impl_issue["owner"], proof_issue["owner"]}:
            raise ValueError("runtime_checks_reviewer_not_independent")
        for artifact in (proof, review):
            if any(artifact[k] != request[k] for k in ("coordinate", "definition_ref", "gate_digest", "evaluator_profile", "source_scope_ref")) or artifact["request_ref"] != request["request_ref"] or artifact["request_publication_ref"] != request_pub["publication_ref"]:
                raise ValueError("runtime_checks_cross_role_mismatch")
        if review["proof_ref"] != proof["proof_ref"] or review["proof_publication_ref"] != proof_pub["publication_ref"] or review["reviewed_changed_paths_ref"] != impl["changed_paths_ref"]:
            raise ValueError("runtime_checks_cross_role_mismatch")
        if not (text(request["issued_at"]) <= text(proof["issued_at"]) <= text(review["issued_at"])):
            raise ValueError("runtime_checks_publication_time_order")
        require_runtime_checks_dependency_profile(doc, request)
        scope = cast(list[dict[str, object]], request["source_scope"])
        scope_paths = {path(r["path"]) for r in scope}
        if not set(changed).issubset(scope_paths):
            raise ValueError("runtime_checks_implementation_path_omitted")
        artifacts = {path(p["artifact_path"]) for p in pubs}
        issues = {path(p["governing_issue_path"]) for p in pubs} | {path(impl["governing_issue_path"])}
        outputs = {path(cast(dict[str, object], c["output"])["path"]) for c in cast(list[dict[str, object]], proof["checks"])}
        if len(artifacts) != 3 or artifacts & issues or outputs & (artifacts | issues) or scope_paths & (artifacts | outputs):
            raise ValueError("runtime_checks_authority_path_overlap")
        inventory: list[dict[str, object]] = []

        def retain(epoch: str, name: str, role: str, issue: dict[str, object] | None = None) -> dict[str, object]:
            self._target(name)
            content, blob = source._regular_file(epoch, name)
            item: dict[str, object] = {"path": name, "blob_ref": blob, "sha256": source._sha(content), "role": role,
                "source_revision_ref": epoch, "issue_authority": issue}
            inventory.append(item)
            return item

        for item in scope:
            bound = retain(origin, path(item["path"]), "source")
            if any(item[k] != bound[k] for k in ("path", "blob_ref", "sha256")):
                raise ValueError("runtime_checks_source_scope_binding")
        _ = retain(impl_parent, path(impl["governing_issue_path"]), "implementation-parent-issue", impl_issue)
        _ = retain(origin, path(impl["governing_issue_path"]), "implementation-source-issue", source_issue)
        for pub, parent, issue, role in zip(pubs, (request_parent, proof_parent, review_parent), (request_issue, proof_issue, review_issue), ("request", "proof", "review")):
            _ = retain(parent, path(pub["governing_issue_path"]), role + "-parent-issue", issue)
            _ = retain(text(pub["repository_revision_ref"]), path(pub["governing_issue_path"]), role + "-issue",
                self._issue_binding(text(pub["repository_revision_ref"]), path(pub["governing_issue_path"])))
            _ = retain(text(pub["repository_revision_ref"]), path(pub["artifact_path"]), role)
        for output in sorted(outputs):
            _ = retain(commits[1], output, "proof-output")
        closure, participating = self._closure(origin, goal_path, lane_key)
        # There must be no hidden selection change between implementation and request.
        for parent, child in source._history_edges(impl_parent, origin):
            before, paths_before = self._closure(parent, goal_path, lane_key)
            after, paths_after = self._closure(child, goal_path, lane_key)
            participating |= paths_before | paths_after
            if before != after:
                raise ValueError("runtime_checks_semantic_scope_changed")
            if child != implementation and path(impl["governing_issue_path"]) in self._changed(parent, child):
                raise ValueError("runtime_checks_implementation_issue_history_unqualified")
        history: list[dict[str, object]] = []
        permitted = {c: (p, paths) for c, p, paths in zip(commits, pubs, (request_paths, proof_paths, review_paths))}
        stale = False
        for parent, child in source._history_edges(origin, head):
            before, paths_before = self._closure(parent, goal_path, lane_key)
            after, paths_after = self._closure(child, goal_path, lane_key)
            participating |= paths_before | paths_after
            if before != closure or after != closure:
                raise ValueError("runtime_checks_semantic_scope_changed")
            paths = self._changed(parent, child)
            admitted = permitted.get(child)
            permitted_ref = None
            if admitted is not None and paths == admitted[1] and source._parents(child) == (parent,):
                permitted_ref = admitted[0]["publication_ref"]
            relevant = [i for i in inventory if i["path"] in paths and source._ancestor(text(i["source_revision_ref"]), parent)]
            if not relevant and permitted_ref is None:
                continue
            stale |= bool(relevant) and permitted_ref is None
            history.append({"parent_ref": parent, "repository_revision_ref": child, "changed_paths": paths,
                "before_closure_ref": "goal-runtime-checks-semantic-closure:" + digest(before),
                "after_closure_ref": "goal-runtime-checks-semantic-closure:" + digest(after),
                "permitted_publication_ref": permitted_ref})
        # External participating Issue authorities must also be history-bound.
        for name in sorted(participating):
            _ = retain(origin, name, "incident-authority")
            if name == goal_path or name in issues:
                continue  # Goal changes were classified by complete per-edge closure above.
            if source._git("log", "--full-history", "--format=%H", f"{origin}..{head}", "--", name):
                raise ValueError("runtime_checks_incident_authority_changed")
        verification = {"schema_id": VERIFICATION, "goal_path": goal_path, "coordinate": request["coordinate"],
            "original_source_revision_ref": origin, "original_document_ref": doc.document_ref,
            "source_scope": scope, "source_scope_ref": request["source_scope_ref"], "authority_publications": pubs,
            "observed_source_revision_ref": head, "observed_document_ref": observed_doc.document_ref,
            "authority_inventory": inventory, "history_effects": history, "scope_currentness": "stale" if stale else "current"}
        verification["verification_ref"] = "goal-runtime-checks-source-verification:" + digest(verification)
        # Terminal capability and concrete target rechecks precede the LAST HEAD read.
        resolver = _require_native_resolver(source._capability)
        _ = resolver.resolve_goal_path(goal_path)
        for name in sorted(participating):
            if resolver.match_goal_path(name) is not None:
                _ = resolver.resolve_goal_path(name)
        for name in sorted(issues):
            source._issues.resolve_issue_path(name)
        for name in sorted({path(i["path"]) for i in inventory}):
            self._target(name)
        if source._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        body = {"request": request, "proof": proof, "review": review, "source_verification": verification,
            "evaluated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")}
        issuer = _GitRuntimeChecksIssuer()
        value = RuntimeChecksVerifiedInputV2(canonical_json(body), issuer)
        _ISSUED[issuer] = (weakref.ref(value), digest(body))
        return value
