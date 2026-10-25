"""Original native creation custody and explicitly selected facade routing.

Only this original synchronous constructor enrolls a facade. Detached frames and
pointer values are not import ports. Libraries and unsettled custody are retained
for process lifetime; garbage collection never dispatches cleanup.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import threading
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, NoReturn
from weakref import WeakKeyDictionary

from .native_bootstrap_creation import (
    MAX_CAPTURE_BYTES,
    NativeBootstrapCallEvidence,
    NativeBootstrapFailure,
    NativeBootstrapRawOutput,
    NativeBootstrapSelection,
    _DecodedCapture,
    _load_creation_ports,
    _NativeCreationPorts,
    decode_bootstrap_capture,
)

if TYPE_CHECKING:
    from pathlib import Path

    from .retained_bootstrap import BootstrapFileCreation, RetainedBootstrapCreation
    from .retained_mutation import RetainedPhysicalEffect

_HANDLES: WeakKeyDictionary[RetainedBootstrapCreation, _Custody] = WeakKeyDictionary()
_LIBRARIES: list[ctypes.CDLL] = []
_LIVE: list[_Custody] = []
_OPERATION_IDS = {
    "validate_current": 3,
    "prepare_next_directory": 4,
    "create_next_file": 5,
    "finish": 6,
}


@dataclass(eq=False)
class _PendingCall:
    """Owner-held call coordinates and original slots, prepared before dispatch."""

    template: NativeBootstrapCallEvidence
    output: NativeBootstrapRawOutput
    length: ctypes.c_uint64
    status: int | None = None
    cause: BaseException | None = None


def lookup(handle: RetainedBootstrapCreation) -> _Custody | None:
    # No table enrollment by decoded markers or numeric addresses.
    from .retained_bootstrap import RetainedBootstrapCreation

    if type(handle) is not RetainedBootstrapCreation:
        return None
    state = _HANDLES.get(handle)
    if state is not None:
        state.check_process()  # before any inherited lock or C call
    return state


def _request(
    root: Path, files: tuple[BootstrapFileCreation, ...], dirs: tuple[str, ...]
) -> bytes:
    def integer(value: int) -> bytes:
        return value.to_bytes(8, "big")

    def coordinate(value: str | Path) -> bytes:
        raw = os.fsencode(value)
        if len(raw) > 4096 or b"\x00" in raw:
            raise ValueError("native_bootstrap_coordinate_unrepresentable")
        if isinstance(value, str) and len(raw.split(b"/")) > 64:
            raise ValueError("native_bootstrap_coordinate_unrepresentable")
        return raw

    def span(value: bytes) -> bytes:
        return integer(len(value)) + value

    parts = [
        b"aware.fs.bootstrap.request.v1",
        span(coordinate(root)),
        integer(len(dirs)),
    ]
    parts.extend(span(coordinate(path)) for path in dirs)
    parts.append(integer(len(files)))
    for item in files:
        parts.extend(
            (span(coordinate(item.path)), integer(item.mode), span(item.content))
        )
    parts.append(span(b"descriptor_walk_v1"))
    request = b"".join(parts)
    if len(request) > 50_614_272:
        raise ValueError("native_bootstrap_request_unrepresentable")
    return request


@dataclass(eq=False)
class _Custody:
    ports: _NativeCreationPorts
    request: bytes
    pid: int = field(default_factory=os.getpid)
    lock: threading.Lock = field(default_factory=threading.Lock)
    owner: ctypes.c_void_p = field(default_factory=ctypes.c_void_p)
    length: ctypes.c_uint64 = field(default_factory=ctypes.c_uint64)
    records: tuple[NativeBootstrapCallEvidence, ...] = ()
    snapshot: _DecodedCapture | None = None
    primary: NativeBootstrapCallEvidence | None = None
    pending: _PendingCall | None = None
    sequence: int = 0
    operation: str = "retain"
    next_sequence: int | None = 1
    routing: bool = False
    status: int | None = None
    guard: bytes | None = None
    quarantine: bool = False
    release_spent: bool = False
    release_complete: bool = False
    destroy_spent: bool = False
    destroyed: bool = False
    receiving_cause: BaseException | None = None
    # Keep initialized allocations even if snapshotting fails after dispatch.
    buffers: list[object] = field(default_factory=list)

    def check_process(self) -> None:
        if self.pid != os.getpid():
            self.fail("native_bootstrap_foreign_process")

    def fail(
        self,
        code: str,
        handle: RetainedBootstrapCreation | None = None,
        cause: BaseException | None = None,
    ) -> NoReturn:
        snapshot = self.snapshot
        error = NativeBootstrapFailure(
            code,
            native_evidence=self.records,
            effects=() if snapshot is None else snapshot.evidence.effects or (),
            residual_scratch_paths=()
            if snapshot is None
            else snapshot.evidence.residual_scratch_paths or (),
            effects_complete=snapshot is not None
            and snapshot.evidence.effects is not None
            and snapshot.evidence.capture_complete
            and not self.quarantine,
            cleanup_handle=handle if self.owner.value else None,
        )
        if cause is not None:
            raise error from cause
        raise error

    def enter(self) -> None:
        self.check_process()
        if not self.lock.acquire(blocking=False):
            self.fail("native_bootstrap_busy")

    def evidence(self) -> tuple[NativeBootstrapCallEvidence, ...]:
        self.enter()
        try:
            return self.records
        finally:
            self.lock.release()

    def phase(self) -> str:
        self.enter()
        try:
            if self.quarantine or self.snapshot is None:
                self.fail("native_bootstrap_frozen")
            phase = self.snapshot.evidence.phase_after
            if phase is None:
                self.fail("native_bootstrap_frozen")
            return phase
        finally:
            self.lock.release()

    def effects(self) -> tuple[RetainedPhysicalEffect, ...]:
        self.enter()
        try:
            if (
                self.quarantine
                or self.snapshot is None
                or self.snapshot.evidence.effects is None
            ):
                self.fail("native_bootstrap_frozen")
            return self.snapshot.evidence.effects
        finally:
            self.lock.release()

    def unavailable(self) -> NoReturn:
        self.check_process()
        self.fail("native_bootstrap_frozen")

    def record_call(
        self,
        pending: _PendingCall,
        handle: RetainedBootstrapCreation,
        *,
        no_dispatch: bool = False,
    ) -> NativeBootstrapCallEvidence:
        """Receipt allocation cannot replace current call custody with old state.

        Fallback snapshots derive from pre-dispatch immutable templates. They can
        still allocate: this is not a general emergency-memory guarantee.
        """
        template = pending.template
        try:
            primary = NativeBootstrapCallEvidence(
                template.operation,
                template.sequence,
                True,
                pending.status,
                None,
                (NativeBootstrapRawOutput(pending.output.name, pending.length.value),),
                None,
                None,
                False,
                pending.cause,
            )
            self.records += (primary,)
        except BaseException as error:  # noqa: BLE001 - original call is already held
            self.receiving_cause = error
            if not no_dispatch:
                self.quarantine = True
            primary = replace(
                template,
                native_status=pending.status,
                outputs=(replace(pending.output, value=pending.length.value),),
                python_cause=pending.cause,
            )
            if not no_dispatch:
                self.primary = primary
            self.records += (primary, replace(primary, python_cause=error))
            self.fail("native_bootstrap_capture_unavailable", handle, error)
        if not no_dispatch:
            self.primary = primary
        return primary

    def advance(
        self, operation: str, handle: RetainedBootstrapCreation
    ) -> _DecodedCapture:
        self.enter()
        try:
            sequence = self.next_sequence
            if (
                not self.routing
                or self.quarantine
                or self.release_spent
                or self.destroy_spent
                or self.status != 0
                or self.snapshot is None
                or self.snapshot.core_kind != "complete"
                or self.guard is None
                or sequence is None
                or sequence >= 255
                or operation not in _OPERATION_IDS
            ):
                self.fail("native_bootstrap_frozen", handle)
            try:
                length = ctypes.c_uint64()
                guard = ctypes.create_string_buffer(self.guard)
                length_pointer = ctypes.byref(length)
                self.buffers.extend((length, guard, length_pointer))
                step = self.ports.step
                pending = _PendingCall(
                    NativeBootstrapCallEvidence(
                        operation,
                        sequence,
                        True,
                        None,
                        None,
                        (),
                        None,
                        None,
                        False,
                        None,
                    ),
                    NativeBootstrapRawOutput("capture_length_returned", None),
                    length,
                )
            except BaseException as error:  # noqa: BLE001 - dispatch not attempted
                self.receiving_cause = error
                self.records += (
                    NativeBootstrapCallEvidence(
                        operation,
                        sequence,
                        False,
                        None,
                        None,
                        (),
                        None,
                        None,
                        False,
                        error,
                    ),
                )
                self.fail(
                    "native_bootstrap_interrupted"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "native_bootstrap_transport_unavailable",
                    handle,
                    error,
                )
            previous_sequence, previous_operation = self.sequence, self.operation
            previous_primary, previous_pending = self.primary, self.pending
            self.sequence, self.operation, self.length = sequence, operation, length
            self.primary, self.pending = pending.template, pending
            self.next_sequence = None
            self.quarantine = True  # old snapshots cannot describe an in-flight call
            try:
                pending.status = step(
                    self.owner,
                    _OPERATION_IDS[operation],
                    sequence,
                    guard,
                    length_pointer,
                )
            except BaseException as error:  # noqa: BLE001 - known effects survive missing return
                pending.cause = error
            status, cause = pending.status, pending.cause
            if status == 2:
                self.sequence, self.operation = previous_sequence, previous_operation
                self.primary, self.pending = previous_primary, previous_pending
                self.next_sequence = sequence
                self.quarantine = False  # original transport confirms no dispatch
                _ = self.record_call(pending, handle, no_dispatch=True)
                self.fail("native_bootstrap_transport_unavailable", handle, cause)
            self.status = status
            primary = self.record_call(pending, handle)
            record = self.collect(primary)
            if record.validated and cause is None and status in (0, 1):
                self.quarantine = False
            if not record.validated or self.snapshot is None:
                self.fail(
                    "native_bootstrap_capture_unavailable",
                    handle,
                    cause or record.python_cause,
                )
            if self.snapshot.failure is not None:
                self.fail(
                    self.snapshot.failure.code, handle, cause or record.python_cause
                )
            if self.quarantine or status != 0 or self.snapshot.core_kind != "complete":
                self.fail(
                    "native_bootstrap_interrupted"
                    if isinstance(
                        cause or record.python_cause, (KeyboardInterrupt, SystemExit)
                    )
                    else "native_bootstrap_frozen",
                    handle,
                    cause or record.python_cause,
                )
            return self.snapshot
        finally:
            self.lock.release()

    def collect(
        self, original: NativeBootstrapCallEvidence
    ) -> NativeBootstrapCallEvidence:
        # Setup and final evidence construction can fail too, after the original
        # constructor has already issued custody. Preserve that original call and
        # keep the genuine handle available to the caller, without cleanup here.
        try:
            return self._collect(original)
        except BaseException as error:  # noqa: BLE001 - retain acquired custody
            self.receiving_cause = error
            self.quarantine = True
            record = replace(
                original,
                frame=None,
                frame_sha256=None,
                validated=False,
                python_cause=error,
            )
            self.records += (record,)
            return record

    def _collect(
        self, original: NativeBootstrapCallEvidence
    ) -> NativeBootstrapCallEvidence:
        outputs = list(original.outputs)
        length = ctypes.c_uint64()
        self.buffers.append(length)
        digest = (ctypes.c_ubyte * 32)()
        self.buffers.append(digest)
        core = ctypes.c_int32(-1)
        self.buffers.append(core)
        frame = None
        decoded = None
        cause = None
        try:
            info_status = None
            try:
                info_status = self.ports.capture_info(
                    self.owner,
                    self.sequence,
                    ctypes.byref(length),
                    digest,
                    ctypes.byref(core),
                )
            finally:
                outputs.extend(
                    (
                        NativeBootstrapRawOutput("info_status", info_status),
                        NativeBootstrapRawOutput("capture_length", length.value),
                        NativeBootstrapRawOutput("capture_sha256", bytes(digest)),
                        NativeBootstrapRawOutput("core_status", core.value),
                    )
                )
            if info_status != 0 or not 0 < length.value <= MAX_CAPTURE_BYTES:
                raise ValueError("native_bootstrap_capture_unavailable")
            chunks = []
            offset = 0
            while offset < length.value:
                capacity = min(1_048_576, length.value - offset)
                buffer = ctypes.create_string_buffer(capacity)
                written = ctypes.c_size_t()
                self.buffers.extend((buffer, written))
                copy_status = None
                try:
                    copy_status = self.ports.copy_capture(
                        self.owner,
                        self.sequence,
                        offset,
                        buffer,
                        capacity,
                        ctypes.byref(written),
                    )
                finally:
                    prefix = buffer.raw[: min(written.value, capacity)]
                    outputs.extend(
                        (
                            NativeBootstrapRawOutput(
                                f"copy_{offset}_capacity", capacity
                            ),
                            NativeBootstrapRawOutput(
                                f"copy_{offset}_status", copy_status
                            ),
                            NativeBootstrapRawOutput(
                                f"copy_{offset}_written", written.value
                            ),
                            NativeBootstrapRawOutput(f"copy_{offset}_prefix", prefix),
                        )
                    )
                if copy_status != 0 or written.value != capacity:
                    raise ValueError("native_bootstrap_capture_invalid")
                chunks.append(prefix)
                offset += capacity
            raw = b"".join(chunks)
            call = replace(original, core_status=core.value, outputs=tuple(outputs))
            decoded = decode_bootstrap_capture(
                raw,
                call=call,
                request_digest="sha256:" + hashlib.sha256(self.request).hexdigest(),
                capture_length=length.value,
                capture_sha256=bytes(digest),
            )
            frame = raw
            self.guard = bytes(digest)
        except BaseException as error:  # noqa: BLE001 - preserve interrupted receiving
            cause = error
            self.receiving_cause = error
            self.quarantine = True
        record = replace(
            original,
            core_status=core.value,
            outputs=tuple(outputs),
            frame=frame,
            frame_sha256=None if frame is None else hashlib.sha256(frame).hexdigest(),
            validated=decoded is not None,
            python_cause=cause or original.python_cause,
        )
        self.records += (record,)
        if decoded is not None:
            self.snapshot = decoded
            self.next_sequence = original.sequence + 1
        return record

    def receive(self, handle: RetainedBootstrapCreation) -> NativeBootstrapCallEvidence:
        self.enter()
        try:
            if self.destroyed or self.primary is None or not self.owner.value:
                self.fail("native_bootstrap_capture_unavailable", handle)
            # Observation of the original settled call, never a redispatch.
            return self.collect(self.primary)
        finally:
            self.lock.release()

    def destroy(self, handle: RetainedBootstrapCreation) -> None:
        if self.destroy_spent:
            if not self.destroyed:
                self.fail("native_bootstrap_capture_unavailable", handle)
            return
        self.destroy_spent = True
        status = None
        cause = None
        try:
            status = self.ports.destroy(self.owner, 0)
        except BaseException as error:  # noqa: BLE001 - destruction is never retried
            cause = error
        self.records += (
            NativeBootstrapCallEvidence(
                "release",
                self.sequence,
                False,
                None,
                None,
                (NativeBootstrapRawOutput("wrapper_destroy_status", status),),
                None,
                None,
                False,
                cause,
            ),
        )
        self.destroyed = status == 0
        if self.destroyed:
            _LIVE.remove(self)
        else:
            self.fail("native_bootstrap_capture_unavailable", handle, cause)

    def release(self, handle: RetainedBootstrapCreation) -> None:
        self.enter()
        try:
            if self.release_spent:
                if self.release_complete and self.destroyed:
                    return
                self.fail("native_bootstrap_frozen", handle)
            # Refused constructor has no core session. Explicitly destroy only
            # a fully received terminal wrapper, preserving the original refusal.
            if (
                self.operation == "retain"
                and self.snapshot is not None
                and self.snapshot.core_kind != "complete"
            ):
                if self.quarantine:
                    self.fail("native_bootstrap_frozen", handle)
                self.release_spent = True
                self.destroy(handle)
                self.fail(
                    self.snapshot.failure.code
                    if self.snapshot.failure
                    else "native_bootstrap_frozen",
                    handle,
                )
            if not self.owner.value or (
                self.guard is None and self.status not in (1, 3)
            ):
                self.fail("native_bootstrap_frozen", handle)
            sequence = self.next_sequence
            if sequence is None or not 1 <= sequence <= 255:
                self.fail("native_bootstrap_frozen", handle)
            try:
                length = ctypes.c_uint64()
                guard = (
                    None
                    if self.guard is None
                    else ctypes.create_string_buffer(self.guard)
                )
                length_pointer = ctypes.byref(length)
                self.buffers.extend((length, guard, length_pointer))
                step = self.ports.step
                pending = _PendingCall(
                    NativeBootstrapCallEvidence(
                        "release",
                        sequence,
                        True,
                        None,
                        None,
                        (),
                        None,
                        None,
                        False,
                        None,
                    ),
                    NativeBootstrapRawOutput("capture_length_returned", None),
                    length,
                )
            except BaseException as error:  # noqa: BLE001 - no native dispatch yet
                self.receiving_cause = error
                self.records += (
                    NativeBootstrapCallEvidence(
                        "release",
                        sequence,
                        False,
                        None,
                        None,
                        (),
                        None,
                        None,
                        False,
                        error,
                    ),
                )
                self.fail(
                    "native_bootstrap_interrupted"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "native_bootstrap_transport_unavailable",
                    handle,
                    error,
                )
            previous_sequence, previous_operation = self.sequence, self.operation
            previous_primary, previous_pending = self.primary, self.pending
            self.sequence = sequence
            self.operation = "release"
            self.length = length
            self.primary, self.pending = pending.template, pending
            self.next_sequence = None
            self.release_spent = True
            try:
                pending.status = step(self.owner, 7, sequence, guard, length_pointer)
            except BaseException as error:  # noqa: BLE001 - release stays spent after interruption
                pending.cause = error
            status, cause = pending.status, pending.cause
            if status == 2:
                self.release_spent = False
                self.sequence, self.operation = previous_sequence, previous_operation
                self.primary, self.pending = previous_primary, previous_pending
                self.next_sequence = sequence
                _ = self.record_call(pending, handle, no_dispatch=True)
                self.fail("native_bootstrap_transport_unavailable", handle, cause)
            self.status = status
            primary = self.record_call(pending, handle)
            record = self.collect(primary)
            self.release_complete = (
                status == 0
                and cause is None
                and record.validated
                and self.snapshot is not None
                and self.snapshot.core_kind == "complete"
            )
            if not self.release_complete:
                self.quarantine = True
                self.fail("native_bootstrap_frozen", handle, record.python_cause)
            if not self.quarantine:
                self.destroy(handle)
            else:
                self.fail("native_bootstrap_capture_unavailable", handle)
        finally:
            self.lock.release()


def retain(
    root: Path,
    files: tuple[BootstrapFileCreation, ...],
    dirs: tuple[str, ...],
    selection: NativeBootstrapSelection,
    *,
    routing: bool = False,
) -> RetainedBootstrapCreation:
    from .retained_bootstrap import RetainedBootstrapCreation

    request = _request(root, files, dirs)  # pure representability before library IO
    try:
        ports = _load_creation_ports(selection)
    except BaseException as cause:
        raise NativeBootstrapFailure(
            "native_bootstrap_interrupted"
            if isinstance(cause, (KeyboardInterrupt, SystemExit))
            else "native_bootstrap_transport_unavailable",
            native_evidence=(),
        ) from cause
    state = _Custody(ports, request)
    state.routing = routing
    handle = object.__new__(RetainedBootstrapCreation)
    buffer = ctypes.create_string_buffer(request)
    state.buffers.append(buffer)
    _LIBRARIES.append(ports.library)  # pin before dispatch, even missing return
    _LIVE.append(state)
    status = None
    cause = None
    try:
        status = ports.retain(
            buffer, len(request), ctypes.byref(state.owner), ctypes.byref(state.length)
        )
    except BaseException as error:  # noqa: BLE001 - preserve issued custody on interruption
        cause = error
        state.receiving_cause = error
    state.status = status
    state.primary = NativeBootstrapCallEvidence(
        "retain",
        0,
        True,
        status,
        None,
        (
            NativeBootstrapRawOutput("owner_issued", int(bool(state.owner.value))),
            NativeBootstrapRawOutput("capture_length_returned", state.length.value),
        ),
        None,
        None,
        False,
        cause,
    )
    state.records = (state.primary,)
    if state.owner.value:
        _HANDLES[handle] = state
        record = state.collect(state.primary)
    else:
        state.records = (state.primary,)
        record = state.primary
    if (
        status != 0
        or cause is not None
        or not record.validated
        or state.snapshot is None
        or state.snapshot.core_kind != "complete"
    ):
        state.quarantine = cause is not None or not record.validated
        code = (
            "native_bootstrap_interrupted"
            if isinstance(cause or record.python_cause, (KeyboardInterrupt, SystemExit))
            else "native_bootstrap_capture_unavailable"
        )
        if (
            record.validated
            and state.snapshot is not None
            and state.snapshot.failure is not None
        ):
            code = state.snapshot.failure.code
        state.fail(code, handle, cause or record.python_cause)
    return handle
