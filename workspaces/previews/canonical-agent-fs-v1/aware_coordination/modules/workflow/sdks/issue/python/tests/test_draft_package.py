import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest
from aware_issue_sdk.draft_package import (
    ISSUE_DRAFT_PACKAGE_MAX_MEMBER_BYTES,
    ISSUE_DRAFT_PACKAGE_MAX_MEMBERS,
    IssueDraftPackageRequest,
)
from aware_issue_sdk.source_change import IssueSourceChangeRequest

SCRATCH = "docs/specs/.aware-spec-draft-" + "a" * 32
DIGEST = "sha256:" + "0" * 64


def request(**changes):
    values = {
        "issue_ref": "fb/2026-10-06/draft",
        "expected_issue_sha256": DIGEST,
        "manifest_locator": "aware.protocol.toml",
        "expected_manifest_sha256": DIGEST,
        "target_locator": "docs/specs/example",
        "scratch_locator": SCRATCH,
        "ordered_members": (
            ("SPEC.md", b"draft"),
            ("phases/first/README.md", b"phase"),
        ),
        "authoring_intent_ref": "draft-intent:one",
        "client_intent_id": "request:one",
    }
    values.update(changes)
    return IssueDraftPackageRequest(**values)


def test_exact_effect_footprint_includes_scratch_and_public_directories_and_members():
    candidate = request()
    assert candidate.ordered_effect_paths == tuple(
        path
        for root in (SCRATCH, "docs/specs/example")
        for path in (
            root,
            root + "/phases",
            root + "/phases/first",
            root + "/SPEC.md",
            root + "/phases/first/README.md",
        )
    )
    assert "aware.protocol.toml" not in candidate.ordered_effect_paths
    assert "docs/specs" not in candidate.ordered_effect_paths
    assert len(set(candidate.ordered_effect_paths)) == len(
        candidate.ordered_effect_paths
    )


def test_members_are_immutable_and_values_are_not_admission():
    candidate = request()
    with pytest.raises(FrozenInstanceError):
        candidate.intent = "protocol_specification_setup_v1"
    assert not hasattr(candidate, "publish_package")
    assert not hasattr(candidate, "validate_current")
    assert replace(candidate) == candidate


@pytest.mark.parametrize(
    "path",
    [
        "",
        ".",
        "..",
        "a/../b",
        "/a",
        "a//b",
        "a/./b",
        "a/",
        "a\\b",
        "a\x00b",
        "a\nb",
        "a\x7fb",
        " a",
        "a ",
        "\ud800",
    ],
)
def test_noncanonical_member_paths_refuse(path):
    with pytest.raises(ValueError):
        request(ordered_members=((path, b""),))


@pytest.mark.parametrize(
    "field", ["manifest_locator", "target_locator", "scratch_locator"]
)
@pytest.mark.parametrize("path", ["/outside", "../outside", "a//b", "a\x00b"])
def test_noncanonical_effect_and_observation_locators_refuse(field, path):
    with pytest.raises(ValueError):
        request(**{field: path})


@pytest.mark.parametrize(
    "field", ["issue_ref", "authoring_intent_ref", "client_intent_id"]
)
@pytest.mark.parametrize("value", ["", " padded", "control\nvalue", None])
def test_invalid_intent_coordinates_refuse(field, value):
    with pytest.raises(ValueError):
        request(**{field: value})


@pytest.mark.parametrize("field", ["expected_issue_sha256", "expected_manifest_sha256"])
@pytest.mark.parametrize(
    "value", ["0" * 64, "sha256:" + "A" * 64, "sha256:short", None]
)
def test_byte_digests_are_exact(field, value):
    with pytest.raises(ValueError):
        request(**{field: value})


@pytest.mark.parametrize(
    "members",
    [
        (),
        [],
        (("a", b""), ("a", b"")),
        (("b", b""), ("a", b"")),
        (("a", b""), ("a/b", b"")),
        (("a/b", b""), ("a/b/c", b"")),
        (["a", b""],),
        (("a", bytearray()),),
        (("a", "text"),),
        (("a",),),
    ],
)
def test_member_shape_order_and_file_directory_conflicts_refuse(members):
    with pytest.raises(ValueError):
        request(ordered_members=members)


@pytest.mark.parametrize(
    "scratch",
    [
        "docs/elsewhere/.aware-spec-draft-" + "a" * 32,
        "docs/specs/example",
        "docs/specs/tmp",
        "docs/specs/.aware-spec-draft-" + "A" * 32,
        "docs/specs/.aware-spec-draft-" + "a" * 31,
    ],
)
def test_exact_same_parent_private_scratch_profile(scratch):
    with pytest.raises(ValueError):
        request(scratch_locator=scratch)


@pytest.mark.parametrize(
    "manifest",
    [
        "docs/specs/example",
        "docs/specs/example/aware.protocol.toml",
        SCRATCH,
        SCRATCH + "/aware.protocol.toml",
    ],
)
def test_observed_manifest_cannot_be_inside_effect_roots(manifest):
    with pytest.raises(ValueError):
        request(manifest_locator=manifest)


def test_utf8_byte_bound_not_character_bound():
    request(ordered_members=(("é" * 512, b""),))
    with pytest.raises(ValueError):
        request(ordered_members=(("é" * 513, b""),))


def test_member_count_limit():
    members = tuple(
        (f"member-{index:05d}", b"") for index in range(ISSUE_DRAFT_PACKAGE_MAX_MEMBERS)
    )
    request(ordered_members=members)
    with pytest.raises(ValueError):
        request(ordered_members=(*members, ("member-extra", b"")))


def test_member_byte_limit():
    body = b"x" * ISSUE_DRAFT_PACKAGE_MAX_MEMBER_BYTES
    request(ordered_members=(("a", body),))
    with pytest.raises(ValueError):
        request(ordered_members=(("a", body + b"x"),))


def test_total_byte_limit():
    body = b"x" * ISSUE_DRAFT_PACKAGE_MAX_MEMBER_BYTES
    request(ordered_members=tuple((f"{index:02d}", body) for index in range(32)))
    with pytest.raises(ValueError):
        request(ordered_members=tuple((f"{index:02d}", body) for index in range(33)))


def test_empty_member_body_and_repository_root_parent_are_valid():
    candidate = request(
        target_locator="example",
        scratch_locator=".aware-spec-draft-" + "a" * 32,
        ordered_members=(("a", b""),),
    )
    assert len(candidate.ordered_effect_paths) == 4


def test_member_digest_binds_lengths_paths_and_exact_bytes_not_context():
    candidate = request(ordered_members=(("a", b"bc"),))
    assert candidate.candidate_sha256 == replace(candidate).candidate_sha256
    assert (
        candidate.candidate_sha256
        != request(ordered_members=(("ab", b"c"),)).candidate_sha256
    )
    assert (
        candidate.candidate_sha256
        != request(ordered_members=(("a", b"bd"),)).candidate_sha256
    )
    assert (
        candidate.candidate_sha256
        == replace(candidate, client_intent_id="request:two").candidate_sha256
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"intent": "protocol_specification_setup_v1"},
        {"intent": None},
        {"mode_profile": "arbitrary"},
        {"mode_profile": None},
    ],
)
def test_cross_intent_or_mode_profile_refuses(changes):
    with pytest.raises(ValueError):
        request(**changes)


def test_setup_request_does_not_accept_draft_intent():
    with pytest.raises(ValueError):
        IssueSourceChangeRequest(
            "issue",
            DIGEST,
            "aware.protocol.toml",
            DIGEST,
            b"",
            (),
            "client",
            intent="protocol_specification_draft_v1",
        )


def test_new_facade_exports_are_advertised_and_resolve():
    import aware_issue_sdk

    for name in (
        "IssueDraftPackageRequest",
        "ISSUE_DRAFT_PACKAGE_INTENT",
        "ISSUE_DRAFT_PACKAGE_MODE_PROFILE",
    ):
        assert name in aware_issue_sdk.__all__
        assert getattr(aware_issue_sdk, name) is not None
    assert aware_issue_sdk.IssueDraftPackageRequest is IssueDraftPackageRequest


@pytest.mark.parametrize(
    "path",
    ["e\u0301/README.md", *[f"a{chr(code)}b/README.md" for code in range(0x7F, 0xA0)]],
)
def test_non_nfc_and_full_c1_control_range_refuse_for_members_and_locators(path):
    with pytest.raises(ValueError):
        request(ordered_members=((path, b"exact bytes"),))
    for field in ("manifest_locator", "target_locator", "scratch_locator"):
        with pytest.raises(
            ValueError, match="canonical relative locators|non-control text"
        ):
            request(**{field: path})


def test_nfc_member_paths_preserve_exact_spelling_and_digest():
    candidate = request(ordered_members=(("\u00e9/README.md", b"exact bytes"),))
    assert candidate.ordered_members[0][0] == "\u00e9/README.md"
    assert SCRATCH + "/\u00e9/README.md" in candidate.ordered_effect_paths
    assert candidate.candidate_sha256 == replace(candidate).candidate_sha256
    with pytest.raises(ValueError):
        request(ordered_members=(("e\u0301/README.md", b"exact bytes"),))


def test_nfc_manifest_and_target_locators_remain_exact():
    candidate = request(
        manifest_locator="\u00e9/aware.protocol.toml",
        target_locator="docs/specs/\u00e9",
    )
    assert candidate.manifest_locator == "\u00e9/aware.protocol.toml"
    assert candidate.target_locator == "docs/specs/\u00e9"


def test_intent_validation_and_footprint_have_no_filesystem_effects(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Neutral intent must not perform filesystem effects")

    for name in ("open", "mkdir", "rename", "replace", "unlink", "rmdir", "stat"):
        monkeypatch.setattr(os, name, forbidden)
    candidate = request()
    assert candidate.candidate_sha256.startswith("sha256:")
    assert len(candidate.ordered_effect_paths) == 10


def test_fresh_facade_resolution_does_not_import_service_or_writer_graph():
    source_root = str(Path(__file__).resolve().parents[1])
    script = f"""
import sys
sys.path.insert(0, {source_root!r})
import aware_issue_sdk
for name in ('IssueDraftPackageRequest', 'ISSUE_DRAFT_PACKAGE_INTENT', 'ISSUE_DRAFT_PACKAGE_MODE_PROFILE'):
    assert name in aware_issue_sdk.__all__
    getattr(aware_issue_sdk, name)
assert not any(name.startswith(('aware_issue_sdk.client', 'aware_issue_sdk.view_state',
    'aware_issue_fs_adapter', 'aware_file_system', 'aware_protocol', 'aware_specification',
    'aware_content_service', 'aware_issue_service')) for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
