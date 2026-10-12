"""Production values/strict wire and dispatch correlation, not FS authority."""

import json
from dataclasses import fields, replace
from pathlib import Path

import pytest
from aware_protocol_sdk import specification_target_fit as sdk

HOME = Path(__file__).resolve().parents[2]


def request():
    return sdk.ProtocolSpecificationTargetFitRequest(
        "/customer",
        "aware.protocol.toml",
        "docs/specs/widget/aware.spec.toml",
        "sha256:" + "0" * 64,
    )


def result(value=None):
    value = request() if value is None else value
    return sdk.ProtocolSpecificationTargetFitResult(
        value,
        sdk.PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_REF,
        sdk.PROTOCOL_SPECIFICATION_TARGET_FIT_DISTRIBUTION,
        "source",
        value.expected_manifest_sha256,
        "docs/specs",
        "<spec-key>/aware.spec.toml",
        "docs/specs/<spec-key>/aware.spec.toml",
        sdk.ProtocolSpecificationTargetFitOutcome.MATCH,
        "matches",
        matched_spec_key="widget",
    )


class Provider:
    def __init__(self, action=None):
        self.calls = []
        self.action = action or result

    def observe_specification_target_fit(self, value):
        self.calls.append(value)
        return self.action(value)


def test_production_authored_roots_and_original_lowering():
    from aware_sdk_contract_runtime_source import materialize_sdk_source_contract

    home = HOME / "aware"
    sources = {p.name: p.read_text() for p in sorted(home.glob("*.aware"))}
    operation = sdk.PROTOCOL_SPECIFICATION_TARGET_FIT_OPERATION_REF
    contract = materialize_sdk_source_contract(
        sdk_toml_text=(home / "aware.sdk.toml").read_text(),
        source_text_by_path=sources,
        selected_operation_refs=(operation,),
    )
    assert (
        contract.manifest.operations[0].provider_operation_ref
        == sdk.PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_OPERATION_REF
    )
    body = sources["specification_target_fit.aware"]
    for name in (
        "ProtocolSpecificationTargetFitRequest",
        "ProtocolSpecificationTargetFitResult",
        "ProtocolSpecificationTargetFitErrorEvidence",
    ):
        declaration = body.split("class " + name + " : inline_value {", 1)[1].split(
            "}", 1
        )[0]
        assert tuple(f.name for f in fields(getattr(sdk, name))) == tuple(
            line.strip().split()[0] for line in declaration.splitlines() if line.strip()
        )
    assert "EvidenceGrade = local_not_observed" in body


@pytest.mark.parametrize(
    "value",
    [
        request(),
        result(),
        sdk.ProtocolSpecificationTargetFitErrorEvidence(
            "local", "not dispatched", request()
        ),
    ],
)
def test_strict_roots_roundtrip_detaches(value):
    payload = value.to_wire()
    copy = sdk.protocol_specification_target_fit_value_from_payload(
        type(value), payload
    )
    assert copy == value and copy is not value
    body = sdk.protocol_specification_target_fit_value_to_json(value)
    assert (
        sdk.protocol_specification_target_fit_value_from_json(type(value), body)
        == value
    )
    assert body == json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("repository_root", " /root"),
        ("protocol_manifest_locator", "\x00bad"),
        ("expected_manifest_sha256", "0" * 64),
        ("contract", "foreign"),
        ("supplied_spec_manifest_locator", "x" * 1025),
        ("repository_root", "\ud800"),
        ("protocol_manifest_locator", False),
    ],
)
def test_request_shapes_refuse(field, value):
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        replace(request(), **{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("provider_ref", "foreign"),
        ("source_sha256", "sha256:" + "1" * 64),
        ("matched_spec_key", None),
        ("cleanup", sdk.ProtocolSpecificationTargetFitCleanup.UNKNOWN),
        ("effect", sdk.ProtocolSpecificationTargetFitEffect.UNKNOWN),
        ("authorizes_retry", 0),
        ("authorizes_retry", True),
        ("diagnostics", ["not tuple"]),
        ("observation_grade", "every_write"),
        ("scope", "authority"),
    ],
)
def test_invalid_result_shapes_refuse(field, value):
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        replace(result(), **{field: value})


@pytest.mark.parametrize(
    "updates",
    [
        {
            "evidence_grade": sdk.ProtocolSpecificationTargetFitEvidenceGrade.PROVIDER_OBSERVATION
        },
        {
            "evidence_grade": sdk.ProtocolSpecificationTargetFitEvidenceGrade.UNVALIDATED_PROVIDER_REPORT
        },
        {"provider_invoked": True},
        {"cleanup": sdk.ProtocolSpecificationTargetFitCleanup.CLOSED},
        {"effect": sdk.ProtocolSpecificationTargetFitEffect.UNKNOWN},
        {"observed_source_sha256": "sha256:" + "0" * 64},
        {"configured_root": "docs/specs"},
        {"path_template": "<spec-key>/aware.spec.toml"},
        {"expected_shape": "docs/specs/<spec-key>/aware.spec.toml"},
        {"observed_fit": sdk.ProtocolSpecificationTargetFitOutcome.MATCH},
        {"reported_result": {"fit": "match"}},
        {"report_diagnostics": ("omitted",)},
    ],
)
def test_local_error_cannot_claim_provider_observations(updates):
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        sdk.ProtocolSpecificationTargetFitErrorEvidence(
            "local", "not dispatched", **updates
        )


def test_unvalidated_report_is_immutable_and_detached():
    reported = {"value": [1, 2]}
    value = sdk.ProtocolSpecificationTargetFitErrorEvidence(
        "unverified",
        "foreign report",
        request(),
        provider_invoked=True,
        cleanup=sdk.ProtocolSpecificationTargetFitCleanup.UNKNOWN,
        effect=sdk.ProtocolSpecificationTargetFitEffect.UNKNOWN,
        reported_result=reported,
        evidence_grade=sdk.ProtocolSpecificationTargetFitEvidenceGrade.UNVALIDATED_PROVIDER_REPORT,
    )
    reported["value"].append(3)
    assert value.to_wire()["reported_result"] == {"value": [1, 2]}
    wire = value.to_wire()
    wire["reported_result"]["value"].append(4)
    assert value.to_wire()["reported_result"] == {"value": [1, 2]}


@pytest.mark.parametrize("change", ["unknown", "missing", "bool", "enum", "nested"])
def test_payloads_refuse_unknown_missing_and_wrong_types(change):
    payload = result().to_wire()
    if change == "unknown":
        payload["extra"] = "unexpected"
    elif change == "missing":
        payload.pop("reason")
    elif change == "bool":
        payload["authorizes_retry"] = 0
    elif change == "enum":
        payload["fit"] = "unavailable"
    else:
        payload["request"]["extra"] = True
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        sdk.protocol_specification_target_fit_value_from_payload(
            type(result()), payload
        )


@pytest.mark.parametrize(
    "body", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', "x" * 131073, "[]"]
)
def test_bad_json_refuses(body):
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        sdk.protocol_specification_target_fit_value_from_json(type(request()), body)


def _invalid_utf8_entry(case):
    if case == "json_body":
        return sdk.protocol_specification_target_fit_value_from_json(
            type(request()), '"\ud800"'
        )
    report = {"value": "\ud800"} if case == "report_value" else {"\ud800": "value"}
    return sdk.ProtocolSpecificationTargetFitErrorEvidence(
        "foreign",
        "unvalidated",
        request(),
        provider_invoked=True,
        cleanup=sdk.ProtocolSpecificationTargetFitCleanup.UNKNOWN,
        effect=sdk.ProtocolSpecificationTargetFitEffect.UNKNOWN,
        reported_result=report,
        evidence_grade=sdk.ProtocolSpecificationTargetFitEvidenceGrade.UNVALIDATED_PROVIDER_REPORT,
    )


@pytest.mark.parametrize("case", ["json_body", "report_value", "report_key"])
def test_invalid_utf8_direct_entries_preserve_typed_error_and_cause(case):
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError) as caught:
        _invalid_utf8_entry(case)
    assert type(caught.value.__cause__) is UnicodeEncodeError
    assert caught.value.__cause__.object == (
        '"\ud800"' if case == "json_body" else "\ud800"
    )


@pytest.mark.parametrize("case", ["json_body", "report_value", "report_key"])
def test_original_unguarded_encoding_reproduces_raw_escape(case, monkeypatch):
    monkeypatch.setattr(sdk, "_utf8", lambda value: value.encode("utf-8", "strict"))
    with pytest.raises(UnicodeEncodeError):
        _invalid_utf8_entry(case)


def test_original_request_and_return_are_detached():
    original = request()
    returned = result(original)
    provider = Provider(lambda _: returned)
    value = sdk.ProtocolSpecificationTargetFitClient(provider).observe(original)
    assert value == returned and value is not returned
    assert provider.calls[0] is not original
    assert value.request is not original


@pytest.mark.parametrize("exception", [ValueError, KeyboardInterrupt])
def test_second_snapshot_failure_never_dispatches(monkeypatch, exception):
    detached = sdk._detached
    count = 0

    def interrupted(value):
        nonlocal count
        count += 1
        if count == 2:
            raise exception("snapshot interrupted")
        return detached(value)

    monkeypatch.setattr(sdk, "_detached", interrupted)
    provider = Provider()
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        sdk.ProtocolSpecificationTargetFitClient(provider).observe(request())
    error = caught.value.evidence
    assert provider.calls == [] and error.request == request()
    assert not error.provider_invoked
    assert error.cleanup.value == "not_acquired" and error.effect.value == "none"
    assert error.evidence_grade.value == "local_not_observed"


@pytest.mark.parametrize("reported", [None, {"fit": "match"}, {"foreign": "x" * 20000}])
def test_malformed_returns_preserve_unvalidated_evidence(reported):
    provider = Provider(lambda _: reported)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        sdk.ProtocolSpecificationTargetFitClient(provider).observe(request())
    wire = caught.value.to_wire()
    assert wire["provider_invoked"]
    assert wire["cleanup"] == wire["effect"] == "unknown"
    assert wire["evidence_grade"] == "unvalidated_provider_report"
    assert wire["request"] == request().to_wire()
    assert not wire["authorizes_retry"] and len(provider.calls) == 1
    if type(reported) is dict and "fit" in reported:
        assert wire["reported_result"] == reported


def test_hostile_report_hooks_never_execute():
    class Hostile:
        def to_wire(self):
            pytest.fail("untrusted serializer executed")

        def __repr__(self):
            pytest.fail("untrusted repr executed")

    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        sdk.ProtocolSpecificationTargetFitClient(Provider(lambda _: Hostile())).observe(
            request()
        )
    assert caught.value.evidence.report_diagnostics == (
        "target_fit_unvalidated_report_omitted",
    )


def test_foreign_request_refuses_without_retry():
    provider = Provider(
        lambda value: result(
            replace(
                value,
                supplied_spec_manifest_locator="docs/specs/foreign/aware.spec.toml",
            )
        )
    )
    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        sdk.ProtocolSpecificationTargetFitClient(provider).observe(request())
    assert caught.value.evidence.request == request()
    assert len(provider.calls) == 1


def test_genuine_error_preserves_owner_evidence():
    evidence = sdk.ProtocolSpecificationTargetFitErrorEvidence(
        "owner_refusal",
        "owner explanation",
        request(),
        provider_invoked=True,
        cleanup=sdk.ProtocolSpecificationTargetFitCleanup.CLOSED,
        observed_source_sha256=request().expected_manifest_sha256,
        evidence_grade=sdk.ProtocolSpecificationTargetFitEvidenceGrade.PROVIDER_OBSERVATION,
    )

    def refuse(_):
        raise sdk.ProtocolSpecificationTargetFitError(evidence)

    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        sdk.ProtocolSpecificationTargetFitClient(Provider(refuse)).observe(request())
    assert caught.value.evidence == evidence
    assert caught.value.evidence is not evidence


def test_forged_error_without_carrier_is_typed_refusal():
    def refuse(_):
        raise RuntimeError.__new__(sdk.ProtocolSpecificationTargetFitError)

    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        sdk.ProtocolSpecificationTargetFitClient(Provider(refuse)).observe(request())
    assert caught.value.code == "target_fit_provider_return_unverified"
    assert caught.value.provider_invoked and caught.value.cleanup.value == "unknown"


@pytest.mark.parametrize(
    "field,valid,invalid",
    [
        ("repository_root", "x" * 4096, "x" * 4097),
        ("protocol_manifest_locator", "é" * 2048, "é" * 2049),
        ("supplied_spec_manifest_locator", "x" * 1024, "x" * 1025),
    ],
)
def test_exact_utf8_request_boundaries(field, valid, invalid):
    replace(request(), **{field: valid})
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        replace(request(), **{field: invalid})


@pytest.mark.parametrize(
    "report",
    [
        {"large": "x" * 16384},
        [0] * 513,
        [[[[[[[[[1]]]]]]]]],
        {"not_finite": float("inf")},
    ],
)
def test_report_encoded_node_and_depth_limits(report):
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        sdk.ProtocolSpecificationTargetFitErrorEvidence(
            "foreign",
            "unvalidated",
            request(),
            provider_invoked=True,
            cleanup=sdk.ProtocolSpecificationTargetFitCleanup.UNKNOWN,
            effect=sdk.ProtocolSpecificationTargetFitEffect.UNKNOWN,
            reported_result=report,
            evidence_grade=sdk.ProtocolSpecificationTargetFitEvidenceGrade.UNVALIDATED_PROVIDER_REPORT,
        )


def test_diagnostic_count_and_mismatch_rules():
    replace(result(), diagnostics=("diagnostic",) * 16)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        replace(result(), diagnostics=("diagnostic",) * 17)
    with pytest.raises(sdk.ProtocolSpecificationTargetFitValueError):
        replace(
            result(),
            fit=sdk.ProtocolSpecificationTargetFitOutcome.MISMATCH,
            matched_spec_key=None,
        )
    value = replace(
        result(),
        fit=sdk.ProtocolSpecificationTargetFitOutcome.MISMATCH,
        matched_spec_key=None,
        diagnostics=("outside binding",),
    )
    assert (
        sdk.protocol_specification_target_fit_value_from_json(
            type(value), sdk.protocol_specification_target_fit_value_to_json(value)
        )
        == value
    )


def test_mutated_caller_request_preserves_original_correlation():
    value = request()
    original_wire = value.to_wire()

    def mutate(dispatch):
        object.__setattr__(
            value, "supplied_spec_manifest_locator", "docs/specs/other/aware.spec.toml"
        )
        return result(dispatch)

    with pytest.raises(sdk.ProtocolSpecificationTargetFitError) as caught:
        sdk.ProtocolSpecificationTargetFitClient(Provider(mutate)).observe(value)
    assert caught.value.to_wire()["request"] == original_wire
    assert caught.value.cleanup.value == "unknown"


def test_neutral_sdk_does_not_import_fs_or_service():
    import subprocess
    import sys

    script = """
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith(("aware_protocol_fs_adapter", "aware_issue", "aware_specification", "aware_service")):
        raise AssertionError("neutral SDK imported " + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from aware_protocol_sdk import ProtocolSpecificationTargetFitClient
assert ProtocolSpecificationTargetFitClient
"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
