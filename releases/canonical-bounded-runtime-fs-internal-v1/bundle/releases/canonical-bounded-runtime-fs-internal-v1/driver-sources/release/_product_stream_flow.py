"""Private original Release feeder/gzip terminal slice,NOT a provider.

No tar/PAX/catalogue,member access,installer or public interface mounting.
Original path/identity/selection policy and original gzip grammar are reused.
Stream bookends are observational,not immutable source custody. No memory fit.
"""

from __future__ import annotations

import gzip
import hashlib
import os
import stat
import threading
from dataclasses import dataclass, field
from weakref import WeakKeyDictionary

from . import whole_envelope as original

WINDOW = 65536
READ_CALLS = 131072
FRAMING_BYTES = 65536
DECODED_MAXIMUM = 640 * 1024**2
_BASE_GZIP = vars(gzip)["_GzipReader"]
COMPACT_HISTORY_PROFILE = "aware.release.compact-flow-history.v1"
_STEP_VIEWS = WeakKeyDictionary()


class StepHistoryCaptureError(RuntimeError):
    def __init__(self, row, count, cause):
        super().__init__("original_flow_step_capture_incomplete")
        self.original_row = row
        self.committed_prefix_count = count
        self.original_cause = cause
        self.authorizes_retry = False


class _StepView:
    """Original-owner historical metadata prefix; never live read authority."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("original_flow_history_owner_required")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("flow_history_subclass_refused")

    def __reduce_ex__(self, protocol):
        raise TypeError("flow_history_serialization_refused")

    def __len__(self):
        return _STEP_VIEWS[self][1]

    def __iter__(self):
        store, count, _, _ = _STEP_VIEWS[self]
        for index in range(count):
            yield store._row(index)

    def __getitem__(self, index):
        store, count, _, _ = _STEP_VIEWS[self]
        if type(index) is not int:
            raise TypeError("original_flow_history_index_required")
        if index < 0:
            index += count
        if not 0 <= index < count:
            raise IndexError(index)
        return store._row(index)


class _StepHistory:
    """Lossless count/digest values, one fixed-width cell per original call."""

    def __init__(self, width):
        if type(width) is not int or width not in (1, 4):
            raise ValueError("original_flow_history_layout_required")
        self.width, self.data = width, bytearray()
        self.head = 0, hashlib.sha256()
        self.failure = None

    def __len__(self):
        return self.head[0]

    def append(self, row):
        try:
            if self.failure is not None or len(self) >= READ_CALLS:
                raise ValueError("original_flow_history_capacity")
            if type(row) is not tuple or len(row) != self.width + 1:
                raise ValueError("original_flow_history_row_required")
            values, digest = row[:-1], row[-1]
            if any(type(n) is not int or not 0 <= n < 2**64 for n in values):
                raise ValueError("bounded_original_flow_history_scalar_required")
            if type(digest) is not str or len(digest) != 64:
                raise ValueError("original_flow_history_digest_required")
            body = bytes.fromhex(digest)
            if body.hex() != digest:
                raise ValueError("canonical_original_flow_history_digest_required")
            cell = b"".join(n.to_bytes(8, "little") for n in values) + body
            updated = self.head[1].copy()
            updated.update(cell)
            self.data.extend(cell)
            # One prefix commit after complete capture. An interrupted tail
            # never becomes an acknowledged occurrence or a retry permission.
            self.head = len(self) + 1, updated
        except BaseException as cause:
            failure = StepHistoryCaptureError(row, len(self), cause)
            if self.failure is None:
                self.failure = failure
            raise failure from cause

    def _row(self, index):
        offset = index * (self.width * 8 + 32)
        return (
            *(
                int.from_bytes(
                    self.data[offset + n * 8 : offset + (n + 1) * 8], "little"
                )
                for n in range(self.width)
            ),
            bytes(
                self.data[offset + self.width * 8 : offset + self.width * 8 + 32]
            ).hex(),
        )

    def snapshot(self):
        value = object.__new__(_StepView)
        _STEP_VIEWS[value] = self, len(self), self.head[1].digest(), self.failure
        return value


def _snapshot_steps(value):
    return value.snapshot() if type(value) is _StepHistory else tuple(value)


def _validate_step_view(value, original) -> _StepHistory:
    if type(value) is not _StepView or value not in _STEP_VIEWS:
        raise ValueError("original_flow_history_view_required")
    store, count, seal, failure = _STEP_VIEWS[value]
    if (
        type(original) is not _StepHistory
        or store is not original
        or count != len(original)
        or failure is not None
        or original.failure is not None
        or len(original.data) != count * (original.width * 8 + 32)
        or hashlib.sha256(original.data).digest() != seal
        or original.head[1].digest() != seal
    ):
        raise ValueError("original_flow_history_prefix_binding_required")
    return original


def _validate_observation_step_history(value, state):
    if value.history_profile != state.history_profile:
        raise ValueError("original_flow_history_profile_mismatch")
    if type(state.decoded_steps) is list and state.history_profile is None:
        return
    if state.history_profile != COMPACT_HISTORY_PROFILE:
        raise ValueError("original_flow_history_profile_required")
    decoded_history = _validate_step_view(value.decoded_steps, state.decoded_steps)
    if (
        decoded_history.width != 1
        or not len(value.decoded_steps)
        or value.decoded_bytes != state.decoded_bytes
        or value.decoded_sha256 != state.decoded_sha256
    ):
        raise ValueError("original_flow_decoded_prefix_required")
    total = 0
    for count, digest in value.decoded_steps:
        if not 0 < count <= WINDOW:
            raise ValueError("original_flow_decoded_step_required")
        total += count
    if (
        total != value.decoded_bytes
        or value.decoded_steps[-1][1] != value.decoded_sha256
    ):
        raise ValueError("original_flow_decoded_total_required")
    for observed, feed in zip(
        (value.prehash, value.decoder_feed, value.posthash), state.feeds, strict=True
    ):
        read_history = _validate_step_view(observed.read_steps, feed.steps)
        if read_history.width != 4 or not len(observed.read_steps):
            raise ValueError("original_flow_read_prefix_required")
        seen = 0
        for index, (start, requested, physical, returned, digest) in enumerate(
            observed.read_steps
        ):
            if (
                start != seen
                or requested <= 0
                or not 0 < physical <= WINDOW
                or not 0 <= returned <= physical
                or (returned == 0) != (index == len(observed.read_steps) - 1)
            ):
                raise ValueError("original_flow_read_step_required")
            seen += returned
        if seen != feed.seen or observed.read_steps[-1][4] != feed.snapshot[1]:
            raise ValueError("original_flow_read_total_required")


@dataclass
class _State:
    phase: str = "selection"
    invocation: str = "not_invoked"
    feeds: list = field(default_factory=list)
    decoder_returns: list = field(default_factory=list)
    decoded_steps: list | _StepHistory = field(default_factory=list)
    decoded_bytes: int = 0
    decoded_sha256: str = field(default_factory=lambda: hashlib.sha256(b"").hexdigest())
    decoder_close_attempted: bool = False
    decoder_close_returned: bool = False
    secondary_causes: list = field(default_factory=list)
    request_snapshot: tuple | None = None
    original_terminal: tuple | None = None
    consumed_bytes: int | None = None
    history_profile: str | None = None

    def __post_init__(self):
        if self.history_profile is not None:
            if self.history_profile != COMPACT_HISTORY_PROFILE:
                raise ValueError("explicit_original_flow_history_profile_required")
            self.decoded_steps = _StepHistory(1)


class ProductFlowError(RuntimeError):
    def __init__(self, request, state, cause):
        super().__init__("private_product_flow_" + state.phase)
        self.original_request = request
        self.request_snapshot = state.request_snapshot
        self.phase = state.phase
        self.invocation = state.invocation
        self.original_source_states = tuple(state.feeds)
        self.original_decoder_returns = tuple(state.decoder_returns)
        self.validated_decoded_prefix = _snapshot_steps(state.decoded_steps)
        self.decoded_bytes = state.decoded_bytes
        self.primary_cause = cause
        self.secondary_causes = tuple(state.secondary_causes)
        self.decoder_close_attempted = state.decoder_close_attempted
        self.decoder_close_returned = state.decoder_close_returned
        self.source_acquisition = (
            "acquired"
            if any(feed.stream is not None for feed in state.feeds)
            else "unknown"
            if any(feed.acquire_attempted for feed in state.feeds)
            else "not_acquired"
        )
        self.original_terminal = state.original_terminal
        self.consumed_bytes = state.consumed_bytes
        self.completion = "incomplete"
        self.cleanup = "not_observed"
        self.raw_capture_complete = False
        self.authorizes_retry = False
        self.authorizes_native_profile = False


@dataclass(frozen=True, slots=True)
class SourceObservation:
    request_snapshot: tuple
    original_file: tuple
    original_returns: tuple[object, ...]
    read_steps: tuple | _StepView
    bytes_seen: int
    bytes_supplied: int
    positive_eof: bool
    close_attempted: bool
    close_returned: bool
    cleanup: str = "not_observed"


@dataclass(frozen=True, slots=True)
class ProductFlowObservation:
    original_request: original.ArchiveBodyRequest
    request_snapshot: tuple
    prehash: SourceObservation
    decoder_feed: SourceObservation
    posthash: SourceObservation
    original_decoder_returns: tuple[object, ...]
    original_terminal: tuple
    decoded_steps: tuple | _StepView
    decoded_bytes: int
    decoded_sha256: str
    consumed_bytes: int
    wrapper_pending_bytes: int
    codec_pending_bytes: int
    gzip_members: int
    decoder_close_attempted: bool
    decoder_close_returned: bool
    cleanup: str = "not_observed"
    catalog_verified: bool = False
    authorizes_native_profile: bool = False
    history_profile: str | None = None


class _SourceFeed:
    """Original-owner readinto extension;no complete raw body retained.

    Shares original policy helpers,not a copied legacy read/body operation.
    The raw original readinto counts/metadata/close returns survive. Emitted
    immutable bytes are bounded transient spans,not old raw read() carriers.
    """

    def __init__(self, request, *, history_profile=None):
        if history_profile is not None and history_profile != COMPACT_HISTORY_PROFILE:
            raise ValueError("explicit_original_source_history_profile_required")
        self.request = self.original_request = request
        self.snapshot = original._guarded_file_snapshot(request)
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.stream = None
        self.acquire_attempted = False
        self.before = self.original_file = None
        self.original_returns = []
        self.steps = _StepHistory(4) if history_profile is not None else []
        self.seen = self.supplied = 0
        self.digest = hashlib.sha256()
        self.source_digest = hashlib.sha256()
        self.eof = self.close_attempted = self.close_returned = False
        self.last_window = None
        self.scratch = bytearray(WINDOW)
        self.reading = False

    def current(self):
        if (
            os.getpid() != self.pid
            or threading.get_ident() != self.thread
            or self.request is not self.original_request
            or original._guarded_file_snapshot(self.request) != self.snapshot
            or self.close_attempted
        ):
            raise ValueError("original_source_lifetime_changed")

    def acquire(self):
        self.current()
        if self.stream is not None:
            raise ValueError("source_already_acquired")
        path = self.snapshot[0]
        resolved = original._path(path)
        self.original_returns.append(resolved)
        if type(resolved) is not type(path) or resolved != path:
            raise ValueError("original_source_path_binding")
        self.before = original._identity(path)
        self.original_returns.append(self.before)
        if (
            type(self.before) is not tuple
            or len(self.before) != 5
            or any(type(part) is not int for part in self.before)
        ):
            raise ValueError("original_source_identity_required")
        regular = path.is_file()
        self.original_returns.append(regular)
        if regular is not True or self.before[2] != self.snapshot[2]:
            raise ValueError("regular_selected_source_required")
        self.acquire_attempted = True
        self.stream = path.open("rb")
        self.original_returns.append(self.stream)  # Custody before fstat/checks.
        value = os.fstat(self.stream.fileno())
        self.original_returns.append(value)
        if (
            type(value) is not os.stat_result
            or not stat.S_ISREG(value.st_mode)
            or (
                value.st_dev,
                value.st_ino,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
            )
            != self.before
        ):
            raise ValueError("original_source_descriptor_mismatch")
        self.current()

    def read(self, requested):
        self.current()
        if type(requested) is not int or requested < 0:
            raise ValueError("positive_bounded_decoder_request_required")
        if requested == 0:
            return b""  # Not a positive EOF observation and no physical call.
        if self.reading or self.stream is None or self.eof:
            if self.eof and not self.reading:
                return b""
            raise ValueError("original_source_read_lifetime")
        amount = min(requested, WINDOW, self.snapshot[2] - self.seen + 1)
        if amount <= 0:
            raise ValueError("original_source_growth")
        self.reading = True
        self.last_window = None
        filled = 0
        try:
            while filled < amount:
                if len(self.steps) >= READ_CALLS:
                    raise ValueError("original_source_read_capacity")
                physical = amount - filled
                with memoryview(self.scratch)[filled:amount] as window:
                    returned = self.stream.readinto(window)
                    self.original_returns.append(returned)
                    self.current()
                    if type(returned) is not int or not 0 <= returned <= physical:
                        raise ValueError("original_bounded_readinto_count")
                    start = self.seen
                    self.seen += returned
                    self.source_digest.update(window[:returned])
                    self.steps.append(
                        (
                            start,
                            requested,
                            physical,
                            returned,
                            self.source_digest.hexdigest(),
                        )
                    )
                    filled += returned
                    if self.seen > self.snapshot[2]:
                        raise ValueError("original_source_growth")
                    if returned == 0:
                        self.eof = True
                        break
            self.last_window = bytes(self.scratch[:filled])
            self.digest.update(self.last_window)
            self.supplied += filled
            return self.last_window
        except BaseException:  # Capture known filled prefix,then preserve cause.
            self.last_window = bytes(self.scratch[:filled]) if filled else None
            raise
        finally:
            self.reading = False

    def finish(self):
        self.current()
        if (
            not self.eof
            or self.seen != self.supplied
            or self.supplied != self.snapshot[2]
            or self.digest.hexdigest() != self.snapshot[1]
            or self.source_digest.hexdigest() != self.digest.hexdigest()
        ):
            raise ValueError("actual_source_feed_digest_or_length_mismatch")
        resolved = original._path(self.snapshot[0])
        self.original_returns.append(resolved)
        if type(resolved) is not type(self.snapshot[0]) or resolved != self.snapshot[0]:
            raise ValueError("original_source_path_binding")
        after = original._identity(self.snapshot[0])
        self.original_returns.append(after)
        if (
            type(after) is not tuple
            or len(after) != 5
            or any(type(part) is not int for part in after)
            or after != self.before
        ):
            raise ValueError("original_source_identity_changed")
        self.current()
        self.original_file = (
            str(self.snapshot[0]),
            self.before,
            self.digest.hexdigest(),
        )
        self.last_window = None

    def close(self):
        # Dispose original custody even if its selected expectations changed.
        if (
            os.getpid() != self.pid
            or threading.get_ident() != self.thread
            or self.close_attempted
        ):
            raise ValueError("original_source_release_lifetime")
        if self.stream is None:
            return
        self.close_attempted = True
        try:
            returned = self.stream.close()
            self.close_returned = True
            self.original_returns.append(returned)
        finally:
            self.scratch = bytearray()

    def observation(self):
        if self.original_file is None or not self.close_returned:
            raise ValueError("original_source_terminal_unavailable")
        return SourceObservation(
            self.snapshot,
            self.original_file,
            tuple(self.original_returns),
            _snapshot_steps(self.steps),
            self.seen,
            self.supplied,
            self.eof,
            self.close_attempted,
            self.close_returned,
        )


class _Cursor:
    """Original gzip padded cursor proxy;no framing parser or source replay."""

    def __init__(self, original_cursor, reader):
        self.original = original_cursor
        self.reader = reader

    def read(self, size):
        framing = self.reader.framing
        if type(size) is not int or not 0 <= size <= 2 * WINDOW:
            raise ValueError("original_gzip_cursor_read_bound")
        if framing and (
            type(size) is not int
            or not 0 <= size <= FRAMING_BYTES - self.reader.framing_bytes
        ):
            raise ValueError("gzip_framing_capacity")
        returned = self.original.read(size)
        if type(returned) is not bytes or len(returned) > size:
            raise TypeError("original_gzip_cursor_bytes_required")
        if framing:
            self.reader.framing_bytes += len(returned)
        return returned

    def prepend(self, body):
        if type(body) is not bytes or len(body) > 2 * WINDOW:
            raise ValueError("original_gzip_prepend_bound")
        returned = self.original.prepend(body)
        self.reader.state.decoder_returns.append(
            ("prepend", len(body), hashlib.sha256(body).hexdigest(), returned)
        )
        return returned

    def seek(self, *_args):
        raise ValueError("gzip_source_seek_refused")


class _Reader(_BASE_GZIP):
    def __init__(self, feed, state):
        super().__init__(feed)
        self._fp = _Cursor(self._fp, self)
        self.state = state
        self.framing = False
        self.framing_bytes = self.members = self.trailers = 0

    def _read_gzip_header(self):
        self.framing = True
        try:
            returned = super()._read_gzip_header()
            self.state.decoder_returns.append(("header", returned))
            if type(returned) is not bool:
                raise TypeError("original_gzip_header_result")
            if returned:
                self.members += 1
                if self.members > 1:
                    raise ValueError("single_gzip_member_required")
            return returned
        finally:
            self.framing = False

    def _read_eof(self):
        self.framing = True
        try:
            returned = super()._read_eof()
            self.state.decoder_returns.append(("trailer", returned))
            self.trailers += 1
            return returned
        finally:
            self.framing = False

    def terminal(self, positive_return, feed):
        # Exact original-instance exhaustion,not decoded tell()/stale buffer len.
        cursor = self._fp.original
        codec = self._decompressor
        evidence = (
            self,
            cursor,
            codec,
            positive_return,
            cursor._read,
            self._new_member,
            codec.needs_input,
            codec.unused_data,
            codec.eof,
            self.members,
            self.trailers,
        )
        self.state.decoder_returns.append(evidence)
        if (
            positive_return != b""
            or not feed.eof
            or cursor.file is not feed
            or cursor._read is not None
            or self._new_member is not True
            or codec.needs_input is not True
            or codec.unused_data != b""
            or codec.eof is not False
            or self.members != 1
            or self.trailers != 1
        ):
            raise ValueError("original_gzip_terminal_unsettled")
        return evidence


def _observe_gzip_flow(request, *, maximum_decoded_bytes):
    """Private source slice,not OriginalProductStreamPort or resource admission."""
    state = _State()
    decoder = None
    primary = None
    terminal = None
    snapshot = pre = scan = post = None
    try:
        snapshot = original._guarded_file_snapshot(request)
        state.request_snapshot = snapshot
        if (
            type(maximum_decoded_bytes) is not int
            or not 0 < maximum_decoded_bytes <= DECODED_MAXIMUM
        ):
            raise ValueError("bounded_decoded_profile_required")
        if vars(gzip)["_GzipReader"] is not _BASE_GZIP:
            raise ValueError("original_gzip_reader_changed")

        def source_phase(label):
            state.phase, state.invocation = label, "not_invoked"
            if original._guarded_file_snapshot(request) != snapshot:
                raise ValueError("original_flow_selection_changed")
            feed = _SourceFeed(request)
            state.feeds.append(feed)
            state.invocation = "unknown"
            feed.acquire()
            return feed

        pre = source_phase("prehash")
        while pre.read(WINDOW):
            pass
        pre.finish()
        pre.close()
        state.invocation = "returned"
        scan = source_phase("decoder_feed")
        if scan.before != pre.before:
            raise ValueError("source_changed_before_decoder")
        decoder = _Reader(scan, state)
        digest = hashlib.sha256()
        state.phase = "decode"
        while True:
            amount = min(WINDOW, maximum_decoded_bytes - state.decoded_bytes + 1)
            returned = decoder.read(amount)
            if type(returned) is not bytes or len(returned) > amount:
                raise ValueError("original_bounded_decoded_return")
            if not returned:
                terminal = decoder.terminal(returned, scan)
                state.original_terminal = terminal
                break
            state.decoded_bytes += len(returned)
            if state.decoded_bytes > maximum_decoded_bytes:
                raise ValueError("decoded_capacity_exceeded")
            digest.update(returned)
            state.decoded_sha256 = digest.hexdigest()
            state.decoded_steps.append((len(returned), state.decoded_sha256))
        state.phase = "feed_final_guard"
        scan.finish()
        if scan.original_file != pre.original_file:
            raise ValueError("source_changed_during_decoder")
        state.consumed_bytes = scan.supplied
        state.phase = "decoder_close"
        state.decoder_close_attempted = True
        closed = decoder.close()
        state.decoder_close_returned = True
        state.decoder_returns.append(("close", closed))
        state.phase = "feed_close"
        scan.close()
        post = source_phase("posthash")
        while post.read(WINDOW):
            pass
        post.finish()
        post.close()
        if post.original_file != pre.original_file:
            raise ValueError("source_changed_after_decoder")
        if original._guarded_file_snapshot(request) != snapshot:
            raise ValueError("original_flow_selection_changed")
        state.phase, state.invocation = "result", "returned"
    except BaseException as cause:  # noqa: BLE001 -- preserve original interruption and settle once
        primary = cause
    finally:
        if decoder is not None and not state.decoder_close_attempted:
            state.decoder_close_attempted = True
            try:
                closed = decoder.close()
                state.decoder_close_returned = True
                state.decoder_returns.append(("close", closed))
            except BaseException as cause:  # noqa: BLE001 -- preserve primary and original close interruption
                if primary is None:
                    primary = cause
                else:
                    state.secondary_causes.append(cause)
        for feed in reversed(state.feeds):
            if feed.stream is not None and not feed.close_attempted:
                try:
                    feed.close()
                except BaseException as cause:  # noqa: BLE001 -- no repeated disposal after any late return
                    if primary is None:
                        primary = cause
                    else:
                        state.secondary_causes.append(cause)
    if primary is not None:
        raise ProductFlowError(request, state, primary) from primary
    if (
        terminal is None
        or snapshot is None
        or pre is None
        or scan is None
        or post is None
        or decoder is None
    ):
        raise ProductFlowError(request, state, RuntimeError("terminal_unavailable"))
    return ProductFlowObservation(
        request,
        snapshot,
        pre.observation(),
        scan.observation(),
        post.observation(),
        tuple(state.decoder_returns),
        terminal,
        _snapshot_steps(state.decoded_steps),
        state.decoded_bytes,
        state.decoded_sha256,
        scan.supplied,
        0,
        0,
        decoder.members,
        state.decoder_close_attempted,
        state.decoder_close_returned,
    )
