"""Private single-pass child flow; all returned evidence remains provisional.

No outer replay scheduling, catalog issuance, file identity invention or public
provider. Original gzip, tar, checksum and cursor owners retain their policies.
"""

from __future__ import annotations

import gzip
import hashlib
from dataclasses import dataclass

from . import _product_catalog_flow as joined
from . import _product_stream_catalog as catalog
from . import _product_stream_flow as flow

PROFILE = "observed-parent-member-singlepass-v1"
INNER_BYTES = 67108864


class ParentMemberFlowError(RuntimeError):
    def __init__(self, cursor, pin, state, feed, decoder, decoded, account, cause):
        super().__init__("private_parent_member_flow_" + state.phase)
        self.original_cursor, self.original_pin = cursor, pin
        self.original_state, self.original_feed = state, feed
        self.original_decoder, self.original_decoded = decoder, decoded
        self.original_member_account = account
        self.primary_cause = cause
        self.secondary_causes = tuple(state.secondary_causes)
        self.newly_captured_window = None if feed is None else feed.last_window
        self.raw_history_available = False
        self.catalog_verified = self.authorizes_retry = False
        self.authorizes_native_profile = False
        self.cleanup = "not_observed"


@dataclass(frozen=True)
class ProvisionalChildFlow:
    original_cursor: catalog._MemberCursor
    original_pin: tuple
    original_feed: object
    original_decoder: object
    original_decoded: joined._DecodedTarSource
    original_member_account: catalog.ProductMemberAccount
    original_state: flow._State
    original_terminal: tuple
    parent_member_digest: str
    provisional: bool = True
    enclosing_flow_pending: bool = True
    parent_member_release_pending: bool = True
    catalog_verified: bool = False
    authorizes_native_profile: bool = False
    cleanup: str = "not_observed"


class _ParentMemberFeed:
    def __init__(self, cursor, pin, profile):
        # Unsupported child three-phase requests refuse before enrollment/IO.
        if type(profile) is not str or profile != PROFILE:
            raise ValueError("parent_member_profile_unsupported")
        if (
            type(cursor) is not catalog._MemberCursor
            or type(pin) is not tuple
            or len(pin) != 3
            or type(pin[0]) is not str
            or type(pin[1]) is not int
            or not 0 < pin[1] <= INNER_BYTES
            or type(pin[2]) is not str
            or catalog.re.fullmatch("[0-9a-f]{64}", pin[2]) is None
        ):
            raise ValueError("original_parent_member_selection_required")
        cursor._affinity()
        cursor._context()
        source = cursor.archive.fileobj.fileobj
        if (
            type(source) is not joined._DecodedTarSource
            or type(source.reader) is not flow._Reader
            or type(source.feed) is not flow._SourceFeed
            or type(cursor.state.header_policy) is not joined._ObservedHeaderPolicy
            or cursor.state.header_policy.decoded is not source
        ):
            raise ValueError("original_regular_parent_layer_required")
        if (
            not cursor.open_attempted
            or cursor.stream is None
            or cursor.release_attempted
            or cursor.failed
            or cursor.finished
            or cursor.eof
            or cursor.reading
            or cursor._active_child is not None
            or cursor.state.member_bytes != 0
            or catalog._snapshot(cursor.item) != cursor.snapshot
            or pin[:2] != (cursor.item.name, cursor.selected_size)
            or cursor.expected_sha256 not in (None, pin[2])
        ):
            raise ValueError("unspent_original_parent_member_required")
        self.cursor, self.pin, self.original_pin = cursor, pin, pin
        self.source = source
        self.parent_reader, self.parent_feed = source.reader, source.feed
        self.child_state: flow._State | None = None
        self.child_decoder: flow._Reader | None = None
        self.stream = cursor.stream
        self.seen = self.supplied = self.read_calls = 0
        self.digest = hashlib.sha256()
        self.last_window = None
        self.eof = self.failed = self.closed = False
        self.reading = False
        self.member_digest = None
        # One original-cursor child slot, not a parallel handle registry.
        cursor._active_child = self

    def current(self):
        self.cursor._affinity()
        try:
            self.cursor._context()
        except BaseException:
            self.failed = True
            raise
        if (
            self.closed
            or self.pin is not self.original_pin
            or self.cursor._active_child is not self
            or self.cursor.archive.fileobj.fileobj is not self.source
            or self.source.reader is not self.parent_reader
            or self.source.feed is not self.parent_feed
            or self.cursor.stream is not self.stream
            or self.pin[:2] != (self.cursor.item.name, self.cursor.selected_size)
            or catalog._snapshot(self.cursor.item) != self.cursor.snapshot
        ):
            self.failed = True
            raise ValueError("original_parent_feed_binding_changed")

    def read(self, requested):
        self.current()
        if type(requested) is not int or requested < 0:
            raise ValueError("bounded_parent_feed_read_required")
        if requested == 0:
            return b""  # Not an EOF observation or a charged delivery.
        if self.reading:
            raise ValueError("original_parent_feed_reentrant_read")
        if self.failed:
            raise ValueError("original_parent_feed_failed")
        if self.eof:
            return b""  # Wrapper reuse, not a second source delivery.
        self.reading = True
        self.last_window = None
        window = None
        filled = 0
        try:
            amount = min(requested, flow.WINDOW)
            window = bytearray(amount)
            while filled < amount:
                if self.read_calls >= flow.READ_CALLS:
                    raise ValueError("original_parent_feed_read_capacity")
                # Charge every original cursor step, including EOF/failure.
                # The cursor independently charges its shared parent budget.
                self.read_calls += 1
                returned = self.cursor._read_for_child(self, amount - filled)
                self.current()
                if not returned:
                    self.eof = True
                    break
                window[filled : filled + len(returned)] = returned
                filled += len(returned)
                self.seen += len(returned)
            self.last_window = bytes(window[:filled])
            self.digest.update(self.last_window)
            self.supplied += filled
            return self.last_window
        except BaseException:
            # This prefix was consumed from the parent, not delivered to the
            # child. Original cursor returns/causes remain separately retained.
            self.last_window = (
                bytes(window[:filled]) if filled and window is not None else None
            )
            self.failed = True
            raise
        finally:
            self.reading = False

    def finish(self):
        self.current()
        if (
            self.failed
            or not self.eof
            or self.seen != self.supplied
            or self.supplied != self.pin[1]
            or self.digest.hexdigest() != self.pin[2]
            or self.cursor.state.member_bytes != self.supplied
            or self.cursor.original_positive_eof != b""
        ):
            raise ValueError("actual_parent_member_feed_mismatch")
        self.member_digest = self.cursor._finish_for_child(self)
        if self.member_digest != self.pin[2]:
            raise ValueError("original_parent_member_digest_mismatch")

    def detach(self):
        # Only after known child decoder release; never closes the parent.
        self.cursor._affinity()
        if self.closed or self.cursor._active_child is not self:
            raise ValueError("original_parent_feed_already_detached")
        if self.child_state is not None and (
            not self.child_state.decoder_close_returned
            or self.child_decoder is None
            or self.child_decoder.closed is not True
        ):
            raise ValueError("original_child_release_required_before_detach")
        self.closed = True
        self.cursor._active_child = None


def _observe_parent_member_child(
    cursor, pin, *, profile, maximum_decoded_bytes, _selection=None
):
    """One private two-layer attempt; no outer terminal or child acceptance."""
    state = flow._State()
    feed = decoder = decoded = account = None
    decoder_attempted = False
    primary = None
    try:
        if (
            type(maximum_decoded_bytes) is not int
            or not 0 < maximum_decoded_bytes <= INNER_BYTES
            or vars(gzip)["_GzipReader"] is not flow._BASE_GZIP
        ):
            raise ValueError("original_bounded_child_decoder_required")
        feed = _ParentMemberFeed(cursor, pin, profile)
        state.phase = "child_decoder"
        feed.child_state = state
        decoder_attempted = True
        decoder = flow._Reader(feed, state)
        feed.child_decoder = decoder
        decoded = joined._DecodedTarSource(decoder, feed, state, maximum_decoded_bytes)
        state.phase = "child_catalog"
        if _selection is None:
            account = catalog._scan_product_flow_members(decoded)
        else:
            account = catalog._scan_product_flow_members(decoded, _selection=_selection)
        if (
            type(account) is not catalog.ProductMemberAccount
            or account.original_decoded_source is not decoded
            or type(account.original_header_policy) is not joined._ObservedHeaderPolicy
            or account.original_header_policy.decoded is not decoded
            or account.member_checksums_matched is not True
            or not decoded.finished
            or decoded.read_ahead is None
            or state.original_terminal is None
        ):
            raise ValueError("original_provisional_child_account_required")
        state.phase = "parent_member_finish"
        feed.finish()
        state.consumed_bytes = feed.supplied
    except BaseException as cause:  # noqa: BLE001 -- retain original interruption and partial evidence
        primary = cause
    finally:
        if decoder is not None:
            state.decoder_close_attempted = True
            try:
                returned = decoder.close()
                vars(state)["original_child_close_return"] = returned
                state.decoder_close_returned = True
                state.decoder_returns.append(("close", returned))
                if decoder.closed is not True:
                    raise ValueError("original_child_decoder_release_unconfirmed")
            except BaseException as cause:  # noqa: BLE001 -- no repeated child close
                if primary is None:
                    primary = cause
                else:
                    state.secondary_causes.append(cause)
        # An unknown child close keeps the original child slot occupied.
        if feed is not None and (not decoder_attempted or state.decoder_close_returned):
            try:
                feed.detach()
            except BaseException as cause:  # noqa: BLE001 -- preserve cleanup uncertainty
                if primary is None:
                    primary = cause
                else:
                    state.secondary_causes.append(cause)
    if primary is not None:
        raise ParentMemberFlowError(
            cursor, pin, state, feed, decoder, decoded, account, primary
        ) from primary
    if (
        feed is None
        or decoder is None
        or decoded is None
        or account is None
        or state.original_terminal is None
        or feed.member_digest is None
    ):
        cause = ValueError("original_child_completion_evidence_required")
        raise ParentMemberFlowError(
            cursor, pin, state, feed, decoder, decoded, account, cause
        ) from cause
    return ProvisionalChildFlow(
        cursor,
        pin,
        feed,
        decoder,
        decoded,
        account,
        state,
        state.original_terminal,
        feed.member_digest,
    )
