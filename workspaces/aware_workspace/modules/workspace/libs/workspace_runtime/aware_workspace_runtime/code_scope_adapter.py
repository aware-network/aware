"""Mechanical retained scope projection; no policy or bootstrap authority."""

from __future__ import annotations

import inspect

from aware_code_semantic_contract_runtime import ContentDigest
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
    CodeRetainedScopePackage,
    CodeRetainedScopeProjection,
)

from .complete_scope_observation import (
    WorkspaceCompleteScopeObservationRuntime,
    WorkspaceCompleteScopeSnapshot,
    _performance_count,
    _performance_phase,
)
from .source_observation import WorkspaceRetainedObservedBody
from .source_observation_io import SourceObservationUnavailable


def _body(
    coordinate: WorkspaceRetainedObservedBody, body: bytes
) -> CodeRetainedScopeBody:
    if coordinate.size_bytes != len(body):
        raise SourceObservationUnavailable("scope_body_size_mismatch")
    return CodeRetainedScopeBody(
        relative_path=coordinate.relative_path,
        body_ref=coordinate.body_ref,
        content_digest=ContentDigest.of_wire(coordinate.content_digest),
        body=body,
    )


class WorkspaceCodeScopeAdapter:
    """Expose Code's reader/validator signatures over the original Workspace owner.

    Construction grants no trusted host authority. Code's future origin binding
    must authenticate this adapter and retain its exact callables separately.
    """

    def __init__(self, *, scope_runtime: WorkspaceCompleteScopeObservationRuntime):
        if type(scope_runtime) is not WorkspaceCompleteScopeObservationRuntime:
            raise TypeError("exact Workspace complete-scope runtime required")
        self._scope_runtime = scope_runtime
        self._reader = scope_runtime._begin_projection_read
        self._batch_reader = scope_runtime._begin_projection_batch_read
        self._validator = scope_runtime.validate_complete_scope
        self._batch_validator = scope_runtime.validate_complete_scope_batch
        self._entrances = tuple(
            (name, inspect.getattr_static(scope_runtime, name), method)
            for name, method in (
                ("_begin_projection_read", self._reader),
                ("_begin_projection_batch_read", self._batch_reader),
                ("validate_complete_scope", self._validator),
                ("validate_complete_scope_batch", self._batch_validator),
            )
        )
        self._check_origin()

    def _check_origin(self) -> None:
        for name, descriptor, method in self._entrances:
            if (
                not inspect.ismethod(method)
                or method.__self__ is not self._scope_runtime
                or method.__func__ is not descriptor
                or inspect.getattr_static(self._scope_runtime, name) is not descriptor
            ):
                raise SourceObservationUnavailable("scope_reader_origin_changed")

    def read_complete_scope_projection(
        self,
        snapshot: WorkspaceCompleteScopeSnapshot,
    ) -> CodeRetainedScopeProjection:
        self._check_origin()
        with _performance_phase("workspace.scope_adapter_source_read"):
            read = self._reader(snapshot)
        try:
            source = read.source
            with _performance_phase("workspace.scope_adapter_projection_build"):
                projection = self._projection_from_source(source)
            # Enforce Code's complete canonical projection bound as well as row bounds.
            with _performance_phase("workspace.scope_adapter_projection_digest"):
                projection.projection_digest
            with _performance_phase("workspace.scope_adapter_postvalidation"):
                self._validator(snapshot)
            read.complete()
            self._check_origin()
            return projection
        except BaseException:
            read.abort()
            raise

    @staticmethod
    def _projection_from_source(source):
        return CodeRetainedScopeProjection(
            repository_binding_ref=source.observation.repository_binding_ref,
            observation_digest=ContentDigest.of_wire(
                source.observation.observation_digest
            ),
            workspace_manifest=_body(
                source.workspace_coordinate, source.workspace_body
            ),
            modules=tuple(
                CodeRetainedScopeModule(
                    module.module_id,
                    _body(module.coordinate, module.body),
                )
                for module in source.modules
            ),
            packages=tuple(
                CodeRetainedScopePackage(
                    module_id=package.membership.module_id,
                    package_id=package.membership.package_id,
                    package_kind=package.membership.package_kind,
                    module_manifest_path=package.membership.module_manifest_path,
                    package_root=package.membership.package_root,
                    manifest_relative_path=package.membership.manifest_relative_path,
                    source_identity_digest=package.membership.source_identity_digest,
                    manifest=_body(
                        package.manifest_coordinate, package.manifest_body
                    ),
                )
                for package in source.packages
            ),
        )

    def read_complete_scope_projections(
        self, snapshots: tuple[WorkspaceCompleteScopeSnapshot, ...]
    ) -> tuple[CodeRetainedScopeProjection, ...]:
        """Project one closure's scopes under one original validator envelope."""
        self._check_origin()
        batch = self._batch_reader(snapshots)
        try:
            with _performance_phase("workspace.scope_adapter_batch_projection_build"):
                projections = tuple(
                    self._projection_from_source(batch.source(index))
                    for index in range(len(snapshots))
                )
            with _performance_phase("workspace.scope_adapter_batch_projection_digest"):
                for projection in projections:
                    projection.projection_digest
            _performance_count(
                "workspace.scope_adapter_projection_scopes", len(projections)
            )
            _performance_count(
                "workspace.scope_adapter_projection_modules",
                sum(len(projection.modules) for projection in projections),
            )
            _performance_count(
                "workspace.scope_adapter_projection_packages",
                sum(len(projection.packages) for projection in projections),
            )
            with _performance_phase("workspace.scope_adapter_batch_postvalidation"):
                self._batch_validator(snapshots)
            batch.complete()
            self._check_origin()
            return projections
        except BaseException:
            batch.abort()
            raise

    def validate_complete_scope_projection(
        self,
        snapshot: WorkspaceCompleteScopeSnapshot,
        *,
        projection_digest: ContentDigest | None = None,
    ) -> None:
        self._check_origin()
        if projection_digest is None:
            self._validator(snapshot)
        else:
            if type(projection_digest) is not ContentDigest:
                raise TypeError("exact projection digest required")
            projection_digest.__post_init__()
            actual = self.read_complete_scope_projection(snapshot).projection_digest
            if actual != projection_digest:
                raise SourceObservationUnavailable("scope_projection_digest_mismatch")
        self._check_origin()
