from __future__ import annotations

from uuid import UUID, uuid4, uuid5

import pytest

from aware_experience.handlers.impl.projection import (
    projection_experience_node_class_identity as class_identity_handler,
)
from aware_experience.handlers.impl.projection import (
    projection_experience_node_class_identity_key_binding as key_binding_handler,
)
from aware_experience.handlers.impl.projection import (
    projection_experience_node_key as node_key_handler,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.stable_ids import NS_EXPERIENCE
from aware_meta_ontology.graph.projection.object_projection_graph_node_key import (
    ObjectProjectionGraphNodeKey,
)


class _ProjectionExperienceNodeKeyShim:
    def __init__(self, **data) -> None:
        for key, value in data.items():
            setattr(self, key, value)


class _ProjectionExperienceNodeClassIdentityKeyBindingShim:
    def __init__(self, **data) -> None:
        for key, value in data.items():
            setattr(self, key, value)


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, UUID(str(value_id))))


def _stable_projection_experience_node_key_id(
    *,
    projection_experience_node_id: UUID,
    object_projection_graph_node_key_id: UUID,
) -> UUID:
    return uuid5(
        NS_EXPERIENCE,
        f"aware:projection_experience_node_key:{projection_experience_node_id}:{object_projection_graph_node_key_id}",
    )


def _stable_projection_experience_node_class_identity_key_binding_id(
    *,
    projection_experience_node_class_identity_id: UUID,
    projection_experience_node_key_id: UUID,
) -> UUID:
    return uuid5(
        NS_EXPERIENCE,
        "aware:projection_experience_node_class_identity_key_binding:"
        f"{projection_experience_node_class_identity_id}:{projection_experience_node_key_id}",
    )


def _projection_experience_node(
    *, node_id: UUID, object_projection_graph_node_id: UUID
) -> ProjectionExperienceNode:
    return ProjectionExperienceNode.model_construct(
        id=node_id,
        projection_experience_id=uuid4(),
        object_projection_graph_node_id=object_projection_graph_node_id,
        key="door",
        projection_experience_node_identities=[],
        projection_experience_node_keys=[],
    )


def _object_projection_graph_node_key(
    *,
    key_id: UUID,
    object_projection_graph_node_id: UUID,
) -> ObjectProjectionGraphNodeKey:
    return ObjectProjectionGraphNodeKey.model_construct(
        id=key_id,
        object_projection_graph_node_id=object_projection_graph_node_id,
        object_config_graph_binding_class_id=uuid4(),
        key="door_by_label",
        position=0,
        required=True,
    )


def _projection_experience_node_identity(
    *,
    node_identity_id: UUID,
    projection_experience_node_id: UUID,
) -> ProjectionExperienceNodeIdentity:
    return ProjectionExperienceNodeIdentity.model_construct(
        id=node_identity_id,
        projection_experience_node_id=projection_experience_node_id,
        key="front_door",
    )


def _projection_experience_node_class_identity(
    *,
    class_identity_id: UUID,
    node_identity_id: UUID,
) -> ProjectionExperienceNodeClassIdentity:
    return ProjectionExperienceNodeClassIdentity.model_construct(
        id=class_identity_id,
        projection_experience_oigi_id=uuid4(),
        projection_experience_node_identity_id=node_identity_id,
        class_instance_identity_id=uuid4(),
        key="front_door",
        key_bindings=[],
    )


def _install_projection_key_shims(monkeypatch) -> None:
    monkeypatch.setattr(
        node_key_handler,
        "ProjectionExperienceNodeKey",
        _ProjectionExperienceNodeKeyShim,
    )
    monkeypatch.setattr(
        class_identity_handler,
        "ProjectionExperienceNodeKey",
        _ProjectionExperienceNodeKeyShim,
    )
    monkeypatch.setattr(
        key_binding_handler,
        "ProjectionExperienceNodeKey",
        _ProjectionExperienceNodeKeyShim,
    )
    monkeypatch.setattr(
        class_identity_handler,
        "ProjectionExperienceNodeClassIdentityKeyBinding",
        _ProjectionExperienceNodeClassIdentityKeyBindingShim,
    )
    monkeypatch.setattr(
        key_binding_handler,
        "ProjectionExperienceNodeClassIdentityKeyBinding",
        _ProjectionExperienceNodeClassIdentityKeyBindingShim,
    )


@pytest.mark.asyncio
async def test_projection_experience_node_key_consumes_meta_projection_key(
    monkeypatch,
) -> None:
    session = _Session()
    _install_projection_key_shims(monkeypatch)
    monkeypatch.setattr(node_key_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        node_key_handler,
        "stable_projection_experience_node_key_id",
        _stable_projection_experience_node_key_id,
    )

    projection_experience_node_id = uuid4()
    object_projection_graph_node_id = uuid4()
    object_projection_graph_node_key_id = uuid4()

    projection_experience_node = _projection_experience_node(
        node_id=projection_experience_node_id,
        object_projection_graph_node_id=object_projection_graph_node_id,
    )
    meta_key = _object_projection_graph_node_key(
        key_id=object_projection_graph_node_key_id,
        object_projection_graph_node_id=object_projection_graph_node_id,
    )
    session.put(projection_experience_node)
    session.put(meta_key)

    created = await node_key_handler.build_via_projection_experience_node(
        projection_experience_node_id=projection_experience_node_id,
        object_projection_graph_node_key_id=object_projection_graph_node_key_id,
    )
    expected_id = _stable_projection_experience_node_key_id(
        projection_experience_node_id=projection_experience_node_id,
        object_projection_graph_node_key_id=object_projection_graph_node_key_id,
    )
    assert created.id == expected_id
    assert (
        created.object_projection_graph_node_key_id
        == object_projection_graph_node_key_id
    )

    session.put(created)
    created_again = await node_key_handler.build_via_projection_experience_node(
        projection_experience_node_id=projection_experience_node_id,
        object_projection_graph_node_key_id=object_projection_graph_node_key_id,
    )
    assert created_again is created


@pytest.mark.asyncio
async def test_projection_experience_node_key_fails_closed_on_node_mismatch(
    monkeypatch,
) -> None:
    session = _Session()
    _install_projection_key_shims(monkeypatch)
    monkeypatch.setattr(node_key_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        node_key_handler,
        "stable_projection_experience_node_key_id",
        _stable_projection_experience_node_key_id,
    )

    projection_experience_node = _projection_experience_node(
        node_id=uuid4(),
        object_projection_graph_node_id=uuid4(),
    )
    meta_key = _object_projection_graph_node_key(
        key_id=uuid4(),
        object_projection_graph_node_id=uuid4(),
    )
    session.put(projection_experience_node)
    session.put(meta_key)

    with pytest.raises(RuntimeError, match="node mismatch"):
        await node_key_handler.build_via_projection_experience_node(
            projection_experience_node_id=projection_experience_node.id,
            object_projection_graph_node_key_id=meta_key.id,
        )


@pytest.mark.asyncio
async def test_projection_experience_node_class_identity_key_binding_is_payload_idempotent(
    monkeypatch,
) -> None:
    session = _Session()
    _install_projection_key_shims(monkeypatch)
    monkeypatch.setattr(node_key_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        class_identity_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(key_binding_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        node_key_handler,
        "stable_projection_experience_node_key_id",
        _stable_projection_experience_node_key_id,
    )
    monkeypatch.setattr(
        key_binding_handler,
        "stable_projection_experience_node_class_identity_key_binding_id",
        _stable_projection_experience_node_class_identity_key_binding_id,
    )
    monkeypatch.setattr(
        class_identity_handler.ProjectionExperienceNodeClassIdentityKeyBinding,
        "build_via_projection_experience_node_class_identity",
        key_binding_handler.build_via_projection_experience_node_class_identity,
        raising=False,
    )

    projection_experience_node = _projection_experience_node(
        node_id=uuid4(),
        object_projection_graph_node_id=uuid4(),
    )
    meta_key = _object_projection_graph_node_key(
        key_id=uuid4(),
        object_projection_graph_node_id=projection_experience_node.object_projection_graph_node_id,
    )
    node_identity = _projection_experience_node_identity(
        node_identity_id=uuid4(),
        projection_experience_node_id=projection_experience_node.id,
    )
    class_identity = _projection_experience_node_class_identity(
        class_identity_id=uuid4(),
        node_identity_id=node_identity.id,
    )

    session.put(projection_experience_node)
    session.put(meta_key)
    session.put(node_identity)
    session.put(class_identity)

    projection_experience_node_key = (
        await node_key_handler.build_via_projection_experience_node(
            projection_experience_node_id=projection_experience_node.id,
            object_projection_graph_node_key_id=meta_key.id,
        )
    )
    session.put(projection_experience_node_key)

    created = await class_identity_handler.add_key_binding(
        projection_experience_node_class_identity=class_identity,
        projection_experience_node_key_id=projection_experience_node_key.id,
        value={"door_label": "front_door"},
    )
    expected_id = _stable_projection_experience_node_class_identity_key_binding_id(
        projection_experience_node_class_identity_id=class_identity.id,
        projection_experience_node_key_id=projection_experience_node_key.id,
    )
    assert created.id == expected_id
    assert created.value == {"door_label": "front_door"}

    session.put(created)
    created_again = await class_identity_handler.add_key_binding(
        projection_experience_node_class_identity=class_identity,
        projection_experience_node_key_id=projection_experience_node_key.id,
        value={"door_label": "front_door"},
    )
    assert created_again is created
    assert len(class_identity.key_bindings) == 1
