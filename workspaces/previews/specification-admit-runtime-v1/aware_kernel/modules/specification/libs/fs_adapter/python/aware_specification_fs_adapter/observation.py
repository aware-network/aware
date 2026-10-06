"""Descriptor-stable Linux observation for Specification filesystem roots."""

from __future__ import annotations

import os
import re
import stat
import tomllib
import unicodedata
from dataclasses import dataclass
from hashlib import sha256

from aware_specification_fs_source_contract import (
    SpecificationFsParserProfileCoordinate,
    SpecificationFsSourceClosure,
    SpecificationFsSourceMember,
    SpecificationFsSourceRole,
)
from jsonschema import Draft202012Validator

from .contracts import (
    SpecificationFsProfileOutcome,
    SpecificationFsProfileOutcomeKind,
)
from .manifest import (
    ManifestError,
    manifest_entrypoints,
    parse_manifest,
    reject_raw_dotted_keys,
)

MAX_DESCENDANTS = 16_384
MAX_DEPTH = 32

_INVARIANT = re.compile(r"invariants/[0-9]{2,}-[a-z][a-z0-9-]*/README\.md\Z")
_PHASE = re.compile(r"phases/[0-9]{2,}-[a-z][a-z0-9-]*/README\.md\Z")
_ITERATION = re.compile(
    r"phases/[0-9]{2,}-[a-z][a-z0-9-]*/iterations/"
    r"[0-9]{2,}-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z][a-z0-9-]*/README\.md\Z"
)


class ObservationError(OSError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ObservedRoot:
    outcome: SpecificationFsProfileOutcome
    closure: SpecificationFsSourceClosure | None
    identity: tuple[object, ...]


def mount_namespace_identity() -> tuple[int, int, int]:
    try:
        value = os.stat("/proc/self/ns/mnt", follow_symlinks=True)
        with open("/proc/self/mountinfo", "rb") as stream:
            mountinfo = stream.read()
    except OSError as error:
        raise ObservationError("platform_observation_unsupported") from error
    return value.st_dev, value.st_ino, int.from_bytes(sha256(mountinfo).digest(), "big")


def fd_mount_id(fd: int) -> int:
    try:
        with open(f"/proc/self/fdinfo/{fd}", encoding="ascii") as stream:
            lines = stream.read().splitlines()
    except (OSError, UnicodeError) as error:
        raise ObservationError("platform_observation_unsupported") from error
    values = [
        line.removeprefix("mnt_id:\t") for line in lines if line.startswith("mnt_id:\t")
    ]
    if len(values) != 1 or not values[0].isdigit():
        raise ObservationError("platform_observation_unsupported")
    return int(values[0])


def validate_source_base(fd: int) -> tuple[int, int, int]:
    if type(fd) is not int or fd < 0:
        raise ObservationError("source_base_invalid")
    try:
        value = os.fstat(fd)
        if not stat.S_ISDIR(value.st_mode):
            raise ObservationError("source_base_invalid")
    except OSError as error:
        raise ObservationError("source_base_invalid") from error
    return value.st_dev, value.st_ino, fd_mount_id(fd)


def _canonical_root(value: object) -> str:
    if type(value) is not str:
        raise ValueError("spec root must be exact text")
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeEncodeError as error:
        raise ValueError("spec root must be strict UTF-8") from error
    parts = value.split("/")
    if (
        not encoded
        or len(encoded) > 1024
        or not unicodedata.is_normalized("NFC", value)
        or value.startswith("/")
        or value.endswith("/")
        or "\\" in value
        or any(part in {"", ".", ".."} for part in parts)
        or any(
            ord(character) <= 0x1F
            or 0x7F <= ord(character) <= 0x9F
            or 0xD800 <= ord(character) <= 0xDFFF
            for character in value
        )
    ):
        raise ValueError("spec root must be canonical relative path")
    return value


def _open_root(base_fd: int, spec_root: str) -> int:
    current = os.dup(base_fd)
    try:
        for segment in spec_root.split("/"):
            next_fd = os.open(
                segment,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=current,
            )
            os.close(current)
            current = next_fd
        return current
    except BaseException:
        os.close(current)
        raise


def _stat_identity(
    value: os.stat_result, mnt_id: int, *, file: bool
) -> tuple[int, ...]:
    base = (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_mtime_ns,
        value.st_ctime_ns,
        mnt_id,
    )
    return (*base, value.st_nlink, value.st_size) if file else base


def _read_file(
    directory_fd: int, name: str, expected_mnt_id: int
) -> tuple[str, tuple[int, ...]]:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd)
    try:
        before = os.fstat(fd)
        import stat as stat_module

        if not stat_module.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ObservationError("source_observation_failed")
        mnt_id = fd_mount_id(fd)
        if mnt_id != expected_mnt_id:
            raise ObservationError("source_observation_failed")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 131_072)
            if not chunk:
                break
            total += len(chunk)
            if total > 2_097_152:
                raise ObservationError("source_observation_failed")
            chunks.append(chunk)
        after = os.fstat(fd)
        before_identity = _stat_identity(before, mnt_id, file=True)
        if before_identity != _stat_identity(after, fd_mount_id(fd), file=True):
            raise ObservationError("source_observation_failed")
        try:
            body = b"".join(chunks).decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            raise ObservationError("source_observation_failed") from error
        return body, before_identity
    finally:
        os.close(fd)


def _inventory(
    root_fd: int, expected_mnt_id: int
) -> tuple[dict[str, tuple[str, tuple[int, ...]]], tuple[object, ...]]:
    files: dict[str, tuple[str, tuple[int, ...]]] = {}
    directories: list[tuple[str, tuple[int, ...]]] = []
    count = 0

    def walk(directory_fd: int, prefix: str, depth: int) -> None:
        nonlocal count
        if depth > MAX_DEPTH:
            raise ObservationError("source_observation_failed")
        before = os.fstat(directory_fd)
        if fd_mount_id(directory_fd) != expected_mnt_id:
            raise ObservationError("source_observation_failed")
        with os.scandir(directory_fd) as entries:
            ordered = sorted(entries, key=lambda item: item.name.encode("utf-8"))
        for entry in ordered:
            count += 1
            if count > MAX_DESCENDANTS or type(entry.name) is not str:
                raise ObservationError("source_observation_failed")
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            value = entry.stat(follow_symlinks=False)
            import stat as stat_module

            if stat_module.S_ISLNK(value.st_mode):
                raise ObservationError("source_observation_failed")
            if stat_module.S_ISDIR(value.st_mode):
                child = os.open(
                    entry.name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=directory_fd,
                )
                try:
                    walk(child, relative, depth + 1)
                finally:
                    os.close(child)
            elif stat_module.S_ISREG(value.st_mode):
                body, identity = _read_file(directory_fd, entry.name, expected_mnt_id)
                files[relative] = (body, identity)
            else:
                raise ObservationError("source_observation_failed")
        after = os.fstat(directory_fd)
        before_identity = _stat_identity(before, expected_mnt_id, file=False)
        if before_identity != _stat_identity(
            after, fd_mount_id(directory_fd), file=False
        ):
            raise ObservationError("source_observation_failed")
        directories.append((prefix, before_identity))

    walk(root_fd, "", 0)
    return files, tuple(directories)


def _recognized_legacy(path: str) -> bool:
    return path in {"SPEC.md", "PHASES.md", "invariants/README.md"} or any(
        pattern.fullmatch(path) is not None
        for pattern in (_INVARIANT, _PHASE, _ITERATION)
    )


def _legacy_kind(paths: set[str]) -> SpecificationFsProfileOutcomeKind:
    recognized = {path for path in paths if _recognized_legacy(path)}
    complete = (
        {"SPEC.md", "PHASES.md", "invariants/README.md"} <= recognized
        and any(_INVARIANT.fullmatch(path) for path in recognized)
        and any(_PHASE.fullmatch(path) for path in recognized)
    )
    return (
        SpecificationFsProfileOutcomeKind.LEGACY_SUPPORTED_STRUCTURE
        if complete
        else SpecificationFsProfileOutcomeKind.LEGACY_NONCANONICAL_STRUCTURE
    )


def observe_root(
    base_fd: int,
    spec_root: object,
    expected_mnt_id: int,
    expected_namespace_identity: tuple[int, int, int],
    profile: SpecificationFsParserProfileCoordinate,
    validator: Draft202012Validator,
) -> ObservedRoot:
    root = _canonical_root(spec_root)
    before_namespace = mount_namespace_identity()
    if before_namespace != expected_namespace_identity:
        raise ObservationError("source_observation_failed")
    root_fd = _open_root(base_fd, root)
    try:
        if fd_mount_id(root_fd) != expected_mnt_id:
            raise ObservationError("source_observation_failed")
        root_before = os.fstat(root_fd)
        files, identities = _inventory(root_fd, expected_mnt_id)
        root_after = os.fstat(root_fd)
        if _stat_identity(root_before, expected_mnt_id, file=False) != _stat_identity(
            root_after, fd_mount_id(root_fd), file=False
        ):
            raise ObservationError("source_observation_failed")
    finally:
        os.close(root_fd)
    if expected_namespace_identity != mount_namespace_identity():
        raise ObservationError("source_observation_failed")

    manifest_value = files.get("aware.spec.toml")
    if manifest_value is None:
        kind = _legacy_kind(set(files))
        outcome = SpecificationFsProfileOutcome(
            root,
            kind,
            {
                SpecificationFsProfileOutcomeKind.LEGACY_SUPPORTED_STRUCTURE: "profile_upgrade_required",
                SpecificationFsProfileOutcomeKind.LEGACY_NONCANONICAL_STRUCTURE: "legacy_layout_unsupported",
            }[kind],
        )
        return ObservedRoot(outcome, None, identities)
    try:
        reject_raw_dotted_keys(manifest_value[0])
        raw_manifest = tomllib.loads(manifest_value[0])
        specification = raw_manifest.get("specification")
        raw_profile = (
            specification.get("profile") if type(specification) is dict else None
        )
    except (ManifestError, tomllib.TOMLDecodeError, ValueError):
        raw_profile = None
    if type(raw_profile) is str and raw_profile != "specification_fs_v1":
        outcome = SpecificationFsProfileOutcome(
            root,
            SpecificationFsProfileOutcomeKind.FOREIGN_PROFILE,
            "unsupported_specification_profile",
        )
        return ObservedRoot(outcome, None, identities)
    try:
        manifest = parse_manifest(manifest_value[0], validator)
    except ManifestError:
        outcome = SpecificationFsProfileOutcome(
            root,
            SpecificationFsProfileOutcomeKind.MALFORMED_V1,
            "malformed_specification_fs_v1",
        )
        return ObservedRoot(outcome, None, identities)
    entrypoints = {"aware.spec.toml": "manifest", **manifest_entrypoints(manifest)}
    semantic_actual = {
        path for path in files if path == "aware.spec.toml" or _recognized_legacy(path)
    }
    if semantic_actual != set(entrypoints):
        outcome = SpecificationFsProfileOutcome(
            root,
            SpecificationFsProfileOutcomeKind.MALFORMED_V1,
            "malformed_specification_fs_v1",
        )
        return ObservedRoot(outcome, None, identities)
    role_by_text = {role.value: role for role in SpecificationFsSourceRole}
    try:
        members = tuple(
            SpecificationFsSourceMember(
                path, role_by_text[entrypoints[path]], files[path][0]
            )
            for path in sorted(entrypoints, key=lambda item: item.encode("utf-8"))
        )
        closure = SpecificationFsSourceClosure(root, profile, members)
    except (KeyError, ValueError):
        outcome = SpecificationFsProfileOutcome(
            root,
            SpecificationFsProfileOutcomeKind.MALFORMED_V1,
            "malformed_specification_fs_v1",
        )
        return ObservedRoot(outcome, None, identities)
    outcome = SpecificationFsProfileOutcome(
        root, SpecificationFsProfileOutcomeKind.CANONICAL_V1, "canonical"
    )
    return ObservedRoot(outcome, closure, identities)
