from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.handlers.impl.class_.class_config import (
    update_config as _update_class_config_impl,
    remove_relationship_config as _remove_relationship_config_impl,
)
from aware_meta.handlers.impl.class_.class_config_attribute_config import (
    update_config as _update_class_config_attribute_config_impl,
)
from aware_meta.handlers.impl.class_.class_config_function_config import (
    update_config as _update_class_config_function_config_impl,
)
from aware_meta.handlers.impl.class_.class_config_relationship import (
    update_config as _update_relationship_config_impl,
)
from aware_meta.handlers.impl.function.function_config import (
    update_config as _update_function_config_impl,
)
from aware_meta.handlers.impl.function.function_config_attribute_config import (
    update_config as _update_function_config_attribute_config_impl,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import (
    ClassIdentityMode,
    ClassValueMode,
)
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionIdentityKeyOrigin,
    FunctionKind,
)


def _test_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware:test:meta-provider-delta:{key}")


@pytest.mark.asyncio
async def test_class_config_update_config_mutates_only_class() -> None:
    class_id = _test_uuid("handler-update-class")
    class_config = ClassConfig(
        id=class_id,
        class_fqn="aware_demo.default.home.Room",
        name="Room",
        description="A room.",
        is_base=True,
        is_edge=False,
        value_mode=ClassValueMode.graph_ref,
        identity_mode=ClassIdentityMode.contained,
    )

    await _update_class_config_impl(
        class_config,
        description="A room people can occupy.",
        is_base=False,
        is_edge=True,
        value_mode=ClassValueMode.inline_value,
        identity_mode=ClassIdentityMode.standalone,
    )

    assert class_config.id == class_id
    assert class_config.class_fqn == "aware_demo.default.home.Room"
    assert class_config.name == "Room"
    assert class_config.description == "A room people can occupy."
    assert class_config.is_base is False
    assert class_config.is_edge is True
    assert class_config.value_mode is ClassValueMode.inline_value
    assert class_config.identity_mode is ClassIdentityMode.standalone


@pytest.mark.asyncio
async def test_function_config_update_config_mutates_only_function() -> None:
    function_id = _test_uuid("handler-update-function")
    function_config = FunctionConfig(
        id=function_id,
        owner_key="aware_demo.default.home.Room",
        name="rename",
        description="Rename the room.",
        verb=None,
        is_async=False,
        kind=FunctionKind.instance,
    )

    await _update_function_config_impl(
        function_config,
        description="Rename the room for people.",
        verb="rename",
        is_async=True,
    )

    assert function_config.id == function_id
    assert function_config.owner_key == "aware_demo.default.home.Room"
    assert function_config.name == "rename"
    assert function_config.kind is FunctionKind.instance
    assert function_config.description == "Rename the room for people."
    assert function_config.verb == "rename"
    assert function_config.is_async is True


@pytest.mark.asyncio
async def test_class_config_function_config_update_config_mutates_only_edge() -> None:
    edge_id = _test_uuid("handler-update-function-membership")
    class_config_id = _test_uuid("handler-update-function-membership-class")
    function_config_id = _test_uuid("handler-update-function-membership-function")
    edge = ClassConfigFunctionConfig(
        id=edge_id,
        class_config_id=class_config_id,
        function_config_id=function_config_id,
        function_config=FunctionConfig(
            id=function_config_id,
            owner_key="aware_demo.default.home.Room",
            name="rename",
            description="Rename the room.",
            is_async=False,
            kind=FunctionKind.instance,
        ),
        is_public=True,
        is_constructor=False,
        position=0,
    )

    await _update_class_config_function_config_impl(
        edge,
        is_public=False,
        is_constructor=True,
        position=2,
    )

    assert edge.id == edge_id
    assert edge.class_config_id == class_config_id
    assert edge.function_config_id == function_config_id
    assert edge.function_config.id == function_config_id
    assert edge.is_public is False
    assert edge.is_constructor is True
    assert edge.position == 2


@pytest.mark.asyncio
async def test_class_config_attribute_config_update_config_mutates_only_edge() -> None:
    edge_id = _test_uuid("handler-update-class-attribute-membership")
    class_config_id = _test_uuid("handler-update-class-attribute-membership-class")
    attribute_config_id = _test_uuid(
        "handler-update-class-attribute-membership-attribute"
    )
    attribute_config = AttributeConfig(
        id=attribute_config_id,
        owner_key="aware_demo.default.home.Room",
        name="name",
        type_descriptor=AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive,
        ),
        is_required=True,
    )
    edge = ClassConfigAttributeConfig(
        id=edge_id,
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
        attribute_config=attribute_config,
        position=0,
        is_identity_key=False,
    )

    await _update_class_config_attribute_config_impl(
        edge,
        position=3,
        is_identity_key=True,
    )

    assert edge.id == edge_id
    assert edge.class_config_id == class_config_id
    assert edge.attribute_config_id == attribute_config_id
    assert edge.attribute_config.id == attribute_config_id
    assert edge.attribute_config.name == "name"
    assert edge.position == 3
    assert edge.is_identity_key is True


@pytest.mark.asyncio
async def test_function_config_attribute_config_update_config_mutates_only_edge() -> (
    None
):
    edge_id = _test_uuid("handler-update-function-attribute-membership")
    function_config_id = _test_uuid(
        "handler-update-function-attribute-membership-function"
    )
    attribute_config_id = _test_uuid(
        "handler-update-function-attribute-membership-attribute"
    )
    attribute_config = AttributeConfig(
        id=attribute_config_id,
        owner_key="aware_demo.default.home.Room.rename::input",
        name="name",
        type_descriptor=AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive,
        ),
        is_required=True,
    )
    edge = FunctionConfigAttributeConfig(
        id=edge_id,
        function_config_id=function_config_id,
        attribute_config_id=attribute_config_id,
        attribute_config=attribute_config,
        name="name",
        position=0,
        type=FunctionAttributeType.input,
        is_identity_key=False,
        identity_key_origin=FunctionIdentityKeyOrigin.standalone,
    )

    await _update_function_config_attribute_config_impl(
        edge,
        position=2,
        is_identity_key=True,
        identity_key_origin=FunctionIdentityKeyOrigin.propagated_parent,
    )

    assert edge.id == edge_id
    assert edge.function_config_id == function_config_id
    assert edge.attribute_config_id == attribute_config_id
    assert edge.attribute_config.id == attribute_config_id
    assert edge.name == "name"
    assert edge.type is FunctionAttributeType.input
    assert edge.position == 2
    assert edge.is_identity_key is True
    assert edge.identity_key_origin is FunctionIdentityKeyOrigin.propagated_parent


@pytest.mark.asyncio
async def test_class_config_remove_relationship_config_removes_membership() -> None:
    class_config_id = _test_uuid("handler-remove-relationship-class")
    first_relationship_id = _test_uuid("handler-remove-relationship-first")
    second_relationship_id = _test_uuid("handler-remove-relationship-second")
    class_config = ClassConfig(
        id=class_config_id,
        class_fqn="aware_demo.default.home.Room",
        name="Room",
        class_config_relationships=[
            ClassConfigRelationship(
                id=first_relationship_id,
                class_config_id=class_config_id,
                target_class_config_id=_test_uuid(
                    "handler-remove-relationship-device-class"
                ),
                relationship_key="room_devices",
                relationship_type=ClassConfigRelationshipType.one_to_many,
                forward_required=False,
            ),
            ClassConfigRelationship(
                id=second_relationship_id,
                class_config_id=class_config_id,
                target_class_config_id=_test_uuid(
                    "handler-remove-relationship-zone-class"
                ),
                relationship_key="room_zones",
                relationship_type=ClassConfigRelationshipType.one_to_many,
                forward_required=False,
            ),
        ],
    )

    await _remove_relationship_config_impl(
        class_config,
        relationship_key="ignored_when_id_present",
        relationship_config_id=first_relationship_id,
    )

    assert [
        relationship.id for relationship in class_config.class_config_relationships
    ] == [
        second_relationship_id,
    ]

    await _remove_relationship_config_impl(
        class_config,
        relationship_key="room_zones",
    )

    assert class_config.class_config_relationships == []


@pytest.mark.asyncio
async def test_class_config_relationship_update_config_mutates_only_relationship() -> (
    None
):
    class_config_id = _test_uuid("handler-update-relationship-class")
    relationship_id = _test_uuid("handler-update-relationship")
    relationship = ClassConfigRelationship(
        id=relationship_id,
        class_config_id=class_config_id,
        target_class_config_id=_test_uuid("handler-update-relationship-target"),
        relationship_key="room_devices",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        identity_rail=ClassConfigRelationshipIdentityRail.containment,
        forward_required=False,
        forward_loading_strategy=ClassConfigRelationshipSideLoadingStrategy.lazy,
        reverse_loading_strategy=None,
    )

    await _update_relationship_config_impl(
        relationship,
        relationship_type=ClassConfigRelationshipType.one_to_one,
        identity_rail=ClassConfigRelationshipIdentityRail.reference,
        forward_required=True,
        forward_loading_strategy=ClassConfigRelationshipSideLoadingStrategy.eager,
        reverse_loading_strategy=ClassConfigRelationshipSideLoadingStrategy.lazy,
        reified_from_relationship_id=None,
        reified_role=ClassConfigRelationshipReifiedRole.source_to_association,
    )

    assert relationship.id == relationship_id
    assert relationship.class_config_id == class_config_id
    assert relationship.relationship_key == "room_devices"
    assert relationship.relationship_type is ClassConfigRelationshipType.one_to_one
    assert relationship.identity_rail is ClassConfigRelationshipIdentityRail.reference
    assert relationship.forward_required is True
    assert (
        relationship.forward_loading_strategy
        is ClassConfigRelationshipSideLoadingStrategy.eager
    )
    assert (
        relationship.reverse_loading_strategy
        is ClassConfigRelationshipSideLoadingStrategy.lazy
    )
    assert relationship.reified_from_relationship_id is None
    assert relationship.reified_from_relationship is None
    assert (
        relationship.reified_role
        is ClassConfigRelationshipReifiedRole.source_to_association
    )
