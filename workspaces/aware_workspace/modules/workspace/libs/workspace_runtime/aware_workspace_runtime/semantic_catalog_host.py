"""Sole paired catalog transaction, entered only by authenticated parent assembly.

This internal mechanism does not authenticate a caller merely because its validator
succeeds. Resident assembly retains its existing nominal generation admission;
future direct assembly must establish its own original bootstrap.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
from collections.abc import Callable
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from aware_code_semantic_contract_runtime import (
    AdmittedCodeSemanticContractCatalog,
    CodeSemanticContractCatalog,
    CodeSemanticContractCatalogResolver,
    CodeSemanticDependencyPlanner,
    ContentDigest,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.catalog_host_leg import (
    PreparedCodeCatalogLeg,
    bind_code_catalog_leg_publication,
    code_catalog_leg_snapshot,
    prepare_code_catalog_leg,
    published_code_catalog_leg,
    revoke_code_catalog_leg,
    validate_code_catalog_leg,
)

from .catalog_publication_epochs import _CatalogPublicationRecords
from .command_lifetime import (
    WorkspaceCommandLifetimeRuntime,
    WorkspaceCommandLifetimeUnavailable,
)
from .materialization_membership_catalog import (
    AdmittedWorkspaceSemanticMaterializationMembershipCatalog,
    WorkspaceSemanticMaterializationMembershipCatalog,
    WorkspaceSemanticMaterializationMembershipResolver,
    _issue_workspace_semantic_materialization_membership_catalog,
    _revoke_workspace_semantic_materialization_membership_catalog,
)
from .source_admission_catalog import WorkspaceV3GraphSourceCorrespondence


@dataclass(frozen=True, slots=True)
class WorkspaceJointCatalogResolvers:
    code: CodeSemanticContractCatalogResolver
    workspace: WorkspaceSemanticMaterializationMembershipResolver
    contribution_digest: str
    code_admission: AdmittedCodeSemanticContractCatalog
    workspace_admission: AdmittedWorkspaceSemanticMaterializationMembershipCatalog


@dataclass(slots=True)
class _PreparedSuccessorCatalogPair:
    expected: CatalogPublicationExpectation
    code_leg: PreparedCodeCatalogLeg
    workspace_admission: AdmittedWorkspaceSemanticMaterializationMembershipCatalog
    workspace_snapshot: WorkspaceSemanticMaterializationMembershipCatalog
    workspace_reader: Callable[[], WorkspaceSemanticMaterializationMembershipCatalog]
    workspace_body: bytes
    workspace_coordinates: _CatalogCoordinates
    liveness: dict[str, object]
    provider_executable_bindings: object
    dependency_planner_bindings: object
    source_correspondences: tuple[WorkspaceV3GraphSourceCorrespondence, ...]


def _source_correspondence_entries(snapshot, correspondences):
    if type(correspondences) is not tuple:
        raise TypeError("original source correspondence tuple required")
    entries = {entry.package.package_ref: entry for entry in snapshot.entries}
    result = []
    previous = None
    for correspondence in correspondences:
        if type(correspondence) is not WorkspaceV3GraphSourceCorrespondence:
            raise TypeError("original Workspace source correspondence required")
        package_ref = correspondence.package().package_ref
        if (
            package_ref not in entries
            or (previous is not None and previous.encode() >= package_ref.encode())
        ):
            raise RuntimeError("source correspondences differ from successor entries")
        result.append((correspondence, entries[package_ref]))
        previous = package_ref
    required = {
        entry.package.package_ref
        for entry in snapshot.entries
        if entry.participation_policy.policy_revision == 2
    }
    if not required <= {entry.package.package_ref for _, entry in result}:
        raise RuntimeError("product-eligible entry lacks original source correspondence")
    return tuple(result)


def _validate_source_correspondences(snapshot, correspondences):
    for correspondence, entry in _source_correspondence_entries(
        snapshot, correspondences
    ):
        correspondence.validate_catalog_entry(entry)


def _check_source_correspondences_locked(snapshot, correspondences, guard):
    for correspondence, entry in _source_correspondence_entries(
        snapshot, correspondences
    ):
        correspondence.check_catalog_entry_locked(entry, guard)


class _CommandCatalogParent:
    """Original parent/guard binding; construction is not bootstrap authentication."""

    def __init__(self, owner, parent, invocation):
        if (
            type(owner) is not WorkspaceCommandLifetimeRuntime
            or type(invocation) is not DirectInvocationExpectation
        ):
            raise TypeError("original command runtime and exact invocation required")
        self.owner, self.parent = owner, parent
        self.invocation = DirectInvocationExpectation(
            invocation.invocation_identity,
            invocation.lifetime_epoch_identity,
            invocation.process_id,
        )
        self.methods = {}
        for name in (
            "validate_direct_invocation_parent",
            "acquire_catalog_epoch_exclusion",
            "release_catalog_epoch_exclusion",
            "validate_catalog_epoch_exclusion",
        ):
            descriptor = inspect.getattr_static(owner, name)
            method = getattr(owner, name)
            if (
                not inspect.ismethod(method)
                or method.__self__ is not owner
                or method.__func__ is not descriptor
            ):
                raise TypeError("original command method required")
            self.methods[name] = descriptor, method
        self.validate_catalog_parent()
        self.records = _CatalogPublicationRecords(
            owner=owner, parent=parent, invocation=self.invocation
        )
        self.expected = None

    def _call(self, name, *args, **kwargs):
        descriptor, method = self.methods[name]
        if inspect.getattr_static(self.owner, name) is not descriptor:
            raise RuntimeError("original command method substituted")
        result = method(*args, **kwargs)
        if inspect.getattr_static(self.owner, name) is not descriptor:
            raise RuntimeError("original command method substituted")
        return result

    def validate_catalog_parent(self):
        if (
            self._call(
                "validate_direct_invocation_parent",
                self.parent,
                expected=self.invocation,
            )
            is not None
        ):
            raise RuntimeError("command parent validation returned a value")

    @contextmanager
    def guarded(self):
        # Reentrant consumers participate in the exact already-held owner guard.
        # The owner lock prevents borrowing a guard held by another thread.
        with self.owner._lock:
            existing = self.owner._guard
            if existing is not None:
                self._call(
                    "validate_catalog_epoch_exclusion",
                    existing,
                    parent=self.parent,
                    expected=self.invocation,
                )
                yield existing
                return
            guard = self._call(
                "acquire_catalog_epoch_exclusion", self.parent, expected=self.invocation
            )
            try:
                yield guard
            finally:
                self._call("release_catalog_epoch_exclusion", guard)

    def prepare_expectation(
        self,
        *,
        code_catalog,
        workspace_catalog,
        contribution_digest,
    ):
        if not code_catalog.entries:
            raise RuntimeError("initial command requires Code contributions")
        if workspace_catalog.entries:
            raise RuntimeError("initial command membership must be empty")
        epoch = CatalogPairEpochExpectation(
            self.invocation,
            object(),
            deepcopy(code_catalog.catalog_root_digest),
            deepcopy(workspace_catalog.catalog_root_digest),
            ContentDigest(contribution_digest),
        )
        expected = CatalogPublicationExpectation(
            object(),
            None,
            epoch,
            ContentDigest.of_bytes(canonical_json_bytes([])),
        )
        return expected

    def publish_initial(self, *, code_leg, workspace_admission, expected):
        with self.guarded() as guard:
            preparation = self.records._prepare(
                guard, expected=expected, pair=(code_leg, workspace_admission)
            )
            bind_code_catalog_leg_publication(code_leg, preparation, guard)
            self.records._commit(guard, preparation, expected=expected, transfer=None)
            self.expected = expected.successor

    def current_record(self, expected):
        self.validate_catalog_parent()
        return self.records._read_current_for_parent(expected=expected)

    def retire_records(self):
        if self.records._closed:
            return
        try:
            with self.guarded() as guard:
                self.records._close(guard)
        except WorkspaceCommandLifetimeUnavailable:
            # Original parent/process loss already makes every record read refuse.
            return

    def published(self):
        # The existing record is the visibility decision, never a second flag.
        return self.records._current is not None


class WorkspaceSemanticCatalogHost:
    """Internal owner mechanism; no public constructor or independent trust root."""

    _issuing_workspace: bool
    _contribution: Any
    _parent: Any
    _descriptor: object
    _validate_parent: Callable[[], None]
    _pid: int
    _lock: Any
    _phase: str
    _code_leg: PreparedCodeCatalogLeg | None
    _workspace_admission: (
        AdmittedWorkspaceSemanticMaterializationMembershipCatalog | None
    )
    _code_admission: AdmittedCodeSemanticContractCatalog | None
    _result: WorkspaceJointCatalogResolvers | None
    _command_parent: _CommandCatalogParent | None
    _successor_attempts: dict[object, _PreparedSuccessorCatalogPair]

    def __new__(cls):
        raise TypeError("semantic_catalog_host_requires_original_assembly")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("semantic_catalog_host_is_final")

    def __reduce__(self):
        raise TypeError("semantic_catalog_host_is_process_local")

    def validate_catalog_parent(self) -> None:
        if self._pid != os.getpid() or self._phase == "closed":
            raise RuntimeError("semantic_materialization_catalog_host_not_live")
        if (
            inspect.getattr_static(self._parent, "validate_catalog_parent")
            is not self._descriptor
        ):
            raise RuntimeError("catalog_parent_entrance_substituted")
        if self._validate_parent() is not None:
            raise RuntimeError("catalog_parent_validation_invalid")
        if (
            inspect.getattr_static(self._parent, "validate_catalog_parent")
            is not self._descriptor
        ):
            raise RuntimeError("catalog_parent_entrance_substituted")

    def catalogs_published(self) -> bool:
        self.validate_catalog_parent()
        return (
            self._command_parent.published()
            if self._command_parent is not None
            else self._phase == "published"
        )

    def _workspace_live(self) -> bool:
        try:
            self.validate_catalog_parent()
            return self._issuing_workspace or self.catalogs_published()
        except Exception:
            return False

    def admit_catalogs(
        self,
        *,
        code_catalog,
        workspace_catalog_reader: Callable[
            [], WorkspaceSemanticMaterializationMembershipCatalog
        ],
        provider_executable_bindings,
        dependency_planner_bindings,
    ):
        self.validate_catalog_parent()
        with self._lock:
            self.validate_catalog_parent()
            if self._phase != "new":
                raise RuntimeError("semantic_materialization_catalogs_already_admitted")
            self._phase = "preparing"
        code_leg = None
        workspace_admission = None
        try:
            # Keep the exact reader from the authenticated contribution.
            if not callable(workspace_catalog_reader):
                raise TypeError("workspace_catalog_reader_must_be_callable")
            publication = None
            captured = None
            if self._command_parent is not None:
                captured = _capture_workspace_catalog(workspace_catalog_reader())
                snapshot, body, coordinates = captured
                publication = self._command_parent.prepare_expectation(
                    code_catalog=code_catalog,
                    workspace_catalog=snapshot,
                    contribution_digest=_contribution_digest(
                        code_catalog=code_catalog,
                        workspace_catalog=snapshot,
                        provider_executable_bindings=provider_executable_bindings,
                        dependency_planner_bindings=dependency_planner_bindings,
                    ),
                )
            code_leg = prepare_code_catalog_leg(
                joint_host=self,
                catalog=code_catalog,
                provider_executable_bindings=provider_executable_bindings,
                dependency_planner_bindings=dependency_planner_bindings,
                publication=publication,
            )
            if captured is None:
                captured = _capture_workspace_catalog(workspace_catalog_reader())
            snapshot, body, coordinates = captured
            validate_code_catalog_leg(code_leg)
            _assert_workspace_catalog_source(
                workspace_catalog_reader, body, coordinates
            )
            validate_code_catalog_leg(code_leg)
            self._issuing_workspace = True
            try:
                workspace_admission = (
                    _issue_workspace_semantic_materialization_membership_catalog(
                        catalog=snapshot,
                        host_liveness=self._workspace_live,
                    )
                )
            finally:
                self._issuing_workspace = False
            _assert_workspace_catalog_source(
                workspace_catalog_reader, body, coordinates
            )
            validate_code_catalog_leg(code_leg)
            code_snapshot = code_catalog_leg_snapshot(code_leg)
            digest = _contribution_digest(
                code_catalog=code_snapshot,
                workspace_catalog=snapshot,
                provider_executable_bindings=provider_executable_bindings,
                dependency_planner_bindings=dependency_planner_bindings,
            )
            _assert_workspace_catalog_source(
                workspace_catalog_reader, body, coordinates
            )
            validate_code_catalog_leg(code_leg)
            # The same lock guards the original resident parent close. No source
            # reader is invoked while it is held.
            with self._lock:
                self.validate_catalog_parent()
                if self._phase != "preparing":
                    raise RuntimeError("semantic_materialization_catalog_host_moved")
                self._code_leg = code_leg
                self._workspace_admission = workspace_admission
                if self._command_parent is not None:
                    if publication is None:
                        raise RuntimeError("original publication missing")
                    if publication.successor.contribution_digest != ContentDigest(
                        digest
                    ):
                        raise RuntimeError("prepared contribution changed")
                    self._command_parent.publish_initial(
                        code_leg=code_leg,
                        workspace_admission=workspace_admission,
                        expected=publication,
                    )
                self._phase = "published"
            # Code's published accessor rereads its source, so invoke outside the
            # publication lock and revoke both if that final read refuses.
            code_admission, code_resolver = published_code_catalog_leg(code_leg)
            result = WorkspaceJointCatalogResolvers(
                code=code_resolver,
                workspace=WorkspaceSemanticMaterializationMembershipResolver(
                    workspace_admission
                ),
                contribution_digest=digest,
                code_admission=code_admission,
                workspace_admission=workspace_admission,
            )
            with self._lock:
                self.validate_catalog_parent()
                if self._phase != "published":
                    raise RuntimeError("semantic_materialization_catalog_host_moved")
                self._contribution = (
                    code_snapshot,
                    snapshot,
                    workspace_catalog_reader,
                    provider_executable_bindings,
                    dependency_planner_bindings,
                )
                self._code_admission = code_admission
                self._result = result
            return result
        except BaseException:
            with self._lock:
                self._phase = "closed"
            try:
                if self._command_parent is not None:
                    self._command_parent.retire_records()
            finally:
                self._revoke_pair(code_leg, workspace_admission)
            raise

    def prepare_successor_catalogs(
        self,
        *,
        code_catalog: CodeSemanticContractCatalog,
        workspace_catalog_reader: Callable[
            [], WorkspaceSemanticMaterializationMembershipCatalog
        ],
        provider_executable_bindings,
        dependency_planner_bindings,
        source_correspondences: tuple[WorkspaceV3GraphSourceCorrespondence, ...] = (),
    ) -> tuple[object, CatalogPublicationExpectation]:
        """Prepare both hidden successor legs against the exact current pair.

        This performs all source reads outside the final publication exclusion.
        The returned nominal preparation is usable only by Code's completion
        transfer runtime and this original host. It is not a catalog resolver.
        """
        self.validate_catalog_parent()
        command = self._command_parent
        if command is None or self._phase != "published" or self._result is None:
            raise RuntimeError("successor_catalog_preparation_unavailable")
        if not callable(workspace_catalog_reader):
            raise TypeError("workspace_catalog_reader_must_be_callable")
        predecessor = self.read_initial_publication()
        captured = _capture_workspace_catalog(workspace_catalog_reader())
        snapshot, body, coordinates = captured
        if not snapshot.entries:
            raise RuntimeError("successor_workspace_membership_must_be_nonempty")
        _source_correspondence_entries(snapshot, source_correspondences)
        digest = _contribution_digest(
            code_catalog=code_catalog,
            workspace_catalog=snapshot,
            provider_executable_bindings=provider_executable_bindings,
            dependency_planner_bindings=dependency_planner_bindings,
        )
        successor = CatalogPairEpochExpectation(
            DirectInvocationExpectation(
                predecessor.invocation.invocation_identity,
                predecessor.invocation.lifetime_epoch_identity,
                predecessor.invocation.process_id,
            ),
            object(),
            deepcopy(code_catalog.catalog_root_digest),
            deepcopy(snapshot.catalog_root_digest),
            ContentDigest(digest),
        )
        expected = CatalogPublicationExpectation(
            object(),
            predecessor,
            successor,
            _workspace_entry_inputs_digest(snapshot),
        )
        code_leg = None
        workspace_admission = None
        preparation = None
        liveness: dict[str, object] = {
            "preparing": True,
            "closed": False,
            "preparation": None,
        }

        def workspace_live() -> bool:
            try:
                self.validate_catalog_parent()
                if liveness["closed"]:
                    return False
                if liveness["preparing"]:
                    return self._issuing_workspace
                retained = liveness["preparation"]
                if retained is None:
                    return False
                record = command.current_record(expected.successor)
                return (
                    record.preparation is retained
                    and record.attempt.pair[1] is workspace_admission
                )
            except Exception:
                return False

        try:
            code_leg = prepare_code_catalog_leg(
                joint_host=self,
                catalog=code_catalog,
                provider_executable_bindings=provider_executable_bindings,
                dependency_planner_bindings=dependency_planner_bindings,
                publication=expected,
            )
            validate_code_catalog_leg(code_leg)
            _assert_workspace_catalog_source(
                workspace_catalog_reader, body, coordinates
            )
            self._issuing_workspace = True
            try:
                workspace_admission = (
                    _issue_workspace_semantic_materialization_membership_catalog(
                        catalog=snapshot,
                        host_liveness=workspace_live,
                    )
                )
            finally:
                self._issuing_workspace = False
            _assert_workspace_catalog_source(
                workspace_catalog_reader, body, coordinates
            )
            validate_code_catalog_leg(code_leg)
            _validate_source_correspondences(snapshot, source_correspondences)
            with command.guarded() as guard:
                command.records._read_current(guard, expected=predecessor)
                _check_source_correspondences_locked(
                    snapshot, source_correspondences, guard
                )
                preparation = command.records._prepare(
                    guard,
                    expected=expected,
                    pair=(code_leg, workspace_admission),
                )
                attempt = _PreparedSuccessorCatalogPair(
                    expected,
                    code_leg,
                    workspace_admission,
                    snapshot,
                    workspace_catalog_reader,
                    body,
                    coordinates,
                    liveness,
                    provider_executable_bindings,
                    dependency_planner_bindings,
                    source_correspondences,
                )
                self._successor_attempts[preparation] = attempt
                liveness["preparation"] = preparation
                bind_code_catalog_leg_publication(code_leg, preparation, guard)
            liveness["preparing"] = False
            self.validate_prepared_catalog_publication(preparation, expected=expected)
            return preparation, expected
        except BaseException:
            liveness["closed"] = True
            liveness["preparing"] = False
            if preparation is not None:
                self._successor_attempts.pop(preparation, None)
                try:
                    with command.guarded() as guard:
                        command.records._discard(guard, preparation)
                except BaseException:
                    pass
            self._revoke_pair(code_leg, workspace_admission)
            raise

    def discard_successor_catalogs(self, preparation, *, expected) -> None:
        """Discard only this unpublished attempt; preserve the live predecessor."""
        self.validate_catalog_parent()
        attempt = self._successor_attempts.get(preparation)
        if attempt is None:
            raise RuntimeError("original successor preparation differs")
        command = self._command_parent
        assert command is not None
        with command.guarded() as guard:
            pending = command.records._pending(preparation, expected)
            if pending.pair != (attempt.code_leg, attempt.workspace_admission):
                raise RuntimeError("original prepared pair differs")
            command.records._discard(guard, preparation)
            self._successor_attempts.pop(preparation)
            attempt.liveness["closed"] = True
        self._revoke_pair(attempt.code_leg, attempt.workspace_admission)

    def validate_prepared_catalog_publication(self, preparation, *, expected):
        self.validate_catalog_parent()
        command = self._command_parent
        if command is None:
            raise RuntimeError("original command preparation required")
        if expected.predecessor is not None:
            attempt = self._successor_attempts.get(preparation)
            if attempt is None:
                raise RuntimeError("original successor preparation differs")
            validate_code_catalog_leg(attempt.code_leg)
            _assert_workspace_catalog_source(
                attempt.workspace_reader,
                attempt.workspace_body,
                attempt.workspace_coordinates,
            )
            with command.guarded() as guard:
                pending = command.records._pending(preparation, expected)
                if pending.pair != (
                    attempt.code_leg,
                    attempt.workspace_admission,
                ):
                    raise RuntimeError("original prepared pair differs")
                _check_source_correspondences_locked(
                    attempt.workspace_snapshot, attempt.source_correspondences, guard
                )
            validate_code_catalog_leg(attempt.code_leg)
            _assert_workspace_catalog_source(
                attempt.workspace_reader,
                attempt.workspace_body,
                attempt.workspace_coordinates,
            )
            return
        with command.guarded() as guard:
            command.records._guard(guard)
            attempt = command.records._pending(preparation, expected)
            if (
                attempt.pair[0] is not self._code_leg
                or attempt.pair[1] is not self._workspace_admission
            ):
                raise RuntimeError("original prepared pair differs")

    def validate_catalog_epoch_publication_guard(self, guard, *, preparation, expected):
        self.validate_catalog_parent()
        command = self._command_parent
        if command is None:
            raise RuntimeError("original command required")
        command.records._guard(guard)
        if expected.predecessor is None:
            attempt = command.records._pending(preparation, expected)
            if (
                attempt.pair[0] is not self._code_leg
                or attempt.pair[1] is not self._workspace_admission
            ):
                raise RuntimeError("original prepared pair differs")
        else:
            retained = self._successor_attempts.get(preparation)
            if retained is None:
                raise RuntimeError("original successor preparation differs")
            attempt = command.records._pending(preparation, expected)
            if attempt.pair != (
                retained.code_leg,
                retained.workspace_admission,
            ):
                raise RuntimeError("original prepared pair differs")
        command.records._guard(guard)

    def validate_committed_catalog_publication(
        self, preparation, completion_transfer, *, expected
    ):
        self.validate_catalog_parent()
        command = self._command_parent
        if command is None:
            raise RuntimeError("original command required")
        with command.guarded() as guard:
            record = command.records._read_committed(
                guard, preparation, transfer=completion_transfer
            )
            if not record.attempt.successor.matches(
                command.records._expected(expected)[1]
            ):
                raise RuntimeError("committed successor differs")

    def validate_committed_successor_epoch_guard(
        self, guard, preparation, completion_transfer, *, expected
    ) -> None:
        """Check the committed current pair under the original held exclusion.

        Code uses this only for its final in-guard epoch adoption check. Source
        reads and transfer validation occur before acquiring the exclusion.
        """
        command = self._command_parent
        if (
            command is None
            or self._pid != os.getpid()
            or self._phase != "published"
            or type(expected) is not CatalogPublicationExpectation
            or expected.predecessor is None
            or completion_transfer is None
        ):
            raise RuntimeError("committed successor unavailable")
        record = command.records._read_committed(
            guard, preparation, transfer=completion_transfer
        )
        current = command.records._read_current(
            guard, expected=expected.successor
        )
        predecessor, successor, entry_digest = command.records._expected(expected)
        if (
            record is not current
            or record.attempt.identity is not expected.preparation_identity
            or record.attempt.predecessor is None
            or predecessor is None
            or not record.attempt.predecessor.matches(predecessor)
            or not record.attempt.successor.matches(successor)
            or record.attempt.entry_digest != entry_digest
            or record.attempt.pair[0] is not self._code_leg
            or record.attempt.pair[1] is not self._workspace_admission
            or command.expected is not expected.successor
        ):
            raise RuntimeError("committed successor is not the current pair")

    def publish_successor_catalogs(
        self,
        preparation,
        completion_transfer,
        *,
        publication_expected,
        transfer_expected,
        transfer_runtime,
    ) -> WorkspaceJointCatalogResolvers:
        """Commit the exact sealed Code completion and both prepared legs once.

        All source-backed validation runs before the original parent exclusion.
        Under that exclusion Code retires the complete predecessor operation and
        Workspace writes the sole paired publication record.  The committed
        record is the visibility decision; there is no second publication flag.
        """
        from aware_code_retained_registry_policy_runtime.catalog_completion_transfer import (
            AuthorityCatalogCompletionTransferRuntime,
            CatalogCompletionTransfer,
        )

        if type(transfer_runtime) is not AuthorityCatalogCompletionTransferRuntime:
            raise TypeError("exact Code completion-transfer runtime required")
        if type(completion_transfer) is not CatalogCompletionTransfer:
            raise TypeError("exact Code completion transfer required")
        attempt = self._successor_attempts.get(preparation)
        if attempt is None:
            raise RuntimeError("original successor preparation differs")
        _validate_source_correspondences(
            attempt.workspace_snapshot, attempt.source_correspondences
        )
        self.validate_prepared_catalog_publication(
            preparation, expected=publication_expected
        )
        transfer_runtime.validate_catalog_completion_transfer(
            completion_transfer, expected=transfer_expected
        )
        command = self._command_parent
        if attempt is None or command is None:
            raise RuntimeError("original successor preparation differs")
        old_code_leg = self._code_leg
        old_workspace_admission = self._workspace_admission
        with command.guarded() as guard:
            self.validate_catalog_epoch_publication_guard(
                guard, preparation=preparation, expected=publication_expected
            )
            _check_source_correspondences_locked(
                attempt.workspace_snapshot, attempt.source_correspondences, guard
            )
            transfer_runtime.seal_catalog_completion_transfer(
                completion_transfer, guard, expected=transfer_expected
            )
            command.records._commit(
                guard,
                preparation,
                expected=publication_expected,
                transfer=completion_transfer,
            )
            command.expected = publication_expected.successor
            self._successor_attempts.pop(preparation)
            self._code_leg = attempt.code_leg
            self._workspace_admission = attempt.workspace_admission
            self._code_admission = None
            self._result = None
            self._contribution = None

        # These reads are deliberately outside the parent exclusion.  They can
        # only observe the record committed above and refuse any substituted leg.
        code_admission, code_resolver = published_code_catalog_leg(attempt.code_leg)
        result = WorkspaceJointCatalogResolvers(
            code=code_resolver,
            workspace=WorkspaceSemanticMaterializationMembershipResolver(
                attempt.workspace_admission
            ),
            contribution_digest=(
                publication_expected.successor.contribution_digest.value
            ),
            code_admission=code_admission,
            workspace_admission=attempt.workspace_admission,
        )
        self._code_admission = code_admission
        self._result = result
        self._contribution = (
            code_catalog_leg_snapshot(attempt.code_leg),
            attempt.workspace_snapshot,
            attempt.workspace_reader,
            attempt.provider_executable_bindings,
            attempt.dependency_planner_bindings,
        )
        transfer_runtime.validate_committed_catalog_completion_transfer(
            completion_transfer, expected=transfer_expected
        )
        self.validate_current_catalog_epoch(
            preparation, expected=publication_expected.successor
        )
        attempt.liveness["closed"] = False
        self._revoke_pair(old_code_leg, old_workspace_admission)
        return result

    def validate_current_catalog_epoch(self, epoch, *, expected):
        self.validate_catalog_parent()
        command = self._command_parent
        if command is None:
            raise RuntimeError("original command required")
        record = command.current_record(expected)
        if (
            record.preparation is not epoch
            or record.attempt.pair[0] is not self._code_leg
            or record.attempt.pair[1] is not self._workspace_admission
        ):
            raise RuntimeError("original current pair differs")

    def read_code_catalog_for_epoch(self, epoch, *, expected):
        self.validate_current_catalog_epoch(epoch, expected=expected)
        result = self._result
        if result is None or result.code_admission is not self._code_admission:
            raise RuntimeError("original Code admission unavailable")
        result.code.validate_catalog()
        self.validate_current_catalog_epoch(epoch, expected=expected)
        return result.code_admission

    def read_initial_epoch(self):
        expected = self.read_initial_publication()
        command = self._command_parent
        assert command is not None
        return command.current_record(expected).preparation

    def validate_initial_publication(
        self,
        expected,
        *,
        command_owner,
        command_parent,
        code_admission,
        workspace_admission,
    ) -> None:
        """Validate original command/pair identity; no execution or graph admission."""
        self.validate_catalog_parent()
        origin, result = self._command_parent, self._result
        if (
            origin is None
            or result is None
            or origin.owner is not command_owner
            or origin.parent is not command_parent
        ):
            raise RuntimeError("original command publication unavailable")
        if (
            code_admission is not self._code_admission
            or code_admission is not result.code_admission
            or workspace_admission is not self._workspace_admission
            or workspace_admission is not result.workspace_admission
        ):
            raise RuntimeError("original catalog pair substituted")
        record = origin.current_record(expected)
        if (
            record.attempt.pair[0] is not self._code_leg
            or record.attempt.pair[1] is not workspace_admission
        ):
            raise RuntimeError("publication record pair differs")
        # Potential source reads stay outside the exclusion guard.
        result.code.validate_catalog()
        workspace = result.workspace.catalog
        if workspace.catalog_root_digest != expected.membership_catalog_digest:
            raise RuntimeError("membership publication digest differs")
        self.validate_catalog_parent()
        if (
            origin.current_record(expected) is not record
            or self._result is not result
            or self._command_parent is not origin
            or origin.owner is not command_owner
            or origin.parent is not command_parent
            or self._code_admission is not code_admission
            or self._workspace_admission is not workspace_admission
            or record.attempt.pair[0] is not self._code_leg
            or record.attempt.pair[1] is not workspace_admission
        ):
            raise RuntimeError("publication moved during validation")

    def read_initial_publication(self):
        """Detached comparison values; possession does not grant publication authority."""
        self.validate_catalog_parent()
        origin, result = self._command_parent, self._result
        if origin is None or result is None or origin.expected is None:
            raise RuntimeError("original command publication unavailable")
        expected = origin.expected
        self.validate_initial_publication(
            expected,
            command_owner=origin.owner,
            command_parent=origin.parent,
            code_admission=result.code_admission,
            workspace_admission=result.workspace_admission,
        )
        return CatalogPairEpochExpectation(
            DirectInvocationExpectation(
                expected.invocation.invocation_identity,
                expected.invocation.lifetime_epoch_identity,
                expected.invocation.process_id,
            ),
            expected.publication_identity,
            deepcopy(expected.code_catalog_digest),
            deepcopy(expected.membership_catalog_digest),
            deepcopy(expected.contribution_digest),
        )

    @staticmethod
    def _revoke_pair(code_leg, workspace_admission):
        # Both attempts are mandatory even if the first cleanup fails.
        try:
            if workspace_admission is not None:
                _revoke_workspace_semantic_materialization_membership_catalog(
                    workspace_admission
                )
        finally:
            if code_leg is not None:
                revoke_code_catalog_leg(code_leg)

    def close(self) -> None:
        if self._pid != os.getpid():
            raise RuntimeError("catalog_host_process_changed")
        with self._lock:
            self._phase = "closed"
            code_leg, workspace = self._code_leg, self._workspace_admission
            pending = tuple(self._successor_attempts.values())
            self._successor_attempts.clear()
            for attempt in pending:
                attempt.liveness["closed"] = True
        try:
            if self._command_parent is not None:
                self._command_parent.retire_records()
        finally:
            try:
                self._revoke_pair(code_leg, workspace)
            finally:
                for attempt in pending:
                    self._revoke_pair(attempt.code_leg, attempt.workspace_admission)


def _assemble_authenticated_catalog_host(
    *, parent, publication_lock
) -> WorkspaceSemanticCatalogHost:
    """Privileged assembly only, after the original owner has admitted parent.

    Not exported as command API. Its caller owns bootstrap authentication; this
    function retains original objects, it cannot establish their authenticity.
    """
    descriptor = inspect.getattr_static(parent, "validate_catalog_parent")
    verifier = parent.validate_catalog_parent
    if (
        not inspect.ismethod(verifier)
        or verifier.__self__ is not parent
        or verifier.__func__ is not descriptor
    ):
        raise TypeError("original_parent_verifier_required")
    host = object.__new__(WorkspaceSemanticCatalogHost)
    host._command_parent = None
    host._parent = parent
    host._descriptor = descriptor
    host._validate_parent = verifier
    host._pid = os.getpid()
    host._lock = publication_lock
    host._phase = "new"
    host._code_leg = None
    host._workspace_admission = None
    host._code_admission = None
    host._result = None
    host._contribution = None
    host._issuing_workspace = False
    host._successor_attempts = {}
    host.validate_catalog_parent()
    return host


def _assemble_command_catalog_host(*, owner, parent, invocation):
    """Fixed original-resource composition; no caller-selected parent verifier.

    Borrows the already issued parent. The command's original assembly remains
    responsible for authenticating and retaining this exact host; no standalone
    trusted-bootstrap or selected-execution admission is issued here.
    """
    original = _CommandCatalogParent(owner, parent, invocation)
    host = _assemble_authenticated_catalog_host(
        parent=original, publication_lock=owner._lock
    )
    host._command_parent = original
    return host


def _contribution_digest(
    *,
    code_catalog: CodeSemanticContractCatalog,
    workspace_catalog: WorkspaceSemanticMaterializationMembershipCatalog,
    provider_executable_bindings: tuple[
        tuple[
            SemanticImplementationCoordinate, SemanticConfigurationCoordinate, object
        ],
        ...,
    ],
    dependency_planner_bindings: tuple[
        tuple[
            SemanticImplementationCoordinate,
            SemanticConfigurationCoordinate,
            CodeSemanticDependencyPlanner,
        ],
        ...,
    ],
) -> str:
    payload = {
        "code_catalog_root": code_catalog.catalog_root_digest.to_wire(),
        "dependency_planners": [
            [implementation.to_wire(), configuration.to_wire()]
            for implementation, configuration, _planner in dependency_planner_bindings
        ],
        "provider_executables": [
            [implementation.to_wire(), configuration.to_wire()]
            for implementation, configuration, _exe in provider_executable_bindings
        ],
        "workspace_catalog_root": workspace_catalog.catalog_root_digest.to_wire(),
    }
    return (
        "sha256:"
        + hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    )


def _workspace_entry_inputs_digest(
    catalog: WorkspaceSemanticMaterializationMembershipCatalog,
) -> ContentDigest:
    """Bind the exact authenticated entry-input closure, not catalog identity."""
    catalog.__post_init__()
    return ContentDigest.of_bytes(
        canonical_json_bytes([entry.to_wire() for entry in catalog.entries])
    )


type _CatalogCoordinates = tuple[str, int, str]


def _workspace_catalog_bytes(value: object) -> bytes:
    if type(value) is not WorkspaceSemanticMaterializationMembershipCatalog:
        raise TypeError("workspace_catalog_reader_result_must_be_exact")
    return canonical_json_bytes(value.to_wire())


def _catalog_coordinates(
    value: CodeSemanticContractCatalog
    | WorkspaceSemanticMaterializationMembershipCatalog,
) -> _CatalogCoordinates:
    catalog_ref = value.catalog_ref
    catalog_generation = value.catalog_generation
    catalog_root_digest = value.catalog_root_digest
    if type(catalog_ref) is not str or type(catalog_generation) is not int:
        raise TypeError("catalog_coordinates_must_be_exact")
    if type(catalog_root_digest) is not ContentDigest:
        raise TypeError("catalog_root_digest_must_be_exact")
    catalog_root_digest.__post_init__()
    return catalog_ref, catalog_generation, catalog_root_digest.value


def _capture_workspace_catalog(
    source: WorkspaceSemanticMaterializationMembershipCatalog,
) -> tuple[
    WorkspaceSemanticMaterializationMembershipCatalog,
    bytes,
    _CatalogCoordinates,
]:
    initial = _workspace_catalog_bytes(source)
    coordinates = _catalog_coordinates(source)
    snapshot = deepcopy(source)
    if _workspace_catalog_bytes(snapshot) != initial:
        raise RuntimeError("workspace_membership_catalog_source_moved")
    if _catalog_coordinates(snapshot) != coordinates:
        raise RuntimeError("workspace_membership_catalog_source_moved")
    if _workspace_catalog_bytes(source) != initial:
        raise RuntimeError("workspace_membership_catalog_source_moved")
    if _catalog_coordinates(source) != coordinates:
        raise RuntimeError("workspace_membership_catalog_source_moved")
    return snapshot, initial, coordinates


def _assert_workspace_catalog_source(
    reader: Callable[[], WorkspaceSemanticMaterializationMembershipCatalog],
    expected_bytes: bytes,
    expected_coordinates: _CatalogCoordinates,
) -> None:
    source = reader()
    if (
        _workspace_catalog_bytes(source) != expected_bytes
        or _catalog_coordinates(source) != expected_coordinates
    ):
        raise RuntimeError("workspace_membership_catalog_source_moved")
