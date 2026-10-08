"""Whole CLI completion over original custody, publisher and cleanup owners."""

import importlib
from dataclasses import replace

import pytest
from aware_file_system import retained_package as physical
from aware_issue_fs_adapter.draft_package import FilesystemIssueDraftPackageAdmission
from aware_protocol_fs_adapter import specification_draft_target as protocol
from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
from aware_specification_sdk import SpecificationSdkClient

from . import test_draft_commands as helpers

inputs = helpers.inputs
repository_descriptors = helpers.repository_descriptors
run = helpers.run


@pytest.mark.parametrize(
    "fault,apply",
    [
        ("physical", False),
        ("physical", True),
        ("independent_reader", True),
        ("reader_close", True),
    ],
)
def test_protocol_complete_does_not_hide_late_whole_context_failure(
    inputs, capsys, monkeypatch, apply, fault
):
    root, _, _, _, args = inputs
    before = repository_descriptors(root)
    calls = []
    if fault == "physical":
        owner = physical
        name = "release_package_input"
    elif fault == "independent_reader":
        owner = FilesystemIssueDraftPackageAdmission
        name = "release_published_read"
    else:
        owner = SpecificationFsSdkProvider
        name = "close"
    original = getattr(owner, name)

    def fail(*args, **kwargs):
        value = original(*args, **kwargs)
        calls.append(value)
        raise OSError("controlled late original cleanup fault")

    if fault == "reader_close":
        create = SpecificationSdkClient.create_draft

        def published(client, request):
            result = create(client, request)
            # Fault the actual published reader, not the earlier staged reader.
            monkeypatch.setattr(owner, name, fail)
            return result

        monkeypatch.setattr(SpecificationSdkClient, "create_draft", published)
    else:
        monkeypatch.setattr(owner, name, fail)
    result = run(args + (["--apply"] if apply else []), capsys)
    assert result["consumer_completion_verified"] is False
    assert result["protocol_owner_completion"] == "completed"
    assert result["cleanup_evidence"]["protocol_owner_attempted"] is True
    assert result["error"] != "draft_cleanup_completion_unverified"
    assert result["effect"] == ("published" if apply else "none")
    assert calls
    assert repository_descriptors(root) == before
    assert (root / "customer/specs/widget").exists() is apply


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("fault", ["before_close", "after_close", "no_op"])
def test_terminal_original_cleanup_outcome_is_never_upgraded_by_later_disposal(
    inputs, capsys, monkeypatch, apply, fault
):
    root, _, _, _, args = inputs
    before = repository_descriptors(root)
    original = protocol._release_owned_selection
    retained = []

    def fail(selection):
        retained.append(selection)
        if fault == "no_op":
            return
        if fault == "after_close":
            original(selection)
        raise OSError("controlled original Protocol completion fault")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(protocol, "_release_owned_selection", fail)
            result = run(args + (["--apply"] if apply else []), capsys)
        expected = "unknown" if fault == "no_op" else "incomplete"
        assert result["protocol_owner_completion"] == expected
        assert result["cleanup_evidence"]["protocol_owner_attempted"] is True
        assert result["consumer_completion_verified"] is False
        assert result["effect"] == ("published" if apply else "none")
        assert len(retained) == 1
        assert (
            result["cleanup_evidence"]["input_custody"]["physical"][
                "owner_cleanup_outcome"
            ]
            == "completed"
        )
    finally:
        # Explicit test-owner hygiene, not product retry or new completion proof.
        for selection in retained:
            original(selection)
    assert result["protocol_owner_completion"] == expected
    assert len(retained) == 1
    assert repository_descriptors(root) == before


@pytest.mark.parametrize("apply", [False, True])
def test_legacy_factory_cannot_gain_completion_from_new_supplier_version(
    inputs, capsys, monkeypatch, apply
):
    root, _, _, _, args = inputs
    before = repository_descriptors(root)
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")
    original = spec.open_governed_specification_draft
    retained = []

    def legacy(**kwargs):
        retained.append(kwargs.pop("input_custody"))
        return original(**kwargs)

    monkeypatch.setattr(spec, "open_governed_specification_draft", legacy)
    # CLI-reserved originals cannot silently be reclaimed by a legacy entrance.
    try:
        result = run(args + (["--apply"] if apply else []), capsys)
        assert result["consumer_completion_verified"] is False
        assert result["protocol_owner_completion"] == "unknown"
        assert result["cleanup_evidence"]["protocol_owner_attempted"] is None
        assert not (root / "customer/specs/widget").exists()
    finally:
        # Unsupported callee deliberately discarded original custody. Its test
        # owner disposes that unassociated reservation; no product fallback.
        for guard in retained:
            guard.release()
    assert repository_descriptors(root) == before


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "historical_unknown",
        "not_attempted",
        "wrong_context",
        "unavailable",
        "malformed",
    ],
)
def test_projection_faults_cannot_claim_whole_context_success(
    inputs, capsys, monkeypatch, apply, fault
):
    root, _, _, _, args = inputs
    before = repository_descriptors(root)
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")
    original = spec.open_governed_specification_draft

    def factory(**kwargs):
        context = original(**kwargs)

        class ViewFault:
            def __enter__(self):
                return context.__enter__()

            def __exit__(self, *args):
                return context.__exit__(*args)

            def observe_draft_cleanup(self):
                value = context.observe_draft_cleanup()
                if fault == "unavailable":
                    raise RuntimeError("CLI view unavailable after original exit")
                if fault == "malformed":
                    return object()
                if fault == "historical_unknown":
                    return replace(
                        value,
                        protocol_owner_attempted=None,
                        protocol_owner_outcome="unknown",
                    )
                if fault == "not_attempted":
                    return replace(
                        value,
                        protocol_owner_attempted=False,
                        protocol_owner_outcome="not_attempted",
                        input_custody=replace(
                            value.input_custody,
                            protocol=replace(
                                value.input_custody.protocol,
                                owner_cleanup_attempted=False,
                                owner_cleanup_outcome="not_attempted",
                            ),
                        ),
                    )
                return replace(
                    value,
                    input_custody=replace(
                        value.input_custody, context_ref="foreign-context"
                    ),
                )

        return ViewFault()

    monkeypatch.setattr(spec, "open_governed_specification_draft", factory)
    result = run(args + (["--apply"] if apply else []), capsys)
    assert result["consumer_completion_verified"] is False
    assert result["error"] == "draft_cleanup_completion_unverified"
    assert result["effect"] == ("published" if apply else "none")
    assert repository_descriptors(root) == before
    if fault == "historical_unknown":
        assert result["protocol_owner_completion"] == "unknown"
        assert result["cleanup_evidence"]["protocol_owner_attempted"] is None


@pytest.mark.parametrize("apply", [False, True])
def test_no_json_is_emitted_until_original_context_has_exited(
    inputs, capsys, monkeypatch, apply
):
    root, _, _, _, args = inputs
    before = repository_descriptors(root)
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")
    original = spec.open_governed_specification_draft
    exited = []

    def factory(**kwargs):
        context = original(**kwargs)

        class ExitWitness:
            def __enter__(self):
                return context.__enter__()

            def __exit__(self, *args):
                assert capsys.readouterr().out == ""
                value = context.__exit__(*args)
                exited.append(True)
                assert repository_descriptors(root) == before
                return value

            def observe_draft_cleanup(self):
                assert exited
                return context.observe_draft_cleanup()

        return ExitWitness()

    monkeypatch.setattr(spec, "open_governed_specification_draft", factory)
    result = run(args + (["--apply"] if apply else []), capsys, exit_code=0)
    assert exited == [True]
    assert result["consumer_completion_verified"] is True
    assert result["protocol_owner_completion"] == "completed"
    assert not result["cleanup_diagnostics"]
    assert not result["caller_cleanup"]
    assert (root / "unrelated.txt").read_text() == "untouched dirty work\n"
