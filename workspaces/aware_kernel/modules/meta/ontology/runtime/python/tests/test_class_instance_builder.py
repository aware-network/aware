from __future__ import annotations

import json
from uuid import UUID, uuid4

import pytest

from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)

from aware_meta.attribute.instance.value import UnionSelection
from aware_meta.class_.instance.builder import (
    ClassInstanceBuildProfile,
    ClassInstanceBuildError,
    build_class_instance,
)
from aware_meta.graph.config.stable_ids import stable_class_instance_id
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_relationship,
    test_class_fqn,
)

from aware_orm.models.introspection import MappingModelSource


def _desc(
    kind: Kind,
    *,
    collection_kind: AttributeCollectionType = AttributeCollectionType.single,
) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=kind,
        collection_kind=collection_kind,
        child_links=[],
    )


def _dlink(
    child: AttributeTypeDescriptor, role: Role, *, position: int = 0
) -> AttributeTypeDescriptorLink:
    return AttributeTypeDescriptorLink(
        child=child,
        role=role,
        position=position,
        attribute_type_descriptor_id=uuid4(),
        child_id=child.id,
    )


def _make_class(name: str, **kwargs) -> ClassConfig:
    return make_class_config(name, class_fqn=test_class_fqn(name), **kwargs)


def _class_instance_id(
    *, object_instance_graph_id: UUID, class_config: ClassConfig, source_object_id: UUID
) -> UUID:
    return stable_class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=source_object_id,
    )


def test_build_class_instance_builds_descriptor_value_trees() -> None:
    user_fqn = test_class_fqn("User")
    name_desc = _desc(Kind.primitive)
    nums_elem_desc = _desc(Kind.primitive)
    nums_desc = _desc(Kind.collection, collection_kind=AttributeCollectionType.list)
    nums_desc.child_links = [_dlink(nums_elem_desc, Role.element)]

    name_cfg = make_attribute_config(
        owner_key=user_fqn, name="name", is_required=True, type_descriptor=name_desc
    )
    nums_cfg = make_attribute_config(
        owner_key=user_fqn, name="nums", is_required=False, type_descriptor=nums_desc
    )

    cls = _make_class("User", class_config_attribute_configs=[])
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        ),
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=nums_cfg,
            name=nums_cfg.name,
            position=1,
        ),
    ]

    instance_id = uuid4()
    object_instance_graph_id = uuid4()
    ci = build_class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config=cls,
        source=MappingModelSource(
            id=instance_id, values={"name": "Luis", "nums": [1, 2]}
        ),
    )
    assert ci.class_config_id == cls.id
    assert ci.id == _class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config=cls,
        source_object_id=instance_id,
    )
    assert ci.source_object_id == instance_id
    assert len(ci.attributes) == 2

    attr_name = ci.attributes[0]
    assert attr_name.attribute_config_id == name_cfg.id
    assert attr_name.owner_key == ci.source_object_id
    assert attr_name.value_root is not None
    assert attr_name.value_root.type_descriptor_id == name_desc.id
    assert attr_name.value_root.primitive_value == {"value": "Luis"}

    attr_nums = ci.attributes[1]
    assert attr_nums.attribute_config_id == nums_cfg.id
    assert attr_nums.value_root is not None
    assert [l.position for l in attr_nums.value_root.child_links] == [0, 1]
    values = []
    for l in attr_nums.value_root.child_links:
        assert l.child is not None
        assert l.child.primitive_value is not None
        values.append(l.child.primitive_value["value"])
    assert values == [1, 2]


def test_build_class_instance_dedupes_duplicate_attribute_links() -> None:
    user_fqn = test_class_fqn("User")
    name_desc = _desc(Kind.primitive)
    name_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="name",
        is_required=True,
        type_descriptor=name_desc,
    )
    cls = _make_class("User", class_config_attribute_configs=[])
    first_link = make_class_attribute_edge(
        class_config_id=cls.id,
        attribute_config=name_cfg,
        name=name_cfg.name,
        position=0,
    )
    cls.class_config_attribute_configs = [
        first_link,
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=1,
        ),
    ]

    profile = ClassInstanceBuildProfile()
    ci = build_class_instance(
        object_instance_graph_id=uuid4(),
        class_config=cls,
        source=MappingModelSource(id=uuid4(), values={"name": "Luis"}),
        build_profile=profile,
    )

    assert [attribute.attribute_config_id for attribute in ci.attributes] == [
        name_cfg.id
    ]
    assert profile.attr_links_total == 2
    assert profile.duplicate_attribute_links_skipped == 1


def test_build_class_instance_uses_default_value_when_missing() -> None:
    user_fqn = test_class_fqn("User")
    age_desc = _desc(Kind.primitive)
    age_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="age",
        is_required=False,
        default_value=json.dumps(42),
        type_descriptor=age_desc,
    )

    cls = _make_class("User", class_config_attribute_configs=[])
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id, attribute_config=age_cfg, name=age_cfg.name
        )
    ]

    ci = build_class_instance(
        object_instance_graph_id=uuid4(),
        class_config=cls,
        source=MappingModelSource(id=uuid4(), values={}),
    )
    assert len(ci.attributes) == 1
    assert ci.attributes[0].value_root is not None
    assert ci.attributes[0].value_root.primitive_value == {"value": 42}


def test_build_class_instance_raises_for_missing_required_attribute() -> None:
    user_fqn = test_class_fqn("User")
    req_desc = _desc(Kind.primitive)
    req_cfg = make_attribute_config(
        owner_key=user_fqn, name="required", is_required=True, type_descriptor=req_desc
    )

    cls = _make_class("User", class_config_attribute_configs=[])
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id, attribute_config=req_cfg, name=req_cfg.name
        )
    ]

    with pytest.raises(ClassInstanceBuildError):
        build_class_instance(
            object_instance_graph_id=uuid4(),
            class_config=cls,
            source=MappingModelSource(id=uuid4(), values={}),
        )


def test_build_class_instance_passes_union_selection() -> None:
    user_fqn = test_class_fqn("User")
    m1 = _desc(Kind.primitive)
    m2 = _desc(Kind.enum)
    uni_desc = _desc(Kind.union)
    uni_desc.child_links = [
        _dlink(m1, Role.member, position=1),
        _dlink(m2, Role.member, position=2),
    ]

    choice_cfg = make_attribute_config(
        owner_key=user_fqn, name="choice", is_required=True, type_descriptor=uni_desc
    )
    cls = _make_class("User", class_config_attribute_configs=[])
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=choice_cfg,
            name=choice_cfg.name,
            position=0,
        )
    ]

    enum_opt_id = uuid4()
    ci = build_class_instance(
        object_instance_graph_id=uuid4(),
        class_config=cls,
        source=MappingModelSource(id=uuid4(), values={"choice": "ignored"}),
        union_selections={"choice": UnionSelection(position=2, value=enum_opt_id)},
    )
    assert len(ci.attributes) == 1
    root = ci.attributes[0].value_root
    assert root is not None and len(root.child_links) == 1
    assert root.child_links[0].position == 2
    assert root.child_links[0].child is not None
    assert root.child_links[0].child.enum_option_id == enum_opt_id


def test_build_class_instance_rejects_non_introspection_source() -> None:
    user_fqn = test_class_fqn("User")
    desc = _desc(Kind.primitive)
    cfg = make_attribute_config(
        owner_key=user_fqn, name="name", is_required=False, type_descriptor=desc
    )
    cls = _make_class("User", class_config_attribute_configs=[])
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id, attribute_config=cfg, name=cfg.name
        )
    ]

    with pytest.raises(ClassInstanceBuildError):
        build_class_instance(
            object_instance_graph_id=uuid4(),
            class_config=cls,
            source={"name": "x"},
        )  # type: ignore


def test_build_class_instance_uses_source_object_id_when_present() -> None:
    user_fqn = test_class_fqn("User")
    desc = _desc(Kind.primitive)
    cfg = make_attribute_config(
        owner_key=user_fqn, name="name", is_required=True, type_descriptor=desc
    )
    cls = _make_class("User", class_config_attribute_configs=[])
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id, attribute_config=cfg, name=cfg.name
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class Source(BaseORMModel):
        name: str

    src_id = uuid4()
    object_instance_graph_id = uuid4()
    ci = build_class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config=cls,
        source=Source(id=src_id, name="Luis"),
    )
    assert ci.id == _class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config=cls,
        source_object_id=src_id,
    )
    assert ci.source_object_id == src_id
    assert ci.attributes[0].value_root is not None
    assert ci.attributes[0].value_root.primitive_value == {"value": "Luis"}


def test_build_class_instance_skips_relationship_attributes() -> None:
    # Relationship attribute (REFERENCE) must be omitted from instance attributes.
    user_fqn = test_class_fqn("User")
    rel_desc = _desc(Kind.class_)
    rel_cfg = make_attribute_config(
        owner_key=user_fqn, name="org", is_required=True, type_descriptor=rel_desc
    )

    data_desc = _desc(Kind.primitive)
    data_cfg = make_attribute_config(
        owner_key=user_fqn, name="name", is_required=True, type_descriptor=data_desc
    )

    cls = _make_class(
        "User", class_config_attribute_configs=[], class_config_relationships=[]
    )
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=data_cfg,
            name=data_cfg.name,
            position=0,
        ),
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=rel_cfg,
            name=rel_cfg.name,
            position=1,
        ),
    ]

    rel = make_relationship(
        class_config_id=cls.id,
        target_class_config_id=uuid4(),
        relationship_type=ClassConfigRelationshipType.many_to_one,
        relationship_key="user_org",
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=rel_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    )
    cls.class_config_relationships = [rel]

    ci = build_class_instance(
        object_instance_graph_id=uuid4(),
        class_config=cls,
        source=MappingModelSource(id=uuid4(), values={"name": "Luis"}),
    )
    assert [a.attribute_config_id for a in ci.attributes] == [data_cfg.id]


def test_build_class_instance_enforces_required_fk_from_relationship_truth() -> None:
    child_fqn = test_class_fqn("Child")
    fk_desc = _desc(Kind.primitive)
    fk_cfg = make_attribute_config(
        owner_key=child_fqn,
        name="parent_id",
        is_required=False,  # Language serialization ergonomics may keep FK optional.
        type_descriptor=fk_desc,
    )
    rel_desc = _desc(Kind.class_)
    rel_cfg = make_attribute_config(
        owner_key=child_fqn, name="parent", is_required=False, type_descriptor=rel_desc
    )

    cls = _make_class(
        "Child", class_config_attribute_configs=[], class_config_relationships=[]
    )
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=rel_cfg,
            name=rel_cfg.name,
            position=0,
        ),
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=fk_cfg,
            name=fk_cfg.name,
            position=1,
        ),
    ]

    rel = make_relationship(
        class_config_id=cls.id,
        target_class_config_id=uuid4(),
        relationship_type=ClassConfigRelationshipType.many_to_one,
        relationship_key="child_parent",
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=rel_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
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

    with pytest.raises(ClassInstanceBuildError, match="parent_id"):
        build_class_instance(
            object_instance_graph_id=uuid4(),
            class_config=cls,
            source=MappingModelSource(id=uuid4(), values={}),
            relationship_attribute_config_ids={fk_cfg.id, rel_cfg.id},
            include_relationship_attribute_config_ids={fk_cfg.id},
        )


def test_build_class_instance_enforces_reverse_fk_required_for_one_to_many() -> None:
    child_fqn = test_class_fqn("Child")
    fk_desc = _desc(Kind.primitive)
    fk_cfg = make_attribute_config(
        owner_key=child_fqn,
        name="parent_id",
        is_required=False,
        type_descriptor=fk_desc,
    )

    cls = _make_class(
        "Child", class_config_attribute_configs=[], class_config_relationships=[]
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
        class_config_id=uuid4(),  # parent class id
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

    with pytest.raises(ClassInstanceBuildError, match="parent_id"):
        build_class_instance(
            object_instance_graph_id=uuid4(),
            class_config=cls,
            source=MappingModelSource(id=uuid4(), values={}),
            relationship_attribute_config_ids={fk_cfg.id},
            include_relationship_attribute_config_ids={fk_cfg.id},
        )


def test_build_class_instance_collects_profile_counts() -> None:
    user_fqn = test_class_fqn("User")
    data_desc = _desc(Kind.primitive)
    rel_desc = _desc(Kind.class_)

    name_cfg = make_attribute_config(
        owner_key=user_fqn, name="name", is_required=True, type_descriptor=data_desc
    )
    age_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="age",
        is_required=False,
        default_value=json.dumps(42),
        type_descriptor=data_desc,
    )
    virtual_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="derived_name",
        is_required=False,
        is_virtual=True,
        type_descriptor=data_desc,
    )
    org_cfg = make_attribute_config(
        owner_key=user_fqn, name="org", is_required=False, type_descriptor=rel_desc
    )

    cls = _make_class(
        "User", class_config_attribute_configs=[], class_config_relationships=[]
    )
    cls.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        ),
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=age_cfg,
            name=age_cfg.name,
            position=1,
        ),
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=virtual_cfg,
            name=virtual_cfg.name,
            position=2,
        ),
        make_class_attribute_edge(
            class_config_id=cls.id,
            attribute_config=org_cfg,
            name=org_cfg.name,
            position=3,
        ),
    ]

    rel = make_relationship(
        class_config_id=cls.id,
        target_class_config_id=uuid4(),
        relationship_type=ClassConfigRelationshipType.many_to_one,
        relationship_key="user_org",
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=org_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    )
    cls.class_config_relationships = [rel]

    profile = ClassInstanceBuildProfile()
    ci = build_class_instance(
        object_instance_graph_id=uuid4(),
        class_config=cls,
        source=MappingModelSource(id=uuid4(), values={"name": "Luis"}),
        build_profile=profile,
    )

    assert [attribute.attribute_config_id for attribute in ci.attributes] == [
        name_cfg.id,
        age_cfg.id,
    ]
    assert profile.attr_links_total == 4
    assert profile.relationship_attribute_ids_total == 1
    assert profile.required_fk_attribute_ids_total == 0
    assert profile.attributes_built == 2
    assert profile.virtual_attributes_skipped == 1
    assert profile.relationship_attributes_skipped == 1
    assert profile.optional_attributes_omitted == 0
    assert profile.default_values_used == 1
