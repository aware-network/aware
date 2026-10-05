"""Strict ``aware.protocol.toml`` filesystem admission."""

from __future__ import annotations

import errno
import json
import tomllib
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Mapping, cast
from types import MappingProxyType

from jsonschema import Draft202012Validator

from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAdmissionResult,
    ProtocolAuthorityMode,
    ProtocolBootstrap,
    ProtocolContractError,
    ProtocolIdentity,
    ProtocolManifest,
    ProtocolRecordBinding,
    ProtocolRecordRole,
    ProtocolTarget,
    ProtocolTargetKind,
)

from .goal_templates import NATIVE_GOAL_PATH_TEMPLATES, canonical_relative_path

MANIFEST_FILENAME = "aware.protocol.toml"
COLLABORATION_PROTOCOL_NAME = "aware.collaboration"
COLLABORATION_FS_PROFILE = "aware.collaboration.fs_v1"
COLLABORATION_NATIVE_FS_PROFILE = "aware.collaboration.fs_v2"
NATIVE_GOAL_RECORD_PROFILE = "aware.goal.phase.markdown.v1"
SUPPORTED_RECORD_PROFILES: Mapping[str, str] = {
    "goal": "aware.goal.markdown.v1",
    "issue": "aware.issue.markdown.v1",
    "feed": "aware.feed.projection.v1",
    "specification": "specification_fs_v1",
    "evidence": "aware.protocol.evidence.v1",
}
SUPPORTED_NATIVE_RECORD_PROFILES: Mapping[str, str] = MappingProxyType({
    **SUPPORTED_RECORD_PROFILES,
    "goal": NATIVE_GOAL_RECORD_PROFILE,
})


@dataclass(frozen=True, slots=True)
class FilesystemRecordBinding:
    record_key: str
    root: str
    path_template: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("record_key", self.record_key),
            ("root", self.root),
            ("path_template", self.path_template),
        ):
            if type(value) is not str or not value:
                raise ProtocolContractError(
                    f"filesystem binding {field_name} must be non-empty text"
                )

    def to_wire(self) -> dict[str, str]:
        return {
            "record_key": self.record_key,
            "root": self.root,
            "path_template": self.path_template,
        }


@dataclass(frozen=True, slots=True)
class FilesystemProtocolProfile:
    protocol_manifest: ProtocolManifest
    agent_contract_path: str
    record_bindings: tuple[FilesystemRecordBinding, ...]

    def __post_init__(self) -> None:
        if type(self.protocol_manifest) is not ProtocolManifest:
            raise ProtocolContractError(
                "protocol_manifest must be ProtocolManifest"
            )
        if type(self.agent_contract_path) is not str or not self.agent_contract_path:
            raise ProtocolContractError(
                "agent_contract_path must be non-empty text"
            )
        try:
            bindings = tuple(self.record_bindings)
        except TypeError as error:
            raise ProtocolContractError(
                "record_bindings must be iterable"
            ) from error
        if any(type(item) is not FilesystemRecordBinding for item in bindings):
            raise ProtocolContractError(
                "record_bindings must contain FilesystemRecordBinding"
            )
        keys = tuple(item.record_key for item in bindings)
        if len(keys) != len(set(keys)):
            raise ProtocolContractError(
                "filesystem record bindings must have unique record_key"
            )
        expected_keys = {
            item.record_key
            for item in self.protocol_manifest.records
            if item.role is not ProtocolRecordRole.UNAVAILABLE
        }
        if set(keys) != expected_keys:
            raise ProtocolContractError(
                "filesystem record bindings must match available Protocol records"
            )
        if (
            self.protocol_manifest.bootstrap.agent_contract_ref
            != f"repository:{self.agent_contract_path}"
        ):
            raise ProtocolContractError(
                "agent_contract_path must match Protocol bootstrap reference"
            )
        object.__setattr__(self, "record_bindings", bindings)

    def to_wire(self) -> dict[str, object]:
        return {
            "protocol_manifest": self.protocol_manifest.to_wire(),
            "agent_contract_path": self.agent_contract_path,
            "record_bindings": [item.to_wire() for item in self.record_bindings],
        }


@dataclass(frozen=True, slots=True)
class FilesystemProtocolAdmissionResult:
    admission: ProtocolAdmissionResult
    filesystem_profile: FilesystemProtocolProfile | None = None

    def __post_init__(self) -> None:
        if type(self.admission) is not ProtocolAdmissionResult:
            raise ProtocolContractError(
                "admission must be ProtocolAdmissionResult"
            )
        if (
            self.filesystem_profile is not None
            and type(self.filesystem_profile) is not FilesystemProtocolProfile
        ):
            raise ProtocolContractError(
                "filesystem_profile must be FilesystemProtocolProfile or null"
            )
        if self.admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1:
            if self.filesystem_profile is None:
                raise ProtocolContractError(
                    "canonical filesystem admission requires filesystem_profile"
                )
            if self.filesystem_profile.protocol_manifest is not self.admission.manifest:
                raise ProtocolContractError(
                    "filesystem_profile must retain the admitted Protocol manifest"
                )
        elif self.filesystem_profile is not None:
            raise ProtocolContractError(
                "refused filesystem admission must not expose filesystem_profile"
            )

    @property
    def outcome(self) -> ProtocolAdmissionOutcomeKind:
        return self.admission.outcome

    @property
    def source_sha256(self) -> str | None:
        return self.admission.source_sha256

    @property
    def manifest(self) -> ProtocolManifest | None:
        return self.admission.manifest

    @property
    def diagnostics(self) -> tuple[str, ...]:
        return self.admission.diagnostics


@dataclass(frozen=True, slots=True)
class RepositoryPathResolution:
    """At-use resolution of one repository-relative concrete target."""

    path: Path | None
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.path is None) == (not self.diagnostics):
            raise ProtocolContractError(
                "repository path resolution requires either path or diagnostics"
            )


def protocol_manifest_schema() -> dict[str, object]:
    resource = files("aware_protocol_fs_adapter").joinpath(
        "schemas/aware-protocol-manifest-v1.schema.json"
    )
    return cast(dict[str, object], json.loads(resource.read_text(encoding="utf-8")))


def admit_protocol_manifest(
    *,
    manifest_path: Path,
    repository_root: Path,
) -> FilesystemProtocolAdmissionResult:
    root_resolution = _resolve_repository_root(
        repository_root=repository_root,
        source_digest=None,
    )
    if isinstance(root_resolution, FilesystemProtocolAdmissionResult):
        return root_resolution
    resolved_root = root_resolution
    try:
        resolved_manifest = manifest_path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        return _failure_without_source(
            outcome=ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE,
            diagnostics=(_filesystem_diagnostic("manifest_unavailable", error),),
        )
    try:
        _ = resolved_manifest.relative_to(resolved_root)
    except ValueError:
        return _failure_without_source(
            outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
            diagnostics=("manifest_outside_repository_root",),
        )
    if resolved_manifest.name != MANIFEST_FILENAME:
        return _failure_without_source(
            outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
            diagnostics=(f"manifest_filename_must_be:{MANIFEST_FILENAME}",),
        )
    try:
        source = resolved_manifest.read_bytes()
    except OSError as error:
        return _failure_without_source(
            outcome=ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE,
            diagnostics=(_filesystem_diagnostic("manifest_unreadable", error),),
        )
    return admit_protocol_manifest_bytes(
        source=source,
        repository_root=resolved_root,
    )


def admit_protocol_manifest_bytes(
    *,
    source: bytes,
    repository_root: Path,
) -> FilesystemProtocolAdmissionResult:
    source_digest = _source_digest(source)
    root_resolution = _resolve_repository_root(
        repository_root=repository_root,
        source_digest=source_digest,
    )
    if isinstance(root_resolution, FilesystemProtocolAdmissionResult):
        return root_resolution
    resolved_root = root_resolution
    try:
        parsed = tomllib.loads(source.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
            diagnostics=(f"toml_parse_error:{error}",),
        )

    errors = sorted(
        Draft202012Validator(protocol_manifest_schema()).iter_errors(parsed),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
            diagnostics=tuple(_schema_diagnostic(error) for error in errors),
        )

    protocol = cast(dict[str, object], parsed["protocol"])
    if (
        protocol["name"] != COLLABORATION_PROTOCOL_NAME
        or (protocol["profile"], protocol["semantic_version"]) not in {
            (COLLABORATION_FS_PROFILE, 1), (COLLABORATION_NATIVE_FS_PROFILE, 2)
        }
    ):
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE,
            diagnostics=("unsupported_protocol_profile",),
        )

    target = cast(dict[str, object], parsed["target"])
    if target["authority_mode"] != ProtocolAuthorityMode.FILESYSTEM.value:
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.AUTHORITY_UNAVAILABLE,
            diagnostics=("filesystem_adapter_requires_filesystem_authority",),
        )

    records = cast(dict[str, dict[str, object]], parsed["records"])
    native = protocol["profile"] == COLLABORATION_NATIVE_FS_PROFILE
    supported = SUPPORTED_NATIVE_RECORD_PROFILES if native else SUPPORTED_RECORD_PROFILES
    profile_errors = tuple(
        f"record_profile_mismatch:{record_key}:{record["profile"]}"
        for record_key, record in sorted(records.items())
        if record["profile"] != supported[record_key]
    )
    if profile_errors:
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.FOREIGN_PROFILE,
            diagnostics=profile_errors,
        )

    if native:
        native_errors = tuple(
            f"native_record_requires_authority:{key}"
            for key in ("goal", "issue")
            if records[key]["role"] != ProtocolRecordRole.AUTHORITY.value
        )
        if records["goal"].get("path_template") not in NATIVE_GOAL_PATH_TEMPLATES:
            native_errors += ("native_goal_template_unsupported",)
        if not canonical_relative_path(cast(str, records["goal"].get("root", ""))):
            native_errors += ("native_goal_root_not_canonical",)
        if native_errors:
            return _admission_failure(
                source_digest=source_digest,
                outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
                diagnostics=native_errors,
            )

    containment_errors = _containment_errors(
        parsed=parsed,
        repository_root=resolved_root,
    )
    if containment_errors:
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
            diagnostics=containment_errors,
        )

    if native:
        goal_root = resolved_root / str(records["goal"]["root"])
        if goal_root.exists() and not goal_root.is_dir():
            return _admission_failure(
                source_digest=source_digest,
                outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
                diagnostics=("native_goal_root_not_directory",),
            )

    try:
        filesystem_profile = _lower(parsed)
    except (KeyError, TypeError, ValueError, ProtocolContractError) as error:
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.MALFORMED_V1,
            diagnostics=(f"lowering_error:{error}",),
        )
    admission = ProtocolAdmissionResult(
        outcome=ProtocolAdmissionOutcomeKind.CANONICAL_V1,
        source_sha256=source_digest,
        manifest=filesystem_profile.protocol_manifest,
    )
    return FilesystemProtocolAdmissionResult(
        admission=admission,
        filesystem_profile=filesystem_profile,
    )


def resolve_repository_path_at_use(
    *,
    repository_root: Path,
    relative_path: str,
    field_name: str,
) -> RepositoryPathResolution:
    """Resolve a concrete operation target under the current filesystem topology."""

    root_resolution = _resolve_repository_root(
        repository_root=repository_root,
        source_digest=None,
    )
    if isinstance(root_resolution, FilesystemProtocolAdmissionResult):
        return RepositoryPathResolution(
            path=None,
            diagnostics=root_resolution.diagnostics,
        )
    path, diagnostics = _resolve_declared_repository_path(
        repository_root=root_resolution,
        relative_path=relative_path,
        field_name=field_name,
    )
    if diagnostics:
        return RepositoryPathResolution(path=None, diagnostics=diagnostics)
    if path is None:
        raise AssertionError("path resolution returned no result or diagnostic")
    return RepositoryPathResolution(path=path)


def _lower(parsed: dict[str, object]) -> FilesystemProtocolProfile:
    protocol = cast(dict[str, object], parsed["protocol"])
    target = cast(dict[str, object], parsed["target"])
    bootstrap = cast(dict[str, object], parsed["bootstrap"])
    raw_records = cast(dict[str, dict[str, object]], parsed["records"])
    records = {
        record_key: ProtocolRecordBinding(
            record_key=record_key,
            profile=str(value["profile"]),
            role=ProtocolRecordRole(str(value["role"])),
        )
        for record_key, value in raw_records.items()
    }
    manifest = ProtocolManifest.from_mapping(
        protocol=ProtocolIdentity(
            name=str(protocol["name"]),
            profile=str(protocol["profile"]),
            semantic_version=cast(int, protocol["semantic_version"]),
        ),
        target=ProtocolTarget(
            kind=ProtocolTargetKind(str(target["kind"])),
            authority_mode=ProtocolAuthorityMode(str(target["authority_mode"])),
            authority_ref=cast(str | None, target.get("authority_ref")),
        ),
        bootstrap=ProtocolBootstrap(
            agent_contract_ref=f"repository:{bootstrap['agent_contract']}",
        ),
        records=records,
    )
    bindings = tuple(
        FilesystemRecordBinding(
            record_key=record_key,
            root=str(value["root"]),
            path_template=str(value["path_template"]),
        )
        for record_key, value in sorted(raw_records.items())
        if value["role"] != ProtocolRecordRole.UNAVAILABLE.value
    )
    return FilesystemProtocolProfile(
        protocol_manifest=manifest,
        agent_contract_path=str(bootstrap["agent_contract"]),
        record_bindings=bindings,
    )


def _containment_errors(
    *,
    parsed: dict[str, object],
    repository_root: Path,
) -> tuple[str, ...]:
    candidates: list[tuple[str, str]] = []
    bootstrap = cast(dict[str, object], parsed["bootstrap"])
    candidates.append(("bootstrap.agent_contract", str(bootstrap["agent_contract"])))
    records = cast(dict[str, dict[str, object]], parsed["records"])
    for record_key, record in sorted(records.items()):
        root = record.get("root")
        if root is not None:
            candidates.append((f"records.{record_key}.root", str(root)))
    errors: list[str] = []
    for field_name, relative_path in candidates:
        resolved, resolution_errors = _resolve_declared_repository_path(
            repository_root=repository_root,
            relative_path=relative_path,
            field_name=field_name,
        )
        if resolution_errors:
            errors.extend(resolution_errors)
            continue
        if resolved is None:
            raise AssertionError("path resolution returned no result or diagnostic")
        try:
            _ = resolved.relative_to(repository_root)
        except ValueError:
            errors.append(f"repository_containment_error:{field_name}")
    return tuple(errors)


def _resolve_declared_repository_path(
    *,
    repository_root: Path,
    relative_path: str,
    field_name: str,
) -> tuple[Path | None, tuple[str, ...]]:
    """Resolve observed prefixes strictly while permitting a missing tail."""

    parts = PurePosixPath(relative_path).parts
    current = repository_root
    for index, part in enumerate(parts):
        candidate = current / part
        try:
            candidate.lstat()
        except FileNotFoundError:
            return current.joinpath(*parts[index:]), ()
        except (OSError, ValueError) as error:
            return None, _path_resolution_diagnostics(
                field_name=field_name,
                reason="filesystem_error",
                error=error,
            )

        try:
            current = candidate.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as error:
            return None, _path_resolution_diagnostics(
                field_name=field_name,
                reason=_path_resolution_failure_reason(error),
                error=error,
            )

        try:
            _ = current.relative_to(repository_root)
        except ValueError:
            return None, (f"repository_containment_error:{field_name}",)

    return current, ()


def _path_resolution_failure_reason(error: BaseException) -> str:
    if isinstance(error, RuntimeError):
        return "symlink_loop"
    if isinstance(error, OSError) and error.errno == errno.ELOOP:
        return "symlink_loop"
    return "resolution_failure"


def _path_resolution_diagnostics(
    *,
    field_name: str,
    reason: str,
    error: BaseException,
) -> tuple[str, str]:
    return (
        f"repository_path_unresolvable:{field_name}:{reason}",
        f"repository_path_resolution_detail:{field_name}:{type(error).__name__}",
    )


def _schema_diagnostic(error: object) -> str:
    path = ".".join(str(item) for item in getattr(error, "absolute_path", ()))
    message = str(getattr(error, "message", "schema validation failed"))
    return f"schema_error:{path or '$'}:{message}"


def _source_digest(source: bytes) -> str:
    if type(source) is not bytes:
        raise TypeError("source must be bytes")
    return f"sha256:{sha256(source).hexdigest()}"


def _failure_without_source(
    *,
    outcome: ProtocolAdmissionOutcomeKind,
    diagnostics: tuple[str, ...],
) -> FilesystemProtocolAdmissionResult:
    return _admission_failure(
        source_digest=None,
        outcome=outcome,
        diagnostics=diagnostics,
    )


def _admission_failure(
    *,
    source_digest: str | None,
    outcome: ProtocolAdmissionOutcomeKind,
    diagnostics: tuple[str, ...],
) -> FilesystemProtocolAdmissionResult:
    return FilesystemProtocolAdmissionResult(
        admission=ProtocolAdmissionResult(
            outcome=outcome,
            source_sha256=source_digest,
            diagnostics=diagnostics,
        )
    )


def _resolve_repository_root(
    *,
    repository_root: Path,
    source_digest: str | None,
) -> Path | FilesystemProtocolAdmissionResult:
    if not isinstance(repository_root, Path):
        raise TypeError("repository_root must be pathlib.Path")
    try:
        resolved_root = repository_root.resolve(strict=True)
        if not resolved_root.is_dir():
            return _admission_failure(
                source_digest=source_digest,
                outcome=ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE,
                diagnostics=("repository_root_not_directory",),
            )
    except (OSError, RuntimeError, ValueError) as error:
        return _admission_failure(
            source_digest=source_digest,
            outcome=ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE,
            diagnostics=(_filesystem_diagnostic("repository_root_unavailable", error),),
        )
    return resolved_root


def _filesystem_diagnostic(prefix: str, error: BaseException) -> str:
    return f"{prefix}:{type(error).__name__}"
