from __future__ import annotations

from importlib import import_module
from typing import Protocol, cast
from uuid import UUID

from aware_history_ontology.stable_ids import (
    stable_branch_id as stable_history_branch_id,
)


class _EnvironmentBranchingModule(Protocol):
    def normalize_branch_tail(self, *, tail: str | None) -> str: ...

    def resolve_environment_thread_branch_key(
        self, *, environment_id: UUID, thread_id: UUID, tail: str | None = None
    ) -> str: ...

    def resolve_environment_turn_branch_key(
        self, *, environment_id: UUID, turn_id: UUID
    ) -> str: ...

    def stable_environment_thread_branch_id(
        self, *, environment_id: UUID, thread_id: UUID, tail: str | None = None
    ) -> UUID: ...

    def stable_environment_turn_branch_id(
        self, *, environment_id: UUID, turn_id: UUID
    ) -> UUID: ...


def _module() -> _EnvironmentBranchingModule:
    return cast(
        _EnvironmentBranchingModule,
        cast(object, import_module("aware_environment.branching")),
    )


def test_environment_thread_branch_key_is_canonical_and_normalized() -> None:
    module = _module()
    environment_id = UUID("00000000-0000-0000-0000-000000000123")
    thread_id = UUID("00000000-0000-0000-0000-000000000456")
    assert module.normalize_branch_tail(tail=None) == "default"
    assert module.normalize_branch_tail(tail="  DEV  ") == "dev"
    assert (
        module.resolve_environment_thread_branch_key(
            environment_id=environment_id,
            thread_id=thread_id,
            tail="  DEV  ",
        )
        == f"env:{environment_id}:thread:{thread_id}:key:dev"
    )


def test_environment_thread_branch_id_delegates_to_history_identity_primitive() -> None:
    module = _module()
    environment_id = UUID("00000000-0000-0000-0000-000000000111")
    thread_id = UUID("00000000-0000-0000-0000-000000000222")
    key = module.resolve_environment_thread_branch_key(
        environment_id=environment_id,
        thread_id=thread_id,
        tail="provider",
    )
    assert module.stable_environment_thread_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
        tail="provider",
    ) == stable_history_branch_id(key=key)


def test_environment_turn_branch_key_is_canonical() -> None:
    module = _module()
    environment_id = UUID("00000000-0000-0000-0000-000000000abc")
    turn_id = UUID("00000000-0000-0000-0000-000000000def")
    assert (
        module.resolve_environment_turn_branch_key(
            environment_id=environment_id,
            turn_id=turn_id,
        )
        == f"env:{environment_id}:turn:{turn_id}"
    )


def test_environment_turn_branch_id_delegates_to_history_identity_primitive() -> None:
    module = _module()
    environment_id = UUID("00000000-0000-0000-0000-000000000aaa")
    turn_id = UUID("00000000-0000-0000-0000-000000000bbb")
    key = module.resolve_environment_turn_branch_key(
        environment_id=environment_id,
        turn_id=turn_id,
    )
    assert module.stable_environment_turn_branch_id(
        environment_id=environment_id,
        turn_id=turn_id,
    ) == stable_history_branch_id(key=key)
