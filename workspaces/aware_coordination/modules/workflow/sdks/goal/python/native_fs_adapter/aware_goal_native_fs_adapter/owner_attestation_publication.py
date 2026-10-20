"""Concrete committed-publication proof; NOT qualified actor-action authority.

This provider checks source, target, Goal ownership and exact Issue/commit
effects. It deliberately does not resolve actor identity, owner appointment,
action occurrence or cited evidence issuance. No neutral acceptance entrance
consumes this proof. Commit trailers authenticate the repository publication
profile only; they are not signatures by the named actor.
"""

from __future__ import annotations

# Reuse provider-owned Protocol/Issue/source primitives, never echo callbacks.
# pyright: reportPrivateUsage=false

import json
import re
import weakref
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import cast

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_owner_attestation import (
    OwnerAttestationClaimV2, decode_owner_attestation_v2, encode_owner_attestation_v2,
)

from .native_lane_source import NativeGitLaneSource
from .phase_operation import _require_native_resolver

PROFILE = "aware.goal.git-owner-attestation-publication.v2"
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GitOwnerAttestationPublicationProofV2:
    """Live-process source proof. Unresolved action/identity/evidence remain claims."""

    canonical_body: str

    def to_wire(self) -> dict[str, object]:
        body = cast(dict[str, object], json.loads(self.canonical_body))
        return {**body, "publication_verification_ref": "goal-git-owner-attestation-publication:" + fingerprint(body)}


_ISSUED: weakref.WeakKeyDictionary[GitOwnerAttestationPublicationProofV2, str] = weakref.WeakKeyDictionary()


def require_verified_owner_attestation_publication(
    value: GitOwnerAttestationPublicationProofV2,
) -> GitOwnerAttestationPublicationProofV2:
    if type(value) is not GitOwnerAttestationPublicationProofV2:
        raise ValueError("owner_attestation_publication_unissued_or_mutated")
    if _ISSUED.get(value) != value.canonical_body:
        raise ValueError("owner_attestation_publication_unissued_or_mutated")
    return value


class GitOwnerAttestationPublicationVerifierV2:
    """Read-only concrete provider. No actor, policy, evidence or Gate issuer."""

    def __init__(self, *, resolver_capability: object) -> None:
        self._source: NativeGitLaneSource = NativeGitLaneSource(resolver_capability=resolver_capability)

    @property
    def source_binding_ref(self) -> str:
        resolver = _require_native_resolver(self._source._capability)
        stat = resolver.repository_root.stat()
        return "goal-git-source-binding:" + fingerprint({
            "schema_id": PROFILE, "repository_root": str(resolver.repository_root),
            "repository_device": stat.st_dev, "repository_inode": stat.st_ino,
            "protocol_manifest_sha256": resolver.manifest_sha256,
        })

    def _artifact_target(self, path: str) -> None:
        if (
            type(path) is not str or not path or str(PurePosixPath(path)) != path
            or path.startswith("/") or any(p in {"", ".", "..", ".git"} for p in path.split("/"))
            or ":" in path or "\\" in path or any(ord(c) < 32 for c in path)
        ):
            raise ValueError("owner_attestation_artifact_path_invalid")
        root = self._source._root
        target = root / path
        # Every existing component is checked. An absent projection is allowed;
        # no worktree bytes are read as artifact authority, and nothing is written.
        for part in (target, *target.parents):
            if part == root:
                break
            if part.is_symlink():
                raise ValueError("owner_attestation_artifact_target_unsafe")
        if not target.resolve().is_relative_to(root):
            raise ValueError("owner_attestation_artifact_target_unsafe")

    def verify(
        self, *, goal_path: str, artifact_path: str, publication_commit: str,
        repository_commit_receipt_ref: str, issue_path: str,
        expected_claim: OwnerAttestationClaimV2,
    ) -> GitOwnerAttestationPublicationProofV2:
        source = self._source
        resolver = _require_native_resolver(source._capability)
        resolver.revalidate()
        _ = resolver.resolve_goal_path(goal_path)
        source._issues.resolve_issue_path(issue_path)
        self._artifact_target(artifact_path)
        if artifact_path in {goal_path, issue_path}:
            raise ValueError("owner_attestation_artifact_path_collision")
        # Validate claims BEFORE any reconstruction; do not repair mutations.
        expected_bytes = encode_owner_attestation_v2(expected_claim)
        claim = expected_claim.to_wire()
        head = source._commit("HEAD")
        commit = source._commit(publication_commit)
        if publication_commit != commit or repository_commit_receipt_ref != "repository-commit:" + commit:
            raise ValueError("owner_attestation_publication_commit_receipt_mismatch")
        parents = source._parents(commit)
        if len(parents) != 1 or not source._ancestor(commit, head):
            raise ValueError("owner_attestation_publication_lineage_invalid")
        parent = parents[0]
        epoch = cast(dict[str, str], claim["source_epoch"])
        revision = epoch["source_revision"]
        if not _OID.fullmatch(revision) or source._commit(revision) != revision or not source._ancestor(revision, parent):
            raise ValueError("owner_attestation_source_lineage_invalid")
        if epoch["provider_binding_ref"] != self.source_binding_ref:
            raise ValueError("owner_attestation_source_binding_mismatch")
        document, projection, payload, blob = source._snapshot(revision, goal_path)
        if epoch["document_ref"] != document.document_ref or epoch["goal_sha256"] != source._sha(payload):
            raise ValueError("owner_attestation_source_epoch_mismatch")
        coordinate = cast(dict[str, str], claim["coordinate"])
        matches = [d for d in document.definitions if {
            "goal_tag": d.coordinate.goal_tag, "lane_key": d.coordinate.lane_key,
            "phase_key": d.coordinate.phase_key,
        } == coordinate]
        if len(matches) != 1 or matches[0].definition_ref != claim["definition_ref"] or matches[0].gate.gate_digest != claim["gate_digest"]:
            raise ValueError("owner_attestation_target_mismatch")
        owner = projection.global_authority.owner_ref
        if owner != claim["owner_execution_id"]:
            raise ValueError("owner_attestation_goal_owner_mismatch")
        before_issue = source._issue(parent, issue_path)
        after_issue = source._issue(commit, issue_path)
        for field in ("path", "tag", "owner", "status", "scope", "scope_digest"):
            if before_issue[field] != after_issue[field]:
                raise ValueError("owner_attestation_issue_authority_changed")
        if before_issue["owner"] != owner or before_issue["status"] != "in_progress":
            raise ValueError("owner_attestation_issue_owner_or_status_invalid")
        paths = tuple(sorted((artifact_path, issue_path)))
        if set(cast(tuple[str, ...], before_issue["scope"])) != set(paths):
            raise ValueError("owner_attestation_issue_scope_mismatch")
        for at in (parent, commit):
            text, _ = source._regular_file(at, issue_path)
            tags = cast(list[bytes], re.findall(rb"(?m)^- Goal:\s*`?([^`\r\n]+)`?\s*$", text))
            if tuple(t.strip().decode() for t in tags) != (document.goal_tag,):
                raise ValueError("owner_attestation_issue_goal_mismatch")
        changed = source._git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", parent, commit)
        if changed != b"".join(p.encode() + b"\0" for p in paths):
            raise ValueError("owner_attestation_publication_effect_invalid")
        # First issuance only. Inheriting, replacing or copying an old publication
        # at its claimed path is not this profile's publication effect.
        if source._git("ls-tree", "-z", parent, "--", artifact_path):
            raise ValueError("owner_attestation_artifact_preexisting")
        actual_bytes, artifact_blob = source._regular_file(commit, artifact_path)
        actual = decode_owner_attestation_v2(actual_bytes)
        if encode_owner_attestation_v2(actual) != expected_bytes:
            raise ValueError("owner_attestation_artifact_claim_mismatch")
        source._issue_effect_issuance(commit, issue_path, before_issue, paths)
        self._unchanged(revision, head, (goal_path,))
        self._unchanged(commit, head, paths)
        resolver.revalidate()
        _ = resolver.resolve_goal_path(goal_path)
        source._issues.resolve_issue_path(issue_path)
        self._artifact_target(artifact_path)
        binding = self.source_binding_ref
        if source._commit("HEAD") != head:
            raise ValueError("repository_head_advanced")
        body = {
            "schema_id": "aware.goal.git-owner-attestation-publication-proof.v2",
            "verifier_profile": PROFILE, "claim": actual.to_wire(),
            "goal_path": goal_path, "source_goal_blob_oid": blob,
            "source_binding_ref": binding, "artifact_path": artifact_path,
            "artifact_blob_oid": artifact_blob, "artifact_sha256": source._sha(actual_bytes),
            "publication_commit": commit, "publication_parent": parent,
            "repository_commit_receipt_ref": repository_commit_receipt_ref,
            "parent_issue_authority": before_issue, "publication_issue_authority": after_issue,
            "verified_goal_owner_execution_id": owner, "observed_head": head,
            "protected_paths": sorted((goal_path, *paths)),
            "actor_identity_authority": "unavailable", "action_issuance_authority": "unavailable",
            "owner_appointment_authority": "unavailable", "evidence_issuance_authority": "unavailable",
            "effect_profile": "read_only_publication_proof_not_acceptance_authority",
        }
        result = GitOwnerAttestationPublicationProofV2(json.dumps(body, sort_keys=True, separators=(",", ":")))
        _ISSUED[result] = result.canonical_body
        return result

    def _unchanged(self, before: str, after: str, paths: tuple[str, ...]) -> None:
        # Full history, not final-tree equality: restored unauthorized effects
        # and effects from merged branches remain visible and refuse.
        _ = self._source._history_edges(before, after)
        if self._source._git("log", "--full-history", "--format=%H", f"{before}..{after}", "--", *paths).strip():
            raise ValueError("owner_attestation_protected_history_changed")
