from __future__ import annotations

import random
from pydantic import Field
from uuid import UUID, uuid4

from aware_orm.models.orm_model import ORMModel
from aware_orm.session import change_collector
from aware_orm.session.change_collector import (
    TrackedList,
    disable_change_tracking_hooks,
    disable_tracked_list_wrapping,
    scoped_change_collection,
)


class _Owner(ORMModel):
    values: list[int] = Field(default_factory=list)


class _UuidOwner(ORMModel):
    values: list[UUID] = Field(default_factory=list)


def test_disable_tracked_list_wrapping_context_skips_wrapping() -> None:
    with disable_tracked_list_wrapping():
        owner = _Owner(values=[1, 2, 3])

    assert isinstance(owner.values, list)
    assert not isinstance(owner.values, TrackedList)


def test_disable_tracked_list_wrapping_context_restores_after_exit() -> None:
    with disable_tracked_list_wrapping():
        _ = _Owner(values=[1, 2, 3])

    owner = _Owner(values=[4, 5, 6])
    assert isinstance(owner.values, TrackedList)


def test_disable_change_tracking_hooks_context_skips_wrapping_and_assignment_hooks() -> None:
    with disable_change_tracking_hooks():
        owner = _Owner(values=[1, 2, 3])
        owner.values = [4, 5, 6]
        assert isinstance(owner.values, list)
        assert not isinstance(owner.values, TrackedList)

    owner.values = [7, 8, 9]
    assert isinstance(owner.values, TrackedList)


def test_tracked_list_does_not_snapshot_for_append(monkeypatch) -> None:
    owner = _Owner()

    calls = {"count": 0}
    original = change_collector.snapshot_list

    def _wrapped(value):
        calls["count"] += 1
        return original(value)

    monkeypatch.setattr(change_collector, "snapshot_list", _wrapped)

    with scoped_change_collection() as collector:
        for i in range(500):
            owner.values.append(i)
        change_set = collector.snapshot()

    assert calls["count"] == 0
    assert change_set.list_baseline == {}
    assert owner.id in change_set.touched_ids
    assert change_set.list_fields_by_id.get(owner.id) == {"values"}


def test_tracked_list_skips_snapshot_when_filtered(monkeypatch) -> None:
    owner = _Owner()

    calls = {"count": 0}
    original = change_collector.snapshot_list

    def _wrapped(value):
        calls["count"] += 1
        return original(value)

    monkeypatch.setattr(change_collector, "snapshot_list", _wrapped)

    with scoped_change_collection(should_track=lambda _: False) as collector:
        for i in range(200):
            owner.values.append(i)
        change_set = collector.snapshot()

    assert calls["count"] == 0
    assert change_set.list_baseline == {}
    assert change_set.touched_ids == frozenset()
    assert change_set.list_fields_by_id == {}


def test_tracked_list_delta_sets_cancel_add_then_remove() -> None:
    owner = _UuidOwner()
    u1 = uuid4()
    u2 = uuid4()

    with scoped_change_collection() as collector:
        owner.values.append(u1)
        owner.values.append(u2)
        owner.values.remove(u1)
        change_set = collector.snapshot()

    key = (owner.id, "values")
    assert change_set.list_added.get(key) == {u2}
    assert change_set.list_removed.get(key) in (None, set())


def test_tracked_list_delta_sets_record_remove_of_baseline_member() -> None:
    owner = _UuidOwner()
    u1 = uuid4()
    u2 = uuid4()
    owner.values.extend([u1, u2])

    with scoped_change_collection() as collector:
        owner.values.remove(u1)
        change_set = collector.snapshot()

    key = (owner.id, "values")
    assert change_set.list_removed.get(key) == {u1}
    assert change_set.list_added.get(key) in (None, set())


def test_tracked_list_uuid_append_records_deltas_without_snapshot(monkeypatch) -> None:
    owner = _UuidOwner()
    u1 = uuid4()

    def _boom(_value):
        raise AssertionError("snapshot_list should not be called for list membership deltas")

    monkeypatch.setattr(change_collector, "snapshot_list", _boom)

    with scoped_change_collection() as collector:
        owner.values.append(u1)
        change_set = collector.snapshot()

    key = (owner.id, "values")
    assert change_set.list_added.get(key) == {u1}


def test_tracked_list_iadd_records_deltas_without_snapshot(monkeypatch) -> None:
    owner = _UuidOwner()
    u1 = uuid4()

    def _boom(_value):
        raise AssertionError("snapshot_list should not be called for list membership deltas")

    monkeypatch.setattr(change_collector, "snapshot_list", _boom)

    with scoped_change_collection() as collector:
        owner.values += [u1]
        change_set = collector.snapshot()

    key = (owner.id, "values")
    assert change_set.list_added.get(key) == {u1}


def test_tracked_list_imul_clear_records_removes_without_snapshot(monkeypatch) -> None:
    owner = _UuidOwner()
    u1 = uuid4()
    u2 = uuid4()
    owner.values.extend([u1, u2])

    def _boom(_value):
        raise AssertionError("snapshot_list should not be called for list membership deltas")

    monkeypatch.setattr(change_collector, "snapshot_list", _boom)

    with scoped_change_collection() as collector:
        owner.values *= 0
        change_set = collector.snapshot()

    key = (owner.id, "values")
    assert change_set.list_removed.get(key) == {u1, u2}
    assert change_set.list_added.get(key) in (None, set())


def test_tracked_list_uuid_fuzz_delta_sets_match_membership_diff(monkeypatch) -> None:
    owner = _UuidOwner()
    initial = [uuid4() for _ in range(8)]
    owner.values.extend(initial)

    baseline = set(initial)

    def _boom(_value):
        raise AssertionError("snapshot_list should not be called for TrackedList mutation fuzzing")

    monkeypatch.setattr(change_collector, "snapshot_list", _boom)

    rng = random.Random(1337)
    shadow = list(owner.values)
    pool = [uuid4() for _ in range(8)]
    max_len = 200

    with scoped_change_collection() as collector:
        for _ in range(250):
            if len(shadow) > max_len:
                index = rng.randrange(0, len(shadow))
                del owner.values[index]
                del shadow[index]
                continue

            op = rng.choice(
                [
                    "append",
                    "insert",
                    "remove",
                    "pop",
                    "setitem",
                    "delitem",
                    "iadd",
                    "imul2",
                ]
            )

            if op == "append":
                if len(shadow) >= max_len:
                    continue
                value = rng.choice(shadow) if shadow and rng.random() < 0.3 else rng.choice(pool)
                owner.values.append(value)
                shadow.append(value)
                continue

            if op == "insert":
                if len(shadow) >= max_len:
                    continue
                value = rng.choice(shadow) if shadow and rng.random() < 0.3 else rng.choice(pool)
                index = rng.randrange(0, len(shadow) + 1) if shadow else 0
                owner.values.insert(index, value)
                shadow.insert(index, value)
                continue

            if op == "remove":
                if not shadow:
                    continue
                value = rng.choice(shadow)
                owner.values.remove(value)
                shadow.remove(value)
                continue

            if op == "pop":
                if not shadow:
                    continue
                index = rng.randrange(-len(shadow), len(shadow))
                out1 = owner.values.pop(index)
                out2 = shadow.pop(index)
                assert out1 == out2
                continue

            if op == "setitem":
                if not shadow:
                    continue
                index = rng.randrange(0, len(shadow))
                value = rng.choice(shadow) if rng.random() < 0.2 else rng.choice(pool)
                owner.values[index] = value
                shadow[index] = value
                continue

            if op == "delitem":
                if not shadow:
                    continue
                index = rng.randrange(0, len(shadow))
                del owner.values[index]
                del shadow[index]
                continue

            if op == "iadd":
                remaining = max_len - len(shadow)
                if remaining <= 0:
                    continue
                to_add = [rng.choice(pool) for _ in range(rng.randrange(0, min(4, remaining) + 1))]
                owner.values += to_add
                shadow += to_add
                continue

            if op == "imul2":
                if not shadow:
                    continue
                if len(shadow) > max_len // 2:
                    continue
                owner.values *= 2
                shadow *= 2
                continue

        change_set = collector.snapshot()

    final = set(shadow)
    expected_added = final - baseline
    expected_removed = baseline - final

    key = (owner.id, "values")
    assert change_set.list_added.get(key, set()) == expected_added
    assert change_set.list_removed.get(key, set()) == expected_removed
