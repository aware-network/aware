"""Process-local native source capability, issued only by fresh admission.

This guards public caller-data entrances, not hostile Python code running with
access to module internals. No serialized object or digest authenticates it.
Goal owns committed-file/Goal identity, carrier, Gate and Git-epoch checks.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import NoReturn, SupportsIndex
from weakref import WeakKeyDictionary

from aware_protocol_runtime import ProtocolAdmissionOutcomeKind, ProtocolContractError

from .goal_templates import canonical_relative_path, match_native_goal_path
from .manifest import (
    COLLABORATION_NATIVE_FS_PROFILE,
    FilesystemProtocolAdmissionResult,
    FilesystemProtocolProfile,
    admit_protocol_manifest,
    resolve_repository_path_at_use,
)


class NativeGoalResolverError(ProtocolContractError):
    """Pre-source typed refusal; never fabricates a Goal observation envelope."""

    def __init__(self, code: str, *, diagnostics: tuple[str, ...] = ()) -> None:
        self.code = code
        self.diagnostics = (code, *diagnostics)
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class NativeGoalLocation:
    relative_path: str
    resolved_path: Path
    location_date: str
    location_slug: str


@dataclass(frozen=True, slots=True)
class _RetainedAdmission:
    repository_root: Path
    repository_identity: tuple[int, int]
    manifest_path: Path
    resolved_manifest_path: Path
    manifest_sha256: str
    profile: FilesystemProtocolProfile
    goal_root: str
    goal_template: str
    issuer_pid: int


_ISSUED: WeakKeyDictionary[NativeGoalResolverCapability, _RetainedAdmission] = WeakKeyDictionary()


class NativeGoalResolverCapability:
    """Opaque issuer-retained capability; public construction is forbidden."""

    __slots__ = ("__weakref__",)

    def __new__(cls) -> NativeGoalResolverCapability:
        raise TypeError("use admit_native_goal_resolver")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("native Goal capability cannot be subclassed")

    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("native Goal capability cannot be copied or serialized")

    @property
    def repository_root(self) -> Path:
        return _retained(self).repository_root

    @property
    def manifest_sha256(self) -> str:
        return _retained(self).manifest_sha256

    @property
    def manifest_path(self) -> Path:
        return _retained(self).manifest_path

    @property
    def goal_root(self) -> str:
        return _retained(self).goal_root

    @property
    def goal_template(self) -> str:
        return _retained(self).goal_template

    @property
    def protocol_digest(self) -> str:
        return _retained(self).profile.protocol_manifest.digest

    def revalidate(self) -> None:
        retained = _retained(self)
        try:
            root = retained.repository_root.resolve(strict=True)
            stat = root.stat()
        except (OSError, RuntimeError, ValueError) as error:
            raise NativeGoalResolverError("native_goal_repository_unavailable") from error
        if root != retained.repository_root or (stat.st_dev, stat.st_ino) != retained.repository_identity:
            raise NativeGoalResolverError("native_goal_repository_changed")
        current = admit_protocol_manifest(
            repository_root=root, manifest_path=retained.manifest_path,
        )
        if current.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1:
            raise NativeGoalResolverError("native_goal_admission_unavailable", diagnostics=current.diagnostics)
        if current.source_sha256 != retained.manifest_sha256 or current.filesystem_profile != retained.profile:
            raise NativeGoalResolverError("native_goal_manifest_changed")
        try:
            resolved_manifest = retained.manifest_path.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as error:
            raise NativeGoalResolverError("native_goal_manifest_unavailable") from error
        if resolved_manifest != retained.resolved_manifest_path:
            raise NativeGoalResolverError("native_goal_manifest_source_changed")

    def match_goal_path(self, relative_path: str) -> tuple[str, str] | None:
        """Bounded location classification for committed-tree discovery.

        Returned date/slug is location metadata, never authenticated Goal identity.
        Revalidate at use; Goal still verifies each candidate's committed source.
        """
        self.revalidate()
        retained = _retained(self)
        prefix = retained.goal_root + "/"
        if not canonical_relative_path(relative_path) or not relative_path.startswith(prefix):
            return None
        return match_native_goal_path(retained.goal_template, relative_path[len(prefix):])

    def resolve_goal_path(self, relative_path: str) -> NativeGoalLocation:
        """Revalidate binding and topology without reading Goal source bytes."""
        match = self.match_goal_path(relative_path)
        if match is None:
            raise NativeGoalResolverError("native_goal_target_outside_binding")
        retained = _retained(self)
        root_resolution = resolve_repository_path_at_use(
            repository_root=retained.repository_root,
            relative_path=retained.goal_root,
            field_name="records.goal.root",
        )
        resolution = resolve_repository_path_at_use(
            repository_root=retained.repository_root,
            relative_path=relative_path,
            field_name="records.goal.target",
        )
        if root_resolution.path is None or resolution.path is None:
            raise NativeGoalResolverError("native_goal_target_unresolvable", diagnostics=root_resolution.diagnostics + resolution.diagnostics)
        if not resolution.path.is_relative_to(root_resolution.path):
            raise NativeGoalResolverError("native_goal_target_outside_binding")
        self.revalidate()
        return NativeGoalLocation(relative_path, resolution.path, *match)


def _retained(capability: object) -> _RetainedAdmission:
    if type(capability) is not NativeGoalResolverCapability:
        raise NativeGoalResolverError("native_goal_capability_invalid")
    retained = _ISSUED.get(capability)
    if retained is None:
        raise NativeGoalResolverError("native_goal_capability_invalid")
    if retained.issuer_pid != os.getpid():
        raise NativeGoalResolverError("native_goal_capability_foreign_process")
    return retained


def require_native_goal_resolver(capability: object) -> NativeGoalResolverCapability:
    """Validate actual issuance and freshness, not just nominal type/digest."""
    _retained(capability)
    assert isinstance(capability, NativeGoalResolverCapability)
    capability.revalidate()
    return capability


@dataclass(frozen=True, slots=True)
class NativeGoalResolverAdmission:
    admission: FilesystemProtocolAdmissionResult
    capability: NativeGoalResolverCapability | None


def admit_native_goal_resolver(*, repository_root: Path, manifest_path: Path) -> NativeGoalResolverAdmission:
    """The sole public issuer: fresh on-disk native admission, never decoded data."""
    admission = admit_protocol_manifest(repository_root=repository_root, manifest_path=manifest_path)
    profile = admission.filesystem_profile
    if profile is None:
        return NativeGoalResolverAdmission(admission, None)
    if profile.protocol_manifest.protocol.profile != COLLABORATION_NATIVE_FS_PROFILE:
        raise NativeGoalResolverError("native_goal_profile_required")
    try:
        root = repository_root.resolve(strict=True)
        stat = root.stat()
        resolved_manifest = manifest_path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise NativeGoalResolverError("native_goal_issuance_source_unavailable") from error
    binding = next(item for item in profile.record_bindings if item.record_key == "goal")
    assert admission.source_sha256 is not None
    capability = object.__new__(NativeGoalResolverCapability)
    _ISSUED[capability] = _RetainedAdmission(
        root, (stat.st_dev, stat.st_ino), manifest_path.absolute(),
        resolved_manifest, admission.source_sha256, profile,
        binding.root, binding.path_template, os.getpid(),
    )
    # Reread before issuing; any concurrent manifest/root change refuses.
    capability.revalidate()
    return NativeGoalResolverAdmission(admission, capability)
