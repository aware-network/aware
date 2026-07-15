from __future__ import annotations

from uuid import uuid4

import pytest

from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import scoped_change_collection
from aware_orm.session.execution_guard import is_read_only_scope, scoped_execution_mode


class Thing(BaseORMModel):
    value: int = 0


def test_read_only_barrier_blocks_nested_write_invocations_inside_write_scope() -> None:
    with scoped_execution_mode("write"):
        assert not is_read_only_scope()
        with scoped_execution_mode("read"):
            assert is_read_only_scope()
            with pytest.raises(PermissionError):
                with scoped_execution_mode("write"):
                    pass


def test_read_only_barrier_blocks_mutation_inside_write_scope() -> None:
    with disable_autobind():
        obj = Thing(id=uuid4(), value=0)

    with scoped_execution_mode("write"):
        with scoped_execution_mode("read"):
            with scoped_change_collection():
                with pytest.raises(PermissionError):
                    obj.value = 1


def test_write_scope_allows_mutation_and_collects_changes() -> None:
    with disable_autobind():
        obj = Thing(id=uuid4(), value=0)

    with scoped_execution_mode("write"):
        with scoped_change_collection() as collector:
            obj.value = 1
            changes = collector.snapshot()

    assert obj.id in changes.touched_ids
