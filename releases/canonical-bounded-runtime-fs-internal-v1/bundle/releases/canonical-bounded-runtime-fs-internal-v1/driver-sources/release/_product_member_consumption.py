"""Provisional bounded sink composition over the unchanged original reader.

No scanner mounting, filesystem writer, root authority or installation is
provided. Acknowledgements are typed caller-sink claims, not physical proof.
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from . import _product_stream_catalog as original

_READ = original._read_member
_CURSOR = original._MemberCursor
WRITE_CALLS = original.READ_CALLS
LAYERS = 2  # One explicit outer and one inner consumption layer; no refunds.
_LAYERS: list = []


@dataclass(frozen=True, slots=True, eq=False)
class SpanKey:
    binding: object
    pin: tuple
    span_offset: int
    span_size: int
    span_sha256: str
    write_offset: int
    sequence: int


@dataclass(frozen=True, slots=True, eq=False)
class WriteSpan:
    key: SpanKey
    body: bytes
    body_offset: int


@dataclass(frozen=True, slots=True, eq=False)
class WriteAcknowledgement:
    key: SpanKey
    original_return: object


@dataclass(frozen=True, slots=True, eq=False)
class MemberConsumer:
    binding: object
    write: Callable[[WriteSpan], WriteAcknowledgement]


@dataclass(eq=False, slots=True)
class _Ledger:
    state: original._State
    records: list = field(default_factory=list)
    attempts: list = field(default_factory=list)
    failed: bool = False
    affinity: tuple = field(
        default_factory=lambda: (os.getpid(), threading.get_ident())
    )


@dataclass(eq=False, slots=True)
class _Record:
    ledger: _Ledger
    archive: object
    item: object
    pin: tuple
    pin_snapshot: tuple
    consumer: MemberConsumer
    binding: object
    write: Callable
    affinity: tuple
    item_snapshot: tuple
    phase: str = "enrolled"
    active_span: WriteSpan | None = None
    in_write: bool = False
    digest_return: object = None
    reader_invocation: str = "not_invoked"

    @property
    def acknowledged_bytes(self):
        return sum(
            attempt.validated_count
            for attempt in self.ledger.attempts
            if attempt.record is self and attempt.validated_count is not None
        )


@dataclass(eq=False, slots=True)
class _Attempt:
    record: _Record
    key: SpanKey
    invocation: str = "not_invoked"
    original_return: object = None
    validated_count: int | None = None

    @property
    def accepted(self):
        return self.validated_count is not None


@dataclass(frozen=True, slots=True, eq=False)
class ProvisionalMemberConsumption:
    original_pin: tuple
    original_state: original._State
    original_cursor: original._MemberCursor
    original_attempts: tuple
    original_digest_return: str
    acknowledged_bytes: int
    provisional: bool = True
    enclosing_flow_verified: bool = False
    physical_writes_verified: bool = False
    authorizes_installation: bool = False
    cleanup: str = "not_observed"


class MemberConsumptionError(RuntimeError):
    def __init__(self, supplied, record, cause):
        super().__init__("private_original_member_consumption_failed")
        self.original_supplied = supplied
        self.original_state = supplied[0]
        self.phase = "selection" if record is None else record.phase
        self.original_attempts = () if record is None else _attempts(record)
        self.active_span = None if record is None else record.active_span
        self.acknowledged_bytes = 0 if record is None else record.acknowledged_bytes
        self.original_digest_return = None if record is None else record.digest_return
        self.reader_invocation = (
            "not_invoked" if record is None else record.reader_invocation
        )
        self.original_cursor = (
            vars(supplied[0]).get("_original_member_cursor")
            if type(supplied[0]) is original._State
            else None
        )
        self.primary_cause = cause
        self.provisional = True
        self.cleanup = "not_observed"
        layer = next((layer for layer in _LAYERS if layer.state is supplied[0]), None)
        self.layer_stopped = False if layer is None else layer.failed
        self.original_layer_attempts = () if layer is None else tuple(layer.attempts)
        self.original_layer_records = () if layer is None else tuple(layer.records)
        self.authorizes_retry = self.authorizes_installation = False


def _attempts(record):
    return tuple(a for a in record.ledger.attempts if a.record is record)


def _current(record):
    state = record.ledger.state
    if (
        record.affinity != (os.getpid(), threading.get_ident())
        or record.ledger.failed
        or original._read_member is not _READ
        or original._MemberCursor is not _CURSOR
        or record.consumer.binding is not record.binding
        or record.consumer.write is not record.write
        or record.pin != record.pin_snapshot
        or state.archive is not record.archive
        or state.original_item is not record.item
        or original._snapshot(record.item) != record.item_snapshot
    ):
        raise ValueError("original_member_consumption_binding_changed")


def _key_snapshot(key):
    return (
        key.binding,
        key.pin,
        key.span_offset,
        key.span_size,
        key.span_sha256,
        key.write_offset,
        key.sequence,
    )


class _ConsumerFeed:
    def __init__(self, record):
        self.record = record
        self.total = 0
        state = record.ledger.state
        self.checksum = (
            original._ChecksumLines(state)
            if record.item.name == state.root + "/SHA256SUMS"
            else None
        )

    def feed(self, body):
        record, state = self.record, self.record.ledger.state
        _current(record)
        if (
            record.in_write
            or record.active_span is not None
            or type(body) is not bytes
            or not 0 < len(body) <= original.WINDOW
            or state.last_return is not body
            or state.original_read_return is not body
            or state.member_bytes != self.total + len(body)
        ):
            raise ValueError("original_consumption_span_required")
        digest = hashlib.sha256(body).hexdigest()
        offset = 0
        while offset < len(body):
            record.phase = "sink_preflight"
            _current(record)
            key = SpanKey(
                record.binding,
                record.pin,
                self.total,
                len(body),
                digest,
                self.total + offset,
                len(record.ledger.attempts),
            )
            snapshot = _key_snapshot(key)
            span = WriteSpan(key, body, offset)
            record.active_span = span
            if len(record.ledger.attempts) >= WRITE_CALLS:
                raise ValueError("original_consumption_write_capacity")
            attempt = _Attempt(record, key)
            record.ledger.attempts.append(
                attempt
            )  # Charge before dispatch, never refund.
            record.phase, attempt.invocation = "sink_write", "unknown"
            record.in_write = True
            try:
                returned = record.write(span)
                attempt.original_return = returned  # Preserve before receiving checks.
                attempt.invocation = "returned"
            finally:
                record.in_write = False
            record.phase = "sink_receiving"
            _current(record)
            if (
                record.active_span is not span
                or span.key is not key
                or span.body is not body
                or span.body_offset != offset
                or type(span.body_offset) is not int
                or type(key) is not SpanKey
                or type(key.span_sha256) is not str
                or any(
                    type(value) is not int
                    for value in (
                        key.span_offset,
                        key.span_size,
                        key.write_offset,
                        key.sequence,
                    )
                )
                or _key_snapshot(key) != snapshot
                or key.binding is not record.binding
                or key.pin is not record.pin
                or state.last_return is not body
                or state.original_read_return is not body
                or state.member_bytes != self.total + len(body)
                or type(returned) is not WriteAcknowledgement
                or returned.key is not key
                or type(returned.original_return) is not int
                or not 0 < returned.original_return <= len(body) - offset
            ):
                raise ValueError("original_consumption_acknowledgement_required")
            count = returned.original_return
            attempt.validated_count = count  # Sole acknowledged-prefix commit point.
            offset += count
            record.active_span = None
        self.total += len(body)
        if self.checksum is not None:
            self.checksum.feed(body)

    def finish(self):
        record, state = self.record, self.record.ledger.state
        _current(record)
        if (
            record.active_span is not None
            or self.total != record.pin[1]
            or record.acknowledged_bytes != self.total
            or state.member_bytes != self.total
            or state.last_return != b""
        ):
            raise ValueError("original_consumption_eof_required")
        if self.checksum is not None:
            self.checksum.finish()


def consume_member(state, archive, item, pin, consumer):
    """One original read/finish/release call; only sink claims are accepted.

    Caller must separately admit and qualify any physical write provider. This
    helper does not mount itself into the scanner or accept enclosing flow.
    """
    record = None
    supplied = state, archive, item, pin, consumer
    try:
        if (
            type(state) is not original._State
            or type(archive) is not original.tarfile.TarFile
            or state.archive is not archive
            or state.original_item is not item
            or type(pin) is not tuple
            or len(pin) != 3
            or type(pin[0]) is not str
            or pin[0] != item.name
            or type(pin[1]) is not int
            or pin[1] != item.size
            or type(pin[2]) is not str
            or re.fullmatch("[0-9a-f]{64}", pin[2]) is None
            or type(consumer) is not MemberConsumer
            or not callable(consumer.write)
        ):
            raise ValueError("explicit_original_member_consumption_required")
        ledger = next((layer for layer in _LAYERS if layer.state is state), None)
        if ledger is None:
            if len(_LAYERS) >= LAYERS:
                raise ValueError("original_consumption_layer_capacity")
            ledger = _Ledger(state)
            _LAYERS.append(ledger)
        if (
            ledger.failed
            or ledger.affinity != (os.getpid(), threading.get_ident())
            or len(ledger.records) >= original.FILES
        ):
            raise ValueError("original_consumption_layer_stopped_or_full")
        if any(r.item is item for r in ledger.records):
            raise ValueError("original_member_consumption_already_spent")
        record = _Record(
            ledger,
            archive,
            item,
            pin,
            tuple(pin),
            consumer,
            consumer.binding,
            consumer.write,
            (os.getpid(), threading.get_ident()),
            original._snapshot(item),
        )
        ledger.records.append(record)
        _current(record)
        record.phase, record.reader_invocation = "original_member_read", "unknown"
        returned = _READ(state, archive, item, _ConsumerFeed(record))
        record.digest_return, record.reader_invocation = returned, "returned"
        record.phase = "terminal_receiving"
        _current(record)
        cursor = vars(state).get("_original_member_cursor")
        if (
            type(cursor) is not _CURSOR
            or cursor.state is not state
            or cursor.item is not item
            or cursor.archive is not archive
            or not cursor.finished
            or not cursor.eof
            or not cursor.release_attempted
            or not cursor.close_returned
            or cursor.original_close_return is not None
            or type(cursor.stream) is not original.tarfile.ExFileObject
            or cursor.stream.closed is not True
            or type(returned) is not str
            or returned != pin[2]
            or record.acknowledged_bytes != pin[1]
            or record.active_span is not None
        ):
            raise ValueError("original_consumption_terminal_required")
        record.phase = "provisional"
        return ProvisionalMemberConsumption(
            pin, state, cursor, _attempts(record), returned, record.acknowledged_bytes
        )
    except (
        BaseException
    ) as cause:  # Preserve original interrupted reader/sink and cleanup errors.
        if record is not None:
            record.ledger.failed = True
        raise MemberConsumptionError(supplied, record, cause) from cause
