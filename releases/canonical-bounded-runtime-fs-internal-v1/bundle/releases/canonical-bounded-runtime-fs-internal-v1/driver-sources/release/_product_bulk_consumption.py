"""Private explicit bulk mount; sink claims never certify physical staging.

Plans are caller inputs, not catalog authority. The original scanner owns
checksums/framing; the original flow owner owns source guards and disposal.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass

from . import _product_catalog_flow as flow
from . import _product_member_consumption as member

catalog = member.original
_CONSUME = member.consume_member
DIRECT_CURRENTNESS_PROFILE = "aware.release.in-place-bulk-currentness.v1"


@dataclass(frozen=True, slots=True, eq=False)
class PinnedConsumer:
    pin: tuple
    consumer: member.MemberConsumer


@dataclass(frozen=True, slots=True, eq=False)
class ProvisionalBulkConsumption:
    original_flow: flow.CatalogFlowObservation
    original_members: tuple
    provisional: bool = True
    physical_writes_verified: bool = False
    authorizes_installation: bool = False


class BulkConsumptionError(RuntimeError):
    def __init__(self, request, supplied, selection, cause):
        super().__init__("private_bulk_consumption_failed")
        self.original_request = request
        self.original_plan = supplied
        self.original_selection = selection
        self.original_members = () if selection is None else tuple(selection.returned)
        self.primary_cause = cause
        self.provisional = True
        self.authorizes_retry = self.authorizes_installation = False
        self.cleanup = "not_observed"


def _seal(plan):
    if type(plan) is not tuple or not 0 < len(plan) <= catalog.FILES:
        raise ValueError("bounded_explicit_bulk_plan_required")
    names, rows, path_bytes = set(), [], 0
    for value in plan:
        if type(value) is not PinnedConsumer:
            raise ValueError("original_pinned_consumer_required")
        pin, consumer = value.pin, value.consumer
        if (
            type(pin) is not tuple
            or len(pin) != 3
            or type(pin[0]) is not str
            or type(pin[1]) is not int
            or not 0 <= pin[1] <= catalog.headers.DECODED_BYTES
            or type(pin[2]) is not str
            or re.fullmatch("[0-9a-f]{64}", pin[2]) is None
            or type(consumer) is not member.MemberConsumer
            or not callable(consumer.write)
        ):
            raise ValueError("original_bulk_pin_and_consumer_required")
        catalog.headers._path(pin[0])
        path_bytes += len(pin[0].encode("utf-8", "strict"))
        if pin[0] in names or path_bytes > catalog.PATH_BYTES:
            raise ValueError("bulk_duplicate_or_path_capacity")
        names.add(pin[0])
        rows.append((value, pin, consumer, consumer.binding, consumer.write))
    return tuple(rows)


class _BulkSelection:
    def __init__(self, plan, *, comparison_profile=None):
        if comparison_profile is not None and (
            type(comparison_profile) is not str
            or comparison_profile != DIRECT_CURRENTNESS_PROFILE
        ):
            raise ValueError("explicit_original_bulk_comparison_profile_required")
        self.comparison_profile = comparison_profile
        self.plan = plan
        self.seal = _seal(plan)
        self.by_name = {row[1][0]: row[0] for row in self.seal}
        self.affinity = os.getpid(), threading.get_ident()
        self.spent = False
        self.state = None
        self.returned = []
        self.seen = set()

    def _matches_original_selection(self):
        """Compare against the original captured rows without allocating a copy."""
        if (
            type(self.plan) is not tuple
            or len(self.plan) != len(self.seal)
            or type(self.by_name) is not dict
            or len(self.by_name) != len(self.seal)
        ):
            return False
        for index, value in enumerate(self.plan):
            selected, pin, consumer, binding, write = self.seal[index]
            if (
                value is not selected
                or type(value) is not PinnedConsumer
                or type(value.pin) is not tuple
                or len(value.pin) != 3
                or any(
                    type(value.pin[i]) is not type(pin[i]) or value.pin[i] != pin[i]
                    for i in range(3)
                )
                or value.consumer is not consumer
                or type(consumer) is not member.MemberConsumer
                or consumer.binding is not binding
                or consumer.write is not write
                or self.by_name.get(pin[0]) is not selected
            ):
                return False
        return True

    def current(self, state):
        if (
            not self.spent
            or self.state is not state
            or self.affinity != (os.getpid(), threading.get_ident())
            or (
                not self._matches_original_selection()
                if self.comparison_profile == DIRECT_CURRENTNESS_PROFILE
                else _seal(self.plan) != self.seal
            )
            or member.consume_member is not _CONSUME
            or (
                self.comparison_profile is not None
                and (
                    type(self.comparison_profile) is not str
                    or self.comparison_profile != DIRECT_CURRENTNESS_PROFILE
                )
            )
            or (
                self.comparison_profile is None
                and self.by_name != {row[1][0]: row[0] for row in self.seal}
            )
        ):
            raise ValueError("original_bulk_selection_changed")

    def begin(self, state):
        if self.spent or self.affinity != (os.getpid(), threading.get_ident()):
            raise ValueError("original_bulk_selection_spent_or_foreign")
        self.spent = True
        self.state = state
        self.current(state)

    def handles(self, state, item):
        self.current(state)
        return item.name in self.by_name

    def consume(self, state, archive, item, entry):
        self.current(state)
        selected = self.by_name[item.name]
        if (
            item.name in self.seen
            or selected.pin[:2] != (entry.name, entry.size)
            or state.archive is not archive
            or state.original_item is not item
        ):
            raise ValueError("original_bulk_member_binding_required")
        self.seen.add(item.name)  # Spent even if original consumption fails.
        returned = _CONSUME(state, archive, item, selected.pin, selected.consumer)
        self.returned.append(returned)  # Preserve before post-call checks.
        self.current(state)
        return returned.original_digest_return

    def finish(self, state):
        self.current(state)
        if self.seen != set(self.by_name) or len(self.returned) != len(self.seal):
            raise ValueError("original_bulk_members_missing")


def observe_bulk_consumption(
    request,
    plan,
    *,
    maximum_decoded_bytes,
    history_profile=None,
    comparison_profile=None,
):
    """One explicit original regular-file flow; no staging or nested dispatch."""
    selection = None
    try:
        selection = _BulkSelection(plan, comparison_profile=comparison_profile)
        observed = flow._observe_product_catalog_flow(
            request,
            maximum_decoded_bytes=maximum_decoded_bytes,
            _selection=selection,
            _history_profile=history_profile,
        )
        selection.finish(selection.state)
        return ProvisionalBulkConsumption(observed, tuple(selection.returned))
    except (
        BaseException
    ) as cause:  # Preserve original IO/interruption and partial sinks.
        raise BulkConsumptionError(request, plan, selection, cause) from cause
