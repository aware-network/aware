"""Logical portable correspondence, codec poison and existing context execution."""

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime import semantic_input_producer as inputs
from aware_code_semantic_contract_runtime import source_origin as origins
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF,
)
from aware_code_semantic_contract_runtime.source_selection import (
    SemanticSelectedSource,
    SemanticSourceSelection,
    source_selection_body,
)
from test_contextual_semantic_input_producer import OriginalSource
from test_semantic_input_producer import _DECLARATION, _body, _expectation


def digest(value):
    return ContentDigest.of_bytes(value.encode())


RAW = SemanticContractRef("fixture.raw.v1", "1", digest("raw"))


def source(path, *, body=b"same bytes", role="source", contract=RAW):
    return inputs.SemanticInputSourceCoordinate(path, SemanticValueCoordinate(
        role, contract, "cas:" + ContentDigest.of_bytes(body).value,
        ContentDigest.of_bytes(body), len(body),
    ))


def occurrence():
    return origins.SemanticInputPackageOccurrence(
        "repository:fixture", "workspaces/kernel/aware.workspace.toml", "fixture",
        "ontology", "workspaces/kernel/modules/fixture/ontology", "aware.ontology.toml",
    )


def fixture(coords=None, *, package=None, production_digest=None):
    o = occurrence()
    outer = source(o.outer_manifest_path, body=b"manifest", role="outer_manifest")
    coords = coords if coords is not None else (source("structure/aware/a.aware"), source("structure/aware/b.aware"))
    p = package or SemanticPackageCoordinate("fixture:public@1", "opaque", outer.coordinate.digest)
    if p.manifest_digest != outer.coordinate.digest:
        outer = replace(outer, coordinate=replace(outer.coordinate, digest=p.manifest_digest))
    selected = SemanticSourceSelection(p, digest("epoch"), production_digest or digest("original selection input"), (), tuple(
        SemanticSelectedSource(x.coordinate.role, x.coordinate.contract, x.relative_path, x.coordinate.digest) for x in coords
    ))
    body = source_selection_body(selected, role="selected_sources")
    origin = origins.SemanticInputSourceOrigin(
        p, selected.source_identity_digest, body.coordinate, selected.production_input_digest,
        o, "/repo/workspaces/kernel/modules/fixture/ontology", outer, tuple(
            origins.SemanticInputSourceOccurrence(x, origins.source_occurrence_ref(o, x.relative_path)) for x in coords
        ),
    )
    return origin, selected, body, coords


def test_roundtrip_and_pinned_descriptor():
    value, selection, selected_body, coords = fixture()
    encoded = origins.encode_source_origin(value)
    assert origins.decode_source_origin(encoded) == value
    assert origins.SemanticInputSourceOriginCodec().decode(encoded) == value
    origins.validate_source_origin_selection(value, selection=selection, selection_coordinate=selected_body.coordinate, source_coordinates=coords)
    assert len(origins.SOURCE_ORIGIN_DESCRIPTOR) == 1117
    assert origins.SOURCE_ORIGIN_REF.schema_digest.value == "sha256:683d20e21d23af61e7d0bce9d63c163eae7571f30c5e24e82960aabedfb63a53"
    assert origins.SOURCE_ORIGIN_CODEC_IMPLEMENTATION.closure_digest.value == "sha256:dadbb46e38740544cf349e43619b2999070f9e1d4c7e9784f4d413cd392c1fc6"


@pytest.mark.parametrize("token", ["repository:ascii", "répository:NFC", "仓库:source"])
def test_closed_wire_matches_shared_canonical_json_for_ascii_and_unicode(token):
    value = fixture()[0]
    occurrence = replace(value.occurrence, repository_binding_ref=token)
    rows = tuple(replace(row, occurrence_ref=origins.source_occurrence_ref(
        occurrence, row.source.relative_path)) for row in value.sources)
    value = replace(value, occurrence=occurrence, sources=rows)
    body = origins.encode_source_origin(value)
    assert body == canonical_json_bytes(value.to_wire())
    assert origins.decode_source_origin(body) == value


@pytest.mark.parametrize("forbidden", [chr(n) for n in (0, 9, 10, 11, 12, 13, 28, 29, 30, 31, 32, 133, 160, 8192)])
def test_text_fast_path_preserves_control_and_unicode_whitespace_refusal(forbidden):
    value = fixture()[0]
    wire = value.to_wire()
    cast(dict[str, object], wire["occurrence"])["repository_binding_ref"] = "repository:" + forbidden + "source"
    with pytest.raises(ContractViolation):
        origins.decode_source_origin(canonical_json_bytes(wire))


def test_non_normalized_text_refuses_before_constructor_normalization():
    value = fixture()[0]
    wire = value.to_wire()
    cast(dict[str, object], wire["selection_coordinate"])["value_ref"] = "selection:e\u0301"
    with pytest.raises(ContractViolation):
        origins.decode_source_origin(canonical_json_bytes(wire))


def test_logical_address_vectors_and_equal_bytes():
    a = origins.source_occurrence_ref(occurrence(), "structure/aware/a.aware")
    b = origins.source_occurrence_ref(occurrence(), "structure/aware/b.aware")
    assert a == "code-source-occurrence:sha256:e5ba89f8e347ea9edd53f7591af2ea8957a85833b99a8a67ba569fe1d590e710"
    assert b == "code-source-occurrence:sha256:05de78875669abdf8a767cc255dc8caf3e70fd5930ba147ee552144c948486d2"
    value, _, _, _ = fixture()
    assert value.sources[0].source.coordinate == value.sources[1].source.coordinate
    assert value.sources[0].occurrence_ref != value.sources[1].occurrence_ref
    # Same path address survives body/epoch changes; no lineage authority follows.
    changed = fixture((source("structure/aware/a.aware", body=b"edited"),))[0]
    assert changed.sources[0].occurrence_ref == value.sources[0].occurrence_ref
    assert replace(value, source_identity_digest=digest("new epoch")).sources == value.sources
    for key in ("repository_binding_ref", "scope_key", "module_id", "package_id", "package_root", "outer_manifest_path"):
        other = replace(occurrence(), **{key: "other"})
        assert origins.source_occurrence_ref(other, "structure/aware/a.aware") != a


@pytest.mark.parametrize("path", ["/repo//pkg", "/repo/../pkg", "/repo/./pkg", "/repo/pkg/", "relative", "\\repo", "/repo/", "/repo/" + "x" * 256, "/repo/e\u0301"])
def test_noncanonical_location_refuses(path):
    with pytest.raises(ContractViolation):
        replace(fixture()[0], outer_package_root=path)


def test_location_validation_never_resolves_or_reads_filesystem(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("portable codec accessed filesystem")
    monkeypatch.setattr(Path, "resolve", forbidden)
    monkeypatch.setattr(Path, "stat", forbidden)
    value = replace(fixture()[0], outer_package_root="/not/a/physical/root")
    assert origins.decode_source_origin(origins.encode_source_origin(value)) == value
    assert replace(value, outer_package_root="/")
    assert replace(occurrence(), package_root="").occurrence_ref


@pytest.mark.parametrize("change", ["rows_reverse", "rows_duplicate", "row_ref", "outer_path", "outer_digest", "selection_contract", "dependency_source", "mixed_role_contract", "module_path", "scope_alias", "bad_digest", "bool_size"])
def test_closed_shape_refusals(change):
    v, _, _, _ = fixture()
    with pytest.raises((ContractViolation, TypeError)):
        if change == "rows_reverse": replace(v, sources=v.sources[::-1])
        elif change == "rows_duplicate": replace(v, sources=(v.sources[0], v.sources[0]))
        elif change == "row_ref": replace(v, sources=(replace(v.sources[0], occurrence_ref="forged"),))
        elif change == "outer_path": replace(v, outer_manifest=replace(v.outer_manifest, relative_path="wrong.toml"))
        elif change == "outer_digest": replace(v, outer_manifest=replace(v.outer_manifest, coordinate=replace(v.outer_manifest.coordinate, digest=digest("wrong"))))
        elif change == "selection_contract": replace(v, selection_coordinate=replace(v.selection_coordinate, contract=RAW))
        elif change == "dependency_source": source("a.aware", contract=SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF).__post_init__(); origins.SemanticInputSourceOccurrence(source("a.aware", contract=SEMANTIC_DEPENDENCY_PRODUCT_INPUT_REF), "x")
        elif change == "mixed_role_contract":
            row = v.sources[1]
            altered = replace(row.source, coordinate=replace(row.source.coordinate, contract=SemanticContractRef("other", "1", digest("other"))))
            replace(v, sources=(v.sources[0], replace(row, source=altered)))
        elif change == "module_path": replace(occurrence(), module_id="module/path")
        elif change == "scope_alias": replace(occurrence(), scope_key="./aware.workspace.toml")
        elif change == "bad_digest":
            object.__setattr__(v.source_identity_digest, "value", "not-a-digest")
            origins.encode_source_origin(v)
        else:
            object.__setattr__(v.sources[0].source.coordinate, "size_bytes", True)
            origins.encode_source_origin(v)


@pytest.mark.parametrize("change", ["package", "epoch", "input", "coordinate", "missing", "extra", "wrong_body", "wrong_role"])
def test_complete_selection_correspondence_refuses(change):
    v, selected, body, coords = fixture()
    if change == "package": selected = replace(selected, package=replace(selected.package, package_ref="foreign"))
    elif change == "epoch": selected = replace(selected, source_identity_digest=digest("foreign"))
    elif change == "input": selected = replace(selected, production_input_digest=digest("next invocation, not selection"))
    elif change == "coordinate": body = replace(body, coordinate=replace(body.coordinate, value_ref="foreign"))
    elif change == "missing": coords = coords[:-1]
    elif change == "extra": coords += (source("z.aware"),)
    elif change == "wrong_body": coords = (replace(coords[0], coordinate=replace(coords[0].coordinate, digest=digest("foreign"))), *coords[1:])
    else: coords = (replace(coords[0], coordinate=replace(coords[0].coordinate, role="foreign")), *coords[1:])
    with pytest.raises(ContractViolation):
        origins.validate_source_origin_selection(v, selection=selected, selection_coordinate=body.coordinate, source_coordinates=coords)


@pytest.mark.parametrize("count", [0, 1, 17, 3500])
def test_combined_fresh_decode_preserves_complete_correspondence(count):
    coords = tuple(source(f"structure/aware/m{i:05d}.aware") for i in range(count))
    value, selected, body, coords = fixture(coords)
    raw = origins.encode_source_origin(value)
    origins.validate_source_origin_selection(
        value, selection=selected, selection_coordinate=body.coordinate, source_coordinates=coords,
    )
    decoded = origins.decode_source_origin_selection(
        raw, selection_body=body.canonical_body, source_coordinates=coords,
    )
    assert decoded == value and decoded is not value
    assert origins.encode_source_origin(decoded) == raw


@pytest.mark.parametrize("change", ["epoch", "input", "missing", "extra", "wrong_body", "wrong_role", "noncanonical", "bad_origin"])
def test_combined_fresh_decode_refuses_correspondence_and_body_changes(change):
    value, selected, body, coords = fixture()
    raw = origins.encode_source_origin(value)
    if change == "epoch": selected = replace(selected, source_identity_digest=digest("foreign"))
    elif change == "input": selected = replace(selected, production_input_digest=digest("foreign"))
    elif change == "missing": coords = coords[:-1]
    elif change == "extra": coords += (source("z.aware"),)
    elif change == "wrong_body": coords = (replace(coords[0], coordinate=replace(coords[0].coordinate, digest=digest("foreign"))), *coords[1:])
    elif change == "wrong_role": coords = (replace(coords[0], coordinate=replace(coords[0].coordinate, role="foreign")), *coords[1:])
    selection_raw = source_selection_body(selected, role=body.coordinate.role).canonical_body
    if change == "noncanonical": selection_raw += b"\n"
    elif change == "bad_origin": raw += b"\n"
    with pytest.raises(ContractViolation):
        origins.decode_source_origin_selection(raw, selection_body=selection_raw, source_coordinates=coords)


def test_combined_decode_has_no_retained_validation_state():
    value, _, body, coords = fixture()
    raw = origins.encode_source_origin(value)
    decoded = origins.decode_source_origin_selection(raw, selection_body=body.canonical_body, source_coordinates=coords)
    object.__setattr__(decoded.sources[0], "occurrence_ref", "restamped")
    with pytest.raises(ContractViolation):
        origins.validate_source_origin_selection(
            decoded, selection=fixture()[1], selection_coordinate=body.coordinate, source_coordinates=coords,
        )
    assert origins.decode_source_origin_selection(raw, selection_body=body.canonical_body, source_coordinates=coords) == value


def test_combined_decode_rejects_foreign_borrowed_coordinate_without_calls():
    value, _, body, _ = fixture()
    calls = []
    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign access")
        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality")
    with pytest.raises(ContractViolation):
        origins.decode_source_origin_selection(
            origins.encode_source_origin(value), selection_body=body.canonical_body,
            source_coordinates=(Foreign(), Foreign()),
        )
    assert calls == []


@pytest.mark.parametrize("change", ["extra", "missing", "nested_extra", "duplicate", "noncanonical", "wrong_contract", "nonfinite", "too_deep", "bad_utf8", "array", "bool_size"])
def test_strict_json_refusals(change):
    v = fixture()[0]
    raw = v.to_wire()
    if change == "extra": raw["extra"] = True
    elif change == "missing": raw.pop("occurrence")
    elif change == "nested_extra": raw["sources"][0]["source"]["extra"] = 1
    elif change == "wrong_contract": raw["contract"] = "foreign"
    elif change == "bool_size": raw["sources"][0]["source"]["coordinate"]["size_bytes"] = True
    body = canonical_json_bytes(raw)
    if change == "duplicate": body = body.replace(b'{"contract":', b'{"contract":"duplicate","contract":', 1)
    elif change == "noncanonical": body += b"\n"
    elif change == "nonfinite": body = body.replace(b'"size_bytes":10', b'"size_bytes":NaN')
    elif change == "too_deep": body = b"[" * 1100 + b"0" + b"]" * 1100
    elif change == "bad_utf8": body = b"\xff"
    elif change == "array": body = b"[]"
    with pytest.raises(ContractViolation): origins.decode_source_origin(body)


def test_count_byte_and_token_bounds(monkeypatch):
    v = fixture()[0]
    body = origins.encode_source_origin(v)
    monkeypatch.setattr(origins, "MAX_SOURCE_ORIGIN_BYTES", len(body))
    assert origins.encode_source_origin(v) == body
    monkeypatch.setattr(origins, "MAX_SOURCE_ORIGIN_BYTES", len(body) - 1)
    with pytest.raises(ContractViolation): origins.encode_source_origin(v)
    with pytest.raises(ContractViolation): origins.decode_source_origin(body)
    monkeypatch.setattr(origins, "MAX_SOURCE_ORIGIN_BYTES", 8_388_608)
    with pytest.raises(ContractViolation): replace(v, sources=v.sources * (MAX := 8193))
    assert MAX * 2 > 16384
    with pytest.raises(ContractViolation): replace(occurrence(), repository_binding_ref="x" * 513)
    with pytest.raises(ContractViolation): replace(occurrence(), module_id="x" * 256)


def test_hostile_rows_and_nested_values_execute_no_foreign_behavior():
    calls = []
    class Hostile:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign access")
        def __eq__(self, other):
            calls.append("eq")
            raise AssertionError("foreign equality")
    v = fixture()[0]
    with pytest.raises(ContractViolation): replace(v, sources=(Hostile(),))
    with pytest.raises(ContractViolation): replace(v, occurrence=Hostile())
    with pytest.raises(ContractViolation): replace(v, outer_package_root=Hostile())
    object.__setattr__(v.selection_coordinate, "contract", Hostile())
    with pytest.raises(ContractViolation): origins.encode_source_origin(v)
    assert calls == []


@pytest.mark.asyncio
async def test_existing_registered_context_rail_binds_origin_and_refuses_currentness_loss():
    source_handle, operation = object(), object()
    base = _expectation(operation, source_handle)
    v, selected, selection_body, coords = fixture(base.source_coordinates, package=base.package_identity.package, production_digest=digest("earlier selection input"))
    contexts = (selection_body, origins.source_origin_body(v, role="source_origin"))
    owner = OriginalSource(source_handle, operation, contexts)
    host = inputs.SemanticInputProducerHost()
    seen = []
    async def produce(value):
        decoded = origins.decode_source_origin(value.context_bodies[1].canonical_body)
        origins.validate_source_origin_selection(decoded, selection=selected, selection_coordinate=selection_body.coordinate, source_coordinates=tuple(x.source for x in value.sources))
        assert decoded.selection_input_digest != value.input_digest
        seen.append(value)
        return _body()
    declared = replace(_DECLARATION, context_contracts=(
        inputs.SemanticInputContextContract(selection_body.coordinate.role, selection_body.coordinate.contract),
        inputs.SemanticInputContextContract("source_origin", origins.SOURCE_ORIGIN_REF),
    ))
    reg = inputs.register_semantic_input_producer(host, declaration=declared, producer=produce,
        validator=owner, validator_entrance=owner.validate_semantic_input_source,
        reader=owner, reader_entrance=owner.read_semantic_input_sources,
        context_validator_entrance=owner.validate_semantic_input_context, retain_result=True)
    expected = inputs.SemanticInputProductionExpectation.create(use_ref="new-assembly", operation_ref=base.operation_ref,
        stage=base.stage, package_identity=base.package_identity, operation_identity=operation,
        source_identity=source_handle, source_coordinates=coords, context_bodies=contexts)
    result = await inputs.execute_registered_semantic_input(host, reg, source_admission=source_handle, expected=expected)
    assert len(seen) == 1 and owner.context_calls >= 2
    owner.live = False
    with pytest.raises(ContractViolation): inputs.validate_registered_semantic_input_result(host, reg, source_admission=source_handle, expected=expected, result=result)
    assert not host._results
    host.close()
