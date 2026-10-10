"""Real owner transfer boundaries; detached responsibility is not authority."""

import importlib.util
from pathlib import Path

import pytest
from aware_file_system import retained_package as physical
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk.draft_package import IssueDraftPackageRefusal
from aware_protocol_fs_adapter import SpecificationDraftTargetSelection
from aware_specification_fs_sdk_adapter import open_governed_specification_draft
from aware_specification_sdk import SpecificationOperationError


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "preissuance_original_fixture",
        Path(__file__).with_name("test_governed_draft.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = module.context.__wrapped__(tmp_path, monkeypatch)
    yield next(source)
    monkeypatch.undo()
    with pytest.raises(StopIteration):
        next(source)


@pytest.mark.parametrize("change", [b"\n# changed bytes\n", b"invalid TOML\x00"])
def test_preissuance_currentness_refusal_keeps_unverified_ownership_unknown(
    inputs, change
):
    root, manifest, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    manifest.write_bytes(manifest.read_bytes() + change)
    with pytest.raises(SpecificationOperationError) as caught:
        manager.__enter__()
    evidence = caught.value.cleanup_evidence
    assert caught.value.code == "specification_draft_currentness_failed"
    assert evidence.issue_disposition is None
    assert evidence.physical_invocation.responsibility == "unknown"
    assert evidence.protocol_invocation.responsibility == "unknown"
    assert evidence.physical_invocation.invocation_state == "not_invoked"
    assert evidence.protocol_invocation.invocation_state == "not_invoked"
    assert evidence.physical_observation.attempted is False
    assert evidence.physical_observation.outcome == "not_attempted"
    assert evidence.protocol_owner_attempted is None
    assert evidence.protocol_owner_outcome == "unknown"
    assert not (root / "customer/specs/widget").exists()
    # Fixture-only disposal remains separate. This carrier does not qualify a
    # consumer release, even though this test preparer owns these originals.


@pytest.mark.parametrize("operand", ["physical_package_plan", "protocol_draft_target"])
@pytest.mark.parametrize("forged", [False, True])
def test_unverified_holders_do_not_receive_qualified_caller_disposition(
    inputs, operand, forged
):
    _, _, _, kwargs = inputs
    bad = object()
    if forged:
        kind = (
            physical.RetainedPackagePublication
            if operand == "physical_package_plan"
            else SpecificationDraftTargetSelection
        )
        bad = object.__new__(kind)
    manager = open_governed_specification_draft(**{**kwargs, operand: bad})
    with pytest.raises(SpecificationOperationError) as caught:
        manager.__enter__()
    evidence = caught.value.cleanup_evidence
    assert evidence.issue_disposition is None
    assert evidence.physical_invocation.responsibility == "unknown"
    assert evidence.protocol_invocation.responsibility == "unknown"
    assert not physical.observe_package_cleanup(
        kwargs["physical_package_plan"]
    ).attempted


@pytest.mark.parametrize("fault", [OSError, KeyboardInterrupt, SystemExit])
def test_potential_issuance_without_disposition_never_retains_caller_responsibility(
    inputs, monkeypatch, fault
):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    snapshots = []

    def issuer(*args, **kwargs):
        snapshots.append(manager.observe_draft_cleanup())
        raise fault("unavailable issuance outcome")

    monkeypatch.setattr(FilesystemIssueOperationProvider, "admit_draft_package", issuer)
    with pytest.raises(SpecificationOperationError) as caught:
        manager.__enter__()
    for evidence in (
        *snapshots,
        caught.value.cleanup_evidence,
        manager.observe_draft_cleanup(),
    ):
        assert evidence.issue_disposition is None
        assert evidence.physical_invocation.responsibility == "unknown"
        assert evidence.protocol_invocation.responsibility == "unknown"
        assert evidence.physical_observation.attempted is False
        assert "issue_cleanup_observation_unavailable" in evidence.cleanup_diagnostics


def test_unannotated_failure_after_real_claim_uses_original_owner_not_caller(
    inputs, monkeypatch
):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    original = FilesystemIssueOperationProvider.admit_draft_package
    admissions = []

    def issuer(self, *args, **kwargs):
        admissions.append(original(self, *args, **kwargs))
        raise OSError("failure after genuine admission before return")

    monkeypatch.setattr(FilesystemIssueOperationProvider, "admit_draft_package", issuer)
    try:
        with pytest.raises(SpecificationOperationError) as caught:
            manager.__enter__()
        evidence = caught.value.cleanup_evidence
        assert evidence.issue_disposition.physical_claim == "claimed"
        assert evidence.issue_disposition.physical_cleanup_attempted is False
        assert evidence.physical_invocation.responsibility == "unknown"
        assert evidence.protocol_invocation.responsibility == "unknown"
        assert evidence.physical_invocation.invocation_state == "not_invoked"
    finally:
        # The fault wrapper withheld the genuine admission. Test hygiene through
        # that owner, not permission for a consumer to guess or retry cleanup.
        for admission in admissions:
            admission.release()


def test_legacy_preclaim_disposition_does_not_restore_caller_after_owner_disposal(
    inputs,
):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(
        **{**kwargs, "expected_issue_sha256": "sha256:" + "0" * 64}
    )
    with pytest.raises(SpecificationOperationError) as caught:
        manager.__enter__()
    evidence = caught.value.cleanup_evidence
    assert evidence.issue_disposition.physical_claim == "unclaimed"
    assert evidence.issue_disposition.physical_cleanup_owner == "issue"
    assert evidence.physical_invocation.responsibility == "unknown"
    assert evidence.protocol_invocation.responsibility == "unknown"
    assert evidence.physical_observation.attempted is True


def test_real_success_transfers_both_holders_and_cleanup_is_once_only(inputs):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs)
    with manager:
        evidence = manager.observe_draft_cleanup()
        assert evidence.physical_invocation.responsibility == "context"
        assert evidence.protocol_invocation.responsibility == "context"
    after = manager.observe_draft_cleanup()
    assert after.physical_invocation.invocation_state == "returned"
    assert after.protocol_invocation.invocation_state == "returned"
    assert manager.observe_draft_cleanup() == after


@pytest.mark.parametrize("fresh_provider", [False, True])
@pytest.mark.parametrize("stale_manifest", [False, True])
def test_second_context_never_treats_preclaimed_originals_as_caller_owned(
    inputs, fresh_provider, stale_manifest
):
    root, manifest, _, kwargs = inputs
    first = open_governed_specification_draft(**kwargs)
    try:
        first.__enter__()
        before = first.observe_draft_cleanup()
        assert before.issue_disposition.physical_claim == "claimed"
        assert before.issue_disposition.physical_cleanup_owner == "issue"
        assert before.physical_invocation.responsibility == "context"
        assert before.protocol_invocation.responsibility == "context"
        assert not before.physical_observation.attempted
        other = dict(kwargs)
        if fresh_provider:
            other["issue_provider"] = FilesystemIssueOperationProvider(
                repository_root=root,
                protocol_source_ref="configuration/team/aware.protocol.toml",
            )
        if stale_manifest:
            manifest.write_bytes(manifest.read_bytes() + b"\n# second context\n")
        second = open_governed_specification_draft(**other)
        with pytest.raises(SpecificationOperationError) as caught:
            second.__enter__()
        evidence = caught.value.cleanup_evidence
        assert evidence.physical_invocation.responsibility == "unknown"
        assert evidence.protocol_invocation.responsibility == "unknown"
        assert evidence.physical_invocation.invocation_state == "not_invoked"
        assert evidence.protocol_invocation.invocation_state == "not_invoked"
        assert not evidence.physical_observation.attempted
        original = first.observe_draft_cleanup()
        assert original.issue_disposition.physical_claim == "claimed"
        assert original.issue_disposition.physical_cleanup_owner == "issue"
        assert original.physical_invocation.responsibility == "context"
        assert not original.physical_observation.attempted
        assert not (root / "customer/specs/widget").exists()
    finally:
        # Only the first genuine context owns cleanup. The rejected second
        # context/carrier never supplies cleanup permission over these inputs.
        first.__exit__(None, None, None)


def test_absent_issue_lookup_is_not_positive_untransferred_evidence(inputs):
    _, _, _, kwargs = inputs
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        kwargs["issue_provider"].observe_draft_package_cleanup(
            protocol_target=kwargs["protocol_draft_target"],
            physical_plan=kwargs["physical_package_plan"],
        )
    assert caught.value.code == "draft_cleanup_observation_unavailable"
    assert not physical.observe_package_cleanup(
        kwargs["physical_package_plan"]
    ).attempted
