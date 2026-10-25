"""Private two-layer bulk scheduling through the original child-flow owner.

One child archive, no recursive extraction, files or live catalog authority.
All sinks remain provisional even after original outer guards succeed.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass

from . import _product_bulk_consumption as bulk
from . import _product_nested_mount as nested

catalog = bulk.catalog


@dataclass(frozen=True, slots=True, eq=False)
class ProvisionalNestedBulk:
    original_outer_flow: bulk.flow.CatalogFlowObservation
    original_child_flow: nested.child.ProvisionalChildFlow
    original_outer_members: tuple
    original_child_members: tuple
    provisional: bool = True
    physical_writes_verified: bool = False
    authorizes_installation: bool = False
    cleanup: str = "not_observed"


class NestedBulkError(RuntimeError):
    def __init__(self, supplied, selection, cause):
        super().__init__("private_nested_bulk_failed")
        self.original_supplied = supplied
        self.original_selection = selection
        self.original_outer_members = (
            ()
            if selection is None or selection.parent is None
            else tuple(selection.parent.returned)
        )
        self.original_child_members = (
            () if selection is None else tuple(selection.child.returned)
        )
        self.original_child_flow = (
            None if selection is None else selection.nested.returned
        )
        self.original_child_error = (
            None if selection is None else selection.nested.error
        )
        self.primary_cause = cause
        self.provisional = True
        self.authorizes_retry = self.authorizes_installation = False
        self.cleanup = "not_observed"


class _NestedBulkSelection:
    def __init__(self, child_pin, child_plan, outer_plan, maximum_child_bytes):
        if (
            type(child_pin) is not tuple
            or len(child_pin) != 3
            or type(child_pin[0]) is not str
            or type(child_pin[1]) is not int
            or not 0 < child_pin[1] <= nested.child.INNER_BYTES
            or type(child_pin[2]) is not str
            or re.fullmatch("[0-9a-f]{64}", child_pin[2]) is None
            or type(maximum_child_bytes) is not int
            or not 0 < maximum_child_bytes <= nested.child.INNER_BYTES
            or type(outer_plan) is not tuple
        ):
            raise ValueError("explicit_bounded_nested_bulk_required")
        catalog.headers._path(child_pin[0])
        self.child = bulk._BulkSelection(child_plan)
        self.parent = None if not outer_plan else bulk._BulkSelection(outer_plan)
        if self.parent is not None and child_pin[0] in self.parent.by_name:
            raise ValueError("nested_archive_cannot_be_consumed_twice")
        self.child_pin, self.maximum = child_pin, maximum_child_bytes
        self.nested = nested._NestedSelection(
            child_pin,
            nested.child.PROFILE,
            maximum_child_bytes,
            _child_selection=self.child,
        )
        self.affinity = os.getpid(), threading.get_ident()
        self.spent = self.child_seen = False
        self.state = None

    def current(self, state):
        if (
            not self.spent
            or self.state is not state
            or self.affinity != (os.getpid(), threading.get_ident())
            or self.nested.pin is not self.child_pin
            or self.nested.profile != nested.child.PROFILE
            or type(self.nested.maximum) is not int
            or self.nested.maximum != self.maximum
            or self.nested._child_selection is not self.child
            or bulk._seal(self.child.plan) != self.child.seal
        ):
            raise ValueError("original_nested_bulk_binding_changed")
        if self.parent is not None:
            self.parent.current(state)

    def begin(self, state):
        if self.spent or self.affinity != (os.getpid(), threading.get_ident()):
            raise ValueError("original_nested_bulk_spent_or_foreign")
        self.spent = True
        self.state = state
        if self.parent is not None:
            self.parent.begin(state)
        self.current(state)

    def handles(self, state, item):
        self.current(state)
        return item.name == self.child_pin[0] or (
            self.parent is not None and self.parent.handles(state, item)
        )

    def consume(self, state, archive, item, entry):
        self.current(state)
        if item.name == self.child_pin[0]:
            if self.child_seen or self.child_pin[:2] != (entry.name, entry.size):
                raise ValueError("original_nested_bulk_member_required")
            self.child_seen = True
            returned = self.nested.consume(state, archive, item, entry)
            self.current(state)
            return returned
        if self.parent is None:
            raise ValueError("original_outer_bulk_selection_required")
        return self.parent.consume(state, archive, item, entry)

    def finish(self, state):
        self.current(state)
        if self.parent is not None:
            self.parent.finish(state)
        value = self.nested.returned
        if (
            not self.child_seen
            or value is None
            or self.nested.seal is None
            or nested._child_seal(value) != self.nested.seal
            or self.child.state is None
            or value.original_member_account.original_archive
            is not self.child.state.archive
        ):
            raise ValueError("original_nested_bulk_completion_required")
        self.child.finish(self.child.state)


def observe_nested_bulk(
    request,
    child_pin,
    child_plan,
    *,
    maximum_decoded_bytes,
    maximum_child_bytes,
    outer_plan=(),
):
    """One explicit regular outer flow and one original single-pass child."""
    selection = None
    supplied = (
        request,
        child_pin,
        child_plan,
        outer_plan,
        maximum_decoded_bytes,
        maximum_child_bytes,
    )
    try:
        selection = _NestedBulkSelection(
            child_pin, child_plan, outer_plan, maximum_child_bytes
        )
        outer = bulk.flow._observe_product_catalog_flow(
            request, maximum_decoded_bytes=maximum_decoded_bytes, _selection=selection
        )
        selection.finish(selection.state)
        child = selection.nested.returned
        assert child is not None
        return ProvisionalNestedBulk(
            outer,
            child,
            () if selection.parent is None else tuple(selection.parent.returned),
            tuple(selection.child.returned),
        )
    except BaseException as cause:  # Preserve original effects/custody; never replay.
        raise NestedBulkError(supplied, selection, cause) from cause
