"""Genuine typed boundary/parity proofs; synthetic providers grant no authority."""

from dataclasses import replace
from pathlib import Path

import pytest
from aware_meta_type_schema import TypeSchemaBundle, validate_typed_value
from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAdmissionResult,
    ProtocolAuthorityMode,
    ProtocolBootstrap,
    ProtocolIdentity,
    ProtocolManifest,
    ProtocolRecordBinding,
    ProtocolRecordRole,
    ProtocolTarget,
    ProtocolTargetKind,
)
from aware_protocol_sdk import (
    ProtocolSdkClient,
    ProtocolTargetAdmissionError,
    ProtocolTargetAdmissionRequest,
    ProtocolTargetAdmissionResult,
)
from aware_sdk_contract_runtime_source import materialize_sdk_source_contract


def request():
    return ProtocolTargetAdmissionRequest(
        authority_mode=ProtocolAuthorityMode.FILESYSTEM,
        target_ref="/customer",
        source_ref="aware.protocol.toml",
    )


def result(req=None, canonical=False):
    manifest = (
        ProtocolManifest(
            protocol=ProtocolIdentity(
                "aware.collaboration", "aware.collaboration.fs_v1", 1
            ),
            target=ProtocolTarget(
                ProtocolTargetKind.REPOSITORY, ProtocolAuthorityMode.FILESYSTEM
            ),
            bootstrap=ProtocolBootstrap("AGENTS.md"),
            records=(
                ProtocolRecordBinding(
                    "issue", "aware.issue.markdown.v1", ProtocolRecordRole.AUTHORITY
                ),
            ),
        )
        if canonical
        else None
    )
    return ProtocolTargetAdmissionResult(
        request=request() if req is None else req,
        provider_ref="test.provider",
        provider_distribution="test-provider",
        provider_version="1",
        admission=ProtocolAdmissionResult(
            outcome=ProtocolAdmissionOutcomeKind.CANONICAL_V1
            if canonical
            else ProtocolAdmissionOutcomeKind.SOURCE_UNAVAILABLE,
            source_sha256="sha256:" + "a" * 64 if canonical else None,
            manifest=manifest,
            diagnostics=() if canonical else ("source_missing",),
        ),
        evidence=("observed:test",),
    )


class Provider:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def admit_target(self, received):
        self.calls += 1
        self.received = received
        return self.response


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_ref", "/another"),
        ("source_ref", "nested/aware.protocol.toml"),
        ("authority_mode", ProtocolAuthorityMode.SERVICE_API),
    ],
)
def test_different_request_refuses_once_and_preserves_report(field, value):
    reported = result(replace(request(), **{field: value}))
    provider = Provider(reported)
    with pytest.raises(ProtocolTargetAdmissionError) as refusal:
        ProtocolSdkClient(provider).admit_target(request())
    wire = refusal.value.to_wire()
    assert provider.calls == 1
    assert wire["code"] == "admission_provider_result_invalid"
    assert wire["effect"] == "unknown"
    assert wire["provider_invoked"] is True
    assert wire["authorizes_retry"] is False
    assert wire["evidence_grade"] == "unvalidated_provider_report"
    assert wire["reported_result"]["request"][field] == str(value)
    assert wire["reported_result"]["evidence"] == ["observed:test"]
    assert wire["reported_result"]["admission"]["diagnostics"] == ["source_missing"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("operation_ref", "protocol_sdk.setup_specification"),
        ("provider_ref", ""),
        ("provider_distribution", 1),
        ("provider_version", None),
        ("request", {}),
        ("admission", {}),
        ("evidence", [None]),
    ],
)
def test_bypass_mutated_result_refuses_with_report(field, value):
    reported = result()
    object.__setattr__(reported, field, value)
    provider = Provider(reported)
    with pytest.raises(ProtocolTargetAdmissionError) as refusal:
        ProtocolSdkClient(provider).admit_target(request())
    assert provider.calls == 1
    assert refusal.value.to_wire()["reported_result"] is not None


@pytest.mark.parametrize(
    "field,value",
    [
        ("outcome", "canonical_v1"),
        ("source_sha256", "bare"),
        ("diagnostics", [None]),
        ("manifest", {}),
    ],
)
def test_nested_admission_is_revalidated(field, value):
    reported = result()
    object.__setattr__(reported.admission, field, value)
    with pytest.raises(ProtocolTargetAdmissionError):
        ProtocolSdkClient(Provider(reported)).admit_target(request())


@pytest.mark.parametrize(
    "part,field,value",
    [
        ("protocol", "semantic_version", True),
        ("bootstrap", "agent_contract_ref", ""),
        ("target", "authority_mode", "filesystem"),
        ("records", "role", "authority"),
    ],
)
def test_manifest_children_are_revalidated(part, field, value):
    reported = result(canonical=True)
    child = getattr(reported.admission.manifest, part)
    object.__setattr__(child[0] if part == "records" else child, field, value)
    with pytest.raises(ProtocolTargetAdmissionError):
        ProtocolSdkClient(Provider(reported)).admit_target(request())


def test_valid_but_foreign_manifest_authority_refuses():
    reported = result(canonical=True)
    manifest = replace(
        reported.admission.manifest,
        target=ProtocolTarget(
            ProtocolTargetKind.REPOSITORY,
            ProtocolAuthorityMode.SERVICE_API,
            "service:other",
        ),
    )
    reported = replace(
        reported, admission=replace(reported.admission, manifest=manifest)
    )
    with pytest.raises(ProtocolTargetAdmissionError):
        ProtocolSdkClient(Provider(reported)).admit_target(request())


@pytest.mark.parametrize("bad", [{}, None, "request"])
def test_foreign_request_refuses_before_provider(bad):
    provider = Provider(result())
    with pytest.raises(ProtocolTargetAdmissionError) as refusal:
        ProtocolSdkClient(provider).admit_target(bad)
    assert provider.calls == 0
    assert refusal.value.effect == "none"
    assert refusal.value.to_wire()["reported_result"] is None


def test_bypass_mutated_request_refuses_before_provider():
    req = request()
    object.__setattr__(req, "source_ref", "")
    provider = Provider(result())
    with pytest.raises(ProtocolTargetAdmissionError):
        ProtocolSdkClient(provider).admit_target(req)
    assert provider.calls == 0


def test_provider_cannot_mutate_the_original_correlation_request():
    class Mutator(Provider):
        def admit_target(self, received):
            self.calls += 1
            object.__setattr__(received, "source_ref", "other")
            return result(received)

    original = request()
    provider = Mutator(None)
    with pytest.raises(ProtocolTargetAdmissionError):
        ProtocolSdkClient(provider).admit_target(original)
    assert original.source_ref == "aware.protocol.toml"
    assert provider.calls == 1


def test_result_detaches_nested_values_without_mutating_original():
    reported = result(canonical=True)
    original_records = list(reported.admission.manifest.records)
    object.__setattr__(reported.admission.manifest, "records", original_records)
    accepted = ProtocolSdkClient(Provider(reported)).admit_target(request())
    assert reported.admission.manifest.records is original_records
    object.__setattr__(reported.request, "source_ref", "other")
    object.__setattr__(reported.admission.manifest.protocol, "name", "changed")
    original_records.clear()
    assert accepted.request == request()
    assert accepted.admission.manifest.protocol.name == "aware.collaboration"
    assert len(accepted.admission.manifest.records) == 1


def test_provider_exception_is_not_retried_or_rewritten():
    failure = OSError("original")

    class Failing(Provider):
        def admit_target(self, received):
            self.calls += 1
            raise failure

    provider = Failing(None)
    with pytest.raises(OSError) as caught:
        ProtocolSdkClient(provider).admit_target(request())
    assert caught.value is failure
    assert provider.calls == 1


def test_unknown_report_does_not_execute_provider_hooks():
    class Foreign:
        def to_wire(self):
            pytest.fail("foreign serializer called")

        def __repr__(self):
            pytest.fail("foreign repr called")

        def __iter__(self):
            pytest.fail("foreign iterator called")

    with pytest.raises(ProtocolTargetAdmissionError) as refusal:
        ProtocolSdkClient(Provider(Foreign())).admit_target(request())
    assert refusal.value.to_wire()["report_diagnostics"] == [
        "reported_result:unsupported_value_omitted"
    ]


def test_report_is_detached_bounded_and_omissions_are_explicit():
    reported = {"evidence": ["x" * 5000, 1 << 20000], "unknown": "not transported"}
    with pytest.raises(ProtocolTargetAdmissionError) as refusal:
        ProtocolSdkClient(Provider(reported)).admit_target(request())
    wire = refusal.value.to_wire()
    reported["evidence"].clear()
    assert wire == refusal.value.to_wire()
    assert len(wire["reported_result"]["evidence"][0]) == 4096
    assert len(wire["report_diagnostics"]) == 3
    wire["reported_result"].clear()
    assert refusal.value.to_wire()["reported_result"]


def test_cyclic_report_has_explicit_depth_omission():
    cyclic = {}
    cyclic["evidence"] = cyclic
    with pytest.raises(ProtocolTargetAdmissionError) as refusal:
        ProtocolSdkClient(Provider(cyclic)).admit_target(request())
    assert any(
        "capacity_omitted" in value for value in refusal.value.report_diagnostics
    )


@pytest.mark.parametrize("field", ["evidence", "diagnostics", "records"])
def test_malformed_iterables_are_not_executed(field):
    class ForeignIterator:
        def __iter__(self):
            pytest.fail("malformed provider iterator executed")

    reported = result(canonical=True)
    owner = (
        reported
        if field == "evidence"
        else reported.admission
        if field == "diagnostics"
        else reported.admission.manifest
    )
    object.__setattr__(owner, field, ForeignIterator())
    with pytest.raises(ProtocolTargetAdmissionError) as refusal:
        ProtocolSdkClient(Provider(reported)).admit_target(request())
    assert any(
        "unsupported_value_omitted" in value
        for value in refusal.value.report_diagnostics
    )


@pytest.fixture(scope="module")
def schema_bundle():
    source = Path(__file__).resolve().parents[2] / "aware"
    materialized = materialize_sdk_source_contract(
        sdk_toml_text=(source / "aware.sdk.toml").read_text(),
        source_text_by_path={
            path.name: path.read_text() for path in source.glob("*.aware")
        },
        selected_operation_refs=("protocol_sdk.admit_target",),
    )
    definitions = {
        definition.type_ref: definition
        for schema in materialized.manifest.schema_slices
        for definition in schema.types
    }
    return TypeSchemaBundle.create(
        namespace="aware_protocol_sdk",
        semantic_version="2",
        types=tuple(definitions.values()),
    )


@pytest.mark.parametrize(
    "name,payload",
    [
        ("ProtocolTargetAdmissionRequest", request().to_wire()),
        ("ProtocolTargetAdmissionResult", result().to_wire()),
        ("ProtocolTargetAdmissionResult", result(canonical=True).to_wire()),
        (
            "ProtocolTargetAdmissionError",
            ProtocolTargetAdmissionError("invalid", "Invalid request").to_wire(),
        ),
        (
            "ProtocolTargetAdmissionError",
            ProtocolTargetAdmissionError(
                "invalid",
                "Invalid response",
                provider_invoked=True,
                reported_result=result(),
            ).to_wire(),
        ),
    ],
)
def test_authored_and_python_carriers_have_exact_wire_parity(
    schema_bundle, name, payload
):
    type_ref = "aware_protocol_sdk." + name
    definition = next(item for item in schema_bundle.types if item.type_ref == type_ref)
    assert {field.name for field in definition.fields} == set(payload)
    assert validate_typed_value(schema_bundle, type_ref, payload).is_valid
    assert not validate_typed_value(
        schema_bundle, type_ref, {**payload, "extra": 1}
    ).is_valid


def test_authored_result_requires_typed_correlated_request(schema_bundle):
    payload = result().to_wire()
    type_ref = "aware_protocol_sdk.ProtocolTargetAdmissionResult"
    assert not validate_typed_value(
        schema_bundle, type_ref, {**payload, "request": None}
    ).is_valid
    assert not validate_typed_value(
        schema_bundle, type_ref, {**payload, "request": {"target_ref": "/customer"}}
    ).is_valid
