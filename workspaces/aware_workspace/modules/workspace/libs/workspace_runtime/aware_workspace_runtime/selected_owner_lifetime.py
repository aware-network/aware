"""Private custody mechanics, not selected-owner admission or installation.

The installed composition must authenticate the owner and its transferred
cancellation entrance before taking custody. This module authenticates neither
that origin nor an owner result. It is intentionally not wired into commands.
All calls, including release, belong outside parent exclusion.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from threading import RLock, current_thread
from types import BuiltinMethodType, GeneratorType
from typing import Never, cast, final, override
from weakref import ReferenceType, WeakKeyDictionary, ref


@final
class _SelectedOwnerCancellationCustody:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] - allocated only by storage transfer

    def __new__(cls) -> Never:
        raise TypeError("original owner cancellation transfer required")

    def __init_subclass__(cls, **kwargs: object) -> Never:
        raise TypeError("owner cancellation custody is final")

    @override
    def __reduce_ex__(self, protocol: object) -> Never:
        raise TypeError("owner cancellation custody is process-local")


@dataclass(slots=True, weakref_slot=True)
class _CustodyRecord:
    operation_use: object | None
    registration: object | None
    cancellation: BuiltinMethodType | None
    process_id: int
    thread: object
    cancellation_origin: tuple[BuiltinMethodType, ...]
    owner_result: object | None = None
    retained: bool = False
    terminal: bool = False


_CUSTODIES: WeakKeyDictionary[
    _SelectedOwnerCancellationCustody, _CustodyRecord | ReferenceType[_CustodyRecord]
] = WeakKeyDictionary()
# Weak keys preserve once-only transfer without retaining native generator
# frames after terminal cleanup, even if a cancelled generator ignored exit.
_TRANSFERRED: WeakKeyDictionary[object, bool] = WeakKeyDictionary()
_REGISTRY_LOCK = RLock()
_REGISTRY_PROCESS_ID = os.getpid()


def _require_registry_process() -> None:
    # A fork may inherit a lock held by a now-absent parent thread. Refuse
    # before touching that lock; do not reset it or adopt inherited resources.
    if os.getpid() != _REGISTRY_PROCESS_ID:
        raise RuntimeError("owner custody belongs to its original process/thread")


def _record_by_identity(custody: object) -> _CustodyRecord:
    # Restamping a registered custody must not trigger foreign hash/equality or
    # attribute behavior, including on terminal release.
    original: object | None = None
    record: _CustodyRecord | None = None
    try:
        _require_registry_process()
        with _REGISTRY_LOCK:
            for original, stored in _CUSTODIES.items():
                if original is custody:
                    # Attached records belong strongly to the original slot.
                    # Legacy unattached records retain their accepted storage.
                    record = (
                        cast(ReferenceType[_CustodyRecord], stored)()
                        if type(stored) is ReferenceType else cast(_CustodyRecord, stored)
                    )
                    if type(record) is not _CustodyRecord:
                        raise RuntimeError("owner custody record retired")
                    if record.process_id != os.getpid() or record.thread is not current_thread():
                        raise RuntimeError("owner custody belongs to its original process/thread")
                    return record
        raise TypeError("registered owner cancellation custody required")
    finally:
        # An unknown/foreign-context error must not pin the last scanned
        # family or the argument through a retained Workspace traceback.
        custody = original = record = stored = None


def _take_selected_owner_cancellation(
    operation_use: object,
    registration: object,
    cancellation: object,
) -> _SelectedOwnerCancellationCustody:
    """Hold an already authenticated transfer; this grants no execution rights.

    This private storage helper is not the proposed command preparation API.
    There is no production caller until the original resource inlet is installed.
    Arbitrary callbacks and reconstructed close methods do not authenticate an
    origin here; origin verification is an independent installer obligation.
    """
    generator: object | None = None
    custody: _SelectedOwnerCancellationCustody | None = None
    try:
        _require_registry_process()
        if operation_use is None or registration is None:
            raise TypeError("original use and registration storage keys required")
        if type(cancellation) is not BuiltinMethodType:
            raise TypeError("transferred native generator close method required")
        generator = cancellation.__self__
        if type(generator) is not GeneratorType or cancellation.__name__ != "close":
            raise TypeError("transferred native generator close method required")
        if not generator.gi_suspended:
            raise RuntimeError("owner cancellation generator must be primed and suspended")
        with _REGISTRY_LOCK:
            if generator in _TRANSFERRED:
                raise RuntimeError("owner cancellation already transferred")
            custody = object.__new__(_SelectedOwnerCancellationCustody)
            _CUSTODIES[custody] = _CustodyRecord(
                operation_use, registration, cancellation, os.getpid(), current_thread(), (cancellation,)
            )
            _TRANSFERRED[generator] = True
        return custody
    finally:
        # Clear only this helper's references, including pre-transfer rejection.
        # Borrowed generators/resources and foreign owner frames stay untouched.
        operation_use = registration = cancellation = generator = custody = None


def _release_record(record: _CustodyRecord) -> None:
    if record.terminal:
        return
    # The command loses its live bindings before owner cleanup, including when
    # cleanup raises. Never retain the cleanup exception or permit a retry.
    cancellation = record.cancellation_origin[0]
    record.terminal = True
    record.operation_use = None
    record.registration = None
    record.owner_result = None
    record.cancellation = None
    record.cancellation_origin = ()
    try:
        cancellation()
    finally:
        cancellation = None


def _retain_selected_owner_result(
    custody: object,
    operation_use: object,
    registration: object,
    owner_result: object,
) -> None:
    """Store an independently verified post-return result, never verify it here."""
    try:
        record = _record_by_identity(custody)
        if record.terminal:
            raise RuntimeError("owner cancellation custody terminal")
        error: Exception | None = None
        if type(custody) is not _SelectedOwnerCancellationCustody:
            error = TypeError("original owner cancellation custody required")
        elif record.cancellation is not record.cancellation_origin[0]:
            error = RuntimeError("owner cancellation storage substituted")
        elif record.operation_use is not operation_use or record.registration is not registration:
            error = RuntimeError("owner custody use or registration substituted")
        elif record.retained:
            error = RuntimeError("owner result already retained")
        elif owner_result is None:
            error = TypeError("owner result storage value required")
        if error is not None:
            try:
                _release_record(record)
            except BaseException as cleanup_error:  # noqa: BLE001 - preserve rejection and owner cancellation failure
                raise BaseExceptionGroup(
                    "owner result custody rejection and cleanup failed", [error, cleanup_error]
                ) from None
            raise error
        record.owner_result = owner_result
        record.retained = True
    finally:
        # Retained exception tracebacks must not become another custody rail.
        custody = operation_use = registration = owner_result = record = None


def _release_selected_owner_cancellation(custody: object) -> None:
    """Release the known transfer without dispatch through rejected behavior.

    Unknown values cannot cancel other families. A foreign thread/process cannot
    execute owner cleanup; the original command retains that responsibility.
    Durable receipts and reconciliation remain with the owner, outside custody.
    """
    try:
        _release_record(_record_by_identity(custody))
    finally:
        custody = None


@final
class _WorkspaceSelectedOwnerAttachment:
    """Storage-only handle; neither construction nor registration admits an owner."""

    __slots__ = ("__weakref__", "_command", "_custody_record", "_pending_custody", "_record", "_use")  # pyright: ignore[reportUninitializedInstanceVariable] - reserved by object.__new__, not public construction
    _command: object | None  # pyright: ignore[reportUninitializedInstanceVariable] - initialized by reserve before publication
    _use: object | None  # pyright: ignore[reportUninitializedInstanceVariable] - initialized by reserve before publication
    _pending_custody: _SelectedOwnerCancellationCustody | None  # pyright: ignore[reportUninitializedInstanceVariable] - initialized by reserve before publication
    _record: _OwnerAttachmentRecord  # pyright: ignore[reportUninitializedInstanceVariable] - initialized by reserve before publication
    _custody_record: _CustodyRecord | None  # pyright: ignore[reportUninitializedInstanceVariable] - initialized by reserve before publication

    def __new__(cls) -> Never:
        raise TypeError("original command attachment storage required")

    def __init_subclass__(cls, **kwargs: object) -> Never:
        raise TypeError("owner attachment is final")

    @override
    def __reduce_ex__(self, protocol: object) -> Never:
        raise TypeError("owner attachment is process-local")


@dataclass(slots=True, weakref_slot=True)
class _OwnerAttachmentRecord:
    selection: object | None
    delivery: object | None
    port_origins: tuple[object, ...]
    registration: object | None
    process_id: int
    thread: object
    phase: str = "reserved"
    attach_state: str = "unspent"
    prepare_state: str = "unspent"
    retain_state: str = "unspent"
    close_state: str = "unspent"
    transfer_state: str = "unspent"
    cancel_close_state: str = "unspent"
    native_cancellation: BuiltinMethodType | None = None
    cancellation_custody: _SelectedOwnerCancellationCustody | None = None
    owner_result: object | None = None


_ATTACHMENTS: WeakKeyDictionary[
    _WorkspaceSelectedOwnerAttachment, ReferenceType[_OwnerAttachmentRecord]
] = WeakKeyDictionary()


_ACTIVE_OWNER_CAPTURES: list[ReferenceType[_OwnerAttachmentRecord]] = []


def _require_no_active_owner_capture(record: _OwnerAttachmentRecord) -> None:
    """Reject same-thread reentry without owning another custody reference."""
    active: ReferenceType[_OwnerAttachmentRecord] | None = None
    try:
        for active in _ACTIVE_OWNER_CAPTURES:
            if active() is record:
                raise RuntimeError("owner attachment capture in progress")
    finally:
        del record
        active = None


def _owner_attachment_record(attachment: object) -> _OwnerAttachmentRecord:
    original: object | None = None
    record: _OwnerAttachmentRecord | None = None
    try:
        _require_registry_process()
        with _REGISTRY_LOCK:
            for original, record_ref in _ATTACHMENTS.items():
                if original is attachment:
                    if type(record_ref) is not ReferenceType:
                        raise RuntimeError("owner attachment index substituted")
                    record = record_ref()
                    if type(record) is not _OwnerAttachmentRecord:
                        raise RuntimeError("owner attachment record substituted")
                    if type(record.process_id) is not int or record.process_id != os.getpid() or record.thread is not current_thread():
                        raise RuntimeError("owner attachment belongs to its original process/thread")
                    if type(record.phase) is not str:
                        record.phase = "held"
                        raise RuntimeError("owner attachment phase substituted")
                    for state in (
                        record.attach_state, record.prepare_state, record.retain_state,
                        record.close_state, record.transfer_state, record.cancel_close_state,
                    ):
                        if type(state) is not str or state not in ("unspent", "spent", "complete", "uncertain"):
                            record.phase = "held"
                            raise RuntimeError("owner attachment state substituted")
                    if type(attachment) is not _WorkspaceSelectedOwnerAttachment:
                        record.phase = "held"
                        raise TypeError("original owner attachment required")
                    if record.phase == "closed":
                        raise RuntimeError("owner attachment closed")
                    return record
        raise TypeError("registered owner attachment required")
    finally:
        attachment = original = record = record_ref = state = None


def _reserve_owner_attachment_storage(
    command_position: list[object], command: object, operation_use: object,
    registration: object,
) -> _WorkspaceSelectedOwnerAttachment:
    """Reserve storage only after independent original-command admission.

    There is deliberately no production caller. A fixture-created slot is local
    bookkeeping and cannot enter the installed receiving interfaces.
    """
    record: _OwnerAttachmentRecord | None = None
    attachment: _WorkspaceSelectedOwnerAttachment | None = None
    try:
        _require_registry_process()
        if type(command_position) is not list or len(command_position) != 1:
            raise TypeError("single command-owned attachment position required")
        if command is None or operation_use is None or registration is None:
            raise TypeError("original attachment storage associations required")
        with _REGISTRY_LOCK:
            if command_position[0] is not None:
                raise RuntimeError("command attachment position already spent")
            record = _OwnerAttachmentRecord(None, None, (), registration, os.getpid(), current_thread())
            command_position[0] = record
            record.attach_state = "spent"
            attachment = object.__new__(_WorkspaceSelectedOwnerAttachment)
            attachment._command = command
            attachment._use = operation_use
            attachment._pending_custody = None
            attachment._record = record
            attachment._custody_record = None
            _ATTACHMENTS[attachment] = ref(record)
            command_position[0] = attachment
        return attachment
    except BaseException:
        if record is not None:
            record.phase = "held"
            record.attach_state = "uncertain"
        raise
    finally:
        del command_position
        command = operation_use = registration = record = attachment = None


def _capture_owner_attachment_cancellation(
    attachment: object, registration: object, cancellation: object,
) -> None:
    """Publish a transfer in storage; never authenticate the native owner."""
    record: _OwnerAttachmentRecord | None = None
    capture_ref: ReferenceType[_OwnerAttachmentRecord] | None = None
    generator: object | None = None
    custody: _SelectedOwnerCancellationCustody | None = None
    try:
        record = _owner_attachment_record(attachment)
        attachment = cast(_WorkspaceSelectedOwnerAttachment, attachment)
        with _REGISTRY_LOCK:
            _require_no_active_owner_capture(record)
            capture_ref = ref(record)
            _ACTIVE_OWNER_CAPTURES.append(capture_ref)
        if record.phase != "preparing" or record.prepare_state != "spent" or record.close_state != "unspent":
            raise RuntimeError("original preparing owner attachment required")
        if record.registration is not registration or record.transfer_state != "unspent":
            raise RuntimeError("owner attachment transfer substituted or spent")
        if type(cancellation) is not BuiltinMethodType:
            raise TypeError("transferred native generator close method required")
        generator = cancellation.__self__
        if type(generator) is not GeneratorType or cancellation.__name__ != "close" or not generator.gi_suspended:
            raise TypeError("primed suspended native generator close required")
        with _REGISTRY_LOCK:
            # Close spending fences capture independently of the phase write.
            # Recheck at publication, including a reentrant close during the
            # validation above; a closing/uncertain position is never refunded.
            if record.close_state != "unspent" or record.phase != "preparing":
                raise RuntimeError("owner attachment close already submitted")
            if generator in _TRANSFERRED:
                raise RuntimeError("owner cancellation already transferred")
            record.native_cancellation = cancellation
            record.transfer_state = "spent"
            # Fence other takes before allocation. A spent position is never
            # refunded, even if construction/publication is interrupted.
            _TRANSFERRED[generator] = True
            attachment._pending_custody = object.__new__(_SelectedOwnerCancellationCustody)
            custody = attachment._pending_custody
            attachment._custody_record = _CustodyRecord(
                attachment._use, registration, cancellation, os.getpid(), current_thread(), (cancellation,)
            )
            _CUSTODIES[custody] = ref(attachment._custody_record)
            # This strong publication, after registry installation, transfers
            # cleanup ownership. Pending custody alone is producer-owned.
            record.cancellation_custody = custody
            attachment._pending_custody = None
            record.transfer_state = "complete"
    except BaseException:
        if record is not None and capture_ref is not None:
            record.phase = "held"
            if record.transfer_state == "spent":
                record.transfer_state = "uncertain"
        raise
    finally:
        # Only this invocation removes its marker, after its final possible
        # publication. Identity removal avoids weakref/record equality dispatch.
        try:
            if capture_ref is not None:
                with _REGISTRY_LOCK:
                    for index, active in enumerate(_ACTIVE_OWNER_CAPTURES):
                        if active is capture_ref:
                            del _ACTIVE_OWNER_CAPTURES[index]
                            break
        finally:
            attachment = registration = cancellation = record = generator = custody = capture_ref = active = None


def _join_owner_attachment_storage(
    attachment: object, selection: object, delivery: object,
    port_origins: tuple[object, ...],
) -> None:
    """Store already independently verified originals without invoking them."""
    record: _OwnerAttachmentRecord | None = None
    try:
        record = _owner_attachment_record(attachment)
        if record.phase != "reserved" or record.attach_state != "spent":
            raise RuntimeError("owner attachment already joined or held")
        if selection is None or delivery is None or type(port_origins) is not tuple or len(port_origins) != 4:
            raise TypeError("complete original attachment storage values required")
        record.phase = "attaching"
        record.selection = selection
        record.delivery = delivery
        record.port_origins = port_origins
        record.attach_state = "complete"
        record.phase = "attached"
    except BaseException:
        if record is not None:
            record.phase = "held"
            record.attach_state = "uncertain"
        raise
    finally:
        del port_origins
        attachment = selection = delivery = record = None


def _begin_owner_attachment_prepare(attachment: object) -> None:
    record: _OwnerAttachmentRecord | None = None
    try:
        record = _owner_attachment_record(attachment)
        if record.phase != "attached" or record.prepare_state != "unspent":
            raise RuntimeError("owner attachment preparation already spent or held")
        record.prepare_state = "spent"
        record.phase = "preparing"
    except BaseException:
        if record is not None:
            record.phase = "held"
        raise
    finally:
        attachment = record = None


def _begin_owner_attachment_close(attachment: object) -> None:
    record: _OwnerAttachmentRecord | None = None
    try:
        record = _owner_attachment_record(attachment)
        with _REGISTRY_LOCK:
            _require_no_active_owner_capture(record)
            if record.close_state != "unspent":
                raise RuntimeError("owner attachment close already submitted")
            try:
                record.close_state = "spent"
                record.phase = "closing"
            except BaseException:
                # The close may have been submitted. Never reopen capture or
                # resubmit close after an interrupted transition.
                record.close_state = "uncertain"
                record.phase = "held"
                raise
    finally:
        attachment = record = None


def _complete_owner_attachment_close(attachment: object) -> None:
    """Record a known port-close return, not infer it from generator state.

    Only the independently authenticated close dispatcher may assert this
    outcome in a future installed integration. This primitive performs no owner
    call; synthetic fixture completion is not an installed close receipt.
    """
    record: _OwnerAttachmentRecord | None = None
    try:
        record = _owner_attachment_record(attachment)
        attachment = cast(_WorkspaceSelectedOwnerAttachment, attachment)
        if record.phase != "closing" or record.close_state != "spent":
            raise RuntimeError("original pending close required")
        if record.cancellation_custody is not None and record.cancel_close_state != "complete":
            raise RuntimeError("transferred cancellation close not complete")
        if record.cancellation_custody is not None and attachment._pending_custody is not None:
            # T09 can leave the pending slot aliasing the strongly published
            # holder. Known successful cleanup reconciles only that same
            # identity; a foreign pending holder must remain held.
            if attachment._pending_custody is not record.cancellation_custody:
                raise RuntimeError("pending owner custody substituted")
            attachment._pending_custody = None
        if record.cancellation_custody is None:
            # The original producer submitted cleanup in this branch. Its
            # known close return permits releasing pending bookkeeping only.
            attachment._pending_custody = None
            record.native_cancellation = None
            record.cancel_close_state = "complete"
        record.close_state = "complete"
    except BaseException:
        if record is not None:
            record.close_state = "uncertain"
            record.phase = "held"
        raise
    finally:
        attachment = record = None


def _read_owner_attachment_cancellation(
    attachment: object,
) -> tuple[BuiltinMethodType, _SelectedOwnerCancellationCustody] | None:
    record: _OwnerAttachmentRecord | None = None
    try:
        record = _owner_attachment_record(attachment)
        attachment = cast(_WorkspaceSelectedOwnerAttachment, attachment)
        with _REGISTRY_LOCK:
            _require_no_active_owner_capture(record)
            if attachment._record is not record:
                raise RuntimeError("owner attachment record substituted")
            if record.cancel_close_state != "unspent":
                raise RuntimeError("owner cancellation cleanup already submitted")
            if record.cancellation_custody is None:
                # The original, thread-confined slot records the linearization
                # point. A failed capture cannot publish after this readback;
                # pending allocation/registry installation is still producer
                # custody. Do not infer absence during a live reentrant capture.
                if record.transfer_state != "unspent" and not (
                    record.transfer_state == "uncertain"
                    and (record.phase == "held" or record.close_state != "unspent")
                ):
                    raise RuntimeError("owner transfer reconciliation required")
                return None
        custody_record = _record_by_identity(record.cancellation_custody)
        if (
            type(record.cancellation_custody) is not _SelectedOwnerCancellationCustody
            or custody_record.terminal
            or custody_record.operation_use is not attachment._use
            or custody_record.registration is not record.registration
            or custody_record.cancellation is not record.native_cancellation
            or record.native_cancellation is None
        ):
            record.phase = "held"
            raise RuntimeError("owner attachment custody substituted")
        return record.native_cancellation, record.cancellation_custody
    finally:
        attachment = record = custody_record = None


def _release_owner_attachment_cancellation(attachment: object) -> None:
    record: _OwnerAttachmentRecord | None = None
    try:
        record = _owner_attachment_record(attachment)
        if record.cancel_close_state != "unspent":
            raise RuntimeError("owner cancellation cleanup already submitted")
        pair = _read_owner_attachment_cancellation(attachment)
        if pair is None:
            raise RuntimeError("no transferred owner cancellation")
        record.cancel_close_state = "spent"
        _release_selected_owner_cancellation(pair[1])
        record.cancel_close_state = "complete"
        record.native_cancellation = None
    except BaseException:
        if record is not None and record.cancel_close_state == "spent":
            record.cancel_close_state = "uncertain"
            record.phase = "held"
        raise
    finally:
        attachment = record = pair = None


def _seal_owner_attachment_storage(attachment: object) -> None:
    record: _OwnerAttachmentRecord | None = None
    try:
        record = _owner_attachment_record(attachment)
        attachment = cast(_WorkspaceSelectedOwnerAttachment, attachment)
        if record.phase != "closing" or record.close_state != "complete":
            raise RuntimeError("known successful original owner close required")
        if record.transfer_state != "unspent" and record.cancel_close_state != "complete":
            raise RuntimeError("known successful cancellation cleanup required")
        if attachment._pending_custody is not None:
            raise RuntimeError("pending owner custody reconciliation required")
        record.phase = "held"
        record.selection = record.delivery = record.registration = record.owner_result = None
        record.port_origins = ()
        record.native_cancellation = record.cancellation_custody = None
        attachment._command = attachment._use = None
        attachment._custody_record = None
        record.phase = "closed"
    finally:
        attachment = record = None
