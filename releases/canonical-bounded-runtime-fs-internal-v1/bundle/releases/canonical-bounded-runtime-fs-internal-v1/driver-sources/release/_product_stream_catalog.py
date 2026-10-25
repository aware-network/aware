"""Private streamed member/checksum policy; not a verified catalog provider.

Original tar parser and header policy own parsing. Decoded input remains
caller-owned and unqualified here; tar iteration EOF is not whole-flow EOF.
No retained member-body dictionary or archive acquisition is introduced.
"""

from __future__ import annotations

import hashlib
import os
import re
import tarfile
import threading
from dataclasses import dataclass, field
from typing import cast

from . import _product_tar_policy as headers

WINDOW = 65536
FILES = DIRECTORIES = ROWS = 8192
PATH_BYTES = 1048576
CHECKSUM_BYTES = 2097152
LINE_BYTES = 4163
READ_CALLS = 131072
_OPEN = tarfile.open
_EXTRACT = tarfile.TarFile.extractfile


@dataclass(slots=True)
class _Entry:
    name: str
    kind: str
    size: int = 0
    sha256: str | None = None
    original_item: object = None
    snapshot: tuple | None = None
    explicit: bool = False


@dataclass
class _State:
    phase: str = "open"
    archive: object = None
    header_policy: headers._ProductHeaderPolicy = field(
        default_factory=headers._ProductHeaderPolicy
    )
    entries: dict[str, _Entry] = field(default_factory=dict)
    expected: dict[str, str] = field(default_factory=dict)
    path_bytes: int = 0
    files: int = 0
    directories: int = 0
    declared_bytes: int = 0
    read_calls: int = 0
    observed_bytes: int = 0
    root: str | None = None
    checksums_matched: bool = False
    original_member_stream: object = None
    original_item: object = None
    member_bytes: int = 0
    member_sha256: str = ""
    last_return: bytes | None = None
    original_read_return: object = None
    stream_close_attempted: bool = False
    archive_close_attempted: bool = False
    close_returns: list = field(default_factory=list)
    secondary_causes: list = field(default_factory=list)

    def charge_path(self, name):
        headers._path(name)
        size = len(name.encode("utf-8", "strict"))
        if self.path_bytes + size > PATH_BYTES:
            raise ValueError("product_catalog_path_capacity")
        self.path_bytes += size


class ProductCatalogError(RuntimeError):
    def __init__(self, decoded, state, cause):
        super().__init__("private_product_catalog_" + state.phase)
        self.original_decoded_source = decoded
        self.original_state = state
        self.primary_cause = cause
        self.secondary_causes = self.validated_row_prefix = ()
        self.failure_capture_complete = False
        self.unavailable_capture_fields = ("secondary_causes", "validated_row_prefix")
        self.failure_capture_error = None
        try:
            self.secondary_causes = tuple(state.secondary_causes)
            self.unavailable_capture_fields = ("validated_row_prefix",)
            self.validated_row_prefix = tuple(state.expected.items())
            self.unavailable_capture_fields = ()
            self.failure_capture_complete = True
        except BaseException as capture_error:  # noqa: BLE001 - preserve primary parser/IO failure before independent diagnostic projection
            # The original cause, mapping, lists and custody stay on original_state.
            # Missing detached projections do not establish missing original facts.
            self.failure_capture_error = capture_error
        self.original_member_stream = state.original_member_stream
        self.original_item = state.original_item
        self.last_original_return = state.last_return
        self.original_unvalidated_read_return = state.original_read_return
        self.raw_read_history_available = False
        self.catalog_verified = False
        self.member_checksums_matched = state.checksums_matched
        self.whole_flow_verified = False
        self.authorizes_retry = False
        self.cleanup = "not_observed"


@dataclass(frozen=True)
class ProductMemberAccount:
    original_decoded_source: object
    original_archive: object
    original_header_policy: headers._ProductHeaderPolicy
    root: str
    entries: tuple[_Entry, ...]
    checksum_rows: tuple[tuple[str, str], ...]
    read_calls: int
    observed_member_bytes: int
    charged_path_bytes: int
    original_close_returns: tuple
    member_checksums_matched: bool = True
    catalog_verified: bool = False
    whole_flow_verified: bool = False
    cleanup: str = "not_observed"


class _ChecksumLines:
    def __init__(self, state):
        self.state = state
        self.pending = bytearray()
        self.bytes = 0

    def _line(self):
        raw = bytes(self.pending)
        self.pending.clear()
        if raw.endswith(b"\r"):
            raw = raw[:-1]
        line = raw.decode("utf-8", "strict")
        digest, name = line.split("  ", 1)
        if re.fullmatch("[0-9a-f]{64}", digest) is None:
            raise ValueError("product_checksum_digest_required")
        if name in self.state.expected or len(self.state.expected) >= ROWS:
            raise ValueError("product_checksum_row_capacity_or_duplicate")
        self.state.charge_path(name)
        self.state.expected[name] = digest

    def feed(self, body):
        if self.bytes + len(body) > CHECKSUM_BYTES:
            raise ValueError("product_checksum_document_capacity")
        self.bytes += len(body)
        # A bounded pending line, not splitlines() over the whole document.
        offset = 0
        while offset < len(body):
            newline = body.find(b"\n", offset)
            end = len(body) if newline < 0 else newline
            if len(self.pending) + end - offset > LINE_BYTES:
                raise ValueError("product_checksum_line_capacity")
            self.pending.extend(body[offset:end])
            if newline < 0:
                break
            self._line()
            offset = newline + 1

    def finish(self):
        if self.pending:
            self._line()


def _snapshot(item):
    return item.name, item.type, item.size, item.mode, item.offset_data


def _enroll(state, item):
    name = headers._path(item.name)
    root = name.split("/", 1)[0]
    if state.root is None:
        state.root = root
    if root != state.root:
        raise ValueError("product_requires_single_root")
    parts = name.split("/")
    for end in range(1, len(parts)):
        parent = "/".join(parts[:end])
        existing = state.entries.get(parent)
        if existing is not None and existing.kind != "directory":
            raise ValueError("product_file_ancestor_refused")
        if existing is None:
            if state.directories >= DIRECTORIES:
                raise ValueError("product_directory_capacity")
            state.charge_path(parent)
            state.entries[parent] = _Entry(parent, "directory")
            state.directories += 1
    kind = "directory" if item.isdir() else "file" if item.isfile() else None
    if kind is None:
        raise ValueError("product_catalog_type_refused")
    existing = state.entries.get(name)
    if existing is not None:
        if existing.explicit or kind != "directory" or existing.kind != "directory":
            raise ValueError("product_duplicate_or_type_collision")
        entry = existing
    else:
        if kind == "file" and state.files >= FILES:
            raise ValueError("product_file_capacity")
        if kind == "directory" and state.directories >= DIRECTORIES:
            raise ValueError("product_directory_capacity")
        state.charge_path(name)
        entry = state.entries[name] = _Entry(name, kind)
        if kind == "file":
            state.files += 1
        else:
            state.directories += 1
    if state.declared_bytes + item.size > headers.DECODED_BYTES:
        raise ValueError("product_declared_member_capacity")
    state.declared_bytes += item.size
    entry.size, entry.original_item, entry.snapshot, entry.explicit = (
        item.size,
        item,
        _snapshot(item),
        True,
    )
    return entry


class _MemberCursor:
    """Original private read custody, not an externally admitted member port.

    No member-body history is retained. The shared parser state remains the
    counter owner; caller-held provisional spans require separate accounting.
    """

    def __init__(self, state, archive, item, *, expected_sha256=None):
        if expected_sha256 is not None and (
            type(expected_sha256) is not str
            or re.fullmatch("[0-9a-f]{64}", expected_sha256) is None
        ):
            raise ValueError("original_cursor_digest_required")
        self.state, self.archive, self.item = state, archive, item
        self.snapshot = _snapshot(item)
        self.entry = state.entries.get(item.name) if type(state) is _State else None
        self.selected_size = item.size
        self.expected_sha256 = expected_sha256
        self.affinity = os.getpid(), threading.get_ident()
        self.digest = hashlib.sha256()
        self.stream = None
        self.open_attempted = self.release_attempted = False
        self.close_returned = self.reading = self.failed = False
        self.eof = self.finished = False
        self.original_positive_eof = None
        self.original_close_return = None
        self._active_child: object | None = None  # Original private child slot.

    def _affinity(self):
        if self.affinity != (os.getpid(), threading.get_ident()):
            raise ValueError("original_member_cursor_affinity_required")

    def _context(self):
        if (
            vars(self.state).get("_original_member_cursor") is not self
            or self.state.archive is not self.archive
            or self.state.original_item is not self.item
            or self.state.entries.get(self.item.name) is not self.entry
            or vars(self.archive).get("closed") is not False
        ):
            raise ValueError("original_member_cursor_context_changed")

    def open(self):
        self._affinity()
        if self.open_attempted or self.release_attempted:
            raise ValueError("original_member_cursor_already_spent")
        if (
            type(self.state) is not _State
            or type(self.archive) is not tarfile.TarFile
            or self.state.archive is not self.archive
            or self.state.original_item is not self.item
            or type(self.selected_size) is not int
            or type(self.entry) is not _Entry
            or self.entry.original_item is not self.item
            or self.entry.snapshot != self.snapshot
            or not 0 <= self.selected_size <= headers.DECODED_BYTES
            or _snapshot(self.item) != self.snapshot
        ):
            raise ValueError("original_member_cursor_selection_required")
        previous = vars(self.state).get("_original_member_cursor")
        if previous is not None and (
            type(previous) is not _MemberCursor
            or not previous.close_returned
            or previous.item is self.item
        ):
            raise ValueError("original_member_cursor_still_owned")
        self.open_attempted = True
        vars(self.state)["_original_member_cursor"] = self
        self._context()
        state = self.state
        state.phase = "member_open"
        state.original_member_stream = None
        state.stream_close_attempted = False
        state.member_bytes = 0
        state.last_return = state.original_read_return = None
        state.member_sha256 = self.digest.hexdigest()
        try:
            self.stream = _EXTRACT(self.archive, self.item)
            # Original custody above survives interruption of this legacy alias.
            state.original_member_stream = self.stream
            if self.stream is None:
                raise ValueError("original_member_stream_required")
        except BaseException:
            self.failed = True
            raise

    def read(self, maximum_bytes):
        return self._read(maximum_bytes, None)

    def _read_for_child(self, child, maximum_bytes):
        if child is None or self._active_child is not child:
            raise ValueError("original_member_cursor_child_required")
        return self._read(maximum_bytes, child)

    def _read(self, maximum_bytes, child):
        if type(maximum_bytes) is not int or not 1 <= maximum_bytes <= WINDOW:
            raise ValueError("bounded_original_member_cursor_read_required")
        self._affinity()
        if self.reading or self._active_child is not child:
            raise ValueError("original_member_cursor_reentrant_or_child_active")
        if (
            self.failed
            or self.finished
            or self.eof
            or self.release_attempted
            or self.stream is None
        ):
            raise ValueError("original_member_cursor_read_lifetime")
        self.reading = True
        state = self.state
        try:
            state.phase = "member_read"
            self._context()
            if _snapshot(self.item) != self.snapshot:
                raise ValueError("original_product_member_changed")
            if state.read_calls >= READ_CALLS:
                raise ValueError("product_member_read_capacity")
            amount = min(maximum_bytes, self.selected_size - state.member_bytes + 1)
            state.read_calls += 1
            state.original_read_return = None
            returned = self.stream.read(amount)
            state.original_read_return = returned
            if type(returned) is not bytes or len(returned) > amount:
                raise ValueError("bounded_original_member_return_required")
            state.last_return = returned
            if not returned:
                self.original_positive_eof = returned
                self.eof = True
                return returned
            if state.member_bytes + len(returned) > self.selected_size:
                raise ValueError("product_member_size_exceeded")
            state.member_bytes += len(returned)
            state.observed_bytes += len(returned)
            self.digest.update(returned)
            state.member_sha256 = self.digest.hexdigest()
            return returned
        except BaseException:
            self.failed = True
            raise
        finally:
            self.reading = False

    def finish(self):
        return self._finish(None)

    def _finish_for_child(self, child):
        if child is None or self._active_child is not child:
            raise ValueError("original_member_cursor_child_required")
        return self._finish(child)

    def _finish(self, child):
        self._affinity()
        if (
            self.failed
            or self.finished
            or self.release_attempted
            or self._active_child is not child
        ):
            raise ValueError("original_member_cursor_finish_lifetime")
        if not self.eof:
            raise ValueError("product_member_truncated")
        try:
            self._context()
            if (
                self.state.member_bytes != self.selected_size
                or _snapshot(self.item) != self.snapshot
            ):
                raise ValueError("product_member_truncated")
            result = self.digest.hexdigest()
            if self.expected_sha256 is not None and result != self.expected_sha256:
                raise ValueError("original_member_cursor_digest_mismatch")
            self.finished = True
            return result
        except BaseException:
            self.failed = True
            raise

    def release(self):
        self._affinity()
        if self.release_attempted or self._active_child is not None or self.reading:
            raise ValueError("original_member_cursor_release_lifetime")
        self.release_attempted = True
        if self.stream is None:
            return  # No known stream; never claim physical release.
        self.state.stream_close_attempted = True
        returned = self.stream.close()
        self.original_close_return = returned
        self.close_returned = True
        self.state.close_returns.append(("member", returned))


def _read_member(state, archive, item, checksum):
    cursor = _MemberCursor(state, archive, item)
    primary = None
    result = None
    try:
        cursor.open()
        while True:
            returned = cursor.read(WINDOW)
            if not returned:
                break
            if checksum is not None:
                checksum.feed(returned)
        result = cursor.finish()
        if checksum is not None:
            checksum.finish()
    except BaseException as cause:  # noqa: BLE001 -- retain original interruption and settle once
        primary = cause
    finally:
        if cursor.stream is not None and primary is None:
            state.phase = "member_close"
        try:
            cursor.release()
        except BaseException as cause:  # noqa: BLE001 -- preserve primary plus original close interruption
            if primary is None:
                primary = cause
            else:
                state.secondary_causes.append(cause)
    if primary is not None:
        raise primary
    state.last_return = None
    state.original_read_return = None
    return result


def _nested_parent_release_blocked(decoded):
    cursor = getattr(decoded, "_nested_cursor", None)
    if cursor is None:
        return False
    return (
        type(cursor) is not _MemberCursor
        or cursor._active_child is not None
        or (
            cursor.stream is not None
            and (
                not cursor.release_attempted
                or not cursor.close_returned
                or cursor.original_close_return is not None
                or type(cursor.stream) is not tarfile.ExFileObject
                or cursor.stream.closed is not True
            )
        )
    )


def _scan_product_members(decoded):
    """One original parser pass; account remains provisional after tar EOF."""
    return _scan_members(decoded, headers._ProductHeaderPolicy(), finish_flow=False)


def _scan_product_flow_members(decoded, *, _selection=None):
    from ._product_catalog_flow import _DecodedTarSource, _ObservedHeaderPolicy

    if type(decoded) is not _DecodedTarSource:
        raise TypeError("original_decoded_tar_source_required")
    return _scan_members(
        decoded, _ObservedHeaderPolicy(decoded), finish_flow=True, _selection=_selection
    )


def _scan_members(decoded, policy, *, finish_flow, _selection=None):
    bulk = None
    if _selection is not None:
        from ._product_bulk_consumption import _BulkSelection
        from ._product_capture_mount import _CaptureSelection
        from ._product_nested_bulk import _NestedBulkSelection
        from ._product_nested_mount import _NestedSelection

        if type(_selection) not in (
            _CaptureSelection,
            _NestedSelection,
            _BulkSelection,
            _NestedBulkSelection,
        ):
            raise TypeError("original_selected_capture_request_required")
        if type(_selection) in (_BulkSelection, _NestedBulkSelection):
            bulk = _selection
            _selection = None
    state = _State(header_policy=policy)
    archive = None
    primary = None
    checksum_found = False
    try:
        if bulk is not None:
            bulk.begin(state)
        if tarfile.open is not _OPEN or tarfile.TarFile.extractfile is not _EXTRACT:
            raise ValueError("original_product_parser_required")
        archive = _OPEN(
            fileobj=decoded,
            mode="r|",
            tarinfo=state.header_policy.tarinfo_type(),
            encoding="utf-8",
            errors="strict",
        )
        state.archive = archive
        iterator = iter(archive)
        while True:
            state.phase = "next_header"
            try:
                item = next(iterator)
            except StopIteration:
                break
            state.phase = "member_policy"
            state.original_item = item
            entry = _enroll(state, item)
            if entry.kind == "directory":
                continue
            if state.root is None:
                raise ValueError("product_root_unavailable")
            is_checksum = item.name == state.root + "/SHA256SUMS"
            if is_checksum and item.size > CHECKSUM_BYTES:
                raise ValueError("product_checksum_document_capacity")
            checksum = _ChecksumLines(state) if is_checksum else None
            if bulk is not None and bulk.handles(state, item):
                entry.sha256 = bulk.consume(state, archive, item, entry)
            elif (
                bulk is None
                and _selection is not None
                and item.name == _selection.pin[0]
            ):
                from ._product_nested_mount import _NestedSelection

                if type(_selection) is _NestedSelection:
                    entry.sha256 = _selection.consume(state, archive, item, entry)
                else:
                    from ._product_capture_mount import _CaptureSelection
                    from ._product_member_capture import _capture_selected_member

                    assert type(_selection) is _CaptureSelection
                    selection = cast(_CaptureSelection, _selection)
                    captured = _capture_selected_member(
                        state, archive, item, selection.pin
                    )
                    selection.publish(captured, state, item, entry)
                    entry.sha256 = captured.original_digest_return
            else:
                entry.sha256 = _read_member(state, archive, item, checksum)
            if _snapshot(item) != entry.snapshot:
                raise ValueError("original_product_member_changed")
            checksum_found |= is_checksum
        state.phase = "checksum_coverage"
        if (
            state.root is None
            or not checksum_found
            or len(state.expected) != state.files - 1
        ):
            raise ValueError("product_incomplete_checksum_coverage")
        for name, digest in state.expected.items():
            entry = state.entries.get(state.root + "/" + name)
            if (
                entry is None
                or entry.kind != "file"
                or name == "SHA256SUMS"
                or entry.sha256 != digest
            ):
                raise ValueError("product_member_digest_or_coverage_mismatch")
        for entry in state.entries.values():
            if entry.explicit and _snapshot(entry.original_item) != entry.snapshot:
                raise ValueError("original_product_member_changed")
        state.checksums_matched = True
        if bulk is not None:
            bulk.finish(state)
        if finish_flow:
            state.phase = "tar_framing"
            decoded.finish_tar(archive)
    except BaseException as cause:  # noqa: BLE001 -- retain original parser interruption and settle once
        primary = cause
    finally:
        if archive is not None and _nested_parent_release_blocked(decoded):
            cause = ValueError("original_nested_parent_release_pending")
            if primary is None:
                primary = cause
            else:
                state.secondary_causes.append(cause)
        elif archive is not None:
            state.archive_close_attempted = True
            if primary is None:
                state.phase = "archive_close"
            try:
                state.close_returns.append(("archive", archive.close()))
            except BaseException as cause:  # noqa: BLE001 -- no repeated close after late failure
                if primary is None:
                    primary = cause
                else:
                    state.secondary_causes.append(cause)
    if primary is not None:
        raise ProductCatalogError(decoded, state, primary) from primary
    if state.root is None:
        raise ProductCatalogError(
            decoded, state, ValueError("product_root_unavailable")
        )
    return ProductMemberAccount(
        decoded,
        archive,
        state.header_policy,
        state.root,
        tuple(state.entries.values()),
        tuple(state.expected.items()),
        state.read_calls,
        state.observed_bytes,
        state.path_bytes,
        tuple(state.close_returns),
    )
