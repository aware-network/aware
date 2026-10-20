"""Shared concrete Git/Protocol source checks; no direction or evidence issuer.

Extracted publication, committed-source and history primitives are reused by
the independent direction and hold verifiers. No eligibility is decided here.
"""

from __future__ import annotations

# Adapter modules share exact internal Protocol/projector primitives.
# pyright: reportPrivateUsage=false

import hashlib
import re
import subprocess
from pathlib import Path
from typing import cast

from aware_goal_operational_runtime import (
    GoalLanePhaseWorkDisposition, GoalNativeLaneDependencySourceV1,
    GoalNativeLaneIntroductionPublicationReceiptV1,
    GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4,
    extract_goal_phase_native_carrier as extract_goal_phase_native_document,
    require_exact_native_lane_introduction,
)
from aware_goal_operational_runtime.identity import fingerprint
from .compatibility_source import (
    GitCommittedGoalCompatibilityDirectionProjector, GoalCompatibilityDirectionProjectionV1,
    GoalNativeScopeSourceError,
)
from .phase_operation import _NativeAdmittedIssueLocation, _require_native_resolver

_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


class NativeGitLaneSource:
    """Provider-owned source entrance, not source claims or resolver callbacks."""

    def __init__(self, *, resolver_capability: object) -> None:
        self._capability: object = resolver_capability
        resolver = _require_native_resolver(resolver_capability)
        self._root: Path = resolver.repository_root
        self._issues: _NativeAdmittedIssueLocation = _NativeAdmittedIssueLocation(resolver)
        self._projector: GitCommittedGoalCompatibilityDirectionProjector = GitCommittedGoalCompatibilityDirectionProjector(
            self._root, admitted_issue_location=self._issues,
        )

    def _authenticate_introduction(
        self, receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
    ) -> str:
        """Shared publication authentication; no currentness or direction seal."""
        resolver = _require_native_resolver(self._capability)
        location = resolver.resolve_goal_path(receipt.goal_path)
        if receipt.goal_tag != f"goal/{location.location_date}/{location.location_slug}":
            raise ValueError("native_goal_location_identity_mismatch")
        self._issues.resolve_issue_path(receipt.publication_issue_path)
        commit = self._commit(receipt.repository_commit_ref)
        parent = self._commit(receipt.repository_parent_ref)
        if self._parents(commit) != (parent,):
            raise ValueError("lane_publication_parent_mismatch")
        changed = self._git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", parent, commit)
        if changed != receipt.goal_path.encode() + b"\0":
            raise ValueError("lane_publication_not_one_goal_path")
        before, before_projection, before_bytes, before_blob = self._snapshot(parent, receipt.goal_path)
        after, after_projection, after_bytes, after_blob = self._snapshot(commit, receipt.goal_path)
        if type(after) is not GoalPhaseNativeDocumentV4:
            raise ValueError("lane_publication_postimage_not_v4")
        if (
            before_blob != receipt.before_goal_blob_oid
            or after_blob != receipt.after_goal_blob_oid
            or self._sha(before_bytes) != receipt.before_goal_sha256
            or self._sha(after_bytes) != receipt.after_goal_sha256
            or extract_goal_phase_native_document(before_bytes)[0]
            != extract_goal_phase_native_document(after_bytes)[0]
        ):
            raise ValueError("lane_publication_source_mismatch")
        _ = require_exact_native_lane_introduction(before=before, after=after, receipt=receipt)
        issue = self._issue(parent, receipt.publication_issue_path)
        if (
            issue["blob_oid"] != receipt.publication_issue_blob_oid
            or issue["owner"] != receipt.publication_issue_owner_execution_id
            or issue["status"] != receipt.publication_issue_status
            or issue["scope_digest"] != receipt.publication_issue_scope_digest
            or receipt.goal_path not in cast(tuple[str, ...], issue["scope"])
            or before_projection.global_authority.owner_ref != issue["owner"]
            or after_projection.global_authority.owner_ref != issue["owner"]
        ):
            raise ValueError("lane_publication_goal_owner_issue_mismatch")
        self._issuance(commit, receipt, issue)
        return commit

    def _dependency_sources(
        self, revision: str, document: GoalPhaseNativeDocumentV4,
        receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
    ) -> tuple[dict[str, GoalNativeLaneDependencySourceV1], set[str], tuple[tuple[str, str, str, str, str, str], ...]]:
        return self._incident_sources(revision, document, goal_path=receipt.goal_path, lane_key=receipt.lane_key)

    def _incident_sources(
        self, revision: str, document: GoalPhaseNativeDocumentV4, *, goal_path: str, lane_key: str,
    ) -> tuple[dict[str, GoalNativeLaneDependencySourceV1], set[str], tuple[tuple[str, str, str, str, str, str], ...]]:
        """Restore the complete incident set; there is no caller path inventory."""
        incident = tuple(d for d in document.operational_bundle.dependencies if any(
            c.goal_tag == document.goal_tag and c.lane_key == lane_key
            for c in (d.dependent, d.prerequisite)
        ))
        coordinates = tuple(c for d in incident for c in (d.dependent, d.prerequisite))
        facts: dict[str, GoalNativeLaneDependencySourceV1] = {}
        paths: set[str] = set()
        epochs: list[tuple[str, str, str, str, str, str]] = []
        for tag in sorted({c.goal_tag for c in coordinates}):
            path = goal_path if tag == document.goal_tag else self._goal_path(revision, tag)
            source, projection, payload, blob = self._snapshot(revision, path)
            if source.goal_tag != tag:
                raise ValueError("incident_dependency_goal_source_mismatch")
            paths.add(path)
            endpoint_lanes = {c.lane_key for c in coordinates if c.goal_tag == tag}
            issues: dict[str, dict[str, object]] = {}
            for phase in source.operational_bundle.phases:
                if phase.coordinate.lane_key not in endpoint_lanes:
                    continue
                for work in phase.work_associations:
                    if work.disposition is not GoalLanePhaseWorkDisposition.CURRENT:
                        continue
                    issue_path = self._projector._resolve_issue_path(
                        revision=revision, goal_path=path, issue_ref=work.issue_ref,
                    )
                    issues[work.issue_ref] = self._issue(revision, issue_path)
                    paths.add(issue_path)
            facts[tag] = GoalNativeLaneDependencySourceV1(
                document=source, global_authority=projection.global_authority,
                lane_authorities=projection.lane_authorities,
                issue_authorities=issues, source_revision_ref=revision,
            )
            epochs.append((revision, tag, path, source.document_ref, blob, self._sha(payload)))
        return facts, paths, tuple(epochs)

    def _goal_path(self, revision: str, goal_tag: str) -> str:
        resolver = _require_native_resolver(self._capability)
        matches: list[str] = []
        for path in self._git("ls-tree", "-r", "--name-only", revision, "--", resolver.goal_root).decode().splitlines():
            location = resolver.match_goal_path(path)
            if location is not None and f"goal/{location[0]}/{location[1]}" == goal_tag:
                matches.append(path)
        if len(matches) != 1:
            raise ValueError("incident_dependency_goal_source_unavailable")
        # Template matching is discovery only; the retained capability owns
        # concrete root/target containment under the current topology.
        _ = resolver.resolve_goal_path(matches[0])
        return matches[0]

    def _snapshot(self, revision: str, path: str) -> tuple[
        GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4,
        GoalCompatibilityDirectionProjectionV1, bytes, str,
    ]:
        resolver = _require_native_resolver(self._capability)
        location = resolver.resolve_goal_path(path)
        payload, blob = self._regular_file(revision, path)
        document, projection = self._projector.project_committed(
            revision_ref=revision, goal_path=path,
            expected_goal_sha256=self._sha(payload), expected_goal_blob_oid=blob,
        )
        if document.goal_tag != f"goal/{location.location_date}/{location.location_slug}":
            raise ValueError("native_goal_location_identity_mismatch")
        matches: list[str] = []
        for candidate in self._git("ls-tree", "-r", "--name-only", revision, "--", resolver.goal_root).decode().splitlines():
            if resolver.match_goal_path(candidate) is None:
                continue
            data, _ = self._regular_file(revision, candidate)
            tags = cast(list[bytes], re.findall(rb"(?m)^- Tag:\s*`?([^`\r\n]+)`?\s*$", data))
            if tuple(x.strip().decode() for x in tags) == (document.goal_tag,):
                matches.append(candidate)
        if matches != [path]:
            raise ValueError("goal_source_ambiguous")
        return document, projection, payload, blob

    def _issue(self, revision: str, path: str) -> dict[str, object]:
        self._issues.resolve_issue_path(path)
        payload, blob = self._regular_file(revision, path)
        text = payload.decode("utf-8")
        def field(name: str) -> str:
            matches = cast(list[str], re.findall(rf"(?m)^- {name}:\s*`?([^`\n]+)`?\s*$", text))
            if len(matches) != 1:
                raise ValueError("lane_issue_metadata_ambiguous")
            return matches[0].strip()
        tag = field("Tag")
        if tag != self._issues.issue_tag_for_path(path):
            raise ValueError("lane_issue_tag_mismatch")
        sections = cast(list[str], re.findall(r"(?ms)^## Ownership Scope\s*\n(.*?)(?=^## |\Z)", text))
        if len(sections) != 1:
            raise ValueError("lane_issue_scope_ambiguous")
        scope = tuple(cast(list[str], re.findall(r"(?m)^- `([^`]+)`\s*$", sections[0])))
        if not scope or len(set(scope)) != len(scope):
            raise ValueError("lane_issue_scope_invalid")
        if any(
            any(part in {"", ".", ".."} for part in p.split("/"))
            or ":" in p or "\\" in p or any(ord(c) < 32 for c in p) for p in scope
        ):
            raise ValueError("lane_issue_scope_invalid")
        return {
            "path": path, "blob_oid": blob, "tag": tag,
            "owner": field("Owner"), "status": field("Status").lower().replace(" ", "_"),
            "scope": scope, "scope_digest": fingerprint({"ownership_scope": list(scope)}),
        }

    def _issuance(self, commit: str, receipt: GoalNativeLaneIntroductionPublicationReceiptV1, issue: dict[str, object]) -> None:
        self._issue_effect_issuance(commit, receipt.publication_issue_path, issue, (receipt.goal_path,))

    def _issue_effect_issuance(
        self, commit: str, issue_path: str, issue: dict[str, object], paths: tuple[str, ...],
    ) -> None:
        message = self._git("show", "-s", "--format=%B", commit).decode()
        values: dict[str, str] = {}
        for name in ("Issue-Tag", "Issue-Path", "Owner", "Owned-Paths"):
            matches = cast(list[str], re.findall(rf"(?m)^{name}: ([^\n]+)$", message))
            if len(matches) != 1:
                raise ValueError("lane_publication_issue_receipt_absent")
            values[name] = matches[0]
        if values != {
            "Issue-Tag": issue["tag"], "Issue-Path": issue_path,
            "Owner": issue["owner"], "Owned-Paths": ",".join(paths),
        }:
            raise ValueError("lane_publication_issue_receipt_mismatch")

    def _history_edges(self, origin: str, head: str) -> tuple[tuple[str, str], ...]:
        # Do not use first-parent: every merge parent and side-branch effect
        # participates. A branch forked before introduction cannot be qualified.
        lines = self._git("rev-list", "--reverse", "--topo-order", "--parents", head, "^" + origin).decode().splitlines()
        edges: list[tuple[str, str]] = []
        for line in lines:
            child, *parents = line.split()
            if not parents:
                raise ValueError("native_lane_history_incomplete")
            for parent in parents:
                if not self._ancestor(origin, parent):
                    raise ValueError("native_lane_history_unqualified_branch")
                edges.append((parent, child))
        return tuple(edges)

    def _regular_file(self, revision: str, path: str) -> tuple[bytes, str]:
        entry = self._git("ls-tree", "-z", revision, "--", path).split(b"\0")
        if len(entry) != 2 or entry[1]:
            raise ValueError("native_lane_source_not_regular")
        metadata, listed = entry[0].split(b"\t", 1)
        mode, kind, blob = metadata.decode().split()
        if listed.decode() != path or mode not in {"100644", "100755"} or kind != "blob" or not _OID.fullmatch(blob):
            raise ValueError("native_lane_source_not_regular")
        return self._git("show", f"{revision}:{path}"), blob

    def _parents(self, commit: str) -> tuple[str, ...]:
        return tuple(self._git("show", "-s", "--format=%P", commit).decode().strip().split())

    def _commit(self, value: str) -> str:
        result = self._git("rev-parse", "--verify", f"{value}^{{commit}}").decode().strip()
        if not _OID.fullmatch(result):
            raise ValueError("native_lane_commit_invalid")
        return result

    def _ancestor(self, before: str, after: str) -> bool:
        result = subprocess.run(
            ("git", "merge-base", "--is-ancestor", before, after),
            cwd=self._root, capture_output=True, timeout=10,
        )
        if result.returncode not in {0, 1}:
            raise ValueError("native_lane_lineage_unavailable")
        return result.returncode == 0

    def _git(self, *args: str) -> bytes:
        try:
            return subprocess.run(
                ("git", *args), cwd=self._root, check=True, capture_output=True, timeout=10,
            ).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            raise GoalNativeScopeSourceError("native_lane_source_unavailable", "Git authority could not be read") from error

    @staticmethod
    def _sha(payload: bytes) -> str:
        return "sha256:" + hashlib.sha256(payload).hexdigest()
