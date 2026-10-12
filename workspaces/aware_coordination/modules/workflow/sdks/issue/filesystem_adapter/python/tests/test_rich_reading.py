import hashlib
from dataclasses import replace
from datetime import datetime

import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_fs_adapter.provider import (
    FILESYSTEM_ISSUE_DISTRIBUTION,
    FILESYSTEM_ISSUE_PROVIDER_REF,
    _distribution_version,
)
from aware_issue_sdk import (
    IssueReadingProviderBinding,
    IssueReadingResolveRequest,
    IssueReadProjectionResolveRequest,
    IssueSdkOperationClient,
)

ISSUE = "fb/2026-10-11/example"
PATH = "docs/issues/2026/10/11/fb-2026-10-11-example.md"
SOURCE = f"# Issue: Example\n\n- Tag: {ISSUE}\n- Status: Open\n"
MANIFEST = """aware = 1
[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1
[target]
kind = "repository"
authority_mode = "filesystem"
[bootstrap]
agent_contract = "AGENTS.md"
[records.issue]
profile = "aware.issue.markdown.v1"
root = "docs/issues"
role = "authority"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"
[records.goal]
profile = "aware.goal.markdown.v1"
role = "unavailable"
[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"
[records.specification]
profile = "specification_fs_v1"
role = "unavailable"
[records.evidence]
profile = "aware.protocol.evidence.v1"
role = "unavailable"
"""


@pytest.fixture
def installed(tmp_path):
    (tmp_path / "aware.protocol.toml").write_text(MANIFEST)
    (tmp_path / "AGENTS.md").write_text("# Contract\n")
    path = tmp_path / PATH
    path.parent.mkdir(parents=True)
    path.write_text(SOURCE)
    ordinary = FilesystemIssueOperationProvider(repository_root=tmp_path)
    profile = ordinary._admit_manifest()
    binding = IssueReadingProviderBinding(
        FILESYSTEM_ISSUE_PROVIDER_REF,
        FILESYSTEM_ISSUE_DISTRIBUTION,
        _distribution_version(FILESYSTEM_ISSUE_DISTRIBUTION),
        "installation:private",
        "generation:1",
        "repository:fixture",
        profile.protocol_manifest.protocol.profile,
        "sha256:"
        + hashlib.sha256((tmp_path / "aware.protocol.toml").read_bytes()).hexdigest(),
        "issue.reading.local-private.v1",
    )
    provider = FilesystemIssueOperationProvider(
        repository_root=tmp_path, reading_binding=binding
    )
    return tmp_path, provider, IssueReadingResolveRequest("request:1", ISSUE, binding)


def test_original_capture_is_single_read_and_source_time_is_owner_issued(
    installed, monkeypatch
):
    root, provider, request = installed
    actual = provider._read_source
    reads = []

    def capture(path, **kwargs):
        if path == root / PATH:
            reads.append(path)
        return actual(path, **kwargs)

    monkeypatch.setattr(provider, "_read_source", capture)
    before = datetime.now().astimezone()
    value = IssueSdkOperationClient(provider).resolve_reading(request)
    after = datetime.now().astimezone()
    assert len(reads) == 1
    assert value.projection.source.raw_markdown == SOURCE
    assert (
        value.projection.source.digest
        == "sha256:" + hashlib.sha256(SOURCE.encode()).hexdigest()
    )
    instant = datetime.fromisoformat(value.projection.source.observed_at)
    assert before.replace(microsecond=0) <= instant <= after
    assert value.observation_ref and value.horizon_ref
    next_value = provider.resolve_reading(replace(request, request_ref="request:2"))
    assert (
        next_value.projection.projection_revision
        == value.projection.projection_revision
    )
    assert next_value.observation_ref != value.observation_ref
    assert next_value.horizon_ref != value.horizon_ref


def test_base_wire_is_unchanged_and_never_gains_raw_source(installed):
    root, provider, request = installed
    base_request = IssueReadProjectionResolveRequest(ISSUE)
    before = provider.resolve_read_projection(base_request).to_wire()
    provider.resolve_reading(request)
    after = provider.resolve_read_projection(base_request).to_wire()
    assert before == after
    assert "raw_markdown" not in before["projection"]
    ordinary = FilesystemIssueOperationProvider(repository_root=root)
    assert ordinary.resolve_reading(request).projection is None


@pytest.mark.parametrize(
    "coordinate",
    ["generation_ref", "repository_ref", "installation_ref", "profile_ref"],
)
def test_foreign_selected_binding_refuses_before_source_read(
    installed, monkeypatch, coordinate
):
    _, provider, request = installed
    monkeypatch.setattr(
        provider, "_read_source", lambda *a, **k: pytest.fail("source read")
    )
    bad = replace(request, binding=replace(request.binding, **{coordinate: "foreign"}))
    assert provider.resolve_reading(bad).projection is None


@pytest.mark.parametrize(
    "source",
    [b"x" * 262145, b"\xff", b"# Issue: Wrong\n- Tag: fb/2026-10-11/foreign\n"],
)
def test_malformed_overlimit_or_foreign_source_has_no_usable_payload(installed, source):
    root, provider, request = installed
    (root / PATH).write_bytes(source)
    value = provider.resolve_reading(request)
    assert (
        value.projection is None
        and value.observation_ref is None
        and value.horizon_ref is None
    )


def test_missing_source_and_replaced_manifest_fail_closed(installed):
    root, provider, request = installed
    (root / PATH).unlink()
    assert provider.resolve_reading(request).outcome.value == "absent"
    (root / "aware.protocol.toml").write_text(MANIFEST + "\n# changed\n")
    assert provider.resolve_reading(request).projection is None
    (root / "aware.protocol.toml").write_text(
        MANIFEST.replace('root = "docs/issues"', 'root = "other/issues"')
    )
    assert provider.resolve_reading(request).projection is None


def test_manifest_replacement_after_capture_cannot_publish(installed, monkeypatch):
    root, provider, request = installed
    actual = provider._read_source

    def move(path, **kwargs):
        source = actual(path, **kwargs)
        if path == root / PATH:
            (root / "aware.protocol.toml").write_text(
                MANIFEST.replace('root = "docs/issues"', 'root = "other/issues"')
            )
        return source

    monkeypatch.setattr(provider, "_read_source", move)
    assert provider.resolve_reading(request).projection is None


def test_unreadable_duplicate_candidate_is_not_silently_skipped(installed):
    root, provider, request = installed
    other = root / "docs/issues/2026/10/11/fb-2026-10-11-other.md"
    other.write_bytes(b"x" * 262145)
    assert provider.resolve_reading(request).projection is None
