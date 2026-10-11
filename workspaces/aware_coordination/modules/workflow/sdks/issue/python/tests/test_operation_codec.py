import json
from dataclasses import replace

import pytest
from aware_issue_sdk import operation as op
from aware_issue_sdk.operation_codec import (
    REQUEST_TYPES,
    decode_issue_request,
    decode_issue_result,
    encode_issue_request,
    encode_issue_result,
)

REF = "fb/2026-10-11/example"
COMMON = {
    "issue_ref": REF,
    "expected_source_sha256": "sha256:" + "a" * 64,
    "client_intent_id": "intent",
    "actor_ref": "actor",
    "actor_evidence_ref": "evidence",
}


def requests():
    return [
        op.IssueReadProjectionResolveRequest(REF),
        op.IssueEnsureSnapshotRequest(
            issue_ref=REF,
            title="Example",
            priority="P1",
            actor_ref="actor",
            actor_evidence_ref="evidence",
            client_intent_id="ensure",
        ),
        op.IssueStartProgressRequest(**COMMON),
        op.IssueBlockRequest(**COMMON),
        op.IssueResumeRequest(**COMMON),
        op.IssueSetOwnerRequest(**COMMON, new_owner_ref="next"),
        op.IssueBindScopePathsRequest(**COMMON, scope_paths=("src/a",)),
        op.IssueAppendUpdateRequest(**COMMON, message="update"),
        op.IssueAppendEvidenceRequest(**COMMON, path="proof.txt"),
    ]


@pytest.mark.parametrize("value", requests())
def test_all_nine_request_roundtrips(value):
    key = next(key for key, cls in REQUEST_TYPES.items() if type(value) is cls)
    assert decode_issue_request(key, encode_issue_request(value)) == value


@pytest.mark.parametrize("value", requests())
@pytest.mark.parametrize("poison", ["extra", "missing", "type", "operation"])
def test_request_poison(value, poison):
    key = next(key for key, cls in REQUEST_TYPES.items() if type(value) is cls)
    wire = encode_issue_request(value)
    if poison == "extra":
        wire["accepted"] = True
    elif poison == "missing":
        wire.pop("issue_ref")
    elif poison == "type":
        wire["issue_ref"] = True
    else:
        wire["contract" if "contract" in wire else "operation_ref"] = "foreign"
    with pytest.raises(ValueError):
        decode_issue_request(key, wire)


@pytest.mark.parametrize("outcome", list(op.IssueMutationOutcome))
def test_refused_mutation_roundtrip(outcome):
    if outcome in (op.IssueMutationOutcome.APPLIED, op.IssueMutationOutcome.IDEMPOTENT):
        return
    result = op.IssueMutationResult(
        op.ISSUE_BLOCK_OPERATION_REF, outcome, REF, "provider", "package", "1.0"
    )
    wire = encode_issue_result(result)
    assert decode_issue_result(op.ISSUE_BLOCK_PROVIDER_OPERATION_REF, wire) == result
    with pytest.raises(ValueError):
        decode_issue_result(op.ISSUE_START_PROGRESS_PROVIDER_OPERATION_REF, wire)


def test_byte_node_depth_and_cycle_limits():
    request = replace(requests()[1], title="a" * 65536)
    with pytest.raises(ValueError):
        encode_issue_request(request)
    wire = requests()[0].to_wire()
    wire["recursive"] = wire
    with pytest.raises(ValueError):
        decode_issue_request(
            op.ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF, wire
        )


def test_request_byte_exact_boundary():
    value = requests()[1]
    base = len(
        json.dumps(
            encode_issue_request(value), ensure_ascii=False, separators=(",", ":")
        ).encode()
    )
    value = replace(value, title="a" * (65536 - base + len(value.title)))
    assert (
        len(json.dumps(encode_issue_request(value), separators=(",", ":")).encode())
        == 65536
    )
    with pytest.raises(ValueError):
        encode_issue_request(replace(value, title=value.title + "a"))


@pytest.mark.parametrize(
    "resource", ["depth", "nodes", "array", "string", "result_bytes"]
)
def test_exact_inner_structure_bound_and_successor(resource):
    from aware_issue_sdk.operation_codec import MAX_RESULT_BYTES, _bounded

    if resource == "depth":
        legal = "x"
        for _ in range(32):
            legal = [legal]
        illegal = [legal]
    elif resource == "nodes":
        legal = {str(i): None for i in range(4095)}
        illegal = {**legal, "next": None}
    elif resource == "array":
        legal, illegal = [None] * 4096, [None] * 4097
    elif resource == "string":
        legal, illegal = "a" * 262144, "a" * 262145
    else:
        legal = ["a" * 262144, "a" * 262144, ""]
        used = len(json.dumps(legal, separators=(",", ":")).encode())
        legal[-1] = "a" * (MAX_RESULT_BYTES - used)
        illegal = [*legal[:-1], legal[-1] + "a"]
    assert _bounded(legal, MAX_RESULT_BYTES) == legal
    with pytest.raises(ValueError):
        _bounded(illegal, MAX_RESULT_BYTES)


@pytest.mark.parametrize(
    "poison",
    [
        "schema",
        "identity",
        "digest",
        "after",
        "raw",
        "bool",
        "enum",
        "extra",
        "missing",
    ],
)
def test_projection_poison(poison):
    from aware_issue_runtime import parse_issue_projection

    projection = parse_issue_projection(
        text=f"# Issue: Example\n\n- Tag: `{REF}`\n- Status: Open\n",
        source_path="docs/issues/2026/10/11/fb-2026-10-11-example.md",
    )
    result = op.IssueMutationResult(
        op.ISSUE_START_PROGRESS_OPERATION_REF,
        op.IssueMutationOutcome.APPLIED,
        REF,
        "provider",
        "package",
        "1.0",
        source_sha256_after=projection.source_digest,
        projection=projection,
    )
    wire = encode_issue_result(result)
    assert (
        decode_issue_result(
            op.ISSUE_START_PROGRESS_PROVIDER_OPERATION_REF, wire
        ).to_wire()
        == wire
    )
    if poison == "schema":
        wire["projection"]["schema_version"] = "foreign"
    elif poison == "identity":
        wire["projection"]["issue_ref"] = "fb/2026-10-11/other"
    elif poison == "digest":
        wire["projection"]["source"]["digest"] = "foreign"
    elif poison == "after":
        wire["source_sha256_after"] = "sha256:" + "a" * 64
    elif poison == "raw":
        wire["projection"]["source"]["raw_markdown"] = "invented"
    elif poison == "bool":
        wire["projection"]["identity"]["title"] = True
    elif poison == "enum":
        wire["outcome"] = "accepted"
    elif poison == "extra":
        wire["projection"]["source"]["accepted"] = True
    else:
        wire["projection"]["identity"].pop("owner_ref")
    with pytest.raises(ValueError):
        decode_issue_result(op.ISSUE_START_PROGRESS_PROVIDER_OPERATION_REF, wire)
