"""Private same-selection child evidence receiving, not catalog issuance.

The original lease/replay registry remains the sole spend point. Child success
is provisional until the original outer replay and final guards return.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import _product_member_replay as replay
from . import _product_parent_member_feed as child

catalog = child.catalog
_PINS = (
    (
        Path(replay.__file__),
        "38d5825f641822f62d7faaff00fe04b80595eb64c136585d02f8c22bbeb14983",
    ),
    (
        Path(child.__file__),
        "a41933516086ccb845c286c2d46d8a797c06833d15fbbc5d72dd58c470a609d9",
    ),
)


def _child_seal(value):
    if type(value) is not child.ProvisionalChildFlow:
        raise ValueError("original_provisional_child_required")
    cursor, feed, decoder, decoded, account, state = (
        value.original_cursor,
        value.original_feed,
        value.original_decoder,
        value.original_decoded,
        value.original_member_account,
        value.original_state,
    )
    if (
        type(cursor) is not catalog._MemberCursor
        or type(feed) is not child._ParentMemberFeed
        or type(decoder) is not child.flow._Reader
        or type(decoded) is not child.joined._DecodedTarSource
        or type(account) is not catalog.ProductMemberAccount
        or type(state) is not child.flow._State
        or value.provisional is not True
        or value.enclosing_flow_pending is not True
        or value.parent_member_release_pending is not True
        or value.catalog_verified is not False
        or value.authorizes_native_profile is not False
        or value.cleanup != "not_observed"
        or feed.cursor is not cursor
        or feed.pin is not value.original_pin
        or feed.child_state is not state
        or feed.child_decoder is not decoder
        or decoded.reader is not decoder
        or decoded.feed is not feed
        or decoded.state is not state
        or account.original_decoded_source is not decoded
        or type(account.original_header_policy)
        is not child.joined._ObservedHeaderPolicy
        or account.original_header_policy.decoded is not decoded
        or account.member_checksums_matched is not True
        or account.catalog_verified is not False
        or account.whole_flow_verified is not False
        or account.cleanup != "not_observed"
        or vars(account.original_archive).get("closed") is not True
        or not decoded.finished
        or not decoded.eof
        or decoded.read_ahead is None
        or value.original_terminal is not state.original_terminal
        or type(value.original_terminal) is not tuple
        or len(value.original_terminal) != 11
        or value.original_terminal[0] is not decoder
        or value.original_terminal[1] is not decoder._fp.original
        or type(value.original_terminal[3]) is not bytes
        or value.original_terminal[3:] != (b"", None, True, True, b"", False, 1, 1)
        or any(type(value.original_terminal[i]) is not bool for i in (5, 6, 8))
        or any(type(value.original_terminal[i]) is not int for i in (9, 10))
        or decoder._fp.original._read is not None
        or decoder.members != 1
        or decoder.trailers != 1
        or decoder._fp.original.file is not feed
        or not state.decoder_close_attempted
        or not state.decoder_close_returned
        or decoder.closed is not True
        or not feed.closed
        or feed.failed
        or not feed.eof
        or feed.member_digest != value.original_pin[2]
        or value.parent_member_digest != value.original_pin[2]
        or feed.digest.hexdigest() != value.original_pin[2]
        or feed.seen != feed.supplied
        or feed.supplied != value.original_pin[1]
        or state.consumed_bytes != feed.supplied
        or not cursor.finished
        or not cursor.eof
        or cursor.original_positive_eof != b""
        or cursor.digest.hexdigest() != value.original_pin[2]
        or not cursor.release_attempted
        or not cursor.close_returned
        or cursor.original_close_return is not None
        or cursor.stream is None
        or cursor.stream.closed is not True
        or cursor._active_child is not None
    ):
        raise ValueError("original_child_terminal_binding_required")
    if (
        type(state.decoded_bytes) is not int
        or not 0 < state.decoded_bytes <= decoded.maximum
        or state.decoded_sha256 != decoded.digest.hexdigest()
        or type(state.decoded_steps) is not list
        or not 0 < len(state.decoded_steps) < child.flow.READ_CALLS
        or decoded.read_calls != len(state.decoded_steps) + 1
    ):
        raise ValueError("original_child_decoded_prefix_required")
    total = 0
    for step in state.decoded_steps:
        if (
            type(step) is not tuple
            or len(step) != 2
            or type(step[0]) is not int
            or not 0 < step[0] <= child.flow.WINDOW
        ):
            raise ValueError("original_child_decoded_step_required")
        total += step[0]
    if (
        total != state.decoded_bytes
        or state.decoded_steps[-1][1] != state.decoded_sha256
    ):
        raise ValueError("original_child_decoded_total_required")
    entries = tuple(
        (
            id(e),
            e.name,
            e.kind,
            e.size,
            e.sha256,
            e.explicit,
            id(e.original_item),
            None if e.original_item is None else catalog._snapshot(e.original_item),
        )
        for e in account.entries
    )
    headers = tuple((id(row[0]), *row[1:]) for row in decoded.headers)
    return (
        id(value),
        id(cursor),
        id(feed),
        id(decoder),
        id(decoded),
        id(account),
        id(state),
        id(value.original_terminal),
        value.original_pin,
        value.parent_member_digest,
        decoded.maximum,
        state.decoded_bytes,
        state.decoded_sha256,
        tuple(state.decoded_steps),
        headers,
        account.root,
        entries,
        account.checksum_rows,
        account.read_calls,
        account.observed_member_bytes,
        account.charged_path_bytes,
        tuple(
            (label, id(returned)) for label, returned in account.original_close_returns
        ),
        tuple(id(returned) for returned in state.decoder_returns),
        feed.read_calls,
        feed.seen,
        feed.supplied,
        id(decoded.read_ahead),
    )


@dataclass
class _NestedSelection:
    pin: tuple
    profile: str
    maximum: int
    cursor: catalog._MemberCursor | None = None
    returned: child.ProvisionalChildFlow | None = None
    error: BaseException | None = None
    seal: tuple | None = None
    item: object = None
    entry: object = None
    consumed: bool = False
    _child_selection: object = None

    def consume(self, state, archive, item, entry):
        if self.consumed:
            raise ValueError("original_nested_selection_already_spent")
        self.consumed = True
        self.item, self.entry = item, entry
        self.cursor = catalog._MemberCursor(
            state, archive, item, expected_sha256=self.pin[2]
        )
        # Original outer owners consult this custody before error retirement.
        vars(state.header_policy.decoded)["_nested_cursor"] = self.cursor
        primary = None
        try:
            self.cursor.open()
            if self._child_selection is None:
                self.returned = child._observe_parent_member_child(
                    self.cursor,
                    self.pin,
                    profile=self.profile,
                    maximum_decoded_bytes=self.maximum,
                )
            else:
                self.returned = child._observe_parent_member_child(
                    self.cursor,
                    self.pin,
                    profile=self.profile,
                    maximum_decoded_bytes=self.maximum,
                    _selection=self._child_selection,
                )
        except BaseException as cause:  # noqa: BLE001 -- retain original child failure
            self.error = primary = cause
        finally:
            if self.cursor._active_child is None and not self.cursor.release_attempted:
                try:
                    self.cursor.release()
                except BaseException as cause:  # noqa: BLE001 -- once-only parent member release
                    if primary is None:
                        self.error = primary = cause
                    else:
                        state.secondary_causes.append(cause)
        if primary is not None:
            raise primary
        self.seal = _child_seal(self.returned)
        return self.pin[2]


@dataclass(frozen=True)
class NestedReplayObservation:
    original_provisional_child: child.ProvisionalChildFlow
    original_replay: replay.MemberReplayObservation
    enclosing_flow_correlated: bool = True
    final_guards_verified: bool = True
    child_catalog_available: bool = False
    authorizes_native_profile: bool = False
    cleanup: str = "not_observed"


class NestedReplayError(RuntimeError):
    def __init__(self, handle, cause, outcome, selection):
        super().__init__("private_nested_replay_receiving")
        self.original_handle = handle
        self.primary_cause = cause
        self.original_replay_error = cause
        self.original_replay_outcome = outcome
        self.original_provisional_child = (
            None if selection is None else selection.returned
        )
        self.original_child_error = None if selection is None else selection.error
        self.original_cursor = None if selection is None else selection.cursor
        self.child_catalog_available = self.authorizes_retry = False
        self.authorizes_native_profile = False
        self.cleanup = "not_observed"


class _OriginalNestedReceiver(replay._OriginalMemberReplayReceiver):
    def __init__(self):
        super().__init__()
        self._choice: tuple | None = None

    def release_member(self, handle):
        member = self._member(handle)
        attempt = self._replays.get(handle)
        if attempt is not None:
            selection = vars(attempt.flow).get("_nested_selection")
            if type(selection) is _NestedSelection and selection.cursor is not None:
                decoded = selection.cursor.state.header_policy.decoded
                if catalog._nested_parent_release_blocked(decoded):
                    cause = ValueError("original_nested_custody_prevents_lease_release")
                    raise replay.members.MemberLeaseError(
                        handle,
                        member,
                        member.catalog_record,
                        "release",
                        cause,
                        self._member_opens,
                    ) from cause
        return super().release_member(handle)

    def _new_attempt(self, member, record):
        if self._choice is None or not 0 < member.pin[1] <= child.INNER_BYTES:
            raise ValueError("original_explicit_nested_request_required")
        profile, maximum = self._choice
        vars(record)["_nested_selection"] = _NestedSelection(
            member.pin, profile, maximum
        )
        return super()._new_attempt(member, record)

    @staticmethod
    def _invoke(record):
        selection = vars(record).get("_nested_selection")
        if selection is None:
            return replay.catalog._OriginalCatalogReceiver._invoke(record)
        if type(selection) is not _NestedSelection:
            raise ValueError("original_nested_selection_required")
        return child.joined._observe_product_catalog_flow(
            record.request,
            maximum_decoded_bytes=record.maximum,
            _selection=selection,
        )

    def _guards(self, record):
        returned = super()._guards(record)
        for path, digest in _PINS:
            value = replay.catalog.base._FILE(path, digest)
            record.guards += (value,)
            returned += (value,)
        return returned

    def verify_nested(self, handle, *, profile, maximum_decoded_bytes):
        outcome = selection = None
        allowed = False
        try:
            self._check()
            allowed = True
            if (
                self._choice is not None
                or type(profile) is not str
                or profile != child.PROFILE
                or type(maximum_decoded_bytes) is not int
                or not 0 < maximum_decoded_bytes <= child.INNER_BYTES
            ):
                raise ValueError("original_bounded_nested_profile_required")
            self._choice = profile, maximum_decoded_bytes
            try:
                outcome = self.replay_member(handle)
            finally:
                self._choice = None
            attempt = self._replays[handle]
            selection = vars(attempt.flow).get("_nested_selection")
            if (
                type(selection) is not _NestedSelection
                or selection.pin is not attempt.member.pin
                or selection.profile != profile
                or selection.maximum != maximum_decoded_bytes
                or selection.returned is None
                or selection.cursor is None
                or selection.cursor is not selection.returned.original_cursor
                or selection.returned.original_pin is not selection.pin
                or selection.seal != _child_seal(selection.returned)
                or outcome.original_replay_observation is not attempt.flow.returned
                or outcome.selected_pin is not selection.pin
            ):
                raise ValueError("original_nested_projection_changed")
            account = outcome.original_replay_observation.original_member_account
            cursor = selection.cursor
            feed = selection.returned.original_feed
            if (
                type(cursor) is not catalog._MemberCursor
                or type(cursor.entry) is not catalog._Entry
                or type(feed) is not child._ParentMemberFeed
                or selection.returned.original_decoded.maximum != maximum_decoded_bytes
                or cursor.state.archive is not account.original_archive
                or cursor.state.header_policy is not account.original_header_policy
                or cursor.item is not selection.item
                or cursor.entry is not selection.entry
                or not any(entry is selection.entry for entry in account.entries)
                or cursor.entry.snapshot != catalog._snapshot(cursor.item)
                or (cursor.entry.name, cursor.entry.size, cursor.entry.sha256)
                != selection.pin
                or feed.source
                is not outcome.original_replay_observation.original_decoded_source
                or vars(feed.source).get("_nested_cursor") is not cursor
            ):
                raise ValueError("original_nested_parent_binding_required")
            return NestedReplayObservation(selection.returned, outcome)
        except BaseException as cause:
            if (
                allowed
                and type(cause) is replay.MemberReplayError
                and cause.disposition == "spent"
            ):
                attempt = self._replays.get(handle)
                if attempt is not None:
                    selected = vars(attempt.flow).get("_nested_selection")
                    if type(selected) is _NestedSelection:
                        selection = selected
            raise NestedReplayError(handle, cause, outcome, selection) from cause
