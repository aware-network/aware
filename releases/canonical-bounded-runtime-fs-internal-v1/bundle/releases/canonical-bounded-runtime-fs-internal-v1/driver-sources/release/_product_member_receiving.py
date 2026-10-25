"""Private logical member leases over the original received selection.

No byte reads, source revalidation, nested decoder or public stream provider.
Physical replay must later correlate its own original flow and final guards.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import _product_catalog_receiving as catalog

MEMBER_OPENS = 64


class _MemberLeaseHandle:
    __slots__ = ()

    def __new__(cls):
        raise TypeError("original_member_lease_enrollment_required")


@dataclass
class _MemberRecord:
    catalog_handle: catalog._ReceivedCatalogHandle
    catalog_record: catalog._CatalogRecord
    pin: tuple
    state: str = "open"


class MemberLeaseError(RuntimeError):
    def __init__(self, handle, record, parent, phase, cause, opened, *, requested=None):
        super().__init__("private_product_member_" + phase)
        self.original_handle = handle
        self.original_catalog_handle = None if record is None else record.catalog_handle
        self.original_pin = None if record is None else record.pin
        self.original_requested_selection = requested
        self.original_observation = (
            None if parent is None else parent.prepared_record.returned
        )
        self.disposition = "not_enrolled" if record is None else record.state
        self.open_calls_charged = opened
        self.primary_cause = cause
        self.source_acquisition = "not_acquired"
        self.flow_invocation = "not_invoked"
        self.cleanup = "not_observed"
        self.authorizes_retry = False
        self.authorizes_native_profile = False


class _OriginalMemberReceiver(catalog._OriginalCatalogReceiver):
    """One active lease and 64 cumulative opens per receiver, without refill.

    This private capacity is conservatively narrower than a per-root budget.
    Handles are logical only and cannot yet read or authenticate member bytes.
    """

    def __init__(self):
        super().__init__()
        self._members: dict[_MemberLeaseHandle, _MemberRecord] = {}

    @property
    def _member_opens(self):
        # Enrollment is the sole charge point. Records are never removed.
        return len(self._members)

    @property
    def _active_member(self):
        # Do not maintain a second independently mutable enrollment state.
        active = None
        for handle, record in self._members.items():
            if record.state == "open":
                if active is not None:
                    raise ValueError("original_member_multiple_live_leases")
                active = handle
        return active

    def open_member(self, handle, pin):
        parent = record = lease = None
        try:
            parent = self._catalog(handle)
            snapshot = self.snapshot_catalog(handle)  # Pure historical seal check.
            if (
                type(pin) is not tuple
                or len(pin) != 3
                or type(pin[0]) is not str
                or type(pin[1]) is not int
                or pin[1] < 0
                or type(pin[2]) is not str
            ):
                raise ValueError("original_member_pin_required")
            selected = next(
                (item for item in snapshot.member_pins if item == pin), None
            )
            if selected is None:
                raise ValueError("original_catalog_member_selection_required")
            if self._active_member is not None or self._member_opens >= MEMBER_OPENS:
                raise ValueError("original_member_lease_capacity")
            lease = object.__new__(_MemberLeaseHandle)
            record = _MemberRecord(handle, parent, selected)
            # One original dict insertion publishes the entire lease and
            # charges capacity. Interruption after this point leaves a live,
            # charged, releasable record, without a repair or enrollment retry.
            self._members[lease] = record
            return lease
        except BaseException as cause:
            if lease is None or self._members.get(lease) is not record:
                record = None  # Allocated but never enrolled is not "open".
            raise MemberLeaseError(
                lease,
                record,
                parent,
                "open",
                cause,
                self._member_opens,
                requested=(handle, pin),
            ) from cause

    def _member(self, handle):
        self._check()
        if type(handle) is not _MemberLeaseHandle or handle not in self._members:
            raise ValueError("original_member_lease_handle_required")
        record = self._members[handle]
        if self._catalog(record.catalog_handle) is not record.catalog_record:
            raise ValueError("original_member_parent_binding_required")
        return record

    def member_status(self, handle):
        record = None
        try:
            record = self._member(handle)
            parent = record.catalog_record
            if catalog._describe(parent.prepared_record)[0] != parent.seal:
                raise ValueError("original_member_catalog_changed")
            snapshot = self._snapshot(parent)
            if not any(record.pin is item for item in snapshot.member_pins):
                raise ValueError("original_member_pin_binding_required")
            # Only immutable tuples are newly projected. The exposed original
            # snapshot still passes the original eight-field validation above.
            return record.state, record.pin, snapshot
        except BaseException as cause:
            raise MemberLeaseError(
                handle,
                record,
                None if record is None else record.catalog_record,
                "status",
                cause,
                self._member_opens,
            ) from cause

    def release_member(self, handle):
        record = None
        try:
            record = self._member(handle)
            if record.state != "open" or self._active_member is not handle:
                raise ValueError("original_member_lease_live_required")
            # Logical release must remain possible after historical evidence
            # drift. No seal refresh, physical close or capacity refund occurs.
            record.state = "released"
        except BaseException as cause:
            raise MemberLeaseError(
                handle,
                record,
                None if record is None else record.catalog_record,
                "release",
                cause,
                self._member_opens,
            ) from cause

    def retire_catalog(self, handle):
        parent = None
        try:
            parent = self._catalog(handle)
            active = self._active_member
            if active is not None and self._members[active].catalog_record is parent:
                raise ValueError("original_member_lease_prevents_parent_retirement")
        except BaseException as cause:
            raise catalog.CatalogCustodyError(
                handle, parent, "retire", cause
            ) from cause
        return super().retire_catalog(handle)
