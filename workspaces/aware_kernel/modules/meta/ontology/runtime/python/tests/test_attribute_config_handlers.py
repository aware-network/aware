from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_meta.handlers.impl.attribute import (
    attribute_config as attribute_config_handler,
)
from aware_meta.handlers.impl.attribute import (
    attribute_type_descriptor as descriptor_handler,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.enum.enum_config import EnumConfig
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.stable_ids import (
    stable_attribute_config_id,
    stable_attribute_type_descriptor_id,
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


class _Index:
    def __init__(self, *, class_configs_by_id: dict[UUID, ClassConfig]) -> None:
        self.class_configs_by_id = class_configs_by_id


@pytest.mark.asyncio
async def test_attribute_config_create_primitive_materializes_stable_descriptor(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_primitive",
        descriptor_handler.create_primitive,
    )

    created = await attribute_config_handler.create_primitive(
        owner_key="tests.meta.Counter",
        name="value",
        primitive_base_type=CodePrimitiveBaseType.integer,
    )

    assert created.id == stable_attribute_config_id(
        owner_key="tests.meta.Counter", name="value"
    )
    assert created.type_descriptor is not None
    assert created.type_descriptor.kind == AttributeTypeDescriptorKind.primitive
    assert created.type_descriptor.id == stable_attribute_type_descriptor_id(
        kind=AttributeTypeDescriptorKind.primitive.value,
        collection_kind="single",
        entity_id=created.type_descriptor.primitive_config_id,
        child_links_fingerprint="",
    )


@pytest.mark.asyncio
async def test_attribute_config_create_enum_requires_existing_enum(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_enum",
        descriptor_handler.create_enum,
    )

    with pytest.raises(RuntimeError, match="requires existing EnumConfig"):
        await attribute_config_handler.create_enum(
            owner_key="tests.meta.Counter",
            name="status",
            enum_config_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_attribute_config_create_class_requires_existing_class(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_class",
        descriptor_handler.create_class,
    )

    with pytest.raises(RuntimeError, match="requires existing ClassConfig"):
        await attribute_config_handler.create_class(
            owner_key="tests.meta.Counter",
            name="child",
            type_class_config_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_attribute_config_create_enum_materializes_existing_enum(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_enum",
        descriptor_handler.create_enum,
    )

    enum_config = EnumConfig(
        id=uuid4(),
        name="Status",
        enum_fqn="tests.meta.default.default.Status",
    )
    session.put(enum_config)

    created = await attribute_config_handler.create_enum(
        owner_key="tests.meta.Counter",
        name="status",
        enum_config_id=enum_config.id,
    )

    assert created.type_descriptor is not None
    assert created.type_descriptor.kind == AttributeTypeDescriptorKind.enum
    assert created.type_descriptor.enum_config_id == enum_config.id


@pytest.mark.asyncio
async def test_attribute_config_create_class_materializes_existing_class(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_class",
        descriptor_handler.create_class,
    )

    class_config = ClassConfig(
        id=uuid4(),
        name="Child",
        class_fqn="tests.meta.default.default.Child",
    )
    session.put(class_config)

    created = await attribute_config_handler.create_class(
        owner_key="tests.meta.Counter",
        name="child",
        type_class_config_id=class_config.id,
    )

    assert created.type_descriptor is not None
    assert created.type_descriptor.kind == AttributeTypeDescriptorKind.class_
    assert created.type_descriptor.class_config_id == class_config.id


@pytest.mark.asyncio
async def test_attribute_config_create_class_accepts_json_uuid_string(
    monkeypatch,
) -> None:
    session = _Session()
    class_config = ClassConfig(
        id=uuid4(),
        name="Child",
        class_fqn="tests.meta.default.default.Child",
    )
    session.put(class_config)
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_class",
        descriptor_handler.create_class,
    )

    created = await attribute_config_handler.create_class(
        owner_key="tests.meta.Counter",
        name="child",
        type_class_config_id=str(class_config.id),
    )

    assert created.type_descriptor is not None
    assert created.type_descriptor.kind == AttributeTypeDescriptorKind.class_
    assert created.type_descriptor.class_config_id == class_config.id


@pytest.mark.asyncio
async def test_attribute_config_update_class_uses_runtime_index_target(
    monkeypatch,
) -> None:
    session = _Session()
    class_config = ClassConfig(
        id=uuid4(),
        name="Child",
        class_fqn="tests.meta.default.default.Child",
    )
    index = _Index(class_configs_by_id={class_config.id: class_config})
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_index", lambda: index
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(descriptor_handler, "current_handler_index", lambda: index)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_primitive",
        descriptor_handler.create_primitive,
    )
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_class",
        descriptor_handler.create_class,
    )

    attribute_config = await attribute_config_handler.create_primitive(
        owner_key="tests.meta.Counter",
        name="child",
        primitive_base_type=CodePrimitiveBaseType.string,
    )

    await attribute_config_handler.update_class(
        attribute_config=attribute_config,
        type_class_config_id=class_config.id,
        is_required=True,
    )

    assert attribute_config.type_descriptor is not None
    assert attribute_config.type_descriptor.kind == AttributeTypeDescriptorKind.class_
    assert attribute_config.type_descriptor.class_config_id == class_config.id
    assert attribute_config.type_descriptor.class_config is class_config
    assert attribute_config.is_required is True


@pytest.mark.asyncio
async def test_attribute_config_update_class_accepts_json_uuid_string(
    monkeypatch,
) -> None:
    session = _Session()
    class_config = ClassConfig(
        id=uuid4(),
        name="Child",
        class_fqn="tests.meta.default.default.Child",
    )
    index = _Index(class_configs_by_id={class_config.id: class_config})
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        attribute_config_handler, "current_handler_index", lambda: index
    )
    monkeypatch.setattr(descriptor_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(descriptor_handler, "current_handler_index", lambda: index)
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_primitive",
        descriptor_handler.create_primitive,
    )
    monkeypatch.setattr(
        attribute_config_handler.AttributeTypeDescriptor,
        "create_class",
        descriptor_handler.create_class,
    )

    attribute_config = await attribute_config_handler.create_primitive(
        owner_key="tests.meta.Counter",
        name="child",
        primitive_base_type=CodePrimitiveBaseType.string,
    )

    await attribute_config_handler.update_class(
        attribute_config=attribute_config,
        type_class_config_id=str(class_config.id),
        is_required=True,
    )

    assert attribute_config.type_descriptor is not None
    assert attribute_config.type_descriptor.kind == AttributeTypeDescriptorKind.class_
    assert attribute_config.type_descriptor.class_config_id == class_config.id
    assert attribute_config.type_descriptor.class_config is class_config
