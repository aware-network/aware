"""Private bounded body sink over the unchanged original member reader.

All returned chunks are provisional. Enclosing flow, final guards, cumulative
root budgets and receiving custody are deliberately not established here.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from . import _product_stream_catalog as original

SMALL_BYTES = 2097152
_READ = original._read_member


@dataclass(frozen=True)
class ProvisionalMemberCapture:
    original_pin: tuple
    original_chunks: tuple[bytes, ...]
    original_digest_return: str
    original_eof: tuple
    original_close_return: tuple
    original_state: original._State
    provisional: bool = True
    enclosing_flow_verified: bool = False
    final_guards_verified: bool = False
    authorizes_native_profile: bool = False
    cleanup: str = "not_observed"


class MemberCaptureError(RuntimeError):
    def __init__(self, pin, state, sink, cause, invocation, returned):
        super().__init__("private_selected_member_capture")
        self.original_pin = pin
        self.original_state = state
        self.original_digest_return = returned
        self.original_eof = None if sink is None else sink.eof
        self.captured_bytes = 0 if sink is None else sink.total
        self.captured_bytes_complete = False  # Validated prefix, not full raw history.
        self.newly_captured_window = None if sink is None else sink.last_positive
        self.raw_history_available = False
        self.invocation = invocation
        self.primary_cause = cause
        self.secondary_causes = (
            tuple(state.secondary_causes) if type(state) is original._State else ()
        )
        self.authorizes_retry = False
        self.authorizes_native_profile = False
        self.cleanup = "not_observed"


class _SelectedSink:
    def __init__(self, state, item, pin, checksum):
        self.state, self.item, self.pin, self.checksum = state, item, pin, checksum
        self.snapshot = original._snapshot(item)
        self.parts: list[bytes] = []
        self.total = 0
        self.eof = None
        self.last_positive = None

    def feed(self, body):
        if (
            type(body) is not bytes
            or not 0 < len(body) <= original.WINDOW
            or self.state.last_return is not body
            or self.state.original_read_return is not body
            or self.state.member_bytes != self.total + len(body)
            or self.total + len(body) > self.pin[1]
            or self.total + len(body) > SMALL_BYTES
            or original._snapshot(self.item) != self.snapshot
        ):
            raise ValueError("original_selected_member_span_required")
        self.parts.append(body)  # Exact original return reference, no body copy.
        self.total += len(body)
        self.last_positive = body
        if self.checksum is not None:
            self.checksum.feed(body)

    def finish(self):
        if (
            self.eof is not None
            or self.state.last_return != b""
            or type(self.state.last_return) is not bytes
            or self.state.original_read_return is not self.state.last_return
            or self.total != self.pin[1]
            or self.state.member_bytes != self.total
            or original._snapshot(self.item) != self.snapshot
        ):
            raise ValueError("original_selected_member_eof_required")
        self.eof = (
            self.state.original_member_stream,
            self.state.last_return,
            self.state.member_bytes,
        )
        if self.checksum is not None:
            self.checksum.finish()


def _capture_selected_member(state, archive, item, pin):
    sink = returned = None
    invocation = "not_invoked"
    try:
        if (
            type(state) is not original._State
            or type(archive) is not original.tarfile.TarFile
            or state.archive is not archive
            or vars(archive).get("closed") is not False
            or type(state.root) is not str
            or state.original_item is not item
            or type(pin) is not tuple
            or len(pin) != 3
            or type(pin[0]) is not str
            or type(pin[1]) is not int
            or not 0 <= pin[1] <= SMALL_BYTES
            or type(pin[2]) is not str
            or original.re.fullmatch("[0-9a-f]{64}", pin[2]) is None
            or pin[0] != original.headers._path(item.name)
            or pin[1] != item.size
            or not item.isfile()
            or "_selected_member_capture" in vars(state)
            or original._read_member is not _READ
        ):
            raise ValueError("original_bounded_member_selection_required")
        entry = state.entries.get(item.name)
        if (
            entry is None
            or entry.original_item is not item
            or entry.snapshot != original._snapshot(item)
        ):
            raise ValueError("original_selected_member_enrollment_required")
        checksum = (
            original._ChecksumLines(state)
            if item.name == state.root + "/SHA256SUMS"
            else None
        )
        sink = _SelectedSink(state, item, pin, checksum)
        # Original-state extension records the single selected capture attempt.
        # This is not a lease, detached admission or cumulative root budget.
        vars(state)["_selected_member_capture"] = pin
        invocation = "unknown"
        returned = _READ(state, archive, item, sink)
        invocation = "returned"
        chunks = tuple(sink.parts)
        digest = hashlib.sha256()
        total = 0
        for body in chunks:
            if type(body) is not bytes or not 0 < len(body) <= original.WINDOW:
                raise ValueError("bounded_original_capture_chunk_required")
            total += len(body)
            if total > pin[1]:
                raise ValueError("original_capture_size_changed")
            digest.update(body)
        if (
            total != pin[1]
            or total != sink.total
            or digest.hexdigest() != pin[2]
            or returned != pin[2]
            or type(returned) is not str
            or sink.eof is None
            or sink.eof[0] is not state.original_member_stream
            or state.stream_close_attempted is not True
            or not state.close_returns
            or state.close_returns[-1] != ("member", None)
            or original._snapshot(item) != entry.snapshot
            or original._snapshot(item) != sink.snapshot
            or state.original_item is not item
            or state.archive is not archive
            or state.entries.get(item.name) is not entry
        ):
            raise ValueError("original_capture_digest_eof_or_close_required")
        return ProvisionalMemberCapture(
            pin, chunks, returned, sink.eof, state.close_returns[-1], state
        )
    except BaseException as cause:
        chunks = ()
        if sink is not None:
            sink.parts.clear()  # Failure evidence explicitly bounded, not full history.
        raise MemberCaptureError(
            pin, state, sink, cause, invocation, returned
        ) from cause
