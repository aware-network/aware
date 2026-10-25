"""Private same-selection original catalog replay; no member-body outcome.

One explicit attempt per genuine member lease. Original three-phase IO,
parsing, terminal correlation and disposal remain with their original owners.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import _product_member_receiving as members

catalog = members.catalog
_PINS = (
    (
        Path(members.__file__),
        "176b50011be23ab1bed6546e9af9f955abb40c8179b35bafd1841a614b125617",
    ),
    (
        Path(catalog.__file__),
        "7316b50d9d63136294c84c7bd42b5473b3a799324e0e5c4a1e3518e94459551c",
    ),
)


@dataclass
class _ReplayAttempt:
    member: members._MemberRecord
    flow: catalog.base._Record
    phase: str = "enrolled"
    invocation: str = "not_invoked"


@dataclass(frozen=True)
class MemberReplayObservation:
    selected_pin: tuple
    original_catalog_observation: catalog.joined.CatalogFlowObservation
    original_replay_observation: catalog.joined.CatalogFlowObservation
    original_guard_returns: tuple
    catalog_verified: bool = False
    member_bytes_available: bool = False
    authorizes_native_profile: bool = False
    cleanup: str = "not_observed"


class MemberReplayError(RuntimeError):
    def __init__(self, handle, attempt, cause):
        super().__init__(
            "private_member_replay_"
            + ("selection" if attempt is None else attempt.phase)
        )
        self.original_handle = handle
        self.request_snapshot = None if attempt is None else attempt.flow.snapshot
        self.original_request = None if attempt is None else attempt.flow.request
        self.disposition = "unspent" if attempt is None else "spent"
        self.original_pin = None if attempt is None else attempt.member.pin
        self.original_catalog_observation = (
            None
            if attempt is None
            else attempt.member.catalog_record.prepared_record.returned
        )
        self.original_replay_return = None if attempt is None else attempt.flow.returned
        self.original_replay_error = None if attempt is None else attempt.flow.error
        self.original_guard_returns = () if attempt is None else attempt.flow.guards
        self.flow_invocation = "not_invoked" if attempt is None else attempt.invocation
        self.primary_cause = cause
        self.cleanup = "not_observed"
        self.authorizes_retry = False
        self.authorizes_native_profile = False


class _OriginalMemberReplayReceiver(members._OriginalMemberReceiver):
    def __init__(self):
        super().__init__()
        self._replays: dict[members._MemberLeaseHandle, _ReplayAttempt] = {}

    def _check(self):
        super()._check()
        if any(
            attempt.phase not in ("returned", "failed")
            for attempt in self._replays.values()
        ):
            raise ValueError("original_member_replay_reentrant")

    def _guards(self, record):
        returned = super()._guards(record)
        for path, digest in _PINS:
            value = catalog.base._FILE(path, digest)
            record.guards += (value,)
            returned += (value,)
        return returned

    def _new_attempt(self, member, record):
        return _ReplayAttempt(member, record)

    def replay_member(self, handle):
        attempt = None
        prior = False
        try:
            member = self._member(handle)
            attempt = self._replays.get(handle)
            if attempt is not None:
                prior = True
                raise ValueError("original_member_replay_already_spent")
            if member.state != "open" or self._active_member is not handle:
                raise ValueError("original_live_member_lease_required")
            parent = member.catalog_record
            snapshot = self.snapshot_catalog(member.catalog_handle)
            if not any(member.pin is pin for pin in snapshot.member_pins):
                raise ValueError("original_member_replay_selection_required")
            original = parent.prepared_record
            historical = snapshot.original_observation
            if historical is not original.returned:
                raise ValueError("original_member_replay_history_required")
            # This is an original evidence carrier, not another enrolled
            # preparation/admission or a replacement live authority handle.
            record = catalog.base._Record(
                original.request, original.snapshot, original.maximum
            )
            attempt = self._new_attempt(member, record)
            self._replays[handle] = attempt  # Sole permanent replay spend point.
            attempt.phase = "source_before"
            if (
                catalog.base.original._guarded_file_snapshot(record.request)
                != record.snapshot
            ):
                raise ValueError("original_member_replay_request_changed")
            before = self._guards(record)
            attempt.phase, attempt.invocation = "original_flow", "unknown"
            try:
                record.returned = self._invoke(record)
            except BaseException as cause:
                record.error = cause
                raise
            attempt.invocation = "returned"
            attempt.phase = "correlation"
            seal, pins, directories = catalog._describe(record)
            value = record.returned
            if type(value) is not catalog.joined.CatalogFlowObservation:
                raise ValueError("original_member_replay_return_required")
            if (
                pins != snapshot.member_pins
                or directories != snapshot.directories
                or value.original_member_account.root != snapshot.root
                or value.original_flow.prehash.original_file
                != historical.original_flow.prehash.original_file
            ):
                raise ValueError("original_member_replay_catalog_or_identity_changed")
            attempt.phase = "source_after"
            after = self._guards(record)
            if (
                before != after
                or catalog._describe(record)[0] != seal
                or catalog._describe(original)[0] != parent.seal
                or self._snapshot(parent) is not snapshot
                or member.pin not in snapshot.member_pins
                or catalog.base.original._guarded_file_snapshot(record.request)
                != record.snapshot
            ):
                raise ValueError("original_member_replay_final_guard_changed")
            outcome = MemberReplayObservation(
                member.pin, historical, value, record.guards
            )
            attempt.phase = "returned"
            return outcome
        except BaseException as cause:
            # A second explicit request cannot erase the first spent attempt.
            # Pre-insertion failures do not invent an enrolled replay.
            if attempt is not None and self._replays.get(handle) is not attempt:
                attempt = None
            error = MemberReplayError(handle, attempt, cause)
            if attempt is not None and not prior:
                attempt.phase = "failed"
            raise error from cause
