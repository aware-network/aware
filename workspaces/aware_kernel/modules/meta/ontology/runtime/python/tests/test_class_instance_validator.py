from __future__ import annotations

from uuid import uuid4

import pytest

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_instance import ClassInstance

from aware_meta.class_.instance.validator import (
    ClassInstanceValidationError,
    validate_class_instance,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_relationship,
    test_class_fqn,
)


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive)


def test_validate_class_instance_enforces_required_fk_from_relationship_truth() -> None:
    actor_fqn = test_class_fqn("Actor")
    fk_cfg = make_attribute_config(
        owner_key=actor_fqn,
        name="identity_id",
        is_required=False,
        type_descriptor=_primitive_desc(),
    )

    cls = make_class_config(
        "Actor",
        class_fqn=actor_fqn,
        class_config_attribute_configs=[],
        class_config_relationships=[],
    )
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=fk_cfg,
            name=fk_cfg.name,
            position=0,
        ),
    ]

    rel = make_relationship(
        class_config_id=cls.id,
        target_class_config_id=uuid4(),
        relationship_type=ClassConfigRelationshipType.many_to_one,
        relationship_key="actor_identity",
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=fk_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    )
    cls.class_config_relationships = [rel]

    graph_id = uuid4()
    ci = ClassInstance(
        object_instance_graph_id=graph_id,
        class_config_id=cls.id,
        source_object_id=uuid4(),
        class_config=cls,
        attributes=[],
    )
    with pytest.raises(ClassInstanceValidationError, match="identity_id"):
        validate_class_instance(
            class_instance=ci,
            class_config=cls,
            relationship_attribute_config_ids={fk_cfg.id},
            include_relationship_attribute_config_ids={fk_cfg.id},
        )


def test_validate_class_instance_enforces_reverse_fk_required_for_one_to_many() -> None:
    child_fqn = test_class_fqn("Child")
    fk_cfg = make_attribute_config(
        owner_key=child_fqn,
        name="parent_id",
        is_required=False,
        type_descriptor=_primitive_desc(),
    )

    cls = make_class_config(
        "Child",
        class_fqn=child_fqn,
        class_config_attribute_configs=[],
        class_config_relationships=[],
    )
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=fk_cfg,
            name=fk_cfg.name,
            position=0,
        ),
    ]

    rel = make_relationship(
        class_config_id=uuid4(),
        target_class_config_id=cls.id,
        relationship_type=ClassConfigRelationshipType.one_to_many,
        relationship_key="parent_children",
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=fk_cfg.id,
            direction=ClassConfigRelationshipDirection.reverse,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    )
    cls.class_config_relationships = [rel]

    graph_id = uuid4()
    ci = ClassInstance(
        object_instance_graph_id=graph_id,
        class_config_id=cls.id,
        source_object_id=uuid4(),
        class_config=cls,
        attributes=[],
    )
    with pytest.raises(ClassInstanceValidationError, match="parent_id"):
        validate_class_instance(
            class_instance=ci,
            class_config=cls,
            relationship_attribute_config_ids={fk_cfg.id},
            include_relationship_attribute_config_ids={fk_cfg.id},
        )
