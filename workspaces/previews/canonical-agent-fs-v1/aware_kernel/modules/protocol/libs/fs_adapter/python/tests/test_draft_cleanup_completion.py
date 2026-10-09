"""Original owner completion, never phase/FD-count or caller-DTO inference."""

from __future__ import annotations

import gc
import os
import threading
from dataclasses import FrozenInstanceError

import pytest
from aware_file_system import retained_package as physical
from aware_protocol_fs_adapter import specification_draft_target as owner
from aware_protocol_fs_adapter import specification_selection as selection_owner
from test_draft_input_custody import Context


@pytest.fixture
def context(tmp_path):
    value = Context(tmp_path)
    yield value
    value.close()


@pytest.mark.parametrize("transferred", [False, True])
def test_original_completion_is_detached_and_preserves_physical_ownership(
    context, transferred
):
    handle = context.transfer() if transferred else context.reserve()
    before = owner.observe_specification_draft_input(handle)
    assert before.owner_cleanup_attempted is False
    assert before.owner_cleanup_outcome == "not_attempted"
    after = owner.release_specification_draft_input(handle)
    assert after.owner_cleanup_attempted is True
    assert after.owner_cleanup_outcome == "completed"
    assert owner.release_specification_draft_input(handle) == after
    assert owner.observe_specification_draft_input(handle) == after
    assert context.plan.phase == ("planned" if transferred else "released")
    assert before.owner_cleanup_outcome == "not_attempted"
    with pytest.raises(FrozenInstanceError):
        after.owner_cleanup_outcome = "unknown"
    with pytest.raises(
        owner.SpecificationDraftSelectionError,
        match="terminal" if transferred else "claim_required",
    ):
        owner.require_specification_draft_target(
            context.target, input_claim=context.claim
        )


@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt])
@pytest.mark.parametrize("when", ["before_close", "after_close"])
def test_actual_descriptor_failure_never_retries_or_upgrades(
    context, monkeypatch, failure, when
):
    handle = context.transfer()
    state = owner._ISSUED[context.target]
    descriptor = selection_owner._retained(state.selection).repository_fd
    original = os.close
    calls = []

    def fail(fd):
        if fd != descriptor:
            return original(fd)
        calls.append(fd)
        if when == "after_close":
            original(fd)
        raise failure("controlled original close interruption")

    with monkeypatch.context() as patch:
        patch.setattr(selection_owner.os, "close", fail)
        with pytest.raises(owner.SpecificationDraftInputCustodyRefusal) as caught:
            owner.release_specification_draft_input(handle)
        after = caught.value.input_observation
        assert after.owner_cleanup_attempted is True
        assert after.owner_cleanup_outcome == "incomplete"
        assert any("cleanup" in item for item in after.diagnostics)
    with pytest.raises(owner.SpecificationDraftInputCustodyRefusal) as replay:
        owner.release_specification_draft_input(handle)
    assert replay.value.input_observation == after
    assert owner.observe_specification_draft_input(handle) == after
    assert len(calls) == 1
    assert context.plan.phase == "planned"
    if when == "before_close":
        original(descriptor)  # Test-only disposal, never product retry evidence.
    # Reusing the old number must not let any product retry close foreign state.
    foreign = os.open(context.root, os.O_RDONLY | os.O_DIRECTORY)
    if foreign != descriptor:
        os.dup2(foreign, descriptor)
        original(foreign)
    try:
        with pytest.raises(owner.SpecificationDraftInputCustodyRefusal):
            owner.release_specification_draft_input(handle)
        assert os.fstat(descriptor).st_ino == context.root.stat().st_ino
    finally:
        original(descriptor)
    context.claim = None  # Failed release is terminal; fixture must not retry it.
    context.reservation = None


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_retirement_failure_cannot_be_healed_by_later_normal_release(
    context, monkeypatch, failure
):
    handle = context.transfer()
    state = owner._ISSUED[context.target]
    original = owner._release_owned_selection
    calls = []

    def fail(value):
        calls.append(value)
        raise failure("controlled retirement interruption")

    with monkeypatch.context() as patch:
        patch.setattr(owner, "_release_owned_selection", fail)
        context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
        with pytest.raises((owner.SpecificationDraftSelectionError, failure)):
            context.target.revalidate(input_claim=handle)
    before = owner.observe_specification_draft_input(handle)
    assert before.owner_cleanup_attempted is True
    assert before.owner_cleanup_outcome == "incomplete"
    after = owner.release_specification_draft_input(handle)
    assert after.release_invocation == "returned"
    assert after.owner_cleanup_outcome == "incomplete"
    assert len(calls) == 1
    original(state.selection)  # Test-only disposal must not improve target ledger.
    assert owner.observe_specification_draft_input(handle).owner_cleanup_outcome == (
        "incomplete"
    )


def test_normal_return_and_terminal_phase_are_not_completion(context, monkeypatch):
    handle = context.transfer()
    state = owner._ISSUED[context.target]
    original = owner._release_owned_selection
    with monkeypatch.context() as patch:
        patch.setattr(owner, "_release_owned_selection", lambda value: None)
        with pytest.raises(owner.SpecificationDraftInputCustodyRefusal) as caught:
            owner.release_specification_draft_input(handle)
    assert context.target.phase == "released"
    assert caught.value.input_observation.owner_cleanup_outcome == "unknown"
    original(state.selection)
    assert owner.observe_specification_draft_input(handle).owner_cleanup_outcome == (
        "unknown"
    )
    context.claim = None
    context.reservation = None


def test_later_observation_failure_extends_terminal_cleanup_history(
    context, monkeypatch
):
    handle = context.transfer()
    state = owner._ISSUED[context.target]
    original = owner._release_owned_selection

    def fail_release(value):
        raise RuntimeError("controlled original cleanup failure")

    with monkeypatch.context() as patch:
        patch.setattr(owner, "_release_owned_selection", fail_release)
        context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
        with pytest.raises(owner.SpecificationDraftSelectionError):
            context.target.revalidate(input_claim=handle)
    before = owner.observe_specification_draft_input(handle)

    def fail_observe(value):
        raise OSError("controlled later physical observer loss")

    with monkeypatch.context() as patch:
        patch.setattr(physical, "observe_package_input", fail_observe)
        after = owner.observe_specification_draft_input(handle)
        assert after.diagnostics[: len(before.diagnostics)] == before.diagnostics
        assert len(after.diagnostics) == len(before.diagnostics) + 1
        assert owner.observe_specification_draft_input(handle) == after
        assert after.owner_cleanup_outcome == "incomplete"
        assert before.owner_cleanup_outcome == "incomplete"
    original(state.selection)  # Test-only disposal does not repair owner history.


def test_completed_retirement_can_later_enroll_cleanup_only_custody(context):
    context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
    with pytest.raises(owner.SpecificationDraftSelectionError):
        context.target.revalidate()
    handle = context.reserve()
    evidence = owner.observe_specification_draft_input(handle)
    assert evidence.owner_cleanup_attempted is True
    assert evidence.owner_cleanup_outcome == "completed"
    receiver = object()
    context.physical_claim = physical.transfer_package_input(
        handle.physical_reservation, receiver=receiver
    )
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="cleanup_only"
    ):
        owner.transfer_specification_draft_input(
            handle, physical_claim=context.physical_claim, receiver=receiver
        )


def test_competing_release_reports_once_only_original_completion(context, monkeypatch):
    handle = context.transfer()
    original = owner._release_owned_selection
    calls = []
    barrier = threading.Barrier(2)
    results = []

    def counted(selection):
        calls.append(selection)
        original(selection)

    def release():
        barrier.wait()
        results.append(owner.release_specification_draft_input(handle))

    monkeypatch.setattr(owner, "_release_owned_selection", counted)
    threads = [threading.Thread(target=release), threading.Thread(target=release)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert len(results) == 2 and results[0] == results[1]
    assert results[0].owner_cleanup_outcome == "completed"
    assert len(calls) == 1
    assert context.plan.phase == "planned"


def test_claim_collection_keeps_original_completion_and_physical_claim(context):
    context.transfer()
    context.claim = None
    gc.collect()
    evidence = owner.observe_specification_draft_input(context.reservation)
    assert evidence.owner_cleanup_attempted is True
    assert evidence.owner_cleanup_outcome == "completed"
    assert context.plan.phase == "planned"
    assert context.target.phase == "released"
    context.reservation = None  # Collected transferred claim is already spent.


@pytest.mark.parametrize("correlation_failed", [False, True])
@pytest.mark.parametrize("descriptor_failed", [False, True])
def test_original_selection_tracks_both_cleanup_components_once(
    tmp_path, monkeypatch, correlation_failed, descriptor_failed
):
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    original_close = os.close
    calls = []

    class Correlation:
        def release(self):
            calls.append("correlation")
            if correlation_failed:
                raise KeyboardInterrupt("controlled reader close interruption")

    resources = selection_owner._SelectionResources(descriptor, Correlation())

    def close(value):
        calls.append("descriptor")
        original_close(value)
        if descriptor_failed:
            raise OSError("controlled post-close refusal")

    with monkeypatch.context() as patch:
        patch.setattr(selection_owner.os, "close", close)
        if correlation_failed or descriptor_failed:
            with pytest.raises((KeyboardInterrupt, OSError)):
                selection_owner._cleanup_selection(resources)
        else:
            selection_owner._cleanup_selection(resources)
        selection_owner._cleanup_selection(resources)
    assert calls == ["correlation", "descriptor"]
    assert resources.cleanup_attempted is True
    assert resources.cleanup_outcome == (
        "incomplete" if correlation_failed or descriptor_failed else "completed"
    )
    assert len(resources.cleanup_diagnostics) == (
        int(correlation_failed) + int(descriptor_failed)
    )
