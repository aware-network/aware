"""Committed-source canaries in disposable repositories only."""

from copy import copy
from dataclasses import replace
import json
from pathlib import Path

import pytest
from aware_goal_native_fs_adapter.native_view_source import CommittedGoalViewSourceProvider
from aware_goal_native_fs_adapter.compatibility_source import GoalNativeScopeSourceError
from aware_goal_operational_runtime.phase_native_view import project_goal_native_view_v2
from aware_goal_operational_runtime import GoalPhaseFutureScheduleV1, encode_goal_phase_future_schedule
from test_native_provider import (
    CUSTOMER_PATH, CUSTOMER_ISSUE_PATH, CUSTOMER_ISSUE_TAG, GOAL,
    _source, _native_capability, _git, _publish_customer_issue, _publish_native_only_lane,
)


def provider_fixture(tmp_path, monkeypatch, *, work=False, schedule=False):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH, unresolved=True,
        current_issue_ref=CUSTOMER_ISSUE_TAG if work else None)
    capability = _native_capability(root, monkeypatch)
    _git(root, "add", "aware.protocol.toml")
    _git(root, "commit", "-qm", "Commit admitted Protocol test source")
    _publish_native_only_lane(root)
    if work or schedule:
        _publish_customer_issue(root)
    provider = CommittedGoalViewSourceProvider(resolver_capability=capability,
        provider_ref="provider:test", provider_generation="generation:test",
        source_scope_ref="scope:test")
    if schedule:
        _, document = __import__("aware_goal_sdk").extract_goal_phase_native_document((root / CUSTOMER_PATH).read_bytes())
        from aware_goal_operational_runtime import schedule_path
        path = schedule_path(goal_doc_path=CUSTOMER_PATH, lane_key="runtime")
        # Existing schedule V1 has a docs/issues-only contract. The provider
        # must honor that profile, not weaken it for customer-root tests.
        issue_path = "docs/issues/2026/09/26/fb-2026-09-26-customer-work.md"
        issue = root / issue_path
        issue.parent.mkdir(parents=True)
        issue.write_text((root / CUSTOMER_ISSUE_PATH).read_text())
        issue.write_text(issue.read_text().replace("## Ownership Scope\n", f"## Ownership Scope\n- `{path}`\n"))
        manifest = root / "aware.protocol.toml"
        manifest.write_text(manifest.read_text().replace('root = "work/issues"', 'root = "docs/issues"'))
        _git(root, "add", issue_path, "aware.protocol.toml")
        _git(root, "commit", "-qm", "Govern schedule test source")
        from aware_protocol_fs_adapter.native_goal_resolver import admit_native_goal_resolver
        capability = admit_native_goal_resolver(repository_root=root, manifest_path=manifest).capability
        provider = CommittedGoalViewSourceProvider(resolver_capability=capability,
            provider_ref="provider:test", provider_generation="generation:test", source_scope_ref="scope:test")
        schedule = GoalPhaseFutureScheduleV1(goal_tag=GOAL, goal_doc_path=CUSTOMER_PATH,
            lane_key="runtime", definition_bindings=tuple(sorted((d.coordinate.phase_key, d.definition_ref)
                for d in document.definitions if d.coordinate.lane_key == "runtime")),
            authored_order=("first", "later"), retained_unscheduled=(),
            decision_issue_path=issue_path,
            decision_issue_blob_oid=_git(root, "rev-parse", "HEAD:" + issue_path))
        target = root / path
        target.parent.mkdir(parents=True)
        target.write_bytes(encode_goal_phase_future_schedule(schedule))
        _git(root, "add", path)
        _git(root, "commit", "-qm", "Publish schedule\n\nIssue-Tag: " + CUSTOMER_ISSUE_TAG
            + "\nIssue-Path: " + issue_path + "\nOwner: codex-test\nOwned-Paths: " + path)
    return root, provider


def test_single_epoch_reading_keeps_stale_worktree_and_native_only_lane(tmp_path, monkeypatch):
    root, provider = provider_fixture(tmp_path, monkeypatch, work=True)
    initial = (root / CUSTOMER_PATH).read_bytes()
    (root / CUSTOMER_PATH).write_bytes(initial + b"\nlocal uncommitted note\n")
    reading = provider.observe(goal_tag=GOAL)
    provider.require_current(reading)
    state = project_goal_native_view_v2(reading.to_wire(), observation_ref=reading.observation_ref)
    assert state["source"]["projection_health"] == "stale"
    assert [l["reading"]["lane_key"] for l in state["lanes"]] == ["runtime", "foundation"]
    assert state["lanes"][1]["reading"]["authority_availability"] == "unavailable"
    assert state["linked_issues"][0]["reading_view_ref"] == "issue.issue_reading"
    assert (root / CUSTOMER_PATH).read_bytes() == initial + b"\nlocal uncommitted note\n"
    assert state["operational_phase_count"] == 2


def test_current_schedule_comes_from_committed_publication_not_local_projection(tmp_path, monkeypatch):
    root, provider = provider_fixture(tmp_path, monkeypatch, schedule=True)
    from aware_goal_operational_runtime import schedule_path
    path = schedule_path(goal_doc_path=CUSTOMER_PATH, lane_key="runtime")
    (root / path).unlink()
    reading = provider.observe(goal_tag=GOAL)
    state = project_goal_native_view_v2(reading.to_wire(), observation_ref=reading.observation_ref)
    assert state["lanes"][0]["schedule"]["status"] == "current"
    assert state["lanes"][0]["schedule"]["schedule"]["authored_order"] == ["first", "later"]
    assert not (root / path).exists()


def test_copied_mutated_and_advanced_sources_refuse(tmp_path, monkeypatch):
    root, provider = provider_fixture(tmp_path, monkeypatch)
    reading = provider.observe(goal_tag=GOAL)
    with pytest.raises(ValueError, match="not_issued"):
        provider.require_issued(copy(reading))
    object.__setattr__(reading, "observation_ref", "forged")
    with pytest.raises(ValueError, match="mutated"):
        provider.require_issued(reading)
    fresh = provider.observe(goal_tag=GOAL)
    _git(root, "commit", "--allow-empty", "-qm", "Advance test HEAD")
    with pytest.raises(ValueError, match="repository_head_advanced"):
        provider.require_current(fresh)


def test_terminal_target_io_cannot_issue_against_old_head(tmp_path, monkeypatch):
    root, provider = provider_fixture(tmp_path, monkeypatch)
    original = provider._contain_schedule
    resolutions = 0
    def interleave(path, goal_root):
        nonlocal resolutions
        original(path, goal_root)
        resolutions += 1
        # Two source reads first, then terminal target re-resolution.
        if resolutions == 3:
            _git(root, "commit", "--allow-empty", "-qm", "Interleave HEAD advance")
    monkeypatch.setattr(provider, "_contain_schedule", interleave)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        provider.observe(goal_tag=GOAL)


def test_foreign_goal_symlink_refuses(tmp_path, monkeypatch):
    root, provider = provider_fixture(tmp_path, monkeypatch)
    target = root / CUSTOMER_PATH
    external = tmp_path / "external.md"
    external.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(external)
    with pytest.raises(ValueError):
        provider.observe(goal_tag=GOAL)


def test_retained_but_uncommitted_manifest_does_not_issue_source(tmp_path, monkeypatch):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    capability = _native_capability(root, monkeypatch)
    provider = CommittedGoalViewSourceProvider(resolver_capability=capability,
        provider_ref="provider:test", provider_generation="generation:test", source_scope_ref="scope:test")
    with pytest.raises(ValueError):
        provider.observe(goal_tag=GOAL)


def compatibility_only_fixture(tmp_path, monkeypatch):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH, operational=False,
        current_issue_ref=CUSTOMER_ISSUE_TAG)
    capability = _native_capability(root, monkeypatch)
    _publish_customer_issue(root)
    _git(root, "add", "aware.protocol.toml")
    _git(root, "commit", "-qm", "Commit admitted Protocol test source")
    provider = CommittedGoalViewSourceProvider(resolver_capability=capability,
        provider_ref="provider:test", provider_generation="generation:test",
        source_scope_ref="scope:test")
    return root, provider


def test_compatibility_only_issue_is_in_complete_source_inventory(tmp_path, monkeypatch):
    root, provider = compatibility_only_fixture(tmp_path, monkeypatch)
    reading = provider.observe(goal_tag=GOAL)
    wire = reading.to_wire()
    blob = _git(root, "rev-parse", "HEAD:" + CUSTOMER_ISSUE_PATH)
    assert f"git-blob:{CUSTOMER_ISSUE_PATH}:{blob}" in wire["source"]["input_refs"]
    assert wire["lanes"][0]["authority_availability"] == "source_recorded"
    assert wire["lanes"][0]["current_issue_ref"] == CUSTOMER_ISSUE_TAG
    assert wire["linked_issues"] == []  # No invented native Work association.
    provider.require_current(reading)


@pytest.mark.parametrize("at_issuance", [False, True])
def test_compatibility_only_issue_target_is_rechecked(tmp_path, monkeypatch, at_issuance):
    root, provider = compatibility_only_fixture(tmp_path, monkeypatch)
    target = root / CUSTOMER_ISSUE_PATH
    external = tmp_path / "foreign-issue.md"
    external.write_bytes(target.read_bytes())
    def replace_target():
        target.unlink()
        target.symlink_to(external)
    if at_issuance:
        original = provider._contain_schedule
        replaced = False
        def interleave(path, goal_root):
            nonlocal replaced
            original(path, goal_root)
            if not replaced:
                replace_target()
                replaced = True
        monkeypatch.setattr(provider, "_contain_schedule", interleave)
        with pytest.raises(GoalNativeScopeSourceError, match="escaped admitted root"):
            provider.observe(goal_tag=GOAL)
    else:
        reading = provider.observe(goal_tag=GOAL)
        replace_target()
        with pytest.raises(GoalNativeScopeSourceError, match="escaped admitted root"):
            provider.require_current(reading)


def test_compatibility_issue_terminal_freshness_checks_head_after_io(tmp_path, monkeypatch):
    root, provider = compatibility_only_fixture(tmp_path, monkeypatch)
    reading = provider.observe(goal_tag=GOAL)
    original = provider._issues.resolve_issue_path
    def interleave(path):
        original(path)
        assert path == CUSTOMER_ISSUE_PATH
        _git(root, "commit", "--allow-empty", "-qm", "Advance during compatibility Issue check")
    monkeypatch.setattr(provider._issues, "resolve_issue_path", interleave)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        provider.require_current(reading)
