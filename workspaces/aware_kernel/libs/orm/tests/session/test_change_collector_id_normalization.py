from __future__ import annotations

from uuid import uuid4

from pydantic import Field

from aware_orm.models.orm_model import ORMModel
from aware_orm.session.change_collector import scoped_change_collection


class _Child(ORMModel):
    name: str | None = None


class _Parent(ORMModel):
    child: _Child | None = Field(default=None, exclude=True)


def test_snapshot_normalizes_created_object_ids_after_stabilization() -> None:
    provisional_child_id = uuid4()
    stable_child_id = uuid4()

    parent = _Parent()

    with scoped_change_collection() as collector:
        child = _Child(id=provisional_child_id, name="child")
        collector.record_create(child)
        child.id = stable_child_id
        parent.child = child
        change_set = collector.snapshot()

    assert provisional_child_id not in change_set.created_ids
    assert stable_child_id in change_set.created_ids
    assert provisional_child_id not in change_set.touched_ids
    assert stable_child_id in change_set.touched_ids
    assert provisional_child_id not in change_set.objects_by_id
    assert change_set.objects_by_id[stable_child_id] is child
    assert parent.id in change_set.touched_ids


def test_snapshot_clears_deleted_id_when_same_id_is_recreated() -> None:
    stable_child_id = uuid4()

    with scoped_change_collection() as collector:
        original = _Child(id=stable_child_id, name="old")
        collector.record_delete(original)

        replacement = _Child(id=stable_child_id, name="new")
        collector.record_create(replacement)
        change_set = collector.snapshot()

    assert stable_child_id in change_set.created_ids
    assert stable_child_id not in change_set.deleted_ids
    assert change_set.objects_by_id[stable_child_id] is replacement
