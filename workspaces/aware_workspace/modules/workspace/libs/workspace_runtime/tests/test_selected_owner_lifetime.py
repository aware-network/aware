"""Non-authorizing cancellation-custody proofs; no installed owner is used."""

from __future__ import annotations

import gc
import hashlib
import os
import pickle
import select
import signal
import sys
from dataclasses import fields
from io import StringIO
from pathlib import Path
from threading import Event, Thread
from types import ModuleType
from weakref import ref

import pytest

# isort: split
from aware_workspace_runtime import selected_owner_lifetime as lifetime

# Source-only successor capture. New capture execution requires the separately
# accepted literal footprint; authoring this fixture does not grant that review.
_ATTACHMENT_SOURCE_SHA256 = "8001e321c2068d38ae2ad94747ba8dbc4646b1a9df7790f27d01e80209595f96"


@pytest.fixture
def attachment_storage():
    source_path = Path(__file__).parents[1] / "aware_workspace_runtime/selected_owner_lifetime.py"
    source = source_path.read_bytes()
    assert hashlib.sha256(source).hexdigest() == _ATTACHMENT_SOURCE_SHA256
    module = ModuleType("_workspace_attachment_custody_capture")
    module.__file__ = str(source_path)
    assert module.__name__ not in sys.modules
    sys.modules[module.__name__] = module
    try:
        exec(compile(source, str(source_path), "exec"), module.__dict__)  # noqa: S102 - exact pinned source, isolated diagnostic module
        yield module
    finally:
        sys.modules.pop(module.__name__, None)


def _attachment_storage_fixture(module, events, *, fail=False):
    command, use, registration = _Value(), _Value(), _Value()
    position = [None]
    attachment = module._reserve_owner_attachment_storage(position, command, use, registration)
    module._join_owner_attachment_storage(attachment, _Value(), _Value(), tuple(_Value() for _ in range(4)))
    module._begin_owner_attachment_prepare(attachment)
    generator = _owner(events, fail=fail)
    next(generator)
    cancel = generator.close
    return position, attachment, registration, generator, cancel


def test_attachment_layout_and_known_release_then_seal(attachment_storage):
    module, events = attachment_storage, []
    position, attachment, registration, generator, cancel = _attachment_storage_fixture(module, events)
    record = module._owner_attachment_record(attachment)
    assert tuple(f.name for f in fields(record)) == (
        "selection", "delivery", "port_origins", "registration", "process_id", "thread", "phase",
        "attach_state", "prepare_state", "retain_state", "close_state", "transfer_state",
        "cancel_close_state", "native_cancellation", "cancellation_custody", "owner_result",
    )
    module._capture_owner_attachment_cancellation(attachment, registration, cancel)
    pair = module._read_owner_attachment_cancellation(attachment)
    assert pair[0] is cancel and pair[1] is record.cancellation_custody
    assert position[0] is attachment and events == []
    module._begin_owner_attachment_close(attachment)
    module._release_owner_attachment_cancellation(attachment)
    module._complete_owner_attachment_close(attachment)
    module._seal_owner_attachment_storage(attachment)
    assert events == ["cancel"] and record.phase == "closed"
    assert record.selection is record.delivery is record.registration is record.owner_result is None
    assert record.native_cancellation is record.cancellation_custody is None
    assert attachment._command is attachment._use is None
    with pytest.raises(RuntimeError, match="closed"):
        module._read_owner_attachment_cancellation(attachment)
    assert not generator.gi_suspended


def test_attachment_terminal_fence_does_not_prove_cancel_success(attachment_storage):
    module, events = attachment_storage, []
    _, attachment, registration, _, cancel = _attachment_storage_fixture(module, events, fail=True)
    module._capture_owner_attachment_cancellation(attachment, registration, cancel)
    module._begin_owner_attachment_close(attachment)
    record = module._owner_attachment_record(attachment)
    with pytest.raises(RuntimeError, match="owner cleanup failed"):
        module._release_owner_attachment_cancellation(attachment)
    assert record.cancel_close_state == "uncertain" and record.phase == "held"
    assert module._record_by_identity(record.cancellation_custody).terminal
    with pytest.raises(RuntimeError):
        module._seal_owner_attachment_storage(attachment)
    with pytest.raises(RuntimeError):
        module._release_owner_attachment_cancellation(attachment)
    assert events == ["cancel"]


def test_attachment_close_reconciliation_preserves_foreign_pending_custody(attachment_storage):
    module = attachment_storage
    events = [[], []]
    families = [_attachment_storage_fixture(module, item) for item in events]
    for _, attachment, registration, _, cancel in families:
        module._capture_owner_attachment_cancellation(attachment, registration, cancel)
    _, attachment, _, _, _ = families[0]
    _, other, _, _, _ = families[1]
    record = module._owner_attachment_record(attachment)
    other_record = module._owner_attachment_record(other)
    foreign_pending = other_record.cancellation_custody
    try:
        # Poison only the pending slot: cleanup must not discard or submit
        # another family's holder, even after this family's known cleanup.
        attachment._pending_custody = foreign_pending
        module._release_owner_attachment_cancellation(attachment)
        module._begin_owner_attachment_close(attachment)
        with pytest.raises(RuntimeError, match="pending owner custody substituted"):
            module._complete_owner_attachment_close(attachment)
        assert record.phase == "held" and record.close_state == "uncertain"
        assert attachment._pending_custody is foreign_pending
        assert events == [["cancel"], []]
        assert other_record.phase == "preparing" and other_record.cancel_close_state == "unspent"
        with pytest.raises(RuntimeError, match="known successful"):
            module._seal_owner_attachment_storage(attachment)
        assert module._read_owner_attachment_cancellation(other)[1] is foreign_pending
        module._release_owner_attachment_cancellation(other)
        module._begin_owner_attachment_close(other)
        module._complete_owner_attachment_close(other)
        module._seal_owner_attachment_storage(other)
        assert attachment._pending_custody is foreign_pending
        assert events == [["cancel"], ["cancel"]]
    finally:
        for _, original, _, generator, _ in families:
            if generator.gi_suspended:
                assert module._read_owner_attachment_cancellation(original) is not None
                module._release_owner_attachment_cancellation(original)


def test_attachment_indexes_do_not_own_command_cycles_or_unknown_error_families(attachment_storage):
    module, events = attachment_storage, []

    def make_cycle():
        command = _Value()
        command.position = [None]
        registration = _Value()
        attachment = module._reserve_owner_attachment_storage(command.position, command, command, registration)
        module._join_owner_attachment_storage(attachment, command, _Value(), tuple(_Value() for _ in range(4)))
        module._begin_owner_attachment_prepare(attachment)
        generator = _owner(events)
        next(generator)
        module._capture_owner_attachment_cancellation(attachment, registration, generator.close)
        return ref(command), ref(attachment), ref(generator)

    def held_unknown_error():
        try:
            module._owner_attachment_record(_Hostile())
        except TypeError as error:
            return error
        raise AssertionError("unknown value unexpectedly accepted")

    families = [make_cycle(), make_cycle(), make_cycle()]
    error = held_unknown_error()
    gc.collect()
    assert error is not None and all(value() is None for family in families for value in family)
    assert events == ["cancel", "cancel", "cancel"]
    # Collection/native finalization is a local leak oracle, not an installed
    # cancellation receipt or proof of durable retirement/backing refunds.


_ATTACHMENT_TRANSFER_CUTS = (
    ("T05", 'record.transfer_state = "spent"', False),
    ("T06", "attachment._pending_custody = object.__new__", False),
    ("T07", "custody = attachment._pending_custody", False),
    ("T08", "record.cancellation_custody = custody", False),
    ("T09", "attachment._pending_custody = None", True),
)


@pytest.mark.parametrize("interruption", (KeyboardInterrupt, SystemExit))
@pytest.mark.parametrize(("cut", "anchor", "published"), _ATTACHMENT_TRANSFER_CUTS)
def test_real_attachment_transfer_cuts_conserve_three_families(
    attachment_storage, interruption, cut, anchor, published,
):
    module = attachment_storage
    events = [[], [], []]
    families = [_attachment_storage_fixture(module, item) for item in events]
    _, attachment, registration, _, cancel = families[0]
    source_lines = Path(module.__file__).read_text().splitlines()
    start = module._capture_owner_attachment_cancellation.__code__.co_firstlineno
    line = next(i for i, text in enumerate(source_lines, 1) if i > start and anchor in text)
    hit = []
    previous = sys.gettrace()

    def trace(frame, event, arg):
        if frame.f_code is module._capture_owner_attachment_cancellation.__code__ and event == "line" and frame.f_lineno == line:
            hit.append(cut)
            raise interruption(cut)
        return trace

    try:
        sys.settrace(trace)
        with pytest.raises(interruption):
            module._capture_owner_attachment_cancellation(attachment, registration, cancel)
    finally:
        sys.settrace(previous)
    try:
        assert hit == [cut]
        record = module._owner_attachment_record(attachment)
        assert record.phase == "held" and record.native_cancellation is cancel
        assert (record.cancellation_custody is not None) is published
        assert all(not item for item in events)
        with pytest.raises(RuntimeError):
            module._capture_owner_attachment_cancellation(attachment, registration, cancel)
        pending = attachment._pending_custody
        pending_record = attachment._custody_record
        transfer_state = record.transfer_state
        pair = module._read_owner_attachment_cancellation(attachment)
        if published:
            assert pair[0] is cancel and pair[1] is record.cancellation_custody
            assert pending is record.cancellation_custody
            module._release_owner_attachment_cancellation(attachment)
            assert attachment._pending_custody is pending
        else:
            # Authoritative readback chooses the original producer, including
            # T06-T08. It neither refunds spending nor drops pending records.
            assert pair is None
            assert attachment._pending_custody is pending
            assert attachment._custody_record is pending_record
            assert record.transfer_state == transfer_state
            assert module._read_owner_attachment_cancellation(attachment) is None
            with pytest.raises(RuntimeError, match="no transferred"):
                module._release_owner_attachment_cancellation(attachment)
            assert events == [[], [], []]
            cancel()
        module._begin_owner_attachment_close(attachment)
        module._complete_owner_attachment_close(attachment)
        assert attachment._pending_custody is None
        module._seal_owner_attachment_storage(attachment)
        assert events == [["cancel"], [], []]
        for _, other, _, _, _ in families[1:]:
            assert module._owner_attachment_record(other).phase == "preparing"
    finally:
        for _, other, _, generator, other_cancel in families:
            if generator.gi_suspended:
                remaining = module._read_owner_attachment_cancellation(other)
                if remaining is None:
                    other_cancel()
                else:
                    module._release_owner_attachment_cancellation(other)


@pytest.mark.parametrize("interruption", (KeyboardInterrupt, SystemExit))
@pytest.mark.parametrize("anchor", ('record.close_state = "spent"', 'record.phase = "closing"'))
def test_real_attachment_close_cuts_fence_capture_and_conserve_three_families(
    attachment_storage, interruption, anchor,
):
    module = attachment_storage
    events = [[], [], []]
    families = [_attachment_storage_fixture(module, item) for item in events]
    _, attachment, registration, generator, cancel = families[0]
    source_lines = Path(module.__file__).read_text().splitlines()
    start = module._begin_owner_attachment_close.__code__.co_firstlineno
    line = next(i for i, text in enumerate(source_lines, 1) if i > start and anchor in text)
    hit = []
    previous = sys.gettrace()

    def trace(frame, event, arg):
        if frame.f_code is module._begin_owner_attachment_close.__code__ and event == "line" and frame.f_lineno == line:
            hit.append(anchor)
            if anchor == 'record.phase = "closing"':
                interrupted_record = module._owner_attachment_record(attachment)
                assert interrupted_record.close_state == "spent" and interrupted_record.phase == "preparing"
                with pytest.raises(RuntimeError, match="preparing"):
                    module._capture_owner_attachment_cancellation(attachment, registration, cancel)
                assert interrupted_record.close_state == "spent"
                assert interrupted_record.cancellation_custody is None and events == [[], [], []]
            raise interruption(anchor)
        return trace

    try:
        sys.settrace(trace)
        with pytest.raises(interruption):
            module._begin_owner_attachment_close(attachment)
    finally:
        sys.settrace(previous)
    try:
        assert hit == [anchor]
        record = module._owner_attachment_record(attachment)
        assert record.phase == "held" and record.close_state == "uncertain"
        assert events == [[], [], []] and generator.gi_suspended
        # Even restoring the old phase cannot reopen capture after spending.
        record.phase = "preparing"
        with pytest.raises(RuntimeError, match="preparing"):
            module._capture_owner_attachment_cancellation(attachment, registration, cancel)
        assert record.phase == "held" and record.close_state == "uncertain"
        assert record.native_cancellation is record.cancellation_custody is None
        assert generator not in module._TRANSFERRED
        with pytest.raises(RuntimeError, match="already submitted"):
            module._begin_owner_attachment_close(attachment)
        assert record.close_state == "uncertain"
        # No transfer occurred: cleanup ownership comes from this readback.
        assert module._read_owner_attachment_cancellation(attachment) is None
        cancel()
        assert events == [["cancel"], [], []]
        for _, other, _, _, _ in families[1:]:
            other_record = module._owner_attachment_record(other)
            assert other_record.phase == "preparing" and other_record.close_state == "unspent"
    finally:
        for _, other, _, other_generator, other_cancel in families:
            if other_generator.gi_suspended:
                assert module._read_owner_attachment_cancellation(other) is None
                other_cancel()


_ATTACHMENT_REENTRY_CUTS = (
    ("post_guard", "if generator in _TRANSFERRED:", False),
    ("native_binding", "record.native_cancellation = cancellation", False),
    ("transfer_spend", 'record.transfer_state = "spent"', False),
    ("publication", "record.cancellation_custody = custody", False),
    ("published", 'record.transfer_state = "complete"', True),
)


@pytest.mark.parametrize("interruption", (None, KeyboardInterrupt, SystemExit))
@pytest.mark.parametrize(("cut", "anchor", "published"), _ATTACHMENT_REENTRY_CUTS)
def test_real_close_during_capture_cannot_reconcile_or_clean_up(
    attachment_storage, interruption, cut, anchor, published,
):
    module = attachment_storage
    events = [[], [], []]
    families = [_attachment_storage_fixture(module, item) for item in events]
    _, attachment, registration, generator, cancel = families[0]
    source_lines = Path(module.__file__).read_text().splitlines()
    start = module._capture_owner_attachment_cancellation.__code__.co_firstlineno
    line = next(i for i, text in enumerate(source_lines, 1) if i > start and anchor in text)
    hit = []
    previous = sys.gettrace()

    def trace(frame, event, arg):
        if frame.f_code is module._capture_owner_attachment_cancellation.__code__ and event == "line" and frame.f_lineno == line:
            hit.append(cut)
            # Use the real entrances; do not restamp the record or invent busy
            # state. RLock is reentrant here, so the activity fence must refuse.
            with pytest.raises(RuntimeError, match="capture in progress"):
                module._begin_owner_attachment_close(attachment)
            with pytest.raises(RuntimeError, match="capture in progress"):
                module._read_owner_attachment_cancellation(attachment)
            with pytest.raises(RuntimeError, match="capture in progress"):
                module._capture_owner_attachment_cancellation(attachment, registration, cancel)
            record = module._owner_attachment_record(attachment)
            assert record.phase == "preparing" and record.close_state == "unspent"
            assert len(module._ACTIVE_OWNER_CAPTURES) == 1
            assert generator.gi_suspended and events == [[], [], []]
            if interruption is not None:
                raise interruption(cut)
        return trace

    try:
        try:
            sys.settrace(trace)
            if interruption is None:
                module._capture_owner_attachment_cancellation(attachment, registration, cancel)
            else:
                with pytest.raises(interruption):
                    module._capture_owner_attachment_cancellation(attachment, registration, cancel)
        finally:
            sys.settrace(previous)
        assert hit == [cut] and module._ACTIVE_OWNER_CAPTURES == []
        assert events == [[], [], []] and generator.gi_suspended
        record = module._owner_attachment_record(attachment)
        assert record.close_state == "unspent"
        pair = module._read_owner_attachment_cancellation(attachment)
        if interruption is None or published:
            assert pair[0] is cancel and pair[1] is record.cancellation_custody
            module._release_owner_attachment_cancellation(attachment)
        else:
            assert record.phase == "held" and pair is None
            cancel()
        module._begin_owner_attachment_close(attachment)
        module._complete_owner_attachment_close(attachment)
        module._seal_owner_attachment_storage(attachment)
        assert events == [["cancel"], [], []]
        for _, other, _, _, _ in families[1:]:
            other_record = module._owner_attachment_record(other)
            assert other_record.phase == "preparing" and other_record.close_state == "unspent"
    finally:
        for _, other, _, other_generator, other_cancel in families:
            if other_generator.gi_suspended:
                remaining = module._read_owner_attachment_cancellation(other)
                if remaining is None:
                    other_cancel()
                else:
                    module._release_owner_attachment_cancellation(other)


class _Value:
    pass


class _Hostile:
    def __getattribute__(self, name):
        raise AssertionError("foreign attribute access")

    def __eq__(self, other):
        raise AssertionError("foreign equality")

    def __hash__(self):
        raise AssertionError("foreign hashing")

    def __call__(self):
        raise AssertionError("foreign invocation")


class _RestampedCustody:
    __slots__ = ("__weakref__",)
    __getattribute__ = _Hostile.__getattribute__
    __eq__ = _Hostile.__eq__
    __hash__ = _Hostile.__hash__


def _owner(events, *, fail=False, during_cleanup=None):
    try:
        yield
    finally:
        events.append("cancel")
        if during_cleanup is not None:
            during_cleanup()
        if fail:
            raise RuntimeError("owner cleanup failed")


def _take(events, *, fail=False, during_cleanup=None):
    generator = _owner(events, fail=fail, during_cleanup=during_cleanup)
    next(generator)
    use, registration = _Value(), _Value()
    cancel = generator.close
    custody = lifetime._take_selected_owner_cancellation(use, registration, cancel)
    return custody, use, registration, generator, cancel


def test_exact_method_and_result_remain_held_until_explicit_release():
    events = []
    custody, use, registration, generator, cancel = _take(events)
    generator_ref, use_ref, registration_ref = ref(generator), ref(use), ref(registration)
    result = _Value()
    result_ref = ref(result)
    record = lifetime._record_by_identity(custody)
    assert record.cancellation is cancel
    lifetime._retain_selected_owner_result(custody, use, registration, result)
    del generator, cancel, use, registration, result
    gc.collect()
    assert generator_ref() is not None and use_ref() is not None
    assert registration_ref() is not None and result_ref() is not None
    assert events == []
    lifetime._release_selected_owner_cancellation(custody)
    gc.collect()
    assert events == ["cancel"]
    assert all(value() is None for value in (generator_ref, use_ref, registration_ref, result_ref))
    assert record.terminal


@pytest.mark.parametrize("fail", (False, True))
def test_bindings_clear_before_owner_cleanup_and_cleanup_is_never_retried(fail):
    events = []
    holder = []

    def verify_released():
        record = holder[0]
        assert record.terminal
        assert record.operation_use is record.registration is record.owner_result is record.cancellation is None
        assert record.cancellation_origin == ()

    custody, use, registration, _, _ = _take(events, fail=fail, during_cleanup=verify_released)
    holder.append(lifetime._record_by_identity(custody))
    lifetime._retain_selected_owner_result(custody, use, registration, _Value())
    if fail:
        with pytest.raises(RuntimeError, match="owner cleanup failed"):
            lifetime._release_selected_owner_cancellation(custody)
    else:
        lifetime._release_selected_owner_cancellation(custody)
    lifetime._release_selected_owner_cancellation(custody)
    assert events == ["cancel"]
    with pytest.raises(RuntimeError, match="terminal"):
        lifetime._retain_selected_owner_result(custody, use, registration, _Value())


@pytest.mark.parametrize("which", ("use", "registration", "missing_result", "duplicate"))
def test_bad_result_join_terminally_releases_only_that_custody(which):
    events, other_events = [], []
    custody, use, registration, _, _ = _take(events)
    other, _, _, _, _ = _take(other_events)
    try:
        if which == "duplicate":
            lifetime._retain_selected_owner_result(custody, use, registration, _Value())
        bad_use = _Hostile() if which == "use" else use
        bad_registration = _Hostile() if which == "registration" else registration
        result = None if which == "missing_result" else _Value()
        with pytest.raises((TypeError, RuntimeError)):
            lifetime._retain_selected_owner_result(custody, bad_use, bad_registration, result)
        assert events == ["cancel"] and other_events == []
        assert lifetime._record_by_identity(custody).terminal
        with pytest.raises(RuntimeError, match="terminal"):
            lifetime._retain_selected_owner_result(custody, use, registration, _Value())
    finally:
        lifetime._release_selected_owner_cancellation(other)


def test_rejection_and_owner_cleanup_errors_are_both_reported_without_retry():
    events = []
    custody, _use, registration, _, _ = _take(events, fail=True)
    with pytest.raises(BaseExceptionGroup) as caught:
        lifetime._retain_selected_owner_result(custody, _Hostile(), registration, _Value())
    assert len(caught.value.exceptions) == 2
    assert "substituted" in str(caught.value.exceptions[0])
    assert "cleanup failed" in str(caught.value.exceptions[1])
    lifetime._release_selected_owner_cancellation(custody)
    assert events == ["cancel"]


def test_retained_rejection_traceback_does_not_retain_use_registration_or_result():
    events = []
    custody, use, registration, generator, cancel = _take(events)
    result = _Value()
    refs = ref(use), ref(registration), ref(result), ref(generator)
    lifetime._retain_selected_owner_result(custody, use, registration, result)
    error = None
    try:
        lifetime._retain_selected_owner_result(custody, use, registration, result)
    except RuntimeError as caught:
        error = caught
    del use, registration, result, generator, cancel
    gc.collect()
    assert error is not None and error.__traceback__ is not None
    assert all(value() is None for value in refs)
    assert events == ["cancel"]


def _held_transfer_rejection(use, registration, cancellation):
    try:
        lifetime._take_selected_owner_cancellation(use, registration, cancellation)
    except (RuntimeError, TypeError) as error:
        return error
    finally:
        # The test caller must not supply the retention being measured.
        use = registration = cancellation = None
    raise AssertionError("transfer unexpectedly succeeded")


@pytest.mark.parametrize("which", ("duplicate", "missing_use", "missing_registration", "wrong_method"))
def test_held_transfer_rejection_does_not_extend_released_owner_custody(which):
    events = []
    custody, use, registration, generator, cancel = _take(events)
    refs = ref(use), ref(registration), ref(generator)
    arguments = (
        None if which == "missing_use" else use,
        None if which == "missing_registration" else registration,
        generator.send if which == "wrong_method" else cancel,
    )
    held_error = _held_transfer_rejection(*arguments)
    del arguments
    assert held_error.__traceback__ is not None
    assert events == []  # Rejection does not close the borrowed owner.
    lifetime._release_selected_owner_cancellation(custody)
    del use, registration, generator, cancel
    gc.collect()
    assert held_error.__traceback__ is not None
    assert all(value() is None for value in refs)
    assert events == ["cancel"]


@pytest.mark.parametrize("state", ("unprimed", "closed"))
def test_held_invalid_generator_rejection_does_not_retain_borrowed_arguments(state):
    events = []
    generator = _owner(events)
    use, registration = _Value(), _Value()
    if state == "closed":
        next(generator)
        generator.close()
    before = list(events)
    refs = ref(use), ref(registration), ref(generator)
    held_error = _held_transfer_rejection(use, registration, generator.close)
    assert events == before
    # External test-owner disposal; the rejection may not cancel it.
    generator.close()
    del use, registration, generator
    gc.collect()
    assert held_error.__traceback__ is not None
    assert all(value() is None for value in refs)


def test_held_wrong_resource_rejection_neither_closes_nor_retains_borrowed_resource():
    borrowed = StringIO("borrowed")
    use, registration = _Value(), _Value()
    refs = ref(use), ref(registration), ref(borrowed)
    held_error = _held_transfer_rejection(use, registration, borrowed.close)
    assert not borrowed.closed and borrowed.read() == "borrowed"
    borrowed.close()  # Only the external test owner closes this resource.
    del use, registration, borrowed
    gc.collect()
    assert held_error.__traceback__ is not None
    assert all(value() is None for value in refs)


def _observed_family(events):
    custody, use, registration, generator, _cancel = _take(events)
    result = _Value()
    lifetime._retain_selected_owner_result(custody, use, registration, result)
    return custody, (ref(use), ref(registration), ref(generator), ref(result))


def _held_unknown_rejection(action):
    try:
        if action == "lookup":
            lifetime._record_by_identity(_Hostile())
        elif action == "retain":
            lifetime._retain_selected_owner_result(_Hostile(), _Value(), _Value(), _Value())
        else:
            lifetime._release_selected_owner_cancellation(_Hostile())
    except TypeError as error:
        return error
    raise AssertionError("unknown custody unexpectedly accepted")


@pytest.mark.parametrize("action", ("lookup", "retain", "release"))
def test_held_unknown_rejection_cannot_pin_any_unrelated_family(action):
    events = [[], [], []]
    families = [_observed_family(owner_events) for owner_events in events]
    custody_refs = [ref(custody) for custody, _ in families]
    resource_refs = [value for _, refs in families for value in refs]
    held_error = _held_unknown_rejection(action)
    assert held_error.__traceback__ is not None
    assert events == [[], [], []]  # Unknown rejection must not cancel a family.
    del families  # Drop each legitimate fixture owner; preserve the error.
    gc.collect()
    assert all(value() is None for value in custody_refs + resource_refs)
    assert events == [["cancel"], ["cancel"], ["cancel"]]
    assert held_error.__traceback__ is not None


@pytest.mark.parametrize("action", ("retain", "release"))
def test_registered_restamping_releases_without_foreign_behavior(action):
    events = []
    custody, use, registration, _, _ = _take(events)
    original = type(custody)
    object.__setattr__(custody, "__class__", _RestampedCustody)
    try:
        if action == "retain":
            with pytest.raises(TypeError, match="original owner"):
                lifetime._retain_selected_owner_result(custody, use, registration, _Value())
        else:
            lifetime._release_selected_owner_cancellation(custody)
    finally:
        object.__setattr__(custody, "__class__", original)
    assert events == ["cancel"]
    with pytest.raises(RuntimeError, match="terminal"):
        lifetime._retain_selected_owner_result(custody, use, registration, _Value())


def test_unknown_hostile_custody_preserves_other_owner():
    events = []
    custody, use, registration, _, _ = _take(events)
    try:
        with pytest.raises(TypeError, match="registered"):
            lifetime._release_selected_owner_cancellation(_Hostile())
        with pytest.raises(TypeError, match="registered"):
            lifetime._retain_selected_owner_result(_Hostile(), use, registration, _Value())
        assert events == [] and not lifetime._record_by_identity(custody).terminal
    finally:
        lifetime._release_selected_owner_cancellation(custody)


@pytest.mark.parametrize("replacement", ("hostile", "different_native"))
def test_cancel_storage_substitution_still_closes_only_the_original_owner(replacement):
    events, other_events = [], []
    custody, use, registration, _, _ = _take(events)
    other_generator = _owner(other_events)
    next(other_generator)
    try:
        record = lifetime._record_by_identity(custody)
        object.__setattr__(
            record, "cancellation",
            _Hostile() if replacement == "hostile" else other_generator.close,
        )
        with pytest.raises(RuntimeError, match="storage substituted"):
            lifetime._retain_selected_owner_result(custody, use, registration, _Value())
        assert events == ["cancel"] and other_events == []
        assert record.terminal and record.cancellation_origin == ()
        lifetime._release_selected_owner_cancellation(custody)
        assert other_events == []
    finally:
        other_generator.close()


@pytest.mark.parametrize("action", ("retain", "release"))
def test_foreign_thread_cannot_dispatch_owner_cleanup(action):
    events, errors = [], []
    custody, use, registration, _, _ = _take(events)

    def run():
        try:
            if action == "retain":
                lifetime._retain_selected_owner_result(custody, use, registration, _Value())
            else:
                lifetime._release_selected_owner_cancellation(custody)
        except RuntimeError as error:
            errors.append(str(error))

    worker = Thread(target=run)
    worker.start()
    worker.join()
    assert errors and "original process/thread" in errors[0]
    assert events == []
    lifetime._release_selected_owner_cancellation(custody)
    assert events == ["cancel"]


@pytest.mark.skipif(not hasattr(os, "fork"), reason="real fork proof requires POSIX")
@pytest.mark.filterwarnings("ignore:.*multi-threaded.*fork.*:DeprecationWarning")
@pytest.mark.parametrize("action", ("lookup", "retain", "release", "transfer"))
def test_fork_refuses_before_parent_thread_held_registry_lock(action):
    events = []
    custody, use, registration, generator, cancel = _take(events)
    held, unlock = Event(), Event()

    def hold_registry_lock():
        with lifetime._REGISTRY_LOCK:
            held.set()
            unlock.wait(5)

    worker = Thread(target=hold_registry_lock)
    worker.start()
    assert held.wait(2)
    read_fd, write_fd = os.pipe()
    child = None
    try:
        child = os.fork()
        if child == 0:
            os.close(read_fd)
            signal.signal(signal.SIGALRM, lambda *_: os._exit(124))
            signal.alarm(2)
            try:
                if action == "lookup":
                    lifetime._record_by_identity(custody)
                elif action == "retain":
                    lifetime._retain_selected_owner_result(custody, use, registration, _Value())
                elif action == "release":
                    lifetime._release_selected_owner_cancellation(custody)
                else:
                    lifetime._take_selected_owner_cancellation(use, registration, cancel)
            except RuntimeError as error:
                if "original process/thread" in str(error) and events == []:
                    os.write(write_fd, b"refused_without_cleanup")
                    os._exit(0)
            # Exit without inherited owner teardown or pytest cleanup.
            os._exit(125)
        os.close(write_fd)
        write_fd = None
        ready, _, _ = select.select([read_fd], [], [], 3)
        if not ready:
            os.kill(child, signal.SIGKILL)
        _, status = os.waitpid(child, 0)
        child = None
        assert ready, "child did not promptly refuse inherited custody"
        assert os.waitstatus_to_exitcode(status) == 0
        assert os.read(read_fd, 64) == b"refused_without_cleanup"
    finally:
        if child not in (None, 0):
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
        os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)
        unlock.set()
        worker.join(2)
        assert not worker.is_alive()
    record = lifetime._record_by_identity(custody)
    assert not record.terminal and record.cancellation is cancel
    assert record.operation_use is use and record.registration is registration
    assert generator.gi_suspended and events == []
    lifetime._release_selected_owner_cancellation(custody)
    assert events == ["cancel"]


def test_second_transfer_of_same_generator_preserves_original_custody():
    events = []
    custody, use, registration, generator, _ = _take(events)
    try:
        with pytest.raises(RuntimeError, match="already transferred"):
            lifetime._take_selected_owner_cancellation(use, registration, generator.close)
        assert events == []
    finally:
        lifetime._release_selected_owner_cancellation(custody)


def test_uncertain_cleanup_cannot_transfer_the_same_generator_again():
    events = []

    def ignores_exit():
        try:
            yield
        except GeneratorExit:
            events.append("ignored exit")
            yield

    generator = ignores_exit()
    next(generator)
    use, registration = _Value(), _Value()
    custody = lifetime._take_selected_owner_cancellation(use, registration, generator.close)
    try:
        with pytest.raises(RuntimeError, match="ignored GeneratorExit"):
            lifetime._release_selected_owner_cancellation(custody)
        assert lifetime._record_by_identity(custody).terminal
        with pytest.raises(RuntimeError, match="already transferred"):
            lifetime._take_selected_owner_cancellation(use, registration, generator.close)
        lifetime._release_selected_owner_cancellation(custody)
        assert events == ["ignored exit"]
    finally:
        # Test-owner disposal, not a Workspace retry of uncertain cleanup.
        generator.close()


@pytest.mark.parametrize("missing", ("use", "registration"))
def test_missing_storage_key_does_not_take_or_close_owner_generator(missing):
    events = []
    generator = _owner(events)
    next(generator)
    try:
        with pytest.raises(TypeError, match="storage keys"):
            lifetime._take_selected_owner_cancellation(
                None if missing == "use" else _Value(),
                None if missing == "registration" else _Value(),
                generator.close,
            )
        assert events == []
        assert generator not in lifetime._TRANSFERRED
    finally:
        generator.close()


@pytest.mark.parametrize("kind", ("hostile", "callback", "object", "none"))
def test_foreign_callable_is_never_dispatched(kind):
    cancellation = {
        "hostile": _Hostile(), "callback": lambda: None, "object": object(), "none": None,
    }[kind]
    with pytest.raises(TypeError, match="native generator close"):
        lifetime._take_selected_owner_cancellation(_Value(), _Value(), cancellation)


def test_wrong_generator_method_and_unprimed_or_closed_generator_refuse():
    events = []
    generator = _owner(events)
    with pytest.raises(RuntimeError, match="primed"):
        lifetime._take_selected_owner_cancellation(_Value(), _Value(), generator.close)
    next(generator)
    with pytest.raises(TypeError, match="native generator close"):
        lifetime._take_selected_owner_cancellation(_Value(), _Value(), generator.send)
    generator.close()
    with pytest.raises(RuntimeError, match="primed"):
        lifetime._take_selected_owner_cancellation(_Value(), _Value(), generator.close)
    assert events == ["cancel"]


def test_borrowed_resource_close_is_not_taken_or_called():
    borrowed = StringIO("borrowed")
    try:
        with pytest.raises(TypeError, match="native generator close"):
            lifetime._take_selected_owner_cancellation(_Value(), _Value(), borrowed.close)
        assert not borrowed.closed
        assert borrowed.read() == "borrowed"
    finally:
        borrowed.close()


def test_custody_has_no_public_constructor_or_portable_form():
    with pytest.raises(TypeError, match="transfer"):
        lifetime._SelectedOwnerCancellationCustody()
    events = []
    custody, _, _, _, _ = _take(events)
    try:
        with pytest.raises(TypeError, match="process-local"):
            pickle.dumps(custody)
    finally:
        lifetime._release_selected_owner_cancellation(custody)
