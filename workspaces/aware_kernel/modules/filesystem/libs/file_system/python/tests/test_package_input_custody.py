"""Genuine FileSystem custody proofs, not Issue/Protocol admission assertions."""

import copy
import gc
import os
import pickle
import threading
import tomllib
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
from aware_file_system import retained_package as owner


def plan(root, target="package"):
    return owner.retain_package_publication(
        root=root,
        target_path=target,
        ordered_members=(("a.txt", b"one"), ("nested/b.txt", b"two")),
    )


def reserve(value, attempt="attempt:one"):
    return owner.reserve_package_input(
        value, attempt_ref=attempt, client_intent_id="intent:one"
    )


def transferred(value):
    reservation = reserve(value)
    receiver = object()
    claim = owner.transfer_package_input(reservation, receiver=receiver)
    return reservation, receiver, claim


def descriptor_count():
    return len(os.listdir("/proc/self/fd"))


def forbidden_freshness(state):
    raise AssertionError("An unauthorized entrance reached freshness")


def test_exact_observation_schema_and_no_freshness_acquisition(tmp_path, monkeypatch):
    value = plan(tmp_path)
    before = owner.observe_package_plan(value)
    monkeypatch.setattr(owner, "_verify", forbidden_freshness)
    reservation = reserve(value)
    observation = owner.observe_package_input(reservation)
    assert observation.binding == before
    assert observation.resource_state == "reserved"
    assert observation.transfer_state == "not_attempted"
    assert observation.release_invocation == "not_invoked"
    assert observation.owner_cleanup_attempted is False
    assert observation.owner_cleanup_outcome == "not_attempted"
    assert [field.name for field in fields(observation)] == [
        "attempt_ref",
        "client_intent_id",
        "resource_state",
        "transfer_state",
        "release_invocation",
        "owner_cleanup_attempted",
        "owner_cleanup_outcome",
        "diagnostics",
        "binding",
        "cleanup",
    ]
    with pytest.raises(FrozenInstanceError):
        observation.resource_state = "transferred"
    # This historical view does not revalidate or grant publication.
    assert not (tmp_path / value.scratch_path).exists()
    after = owner.release_package_input(reservation)
    assert after.owner_cleanup_outcome == "completed"
    assert observation.resource_state == "reserved"


@pytest.mark.parametrize("state_kind", ["reserved", "transferred"])
@pytest.mark.parametrize(
    "entrance",
    [
        "validate",
        "stage",
        "next",
        "lend",
        "publish",
        "finish",
        "release",
        "require",
        "observe",
        "plan",
        "lens",
        "image",
        "require_image",
    ],
)
@pytest.mark.parametrize("wrong", ["none", "reservation", "forged", "snapshot"])
def test_all_borrowed_entrances_refuse_before_freshness_or_retirement(
    tmp_path, monkeypatch, state_kind, entrance, wrong
):
    value = plan(tmp_path)
    reservation = reserve(value)
    claim = None
    if state_kind == "transferred":
        claim = owner.transfer_package_input(reservation, receiver=object())
    kwargs = {
        "input_claim": {
            "none": None,
            "reservation": reservation,
            "forged": object.__new__(owner.PackageInputClaim),
            "snapshot": owner.observe_package_input(reservation),
        }[wrong]
    }
    calls = {
        "validate": lambda: value.validate_current(**kwargs),
        "stage": lambda: value.stage(**kwargs),
        "next": lambda: value.stage_next_effect(**kwargs),
        "lend": lambda: value.lend_staged_source(**kwargs),
        "publish": lambda: value.publish_package(**kwargs),
        "finish": lambda: value.finish(object(), **kwargs),
        "release": lambda: value.release(**kwargs),
        "require": lambda: owner.require_retained_package_plan(value, **kwargs),
        "observe": lambda: owner.observe_package_plan(value, **kwargs),
        "plan": lambda: owner.validate_package_plan(
            value,
            root=tmp_path,
            target_path="wrong",
            scratch_path="wrong",
            ordered_members=(),
            **kwargs,
        ),
        "lens": lambda: owner.validate_staged_package_source(value, object(), **kwargs),
        "image": lambda: owner.validate_package_postimage(value, object(), **kwargs),
        "require_image": lambda: owner.require_retained_package_postimage(
            object(),
            plan=value,
            **kwargs,
        ),
    }
    before = owner.observe_package_input(reservation)
    monkeypatch.setattr(owner, "_verify", forbidden_freshness)
    with pytest.raises(owner.PackageInputCustodyRefusal):
        calls[entrance]()
    assert owner.observe_package_input(reservation) == before
    assert value.phase == "planned" and not value.evidence.effects
    owner.release_package_input(claim if claim is not None else reservation)


def test_genuine_claim_complete_loop_and_reader_lifetime(tmp_path):
    value = plan(tmp_path)
    reservation, receiver, claim = transferred(value)
    assert (
        owner.require_package_input_claim(claim, plan=value, receiver=receiver) is claim
    )
    kwargs = {"input_claim": claim}
    value.validate_current(**kwargs)
    assert owner.require_retained_package_plan(value, **kwargs) is value
    binding = owner.observe_package_plan(value, **kwargs)
    owner.validate_package_plan(
        value,
        root=tmp_path,
        target_path=binding.target_path,
        scratch_path=binding.scratch_path,
        ordered_members=binding.ordered_members,
        **kwargs,
    )
    lens = value.stage(**kwargs)
    owner.validate_staged_package_source(value, lens, **kwargs)
    assert lens.stage_name == Path(value.scratch_path).name
    descriptor = lens.duplicate_parent_descriptor()
    os.close(descriptor)
    image = value.publish_package(**kwargs)
    owner.validate_package_postimage(value, image, **kwargs)
    assert (
        owner.require_retained_package_postimage(image, plan=value, **kwargs) is image
    )
    with pytest.raises(owner.PackageInputCustodyRefusal):
        owner.retain_package_postimage_read(image)
    reader = owner.retain_package_postimage_read(image, **kwargs)
    value.finish(image, **kwargs)
    assert owner.require_retained_package_plan(value, **kwargs) is value
    with pytest.raises(owner.PackageInputCustodyRefusal):
        owner.release_package_input(reservation)
    snapshot = owner.release_package_input(claim)
    assert snapshot.resource_state == "released"
    assert snapshot.owner_cleanup_outcome == "completed"
    assert snapshot.cleanup.evidence.package_outcome == "published"
    assert owner.release_package_input(claim) == snapshot
    assert value.release(**kwargs) == snapshot.cleanup.evidence
    reader.validate_current()
    owner.validate_package_postimage_read(reader, plan=value)
    reader.release()
    assert (tmp_path / "package/a.txt").read_bytes() == b"one"
    with pytest.raises(owner.PackagePublicationRefusal):
        value.stage(**kwargs)


@pytest.mark.parametrize("phase", ["reserved", "transferred", "released"])
def test_conflict_never_cleans_retires_or_reacquires_existing_owner(
    tmp_path, monkeypatch, phase
):
    value = plan(tmp_path)
    reservation = reserve(value)
    claim = None
    if phase != "reserved":
        claim = owner.transfer_package_input(reservation, receiver=object())
    if phase == "released":
        owner.release_package_input(claim)
    before = owner.observe_package_input(reservation)
    monkeypatch.setattr(owner, "_verify", forbidden_freshness)
    with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
        reserve(value, "attempt:two")
    assert caught.value.code == "package_input_already_owned"
    assert owner.observe_package_input(reservation) == before
    owner.release_package_input(claim if claim is not None else reservation)


@pytest.mark.parametrize("kind", ["reservation", "claim"])
@pytest.mark.parametrize(
    "operation", ["construct", "copy", "deepcopy", "pickle", "subclass"]
)
def test_capabilities_not_reconstructible(tmp_path, kind, operation):
    value = plan(tmp_path)
    reservation, _, claim = transferred(value)
    capability = reservation if kind == "reservation" else claim
    cls = type(capability)
    calls = {
        "construct": cls,
        "copy": lambda: copy.copy(capability),
        "deepcopy": lambda: copy.deepcopy(capability),
        "pickle": lambda: pickle.dumps(capability),
        "subclass": lambda: type("Forgery", (cls,), {}),
    }
    with pytest.raises(TypeError):
        calls[operation]()
    owner.release_package_input(claim)


@pytest.mark.parametrize("kind", ["reservation", "claim", "snapshot", "none"])
@pytest.mark.parametrize("entrance", ["observe", "transfer", "release", "require"])
def test_unissued_and_detached_values_have_no_authority(tmp_path, kind, entrance):
    value = plan(tmp_path)
    reservation = reserve(value)
    candidate = {
        "reservation": object.__new__(owner.PackageInputReservation),
        "claim": object.__new__(owner.PackageInputClaim),
        "snapshot": owner.observe_package_input(reservation),
        "none": None,
    }[kind]
    before = owner.observe_package_input(reservation)
    calls = {
        "observe": lambda: owner.observe_package_input(candidate),
        "transfer": lambda: owner.transfer_package_input(candidate, receiver=object()),
        "release": lambda: owner.release_package_input(candidate),
        "require": lambda: owner.require_package_input_claim(
            candidate,
            plan=value,
            receiver=object(),
        ),
    }
    with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
        calls[entrance]()
    assert caught.value.input_observation is None
    assert caught.value.evidence.package_outcome == "unknown"
    assert owner.observe_package_input(reservation) == before
    owner.release_package_input(reservation)


def test_wrong_receiver_plan_and_claim_refuse_without_freshness(tmp_path, monkeypatch):
    first, second = plan(tmp_path, "first"), plan(tmp_path, "second")
    reservation, receiver, claim = transferred(first)
    other_reservation, _, other_claim = transferred(second)
    before = owner.observe_package_input(reservation)
    monkeypatch.setattr(owner, "_verify", forbidden_freshness)
    for value, selected_plan, selected_receiver in (
        (claim, first, object()),
        (claim, second, receiver),
        (other_claim, first, receiver),
        (reservation, first, receiver),
    ):
        with pytest.raises(owner.PackageInputCustodyRefusal):
            owner.require_package_input_claim(
                value, plan=selected_plan, receiver=selected_receiver
            )
    with pytest.raises(owner.PackageInputCustodyRefusal):
        first.validate_current(input_claim=other_claim)
    assert owner.observe_package_input(reservation) == before
    owner.release_package_input(claim)
    owner.release_package_input(other_claim)
    assert owner.observe_package_input(other_reservation).resource_state == "released"


@pytest.mark.parametrize("field", ["attempt_ref", "client_intent_id"])
@pytest.mark.parametrize(
    "bad",
    ["", " ", " spaced", "e\u0301", "a\u0080b", "a\n", "x" * 1025, None, 1, "\ud800"],
)
def test_invalid_correlation_does_not_acquire_or_cleanup(tmp_path, field, bad):
    value = plan(tmp_path)
    kwargs = {"attempt_ref": "attempt", "client_intent_id": "intent", field: bad}
    with pytest.raises(ValueError):
        owner.reserve_package_input(value, **kwargs)
    assert owner._HANDLES[value].input_custody is None
    assert not value.observe_cleanup().attempted
    value.release()


@pytest.mark.parametrize("entrance", ["reserve", "transfer"])
def test_failed_capability_return_disposes_only_acquired_original(
    tmp_path, monkeypatch, entrance
):
    value = plan(tmp_path, "new")
    existing = plan(tmp_path, "existing")
    existing_reservation = reserve(existing, "existing")
    before = owner.observe_package_input(existing_reservation)
    reservation = reserve(value) if entrance == "transfer" else None
    original = owner.finalize

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt("issuance interrupted before successful return")

    monkeypatch.setattr(owner, "finalize", interrupt)
    with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
        if entrance == "reserve":
            reserve(value)
        else:
            owner.transfer_package_input(reservation, receiver=object())
    observation = caught.value.input_observation
    assert observation.resource_state == "released"
    assert observation.release_invocation == "returned"
    assert observation.owner_cleanup_outcome == "completed"
    assert observation.diagnostics
    assert owner.observe_package_input(existing_reservation) == before
    assert not owner._HANDLES[value].fds
    monkeypatch.setattr(owner, "finalize", original)
    owner.release_package_input(existing_reservation)


@pytest.mark.parametrize("failure", ["cleanup", "close"])
def test_owned_release_interruptions_are_typed_and_once_only(
    tmp_path, monkeypatch, failure
):
    value = plan(tmp_path)
    reservation, _, claim = transferred(value)
    value.stage(input_claim=claim)
    original_cleanup, original_close = owner._cleanup, owner._close_all
    calls = []

    def cleanup(state):
        calls.append("cleanup")
        if failure == "cleanup":
            raise KeyboardInterrupt("cleanup interruption")
        original_cleanup(state)

    def close(state):
        calls.append("close")
        original_close(state)
        if failure == "close":
            raise KeyboardInterrupt("close return interruption")

    monkeypatch.setattr(owner, "_cleanup", cleanup)
    monkeypatch.setattr(owner, "_close_all", close)
    for _ in range(2):
        with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
            owner.release_package_input(claim)
        evidence = caught.value.input_observation
        assert evidence.resource_state == "released"
        assert evidence.owner_cleanup_attempted is True
        assert evidence.owner_cleanup_outcome == "incomplete"
        assert evidence.cleanup.evidence.cleanup_diagnostics
    assert calls == ["cleanup", "close"]
    assert owner.observe_package_input(reservation) == evidence
    assert not owner._HANDLES[value].fds


def test_actual_descriptor_close_interruption_reported_without_retry(
    tmp_path, monkeypatch
):
    value = plan(tmp_path)
    reservation = reserve(value)
    original = owner.os.close
    closed = []

    def close(descriptor):
        original(descriptor)
        closed.append(descriptor)
        raise KeyboardInterrupt("actual close completed; return interrupted")

    monkeypatch.setattr(owner.os, "close", close)
    with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
        owner.release_package_input(reservation)
    count = len(closed)
    assert count > 0
    with pytest.raises(owner.PackageInputCustodyRefusal):
        owner.release_package_input(reservation)
    assert len(closed) == count
    assert (
        "descriptor_close:KeyboardInterrupt"
        in caught.value.evidence.cleanup_diagnostics
    )


def test_interrupted_claim_freshness_retires_and_preserves_effects(
    tmp_path, monkeypatch
):
    value = plan(tmp_path)
    reservation, _, claim = transferred(value)
    value.stage(input_claim=claim)
    effects = value.evidence.effects

    def interrupt(state):
        raise KeyboardInterrupt("freshness interruption")

    monkeypatch.setattr(owner, "_verify", interrupt)
    with pytest.raises(owner.PackagePublicationRefusal):
        value.validate_current(input_claim=claim)
    assert value.phase == "retired"
    assert value.evidence.effects[: len(effects)] == effects
    assert owner.observe_package_input(reservation).owner_cleanup_attempted
    owner.release_package_input(claim)
    with pytest.raises(owner.PackagePublicationRefusal):
        value.stage(input_claim=claim)


@pytest.mark.parametrize(
    "mode", ["competing", "transfer_release", "reserve_raw_release"]
)
@pytest.mark.parametrize("replay", range(20))
def test_real_atomic_owner_races(tmp_path, mode, replay):
    value = plan(tmp_path)
    barrier = threading.Barrier(2)
    reservation = reserve(value) if mode == "transfer_release" else None
    receiver = object()

    def run(index):
        barrier.wait(timeout=5)
        try:
            if mode == "competing":
                return reserve(value, f"attempt:{index}"), None
            if mode == "transfer_release":
                return (
                    owner.transfer_package_input(reservation, receiver=receiver)
                    if index == 0
                    else owner.release_package_input(reservation)
                ), None
            return (reserve(value) if index == 0 else value.release()), None
        except owner.PackageInputCustodyRefusal as error:
            return None, error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, (0, 1)))
    if mode == "competing":
        assert sum(error is None for _, error in outcomes) == 1
        winner = next(result for result, error in outcomes if error is None)
        owner.release_package_input(winner)
    elif mode == "transfer_release":
        assert sum(error is None for _, error in outcomes) == 1
        if outcomes[0][1] is None:
            claim = outcomes[0][0]
            assert owner.observe_package_input(claim).resource_state == "transferred"
            owner.release_package_input(claim)
        else:
            assert owner.observe_package_input(reservation).resource_state == "released"
    else:
        if outcomes[1][1] is None:
            # Disposal won first. A later reservation is cleanup-only, not a
            # reclaimed writer; it may observe and dispose the terminal input.
            assert value.phase == "released"
            if outcomes[0][1] is None:
                with pytest.raises(owner.PackageInputCustodyRefusal):
                    owner.transfer_package_input(outcomes[0][0], receiver=receiver)
                owner.release_package_input(outcomes[0][0])
        else:
            assert value.phase == "planned"
            owner.release_package_input(outcomes[0][0])
    assert not owner._HANDLES[value].fds


@pytest.mark.parametrize("kind", ["reservation", "claim"])
def test_collected_original_disposes_once_and_detached_snapshot_cannot_recover(
    tmp_path, kind
):
    before = descriptor_count()
    value = plan(tmp_path)
    reservation = reserve(value)
    if kind == "claim":
        claim = owner.transfer_package_input(reservation, receiver=object())
        snapshot = owner.observe_package_input(claim)
        del reservation
        gc.collect()
        assert not value.observe_cleanup().attempted
        reference = weakref.ref(claim)
        del claim
    else:
        snapshot = owner.observe_package_input(reservation)
        reference = weakref.ref(reservation)
        del reservation
    gc.collect()
    assert reference() is None
    assert value.observe_cleanup().outcome == "completed"
    assert descriptor_count() == before
    with pytest.raises(owner.PackageInputCustodyRefusal):
        owner.release_package_input(snapshot)


def test_capability_lifetime_retains_original_plan_without_weak_registry_cycle(
    tmp_path,
):
    before = descriptor_count()
    value = plan(tmp_path)
    reference = weakref.ref(value)
    reservation = reserve(value)
    del value
    gc.collect()
    assert reference() is not None
    del reservation
    gc.collect()
    assert reference() is None
    assert descriptor_count() == before


@pytest.mark.parametrize("phase", ["reserved", "transferred"])
def test_genuine_fork_refuses_without_retiring_or_closing_inherited_holder(
    tmp_path, phase
):
    value = plan(tmp_path)
    reservation = reserve(value)
    capability = (
        owner.transfer_package_input(reservation, receiver=object())
        if phase == "transferred"
        else reservation
    )
    before = owner.observe_package_input(capability)
    pid = os.fork()
    if pid == 0:
        try:
            state = owner._HANDLES[value]
            descriptors = dict(state.fds)
            for call in (
                lambda: owner.observe_package_input(capability),
                lambda: owner.release_package_input(capability),
                lambda: value.release(input_claim=capability),
                lambda: reserve(value),
            ):
                try:
                    call()
                except owner.PackageInputCustodyRefusal:
                    pass
                else:
                    os._exit(11)
            if (
                state.fds != descriptors
                or state.phase != "planned"
                or state.cleanup_attempted
            ):
                os._exit(12)
            for descriptor in descriptors.values():
                os.fstat(descriptor)
            os._exit(0)
        except BaseException:  # noqa: BLE001 - fork fault probe must terminate, not enter pytest
            os._exit(13)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert owner.observe_package_input(capability) == before
    owner.release_package_input(capability)


def test_new_unreserved_three_descriptor_plan_disposal_preserves_competing_owner(
    tmp_path,
):
    (tmp_path / "customer/specs").mkdir(parents=True)
    existing = plan(tmp_path, "existing")
    reservation = reserve(existing)
    snapshot = owner.observe_package_input(reservation)
    before = descriptor_count()
    new = plan(tmp_path, "customer/specs/package")
    assert descriptor_count() == before + 3
    result = new.release(input_claim=None)
    assert result.package_outcome == "none"
    assert descriptor_count() == before
    assert owner.observe_package_input(reservation) == snapshot
    owner.release_package_input(reservation)


def test_retired_original_reserves_cleanup_only_without_freshness(
    tmp_path, monkeypatch
):
    value = plan(tmp_path)
    value.release()
    monkeypatch.setattr(owner, "_verify", forbidden_freshness)
    reservation = reserve(value)
    with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
        owner.transfer_package_input(reservation, receiver=object())
    assert caught.value.code == "package_input_cleanup_only"
    observation = owner.release_package_input(reservation)
    assert observation.owner_cleanup_outcome == "completed"


def test_version_and_dependency_boundary():
    manifest = Path(owner.__file__).parents[1] / "pyproject.toml"
    project = tomllib.loads(manifest.read_text())["project"]
    assert project["version"] == "0.3.0"
    assert not any(
        "issue" in item or "protocol" in item for item in project["dependencies"]
    )


@pytest.mark.parametrize("entrance", ["reserve", "transfer"])
@pytest.mark.parametrize("point", ["before", "after"])
def test_registry_interruption_before_successful_return_is_effect_honest(
    tmp_path, monkeypatch, entrance, point
):
    value = plan(tmp_path)
    reservation = reserve(value) if entrance == "transfer" else None
    original = owner._INPUTS

    class InterruptedRegistry(weakref.WeakKeyDictionary):
        def __setitem__(self, key, entry):
            if point == "after":
                super().__setitem__(key, entry)
            raise SystemExit("registry return interrupted")

    registry = InterruptedRegistry()
    # Populate without invoking the injected writer.
    for key, entry in original.items():
        weakref.WeakKeyDictionary.__setitem__(registry, key, entry)
    monkeypatch.setattr(owner, "_INPUTS", registry)
    with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
        if entrance == "reserve":
            reserve(value)
        else:
            owner.transfer_package_input(reservation, receiver=object())
    observation = caught.value.input_observation
    assert observation.owner_cleanup_attempted is True
    assert observation.owner_cleanup_outcome == "completed"
    assert observation.cleanup.evidence.package_outcome == "none"
    assert not owner._HANDLES[value].fds
    assert observation.transfer_state == (
        "attempted" if entrance == "transfer" else "not_attempted"
    )


@pytest.mark.parametrize("entrance", ["validate", "next", "publish", "finish"])
def test_claim_interruptions_preserve_known_publication_and_terminal_cleanup(
    tmp_path, monkeypatch, entrance
):
    value = plan(tmp_path)
    reservation, _, claim = transferred(value)
    value.stage(input_claim=claim)
    image = value.publish_package(input_claim=claim) if entrance == "finish" else None
    before = value.evidence

    def interrupt(state):
        raise KeyboardInterrupt("real owner freshness seam interrupted")

    monkeypatch.setattr(owner, "_verify", interrupt)
    calls = {
        "validate": lambda: value.validate_current(input_claim=claim),
        "next": lambda: value.stage_next_effect(input_claim=claim),
        "publish": lambda: value.publish_package(input_claim=claim),
        "finish": lambda: value.finish(image, input_claim=claim),
    }
    with pytest.raises(owner.PackagePublicationRefusal):
        calls[entrance]()
    assert value.phase == "retired"
    assert value.evidence.effects[: len(before.effects)] == before.effects
    snapshot = owner.release_package_input(claim)
    assert snapshot.cleanup.evidence.package_outcome == before.package_outcome
    assert owner.observe_package_input(reservation) == snapshot
    assert not owner._HANDLES[value].fds
    assert (tmp_path / "package").exists() == (entrance == "finish")


def test_transferred_lens_keeps_original_claim_alive_only_until_lens_collection(
    tmp_path,
):
    value = plan(tmp_path)
    reservation, _, claim = transferred(value)
    lens = value.stage(input_claim=claim)
    reference = weakref.ref(claim)
    del claim, reservation
    gc.collect()
    assert reference() is not None
    assert lens.stage_name == Path(value.scratch_path).name
    assert not value.observe_cleanup().attempted
    del lens
    gc.collect()
    assert reference() is None
    assert value.observe_cleanup().outcome == "completed"


@pytest.mark.parametrize("spent", ["staged", "published", "consumed"])
def test_reservation_cannot_absorb_a_spent_unreserved_writer(
    tmp_path, monkeypatch, spent
):
    value = plan(tmp_path)
    value.stage()
    if spent != "staged":
        image = value.publish_package()
        if spent == "consumed":
            value.finish(image)
    before = value.evidence
    monkeypatch.setattr(owner, "_verify", forbidden_freshness)
    with pytest.raises(owner.PackageInputCustodyRefusal):
        reserve(value)
    assert value.evidence == before
    assert not value.observe_cleanup().attempted
    value.release()


def test_receiver_is_identity_correlation_not_an_injected_validator(tmp_path):
    value = plan(tmp_path)
    reservation = reserve(value)
    calls = []

    def receiver():
        calls.append("must never be evaluated")
        raise AssertionError("FileSystem cannot evaluate Issue authenticity")

    claim = owner.transfer_package_input(reservation, receiver=receiver)
    assert (
        owner.require_package_input_claim(claim, plan=value, receiver=receiver) is claim
    )
    assert calls == []
    owner.release_package_input(claim)


@pytest.mark.parametrize("entrance", ["observe", "release", "issuance", "conflict"])
def test_unavailable_evidence_stays_unknown_without_cleanup_retry(
    tmp_path, monkeypatch, entrance
):
    value = plan(tmp_path)
    reservation = reserve(value) if entrance != "issuance" else None
    original = owner._input_observation

    def unavailable(*args):
        raise KeyboardInterrupt("evidence return interrupted")

    def interrupted_issuance(*args):
        raise KeyboardInterrupt("capability issuance interrupted")

    monkeypatch.setattr(owner, "_input_observation", unavailable)
    if entrance == "issuance":
        monkeypatch.setattr(owner, "finalize", interrupted_issuance)
    calls = {
        "observe": lambda: owner.observe_package_input(reservation),
        "release": lambda: owner.release_package_input(reservation),
        "issuance": lambda: reserve(value),
        "conflict": lambda: reserve(value),
    }
    with pytest.raises(owner.PackageInputCustodyRefusal) as caught:
        calls[entrance]()
    assert caught.value.input_observation is None
    assert caught.value.evidence.package_outcome == "unknown"
    assert value.observe_cleanup().attempted == (entrance in {"release", "issuance"})
    monkeypatch.setattr(owner, "_input_observation", original)
    if reservation is not None:
        owner.release_package_input(reservation)
        assert (
            owner.observe_package_input(reservation).owner_cleanup_outcome
            == "completed"
        )
