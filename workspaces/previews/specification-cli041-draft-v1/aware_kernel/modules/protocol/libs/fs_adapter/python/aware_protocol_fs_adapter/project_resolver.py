"""Process-local fs_v3 Project location capability, not Project source authority.

Issuance retains the genuine Goal capability from the same on-disk manifest
admission. Project owns committed content, identity, discovery and currentness.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, SupportsIndex, final, override
from weakref import WeakKeyDictionary

from aware_protocol_runtime import ProtocolContractError

from .goal_templates import canonical_relative_path
from .manifest import (
    COLLABORATION_PROJECT_FS_PROFILE,
    FilesystemProtocolAdmissionResult,
    resolve_repository_path_at_use,
)
from .native_goal_resolver import (
    NativeGoalResolverCapability,
    NativeGoalResolverError,
    admit_native_goal_resolver,
    require_native_goal_resolver,
)
from .project_templates import match_project_path


class ProjectResolverError(ProtocolContractError):
    """Typed pre-source refusal; never a Project or FO1 reading."""

    code: str
    diagnostics: tuple[str, ...]

    def __init__(self, code: str, *, diagnostics: tuple[str, ...] = ()) -> None:
        self.code = code
        self.diagnostics = (code, *diagnostics)
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ProjectLocation:
    relative_path: str
    resolved_path: Path
    location_slug: str


@dataclass(frozen=True, slots=True)
class _RetainedProjectAdmission:
    goal_capability: NativeGoalResolverCapability
    project_root: str
    project_template: str
    issuer_pid: int


_ISSUED: WeakKeyDictionary[ProjectResolverCapability, _RetainedProjectAdmission] = WeakKeyDictionary()


@final
class ProjectResolverCapability:
    """Nominal, nonserializable location authority retained by this issuer."""

    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> ProjectResolverCapability:
        raise TypeError("use admit_project_resolver")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Project capability cannot be subclassed")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("Project capability cannot be copied or serialized")

    @property
    def repository_root(self) -> Path:
        return _retained(self).goal_capability.repository_root

    @property
    def manifest_path(self) -> Path:
        return _retained(self).goal_capability.manifest_path

    @property
    def manifest_sha256(self) -> str:
        return _retained(self).goal_capability.manifest_sha256

    @property
    def protocol_digest(self) -> str:
        return _retained(self).goal_capability.protocol_digest

    @property
    def project_root(self) -> str:
        return _retained(self).project_root

    @property
    def project_template(self) -> str:
        return _retained(self).project_template

    @property
    def goal_capability(self) -> NativeGoalResolverCapability:
        """The actual participating Goal issuer token for this same manifest."""
        self.revalidate()
        return _retained(self).goal_capability

    def revalidate(self) -> None:
        retained = _retained(self)
        try:
            _ = require_native_goal_resolver(retained.goal_capability)
        except NativeGoalResolverError as error:
            raise ProjectResolverError(
                "project_admission_changed", diagnostics=error.diagnostics
            ) from error

    def match_project_path(self, relative_path: str) -> str | None:
        """Classify a location, never authenticate the record's project_key."""
        self.revalidate()
        retained = _retained(self)
        prefix = retained.project_root + "/"
        if not canonical_relative_path(relative_path) or not relative_path.startswith(prefix):
            return None
        return match_project_path(retained.project_template, relative_path[len(prefix):])

    def resolve_project_path(self, relative_path: str) -> ProjectLocation:
        """Recheck manifest and topology; the owner still verifies committed bytes."""
        slug = self.match_project_path(relative_path)
        if slug is None:
            raise ProjectResolverError("project_target_outside_binding")
        retained = _retained(self)
        root_resolution = resolve_repository_path_at_use(
            repository_root=self.repository_root,
            relative_path=retained.project_root,
            field_name="records.project.root",
        )
        target_resolution = resolve_repository_path_at_use(
            repository_root=self.repository_root,
            relative_path=relative_path,
            field_name="records.project.target",
        )
        if root_resolution.path is None or target_resolution.path is None:
            raise ProjectResolverError(
                "project_target_unresolvable",
                diagnostics=root_resolution.diagnostics + target_resolution.diagnostics,
            )
        if not target_resolution.path.is_relative_to(root_resolution.path):
            raise ProjectResolverError("project_target_outside_binding")
        self.revalidate()
        return ProjectLocation(relative_path, target_resolution.path, slug)


def _retained(capability: object) -> _RetainedProjectAdmission:
    if type(capability) is not ProjectResolverCapability:
        raise ProjectResolverError("project_capability_invalid")
    retained = _ISSUED.get(capability)
    if retained is None:
        raise ProjectResolverError("project_capability_invalid")
    if retained.issuer_pid != os.getpid():
        raise ProjectResolverError("project_capability_foreign_process")
    return retained


def require_project_resolver(capability: object) -> ProjectResolverCapability:
    """Accept only this issuer's live token, never a decoded or forged binding."""
    _ = _retained(capability)
    assert isinstance(capability, ProjectResolverCapability)
    capability.revalidate()
    return capability


@dataclass(frozen=True, slots=True)
class ProjectResolverAdmission:
    admission: FilesystemProtocolAdmissionResult
    capability: ProjectResolverCapability | None


def admit_project_resolver(*, repository_root: Path, manifest_path: Path) -> ProjectResolverAdmission:
    """Issue only from fresh fs_v3 on-disk admission, not caller-built values."""
    try:
        selected = admit_native_goal_resolver(
            repository_root=repository_root, manifest_path=manifest_path
        )
    except NativeGoalResolverError as error:
        code = (
            "project_profile_required" if error.code == "native_goal_profile_required"
            else "project_goal_admission_unavailable"
        )
        raise ProjectResolverError(code, diagnostics=error.diagnostics) from error
    profile = selected.admission.filesystem_profile
    if selected.capability is None or profile is None:
        return ProjectResolverAdmission(selected.admission, None)
    if profile.protocol_manifest.protocol.profile != COLLABORATION_PROJECT_FS_PROFILE:
        raise ProjectResolverError("project_profile_required")
    bindings = tuple(item for item in profile.record_bindings if item.record_key == "project")
    if len(bindings) != 1:
        raise ProjectResolverError("project_binding_unavailable")
    capability = object.__new__(ProjectResolverCapability)
    _ISSUED[capability] = _RetainedProjectAdmission(
        selected.capability, bindings[0].root, bindings[0].path_template, os.getpid()
    )
    capability.revalidate()
    return ProjectResolverAdmission(selected.admission, capability)
