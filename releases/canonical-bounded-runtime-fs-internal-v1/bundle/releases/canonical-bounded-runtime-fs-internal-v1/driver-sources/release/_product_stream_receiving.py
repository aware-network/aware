"""Private single-use receiving around the original flow; not a catalog port.

Named source checks are observational bookends, not loaded-code authentication.
No public mounting, parse permission, native authority or memory-fit verdict.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path

from . import _product_stream_flow as flow
from . import whole_envelope as original

_PINS = (
    (
        Path(original.__file__),
        "c5d8d499c18c5fd49110a1247b7f29a2021101bbd7f0b55cfb86e0bbc0ff29da",
    ),
    (
        Path(flow.__file__),
        "f681040c3d931d9ebea0b547bc67b72c5f4ca48374c2645645a2f57d4e26fa12",
    ),
)
_DELEGATE = flow._observe_gzip_flow
_FILE = original._file


class _PreparedFlowHandle:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original_receiver_enrollment_required")


@dataclass
class _Record:
    request: original.ArchiveBodyRequest
    snapshot: tuple
    maximum: int
    state: str = "prepared"
    guards: tuple = ()
    returned: object = None
    error: BaseException | None = None


class ProductReceivingError(RuntimeError):
    def __init__(self, handle, record, phase, invocation, cause, *, request=None):
        super().__init__("private_product_receiving_" + phase)
        self.original_handle = handle
        self.original_request = request if record is None else record.request
        self.request_snapshot = None if record is None else record.snapshot
        self.disposition = "not_enrolled" if record is None else record.state
        self.phase = phase
        self.flow_invocation = invocation
        self.original_guard_returns = () if record is None else record.guards
        self.original_flow_return = None if record is None else record.returned
        self.original_flow_error = None if record is None else record.error
        self.primary_cause = cause
        self.cleanup = "not_observed"
        self.authorizes_retry = False
        self.authorizes_native_profile = False


class _OriginalFlowReceiver:
    """Process/thread-affine logical custody, with no physical resource custody."""

    def __init__(self):
        self._affinity = os.getpid(), threading.get_ident()
        self._records: dict[_PreparedFlowHandle, _Record] = {}
        self._busy = False

    def _check(self):
        if self._affinity != (os.getpid(), threading.get_ident()):
            raise ValueError("original_receiver_affinity_required")
        if self._busy:
            raise ValueError("original_receiver_reentrant")

    def _record(self, handle):
        self._check()
        if type(handle) is not _PreparedFlowHandle or handle not in self._records:
            raise ValueError("original_receiver_handle_required")
        return self._records[handle]

    def prepare(self, request, *, maximum_decoded_bytes):
        try:
            self._check()
            snapshot = original._guarded_file_snapshot(request)
            if (
                type(maximum_decoded_bytes) is not int
                or not 0 < maximum_decoded_bytes <= flow.DECODED_MAXIMUM
                or len(self._records) >= 64
            ):
                raise ValueError("bounded_receiver_capacity_required")
            handle = object.__new__(_PreparedFlowHandle)
            self._records[handle] = _Record(request, snapshot, maximum_decoded_bytes)
            return handle
        except BaseException as cause:
            raise ProductReceivingError(
                None, None, "prepare", "not_invoked", cause, request=request
            ) from cause

    def status(self, handle):
        """Detached status cannot restore a handle or freshness/authority."""
        try:
            record = self._record(handle)
            return record.state, record.snapshot, record.returned, record.error
        except BaseException as cause:
            raise ProductReceivingError(
                handle, None, "status", "not_invoked", cause
            ) from cause

    def retire_prepared(self, handle):
        record = None
        try:
            record = self._record(handle)
            if record.state != "prepared":
                raise ValueError("prepared_receiver_handle_required")
            record.state = "retired"
        except BaseException as cause:
            raise ProductReceivingError(
                handle, record, "retire", "not_invoked", cause
            ) from cause

    def _guards(self, record):
        if (
            flow.original is not original
            or flow._observe_gzip_flow is not _DELEGATE
            or original._file is not _FILE
        ):
            raise ValueError("original_receiving_namespace_changed")
        returned = []
        for path, digest in _PINS:
            value = _FILE(path, digest)
            returned.append(value)
            record.guards += (value,)
        return tuple(returned)

    @staticmethod
    def _terminal(value, record):
        terminal = value.original_terminal
        returns = value.original_decoder_returns
        if (
            type(terminal) is not tuple
            or len(terminal) != 11
            or type(terminal[0]) is not flow._Reader
            or type(returns) is not tuple
            or len(returns) < 5
        ):
            raise ValueError("original_flow_terminal_required")
        reader, cursor, codec = terminal[:3]
        if (
            reader.state.original_terminal is not terminal
            or reader._fp.original is not cursor
            or codec is None
            or terminal[3] != b""
            or type(terminal[3]) is not bytes
            or terminal[4] is not None
            or terminal[5] is not True
            or terminal[6] is not True
            or type(terminal[7]) is not bytes
            or terminal[7] != b""
            or terminal[8] is not False
            or type(terminal[9]) is not int
            or terminal[9] != value.gzip_members
            or type(terminal[10]) is not int
            or terminal[10] != 1
            or len(returns) != len(reader.state.decoder_returns)
            or any(
                a is not b
                for a, b in zip(returns, reader.state.decoder_returns, strict=True)
            )
            or returns[-2] is not terminal
            or type(returns[-1]) is not tuple
            or returns[-1] != ("close", None)
            or reader.state.request_snapshot != record.snapshot
            or reader.state.consumed_bytes != value.consumed_bytes
            or len(reader.state.feeds) != 3
            or cursor.file is not reader.state.feeds[1]
        ):
            raise ValueError("original_flow_terminal_binding_required")
        # Inspect retained original event objects, not a fresh decoder run.
        headers = []
        trailers = closes = 0
        for event in returns:
            if event is terminal:
                continue
            if type(event) is not tuple or not event:
                raise ValueError("original_flow_decoder_event_required")
            if event[0] == "header" and len(event) == 2 and type(event[1]) is bool:
                headers.append(event[1])
            elif event == ("trailer", None):
                trailers += 1
            elif event == ("close", None):
                closes += 1
            elif event[0] == "prepend" and len(event) == 4:
                if type(event[1]) is not int or not 0 <= event[1] <= 2 * flow.WINDOW:
                    raise ValueError("original_flow_prepend_binding_required")
            else:
                raise ValueError("original_flow_decoder_event_required")
        if headers != [True, False] or trailers != 1 or closes != 1:
            raise ValueError("original_flow_decoder_history_required")
        return reader.state.feeds

    @staticmethod
    def _correlate(record):
        value = record.returned
        if (
            type(value) is not flow.ProductFlowObservation
            or value.original_request is not record.request
            or value.request_snapshot != record.snapshot
            or original._guarded_file_snapshot(record.request) != record.snapshot
            or type(value.decoded_bytes) is not int
            or not 0 <= value.decoded_bytes <= record.maximum
            or type(value.consumed_bytes) is not int
            or value.consumed_bytes != record.snapshot[2]
            or type(value.wrapper_pending_bytes) is not int
            or value.wrapper_pending_bytes != 0
            or type(value.codec_pending_bytes) is not int
            or value.codec_pending_bytes != 0
            or type(value.gzip_members) is not int
            or value.gzip_members != 1
            or value.decoder_close_attempted is not True
            or value.decoder_close_returned is not True
            or value.catalog_verified is not False
            or value.authorizes_native_profile is not False
            or value.cleanup != "not_observed"
        ):
            raise ValueError("original_flow_return_binding_required")
        feeds = _OriginalFlowReceiver._terminal(value, record)
        flow._validate_observation_step_history(value, value.original_terminal[0].state)
        for source, feed in zip(
            (value.prehash, value.decoder_feed, value.posthash), feeds, strict=True
        ):
            if (
                type(source) is not flow.SourceObservation
                or source.request_snapshot != record.snapshot
                or type(source.original_file) is not tuple
                or len(source.original_file) != 3
                or source.original_file[0] != str(record.snapshot[0])
                or type(source.original_file[1]) is not tuple
                or len(source.original_file[1]) != 5
                or any(type(part) is not int for part in source.original_file[1])
                or source.original_file[1][2] != record.snapshot[2]
                or source.original_file[2] != record.snapshot[1]
                or type(source.original_returns) is not tuple
                or len(source.original_returns) < 8
                or source.original_returns[1] is not source.original_file[1]
                or source.original_returns[-2] != source.original_file[1]
                or feed.original_request is not record.request
                or feed.snapshot != record.snapshot
                or feed.original_file != source.original_file
                or len(feed.original_returns) != len(source.original_returns)
                or any(
                    a is not b
                    for a, b in zip(
                        source.original_returns, feed.original_returns, strict=True
                    )
                )
                or type(source.bytes_seen) is not int
                or source.bytes_seen != value.consumed_bytes
                or type(source.bytes_supplied) is not int
                or source.bytes_supplied != value.consumed_bytes
                or source.positive_eof is not True
                or source.close_attempted is not True
                or source.close_returned is not True
                or source.cleanup != "not_observed"
                or source.original_file != value.prehash.original_file
            ):
                raise ValueError("original_flow_source_binding_required")

    @staticmethod
    def _invoke(record):
        return _DELEGATE(record.request, maximum_decoded_bytes=record.maximum)

    def observe(self, handle):
        record = None
        phase, invocation = "handle", "not_invoked"
        owns_busy = False
        try:
            record = self._record(handle)
            if record.state != "prepared":
                raise ValueError("prepared_receiver_handle_required")
            if original._guarded_file_snapshot(record.request) != record.snapshot:
                raise ValueError("original_receiving_selection_changed")
            record.state = "spent"
            self._busy = owns_busy = True
            phase = "source_before"
            before = self._guards(record)
            phase, invocation = "original_flow", "unknown"
            try:
                record.returned = self._invoke(record)
            except BaseException as cause:
                record.error = cause
                raise
            invocation = "returned"
            phase = "correlation"
            self._correlate(record)
            phase = "source_after"
            after = self._guards(record)
            if before != after:
                raise ValueError("original_receiving_source_changed")
            return record.returned
        except BaseException as cause:
            raise ProductReceivingError(
                handle, record, phase, invocation, cause
            ) from cause
        finally:
            if owns_busy:
                self._busy = False
