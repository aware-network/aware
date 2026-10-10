"""Portable closure conformance, no issuer or membership authority."""
import json
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    CodeRetainedDependencyScopeClosure,
    DependencyScopeDeclaration,
    DependencyScopeEdge,
    DependencyScopeEntry,
    DependencyScopeRestriction,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec import (
    decode_dependency_scope_closure as decode,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec import (
    encode_dependency_scope_closure as encode,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeProjection,
)


def fixture():
    body = CodeRetainedScopeBody("aware.workspace.toml", "same-content", ContentDigest.of_bytes(b"x"), b"x")
    projection = CodeRetainedScopeProjection("repo", ContentDigest.of_bytes(b"obs"), body, (), ())
    scopes = tuple(DependencyScopeEntry(f"{k}/aware.workspace.toml", k, projection) for k in ("a", "b"))
    tag = lambda v: DependencyScopeRestriction("present", v)
    edge = DependencyScopeEdge(scopes[0].scope_key, scopes[1].scope_key,
        DependencyScopeDeclaration(body.relative_path, body.content_digest, 0, 0),
        "b", "workspace", "workspace://b", tag("local"), tag("workspace-revision:local"),
        "workspace://b#default", tag("default"), tag(("provider",)))
    return CodeRetainedDependencyScopeClosure(scopes[0].scope_key, scopes, (edge,))


def test_roundtrip_preserves_distinct_scopes_with_shared_body_refs():
    value = fixture()
    result = decode(encode(value))
    assert result == value and result is not value
    assert len(result.scopes) == 2
    assert result.scopes[0].projection is not value.scopes[0].projection


@pytest.mark.parametrize("state", ["unavailable", "absent"])
def test_nonpresent_restrictions_are_preserved_not_promoted(state):
    value = fixture()
    value = replace(value, edges=(replace(value.edges[0], channel=DependencyScopeRestriction(state)),))
    assert decode(encode(value)) == value


@pytest.mark.parametrize("field", ["dependency_id", "dependency_kind", "dependency_source", "profile_package_ref"])
def test_every_edge_text_changes_digest(field):
    value = fixture()
    changed = replace(value, edges=(replace(value.edges[0], **{field: "different"}),))
    assert changed.closure_digest != value.closure_digest


@pytest.mark.parametrize("mutation", ["extra", "digest", "whitespace", "duplicate", "tag", "index", "hex", "scope"])
def test_wire_rejections(mutation):
    body = encode(fixture()); wire = json.loads(body)
    if mutation == "extra": wire["unknown"] = 1
    elif mutation == "digest": wire["closure_digest"] = ContentDigest.of_bytes(b"wrong").value
    elif mutation == "whitespace": body += b"\n"
    elif mutation == "duplicate": body = body.replace(b'{', b'{"contract":"duplicate",', 1)
    elif mutation == "tag": wire["edges"][0]["channel"]["state"] = "absent"
    elif mutation == "index": wire["edges"][0]["declaration"]["dependency_index"] = True
    elif mutation == "hex": wire["scopes"][0]["projection"]["workspace_manifest"]["body_hex"] = "zz"
    else: wire["scopes"][0]["workspace_handle"] = " a"
    if mutation not in ("whitespace", "duplicate"): body = canonical_json_bytes(wire)
    with pytest.raises(ContractViolation): decode(body)


def test_duplicate_occurrence_cannot_redirect():
    value = fixture()
    with pytest.raises(ContractViolation): replace(value, edges=value.edges * 2)
    with pytest.raises(ContractViolation): replace(value, consumer_scope_key="missing")


@pytest.mark.parametrize("keys", [("b", "a"), ("a", "a"), tuple(str(i) for i in range(257))])
def test_provider_restriction_order_duplicates_and_bound(keys):
    with pytest.raises(ContractViolation): DependencyScopeRestriction("present", keys)


def test_size_bounds_precede_json_decode(monkeypatch):
    from aware_code_semantic_contract_runtime import (
        dependency_scope_closure_codec as codec,
    )
    monkeypatch.setattr(codec, "MAX_CANONICAL_BYTES", 1)
    with pytest.raises(ContractViolation): codec.decode_dependency_scope_closure(b"{}")
    with pytest.raises(ContractViolation): codec.encode_dependency_scope_closure(fixture())


@pytest.mark.parametrize("bound", ["MAX_SCOPES", "MAX_EDGES", "MAX_PATHS", "MAX_BODY_BYTES"])
def test_aggregate_limits_refuse_without_truncation(monkeypatch, bound):
    from aware_code_semantic_contract_runtime import dependency_scope_closure as model
    value = fixture()
    monkeypatch.setattr(model, bound, 0)
    with pytest.raises(ContractViolation):
        encode(value)


def test_foreign_witness_and_endpoint_refuse():
    value = fixture()
    edge = value.edges[0]
    with pytest.raises(ContractViolation):
        replace(value, edges=(replace(edge, target_scope_key="foreign"),))
    declaration = replace(edge.declaration, manifest_content_digest=ContentDigest.of_bytes(b"other"))
    with pytest.raises(ContractViolation):
        replace(value, edges=(replace(edge, declaration=declaration),))


def test_reader_signature_returns_concrete_portable_closure():
    import typing

    from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
        DependencyScopeReader,
    )
    assert typing.get_type_hints(DependencyScopeReader.read_dependency_scope_closure)["return"] is CodeRetainedDependencyScopeClosure
