"""Real committed-source compositions; no production activation or writes."""

import json

import pytest
from aware_goal_native_fs_adapter.consumer_read import NativeGoalConsumerReadClient
from aware_goal_sdk.phase_operation import GoalPhaseOperationClient
from test_native_provider import (
    CUSTOMER_EXTERNAL_PATH,
    CUSTOMER_ISSUE_PATH,
    CUSTOMER_PATH,
    EXTERNAL_GOAL,
    _git,
    _native_capability,
    _publish_external_source,
    _source,
)
from test_native_view_source import provider_fixture


def consumer_fixture(tmp_path, monkeypatch, *, v3=False, dependency=False):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH, v3=v3, dependency=dependency)
    capability = _native_capability(root, monkeypatch)
    _git(root, "add", "aware.protocol.toml")
    _git(root, "commit", "-qm", "Commit native test configuration")
    return root, NativeGoalConsumerReadClient(capability)


@pytest.mark.parametrize("v3", [False, True])
def test_eligibility_composes_original_request_and_decision_once(
    tmp_path, monkeypatch, v3
):
    root, client = consumer_fixture(tmp_path, monkeypatch, v3=v3)
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "status", "--porcelain=v1"))
    result = client.eligibility(
        goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
    )
    request = client._eligibility.discover_eligibility_request(
        goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
    )
    assert result["request"] == request.to_wire()
    assert result["result"] == GoalPhaseOperationClient(
        client._eligibility
    ).observe_eligibility(request)
    assert (
        result["discovered_revision"]
        == before[0]
        == result["result"]["source_revision_ref"]
    )
    assert result["result"]["eligibility"] == "eligible"
    assert (
        result["result"]["event_effect"]
        == result["result"]["dispatch_effect"]
        == "none"
    )
    assert (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "status", "--porcelain=v1"),
    ) == before


def test_missing_dependency_evidence_stays_held_not_evaluated(tmp_path, monkeypatch):
    _, client = consumer_fixture(tmp_path, monkeypatch, dependency=True)
    result = client.eligibility(
        goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
    )["result"]
    assert result["eligibility"] == "held"
    assert result["dependency_gate"]["not_evaluated"]


@pytest.mark.parametrize("v3", [False, True])
def test_show_uses_original_complete_reading_and_preserves_dirty_goal(
    tmp_path, monkeypatch, v3
):
    root, client = consumer_fixture(tmp_path, monkeypatch, v3=v3)
    goal = root / CUSTOMER_PATH
    goal.write_bytes(goal.read_bytes() + b"\nlocal note\n")
    before = (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "status", "--porcelain=v1"),
        goal.read_bytes(),
    )
    result = client.show(goal_path=CUSTOMER_PATH)
    assert result["reading"]["document"]["schema_id"].endswith("v3" if v3 else "v2")
    assert result["state"]["source"]["projection_health"] == "stale"
    assert result["state"]["capability_availability"] == "unavailable"
    assert any(
        ref.startswith("git-blob:aware.protocol.toml:")
        for ref in result["reading"]["source"]["input_refs"]
    )
    assert (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "status", "--porcelain=v1"),
        goal.read_bytes(),
    ) == before


def test_show_never_splices_dirty_issue_titles_into_committed_reading(
    tmp_path, monkeypatch
):
    root, source = provider_fixture(tmp_path, monkeypatch, work=True)
    client = NativeGoalConsumerReadClient(source._capability)
    committed = client.show(goal_path=CUSTOMER_PATH)
    issue = root / CUSTOMER_ISSUE_PATH
    issue.write_text(
        issue.read_text().replace("# Issue:", "# Issue: UNCOMMITTED TITLE ")
    )
    before = (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "status", "--porcelain=v1"),
        issue.read_bytes(),
    )
    result = client.show(goal_path=CUSTOMER_PATH)
    assert result["state"]["linked_issues"] == committed["state"]["linked_issues"]
    assert "UNCOMMITTED TITLE" not in json.dumps(result)
    assert any(
        ref.startswith("git-blob:" + CUSTOMER_ISSUE_PATH + ":")
        for ref in result["reading"]["source"]["input_refs"]
    )
    assert (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "status", "--porcelain=v1"),
        issue.read_bytes(),
    ) == before


@pytest.mark.parametrize(
    "when", ["after_discovery", "before_observation", "after_observation"]
)
def test_head_advance_never_rediscover_or_refreshes(tmp_path, monkeypatch, when):
    root, client = consumer_fixture(tmp_path, monkeypatch)
    discover, observe = (
        client._eligibility.discover_eligibility_request,
        client._eligibility.observe_eligibility,
    )
    calls = {"discover": 0, "observe": 0}

    def discovered(**kwargs):
        calls["discover"] += 1
        result = discover(**kwargs)
        if when == "after_discovery":
            _git(root, "commit", "--allow-empty", "-qm", "Unrelated advancement")
        return result

    def observed(request):
        calls["observe"] += 1
        if when == "before_observation":
            _git(root, "commit", "--allow-empty", "-qm", "Unrelated advancement")
        result = observe(request)
        if when == "after_observation":
            _git(root, "commit", "--allow-empty", "-qm", "Unrelated advancement")
        return result

    monkeypatch.setattr(client._eligibility, "discover_eligibility_request", discovered)
    monkeypatch.setattr(client._eligibility, "observe_eligibility", observed)
    with pytest.raises(ValueError, match="repository_head_advanced"):
        client.eligibility(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
        )
    assert calls["discover"] == 1
    assert calls["observe"] == (0 if when == "after_discovery" else 1)


def test_uncommitted_manifest_refuses_before_discovery(tmp_path, monkeypatch):
    root, _ = _source(tmp_path, goal_path=CUSTOMER_PATH)
    capability = _native_capability(root, monkeypatch)
    client = NativeGoalConsumerReadClient(capability)
    with pytest.raises(
        ValueError,
        match="native_view_protocol_not_committed|native_lane_source_not_regular",
    ):
        client.eligibility(
            goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
        )


def test_manifest_change_never_reenters_admission(tmp_path, monkeypatch):
    root, client = consumer_fixture(tmp_path, monkeypatch)
    manifest = root / "aware.protocol.toml"
    manifest.write_bytes(manifest.read_bytes() + b"\n# changed\n")
    with pytest.raises(ValueError, match="native_goal_manifest_changed"):
        client.show(goal_path=CUSTOMER_PATH)


def test_raw_root_cannot_construct_consumer(tmp_path):
    with pytest.raises(ValueError):
        NativeGoalConsumerReadClient(tmp_path)


def test_composed_cross_goal_observation_retains_historical_staleness(
    tmp_path, monkeypatch
):
    root, _ = _source(
        tmp_path, goal_path=CUSTOMER_PATH, dependency=True, external_dependency=True
    )
    _publish_external_source(root, goal_path=CUSTOMER_EXTERNAL_PATH)
    capability = _native_capability(root, monkeypatch)
    _git(root, "add", "aware.protocol.toml")
    _git(root, "commit", "-qm", "Commit native configuration")
    client = NativeGoalConsumerReadClient(
        capability, prerequisite_goal_paths={EXTERNAL_GOAL: CUSTOMER_EXTERNAL_PATH}
    )
    result = client.eligibility(
        goal_path=CUSTOMER_PATH, lane_key="runtime", phase_key="first"
    )
    assert result["result"]["eligibility"] == "held"
    assert result["result"]["dependency_gate"]["stale"] == ["first-requires-later"]
    assert result["discovered_revision"] == result["result"]["source_revision_ref"]


def test_show_refuses_head_race_after_qualified_observation(tmp_path, monkeypatch):
    root, client = consumer_fixture(tmp_path, monkeypatch)
    original = client._source.observe

    def observed(**kwargs):
        reading = original(**kwargs)
        _git(root, "commit", "--allow-empty", "-qm", "Concurrent source advancement")
        return reading

    monkeypatch.setattr(client._source, "observe", observed)
    with pytest.raises(
        ValueError,
        match="source_revision_changed|repository_head_advanced|source_stale",
    ):
        client.show(goal_path=CUSTOMER_PATH)
