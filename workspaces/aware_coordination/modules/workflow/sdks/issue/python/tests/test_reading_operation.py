from dataclasses import FrozenInstanceError, replace

import pytest
from aware_issue_sdk import (
    IssueReadingProviderBinding,
    IssueReadingResolveRequest,
    IssueReadingResolveResult,
    IssueReadProjectionResolveOutcome,
    IssueSdkOperationClient,
    build_issue_development_read_projection_v2,
)
from aware_issue_sdk.reading_operation import canonical_bytes, decode_json


def binding():
    return IssueReadingProviderBinding(
        "fs",
        "fs-package",
        "1.0.0",
        "install:a",
        "generation:a",
        "repository:a",
        "aware.collaboration.fs_v1",
        "sha256:" + "a" * 64,
        "issue.reading.local-private.v1",
    )


def result():
    issue = "fb/2026-10-11/example"
    projection = build_issue_development_read_projection_v2(
        content_text=f"# Issue: Example\n\n- Tag: {issue}\n- Status: Open\n",
        source_path="docs/issues/2026/10/11/fb-2026-10-11-example.md",
        source_observed_at="2026-10-11T00:00:00Z",
    )
    return IssueReadingResolveResult(
        "request:1",
        issue,
        IssueReadProjectionResolveOutcome.FOUND,
        binding(),
        projection,
        "source-observation:1",
        "completed-snapshot:1",
    )


def test_rich_types_are_immutable_and_byte_roundtrip_is_exact():
    value = result()
    encoded = canonical_bytes(value.to_wire())
    assert IssueReadingResolveResult.from_wire(decode_json(encoded)) == value
    with pytest.raises(FrozenInstanceError):
        value.request_ref = "another"
    request = IssueReadingResolveRequest(
        value.request_ref, value.issue_ref, value.binding
    )
    assert IssueReadingResolveRequest.from_wire(request.to_wire()) == request


@pytest.mark.parametrize("part", ["request_ref", "issue_ref", "binding"])
def test_independent_request_coordinates_are_bound(part):
    value = result()
    request = IssueReadingResolveRequest(
        value.request_ref, value.issue_ref, value.binding
    )
    substitutions = {
        "request_ref": "request:foreign",
        "issue_ref": "fb/2026-10-11/foreign",
        "binding": replace(value.binding, generation_ref="generation:foreign"),
    }
    with pytest.raises(ValueError):
        value.require_request(replace(request, **{part: substitutions[part]}))


@pytest.mark.parametrize(
    "field", ["schema_ref", "projection_revision", "source", "identity"]
)
def test_forged_or_incomplete_rich_projection_rejects(field):
    wire = result().to_wire()
    if field == "source":
        wire["projection"]["source"]["raw_markdown"] += "substituted"
    elif field == "identity":
        wire["projection"]["identity"]["issue_ref"] = "fb/2026-10-11/foreign"
    else:
        del wire["projection"][field]
    with pytest.raises((TypeError, ValueError)):
        IssueReadingResolveResult.from_wire(wire)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.update(extra=True),
        lambda row: row["binding"].update(extra=True),
        lambda row: row["projection"]["identity"].update(title=123),
        lambda row: row.update(outcome="absent"),
        lambda row: row.update(observation_ref=None),
        lambda row: row.update(horizon_ref=None),
    ],
)
def test_strict_decoding_has_no_coercion_or_mixed_success(mutate):
    row = result().to_wire()
    mutate(row)
    with pytest.raises((TypeError, ValueError)):
        IssueReadingResolveResult.from_wire(row)


def test_duplicate_json_and_bounds_reject_before_use():
    with pytest.raises(ValueError, match="duplicate"):
        decode_json(b'{"request_ref":"a","request_ref":"b"}')
    with pytest.raises(ValueError, match="limit"):
        decode_json(b" " * 65, limit=64)
    with pytest.raises(ValueError):
        canonical_bytes({"x": float("nan")})


def test_unsupported_provider_fails_before_any_ordinary_operation():
    class Ordinary:
        def resolve_read_projection(self, request):
            pytest.fail("rich reading must not fall back to ordinary read")

    value = result()
    with pytest.raises(TypeError, match="unsupported"):
        IssueSdkOperationClient(Ordinary()).resolve_reading(
            IssueReadingResolveRequest(
                value.request_ref, value.issue_ref, value.binding
            )
        )


def test_sdk_rechecks_original_result_not_provider_self_assertion():
    value = result()

    class Foreign:
        def resolve_reading(self, request):
            return replace(value, request_ref="foreign")

    with pytest.raises(ValueError, match="correspondence"):
        IssueSdkOperationClient(Foreign()).resolve_reading(
            IssueReadingResolveRequest(
                value.request_ref, value.issue_ref, value.binding
            )
        )
