"""Nominal complete Workspace scope source evidence, never a policy admission.

Every declared package is retained, including potential nonparticipants. Policy
classification belongs to Code; callers cannot submit a filtered package list.
"""

from __future__ import annotations

import copy
import hashlib
import os
import threading
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from dataclasses import dataclass, fields
from time import perf_counter_ns, process_time_ns
from typing import Any

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    AwareModuleSpecV3,
    parse_module_manifest,
)

from .composition import RetainedWorkspaceCompositionProvider
from .observed_membership import (
    WorkspaceObservedPackageMembership,
    WorkspaceObservedPackageMembershipEvidence,
    WorkspaceObservedPackageMembershipRuntime,
)
from .repository_delta_store_contract import WorkspaceRepositoryDeltaStoreError
from .source_exclusion import WorkspaceSourceExclusion, require_same_exclusion
from .source_observation import (
    WorkspaceObservedRootEvidence,
    WorkspaceRetainedObservedBody,
    WorkspaceRetainedRootObservation,
    WorkspaceSourceObservationRuntime,
)
from .source_observation_io import SourceObservationUnavailable, validate_relative_path


_PERFORMANCE_PROBE: ContextVar[object | None] = ContextVar(
    "aware_workspace_performance_probe", default=None
)
_PERFORMANCE_SPAN_STACK: ContextVar[tuple[dict[str, object], ...]] = ContextVar(
    "aware_workspace_performance_span_stack", default=()
)
_PERFORMANCE_SPAN_SEQUENCE: ContextVar[int] = ContextVar(
    "aware_workspace_performance_span_sequence", default=0
)


def set_performance_probe(probe):
    """Install an optional diagnostic sink for this execution context only."""

    return _PERFORMANCE_PROBE.set(probe)


def reset_performance_probe(token) -> None:
    _PERFORMANCE_PROBE.reset(token)


def _performance_record(kind: str, name: str, **fields) -> None:
    probe = _PERFORMANCE_PROBE.get()
    if probe is None:
        return
    record = getattr(probe, "record", None)
    if record is None:
        return
    try:
        record(kind=kind, name=name, **fields)
    except Exception:
        return


def _performance_count(name: str, amount: int = 1) -> None:
    _performance_record("counter", name, amount=amount)


@contextmanager
def _performance_lock(lock, name: str):
    """Acquire a lock while optionally measuring wait and hold time."""

    probe = _PERFORMANCE_PROBE.get()
    if probe is None or getattr(probe, "record", None) is None:
        with lock:
            yield
        return
    wait_start = perf_counter_ns()
    lock.acquire()
    wait_ns = perf_counter_ns() - wait_start
    _performance_count(f"{name}.acquires")
    _performance_count(f"{name}.wait_ns", wait_ns)
    hold_start = perf_counter_ns()
    try:
        yield
    finally:
        _performance_count(f"{name}.hold_ns", perf_counter_ns() - hold_start)
        lock.release()


@contextmanager
def _performance_phase(name: str):
    probe = _PERFORMANCE_PROBE.get()
    if probe is None or getattr(probe, "record", None) is None:
        yield
        return
    start = perf_counter_ns()
    cpu_start = process_time_ns()
    parent_stack = _PERFORMANCE_SPAN_STACK.get()
    span_id = _PERFORMANCE_SPAN_SEQUENCE.get() + 1
    _PERFORMANCE_SPAN_SEQUENCE.set(span_id)
    frame: dict[str, object] = {
        "span_id": span_id,
        "child_wall_ns": 0,
        "child_cpu_ns": 0,
    }
    stack_token = _PERFORMANCE_SPAN_STACK.set(parent_stack + (frame,))
    _performance_record(
        "phase_start",
        name,
        span_id=span_id,
        parent_span_id=(parent_stack[-1]["span_id"] if parent_stack else None),
    )
    try:
        yield
    finally:
        elapsed_ns = perf_counter_ns() - start
        cpu_ns = process_time_ns() - cpu_start
        child_wall_ns = int(frame["child_wall_ns"])
        child_cpu_ns = int(frame["child_cpu_ns"])
        _performance_record(
            "phase_end",
            name,
            span_id=span_id,
            parent_span_id=(parent_stack[-1]["span_id"] if parent_stack else None),
            elapsed_seconds=elapsed_ns / 1_000_000_000,
            exclusive_seconds=max(0, elapsed_ns - child_wall_ns)
            / 1_000_000_000,
            cpu_seconds=cpu_ns / 1_000_000_000,
            exclusive_cpu_seconds=max(0, cpu_ns - child_cpu_ns)
            / 1_000_000_000,
        )
        if parent_stack:
            parent_stack[-1]["child_wall_ns"] = (
                int(parent_stack[-1]["child_wall_ns"]) + elapsed_ns
            )
            parent_stack[-1]["child_cpu_ns"] = (
                int(parent_stack[-1]["child_cpu_ns"]) + cpu_ns
            )
        _PERFORMANCE_SPAN_STACK.reset(stack_token)
        if not parent_stack:
            _PERFORMANCE_SPAN_SEQUENCE.set(0)


def _parse_module_meaning(body: bytes, parsed_modules: dict, *, digest: str):
    missing = object()
    model = parsed_modules.get(digest, missing)
    if model is missing:
        _performance_count("workspace.complete_scope_module_parse_miss")
        model = parse_module_manifest(body)
        parsed_modules[digest] = model
    else:
        _performance_count("workspace.complete_scope_module_parse_hit")
    return model


class WorkspaceCompleteScopeSnapshot:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("Workspace issues complete scope snapshots")

    def __reduce__(self):
        raise TypeError("scope snapshots cannot be copied or serialized")


class _CompleteScopeProjectionRead:
    """One-use detached source read awaiting adapter-side final validation."""

    __slots__ = ("_runtime", "_snapshot", "_source", "_state")

    def __new__(cls):
        raise TypeError("projection reads are issued by Workspace")

    def __reduce__(self):
        raise TypeError("projection reads cannot be copied or serialized")

    @classmethod
    def _issue(cls, runtime, snapshot, source):
        value = object.__new__(cls)
        value._runtime = runtime
        value._snapshot = snapshot
        value._source = source
        value._state = "open"
        return value

    @property
    def source(self):
        if self._state != "open":
            raise SourceObservationUnavailable("projection_read_unavailable")
        return self._source

    def complete(self):
        if self._state != "open" or self._runtime._closed:
            raise SourceObservationUnavailable("projection_read_unavailable")
        self._state = "completed"

    def abort(self):
        if self._state == "open":
            self._state = "aborted"


class _CompleteScopeProjectionBatchRead:
    """One-use source receipts for one operation-local scope batch."""

    __slots__ = ("_runtime", "_snapshots", "_sources", "_state")

    def __new__(cls):
        raise TypeError("projection batches are issued by Workspace")

    def __reduce__(self):
        raise TypeError("projection batches cannot be copied or serialized")

    @classmethod
    def _issue(cls, runtime, snapshots, sources):
        value = object.__new__(cls)
        value._runtime = runtime
        value._snapshots = snapshots
        value._sources = sources
        value._state = "open"
        return value

    def source(self, index):
        if self._state != "open" or type(index) is not int:
            raise SourceObservationUnavailable("projection_batch_unavailable")
        if index < 0 or index >= len(self._sources):
            raise SourceObservationUnavailable("projection_batch_index_invalid")
        return self._sources[index]

    def complete(self):
        if self._state != "open" or self._runtime._closed:
            raise SourceObservationUnavailable("projection_batch_unavailable")
        self._state = "completed"

    def abort(self):
        if self._state == "open":
            self._state = "aborted"


@dataclass(frozen=True, slots=True)
class WorkspaceScopeModuleSource:
    module_id: str
    coordinate: WorkspaceRetainedObservedBody
    body: bytes
    meaning: AwareModuleSpecV2 | AwareModuleSpecV3


@dataclass(frozen=True, slots=True)
class WorkspaceScopePackageSource:
    membership: WorkspaceObservedPackageMembershipEvidence
    manifest_coordinate: WorkspaceRetainedObservedBody
    manifest_body: bytes


@dataclass(frozen=True, slots=True)
class WorkspaceCompleteScopeSource:
    """Detached inspection only. The nominal snapshot/validator prove provenance."""

    observation: WorkspaceObservedRootEvidence
    workspace_coordinate: WorkspaceRetainedObservedBody
    workspace_body: bytes
    modules: tuple[WorkspaceScopeModuleSource, ...]
    packages: tuple[WorkspaceScopePackageSource, ...]


@dataclass(frozen=True)
class _Scope:
    observation: WorkspaceRetainedRootObservation
    workspace_manifest_path: str
    modules: tuple[tuple[str, str], ...]
    memberships: tuple[WorkspaceObservedPackageMembership, ...]
    root_record: WorkspaceObservedRootEvidence
    membership_records: tuple[object, ...]


class WorkspaceCompleteScopeObservationRuntime:
    def __init__(
        self,
        *,
        observation_runtime: WorkspaceSourceObservationRuntime,
        membership_runtime: WorkspaceObservedPackageMembershipRuntime,
        exclusion: WorkspaceSourceExclusion | None = None,
    ):
        if type(observation_runtime) is not WorkspaceSourceObservationRuntime:
            raise TypeError("exact observation runtime required")
        if type(membership_runtime) is not WorkspaceObservedPackageMembershipRuntime:
            raise TypeError("exact membership runtime required")
        membership_runtime.validate_runtime_origin(
            observation_runtime=observation_runtime
        )
        require_same_exclusion(observation_runtime._exclusion, exclusion)
        require_same_exclusion(membership_runtime._exclusion, exclusion)
        if exclusion is not None:
            exclusion.check_live()
        self._exclusion = exclusion
        self._observation_runtime = observation_runtime
        self._membership_runtime = membership_runtime
        self._records: dict[WorkspaceCompleteScopeSnapshot, _Scope] = {}
        self._pid = os.getpid()
        self._closed = False
        self._lock = threading.RLock()

    def _live(self):
        if self._exclusion is not None:
            self._exclusion.check_live()
        if self._closed or os.getpid() != self._pid:
            raise SourceObservationUnavailable("complete_scope_runtime_unavailable")
        self._membership_runtime.validate_runtime_origin(
            observation_runtime=self._observation_runtime
        )

    def _release_memberships(self, memberships):
        failures = []
        for member in reversed(memberships):
            try:
                self._membership_runtime.release(member)
            except SourceObservationUnavailable:
                # A retired membership needs no further cleanup.
                pass
            except BaseException as error:
                failures.append(error)
        if failures:
            raise BaseExceptionGroup("scope membership cleanup failed", failures)

    def capture_complete_scope(
        self,
        *,
        observation: WorkspaceRetainedRootObservation,
        workspace_manifest_path: str,
    ) -> WorkspaceCompleteScopeSnapshot:
        """Enumerate the selected scope completely; accept no package filter."""
        _performance_count("workspace.complete_scope_capture")
        self._live()
        if len(self._records) >= 16:
            raise SourceObservationUnavailable("complete_scope_capacity")
        with self._observation_runtime._lock:
            root_record = self._observation_runtime._evidence(observation)
        validate_relative_path(workspace_manifest_path)
        self._observation_runtime.revalidate(observation)
        projection: Any = RetainedWorkspaceCompositionProvider().describe_retained(
            observation_runtime=self._observation_runtime, observation=observation
        )
        workspaces = projection["repository"]["workspaces"]
        paths = [w["manifest_path"] for w in workspaces]
        if len(paths) != len(set(paths)):
            raise SourceObservationUnavailable("duplicate_workspace_origin")
        selected = [
            w for w in workspaces if w["manifest_path"] == workspace_manifest_path
        ]
        if len(selected) != 1:
            raise SourceObservationUnavailable("workspace_scope_not_exact")
        workspace = selected[0]
        if workspace["repository_membership_handle"] not in (
            None,
            workspace["workspace_handle"],
        ):
            raise SourceObservationUnavailable("workspace_handle_mismatch")
        modules = sorted(workspace["modules"], key=lambda m: m["module_id"].encode())
        module_paths = [m["manifest_path"] for m in modules]
        if len(module_paths) != len(set(module_paths)):
            raise SourceObservationUnavailable("duplicate_module_origin")
        selections = tuple(
            (module["module_id"], package["package_id"])
            for module in modules
            for package in sorted(
                module["packages"], key=lambda p: p["package_id"].encode()
            )
        )
        memberships = []
        membership_records = []
        parsed_modules = {}
        try:
            for module in modules:
                body = self._observation_runtime.read(
                    observation, relative_path=module["manifest_path"]
                )
                digest = "sha256:" + hashlib.sha256(body).hexdigest()
                if type(_parse_module_meaning(body, parsed_modules, digest=digest)) not in (
                    AwareModuleSpecV2,
                    AwareModuleSpecV3,
                ):
                    raise SourceObservationUnavailable("complete_scope_requires_v2")
            memberships.extend(
                self._membership_runtime.admit_many(
                    observation=observation,
                    workspace_manifest_path=workspace_manifest_path,
                    selections=selections,
                )
            )
            with self._membership_runtime._lock:
                for member in memberships:
                    self._membership_runtime._record(member)
                    membership_records.append(self._membership_runtime._records[member])
            self._observation_runtime.revalidate(observation)
            record = _Scope(
                observation,
                workspace_manifest_path,
                tuple((m["module_id"], m["manifest_path"]) for m in modules),
                tuple(memberships),
                root_record,
                tuple(membership_records),
            )
            # Prove every required retained body before publishing the handle.
            self._read(record, parsed_modules=parsed_modules)
            self._live()
            self._observation_runtime.revalidate(observation)
            handle = object.__new__(WorkspaceCompleteScopeSnapshot)
            with (
                self._exclusion.mutation() if self._exclusion else nullcontext()
            ) as guard:
                with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                    if self._closed or len(self._records) >= 16:
                        raise SourceObservationUnavailable(
                            "complete_scope_capacity_or_lifetime"
                        )
                    if self._exclusion is not None:
                        self._observation_runtime._check_record_locked(
                            observation, guard=guard, expected_record=record.root_record
                        )
                        for member, original in zip(
                            record.memberships, record.membership_records, strict=True
                        ):
                            self._membership_runtime._check_record_locked(
                                member, guard=guard, expected_record=original
                            )
                    self._records[handle] = record
            return handle
        except BaseException:
            self._release_memberships(memberships)
            raise

    def _record(self, snapshot):
        self._live()
        if (
            type(snapshot) is not WorkspaceCompleteScopeSnapshot
            or snapshot not in self._records
        ):
            raise SourceObservationUnavailable("foreign_or_expired_complete_scope")
        return self._records[snapshot]

    def validate_complete_scope(self, snapshot: WorkspaceCompleteScopeSnapshot) -> None:
        """Original validator to invoke before AND after Code policy production."""
        _performance_count("workspace.complete_scope_validation")
        with _performance_phase("workspace.complete_scope_validation_total"):
            with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                record = self._record(snapshot)
                _performance_count("workspace.complete_scope_validation_scopes")
                _performance_count(
                    "workspace.complete_scope_validation_memberships",
                    len(record.memberships),
                )
                with _performance_phase("workspace.complete_scope_revalidation"):
                    self._observation_runtime.revalidate(record.observation)
                with _performance_phase(
                    "workspace.complete_scope_membership_validation"
                ):
                    self._membership_runtime._validate_records_after_observation(
                        tuple(
                            zip(
                                record.memberships,
                                record.membership_records,
                                strict=True,
                            )
                        ),
                        observation=record.observation,
                        root_record=record.root_record,
                    )

    def validate_complete_scope_batch(
        self, snapshots: tuple[WorkspaceCompleteScopeSnapshot, ...]
    ) -> None:
        """Validate one operation's scopes with one shared root revalidation."""
        if type(snapshots) is not tuple:
            raise TypeError("exact complete-scope snapshot tuple required")
        if len(snapshots) != len(set(snapshots)):
            raise SourceObservationUnavailable("duplicate_complete_scope_snapshot")
        _performance_count("workspace.complete_scope_batch_validation")
        with _performance_phase("workspace.complete_scope_batch_validation_total"):
            with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                records = tuple(self._record(snapshot) for snapshot in snapshots)
                if not records:
                    return
                _performance_count(
                    "workspace.complete_scope_batch_validation_scopes", len(records)
                )
                _performance_count(
                    "workspace.complete_scope_batch_validation_memberships",
                    sum(len(record.memberships) for record in records),
                )
                observation = records[0].observation
                if any(record.observation is not observation for record in records):
                    raise SourceObservationUnavailable(
                        "complete_scope_observation_mismatch"
                    )
                root_record = records[0].root_record
                if any(record.root_record is not root_record for record in records):
                    raise SourceObservationUnavailable(
                        "complete_scope_root_record_mismatch"
                    )
                with _performance_phase(
                    "workspace.complete_scope_batch_revalidation"
                ):
                    self._observation_runtime.revalidate(observation)
                with _performance_phase(
                    "workspace.complete_scope_batch_membership_validation"
                ):
                    self._membership_runtime._validate_records_after_observation(
                        tuple(
                            (member, original)
                            for record in records
                            for member, original in zip(
                                record.memberships,
                                record.membership_records,
                                strict=True,
                            )
                        ),
                        observation=observation,
                        root_record=root_record,
                    )

    def _read_retained_body_set(self, observed):
        """Read the original retained root once for a validated scope read."""
        coordinates = {b.relative_path: b for b in observed.bodies}
        contents = {}
        missing = object()
        resolved_by_ref = {}
        _performance_count(
            "workspace.complete_scope_retained_body_count", len(observed.bodies)
        )
        _performance_count(
            "workspace.complete_scope_retained_body_bytes",
            sum(body.size_bytes for body in observed.bodies),
        )
        _performance_count(
            "workspace.complete_scope_retained_body_unique_refs",
            len({body.body_ref for body in observed.bodies}),
        )
        with _performance_phase("workspace.complete_scope_body_batch_read"):
            for coordinate in observed.bodies:
                value = resolved_by_ref.get(coordinate.body_ref, missing)
                if value is missing:
                    _performance_count(
                        "workspace.complete_scope_retained_body_cache_miss"
                    )
                    try:
                        value = self._observation_runtime._store.resolve_body(
                            coordinate.body_ref
                        )
                    except (WorkspaceRepositoryDeltaStoreError, OSError) as error:
                        raise SourceObservationUnavailable(
                            "retained_body_unavailable"
                        ) from error
                    resolved_by_ref[coordinate.body_ref] = value
                else:
                    _performance_count(
                        "workspace.complete_scope_retained_body_cache_hit"
                    )
                if (
                    value is None
                    or len(value) != coordinate.size_bytes
                    or "sha256:" + hashlib.sha256(value).hexdigest()
                    != coordinate.content_digest
                ):
                    raise SourceObservationUnavailable("retained_body_unavailable")
                contents[coordinate.relative_path] = value
        return coordinates, contents

    def _read(self, record, *, parsed_modules=None):
        _performance_count("workspace.complete_scope_read")
        # ``read_complete_scope`` validates and revalidates the complete
        # observation around this method. Capture performs the same two
        # revalidations around its initial read. Reuse that proof here and
        # resolve each retained body once; calling the public single-path
        # readers for every member would reread the entire root for each path.
        self._live()
        with self._observation_runtime._lock:
            observed = self._observation_runtime._evidence(record.observation)
        if observed is not record.root_record:
            raise SourceObservationUnavailable("observation_record_replaced")
        coordinates, contents = self._read_retained_body_set(observed)
        if parsed_modules is None:
            parsed_modules = {}

        def body_at(path):
            coordinate = coordinates.get(path)
            if coordinate is None:
                raise SourceObservationUnavailable("body_not_observed")
            return coordinate, contents[path]

        with _performance_phase("workspace.complete_scope_module_parse"):
            modules = []
            for module_id, path in record.modules:
                coordinate, body = body_at(path)
                model = _parse_module_meaning(
                    body, parsed_modules, digest=coordinate.content_digest
                )
                if type(model) is not AwareModuleSpecV2 and type(model) is not AwareModuleSpecV3:
                    raise SourceObservationUnavailable("complete_scope_requires_v2")
                for declaration in model.package_declarations:
                    if declaration.occurrence_declared and any(
                        getattr(declaration.occurrence, field.name).state == "unavailable"
                        for field in fields(declaration.occurrence)
                    ):
                        raise SourceObservationUnavailable(
                            "incomplete_authored_scope_participant"
                        )
                modules.append(
                    WorkspaceScopeModuleSource(module_id, coordinate, body, model)
                )
        _performance_count("workspace.complete_scope_module_count", len(modules))
        with _performance_phase("workspace.complete_scope_membership_projection"):
            packages = []
            for member, original in zip(
                record.memberships, record.membership_records, strict=True
            ):
                with self._membership_runtime._lock:
                    if (
                        self._membership_runtime._closed
                        or self._membership_runtime._records.get(member) is not original
                    ):
                        raise SourceObservationUnavailable(
                            "foreign_or_expired_membership"
                        )
                observation, evidence, root_record = original
                if (
                    observation is not record.observation
                    or root_record is not record.root_record
                ):
                    raise SourceObservationUnavailable("membership_record_changed")
                prefix = "" if evidence.package_root == "." else evidence.package_root + "/"
                coordinate, body = body_at(
                    prefix + evidence.manifest_relative_path
                )
                packages.append(
                    WorkspaceScopePackageSource(evidence, coordinate, body)
                )
        _performance_count("workspace.complete_scope_package_count", len(packages))
        workspace_coordinate, workspace_body = body_at(record.workspace_manifest_path)
        with _performance_phase("workspace.complete_scope_source_assembly"):
            return WorkspaceCompleteScopeSource(
                observed,
                workspace_coordinate,
                workspace_body,
                tuple(modules),
                tuple(packages),
            )

    def read_complete_scope(
        self, snapshot: WorkspaceCompleteScopeSnapshot
    ) -> WorkspaceCompleteScopeSource:
        _performance_count("workspace.complete_scope_read_operation")
        with _performance_phase("workspace.complete_scope_read_operation_total"):
            with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                with _performance_phase("workspace.complete_scope_prevalidation"):
                    self.validate_complete_scope(snapshot)
                with _performance_phase("workspace.complete_scope_source_read"):
                    result = self._read(self._record(snapshot))
                with _performance_phase("workspace.complete_scope_postvalidation"):
                    self.validate_complete_scope(snapshot)
                with _performance_phase("workspace.complete_scope_detached_copy"):
                    return copy.deepcopy(result)

    def _begin_projection_read(
        self, snapshot: WorkspaceCompleteScopeSnapshot
    ) -> _CompleteScopeProjectionRead:
        """Read once for the adapter; its original validator must finalize it."""
        _performance_count("workspace.complete_scope_projection_read")
        with _performance_phase("workspace.complete_scope_projection_read_total"):
            with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                with _performance_phase("workspace.complete_scope_prevalidation"):
                    self.validate_complete_scope(snapshot)
                with _performance_phase("workspace.complete_scope_source_read"):
                    result = self._read(self._record(snapshot))
                with _performance_phase("workspace.complete_scope_detached_copy"):
                    detached = copy.deepcopy(result)
        return _CompleteScopeProjectionRead._issue(self, snapshot, detached)

    def _begin_projection_batch_read(
        self, snapshots: tuple[WorkspaceCompleteScopeSnapshot, ...]
    ) -> _CompleteScopeProjectionBatchRead:
        """Read several scopes under one operation-local validation envelope."""
        if type(snapshots) is not tuple or not snapshots:
            raise TypeError("nonempty complete-scope snapshot tuple required")
        if len(snapshots) != len(set(snapshots)):
            raise SourceObservationUnavailable("duplicate_complete_scope_snapshot")
        _performance_count("workspace.complete_scope_projection_batch_read")
        with _performance_phase("workspace.complete_scope_projection_batch_read_total"):
            with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                records = tuple(self._record(snapshot) for snapshot in snapshots)
                with _performance_phase(
                    "workspace.complete_scope_projection_batch_prevalidation"
                ):
                    self.validate_complete_scope_batch(snapshots)
                with _performance_phase(
                    "workspace.complete_scope_projection_batch_source_read"
                ):
                    sources = tuple(self._read(record) for record in records)
                with _performance_phase(
                    "workspace.complete_scope_projection_batch_detached_copy"
                ):
                    detached = tuple(copy.deepcopy(source) for source in sources)
        return _CompleteScopeProjectionBatchRead._issue(
            self, snapshots, detached
        )

    def _check_record_locked(self, snapshot, *, guard, expected_record):
        if self._exclusion is None:
            raise SourceObservationUnavailable("source_exclusion_unavailable")
        self._exclusion.check_locked(guard)
        if self._closed or type(snapshot) is not WorkspaceCompleteScopeSnapshot:
            raise SourceObservationUnavailable("foreign_or_expired_complete_scope")
        record = self._records.get(snapshot)
        if record is None or record is not expected_record:
            raise SourceObservationUnavailable("foreign_or_expired_complete_scope")
        self._observation_runtime._check_record_locked(
            record.observation, guard=guard, expected_record=record.root_record
        )
        for member, original in zip(
            record.memberships, record.membership_records, strict=True
        ):
            self._membership_runtime._check_record_locked(
                member, guard=guard, expected_record=original
            )
        return record

    def release(self, snapshot: WorkspaceCompleteScopeSnapshot) -> None:
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("complete_scope_runtime_unavailable")
        with (
            self._exclusion.mutation(retiring=True)
            if self._exclusion
            else nullcontext()
        ):
            with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                if (
                    self._closed
                    or type(snapshot) is not WorkspaceCompleteScopeSnapshot
                    or snapshot not in self._records
                ):
                    raise SourceObservationUnavailable(
                        "foreign_or_expired_complete_scope"
                    )
                record = self._records.pop(snapshot)
        self._release_memberships(record.memberships)

    def close(self) -> None:
        if self._exclusion is not None and os.getpid() != self._pid:
            raise SourceObservationUnavailable("complete_scope_runtime_unavailable")
        with (
            self._exclusion.mutation(retiring=True)
            if self._exclusion
            else nullcontext()
        ):
            with _performance_lock(self._lock, "workspace.complete_scope_lock"):
                self._closed = True
                records = tuple(self._records.values())
                self._records.clear()
        self._release_memberships(
            tuple(m for record in records for m in record.memberships)
        )
