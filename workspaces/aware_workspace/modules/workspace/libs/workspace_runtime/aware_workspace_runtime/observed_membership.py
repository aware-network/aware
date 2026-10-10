"""Observed declaration membership; no committed identity or semantic authority."""

from __future__ import annotations

import copy
import os
import threading
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, cast

from aware_code_semantic_contract_runtime import (
    CodeSemanticCandidate,
    CodeSemanticCandidateListing,
    ContentDigest,
    canonical_json_bytes,
)

from .composition import RetainedWorkspaceCompositionProvider
from .source_exclusion import WorkspaceSourceExclusion, require_same_exclusion
from .source_observation import (
    WorkspaceObservedRootEvidence,
    WorkspaceRetainedRootObservation,
    WorkspaceSourceObservationRuntime,
)
from .source_observation_io import SourceObservationUnavailable, validate_relative_path


@dataclass(frozen=True, slots=True)
class WorkspaceObservedPackageMembershipEvidence:
    repository_binding_ref: str
    observation_digest: str
    workspace_manifest_path: str
    module_manifest_path: str
    module_id: str
    package_id: str
    package_kind: str
    package_root: str
    manifest_relative_path: str
    visibility: str
    source_identity_digest: ContentDigest
    candidate_listing: CodeSemanticCandidateListing


class WorkspaceObservedPackageMembership:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Workspace issues observed membership")

    def __reduce__(self):
        raise TypeError("observed membership cannot be serialized")


class WorkspaceObservedPackageMembershipRuntime:
    """Host resource deriving membership from a complete retained declaration root.

    Initial policy observes the whole repository/workspace declaration root with
    no exclusions. This is deliberately bounded, not suitable for arbitrarily
    large checkouts. Selection identifiers never supply declarations or bodies.
    """

    def __init__(
        self,
        *,
        observation_runtime: WorkspaceSourceObservationRuntime,
        exclusion: WorkspaceSourceExclusion | None = None,
    ):
        if type(observation_runtime) is not WorkspaceSourceObservationRuntime:
            raise TypeError("exact Workspace observation runtime required")
        require_same_exclusion(observation_runtime._exclusion, exclusion)
        if exclusion is not None:
            exclusion.check_live()
        self._exclusion = exclusion
        self._pid = os.getpid()
        self._runtime = observation_runtime
        self._records: dict[
            WorkspaceObservedPackageMembership,
            tuple[
                WorkspaceRetainedRootObservation,
                WorkspaceObservedPackageMembershipEvidence,
                WorkspaceObservedRootEvidence,
            ],
        ] = {}
        self._lock = threading.RLock()
        self._closed = False

    def admit(
        self,
        *,
        observation: WorkspaceRetainedRootObservation,
        workspace_manifest_path: str,
        module_id: str,
        package_id: str,
    ) -> WorkspaceObservedPackageMembership:
        handles = self.admit_many(
            observation=observation,
            workspace_manifest_path=workspace_manifest_path,
            selections=((module_id, package_id),),
        )
        return handles[0]

    def admit_many(
        self,
        *,
        observation: WorkspaceRetainedRootObservation,
        workspace_manifest_path: str,
        selections: tuple[tuple[str, str], ...],
    ) -> tuple[WorkspaceObservedPackageMembership, ...]:
        """Issue independent package handles from one retained declaration scan.

        The operation shares only descriptive retained-composition work. Every
        selected package still receives its own nominal handle and evidence
        record, and the whole batch is checked against the original root under
        one final exclusion boundary before publication.
        """
        if type(selections) is not tuple:
            raise TypeError("exact membership selection tuple required")
        for selection in selections:
            if type(selection) is not tuple or len(selection) != 2:
                raise TypeError("exact module/package selection required")
            for value in selection:
                if type(value) is not str or not value or value != value.strip():
                    raise SourceObservationUnavailable("invalid_membership_selector")
        if len(selections) != len(set(selections)):
            raise SourceObservationUnavailable("duplicate_membership_selector")
        if self._exclusion is not None:
            self._exclusion.check_live()
        validate_relative_path(workspace_manifest_path)
        with self._lock:
            if self._closed or len(self._records) + len(selections) > 1024:
                raise SourceObservationUnavailable("membership_runtime_unavailable")
        if not selections:
            with self._runtime._lock:
                self._runtime._evidence(observation)
            return ()

        with self._runtime._lock:
            root_record = self._runtime._evidence(observation)
            observed = self._runtime.evidence(observation)
        projection = RetainedWorkspaceCompositionProvider().describe_retained(
            observation_runtime=self._runtime, observation=observation
        )
        selected: dict[
            tuple[str, str], tuple[dict[str, object], dict[str, object]]
        ] = {}
        declaration_roots = []
        workspace_paths = set()
        repository = cast(dict[str, Any], projection["repository"])
        requested = set(selections)
        for workspace in repository["workspaces"]:
            path = workspace["manifest_path"]
            if path in workspace_paths:
                raise SourceObservationUnavailable("duplicate_workspace_origin")
            workspace_paths.add(path)
            if workspace["repository_membership_handle"] not in (
                None,
                workspace["workspace_handle"],
            ):
                raise SourceObservationUnavailable(
                    "workspace_membership_handle_mismatch"
                )
            module_paths = set()
            for module in workspace["modules"]:
                if module["manifest_path"] in module_paths:
                    raise SourceObservationUnavailable("duplicate_module_origin")
                module_paths.add(module["manifest_path"])
                package_paths = set()
                for package in module["packages"]:
                    if package["manifest_path"] in package_paths:
                        raise SourceObservationUnavailable(
                            "duplicate_package_origin"
                        )
                    package_paths.add(package["manifest_path"])
                    declaration_roots.append(package["package_root"])
                    key = (module["module_id"], package["package_id"])
                    if path == workspace_manifest_path and key in requested:
                        if key in selected:
                            raise SourceObservationUnavailable(
                                "package_membership_not_exact"
                            )
                        selected[key] = (module, package)
        if len(selected) != len(selections):
            raise SourceObservationUnavailable("package_membership_not_exact")

        records = []
        handles = []
        for module_id, package_id in selections:
            module, package = selected[(module_id, package_id)]
            root = package["package_root"]
            # No inferred package-boundary exclusion: until an admitted boundary
            # policy exists, overlapping package roots cannot establish completeness.
            if (
                any(
                    other != root
                    and (
                        root == "."
                        or other == "."
                        or other.startswith(root + "/")
                        or root.startswith(other + "/")
                    )
                    for other in declaration_roots
                )
                or declaration_roots.count(root) != 1
            ):
                raise SourceObservationUnavailable(
                    "overlapping_package_roots_unsupported"
                )
            if package["visibility"] not in (
                "module",
                "workspace",
                "repository",
                "public",
            ):
                raise SourceObservationUnavailable("package_visibility_unsupported")
            prefix = "" if root == "." else root + "/"
            bodies = tuple(
                body
                for body in observed.bodies
                if body.relative_path.startswith(prefix)
            )
            manifest = package["manifest_path"][len(prefix) :]
            if not any(
                body.relative_path[len(prefix) :] == manifest for body in bodies
            ):
                raise SourceObservationUnavailable("package_manifest_not_retained")
            source = ContentDigest.of_bytes(
                canonical_json_bytes(
                    {
                        "contract": (
                            "aware.workspace.observed-package-source-identity.v1"
                        ),
                        "repository_binding_ref": observed.repository_binding_ref,
                        "observation_digest": observed.observation_digest,
                        "workspace_manifest_path": workspace_manifest_path,
                        "module_manifest_path": module["manifest_path"],
                        "module_id": module_id,
                        "package_id": package_id,
                        "package_kind": package["package_kind"],
                        "package_root": root,
                        "manifest_relative_path": manifest,
                        "visibility": package["visibility"],
                        "enumeration_policy": observed.policy_ref,
                        "members": [
                            [
                                b.relative_path[len(prefix) :],
                                b.content_digest,
                                b.size_bytes,
                            ]
                            for b in bodies
                        ],
                    }
                )
            )
            candidates = CodeSemanticCandidateListing(
                source,
                tuple(
                    CodeSemanticCandidate(
                        b.relative_path[len(prefix) :],
                        ContentDigest.of_wire(b.content_digest),
                    )
                    for b in bodies
                ),
            )
            evidence = WorkspaceObservedPackageMembershipEvidence(
                observed.repository_binding_ref,
                observed.observation_digest,
                workspace_manifest_path,
                module["manifest_path"],
                module_id,
                package_id,
                package["package_kind"],
                root,
                manifest,
                package["visibility"],
                source,
                candidates,
            )
            handle = object.__new__(WorkspaceObservedPackageMembership)
            handles.append(handle)
            records.append((observation, evidence, root_record))

        # Validate once after deriving the complete batch. Publication below
        # repeats the original identity check while holding the shared guard.
        self._runtime.revalidate(observation)
        with self._exclusion.mutation() if self._exclusion else nullcontext() as guard:
            with self._lock:
                if self._closed or len(self._records) + len(handles) > 1024:
                    raise SourceObservationUnavailable("membership_runtime_unavailable")
                if self._exclusion is not None:
                    self._runtime._check_record_locked(
                        observation, guard=guard, expected_record=root_record
                    )
                self._records.update(zip(handles, records, strict=True))
        return tuple(handles)

    def _record(self, membership):
        if self._exclusion is not None:
            self._exclusion.check_live()
        if (
            self._closed
            or type(membership) is not WorkspaceObservedPackageMembership
            or membership not in self._records
        ):
            raise SourceObservationUnavailable("foreign_or_expired_membership")
        observation, evidence, root_record = self._records[membership]
        with self._runtime._lock:
            if self._runtime._evidence(observation) is not root_record:
                raise SourceObservationUnavailable("observation_record_replaced")
            self._runtime.evidence(observation)
        return observation, evidence

    def evidence(
        self, membership: WorkspaceObservedPackageMembership
    ) -> WorkspaceObservedPackageMembershipEvidence:
        with self._lock:
            _, evidence = self._record(membership)
            return copy.deepcopy(evidence)

    def _evidence_after_observation_validation(
        self,
        membership: WorkspaceObservedPackageMembership,
        *,
        observation_runtime: WorkspaceSourceObservationRuntime,
        observation: WorkspaceRetainedRootObservation,
    ) -> WorkspaceObservedPackageMembershipEvidence:
        """Read detached evidence inside an owner-held validation interval.

        The caller must perform complete root currentness validation before and
        after the interval. This entrance preserves the original nominal
        membership and root-record identities without rereading the complete
        retained body set for every field comparison inside that interval.
        """

        with self._lock:
            if (
                self._closed
                or observation_runtime is not self._runtime
                or type(membership) is not WorkspaceObservedPackageMembership
            ):
                raise SourceObservationUnavailable(
                    "foreign_or_expired_membership"
                )
            record = self._records.get(membership)
            if record is None or record[0] is not observation:
                raise SourceObservationUnavailable("foreign_observation_origin")
            with self._runtime._lock:
                if self._runtime._evidence(observation) is not record[2]:
                    raise SourceObservationUnavailable(
                        "observation_record_replaced"
                    )
            return copy.deepcopy(record[1])

    def _validate_observation_origin_after_revalidation(
        self,
        membership: WorkspaceObservedPackageMembership,
        *,
        observation_runtime: WorkspaceSourceObservationRuntime,
        observation: WorkspaceRetainedRootObservation,
    ) -> None:
        self._evidence_after_observation_validation(
            membership,
            observation_runtime=observation_runtime,
            observation=observation,
        )

    def _validate_records_after_observation(
        self,
        records: tuple[
            tuple[WorkspaceObservedPackageMembership, object], ...
        ],
        *,
        observation: WorkspaceRetainedRootObservation,
        root_record: WorkspaceObservedRootEvidence,
    ) -> None:
        """Validate retained membership identities after root revalidation.

        The caller owns the shared observation revalidation. This entrance only
        checks that every original membership handle still points at its exact
        retained record and the same observation/root record; it deliberately
        does not reread the retained body set once per membership.
        """

        if type(records) is not tuple:
            raise TypeError("exact membership record tuple required")
        with self._lock:
            if self._closed:
                raise SourceObservationUnavailable(
                    "foreign_or_expired_membership"
                )
            for membership, expected in records:
                if type(membership) is not WorkspaceObservedPackageMembership:
                    raise SourceObservationUnavailable(
                        "foreign_or_expired_membership"
                    )
                current = self._records.get(membership)
                if current is not expected:
                    raise SourceObservationUnavailable(
                        "foreign_or_expired_membership"
                    )
                original_observation, _, original_root = current
                if (
                    original_observation is not observation
                    or original_root is not root_record
                ):
                    raise SourceObservationUnavailable(
                        "membership_record_changed"
                    )

    def read(
        self, membership: WorkspaceObservedPackageMembership, *, relative_path: str
    ) -> bytes:
        validate_relative_path(relative_path)
        with self._lock:
            observation, evidence = self._record(membership)
            if relative_path not in {
                c.relative_path for c in evidence.candidate_listing.candidates
            }:
                raise SourceObservationUnavailable("source_not_in_package")
            prefix = "" if evidence.package_root == "." else evidence.package_root + "/"
            return self._runtime.read(observation, relative_path=prefix + relative_path)

    def validate_runtime_origin(
        self, *, observation_runtime: WorkspaceSourceObservationRuntime
    ) -> None:
        """Check original resource identity even for an empty declaration scope."""
        with self._lock:
            if self._closed or observation_runtime is not self._runtime:
                raise SourceObservationUnavailable("foreign_or_closed_runtime_origin")

    def validate_observation_origin(
        self,
        membership: WorkspaceObservedPackageMembership,
        *,
        observation_runtime: WorkspaceSourceObservationRuntime,
        observation: WorkspaceRetainedRootObservation,
    ) -> None:
        """Validate original references, never equivalent inspection coordinates."""
        with self._lock:
            original, _ = self._record(membership)
            if observation_runtime is not self._runtime or observation is not original:
                raise SourceObservationUnavailable("foreign_observation_origin")
            self._runtime.revalidate(original)

    def read_declaring_module(
        self, membership: WorkspaceObservedPackageMembership
    ) -> bytes:
        """Read the original declaring module after complete nominal revalidation.

        The declaration is outside most package candidate sets. Its path comes
        only from the original membership record, never from a caller path or
        detached evidence. Retention failure cannot fall back to the checkout.
        """
        with self._lock:
            observation, evidence = self._record(membership)
            self._runtime.revalidate(observation)
            return self._runtime.read(
                observation, relative_path=evidence.module_manifest_path
            )

    def revalidate(self, membership: WorkspaceObservedPackageMembership) -> None:
        with self._lock:
            observation, _ = self._record(membership)
            self._runtime.revalidate(observation)

    def _check_record_locked(self, membership, *, guard, expected_record):
        if self._exclusion is None:
            raise SourceObservationUnavailable("source_exclusion_unavailable")
        self._exclusion.check_locked(guard)
        if self._closed or type(membership) is not WorkspaceObservedPackageMembership:
            raise SourceObservationUnavailable("foreign_or_expired_membership")
        record = self._records.get(membership)
        if record is None or record is not expected_record:
            raise SourceObservationUnavailable("foreign_or_expired_membership")
        self._runtime._check_record_locked(
            record[0], guard=guard, expected_record=record[2]
        )
        return record

    def release(self, membership: WorkspaceObservedPackageMembership) -> None:
        if self._exclusion is None:
            with self._lock:
                self._record(membership)
                del self._records[membership]
            return
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("membership_runtime_unavailable")
        with (
            self._exclusion.mutation(retiring=True)
            if self._exclusion
            else nullcontext()
        ):
            with self._lock:
                if (
                    self._closed
                    or type(membership) is not WorkspaceObservedPackageMembership
                    or membership not in self._records
                ):
                    raise SourceObservationUnavailable("foreign_or_expired_membership")
                del self._records[membership]

    def close(self) -> None:
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("membership_runtime_unavailable")
        with (
            self._exclusion.mutation(retiring=True)
            if self._exclusion
            else nullcontext()
        ):
            with self._lock:
                self._closed = True
                self._records.clear()
