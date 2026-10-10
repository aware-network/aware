"""Genuine owners with entrance fault injection; never copied policy/writers."""

# ruff: noqa: SIM117 - observe refusal after the tested owner context exits

import importlib.util
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest
from aware_file_system import retained_package as physical
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_fs_adapter.draft_package import FilesystemIssueDraftPackageAdmission
from aware_protocol_fs_adapter import specification_draft_target as protocol
from aware_specification_fs_sdk_adapter import open_governed_specification_draft
from aware_specification_sdk import SpecificationOperationError, SpecificationSdkClient


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    # Reuse the original actual-owner fixture, not its policy or operation code.
    spec = importlib.util.spec_from_file_location(
        "cleanup_original_spec_fixture",
        Path(__file__).with_name("test_governed_draft.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = module.context.__wrapped__(tmp_path, monkeypatch)
    yield next(source)
    monkeypatch.undo()  # Restore fault wrappers before test-only holder disposal.
    with pytest.raises(StopIteration):
        next(source)


def test_preview_exit_observes_original_lifetimes_without_completion_inference(inputs):
    root, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    with manager:
        before = manager.observe_draft_cleanup()
        assert before.issue_disposition.physical_claim == "claimed"
        assert before.physical_invocation.responsibility == "context"
        assert before.physical_invocation.invocation_state == "not_invoked"
    after = manager.observe_draft_cleanup()
    assert after.context_state == "closed"
    assert after.issue_disposition.physical_cleanup_outcome == "completed"
    assert after.physical_invocation.invocation_state == "returned"
    assert after.protocol_invocation.invocation_state == "returned"
    assert (
        after.protocol_owner_attempted is None
        and after.protocol_owner_outcome == "unknown"
    )
    assert after.issue_disposition.protocol_cleanup_owner == "issue"
    assert after.physical_observation.root_locator == str(root)
    assert after.physical_observation.evidence.ledger_complete is None
    assert not (root / "customer/specs/widget").exists()
    with pytest.raises(FrozenInstanceError):
        after.context_state = "entered"
    assert not before.issue_disposition.physical_cleanup_attempted


@pytest.mark.parametrize("interrupted", [False, True])
def test_failed_claimed_issuance_preserves_disposition_and_never_retries(
    inputs, monkeypatch, interrupted
):
    root, _, _, kwargs = inputs
    calls = []

    def bind(*args, **kwargs):
        raise OSError("original bind fault")

    monkeypatch.setattr(protocol, "bind_specification_draft_physical_plan", bind)
    if interrupted:

        def release(*args, **kwargs):
            calls.append("release")
            raise KeyboardInterrupt("before original body")

        monkeypatch.setattr(physical, "release_package_input", release)
    manager = open_governed_specification_draft(**kwargs)
    with pytest.raises(SpecificationOperationError) as caught:
        manager.__enter__()
    carrier = caught.value.cleanup_evidence
    assert carrier.issue_disposition.physical_claim == "claimed"
    assert carrier.issue_disposition.physical_cleanup_attempted is True
    assert carrier.issue_disposition.request.ordered_members == manager.members
    assert (
        carrier.issue_disposition.execution_ref
        == "codex-spec-governed-real-source-proof"
    )
    assert carrier.physical_invocation.invocation_state == "not_invoked"
    assert carrier.protocol_invocation.invocation_state == "not_invoked"
    assert carrier.protocol_invocation.responsibility == "unknown"
    assert carrier.protocol_owner_outcome == "unknown"
    assert not (root / "customer/specs/widget").exists()
    assert (
        manager.observe_draft_cleanup().issue_disposition.request
        == carrier.issue_disposition.request
    )
    if interrupted:
        assert calls == ["release"]
        assert carrier.issue_disposition.physical_cleanup_outcome == "unknown"
        assert caught.value.effect == "unknown"


def test_legacy_preclaim_refusal_retains_successor_owner_disposal(inputs):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(
        **{**kwargs, "expected_issue_sha256": "sha256:" + "0" * 64}
    )
    with pytest.raises(SpecificationOperationError) as caught:
        manager.__enter__()
    issue = caught.value.cleanup_evidence.issue_disposition
    assert (
        issue.physical_claim == "unclaimed" and issue.physical_cleanup_owner == "issue"
    )
    assert issue.physical_cleanup_attempted is True
    assert (
        manager.observe_draft_cleanup().physical_invocation.invocation_state
        == "not_invoked"
    )


def test_constructor_refusal_carries_unknown_without_observing_or_releasing(inputs):
    root, _, _, kwargs = inputs
    with pytest.raises(SpecificationOperationError) as caught:
        open_governed_specification_draft(**{**kwargs, "request": object()})
    evidence = caught.value.cleanup_evidence
    assert evidence.context_state == "not_entered"
    assert evidence.issue_disposition is None and evidence.physical_observation is None
    assert evidence.physical_invocation.responsibility == "unknown"
    assert evidence.protocol_invocation.invocation_state == "not_invoked"
    assert not (root / "customer/specs/widget").exists()


def test_retirement_fault_then_normal_later_release_never_proves_protocol_completion(
    inputs, monkeypatch
):
    root, manifest, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    original = protocol._release_owned_selection
    captures = []

    def interrupted(selection):
        captures.append(selection)
        raise OSError("retirement cleanup fault")

    with pytest.raises(SpecificationOperationError) as caught, manager as client:
        monkeypatch.setattr(protocol, "_release_owned_selection", interrupted)
        manifest.write_bytes(manifest.read_bytes() + b"\n# stale\n")
        client.create_draft(kwargs["request"])
    evidence = caught.value.cleanup_evidence
    assert len(captures) == 1
    assert "draft_target_cleanup_failed:OSError" in evidence.cleanup_diagnostics
    assert evidence.protocol_invocation.invocation_state == "returned"
    assert evidence.protocol_owner_attempted is None
    assert evidence.protocol_owner_outcome == "unknown"
    assert not (root / "customer/specs/widget").exists()
    monkeypatch.setattr(protocol, "_release_owned_selection", original)
    original(captures[0])  # Test-only disposal, not an authorized product retry.


def test_combined_primary_reader_and_target_faults_preserve_all_evidence(
    inputs, monkeypatch
):
    from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider

    root, _, _, kwargs = inputs
    guard = kwargs["issue_provider"].retain_draft_inputs(
        attempt_ref="combined-cleanup:original",
        client_intent_id=kwargs["client_intent_id"],
        protocol_target=kwargs["protocol_draft_target"],
        physical_plan=kwargs["physical_package_plan"],
    )
    manager = open_governed_specification_draft(**kwargs, input_custody=guard)
    original = SpecificationFsSdkProvider.close
    original_target = protocol.release_specification_draft_input
    calls = []

    def invalid(self, request):
        raise SpecificationOperationError("strict_stage_primary")

    def close(self):
        calls.append("reader")
        original(self)
        raise OSError("reader close fault")

    def target_close(target, *args, **kwargs):
        calls.append("target")
        original_target(target, *args, **kwargs)
        raise OSError("target close fault")

    monkeypatch.setattr(SpecificationFsSdkProvider, "_observe_adaptation", invalid)
    monkeypatch.setattr(SpecificationFsSdkProvider, "close", close)
    monkeypatch.setattr(protocol, "release_specification_draft_input", target_close)
    with pytest.raises(
        SpecificationOperationError, match="strict_stage_primary"
    ) as caught:
        with manager as client:
            client.create_draft(kwargs["request"])
    evidence = caught.value.cleanup_evidence
    assert calls == ["reader", "target"]
    assert "staged_reader_close_failed:OSError" in evidence.cleanup_diagnostics
    assert (
        "issue_release_failed:IssueDraftPackageRefusal" in evidence.cleanup_diagnostics
    )
    assert "protocol_release_failed:OSError" in evidence.input_custody.diagnostics
    assert evidence.issue_disposition.evidence.effects
    assert evidence.protocol_invocation.invocation_state == "raised"
    assert caught.value.effect == "unknown"
    assert not (root / "customer/specs/widget").exists()


def test_returned_admission_entry_failure_tracks_context_cleanup_once(
    inputs, monkeypatch
):
    _, _, _, kwargs = inputs
    calls = []
    original = FilesystemIssueDraftPackageAdmission.release

    def invalid(self):
        raise ValueError("binding invalid")

    def release(self):
        calls.append(self)
        return original(self)

    monkeypatch.setattr(
        FilesystemIssueOperationProvider,
        "observe_draft_package_binding",
        lambda *a: invalid(None),
    )
    monkeypatch.setattr(FilesystemIssueDraftPackageAdmission, "release", release)
    manager = open_governed_specification_draft(**kwargs)
    with pytest.raises(SpecificationOperationError) as caught:
        manager.__enter__()
    evidence = caught.value.cleanup_evidence
    assert evidence.physical_invocation.responsibility == "context"
    assert evidence.physical_invocation.invocation_state == "returned"
    assert evidence.protocol_invocation.invocation_state == "returned"
    manager.__exit__(None, None, None)
    assert len(calls) == 1


def test_late_exit_failure_preserves_publication_and_exact_order(inputs, monkeypatch):
    root, _, _, kwargs = inputs
    original = FilesystemIssueDraftPackageAdmission.release_published_read

    def release(self, value):
        original(self, value)
        raise OSError("late independent read exit")

    manager = open_governed_specification_draft(**kwargs)
    with pytest.raises(SpecificationOperationError) as caught, manager as client:
        result = client.create_draft(kwargs["request"])
        prior = manager.observe_draft_cleanup()
        monkeypatch.setattr(
            FilesystemIssueDraftPackageAdmission, "release_published_read", release
        )
    evidence = caught.value.cleanup_evidence
    assert evidence.issue_disposition.evidence.package_outcome == "published"
    assert (
        evidence.issue_disposition.evidence.effects[
            : len(prior.issue_disposition.evidence.effects)
        ]
        == prior.issue_disposition.evidence.effects
    )
    assert evidence.protocol_invocation.invocation_state == "returned"
    assert "protocol_read_release_failed:OSError" in evidence.cleanup_diagnostics
    assert caught.value.effect == "published"
    assert (root / "customer/specs/widget/aware.spec.toml").is_file()
    assert result.evidence.package_outcome == "published"


def test_missing_original_lookup_preserves_last_history_as_unknown(inputs, monkeypatch):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    with manager as client:
        client.create_draft(kwargs["request"])
    prior = manager.observe_draft_cleanup()

    def unavailable(*args, **kwargs):
        raise OSError("lost lookup")

    monkeypatch.setattr(
        FilesystemIssueDraftPackageAdmission, "observe_cleanup", unavailable
    )
    monkeypatch.setattr(physical, "observe_package_cleanup", unavailable)
    after = manager.observe_draft_cleanup()
    assert after.issue_disposition.physical_claim == "claimed"
    assert after.issue_disposition.evidence.package_outcome == "published"
    assert (
        after.issue_disposition.evidence.effects
        == prior.issue_disposition.evidence.effects
    )
    assert after.issue_disposition == prior.issue_disposition
    assert after.physical_observation == prior.physical_observation
    assert "issue_cleanup_observation_unavailable" in after.cleanup_diagnostics
    assert "physical_cleanup_observation_unavailable" in after.cleanup_diagnostics
    assert after.physical_invocation == prior.physical_invocation


@pytest.mark.parametrize("mutation", ["request", "effects", "publication"])
def test_corrupted_same_attempt_observation_retains_last_history(
    inputs, monkeypatch, mutation
):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    with manager as client:
        client.create_draft(kwargs["request"])
    before = manager.observe_draft_cleanup()
    original = FilesystemIssueDraftPackageAdmission.observe_cleanup

    def corrupt(self):
        value = original(self)
        if mutation == "request":
            return replace(
                value, request=replace(value.request, client_intent_id="other")
            )
        if mutation == "effects":
            return replace(value, evidence=replace(value.evidence, effects=()))
        return replace(value, evidence=replace(value.evidence, package_outcome="none"))

    monkeypatch.setattr(
        FilesystemIssueDraftPackageAdmission, "observe_cleanup", corrupt
    )
    after = manager.observe_draft_cleanup()
    assert after.issue_disposition.request == before.issue_disposition.request
    assert (
        after.issue_disposition.evidence.effects
        == before.issue_disposition.evidence.effects
    )
    assert after.issue_disposition.evidence.package_outcome == "published"
    assert after.cleanup_diagnostics


@pytest.mark.parametrize("holder", ["issue", "physical"])
@pytest.mark.parametrize("outcome", ["not_attempted", "unknown", "incomplete"])
def test_published_owner_outcome_regression_retains_original_sdk_history(
    inputs, monkeypatch, holder, outcome
):
    root, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    with manager as client:
        client.create_draft(kwargs["request"])
    before = manager.observe_draft_cleanup()
    assert before.issue_disposition.physical_cleanup_outcome == "completed"
    assert before.physical_observation.outcome == "completed"

    if holder == "issue":
        original = FilesystemIssueDraftPackageAdmission.observe_cleanup

        def corrupt_issue(self):
            return replace(original(self), physical_cleanup_outcome=outcome)

        monkeypatch.setattr(
            FilesystemIssueDraftPackageAdmission, "observe_cleanup", corrupt_issue
        )
    else:
        original = physical.observe_package_cleanup

        def corrupt_physical(plan):
            return replace(original(plan), outcome=outcome)

        monkeypatch.setattr(physical, "observe_package_cleanup", corrupt_physical)

    after = manager.observe_draft_cleanup()
    assert after.issue_disposition == before.issue_disposition
    assert after.physical_observation == before.physical_observation
    assert "draft_cleanup_history_unavailable" in after.cleanup_diagnostics
    assert after.physical_invocation == before.physical_invocation
    assert after.protocol_invocation == before.protocol_invocation
    # Reuse the actual terminal provider, not a second writer or copied refusal.
    with pytest.raises(SpecificationOperationError) as caught:
        SpecificationSdkClient(manager, draft_evidence_reader=manager).create_draft(
            kwargs["request"]
        )
    assert caught.value.code == "governed_draft_context_terminal"
    assert caught.value.evidence.package_outcome == "published"
    assert caught.value.cleanup_evidence.issue_disposition == before.issue_disposition
    assert (
        caught.value.cleanup_evidence.physical_observation
        == before.physical_observation
    )
    assert (
        "draft_cleanup_history_unavailable"
        in caught.value.cleanup_evidence.cleanup_diagnostics
    )
    assert caught.value.cleanup_evidence.protocol_owner_outcome == "unknown"
    assert (root / "customer/specs/widget/aware.spec.toml").is_file()
