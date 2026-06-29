from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_meta.handlers.impl.attribute import (
    attribute_type_descriptor as attribute_type_descriptor_handler,
)
from aware_meta.handlers.impl.attribute import (
    attribute_type_descriptor_link as attribute_type_descriptor_link_handler,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.stable_ids import stable_attribute_type_descriptor_link_id


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
async def test_attribute_type_descriptor_link_build_is_idempotent(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_type_descriptor_link_handler,
        "current_handler_session",
        lambda: session,
    )

    parent_id = uuid4()
    child = AttributeTypeDescriptor(
        id=uuid4(),
        kind=AttributeTypeDescriptorKind.primitive,
    )
    session.put(child)

    created = await attribute_type_descriptor_link_handler.build_via_attribute_type_descriptor(
        attribute_type_descriptor_id=parent_id,
        child_id=child.id,
        role=AttributeTypeDescriptorRole.element,
        position=0,
    )
    expected_id = stable_attribute_type_descriptor_link_id(
        attribute_type_descriptor_id=parent_id,
        child_id=child.id,
        role=AttributeTypeDescriptorRole.element.value,
        position=0,
    )
    assert created.id == expected_id
    assert created.child_id == child.id
    assert created.child is child
    session.put(created)

    created_again = await attribute_type_descriptor_link_handler.build_via_attribute_type_descriptor(
        attribute_type_descriptor_id=parent_id,
        child_id=child.id,
        role=AttributeTypeDescriptorRole.element,
        position=0,
    )
    assert created_again is created


@pytest.mark.asyncio
async def test_attribute_type_descriptor_link_build_rejects_missing_child(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_type_descriptor_link_handler,
        "current_handler_session",
        lambda: session,
    )

    with pytest.raises(RuntimeError, match="requires existing child descriptor"):
        await attribute_type_descriptor_link_handler.build_via_attribute_type_descriptor(
            attribute_type_descriptor_id=uuid4(),
            child_id=uuid4(),
            role=AttributeTypeDescriptorRole.element,
            position=0,
        )


@pytest.mark.asyncio
async def test_attribute_type_descriptor_create_child_link_appends_once(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_type_descriptor_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        attribute_type_descriptor_link_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        attribute_type_descriptor_handler.AttributeTypeDescriptorLink,
        "build_via_attribute_type_descriptor",
        attribute_type_descriptor_link_handler.build_via_attribute_type_descriptor,
    )

    parent = AttributeTypeDescriptor(
        id=uuid4(),
        kind=AttributeTypeDescriptorKind.collection,
        child_links=[],
    )
    child = AttributeTypeDescriptor(
        id=uuid4(),
        kind=AttributeTypeDescriptorKind.primitive,
    )
    session.put(parent)
    session.put(child)

    created = await attribute_type_descriptor_handler.create_child_link(
        attribute_type_descriptor=parent,
        child_id=child.id,
        role=AttributeTypeDescriptorRole.element,
        position=0,
    )
    session.put(created)

    created_again = await attribute_type_descriptor_handler.create_child_link(
        attribute_type_descriptor=parent,
        child_id=child.id,
        role=AttributeTypeDescriptorRole.element,
        position=0,
    )

    assert created_again.id == created.id
    assert len(parent.child_links) == 1
    assert parent.child_links[0].child is child


@pytest.mark.asyncio
async def test_attribute_type_descriptor_link_build_rejects_payload_mismatch(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_type_descriptor_link_handler,
        "current_handler_session",
        lambda: session,
    )

    parent_id = uuid4()
    child = AttributeTypeDescriptor(
        id=uuid4(),
        kind=AttributeTypeDescriptorKind.primitive,
    )
    session.put(child)
    stable_id = stable_attribute_type_descriptor_link_id(
        attribute_type_descriptor_id=parent_id,
        child_id=child.id,
        role=AttributeTypeDescriptorRole.element.value,
        position=0,
    )
    session.put(
        AttributeTypeDescriptorLink(
            id=stable_id,
            attribute_type_descriptor_id=parent_id,
            child=child,
            child_id=child.id,
            role=AttributeTypeDescriptorRole.element,
            position=1,
        )
    )

    with pytest.raises(RuntimeError, match="payload mismatch for existing link"):
        await attribute_type_descriptor_link_handler.build_via_attribute_type_descriptor(
            attribute_type_descriptor_id=parent_id,
            child_id=child.id,
            role=AttributeTypeDescriptorRole.element,
            position=0,
        )
