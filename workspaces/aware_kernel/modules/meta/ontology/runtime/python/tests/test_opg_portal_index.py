# @code-under-test: ../aware_meta/graph/projection/portal_index.py

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
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
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
    ObjectProjectionGraphRelationship,
)
from aware_meta_ontology.function.function_config import FunctionConfig

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_meta.graph.projection.portal_index import build_portal_index
from aware_meta.graph.projection.stable_ids import (
    stable_object_projection_graph_relationship_id,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta.test_support import (
    make_class_attribute_edge,
    make_class_config,
    make_ocg_node,
    make_relationship,
)


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def _runtime_graph_with_opgs(graph, *, namespace_by_code_id):
    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id
    ).transform(graph)
    runtime.object_projection_graphs = build_object_projection_graphs(runtime)
    return runtime


PORTAL_CODE = """
class User { posts Post[] }
class Post { title String }

projection Users {
    root test.User
    test.User::posts Posts
}

projection Posts {
    root test.Post
}
""".strip()


def _portal_index_fixture() -> tuple[
    ObjectConfigGraph,
    ObjectProjectionGraph,
    ObjectProjectionGraph,
    ClassConfigRelationship,
]:
    user_class = make_class_config(
        "User",
        class_fqn="pkg.dom.test.User",
    )
    post_class = make_class_config(
        "Post",
        class_fqn="pkg.dom.test.Post",
    )
    posts_attr = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key=user_class.class_fqn,
        name="posts",
    )
    user_class.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_class.id,
            attribute_config=posts_attr,
            position=0,
        )
    ]
    relationship = make_relationship(
        class_config_id=user_class.id,
        target_class_config_id=post_class.id,
        relationship_type=ClassConfigRelationshipType.one_to_many,
        relationship_key="pkg.dom.test.User.posts",
        forward_required=False,
        class_config_relationship_attributes=[],
    )
    relationship.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=relationship.id,
            attribute_config_id=posts_attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    )
    user_class.class_config_relationships = [relationship]

    graph = ObjectConfigGraph(
        name="portal",
        description="portal",
        hash="sha256:portal",
        fqn_prefix="pkg",
        language=CodeLanguage.aware,
    )
    graph.object_config_graph_nodes = [
        make_ocg_node(
            object_config_graph_id=graph.id,
            type=ObjectConfigGraphNodeType.class_,
            class_config=user_class,
        ),
        make_ocg_node(
            object_config_graph_id=graph.id,
            type=ObjectConfigGraphNodeType.class_,
            class_config=post_class,
        ),
        make_ocg_node(
            object_config_graph_id=graph.id,
            type=ObjectConfigGraphNodeType.relationship,
            class_config_relationship=relationship,
        ),
    ]

    users = ObjectProjectionGraph(
        name="users",
        description=None,
        language=CodeLanguage.aware,
        projection_hash="sha256:test:users",
        object_config_graph_id=graph.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    user_root = ObjectProjectionGraphNode(
        object_projection_graph_id=users.id,
        class_config_id=user_class.id,
        is_root=True,
        selection=ObjectProjectionGraphNodeSelection.one,
    )
    users.object_projection_graph_nodes = [user_root]

    posts = ObjectProjectionGraph(
        name="posts",
        description=None,
        language=CodeLanguage.aware,
        projection_hash="sha256:test:posts",
        object_config_graph_id=graph.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    post_root = ObjectProjectionGraphNode(
        object_projection_graph_id=posts.id,
        class_config_id=post_class.id,
        is_root=True,
        selection=ObjectProjectionGraphNodeSelection.one,
    )
    posts.object_projection_graph_nodes = [post_root]

    users.object_projection_graph_relationships = [
        ObjectProjectionGraphRelationship(
            id=stable_object_projection_graph_relationship_id(
                source_opg_id=users.id,
                class_config_relationship_id=relationship.id,
                target_opg_id=posts.id,
            ),
            object_projection_graph_id=users.id,
            target_object_projection_graph_id=posts.id,
            target_object_projection_graph=posts,
            class_config_relationship_id=relationship.id,
            class_config_relationship=relationship,
            source_object_projection_graph_node_id=user_root.id,
            target_object_projection_graph_node_id=post_root.id,
        )
    ]
    graph.object_projection_graphs = [users, posts]
    return graph, users, posts, relationship


def test_portal_index_builds_reference_field_and_targets() -> None:
    graph, users, posts, _relationship = _portal_index_fixture()

    idx = build_portal_index(graph)
    assert idx.portals
    assert users.projection_hash in idx.portals_by_source_projection_hash

    portal = idx.portals_by_source_projection_hash[users.projection_hash][0]
    assert portal.source_object_projection_graph_id == users.id
    assert portal.target_object_projection_graph_id == posts.id
    assert portal.source_projection_hash == users.projection_hash
    assert portal.target_projection_hash == posts.projection_hash
    assert portal.reference_field_name == "posts"

    assert users.object_projection_graph_relationships
    opg_rel = users.object_projection_graph_relationships[0]
    assert opg_rel.id == stable_object_projection_graph_relationship_id(
        source_opg_id=users.id,
        class_config_relationship_id=portal.class_config_relationship_id,
        target_opg_id=posts.id,
    )

    # Direct lookup by (source_hash, relationship_id) must exist.
    rel_map = idx.portals_by_source_projection_hash_and_relationship_id[
        users.projection_hash
    ]
    assert portal.class_config_relationship_id in rel_map
    assert (
        rel_map[portal.class_config_relationship_id][0].target_projection_hash
        == posts.projection_hash
    )


def test_portal_index_resolves_relationship_from_class_node_metadata() -> None:
    graph, users, posts, source_rel = _portal_index_fixture()
    opg_rel = users.object_projection_graph_relationships[0]

    graph.object_config_graph_nodes = [
        node
        for node in graph.object_config_graph_nodes
        if node.type != ObjectConfigGraphNodeType.relationship
    ]
    graph.object_config_graph_relationships = []
    opg_rel.class_config_relationship = None

    idx = build_portal_index(graph)

    portal = idx.portals_by_source_projection_hash[users.projection_hash][0]
    assert portal.class_config_relationship_id == source_rel.id
    assert portal.target_object_projection_graph_id == posts.id
    assert portal.reference_field_name == "posts"


def test_portal_index_resolves_relationship_from_installed_binding_metadata() -> None:
    graph, users, posts, source_rel = _portal_index_fixture()
    source_class = next(
        node.class_config
        for node in graph.object_config_graph_nodes
        if node.class_config is not None
        and node.class_config.id == source_rel.class_config_id
    )
    assert source_class is not None
    installed_source_class = source_class.model_copy(deep=True)
    graph.object_config_graph_nodes = [
        node
        for node in graph.object_config_graph_nodes
        if node.type != ObjectConfigGraphNodeType.relationship
    ]
    graph.object_config_graph_relationships = []
    for node in graph.object_config_graph_nodes:
        if node.class_config is not None:
            node.class_config.class_config_relationships = []
    users.object_projection_graph_relationships[0].class_config_relationship = None

    class PortalUser(ORMModel):
        pass

    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(PortalUser)
        PortalUser.bind_class_config(installed_source_class)
        idx = build_portal_index(graph)

    portal = idx.portals_by_source_projection_hash[users.projection_hash][0]
    assert portal.class_config_relationship_id == source_rel.id
    assert portal.target_object_projection_graph_id == posts.id
    assert portal.reference_field_name == "posts"


def test_portal_index_does_not_merge_installed_attributes_into_graph_class() -> None:
    graph, users, _posts, source_rel = _portal_index_fixture()
    source_class = next(
        node.class_config
        for node in graph.object_config_graph_nodes
        if node.class_config is not None
        and node.class_config.id == source_rel.class_config_id
    )
    assert source_class is not None
    installed_source_class = source_class.model_copy(deep=True)
    stale_attr = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key=installed_source_class.class_fqn,
        name="stale_installed_field",
    )
    installed_source_class.class_config_attribute_configs.append(
        make_class_attribute_edge(
            class_config_id=installed_source_class.id,
            attribute_config=stale_attr,
            position=99,
        )
    )
    installed_function = FunctionConfig.model_construct(
        id=uuid4(),
        owner_key=installed_source_class.class_fqn,
        name="runtime_bridge",
    )
    installed_source_class.class_config_function_configs.append(
        ClassConfigFunctionConfig.model_construct(
            id=uuid4(),
            class_config_id=installed_source_class.id,
            function_config_id=installed_function.id,
            function_config=installed_function,
            is_public=True,
            is_constructor=False,
            position=99,
        )
    )

    class PortalUserWithStaleMetadata(ORMModel):
        pass

    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(PortalUserWithStaleMetadata)
        PortalUserWithStaleMetadata.bind_class_config(installed_source_class)
        idx = build_portal_index(graph)

    assert (
        idx.portals_by_source_projection_hash[users.projection_hash][
            0
        ].reference_field_name
        == "posts"
    )
    assert [
        link.attribute_config.name
        for link in source_class.class_config_attribute_configs
    ] == ["posts"]
    assert any(
        link.function_config is not None
        and link.function_config.name == "runtime_bridge"
        for link in source_class.class_config_function_configs
    )


def test_portal_index_fails_closed_when_portal_relationship_missing_runtime_metadata() -> (
    None
):
    graph, users, _posts, _source_rel = _portal_index_fixture()
    graph.object_config_graph_nodes = [
        node
        for node in graph.object_config_graph_nodes
        if node.type != ObjectConfigGraphNodeType.relationship
    ]
    graph.object_config_graph_relationships = []
    for node in graph.object_config_graph_nodes:
        if node.class_config is not None:
            node.class_config.class_config_relationships = []
    users.object_projection_graph_relationships[0].class_config_relationship = None

    with pytest.raises(
        ValueError,
        match="ObjectProjectionGraphRelationship missing ClassConfigRelationship binding",
    ):
        build_portal_index(graph)


def test_portal_index_resolves_external_target_opgs(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    ext_code = _build_code(
        tmp_path,
        "ext.aware",
        """
class Child {}
""".strip(),
    )
    ext_ns, ext_domains = _ns(
        fqn_prefix="aware_ext",
        namespace="schema",
        code_ids=[ext_code.id],
    )
    ext_graph = build_object_config_graph_from_code(
        name="ext",
        description="ext",
        fqn_prefix="aware_ext",
        file_codes=[("ext.aware", ext_code)],
        namespace_by_code_id=ext_ns,
    ).graph

    local_code = _build_code(
        tmp_path,
        "local.aware",
        """
class Parent {
    child aware_ext.schema.Child
}
""".strip(),
    )
    local_ns, local_domains = _ns(
        fqn_prefix="aware_local",
        namespace="schema",
        code_ids=[local_code.id],
    )
    local_build = build_object_config_graph_from_code(
        name="local",
        description="local",
        fqn_prefix="aware_local",
        file_codes=[("local.aware", local_code)],
        namespace_by_code_id=local_ns,
        external_graphs=[ext_graph],
    )
    local_graph = local_build.graph
    cross_rels = local_build.cross_relationships_by_target_ocg.get(ext_graph.id)
    assert cross_rels is not None and len(cross_rels) == 1

    local_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=local_graph.id,
            target_object_config_graph_id=ext_graph.id,
            class_config_relationships=[cross_rels[0]],
        )
    )

    parent_cc_id = next(
        node.class_config.id
        for node in local_graph.object_config_graph_nodes
        if node.type == ObjectConfigGraphNodeType.class_
        and node.class_config is not None
        and node.class_config.name == "Parent"
    )
    child_cc_id = next(
        node.class_config.id
        for node in ext_graph.object_config_graph_nodes
        if node.type == ObjectConfigGraphNodeType.class_
        and node.class_config is not None
        and node.class_config.name == "Child"
    )

    ext_opg = ObjectProjectionGraph(
        name="children",
        description=None,
        language=CodeLanguage.aware,
        projection_hash="sha256:test:children",
        object_config_graph_id=ext_graph.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    ext_root = ObjectProjectionGraphNode(
        object_projection_graph_id=ext_opg.id,
        class_config_id=child_cc_id,
        is_root=True,
        selection=ObjectProjectionGraphNodeSelection.one,
    )
    ext_opg.object_projection_graph_nodes = [ext_root]
    ext_graph.object_projection_graphs = [ext_opg]

    local_opg = ObjectProjectionGraph(
        name="parents",
        description=None,
        language=CodeLanguage.aware,
        projection_hash="sha256:test:parents",
        object_config_graph_id=local_graph.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    local_root = ObjectProjectionGraphNode(
        object_projection_graph_id=local_opg.id,
        class_config_id=parent_cc_id,
        is_root=True,
        selection=ObjectProjectionGraphNodeSelection.one,
    )
    local_opg.object_projection_graph_nodes = [local_root]
    local_opg.object_projection_graph_relationships = [
        ObjectProjectionGraphRelationship(
            object_projection_graph_id=local_opg.id,
            target_object_projection_graph_id=ext_opg.id,
            class_config_relationship_id=cross_rels[0].id,
            source_object_projection_graph_node_id=local_root.id,
            target_object_projection_graph_node_id=ext_root.id,
        )
    ]
    local_graph.object_projection_graphs = [local_opg]

    idx = build_portal_index(local_graph, external_graphs=[ext_graph])

    assert idx.portals
    portal = idx.portals[0]
    assert portal.source_object_projection_graph_id == local_opg.id
    assert portal.target_object_projection_graph_id == ext_opg.id
    assert portal.reference_field_name == "child"
