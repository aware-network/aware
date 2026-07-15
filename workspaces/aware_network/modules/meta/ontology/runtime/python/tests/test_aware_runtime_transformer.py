# @code-under-test: ../../languages/aware/grammar/grammar/aware_grammar/transformers/aware_to_runtime_transformer.py

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_mirror import (
    ObjectConfigGraphMirror,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_mirror_enums import (
    ObjectConfigGraphMirrorTargetKind,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_instruction import (
    FunctionImplInstruction,
)
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInstructionType,
    FunctionImplInvokeKind,
)
from aware_meta_ontology.function.function_impl_instruction_invoke import (
    FunctionImplInstructionInvoke,
)
from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
    FunctionImplInstructionInvokeAttributeConfig,
)

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Runtime
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.handlers import (
    build_object_config_graph_overlays_from_annotations,
    build_object_projection_graphs,
)
from aware_meta_ontology.stable_ids import (
    stable_function_impl_id,
    stable_function_impl_instruction_id,
    stable_function_impl_instruction_invoke_id,
)
from aware_meta.fqn_resolver import NamespacePath

# Transformer under test (runtime IR)
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)
from aware_grammar.transformers.runtime import (
    RuntimeFunctionSurfaceSupport,
    RuntimeTransformSupport,
)
from sql_grammar.transformers.runtime_to_sql_transformer import RuntimeToSQLTransformer
from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.renderers.renderer import SQLRenderer

DEFAULT_CODE = """
class Parent {
    children Child[]
}

class Child {
    profile Profile? unique
}

class Profile { id String }

ann default.Parent::children load reverse eager

class Membership {
    users User[] @UserGroupEdge many
}
class User { id String }
edge UserGroupEdge { status String }
"""

PATH_SCOPED_CONSTRUCTOR_CODE = """
class Parent {
    children Child[]

    fn add_child(value String) -> UUID {
        let child = construct children.create_child(value = value)
    }
}

class Child {
    fn create_child construct(value String) -> Child {
        // Canonical child constructor stays parent-agnostic in .aware.
    }
}
"""

PATH_SCOPED_CONSTRUCTOR_ONE_TO_ONE_CODE = """
class Parent {
    child Child unique

    fn add_child(value String) -> UUID {
        let child = construct child.create_child(value = value)
    }
}

class Child {
    fn create_child construct(value String) -> Child {
        // Canonical child constructor stays parent-agnostic in .aware.
    }
}
"""

EDGE_TARGET_CONTAINMENT_CHILD_FK_ONLY_CODE = """
class Package {
    codes Code[] @PackageCode

    fn create_code(relative_path String key) -> PackageCode {
        let created = construct codes.create(relative_path = relative_path)
    }
}

edge PackageCode {
    relative_path String key

    fn create construct(relative_path String key) -> PackageCode {
        let created = construct code.create(relative_path = relative_path)
    }
}

class Code {
    relative_path String key

    fn create construct(relative_path String key) -> Code {
    }
}
"""

PATH_SCOPED_CONSTRUCTOR_MANY_TO_MANY_CODE = """
class Parent {
    children Child[] many

    fn add_child(value String) -> UUID {
        let child = construct children.create_child(value = value)
    }
}

class Child {
    fn create_child construct(value String) -> Child {
        // Canonical child constructor stays parent-agnostic in .aware.
    }
}
"""

PATH_SCOPED_CONSTRUCTOR_ASSOCIATION_EDGE_CODE = """
class Parent {
    children Child[] @ParentChildEdge

    fn add_child(value String) -> UUID {
        let edge = construct children.build(value = value)
    }
}

class Child { id String }

edge ParentChildEdge {
    fn build construct(value String) -> ParentChildEdge {
        // Canonical edge constructor stays parent-agnostic in .aware.
    }
}
"""

PATH_SCOPED_CONSTRUCTOR_ASSOCIATION_EDGE_REFERENCE_KEY_CODE = """
class Parent {
    child Child? @ParentChildEdge

    fn attach_child(child_id UUID) -> UUID {
        let edge = construct child.build(child_id = child_id)
    }
}

class Child { id String }

edge ParentChildEdge {
    fn build construct(child_id UUID key) -> ParentChildEdge {
        // Edge constructor explicitly keys the referenced endpoint.
    }
}
"""

PATH_SCOPED_CONSTRUCTOR_STANDALONE_TARGET_CODE = """
class Parent {
    edges Edge[]
}

class AttributeConfig {
    owner_key String key
    name String key

    fn create construct(owner_key String key, name String key) -> AttributeConfig {
        // Standalone schema primitive constructor.
    }
}

ann default.AttributeConfig identity standalone

class Edge {
    attribute_config AttributeConfig

    fn create construct(owner_key String, name String) -> Edge {
        let created = construct attribute_config.create(owner_key = owner_key, name = name)
    }
}
"""

PATH_SCOPED_CONSTRUCTOR_MIXED_CONTAINED_AND_STANDALONE_CODE = """
class Parent {
    children Child[]
    edges Edge[]

    fn add_child(value String) -> UUID {
        let child = construct children.create_child(value = value)
    }

    fn add_edge(owner_key String, name String) -> UUID {
        let edge = construct edges.create(owner_key = owner_key, name = name)
    }
}

class Child {
    fn create_child construct(value String) -> Child {
        // Canonical child constructor stays parent-agnostic in .aware.
    }
}

class AttributeConfig {
    owner_key String key
    name String key

    fn create construct(owner_key String key, name String key) -> AttributeConfig {
        // Standalone schema primitive constructor.
    }
}

ann default.AttributeConfig identity standalone

class Edge {
    attribute_config AttributeConfig

    fn create construct(owner_key String, name String) -> Edge {
        let created = construct attribute_config.create(owner_key = owner_key, name = name)
    }
}
"""

RELATIONSHIP_REFERENCE_KEY_TO_FK_CODE = """
class AttributeConfig {
    name String
}

class Attribute {
    attribute_config AttributeConfig key

    fn create construct (
        attribute_config_id UUID key
    ) -> Attribute {
        // Backward-compat constructor identity is primitive; class key comes from relationship rail.
    }
}
"""

RELATIONSHIP_REFERENCE_KEY_LIST_ASSOCIATION_TO_FK_CODE = """
class ClassConfig {
    name String
}

class ObjectConfigGraphOverlay {
    classes ClassConfig[] @ClassConfigOverlay key
}

edge ClassConfigOverlay {
    rendered_name String?
}
"""

REFERENCE_BIND_CODE = """
class Actor {
    authored_commits Commit[]
}

class Commit {
    author_id UUID
}

ann default.Commit::author_id reference port
ann default.Actor::authored_commits reference bind "default.Commit::author_id"
"""

REFERENCE_BIND_OPTIONAL_PORT_CODE = """
class Actor {
    authored_commits Commit[]
}

class Commit {
    author_id UUID?
}

ann default.Commit::author_id reference port
ann default.Actor::authored_commits reference bind "default.Commit::author_id"
"""

REFERENCE_BIND_MISSING_PORT_CODE = """
class Actor {
    authored_commits Commit[]
}

class Commit {
    author_id UUID
}

ann default.Actor::authored_commits reference bind "default.Commit::author_id"
"""

EXTERNAL_ONE_TO_MANY_CODE_DEP = """
class Task {
    id String
}
"""

EXTERNAL_ONE_TO_MANY_CODE_MOD = """
class SmartContractTaskConfig {
    tasks dep.workflow.task.Task[]
}
"""

EXTERNAL_DUPLICATE_ONE_TO_MANY_CODE_DEP = """
class NetworkOperationHop {
    id String
}
"""

EXTERNAL_DUPLICATE_ONE_TO_MANY_CODE_MOD = """
class Interface {
    source_network_operation_hops dep.network.topology.NetworkOperationHop[]
    target_network_operation_hops dep.network.topology.NetworkOperationHop[]
}
"""

EXTERNAL_MANY_TO_MANY_CODE_DEP = """
class Asset {
    id String
}
"""

EXTERNAL_MANY_TO_MANY_CODE_MOD = """
class Portfolio {
    assets dep.finance.asset.Asset[] @PortfolioAssetEdge many
}
edge PortfolioAssetEdge { note String }
"""

EXTERNAL_EDGE_RECEIVER_RESOLUTION_DEP_CODE = """
class CodePackage {
    relative_path String key
}
"""

EXTERNAL_EDGE_RECEIVER_RESOLUTION_MOD_CODE = """
class Repository {
    code_packages dep.code.package.CodePackage[] @RepositoryCodePackage

    fn create_code_package(relative_path String key) -> RepositoryCodePackage {
        let created = construct code_packages.create(relative_path = relative_path)
    }
}

edge RepositoryCodePackage {
    relative_path String key

    fn create construct(relative_path String key) -> RepositoryCodePackage {
        // Edge constructor stays parent-agnostic in authored Aware.
    }
}
"""

EXTERNAL_REFERENCE_BIND_PORT_DEP_CODE = """
class NetworkOperationHop {
    target_interface_id UUID
}

ann network.NetworkOperationHop::target_interface_id reference port
"""

EXTERNAL_REFERENCE_BIND_PORT_MOD_CODE = """
class Interface {
    target_network_operation_hops dep.network.NetworkOperationHop[]
}

ann interface.Interface::target_network_operation_hops reference bind "dep.network.NetworkOperationHop::target_interface_id"
"""

OPG_FRONTIER_ONE_TO_MANY_CODE = """
class Root {
    parents Parent[]
    children Child[]
}

class Parent {
    children Child[]
}

class Child { id String }

// Include both nodes in the projection, but omit Parent.children membership edge to make it a frontier soft ref.
projection P {
    root default.Root
    default.Root::parents
    default.Root::children
}
"""

OPG_FRONTIER_MANY_TO_MANY_CODE = """
class Root {
    a A? unique
    b B? unique
}

class A {
    bs B[] many
}

class B { id String }

// Include both nodes in the projection, but omit A.bs membership edge to make it a frontier soft ref.
projection P {
    root default.Root
    default.Root::a
    default.Root::b
}
"""

OPG_FRONTIER_ONE_TO_ONE_CODE = """
class Root {
    profiles Profile[]
    blobs Blob[]
}

class Blob { id String }

class Profile {
    image Blob? unique
}

// Include both nodes in the projection, but omit Profile.image membership edge to make it a frontier soft ref.
projection P {
    root default.Root
    default.Root::profiles
    default.Root::blobs
}
"""

MIRROR_PRESERVATION_CODE = """
enum CodeLanguageLike {
    python
}

class RepositoryDeltaUpdate {
    language CodeLanguageLike
}
"""


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


def _namespaces(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }


def _derive_runtime_opgs(graph: ObjectConfigGraph) -> ObjectConfigGraph:
    # Current canonical builder keeps projection declarations on the graph, while
    # concrete OPG instances are runtime-derived. Frontier SQL tests need the
    # derived runtime OPG lens before SQL lowering.
    if not graph.object_projection_graphs:
        graph.object_projection_graphs = build_object_projection_graphs(graph)
    return graph


def _get_class(graph: ObjectConfigGraph, name: str):
    for n in graph.object_config_graph_nodes:
        if n.class_config and n.class_config.name == name:
            return n.class_config
    raise KeyError(name)


def _get_enum(graph: ObjectConfigGraph, name: str):
    for n in graph.object_config_graph_nodes:
        if n.enum_config and n.enum_config.name == name:
            return n.enum_config
    raise KeyError(name)


def _get_relationship(
    graph: ObjectConfigGraph, source: str, attr_name: str, target: str
):
    # Relationship is declared by source attribute in canonical mode; match via rel-attr REFERENCE.
    src = _get_class(graph, source)
    tgt = _get_class(graph, target)
    for n in graph.object_config_graph_nodes:
        rel = n.class_config_relationship
        if rel is None:
            continue
        if rel.class_config_id != src.id or rel.target_class_config_id != tgt.id:
            continue
        # find forward reference attr name
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
            ):
                # resolve attribute config
                for link in src.class_config_attribute_configs:
                    if (
                        link.attribute_config
                        and link.attribute_config.id == ra.attribute_config_id
                    ):
                        if link.attribute_config.name == attr_name:
                            return rel

    # Fallback: some runtime graphs attach relationships directly to the source class (not as RELATIONSHIP nodes).
    for rel in src.class_config_relationships or []:
        if rel.class_config_id != src.id or rel.target_class_config_id != tgt.id:
            continue
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
            ):
                for link in src.class_config_attribute_configs:
                    if (
                        link.attribute_config
                        and link.attribute_config.id == ra.attribute_config_id
                    ):
                        if link.attribute_config.name == attr_name:
                            return rel
    raise KeyError((source, attr_name, target))


def _get_relationship_by_endpoints(
    graph: ObjectConfigGraph, source: str, target: str
) -> ClassConfigRelationship:
    src = _get_class(graph, source)
    tgt = _get_class(graph, target)
    for n in graph.object_config_graph_nodes:
        rel = n.class_config_relationship
        if rel is None:
            continue
        if rel.class_config_id == src.id and rel.target_class_config_id == tgt.id:
            return rel
    raise KeyError((source, target))


def test_aware_runtime_transformer(tmp_path: Path) -> None:
    """
    Advanced honesty validations:
    - Reverse load materializes reverse REFERENCE attribute and records it on relationship
    - Optional one-to-one produces optional FK (required=False)
    - ONE_TO_MANY materializes expected FK when no collision exists
    - Association (many-to-many) produces join FKs on association class + edge helper on source + relationship attribute roles
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "runtime.aware",
        DEFAULT_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="runtime",
        description="runtime",
        fqn_prefix="pkg",
        file_codes=[("runtime.aware", code)],
        namespace_by_code_id=ns,
    )

    transformer = AwareToRuntimeTransformer(namespace_by_code_id=ns)
    out = transformer.transform(built.graph)

    parent = _get_class(out, "Parent")
    child = _get_class(out, "Child")

    parent_attr_names = {
        l.attribute_config.name
        for l in parent.class_config_attribute_configs
        if l.attribute_config
    }
    child_attr_names = {
        l.attribute_config.name
        for l in child.class_config_attribute_configs
        if l.attribute_config
    }

    # Reverse load: Child.parent should be materialized
    assert "parent" in child_attr_names

    rel_parent_children = _get_relationship(out, "Parent", "children", "Child")
    # Reverse reference recorded on relationship
    assert any(
        ra.direction == ClassConfigRelationshipDirection.reverse
        and ra.role == ClassConfigRelationshipAttributeRole.reference
        for ra in rel_parent_children.class_config_relationship_attributes
    )

    # ONE_TO_MANY: FK on Child is materialized as parent_id.
    assert "parent_id" in child_attr_names
    parent_fk_attr = next(
        l.attribute_config
        for l in child.class_config_attribute_configs
        if l.attribute_config and l.attribute_config.name == "parent_id"
    )
    assert parent_fk_attr is not None
    # Reverse eager keeps FK optional in generated language models.
    assert parent_fk_attr.is_required is False
    assert any(
        ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        and ra.direction == ClassConfigRelationshipDirection.reverse
        for ra in rel_parent_children.class_config_relationship_attributes
    )

    # ONE_TO_ONE optional: Child.profile unique? => FK on Child, required=False
    rel_child_profile = _get_relationship(out, "Child", "profile", "Profile")
    assert rel_child_profile.relationship_type == ClassConfigRelationshipType.one_to_one
    fk_ids = [
        ra.attribute_config_id
        for ra in rel_child_profile.class_config_relationship_attributes
        if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        and ra.direction == ClassConfigRelationshipDirection.forward
    ]
    assert fk_ids
    fk_attr = next(
        l.attribute_config
        for l in child.class_config_attribute_configs
        if l.attribute_config and l.attribute_config.id == fk_ids[0]
    )
    assert fk_attr is not None
    assert fk_attr.is_required is False

    # MANY_TO_MANY association: Membership.users User[] @UserGroupEdge many
    membership = _get_class(out, "Membership")
    membership_names = {
        l.attribute_config.name
        for l in membership.class_config_attribute_configs
        if l.attribute_config
    }
    # Declaring relationship attr is preserved as a virtual view; canonical A->B remains,
    # while reified edges provide the runtime traversal path (A->Edge->B).
    assert "users" in membership_names
    users_attr = next(
        l.attribute_config
        for l in membership.class_config_attribute_configs
        if l.attribute_config and l.attribute_config.name == "users"
    )
    assert users_attr.is_virtual is True
    rel_membership_users = _get_relationship(out, "Membership", "users", "User")
    assert rel_membership_users.class_config_relationship_association_edge is not None
    assert rel_membership_users.reified_from_relationship_id is None
    assert rel_membership_users.reified_role is None

    assoc = _get_class(out, "UserGroupEdge")
    assoc_names = {
        l.attribute_config.name
        for l in assoc.class_config_attribute_configs
        if l.attribute_config
    }

    # Join FKs exist on association class
    assert "membership_id" in assoc_names
    assert "user_id" in assoc_names

    # Reified relationships exist: Membership -> UserGroupEdge -> User
    rel_membership_edges = _get_relationship_by_endpoints(
        out, "Membership", "UserGroupEdge"
    )
    assert (
        rel_membership_edges.relationship_type
        == ClassConfigRelationshipType.one_to_many
    )
    assert rel_membership_edges.reified_from_relationship_id == rel_membership_users.id
    assert (
        rel_membership_edges.reified_role
        == ClassConfigRelationshipReifiedRole.source_to_association
    )

    rel_edge_user = _get_relationship_by_endpoints(out, "UserGroupEdge", "User")
    assert rel_edge_user.relationship_type == ClassConfigRelationshipType.many_to_one
    assert rel_edge_user.reified_from_relationship_id == rel_membership_users.id
    assert (
        rel_edge_user.reified_role
        == ClassConfigRelationshipReifiedRole.association_to_target
    )

    # Edge helper attribute exists on Membership (reference for Membership -> UserGroupEdge)
    assert (
        "user_group_edges" in membership_names
        or "users_group_edges" in membership_names
    )

    # Relationship roles:
    # - Membership -> UserGroupEdge uses the edge helper as REFERENCE + association FK as REVERSE FOREIGN_KEY.
    roles_membership_edges = {
        (ra.direction, ra.role)
        for ra in rel_membership_edges.class_config_relationship_attributes
    }
    assert (
        ClassConfigRelationshipDirection.forward,
        ClassConfigRelationshipAttributeRole.reference,
    ) in roles_membership_edges
    assert (
        ClassConfigRelationshipDirection.reverse,
        ClassConfigRelationshipAttributeRole.foreign_key,
    ) in roles_membership_edges

    # - UserGroupEdge -> User uses association target ref as REFERENCE + association FK as FORWARD FOREIGN_KEY.
    roles_edge_user = {
        (ra.direction, ra.role)
        for ra in rel_edge_user.class_config_relationship_attributes
    }
    assert (
        ClassConfigRelationshipDirection.forward,
        ClassConfigRelationshipAttributeRole.reference,
    ) in roles_edge_user
    assert (
        ClassConfigRelationshipDirection.forward,
        ClassConfigRelationshipAttributeRole.foreign_key,
    ) in roles_edge_user


DUPLICATE_SYNTHESIZED_FK_NAME_CODE = """
class Parent {
    children Child[]
}

class Child {
    parent_id UUID
}
"""


def test_aware_runtime_transformer_rejects_duplicate_synthesized_fk_name(
    tmp_path: Path,
) -> None:
    """
    Duplicate synthetic/runtime-lowered attribute names are fail-closed.

    Contract:
    - Transformer must not auto-suffix collisions (e.g. parent_id_1).
    - It must raise with deterministic class + attribute context.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "duplicate_fk_name.aware",
        DUPLICATE_SYNTHESIZED_FK_NAME_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="duplicate_fk_name",
        description="duplicate_fk_name",
        fqn_prefix="pkg",
        file_codes=[("duplicate_fk_name.aware", code)],
        namespace_by_code_id=ns,
    )

    with pytest.raises(
        Exception,
        match=r"Class: pkg\.dom\.default\.Child, Attribute name parent_id already exists",
    ):
        AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)


def test_aware_runtime_transformer_materializes_path_scoped_constructors(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "path_scoped_constructor.aware", PATH_SCOPED_CONSTRUCTOR_CODE.strip()
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor",
        description="path_scoped_constructor",
        fqn_prefix="pkg",
        file_codes=[("path_scoped_constructor.aware", code)],
        namespace_by_code_id=ns,
    )

    source_parent = _get_class(built.graph, "Parent")
    source_add_child_fn = next(
        link.function_config
        for link in source_parent.class_config_function_configs
        if link.function_config is not None and link.function_config.name == "add_child"
    )
    source_child = _get_class(built.graph, "Child")
    source_template_ctor = next(
        link.function_config
        for link in source_child.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == "create_child"
    )
    source_template_value_input = next(
        edge
        for edge in source_template_ctor.function_config_attribute_configs
        if edge.type == FunctionAttributeType.input
        and edge.attribute_config is not None
        and edge.attribute_config.name == "value"
    )
    assert len(source_add_child_fn.invocations) == 1
    source_invocation = source_add_child_fn.invocations[0]
    source_function_impl_id = stable_function_impl_id(
        function_config_id=source_add_child_fn.id
    )
    source_instruction_id = stable_function_impl_instruction_id(
        function_impl_id=source_function_impl_id,
        type=FunctionImplInstructionType.invoke.value,
        sequence=0,
    )
    source_invoke_id = stable_function_impl_instruction_invoke_id(
        function_impl_instruction_id=source_instruction_id
    )
    source_add_child_fn.function_impl = FunctionImpl(
        id=source_function_impl_id,
        key="default",
        function_config_id=source_add_child_fn.id,
        instructions=[
            FunctionImplInstruction(
                id=source_instruction_id,
                function_impl_id=source_function_impl_id,
                type=FunctionImplInstructionType.invoke,
                sequence=0,
                instruction_invoke=FunctionImplInstructionInvoke(
                    id=source_invoke_id,
                    function_impl_instruction_id=source_instruction_id,
                    target_function_config_id=source_invocation.target_function_config_id,
                    class_config_relationship_id=source_invocation.class_config_relationship_id,
                    kind=FunctionImplInvokeKind.construct,
                    attribute_configs=[
                        FunctionImplInstructionInvokeAttributeConfig(
                            id=UUID("9c76f4f8-11e8-4a62-b9dd-4cbfca10e7de"),
                            function_impl_instruction_invoke_id=source_invoke_id,
                            attribute_config_id=source_template_value_input.attribute_config_id,
                            attribute_config=source_template_value_input.attribute_config,
                            value_expr={"kind": "reference", "name": "value"},
                            position=0,
                        )
                    ],
                ),
            )
        ],
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)
    assert not [
        node
        for node in out.object_config_graph_nodes
        if node.type == ObjectConfigGraphNodeType.function
    ]

    parent = _get_class(out, "Parent")
    child = _get_class(out, "Child")

    child_fn_by_name = {
        link.function_config.name: link.function_config
        for link in child.class_config_function_configs
        if link.function_config is not None
    }
    path_ctor_name = "create_child_via_parent"
    assert path_ctor_name in child_fn_by_name

    path_ctor = child_fn_by_name[path_ctor_name]
    path_inputs = [
        edge
        for edge in sorted(
            path_ctor.function_config_attribute_configs, key=lambda edge: edge.position
        )
        if edge.type == FunctionAttributeType.input
        and edge.attribute_config is not None
    ]
    assert [edge.attribute_config.name for edge in path_inputs][:2] == [
        "parent_id",
        "value",
    ]
    # Path-scoped constructor lowering injects parent traversal identity as key.
    assert path_inputs[0].is_identity_key is True
    # Propagation rail is class-identity SSOT: synthesized FK link is marked as identity key.
    child_parent_fk_link = next(
        link
        for link in child.class_config_attribute_configs
        if link.attribute_config and link.attribute_config.name == "parent_id"
    )
    assert child_parent_fk_link.is_identity_key is True

    add_child_fn = next(
        link.function_config
        for link in parent.class_config_function_configs
        if link.function_config is not None and link.function_config.name == "add_child"
    )
    assert len(add_child_fn.invocations) == 1
    invocation = add_child_fn.invocations[0]
    assert invocation.target_function_config_id == path_ctor.id
    assert invocation.target_function_config is not None
    assert invocation.target_function_config.name == path_ctor_name

    function_impl = add_child_fn.function_impl
    assert function_impl is not None
    impl_construct_invokes = [
        ins.instruction_invoke
        for ins in function_impl.instructions
        if ins.instruction_invoke is not None
        and ins.instruction_invoke.kind.value == "construct"
    ]
    assert impl_construct_invokes
    for impl_invoke in impl_construct_invokes:
        assert impl_invoke.target_function_config_id == path_ctor.id
        assert impl_invoke.target_function_config is not None
        assert impl_invoke.target_function_config.name == path_ctor_name
        assert impl_invoke.attribute_configs
        binding_by_name = {
            binding.attribute_config.name: binding
            for binding in impl_invoke.attribute_configs
            if binding.attribute_config is not None
        }
        assert list(binding_by_name)[:2] == ["parent_id", "value"]

        parent_binding = binding_by_name["parent_id"]
        assert dict(parent_binding.value_expr or {}) == {"kind": "self_id"}

        value_binding = binding_by_name["value"]
        assert (
            value_binding.attribute_config_id
            != source_template_value_input.attribute_config_id
        )
        assert dict(value_binding.value_expr or {}) == {
            "kind": "reference",
            "name": "value",
        }


def test_aware_runtime_transformer_preserves_object_config_graph_mirrors_in_runtime_output(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "mirror_preservation.aware", MIRROR_PRESERVATION_CODE.strip()
    )
    ns = _namespaces(
        fqn_prefix="pkg_api", namespace="dom.repository", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="mirror_preservation",
        description="mirror_preservation",
        fqn_prefix="pkg_api",
        file_codes=[("mirror_preservation.aware", code)],
        namespace_by_code_id=ns,
    )

    enum_cfg = _get_enum(built.graph, "CodeLanguageLike")
    built.graph.object_config_graph_mirrors.append(
        ObjectConfigGraphMirror(
            fqn_prefix="pkg_api",
            namespace="dom.repository",
            target_text="dep.code.CodeLanguageLike",
            layout_kind="aware",
            relative_path="repository/repository_types.aware",
            source_position=1,
            target_kind=ObjectConfigGraphMirrorTargetKind.enum,
            object_config_graph_id=built.graph.id,
            source_object_config_graph_id=built.graph.id,
            enum_config_id=enum_cfg.id,
            code_section_mirror_id=UUID("85fd2dbf-6b4d-4ec4-94dd-c56f17a9612c"),
        )
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    assert len(out.object_config_graph_mirrors) == 1
    mirror = out.object_config_graph_mirrors[0]
    assert mirror.target_text == "dep.code.CodeLanguageLike"
    assert mirror.enum_config_id == enum_cfg.id
    assert mirror.relative_path == "repository/repository_types.aware"
    assert out.hash != built.graph.hash


def test_aware_runtime_transformer_materializes_path_scoped_constructors_one_to_one_containment(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "path_scoped_constructor_one_to_one.aware",
        PATH_SCOPED_CONSTRUCTOR_ONE_TO_ONE_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor_one_to_one",
        description="path_scoped_constructor_one_to_one",
        fqn_prefix="pkg",
        file_codes=[("path_scoped_constructor_one_to_one.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    child = _get_class(out, "Child")
    rel = _get_relationship(out, "Parent", "child", "Child")

    rel_fk = [
        ra
        for ra in rel.class_config_relationship_attributes
        if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        and ra.direction == ClassConfigRelationshipDirection.reverse
    ]
    assert len(rel_fk) == 1

    child_parent_fk_link = next(
        link
        for link in child.class_config_attribute_configs
        if link.attribute_config and link.attribute_config.name == "parent_id"
    )
    assert child_parent_fk_link.is_identity_key is True

    path_ctor = next(
        link.function_config
        for link in child.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == "create_child_via_parent"
    )
    path_inputs = [
        edge
        for edge in sorted(
            path_ctor.function_config_attribute_configs, key=lambda edge: edge.position
        )
        if edge.type == FunctionAttributeType.input
        and edge.attribute_config is not None
    ]
    assert path_inputs[0].attribute_config.name == "parent_id"
    assert path_inputs[0].is_identity_key is True


def test_aware_runtime_transformer_path_constructor_rejects_no_fk_guess_on_many_to_many(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "path_scoped_constructor_many_to_many.aware",
        PATH_SCOPED_CONSTRUCTOR_MANY_TO_MANY_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor_many_to_many",
        description="path_scoped_constructor_many_to_many",
        fqn_prefix="pkg",
        file_codes=[("path_scoped_constructor_many_to_many.aware", code)],
        namespace_by_code_id=ns,
    )

    with pytest.raises(
        ValueError,
        match=r"containment relationship cardinality is not allowed for propagation identity rails",
    ):
        AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)


def test_aware_runtime_transformer_path_constructor_association_fk_resolution_is_owner_side(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "path_scoped_constructor_association_edge.aware",
        PATH_SCOPED_CONSTRUCTOR_ASSOCIATION_EDGE_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor_association_edge",
        description="path_scoped_constructor_association_edge",
        fqn_prefix="pkg",
        file_codes=[("path_scoped_constructor_association_edge.aware", code)],
        namespace_by_code_id=ns,
    )

    transformer = AwareToRuntimeTransformer(namespace_by_code_id=ns)
    out = transformer.transform(built.graph)

    rel_parent_children = _get_relationship(out, "Parent", "children", "Child")
    rel_edge_child = _get_relationship_by_endpoints(out, "ParentChildEdge", "Child")
    assert rel_edge_child.relationship_type == ClassConfigRelationshipType.one_to_one
    assert (
        rel_edge_child.reified_role
        == ClassConfigRelationshipReifiedRole.association_to_target
    )

    edge = _get_class(out, "ParentChildEdge")
    edge_attrs_by_name = {
        link.attribute_config.name: link.attribute_config
        for link in edge.class_config_attribute_configs
        if link.attribute_config is not None
    }
    parent_fk_attr = edge_attrs_by_name["parent_id"]
    child_fk_attr = edge_attrs_by_name["child_id"]

    # Relationship-side disambiguation is deterministic by owner-side direction.
    function_surface_support = RuntimeFunctionSurfaceSupport(
        support=RuntimeTransformSupport(namespace_by_code_id=ns),
    )
    resolved_parent_fk = function_surface_support._resolve_parent_fk_attribute_for_path(
        target_class=edge,
        owner_class=_get_class(out, "Parent"),
        relationship=rel_parent_children,
        fk_attrs_by_relationship_and_owner_class={
            (rel_parent_children.id, edge.id): (
                (
                    ClassConfigRelationshipAttribute(
                        id=UUID("90dc4bb4-cd54-4b86-95fb-e9884f24824c"),
                        class_config_relationship_id=rel_parent_children.id,
                        attribute_config_id=parent_fk_attr.id,
                        direction=ClassConfigRelationshipDirection.forward,
                        role=ClassConfigRelationshipAttributeRole.foreign_key,
                    ),
                    parent_fk_attr,
                ),
                (
                    ClassConfigRelationshipAttribute(
                        id=UUID("5915bff3-915a-48e9-90af-ea582ac74cc1"),
                        class_config_relationship_id=rel_parent_children.id,
                        attribute_config_id=child_fk_attr.id,
                        direction=ClassConfigRelationshipDirection.reverse,
                        role=ClassConfigRelationshipAttributeRole.foreign_key,
                    ),
                    child_fk_attr,
                ),
            ),
        },
    )
    assert resolved_parent_fk.name == "parent_id"

    path_ctor = next(
        link.function_config
        for link in edge.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == "build_via_parent"
    )
    path_inputs = [
        edge
        for edge in sorted(
            path_ctor.function_config_attribute_configs, key=lambda edge: edge.position
        )
        if edge.type == FunctionAttributeType.input
        and edge.attribute_config is not None
    ]
    # Ambiguous dual-FK relationships resolve deterministically to the owner-side FK.
    assert path_inputs[0].attribute_config.name == "parent_id"
    assert path_inputs[0].is_identity_key is True
    assert path_inputs[0].attribute_config.is_required is True
    assert path_inputs[0].attribute_config.default_value is None

    edge_parent_fk_link = next(
        link
        for link in edge.class_config_attribute_configs
        if link.attribute_config and link.attribute_config.name == "parent_id"
    )
    assert edge_parent_fk_link.is_identity_key is True


def test_aware_runtime_transformer_maps_association_constructor_target_key_to_fk_identity(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "path_scoped_constructor_association_edge_reference_key.aware",
        PATH_SCOPED_CONSTRUCTOR_ASSOCIATION_EDGE_REFERENCE_KEY_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor_association_edge_reference_key",
        description="path_scoped_constructor_association_edge_reference_key",
        fqn_prefix="pkg",
        file_codes=[
            ("path_scoped_constructor_association_edge_reference_key.aware", code)
        ],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    edge = _get_class(out, "ParentChildEdge")
    edge_links = {
        link.attribute_config.name: link
        for link in edge.class_config_attribute_configs
        if link.attribute_config is not None
    }
    assert edge_links["parent_id"].is_identity_key is True
    assert edge_links["child_id"].is_identity_key is True

    path_ctor = next(
        link.function_config
        for link in edge.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == "build_via_parent"
    )
    path_inputs = [
        edge
        for edge in sorted(
            path_ctor.function_config_attribute_configs, key=lambda edge: edge.position
        )
        if edge.type == FunctionAttributeType.input
        and edge.attribute_config is not None
    ]
    assert [edge.attribute_config.name for edge in path_inputs] == [
        "parent_id",
        "child_id",
    ]
    assert path_inputs[0].is_identity_key is True
    assert path_inputs[1].is_identity_key is True


def test_aware_runtime_transformer_does_not_materialize_path_constructor_for_standalone_target(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "path_scoped_constructor_standalone_target.aware",
        PATH_SCOPED_CONSTRUCTOR_STANDALONE_TARGET_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor_standalone_target",
        description="path_scoped_constructor_standalone_target",
        fqn_prefix="pkg",
        file_codes=[("path_scoped_constructor_standalone_target.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    edge = _get_class(out, "Edge")
    attribute_config = _get_class(out, "AttributeConfig")

    attribute_config_function_names = {
        link.function_config.name
        for link in attribute_config.class_config_function_configs
        if link.function_config is not None
    }
    assert "create" in attribute_config_function_names
    assert "create_via_edge" not in attribute_config_function_names

    edge_create_fn = next(
        link.function_config
        for link in edge.class_config_function_configs
        if link.function_config is not None and link.function_config.name == "create"
    )
    by_name = {
        edge.attribute_config.name: edge
        for edge in edge_create_fn.function_config_attribute_configs
        if edge.attribute_config is not None
    }
    assert by_name["owner_key"].is_identity_key is False
    assert by_name["name"].is_identity_key is False
    assert len(edge_create_fn.invocations) == 1
    invocation = edge_create_fn.invocations[0]
    assert invocation.target_function_config is not None
    assert invocation.target_function_config.name == "create"


def test_aware_runtime_transformer_materializes_function_impl_for_path_constructor_with_standalone_target(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "path_scoped_constructor_mixed_standalone_impl.aware",
        PATH_SCOPED_CONSTRUCTOR_MIXED_CONTAINED_AND_STANDALONE_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor_mixed_standalone_impl",
        description="path_scoped_constructor_mixed_standalone_impl",
        fqn_prefix="pkg",
        file_codes=[("path_scoped_constructor_mixed_standalone_impl.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    edge = _get_class(out, "Edge")
    path_fn = next(
        link.function_config
        for link in edge.class_config_function_configs
        if link.function_config is not None
        and link.function_config.name == "create_via_parent"
    )

    assert path_fn.function_impl is not None
    assert len(path_fn.function_impl.instructions) == 1
    instruction = path_fn.function_impl.instructions[0]
    assert instruction.type == FunctionImplInstructionType.invoke
    assert instruction.instruction_invoke is not None
    invoke = instruction.instruction_invoke
    assert invoke.kind == FunctionImplInvokeKind.construct
    assert invoke.target_function_config is not None
    assert invoke.target_function_config.name == "create"
    assert [binding.attribute_config.name for binding in invoke.attribute_configs] == [
        "owner_key",
        "name",
    ]
    by_name = {
        edge.attribute_config.name: edge
        for edge in path_fn.function_config_attribute_configs
        if edge.attribute_config is not None
    }
    assert by_name["owner_key"].is_identity_key is False
    assert by_name["name"].is_identity_key is False


def test_aware_runtime_transformer_reified_containment_target_uses_child_fk_only(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "edge_target_containment_child_fk_only.aware",
        EDGE_TARGET_CONTAINMENT_CHILD_FK_ONLY_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="edge_target_containment_child_fk_only",
        description="edge_target_containment_child_fk_only",
        fqn_prefix="pkg",
        file_codes=[("edge_target_containment_child_fk_only.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    edge = _get_class(out, "PackageCode")
    child = _get_class(out, "Code")
    rel = _get_relationship(out, "PackageCode", "code", "Code")

    edge_links = {
        link.attribute_config.name: link
        for link in edge.class_config_attribute_configs
        if link.attribute_config is not None
    }
    child_links = {
        link.attribute_config.name: link
        for link in child.class_config_attribute_configs
        if link.attribute_config is not None
    }

    assert "package_id" in edge_links
    assert "code" in edge_links
    assert "code_id" not in edge_links
    assert "package_code_id" in child_links
    child_fk_link = child_links["package_code_id"]
    assert child_fk_link.is_identity_key is True
    assert child_fk_link.attribute_config is not None

    fk_rel_attrs = [
        rel_attr
        for rel_attr in rel.class_config_relationship_attributes
        if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
    ]
    assert len(fk_rel_attrs) == 1
    assert fk_rel_attrs[0].direction == ClassConfigRelationshipDirection.reverse
    assert fk_rel_attrs[0].attribute_config_id == child_fk_link.attribute_config.id


def test_aware_runtime_transformer_keeps_standalone_template_when_other_path_constructors_exist(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "path_scoped_constructor_mixed_contained_and_standalone.aware",
        PATH_SCOPED_CONSTRUCTOR_MIXED_CONTAINED_AND_STANDALONE_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="path_scoped_constructor_mixed_contained_and_standalone",
        description="path_scoped_constructor_mixed_contained_and_standalone",
        fqn_prefix="pkg",
        file_codes=[
            ("path_scoped_constructor_mixed_contained_and_standalone.aware", code)
        ],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    child = _get_class(out, "Child")
    edge = _get_class(out, "Edge")
    attribute_config = _get_class(out, "AttributeConfig")

    child_function_names = {
        link.function_config.name
        for link in child.class_config_function_configs
        if link.function_config is not None
    }
    edge_function_names = {
        link.function_config.name
        for link in edge.class_config_function_configs
        if link.function_config is not None
    }
    attribute_config_function_names = {
        link.function_config.name
        for link in attribute_config.class_config_function_configs
        if link.function_config is not None
    }

    assert "create_child" not in child_function_names
    assert "create_child_via_parent" in child_function_names
    assert "create" not in edge_function_names
    assert "create_via_parent" in edge_function_names
    assert "create" in attribute_config_function_names
    assert "create_via_edge" not in attribute_config_function_names


def test_aware_runtime_transformer_maps_relationship_reference_key_to_fk_identity(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "relationship_reference_key_to_fk.aware",
        RELATIONSHIP_REFERENCE_KEY_TO_FK_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="relationship_reference_key_to_fk",
        description="relationship_reference_key_to_fk",
        fqn_prefix="pkg",
        file_codes=[("relationship_reference_key_to_fk.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    attribute_cls = _get_class(out, "Attribute")
    rel = _get_relationship(out, "Attribute", "attribute_config", "AttributeConfig")

    by_name = {
        link.attribute_config.name: link
        for link in attribute_cls.class_config_attribute_configs
        if link.attribute_config is not None
    }
    assert by_name["attribute_config"].is_identity_key is False
    assert by_name["attribute_config_id"].is_identity_key is True

    fk_attr_ids = [
        ra.attribute_config_id
        for ra in rel.class_config_relationship_attributes
        if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        and ra.direction == ClassConfigRelationshipDirection.forward
    ]
    assert fk_attr_ids == [by_name["attribute_config_id"].attribute_config.id]
    class_rel = next(
        relationship
        for relationship in attribute_cls.class_config_relationships
        if relationship.id == rel.id
    )
    assert {
        (ra.role, ra.direction, ra.attribute_config_id)
        for ra in class_rel.class_config_relationship_attributes
    } == {
        (ra.role, ra.direction, ra.attribute_config_id)
        for ra in rel.class_config_relationship_attributes
    }


def test_aware_runtime_transformer_maps_relationship_reference_key_list_association_to_fk_identity(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "relationship_reference_key_list_association_to_fk.aware",
        RELATIONSHIP_REFERENCE_KEY_LIST_ASSOCIATION_TO_FK_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="relationship_reference_key_list_association_to_fk",
        description="relationship_reference_key_list_association_to_fk",
        fqn_prefix="pkg",
        file_codes=[("relationship_reference_key_list_association_to_fk.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    overlay = _get_class(out, "ObjectConfigGraphOverlay")
    edge = _get_class(out, "ClassConfigOverlay")
    rel = _get_relationship(out, "ObjectConfigGraphOverlay", "classes", "ClassConfig")

    overlay_links = {
        link.attribute_config.name: link
        for link in overlay.class_config_attribute_configs
        if link.attribute_config is not None
    }
    assert overlay_links["classes"].is_identity_key is False

    edge_links = {
        link.attribute_config.name: link
        for link in edge.class_config_attribute_configs
        if link.attribute_config is not None
    }
    overlay_fk_link = edge_links["object_config_graph_overlay_id"]
    target_fk_link = edge_links["class_config_id"]
    assert overlay_fk_link.is_identity_key is True
    assert target_fk_link.is_identity_key is True

    fk_attrs_by_id = {
        rel_attr.attribute_config_id: rel_attr
        for rel_attr in rel.class_config_relationship_attributes
        if rel_attr.role == ClassConfigRelationshipAttributeRole.foreign_key
    }
    overlay_fk_rel_attr = fk_attrs_by_id[overlay_fk_link.attribute_config.id]
    target_fk_rel_attr = fk_attrs_by_id[target_fk_link.attribute_config.id]
    assert overlay_fk_rel_attr.direction == ClassConfigRelationshipDirection.forward
    assert target_fk_rel_attr.direction == ClassConfigRelationshipDirection.reverse


def test_aware_runtime_transformer_reference_bind_reuses_port_fk(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "ref_bind.aware", REFERENCE_BIND_CODE.strip())
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="ref_bind",
        description="ref_bind",
        fqn_prefix="pkg",
        file_codes=[("ref_bind.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    actor = _get_class(out, "Actor")
    commit = _get_class(out, "Commit")

    commit_attr_names = {
        l.attribute_config.name
        for l in commit.class_config_attribute_configs
        if l.attribute_config
    }
    # Without bind, ONE_TO_MANY would synthesize actor_id on Commit.
    assert "actor_id" not in commit_attr_names

    rel = _get_relationship(out, "Actor", "authored_commits", "Commit")
    fk_ids = [
        ra.attribute_config_id
        for ra in rel.class_config_relationship_attributes
        if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        and ra.direction == ClassConfigRelationshipDirection.reverse
    ]
    assert fk_ids
    fk_attr = next(
        l.attribute_config
        for l in commit.class_config_attribute_configs
        if l.attribute_config and l.attribute_config.id == fk_ids[0]
    )
    assert fk_attr is not None
    assert fk_attr.name == "author_id"


def test_aware_runtime_transformer_reference_bind_allows_optional_uuid_port(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "ref_bind_optional_port.aware",
        REFERENCE_BIND_OPTIONAL_PORT_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="ref_bind_optional_port",
        description="ref_bind_optional_port",
        fqn_prefix="pkg",
        file_codes=[("ref_bind_optional_port.aware", code)],
        namespace_by_code_id=ns,
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)

    commit = _get_class(out, "Commit")
    commit_attr_names = {
        l.attribute_config.name
        for l in commit.class_config_attribute_configs
        if l.attribute_config
    }
    # Without bind, ONE_TO_MANY would synthesize actor_id on Commit.
    assert "actor_id" not in commit_attr_names

    rel = _get_relationship(out, "Actor", "authored_commits", "Commit")
    fk_ids = [
        ra.attribute_config_id
        for ra in rel.class_config_relationship_attributes
        if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        and ra.direction == ClassConfigRelationshipDirection.reverse
    ]
    assert fk_ids
    fk_attr = next(
        l.attribute_config
        for l in commit.class_config_attribute_configs
        if l.attribute_config and l.attribute_config.id == fk_ids[0]
    )
    assert fk_attr is not None
    assert fk_attr.name == "author_id"


def test_aware_runtime_transformer_reference_bind_requires_port(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "ref_bind_missing_port.aware",
        REFERENCE_BIND_MISSING_PORT_CODE.strip(),
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="ref_bind_missing_port",
        description="ref_bind_missing_port",
        fqn_prefix="pkg",
        file_codes=[("ref_bind_missing_port.aware", code)],
        namespace_by_code_id=ns,
    )

    with pytest.raises(
        ValueError, match="reference bind target must be declared as a reference port"
    ):
        AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)


def test_aware_runtime_transformer_reference_bind_can_resolve_ports_from_external_graphs_by_id(
    tmp_path: Path,
) -> None:
    """
    Regression: external dependency graphs are not guaranteed to be reachable via
    `object_config_graph_relationships[*].target_object_config_graph` (e.g., graphs loaded
    from `.aware/environment.json`). Reference bind validation must still be able to see
    reference ports declared on dependency graphs via `external_graphs_by_id`.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path,
        "dep_network_op_hop.aware",
        EXTERNAL_REFERENCE_BIND_PORT_DEP_CODE.strip(),
    )
    dep_ns = _namespaces(
        fqn_prefix="dep",
        namespace="network",
        code_ids=[dep_code.id],
    )
    dep = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep",
        file_codes=[("dep_network_op_hop.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    mod_code = _build_code(
        tmp_path,
        "mod_interface.aware",
        EXTERNAL_REFERENCE_BIND_PORT_MOD_CODE.strip(),
    )
    mod_ns = _namespaces(
        fqn_prefix="mod",
        namespace="interface",
        code_ids=[mod_code.id],
    )
    mod = build_object_config_graph_from_code(
        name="mod",
        description="mod",
        fqn_prefix="mod",
        file_codes=[("mod_interface.aware", mod_code)],
        namespace_by_code_id=mod_ns,
        external_graphs=[dep.graph],
    )

    cross = mod.cross_relationships_by_target_ocg.get(dep.graph.id)
    assert cross, "Expected cross-OCG relationships to dependency graph"
    mod.graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=mod.graph.id,
            target_object_config_graph_id=dep.graph.id,
            # Intentionally omit `target_object_config_graph` to simulate environment.json-loaded graphs.
            class_config_relationships=cross,
        )
    )

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=mod_ns,
        external_graphs_by_id={dep.graph.id: dep.graph},
    ).transform(mod.graph)

    assert runtime.object_config_graph_relationships
    rel = runtime.object_config_graph_relationships[0].class_config_relationships[0]

    hop = _get_class(dep.graph, "NetworkOperationHop")
    target_fk_attr_id = next(
        link.attribute_config.id
        for link in hop.class_config_attribute_configs
        if link.attribute_config is not None
        and link.attribute_config.name == "target_interface_id"
    )
    assert any(
        ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        and ra.attribute_config_id == target_fk_attr_id
        for ra in rel.class_config_relationship_attributes
    )


def test_aware_runtime_transformer_reference_ports_are_idempotent_across_graph_variants(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path,
        "dep_network_op_hop.aware",
        EXTERNAL_REFERENCE_BIND_PORT_DEP_CODE.strip(),
    )
    dep_ns = _namespaces(
        fqn_prefix="dep",
        namespace="network",
        code_ids=[dep_code.id],
    )
    dep = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep",
        file_codes=[("dep_network_op_hop.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )
    dep_variant = dep.graph.model_copy(deep=True, update={"id": uuid4()})

    mod_code = _build_code(
        tmp_path,
        "mod_interface.aware",
        EXTERNAL_REFERENCE_BIND_PORT_MOD_CODE.strip(),
    )
    mod_ns = _namespaces(
        fqn_prefix="mod",
        namespace="interface",
        code_ids=[mod_code.id],
    )
    mod = build_object_config_graph_from_code(
        name="mod",
        description="mod",
        fqn_prefix="mod",
        file_codes=[("mod_interface.aware", mod_code)],
        namespace_by_code_id=mod_ns,
        external_graphs=[dep.graph],
    )
    cross = mod.cross_relationships_by_target_ocg.get(dep.graph.id)
    assert cross
    mod.graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=mod.graph.id,
            target_object_config_graph_id=dep.graph.id,
            target_object_config_graph=dep.graph,
            class_config_relationships=cross,
        )
    )

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=mod_ns,
        external_graphs_by_id={dep_variant.id: dep_variant},
    ).transform(mod.graph)

    assert runtime.object_config_graph_relationships


def test_runtime_transform_support_preserves_external_class_namespace(
    tmp_path: Path,
) -> None:
    """
    Runtime namespace contract:
    - A derived runtime graph may include a class owned by an external OCG.
    - When explicit external graph context is supplied, the namespace bundle must
      keep the external class's owning namespace instead of assigning local fallback.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path,
        "storage_bucket.aware",
        "class StorageBucket {\n    name String\n}\n",
    )
    dep_ns = _namespaces(
        fqn_prefix="aware_storage",
        namespace="bucket",
        code_ids=[dep_code.id],
    )
    dep = build_object_config_graph_from_code(
        name="storage",
        description="storage",
        fqn_prefix="aware_storage",
        file_codes=[("storage_bucket.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    local_code = _build_code(
        tmp_path,
        "experience_profile.aware",
        "class ExperienceProfile {\n    title String\n}\n",
    )
    local_ns = _namespaces(
        fqn_prefix="aware_experience",
        namespace="profile",
        code_ids=[local_code.id],
    )
    local = build_object_config_graph_from_code(
        name="experience",
        description="experience",
        fqn_prefix="aware_experience",
        file_codes=[("experience_profile.aware", local_code)],
        namespace_by_code_id=local_ns,
    )

    profile = _get_class(local.graph, "ExperienceProfile")
    bucket = _get_class(dep.graph, "StorageBucket")
    bundle = RuntimeTransformSupport(
        namespace_by_code_id=local_ns,
        external_graphs_by_id={dep.graph.id: dep.graph},
    ).resolve_namespace_bundle_for_derived_graph(
        source_graph=local.graph,
        derived_class_configs=[profile, bucket],
        derived_relationships=[],
        derived_enum_configs=[],
        derived_function_configs=[],
        namespace_by_code_id=local_ns,
    )

    assert bundle.namespace_for_class(profile.id) == NamespacePath(
        package="aware_experience",
        namespace="profile",
    )
    assert bundle.namespace_for_class(bucket.id) == NamespacePath(
        package="aware_storage",
        namespace="bucket",
    )


def test_aware_runtime_transformer_skips_external_fk_synthesis_by_default(
    tmp_path: Path,
) -> None:
    """
    Cross-package contract:
    - The runtime transformer must never mutate dependency packages (external classes) by synthesizing FK columns.
    - For ONE_TO_MANY where the FK would live on an external target class, we skip FK synthesis (no crash).
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path, "task.aware", EXTERNAL_ONE_TO_MANY_CODE_DEP.strip()
    )
    dep_ns = _namespaces(
        fqn_prefix="dep", namespace="workflow.task", code_ids=[dep_code.id]
    )
    dep = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep",
        file_codes=[("task.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    mod_code = _build_code(tmp_path, "mod.aware", EXTERNAL_ONE_TO_MANY_CODE_MOD.strip())
    mod_ns = _namespaces(
        fqn_prefix="mod",
        namespace="economy.smart_contract",
        code_ids=[mod_code.id],
    )
    mod = build_object_config_graph_from_code(
        name="mod",
        description="mod",
        fqn_prefix="mod",
        file_codes=[("mod.aware", mod_code)],
        namespace_by_code_id=mod_ns,
        external_graphs=[dep.graph],
    )

    cross = mod.cross_relationships_by_target_ocg.get(dep.graph.id)
    assert cross, "Expected cross-OCG relationships to dependency graph"
    mod.graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=mod.graph.id,
            target_object_config_graph_id=dep.graph.id,
            target_object_config_graph=dep.graph,
            class_config_relationships=cross,
        )
    )

    out = AwareToRuntimeTransformer(namespace_by_code_id=mod_ns).transform(mod.graph)
    assert out.object_config_graph_relationships
    rel = out.object_config_graph_relationships[0].class_config_relationships[0]
    assert rel.relationship_type == ClassConfigRelationshipType.one_to_many
    assert not any(
        ra.role == ClassConfigRelationshipAttributeRole.foreign_key
        for ra in rel.class_config_relationship_attributes
    )


def test_sql_transformer_synthesizes_join_table_for_external_one_to_many(
    tmp_path: Path,
) -> None:
    """
    SQL contract:
    - When a ONE_TO_MANY would place an FK column on an external (dependency) class, represent it via a join table.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path, "task.aware", EXTERNAL_ONE_TO_MANY_CODE_DEP.strip()
    )
    dep_ns = _namespaces(
        fqn_prefix="dep", namespace="workflow.task", code_ids=[dep_code.id]
    )
    dep = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep",
        file_codes=[("task.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    mod_code = _build_code(tmp_path, "mod.aware", EXTERNAL_ONE_TO_MANY_CODE_MOD.strip())
    mod_ns = _namespaces(
        fqn_prefix="mod",
        namespace="economy.smart_contract",
        code_ids=[mod_code.id],
    )
    mod = build_object_config_graph_from_code(
        name="mod",
        description="mod",
        fqn_prefix="mod",
        file_codes=[("mod.aware", mod_code)],
        namespace_by_code_id=mod_ns,
        external_graphs=[dep.graph],
    )
    cross = mod.cross_relationships_by_target_ocg.get(dep.graph.id)
    assert cross, "Expected cross-OCG relationships to dependency graph"
    mod.graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=mod.graph.id,
            target_object_config_graph_id=dep.graph.id,
            target_object_config_graph=dep.graph,
            class_config_relationships=cross,
        )
    )

    runtime = AwareToRuntimeTransformer(namespace_by_code_id=mod_ns).transform(
        mod.graph
    )
    sql_graph = RuntimeToSQLTransformer().transform(runtime)
    # Mirror pipeline behavior: preserve cross-OCG relationships on the lowered SQL graph.
    sql_graph.object_config_graph_relationships = list(
        runtime.object_config_graph_relationships
    )

    join = _get_class(sql_graph, "SmartContractTaskConfigTaskJoin")
    join_attr_names = {
        l.attribute_config.name
        for l in join.class_config_attribute_configs
        if l.attribute_config
    }
    assert "smart_contract_task_config_id" in join_attr_names
    assert "task_id" in join_attr_names


def test_sql_transformer_disambiguates_external_one_to_many_join_names_for_same_endpoints(
    tmp_path: Path,
) -> None:
    """
    SQL lowering must preserve relationship role identity in generated join class names
    when multiple external ONE_TO_MANY rails share the same endpoint pair.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path,
        "network_operation_hop.aware",
        EXTERNAL_DUPLICATE_ONE_TO_MANY_CODE_DEP.strip(),
    )
    dep_ns = _namespaces(
        fqn_prefix="dep",
        namespace="network.topology",
        code_ids=[dep_code.id],
    )
    dep = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep",
        file_codes=[("network_operation_hop.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    mod_code = _build_code(
        tmp_path, "interface.aware", EXTERNAL_DUPLICATE_ONE_TO_MANY_CODE_MOD.strip()
    )
    mod_ns = _namespaces(
        fqn_prefix="mod",
        namespace="interface.control",
        code_ids=[mod_code.id],
    )
    mod = build_object_config_graph_from_code(
        name="mod",
        description="mod",
        fqn_prefix="mod",
        file_codes=[("interface.aware", mod_code)],
        namespace_by_code_id=mod_ns,
        external_graphs=[dep.graph],
    )
    cross = mod.cross_relationships_by_target_ocg.get(dep.graph.id)
    assert cross is not None
    assert len(cross) == 2
    mod.graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=mod.graph.id,
            target_object_config_graph_id=dep.graph.id,
            target_object_config_graph=dep.graph,
            class_config_relationships=cross,
        )
    )

    runtime = AwareToRuntimeTransformer(namespace_by_code_id=mod_ns).transform(
        mod.graph
    )
    sql_graph = RuntimeToSQLTransformer().transform(runtime)

    source_join = _get_class(sql_graph, "InterfaceSourceNetworkOperationHopJoin")
    target_join = _get_class(sql_graph, "InterfaceTargetNetworkOperationHopJoin")
    sql_class_names = {
        node.class_config.name
        for node in sql_graph.object_config_graph_nodes
        if node.class_config is not None
    }

    assert source_join.id != target_join.id
    assert "InterfaceNetworkOperationHopJoin" not in sql_class_names
    build_object_config_graph_overlays_from_annotations(sql_graph)


def test_sql_renderer_skips_fk_constraints_for_frontier_one_to_many(
    tmp_path: Path,
) -> None:
    """
    SQL frontier contract (v0):
    - When a relationship is not included as a membership edge in the FK-owner class's home OPG,
      SQL must keep the UUID column but MUST NOT emit DB FK constraints.

    For ONE_TO_MANY, the FK-owner is the target class.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "frontier_one_to_many.aware", OPG_FRONTIER_ONE_TO_MANY_CODE.strip()
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="frontier_one_to_many",
        description="frontier_one_to_many",
        fqn_prefix="pkg",
        file_codes=[("frontier_one_to_many.aware", code)],
        namespace_by_code_id=ns,
    )

    runtime = _derive_runtime_opgs(
        AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)
    )
    sql_graph = RuntimeToSQLTransformer().transform(runtime)

    rel = _get_relationship(sql_graph, "Parent", "children", "Child")
    fk_attr_id = next(
        ra.attribute_config_id
        for ra in rel.class_config_relationship_attributes
        if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
    )
    fk_owner = _get_class(sql_graph, "Child")
    fk_attr = next(
        acc.attribute_config
        for acc in fk_owner.class_config_attribute_configs
        if acc.attribute_config is not None and acc.attribute_config.id == fk_attr_id
    )
    fk_col_name = fk_attr.name

    class_lookup = {
        n.class_config.id: n.class_config
        for n in sql_graph.object_config_graph_nodes
        if n.class_config is not None
    }
    renderer = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.bind_object_config_graph(sql_graph)
    assert renderer._db_enforced_relationship_ids is not None
    ddl = renderer._emit_table(fk_owner, class_lookup=class_lookup)

    assert fk_col_name in ddl
    assert f"FOREIGN KEY (branch_id, projection_hash, {fk_col_name})" not in ddl


def test_sql_renderer_skips_fk_constraints_for_frontier_many_to_many(
    tmp_path: Path,
) -> None:
    """
    SQL frontier contract (v0):
    - MANY_TO_MANY relationships without an explicit association class are represented as join tables in SQL.
    - If the relationship edge is not included in the declaring class's projection membership, SQL must keep
      the UUID columns but MUST NOT emit DB FK constraints.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "frontier_many_to_many.aware", OPG_FRONTIER_MANY_TO_MANY_CODE.strip()
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="frontier_many_to_many",
        description="frontier_many_to_many",
        fqn_prefix="pkg",
        file_codes=[("frontier_many_to_many.aware", code)],
        namespace_by_code_id=ns,
    )

    runtime = _derive_runtime_opgs(
        AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)
    )
    sql_graph = RuntimeToSQLTransformer().transform(runtime)

    rel = _get_relationship(sql_graph, "A", "bs", "B")
    assert rel.relationship_type == ClassConfigRelationshipType.many_to_many
    join = _get_class(sql_graph, "ABJoin")

    class_lookup = {
        n.class_config.id: n.class_config
        for n in sql_graph.object_config_graph_nodes
        if n.class_config is not None
    }
    renderer = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.bind_object_config_graph(sql_graph)
    assert renderer._db_enforced_relationship_ids is not None
    ddl = renderer._emit_table(join, class_lookup=class_lookup)

    assert "FOREIGN KEY" not in ddl


def test_sql_renderer_skips_fk_constraints_for_frontier_one_to_one(
    tmp_path: Path,
) -> None:
    """
    SQL frontier contract (v0):
    - When a relationship is not included as a membership edge in the FK-owner class's home OPG,
      SQL must keep the UUID column but MUST NOT emit DB FK constraints.

    For ONE_TO_ONE, the FK-owner is the declaring (source) class.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path, "frontier_one_to_one.aware", OPG_FRONTIER_ONE_TO_ONE_CODE.strip()
    )
    ns = _namespaces(
        fqn_prefix="pkg", namespace="dom.default", code_ids=[code.id]
    )
    built = build_object_config_graph_from_code(
        name="frontier_one_to_one",
        description="frontier_one_to_one",
        fqn_prefix="pkg",
        file_codes=[("frontier_one_to_one.aware", code)],
        namespace_by_code_id=ns,
    )

    runtime = _derive_runtime_opgs(
        AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)
    )
    sql_graph = RuntimeToSQLTransformer().transform(runtime)

    rel = _get_relationship(sql_graph, "Profile", "image", "Blob")
    fk_attr_id = next(
        ra.attribute_config_id
        for ra in rel.class_config_relationship_attributes
        if ra.role == ClassConfigRelationshipAttributeRole.foreign_key
    )
    fk_owner = _get_class(sql_graph, "Profile")
    fk_attr = next(
        acc.attribute_config
        for acc in fk_owner.class_config_attribute_configs
        if acc.attribute_config is not None and acc.attribute_config.id == fk_attr_id
    )
    fk_col_name = fk_attr.name

    class_lookup = {
        n.class_config.id: n.class_config
        for n in sql_graph.object_config_graph_nodes
        if n.class_config is not None
    }
    renderer = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.bind_object_config_graph(sql_graph)
    assert renderer._db_enforced_relationship_ids is not None
    ddl = renderer._emit_table(fk_owner, class_lookup=class_lookup)

    assert fk_col_name in ddl
    assert f"FOREIGN KEY (branch_id, projection_hash, {fk_col_name})" not in ddl


def test_sql_transformer_preserves_association_for_external_many_to_many(
    tmp_path: Path,
) -> None:
    """
    SQL contract:
    - Many-to-many associations should retain their association class and FKs,
      even when the target class lives in an external graph.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path, "asset.aware", EXTERNAL_MANY_TO_MANY_CODE_DEP.strip()
    )
    dep_ns = _namespaces(
        fqn_prefix="dep", namespace="finance.asset", code_ids=[dep_code.id]
    )
    dep = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep",
        file_codes=[("asset.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    mod_code = _build_code(
        tmp_path, "portfolio.aware", EXTERNAL_MANY_TO_MANY_CODE_MOD.strip()
    )
    mod_ns = _namespaces(
        fqn_prefix="mod",
        namespace="economy.portfolio",
        code_ids=[mod_code.id],
    )
    mod = build_object_config_graph_from_code(
        name="mod",
        description="mod",
        fqn_prefix="mod",
        file_codes=[("portfolio.aware", mod_code)],
        namespace_by_code_id=mod_ns,
        external_graphs=[dep.graph],
    )
    cross = mod.cross_relationships_by_target_ocg.get(dep.graph.id)
    assert cross, "Expected cross-OCG relationships to dependency graph"
    mod.graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=mod.graph.id,
            target_object_config_graph_id=dep.graph.id,
            target_object_config_graph=dep.graph,
            class_config_relationships=cross,
        )
    )

    runtime = AwareToRuntimeTransformer(namespace_by_code_id=mod_ns).transform(
        mod.graph
    )
    sql_graph = RuntimeToSQLTransformer().transform(runtime)
    sql_graph.object_config_graph_relationships = list(
        runtime.object_config_graph_relationships
    )

    assoc = _get_class(sql_graph, "PortfolioAssetEdge")
    assoc_attr_names = {
        l.attribute_config.name
        for l in assoc.class_config_attribute_configs
        if l.attribute_config
    }
    assert "portfolio_id" in assoc_attr_names
    assert "asset_id" in assoc_attr_names

    rel = next(
        r
        for rel_block in sql_graph.object_config_graph_relationships
        for r in rel_block.class_config_relationships
        if r.relationship_type == ClassConfigRelationshipType.many_to_many
    )
    assert rel.class_config_relationship_association_edge is not None
    assert rel.class_config_relationship_association_edge.class_config_id == assoc.id


def test_aware_runtime_transformer_preserves_cross_ocg_source_relationship_views_for_body_lowering(
    tmp_path: Path,
) -> None:
    """
    Runtime lowering contract:
    - Cross-OCG relationships remain detached in `object_config_graph_relationships`.
    - Local source classes must still keep those rails on `class_config_relationships`,
      otherwise runtime FunctionImpl rebuilding cannot resolve body receivers like
      `code_packages.create`.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path,
        "dep_code_package.aware",
        EXTERNAL_EDGE_RECEIVER_RESOLUTION_DEP_CODE.strip(),
    )
    dep_ns = _namespaces(
        fqn_prefix="dep",
        namespace="code.package",
        code_ids=[dep_code.id],
    )
    dep = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep",
        file_codes=[("dep_code_package.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    mod_code = _build_code(
        tmp_path, "repository.aware", EXTERNAL_EDGE_RECEIVER_RESOLUTION_MOD_CODE.strip()
    )
    mod_ns = _namespaces(
        fqn_prefix="mod",
        namespace="structure.repository",
        code_ids=[mod_code.id],
    )
    mod = build_object_config_graph_from_code(
        name="mod",
        description="mod",
        fqn_prefix="mod",
        file_codes=[("repository.aware", mod_code)],
        namespace_by_code_id=mod_ns,
        external_graphs=[dep.graph],
    )
    cross = mod.cross_relationships_by_target_ocg.get(dep.graph.id)
    assert cross, "Expected cross-OCG relationships to dependency graph"
    mod.graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=mod.graph.id,
            target_object_config_graph_id=dep.graph.id,
            target_object_config_graph=dep.graph,
            class_config_relationships=cross,
        )
    )

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=mod_ns,
        external_graphs_by_id={dep.graph.id: dep.graph},
    ).transform(mod.graph)

    repo = _get_class(runtime, "Repository")
    repo_attr_by_id: dict[UUID, str] = {}
    for link in repo.class_config_attribute_configs:
        attr = link.attribute_config
        if attr is None:
            continue
        repo_attr_by_id[attr.id] = attr.name
    repo_relationship_names = {
        repo_attr_by_id[rel_attr.attribute_config_id]
        for rel in repo.class_config_relationships
        for rel_attr in rel.class_config_relationship_attributes
        if rel_attr.direction == ClassConfigRelationshipDirection.forward
        and rel_attr.role == ClassConfigRelationshipAttributeRole.reference
        and rel_attr.attribute_config_id in repo_attr_by_id
    }
    assert "code_packages" in repo_relationship_names

    create_code_package = next(
        link.function_config
        for link in repo.class_config_function_configs
        if link.function_config.name == "create_code_package"
    )
    assert create_code_package.function_impl is not None
    assert create_code_package.invocations
    invocation = create_code_package.invocations[0]
    assert invocation.class_config_relationship_id is not None
    assert invocation.target_function_config is not None
    assert invocation.target_function_config.name == "create_via_repository"
