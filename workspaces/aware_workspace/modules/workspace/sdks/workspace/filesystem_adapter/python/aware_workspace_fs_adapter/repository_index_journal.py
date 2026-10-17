"""Private versioned representation of freshly serialized repository indexes.

This layer supplies no mutation authority. Its inputs are the original owner's
complete canonical bytes; replay feeds those bytes to that owner's validators.
The writer is the retained original metadata atomic writer, not a tree writer.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import struct
import threading
import types
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_MAGIC = b"AWRIDX2\n"
_ZERO = bytes(32)
_U64 = struct.Struct(">Q")
_DELTA_MAGIC = b"RDX1"
_DELTA_LIMIT = 32 * 1024 * 1024


class IndexJournalError(ValueError):
    """Invalid representation, stale writer, or terminal local publication."""


@dataclass(frozen=True, slots=True)
class IndexPublicationEvidence:
    sequence: int
    publication: str
    cleanup: str
    phase: str


class DeferredIndexBytes:
    """Private exact original producer, checked before and after dispatch."""

    __slots__ = (
        "_cells",
        "_code",
        "_defaults",
        "_function",
        "_keywords",
        "_spent",
        "_values",
    )

    def __init__(self, function):
        if type(function) is not types.FunctionType:
            raise TypeError("Original index preparation function required")
        self._function = function
        self._code = function.__code__
        self._defaults = function.__defaults__
        keywords = function.__kwdefaults__
        if keywords is not None and type(keywords) is not dict:
            raise IndexJournalError("Original index preparation keywords required")
        self._keywords = tuple((keywords or {}).items())
        self._cells = function.__closure__
        self._values = tuple(cell.cell_contents for cell in (self._cells or ()))
        self._spent = False

    def read(self) -> bytes:
        function = self._function

        def check(*, before):
            if (
                type(function) is not types.FunctionType
                or function.__code__ is not self._code
                or function.__defaults__ is not self._defaults
                or (
                    function.__kwdefaults__ is not None
                    and type(function.__kwdefaults__) is not dict
                )
                or len(function.__kwdefaults__ or {}) != len(self._keywords)
                or any(
                    (function.__kwdefaults__ or {}).get(key) is not value
                    for key, value in self._keywords
                )
                or function.__closure__ is not self._cells
                or (
                    before
                    and any(
                        cell.cell_contents is not value
                        for cell, value in zip(
                            self._cells or (), self._values, strict=True
                        )
                    )
                )
            ):
                raise IndexJournalError("Original index preparation was substituted")

        if self._spent:
            raise IndexJournalError("Original index preparation already spent")
        self._spent = True
        try:
            if type(function) is not types.FunctionType:
                raise IndexJournalError("Original index preparation is unavailable")
            check(before=True)
            result = function()
            # Original preparation changes its output cells. Code, defaults and
            # closure-tuple identity remain authenticated after that execution.
            check(before=False)
            if type(result) is not bytes:
                raise TypeError("Original index preparation must return exact bytes")
            return result
        finally:
            self._function = self._defaults = None
            self._keywords = self._values = ()
            self._cells = None
            function = None


@dataclass(frozen=True, slots=True)
class _Frame:
    sequence: int
    mode: int
    previous: bytes
    result_length: int
    data: bytes
    digest: bytes


def _uint(value: int) -> bytes:
    encoded = value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")
    return _U64.pack(len(encoded)) + encoded


def _frame(
    kind: int,
    sequence: int,
    binding: bytes,
    mode: int,
    previous: bytes,
    result_length: int,
    data: bytes,
) -> bytes:
    header = b"".join(
        (
            _MAGIC,
            bytes((kind, mode)),
            _uint(sequence),
            _U64.pack(len(binding)),
            binding,
            previous,
            _U64.pack(result_length),
            _U64.pack(len(data)),
        )
    )
    digest = hashlib.sha256(header)
    digest.update(data)
    return b"".join((header, data, digest.digest()))


def _parse(encoded: bytes, *, kind: int, binding: bytes) -> _Frame:
    if type(encoded) is not bytes or len(encoded) < 107:
        raise IndexJournalError("Truncated repository index transaction")
    if encoded[:8] != _MAGIC or encoded[8] != kind or encoded[9] not in (0, 1):
        raise IndexJournalError("Repository index transaction identity differs")
    digest = hashlib.sha256(memoryview(encoded)[:-32]).digest()
    if encoded[-32:] != digest:
        raise IndexJournalError("Repository index transaction digest differs")
    offset = 10

    def take_size() -> int:
        nonlocal offset
        if offset + 8 > len(encoded) - 32:
            raise IndexJournalError("Truncated repository index field")
        value = _U64.unpack_from(encoded, offset)[0]
        offset += 8
        return value

    sequence_size = take_size()
    if not 1 <= sequence_size <= len(encoded) - 32 - offset:
        raise IndexJournalError("Repository index sequence length differs")
    raw_sequence = encoded[offset : offset + sequence_size]
    offset += sequence_size
    if len(raw_sequence) > 1 and raw_sequence[0] == 0:
        raise IndexJournalError("Repository index sequence is not minimal")
    sequence = int.from_bytes(raw_sequence, "big")
    if sequence == 0:
        raise IndexJournalError("Repository index sequence must be positive")
    binding_size = take_size()
    if (
        binding_size != len(binding)
        or encoded[offset : offset + binding_size] != binding
    ):
        raise IndexJournalError("Repository index binding differs")
    offset += binding_size
    if offset + 48 > len(encoded) - 32:
        raise IndexJournalError("Truncated repository index commitment")
    previous = encoded[offset : offset + 32]
    offset += 32
    result_length, data_length = take_size(), take_size()
    if offset + data_length != len(encoded) - 32:
        raise IndexJournalError("Repository index payload length differs")
    data = encoded[offset : offset + data_length]
    mode = encoded[9]
    if mode == 0 and len(data) != result_length:
        raise IndexJournalError("Repository index FULL length differs")
    if mode == 1 and result_length > _DELTA_LIMIT:
        raise IndexJournalError("Repository index DELTA length exceeds codec limit")
    if (sequence == 1) != (previous == _ZERO) or (sequence == 1 and mode != 0):
        raise IndexJournalError("Repository index initial commitment differs")
    return _Frame(sequence, mode, previous, result_length, data, digest)


def _apply_delta(previous: bytes, program: bytes, result_length: int) -> bytes:
    """Bounded exact-byte reference decoder; no JSON semantics or callbacks."""
    if (
        type(previous) is not bytes
        or type(program) is not bytes
        or type(result_length) is not int
        or not 0 <= result_length <= _DELTA_LIMIT
        or len(previous) > _DELTA_LIMIT
        or len(program) < 16
        or program[:4] != _DELTA_MAGIC
        or _U64.unpack_from(program, 4)[0] != result_length
    ):
        raise IndexJournalError("Invalid repository index DELTA program")
    count = struct.unpack_from(">I", program, 12)[0]
    # Every command requires at least nine bytes. Reject impossible counts
    # before allocating or iterating attacker-selected output quantities.
    if count > (len(program) - 16) // 9:
        raise IndexJournalError("Repository index DELTA command count differs")
    offset, size = 16, 0
    parts: list[bytes] = []
    for _ in range(count):
        if offset + 9 > len(program):
            raise IndexJournalError("Truncated repository index DELTA command")
        operation = program[offset]
        length = _U64.unpack_from(program, offset + 1)[0]
        offset += 9
        if length == 0 or size + length > result_length:
            raise IndexJournalError("Repository index DELTA expansion differs")
        if operation == 0:
            if offset + length > len(program):
                raise IndexJournalError("Truncated repository index DELTA literal")
            part = program[offset : offset + length]
            offset += length
        elif operation == 1:
            if offset + 8 > len(program):
                raise IndexJournalError("Truncated repository index DELTA copy")
            start = _U64.unpack_from(program, offset)[0]
            offset += 8
            if start + length > len(previous):
                raise IndexJournalError("Repository index DELTA copy exceeds source")
            part = previous[start : start + length]
        else:
            raise IndexJournalError("Unknown repository index DELTA command")
        parts.append(part)
        size += length
    if offset != len(program) or size != result_length:
        raise IndexJournalError("Repository index DELTA output length differs")
    return b"".join(parts)


class IndexJournal:
    """Per-owner index representation, with a terminal local writer on failure.

    Construction and read are observation-only. A v2 directory without a
    committed transaction is corrupt, not typed-empty genesis. Writer exclusion
    is acquired only for a publication and is shared by updated v1/v2 writers.
    No protection against unmodified legacy binaries or rollback is claimed.
    """

    def __init__(self, index: Path, *, binding: str, kind: int, index_format: str):
        if type(index_format) is not str or index_format not in (
            "json_v1",
            "events_v2",
            "auto",
        ):
            raise ValueError("Unknown repository index format")
        if type(binding) is not str or type(kind) is not int or kind not in (1, 2):
            raise ValueError("Invalid repository index identity")
        self.index = index
        self.directory = index.with_name("index.events-v2")
        self.binding = binding.encode("utf-8", "surrogatepass")
        self.kind = kind
        self.pid = os.getpid()
        self._lock = threading.RLock()
        self._writing = False
        self._held = False
        self._sequence = 0
        self._digest = _ZERO
        self._content: bytes | None = None
        self._segments: tuple[tuple[Path, int, bytes], ...] = ()
        self.failure_evidence: IndexPublicationEvidence | None = None
        legacy, journal = self.index.exists(), self.directory.exists()
        if legacy and journal:
            raise IndexJournalError("Mixed repository index formats")
        if index_format == "events_v2" and legacy:
            raise IndexJournalError("Repository index migration is not admitted")
        self.format = (
            "events_v2"
            if journal
            else ("json_v1" if legacy or index_format == "json_v1" else "events_v2")
        )
        if self.format == "events_v2" and journal:
            self._load()

    def read(self) -> bytes | None:
        if os.getpid() != self.pid:
            raise IndexJournalError("Inherited repository index reader")
        return self._content

    def _paths(self) -> tuple[tuple[int, Path], ...]:
        if not self.directory.exists():
            return ()
        if not self.directory.is_dir() or self.directory.is_symlink():
            raise IndexJournalError("Invalid repository index directory")
        paths = []
        for path in self.directory.iterdir():
            if path.name.startswith(".pending-"):
                # Unpublished temporaries grant no history or renewed custody.
                continue
            name = path.name.removesuffix(".txn")
            if (
                not path.name.endswith(".txn")
                or not name.isascii()
                or not name.isdigit()
            ):
                raise IndexJournalError("Unknown repository index fragment")
            sequence = int(name)
            if sequence < 1 or path.name != f"{sequence:020d}.txn":
                raise IndexJournalError("Noncanonical repository index fragment")
            if path.is_symlink() or not path.is_file():
                raise IndexJournalError("Invalid repository index fragment")
            paths.append((sequence, path))
        return tuple(sorted(paths))

    def _load(self) -> None:
        paths = self._paths()
        if not paths:
            raise IndexJournalError("Repository v2 index has no committed checkpoint")
        suffix = []
        for sequence, path in reversed(paths):
            encoded = path.read_bytes()
            frame = _parse(encoded, kind=self.kind, binding=self.binding)
            if frame.sequence != sequence:
                raise IndexJournalError("Repository index filename sequence differs")
            suffix.append((path, len(encoded), frame))
            if frame.mode == 0:
                break
        suffix.reverse()
        first = suffix[0][2]
        if first.mode != 0:
            raise IndexJournalError("Repository index checkpoint is absent")
        content, previous, sequence = first.data, first.digest, first.sequence
        for _, _, frame in suffix[1:]:
            if frame.sequence != sequence + 1 or frame.previous != previous:
                raise IndexJournalError("Repository index suffix is discontinuous")
            content = _apply_delta(content, frame.data, frame.result_length)
            previous, sequence = frame.digest, frame.sequence
        self._content, self._digest, self._sequence = content, previous, sequence
        self._segments = tuple(
            (path, size, frame.digest) for path, size, frame in suffix
        )
        # Replay ignores obsolete frames semantically, not physical cleanup debt.
        obsolete = any(number < first.sequence for number, _ in paths)
        pending = any(
            path.name.startswith(".pending-") for path in self.directory.iterdir()
        )
        if obsolete or pending:
            self._held = True
            self.failure_evidence = IndexPublicationEvidence(
                sequence, "committed", "unknown", "restart_cleanup_debt"
            )

    def _check_tip(self) -> None:
        legacy, journal = self.index.exists(), self.directory.exists()
        if self.format == "json_v1":
            if journal:
                raise IndexJournalError("Mixed repository index writer formats")
            return
        if legacy:
            raise IndexJournalError("Mixed repository index writer formats")
        paths = self._paths()
        if self._sequence == 0:
            if journal:
                raise IndexJournalError("Repository index changed before initial write")
            return
        if not paths or paths[-1][0] != self._sequence:
            raise IndexJournalError("Repository index writer is stale")
        # Every fragment still required by restart must remain authenticated.
        # The in-memory canonical data is descriptive; it cannot manufacture a
        # physical predecessor if a committed checkpoint/suffix disappeared.
        for path, size, digest in self._segments:
            encoded = path.read_bytes()
            if (
                len(encoded) != size
                or encoded[-32:] != digest
                or hashlib.sha256(memoryview(encoded)[:-32]).digest() != digest
            ):
                raise IndexJournalError("Repository index committed fragment changed")
        if self._segments[-1][2] != self._digest:
            raise IndexJournalError("Repository index tip changed")

    @contextmanager
    def publication_guard(self) -> Iterator[None]:
        # Refuse before acquiring an inherited lock, even while another parent
        # thread held it at fork. flock is nonblocking so reentry via another
        # store instance cannot deadlock the owning thread.
        if os.getpid() != self.pid:
            raise IndexJournalError("Inherited repository index writer")
        with self._lock:
            if self._held or self._writing:
                raise IndexJournalError("Repository index writer is terminal or active")
            self._writing = True
            entry_sequence = self._sequence
            descriptor = None
            primary = None
            try:
                self.index.parent.parent.mkdir(parents=True, exist_ok=True)
                lock = (
                    self.index.parent.parent / f".{self.index.parent.name}.index.lock"
                )
                descriptor = os.open(
                    lock, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600
                )
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._check_tip()
                yield
            except BaseException as error:
                primary = error
                self._held = True
                raise
            finally:
                if descriptor is not None:
                    # Spend before dispatch; a lost close return is never retried.
                    closing, descriptor = descriptor, None
                    try:
                        os.close(closing)
                    except BaseException as cleanup_error:
                        self._held = True
                        prior = self.failure_evidence
                        self.failure_evidence = IndexPublicationEvidence(
                            prior.sequence if prior else self._sequence,
                            prior.publication
                            if prior
                            else (
                                "committed"
                                if self._sequence > entry_sequence
                                else "unchanged_or_committed"
                            ),
                            "unknown",
                            "lock_close",
                        )
                        if primary is None:
                            raise
                        primary.add_note(
                            f"Index lock cleanup uncertain: {cleanup_error!r}"
                        )
                    finally:
                        self._writing = False
                else:
                    self._writing = False
                primary = None

    def publish(
        self,
        content: bytes | Callable[[], bytes],
        *,
        writer: Callable[[Path, Callable[[], bytes]], None],
        delta: Callable[[bytes, bytes], bytes | None] | None = None,
    ) -> None:
        if delta is None:
            native_delta: Any = "_ORIGINAL_NATIVE_INDEX_DELTA_"
            delta = native_delta
        if self.format != "events_v2":
            raise IndexJournalError("Repository index is not a v2 writer")
        if type(writer) is not types.FunctionType:
            raise TypeError("Original repository index writer required")
        writer_code, writer_defaults = writer.__code__, writer.__defaults__
        writer_keywords = writer.__kwdefaults__
        if writer_keywords is not None and type(writer_keywords) is not dict:
            raise IndexJournalError("Original index writer keywords required")
        writer_keyword_items = tuple((writer_keywords or {}).items())
        writer_cells = writer.__closure__
        writer_values = tuple(cell.cell_contents for cell in (writer_cells or ()))
        if type(content) is not bytes and type(content) is not types.FunctionType:
            raise TypeError("Original repository index bytes or producer required")
        producer = content if type(content) is types.FunctionType else None
        producer_code = producer.__code__ if producer else None
        producer_defaults = producer.__defaults__ if producer else None
        producer_keywords = producer.__kwdefaults__ if producer else None
        if producer_keywords is not None and type(producer_keywords) is not dict:
            raise IndexJournalError("Original canonical producer keywords required")
        producer_keyword_items = tuple((producer_keywords or {}).items())
        producer_cells = producer.__closure__ if producer else None
        producer_values = tuple(cell.cell_contents for cell in (producer_cells or ()))
        with self.publication_guard():
            sequence = self._sequence + 1
            path = self.directory / f"{sequence:020d}.txn"
            encoded: bytes | None = None
            fresh: bytes | None = None
            mode = 0
            phase = "pending_or_encoding"

            def prepare() -> bytes:
                nonlocal encoded, fresh, mode
                if producer is not None:
                    if (
                        producer.__code__ is not producer_code
                        or producer.__defaults__ is not producer_defaults
                        or producer.__kwdefaults__ is not producer_keywords
                        or (
                            producer_keywords is not None
                            and (
                                dict.__len__(producer_keywords)
                                != len(producer_keyword_items)
                                or any(
                                    dict.get(producer_keywords, key) is not value
                                    for key, value in producer_keyword_items
                                )
                            )
                        )
                        or producer.__closure__ is not producer_cells
                        or any(
                            cell.cell_contents is not value
                            for cell, value in zip(
                                producer_cells or (), producer_values, strict=True
                            )
                        )
                    ):
                        raise IndexJournalError(
                            "Original canonical producer was substituted"
                        )
                    fresh = producer()
                else:
                    exact_content: Any = content
                    fresh = exact_content
                if type(fresh) is not bytes:
                    raise TypeError(
                        "Original canonical repository index bytes required"
                    )
                # The framing overhead is independent of data bytes. Do not
                # allocate a full historical copy merely to choose a delta.
                full_size = len(
                    _frame(
                        self.kind,
                        sequence,
                        self.binding,
                        0,
                        self._digest,
                        len(fresh),
                        b"",
                    )
                ) + len(fresh)
                if (
                    self._content is not None
                    and delta is not None
                    and len(self._content) <= _DELTA_LIMIT
                    and len(fresh) <= _DELTA_LIMIT
                    # Checkpoint complete history before required-fragment
                    # authentication could grow with lifetime publications.
                    and len(self._segments) < 16
                ):
                    program = delta(self._content, fresh)
                    if program is not None:
                        if type(program) is not bytes:
                            raise TypeError(
                                "Repository index delta must be exact bytes"
                            )
                        if _apply_delta(self._content, program, len(fresh)) != fresh:
                            raise IndexJournalError(
                                "Repository index delta differs from fresh bytes"
                            )
                        candidate = _frame(
                            self.kind,
                            sequence,
                            self.binding,
                            1,
                            self._digest,
                            len(fresh),
                            program,
                        )
                        if len(candidate) < full_size and (
                            sum(size for _, size, _ in self._segments) + len(candidate)
                            <= 2 * full_size
                        ):
                            encoded, mode = candidate, 1
                if encoded is None:
                    encoded = _frame(
                        self.kind,
                        sequence,
                        self.binding,
                        0,
                        self._digest,
                        len(fresh),
                        fresh,
                    )
                return encoded

            try:
                # Transaction fragments are private operational metadata.
                self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
                if (
                    writer.__code__ is not writer_code
                    or writer.__defaults__ is not writer_defaults
                    or writer.__kwdefaults__ is not writer_keywords
                    or (
                        writer_keywords is not None
                        and (
                            dict.__len__(writer_keywords) != len(writer_keyword_items)
                            or any(
                                dict.get(writer_keywords, key) is not value
                                for key, value in writer_keyword_items
                            )
                        )
                    )
                    or writer.__closure__ is not writer_cells
                    or any(
                        cell.cell_contents is not value
                        for cell, value in zip(
                            writer_cells or (), writer_values, strict=True
                        )
                    )
                ):
                    raise IndexJournalError(
                        "Original index writer entry was substituted"
                    )
                writer(path, prepare)
                if (
                    writer.__code__ is not writer_code
                    or writer.__defaults__ is not writer_defaults
                    or writer.__kwdefaults__ is not writer_keywords
                    or (
                        writer_keywords is not None
                        and (
                            dict.__len__(writer_keywords) != len(writer_keyword_items)
                            or any(
                                dict.get(writer_keywords, key) is not value
                                for key, value in writer_keyword_items
                            )
                        )
                    )
                    or writer.__closure__ is not writer_cells
                    or any(
                        cell.cell_contents is not value
                        for cell, value in zip(
                            writer_cells or (), writer_values, strict=True
                        )
                    )
                ):
                    raise IndexJournalError(
                        "Original index writer entry was substituted"
                    )
                if encoded is None or fresh is None:
                    raise IndexJournalError(
                        "Repository index writer omitted original preparation"
                    )
                phase = "directory_sync"
                # Publication is known before sync/reclamation. A sync error
                # must not erase it or turn this local writer back into a retry.
                self._sequence = sequence
                self._digest = encoded[-32:]
                self._content = fresh
                old_segments = self._segments
                self._segments = old_segments + ((path, len(encoded), encoded[-32:]),)
                descriptor = os.open(
                    self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
                )
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                if mode == 0:
                    phase = "obsolete_cleanup"
                    # Include old fragments left by an interrupted checkpoint
                    # cleanup; no enclosing proof directory is ever traversed.
                    for old_sequence, old_path in self._paths():
                        if old_sequence < sequence:
                            old_path.unlink()
                    self._segments = ((path, len(encoded), encoded[-32:]),)
            except BaseException:
                publication = "unknown"
                try:
                    if not path.exists():
                        publication = "not_written"
                    elif encoded is not None and path.read_bytes() == encoded:
                        publication = "committed"
                except BaseException:  # noqa: BLE001 -- retain original failure; unknown evidence is explicit
                    publication = "unknown"
                self.failure_evidence = IndexPublicationEvidence(
                    sequence, publication, "unknown", phase
                )
                self._held = True
                raise
            finally:
                # Do not retain a producer/owner through a held traceback's
                # Workspace-owned frame after publication has failed.
                content = None  # type: ignore[assignment]
                producer = None
                producer_values = ()
                producer_cells = writer_cells = None
                writer_values = ()
                fresh = encoded = None
                delta = writer = None  # type: ignore[assignment]


def bind_deferred_reader():
    """Retain this original receiver; mutable class dispatch cannot select it."""
    owner = DeferredIndexBytes
    reader = vars(owner)["read"]
    code = reader.__code__
    initializer = vars(owner)["__init__"]
    initializer_code = initializer.__code__
    slots = tuple((name, vars(owner)[name]) for name in owner.__slots__)

    def verify():
        if (
            vars(owner).get("read") is not reader
            or reader.__code__ is not code
            or vars(owner).get("__init__") is not initializer
            or initializer.__code__ is not initializer_code
            or any(vars(owner).get(name) is not value for name, value in slots)
        ):
            raise IndexJournalError("Original deferred index reader was substituted")

    verify_code = verify.__code__
    verify_cells = tuple(cell.cell_contents for cell in (verify.__closure__ or ()))

    def read(value):
        if (
            verify.__code__ is not verify_code
            or verify.__defaults__ is not None
            or verify.__kwdefaults__ is not None
            or any(
                cell.cell_contents is not expected
                for cell, expected in zip(
                    verify.__closure__ or (), verify_cells, strict=True
                )
            )
        ):
            raise IndexJournalError("Original deferred verification was substituted")
        verify()
        if type(value) is not owner:
            raise TypeError("Original deferred index bytes required")
        result = reader(value)
        if (
            verify.__code__ is not verify_code
            or verify.__defaults__ is not None
            or verify.__kwdefaults__ is not None
            or any(
                cell.cell_contents is not expected
                for cell, expected in zip(
                    verify.__closure__ or (), verify_cells, strict=True
                )
            )
        ):
            raise IndexJournalError("Original deferred verification was substituted")
        verify()
        return result

    # This is descriptive dispatch identity, never a cached owner verdict. The
    # caller checks these immutable specifications in its own original frame
    # immediately before invoking this mutable Python function object.
    specifications = []
    seen = set()

    def capture(function):
        if id(function) in seen:
            return
        seen.add(id(function))
        cells = function.__closure__
        values = tuple(cell.cell_contents for cell in (cells or ()))
        specifications.append(
            (
                function,
                function.__code__,
                function.__defaults__,
                tuple((function.__kwdefaults__ or {}).items()),
                cells,
                values,
            )
        )
        for value in values:
            if type(value) is types.FunctionType:
                capture(value)

    capture(read)
    return owner, read, tuple(specifications)


def bind_index_writer(original_write):
    """Capture the original metadata writer and constructor before owner use."""
    if type(original_write) is not types.FunctionType:
        raise TypeError("Original metadata atomic writer required")
    owner = DeferredIndexBytes
    initializer = vars(owner)["__init__"]
    initializer_code = initializer.__code__
    write_code = original_write.__code__
    write_defaults = original_write.__defaults__
    write_keywords = tuple((original_write.__kwdefaults__ or {}).items())

    def write(path, prepare):
        if (
            original_write.__code__ is not write_code
            or original_write.__defaults__ is not write_defaults
            or (
                original_write.__kwdefaults__ is not None
                and type(original_write.__kwdefaults__) is not dict
            )
            or len(original_write.__kwdefaults__ or {}) != len(write_keywords)
            or any(
                (original_write.__kwdefaults__ or {}).get(key) is not value
                for key, value in write_keywords
            )
            or vars(owner).get("__init__") is not initializer
            or initializer.__code__ is not initializer_code
        ):
            raise IndexJournalError("Original metadata writer was substituted")
        deferred = object.__new__(owner)
        initializer(deferred, prepare)
        result = original_write(path, deferred)
        if (
            original_write.__code__ is not write_code
            or original_write.__defaults__ is not write_defaults
            or original_write.__kwdefaults__ is not None
        ):
            raise IndexJournalError(
                "Original metadata writer changed during publication"
            )
        return result

    # Installed into the receiving method's code constants; identity/code are
    # checked there, not inside another unguarded callable wrapper.
    return (
        write,
        write.__code__,
        write.__closure__,
        tuple(cell.cell_contents for cell in (write.__closure__ or ())),
    )


# Bind once before the original owners retain this class/entry. No mutable
# module export lookup can choose the native callback during publication.
try:
    from aware_workspace_sdk._tree_native_binding import prepare_index_delta
except ImportError:
    _native_delta = None
else:
    _native_delta = prepare_index_delta()
_publish_original = IndexJournal.publish
IndexJournal.publish = types.FunctionType(
    _publish_original.__code__.replace(
        co_consts=tuple(
            _native_delta
            if type(value) is str and value == "_ORIGINAL_NATIVE_INDEX_DELTA_"
            else value
            for value in _publish_original.__code__.co_consts
        )
    ),
    _publish_original.__globals__,
    _publish_original.__name__,
    _publish_original.__defaults__,
    _publish_original.__closure__,
)
IndexJournal.publish.__kwdefaults__ = _publish_original.__kwdefaults__
IndexJournal.publish.__annotations__ = _publish_original.__annotations__
IndexJournal.publish.__qualname__ = _publish_original.__qualname__
