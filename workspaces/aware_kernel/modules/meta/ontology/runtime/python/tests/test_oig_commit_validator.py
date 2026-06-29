from __future__ import annotations

from uuid import UUID, uuid4

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Code Runtime
from aware_code.types import Json

# History Ontology
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
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
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

# Meta Runtime
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_rooted_object_instance_graph_base,
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.builder import build_object_instance_graph_commit
from aware_meta.graph.instance.commit.validator import (
    OigCommitValidationError,
    validate_object_instance_graph_commit,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _link(
    *,
    parent: AttributeTypeDescriptor,
    child: AttributeTypeDescriptor,
    role: Role,
    position: int = 0,
) -> AttributeTypeDescriptorLink:
    return AttributeTypeDescriptorLink(
        attribute_type_descriptor_id=parent.id,
        child=child,
        child_id=child.id,
        role=role,
        position=position,
    )


def _mapping_desc(
    *, key: AttributeTypeDescriptor, value: AttributeTypeDescriptor
) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    desc.child_links.append(_link(parent=desc, child=key, role=Role.key))
    desc.child_links.append(_link(parent=desc, child=value, role=Role.value_))
    return desc


def _make_user_config(*, attrs: list[AttributeConfig]) -> ClassConfig:
    cc = make_class_config(
        "User", class_fqn=_USER_FQN, class_config_attribute_configs=[]
    )
    cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cc.id, attribute_config=cfg, name=cfg.name, position=pos
        )
        for pos, cfg in enumerate(attrs)
    ]
    return cc


def _make_opg(
    *, ocg_id: UUID, opg_id: UUID, projection_hash: str
) -> ObjectProjectionGraph:
    return ObjectProjectionGraph(
        id=opg_id,
        name="opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        supports_virtual_build=True,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )


def _iter_link_changes(
    value_change: AttributeValueChange,
) -> list[AttributeValueLinkChange]:
    out: list[AttributeValueLinkChange] = []
    for link in value_change.attribute_value_link_changes:
        out.append(link)
        if link.child_attribute_value_change is not None:
            out.extend(_iter_link_changes(link.child_attribute_value_change))
    return out


def _first_update_link(commit: ObjectInstanceGraphCommit) -> AttributeValueLinkChange:
    for root in commit.object_instance_graph_changes:
        for ci in root.class_instance_changes:
            for attr in ci.attribute_changes:
                vc = attr.value_root_change
                if vc is None:
                    continue
                for link in _iter_link_changes(vc):
                    if (
                        link.change is not None
                        and link.change.type == ChangeType.update
                    ):
                        return link
    raise AssertionError(
        "Expected at least one UPDATE AttributeValueLinkChange in commit payload"
    )


def test_commit_validator_rejects_update_link_with_deltas() -> None:
    props_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="props",
        is_required=True,
        type_descriptor=_mapping_desc(key=_primitive_desc(), value=_primitive_desc()),
    )
    user_cc = _make_user_config(attrs=[props_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        props: dict[str, str]

    ocg_id = uuid4()
    opg_id = uuid4()
    opg = _make_opg(ocg_id=ocg_id, opg_id=opg_id, projection_hash="lane")
    graph_id = uuid4()
    user_id = uuid4()

    user_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, props={"k": "v1"}),
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, props={"k": "v2"}),
    )

    g_old = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci_old,
        class_instances=[ci_old],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_new = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci_new,
        class_instances=[ci_new],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    commit = build_object_instance_graph_commit(
        old=g_old,
        new=g_new,
        branch_id=uuid4(),
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=uuid4(),
    )
    assert commit is not None

    link = _first_update_link(commit)
    assert link.change is not None
    link.change.change_deltas.append(
        ChangeDelta(
            change_id=link.change.id,
            position=len(link.change.change_deltas),
            kind=ChangeDeltaKind.scalar_set,
            property="role",
            payload=Json({"value": Role.value_.value}),
        )
    )

    with pytest.raises(OigCommitValidationError, match=r"UPDATE must not carry deltas"):
        validate_object_instance_graph_commit(commit=commit)


def test_commit_validator_rejects_unknown_delta_prop_on_attribute_create() -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = _make_user_config(attrs=[name_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    ocg_id = uuid4()
    opg_id = uuid4()
    opg = _make_opg(ocg_id=ocg_id, opg_id=opg_id, projection_hash="lane")
    graph_id = uuid4()
    user_id = uuid4()

    g0 = build_rooted_object_instance_graph_base(
        key="g",
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
    )

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    commit = build_object_instance_graph_commit(
        old=g0,
        new=g1,
        branch_id=uuid4(),
        object_projection_graph=opg,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        author_id=uuid4(),
    )
    assert commit is not None

    root = commit.object_instance_graph_changes[0]
    ci_change = root.class_instance_changes[0]
    attr_change = ci_change.attribute_changes[0]
    assert attr_change.change is not None
    attr_change.change.change_deltas.append(
        ChangeDelta(
            change_id=attr_change.change.id,
            position=len(attr_change.change.change_deltas),
            kind=ChangeDeltaKind.scalar_set,
            property="wat",
            payload=Json({"value": 1}),
        )
    )

    with pytest.raises(OigCommitValidationError, match=r"unsupported 'wat'"):
        validate_object_instance_graph_commit(commit=commit)
