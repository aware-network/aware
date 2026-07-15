from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.handlers.impl.config import (
    object_config_graph as object_config_graph_handler,
)
from aware_meta.handlers.impl.config import (
    object_config_graph_binding as object_config_graph_binding_handler,
)
from aware_meta.handlers.impl.config import (
    object_config_graph_binding_class as object_config_graph_binding_class_handler,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_binding import (
    ObjectConfigGraphBinding,
)
from aware_meta_ontology.graph.config.object_config_graph_binding_class import (
    ObjectConfigGraphBindingClass,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_binding_class_id,
    stable_object_config_graph_binding_id,
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


def _make_graph(graph_id: UUID, *, fqn_prefix: str) -> ObjectConfigGraph:
    return ObjectConfigGraph(
        id=graph_id,
        name=fqn_prefix,
        hash=f"{fqn_prefix}-hash",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
    )


@pytest.mark.asyncio
async def test_object_config_graph_binding_build_is_idempotent(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_config_graph_binding_handler,
        "current_handler_session",
        lambda: session,
    )

    object_config_graph_id = uuid4()
    target_object_config_graph_id = uuid4()
    target_graph = _make_graph(target_object_config_graph_id, fqn_prefix="aware_target")
    session.put(target_graph)

    created = await object_config_graph_binding_handler.build_via_object_config_graph(
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    expected_id = stable_object_config_graph_binding_id(
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    assert created.id == expected_id
    session.put(created)

    created_again = (
        await object_config_graph_binding_handler.build_via_object_config_graph(
            object_config_graph_id=object_config_graph_id,
            target_object_config_graph_id=target_object_config_graph_id,
        )
    )
    assert created_again is created


@pytest.mark.asyncio
async def test_object_config_graph_binding_build_rejects_payload_mismatch(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_config_graph_binding_handler,
        "current_handler_session",
        lambda: session,
    )

    object_config_graph_id = uuid4()
    target_object_config_graph_id = uuid4()
    target_graph = _make_graph(target_object_config_graph_id, fqn_prefix="aware_target")
    session.put(target_graph)
    expected_id = stable_object_config_graph_binding_id(
        object_config_graph_id=object_config_graph_id,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    session.put(
        ObjectConfigGraphBinding(
            id=expected_id,
            target_object_config_graph=target_graph,
            object_config_graph_id=object_config_graph_id,
            target_object_config_graph_id=uuid4(),
        )
    )

    with pytest.raises(RuntimeError, match="payload mismatch"):
        await object_config_graph_binding_handler.build_via_object_config_graph(
            object_config_graph_id=object_config_graph_id,
            target_object_config_graph_id=target_object_config_graph_id,
        )


@pytest.mark.asyncio
async def test_object_config_graph_create_object_config_graph_binding_appends_once(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_config_graph_binding_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        object_config_graph_handler.ObjectConfigGraphBinding,
        "build_via_object_config_graph",
        object_config_graph_binding_handler.build_via_object_config_graph,
    )

    graph = ObjectConfigGraph(
        id=uuid4(),
        name="Meta",
        hash="hash",
        fqn_prefix="aware_meta_test",
        language=CodeLanguage.aware,
    )
    target_object_config_graph_id = uuid4()
    target_graph = _make_graph(target_object_config_graph_id, fqn_prefix="aware_target")
    session.put(target_graph)

    created = await object_config_graph_handler.create_object_config_graph_binding(
        object_config_graph=graph,
        target_object_config_graph_id=target_object_config_graph_id,
    )
    session.put(created)

    created_again = (
        await object_config_graph_handler.create_object_config_graph_binding(
            object_config_graph=graph,
            target_object_config_graph_id=target_object_config_graph_id,
        )
    )

    assert created_again.id == created.id
    assert len(graph.object_config_graph_bindings) == 1


@pytest.mark.asyncio
async def test_object_config_graph_binding_class_build_is_idempotent(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_config_graph_binding_class_handler,
        "current_handler_session",
        lambda: session,
    )

    object_config_graph_binding_id = uuid4()
    source_class_id = uuid4()
    target_class_id = uuid4()
    target_attribute_id = uuid4()
    source_attr_id = uuid4()
    name = "door_by_label"

    created = await object_config_graph_binding_class_handler.build_via_object_config_graph_binding(
        object_config_graph_binding_id=object_config_graph_binding_id,
        name=name,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
        source_attr_id=source_attr_id,
    )
    expected_id = stable_object_config_graph_binding_class_id(
        object_config_graph_binding_id=object_config_graph_binding_id,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
    )
    assert created.id == expected_id
    assert created.name == name
    session.put(created)

    created_again = await object_config_graph_binding_class_handler.build_via_object_config_graph_binding(
        object_config_graph_binding_id=object_config_graph_binding_id,
        name=name,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
        source_attr_id=source_attr_id,
    )
    assert created_again is created


@pytest.mark.asyncio
async def test_object_config_graph_binding_class_build_rejects_source_attr_mismatch(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_config_graph_binding_class_handler,
        "current_handler_session",
        lambda: session,
    )

    object_config_graph_binding_id = uuid4()
    source_class_id = uuid4()
    target_class_id = uuid4()
    target_attribute_id = uuid4()
    name = "door_by_label"
    expected_id = stable_object_config_graph_binding_class_id(
        object_config_graph_binding_id=object_config_graph_binding_id,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
    )
    session.put(
        ObjectConfigGraphBindingClass(
            id=expected_id,
            object_config_graph_binding_id=object_config_graph_binding_id,
            name=name,
            source_class_id=source_class_id,
            source_attr_id=uuid4(),
            target_class_id=target_class_id,
            target_attribute_id=target_attribute_id,
        )
    )

    with pytest.raises(RuntimeError, match="payload mismatch"):
        await object_config_graph_binding_class_handler.build_via_object_config_graph_binding(
            object_config_graph_binding_id=object_config_graph_binding_id,
            name=name,
            source_class_id=source_class_id,
            target_class_id=target_class_id,
            target_attribute_id=target_attribute_id,
            source_attr_id=None,
        )


@pytest.mark.asyncio
async def test_object_config_graph_binding_create_class_appends_once(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_config_graph_binding_class_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        object_config_graph_binding_handler.ObjectConfigGraphBindingClass,
        "build_via_object_config_graph_binding",
        object_config_graph_binding_class_handler.build_via_object_config_graph_binding,
    )

    target_graph = _make_graph(uuid4(), fqn_prefix="aware_target")
    binding = ObjectConfigGraphBinding(
        id=uuid4(),
        target_object_config_graph=target_graph,
        object_config_graph_id=uuid4(),
        target_object_config_graph_id=target_graph.id,
    )
    source_class_id = uuid4()
    target_class_id = uuid4()
    target_attribute_id = uuid4()
    source_attr_id = uuid4()
    name = "door_by_label"

    created = await object_config_graph_binding_handler.create_class(
        object_config_graph_binding=binding,
        name=name,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
        source_attr_id=source_attr_id,
    )
    session.put(created)

    created_again = await object_config_graph_binding_handler.create_class(
        object_config_graph_binding=binding,
        name=name,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        target_attribute_id=target_attribute_id,
        source_attr_id=source_attr_id,
    )

    assert created_again.id == created.id
    assert created_again.name == name
    assert len(binding.object_config_graph_binding_classes) == 1
