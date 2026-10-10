"""Issuer-retained source selection for the read-only SPEC FS composition.

This is a process-local supported-entrance boundary, not hostile-code isolation.
Protocol owns selection/topology; SPEC owns parsing, source evidence and meaning.
"""

from __future__ import annotations

import os
import stat
import threading
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import NoReturn, Protocol, SupportsIndex, cast, final, override
from weakref import WeakKeyDictionary, finalize

from aware_protocol_runtime import ProtocolAdmissionOutcomeKind, ProtocolContractError

from .goal_templates import canonical_relative_path
from .manifest import (
    COLLABORATION_FS_PROFILE,
    FilesystemProtocolAdmissionResult,
    FilesystemProtocolProfile,
    admit_protocol_manifest_bytes,
)

SPECIFICATION_PATH_TEMPLATE = "<spec-key>/aware.spec.toml"
MAX_SELECTED_SPECIFICATIONS = 64


class _PostimageOwner(Protocol):
    def require_package_postimage_read(self, value: object) -> object: ...
    def validate_package_postimage_read(
        self, value: object, *, plan: object
    ) -> None: ...
    def release_package_postimage_read(self, value: object) -> None: ...


@dataclass(frozen=True, slots=True)
class _PublishedCorrelation:
    reader: object
    owner_module: ModuleType

    def validate(self) -> None:
        module = import_module("aware_file_system.retained_package")
        if module is not self.owner_module:
            raise SpecificationSelectionError("specification_selection_owner_changed")
        _ = cast(_PostimageOwner, cast(object, module)).require_package_postimage_read(
            self.reader
        )

    def release(self) -> None:
        cast(
            _PostimageOwner, cast(object, self.owner_module)
        ).release_package_postimage_read(self.reader)


@dataclass(slots=True)
class _SelectionResources:
    descriptor: int
    correlation: _PublishedCorrelation | None = None
    cleanup_attempted: bool = False
    cleanup_outcome: str = "not_attempted"
    cleanup_diagnostics: tuple[str, ...] = ()


def _cleanup_selection(resources: _SelectionResources) -> None:
    # Read-only cleanup never removes packages or scratch. Attempt both closes.
    # This original ledger survives registry retirement. Do not retry ambiguous
    # closes: the numeric descriptor may already belong to a different owner.
    if resources.cleanup_attempted:
        return
    resources.cleanup_attempted = True
    resources.cleanup_outcome = "unknown"
    primary: BaseException | None = None
    try:
        if resources.correlation is not None:
            resources.correlation.release()
    except BaseException as error:  # noqa: BLE001 -- attempt every owned close on interruption
        primary = error
        resources.cleanup_diagnostics = (
            f"selection_correlation_cleanup_failed:{type(error).__name__}",
        )
    try:
        os.close(resources.descriptor)
    except BaseException as error:  # noqa: BLE001 -- retain ambiguous close without retry
        resources.cleanup_diagnostics = (
            *resources.cleanup_diagnostics,
            f"selection_descriptor_cleanup_failed:{type(error).__name__}",
        )
        if primary is None:
            primary = error
        else:
            primary.add_note(
                f"selection_descriptor_cleanup_failed:{type(error).__name__}"
            )
    resources.cleanup_outcome = "incomplete" if primary is not None else "completed"
    if primary is not None:
        raise primary


class SpecificationSelectionError(ProtocolContractError):
    """Typed pre-source refusal; never an invented SPEC operation result."""

    code: str
    diagnostics: tuple[str, ...]

    def __init__(self, code: str, *, diagnostics: tuple[str, ...] = ()) -> None:
        self.code = code
        self.diagnostics = (code, *diagnostics)
        super().__init__(code)


class SpecificationSelectionConsumer(Protocol):
    """Trusted factory result; owner close also retires its own admissions."""

    def close(self) -> None: ...


_Identity = tuple[int, int, int]


def _identity(fd: int) -> _Identity:
    value = os.fstat(fd)
    # Linux mount identity complements device/inode. No SPEC owner imports.
    try:
        lines = Path(f"/proc/self/fdinfo/{fd}").read_text(encoding="ascii").splitlines()
        mounts = [
            line.split("\t", 1)[1] for line in lines if line.startswith("mnt_id:\t")
        ]
        if len(mounts) != 1 or not mounts[0].isdigit():
            raise ValueError("mount identity unavailable")
    except (OSError, ValueError, UnicodeError) as error:
        raise SpecificationSelectionError(
            "specification_selection_platform_unsupported"
        ) from error
    return value.st_dev, value.st_ino, int(mounts[0])


def _namespace() -> tuple[int, int, bytes]:
    try:
        value = os.stat("/proc/self/ns/mnt")
        body = Path("/proc/self/mountinfo").read_bytes()
    except OSError as error:
        raise SpecificationSelectionError(
            "specification_selection_platform_unsupported"
        ) from error
    return value.st_dev, value.st_ino, sha256(body).digest()


def _canonical(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        body = value.encode("utf-8", "strict")
    except UnicodeError:
        return False
    return (
        len(body) <= 1024
        and canonical_relative_path(value)
        and unicodedata.is_normalized("NFC", value)
        and not any(0x7F <= ord(char) <= 0x9F for char in value)
    )


def _walk(
    base_fd: int, parts: tuple[str, ...], *, missing_allowed: bool
) -> tuple[int | None, dict[str, _Identity]]:
    """Open existing directories without following links; never read SPEC bytes."""
    current = os.dup(base_fd)
    identities: dict[str, _Identity] = {}
    try:
        for index, part in enumerate(parts):
            try:
                before = os.stat(part, dir_fd=current, follow_symlinks=False)
            except FileNotFoundError:
                if missing_allowed:
                    os.close(current)
                    return None, identities
                raise
            if not stat.S_ISDIR(before.st_mode):
                raise SpecificationSelectionError(
                    "specification_selection_path_unresolvable"
                )
            following = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=current,
            )
            try:
                identity = _identity(following)
                if identity[:2] != (before.st_dev, before.st_ino):
                    raise SpecificationSelectionError(
                        "specification_selection_topology_changed"
                    )
            except BaseException:
                os.close(following)
                raise
            os.close(current)
            current = following
            identities["/".join(parts[: index + 1])] = identity
        return current, identities
    except BaseException:
        os.close(current)
        raise


def _manifest_source(
    base_fd: int, relative: str
) -> tuple[bytes, _Identity, dict[str, _Identity]]:
    parts = tuple(relative.split("/"))
    parent, parents = _walk(base_fd, parts[:-1], missing_allowed=False)
    assert parent is not None
    file_fd = None
    try:
        before = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise SpecificationSelectionError(
                "specification_selection_manifest_unresolvable"
            )
        file_fd = os.open(
            parts[-1],
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=parent,
        )
        initial = os.fstat(file_fd)
        if not stat.S_ISREG(initial.st_mode) or (initial.st_dev, initial.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise SpecificationSelectionError(
                "specification_selection_manifest_changed"
            )
        # Bound the owner-read bytes before passing them to canonical admission.
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(file_fd, 65536)
            if not chunk:
                break
            size += len(chunk)
            if size > 1_048_576:
                raise SpecificationSelectionError(
                    "specification_selection_manifest_too_large"
                )
            chunks.append(chunk)
        final_stat = os.fstat(file_fd)
        after = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        if (
            initial.st_dev,
            initial.st_ino,
            initial.st_mode,
            initial.st_size,
            initial.st_mtime_ns,
            initial.st_ctime_ns,
        ) != (
            final_stat.st_dev,
            final_stat.st_ino,
            final_stat.st_mode,
            final_stat.st_size,
            final_stat.st_mtime_ns,
            final_stat.st_ctime_ns,
        ) or (after.st_dev, after.st_ino) != (initial.st_dev, initial.st_ino):
            raise SpecificationSelectionError(
                "specification_selection_manifest_changed"
            )
        return (
            b"".join(chunks),
            _identity(file_fd),
            parents,
        )
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(parent)


def _selected_topology(base_fd: int, roots: tuple[str, ...]) -> dict[str, _Identity]:
    observed: dict[str, _Identity] = {}
    for root in roots:
        directory, identities = _walk(
            base_fd, tuple(root.split("/")), missing_allowed=True
        )
        observed.update(identities)
        if directory is not None:
            try:
                try:
                    source = os.stat(
                        "aware.spec.toml", dir_fd=directory, follow_symlinks=False
                    )
                except FileNotFoundError:
                    continue  # Availability/content remain the SPEC owner's checks.
                if not stat.S_ISREG(source.st_mode):
                    raise SpecificationSelectionError(
                        "specification_selection_path_unresolvable"
                    )
            finally:
                os.close(directory)
    return observed


@dataclass(frozen=True, slots=True)
class _RetainedSelection:
    repository_root: Path
    repository_fd: int
    repository_identity: _Identity
    namespace: tuple[int, int, bytes]
    manifest_path: Path
    manifest_relative: str
    manifest_sha256: str
    manifest_identity: _Identity
    profile: FilesystemProtocolProfile
    selected_manifest_paths: tuple[str, ...]
    roots: tuple[str, ...]
    topology: dict[str, _Identity]
    issuer_pid: int
    lock: threading.RLock
    finalizer: Callable[[], object]
    resources: _SelectionResources


_ISSUED: WeakKeyDictionary[SpecificationSourceSelection, _RetainedSelection] = (
    WeakKeyDictionary()
)


@final
class SpecificationSourceSelection:
    """Opaque source selection, never write or committed-Git authorization."""

    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> SpecificationSourceSelection:
        raise TypeError("use admit_specification_selection")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("SPEC selection cannot be subclassed")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> NoReturn:
        raise TypeError("SPEC selection cannot be copied or serialized")

    @property
    def repository_root(self) -> Path:
        return _retained(self).repository_root

    @property
    def manifest_sha256(self) -> str:
        return _retained(self).manifest_sha256

    @property
    def selected_manifest_paths(self) -> tuple[str, ...]:
        return _retained(self).selected_manifest_paths

    def revalidate(self) -> None:
        retained = _retained(self)
        with retained.lock:
            _ = _retained(self)
            try:
                if retained.resources.correlation is not None:
                    retained.resources.correlation.validate()
                if _namespace() != retained.namespace:
                    raise SpecificationSelectionError(
                        "specification_selection_topology_changed"
                    )
                current_fd = os.open(
                    retained.repository_root,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                )
                try:
                    if (
                        _identity(current_fd) != retained.repository_identity
                        or _identity(retained.repository_fd)
                        != retained.repository_identity
                    ):
                        raise SpecificationSelectionError(
                            "specification_selection_repository_changed"
                        )
                finally:
                    os.close(current_fd)
                body, identity, manifest_parents = _manifest_source(
                    retained.repository_fd, retained.manifest_relative
                )
                digest = "sha256:" + sha256(body).hexdigest()
                # Bytes come only from this live descriptor, never caller data.
                current = admit_protocol_manifest_bytes(
                    source=body, repository_root=retained.repository_root
                )
                if current.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1:
                    raise SpecificationSelectionError(
                        "specification_selection_admission_unavailable",
                        diagnostics=current.diagnostics,
                    )
                if (
                    digest != retained.manifest_sha256
                    or identity != retained.manifest_identity
                    or current.source_sha256 != digest
                    or current.filesystem_profile != retained.profile
                ):
                    raise SpecificationSelectionError(
                        "specification_selection_manifest_changed"
                    )
                topology = _selected_topology(retained.repository_fd, retained.roots)
                topology.update(manifest_parents)
                if any(
                    topology.get(path) != identity
                    for path, identity in retained.topology.items()
                ):
                    raise SpecificationSelectionError(
                        "specification_selection_topology_changed"
                    )
                # Missing tails may become real directories. Once observed,
                # their identity is retained for subsequent use/return checks.
                retained.topology.update(topology)
                if retained.resources.correlation is not None:
                    retained.resources.correlation.validate()
            except OSError as error:
                if retained.resources.correlation is not None:
                    _retire_correlated_selection(self, retained, error)
                raise SpecificationSelectionError(
                    "specification_selection_source_unavailable",
                    diagnostics=(f"filesystem_detail:{type(error).__name__}",),
                ) from error
            except BaseException as error:
                if retained.resources.correlation is not None:
                    _retire_correlated_selection(self, retained, error)
                    if isinstance(error, Exception) and not isinstance(
                        error, SpecificationSelectionError
                    ):
                        raise SpecificationSelectionError(
                            "specification_selection_postimage_changed",
                            diagnostics=(f"owner_detail:{type(error).__name__}",),
                        ) from error
                raise


def _retire_correlated_selection(
    selection: SpecificationSourceSelection,
    retained: _RetainedSelection,
    error: BaseException,
) -> None:
    _ = _ISSUED.pop(selection, None)
    try:
        _ = retained.finalizer()
    except BaseException as cleanup_error:  # noqa: BLE001 -- cleanup cannot mask freshness refusal
        error.add_note(f"selection_cleanup_failed:{type(cleanup_error).__name__}")


def _attach_original_postimage(  # pyright: ignore[reportUnusedFunction] -- private same-owner bridge
    selection: SpecificationSourceSelection, *, reader: object, plan: object
) -> None:
    """Private original-owner join; no public callback/evidence grant entrance."""
    retained = _retained(selection)
    with retained.lock:
        if retained.resources.correlation is not None:
            raise SpecificationSelectionError(
                "specification_selection_already_correlated"
            )
        module = import_module("aware_file_system.retained_package")
        owner = cast(_PostimageOwner, cast(object, module))
        owner.validate_package_postimage_read(reader, plan=plan)
        _ = owner.require_package_postimage_read(reader)
        retained.resources.correlation = _PublishedCorrelation(reader, module)
        # From this assignment, selection owns this new reader on every exit.
        selection.revalidate()


def _release_owned_selection(selection: SpecificationSourceSelection) -> None:  # pyright: ignore[reportUnusedFunction] -- private same-owner cleanup
    """Cleanup an internally owned selection, including an already retired one."""
    retained = _ISSUED.get(selection)
    if retained is not None:
        with retained.lock:
            _ = _ISSUED.pop(selection, None)
            # Internal cleanup also closes a fork child's own descriptor copy;
            # it never grants foreign-process currentness or touches the parent.
            _ = retained.finalizer()


def _retained(selection: object) -> _RetainedSelection:
    if type(selection) is not SpecificationSourceSelection:
        raise SpecificationSelectionError("specification_selection_invalid")
    retained = _ISSUED.get(selection)
    if retained is None:
        raise SpecificationSelectionError("specification_selection_invalid_or_released")
    if retained.issuer_pid != os.getpid():
        raise SpecificationSelectionError("specification_selection_foreign_process")
    return retained


def require_specification_selection(selection: object) -> SpecificationSourceSelection:
    _ = _retained(selection)
    assert isinstance(selection, SpecificationSourceSelection)
    selection.revalidate()
    return selection


def consume_specification_selection[Consumer: SpecificationSelectionConsumer](
    selection: object,
    receiver: Callable[[int, tuple[str, ...], Callable[[], None]], Consumer],
) -> Consumer:
    """Lend a fresh duplicate to a trusted read-only factory, then revalidate.

    Receiver must clean partial construction on exception; returned consumers
    must own their duplicate and close/retire their own admissions on close().
    """
    admitted = require_specification_selection(selection)
    retained = _retained(admitted)
    with retained.lock:
        admitted.revalidate()
        borrowed = os.dup(retained.repository_fd)
        try:
            consumer = receiver(borrowed, retained.roots, admitted.revalidate)
        finally:
            os.close(borrowed)
        try:
            if not callable(getattr(consumer, "close", None)):
                raise SpecificationSelectionError(
                    "specification_selection_consumer_invalid"
                )
            admitted.revalidate()
        except BaseException as error:
            try:
                consumer.close()
            except BaseException as cleanup_error:  # noqa: BLE001 -- preserve the original refusal even if cleanup interrupts
                error.add_note(
                    f"selection_consumer_cleanup_failed:{type(cleanup_error).__name__}"
                )
            raise
        return consumer


def release_specification_selection(selection: object) -> None:
    """Explicit lifetime owner release; provider close must not call this."""
    retained = _retained(selection)
    assert isinstance(selection, SpecificationSourceSelection)
    with retained.lock:
        _ = _retained(selection)
        del _ISSUED[selection]
        _ = retained.finalizer()


@dataclass(frozen=True, slots=True)
class SpecificationSelectionAdmission:
    admission: FilesystemProtocolAdmissionResult
    selection: SpecificationSourceSelection | None


def admit_specification_selection(
    *,
    repository_root: Path,
    manifest_path: Path,
    selected_manifest_paths: tuple[str, ...],
    expected_manifest_sha256: str | None = None,
) -> SpecificationSelectionAdmission:
    """Fresh on-disk issuer. Paths are locators, not SPEC identity or authority."""
    if (
        type(selected_manifest_paths) is not tuple
        or not 1 <= len(selected_manifest_paths) <= MAX_SELECTED_SPECIFICATIONS
        or any(not _canonical(path) for path in selected_manifest_paths)
        or selected_manifest_paths
        != tuple(sorted(set(selected_manifest_paths), key=lambda p: p.encode("utf-8")))
    ):
        raise SpecificationSelectionError("specification_selection_paths_invalid")
    try:
        root = repository_root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise SpecificationSelectionError(
            "specification_selection_source_unavailable"
        ) from error
    source = manifest_path if manifest_path.is_absolute() else root / manifest_path
    source = source.absolute()
    descriptor = None
    retained_finalizer: Callable[[], object] | None = None
    selection = None
    issued = False
    try:
        try:
            relative = source.relative_to(root).as_posix()
        except ValueError as error:
            raise SpecificationSelectionError(
                "specification_selection_manifest_outside_repository"
            ) from error
        if not _canonical(relative) or relative.split("/")[-1] != "aware.protocol.toml":
            raise SpecificationSelectionError(
                "specification_selection_manifest_unresolvable"
            )
        descriptor = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        )
        identity = _identity(descriptor)
        namespace = _namespace()
        body, manifest_identity, manifest_parents = _manifest_source(
            descriptor, relative
        )
        digest = "sha256:" + sha256(body).hexdigest()
        if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
            raise SpecificationSelectionError(
                "specification_selection_manifest_changed"
            )
        # Reuse canonical admission over owner-read on-disk bytes. No bytes/DTO
        # entrance accepts caller data as issuance, and no pathname reopen occurs.
        admission = admit_protocol_manifest_bytes(source=body, repository_root=root)
        profile = admission.filesystem_profile
        if profile is None:
            return SpecificationSelectionAdmission(admission, None)
        if (
            profile.protocol_manifest.protocol.profile != COLLABORATION_FS_PROFILE
            or profile.protocol_manifest.protocol.semantic_version != 1
        ):
            raise SpecificationSelectionError(
                "specification_selection_profile_unsupported"
            )
        record = next(
            item
            for item in profile.protocol_manifest.records
            if item.record_key == "specification"
        )
        if record.role.value != "authority" or record.profile != "specification_fs_v1":
            raise SpecificationSelectionError(
                "specification_selection_authority_required"
            )
        binding = next(
            item
            for item in profile.record_bindings
            if item.record_key == "specification"
        )
        if (
            not _canonical(binding.root)
            or binding.path_template != SPECIFICATION_PATH_TEMPLATE
        ):
            raise SpecificationSelectionError(
                "specification_selection_binding_unsupported"
            )
        roots: list[str] = []
        for path in selected_manifest_paths:
            prefix = binding.root + "/"
            tail = path.removeprefix(prefix).split("/")
            if (
                not path.startswith(prefix)
                or len(tail) != 2
                or tail[-1] != "aware.spec.toml"
            ):
                raise SpecificationSelectionError(
                    "specification_selection_target_outside_binding"
                )
            roots.append(path.removesuffix("/aware.spec.toml"))
        ordered_roots = tuple(roots)
        topology = _selected_topology(descriptor, ordered_roots)
        topology.update(manifest_parents)
        selection = object.__new__(SpecificationSourceSelection)
        resources = _SelectionResources(descriptor)
        retained_finalizer = finalize(selection, _cleanup_selection, resources)
        _ISSUED[selection] = _RetainedSelection(
            root,
            descriptor,
            identity,
            namespace,
            source,
            relative,
            digest,
            manifest_identity,
            profile,
            selected_manifest_paths,
            ordered_roots,
            topology,
            os.getpid(),
            threading.RLock(),
            retained_finalizer,
            resources,
        )
        selection.revalidate()
        issued = True
        return SpecificationSelectionAdmission(admission, selection)
    except OSError as error:
        raise SpecificationSelectionError(
            "specification_selection_source_unavailable",
            diagnostics=(f"filesystem_detail:{type(error).__name__}",),
        ) from error
    finally:
        if not issued:
            if selection is not None:
                _ = _ISSUED.pop(selection, None)
            if retained_finalizer is not None:
                _ = retained_finalizer()
            elif descriptor is not None:
                os.close(descriptor)
