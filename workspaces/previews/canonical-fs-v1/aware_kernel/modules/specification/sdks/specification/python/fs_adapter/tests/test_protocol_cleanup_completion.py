"""Genuine original Protocol completion through Issue custody and SPEC."""

import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest
from aware_issue_fs_adapter.draft_package import FilesystemIssueDraftPackageAdmission
from aware_protocol_fs_adapter import specification_draft_target as protocol
from aware_specification_fs_sdk_adapter import open_governed_specification_draft
from aware_specification_sdk import SpecificationOperationError


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "completion_fixture", Path(__file__).with_name("test_draft_input_custody.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = module.inputs.__wrapped__(tmp_path, monkeypatch)
    root, manifest, issue, kwargs = next(fixture)
    yield root, manifest, issue, kwargs, module
    with pytest.raises(StopIteration):
        next(fixture)


def test_original_attempt_not_attempted_then_completed_with_detached_history(inputs):
    root, _, issue, kwargs, helpers = inputs
    original_issue = issue.read_bytes()
    manager = open_governed_specification_draft(
        **kwargs, input_custody=helpers.custody(kwargs)
    )
    before = manager.observe_draft_cleanup()
    assert before.protocol_owner_attempted is False
    assert before.protocol_owner_outcome == "not_attempted"
    with manager as client:
        result = client.create_draft(kwargs["request"])
        assert result.evidence.package_outcome == "published"
    after = manager.observe_draft_cleanup()
    assert after.protocol_owner_attempted is True
    assert after.protocol_owner_outcome == "completed"
    assert before.protocol_owner_outcome == "not_attempted"
    assert after.input_custody.protocol.owner_cleanup_outcome == "completed"
    assert helpers.repository_descriptors(root) == []
    assert issue.read_bytes() == original_issue


def test_legacy_context_without_custody_keeps_historical_unknown(inputs):
    root, _, _, kwargs, helpers = inputs
    manager = open_governed_specification_draft(**kwargs)
    with manager as client:
        client.create_draft(kwargs["request"])
    after = manager.observe_draft_cleanup()
    assert after.input_custody is None
    assert after.protocol_owner_attempted is None
    assert after.protocol_owner_outcome == "unknown"
    assert helpers.repository_descriptors(root) == []


@pytest.mark.parametrize("fault", ["physical", "independent_reader"])
def test_original_protocol_completion_is_not_whole_context_cleanup(
    inputs, monkeypatch, fault
):
    from aware_file_system import retained_package as physical

    root, _, _, kwargs, helpers = inputs
    manager = open_governed_specification_draft(
        **kwargs, input_custody=helpers.custody(kwargs)
    )
    if fault == "physical":
        original = physical.release_package_input

        def fail(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError("controlled physical release late failure")

        monkeypatch.setattr(physical, "release_package_input", fail)
    with pytest.raises(SpecificationOperationError), manager as client:
        client.create_draft(kwargs["request"])
        if fault == "independent_reader":
            original_read = FilesystemIssueDraftPackageAdmission.release_published_read

            def fail_read(admission, value):
                original_read(admission, value)
                raise OSError("controlled independent reader late failure")

            monkeypatch.setattr(
                FilesystemIssueDraftPackageAdmission,
                "release_published_read",
                fail_read,
            )
    after = manager.observe_draft_cleanup()
    assert after.protocol_owner_attempted is True
    assert after.protocol_owner_outcome == "completed"
    assert after.cleanup_diagnostics or after.input_custody.diagnostics
    assert after.input_custody.physical_evidence.package_outcome == "published"
    assert helpers.repository_descriptors(root) == []


@pytest.mark.parametrize("when", ["before_close", "after_close", "no_op"])
def test_original_failure_or_no_op_cannot_be_upgraded_by_later_disposal(
    inputs, monkeypatch, when
):
    root, _, _, kwargs, helpers = inputs
    manager = open_governed_specification_draft(
        **kwargs, input_custody=helpers.custody(kwargs)
    )
    original = protocol._release_owned_selection
    state = protocol._ISSUED[kwargs["protocol_draft_target"]]
    calls = []

    def fault(selection):
        calls.append(selection)
        if when == "no_op":
            return
        if when == "after_close":
            original(selection)
        raise OSError("controlled original selection cleanup fault")

    with monkeypatch.context() as patch:
        patch.setattr(protocol, "_release_owned_selection", fault)
        with pytest.raises(SpecificationOperationError), manager as client:
            client.create_draft(kwargs["request"])
    after = manager.observe_draft_cleanup()
    outcome = "unknown" if when == "no_op" else "incomplete"
    assert after.protocol_owner_attempted is True
    assert after.protocol_owner_outcome == outcome
    assert after.input_custody.physical_evidence.package_outcome == "published"
    assert after.input_custody.physical.owner_cleanup_outcome == "completed"
    assert len(calls) == 1
    # Test-only disposal, never product completion or permission to retry.
    original(state.selection)
    later = manager.observe_draft_cleanup()
    assert later.protocol_owner_outcome == outcome
    assert len(calls) == 1
    assert helpers.repository_descriptors(root) == []


def test_retirement_failure_then_later_release_retains_original_fault(
    inputs, monkeypatch
):
    root, manifest, _, kwargs, helpers = inputs
    manager = open_governed_specification_draft(
        **kwargs, input_custody=helpers.custody(kwargs)
    )
    state = protocol._ISSUED[kwargs["protocol_draft_target"]]
    original = protocol._release_owned_selection
    calls = []

    def fail(selection):
        calls.append(selection)
        raise OSError("controlled retirement failure")

    with monkeypatch.context() as patch:
        patch.setattr(protocol, "_release_owned_selection", fail)
        manifest.write_bytes(manifest.read_bytes() + b"\n# stale\n")
        with pytest.raises(SpecificationOperationError):
            manager.__enter__()
    after = manager.observe_draft_cleanup()
    assert after.protocol_owner_attempted is True
    assert after.protocol_owner_outcome == "incomplete"
    assert after.input_custody.physical_evidence.package_outcome == "none"
    with pytest.raises(SpecificationOperationError, match="draft_cleanup_failed"):
        manager.__exit__(None, None, None)
    assert manager.observe_draft_cleanup().protocol_owner_outcome == "incomplete"
    assert len(calls) == 1
    original(state.selection)
    assert manager.observe_draft_cleanup().protocol_owner_outcome == "incomplete"
    assert helpers.repository_descriptors(root) == []


@pytest.mark.parametrize("fault", ["lookup", "regression", "wrong_context"])
def test_bad_observation_retains_known_completed_original_history(
    inputs, monkeypatch, fault
):
    _, _, _, kwargs, helpers = inputs
    manager = open_governed_specification_draft(
        **kwargs, input_custody=helpers.custody(kwargs)
    )
    with (
        pytest.raises(SpecificationOperationError, match="draft_cleanup_failed"),
        manager as client,
    ):
        client.create_draft(kwargs["request"])
        before = manager.observe_draft_cleanup()
        assert before.protocol_owner_outcome == "completed"
        original = FilesystemIssueDraftPackageAdmission.observe_input_custody

        def observe(admission):
            value = original(admission)
            if fault == "lookup":
                raise RuntimeError("controlled historical observation failure")
            if fault == "wrong_context":
                return replace(value, context_ref="other-context")
            return replace(
                value,
                protocol=replace(
                    value.protocol,
                    owner_cleanup_attempted=False,
                    owner_cleanup_outcome="not_attempted",
                ),
            )

        with monkeypatch.context() as patch:
            patch.setattr(
                FilesystemIssueDraftPackageAdmission, "observe_input_custody", observe
            )
            after = manager.observe_draft_cleanup()
            assert after.input_custody == before.input_custody
            assert after.protocol_owner_outcome == "completed"
            assert "input_custody_observation_unavailable" in after.cleanup_diagnostics
