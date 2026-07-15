from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_environment.handlers.impl.thread import (
    thread as thread_impl,
)
from aware_environment.handlers.impl.thread import (
    thread_layout as thread_layout_impl,
)
from aware_environment_ontology.stable_ids import (
    stable_process_id,
    stable_thread_id,
    stable_thread_layout_id,
)
from aware_environment_ontology.thread.thread import Thread
from aware_environment_ontology.thread.thread_layout import ThreadLayout


class _Session:
    def __init__(self) -> None:
        self._instances: dict[tuple[type, UUID], object] = {}

    def imap_get(self, cls, object_id):
        return self._instances.get((cls, object_id))

    def put(self, obj: object) -> None:
        object_id = getattr(obj, "id")
        self._instances[(obj.__class__, object_id)] = obj


def _test_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware://tests/environment/thread-layout/{key}")


def _process_id(key: str) -> UUID:
    return stable_process_id(
        environment_profile_id=_test_uuid(f"{key}/environment-profile"),
        process_config_id=_test_uuid(f"{key}/process-config"),
        key=key,
    )


def _thread_ids(key: str) -> tuple[UUID, UUID, UUID]:
    process_id = _process_id(f"{key}/process")
    thread_config_id = _test_uuid(f"{key}/thread-config")
    thread_id = stable_thread_id(
        thread_config_id=thread_config_id,
        process_id=process_id,
        key=key,
    )
    return process_id, thread_config_id, thread_id


@pytest.mark.asyncio
async def test_thread_layout_create_via_thread_is_deterministic_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        thread_layout_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )

    _process_id, _thread_config_id, thread_id = _thread_ids("create/thread")
    layout_id = _test_uuid("create/layout")
    expected_assoc_id = stable_thread_layout_id(
        thread_id=thread_id, layout_id=layout_id
    )

    created = await thread_layout_impl.create_via_thread(
        thread_id=thread_id,
        layout_id=layout_id,
        key=" main ",
    )
    session.put(created)
    replayed = await thread_layout_impl.create_via_thread(
        thread_id=thread_id,
        layout_id=layout_id,
        key="main",
    )

    assert created.id == expected_assoc_id
    assert created.thread_id == thread_id
    assert created.layout_id == layout_id
    assert created.key == "main"
    assert replayed is created


@pytest.mark.asyncio
async def test_thread_layout_has_no_active_flag_or_setter() -> None:
    _process_id, _thread_config_id, thread_id = _thread_ids("set-active/thread")
    layout_id = _test_uuid("set-active/layout")
    assoc = ThreadLayout(
        id=stable_thread_layout_id(thread_id=thread_id, layout_id=layout_id),
        thread_id=thread_id,
        layout_id=layout_id,
    )

    assert not hasattr(assoc, "is_active")
    assert not hasattr(thread_layout_impl, "set_active")


@pytest.mark.asyncio
async def test_thread_add_layout_attaches_once_for_same_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process_id, thread_config_id, thread_id = _thread_ids("add/thread")
    layout_id = _test_uuid("add/layout")
    assoc_id = stable_thread_layout_id(thread_id=thread_id, layout_id=layout_id)
    thread = Thread(
        id=thread_id,
        key="thread",
        process_id=process_id,
        thread_config_id=thread_config_id,
    )
    create_calls: list[tuple[UUID, UUID, str | None]] = []

    created_assoc = ThreadLayout(
        id=assoc_id,
        thread_id=thread_id,
        layout_id=layout_id,
        key="main",
    )

    async def _fake_create_via_thread(
        cls,
        *,
        thread_id: UUID,
        layout_id: UUID,
        key: str | None = None,
    ) -> ThreadLayout:
        _ = cls
        create_calls.append((thread_id, layout_id, key))
        return created_assoc

    monkeypatch.setattr(
        thread_impl.ThreadLayout,
        "create_via_thread",
        classmethod(_fake_create_via_thread),
    )

    first = await thread_impl.add_layout(
        thread=thread, layout_id=layout_id, key=" main "
    )
    replayed = await thread_impl.add_layout(
        thread=thread, layout_id=layout_id, key="secondary"
    )

    assert first.id == assoc_id
    assert replayed.id == assoc_id
    assert len(thread.thread_layouts) == 1
    assert create_calls == [(thread_id, layout_id, "main")]


def test_thread_has_no_active_layout_pointer_or_setter() -> None:
    process_id, thread_config_id, thread_id = _thread_ids("select/thread")
    layout_a_id = _test_uuid("select/layout-a")
    assoc_a = ThreadLayout(
        id=stable_thread_layout_id(thread_id=thread_id, layout_id=layout_a_id),
        thread_id=thread_id,
        layout_id=layout_a_id,
    )
    thread = Thread(
        id=thread_id,
        key="thread",
        process_id=process_id,
        thread_config_id=thread_config_id,
        thread_layouts=[assoc_a],
    )

    assert not hasattr(thread, "active_thread_layout")
    assert not hasattr(thread, "active_thread_layout_id")
    assert not hasattr(thread_impl, "set_active_layout")
