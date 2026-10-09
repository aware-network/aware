"""Genuine Issue/Protocol/FileSystem custody; no copied evaluator or publisher."""

import importlib.util
import os
from dataclasses import replace
from pathlib import Path

import pytest
from aware_issue_fs_adapter.draft_package import FilesystemIssueDraftPackageAdmission
from aware_specification_fs_sdk_adapter import open_governed_specification_draft
from aware_specification_sdk import (
    SpecificationObserveRequest,
    SpecificationOperationError,
)


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "custody_spec_fixture", Path(__file__).with_name("test_governed_draft.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = module.context.__wrapped__(tmp_path, monkeypatch)
    value = next(fixture)
    yield value
    monkeypatch.undo()
    with pytest.raises(StopIteration):
        next(fixture)


def custody(kwargs):
    return kwargs["issue_provider"].retain_draft_inputs(
        attempt_ref="custody:original-attempt",
        client_intent_id=kwargs["client_intent_id"],
        protocol_target=kwargs["protocol_draft_target"],
        physical_plan=kwargs["physical_package_plan"],
    )


def fds():
    return len(os.listdir("/proc/self/fd"))


def repository_descriptors(root):
    result = []
    for name in os.listdir("/proc/self/fd"):
        try:
            path = os.readlink("/proc/self/fd/" + name)
        except FileNotFoundError:
            continue  # The descriptor used for this diagnostic scan closed.
        if path == str(root) or path.startswith(str(root) + "/"):
            result.append((name, path))
    return result


@pytest.mark.parametrize("boundary", ["constructor", "manifest", "issue", "preview"])
def test_actual_associated_refusal_or_preview_disposes_original_descriptors(
    inputs, boundary
):
    root, manifest, _, kwargs = inputs
    guard = custody(kwargs)
    before = fds()
    assert repository_descriptors(root)
    if boundary == "constructor":
        with pytest.raises(SpecificationOperationError) as caught:
            open_governed_specification_draft(
                **{**kwargs, "request": object()}, input_custody=guard
            )
        evidence = caught.value.cleanup_evidence
    else:
        if boundary == "manifest":
            manifest.write_bytes(manifest.read_bytes() + b"\n# stale\n")
        if boundary == "issue":
            kwargs = {**kwargs, "expected_issue_sha256": "sha256:" + "0" * 64}
        manager = open_governed_specification_draft(**kwargs, input_custody=guard)
        if boundary == "preview":
            with manager:
                assert (
                    manager.observe_draft_cleanup().input_custody.attempt_ref
                    == "custody:original-attempt"
                )
        else:
            with pytest.raises(SpecificationOperationError):
                manager.__enter__()
        evidence = manager.observe_draft_cleanup()
    assert fds() < before
    assert repository_descriptors(root) == []
    assert evidence.attempt_ref == "custody:original-attempt"
    assert evidence.input_custody.context_ref.startswith("specification-context:")
    assert evidence.input_custody.physical.owner_cleanup_outcome == "completed"
    assert (
        evidence.protocol_owner_attempted is True
        and evidence.protocol_owner_outcome == "completed"
    )
    assert not (root / "customer/specs/widget").exists()
    assert (root / "unrelated.txt").read_text() == "untouched dirty work\n"


def test_genuine_complete_loop_keeps_claims_private_and_history_after_exit(inputs):
    root, _, issue, kwargs = inputs
    guard = custody(kwargs)
    original_issue = issue.read_bytes()
    manager = open_governed_specification_draft(**kwargs, input_custody=guard)
    with manager as client:
        result = client.create_draft(kwargs["request"])
        assert client.observe(SpecificationObserveRequest()) == result.observation
        assert result.evidence.completion_verified
        assert result.evidence.attempt_ref == "custody:original-attempt"
        observed = manager.observe_draft_cleanup()
        assert observed.input_custody.physical_evidence.package_outcome == "published"
        assert observed.input_custody.physical.transfer == "completed"
    final = manager.observe_draft_cleanup()
    assert (
        final.input_custody.physical_evidence.effects[
            : len(observed.input_custody.physical_evidence.effects)
        ]
        == observed.input_custody.physical_evidence.effects
    )
    assert final.input_custody.physical.owner_cleanup_outcome == "completed"
    assert final.protocol_owner_attempted is True
    assert final.protocol_owner_outcome == "completed"
    assert repository_descriptors(root) == []
    assert issue.read_bytes() == original_issue
    assert (root / "customer/specs/widget/aware.spec.toml").is_file()


def test_failed_original_context_issuance_carries_disposal_without_returned_handle(
    inputs, monkeypatch
):
    from aware_issue_fs_adapter import draft_package as owner

    root, _, _, kwargs = inputs
    guard = custody(kwargs)
    before = fds()

    def failed_finalizer(*args, **kwargs):
        raise OSError("context finalizer registration failed")

    monkeypatch.setattr(owner, "finalize", failed_finalizer)
    with pytest.raises(SpecificationOperationError) as caught:
        open_governed_specification_draft(**kwargs, input_custody=guard)
    evidence = caught.value.cleanup_evidence
    assert caught.value.code == "issue_input_context_claim_failed"
    assert evidence.input_custody.attempt_ref == "custody:original-attempt"
    assert evidence.input_custody.context_ref.startswith("specification-context:")
    assert evidence.input_custody.physical.owner_cleanup_attempted is True
    assert evidence.input_custody.physical.owner_cleanup_outcome == "completed"
    assert evidence.physical_invocation.invocation_state == "not_invoked"
    assert fds() < before
    assert repository_descriptors(root) == []
    assert not (root / "customer/specs/widget").exists()
    after = fds()
    assert guard.observe_cleanup().physical.owner_cleanup_outcome == "completed"
    assert fds() == after  # Detached observation never retries disposal.


@pytest.mark.parametrize("stale", [False, True])
def test_second_context_refuses_without_first_owner_cleanup(inputs, stale):
    _, manifest, _, kwargs = inputs
    guard = custody(kwargs)
    first = open_governed_specification_draft(**kwargs, input_custody=guard)
    before = first.observe_draft_cleanup()
    if stale:
        manifest.write_bytes(manifest.read_bytes() + b"\n# changed\n")
    with pytest.raises(SpecificationOperationError):
        open_governed_specification_draft(**kwargs, input_custody=guard)
    after = first.observe_draft_cleanup()
    assert after.input_custody == before.input_custody
    assert after.input_custody.physical.owner_cleanup_attempted is False
    first.__exit__(None, None, None)
    assert (
        first.observe_draft_cleanup().input_custody.physical.owner_cleanup_attempted
        is True
    )


@pytest.mark.parametrize("kind", ["none", "snapshot", "foreign_plan"])
def test_unverified_custody_never_authorizes_cleanup(inputs, kind):
    _, _, _, kwargs = inputs
    guard = custody(kwargs)
    snapshot = guard.observe_cleanup()
    altered = (
        kwargs
        if kind != "foreign_plan"
        else {**kwargs, "physical_package_plan": object()}
    )
    supplied = object() if kind == "none" else snapshot if kind == "snapshot" else guard
    with pytest.raises(SpecificationOperationError) as caught:
        open_governed_specification_draft(**altered, input_custody=supplied)
    assert guard.observe_cleanup() == snapshot
    assert caught.value.cleanup_evidence.input_custody is None
    guard.release()


@pytest.mark.parametrize("fault", ["lookup", "history", "nested"])
def test_faulted_observer_retains_known_custody_publication(inputs, monkeypatch, fault):
    _, _, _, kwargs = inputs
    manager = open_governed_specification_draft(**kwargs, input_custody=custody(kwargs))
    with (
        pytest.raises(SpecificationOperationError, match="draft_cleanup_failed"),
        manager as client,
    ):
        client.create_draft(kwargs["request"])
        before = manager.observe_draft_cleanup()
        original = FilesystemIssueDraftPackageAdmission.observe_input_custody

        def observe(self):
            value = original(self)
            if fault == "lookup":
                raise RuntimeError("historical lookup failed")
            if fault == "nested":
                return replace(value, physical=object())
            return replace(
                value,
                physical_evidence=replace(
                    value.physical_evidence, package_outcome="none", effects=()
                ),
            )

        monkeypatch.setattr(
            FilesystemIssueDraftPackageAdmission, "observe_input_custody", observe
        )
        after = manager.observe_draft_cleanup()
        assert after.input_custody == before.input_custody
        assert "input_custody_observation_unavailable" in after.cleanup_diagnostics
        monkeypatch.setattr(
            FilesystemIssueDraftPackageAdmission, "observe_input_custody", original
        )
    assert (
        manager.observe_draft_cleanup().input_custody.physical_evidence.package_outcome
        == "published"
    )
