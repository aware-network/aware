from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

from pydantic import Field

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.runtime.oig_model_reifier import (
    bind_oig_models_to_current_handler_session,
    reify_oig_root_model,
    reify_oig_session,
    reify_oig_target_model,
)
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
    MetaGraphHandlerExecutionContext,
    scoped_meta_graph_handler_execution_context,
)
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_attribute import (
    ClassInstanceAttribute,
)
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.session.change_collector import TrackedList
from aware_orm.session.session import Session
from _meta_runtime_test_paths import REPO_ROOT


_REPO_ROOT = REPO_ROOT


class _ReifierChild(ORMModel):
    label: str
    parent_id: UUID | None = None


class _ReifierParent(ORMModel):
    name: str
    children: list[_ReifierChild] = Field(default_factory=list)


def test_reify_oig_root_model_rebuilds_attributes_and_relationships() -> None:
    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        parent_cc = _class_config(
            name="ReifierParent",
            model_class=_ReifierParent,
        )
        child_cc = _class_config(
            name="ReifierChild",
            model_class=_ReifierChild,
        )
        _attach_model(parent_cc, _ReifierParent)
        _attach_model(child_cc, _ReifierChild)

        name_attr = _primitive_attr_config(owner_key="parent", name="name")
        label_attr = _primitive_attr_config(owner_key="child", name="label")
        parent_id_attr = _primitive_attr_config(
            owner_key="child",
            name="parent_id",
            base_type=CodePrimitiveBaseType.uuid,
        )
        children_attr = AttributeConfig.model_construct(
            id=uuid4(),
            owner_key="parent",
            name="children",
            description=None,
            default_value=None,
            is_primary=False,
            is_public=True,
            is_required=False,
            is_unique=False,
            is_virtual=False,
            exclude_serialization=False,
            type_descriptor=AttributeTypeDescriptor.model_construct(
                id=uuid4(),
                kind=AttributeTypeDescriptorKind.collection,
                collection_kind=AttributeCollectionType.list,
                child_links=[],
            ),
        )
        rel_id = uuid4()
        relationship = ClassConfigRelationship.model_construct(
            id=rel_id,
            relationship_key="children",
            relationship_type=ClassConfigRelationshipType.one_to_many,
            identity_rail=None,
            forward_required=False,
            forward_loading_strategy=None,
            reverse_loading_strategy=None,
            reified_role=None,
            class_config_id=parent_cc.id,
            target_class_config_id=child_cc.id,
            reified_from_relationship_id=None,
            class_config_relationship_attributes=[
                ClassConfigRelationshipAttribute.model_construct(
                    id=uuid4(),
                    class_config_relationship_id=rel_id,
                    attribute_config_id=children_attr.id,
                    direction=ClassConfigRelationshipDirection.forward,
                    role=ClassConfigRelationshipAttributeRole.reference,
                ),
                ClassConfigRelationshipAttribute.model_construct(
                    id=uuid4(),
                    class_config_relationship_id=rel_id,
                    attribute_config_id=parent_id_attr.id,
                    direction=ClassConfigRelationshipDirection.reverse,
                    role=ClassConfigRelationshipAttributeRole.foreign_key,
                ),
            ],
        )
        parent_cc.class_config_relationships = [relationship]

        opg = ObjectProjectionGraph.model_construct(
            id=uuid4(),
            object_config_graph_id=uuid4(),
            description=None,
            language=CodeLanguage.python,
            name="ReifierProjection",
            projection_hash="sha256:reifier",
            supports_virtual_build=True,
            object_projection_graph_edges=[
                ObjectProjectionGraphEdge.model_construct(
                    id=uuid4(),
                    object_projection_graph_id=uuid4(),
                    class_config_relationship_id=rel_id,
                )
            ],
            object_projection_graph_nodes=[],
            object_projection_graph_constructors=[],
            object_projection_graph_relationships=[],
            object_instance_graphs=[],
        )
        parent_object_id = uuid4()
        child_object_id = uuid4()
        parent_ci = _class_instance(
            oig_id=uuid4(),
            class_config_id=parent_cc.id,
            source_object_id=parent_object_id,
            attributes=[_class_instance_attribute(parent_object_id, name_attr, "root")],
        )
        child_ci = _class_instance(
            oig_id=parent_ci.object_instance_graph_id,
            class_config_id=child_cc.id,
            source_object_id=child_object_id,
            attributes=[_class_instance_attribute(child_object_id, label_attr, "leaf")],
        )
        child_ci.source_object_id = str(child_object_id)  # type: ignore[assignment]
        oig = ObjectInstanceGraph.model_construct(
            id=parent_ci.object_instance_graph_id,
            object_projection_graph_id=opg.id,
            key="reifier",
            name="Reifier",
            description=None,
            hash="sha256:oig",
            root_class_instance=parent_ci,
            root_class_instance_id=parent_ci.id,
            class_instances=[parent_ci, child_ci],
            class_instance_relationships=[
                ClassInstanceRelationship.model_construct(
                    id=uuid4(),
                    object_instance_graph_id=parent_ci.object_instance_graph_id,
                    class_config_relationship_id=rel_id,
                    source_class_instance_id=parent_ci.id,
                    target_class_instance_id=child_ci.id,
                )
            ],
        )
        index = SimpleNamespace(
            attribute_configs_by_id={
                name_attr.id: name_attr,
                label_attr.id: label_attr,
                parent_id_attr.id: parent_id_attr,
                children_attr.id: children_attr,
            },
            class_configs_by_id={parent_cc.id: parent_cc, child_cc.id: child_cc},
            relationships_by_id={rel_id: relationship},
        )

        root = reify_oig_root_model(
            index=cast(Any, index),
            opg=opg,
            oig=oig,
            model_type=_ReifierParent,
            root_id=parent_object_id,
        )

        assert root is not None
        assert root.id == parent_object_id
        assert root.name == "root"
        assert isinstance(root.children, TrackedList)
        assert [child.id for child in root.children] == [child_object_id]
        assert root.children[0].label == "leaf"
        assert root.children[0].parent_id == parent_object_id

        target = reify_oig_target_model(
            index=cast(Any, index),
            opg=opg,
            oig=oig,
            model_type=_ReifierParent,
            target_class_instance_id=parent_ci.id,
        )

        assert target is not None
        assert target.id == parent_object_id
        assert target.name == "root"

        branch_id = uuid4()
        scratch_session = reify_oig_session(
            index=cast(Any, index),
            opg=opg,
            oig=oig,
            branch_id=branch_id,
        )
        scratch_root = scratch_session.imap_get(_ReifierParent, parent_object_id)
        scratch_child = scratch_session.imap_get(_ReifierChild, child_object_id)
        assert scratch_root is not None
        assert scratch_child is not None
        assert isinstance(scratch_root.children, TrackedList)
        assert scratch_root.children == [scratch_child]
        assert scratch_child.parent_id == parent_object_id

        session = Session(branch_id=branch_id, skip_db=True)
        execution_context = MetaGraphHandlerExecutionContext(
            session=session,
            ctx=MetaGraphHandlerContext(requester_id=uuid4()),
            function_call=FunctionCall.model_construct(id=uuid4()),
            index=cast(Any, index),
        )
        with scoped_meta_graph_handler_execution_context(execution_context):
            scoped_root = reify_oig_root_model(
                index=cast(Any, index),
                opg=opg,
                oig=oig,
                model_type=_ReifierParent,
                root_id=parent_object_id,
                branch_id=branch_id,
            )

        assert scoped_root is not None
        assert isinstance(scoped_root.children, TrackedList)
        assert session.imap_get(_ReifierParent, parent_object_id) is scoped_root
        assert session.imap_get(_ReifierChild, child_object_id) is (
            scoped_root.children[0]
        )

        seed_session = Session(branch_id=branch_id, skip_db=True)
        seed_execution_context = MetaGraphHandlerExecutionContext(
            session=seed_session,
            ctx=MetaGraphHandlerContext(requester_id=uuid4()),
            function_call=FunctionCall.model_construct(id=uuid4()),
            index=cast(Any, index),
        )
        with scoped_meta_graph_handler_execution_context(seed_execution_context):
            seeded_count = bind_oig_models_to_current_handler_session(
                index=cast(Any, index),
                opg=opg,
                oig=oig,
                branch_id=branch_id,
            )

        assert seeded_count == 2
        seeded_root = seed_session.imap_get(_ReifierParent, parent_object_id)
        assert seeded_root is not None
        assert isinstance(seeded_root.children, TrackedList)
        seeded_child = seed_session.imap_get(_ReifierChild, child_object_id)
        assert seeded_child is not None
        assert seeded_child.parent_id == parent_object_id
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def test_reifier_skips_stale_attribute_payloads_removed_from_active_schema() -> None:
    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        parent_cc = _class_config(
            name="ReifierParent",
            model_class=_ReifierParent,
        )
        _attach_model(parent_cc, _ReifierParent)

        name_attr = _primitive_attr_config(owner_key="parent", name="name")
        stale_attr = _primitive_attr_config(owner_key="parent", name="removed_field")
        parent_object_id = uuid4()
        parent_ci = _class_instance(
            oig_id=uuid4(),
            class_config_id=parent_cc.id,
            source_object_id=parent_object_id,
            attributes=[
                _class_instance_attribute(parent_object_id, name_attr, "root"),
                _class_instance_attribute(parent_object_id, stale_attr, "old"),
            ],
        )
        opg = ObjectProjectionGraph.model_construct(
            id=uuid4(),
            object_config_graph_id=uuid4(),
            description=None,
            language=CodeLanguage.python,
            name="ReifierProjection",
            projection_hash="sha256:reifier",
            supports_virtual_build=True,
            object_projection_graph_edges=[],
            object_projection_graph_nodes=[],
            object_projection_graph_constructors=[],
            object_projection_graph_relationships=[],
            object_instance_graphs=[],
        )
        oig = ObjectInstanceGraph.model_construct(
            id=parent_ci.object_instance_graph_id,
            object_projection_graph_id=opg.id,
            key="reifier",
            name="Reifier",
            description=None,
            hash="sha256:oig",
            root_class_instance=parent_ci,
            root_class_instance_id=parent_ci.id,
            class_instances=[parent_ci],
            class_instance_relationships=[],
        )
        index = SimpleNamespace(
            attribute_configs_by_id={name_attr.id: name_attr},
            class_configs_by_id={parent_cc.id: parent_cc},
            relationships_by_id={},
        )

        root = reify_oig_root_model(
            index=cast(Any, index),
            opg=opg,
            oig=oig,
            model_type=_ReifierParent,
            root_id=parent_object_id,
        )

        assert root is not None
        assert root.id == parent_object_id
        assert root.name == "root"
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def test_meta_materialization_lane_rehydration_stays_off_runtime_executor() -> None:
    source = (
        _REPO_ROOT
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "meta"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_meta"
        / "materialization"
        / "service.py"
    ).read_text(encoding="utf-8")

    assert "AwareRuntimeIndex" not in source
    assert "aware_runtime.environment.operation.support" not in source
    assert "aware_runtime.function_call.author" not in source
    assert "aware_runtime.function_call.executor" not in source
    assert "aware_runtime.graph.builder" not in source
    assert "build_object_instance_graph_from_index" not in source
    assert "default_enum_option_resolver" not in source
    assert "ocg_support" not in source
    assert "resolve_author_id" not in source
    assert "hydrate_orm_graph_from_oig" not in source


def test_reifier_resolves_imported_model_from_python_manifest_without_binding() -> None:
    registry_snapshot = ORMModelRegistry.snapshot_state()
    try:
        ORMModelRegistry.clear_registry()
        ORMModelRegistry.register_class_stub(CodePackage)

        code_package_cc = ClassConfig.model_construct(
            id=UUID("9a7eba4c-02f3-51e3-942c-3902db6dd0e0"),
            class_fqn="aware_code.package.CodePackage",
            description=None,
            name="CodePackage",
            is_base=True,
            is_edge=False,
            value_mode=ClassValueMode.graph_ref,
            object_config_graph_node_id=None,
            parent_class_id=None,
            code_section_class_id=None,
            class_config_attribute_configs=[],
            class_config_function_configs=[],
            class_config_relationships=[],
        )
        assert ORMModelRegistry.get_class_by_class_config_id(code_package_cc.id) is None

        attrs = {
            "manifest_kind": _primitive_attr_config(
                owner_key="code_package",
                name="manifest_kind",
            ),
            "manifest_relative_path": _primitive_attr_config(
                owner_key="code_package",
                name="manifest_relative_path",
            ),
            "package_name": _primitive_attr_config(
                owner_key="code_package",
                name="package_name",
            ),
            "package_root": _primitive_attr_config(
                owner_key="code_package",
                name="package_root",
            ),
            "language": _primitive_attr_config(
                owner_key="code_package",
                name="language",
            ),
            "surface": _primitive_attr_config(
                owner_key="code_package",
                name="surface",
            ),
        }
        package_id = uuid4()
        ci = _class_instance(
            oig_id=uuid4(),
            class_config_id=code_package_cc.id,
            source_object_id=package_id,
            attributes=[
                _class_instance_attribute(
                    package_id,
                    attrs["manifest_kind"],
                    "aware_ontology_toml",
                ),
                _class_instance_attribute(
                    package_id,
                    attrs["manifest_relative_path"],
                    "modules/code/aware.ontology.toml",
                ),
                _class_instance_attribute(
                    package_id,
                    attrs["package_name"],
                    "code-ontology",
                ),
                _class_instance_attribute(
                    package_id,
                    attrs["package_root"],
                    "modules/code",
                ),
                _class_instance_attribute(
                    package_id,
                    attrs["language"],
                    CodeLanguage.aware.value,
                ),
                _class_instance_attribute(
                    package_id,
                    attrs["surface"],
                    "structure",
                ),
            ],
        )
        opg = ObjectProjectionGraph.model_construct(
            id=uuid4(),
            object_config_graph_id=uuid4(),
            description=None,
            language=CodeLanguage.python,
            name="CodePackageProjection",
            projection_hash="sha256:code-package",
            supports_virtual_build=True,
            object_projection_graph_edges=[],
            object_projection_graph_nodes=[],
            object_projection_graph_constructors=[],
            object_projection_graph_relationships=[],
            object_instance_graphs=[],
        )
        oig = ObjectInstanceGraph.model_construct(
            id=ci.object_instance_graph_id,
            object_projection_graph_id=opg.id,
            key="code-package",
            name="CodePackage",
            description=None,
            hash="sha256:oig",
            root_class_instance=ci,
            root_class_instance_id=ci.id,
            class_instances=[ci],
            class_instance_relationships=[],
        )
        index = SimpleNamespace(
            attribute_configs_by_id={attr.id: attr for attr in attrs.values()},
            class_configs_by_id={code_package_cc.id: code_package_cc},
            relationships_by_id={},
        )

        root = reify_oig_root_model(
            index=cast(Any, index),
            opg=opg,
            oig=oig,
            model_type=CodePackage,
            root_id=package_id,
        )

        assert root is not None
        assert root.id == package_id
        assert root.package_name == "code-ontology"
        assert root.language is CodeLanguage.aware
        assert root.manifest_relative_path == "modules/code/aware.ontology.toml"
        assert not hasattr(root, "manifest_kind")
    finally:
        ORMModelRegistry.restore_state(registry_snapshot)


def _attach_model(class_config: ClassConfig, model_class: type[ORMModel]) -> None:
    fqn = ORMModelRegistry.register_class_stub(model_class)
    attached = ORMModelRegistry.attach_class_config(fqn, class_config)
    assert attached is True


def _class_config(
    *,
    name: str,
    model_class: type[ORMModel],
) -> ClassConfig:
    return ClassConfig.model_construct(
        id=uuid4(),
        class_fqn=f"{model_class.__module__}.{model_class.__name__}",
        description=None,
        name=name,
        is_base=True,
        is_edge=False,
        value_mode=ClassValueMode.graph_ref,
        object_config_graph_node_id=None,
        parent_class_id=None,
        code_section_class_id=None,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
    )


def _primitive_attr_config(
    *,
    owner_key: str,
    name: str,
    base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.string,
) -> AttributeConfig:
    primitive_type = CodePrimitiveType.model_construct(
        id=uuid4(),
        signature=base_type.value,
        base_type=base_type,
        constraints=None,
    )
    primitive_config = PrimitiveConfig.model_construct(
        id=uuid4(),
        primitive_type=primitive_type,
        primitive_type_id=primitive_type.id,
    )
    type_descriptor = AttributeTypeDescriptor.model_construct(
        id=uuid4(),
        kind=AttributeTypeDescriptorKind.primitive,
        collection_kind=AttributeCollectionType.single,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
        child_links=[],
    )
    return AttributeConfig.model_construct(
        id=uuid4(),
        owner_key=owner_key,
        name=name,
        description=None,
        default_value=None,
        is_primary=False,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        exclude_serialization=False,
        type_descriptor=type_descriptor,
        type_descriptor_id=type_descriptor.id,
    )


def _class_instance(
    *,
    oig_id: UUID,
    class_config_id: UUID,
    source_object_id: UUID,
    attributes: list[ClassInstanceAttribute],
) -> ClassInstance:
    return ClassInstance.model_construct(
        id=uuid4(),
        object_instance_graph_id=oig_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
        class_config=None,
        class_instance_changes=[],
        ownership=None,
        class_instance_attributes=attributes,
    )


def _class_instance_attribute(
    owner_key: UUID,
    attr_config: AttributeConfig,
    value: object,
) -> ClassInstanceAttribute:
    value_root = AttributeValue.model_construct(
        id=uuid4(),
        type_descriptor=attr_config.type_descriptor,
        type_descriptor_id=attr_config.type_descriptor.id,
        primitive_value={"value": value},
        child_links=[],
    )
    attribute = Attribute.model_construct(
        id=uuid4(),
        owner_key=owner_key,
        attribute_config_id=attr_config.id,
        attribute_config=attr_config,
        attribute_changes=[],
        value_root=value_root,
        value_root_id=value_root.id,
    )
    return ClassInstanceAttribute.model_construct(
        id=uuid4(),
        class_instance_id=owner_key,
        attribute=attribute,
        attribute_id=attribute.id,
    )
