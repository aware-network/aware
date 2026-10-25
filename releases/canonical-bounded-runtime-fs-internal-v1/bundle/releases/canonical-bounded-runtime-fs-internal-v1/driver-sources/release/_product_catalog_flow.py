"""Private fixed tar/decoded-source join over the original gzip owner.

Observational file bookends, not immutable custody or an installed provider.
Tar read-ahead is accounted before wrapper close; it is not delivered again.
No new gzip/tar/PAX grammar or member-body dictionary.
"""

from __future__ import annotations

import gzip
import hashlib
import os
import tarfile
import threading
from dataclasses import dataclass

from . import _product_stream_catalog as catalog
from . import _product_stream_flow as flow
from . import _product_tar_policy as headers


class CatalogFlowError(RuntimeError):
    def __init__(self, request, state, cause, member_account, decoded):
        super().__init__("private_product_catalog_flow_" + state.phase)
        self.original_request = request
        self.original_flow_error = flow.ProductFlowError(request, state, cause)
        self.primary_cause = cause
        self.original_member_account = member_account
        self.original_decoded_source = decoded
        self.catalog_verified = False
        self.authorizes_retry = False
        self.cleanup = "not_observed"


@dataclass(frozen=True)
class CatalogFlowObservation:
    original_member_account: catalog.ProductMemberAccount
    original_flow: flow.ProductFlowObservation
    original_decoded_source: object
    raw_header_witnesses: tuple
    original_tar_read_ahead: tuple
    tar_framing_confirmed: bool = True
    compressed_flow_correlated: bool = True
    catalog_verified: bool = False
    authorizes_native_profile: bool = False
    cleanup: str = "not_observed"


class _DecodedTarSource:
    def __init__(self, reader, feed, state, maximum):
        self.reader, self.feed, self.state, self.maximum = reader, feed, state, maximum
        self.affinity = os.getpid(), threading.get_ident()
        self.digest = hashlib.sha256()
        self.window = b""
        self.headers = []
        self.data_end = self.expected_header = 0
        self.read_calls = 0
        self.eof = self.finished = False
        self.read_ahead = None

    def _current(self):
        if self.affinity != (os.getpid(), threading.get_ident()) or self.finished:
            raise ValueError("original_decoded_source_lifetime_required")

    def read(self, size):
        self._current()
        if type(size) is not int or not 0 <= size <= flow.WINDOW:
            raise ValueError("bounded_original_decoded_read_required")
        if size == 0:
            return b""  # Not EOF and no original decoder call.
        if self.eof:
            raise ValueError("original_decoded_eof_already_observed")
        if self.read_calls >= flow.READ_CALLS:
            raise ValueError("original_decoded_read_capacity")
        self.read_calls += 1
        amount = min(size, self.maximum - self.state.decoded_bytes + 1)
        self.state.phase = "decode"
        returned = self.reader.read(amount)
        if type(returned) is not bytes or len(returned) > amount:
            raise ValueError("original_bounded_decoded_return")
        if not returned:
            terminal = self.reader.terminal(returned, self.feed)
            self.state.original_terminal = terminal
            self.eof = True
            return returned
        self.state.decoded_bytes += len(returned)
        if self.state.decoded_bytes > self.maximum:
            raise ValueError("decoded_capacity_exceeded")
        self.digest.update(returned)
        self.state.decoded_sha256 = self.digest.hexdigest()
        self.state.decoded_steps.append((len(returned), self.state.decoded_sha256))
        self.window = (self.window + returned)[-flow.WINDOW :]
        return returned

    def exact(self, offset, size):
        start = self.state.decoded_bytes - len(self.window)
        if (
            type(offset) is not int
            or type(size) is not int
            or not 0 <= size <= flow.WINDOW
            or offset < start
            or offset + size > self.state.decoded_bytes
        ):
            raise ValueError("original_decoded_window_unavailable")
        return self.window[offset - start : offset - start + size]

    def header(self, item):
        self._current()
        if (
            len(self.headers) >= headers.HEADERS
            or type(item.offset) is not int
            or item.offset != self.expected_header
            or type(item.size) is not int
            or not 0 <= item.size <= self.maximum
        ):
            raise ValueError("original_tar_header_order_or_capacity")
        raw = self.exact(item.offset, 512)
        padding = self.exact(self.data_end, item.offset - self.data_end)
        if any(padding) or raw[257:265] not in (tarfile.POSIX_MAGIC, tarfile.GNU_MAGIC):
            raise ValueError("original_tar_padding_or_magic_refused")
        self.headers.append(
            (
                item,
                item.offset,
                item.size,
                hashlib.sha256(raw).hexdigest(),
                len(padding),
            )
        )
        self.data_end = item.offset + 512 + item.size
        self.expected_header = item.offset + 512 + ((item.size + 511) // 512) * 512

    def finish_tar(self, archive):
        self._current()
        stream = archive.fileobj
        if (
            type(stream) is not vars(tarfile)["_Stream"]
            or stream.fileobj is not self
            or stream.closed
            or stream.mode != "r"
            or stream.comptype != "tar"
            or stream._extfileobj is not True
            or type(stream.pos) is not int
            or type(stream.buf) is not bytes
            or stream.pos != self.expected_header + 512
            or stream.pos + len(stream.buf) != self.state.decoded_bytes
        ):
            raise ValueError("original_tar_read_ahead_binding_required")
        first_end = self.exact(self.expected_header, 512)
        padding = self.exact(self.data_end, self.expected_header - self.data_end)
        if any(first_end) or any(padding) or any(stream.buf):
            raise ValueError("original_tar_end_or_padding_refused")
        self.read_ahead = (stream, stream.buf, stream.pos, self.state.decoded_bytes)
        end_bytes = 512 + len(stream.buf)
        # The original wrapper's already-delivered buffer is observed once;
        # only the same still-live original decoder supplies the remainder.
        while not self.eof:
            returned = self.read(flow.WINDOW)
            if any(returned):
                raise ValueError("original_tar_nonzero_trailing_bytes")
            end_bytes += len(returned)
        if end_bytes < 1024 or self.state.decoded_bytes % 512:
            raise ValueError("original_tar_two_end_blocks_and_alignment_required")
        self.finished = True


class _ObservedHeaderPolicy(headers._ProductHeaderPolicy):
    def __init__(self, decoded):
        super().__init__()
        self.decoded = decoded

    def process(self, item, archive):
        self.decoded.header(item)
        return super().process(item, archive)


def _observe_product_catalog_flow(
    request, *, maximum_decoded_bytes, _selection=None, _history_profile=None
):
    """One explicit three-phase original source attempt; no retry/installer."""
    state = flow._State(history_profile=_history_profile)
    decoder = decoded = member_account = None
    snapshot = pre = scan = post = None
    primary = None
    try:
        snapshot = flow.original._guarded_file_snapshot(request)
        state.request_snapshot = snapshot
        if (
            type(maximum_decoded_bytes) is not int
            or not 0 < maximum_decoded_bytes <= flow.DECODED_MAXIMUM
        ):
            raise ValueError("bounded_decoded_profile_required")
        if vars(gzip)["_GzipReader"] is not flow._BASE_GZIP:
            raise ValueError("original_gzip_reader_changed")

        def acquire(label):
            state.phase, state.invocation = label, "not_invoked"
            if flow.original._guarded_file_snapshot(request) != snapshot:
                raise ValueError("original_flow_selection_changed")
            feed = flow._SourceFeed(request, history_profile=_history_profile)
            state.feeds.append(feed)
            state.invocation = "unknown"
            feed.acquire()
            return feed

        pre = acquire("prehash")
        while pre.read(flow.WINDOW):
            pass
        pre.finish()
        pre.close()
        scan = acquire("decoder_feed")
        if scan.before != pre.before:
            raise ValueError("source_changed_before_decoder")
        decoder = flow._Reader(scan, state)
        decoded = _DecodedTarSource(decoder, scan, state, maximum_decoded_bytes)
        state.phase = "member_catalog"
        if _selection is None:
            member_account = catalog._scan_product_flow_members(decoded)
        else:
            member_account = catalog._scan_product_flow_members(
                decoded, _selection=_selection
            )
        if (
            type(member_account) is not catalog.ProductMemberAccount
            or member_account.original_decoded_source is not decoded
            or type(member_account.original_archive) is not tarfile.TarFile
            or type(member_account.original_header_policy) is not _ObservedHeaderPolicy
            or member_account.original_header_policy.decoded is not decoded
            or member_account.member_checksums_matched is not True
            or member_account.catalog_verified is not False
            or member_account.whole_flow_verified is not False
            or member_account.cleanup != "not_observed"
            or decoded.read_ahead is None
            or member_account.original_archive.fileobj is not decoded.read_ahead[0]
            or decoded.read_ahead[0].buf is not decoded.read_ahead[1]
        ):
            raise ValueError("original_member_account_binding_required")
        state.phase = "feed_final_guard"
        if not decoded.finished or state.original_terminal is None:
            raise ValueError("original_catalog_flow_terminal_required")
        scan.finish()
        if scan.original_file != pre.original_file:
            raise ValueError("source_changed_during_decoder")
        state.consumed_bytes = scan.supplied
        state.phase = "decoder_close"
        state.decoder_close_attempted = True
        returned = decoder.close()
        state.decoder_close_returned = True
        state.decoder_returns.append(("close", returned))
        state.phase = "feed_close"
        scan.close()
        post = acquire("posthash")
        while post.read(flow.WINDOW):
            pass
        post.finish()
        post.close()
        if (
            post.original_file != pre.original_file
            or flow.original._guarded_file_snapshot(request) != snapshot
        ):
            raise ValueError("source_changed_after_decoder")
        state.phase, state.invocation = "result", "returned"
    except BaseException as cause:  # noqa: BLE001 -- retain original interruptions and settle each acquired resource once
        primary = cause
    finally:
        blocked = decoded is not None and catalog._nested_parent_release_blocked(
            decoded
        )
        if blocked:
            cause = ValueError("original_nested_parent_release_pending")
            if primary is None:
                primary = cause
            else:
                state.secondary_causes.append(cause)
        if decoder is not None and not state.decoder_close_attempted and not blocked:
            state.decoder_close_attempted = True
            try:
                returned = decoder.close()
                state.decoder_close_returned = True
                state.decoder_returns.append(("close", returned))
            except BaseException as cause:  # noqa: BLE001 -- preserve primary and original close error
                if primary is None:
                    primary = cause
                else:
                    state.secondary_causes.append(cause)
        for feed in reversed(state.feeds):
            if feed.stream is not None and not feed.close_attempted and not blocked:
                try:
                    feed.close()
                except BaseException as cause:  # noqa: BLE001 -- no repeat disposal after late failure
                    if primary is None:
                        primary = cause
                    else:
                        state.secondary_causes.append(cause)
    if primary is not None:
        raise CatalogFlowError(
            request, state, primary, member_account, decoded
        ) from primary
    if (
        snapshot is None
        or pre is None
        or scan is None
        or post is None
        or decoder is None
        or decoded is None
        or decoded.read_ahead is None
        or member_account is None
        or state.original_terminal is None
    ):
        raise CatalogFlowError(
            request,
            state,
            ValueError("original_flow_result_unavailable"),
            member_account,
            decoded,
        )
    observation = flow.ProductFlowObservation(
        request,
        snapshot,
        pre.observation(),
        scan.observation(),
        post.observation(),
        tuple(state.decoder_returns),
        state.original_terminal,
        flow._snapshot_steps(state.decoded_steps),
        state.decoded_bytes,
        state.decoded_sha256,
        scan.supplied,
        0,
        0,
        decoder.members,
        state.decoder_close_attempted,
        state.decoder_close_returned,
        history_profile=state.history_profile,
    )
    return CatalogFlowObservation(
        member_account, observation, decoded, tuple(decoded.headers), decoded.read_ahead
    )
