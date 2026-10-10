"""Original-holder cleanup history and once-only physical attempts."""

from dataclasses import FrozenInstanceError

import pytest
from aware_file_system import retained_package as owner


def make_plan(tmp_path):
    return owner.retain_package_publication(
        root=tmp_path, target_path="package", ordered_members=(("a.txt", b"one"),)
    )


def test_detached_snapshot_survives_release_without_renewing_authority(tmp_path):
    plan = make_plan(tmp_path)
    before = plan.observe_cleanup()
    assert not before.attempted and before.outcome == "not_attempted"
    plan.release()
    after = owner.observe_package_cleanup(plan)
    assert after.attempted and after.outcome == "completed"
    assert before.outcome == "not_attempted"
    with pytest.raises(FrozenInstanceError):
        after.outcome = "not_attempted"
    assert plan.release() == after.evidence
    with pytest.raises(owner.PackagePublicationRefusal):
        plan.stage()


@pytest.mark.parametrize("failure", ["cleanup", "close"])
def test_interruptions_do_not_retry_cleanup_or_descriptor_close(
    tmp_path, monkeypatch, failure
):
    plan = make_plan(tmp_path)
    plan.stage()
    calls = []
    original_cleanup, original_close = owner._cleanup, owner._close_all

    def cleanup(state):
        calls.append("cleanup")
        if failure == "cleanup":
            raise KeyboardInterrupt("injected")
        original_cleanup(state)

    def close(state):
        calls.append("close")
        original_close(state)
        if failure == "close":
            raise KeyboardInterrupt("injected after actual descriptor close")

    monkeypatch.setattr(owner, "_cleanup", cleanup)
    monkeypatch.setattr(owner, "_close_all", close)
    try:
        plan.release()
        snapshot = plan.observe_cleanup()
        assert snapshot.attempted and snapshot.outcome == "incomplete"
        assert snapshot.evidence.cleanup_diagnostics
        plan.release()
        owner._abandon(
            owner._HANDLES[plan]
        )  # Fault proof only, not a consumer entrance.
        assert calls == ["cleanup", "close"]
        assert plan.observe_cleanup() == snapshot
    finally:
        # The cleanup-interrupted tree is deliberately retained, not retried.
        assert not (tmp_path / "package").exists()


def test_retirement_and_release_share_one_attempt(tmp_path, monkeypatch):
    plan = make_plan(tmp_path)
    calls = []
    original = owner._cleanup

    def cleanup(state):
        calls.append("cleanup")
        original(state)

    monkeypatch.setattr(owner, "_cleanup", cleanup)
    (tmp_path / "package").mkdir()
    with pytest.raises(owner.PackagePublicationRefusal):
        plan.validate_current()
    first = plan.observe_cleanup()
    assert first.attempted
    plan.release()
    assert calls == ["cleanup"]
    assert plan.observe_cleanup() == first


@pytest.mark.parametrize("value", [None, object(), 123])
def test_non_original_observation_refuses(value):
    with pytest.raises(owner.PackagePublicationRefusal):
        owner.observe_package_cleanup(value)


def test_foreign_observation_has_no_cleanup_effect(tmp_path, monkeypatch):
    plan = make_plan(tmp_path)
    before = plan.observe_cleanup()
    pid = owner.os.getpid()
    monkeypatch.setattr(owner.os, "getpid", lambda: pid + 1)
    with pytest.raises(owner.PackagePublicationRefusal):
        plan.observe_cleanup()
    monkeypatch.undo()
    assert plan.observe_cleanup() == before
    plan.release()
