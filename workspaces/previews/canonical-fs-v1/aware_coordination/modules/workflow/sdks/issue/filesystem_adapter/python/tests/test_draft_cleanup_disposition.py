"""Genuine Issue/Protocol/FileSystem cleanup disposition; SPEC separately owned."""

import gc
import weakref
from dataclasses import FrozenInstanceError, replace

import pytest
from aware_file_system import retained_package as physical
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueDraftPackageCleanupDisposition,
    IssueDraftPackageRefusal,
)
from aware_protocol_fs_adapter import release_specification_draft_target
from aware_protocol_fs_adapter import specification_draft_target as protocol
from test_draft_package_admission import dispose_test_original, real_locator_context


@pytest.fixture
def inputs(tmp_path):
    mp = pytest.MonkeyPatch()
    values = real_locator_context(
        tmp_path,
        mp,
        target_locator="aware.protocol.toml",
        request_locator="aware.protocol.toml",
    )
    try:
        yield (*values, mp)
    finally:
        mp.undo()
        dispose_test_original(values[3])
        if values[2].phase != "released":
            release_specification_draft_target(values[2])


def admit(values, request=None):
    _, _, target, plan, original_request, provider, _ = values
    return provider.admit_draft_package(
        request or original_request, protocol_target=target, physical_plan=plan
    )


def test_authorization_refusal_disposes_enrolled_inputs_not_caller_owned(inputs):
    _, _, target, plan, request, provider, _ = inputs
    wrong = replace(request, expected_issue_sha256="sha256:" + "0" * 64)
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        admit(inputs, wrong)
    snapshot = caught.value.input_cleanup
    assert type(snapshot) is IssueDraftPackageCleanupDisposition
    assert snapshot.request == wrong and snapshot.request is not wrong
    assert snapshot.physical_claim == "unclaimed"
    assert snapshot.physical_cleanup_owner == "issue"
    assert snapshot.physical_cleanup_attempted is True
    assert snapshot.physical_cleanup_outcome == "completed"
    assert snapshot.protocol_cleanup_owner == "issue"
    assert (
        provider.observe_draft_package_cleanup(
            protocol_target=target, physical_plan=plan
        )
        == snapshot
    )


@pytest.mark.parametrize("nested", [False, True])
def test_failed_claimed_issuance_records_attempt_once_even_without_admission(
    inputs, nested
):
    root, _, target, plan, request, provider, mp = inputs
    calls = []
    original_bind = protocol.bind_specification_draft_physical_plan

    def bind(*args, **kwargs):
        if nested:
            original_bind(*args, **kwargs)
            issue = root / "work/issues/2026/10/06/fb-2026-10-06-locator-proof.md"
            issue.write_bytes(issue.read_bytes() + b"\n# concurrent change\n")
        else:
            raise OSError("binding fault")

    def interrupted(claim):
        assert physical._INPUTS[claim].plan is plan
        calls.append("release")
        raise KeyboardInterrupt("before original physical release body")

    mp.setattr(protocol, "bind_specification_draft_physical_plan", bind)
    mp.setattr(physical, "release_package_input", interrupted)
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        admit(inputs)
    snapshot = caught.value.input_cleanup
    assert snapshot.request == request
    assert snapshot.execution_ref == "codex-real-locator-equality-proof"
    assert snapshot.physical_claim == "claimed"
    assert snapshot.physical_cleanup_owner == "issue"
    assert snapshot.physical_cleanup_attempted is True
    assert snapshot.physical_cleanup_outcome == "unknown"
    assert snapshot.protocol_cleanup_owner == "issue"
    assert (
        "physical_release_failed:KeyboardInterrupt"
        in snapshot.evidence.cleanup_diagnostics
    )
    assert plan.phase == "planned"
    assert calls == ["release"]
    gc.collect()  # Failed issuance retains its correlated snapshot without a live handle.
    assert (
        provider.observe_draft_package_cleanup(
            protocol_target=target, physical_plan=plan
        )
        == snapshot
    )
    assert calls == ["release"]


def test_live_and_terminal_observations_are_detached_and_do_not_renew(inputs):
    _, _, target, plan, request, provider, _ = inputs
    handle = admit(inputs)
    before = handle.observe_cleanup()
    assert before.physical_claim == "claimed" and not before.physical_cleanup_attempted
    handle.release()
    after = handle.observe_cleanup()
    assert after.physical_cleanup_outcome == "completed"
    assert (
        provider.observe_draft_package_cleanup(
            protocol_target=target, physical_plan=plan
        )
        == after
    )
    assert before.request == request and not before.physical_cleanup_attempted
    with pytest.raises(FrozenInstanceError):
        after.physical_cleanup_attempted = False
    with pytest.raises(IssueDraftPackageRefusal):
        provider.validate_draft_package(after)
    with pytest.raises(IssueDraftPackageRefusal):
        handle.stage_next_effect()


def test_unavailable_legacy_observer_does_not_erase_known_custody_history(inputs):
    _, _, _, _, request, _, mp = inputs

    def unavailable(value):
        raise OSError("evidence unavailable")

    mp.setattr(physical, "observe_package_cleanup", unavailable)
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        admit(inputs, replace(request, expected_issue_sha256="sha256:" + "0" * 64))
    snapshot = caught.value.input_cleanup
    assert snapshot.physical_claim == "unclaimed"
    assert snapshot.physical_cleanup_owner == "issue"
    assert snapshot.physical_cleanup_attempted is True
    assert snapshot.physical_cleanup_outcome == "completed"
    assert snapshot.evidence.package_outcome == "none"


def test_cleanup_observation_failure_is_not_reported_as_release_failure(inputs):
    _, _, _, _, _, _, mp = inputs
    handle = admit(inputs)

    def unavailable(value):
        raise OSError("history unavailable")

    mp.setattr(physical, "observe_package_cleanup", unavailable)
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        handle.release()
    snapshot = caught.value.input_cleanup
    assert snapshot.physical_cleanup_attempted is True
    assert snapshot.physical_cleanup_outcome == "unknown"
    assert (
        "physical_cleanup_observation_unavailable:OSError"
        in snapshot.evidence.cleanup_diagnostics
    )
    assert not any(
        d.startswith("physical_release_failed:")
        for d in snapshot.evidence.cleanup_diagnostics
    )


@pytest.mark.parametrize("value", [None, [], object()])
def test_unsupported_disposition_is_unavailable_not_caller_owned(inputs, value):
    _, _, target, _, _, provider, _ = inputs
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        provider.observe_draft_package_cleanup(
            protocol_target=target, physical_plan=value
        )
    assert caught.value.input_cleanup is None  # Public absence is explicitly unknown.


def test_foreign_claim_never_defaults_to_unclaimed(inputs):
    root, _, target, plan, request, _, _ = inputs
    handle = admit(inputs)
    other = FilesystemIssueOperationProvider(
        repository_root=root, protocol_source_ref=request.manifest_locator
    )
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        other.admit_draft_package(request, protocol_target=target, physical_plan=plan)
    assert caught.value.input_cleanup is None
    assert caught.value.input_custody.physical.responsibility == "unknown"
    assert not handle.observe_cleanup().physical_cleanup_attempted
    with pytest.raises(IssueDraftPackageRefusal):
        other.observe_draft_package_cleanup(protocol_target=target, physical_plan=plan)
    handle.release()


def test_duplicate_attempt_does_not_replace_original_correlation(inputs):
    _, _, target, plan, request, provider, _ = inputs
    handle = admit(inputs)
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        admit(inputs, replace(request, client_intent_id="different-attempt"))
    assert caught.value.input_cleanup is None
    assert (
        provider.observe_draft_package_cleanup(
            protocol_target=target, physical_plan=plan
        ).request
        == request
    )
    assert not handle.observe_cleanup().physical_cleanup_attempted
    handle.release()
    assert (
        provider.observe_draft_package_cleanup(
            protocol_target=target, physical_plan=plan
        ).physical_cleanup_outcome
        == "completed"
    )


def test_abandonment_updates_provider_snapshot_without_retaining_handle(inputs):
    _, _, target, plan, _, provider, _ = inputs
    handle = admit(inputs)
    del handle
    gc.collect()
    snapshot = provider.observe_draft_package_cleanup(
        protocol_target=target, physical_plan=plan
    )
    assert (
        snapshot.physical_cleanup_attempted
        and snapshot.physical_cleanup_outcome == "completed"
    )


def test_released_original_target_preserves_historical_observation(inputs):
    _, _, target, plan, _, provider, _ = inputs
    handle = admit(inputs)
    handle.release()
    snapshot = handle.observe_cleanup()
    assert target.phase == "released"
    del handle
    gc.collect()
    assert (
        provider.observe_draft_package_cleanup(
            protocol_target=target, physical_plan=plan
        )
        == snapshot
    )
    assert snapshot.physical_cleanup_outcome == "completed"


def test_collected_original_target_cannot_match_none(tmp_path):
    mp = pytest.MonkeyPatch()
    plan = target = None
    try:
        _, _, target, plan, request, provider = real_locator_context(
            tmp_path,
            mp,
            target_locator="aware.protocol.toml",
            request_locator="aware.protocol.toml",
        )
        handle = provider.admit_draft_package(
            request, protocol_target=target, physical_plan=plan
        )
        handle.release()
        snapshot = handle.observe_cleanup()
        reference = weakref.ref(target)
        assert target.phase == "released"
        del handle
        target = None
        gc.collect()
        assert reference() is None
        physical_before = plan.observe_cleanup()
        with pytest.raises(
            IssueDraftPackageRefusal, match="draft_cleanup_observation_unavailable"
        ) as caught:
            provider.observe_draft_package_cleanup(
                protocol_target=None, physical_plan=plan
            )
        assert caught.value.input_cleanup is None
        assert plan.observe_cleanup() == physical_before
        assert snapshot.physical_cleanup_outcome == "completed"
        assert snapshot.request == request
    finally:
        mp.undo()
        if target is not None and target.phase != "released":
            release_specification_draft_target(target)
        if plan is not None:
            dispose_test_original(plan)


def test_published_history_survives_release(inputs):
    root, _, _, _, _, _, _ = inputs
    handle = admit(inputs)
    while handle.phase != "staged":
        handle.stage_next_effect()
    handle.publish_package()
    before = handle.observe_cleanup()
    handle.release()
    after = handle.observe_cleanup()
    assert (
        after.evidence.package_outcome == before.evidence.package_outcome == "published"
    )
    assert after.evidence.effects == before.evidence.effects
    assert (root / "customer/specs/widget/README.md").read_bytes() == b"draft"


def test_foreign_observer_cannot_retire_original_admission(inputs):
    _, _, _, _, _, _, mp = inputs
    handle = admit(inputs)
    before = handle.observe_cleanup()
    from aware_issue_fs_adapter import draft_package as owner

    pid = owner.os.getpid()
    mp.setattr(owner.os, "getpid", lambda: pid + 1)
    with pytest.raises(IssueDraftPackageRefusal):
        handle.observe_cleanup()
    mp.undo()
    assert handle.observe_cleanup() == before
    handle.release()
