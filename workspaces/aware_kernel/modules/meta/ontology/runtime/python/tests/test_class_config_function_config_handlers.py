from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_meta.handlers.impl.class_ import class_config as class_config_handler
from aware_meta.handlers.impl.class_ import (
    class_config_function_config as class_config_function_config_handler,
)
from aware_meta.handlers.impl.function import function_config as function_config_handler
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.stable_ids import (
    stable_class_config_function_config_id,
    stable_function_config_id,
)


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, UUID(str(value_id))))


@pytest.mark.asyncio
async def test_class_config_create_function_config_returns_standalone_function_and_binds_edge(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        function_config_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        class_config_function_config_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        class_config_handler.ClassConfigFunctionConfig,
        "create_via_class_config",
        class_config_function_config_handler.create_via_class_config,
    )

    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware.meta.test.default.default.User",
        name="User",
    )
    session.put(class_config)

    created = await class_config_handler.create_function_config(
        class_config=class_config,
        name="build",
        description="Create user",
        verb="construct",
        is_async=False,
        kind=FunctionKind.class_,
        is_public=True,
        is_constructor=True,
        position=0,
    )

    expected_function_id = stable_function_config_id(
        owner_key=class_config.class_fqn,
        name="build",
        kind=FunctionKind.class_.value,
    )
    assert created.id == expected_function_id
    assert len(class_config.class_config_function_configs) == 1
    edge = class_config.class_config_function_configs[0]
    assert edge.function_config is created
    assert edge.function_config_id == created.id
    assert edge.id == stable_class_config_function_config_id(
        class_config_id=class_config.id,
        function_config_id=created.id,
    )

    session.put(created)
    session.put(edge)

    created_again = await class_config_handler.create_function_config(
        class_config=class_config,
        name="build",
        description="Create user",
        verb="construct",
        is_async=False,
        kind=FunctionKind.class_,
        is_public=True,
        is_constructor=True,
        position=0,
    )

    assert created_again is created
    assert len(class_config.class_config_function_configs) == 1
