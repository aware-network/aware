"""V2 portable conformance; fixtures confer no original source authority."""

import json
import typing
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec import (
    decode_dependency_scope_closure,
    encode_dependency_scope_closure,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec_v2 import (
    decode_dependency_scope_closure_v2 as decode,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_codec_v2 import (
    encode_dependency_scope_closure_v2 as encode,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
    DependencyScopeProfileAssociation,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
)
from test_dependency_scope_closure import fixture as v1_fixture


def fixture():
    old = v1_fixture()
    edge = old.edges[0]
    raw = b"# retained profile\n"
    body = CodeRetainedScopeBody(
        "semantic_contract/profiles/custom.key/aware.semantic_contract_profile.toml",
        "profile-body",
        ContentDigest.of_bytes(raw),
        raw,
    )
    association = DependencyScopeProfileAssociation(
        edge.declaring_scope_key, edge.declaration, edge.target_scope_key, body
    )
    return CodeRetainedDependencyScopeClosureV2(
        old.consumer_scope_key, old.scopes, old.edges, (association,)
    )


def test_roundtrip_and_no_semantic_admission():
    value = fixture()  # invalid semantic TOML remains faithfully portable
    assert decode(encode(value)) == value
    assert decode(encode(value)) is not value
    assert value.closure_digest != v1_fixture().closure_digest


def test_v1_unchanged_and_cross_version_refuses():
    v1 = v1_fixture()
    v2 = fixture()
    assert decode_dependency_scope_closure(encode_dependency_scope_closure(v1)) == v1
    for call, arg in [
        (decode, encode_dependency_scope_closure(v1)),
        (decode_dependency_scope_closure, encode(v2)),
        (encode, v1),
        (encode_dependency_scope_closure, v2),
    ]:
        with pytest.raises(ContractViolation):
            call(arg)


def test_empty_edges_require_empty_associations():
    value = fixture()
    empty = replace(value, edges=(), profile_associations=())
    assert decode(encode(empty)) == empty
    with pytest.raises(ContractViolation):
        replace(value, edges=())


@pytest.mark.parametrize(
    "mutation", ["missing", "extra", "target", "declaring", "path", "digest", "index"]
)
def test_association_exact_correspondence(mutation):
    value = fixture()
    a = value.profile_associations[0]
    if mutation == "missing":
        rows = ()
    elif mutation == "extra":
        rows = (a, a)
    elif mutation == "target":
        rows = (replace(a, target_scope_key=value.consumer_scope_key),)
    elif mutation == "declaring":
        rows = (replace(a, declaring_scope_key=a.target_scope_key),)
    else:
        key = {
            "path": "manifest_relative_path",
            "digest": "manifest_content_digest",
            "index": "profile_package_index",
        }[mutation]
        changed = {
            "path": "foreign.toml",
            "digest": ContentDigest.of_bytes(b"foreign"),
            "index": 1,
        }[mutation]
        rows = (replace(a, declaration=replace(a.declaration, **{key: changed})),)
    with pytest.raises(ContractViolation):
        replace(value, profile_associations=rows)


def two_edges():
    value = fixture()
    edge = value.edges[0]
    a = value.profile_associations[0]
    declaration = replace(edge.declaration, profile_package_index=1)
    return replace(
        value,
        edges=(edge, replace(edge, declaration=declaration)),
        profile_associations=(a, replace(a, declaration=declaration)),
    )


def test_shared_body_preserves_occurrences_and_order():
    value = two_edges()
    assert len(decode(encode(value)).profile_associations) == 2
    with pytest.raises(ContractViolation):
        replace(value, profile_associations=tuple(reversed(value.profile_associations)))


def test_same_ref_different_paths_valid_same_content():
    value = two_edges()
    a, b = value.profile_associations
    value = replace(
        value,
        profile_associations=(
            a,
            replace(
                b, manifest=replace(b.manifest, relative_path="other/profile.toml")
            ),
        ),
    )
    assert decode(encode(value)) == value


@pytest.mark.parametrize("change", ["content", "ref"])
def test_conflicting_ref_or_path_refuses(change):
    value = two_edges()
    a, b = value.profile_associations
    if change == "content":
        body = replace(
            b.manifest,
            body=b"changed",
            content_digest=ContentDigest.of_bytes(b"changed"),
        )
    else:
        body = replace(b.manifest, body_ref="different")
    with pytest.raises(ContractViolation):
        replace(value, profile_associations=(a, replace(b, manifest=body)))


def test_comment_body_and_coordinate_changes_bind_digest():
    value = fixture()
    a = value.profile_associations[0]
    for body in [
        replace(
            a.manifest,
            body=b"# changed",
            content_digest=ContentDigest.of_bytes(b"# changed"),
        ),
        replace(a.manifest, relative_path="different.toml"),
        replace(a.manifest, body_ref="different"),
    ]:
        changed = replace(value, profile_associations=(replace(a, manifest=body),))
        assert changed.closure_digest != value.closure_digest


@pytest.mark.parametrize(
    "mutation",
    [
        "extra",
        "missing",
        "version",
        "duplicate",
        "whitespace",
        "digest",
        "body_hex",
        "size_bool",
        "association_extra",
    ],
)
def test_strict_wire_rejections(mutation):
    body = encode(fixture())
    wire = json.loads(body)
    if mutation == "extra":
        wire["extra"] = 1
    elif mutation == "missing":
        del wire["profile_associations"]
    elif mutation == "version":
        wire["contract"] = "aware.code.retained-dependency-scope-closure.v1"
    elif mutation == "duplicate":
        body = body.replace(b"{", b'{"contract":"duplicate",', 1)
    elif mutation == "whitespace":
        body += b"\n"
    elif mutation == "digest":
        wire["closure_digest"] = ContentDigest.of_bytes(b"wrong").value
    elif mutation == "body_hex":
        wire["profile_associations"][0]["manifest"]["body_hex"] = "zz"
    elif mutation == "size_bool":
        wire["profile_associations"][0]["manifest"]["size_bytes"] = True
    else:
        wire["profile_associations"][0]["extra"] = True
    if mutation not in ("duplicate", "whitespace"):
        body = canonical_json_bytes(wire)
    with pytest.raises(ContractViolation):
        decode(body)


@pytest.mark.parametrize("limit", ["MAX_PATHS", "MAX_BODY_BYTES"])
def test_repeated_occurrences_count_at_exact_bound(monkeypatch, limit):
    from aware_code_semantic_contract_runtime import (
        dependency_scope_closure_v2 as model,
    )

    value = two_edges()
    n = (
        4
        if limit == "MAX_PATHS"
        else 2 + 2 * len(value.profile_associations[0].manifest.body)
    )
    monkeypatch.setattr(model, limit, n)
    encode(value)
    monkeypatch.setattr(model, limit, n - 1)
    with pytest.raises(ContractViolation):
        encode(value)


@pytest.mark.parametrize(
    "limit",
    ["MAX_BODY_BYTES", "MAX_PATHS", "MAX_SCOPE_BODY_BYTES", "MAX_EDGES", "MAX_SCOPES"],
)
def test_decode_bounds_precede_raw_body_decode(monkeypatch, limit):
    from aware_code_semantic_contract_runtime import (
        dependency_scope_closure_codec_v2 as codec,
    )

    body = encode(fixture())
    monkeypatch.setattr(codec, limit, 0)
    monkeypatch.setattr(
        codec, "_scope", lambda _: pytest.fail("raw body allocation reached")
    )
    with pytest.raises(ContractViolation):
        decode(body)


def test_encoded_bound_precedes_json_decode(monkeypatch):
    from aware_code_semantic_contract_runtime import (
        dependency_scope_closure_codec_v2 as codec,
    )

    body = encode(fixture())
    monkeypatch.setattr(codec, "MAX_CANONICAL_BYTES", len(body) - 1)
    with pytest.raises(ContractViolation):
        encode(fixture())
    with pytest.raises(ContractViolation):
        decode(body)


def test_reader_versions_are_concrete_and_separate():
    from aware_code_semantic_contract_runtime.dependency_scope_interfaces import (
        DependencyScopeReader,
        DependencyScopeReaderV2,
    )

    assert (
        typing.get_type_hints(DependencyScopeReaderV2.read_dependency_scope_closure)[
            "return"
        ]
        is CodeRetainedDependencyScopeClosureV2
    )
    assert typing.get_type_hints(DependencyScopeReader.read_dependency_scope_closure)[
        "return"
    ] is type(v1_fixture())


def test_profile_ref_collision_with_existing_target_body_refuses():
    value = fixture()
    a = value.profile_associations[0]
    target = value.scopes[1].projection.workspace_manifest
    with pytest.raises(ContractViolation):
        replace(
            value,
            profile_associations=(
                replace(a, manifest=replace(a.manifest, body_ref=target.body_ref)),
            ),
        )


def test_unrelated_scope_ref_strings_do_not_merge_domains():
    value = fixture()
    a = value.profile_associations[0]
    consumer = value.scopes[0]
    body = replace(consumer.projection.workspace_manifest, body_ref=a.manifest.body_ref)
    scopes = (
        replace(
            consumer, projection=replace(consumer.projection, workspace_manifest=body)
        ),
        value.scopes[1],
    )
    value = replace(value, scopes=scopes)
    assert decode(encode(value)) == value


def test_empty_retained_profile_bytes_are_portable_not_missing():
    value = fixture()
    a = value.profile_associations[0]
    value = replace(
        value,
        profile_associations=(
            replace(
                a,
                manifest=replace(
                    a.manifest, body=b"", content_digest=ContentDigest.of_bytes(b"")
                ),
            ),
        ),
    )
    assert decode(encode(value)) == value
