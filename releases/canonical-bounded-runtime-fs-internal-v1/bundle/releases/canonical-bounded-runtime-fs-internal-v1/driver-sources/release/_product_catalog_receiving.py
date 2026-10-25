"""Private source-bound observed catalog custody, not public authority.

Reuse the original receiver's prepared registry/spend/error lifecycle. No IO
or authority is reconstructed from a detached snapshot. Physical sources and
decoders are already closed by the original join; retirement is logical only.
"""

from __future__ import annotations

import os
import re
import tarfile
import threading
from dataclasses import dataclass, replace
from pathlib import Path

from . import _product_catalog_flow as joined
from . import _product_stream_receiving as base

_CATALOG_DELEGATE = joined._observe_product_catalog_flow
_PINS = (
    (
        Path(base.__file__),
        "7735ebb78a4625dc1f94220904848aff4e71748a26433681f1bcec7119cf06bf",
    ),
    (
        Path(joined.__file__),
        "d0be5dd6c63da4ee46673cfa6e1f95025c93a94f14b7da5a98b5d8e73f72f47c",
    ),
    (
        Path(joined.catalog.__file__),
        "62d2c44b300f1e6f174bbd561cf3118da953bfcf824a084c65b5432a2bb1773f",
    ),
    (
        Path(joined.headers.__file__),
        "70ca30432e3b214ff9c0321679f480f9d29cd79ac68b72c820d1fc678bca660e",
    ),
)


def _digest(value):
    if (
        type(value) is not str
        or len(value) != 64
        or re.fullmatch("[0-9a-f]{64}", value) is None
    ):
        raise ValueError("original_catalog_digest_required")
    return value


class _ReceivedCatalogHandle:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original_catalog_registry_required")


@dataclass(frozen=True)
class ObservedCatalogSnapshot:
    selection: tuple
    root: str
    member_pins: tuple
    directories: tuple
    original_observation: joined.CatalogFlowObservation
    catalog_verified: bool = False
    authorizes_native_profile: bool = False
    current_source_revalidated: bool = False


@dataclass
class _CatalogRecord:
    prepared_record: base._Record
    seal: tuple
    snapshot: ObservedCatalogSnapshot
    projection: tuple
    state: str = "received"


class CatalogCustodyError(RuntimeError):
    def __init__(self, handle, record, phase, cause, original=None):
        super().__init__("private_catalog_custody_" + phase)
        self.original_handle = handle
        self.original_observation = (
            original if record is None else record.prepared_record.returned
        )
        self.disposition = "not_enrolled" if record is None else record.state
        self.primary_cause = cause
        self.authorizes_retry = False
        self.catalog_verified = False
        self.cleanup = "not_observed"


def _describe(record):
    value = record.returned
    if type(value) is not joined.CatalogFlowObservation:
        raise ValueError("original_catalog_flow_return_required")
    base._OriginalFlowReceiver._correlate(replace(record, returned=value.original_flow))
    account, source, result = (
        value.original_member_account,
        value.original_decoded_source,
        value.original_flow,
    )
    if (
        value.tar_framing_confirmed is not True
        or value.compressed_flow_correlated is not True
        or value.catalog_verified is not False
        or value.authorizes_native_profile is not False
        or value.cleanup != "not_observed"
        or type(account) is not joined.catalog.ProductMemberAccount
        or type(source) is not joined._DecodedTarSource
        or source.finished is not True
        or source.eof is not True
        or source.maximum != record.maximum
        or source.affinity != (os.getpid(), threading.get_ident())
        or source.state is not result.original_terminal[0].state
        or source.reader is not result.original_terminal[0]
        or source.feed is not source.state.feeds[1]
        or account.original_decoded_source is not source
        or type(account.original_header_policy) is not joined._ObservedHeaderPolicy
        or account.original_header_policy.decoded is not source
        or account.member_checksums_matched is not True
        or account.catalog_verified is not False
        or account.whole_flow_verified is not False
        or account.cleanup != "not_observed"
        or result.decoded_bytes != source.state.decoded_bytes
        or result.decoded_sha256 != source.digest.hexdigest()
    ):
        raise ValueError("original_catalog_flow_binding_required")
    if (
        type(result.decoded_steps) is not tuple
        or not 0 < len(result.decoded_steps) <= joined.flow.READ_CALLS
    ):
        raise ValueError("original_decoded_prefix_required")
    total = 0
    if len(result.decoded_steps) != len(source.state.decoded_steps):
        raise ValueError("original_decoded_prefix_binding_required")
    for step, original in zip(
        result.decoded_steps, source.state.decoded_steps, strict=True
    ):
        if (
            step is not original
            or type(step) is not tuple
            or len(step) != 2
            or type(step[0]) is not int
            or not 0 < step[0] <= joined.flow.WINDOW
        ):
            raise ValueError("original_decoded_prefix_binding_required")
        total += step[0]
        _digest(step[1])
    if (
        total != result.decoded_bytes
        or result.decoded_steps[-1][1] != result.decoded_sha256
    ):
        raise ValueError("original_decoded_prefix_total_required")
    if (
        type(source.read_calls) is not int
        or source.read_calls != len(result.decoded_steps) + 1
        or source.read_calls > joined.flow.READ_CALLS
    ):
        raise ValueError("original_decoded_call_total_required")
    for observation, feed in zip(
        (result.prehash, result.decoder_feed, result.posthash),
        source.state.feeds,
        strict=True,
    ):
        if (
            type(observation.read_steps) is not tuple
            or not 0 < len(observation.read_steps) <= joined.flow.READ_CALLS
            or len(observation.read_steps) != len(feed.steps)
        ):
            raise ValueError("original_source_prefix_required")
        seen = 0
        for index, (step, original) in enumerate(
            zip(observation.read_steps, feed.steps, strict=True)
        ):
            if (
                step is not original
                or type(step) is not tuple
                or len(step) != 5
                or type(step[0]) is not int
                or type(step[1]) is not int
                or type(step[2]) is not int
                or type(step[3]) is not int
                or step[0] != seen
                or step[1] <= 0
                or not 0 < step[2] <= joined.flow.WINDOW
                or not 0 <= step[3] <= step[2]
                or (step[3] == 0) != (index == len(observation.read_steps) - 1)
            ):
                raise ValueError("original_source_prefix_binding_required")
            seen += step[3]
            _digest(step[4])
        if (
            seen != record.snapshot[2]
            or observation.read_steps[-1][4] != record.snapshot[1]
        ):
            raise ValueError("original_source_prefix_total_required")
    raw, originals = value.raw_header_witnesses, account.original_header_policy.headers
    if (
        type(raw) is not tuple
        or not 0 < len(raw) <= joined.headers.HEADERS
        or len(raw) != len(source.headers)
        or len(raw) != len(originals)
    ):
        raise ValueError("original_raw_headers_required")
    expected = data_end = 0
    witnesses = {}
    for witness, saved, original in zip(raw, source.headers, originals, strict=True):
        if (
            witness is not saved
            or type(witness) is not tuple
            or len(witness) != 5
            or type(original) is not tuple
            or len(original) != 5
            or witness[0] is not original[0]
            or any(type(x) is not int for x in (witness[1], witness[2], witness[4]))
            or witness[1] != expected
            or witness[1] != original[4]
            or witness[2] != original[3]
            or not 0 <= witness[2] <= record.maximum
            or witness[4] != witness[1] - data_end
            or not 0 <= witness[4] < 512
        ):
            raise ValueError("original_raw_header_binding_required")
        _digest(witness[3])
        witnesses[id(witness[0])] = witness
        data_end = witness[1] + 512 + witness[2]
        expected = witness[1] + 512 + ((witness[2] + 511) // 512) * 512
    ahead = value.original_tar_read_ahead
    if (
        type(ahead) is not tuple
        or len(ahead) != 4
        or source.read_ahead is not ahead
        or type(account.original_archive) is not tarfile.TarFile
    ):
        raise ValueError("original_tar_read_ahead_required")
    stream, buffer, position, delivered = ahead
    if (
        type(stream) is not vars(tarfile)["_Stream"]
        or account.original_archive.fileobj is not stream
        or vars(account.original_archive).get("closed") is not True
        or stream.closed is not True
        or stream.fileobj is not source
        or stream.mode != "r"
        or stream.comptype != "tar"
        or stream._extfileobj is not True
        or type(buffer) is not bytes
        or stream.buf is not buffer
        or any(buffer)
        or type(position) is not int
        or type(delivered) is not int
        or stream.pos != position
        or position != expected + 512
        or position + len(buffer) != delivered
        or delivered > result.decoded_bytes
        or result.decoded_bytes < expected + 1024
        or result.decoded_bytes % 512
        or source.expected_header != expected
        or source.data_end != data_end
    ):
        raise ValueError("original_tar_read_ahead_binding_required")
    if type(account.root) is not str or "/" in account.root:
        raise ValueError("original_catalog_root_required")
    joined.headers._path(account.root)
    if (
        type(account.entries) is not tuple
        or len(account.entries) > joined.catalog.FILES + joined.catalog.DIRECTORIES
    ):
        raise ValueError("original_catalog_entries_required")
    entries = {}
    files = directories = body_bytes = path_bytes = 0
    pins, directory_names, sealed = [], [], []
    original_items = account.original_header_policy.returns
    if (
        type(original_items) is not list
        or len(original_items) != len(raw)
        or len(original_items) > joined.headers.HEADERS
    ):
        raise ValueError("original_catalog_item_prefix_capacity")
    returned_items = {id(item) for item in original_items}
    explicit_items = set()
    for entry in account.entries:
        if type(entry) is not joined.catalog._Entry or type(entry.explicit) is not bool:
            raise ValueError("original_catalog_entry_required")
        name = joined.headers._path(entry.name)
        if (
            name in entries
            or name.split("/", 1)[0] != account.root
            or type(entry.kind) is not str
            or entry.kind not in ("file", "directory")
            or type(entry.size) is not int
            or entry.size < 0
        ):
            raise ValueError("original_catalog_entry_binding_required")
        entries[name] = entry
        path_bytes += len(name.encode("utf-8"))
        if entry.explicit:
            if (
                id(entry.original_item) not in returned_items
                or id(entry.original_item) not in witnesses
                or type(entry.snapshot) is not tuple
                or len(entry.snapshot) != 5
                or entry.snapshot != joined.catalog._snapshot(entry.original_item)
                or entry.snapshot[0] != name
                or entry.snapshot[2] != entry.size
                or entry.size != witnesses[id(entry.original_item)][2]
                or type(entry.snapshot[3]) is not int
                or entry.snapshot[3] < 0
                or type(entry.snapshot[4]) is not int
                or entry.snapshot[4] != witnesses[id(entry.original_item)][1] + 512
            ):
                raise ValueError("original_catalog_item_binding_required")
            explicit_items.add(id(entry.original_item))
        elif (
            entry.original_item is not None
            or entry.snapshot is not None
            or entry.kind != "directory"
        ):
            raise ValueError("original_catalog_implicit_directory_required")
        if entry.kind == "file":
            if (
                not entry.explicit
                or entry.snapshot is None
                or entry.snapshot[1]
                not in (
                    tarfile.REGTYPE,
                    tarfile.AREGTYPE,
                )
            ):
                raise ValueError("original_catalog_regular_file_required")
            files += 1
            body_bytes += entry.size
            pins.append((name, entry.size, _digest(entry.sha256)))
        else:
            if (
                entry.size != 0
                or entry.sha256 is not None
                or (
                    entry.explicit
                    and (entry.snapshot is None or entry.snapshot[1] != tarfile.DIRTYPE)
                )
            ):
                raise ValueError("original_catalog_directory_required")
            directories += 1
            directory_names.append(name)
        sealed.append(
            (
                name,
                entry.kind,
                entry.size,
                entry.sha256,
                entry.snapshot,
                entry.explicit,
                id(entry.original_item),
            )
        )
    if (
        explicit_items != returned_items
        or files > joined.catalog.FILES
        or directories > joined.catalog.DIRECTORIES
    ):
        raise ValueError("original_catalog_item_coverage_required")
    for name in entries:
        parts = name.split("/")
        for index in range(1, len(parts)):
            parent = entries.get("/".join(parts[:index]))
            if parent is None or parent.kind != "directory":
                raise ValueError("original_catalog_ancestor_required")
    checksums = entries.get(account.root + "/SHA256SUMS")
    if (
        checksums is None
        or checksums.kind != "file"
        or checksums.size > joined.catalog.CHECKSUM_BYTES
        or type(account.checksum_rows) is not tuple
        or len(account.checksum_rows) != files - 1
        or len(account.checksum_rows) > joined.catalog.ROWS
    ):
        raise ValueError("original_catalog_checksum_coverage_required")
    seen = set()
    for row in account.checksum_rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("original_catalog_checksum_row_required")
        name, digest = row
        joined.headers._path(name)
        _digest(digest)
        entry = entries.get(account.root + "/" + name)
        if (
            name in seen
            or name == "SHA256SUMS"
            or entry is None
            or entry.kind != "file"
            or entry.sha256 != digest
        ):
            raise ValueError("original_catalog_checksum_row_binding_required")
        seen.add(name)
        path_bytes += len(name.encode("utf-8"))
    if (
        type(account.charged_path_bytes) is not int
        or account.charged_path_bytes != path_bytes
        or path_bytes > joined.catalog.PATH_BYTES
        or type(account.observed_member_bytes) is not int
        or account.observed_member_bytes != body_bytes
        or body_bytes > record.maximum
        or type(account.read_calls) is not int
        or not files <= account.read_calls <= joined.catalog.READ_CALLS
    ):
        raise ValueError("original_catalog_account_totals_required")
    closes = account.original_close_returns
    if (
        type(closes) is not tuple
        or len(closes) != files + 1
        or closes[-1] != ("archive", None)
        or any(row != ("member", None) for row in closes[:-1])
    ):
        raise ValueError("original_catalog_close_returns_required")
    seal = (
        id(value),
        id(result),
        id(source),
        id(account),
        account.root,
        tuple(sealed),
        account.checksum_rows,
        account.read_calls,
        account.observed_member_bytes,
        path_bytes,
        tuple(raw),
        ahead,
        result.decoded_sha256,
        result.decoded_bytes,
        result.decoded_steps,
        result.prehash.read_steps,
        result.decoder_feed.read_steps,
        result.posthash.read_steps,
        closes,
    )
    return seal, tuple(pins), tuple(directory_names)


class _OriginalCatalogReceiver(base._OriginalFlowReceiver):
    def __init__(self):
        super().__init__()
        self._catalogs: dict[_ReceivedCatalogHandle, _CatalogRecord] = {}

    def _guards(self, record):
        prefix = super()._guards(record)
        if (
            joined._observe_product_catalog_flow is not _CATALOG_DELEGATE
            or joined.flow is not base.flow
        ):
            raise ValueError("original_catalog_namespace_required")
        returned = []
        for path, digest in _PINS:
            value = base._FILE(path, digest)
            record.guards += (value,)
            returned.append(value)
        return prefix + tuple(returned)

    @staticmethod
    def _invoke(record):
        return _CATALOG_DELEGATE(record.request, maximum_decoded_bytes=record.maximum)

    @staticmethod
    def _correlate(record):
        # Private receiving-context extension on the genuine enrolled record;
        # never read from a detached snapshot or treated as live authority.
        vars(record)["_catalog_receiving_seal"] = _describe(record)[0]

    def receive_catalog(self, prepared):
        original = None
        try:
            self._check()
            if len(self._catalogs) >= 64:
                raise ValueError("original_catalog_custody_capacity")
            record = self._record(prepared)
            original = self.observe(prepared)
            seal, pins, directories = _describe(
                record
            )  # Final pure guard after code-bookend IO.
            if seal != vars(record).get("_catalog_receiving_seal"):
                raise ValueError("original_catalog_changed_after_correlation")
            if type(original) is not joined.CatalogFlowObservation:
                raise ValueError("original_catalog_flow_return_required")
            projection = (
                record.snapshot,
                original.original_member_account.root,
                pins,
                directories,
                original,
            )
            snapshot = ObservedCatalogSnapshot(*projection)
            handle = object.__new__(_ReceivedCatalogHandle)
            self._catalogs[handle] = _CatalogRecord(record, seal, snapshot, projection)
            return handle
        except base.ProductReceivingError:
            raise
        except BaseException as cause:
            raise CatalogCustodyError(
                prepared, None, "receive", cause, original
            ) from cause

    def _catalog(self, handle):
        self._check()
        if type(handle) is not _ReceivedCatalogHandle or handle not in self._catalogs:
            raise ValueError("original_received_catalog_handle_required")
        return self._catalogs[handle]

    def snapshot_catalog(self, handle):
        record = None
        try:
            record = self._catalog(handle)
            if record.state != "received":
                raise ValueError("original_received_catalog_live_required")
            if _describe(record.prepared_record)[0] != record.seal:
                raise ValueError("original_received_catalog_changed")
            return self._snapshot(record)
        except BaseException as cause:
            raise CatalogCustodyError(handle, record, "snapshot", cause) from cause

    def catalog_status(self, handle):
        record = None
        try:
            record = self._catalog(handle)
            return record.state, self._snapshot(record)
        except BaseException as cause:
            raise CatalogCustodyError(handle, record, "status", cause) from cause

    @staticmethod
    def _snapshot(record):
        snapshot = record.snapshot
        projection = record.projection
        # Retain the original immutable field bindings privately at issuance.
        # Frozen dataclasses alone cannot protect caller-exposed Python objects.
        if (
            type(snapshot) is not ObservedCatalogSnapshot
            or snapshot.selection is not projection[0]
            or snapshot.root is not projection[1]
            or snapshot.member_pins is not projection[2]
            or snapshot.directories is not projection[3]
            or snapshot.original_observation is not projection[4]
            or snapshot.catalog_verified is not False
            or snapshot.authorizes_native_profile is not False
            or snapshot.current_source_revalidated is not False
        ):
            raise ValueError("original_catalog_snapshot_projection_changed")
        return snapshot

    def retire_catalog(self, handle):
        record = None
        try:
            record = self._catalog(handle)
            if record.state != "received":
                raise ValueError("original_received_catalog_live_required")
            record.state = (
                "retired"  # Logical only: no source read or repeated disposal.
            )
        except BaseException as cause:
            raise CatalogCustodyError(handle, record, "retire", cause) from cause
