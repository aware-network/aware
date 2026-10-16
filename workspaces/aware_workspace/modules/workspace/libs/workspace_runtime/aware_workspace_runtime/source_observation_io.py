"""Bounded descriptor-confined root verification; no watcher or package parser."""

from __future__ import annotations

import os
import stat
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class SourceObservationUnavailable(RuntimeError):
    """The complete bounded observation cannot be established."""


@dataclass(frozen=True, slots=True)
class SourceObservationLimits:
    maximum_files: int = 4096
    maximum_directories: int = 16384
    maximum_body_bytes: int = 8 * 1024 * 1024
    maximum_total_bytes: int = 64 * 1024 * 1024

    def __post_init__(self) -> None:
        for name, ceiling in (
            ("maximum_files", 16384),
            ("maximum_directories", 16384),
            ("maximum_body_bytes", 512 * 1024 * 1024),
            ("maximum_total_bytes", 512 * 1024 * 1024),
        ):
            value = getattr(self, name)
            if type(value) is not int or not 0 < value <= ceiling:
                raise ValueError(f"invalid {name}")


def validate_relative_path(path: str) -> tuple[str, ...]:
    if type(path) is not str or not path or len(path.encode("utf-8")) > 4096:
        raise SourceObservationUnavailable("invalid_relative_path")
    parts = tuple(path.split("/"))
    if (
        unicodedata.normalize("NFC", path) != path
        or "\\" in path
        or "\0" in path
        or len(parts) > 128
        or any(
            p in {"", ".", ".."} or not p.strip() or len(p.encode("utf-8")) > 255
            for p in parts
        )
    ):
        raise SourceObservationUnavailable("invalid_relative_path")
    return parts


def validate_root_path(path: str) -> tuple[str, ...]:
    """Dot selects the admitted repository itself; member paths remain strict."""
    return () if type(path) is str and path == "." else validate_relative_path(path)


def open_directory(root_fd: int, relative_path: str) -> int:
    parts = validate_root_path(relative_path)
    current = os.dup(root_fd)
    try:
        for part in parts:
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current
            )
            os.close(current)
            current = child
        return current
    except BaseException:
        os.close(current)
        raise


def identity(fd: int) -> tuple[int, int]:
    value = os.fstat(fd)
    return value.st_dev, value.st_ino


def _stamp(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def capture_complete_root(
    fd: int,
    limits: SourceObservationLimits,
) -> tuple[tuple[str, bytes], ...]:
    return _capture_root(fd, limits, ())


def capture_selected_root(
    fd: int,
    limits: SourceObservationLimits,
    *,
    excluded_nested_roots: tuple[str, ...],
) -> tuple[tuple[str, bytes], ...]:
    """Reuse the complete-root scanner with retained-declaration exclusions."""
    if type(excluded_nested_roots) is not tuple or excluded_nested_roots != tuple(
        sorted(set(excluded_nested_roots), key=str.encode)
    ):
        raise SourceObservationUnavailable("nested_root_set_invalid")
    for path in excluded_nested_roots:
        validate_relative_path(path)
    return _capture_root(fd, limits, excluded_nested_roots)


def _capture_root(
    fd: int,
    limits: SourceObservationLimits,
    excluded_nested_roots: tuple[str, ...],
) -> tuple[tuple[str, bytes], ...]:
    """Read every regular file, refusing unsupported members and partial capture.

    This is an operation-scoped verifier of a root, not a second maintained
    repository observer. Stable sequential reads do not establish atomicity.
    """
    rows: list[tuple[str, bytes]] = []
    total = 0
    directories = 0
    exclusions = set(excluded_nested_roots)
    seen_exclusions: set[str] = set()

    def walk(directory: int, prefix: str) -> None:
        nonlocal total, directories
        directories += 1
        if directories > limits.maximum_directories:
            raise SourceObservationUnavailable("directory_capacity_exceeded")
        before = os.fstat(directory)
        names = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if len(names) >= limits.maximum_files + limits.maximum_directories:
                    raise SourceObservationUnavailable(
                        "directory_entry_capacity_exceeded"
                    )
                names.append(entry.name)
        names.sort(key=lambda name: name.encode("utf-8"))
        for name in names:
            path = prefix + name
            validate_relative_path(path)
            value = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if path in exclusions:
                if not stat.S_ISDIR(value.st_mode):
                    raise SourceObservationUnavailable("nested_root_not_directory")
                seen_exclusions.add(path)
                continue
            if stat.S_ISDIR(value.st_mode):
                child = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
                )
                try:
                    if _stamp(os.fstat(child)) != _stamp(value):
                        raise SourceObservationUnavailable("directory_changed")
                    walk(child, path + "/")
                finally:
                    os.close(child)
            elif stat.S_ISREG(value.st_mode):
                if (
                    len(rows) >= limits.maximum_files
                    or value.st_size > limits.maximum_body_bytes
                ):
                    raise SourceObservationUnavailable("body_capacity_exceeded")
                source = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
                )
                try:
                    if _stamp(os.fstat(source)) != _stamp(value):
                        raise SourceObservationUnavailable("source_changed")
                    chunks = []
                    remaining = (
                        min(
                            limits.maximum_body_bytes,
                            limits.maximum_total_bytes - total,
                        )
                        + 1
                    )
                    while remaining:
                        chunk = os.read(source, min(65536, remaining))
                        if not chunk:
                            break
                        chunks.append(chunk)
                        remaining -= len(chunk)
                    body = b"".join(chunks)
                    if (
                        _stamp(os.fstat(source)) != _stamp(value)
                        or _stamp(
                            os.stat(name, dir_fd=directory, follow_symlinks=False)
                        )
                        != _stamp(value)
                        or len(body) != value.st_size
                    ):
                        raise SourceObservationUnavailable("source_changed")
                finally:
                    os.close(source)
                total += len(body)
                if total > limits.maximum_total_bytes:
                    raise SourceObservationUnavailable("total_capacity_exceeded")
                rows.append((path, body))
            else:
                raise SourceObservationUnavailable("unsupported_member")
        if _stamp(os.fstat(directory)) != _stamp(before):
            raise SourceObservationUnavailable("directory_changed")

    try:
        walk(fd, "")
    except (OSError, UnicodeError) as error:
        raise SourceObservationUnavailable("root_capture_unavailable") from error
    if seen_exclusions != exclusions:
        raise SourceObservationUnavailable("nested_root_unavailable")
    return tuple(sorted(rows, key=lambda row: row[0].encode("utf-8")))


# Fixed primitive entrances are retained at owner import, not rediscovered after IO.
_EXACT_PATH_IO = tuple(
    (name, getattr(os, name))
    for name in ("dup", "open", "close", "fstat", "stat", "read")
)
_EXACT_VALIDATE_PATH = validate_relative_path
_EXACT_STAMP = _stamp


def capture_exact_paths(
    root_fd: int,
    paths: tuple[str, ...],
    limits: SourceObservationLimits,
    *,
    _verify: Callable[[], None] | None = None,
) -> tuple[tuple[str, bytes], ...]:
    """Capture a provisional declaration set through confined descriptors.

    For provisional discovery, the caller must rederive and compare this entire
    set from captured declarations. Original revalidation may reuse the complete
    path set from a retained nominal observation only while every admitted body
    still matches its original bytes. A caller-provided path tuple alone grants
    no authority.
    """
    if _verify is not None:
        _verify()
    entries = dict(_EXACT_PATH_IO)
    io_module = os

    def io(name: str, *args: Any, **kwargs: Any) -> Any:
        if _verify is None:
            return getattr(os, name)(*args, **kwargs)
        # No semantic helper is dispatched inside this primitive. Its retained
        # binding is checked immediately; the complete owner check brackets capture.
        if os is not io_module or vars(io_module).get(name) is not entries[name]:
            raise SourceObservationUnavailable("retained_reader_substituted")
        return entries[name](*args, **kwargs)

    def release(fd: int) -> None:
        # Descriptor custody does not depend on a now-revoked read guard.
        (entries["close"] if _verify is not None else os.close)(fd)

    validate = _EXACT_VALIDATE_PATH if _verify is not None else validate_relative_path
    stamp = _EXACT_STAMP if _verify is not None else _stamp
    if _verify is not None:
        _verify()
        if validate_relative_path is not validate or _stamp is not stamp:
            raise SourceObservationUnavailable("retained_reader_substituted")
    if (
        type(paths) is not tuple
        or not paths
        or len(paths) > limits.maximum_files
        or paths != tuple(sorted(set(paths), key=str.encode))
    ):
        raise SourceObservationUnavailable("declaration_path_set_invalid")
    directories: set[tuple[str, ...]] = {()}
    prepared_paths: list[tuple[str, tuple[str, ...]]] = []
    for path in paths:
        parts = validate(path)
        prepared_paths.append((path, parts))
        directories.update(parts[:index] for index in range(1, len(parts)))
        if len(directories) > limits.maximum_directories:
            raise SourceObservationUnavailable("directory_capacity_exceeded")
    # Operation-local directory custody; no cross-capture cache or authority.
    # Every retained edge is checked before release. The root and file stamps are
    # still checked around reads, and primitive dispatch remains authenticated.
    cache: dict[tuple[str, ...], int] = {}

    def flush() -> None:
        failure: BaseException | None = None
        try:
            for key, descriptor in cache.items():
                if key:
                    current = io(
                        "stat", key[-1], dir_fd=cache[key[:-1]], follow_symlinks=False
                    )
                    opened = io("fstat", descriptor)
                    if (current.st_dev, current.st_ino) != (
                        opened.st_dev,
                        opened.st_ino,
                    ):
                        raise SourceObservationUnavailable(
                            "declaration_directory_changed"
                        )
        finally:
            owned = tuple(cache.values())
            cache.clear()
            for descriptor in reversed(owned):
                try:
                    release(descriptor)
                except BaseException as error:  # noqa: BLE001 -- release all owned descriptors before reporting failure
                    if failure is None:
                        failure = error
            if failure is not None:
                raise failure

    def cached_directory(parts: tuple[str, ...]) -> int:
        missing = sum(parts[:i] not in cache for i in range(len(parts) + 1))
        if len(cache) + missing > 48:
            flush()
        if () not in cache:
            cache[()] = io("dup", root_fd)
        for index, component in enumerate(parts):
            key = parts[: index + 1]
            if key not in cache:
                parent = cache[parts[:index]]
                current = io("stat", component, dir_fd=parent, follow_symlinks=False)
                descriptor = io(
                    "open",
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=parent,
                )
                cache[key] = descriptor  # cleanup custody precedes any later check
                opened = io("fstat", descriptor)
                if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                    raise SourceObservationUnavailable("declaration_directory_changed")
        return cache[parts]

    rows: list[tuple[str, bytes]] = []
    chunks: list[bytes] = []
    total = 0
    try:
        for path, parts in prepared_paths:
            parent = "/".join(parts[:-1]) or "."
            try:
                if _verify is None:
                    directory = open_directory(root_fd, parent)
                else:
                    if len(parts) <= 48:
                        directory = cached_directory(parts[:-1])
                    else:
                        directory = io("dup", root_fd)
                        try:
                            for component in parts[:-1]:
                                child = io(
                                    "open",
                                    component,
                                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                    dir_fd=directory,
                                )
                                release(directory)
                                directory = child
                        except BaseException:
                            release(directory)
                            raise
                try:
                    before_directory = stamp(io("fstat", directory))
                    first = io(
                        "stat", parts[-1], dir_fd=directory, follow_symlinks=False
                    )
                    if not stat.S_ISREG(first.st_mode):
                        raise SourceObservationUnavailable(
                            "declaration_member_unsupported"
                        )
                    if first.st_size > limits.maximum_body_bytes:
                        raise SourceObservationUnavailable("body_capacity_exceeded")
                    source = io(
                        "open",
                        parts[-1],
                        os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                        dir_fd=directory,
                    )
                    try:
                        if stamp(io("fstat", source)) != stamp(first):
                            raise SourceObservationUnavailable(
                                "declaration_source_changed"
                            )
                        remaining = (
                            min(
                                limits.maximum_body_bytes,
                                limits.maximum_total_bytes - total,
                            )
                            + 1
                        )
                        chunks = []
                        while remaining:
                            chunk = io("read", source, min(65536, remaining))
                            if not chunk:
                                break
                            chunks.append(chunk)
                            remaining -= len(chunk)
                        body = b"".join(chunks)
                        if (
                            len(body) != first.st_size
                            or stamp(io("fstat", source)) != stamp(first)
                            or stamp(
                                io(
                                    "stat",
                                    parts[-1],
                                    dir_fd=directory,
                                    follow_symlinks=False,
                                )
                            )
                            != stamp(first)
                        ):
                            raise SourceObservationUnavailable(
                                "declaration_source_changed"
                            )
                    finally:
                        release(source)
                    if stamp(io("fstat", directory)) != before_directory:
                        raise SourceObservationUnavailable(
                            "declaration_directory_changed"
                        )
                finally:
                    if _verify is None or len(parts) > 48:
                        release(directory)
            except (OSError, UnicodeError) as error:
                raise SourceObservationUnavailable(
                    "declaration_capture_unavailable"
                ) from error
            total += len(body)
            if total > limits.maximum_total_bytes:
                raise SourceObservationUnavailable("total_capacity_exceeded")
            rows.append((path, body))
        if _verify is not None:
            _verify()
        return tuple(rows)
    finally:
        try:
            flush()
        finally:
            # A held Workspace IO error must not retain copied source buffers.
            rows.clear()
            prepared_paths.clear()
            chunks.clear()
            body = chunk = b""
