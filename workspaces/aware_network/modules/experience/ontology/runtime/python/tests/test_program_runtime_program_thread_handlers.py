from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_experience.handlers.impl.thread import thread_program as thread_program_impl
from aware_experience_ontology.program.program import Program


class _Session:
    def __init__(self) -> None:
        self._instances: dict[tuple[type, UUID], object] = {}

    def imap_get(self, cls, object_id):
        return self._instances.get((cls, object_id))

    def imap_add(self, obj: object) -> None:
        object_id = getattr(obj, "id")
        self._instances[(obj.__class__, object_id)] = obj

    def put(self, obj: object) -> None:
        self.imap_add(obj)


@pytest.mark.asyncio
async def test_thread_program_create_is_deterministic_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        thread_program_impl,
        "current_handler_session",
        lambda _session=session: _session,
    )
    thread_id = uuid5(NAMESPACE_URL, "aware://tests/experience/thread-id")
    program_id = uuid5(NAMESPACE_URL, "aware://tests/experience/program-id")

    created = await thread_program_impl.create(
        thread_id=thread_id,
        program_id=program_id,
        key="main",
        position=0,
        is_default=False,
    )
    session.put(created)
    replayed = await thread_program_impl.create(
        thread_id=thread_id,
        program_id=program_id,
        key="main",
        position=0,
        is_default=False,
    )

    assert replayed.id == created.id
    assert replayed.thread_id == thread_id
    assert replayed.program_id == program_id

    with pytest.raises(
        RuntimeError,
        match="ThreadProgram.create payload mismatch for existing association",
    ):
        await thread_program_impl.create(
            thread_id=thread_id,
            program_id=program_id,
            key="secondary",
            position=0,
            is_default=False,
        )


def test_program_no_longer_constructs_thread_program() -> None:
    assert not hasattr(Program, "attach_thread")
    assert "thread_bindings" not in Program.model_fields
