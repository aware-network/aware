"""Real authored closure/value parity; decoded data grants no owner authority."""

import hashlib
import importlib.util
import json
from dataclasses import fields, replace
from pathlib import Path

import pytest
from aware_meta_type_schema import TypeSchemaBundle, validate_typed_value
from aware_sdk_contract_runtime_provider import (
    SdkDefinitionRequest,
    lower_parsed_sdk_definition,
)
from aware_sdk_contract_runtime_source import materialize_sdk_source_contract
from aware_specification_runtime import (
    SpecificationIterationIdentity,
    SpecificationIterationPlan,
    SpecificationPhaseDependency,
    SpecificationSnapshot,
)
from aware_specification_runtime.values import canonical_json_bytes
from aware_specification_sdk import (
    SPECIFICATION_SDK_VALUE_CONTRACT,
    SpecificationObserveRequest,
    SpecificationOperationError,
    decode_specification_value,
    encode_specification_value,
    wire,
)
from tree_sitter_aware.parsed_document import (
    AwarePortableParseInput,
    parse_aware_document_batch,
)

SOURCE = Path(__file__).resolve().parents[3] / "aware"
OPERATIONS = ("specification_sdk.create_draft", "specification_sdk.observe")


def fixture_module(name, path=None):
    spec = importlib.util.spec_from_file_location(
        "authored_closure_" + name,
        Path(__file__).with_name(name + ".py") if path is None else path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


draft = fixture_module("test_draft_evidence")
cleanup = fixture_module("test_draft_cleanup")
custody = fixture_module("test_draft_input_custody")


def samples():
    request = draft.request()
    result = draft.result(request)
    definition = request.definition
    evidence = draft.evidence(
        package_outcome="published",
        effects=(draft.effect(),),
    )
    identity = SpecificationIterationIdentity(
        "specification:example/phase:p",
        SpecificationIterationPlan("work", "Work", "Objective"),
    )
    c = cleanup.value()
    k = custody.sample()
    values = (
        definition,
        definition.invariants[0],
        identity,
        identity.plan,
        definition.phases[0],
        SpecificationPhaseDependency(
            "upstream",
            "specification:other/phase:first",
            draft.SHA,
        ),
        definition.phases[0].gate,
        result.observation.snapshot,
        SpecificationObserveRequest(),
        result.observation,
        request,
        replace(result, evidence=evidence),
        evidence.members[0],
        draft.effect(before_identity=(7, 11), after_identity=(9, 13)),
        evidence,
        c.issue_disposition.request,
        c.physical_observation.evidence,
        c.issue_disposition,
        c.physical_observation,
        c.physical_invocation,
        k.input_custody.physical,
        k.input_custody,
        c,
        SpecificationOperationError(
            "primary_refusal",
            effect="unknown",
            evidence=evidence,
            evidence_diagnostics=("original_failure",),
            cleanup_evidence=k,
        ),
    )
    assert {type(value) for value in values} == set(wire._CARRIERS)
    return values


def source_contract(sources=None, operations=OPERATIONS):
    return materialize_sdk_source_contract(
        sdk_toml_text=(SOURCE / "aware.sdk.toml").read_text(),
        source_text_by_path=sources
        if sources is not None
        else {p.name: p.read_text() for p in sorted(SOURCE.glob("*.aware"))},
        selected_operation_refs=operations,
    )


@pytest.fixture(scope="module")
def materialized():
    return source_contract()


@pytest.fixture(scope="module")
def bundle(materialized):
    definitions = {
        definition.type_ref: definition
        for schema in materialized.manifest.schema_slices
        for definition in schema.types
    }
    return TypeSchemaBundle.create(
        namespace="aware_specification_sdk",
        semantic_version="1",
        types=definitions.values(),
    )


def test_source_oracle_and_original_parsed_provider_agree(materialized, bundle):
    sources = {p.name: p.read_text() for p in sorted(SOURCE.glob("*.aware"))}
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
    batch = parse_aware_document_batch(inputs).batch
    request = SdkDefinitionRequest.create(
        sdk_ref="specification_sdk",
        semantic_version="1",
        targets=materialized.manifest.targets,
        selected_operation_refs=OPERATIONS,
    )
    assert (
        lower_parsed_sdk_definition(
            request,
            batch,
            materialized.manifest.schema_slices,
        )
        == materialized.definition_state
    )
    assert materialized.manifest.sdk_ref == "specification_sdk"
    assert (
        tuple(o.operation_ref for o in materialized.manifest.operations) == OPERATIONS
    )
    assert tuple(
        o.provider_operation_ref for o in materialized.manifest.operations
    ) == (
        "specification.draft.create",
        "specification.source.observe",
    )
    assert len(materialized.manifest.schema_slices) == 5
    assert len(bundle.types) == 28
    assert len(materialized.inventory.operation_refs) == 2
    assert materialized.authority_grade == "portable_input"
    assert (
        source_contract(
            dict(reversed(tuple(sources.items()))),
            tuple(reversed(OPERATIONS)),
        )
        == materialized
    )


@pytest.mark.parametrize("value", samples(), ids=lambda v: type(v).__name__)
def test_every_carrier_has_exact_fields_schema_parity_and_lossless_codec(bundle, value):
    body = encode_specification_value(value)
    payload = json.loads(body)
    assert payload["contract"] == SPECIFICATION_SDK_VALUE_CONTRACT
    definition = next(t for t in bundle.types if t.type_ref == payload["type_ref"])
    names = (
        set(wire._ERROR_HINTS)
        if isinstance(value, SpecificationOperationError)
        else {f.name for f in fields(value)}
    )
    assert names == {f.name for f in definition.fields} == set(payload["value"])
    report = validate_typed_value(bundle, payload["type_ref"], payload["value"])
    assert report.is_valid, report.diagnostics
    restored = decode_specification_value(body)
    assert type(restored) is type(value) and restored is not value
    assert encode_specification_value(restored) == body
    if not isinstance(value, SpecificationOperationError):
        assert restored == value
    else:
        assert restored.effect == "unknown"
        assert restored.evidence.package_outcome == "published"
        assert restored.cleanup_evidence.protocol_owner_outcome == "unknown"


def test_exact_nontext_member_bytes_order_and_unknowns_survive():
    original = replace(
        cleanup.request(),
        ordered_members=(("a", b"\x00\xff\n"), ("b", b"")),
    )
    payload = json.loads(encode_specification_value(original))
    assert payload["value"]["ordered_members"] == [
        {"relative_path": "a", "content": {"encoding": "hex", "body": "00ff0a"}},
        {"relative_path": "b", "content": {"encoding": "hex", "body": ""}},
    ]
    assert decode_specification_value(canonical_json_bytes(payload)) == original
    c = decode_specification_value(encode_specification_value(cleanup.value()))
    assert c.issue_disposition.physical_cleanup_attempted is None
    assert c.physical_observation.attempted is False
    assert c.physical_observation.evidence.ledger_complete is None


def test_existing_read_iteration_identity_is_preserved_without_new_writer(bundle):
    result = draft.result(draft.request())
    definition = result.observation.snapshot.definitions[0]
    identity = samples()[2]
    definition = replace(
        definition,
        phases=(replace(definition.phases[0], iterations=(identity.plan,)),),
    )
    observation = replace(
        result.observation,
        snapshot=SpecificationSnapshot((definition,)),
        iterations=(identity,),
    )
    body = encode_specification_value(observation)
    assert decode_specification_value(body) == observation
    payload = json.loads(body)
    assert validate_typed_value(bundle, payload["type_ref"], payload["value"]).is_valid
    with pytest.raises(
        SpecificationOperationError, match="iteration_approval_writer_unavailable"
    ):
        replace(draft.request(), definition=definition)


@pytest.mark.parametrize(
    "operations",
    [
        ("specification_sdk.unknown",),
        ("specification_sdk.observe", "specification_sdk.unknown"),
    ],
)
def test_no_new_operation_identity_is_invented(operations):
    with pytest.raises(ValueError):
        source_contract(operations=operations)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p.update(contract="unknown"),
        lambda p: p.update(type_ref="aware_issue_sdk.SpecificationObserveRequest"),
        lambda p: p["value"].update(extra=True),
        lambda p: p["value"].pop("expected_source_digest"),
        lambda p: p["value"].update(expected_source_digest=13),
    ],
)
def test_envelope_or_structural_forgery_refuses(mutation):
    payload = json.loads(encode_specification_value(SpecificationObserveRequest()))
    mutation(payload)
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        decode_specification_value(canonical_json_bytes(payload))


@pytest.mark.parametrize("bad", ["AA", "aa ", "zz", None, 0])
def test_member_encoding_must_be_exact_canonical_hex(bad):
    payload = json.loads(encode_specification_value(cleanup.request()))
    payload["value"]["ordered_members"][0]["content"]["body"] = bad
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        decode_specification_value(canonical_json_bytes(payload))


@pytest.mark.parametrize(
    "name", ["snapshot_digest", "gate_digest", "plan_digest", "iteration_ref"]
)
def test_derived_fields_cannot_be_forged(name):
    value = {
        "snapshot_digest": draft.result(draft.request()).observation.snapshot,
        "gate_digest": draft.request().definition.phases[0].gate,
        "plan_digest": samples()[2],
        "iteration_ref": samples()[2],
    }[name]
    payload = json.loads(encode_specification_value(value))
    payload["value"][name] = "sha256:" + "f" * 64
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        decode_specification_value(canonical_json_bytes(payload))


@pytest.mark.parametrize("bad", [True, -1, "1", None])
def test_file_identity_is_typed_and_validated(bad):
    payload = json.loads(
        encode_specification_value(draft.effect(after_identity=(7, 9)))
    )
    payload["value"]["after_identity"]["device"] = bad
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        decode_specification_value(canonical_json_bytes(payload))


@pytest.mark.parametrize("body", [b"{}", b"null", b"[]", b"{", b"\xff", "{}", None])
def test_malformed_bytes_have_typed_refusal(body):
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        decode_specification_value(body)


def test_noncanonical_json_and_duplicate_keys_refuse():
    body = encode_specification_value(SpecificationObserveRequest())
    for changed in (
        b" " + body,
        body.replace(b'"contract":', b'"contract":"wrong","contract":', 1),
    ):
        with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
            decode_specification_value(changed)


def test_deep_json_and_incomplete_carriers_have_typed_refusals():
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        decode_specification_value(b"[" * 2000 + b"0" + b"]" * 2000)
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        encode_specification_value(object.__new__(type(draft.result(draft.request()))))


@pytest.mark.parametrize("value", [object(), {"authority": "caller"}, draft.Reader()])
def test_live_objects_are_not_supported_values(value):
    with pytest.raises(SpecificationOperationError, match="invalid_sdk_wire_value"):
        encode_specification_value(value)


@pytest.mark.parametrize(
    "missing",
    [
        "specification_values.aware",
        "specification_evidence.aware",
        "specification_cleanup.aware",
    ],
)
def test_incomplete_authored_closure_refuses(missing):
    sources = {p.name: p.read_text() for p in SOURCE.glob("*.aware")}
    del sources[missing]
    with pytest.raises(ValueError):
        source_contract(sources)


def test_codec_does_not_change_cli_pair_presentation():
    from aware_specification_cli.draft_commands import _wire

    request = cleanup.request()
    cli_payload = json.loads(json.dumps(request, default=_wire))
    assert cli_payload["ordered_members"][0] == [
        "a",
        {"encoding": "hex", "body": b"exact bytes".hex()},
    ]
    event = draft.effect(after_identity=(7, 9))
    assert _wire(event)["after_identity"] == (7, 9)
    assert json.loads(encode_specification_value(event))["value"]["after_identity"] == {
        "device": 7,
        "inode": 9,
    }


@pytest.mark.parametrize("mode", ["preview", "publish", "refuse"])
def test_genuine_owner_snapshots_roundtrip_after_release_without_authority(
    tmp_path,
    monkeypatch,
    bundle,
    mode,
):
    from aware_specification_fs_sdk_adapter import open_governed_specification_draft

    owners = fixture_module(
        "owner_fixture",
        Path(__file__).parents[2] / "fs_adapter/tests/test_draft_input_custody.py",
    )
    fixture = owners.inputs.__wrapped__(tmp_path, monkeypatch)
    root, _, issue, kwargs = next(fixture)
    original_issue = issue.read_bytes()
    guard = owners.custody(kwargs)
    if mode == "refuse":
        kwargs = {**kwargs, "expected_issue_sha256": "sha256:" + "0" * 64}
    manager = open_governed_specification_draft(**kwargs, input_custody=guard)
    if mode == "refuse":
        with pytest.raises(SpecificationOperationError) as caught:
            manager.__enter__()
        failure = decode_specification_value(encode_specification_value(caught.value))
        assert failure.code == caught.value.code
        assert failure.effect == caught.value.effect
        assert failure.cleanup_evidence == caught.value.cleanup_evidence
    else:
        with manager as client:
            if mode == "publish":
                result = client.create_draft(kwargs["request"])
                body = encode_specification_value(result)
                restored = decode_specification_value(body)
                assert restored == result
                assert restored.evidence.package_outcome == "published"
                payload = json.loads(body)
                assert validate_typed_value(
                    bundle,
                    payload["type_ref"],
                    payload["value"],
                ).is_valid
    final = manager.observe_draft_cleanup()
    restored = decode_specification_value(encode_specification_value(final))
    assert restored == final
    assert restored.input_custody.physical.owner_cleanup_outcome == "completed"
    assert restored.protocol_owner_outcome == "completed"
    assert not hasattr(restored, "dispose")
    assert not hasattr(restored, "__enter__")
    assert owners.repository_descriptors(root) == []
    assert issue.read_bytes() == original_issue
    assert (root / "customer/specs/widget").exists() is (mode == "publish")
    assert (root / "unrelated.txt").read_text() == "untouched dirty work\n"
    with pytest.raises(StopIteration):
        next(fixture)
