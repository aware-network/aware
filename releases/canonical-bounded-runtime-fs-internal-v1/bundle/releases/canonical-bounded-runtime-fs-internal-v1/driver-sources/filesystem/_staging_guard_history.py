"""Lossless, non-authorizing historical values owned by the staging provider.

The provider still returns each actual syscall result to its live guard. This
store records complete immutable stat *values*, not live observation rights or
original Python object identity. Each call occurrence remains separate. Expected
EBADF probe values retain fields/locations without live frames; unexpected
errors remain original references. No IO or exception replay.
"""

from __future__ import annotations

import errno
import hashlib
import math
import os
import struct
import weakref
import zlib
from array import array
from dataclasses import dataclass, fields, is_dataclass
from itertools import islice
from uuid import uuid4

PROFILE = "aware.filesystem.recorded-staging-history.v1"
COMPRESSED_PROFILE = "aware.filesystem.compressed-staging-history.v1"
_BLOCK_BYTES = 65536
MAX_EVENTS = 2_000_000
MAX_VALUES = 200_000
MAX_STAT_BYTES = 32 * 1024**2
_CELL = struct.Struct("<I")
_FLOAT = struct.Struct("<d")
_STAT_NAMES = tuple(
    sorted(name for name in dir(os.stat_result) if name.startswith("st_"))
)
_RECORDS = weakref.WeakKeyDictionary()


class HistoryCaptureError(RuntimeError):
    def __init__(self, entry, prefix_count, cause):
        super().__init__("original_staging_history_capture_incomplete")
        self.original_entry = entry
        self.committed_prefix_count = prefix_count
        self.original_cause = cause
        self.authorizes_retry = False


@dataclass(frozen=True, slots=True)
class RecordedClosedProbe:
    """Historical expected EBADF value, never a throwable/live observation.

    Keeps all supported exception fields and traceback locations. Python frame
    objects and their caller-local byte buffers are not historical authority.
    Unexpected errors, causes or attached state stay with the original failure.
    """

    descriptor: int
    arguments: tuple
    number: int
    description: str
    filename: object
    filename2: object
    suppress_context: bool
    traceback_locations: tuple
    authorizes_observation: bool = False


def _closed_probe(error, descriptor):
    if (
        type(descriptor) is not int
        or descriptor < 0
        or type(error) is not OSError
        or error.errno != errno.EBADF
        or error.__cause__ is not None
        or error.__context__ is not None
        or vars(error)
        or error.args != (errno.EBADF, error.strerror)
        or type(error.strerror) is not str
        or error.filename is not None
        or error.filename2 is not None
    ):
        raise ValueError("complete_plain_expected_close_probe_required")
    rows = []
    trace = error.__traceback__
    while trace is not None:
        if len(rows) >= 16:
            raise ValueError("bounded_original_close_probe_trace_required")
        code = trace.tb_frame.f_code
        row = (
            code.co_filename,
            code.co_name,
            code.co_qualname,
            code.co_firstlineno,
            trace.tb_lineno,
            trace.tb_lasti,
        )
        if sum(len(value.encode("utf-8")) for value in row[:3]) > 8192:
            raise ValueError("bounded_original_close_probe_location_required")
        rows.append(row)
        trace = trace.tb_next
    return RecordedClosedProbe(
        descriptor,
        error.args,
        errno.EBADF,
        error.strerror,
        error.filename,
        error.filename2,
        error.__suppress_context__,
        tuple(rows),
    )


def _stat_bytes(value):
    if os.name != "posix" or os.stat_result.n_fields != 19:
        raise ValueError("qualified_stat_value_layout_required")
    if (
        tuple(sorted(name for name in dir(value) if name.startswith("st_")))
        != _STAT_NAMES
    ):
        raise ValueError("complete_stat_attribute_layout_required")
    body = bytearray((len(value), len(_STAT_NAMES)))
    for item in (*value, *(getattr(value, name) for name in _STAT_NAMES)):
        if type(item) is int:
            count = max(1, (item.bit_length() + 8) // 8)
            if count > 17:
                raise ValueError("bounded_original_stat_integer_required")
            body.append(count)
            body.extend(item.to_bytes(count, "little", signed=True))
        elif type(item) is float and math.isfinite(item):
            body.append(255)
            body.extend(_FLOAT.pack(item))
        else:
            raise ValueError("complete_numeric_stat_values_required")
    return bytes(body)


def _stat_from_bytes(body):
    if len(body) < 2 or body[:2] != bytes(
        (os.stat_result.n_sequence_fields, len(_STAT_NAMES))
    ):
        raise ValueError("qualified_recorded_stat_layout_required")
    values, offset = [], 2
    for _ in range(body[0] + body[1]):
        if offset >= len(body):
            raise ValueError("complete_recorded_stat_required")
        tag = body[offset]
        offset += 1
        count = 8 if tag == 255 else tag
        if not (tag == 255 or 1 <= tag <= 17) or offset + count > len(body):
            raise ValueError("bounded_recorded_stat_scalar_required")
        chunk = body[offset : offset + count]
        values.append(
            _FLOAT.unpack(chunk)[0]
            if tag == 255
            else int.from_bytes(chunk, "little", signed=True)
        )
        offset += count
    if offset != len(body):
        raise ValueError("recorded_stat_trailing_bytes")
    return os.stat_result(
        values[: body[0]], dict(zip(_STAT_NAMES, values[body[0] :], strict=True))
    )


def _stat_storage_key(body):
    # Index only: full canonical bytes decide equality, including collisions.
    return hash(body)


_STAT_PAGE_BYTES = 32768
_STAT_READ_PAGES = 4


class _PagedSeals:
    """The same complete seal byte stream, without a whole-stream realloc."""

    def __init__(self, *, authenticated=False):
        if type(authenticated) is not bool:
            raise ValueError("explicit_original_seal_storage_required")
        self.pages = []
        self.length = 0
        self.pending = None
        self.failure = None
        self.authenticated = authenticated
        self.page_seals = []
        self.active_seal = 0, hashlib.sha256()

    def _verify_page(self, index):
        if not self.authenticated:
            return self.pages[index]
        page = self.pages[index]
        if index < len(self.page_seals):
            length, seal = _STAT_PAGE_BYTES, self.page_seals[index]
            if len(page) != length:
                raise ValueError("original_seal_page_changed")
        else:
            length, digest = self.active_seal
            seal = digest.digest()
        if len(page) < length:
            raise ValueError("original_seal_page_changed")
        snapshot = bytes(memoryview(page)[:length])
        if hashlib.sha256(snapshot).digest() != seal:
            raise ValueError("original_seal_page_changed")
        return snapshot

    def __len__(self):
        return self.length

    def extend(self, body):
        if self.pending is not None or self.failure is not None:
            raise ValueError("original_seal_capture_spent")
        if type(body) is not bytes or self.length + len(body) > MAX_VALUES * 32:
            raise ValueError("bounded_original_seal_bytes_required")
        self.pending = body
        try:
            position = 0
            while position < len(body):
                if not self.pages or len(self.pages[-1]) == _STAT_PAGE_BYTES:
                    if self.authenticated and self.pages:
                        self._verify_page(len(self.pages) - 1)
                        self.page_seals.append(self.active_seal[1].digest())
                    self.pages.append(bytearray())
                    if self.authenticated:
                        self.active_seal = 0, hashlib.sha256()
                page = self.pages[-1]
                size = min(_STAT_PAGE_BYTES - len(page), len(body) - position)
                fragment = memoryview(body)[position : position + size]
                digest = None
                if self.authenticated:
                    self._verify_page(len(self.pages) - 1)
                    digest = self.active_seal[1].copy()
                    digest.update(fragment)
                page.extend(fragment)
                if self.authenticated:
                    if digest is None:
                        raise ValueError("original_seal_profile_changed")
                    self.active_seal = self.active_seal[0] + size, digest
                self.length += size
                position += size
            self.pending = None
        except BaseException as cause:
            self.failure = cause
            raise

    def __getitem__(self, key):
        if type(key) is int:
            key = key if key >= 0 else self.length + key
            if not 0 <= key < self.length:
                raise IndexError(key)
            page, offset = divmod(key, _STAT_PAGE_BYTES)
            source = self._verify_page(page)
            return source[offset]
        if type(key) is not slice:
            raise TypeError("original_seal_range_required")
        start, stop, step = key.indices(self.length)
        if step != 1 or stop - start > 32:
            raise ValueError("bounded_original_seal_range_required")
        result = bytearray()
        while start < stop:
            page, offset = divmod(start, _STAT_PAGE_BYTES)
            source = self._verify_page(page)
            size = min(stop - start, _STAT_PAGE_BYTES - offset)
            result.extend(source[offset : offset + size])
            start += size
        return bytes(result)


class _ValueRows:
    """Append-only packed locators without a whole-index realloc peak.

    All pages stay retained. A new page bounds the next allocation; it does
    not refund history, drop raw references or change the parent value limit.
    """

    itemsize = 8
    PAGE_ROWS = 4096

    def __init__(self, *, raw=False):
        if type(raw) is not bool:
            raise ValueError("explicit_original_value_page_kind_required")
        self.raw = raw
        self.pages = []
        self.length = 0

    def __len__(self):
        return self.length

    def append(self, value):
        page, offset = divmod(self.length, self.PAGE_ROWS)
        if page == len(self.pages):
            rows = [] if self.raw else array("Q")
            if not self.raw and getattr(rows, "itemsize", None) != self.itemsize:
                raise ValueError("qualified_original_value_layout_required")
            self.pages.append(rows)
        rows = self.pages[page]
        if len(rows) != offset:
            raise ValueError("original_value_page_prefix_changed")
        rows.append(value)
        self.length += 1

    def _coordinate(self, index):
        if type(index) is not int:
            raise TypeError("original_value_index_required")
        index = index if index >= 0 else self.length + index
        if not 0 <= index < self.length:
            raise IndexError(index)
        return divmod(index, self.PAGE_ROWS)

    def __getitem__(self, index):
        page, offset = self._coordinate(index)
        return self.pages[page][offset]

    def __setitem__(self, index, value):
        page, offset = self._coordinate(index)
        self.pages[page][offset] = value


class _ValueTable:
    """Exact original rows: packed stat locators plus strong raw references.

    Only private bookkeeping tags are reconstructed. A raw provider object is
    never copied or replaced, and failed enrollment never refunds capacity.
    """

    RAW = 1 << 63

    def __init__(self):
        self.rows = _ValueRows()
        if self.rows.itemsize != 8:
            raise ValueError("qualified_original_value_layout_required")
        self.originals = _ValueRows(raw=True)
        self.pending = None
        self.failure = None

    def __len__(self):
        return len(self.rows)

    def append(self, value):
        if self.pending is not None or self.failure is not None:
            raise ValueError("original_value_table_capture_spent")
        if len(self) >= MAX_VALUES:
            raise ValueError("history_value_capacity")
        self.pending = value
        try:
            if type(value) is int and 0 <= value < 2**48:
                self.rows.append(value)
            elif type(value) is tuple and len(value) == 2 and value[0] == "original":
                index = len(self.originals)
                self.originals.append(value[1])
                self.rows.append(self.RAW | index)
            else:
                raise ValueError("original_history_row_required")
            self.pending = None
        except BaseException as cause:
            self.failure = cause
            raise

    def __getitem__(self, index):
        if type(index) is not int:
            raise TypeError("original_value_index_required")
        value = self.rows[index]
        if value & self.RAW:
            row = value & (self.RAW - 1)
            if row >= len(self.originals):
                raise ValueError("original_value_reference_missing")
            return "original", self.originals[row]
        return value

    def __setitem__(self, index, value):
        if type(index) is not int or type(value) is not int or not 0 <= value < 2**48:
            raise ValueError("original_stat_locator_required")
        if self.rows[index] & self.RAW:
            raise ValueError("original_provider_reference_cannot_be_replaced")
        self.rows[index] = value


class _StatBlocks:
    """Lossless closed values; no IO, discarded rows or new observation rights."""

    def __init__(self, *, compact_integrity=False):
        if type(compact_integrity) is not bool:
            raise ValueError("explicit_original_stat_integrity_required")
        self.state = (), bytearray()
        self.compact_integrity = compact_integrity
        self.seals = _PagedSeals(authenticated=compact_integrity)
        self.active_seal = 0, hashlib.sha256()
        self.cache = {}
        self.failure: tuple[object, bytes, BaseException] | None = None

    @staticmethod
    def _inflate(block):
        size, encoded, seal = block
        if (
            type(size) is not int
            or not 0 < size <= _STAT_PAGE_BYTES
            or type(encoded) is not bytes
            or not 0 < len(encoded) <= size + 1024
            or type(seal) is not bytes
            or len(seal) not in (32, 64)
            or hashlib.sha256(size.to_bytes(4, "little") + encoded + seal[32:]).digest()
            != seal[:32]
        ):
            raise ValueError("original_stat_block_changed")
        decoder = zlib.decompressobj()
        body = decoder.decompress(encoded, size + 1)
        if (
            len(body) != size
            or not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
            or (len(seal) == 64 and hashlib.sha256(body).digest() != seal[32:])
        ):
            raise ValueError("complete_original_stat_block_required")
        return body

    @staticmethod
    def _row_seal(index, locator, body):
        return hashlib.sha256(
            index.to_bytes(4, "little") + locator.to_bytes(8, "little") + body
        ).digest()

    def append(self, index, body):
        if self.failure is not None:
            raise ValueError("original_stat_block_capture_spent") from self.failure[2]
        if (
            type(index) is not int
            or not 0 <= index < MAX_VALUES
            or type(body) is not bytes
            or not 0 < len(body) <= 1024
        ):
            raise ValueError("bounded_original_stat_block_input_required")
        blocks, active = self.state
        if self.compact_integrity:
            self._verify_active()
            if len(active) != self.active_seal[0]:
                raise ValueError("unpublished_original_stat_tail_retained")
        if len(active) + len(body) > _STAT_PAGE_BYTES:
            raw_seal = self.active_seal[1].digest() if self.compact_integrity else b""
            original = bytes(active)
            if self.compact_integrity and hashlib.sha256(original).digest() != raw_seal:
                raise ValueError("original_stat_row_or_locator_changed")
            encoded = _low_memory_block(original, window_bits=15, compression_level=9)
            sealed = (
                len(original),
                encoded,
                hashlib.sha256(
                    len(original).to_bytes(4, "little") + encoded + raw_seal
                ).digest()
                + raw_seal,
            )
            if self._inflate(sealed) != original:
                raise ValueError("original_stat_block_roundtrip_required")
            # One representation commit. Existing locators still name exactly
            # the same block/offset across active-to-sealed transition.
            self.state = blocks + (sealed,), bytearray()
            if self.compact_integrity:
                self.active_seal = 0, hashlib.sha256()
            blocks, active = self.state
        if len(blocks) > MAX_STAT_BYTES // _STAT_PAGE_BYTES:
            raise ValueError("original_stat_block_capacity")
        offset = len(active)
        locator = len(blocks) << 32 | offset << 16 | len(body)
        # Keep unacknowledged tails on failure; never truncate or refund.
        digest = None
        if self.compact_integrity:
            digest = self.active_seal[1].copy()
            digest.update(body)
        active.extend(body)
        if self.compact_integrity:
            if digest is None:
                raise ValueError("original_stat_integrity_profile_changed")
            self.active_seal = len(active), digest
        width = 8 if self.compact_integrity else 32
        slot = index * width
        if len(self.seals) > slot:
            raise ValueError("unpublished_original_stat_seal_retained")
        self.seals.extend(b"\0" * (slot - len(self.seals)))
        self.seals.extend(
            locator.to_bytes(8, "little")
            if self.compact_integrity
            else self._row_seal(index, locator, body)
        )
        return locator

    def _verify_active(self):
        active = self.state[1]
        length, digest = self.active_seal
        if (
            type(length) is not int
            or not 0 <= length <= _STAT_PAGE_BYTES
            or len(active) < length
        ):
            raise ValueError("original_stat_row_or_locator_changed")
        snapshot = bytes(memoryview(active)[:length])
        if hashlib.sha256(snapshot).digest() != digest.digest():
            raise ValueError("original_stat_row_or_locator_changed")
        return snapshot

    def read(self, index, locator):
        if (
            type(index) is not int
            or not 0 <= index < MAX_VALUES
            or type(locator) is not int
            or not 0 <= locator < 2**48
        ):
            raise ValueError("original_stat_locator_required")
        block_index, offset, size = (
            locator >> 32,
            locator >> 16 & 65535,
            locator & 65535,
        )
        blocks, active = self.state
        if not 0 < size <= 1024 or block_index > len(blocks):
            raise ValueError("original_stat_locator_outside_storage")
        if block_index == len(blocks):
            source = active
            if self.compact_integrity:
                source = self._verify_active()
        else:
            block = blocks[block_index]
            if len(block[2]) != (64 if self.compact_integrity else 32):
                raise ValueError("original_stat_integrity_profile_changed")
            cached = self.cache.get(block_index)
            if cached is None or cached[0] is not block:
                source = self._inflate(block)
                if len(self.cache) >= _STAT_READ_PAGES:
                    self.cache.pop(next(iter(self.cache)))
                self.cache[block_index] = block, source
            else:
                source = cached[1]
                if self.compact_integrity and (
                    type(source) is not bytes
                    or len(source) != block[0]
                    or hashlib.sha256(source).digest() != block[2][32:]
                ):
                    raise ValueError("original_stat_row_or_locator_changed")
        limit = (
            self.active_seal[0]
            if self.compact_integrity and block_index == len(blocks)
            else len(source)
        )
        if offset + size > limit:
            raise ValueError("original_stat_body_truncated")
        body = bytes(source[offset : offset + size])
        width = 8 if self.compact_integrity else 32
        slot = index * width
        expected = (
            locator.to_bytes(8, "little")
            if self.compact_integrity
            else self._row_seal(index, locator, body)
        )
        if (
            len(self.seals) < slot + width
            or expected != self.seals[slot : slot + width]
        ):
            raise ValueError("original_stat_row_or_locator_changed")
        return body


class _StatIndex:
    """Compact index only; canonical full bytes still decide value equality."""

    def __init__(self, *, dense=False):
        if type(dense) is not bool:
            raise ValueError("explicit_original_index_storage_required")
        keys, rows = array("q", [0]) * 128, array("i", [-1]) * 128
        if keys.itemsize != 8 or rows.itemsize != 4:
            raise ValueError("qualified_stat_index_layout_required")
        self.table = keys, rows
        self.extra = {}
        self.charged = 0
        self.pages = tuple(bytearray() for _ in range(32)) if dense else None
        self.pending = None
        self.failure = None

    def _dense_find(self, key):
        if self.failure is not None or self.pending is not None:
            raise ValueError("original_dense_index_capture_spent")
        if (
            type(key) is not int
            or not -(2**63) <= key < 2**63
            or type(self.pages) is not tuple
            or len(self.pages) != 32
        ):
            raise ValueError("original_dense_index_geometry_required")
        page = self.pages[(key >> 4) & 31]
        if type(page) is not bytearray or len(page) % 12 or len(page) > MAX_VALUES * 12:
            raise ValueError("original_dense_index_page_changed")
        lower, upper = 0, len(page) // 12
        while lower < upper:
            middle = (lower + upper) // 2
            if struct.unpack_from("<q", page, middle * 12)[0] < key:
                lower = middle + 1
            else:
                upper = middle
        offset = lower * 12
        if offset < len(page) and struct.unpack_from("<q", page, offset)[0] == key:
            return page, offset, struct.unpack_from("<i", page, offset + 8)[0]
        return page, offset, -1

    @staticmethod
    def _dense_store(page, offset, found, key, row):
        # One C bytearray splice preserves paired keys/rows on insertion.
        # No full-table replacement or second live hash-table capacity.
        page[offset : offset + (12 if found else 0)] = struct.pack("<qi", key, row)

    @staticmethod
    def _find(table, key):
        keys, rows = table
        size = len(keys)
        if (
            type(key) is not int
            or not -(2**63) <= key < 2**63
            or size != len(rows)
            or size < 128
            or size > 2**20
            or size & (size - 1)
        ):
            raise ValueError("original_stat_index_geometry_required")
        for step in range(size):
            slot = (key + step) & (size - 1)
            if rows[slot] == -1 or keys[slot] == key:
                return slot, rows[slot]
        raise ValueError("original_stat_index_full")

    def _grow(self):
        old = self.table
        size = len(old[0]) * 2
        if size > 2**20:
            raise ValueError("original_stat_index_capacity")
        replacement = array("q", [0]) * size, array("i", [-1]) * size
        for key, row in zip(*old, strict=True):
            if row != -1:
                slot, _ = self._find(replacement, key)
                replacement[0][slot], replacement[1][slot] = key, row
        self.table = replacement  # Existing mapping commits in one step.

    def get(self, key, default=None):
        if self.pages is not None:
            _page, _slot, row = self._dense_find(key)
        else:
            _slot, row = self._find(self.table, key)
        if row == -1:
            return default
        if row == -2:
            value = self.extra.get(key)
            if type(value) is not tuple or not 2 <= len(value) <= 8:
                raise ValueError("original_stat_collision_index_changed")
            return value
        if not 0 <= row < MAX_VALUES:
            raise ValueError("original_stat_index_row_changed")
        return row

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        if not (
            (type(value) is int and 0 <= value < MAX_VALUES)
            or (
                type(value) is tuple
                and 2 <= len(value) <= 8
                and all(type(v) is int and 0 <= v < MAX_VALUES for v in value)
            )
        ):
            raise ValueError("original_stat_index_value_required")
        if self.pages is not None:
            page, offset, row = self._dense_find(key)
            if row == -1:
                self.charged += 1
                if self.charged > MAX_VALUES:
                    raise ValueError("original_stat_index_capacity")
            self.pending = key, value, row, self.extra.get(key)
            try:
                if type(value) is tuple:
                    self.extra[key] = value
                self._dense_store(
                    page, offset, row != -1, key, value if type(value) is int else -2
                )
                self.pending = None
            except BaseException as cause:
                self.failure = cause
                raise
            return
        slot, row = self._find(self.table, key)
        if row == -1:
            self.charged += 1  # Interrupted attempts never refund index capacity.
            if self.charged > MAX_VALUES:
                raise ValueError("original_stat_index_capacity")
            if self.charged > len(self.table[0]) // 2:
                self._grow()
                slot, row = self._find(self.table, key)
        if type(value) is tuple:
            self.extra[key] = value
        self.table[0][slot] = key
        self.table[1][slot] = value if isinstance(value, int) else -2

    def __iter__(self):
        if self.pages is not None:
            if self.failure is not None or self.pending is not None:
                raise ValueError("original_dense_index_capture_spent")
            return (
                struct.unpack_from("<q", page, offset)[0]
                for page in self.pages
                for offset in range(0, len(page), 12)
            )
        keys, rows = self.table
        return (key for key, row in zip(keys, rows, strict=True) if row != -1)

    def __len__(self):
        if self.pages is not None:
            return sum(len(page) // 12 for page in self.pages)
        return sum(row != -1 for row in self.table[1])


class HistoryPool:
    """One canonical value table shared by root/member occurrence streams."""

    def __init__(
        self,
        *,
        compressed=False,
        low_memory_encoding=False,
        packed_stat_storage=False,
        stat_block_storage=False,
    ):
        if (
            type(compressed) is not bool
            or type(low_memory_encoding) is not bool
            or (low_memory_encoding and not compressed)
            or type(packed_stat_storage) is not bool
            or (packed_stat_storage and not low_memory_encoding)
            or type(stat_block_storage) is not bool
            or (stat_block_storage and not packed_stat_storage)
        ):
            raise TypeError("explicit_original_history_storage_required")
        self.compressed = compressed
        self.low_memory_encoding = low_memory_encoding
        self.packed_stat_storage = packed_stat_storage
        self.stat_blocks = (
            _StatBlocks(compact_integrity=True) if stat_block_storage else None
        )
        self._path_names = {}
        self._path_rows = {}
        self.values = _ValueTable() if stat_block_storage else []
        self.labels = []
        self._stats = _StatIndex(dense=True) if stat_block_storage else {}
        # Original objects remain strongly retained in values. The explicit
        # packed profile reuses the original compact exact-key index, avoiding
        # a second Python integer/dict graph and its large resize peak.
        self._raw = _StatIndex(dense=True) if stat_block_storage else {}
        self._labels = {}
        self._probes = {}
        self.stat_bytes = 0

    def path_name(self, value):
        """Share input coordinate text only, never a native resource right."""
        if not self.compressed:
            return value
        if type(value) is not str or not value or len(value.encode("utf-8")) > 1024:
            raise ValueError("bounded_original_path_component_required")
        found = self._path_names.get(value)
        if found is not None:
            if type(found) is not str or found != value:
                raise ValueError("original_path_component_storage_changed")
            return found
        if len(self._path_names) >= 4096:
            self._path_names.pop(next(iter(self._path_names)))
        self._path_names[value] = value
        return value

    def path_row(self, row):
        """Share equal immutable expected-coordinate rows after acquisition.

        Every caller still keeps its own list occurrence and original ledger.
        These fields cannot open, close or authenticate a descriptor.
        """
        if not self.compressed:
            return row

        def valid(value):
            return (
                type(value) is tuple
                and len(value) == 4
                and type(value[0]) is int
                and type(value[1]) is str
                and type(value[2]) is int
                and type(value[3]) is tuple
                and len(value[3]) == 6
                and all(type(n) is int for n in value[3])
            )

        if not valid(row):
            raise ValueError("original_expected_path_row_required")
        found = self._path_rows.get(row)
        if found is not None:
            if not valid(found) or found != row:
                raise ValueError("original_path_row_storage_changed")
            return found
        if len(self._path_rows) >= 4096:
            self._path_rows.pop(next(iter(self._path_rows)))
        self._path_rows[row] = row
        return row

    def _label(self, value):
        if type(value) is not str or not value or len(value.encode("utf-8")) > 256:
            raise ValueError("bounded_original_history_label_required")
        found = self._labels.get(value)
        if found is not None:
            return found
        if len(self.labels) >= 256:
            raise ValueError("history_label_capacity")
        index = len(self.labels)
        self.labels.append(value)
        self._labels[value] = index
        return index

    def _stored_value(self, index):
        stored = self.values[index]
        if self.stat_blocks is not None and type(stored) is int:
            return "stat", self.stat_blocks.read(index, stored)
        if self.packed_stat_storage and type(stored) is bytes:
            if not 0 < len(stored) <= 2048:
                raise ValueError("bounded_original_stat_frame_required")
            decoder = zlib.decompressobj()
            body = decoder.decompress(stored, 1025)
            if (
                not body
                or len(body) > 1024
                or not decoder.eof
                or decoder.unused_data
                or decoder.unconsumed_tail
            ):
                raise ValueError("complete_original_stat_frame_required")
            return "stat", body
        if type(stored) is not tuple or len(stored) != 2:
            raise ValueError("original_history_row_required")
        return stored

    def _packed_stat_value(self, value, body):
        if not 0 < len(body) <= 1024:
            raise ValueError("bounded_original_stat_encoding_required")
        key = _stat_storage_key(body)
        if type(key) is not int or not -(2**63) <= key < 2**63:
            raise ValueError("original_stat_index_key_required")
        found = self._stats.get(key)
        bucket = () if found is None else (found,) if type(found) is int else found
        if type(bucket) is not tuple or len(bucket) > 8:
            raise ValueError("bounded_original_stat_collision_bucket_required")
        for index in bucket:
            if type(index) is not int or not 0 <= index < len(self.values):
                raise ValueError("original_stat_index_changed")
            kind, original = self._stored_value(index)
            if kind != "stat" or _stat_storage_key(original) != key:
                raise ValueError("original_stat_storage_binding_changed")
            if original == body:
                return index
        if (
            len(bucket) == 8
            or len(self.values) >= MAX_VALUES
            or self.stat_bytes + len(body) > MAX_STAT_BYTES
        ):
            raise ValueError("history_value_capacity")
        restored = _stat_from_bytes(body)
        if tuple(restored) != tuple(value) or any(
            type(getattr(restored, name)) is not type(getattr(value, name))
            or getattr(restored, name) != getattr(value, name)
            for name in _STAT_NAMES
        ):
            raise ValueError("complete_stat_value_roundtrip_required")
        if self.stat_blocks is not None:
            index = len(self.values)
            self.stat_bytes += len(body)
            try:
                locator = self.stat_blocks.append(index, body)
                self.values.append(locator)
                if self._stored_value(index) != ("stat", body):
                    raise ValueError("original_stat_storage_roundtrip")
                self._stats[key] = index if not bucket else (*bucket, index)
                return index
            except BaseException as cause:
                self.stat_blocks.failure = value, body, cause
                raise
        encoded = _low_memory_block(body)
        index = len(self.values)
        # Original canonical charge precedes publication; failures never refund.
        self.stat_bytes += len(body)
        self.values.append(encoded)
        if self._stored_value(index) != ("stat", body):
            raise ValueError("original_stat_storage_roundtrip")
        self._stats[key] = index if not bucket else (*bucket, index)
        return index

    def _value(self, value):
        if type(value) is RecordedClosedProbe:
            found = self._probes.get(value)
            if found is not None:
                return found
            body = repr(value).encode("utf-8")
            if (
                len(self.values) >= MAX_VALUES
                or self.stat_bytes + len(body) > MAX_STAT_BYTES
            ):
                raise ValueError("history_value_capacity")
            index = len(self.values)
            self.values.append(("original", value))
            self._probes[value] = index
            self.stat_bytes += len(body)
            return index
        is_stat = type(value) is os.stat_result
        body = _stat_bytes(value) if is_stat else None
        if is_stat and self.packed_stat_storage:
            return self._packed_stat_value(value, body)
        key = body if is_stat else id(value)
        table = self._stats if is_stat else self._raw
        found = table.get(key)
        if found is not None:
            if not is_stat:
                kind, original = self._stored_value(found)
                if kind != "original" or original is not value:
                    raise ValueError("original_history_identity_index_changed")
            return found
        if body is not None:
            restored = _stat_from_bytes(body)
            if tuple(restored) != tuple(value) or any(
                type(getattr(restored, name)) is not type(getattr(value, name))
                or getattr(restored, name) != getattr(value, name)
                for name in _STAT_NAMES
            ):
                raise ValueError("complete_stat_value_roundtrip_required")
        if len(self.values) >= MAX_VALUES or (
            body is not None and self.stat_bytes + len(body) > MAX_STAT_BYTES
        ):
            raise ValueError("history_value_capacity")
        index = len(self.values)
        self.values.append(("stat", body) if is_stat else ("original", value))
        if body is not None:
            self.stat_bytes += len(body)
        table[key] = index
        return index


@dataclass(frozen=True, slots=True)
class _Prefix:
    store: object
    count: int
    digest: bytes
    failure: object


class RecordedHistory:
    """Opaque immutable prefix view. Iteration reconstructs historical values.

    Reconstructed stat objects never substitute for fresh provider returns.
    Explicit iteration may allocate output; installer seals do not iterate it.
    """

    __slots__ = ("__weakref__",)
    profile = PROFILE
    authorizes_observation = False

    def __new__(cls):
        raise TypeError("Use the original staging history owner")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Recorded history cannot be subclassed")

    def __copy__(self):
        raise TypeError("Recorded history cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Recorded history cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Recorded history is not a live or serialized capability")

    def __len__(self):
        return _prefix(self).count

    @property
    def capture_complete(self):
        return _prefix(self).failure is None

    @property
    def recording_failure(self):
        return _prefix(self).failure

    def __iter__(self):
        record = _prefix(self)
        remaining = record.count
        for body in record.store._event_chunks():
            for offset in range(0, min(len(body), remaining * _CELL.size), _CELL.size):
                yield record.store._decode_cell(body, offset)
                remaining -= 1
            if not remaining:
                return
        if remaining:
            raise ValueError("complete_original_history_prefix_required")

    def __getitem__(self, index):
        record = _prefix(self)
        if isinstance(index, slice):
            start, stop, step = index.indices(record.count)
            if step > 0:
                return tuple(islice(iter(self), start, stop, step))
            return tuple(record.store._item(i) for i in range(start, stop, step))
        if type(index) is not int:
            raise TypeError("historical_index_required")
        if index < 0:
            index += record.count
        if not 0 <= index < record.count:
            raise IndexError(index)
        return record.store._item(index)


def _prefix(value):
    if type(value) is not RecordedHistory or value not in _RECORDS:
        raise TypeError("original_recorded_history_required")
    return _RECORDS[value]


def history_seal(value):
    record = _prefix(value)
    return record.store.generation, record.count, record.digest, id(record.failure)


def _low_memory_block(original, *, window_bits=12, compression_level=1):
    """Standard zlib frame with an explicitly small transient context.

    This is selected only by the retained-directory consumer profile. Existing
    compression defaults and all history/prefix semantics remain unchanged.
    """
    if type(window_bits) is not int or window_bits not in (12, 15):
        raise ValueError("explicit_original_history_window_required")
    if type(compression_level) is not int or compression_level not in (1, 9):
        raise ValueError("explicit_original_history_compression_required")
    encoder = zlib.compressobj(level=compression_level, wbits=window_bits, memLevel=3)
    prefix = encoder.compress(original)
    if type(prefix) is not bytes or len(prefix) > len(original) + 1024:
        raise ValueError("bounded_original_history_encoding_required")
    terminal = encoder.flush(zlib.Z_FINISH)
    if (
        type(terminal) is not bytes
        or len(prefix) + len(terminal) > len(original) + 1024
    ):
        raise ValueError("bounded_original_history_encoding_required")
    return prefix + terminal


class GuardHistory:
    __slots__ = ("_cached", "_head", "_storage", "failure", "generation", "pool")

    def __init__(self, pool):
        if type(pool) is not HistoryPool:
            raise TypeError("original_history_pool_required")
        self.pool = pool
        self.generation = uuid4().hex
        self._storage = (), bytearray()
        self._head = 0, hashlib.sha256()
        self.failure = None
        self._cached = None

    def __len__(self):
        return self._head[0]

    @property
    def _events(self):
        return self._storage[1]

    @_events.setter
    def _events(self, value):
        self._storage = self._storage[0], value

    def pack_events(self, *, _original_entry=None):
        """Compress acknowledged metadata only; no IO, disposal or refund."""
        if not self.pool.compressed or not self._events:
            return
        try:
            if (
                self.failure is not None
                or len(self._events) > _BLOCK_BYTES
                or len(self._storage[0]) >= MAX_EVENTS * _CELL.size // _BLOCK_BYTES + 1
            ):
                raise ValueError("bounded_original_history_block_required")
            original = self._events
            encoded = (
                _low_memory_block(original)
                if self.pool.low_memory_encoding
                else zlib.compress(original, level=1)
            )
            if type(encoded) is not bytes or len(encoded) > len(original) + 1024:
                raise ValueError("bounded_original_history_encoding_required")
            block = len(original), encoded, hashlib.sha256(encoded).digest()
            if self._inflate_block(block) != original:
                raise ValueError("lossless_original_history_encoding_required")
            replacement = self._storage[0] + (block,), bytearray()
            # Single representation commit. Interruption before publication
            # leaves the exact original bytes; after it the block is complete.
            self._storage = replacement
        except BaseException as cause:
            error = HistoryCaptureError(
                ("original_history_storage", self)
                if _original_entry is None
                else _original_entry,
                len(self),
                cause,
            )
            if self.failure is None:
                self.failure = error
            raise error from cause

    @staticmethod
    def _inflate_block(block):
        size, encoded, seal = block
        if (
            type(size) is not int
            or not 0 < size <= _BLOCK_BYTES
            or size % _CELL.size
            or type(encoded) is not bytes
            or len(encoded) > size + 1024
            or hashlib.sha256(encoded).digest() != seal
        ):
            raise ValueError("original_history_block_binding_required")
        decoder = zlib.decompressobj()
        body = decoder.decompress(encoded, size + 1)
        if (
            type(body) is not bytes
            or len(body) != size
            or decoder.eof is not True
            or decoder.unused_data != b""
            or decoder.unconsumed_tail != b""
        ):
            raise ValueError("bounded_complete_history_block_required")
        return body

    def _event_chunks(self):
        blocks, tail = self._storage
        for block in blocks:
            yield self._inflate_block(block)
        yield tail

    def append_closed_probe(self, descriptor, error):
        self.append(("close_probe_error", error), _probe_descriptor=descriptor)

    def append(self, entry, *, _probe_descriptor=None):
        count, previous = self._head
        try:
            if self.failure is not None:
                raise ValueError("history_capture_already_failed")
            if type(entry) is not tuple or len(entry) != 2 or count >= MAX_EVENTS:
                raise ValueError("bounded_original_history_entry_required")
            label, value = entry
            if _probe_descriptor is not None:
                value = _closed_probe(value, _probe_descriptor)
            label_index = self.pool._label(label)
            value_index = self.pool._value(value)
            if (
                type(label_index) is not int
                or not 0 <= label_index < 256
                or type(value_index) is not int
                or not 0 <= value_index < MAX_VALUES
                or value_index >= 2**24
            ):
                raise ValueError("bounded_original_history_indices_required")
            cell = _CELL.pack((label_index << 24) | value_index)
            digest = previous.copy()
            digest.update(cell)
            kind, stored = self.pool._stored_value(value_index)
            digest.update(stored if kind == "stat" else str(id(stored)).encode("ascii"))
            self._events.extend(cell)
            # Acknowledged-prefix commit is one assignment. Any appended tail
            # before it remains uncommitted, with the original entry retained.
            self._head = count + 1, digest
            self._cached = None
            if self.pool.compressed and len(self._events) == _BLOCK_BYTES:
                self.pack_events(_original_entry=entry)
        except BaseException as cause:  # Preserve interrupted original capture.
            error = HistoryCaptureError(entry, self._head[0], cause)
            if self.failure is None:
                self.failure = error
            raise error from cause

    def _item(self, index):
        offset = index * _CELL.size
        for body in self._event_chunks():
            if offset < len(body):
                return self._decode_cell(body, offset)
            offset -= len(body)
        raise IndexError(index)

    def _decode_cell(self, body, offset):
        cell = _CELL.unpack_from(body, offset)[0]
        label, value = cell >> 24, cell & 0xFFFFFF
        kind, stored = self.pool._stored_value(value)
        return self.pool.labels[label], _stat_from_bytes(
            stored
        ) if kind == "stat" else stored

    def snapshot(self) -> RecordedHistory:
        cached = None if self._cached is None else self._cached()
        record = None if cached is None else _prefix(cached)
        count, digest = self._head
        if (
            cached is not None
            and record is not None
            and record.count == count
            and record.failure is self.failure
        ):
            return cached
        value = object.__new__(RecordedHistory)
        _RECORDS[value] = _Prefix(self, count, digest.digest(), self.failure)
        self._cached = weakref.ref(value)
        return value


def snapshot_returns(value):
    return value.snapshot() if type(value) is GuardHistory else tuple(value)


class OriginalIdentityRoster:
    """Compact freshness index retaining every distinct original object.

    Numeric ids are only an index: strong references prevent reclamation and
    address reuse. An interrupted update poisons the roster, not a retry right.
    This is private data storage, never an observation or custody capability.
    """

    def __init__(self):
        self.originals = []
        self.index = bytearray()
        self.failed = False

    def _position(self, identity):
        lower, upper = 0, len(self.index) // 8
        while lower < upper:
            middle = (lower + upper) // 2
            current = struct.unpack_from("<Q", self.index, middle * 8)[0]
            if current < identity:
                lower = middle + 1
            else:
                upper = middle
        return lower

    def retain_fresh(self, values):
        if self.failed:
            raise ValueError("original_identity_capture_incomplete")
        rows = {id(value): value for value in values if value is not None}
        if len(self.originals) + len(rows) > MAX_EVENTS:
            raise ValueError("original_identity_capacity")
        for identity in rows:
            position = self._position(identity)
            if (
                position * 8 < len(self.index)
                and struct.unpack_from("<Q", self.index, position * 8)[0] == identity
            ):
                raise ValueError("reused_original_stage_evidence")
        # Retain originals before indexing. A late failure preserves those
        # already obtained but cannot certify another freshness operation.
        self.failed = True
        self.originals.extend(rows.values())
        for identity in rows:
            position = self._position(identity) * 8
            self.index[position:position] = struct.pack("<Q", identity)
        self.failed = False


def value_seal(value):
    """Bounded typed value hash; originals remain with their original owner.

    No copied observation tree, arbitrary repr, IO, provenance or authority.
    Type tags and lengths distinguish values such as bool/int and tuple rows.
    """
    digest, active, count = hashlib.sha256(), set(), 0

    def size(n):
        digest.update(str(n).encode("ascii") + b":")

    def visit(item, depth, recur):
        nonlocal count
        count += 1
        if count > 2_000_000 or depth > 32:
            raise ValueError("bounded_staging_value_seal_required")
        kind = type(item)
        if item is None:
            digest.update(b"n")
        elif kind is bool:
            digest.update(b"t" if item else b"f")
        elif kind is int:
            length = max(1, (item.bit_length() + 8) // 8)
            if length > 33:
                raise ValueError("bounded_staging_seal_integer_required")
            digest.update(b"i")
            size(length)
            digest.update(item.to_bytes(length, "little", signed=True))
        elif kind is str:
            digest.update(b"s")
            size(len(item))
            for start in range(0, len(item), 2048):
                digest.update(item[start : start + 2048].encode("utf-8", "strict"))
        elif kind is bytes:
            digest.update(b"b")
            size(len(item))
            digest.update(item)
        elif kind is tuple or (is_dataclass(item) and not isinstance(item, type)):
            identity = id(item)
            if identity in active:
                raise ValueError("acyclic_staging_value_seal_required")
            active.add(identity)
            try:
                if type(item) is tuple:
                    digest.update(b"q")
                    size(len(item))
                    for child in item:
                        recur(child, depth + 1, recur)
                else:
                    digest.update(b"d")
                    recur(
                        (kind.__module__, kind.__qualname__, id(kind)), depth + 1, recur
                    )
                    members = fields(item)
                    size(len(members))
                    for field in members:
                        recur(field.name, depth + 1, recur)
                        recur(getattr(item, field.name), depth + 1, recur)
            finally:
                active.remove(identity)
        else:
            raise TypeError("original_staging_value_seal_type_required")

    # Explicit recursion avoids a self-referential closure. Failed traversals
    # still retain their original helper and traceback through the call frame.
    visit(value, 0, visit)
    return digest.digest()
