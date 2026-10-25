"""Process-local closed value receipts; neither IO nor reconstructed custody.

Only the original observing owner selects the frozen value types. Snapshots
are detached values. A receipt remains tied to its issuing pool/process/thread.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import threading
import zlib
from dataclasses import dataclass, fields, is_dataclass
from weakref import WeakKeyDictionary

from ._staging_guard_history import _low_memory_block, value_seal

BODY_LIMIT = 8 * 1024**2
STORED_LIMIT = 32 * 1024**2
CALL_LIMIT = 65536
_PAGE_BYTES = 32 * 1024
_BODY_METADATA = struct.Struct("<QIH")
_BODY_RECORD_BYTES = _BODY_METADATA.size + 96


@dataclass(frozen=True, slots=True)
class _SharedBody:
    offset: int
    length: int
    digest: bytes


class _BodyBacking:
    """Append-only canonical bytes, bounded pages, no IO or discarded receipts.

    A receipt names a byte range, not a mutable page projection. Closing an
    active page changes representation only; its exact bytes and every prior
    range remain sealed. Failed appends poison further publication, not reads.
    """

    def __init__(self):
        self.affinity = os.getpid(), threading.get_ident()
        self.state = (), bytearray()
        self.extent = self.charged = 0
        self.pending = None
        self.failure = None
        self.cache = {}

    @staticmethod
    def _inflate(page):
        size, encoded, seal = page
        if (
            type(size) is not int
            or not 0 < size <= _PAGE_BYTES
            or type(encoded) is not bytes
            or not 0 < len(encoded) <= size + 1024
            or hashlib.sha256(size.to_bytes(4, "little") + encoded).digest() != seal
        ):
            raise ValueError("closed_value_backing_page_changed")
        decoder = zlib.decompressobj()
        body = decoder.decompress(encoded, size + 1)
        if (
            len(body) != size
            or not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
        ):
            raise ValueError("complete_closed_value_backing_page_required")
        return body

    def append(self, body):
        if self.affinity != (os.getpid(), threading.get_ident()):
            raise ValueError("closed_value_backing_affinity")
        if self.pending is not None or self.failure is not None:
            raise ValueError("closed_value_backing_capture_spent")
        if type(body) is not bytes or not 0 < len(body) <= BODY_LIMIT:
            raise ValueError("bounded_closed_value_backing_body_required")
        location = _SharedBody(self.extent, len(body), hashlib.sha256(body).digest())
        self.pending = body
        try:
            cursor = 0
            while cursor < len(body):
                pages, active = self.state
                if len(active) == _PAGE_BYTES:
                    original = bytes(active)
                    encoded = _low_memory_block(
                        original, window_bits=15, compression_level=9
                    )
                    page = (
                        len(original),
                        encoded,
                        hashlib.sha256(
                            len(original).to_bytes(4, "little") + encoded
                        ).digest(),
                    )
                    if self._inflate(page) != original:
                        raise ValueError("closed_value_backing_roundtrip_required")
                    if self.charged + len(encoded) + _PAGE_BYTES > STORED_LIMIT:
                        raise ValueError("closed_value_backing_capacity")
                    self.charged += len(encoded)  # Never refund failed captures.
                    self.state = pages + (page,), bytearray()
                    pages, active = self.state
                size = min(_PAGE_BYTES - len(active), len(body) - cursor)
                active.extend(memoryview(body)[cursor : cursor + size])
                cursor += size
            self.extent += len(body)
            self.pending = None
            return location
        except BaseException as cause:
            self.failure = cause
            raise

    def _parts(self, location):
        if self.affinity != (os.getpid(), threading.get_ident()):
            raise ValueError("closed_value_backing_affinity")
        if (
            type(location) is not _SharedBody
            or type(location.offset) is not int
            or type(location.length) is not int
            or not 0 <= location.offset < CALL_LIMIT * BODY_LIMIT
            or not 0 < location.length <= BODY_LIMIT
            or location.offset + location.length > self.extent
            or type(location.digest) is not bytes
            or len(location.digest) != 32
        ):
            raise ValueError("closed_value_backing_location_changed")
        pages, active = self.state
        offset, remaining = location.offset, location.length
        while remaining:
            index, start = divmod(offset, _PAGE_BYTES)
            if index == len(pages):
                source = active
            elif index < len(pages):
                page = pages[index]
                cached = self.cache.get(index)
                if cached is None or cached[0] is not page:
                    if len(self.cache) >= 2:
                        self.cache.pop(next(iter(self.cache)))
                    source = self._inflate(page)
                    self.cache[index] = page, source
                else:
                    source = cached[1]
            else:
                raise ValueError("closed_value_backing_range_missing")
            size = min(remaining, len(source) - start)
            if size <= 0:
                raise ValueError("closed_value_backing_range_truncated")
            yield memoryview(source)[start : start + size]
            offset, remaining = offset + size, remaining - size

    def validate(self, location):
        """Validate the same complete range without another body-sized copy."""
        digest = hashlib.sha256()
        obtained = 0
        for part in self._parts(location):
            digest.update(part)
            obtained += len(part)
        if obtained != location.length or digest.digest() != location.digest:
            raise ValueError("closed_value_backing_body_changed")
        return obtained

    def read(self, location):
        result = bytearray()
        for part in self._parts(location):
            result.extend(part)
        if hashlib.sha256(result).digest() != location.digest:
            raise ValueError("closed_value_backing_body_changed")
        return bytes(result)


class _ValueReceipt:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("original_closed_value_owner_required")

    def __copy__(self):
        raise TypeError("receipt_cannot_be_copied")

    def __deepcopy__(self, memo):
        raise TypeError("receipt_cannot_be_copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("receipt_is_process_local")


class _ValueCaptureError(RuntimeError):
    def __init__(self, original, prefix, frame, cause):
        super().__init__("closed_value_capture_incomplete")
        self.original_value = original
        self.original_prefix = prefix
        self.original_frame = frame
        self.original_cause = cause
        self.authorizes_retry = False


class _ClosedValueEncoder(json.JSONEncoder):
    """One original encoder type; no per-capture class/function cycle."""

    def __init__(self, pool, **kwargs):
        self.pool = pool
        super().__init__(**kwargs)

    def default(self, o):
        item = o
        kind = type(item)
        if kind not in self.pool.types:
            raise TypeError("unsupported_closed_value_type")
        return {
            "t": self.pool.types.index(kind),
            "f": [getattr(item, field.name) for field in fields(kind)],
        }


def _closed_float(value):
    raise TypeError("unsupported_closed_value_type")


class _ClosedValuePool:
    def __init__(self, types, *, shared_bodies=False, receipt_type=_ValueReceipt):
        if (
            type(types) is not tuple
            or not types
            or any(
                not isinstance(t, type)
                or not is_dataclass(t)
                or not getattr(
                    getattr(t, "__dataclass_params__", None), "frozen", False
                )
                for t in types
            )
        ):
            raise TypeError("closed_original_value_types_required")
        self.types = types
        self.affinity = os.getpid(), threading.get_ident()
        self.records = WeakKeyDictionary()
        self.calls = self.charged_bytes = 0
        self._encoder = None
        self._encoding = False
        if type(shared_bodies) is not bool:
            raise TypeError("explicit_closed_value_storage_profile_required")
        if (
            not isinstance(receipt_type, type)
            or not issubclass(receipt_type, _ValueReceipt)
            or (shared_bodies and len(types) > 65536)
        ):
            raise TypeError("original_closed_receipt_type_required")
        self.receipt_type = receipt_type
        self.backing = _BodyBacking() if shared_bodies else None

    def _current(self):
        if self.affinity != (os.getpid(), threading.get_ident()):
            raise ValueError("closed_value_receipt_affinity")

    def _body(self, value):
        # Reuse the original stdlib streaming engine rather than manufacturing
        # a mutually recursive encoder graph for every observation. No JSON
        # grammar or one-shot/full-string encoder is duplicated here.
        if self._encoding:
            raise ValueError("closed_value_capture_reentrant")
        if self._encoder is None:
            encoder = _ClosedValueEncoder(
                self, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            )
            self._encoder = getattr(json.encoder, "_make_iterencode")(  # noqa: B009 -- stdlib stub omits this original engine
                {},
                encoder.default,
                json.encoder.encode_basestring,
                None,
                _closed_float,
                ":",
                ",",
                False,
                False,
                False,
            )
        self._encoding = True
        body = bytearray()
        try:
            for chunk in self._encoder(value, 0):
                part = chunk.encode("utf-8", "strict")
                if len(body) + len(part) > BODY_LIMIT:
                    raise _ValueCaptureError(
                        value, body, part, ValueError("closed_value_body_capacity")
                    )
                body.extend(part)
            return bytes(body)
        except BaseException:
            # Failed generator frames retain their original markers and cause.
            # A later independent capture gets a fresh engine, never a retry.
            self._encoder = None
            raise
        finally:
            self._encoding = False

    def _decode(self, body):
        def integer(text):
            if len(text) > 81:
                raise ValueError("closed_value_integer_capacity")
            value = int(text)
            if value.bit_length() > 264:
                raise ValueError("closed_value_integer_capacity")
            return value

        def value(item, depth, recur):
            if depth > 32:
                raise ValueError("closed_value_depth_capacity")
            if item is None or type(item) in (bool, int, str):
                return item
            if type(item) is list:
                return tuple(recur(part, depth + 1, recur) for part in item)
            if type(item) is not dict or set(item) != {"t", "f"}:
                raise ValueError("closed_value_frame_required")
            index, args = item["t"], item["f"]
            if (
                type(index) is not int
                or not 0 <= index < len(self.types)
                or type(args) is not list
            ):
                raise ValueError("original_closed_value_type_required")
            kind = self.types[index]
            if len(args) != len(fields(kind)):
                raise ValueError("complete_closed_value_fields_required")
            return kind(*(recur(part, depth + 1, recur) for part in args))

        # Recursion is an explicit argument, not a self-referential closure.
        # Original failure frames/causes remain intact.
        return value(json.loads(body, parse_int=integer), 0, value)

    def capture(self, value):
        prefix = frame = None
        try:
            self._current()
            if self.calls >= CALL_LIMIT or type(value) not in self.types:
                raise ValueError("closed_value_capture_capacity_or_type")
            self.calls += 1  # Failed attempts never refund capture capacity.
            original_seal = value_seal(value)
            prefix = self._body(value)
            if value_seal(self._decode(prefix)) != original_seal:
                raise ValueError("complete_closed_value_roundtrip_required")
            frame = _low_memory_block(prefix)
            if self.charged_bytes + len(frame) > STORED_LIMIT:
                raise ValueError("closed_value_storage_capacity")
            self.charged_bytes += len(frame)
            if self.backing is not None:
                # Keep the original per-value compression charge unchanged;
                # shared storage cannot discount occurrence/attempt capacity.
                frame = self.backing.append(prefix)
            length = len(prefix)
            seal = self._seal(type(value), frame, length, original_seal)
            ref = object.__new__(self.receipt_type)
            if self.backing is not None:
                if type(frame) is not _SharedBody:
                    raise ValueError("original_shared_body_location_required")
                self.records[ref] = (
                    _BODY_METADATA.pack(
                        frame.offset, length, self.types.index(type(value))
                    )
                    + original_seal
                    + frame.digest
                    + seal
                )
            else:
                self.records[ref] = type(value), frame, length, seal, original_seal
            self.snapshot(ref)  # Verify exact compressed readback before issue.
            return ref
        except BaseException as cause:
            raise _ValueCaptureError(value, prefix, frame, cause) from cause

    @staticmethod
    def _seal(kind, frame, length, original_seal):
        if type(frame) is _SharedBody:
            frame = (
                b"original_shared_closed_body_v1:"
                + frame.offset.to_bytes(8, "little")
                + frame.length.to_bytes(4, "little")
                + frame.digest
            )
        return hashlib.sha256(
            id(kind).to_bytes(8, "little")
            + length.to_bytes(4, "little")
            + original_seal
            + frame
        ).digest()

    def _record(self, ref):
        self._current()
        if type(ref) is not self.receipt_type or ref not in self.records:
            raise ValueError("original_closed_value_receipt_required")
        record = self.records[ref]
        if self.backing is not None:
            if type(record) is not bytes or len(record) not in (
                _BODY_RECORD_BYTES,
                _BODY_RECORD_BYTES + 32,
            ):
                raise ValueError("original_closed_value_metadata_required")
            offset, length, kind_index = _BODY_METADATA.unpack_from(record)
            if kind_index >= len(self.types) or not 0 < length <= BODY_LIMIT:
                raise ValueError("closed_value_metadata_changed")
            start = _BODY_METADATA.size
            kind, original_seal = self.types[kind_index], record[start : start + 32]
            frame = _SharedBody(offset, length, record[start + 32 : start + 64])
            seal = record[start + 64 : start + 96]
        else:
            kind, frame, length, seal, original_seal = record
        if type(frame) is _SharedBody:
            if self.backing is None:
                raise ValueError("original_closed_value_backing_required")
            self.backing.validate(frame)
        if (
            kind not in self.types
            or not (
                (
                    type(frame) is bytes
                    and self.backing is None
                    and 0 < len(frame) <= BODY_LIMIT + 1024
                )
                or (
                    type(frame) is _SharedBody
                    and self.backing is not None
                    and frame.length == length
                )
            )
            or type(length) is not int
            or not 0 < length <= BODY_LIMIT
            or type(original_seal) is not bytes
            or len(original_seal) != 32
            or self._seal(kind, frame, length, original_seal) != seal
        ):
            raise ValueError("closed_value_receipt_changed")
        return kind, frame, length, seal, original_seal

    def seal(self, ref):
        return self._record(ref)[4]

    def snapshot(self, ref):
        kind, frame, length, _, seal = self._record(ref)
        if type(frame) is _SharedBody:
            if self.backing is None:
                raise ValueError("original_closed_value_backing_required")
            body = self.backing.read(frame)
        else:
            if type(frame) is not bytes:
                raise ValueError("original_closed_value_frame_required")
            decoder = zlib.decompressobj()
            body = decoder.decompress(frame, length + 1)
            if (
                len(body) != length
                or not decoder.eof
                or decoder.unused_data
                or decoder.unconsumed_tail
            ):
                raise ValueError("complete_closed_value_frame_required")
        returned = self._decode(body)
        if type(returned) is not kind or value_seal(returned) != seal:
            raise ValueError("closed_value_snapshot_changed")
        return returned
