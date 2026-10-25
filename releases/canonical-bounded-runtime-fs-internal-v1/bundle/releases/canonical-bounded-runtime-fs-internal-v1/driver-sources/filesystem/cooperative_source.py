"""Local cooperating-writer source custody, not semantic or Actor authority.

All participating mutations take the exclusive root lock and spend its epoch
before effects. A publication reservation takes the shared lock and verifies
the original capture. Arbitrary OS writers, hostile Python reflection and
remote filesystems are outside this explicitly selected local profile.

The control file is physical coordination metadata, never a branch/identity
registry. Reads do not create it. Initialization and writer setup are effects.
"""
# pyright: strict

from __future__ import annotations

import asyncio
import hashlib
import os
import stat
import threading
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import TracebackType
from typing import Literal, Never, Self, SupportsIndex, final, override
from weakref import WeakKeyDictionary, finalize

try:
    import fcntl
except ImportError:
    fcntl = None

PROFILE = "aware.filesystem.local-cooperating-source.v1"
CONTROL_NAME = ".aware-source-authority.v1"
_HEADER = b"AWARE-SOURCE-EPOCH-V1\n"
MAX_SOURCE_BYTES = 262_144
MAX_TOTAL_BYTES = 8_388_608
MAX_SOURCE_FILES = 1024


class SourceAuthorityError(OSError):
    code: str

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """Freely copyable captured facts; only the original handle owns custody."""

    path: str
    content: bytes
    source_sha256: str


@dataclass
class _ReadState:
    root: Path
    root_fd: int
    control_fd: int
    root_identity: tuple[int, int]
    control_identity: tuple[int, int]
    epoch: int
    sources: tuple[tuple[str, bytes, tuple[int, ...]], ...]
    pid: int = field(default_factory=os.getpid)
    phase: str = "retained"
    cleanup_unresolved: bool = False
    lock: threading.RLock = field(default_factory=threading.RLock)
    reservation: _ReservationState | None = None


@dataclass
class _ReservationState:
    read: _ReadState | None
    fd: int
    thread: int
    task: asyncio.Task[object] | None
    pid: int = field(default_factory=os.getpid)
    active: bool = True
    checkpoint: asyncio.Handle | None = None


_READS: WeakKeyDictionary[RetainedSourceRead, _ReadState] = WeakKeyDictionary()
_RESERVATIONS: WeakKeyDictionary[SourcePublicationReservation, _ReservationState] = (
    WeakKeyDictionary()
)


def _task() -> asyncio.Task[object] | None:
    try:
        return asyncio.current_task()
    except RuntimeError:
        return None


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _file_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _path(value: str) -> tuple[str, ...]:
    if type(value) is not str or not value or "\\" in value or "\x00" in value:
        raise SourceAuthorityError("source_path_invalid")
    try:
        if len(value.encode("utf-8")) > 1024:
            raise SourceAuthorityError("source_path_invalid")
    except UnicodeError as error:
        raise SourceAuthorityError("source_path_invalid") from error
    parsed = PurePosixPath(value)
    if (
        parsed.is_absolute()
        or parsed.as_posix() != value
        or any(part in (".", "..") for part in parsed.parts)
        or not 1 <= len(parsed.parts) <= 64
        or parsed.parts[0] == CONTROL_NAME
    ):
        raise SourceAuthorityError("source_path_invalid")
    return parsed.parts


def _close(fd: int) -> bool:
    if fd < 0:
        return True
    try:
        os.close(fd)
        return True
    except OSError:
        # Never retry an uncertain close: the descriptor may have been reused.
        return False


def _root(root: Path) -> int:
    if os.name != "posix" or fcntl is None:
        raise SourceAuthorityError("source_authority_platform_unsupported")
    if (
        type(root) is not type(Path())
        or not root.is_absolute()
        or root.resolve(strict=True) != root
    ):
        raise SourceAuthorityError("canonical_source_root_required")
    return os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)


def _control(root_fd: int, *, create: bool) -> tuple[int, bool]:
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    if create:
        try:
            return os.open(
                CONTROL_NAME, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=root_fd
            ), True
        except FileExistsError:
            pass
    try:
        return os.open(CONTROL_NAME, flags, dir_fd=root_fd), False
    except FileNotFoundError as error:
        raise SourceAuthorityError("source_authority_uninitialized") from error


def _lock(fd: int, *, exclusive: bool) -> None:
    if fcntl is None:
        raise SourceAuthorityError("source_authority_platform_unsupported")
    try:
        fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
    except BlockingIOError as error:
        raise SourceAuthorityError("source_authority_busy") from error


def _validate_control_info(info: os.stat_result) -> None:
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != 0o600
        or info.st_size != len(_HEADER) + 8
    ):
        raise SourceAuthorityError("source_control_invalid")


def _parse_epoch_body(body: bytes) -> int:
    if len(body) != len(_HEADER) + 8 or not body.startswith(_HEADER):
        raise SourceAuthorityError("source_control_invalid")
    return int.from_bytes(body[-8:], "big")


def _epoch(fd: int) -> int:
    info = os.fstat(fd)
    _validate_control_info(info)
    return _parse_epoch_body(os.pread(fd, len(_HEADER) + 8, 0))


def _unlock(fd: int) -> None:
    """Original lock release, separate from owned descriptor settlement."""
    if fcntl is None:
        raise SourceAuthorityError("source_authority_platform_unsupported")
    fcntl.flock(fd, fcntl.LOCK_UN)


def _write_epoch(fd: int, value: int) -> int:
    """Original physical write, separately observable from its durability call."""
    body = _HEADER + value.to_bytes(8, "big")
    return os.pwrite(fd, body, 0)


def _sync_epoch(fd: int) -> None:
    os.fsync(fd)


def _set_epoch(fd: int, value: int) -> None:
    if _write_epoch(fd, value) != len(_HEADER) + 8:
        raise SourceAuthorityError("source_epoch_write_incomplete")
    _sync_epoch(fd)


@contextmanager
def _locked_root(
    root: Path, *, exclusive: bool, create: bool
) -> Generator[tuple[int, int]]:
    pid = os.getpid()
    root_fd = _root(root)
    fd = -1
    locked = False
    try:
        fd, created = _control(root_fd, create=create)
        _lock(fd, exclusive=exclusive)
        locked = True
        if created:
            _set_epoch(fd, 0)
            os.fsync(root_fd)
        _ = _epoch(fd)
        if _identity(
            os.stat(CONTROL_NAME, dir_fd=root_fd, follow_symlinks=False)
        ) != _identity(os.fstat(fd)):
            raise SourceAuthorityError("source_control_replaced")
        yield root_fd, fd
    finally:
        unlocked = True
        if locked and pid == os.getpid() and fcntl is not None:
            try:
                # A retained capture duplicates this OFD to pin the inode.
                # Explicit unlock is essential: close alone would retain its lock.
                _unlock(fd)
            except OSError:
                unlocked = False
        control_closed, root_closed = _close(fd), _close(root_fd)
        if not unlocked or not control_closed or not root_closed:
            raise SourceAuthorityError("source_cleanup_unresolved")
        if pid != os.getpid():
            raise SourceAuthorityError("source_authority_process_changed")


def initialize_source_authority(root: Path) -> None:
    """Explicit local initialization; never creates a semantic namespace/branch."""
    with _locked_root(root, exclusive=True, create=True):
        pass


@contextmanager
def cooperative_source_write(root: Path) -> Generator[None]:
    """Participating writer scope: spend before any source effect, never reset."""
    with _locked_root(root, exclusive=True, create=True) as (_, fd):
        epoch = _epoch(fd)
        if epoch == (1 << 64) - 1:
            raise SourceAuthorityError("source_epoch_exhausted")
        _set_epoch(fd, epoch + 1)
        yield


def _observe(root_fd: int, path: str) -> tuple[bytes, tuple[int, ...]]:
    parts = _path(path)
    parent = root_fd
    owned_parent = False
    leaf = -1
    try:
        for part in parts[:-1]:
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent,
            )
            if owned_parent and not _close(parent):
                _ = _close(child)
                raise SourceAuthorityError("source_cleanup_unresolved")
            parent, owned_parent = child, True
        leaf = os.open(
            parts[-1],
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=parent,
        )
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > MAX_SOURCE_BYTES
        ):
            raise SourceAuthorityError("source_file_unsupported")
        chunks: list[bytes] = []
        length = 0
        while True:
            chunk = os.read(leaf, min(65_536, MAX_SOURCE_BYTES + 1 - length))
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
            if length > MAX_SOURCE_BYTES:
                raise SourceAuthorityError("source_file_limit")
        after = os.fstat(leaf)
        named = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        if _file_identity(before) != _file_identity(after) or _file_identity(
            after
        ) != _file_identity(named):
            raise SourceAuthorityError("source_changed")
        return b"".join(chunks), _file_identity(after)
    finally:
        leaf_closed = _close(leaf)
        parent_closed = not owned_parent or _close(parent)
        if not leaf_closed or not parent_closed:
            raise SourceAuthorityError("source_cleanup_unresolved")


def _require(state: _ReadState, fd: int) -> None:
    if (
        state.pid != os.getpid()
        or state.phase != "retained"
        or _identity(os.stat(state.root, follow_symlinks=False)) != state.root_identity
        or _identity(os.fstat(state.root_fd)) != state.root_identity
        or _identity(os.fstat(fd)) != state.control_identity
        or _identity(os.stat(CONTROL_NAME, dir_fd=state.root_fd, follow_symlinks=False))
        != state.control_identity
        or _epoch(fd) != state.epoch
    ):
        raise SourceAuthorityError("source_read_not_current")
    for path, body, identity in state.sources:
        observed, physical_identity = _observe(state.root_fd, path)
        if physical_identity != identity or observed != body:
            raise SourceAuthorityError("source_read_not_current")


def _unlock_close(fd: int, owner_pid: int) -> bool:
    unlocked = True
    try:
        if fd >= 0 and owner_pid == os.getpid():
            # Closing just this descriptor is insufficient after fork: the
            # child's inherited OFD can keep the parent's lock alive. Only the
            # original process may explicitly unlock that shared OFD.
            if fcntl is None:
                unlocked = False
            else:
                try:
                    _unlock(fd)
                except OSError:
                    unlocked = False
    finally:
        closed = _close(fd)
    return unlocked and closed


def _end_reservation(reservation: _ReservationState) -> None:
    if not reservation.active:
        return
    reservation.active = False
    if reservation.checkpoint is not None:
        reservation.checkpoint.cancel()
        reservation.checkpoint = None
    state, reservation.read = reservation.read, None
    reservation.task = None
    fd, reservation.fd = reservation.fd, -1
    settled = False
    try:
        settled = _unlock_close(fd, reservation.pid)
    finally:
        if state is not None:
            state.reservation = None
            state.cleanup_unresolved |= not settled
    if not settled:
        raise SourceAuthorityError("source_cleanup_unresolved")


def _retire(state: _ReadState, phase: str = "retired") -> None:
    with state.lock:
        if state.phase == "released":
            if state.cleanup_unresolved:
                raise SourceAuthorityError("source_cleanup_unresolved")
            return
        state.phase = phase
        if state.reservation is not None:
            try:
                _end_reservation(state.reservation)
            except SourceAuthorityError:
                state.cleanup_unresolved = True
        control, root = state.control_fd, state.root_fd
        state.control_fd = state.root_fd = -1
        control_closed, root_closed = _close(control), _close(root)
        state.cleanup_unresolved |= not control_closed or not root_closed
        if state.cleanup_unresolved:
            raise SourceAuthorityError("source_cleanup_unresolved")


def _issued(read: RetainedSourceRead) -> _ReadState:
    state = _READS.get(read) if type(read) is RetainedSourceRead else None
    if state is None or state.pid != os.getpid() or state.phase != "retained":
        raise SourceAuthorityError("original_source_read_required")
    return state


def _abandon(state: _ReadState) -> None:
    try:
        _retire(state, "released")
    except SourceAuthorityError:
        state.cleanup_unresolved = True


def _yielded(reservation: _ReservationState) -> None:
    state = reservation.read
    if state is not None and reservation.active:
        try:
            _retire(state)
        except SourceAuthorityError:
            # The retained state reports unresolved cleanup; a loop callback
            # cannot truthfully return a cleanup receipt to the absent caller.
            state.cleanup_unresolved = True


@final
class SourcePublicationReservation:
    # CPython initializes this special slot, including object.__new__ factories.
    __slots__: tuple[str, ...] = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> Self:
        raise TypeError("Use the original retained source read")

    def __copy__(self) -> SourcePublicationReservation:
        raise TypeError("Source reservations cannot be copied")

    def __deepcopy__(self, memo: object) -> SourcePublicationReservation:
        raise TypeError("Source reservations cannot be copied")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> Never:
        raise TypeError("Source reservations cannot be serialized")

    def require_current(self) -> None:
        reservation = (
            _RESERVATIONS.get(self)
            if type(self) is SourcePublicationReservation
            else None
        )
        if (
            reservation is None
            or not reservation.active
            or reservation.read is None
            or reservation.pid != os.getpid()
            or reservation.thread != threading.get_ident()
            or reservation.task is not _task()
        ):
            raise SourceAuthorityError("original_source_reservation_required")
        state = reservation.read
        with state.lock:
            try:
                _require(state, reservation.fd)
            except BaseException:
                _retire(state)
                raise


@final
class RetainedSourceRead:
    # CPython initializes this special slot, including object.__new__ factories.
    __slots__: tuple[str, ...] = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> Self:
        raise TypeError("Use capture_source_read")

    def __copy__(self) -> RetainedSourceRead:
        raise TypeError("Source custody cannot be copied")

    def __deepcopy__(self, memo: object) -> RetainedSourceRead:
        raise TypeError("Source custody cannot be copied")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> Never:
        raise TypeError("Source custody cannot be serialized")

    @property
    def profile(self) -> str:
        _ = _issued(self)
        return PROFILE

    @property
    def sources(self) -> tuple[SourceSnapshot, ...]:
        state = _issued(self)
        with state.lock:
            return tuple(
                SourceSnapshot(path, body, "sha256:" + hashlib.sha256(body).hexdigest())
                for path, body, _ in state.sources
            )

    def require_current(self) -> None:
        with self.reserve_publication() as reservation:
            reservation.require_current()

    def reserve_publication(
        self,
    ) -> AbstractContextManager[SourcePublicationReservation]:
        return _PublicationContext(self)

    def release(self) -> None:
        state = _READS.get(self) if type(self) is RetainedSourceRead else None
        if state is None or state.pid != os.getpid():
            raise SourceAuthorityError("original_source_read_required")
        with state.lock:
            reservation = state.reservation
            if reservation is not None and (
                reservation.thread != threading.get_ident()
                or reservation.task is not _task()
            ):
                raise SourceAuthorityError("original_source_reservation_required")
            _retire(state, "released")


@final
class _PublicationContext(AbstractContextManager[SourcePublicationReservation]):
    """Check the owner before consuming any public context operation.

    A generator's __exit__ advances/closes it before its finally can reject a
    foreign caller. This context deliberately has no such generator to consume.
    """

    def __init__(self, read: RetainedSourceRead) -> None:
        self._read: RetainedSourceRead | None = read
        self._state: _ReadState | None = None
        self._reservation: _ReservationState | None = None
        self._owner: tuple[int, int, asyncio.Task[object] | None] | None = None
        self._entered = False
        self._exited = False

    def __copy__(self) -> _PublicationContext:
        raise TypeError("Source publication contexts cannot be copied")

    def __deepcopy__(self, memo: object) -> _PublicationContext:
        raise TypeError("Source publication contexts cannot be copied")

    @override
    def __reduce_ex__(self, protocol: SupportsIndex) -> Never:
        raise TypeError("Source publication contexts cannot be serialized")

    @override
    def __enter__(self) -> SourcePublicationReservation:
        _ = super().__enter__()
        read = self._read
        if read is None or self._entered:
            raise SourceAuthorityError("source_reservation_context_consumed")
        state = _issued(read)
        with state.lock:
            if self._entered:
                raise SourceAuthorityError("source_reservation_context_consumed")
            self._entered = True
            if state.reservation is not None:
                raise SourceAuthorityError("source_reservation_already_active")
            self._state = state
            self._owner = (os.getpid(), threading.get_ident(), _task())
            fd = -1
            try:
                fd, _ = _control(state.root_fd, create=False)
                _lock(fd, exclusive=False)
                _require(state, fd)
                reservation = _ReservationState(
                    state, fd, threading.get_ident(), _task()
                )
                token = object.__new__(SourcePublicationReservation)
                _RESERVATIONS[token] = reservation
                state.reservation = reservation
                self._reservation = reservation
                if reservation.task is not None:
                    reservation.checkpoint = asyncio.get_running_loop().call_soon(
                        _yielded, reservation
                    )
                return token
            except BaseException:
                self._exited = True
                self._owner = None
                self._read = None
                # Once registered, retirement owns the descriptor; closing it
                # here as well could close an unrelated reused descriptor.
                if self._reservation is None and state.reservation is None:
                    state.cleanup_unresolved |= not _unlock_close(fd, state.pid)
                _retire(state)
                raise

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        # Crucially, refusal precedes any mutation or generator advancement.
        # Keep this owner independently of the reservation's lifetime: the
        # trusted no-await callback may have already retired the reservation.
        owner = self._owner
        if (
            owner is None
            or owner[0] != os.getpid()
            or owner[1] != threading.get_ident()
            or owner[2] is not _task()
        ):
            raise SourceAuthorityError("original_source_reservation_required")
        state, reservation = self._state, self._reservation
        if self._exited or state is None or reservation is None:
            raise SourceAuthorityError("source_reservation_context_consumed")
        with state.lock:
            self._exited = True
            self._owner = None
            try:
                _end_reservation(reservation)
            except BaseException:
                _retire(state)
                raise
            finally:
                self._read = None
                self._state = None
                self._reservation = None
        return False


def capture_source_read(root: Path, paths: tuple[str, ...]) -> RetainedSourceRead:
    """Capture explicit physical inputs; completeness of domain selection is not inferred."""
    if type(paths) is not tuple or not 1 <= len(paths) <= MAX_SOURCE_FILES:
        raise SourceAuthorityError("source_inventory_invalid")
    for path in paths:
        _ = _path(path)
    if len(set(paths)) != len(paths):
        raise SourceAuthorityError("source_inventory_invalid")
    owned_root = owned_control = -1
    state: _ReadState | None = None
    try:
        with _locked_root(root, exclusive=False, create=False) as (root_fd, fd):
            sources: list[tuple[str, bytes, tuple[int, ...]]] = []
            total = 0
            for path in paths:
                body, identity = _observe(root_fd, path)
                total += len(body)
                if total > MAX_TOTAL_BYTES:
                    raise SourceAuthorityError("source_inventory_limit")
                sources.append((path, body, identity))
            owned_root = os.dup(root_fd)
            owned_control = os.dup(fd)
            state = _ReadState(
                root,
                owned_root,
                owned_control,
                _identity(os.fstat(root_fd)),
                _identity(os.fstat(fd)),
                _epoch(fd),
                tuple(sources),
            )
            _require(state, fd)
        # Do not issue until the temporary capture lock has settled. In
        # particular, a context teardown failure must close retained copies now,
        # not leave their cleanup to an unreturned handle's eventual GC.
        result = object.__new__(RetainedSourceRead)
        _READS[result] = state
        _ = finalize(result, _abandon, state)
        return result
    except BaseException:
        if state is not None:
            _retire(state)
        else:
            control_closed, root_closed = _close(owned_control), _close(owned_root)
            if not control_closed or not root_closed:
                raise SourceAuthorityError("source_cleanup_unresolved") from None
        raise
