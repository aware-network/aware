"""Saved capture data qualification; these fixtures never issue operation authority."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import asdict, fields, replace
from pathlib import Path

import pytest
from aware_specification_sdk import (
    SPECIFICATION_DRAFT_EVIDENCE_PROFILE,
    SpecificationDraftEvidence,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalEffect,
    SpecificationSavedReceiptCleanup,
    SpecificationSavedReceiptClient,
    SpecificationSavedReceiptError,
    SpecificationSavedReceiptErrorEvidence,
    SpecificationSavedReceiptEvidenceGrade,
    SpecificationSavedReceiptReadCleanup,
    SpecificationSavedReceiptRequest,
    SpecificationSavedReceiptValueError,
    decode_saved_draft_capture,
    present_saved_draft_capture,
)
from aware_specification_sdk import saved_receipt as owner

SHA = "sha256:" + "1" * 64


def packet():
    return {
        "effect": "none",
        "consumer_completion_verified": False,
        "retained_capability_exported": False,
        "cleanup_evidence": None,
        "input_custody": None,
        "caller_cleanup": {},
        "cleanup_diagnostics": [],
        "protocol_owner_completion": "unknown",
        "error": "original_refusal",
    }


def body(value):
    return json.dumps(value, sort_keys=True, indent=2).encode() + b"\n"


def request(content, **changes):
    return replace(
        SpecificationSavedReceiptRequest(
            "/explicit/root",
            "captures/full.json",
            "sha256:" + hashlib.sha256(content).hexdigest(),
        ),
        **changes,
    )


def present(content, **changes):
    return present_saved_draft_capture(
        request(content, **changes),
        content,
        provider_ref="original-reader:fixture",
        provider_distribution="fixture",
        provider_version="0.0.0",
        cleanup=SpecificationSavedReceiptReadCleanup("closed", 3, 3, 3),
    )


def legacy(effect_state="applied"):
    return {
        "root_locator": "/explicit/root",
        "target_path": "plans/demo",
        "scratch_path": "plans/scratch",
        "attempted": True,
        "outcome": "unknown",
        "evidence": {
            "package_outcome": "unknown",
            "residual_scratch_paths": ["plans/scratch"],
            "cleanup_diagnostics": ["original cleanup uncertain"],
            "durability_confirmed": False,
            "effects": [
                {
                    "path": "plans/scratch/a",
                    "kind": "file_write",
                    "state": effect_state,
                    "durability_confirmed": False,
                    "mode": 0o600,
                    "before_digest": None,
                    "after_digest": SHA,
                    "after_identity": [1, 2],
                }
            ],
        },
    }


def evidence():
    effects = tuple(
        SpecificationDraftPhysicalEffect(
            "plans/scratch/" + state,
            "file_write",
            state,
            None,
            None,
            SHA,
            None,
            (1, index),
            index == 1,
        )
        for index, state in enumerate(("none", "applied", "unknown"))
    )
    return SpecificationDraftEvidence(
        SPECIFICATION_DRAFT_EVIDENCE_PROFILE,
        "attempt:one",
        "issue:one",
        "execution:one",
        "client:one",
        "intent:one",
        SHA,
        "plans/demo",
        "plans/scratch",
        (SpecificationDraftMemberBinding("a", 1, SHA),),
        "unknown",
        effects,
        ("plans/scratch",),
        ("publication_uncertain",),
        False,
        False,
        False,
    )


def test_refused_capture_is_presented_not_replayed_or_reclassified():
    content = body(packet())
    result = present(content)
    assert result.record == packet()
    assert bytes.fromhex(result.full_body_hex) == content
    assert result.presentation_outcome == "presented"
    assert result.capture_grade == "captured_transport_not_authenticated"
    assert result.currentness == "not_revalidated"
    assert (
        result.operation_invoked
        is result.authority_restored
        is result.authorizes_retry
        is False
    )
    assert not result.omissions


@pytest.mark.parametrize("view", ["summary", "full"])
def test_full_exact_original_bytes_and_summary_parity(view):
    original = packet()
    original["caller_cleanup"] = {"physical_observation": legacy()}
    content = body(original)
    result = present(content, view=view)
    assert bytes.fromhex(result.full_body_hex) == content
    assert result.source.source_sha256 == request(content).expected_source_sha256
    if view == "full":
        assert result.record is None and result.omissions == ()
    else:
        pointer = "/caller_cleanup/physical_observation/evidence/effects"
        (descriptor,) = result.omissions
        assert descriptor.pointer == pointer
        assert descriptor.availability == "guarded_source_read"
        assert result.record["caller_cleanup"]["physical_observation"]["evidence"][
            "effects"
        ] == {"omitted": True, "pointer": pointer}
        assert (
            descriptor.effect_applied_count
            == descriptor.durability_unconfirmed_count
            == 1
        )
        assert (
            descriptor.effect_none_count
            == descriptor.effect_unknown_count
            == descriptor.durability_confirmed_count
            == 0
        )
        assert (
            descriptor.encoded_sha256
            == "sha256:"
            + hashlib.sha256(
                owner._json_body(
                    original["caller_cleanup"]["physical_observation"]["evidence"][
                        "effects"
                    ]
                )
            ).hexdigest()
        )
        assert (
            "ledger_complete"
            not in result.record["caller_cleanup"]["physical_observation"]["evidence"]
        )
        assert (
            "before_identity"
            not in decode_saved_draft_capture(content)["caller_cleanup"][
                "physical_observation"
            ]["evidence"]["effects"][0]
        )
    assert decode_saved_draft_capture(content) == original


@pytest.mark.parametrize("state", ["none", "applied", "unknown"])
def test_nonempty_original_legacy_effects_keep_each_state(state):
    original = packet()
    original["caller_cleanup"] = {"physical_observation": legacy(state)}
    result = present(body(original))
    (descriptor,) = result.omissions
    assert getattr(descriptor, "effect_" + state + "_count") == 1
    assert result.record["effect"] == "none"
    assert (
        result.record["caller_cleanup"]["physical_observation"]["outcome"] == "unknown"
    )


def test_all_effect_states_and_failure_fields_survive_summary():
    original = packet()
    value = evidence()
    original["evidence"] = asdict(value)
    original["members"] = [{"path": "a", "bytes": 1, "sha256": SHA}]
    original["effect"] = "unknown"
    result = present(body(original))
    descriptors = {item.pointer: item for item in result.omissions}
    effects = descriptors["/evidence/effects"]
    assert (
        effects.effect_none_count,
        effects.effect_applied_count,
        effects.effect_unknown_count,
    ) == (1, 1, 1)
    assert (
        effects.durability_confirmed_count,
        effects.durability_unconfirmed_count,
    ) == (1, 2)
    assert result.record["evidence"]["ledger_complete"] is False
    assert result.record["evidence"]["cleanup_diagnostics"] == ["publication_uncertain"]
    assert result.record["evidence"]["residual_scratch_paths"] == ["plans/scratch"]
    assert result.record["error"] == "original_refusal"
    assert list(descriptors) == sorted(descriptors)
    assert all(
        v.effect_applied_count is None
        for k, v in descriptors.items()
        if not k.endswith("effects")
    )


@pytest.mark.parametrize("field", ["ledger_complete", "before_identity"])
@pytest.mark.parametrize("injected", [None, True])
def test_legacy_missing_fields_are_not_added_or_accepted(field, injected):
    original = packet()
    raw = legacy()
    original["caller_cleanup"] = {"physical_observation": raw}
    target = (
        raw["evidence"] if field == "ledger_complete" else raw["evidence"]["effects"][0]
    )
    target[field] = injected
    with pytest.raises(SpecificationSavedReceiptValueError):
        present(body(original))


@pytest.mark.parametrize(
    "field,value",
    [
        ("state", "success"),
        ("durability_confirmed", 1),
        ("mode", True),
        ("after_identity", [False, 1]),
        ("path", "../outside"),
        ("after_digest", "wrong"),
        ("unknown_field", None),
    ],
)
def test_malformed_omitted_effect_refuses_before_presentation(field, value):
    original = packet()
    original["caller_cleanup"] = {"physical_observation": legacy()}
    original["caller_cleanup"]["physical_observation"]["evidence"]["effects"][0][
        field
    ] = value
    with pytest.raises(SpecificationSavedReceiptValueError):
        present(body(original))


@pytest.mark.parametrize(
    "changes",
    [
        {"consumer_completion_verified": 0},
        {"retained_capability_exported": 0},
        {"unknown_key": None},
        {"effect": "success"},
        {"cleanup_evidence": {}},
        {"input_custody": {}},
        {"evidence": {}},
        {"input_observation_error": None},
        {"observation": {}},
        {"caller_cleanup": {"unexpected": {}}},
        {"operation_outcome": "approved"},
        {"consumer_completion_verified": True},
        {"input_sha256": "1" * 64},
        {"created_paths": ["../outside"]},
    ],
)
def test_closed_capture_profile_refuses_malformed_fields(changes):
    value = packet()
    value.update(changes)
    with pytest.raises(SpecificationSavedReceiptValueError):
        present(body(value))


@pytest.mark.parametrize(
    "changes",
    [
        {"base_ref": "relative"},
        {"base_ref": "/root/../elsewhere"},
        {"base_ref": "//alias"},
        {"source_ref": "/capture.json"},
        {"source_ref": "./capture.json"},
        {"source_ref": "x//capture.json"},
        {"source_ref": "x/../capture.json"},
        {"source_ref": "x\\capture.json"},
        {"source_ref": "e\u0301.json"},
        {"source_ref": "control\npath"},
        {"source_ref": "x/" * 64 + "capture.json"},
        {"expected_source_sha256": "sha256:" + "A" * 64},
        {"view": "auto"},
        {"input_profile": "guess"},
        {"contract": "wrong"},
    ],
)
def test_explicit_request_bounds_and_no_coordinate_correction(changes):
    with pytest.raises(SpecificationSavedReceiptValueError):
        request(body(packet()), **changes)


@pytest.mark.parametrize("field", ["base_ref", "source_ref"])
def test_invalid_utf8_request_is_typed_with_original_cause(field):
    with pytest.raises(SpecificationSavedReceiptValueError) as failure:
        request(body(packet()), **{field: "\ud800"})
    assert isinstance(failure.value.__cause__, UnicodeEncodeError)


@pytest.mark.parametrize(
    "changes",
    [
        {"acquired_count": True},
        {"closed_count": -1},
        {"acquired_count": 66},
        {"closed_count": 2},
        {"diagnostics": ("uncertain",)},
    ],
)
def test_cleanup_closed_requires_exact_confirmed_counts(changes):
    with pytest.raises(SpecificationSavedReceiptValueError):
        replace(SpecificationSavedReceiptReadCleanup("closed", 3, 3, 3), **changes)


def test_unknown_read_cleanup_cannot_be_presented():
    content = body(packet())
    with pytest.raises(SpecificationSavedReceiptValueError):
        present_saved_draft_capture(
            request(content),
            content,
            provider_ref="fixture",
            provider_distribution="fixture",
            provider_version="0",
            cleanup=SpecificationSavedReceiptReadCleanup(
                "unknown", 3, 3, None, ("original_close_unknown",)
            ),
        )


def test_stale_saved_file_guard_refuses_without_refresh():
    content = body(packet())
    with pytest.raises(SpecificationSavedReceiptValueError, match="correlation"):
        present_saved_draft_capture(
            request(content),
            content + b" ",
            provider_ref="fixture",
            provider_distribution="fixture",
            provider_version="0",
            cleanup=SpecificationSavedReceiptReadCleanup("closed", 3, 3, 3),
        )


def test_source_observation_cannot_claim_bytes_without_acquisition():
    source = present(body(packet())).source
    with pytest.raises(SpecificationSavedReceiptValueError, match="acquisition"):
        replace(
            source,
            cleanup=SpecificationSavedReceiptReadCleanup("not_acquired", 0, 0, 0),
        )


@pytest.mark.parametrize("carrier", ["evidence", "legacy"])
def test_known_publication_remains_visible_and_contradictions_refuse(carrier):
    value = packet()
    if carrier == "evidence":
        value["evidence"] = asdict(replace(evidence(), package_outcome="published"))
    else:
        legacy_value = legacy()
        legacy_value["evidence"]["package_outcome"] = "published"
        value["caller_cleanup"] = {"physical_observation": legacy_value}
    with pytest.raises(SpecificationSavedReceiptValueError, match="publication"):
        present(body(value))
    value["effect"] = "published"
    result = present(body(value))
    assert (
        result.record["effect"] == "published"
        and result.record["error"] == "original_refusal"
    )
    assert result.record["consumer_completion_verified"] is False
    assert result.authorizes_retry is False


@pytest.mark.parametrize(
    "changes",
    [
        {"operation_invoked": True},
        {"authorizes_retry": True},
        {"currentness": "current"},
        {"authority_restored": True},
        {"capture_grade": "authenticated"},
        {"full_body_hex": "00"},
        {"omissions": ()},
    ],
)
def test_result_cannot_omit_full_validation_or_change_authority(changes):
    value = packet()
    value["caller_cleanup"] = {"physical_observation": legacy()}
    result = present(body(value))
    with pytest.raises(SpecificationSavedReceiptValueError):
        replace(result, **changes)


def test_summary_and_full_record_are_detached_from_provider_values():
    content = body(packet())
    returned = present(content)

    class Provider:
        def present_draft_receipt(self, prepared):
            self.prepared = prepared
            return returned

    provider = Provider()
    original = request(content)
    received = SpecificationSavedReceiptClient(provider).present_draft_receipt(original)
    assert received == returned and received is not returned
    assert provider.prepared is not original
    returned.record["error"] = "changed provider report"
    assert received.record["error"] == "original_refusal"


@pytest.mark.parametrize(
    "tamper", ["request", "record", "full_body", "source", "omissions"]
)
def test_invalid_provider_results_remain_unvalidated_unknown_without_retry(tamper):
    content = body(packet())
    result = present(content)
    if tamper == "request":
        object.__setattr__(result.request, "source_ref", "other.json")
    elif tamper == "record":
        result.record["error"] = "invented success"
    elif tamper == "full_body":
        object.__setattr__(result, "full_body_hex", "00")
    elif tamper == "source":
        object.__setattr__(result.source, "observation_grade", "authenticated")
    else:
        object.__setattr__(result, "omissions", ("forged",))

    class Provider:
        calls = 0

        def present_draft_receipt(self, prepared):
            self.calls += 1
            return result

    provider = Provider()
    with pytest.raises(SpecificationSavedReceiptError) as failure:
        SpecificationSavedReceiptClient(provider).present_draft_receipt(
            request(content)
        )
    error = failure.value.evidence
    assert provider.calls == 1
    assert error.request == request(content)
    assert error.provider_invoked is True
    assert (
        error.evidence_grade
        is SpecificationSavedReceiptEvidenceGrade.UNVALIDATED_PROVIDER_REPORT
    )
    assert (
        error.cleanup is SpecificationSavedReceiptCleanup.UNKNOWN
        and error.effect == "unknown"
    )
    assert error.observed_source is None and error.authorizes_retry is False
    assert error.reported_result_type.endswith("SpecificationSavedReceiptResult")


@pytest.mark.parametrize("failure_kind", [ValueError, KeyboardInterrupt, SystemExit])
def test_dispatch_copy_failure_is_local_not_invoked(monkeypatch, failure_kind):
    content = body(packet())
    original = request(content)
    real_replace = owner.replace
    calls = 0
    primary = failure_kind("pre-dispatch copy interrupted")

    def interrupted(value, **changes):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise primary
        return real_replace(value, **changes)

    class Provider:
        calls = 0

        def present_draft_receipt(self, prepared):
            self.calls += 1
            raise AssertionError("provider must not be invoked")

    provider = Provider()
    monkeypatch.setattr(owner, "replace", interrupted)
    with pytest.raises(SpecificationSavedReceiptError) as failure:
        SpecificationSavedReceiptClient(provider).present_draft_receipt(original)
    error = failure.value.evidence
    assert failure.value.__cause__ is primary and provider.calls == 0
    assert error.request == original and error.provider_invoked is False
    assert error.cleanup is SpecificationSavedReceiptCleanup.NOT_ACQUIRED
    assert (
        error.effect == "none"
        and error.evidence_grade
        is SpecificationSavedReceiptEvidenceGrade.LOCAL_NOT_OBSERVED
    )
    assert error.observed_source is error.reported_result is None


@pytest.mark.parametrize(
    "changes",
    [
        {"evidence_grade": "provider_observation"},
        {"provider_invoked": True},
        {"effect": "unknown"},
        {"cleanup": "unknown"},
        {"reported_result": {}},
        {"reported_result_type": "foreign"},
        {"report_diagnostics": ("foreign",)},
        {"authorizes_retry": True},
        {"operation_invoked": True},
    ],
)
def test_local_error_grade_never_claims_provider_observation(changes):
    with pytest.raises(SpecificationSavedReceiptValueError):
        replace(
            SpecificationSavedReceiptErrorEvidence(
                "invalid", "Local validation failed."
            ),
            **changes,
        )


def test_correlated_provider_refusal_is_preserved_not_captured_operation_failure():
    content = body(packet())
    original = request(content)

    class Provider:
        def present_draft_receipt(self, prepared):
            raise SpecificationSavedReceiptError(
                SpecificationSavedReceiptErrorEvidence(
                    "receipt_source_changed",
                    "Original read guard mismatched.",
                    request=prepared,
                    provider_invoked=True,
                    cleanup="closed",
                    evidence_grade="provider_observation",
                    diagnostics=("original guard mismatch",),
                )
            )

    with pytest.raises(SpecificationSavedReceiptError) as failure:
        SpecificationSavedReceiptClient(Provider()).present_draft_receipt(original)
    assert failure.value.evidence.code == "receipt_source_changed"
    assert failure.value.evidence.diagnostics == ("original guard mismatch",)
    assert failure.value.evidence.reported_result is None


@pytest.mark.parametrize(
    "bad_report",
    [
        {"invalid": "\ud800"},
        {"\ud800": "invalid"},
        {"too_large": "x" * (1024**2 + 1)},
    ],
)
def test_untransportable_provider_report_cannot_mask_primary_refusal(bad_report):
    class Provider:
        calls = 0

        def present_draft_receipt(self, prepared):
            self.calls += 1
            return bad_report

    provider = Provider()
    with pytest.raises(SpecificationSavedReceiptError) as failure:
        SpecificationSavedReceiptClient(provider).present_draft_receipt(
            request(body(packet()))
        )
    error = failure.value.evidence
    assert provider.calls == 1
    assert error.reported_result is None
    assert error.report_diagnostics == ("provider_report_not_transportable",)
    assert error.effect == "unknown" and error.cleanup == "unknown"
    assert error.evidence_grade == "unvalidated_provider_report"
    assert isinstance(failure.value.__cause__, SpecificationSavedReceiptValueError)
    assert str(failure.value.__cause__) == "receipt_result_type_invalid"


def test_neutral_sdk_import_and_exports_do_not_activate_optional_owners():
    script = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.startswith(("aware_file_system", "aware_issue", "aware_protocol", "aware_specification_fs")):
            raise AssertionError("forbidden optional owner: " + name)
sys.meta_path.insert(0, Block())
import aware_specification_sdk as sdk
assert all(getattr(sdk, name) is not None for name in sdk.__all__)
"""
    run = subprocess.run(
        [sys.executable, "-B", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr


def test_authored_receipt_values_match_exact_python_field_roots():
    from aware_sdk_contract_runtime_source import materialize_sdk_source_contract

    home = Path(__file__).resolve().parents[3] / "aware"
    operation_ref = owner.SPECIFICATION_SAVED_RECEIPT_OPERATION_REF
    contract = materialize_sdk_source_contract(
        sdk_toml_text=(home / "aware.sdk.toml").read_text(),
        source_text_by_path={p.name: p.read_text() for p in home.glob("*.aware")},
        selected_operation_refs=(operation_ref,),
    )
    (operation,) = contract.manifest.operations
    assert operation.operation_ref == operation_ref
    assert (
        operation.provider_operation_ref
        == owner.SPECIFICATION_SAVED_RECEIPT_PROVIDER_OPERATION_REF
    )
    source = (home / "specification_saved_receipt.aware").read_text()
    for cls in owner._SAVED_VALUES:
        assert "class " + cls.__name__ + " : inline_value" in source
        for field in fields(cls):
            assert "    " + field.name + " " in source


def test_no_projection_reconstructs_success_or_caller_completion():
    value = packet()
    value["caller_cleanup"] = {
        "protocol": {"invocation_state": "returned", "owner_completion": "unknown"}
    }
    saved = copy.deepcopy(value)
    result = present(body(value))
    assert result.record == saved
    assert result.record["consumer_completion_verified"] is False
    assert result.record["protocol_owner_completion"] == "unknown"


def _original_fixture(name):
    location = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("receipt_" + name, location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _producer_bytes(value):
    from aware_specification_cli.draft_commands import _wire

    return json.dumps(value, sort_keys=True, default=_wire).encode()


def test_original_full_cleanup_transport_and_ordered_byte_pairs_validate():
    cleanup = _original_fixture("test_draft_cleanup").value()
    value = packet()
    value["cleanup_evidence"] = cleanup
    content = _producer_bytes(value)
    raw = json.loads(content)
    result = present(content)
    assert bytes.fromhex(result.full_body_hex) == content
    pointers = {item.pointer for item in result.omissions}
    assert "/cleanup_evidence/issue_disposition/request/ordered_members" in pointers
    assert "/cleanup_evidence/physical_observation/evidence/effects" in pointers
    assert (
        raw["cleanup_evidence"]["physical_observation"]["evidence"]["ledger_complete"]
        is None
    )
    assert result.record["cleanup_evidence"]["protocol_owner_outcome"] == "unknown"
    assert (
        result.record["cleanup_evidence"]["issue_disposition"]["request"][
            "candidate_sha256"
        ]
        == SHA
    )


def test_original_cleanup_custody_and_recorded_observation_validate_without_reading():
    custody = _original_fixture("test_draft_input_custody").sample()
    draft = _original_fixture("test_draft_evidence")
    from aware_specification_cli.read_commands import _observation

    value = packet()
    value["cleanup_evidence"] = custody
    value["input_custody"] = _original_issue_custody(custody.input_custody)
    value["effect"] = "published"
    value["observation"] = _observation(draft.result(draft.request()).observation)
    result = present(_producer_bytes(value))
    assert result.record["observation"]["work_authority"] is False
    assert result.record["observation"]["phase_acceptance"] is False
    assert result.record["observation"]["snapshot"] == {
        "omitted": True,
        "pointer": "/observation/snapshot",
    }
    assert (
        result.record["input_custody"]["context_ref"]
        == custody.input_custody.context_ref
    )
    invalid = json.loads(_producer_bytes(value))
    invalid["input_custody"]["client_intent_id"] = "foreign"
    with pytest.raises(SpecificationSavedReceiptValueError, match="correlation"):
        present(body(invalid))


def _original_issue_custody(spec_custody):
    from aware_issue_sdk.draft_input_custody import (
        IssueDraftInputCustodyObservation,
        IssueDraftInputResourceObservation,
    )
    from aware_issue_sdk.draft_package import (
        IssueDraftPackageEffect,
        IssueDraftPackageEvidence,
    )

    raw = asdict(spec_custody)
    for name in ("physical", "protocol"):
        raw[name] = IssueDraftInputResourceObservation(**raw[name])
    ledger = raw["physical_evidence"]
    if ledger is not None:
        effects = []
        for effect in ledger["effects"]:
            del effect["before_identity"]
            effects.append(IssueDraftPackageEffect(**effect))
        raw["physical_evidence"] = IssueDraftPackageEvidence(
            **{**ledger, "effects": tuple(effects)}
        )
    return IssueDraftInputCustodyObservation(**raw)


@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize("complete", [False, True, None])
def test_original_issue_nonempty_transport_does_not_invent_identity_or_completeness(
    view, complete
):
    from aware_specification_sdk import SpecificationDraftCleanupLedger

    cleanup = _original_fixture("test_draft_input_custody").sample()
    original = replace(
        cleanup.input_custody,
        physical_evidence=SpecificationDraftCleanupLedger(
            "unknown",
            evidence().effects,
            ("plans/scratch",),
            ("historical uncertainty",),
            False,
            complete,
        ),
    )
    value = packet()
    value["input_custody"] = _original_issue_custody(original)
    content = _producer_bytes(value)
    if complete is None:
        with pytest.raises(SpecificationSavedReceiptValueError, match="issue_ledger"):
            present(content, view=view)
        return
    result = present(content, view=view)
    assert bytes.fromhex(result.full_body_hex) == content
    raw = json.loads(content)
    ledger = raw["input_custody"]["physical_evidence"]
    assert ledger["ledger_complete"] is complete
    assert all("before_identity" not in effect for effect in ledger["effects"])
    if view == "summary":
        assert (
            result.record["input_custody"]["physical_evidence"]["ledger_complete"]
            is complete
        )
        omitted = next(
            item
            for item in result.omissions
            if item.pointer == "/input_custody/physical_evidence/effects"
        )
        assert (
            omitted.effect_none_count,
            omitted.effect_applied_count,
            omitted.effect_unknown_count,
        ) == (1, 1, 1)


@pytest.mark.parametrize("view", ["summary", "full"])
def test_unreported_execution_stays_unknown_without_weakening_two_custody_join(view):
    cleanup = _original_fixture("test_draft_input_custody").sample()
    custody = replace(cleanup.input_custody, execution_ref=None)
    value = packet()
    value["effect"] = "published"
    value["cleanup_evidence"] = replace(cleanup, input_custody=custody)
    value["input_custody"] = _original_issue_custody(custody)
    value["evidence"] = replace(
        evidence(),
        attempt_ref=custody.attempt_ref,
        client_intent_id=custody.client_intent_id,
        execution_ref=cleanup.input_custody.execution_ref,
    )
    content = _producer_bytes(value)
    result = present(content, view=view)
    assert bytes.fromhex(result.full_body_hex) == content
    raw = json.loads(content)
    assert raw["input_custody"]["execution_ref"] is None
    assert raw["cleanup_evidence"]["input_custody"]["execution_ref"] is None
    if view == "summary":
        assert result.record["input_custody"]["execution_ref"] is None
    value["cleanup_evidence"] = cleanup
    with pytest.raises(SpecificationSavedReceiptValueError, match="correlation"):
        present(_producer_bytes(value), view=view)


def test_input_observation_error_uses_original_constructor_and_exact_fields():
    from aware_specification_sdk import (
        SpecificationInputObservationError,
        SpecificationInputObservationRequest,
    )

    value = packet()
    value["input_observation_error"] = SpecificationInputObservationError(
        "input_not_readable",
        request=SpecificationInputObservationRequest("input.json", "/explicit"),
    )
    content = _producer_bytes(value)
    assert (
        present(content).record["input_observation_error"]
        == json.loads(content)["input_observation_error"]
    )
    raw = json.loads(content)
    raw["input_observation_error"]["provider_invoked"] = 1
    with pytest.raises(SpecificationSavedReceiptValueError):
        present(body(raw))


def test_genuine_lowering_and_authored_value_validation_include_the_new_operation():
    from aware_meta_type_schema import TypeSchemaBundle, validate_typed_value
    from aware_sdk_contract_runtime_provider import (
        SdkDefinitionRequest,
        lower_parsed_sdk_definition,
    )
    from aware_sdk_contract_runtime_source import materialize_sdk_source_contract
    from tree_sitter_aware.parsed_document import (
        AwarePortableParseInput,
        parse_aware_document_batch,
    )

    home = Path(__file__).resolve().parents[3] / "aware"
    sources = {p.name: p.read_text() for p in sorted(home.glob("*.aware"))}
    operation_ref = owner.SPECIFICATION_SAVED_RECEIPT_OPERATION_REF
    selected = (operation_ref,)
    contract = materialize_sdk_source_contract(
        sdk_toml_text=(home / "aware.sdk.toml").read_text(),
        source_text_by_path=sources,
        selected_operation_refs=selected,
    )
    inputs = tuple(
        AwarePortableParseInput(
            "package:specification-sdk@1",
            "specification-sdk",
            "sdk/sources/" + name,
            "cas://sdk-source/" + hashlib.sha256(text.encode()).hexdigest(),
            "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
            len(text.encode()),
            text,
        )
        for name, text in sources.items()
    )
    parsed = parse_aware_document_batch(inputs).batch
    req = SdkDefinitionRequest.create(
        sdk_ref="specification_sdk",
        semantic_version="1",
        targets=contract.manifest.targets,
        selected_operation_refs=selected,
    )
    assert (
        lower_parsed_sdk_definition(req, parsed, contract.manifest.schema_slices)
        == contract.definition_state
    )
    types = {
        item.type_ref: item
        for schema in contract.manifest.schema_slices
        for item in schema.types
    }
    bundle = TypeSchemaBundle.create(
        namespace="aware_specification_sdk", semantic_version="1", types=types.values()
    )
    value = packet()
    value["caller_cleanup"] = {"physical_observation": legacy()}
    result = present(body(value))
    samples = (
        result.request,
        result.source.cleanup,
        result.source,
        result.omissions[0],
        result,
        SpecificationSavedReceiptErrorEvidence("local", "Not invoked."),
    )
    for sample in samples:
        payload = json.loads(owner.encode_specification_saved_receipt_value(sample))
        validation = validate_typed_value(bundle, payload["type_ref"], payload["value"])
        assert validation.is_valid, validation.diagnostics


@pytest.fixture
def accepted_recovery_capture():
    """Explicit private proof input; never publish, edit or replay this capture."""
    source = os.environ.get("AWARE_SAVED_RECEIPT_ACCEPTED_R_CAPTURE")
    assert source, (
        "Supply the accepted r27 capture via AWARE_SAVED_RECEIPT_ACCEPTED_R_CAPTURE"
    )
    content = Path(source).read_bytes()
    assert len(content) == 121484
    assert hashlib.sha256(content).hexdigest() == (
        "5b82f485682523d9afd8aa105dd0f7da7a5a66d7ec21de7b1fcd10a2ecc33007"
    )
    yield content
    assert Path(source).read_bytes() == content


@pytest.mark.parametrize("view", ["summary", "full"])
def test_accepted_recovery_issue_transport_preserves_absence(
    accepted_recovery_capture, view
):
    content = accepted_recovery_capture
    result = present(content, view=view)
    assert bytes.fromhex(result.full_body_hex) == content
    wire = owner.encode_specification_saved_receipt_value(result)
    assert owner.decode_specification_saved_receipt_value(wire) == result
    raw = json.loads(content)
    ledger = raw["input_custody"]["physical_evidence"]
    assert ledger["effects"]
    assert all("before_identity" not in effect for effect in ledger["effects"])
    if view == "full":
        assert result.record is None
        assert json.loads(bytes.fromhex(result.full_body_hex)) == raw
    else:
        assert (
            result.record["input_custody"]["physical_evidence"]["ledger_complete"]
            == ledger["ledger_complete"]
        )
        omitted = next(
            item
            for item in result.omissions
            if item.pointer == "/input_custody/physical_evidence/effects"
        )
        assert omitted.item_count == len(ledger["effects"])


@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize(
    "coordinate", ["attempt_ref", "client_intent_id", "execution_ref"]
)
@pytest.mark.parametrize("top_custody", [True, False])
def test_recovery_evidence_foreign_coordinates_refuse_before_omission(
    accepted_recovery_capture, view, coordinate, top_custody
):
    raw = json.loads(accepted_recovery_capture)
    if not top_custody:
        raw["input_custody"] = None
    raw["evidence"][coordinate] = "foreign:record"
    with pytest.raises(SpecificationSavedReceiptValueError, match="correlation"):
        present(body(raw), view=view)


@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize(
    "mutation",
    [
        "issue_client",
        "issue_execution",
        "context",
        "extra_identity",
        "missing_complete",
    ],
)
def test_recovery_other_carriers_are_strict(accepted_recovery_capture, view, mutation):
    raw = json.loads(accepted_recovery_capture)
    custody = raw["input_custody"]
    if mutation == "issue_client":
        raw["cleanup_evidence"]["issue_disposition"]["request"]["client_intent_id"] = (
            "foreign:client"
        )
    elif mutation == "issue_execution":
        raw["cleanup_evidence"]["issue_disposition"]["execution_ref"] = (
            "foreign:execution"
        )
    elif mutation == "context":
        custody["context_ref"] = "foreign:context"
    elif mutation == "extra_identity":
        custody["physical_evidence"]["effects"][0]["before_identity"] = None
    else:
        del custody["physical_evidence"]["ledger_complete"]
    with pytest.raises(SpecificationSavedReceiptValueError):
        present(body(raw), view=view)


@pytest.mark.parametrize(
    "fault", ["missing", "invalid", "getter_error", "getter_interrupt"]
)
def test_malformed_provider_error_is_read_once_and_preserves_primary(fault):
    error = SpecificationSavedReceiptError(
        SpecificationSavedReceiptErrorEvidence("local", "fixture")
    )
    reads = []
    if fault == "missing":
        del error.evidence
    elif fault == "invalid":
        error.evidence = {"foreign": "unvalidated"}
    else:

        class BrokenError(SpecificationSavedReceiptError):
            def __getattribute__(self, name):
                if name == "evidence" and self.armed:
                    reads.append(name)
                    if fault == "getter_interrupt":
                        raise KeyboardInterrupt("carrier interrupted")
                    raise AttributeError("carrier unreadable")
                return super().__getattribute__(name)

        BrokenError.armed = False
        error = BrokenError(SpecificationSavedReceiptErrorEvidence("local", "fixture"))
        error.armed = True
    calls = []

    class Provider:
        def present_draft_receipt(self, value):
            calls.append(value)
            raise error

    original = request(body(packet()))
    try:
        SpecificationSavedReceiptClient(Provider()).present_draft_receipt(original)
    except BaseException as caught:  # noqa: BLE001 - prove interruption never escapes as an untyped signal
        assert type(caught) is SpecificationSavedReceiptError
        assert caught.__cause__ is error
        evidence = caught.evidence
        assert evidence.request == original
        assert evidence.provider_invoked is True
        assert evidence.evidence_grade == "unvalidated_provider_report"
        assert evidence.cleanup == "unknown" and evidence.effect == "unknown"
        if fault == "invalid":
            assert evidence.reported_result == {"foreign": "unvalidated"}
        else:
            assert evidence.reported_result is None
            assert "provider_report_not_transportable" in evidence.report_diagnostics
    else:
        pytest.fail("Malformed provider error became success")
    assert len(calls) == 1
    assert len(reads) == (1 if fault.startswith("getter") else 0)
