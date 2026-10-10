"""Original source and per-use associations; no self-issued Code bootstrap trust."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import PurePosixPath

from aware_code_semantic_contract_runtime import ContentDigest
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    MAX_EDGES,
    MAX_SCOPES,
    DependencyScopeEntry,
    DependencyScopeEdge,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec_v2 import (
    encode_dependency_scope_closure_v2,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
    DependencyScopeProfileAssociation,
)

from .code_scope_adapter import WorkspaceCodeScopeAdapter, _body
from .complete_scope_observation import (
    WorkspaceCompleteScopeObservationRuntime,
    _performance_count,
    _performance_phase,
)
from .composition import RetainedWorkspaceCompositionProvider
from .dependency_scope_declarations import refuse
from .source_observation import WorkspaceSourceObservationRuntime
from .workspace_profile_declarations import (
    WorkspaceProfileDeclarationError,
    local_profile_paths_from_bytes,
)


class WorkspaceRetainedDependencySource:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original Workspace runtime issues dependency source handles")

    def __reduce__(self):
        raise TypeError("dependency source handles cannot be reconstructed")


@dataclass(frozen=True)
class _Record:
    observation: object
    root_record: object
    consumer: str
    selection: tuple[tuple[str, str], ...]
    edges: tuple[DependencyScopeEdge, ...]
    # key, authored handle, original scope snapshot, original scope record
    scopes: tuple[tuple[str, str, object, object], ...]
    digest: ContentDigest


class WorkspaceDependencyScopeRuntime:
    """Retains borrowed original resources and owns only its new scope handles.

    Preliminary values remain source evidence. Operation methods refuse until
    fixed composition retains an authenticated original Code validator and epoch.
    No bind/read argument accepts a validator callback.
    """

    def __init__(self, *, observation_runtime, scope_runtime):
        if (
            type(observation_runtime) is not WorkspaceSourceObservationRuntime
            or type(scope_runtime) is not WorkspaceCompleteScopeObservationRuntime
        ):
            raise TypeError("original Workspace source runtimes required")
        if (
            scope_runtime._observation_runtime is not observation_runtime
            or observation_runtime._exclusion is None
            or scope_runtime._exclusion is not observation_runtime._exclusion
        ):
            refuse("dependency_source_participation_unavailable")
        self._observation = observation_runtime
        self._scope = scope_runtime
        self._exclusion = observation_runtime._exclusion
        self._exclusion.check_live()
        self._projection = WorkspaceCodeScopeAdapter(scope_runtime=scope_runtime)
        self._records = {}
        self._closed = False
        self._operation_origin = None
        self._methods = {}
        for owner, names in (
            (
                self._projection,
                ("read_complete_scope_projection", "read_complete_scope_projections"),
            ),
            (
                observation_runtime,
                ("evidence", "read", "revalidate", "_check_record_locked"),
            ),
            (
                scope_runtime,
                (
                    "capture_complete_scope",
                    "read_complete_scope",
                    "validate_complete_scope",
                    "validate_complete_scope_batch",
                    "release",
                    "_check_record_locked",
                ),
            ),
        ):
            for name in names:
                method = getattr(owner, name)
                self._methods[(id(owner), name)] = (
                    owner,
                    inspect.getattr_static(owner, name),
                    method,
                )
        self._origin()

    def _origin(self, *, retiring=False):
        if not retiring:
            self._exclusion.check_live()
            if self._closed:
                refuse("dependency_source_closed")
        if (
            self._observation._exclusion is not self._exclusion
            or self._scope._exclusion is not self._exclusion
            or self._scope._observation_runtime is not self._observation
        ):
            refuse("dependency_source_origin_changed")
        for (_, name), (owner, descriptor, method) in self._methods.items():
            if (
                not inspect.ismethod(method)
                or method.__self__ is not owner
                or method.__func__ is not descriptor
                or inspect.getattr_static(owner, name) is not descriptor
            ):
                refuse("dependency_source_method_changed")

    def _call(self, owner, name, *args, **kwargs):
        return self._methods[(id(owner), name)][2](*args, **kwargs)

    def _selection(self, observation, consumer):
        _performance_count("workspace.dependency_scope_selection")
        with _performance_phase("workspace.selection_evidence"):
            evidence = self._call(self._observation, "evidence", observation)
        if evidence.root_relative_path != ".":
            refuse("dependency_source_requires_repository_root")
        with _performance_phase("workspace.selection_provider_description"):
            provider = RetainedWorkspaceCompositionProvider()
            description = provider.describe_retained(
                observation_runtime=self._observation, observation=observation
            )
        if description["root_kind"] != "repository":
            refuse("dependency_source_requires_repository_membership")
        with _performance_phase("workspace.selection_membership"):
            targets = provider.qualified_repository_membership()
        if consumer not in targets.values():
            refuse("dependency_consumer_not_member")
        visited, visiting, edges = set(), set(), []

        def visit(key):
            if key in visiting:
                refuse("dependency_source_cycle")
            if key in visited:
                return
            if len(visited) + len(visiting) >= MAX_SCOPES:
                refuse("dependency_scope_bound")
            visiting.add(key)
            with _performance_phase("workspace.selection_edge_resolution"):
                selected = provider.qualified_dependency_selections(key, targets=targets)
            edges.extend(selected)
            if len(edges) > MAX_EDGES:
                refuse("dependency_edge_bound")
            for edge in selected:
                visit(edge.target_scope_key)
            visiting.remove(key)
            visited.add(key)

        visit(consumer)
        handles = {path: handle for handle, path in targets.items()}
        return tuple(
            (key, handles[key]) for key in sorted(visited, key=lambda k: k.encode())
        ), tuple(sorted(edges, key=lambda e: e.ordering_key))

    def _project(self, observation, consumer, scopes, *, selection=None, edges=None):
        _performance_count("workspace.dependency_scope_projection")
        if selection is None or edges is None:
            with _performance_phase("workspace.preliminary_selection"):
                selected, edges = self._selection(observation, consumer)
        else:
            selected = selection
        if selected != tuple((key, handle) for key, handle, _, _ in scopes):
            refuse("dependency_scope_membership_changed")
        _performance_count("workspace.dependency_scope_projection_scopes", len(scopes))
        _performance_count("workspace.dependency_scope_projection_edges", len(edges))
        with _performance_phase("workspace.preliminary_scope_projection"):
            snapshots = tuple(snapshot for _, _, snapshot, _ in scopes)
            projections = self._call(
                self._projection,
                "read_complete_scope_projections",
                snapshots,
            )
            if type(projections) is not tuple or len(projections) != len(scopes):
                refuse("dependency_scope_projection_batch_changed")
            entries = tuple(
                DependencyScopeEntry(
                    key,
                    handle,
                    projection,
                )
                for (key, handle, _, _), projection in zip(
                    scopes, projections, strict=True
                )
            )
        with _performance_phase("workspace.preliminary_profile_association"):
            evidence = self._call(self._observation, "evidence", observation)
            bodies = {body.relative_path: body for body in evidence.bodies}
            selected_handles = {key: handle for key, handle in selected}
            local_declarations = {}
            associations = []
            for edge in edges:
                target = edge.target_scope_key
                handle = selected_handles[target]
                if target not in local_declarations:
                    if target not in bodies:
                        refuse("profile_owner_manifest_not_retained")
                    owner_body = self._call(
                        self._observation,
                        "read",
                        observation,
                        relative_path=target,
                    )
                    try:
                        local_declarations[target] = dict(
                            local_profile_paths_from_bytes(
                                owner_body, workspace_handle=handle
                            )
                        )
                    except WorkspaceProfileDeclarationError as error:
                        refuse(str(error))
                key = edge.profile_key.value
                declared_path = local_declarations[target].get(key)
                if (
                    declared_path is None
                    or edge.profile_package_ref != f"workspace://{handle}#{key}"
                ):
                    refuse("selected_profile_not_locally_published")
                path = str(
                    PurePosixPath(target).parent / declared_path
                )
                coordinate = bodies.get(path)
                if coordinate is None:
                    refuse("selected_profile_body_not_retained")
                body = self._call(
                    self._observation, "read", observation, relative_path=path
                )
                associations.append(
                    DependencyScopeProfileAssociation(
                        edge.declaring_scope_key,
                        edge.declaration,
                        edge.target_scope_key,
                        _body(coordinate, body),
                    )
                )
            _performance_count(
                "workspace.dependency_scope_projection_profile_associations",
                len(associations),
            )
        result = CodeRetainedDependencyScopeClosureV2(
            consumer, entries, edges, tuple(associations)
        )
        with _performance_phase("workspace.preliminary_closure_encoding"):
            encode_dependency_scope_closure_v2(result)  # include the complete encoded bound
        return result

    def _cleanup(self, scopes):
        failures = []
        for _, _, snapshot, _ in reversed(scopes):
            try:
                self._call(self._scope, "release", snapshot)
            except BaseException as error:
                failures.append(error)
        if failures:
            raise BaseExceptionGroup("dependency source cleanup failed", failures)

    def capture(self, *, observation, consumer_scope_key):
        _performance_count("workspace.dependency_source_capture")
        self._origin()
        self._call(self._observation, "revalidate", observation)
        with self._observation._lock:
            root_record = self._observation._evidence(observation)
        selected, edges = self._selection(observation, consumer_scope_key)
        owned = []
        try:
            for key, handle in selected:
                snapshot = self._call(
                    self._scope,
                    "capture_complete_scope",
                    observation=observation,
                    workspace_manifest_path=key,
                )
                with self._scope._lock:
                    original = self._scope._record(snapshot)
                owned.append((key, handle, snapshot, original))
            projection = self._project(
                observation,
                consumer_scope_key,
                tuple(owned),
                selection=selected,
                edges=edges,
            )
            self._call(self._observation, "revalidate", observation)
            record = _Record(
                observation,
                root_record,
                consumer_scope_key,
                selected,
                edges,
                tuple(owned),
                projection.closure_digest,
            )
            handle = object.__new__(WorkspaceRetainedDependencySource)
            with self._exclusion.mutation() as guard:
                self._origin()
                if len(self._records) >= MAX_SCOPES:
                    refuse("dependency_source_capacity")
                self._check_constituents(record, guard)
                self._records[handle] = record
            return handle
        except BaseException:
            self._cleanup(owned)
            raise

    def _record(self, source):
        self._origin()
        if (
            type(source) is not WorkspaceRetainedDependencySource
            or source not in self._records
        ):
            refuse("dependency_source_foreign_or_retired")
        return self._records[source]

    def _check_constituents(self, record, guard):
        self._exclusion.check_locked(guard)
        self._call(
            self._observation,
            "_check_record_locked",
            record.observation,
            guard=guard,
            expected_record=record.root_record,
        )
        for _, _, snapshot, original in record.scopes:
            self._call(
                self._scope,
                "_check_record_locked",
                snapshot,
                guard=guard,
                expected_record=original,
            )

    def read_preliminary_closure(self, source):
        _performance_count("workspace.preliminary_closure_read")
        record = self._record(source)
        with _performance_phase("workspace.preliminary_closure_prevalidation"):
            self._call(self._observation, "revalidate", record.observation)
        with _performance_phase("workspace.preliminary_closure"):
            projection = self._project(
                record.observation,
                record.consumer,
                record.scopes,
                selection=record.selection,
                edges=record.edges,
            )
        with _performance_phase("workspace.preliminary_closure_postvalidation"):
            self._call(self._observation, "revalidate", record.observation)
            if projection.closure_digest != record.digest:
                refuse("dependency_source_digest_changed")
        with _performance_phase("workspace.preliminary_closure_guard"):
            with self._exclusion.mutation() as guard:
                self._origin()
                if self._records.get(source) is not record:
                    refuse("dependency_source_record_changed")
                self._check_constituents(record, guard)
        return projection

    def release(self, source):
        self._origin(retiring=True)
        with self._exclusion.mutation(retiring=True):
            if (
                type(source) is not WorkspaceRetainedDependencySource
                or source not in self._records
            ):
                refuse("dependency_source_foreign_or_retired")
            from .dependency_scope_operations import retire_source_locked

            retire_source_locked(self, source)
            record = self._records.pop(source)
        self._cleanup(record.scopes)

    def close(self):
        self._origin(retiring=True)
        with self._exclusion.mutation(retiring=True):
            self._closed = True
            records = tuple(self._records.values())
            from .dependency_scope_operations import retire_source_locked

            for source in self._records:
                retire_source_locked(self, source)
            self._records.clear()
        self._cleanup(tuple(s for record in records for s in record.scopes))

    def prepare_dependency_scope_expectation(
        self, source, *, parent_identity, epoch_identity, operation_identity, process_id
    ):
        from .dependency_scope_operations import prepare

        return prepare(
            self,
            source,
            parent_identity=parent_identity,
            epoch_identity=epoch_identity,
            operation_identity=operation_identity,
            process_id=process_id,
        )

    def bind_dependency_scope_operation(self, source, *, expected):
        from .dependency_scope_operations import bind

        bind(self, source, expected=expected)

    def release_dependency_scope_operation(self, source, *, expected):
        from .dependency_scope_operations import release

        release(self, source, expected=expected)

    def read_dependency_scope_closure(self, source, *, expected):
        from .dependency_scope_operations import read

        return read(self, source, expected=expected)

    def validate_dependency_scope_closure(
        self, source, *, expected, closure_digest=None
    ):
        from .dependency_scope_operations import validate

        validate(
            self,
            source,
            expected=expected,
            closure_digest=closure_digest,
        )

    def validate_preliminary_closure(self, source):
        """Revalidate the original source without rebuilding Code's closure.

        This is private operation-stage mechanics.  The retained root and each
        complete scope still run their original currentness validators; the
        operation layer supplies the previously admitted closure digest.
        """
        record = self._record(source)
        with _performance_phase("workspace.preliminary_closure_validation_scopes"):
            snapshots = tuple(snapshot for _, _, snapshot, _ in record.scopes)
            if snapshots:
                self._call(self._scope, "validate_complete_scope_batch", snapshots)
            else:
                with _performance_phase(
                    "workspace.preliminary_closure_validation_source"
                ):
                    self._call(self._observation, "revalidate", record.observation)
        with _performance_phase("workspace.preliminary_closure_validation_guard"):
            with self._exclusion.mutation() as guard:
                self._origin()
                if self._records.get(source) is not record:
                    refuse("dependency_source_record_changed")
                self._check_constituents(record, guard)

    def check_dependency_scope_closure_locked(
        self, source, *, expected, closure_digest, guard
    ):
        from .dependency_scope_operations import check_locked

        check_locked(
            self, source, expected=expected, closure_digest=closure_digest, guard=guard
        )
