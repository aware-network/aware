"""Real Protocol -> FileSystem custody; not Issue or installed CLI acceptance."""

from __future__ import annotations

import copy
import gc
import os
import pickle
import threading
from dataclasses import FrozenInstanceError
from pathlib import Path
from weakref import ref

import pytest
from aware_file_system import retained_package as physical
from aware_protocol_fs_adapter import specification_draft_target as owner
from aware_protocol_fs_adapter.specification_selection import (
    release_specification_selection,
    require_specification_selection,
)
from test_specification_draft_target import digest, new_context


class Context:
    def __init__(self, root):
        self.root, self.manifest, self.target, self.plan = new_context(root)
        self.reservation = self.claim = self.physical_claim = None
        self.reader = None

    def reserve(self):
        self.reservation = owner.reserve_specification_draft_input(
            self.target,
            physical_plan=self.plan,
            attempt_ref="attempt:original",
            client_intent_id="intent:original",
        )
        return self.reservation

    def transfer(self):
        if self.reservation is None:
            self.reserve()
        self.receiver = object()
        self.physical_claim = physical.transfer_package_input(
            self.reservation.physical_reservation, receiver=self.receiver
        )
        self.claim = owner.transfer_specification_draft_input(
            self.reservation,
            physical_claim=self.physical_claim,
            receiver=self.receiver,
        )
        return self.claim

    def close(self):
        if self.reader is not None:
            release_specification_selection(self.reader)
        if self.physical_claim is not None:
            physical.release_package_input(self.physical_claim)
        if self.claim is not None:
            owner.release_specification_draft_input(self.claim)
        elif self.reservation is not None:
            owner.release_specification_draft_input(self.reservation)
        else:
            try:
                owner.release_specification_draft_target(self.target)
            except owner.SpecificationDraftInputCustodyRefusal:
                assert self.target.phase == "released"
            try:
                self.plan.release()
            except physical.PackageInputCustodyRefusal:
                assert self.plan.phase == "released"


@pytest.fixture
def context(tmp_path):
    value = Context(tmp_path)
    yield value
    value.close()


def fd_count():
    return len(os.listdir("/proc/self/fd"))


def test_historical_binding_and_snapshot_never_validate_freshness(context):
    original = digest(context.manifest.read_bytes())
    context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
    reservation = context.reserve()
    observation = owner.observe_specification_draft_input(reservation)
    assert observation.manifest_sha256 == original
    assert observation.manifest_locator == "aware.protocol.toml"
    assert observation.root_locator == str(context.root)
    assert observation.target_locator == "customer/specs/widget"
    assert observation.physical.binding.ordered_members == (
        ("README.md", b"draft"),
        ("aware.spec.toml", b"owned parser input"),
    )
    assert context.target.phase == "absent" and context.plan.phase == "planned"
    assert observation.owner_cleanup_attempted is False
    assert observation.owner_cleanup_outcome == "not_attempted"
    with pytest.raises(FrozenInstanceError):
        observation.resource_state = "transferred"
    released = owner.release_specification_draft_input(reservation)
    assert released.resource_state == "released"
    assert released.physical.owner_cleanup_outcome == "completed"
    assert released.owner_cleanup_outcome == "completed"
    assert observation.resource_state == "reserved"
    assert owner.observe_specification_draft_input(reservation) == released


@pytest.mark.parametrize("stale", [False, True])
def test_target_conflict_precedes_physical_acquisition_and_freshness(context, stale):
    reservation = context.reserve()
    if stale:
        context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
    before = owner.observe_specification_draft_input(reservation)
    new_plan = physical.retain_package_publication(
        root=context.root,
        target_path="customer/specs/widget",
        scratch_path="customer/specs/.aware-spec-draft-" + "b" * 32,
        ordered_members=(("README.md", b"second"),),
    )
    descriptors = fd_count()
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="already_owned"
    ):
        owner.reserve_specification_draft_input(
            context.target,
            physical_plan=new_plan,
            attempt_ref="second",
            client_intent_id="second",
        )
    assert owner.observe_specification_draft_input(reservation) == before
    assert context.target.phase == "absent"
    assert new_plan.phase == "planned"
    new_plan.release()  # Genuine newly created unreserved owner disposal.
    assert fd_count() == descriptors - 3


def test_physical_conflict_disposes_only_new_target(context):
    context.reserve()
    before = owner.observe_specification_draft_input(context.reservation)
    second = owner.admit_specification_draft_target(
        repository_root=context.root,
        manifest_path=Path("aware.protocol.toml"),
        selected_manifest_path="customer/specs/widget/aware.spec.toml",
        expected_manifest_sha256=digest(context.manifest.read_bytes()),
    )
    descriptors = fd_count()
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="reservation_failed"
    ) as caught:
        owner.reserve_specification_draft_input(
            second,
            physical_plan=context.plan,
            attempt_ref="second",
            client_intent_id="second",
        )
    assert caught.value.input_observation.physical is None
    assert second.phase == "released"
    assert fd_count() == descriptors - 1
    assert owner.observe_specification_draft_input(context.reservation) == before


RAW = (
    lambda c, claim: owner.require_specification_draft_target(
        c.target, input_claim=claim
    ),
    lambda c, claim: c.target.revalidate(input_claim=claim),
    lambda c, claim: owner.bind_specification_draft_physical_plan(
        c.target, physical_plan=c.plan, input_claim=claim
    ),
    lambda c, claim: owner.spend_specification_draft_publication(
        c.target, input_claim=claim
    ),
    lambda c, claim: owner.admit_specification_draft_published_read(
        c.target, physical_postimage=object(), input_claim=claim
    ),
    lambda c, claim: owner.finish_specification_draft_target(
        c.target, read_selection=object(), input_claim=claim
    ),
    lambda c, claim: owner.release_specification_draft_target(
        c.target, input_claim=claim
    ),
)


@pytest.mark.parametrize("entrance", RAW)
@pytest.mark.parametrize("kind", ["missing", "reservation", "forged"])
@pytest.mark.parametrize("stale", [False, True])
def test_reserved_raw_entrances_refuse_before_retirement(
    context, entrance, kind, stale
):
    reservation = context.reserve()
    if stale:
        context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
    before = owner.observe_specification_draft_input(reservation)
    claim = {
        "missing": None,
        "reservation": reservation,
        "forged": object.__new__(owner.SpecificationDraftInputClaim),
    }[kind]
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="claim_required"
    ):
        entrance(context, claim)
    assert owner.observe_specification_draft_input(reservation) == before
    assert context.target.phase == "absent" and context.plan.phase == "planned"


def test_manifest_getter_cannot_retire_reserved_target(context):
    context.reserve()
    context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="claim_required"
    ):
        _ = context.target.manifest_locator
    assert context.target.phase == "absent"


def test_transferred_freshness_refuses_and_disposal_remains_available(context):
    context.transfer()
    context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
    with pytest.raises(owner.SpecificationDraftSelectionError):
        owner.require_specification_draft_target(
            context.target, input_claim=context.claim
        )
    assert context.target.phase == "retired"
    assert context.plan.phase == "planned"
    owner.release_specification_draft_input(context.claim)
    assert context.plan.phase == "planned"  # Issue still owns the physical claim.
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="cleanup_transferred"
    ):
        owner.release_specification_draft_input(context.reservation)


def test_real_publication_read_and_reader_lifetime(context):
    context.transfer()
    owner.bind_specification_draft_physical_plan(
        context.target,
        physical_plan=context.plan,
        input_claim=context.claim,
        physical_input_claim=context.physical_claim,
    )
    while context.plan.phase != "staged":
        context.plan.stage_next_effect(input_claim=context.physical_claim)
        owner.require_specification_draft_target(
            context.target, input_claim=context.claim
        )
    owner.spend_specification_draft_publication(
        context.target, input_claim=context.claim
    )
    image = context.plan.publish_package(input_claim=context.physical_claim)
    context.reader = owner.admit_specification_draft_published_read(
        context.target, physical_postimage=image, input_claim=context.claim
    )
    owner.finish_specification_draft_target(
        context.target, read_selection=context.reader, input_claim=context.claim
    )
    context.plan.finish(image, input_claim=context.physical_claim)
    physical.release_package_input(context.physical_claim)
    owner.require_specification_draft_target(context.target, input_claim=context.claim)
    completion = owner.release_specification_draft_input(context.claim)
    assert completion.owner_cleanup_attempted is True
    assert completion.owner_cleanup_outcome == "completed"
    require_specification_selection(context.reader)
    assert (context.root / "customer/specs/widget/README.md").read_bytes() == b"draft"
    with pytest.raises(owner.SpecificationDraftSelectionError, match="terminal"):
        owner.require_specification_draft_target(
            context.target, input_claim=context.claim
        )


@pytest.mark.parametrize("kind", ["reservation", "claim"])
@pytest.mark.parametrize("operation", [copy.copy, copy.deepcopy, pickle.dumps])
def test_original_inputs_cannot_be_copied(context, kind, operation):
    context.transfer() if kind == "claim" else context.reserve()
    value = context.claim if kind == "claim" else context.reservation
    with pytest.raises(TypeError):
        operation(value)


@pytest.mark.parametrize(
    "kind",
    [owner.SpecificationDraftInputReservation, owner.SpecificationDraftInputClaim],
)
@pytest.mark.parametrize(
    "entrance",
    [owner.observe_specification_draft_input, owner.release_specification_draft_input],
)
def test_forged_originals_refuse(kind, entrance):
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="original_local"
    ):
        entrance(object.__new__(kind))


@pytest.mark.parametrize(
    "text",
    ["", " padded", "bad\0", "bad\n", "bad\x7f", "bad\x85", "e\u0301", "a" * 1025],
)
@pytest.mark.parametrize("field", ["attempt_ref", "client_intent_id"])
def test_invalid_correlation_does_not_acquire(context, text, field):
    kwargs = {"attempt_ref": "original", "client_intent_id": "original", field: text}
    with pytest.raises(ValueError):
        owner.reserve_specification_draft_input(
            context.target, physical_plan=context.plan, **kwargs
        )
    assert context.target.phase == "absent" and context.plan.phase == "planned"
    context.reserve()


@pytest.mark.parametrize("where", ["reservation", "transfer"])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt])
def test_finalizer_issuance_failure_disposes_only_owned_resources(
    context, monkeypatch, where, error_type
):
    if where == "transfer":
        context.reserve()
        context.receiver = object()
        context.physical_claim = physical.transfer_package_input(
            context.reservation.physical_reservation, receiver=context.receiver
        )

    def fail(*args, **kwargs):
        raise error_type("controlled finalizer failure")

    monkeypatch.setattr(owner, "finalize", fail)
    if where == "reservation":
        with pytest.raises(owner.SpecificationDraftInputCustodyRefusal):
            context.reserve()
        assert context.plan.phase == "released"
    else:
        with pytest.raises(owner.SpecificationDraftInputCustodyRefusal):
            owner.transfer_specification_draft_input(
                context.reservation,
                physical_claim=context.physical_claim,
                receiver=context.receiver,
            )
        assert (
            context.plan.phase == "planned"
        )  # Physical transfer survives for coordinator cleanup.
    assert context.target.phase == "released"


def test_reservation_collection_disposes_joint_inputs(tmp_path):
    context = Context(tmp_path)
    baseline = fd_count()
    reservation = context.reserve()
    weak = ref(reservation)
    context.reservation = None
    del reservation
    gc.collect()
    assert weak() is None
    assert context.target.phase == context.plan.phase == "released"
    assert fd_count() == baseline - 4


def test_old_reservation_collection_does_not_dispose_transferred_target(context):
    context.transfer()
    weak = ref(context.reservation)
    context.reservation = None
    gc.collect()
    assert weak() is None
    assert context.target.phase == "absent"
    owner.require_specification_draft_target(context.target, input_claim=context.claim)


@pytest.mark.parametrize("iteration", range(12))
def test_real_transfer_release_race_preserves_single_terminal_owner(context, iteration):
    context.reserve()
    receiver = object()
    context.physical_claim = physical.transfer_package_input(
        context.reservation.physical_reservation, receiver=receiver
    )
    barrier = threading.Barrier(2)
    results = []

    def transfer():
        barrier.wait()
        try:
            results.append(
                owner.transfer_specification_draft_input(
                    context.reservation,
                    physical_claim=context.physical_claim,
                    receiver=receiver,
                )
            )
        except owner.SpecificationDraftInputCustodyRefusal:
            results.append("transfer-refused")

    def release():
        barrier.wait()
        try:
            results.append(owner.release_specification_draft_input(context.reservation))
        except owner.SpecificationDraftInputCustodyRefusal:
            results.append("release-refused")

    threads = [threading.Thread(target=transfer), threading.Thread(target=release)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert len(results) == 2
    claims = [r for r in results if type(r) is owner.SpecificationDraftInputClaim]
    if claims:
        context.claim = claims[0]
        assert "release-refused" in results
        assert context.target.phase == "absent"
    else:
        assert "transfer-refused" in results
        assert context.target.phase == "released"
    assert context.plan.phase == "planned"


def test_foreign_process_inputs_do_not_touch_inherited_resources(context):
    context.reserve()
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        before = fd_count()
        try:
            for operation in (
                owner.observe_specification_draft_input,
                owner.release_specification_draft_input,
            ):
                try:
                    operation(context.reservation)
                    os._exit(2)
                except owner.SpecificationDraftInputCustodyRefusal:
                    pass
            os.write(write_fd, b"ok" if fd_count() == before else b"bad")
            os._exit(0)
        except BaseException:  # noqa: BLE001 -- report child proof failure without pytest teardown
            os._exit(3)
    os.close(write_fd)
    result = os.read(read_fd, 16)
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    assert status == 0 and result == b"ok"
    assert context.target.phase == "absent" and context.plan.phase == "planned"


def test_unavailable_observation_does_not_prevent_capability_guarded_cleanup(
    context, monkeypatch
):
    def fail(value):
        raise KeyboardInterrupt("controlled observation loss")

    monkeypatch.setattr(physical, "observe_package_input", fail)
    before = fd_count()
    with pytest.raises(owner.SpecificationDraftInputCustodyRefusal) as caught:
        context.reserve()
    assert (
        caught.value.input_observation.physical is not None
    )  # Original release returned the ledger.
    assert context.target.phase == context.plan.phase == "released"
    assert fd_count() == before - 4


@pytest.mark.parametrize("wrong", ["receiver", "claim", "reservation"])
def test_wrong_physical_transfer_does_not_spend_original(context, wrong):
    context.reserve()
    receiver = object()
    context.physical_claim = physical.transfer_package_input(
        context.reservation.physical_reservation, receiver=receiver
    )
    value = {
        "receiver": context.physical_claim,
        "claim": object(),
        "reservation": context.reservation.physical_reservation,
    }[wrong]
    with pytest.raises(owner.SpecificationDraftInputCustodyRefusal):
        owner.transfer_specification_draft_input(
            context.reservation,
            physical_claim=value,
            receiver=object() if wrong == "receiver" else receiver,
        )
    assert context.target.phase == "absent"
    assert (
        owner.observe_specification_draft_input(context.reservation).transfer_state
        == "not_attempted"
    )
    context.claim = owner.transfer_specification_draft_input(
        context.reservation, physical_claim=context.physical_claim, receiver=receiver
    )


@pytest.mark.parametrize("terminal", ["retired", "released"])
def test_terminal_target_can_retain_cleanup_only_custody(context, terminal):
    if terminal == "released":
        owner.release_specification_draft_target(context.target)
    else:
        context.manifest.write_bytes(context.manifest.read_bytes() + b"\n# stale\n")
        with pytest.raises(owner.SpecificationDraftSelectionError):
            context.target.revalidate()
    context.reserve()
    receiver = object()
    context.physical_claim = physical.transfer_package_input(
        context.reservation.physical_reservation, receiver=receiver
    )
    with pytest.raises(
        owner.SpecificationDraftInputCustodyRefusal, match="cleanup_only"
    ):
        owner.transfer_specification_draft_input(
            context.reservation,
            physical_claim=context.physical_claim,
            receiver=receiver,
        )
    assert context.target.phase == terminal


@pytest.mark.parametrize(
    "missing",
    [
        "reserve_package_input",
        "observe_package_input",
        "require_package_input_claim",
        "release_package_input",
    ],
)
def test_missing_custody_port_refuses_without_physical_acquisition(
    context, monkeypatch, missing
):
    monkeypatch.setattr(physical, missing, None)
    before = fd_count()
    with pytest.raises(owner.SpecificationDraftInputCustodyRefusal):
        context.reserve()
    assert context.target.phase == "released"
    assert context.plan.phase == "planned"
    assert fd_count() == before - 1


@pytest.mark.parametrize("iteration", range(12))
def test_real_competing_joint_reservations_have_one_winner(context, iteration):
    barrier = threading.Barrier(2)
    results = []

    def reserve():
        barrier.wait()
        try:
            results.append(
                owner.reserve_specification_draft_input(
                    context.target,
                    physical_plan=context.plan,
                    attempt_ref="racing",
                    client_intent_id="racing",
                )
            )
        except owner.SpecificationDraftInputCustodyRefusal:
            results.append("refused")

    threads = [threading.Thread(target=reserve), threading.Thread(target=reserve)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert len(results) == 2 and results.count("refused") == 1
    context.reservation = next(
        r for r in results if type(r) is owner.SpecificationDraftInputReservation
    )
    assert context.target.phase == "absent" and context.plan.phase == "planned"


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt])
def test_physical_release_failure_preserves_evidence_and_target_disposal(
    context, monkeypatch, error_type
):
    context.reserve()
    original = physical.release_package_input
    calls = []

    def release(value):
        calls.append(value)
        result = original(value)
        raise physical.PackageInputCustodyRefusal(
            "controlled_after_release", input_observation=result
        ) from error_type()

    monkeypatch.setattr(physical, "release_package_input", release)
    with pytest.raises(owner.SpecificationDraftInputCustodyRefusal) as caught:
        owner.release_specification_draft_input(context.reservation)
    assert caught.value.input_observation.physical.owner_cleanup_outcome == "completed"
    assert caught.value.input_observation.owner_cleanup_outcome == "completed"
    assert caught.value.input_observation.release_invocation == "raised"
    assert context.target.phase == context.plan.phase == "released"
    with pytest.raises(owner.SpecificationDraftInputCustodyRefusal):
        owner.release_specification_draft_input(context.reservation)
    assert len(calls) == 1
    context.reservation = (
        None  # Both effects are already terminal; never fixture-retry unknown cleanup.
    )
