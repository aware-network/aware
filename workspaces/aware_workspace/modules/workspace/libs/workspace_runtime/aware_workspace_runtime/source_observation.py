"""Nominal retained-root observations below package membership and Code admission."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
import threading
import time
from contextlib import nullcontext
from dataclasses import dataclass

from aware_workspace_sdk.repository_delta_retention import (
    WorkspaceRepositoryDeltaRetentionClient,
    WorkspaceRepositoryDeltaRetentionRefusal,
)

from .contracts import WorkspaceRepositoryBinding
from .observation import WorkspaceRepositoryObservationSession
from .repository_delta_store_contract import WorkspaceRepositoryDeltaStoreError
from .source_exclusion import WorkspaceSourceExclusion, require_same_exclusion
from .source_observation_io import (
    SourceObservationLimits,
    SourceObservationUnavailable,
    capture_complete_root,
    capture_exact_paths,
    capture_selected_root,
    identity,
    open_directory,
    validate_relative_path,
    validate_root_path,
)

_BINDING_LOCATION_SLOTS = tuple(
    (name, inspect.getattr_static(WorkspaceRepositoryBinding, name))
    for name in ("root_path", "binding_key", "filter_version")
)


def _digest(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


@dataclass(frozen=True, slots=True)
class WorkspaceRetainedObservedBody:
    relative_path: str
    body_ref: str
    content_digest: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class WorkspaceObservedRootEvidence:
    repository_binding_ref: str
    observation_epoch: str
    root_relative_path: str
    root_identity: tuple[int, int]
    policy_ref: str
    started_ns: int
    completed_ns: int
    bodies: tuple[WorkspaceRetainedObservedBody, ...]
    observation_digest: str


@dataclass(frozen=True, slots=True)
class WorkspaceObservedRootRevalidation:
    observation_digest: str
    started_ns: int
    completed_ns: int


@dataclass(frozen=True, slots=True)
class WorkspaceObservedDeclarationEvidence:
    repository_binding_ref: str
    observation_epoch: str
    root_identity: tuple[int, int]
    policy_ref: str
    started_ns: int
    completed_ns: int
    bodies: tuple[WorkspaceRetainedObservedBody, ...]
    observation_digest: str


@dataclass(frozen=True, slots=True)
class WorkspaceObservedSelectedPackageEvidence:
    declaration_digest: str
    repository_binding_ref: str
    observation_epoch: str
    workspace_manifest_path: str
    module_manifest_path: str
    module_id: str
    package_id: str
    package_kind: str
    package_root: str
    manifest_relative_path: str
    root_identity: tuple[int, int]
    excluded_nested_roots: tuple[str, ...]
    started_ns: int
    completed_ns: int
    bodies: tuple[WorkspaceRetainedObservedBody, ...]
    source_identity_digest: str


class WorkspaceRetainedDeclarationObservation:
    """Nominal declaration-only handle; never a package candidate authority."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Workspace runtime issues declaration handles")

    def __reduce__(self):
        raise TypeError("declaration handles cannot be serialized")


class WorkspaceRetainedSelectedPackageObservation:
    """Nominal selected candidate handle bound to its original declaration."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Workspace runtime issues selected package handles")

    def __reduce__(self):
        raise TypeError("selected package handles cannot be serialized")


class WorkspaceRetainedRootObservation:
    """Opaque preliminary reader handle; inspection evidence is not admission."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Workspace runtime issues observation handles")

    def __reduce__(self):
        raise TypeError("observation handles cannot be serialized")


class WorkspaceSourceObservationRuntime:
    """Host-composed resource over an admitted session and the existing body store.

    Its root selector is a host operation input, not proof of package membership.
    It issues no Code candidate, package source identity or semantic admission.
    """

    def __init__(
        self,
        *,
        session: WorkspaceRepositoryObservationSession,
        store: WorkspaceRepositoryDeltaRetentionClient,
        limits: SourceObservationLimits = SourceObservationLimits(),
        maximum_observations: int = 64,
        exclusion: WorkspaceSourceExclusion | None = None,
    ) -> None:
        if (
            type(session) is not WorkspaceRepositoryObservationSession
            or not session.authority_admitted
        ):
            raise SourceObservationUnavailable("repository_participant_unavailable")
        if type(store) is not WorkspaceRepositoryDeltaRetentionClient:
            raise SourceObservationUnavailable("retention_binding_mismatch")
        try:
            store.verify_repository_binding(expected_binding_ref=session.binding.binding_key)
        except WorkspaceRepositoryDeltaRetentionRefusal as error:
            raise SourceObservationUnavailable("retention_binding_mismatch") from error
        if type(limits) is not SourceObservationLimits:
            raise TypeError("exact observation limits required")
        limits.__post_init__()
        if (
            type(maximum_observations) is not int
            or not 0 < maximum_observations <= 1024
        ):
            raise ValueError("invalid observation capacity")
        require_same_exclusion(exclusion, exclusion)
        if exclusion is not None:
            exclusion.check_live()
        self._exclusion = exclusion
        self._pid = os.getpid()
        self._session = session
        binding = session.binding
        if type(binding) is not WorkspaceRepositoryBinding:
            raise SourceObservationUnavailable("repository_binding_origin_changed")
        root_path = binding.root_path
        self._location_origin = (
            session, binding, root_path, type(root_path), str(root_path),
            binding.binding_key, binding.filter_version,
        )
        self._store = store
        self._retention_binding_ref = session.binding.binding_key
        self._limits = limits
        self._capacity = maximum_observations
        self._epoch = session.current_snapshot.epoch
        self._root_fd = os.open(
            session.binding.root_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        self._location_root_fd = self._root_fd
        try:
            self._root_identity = identity(self._root_fd)
        except BaseException:
            os.close(self._root_fd)
            raise
        self._records: dict[
            WorkspaceRetainedRootObservation, WorkspaceObservedRootEvidence
        ] = {}
        self._declarations: dict[
            WorkspaceRetainedDeclarationObservation,
            WorkspaceObservedDeclarationEvidence,
        ] = {}
        self._selected: dict[
            WorkspaceRetainedSelectedPackageObservation,
            tuple[
                WorkspaceRetainedDeclarationObservation,
                WorkspaceObservedDeclarationEvidence,
                WorkspaceObservedSelectedPackageEvidence,
            ],
        ] = {}
        self._lock = threading.RLock()
        self._closed = False

    def _check_location_origin(self) -> None:
        session, binding, root_path, root_type, root_text, binding_key, policy = self._location_origin
        if (
            self._session is not session
            or type(session) is not WorkspaceRepositoryObservationSession
            or inspect.getattr_static(session, "binding") is not binding
            or type(binding) is not WorkspaceRepositoryBinding
            or type(root_path) is not root_type
            or type(self._root_fd) is not int
            or self._root_fd != self._location_root_fd
        ):
            raise SourceObservationUnavailable("repository_binding_origin_changed")
        for name, descriptor in _BINDING_LOCATION_SLOTS:
            if inspect.getattr_static(WorkspaceRepositoryBinding, name) is not descriptor:
                raise SourceObservationUnavailable("repository_binding_origin_changed")
        path, key, version = tuple(
            descriptor.__get__(binding, WorkspaceRepositoryBinding)
            for _, descriptor in _BINDING_LOCATION_SLOTS
        )
        if (
            path is not root_path or type(key) is not str or key != binding_key
            or type(version) is not str or version != policy
            or str(root_path) != root_text
        ):
            raise SourceObservationUnavailable("repository_binding_origin_changed")

    def close(self) -> None:
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("observation_lifetime_unavailable")
        descriptor = None
        with (
            self._exclusion.mutation(retiring=True)
            if self._exclusion
            else nullcontext(), self._lock
        ):
            if not self._closed:
                self._records.clear()
                self._declarations.clear()
                self._selected.clear()
                self._closed = True
                descriptor = self._location_root_fd
        # Descriptor cleanup is outside parent exclusion and source locks.
        if descriptor is not None:
            os.close(descriptor)

    def _check_record_locked(self, handle, *, guard, expected_record):
        if self._exclusion is None:
            raise SourceObservationUnavailable("source_exclusion_unavailable")
        self._exclusion.check_locked(guard)
        if self._closed or type(handle) is not WorkspaceRetainedRootObservation:
            raise SourceObservationUnavailable("foreign_or_expired_observation")
        record = self._records.get(handle)
        if record is None or record is not expected_record:
            raise SourceObservationUnavailable("foreign_or_expired_observation")
        return record

    def _check_declaration_record_locked(self, handle, *, guard, expected_record):
        if self._exclusion is None:
            raise SourceObservationUnavailable("source_exclusion_unavailable")
        self._exclusion.check_locked(guard)
        if self._closed or type(handle) is not WorkspaceRetainedDeclarationObservation:
            raise SourceObservationUnavailable("foreign_or_expired_declaration")
        record = self._declarations.get(handle)
        if record is None or record is not expected_record:
            raise SourceObservationUnavailable("foreign_or_expired_declaration")
        return record

    def _check_selected_record_locked(self, handle, *, guard, expected_record):
        if self._exclusion is None:
            raise SourceObservationUnavailable("source_exclusion_unavailable")
        self._exclusion.check_locked(guard)
        if self._closed or type(handle) is not WorkspaceRetainedSelectedPackageObservation:
            raise SourceObservationUnavailable("foreign_or_expired_selected_package")
        record = self._selected.get(handle)
        if record is None or record is not expected_record:
            raise SourceObservationUnavailable("foreign_or_expired_selected_package")
        self._check_declaration_record_locked(
            record[0], guard=guard, expected_record=record[1]
        )
        return record

    def _check(self) -> None:
        self._check_location_origin()
        if self._exclusion is not None:
            self._exclusion.check_live()
        if (
            os.getpid() != self._pid
            or self._closed
            or not self._session.authority_admitted
            or self._session.current_snapshot.epoch != self._epoch
        ):
            raise SourceObservationUnavailable("observation_lifetime_unavailable")
        try:
            self._store.verify_repository_binding(expected_binding_ref=self._retention_binding_ref)
        except WorkspaceRepositoryDeltaRetentionRefusal as error:
            raise SourceObservationUnavailable("retention_binding_mismatch") from error
        try:
            value = os.stat(self._session.binding.root_path, follow_symlinks=False)
        except OSError as error:
            raise SourceObservationUnavailable("repository_root_unavailable") from error
        if (value.st_dev, value.st_ino) != self._root_identity:
            raise SourceObservationUnavailable("repository_root_replaced")

    def _capture(
        self, root: str
    ) -> tuple[tuple[int, int], tuple[tuple[str, bytes], ...]]:
        self._check()
        try:
            fd = open_directory(self._root_fd, root)
            try:
                root_id = identity(fd)
                rows = capture_complete_root(fd, self._limits)
            finally:
                os.close(fd)
            final_fd = open_directory(self._root_fd, root)
            try:
                if identity(final_fd) != root_id:
                    raise SourceObservationUnavailable("observed_root_replaced")
            finally:
                os.close(final_fd)
        except OSError as error:
            raise SourceObservationUnavailable("root_unavailable") from error
        self._check()
        return root_id, rows

    def _capture_declarations(
        self,
    ) -> tuple[tuple[str, bytes], ...]:
        """Provisional discovery is checked against retained owner interpretation."""
        from .composition import (
            LocalCheckoutWorkspaceCompositionProvider,
            RetainedWorkspaceCompositionProvider,
            WorkspaceCompositionFailure,
        )

        self._check()
        live = LocalCheckoutWorkspaceCompositionProvider()
        try:
            provisional = live.describe(self._session.binding.root_path)
            paths = live.declaration_body_paths(provisional)
            rows = capture_exact_paths(self._root_fd, paths, self._limits)
            retained = RetainedWorkspaceCompositionProvider()
            description = retained.describe_captured_bodies(rows)
            if retained.declaration_body_paths(description) != paths:
                raise SourceObservationUnavailable("declaration_closure_changed")
        except (WorkspaceCompositionFailure, KeyError, OSError) as error:
            raise SourceObservationUnavailable(
                "declaration_closure_unavailable"
            ) from error
        self._check()
        return rows

    def _capture_selected(
        self, root: str, exclusions: tuple[str, ...]
    ) -> tuple[tuple[int, int], tuple[tuple[str, bytes], ...]]:
        self._check()
        try:
            fd = open_directory(self._root_fd, root)
            try:
                root_id = identity(fd)
                rows = capture_selected_root(
                    fd, self._limits, excluded_nested_roots=exclusions
                )
            finally:
                os.close(fd)
            final_fd = open_directory(self._root_fd, root)
            try:
                if identity(final_fd) != root_id:
                    raise SourceObservationUnavailable("selected_root_replaced")
            finally:
                os.close(final_fd)
        except OSError as error:
            raise SourceObservationUnavailable("selected_root_unavailable") from error
        self._check()
        return root_id, rows

    def observe_declarations(self) -> WorkspaceRetainedDeclarationObservation:
        """Issue a bounded declaration set under the original session/store."""
        with self._lock:
            self._check()
            if len(self._records) + len(self._declarations) >= self._capacity:
                raise SourceObservationUnavailable("observation_capacity_exceeded")
            started = time.monotonic_ns()
            rows = self._capture_declarations()
            refs = self._store.record_bodies(tuple(body for _, body in rows))
            bodies = tuple(
                WorkspaceRetainedObservedBody(path, ref, _digest(body), len(body))
                for (path, body), ref in zip(rows, refs, strict=True)
            )
            self._reread(bodies)
            self._check()
            completed = time.monotonic_ns()
            payload = {
                "contract": "aware.workspace.declaration-observation.v1",
                "repository": self._store.repository_binding_ref,
                "epoch": self._epoch,
                "root_identity": self._root_identity,
                "policy": "declared-repository-structure.v1",
                "started_ns": started,
                "completed_ns": completed,
                "bodies": [
                    (b.relative_path, b.body_ref, b.content_digest, b.size_bytes)
                    for b in bodies
                ],
            }
            evidence = WorkspaceObservedDeclarationEvidence(
                self._store.repository_binding_ref,
                self._epoch,
                self._root_identity,
                payload["policy"],
                started,
                completed,
                bodies,
                _digest(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
                ),
            )
            handle = object.__new__(WorkspaceRetainedDeclarationObservation)
        with self._exclusion.mutation() if self._exclusion else nullcontext():
            with self._lock:
                if (
                    self._closed
                    or len(self._records) + len(self._declarations) >= self._capacity
                ):
                    raise SourceObservationUnavailable(
                        "observation_capacity_or_lifetime"
                    )
                self._declarations[handle] = evidence
        return handle

    def _declaration_evidence(
        self, handle: WorkspaceRetainedDeclarationObservation
    ) -> WorkspaceObservedDeclarationEvidence:
        self._check()
        if (
            type(handle) is not WorkspaceRetainedDeclarationObservation
            or handle not in self._declarations
        ):
            raise SourceObservationUnavailable("foreign_or_expired_declaration")
        return self._declarations[handle]

    def declaration_evidence(
        self, handle: WorkspaceRetainedDeclarationObservation
    ) -> WorkspaceObservedDeclarationEvidence:
        with self._lock:
            evidence = self._declaration_evidence(handle)
            self._reread(evidence.bodies)
            return copy.deepcopy(evidence)

    def read_declaration(
        self, handle: WorkspaceRetainedDeclarationObservation, *, relative_path: str
    ) -> bytes:
        with self._lock:
            evidence = self._declaration_evidence(handle)
            self._reread(evidence.bodies)
            for body in evidence.bodies:
                if body.relative_path == relative_path:
                    result = self._store.resolve_body(body.body_ref)
                    if (
                        result is None
                        or len(result) != body.size_bytes
                        or _digest(result) != body.content_digest
                    ):
                        raise SourceObservationUnavailable("retained_body_unavailable")
                    return result
            raise SourceObservationUnavailable("body_not_observed")

    def read_declarations(
        self, handle: WorkspaceRetainedDeclarationObservation
    ) -> tuple[tuple[WorkspaceRetainedObservedBody, bytes], ...]:
        """One original bulk read; each body remains tied to its retained row."""
        with self._lock:
            evidence = self._declaration_evidence(handle)
            self._reread(evidence.bodies)
            rows = []
            for body in evidence.bodies:
                value = self._store.resolve_body(body.body_ref)
                if (
                    value is None
                    or len(value) != body.size_bytes
                    or _digest(value) != body.content_digest
                ):
                    raise SourceObservationUnavailable("retained_body_unavailable")
                rows.append((body, value))
            return tuple(rows)

    def revalidate_declarations(
        self, handle: WorkspaceRetainedDeclarationObservation
    ) -> WorkspaceObservedRootRevalidation:
        with self._lock:
            evidence = self._declaration_evidence(handle)
            self._reread(evidence.bodies)
            started = time.monotonic_ns()
            # The original observation already interpreted this complete
            # declaration closure. Reread every admitted body through confined
            # descriptors; identical bytes preserve its membership meaning.
            # Changing any parent declaration rejects before a new member can
            # enter. No path discovery, metadata shortcut or grammar replay is
            # needed to verify equality with that original retained closure.
            self._check()
            rows = capture_exact_paths(
                self._root_fd,
                tuple(body.relative_path for body in evidence.bodies),
                self._limits,
            )
            self._check()
            actual = tuple((path, _digest(body), len(body)) for path, body in rows)
            expected = tuple(
                (b.relative_path, b.content_digest, b.size_bytes)
                for b in evidence.bodies
            )
            if actual != expected or evidence.root_identity != self._root_identity:
                raise SourceObservationUnavailable("observed_declaration_changed")
            self._reread(evidence.bodies)
            self._check()
            return WorkspaceObservedRootRevalidation(
                evidence.observation_digest, started, time.monotonic_ns()
            )

    def release_declarations(
        self, handle: WorkspaceRetainedDeclarationObservation
    ) -> None:
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("observation_lifetime_unavailable")
        with self._exclusion.mutation(retiring=True) if self._exclusion else nullcontext():
            with self._lock:
                self._declaration_evidence(handle)
                if any(record[0] is handle for record in self._selected.values()):
                    raise SourceObservationUnavailable("selected_package_still_live")
                del self._declarations[handle]

    def _selected_description(
        self, declaration: WorkspaceRetainedDeclarationObservation
    ) -> dict[str, object]:
        from .composition import RetainedWorkspaceCompositionProvider

        evidence = self._declaration_evidence(declaration)
        self._reread(evidence.bodies)
        rows = []
        for body in evidence.bodies:
            value = self._store.resolve_body(body.body_ref)
            if value is None or _digest(value) != body.content_digest:
                raise SourceObservationUnavailable("retained_body_unavailable")
            rows.append((body.relative_path, value))
        provider = RetainedWorkspaceCompositionProvider()
        description = provider.describe_captured_bodies(tuple(rows))
        if provider.declaration_body_paths(description) != tuple(
            body.relative_path for body in evidence.bodies
        ):
            raise SourceObservationUnavailable("declaration_closure_changed")
        return description

    def observe_selected_package(
        self,
        *,
        declaration: WorkspaceRetainedDeclarationObservation,
        workspace_manifest_path: str,
        module_id: str,
        package_id: str,
    ) -> WorkspaceRetainedSelectedPackageObservation:
        """Capture one package and only its retained-authenticated nested exclusions."""
        from typing import Any, cast

        validate_relative_path(workspace_manifest_path)
        if any(type(value) is not str or not value for value in (module_id, package_id)):
            raise SourceObservationUnavailable("invalid_package_selector")
        with self._lock:
            original = self._declaration_evidence(declaration)
            if len(self._records) + len(self._declarations) + len(self._selected) >= self._capacity:
                raise SourceObservationUnavailable("observation_capacity_exceeded")
            self.revalidate_declarations(declaration)
            description = self._selected_description(declaration)
            repository = cast(dict[str, Any], description["repository"])
            all_roots: list[str] = []
            selected: list[tuple[dict[str, Any], dict[str, Any]]] = []
            for workspace in repository["workspaces"]:
                for module in workspace["modules"]:
                    for package in module["packages"]:
                        all_roots.append(package["package_root"])
                        if (
                            workspace["manifest_path"] == workspace_manifest_path
                            and module["module_id"] == module_id
                            and package["package_id"] == package_id
                        ):
                            selected.append((module, package))
            if len(selected) != 1:
                raise SourceObservationUnavailable("package_membership_not_exact")
            module, package = selected[0]
            root = package["package_root"]
            if all_roots.count(root) != 1:
                raise SourceObservationUnavailable("ambiguous_package_root")
            prefix = "" if root == "." else root + "/"
            nested = {
                other[len(prefix) :]
                for other in all_roots
                if other != root and other.startswith(prefix)
            }
            exclusions = tuple(
                sorted(
                    (
                        path for path in nested
                        if not any(path.startswith(parent + "/") for parent in nested if parent != path)
                    ),
                    key=str.encode,
                )
            )
            started = time.monotonic_ns()
            root_id, rows = self._capture_selected(root, exclusions)
            manifest = package["manifest_path"][len(prefix) :]
            if not any(path == manifest for path, _ in rows):
                raise SourceObservationUnavailable("package_manifest_not_observed")
            refs = self._store.record_bodies(tuple(body for _, body in rows))
            bodies = tuple(
                WorkspaceRetainedObservedBody(path, ref, _digest(body), len(body))
                for (path, body), ref in zip(rows, refs, strict=True)
            )
            self._reread(bodies)
            self.revalidate_declarations(declaration)
            completed = time.monotonic_ns()
            payload = {
                "contract": "aware.workspace.selected-package-source.v2",
                "declaration": original.observation_digest,
                "repository": original.repository_binding_ref,
                "epoch": original.observation_epoch,
                "workspace": workspace_manifest_path,
                "module_manifest": module["manifest_path"],
                "module": module_id,
                "package": package_id,
                "kind": package["package_kind"],
                "root": root,
                "manifest": manifest,
                "root_identity": root_id,
                "exclusions": exclusions,
                "members": [
                    (body.relative_path, body.content_digest, body.size_bytes)
                    for body in bodies
                ],
            }
            evidence = WorkspaceObservedSelectedPackageEvidence(
                original.observation_digest,
                original.repository_binding_ref,
                original.observation_epoch,
                workspace_manifest_path,
                module["manifest_path"],
                module_id,
                package_id,
                package["package_kind"],
                root,
                manifest,
                root_id,
                exclusions,
                started,
                completed,
                bodies,
                _digest(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()),
            )
            handle = object.__new__(WorkspaceRetainedSelectedPackageObservation)
        with self._exclusion.mutation() if self._exclusion else nullcontext():
            with self._lock:
                if (
                    self._closed
                    or len(self._records) + len(self._declarations) + len(self._selected)
                    >= self._capacity
                    or self._declaration_evidence(declaration) is not original
                ):
                    raise SourceObservationUnavailable("declaration_origin_changed")
                self._selected[handle] = (declaration, original, evidence)
        return handle

    def _selected_evidence(
        self, handle: WorkspaceRetainedSelectedPackageObservation
    ) -> tuple[WorkspaceRetainedDeclarationObservation, WorkspaceObservedSelectedPackageEvidence]:
        self._check()
        if type(handle) is not WorkspaceRetainedSelectedPackageObservation:
            raise SourceObservationUnavailable("foreign_or_expired_selected_package")
        record = self._selected.get(handle)
        if record is None or self._declaration_evidence(record[0]) is not record[1]:
            raise SourceObservationUnavailable("foreign_or_expired_selected_package")
        return record[0], record[2]

    def selected_package_evidence(
        self, handle: WorkspaceRetainedSelectedPackageObservation
    ) -> WorkspaceObservedSelectedPackageEvidence:
        with self._lock:
            _, evidence = self._selected_evidence(handle)
            self._reread(evidence.bodies)
            return copy.deepcopy(evidence)

    def read_selected_package_location(
        self, handle: WorkspaceRetainedSelectedPackageObservation,
    ) -> str:
        """Project the original outer location after full currentness checks.

        No ambient resolution or new binding is used. Failure retires only the
        registered selected observation, including when its type was changed.
        This before/after observation is not an external-writer fence.
        """
        original = None
        try:
            with self._lock:
                original = next((record for key, record in self._selected.items()
                                 if key is handle), None)
                _, evidence = self._selected_evidence(handle)
                self.revalidate_selected_package(handle)
                root = self._location_origin[4]
                location = root if evidence.package_root == "." else (
                    root.rstrip("/") + "/" + evidence.package_root
                )
                self.revalidate_selected_package(handle)
                if next((record for key, record in self._selected.items()
                         if key is handle), None) is not original:
                    raise SourceObservationUnavailable("selected_source_replaced")
                return location
        except BaseException:
            # Source locks must be released before acquiring parent exclusion.
            # Retire only this original family; foreign values never dispatch
            # hashing/equality or revoke a different registered observation.
            if original is not None:
                with (
                    self._exclusion.mutation(retiring=True) if self._exclusion else nullcontext()
                ), self._lock:
                    if next((record for key, record in self._selected.items()
                             if key is handle), None) is original:
                        self._selected = {key: record for key, record in self._selected.items()
                                          if key is not handle}
            raise

    def read_selected_package(
        self,
        handle: WorkspaceRetainedSelectedPackageObservation,
        *,
        relative_path: str,
    ) -> bytes:
        validate_relative_path(relative_path)
        with self._lock:
            _, evidence = self._selected_evidence(handle)
            self._reread(evidence.bodies)
            for body in evidence.bodies:
                if body.relative_path == relative_path:
                    value = self._store.resolve_body(body.body_ref)
                    if value is None or _digest(value) != body.content_digest:
                        raise SourceObservationUnavailable("retained_body_unavailable")
                    return value
            raise SourceObservationUnavailable("body_not_observed")

    def revalidate_selected_package(
        self, handle: WorkspaceRetainedSelectedPackageObservation
    ) -> WorkspaceObservedRootRevalidation:
        with self._lock:
            declaration, evidence = self._selected_evidence(handle)
            self.revalidate_declarations(declaration)
            self._reread(evidence.bodies)
            started = time.monotonic_ns()
            root_id, rows = self._capture_selected(
                evidence.package_root, evidence.excluded_nested_roots
            )
            actual = tuple((path, _digest(body), len(body)) for path, body in rows)
            expected = tuple(
                (body.relative_path, body.content_digest, body.size_bytes)
                for body in evidence.bodies
            )
            if root_id != evidence.root_identity or actual != expected:
                raise SourceObservationUnavailable("selected_package_changed")
            self._reread(evidence.bodies)
            self.revalidate_declarations(declaration)
            return WorkspaceObservedRootRevalidation(
                evidence.source_identity_digest, started, time.monotonic_ns()
            )

    def release_selected_package(
        self, handle: WorkspaceRetainedSelectedPackageObservation
    ) -> None:
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("observation_lifetime_unavailable")
        with self._exclusion.mutation(retiring=True) if self._exclusion else nullcontext():
            with self._lock:
                self._selected_evidence(handle)
                del self._selected[handle]

    def observe(self, *, root_relative_path: str) -> WorkspaceRetainedRootObservation:
        validate_root_path(root_relative_path)
        with self._lock:
            self._check()
            if len(self._records) >= self._capacity:
                raise SourceObservationUnavailable("observation_capacity_exceeded")
            started = time.monotonic_ns()
            root_id, rows = self._capture(root_relative_path)
            refs = self._store.record_bodies(tuple(body for _, body in rows))
            bodies = tuple(
                WorkspaceRetainedObservedBody(path, ref, _digest(body), len(body))
                for (path, body), ref in zip(rows, refs, strict=True)
            )
            self._reread(bodies)
            self._check()
            completed = time.monotonic_ns()
            # Earlier observation domain: no Code candidate, package authority,
            # completion or later revalidation digest may enter this evidence.
            payload = {
                "contract": "aware.workspace.observed-root-retention.v1",
                "repository": self._store.repository_binding_ref,
                "epoch": self._epoch,
                "root": root_relative_path,
                "root_identity": root_id,
                "policy": "all-regular-files-no-exclusions.v1",
                "started_ns": started,
                "completed_ns": completed,
                "bodies": [
                    (b.relative_path, b.body_ref, b.content_digest, b.size_bytes)
                    for b in bodies
                ],
            }
            evidence = WorkspaceObservedRootEvidence(
                self._store.repository_binding_ref,
                self._epoch,
                root_relative_path,
                root_id,
                payload["policy"],
                started,
                completed,
                bodies,
                _digest(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
                ),
            )
            handle = object.__new__(WorkspaceRetainedRootObservation)
        with self._exclusion.mutation() if self._exclusion else nullcontext():
            with self._lock:
                if self._closed or len(self._records) >= self._capacity:
                    raise SourceObservationUnavailable(
                        "observation_capacity_or_lifetime"
                    )
                self._records[handle] = evidence
        return handle

    def _evidence(
        self, handle: WorkspaceRetainedRootObservation
    ) -> WorkspaceObservedRootEvidence:
        self._check()
        if (
            type(handle) is not WorkspaceRetainedRootObservation
            or handle not in self._records
        ):
            raise SourceObservationUnavailable("foreign_or_expired_observation")
        return self._records[handle]

    def _reread(self, bodies: tuple[WorkspaceRetainedObservedBody, ...]) -> None:
        for body in bodies:
            try:
                value = self._store.resolve_body(body.body_ref)
            except (WorkspaceRepositoryDeltaStoreError, OSError) as error:
                raise SourceObservationUnavailable(
                    "retained_body_unavailable"
                ) from error
            if (
                value is None
                or len(value) != body.size_bytes
                or _digest(value) != body.content_digest
            ):
                raise SourceObservationUnavailable("retained_body_unavailable")

    def evidence(
        self, handle: WorkspaceRetainedRootObservation
    ) -> WorkspaceObservedRootEvidence:
        with self._lock:
            evidence = self._evidence(handle)
            self._reread(evidence.bodies)
            return copy.deepcopy(evidence)

    def read(
        self, handle: WorkspaceRetainedRootObservation, *, relative_path: str
    ) -> bytes:
        with self._lock:
            evidence = self._evidence(handle)
            self._reread(evidence.bodies)
            for body in evidence.bodies:
                if body.relative_path == relative_path:
                    result = self._store.resolve_body(body.body_ref)
                    if (
                        result is None
                        or len(result) != body.size_bytes
                        or _digest(result) != body.content_digest
                    ):
                        raise SourceObservationUnavailable("retained_body_unavailable")
                    return result
            raise SourceObservationUnavailable("body_not_observed")

    def revalidate(
        self, handle: WorkspaceRetainedRootObservation
    ) -> WorkspaceObservedRootRevalidation:
        with self._lock:
            evidence = self._evidence(handle)
            self._reread(evidence.bodies)
            started = time.monotonic_ns()
            root_id, rows = self._capture(evidence.root_relative_path)
            actual = tuple((path, _digest(body), len(body)) for path, body in rows)
            expected = tuple(
                (b.relative_path, b.content_digest, b.size_bytes)
                for b in evidence.bodies
            )
            if root_id != evidence.root_identity or actual != expected:
                raise SourceObservationUnavailable("observed_root_changed")
            self._reread(evidence.bodies)
            self._check()
            return WorkspaceObservedRootRevalidation(
                evidence.observation_digest, started, time.monotonic_ns()
            )

    def release(self, handle: WorkspaceRetainedRootObservation) -> None:
        if self._exclusion is None:
            with self._lock:
                self._evidence(handle)
                del self._records[handle]
            return
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("observation_lifetime_unavailable")
        with (
            self._exclusion.mutation(retiring=True)
            if self._exclusion
            else nullcontext(), self._lock
        ):
            if (
                self._closed
                or type(handle) is not WorkspaceRetainedRootObservation
                or handle not in self._records
            ):
                raise SourceObservationUnavailable("foreign_or_expired_observation")
            del self._records[handle]
