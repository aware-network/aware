# @code-under-test: ../aware_meta/graph/config/builder.py

from pathlib import Path
from uuid import UUID

import pytest

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipReifiedRole,
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
from aware_meta.graph.config.relationship_analysis import (
    stable_reified_association_target_relationship_id,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.projection.builder import build_object_projection_graph
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
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


def _runtime_graph_with_opgs(
    graph,
    *,
    namespace_by_code_id,
    external_graphs=None,
    cross_relationships_by_target_ocg=None,
):
    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id
    ).transform(graph)
    runtime.object_projection_graphs = build_object_projection_graphs(
        runtime,
        external_graphs=list(external_graphs or []),
        cross_relationships_by_target_ocg=cross_relationships_by_target_ocg,
    )
    return runtime


CANONICAL_CODE = """
class User {
    posts Post[]

    fn build construct() -> User {
        \"\"\"Build a new User.\"\"\"
    }

    fn build_with_actor construct(actor_id UUID) -> User {
        \"\"\"Build a new User with an actor pre-bound.\"\"\"
    }

}

class Post {
    title String
}

// Lens: a projection named 'P' rooted at User, including posts edge
projection P {
    root test.User
    test.User::posts
}
""".strip()

PORTAL_CODE = """
class User {
    posts Post[]
}

class Post {
    title String
}

// Two projections ("islands") + an explicit cross-projection portal.
projection Users {
    root test.User
    test.User::posts Posts
}

projection Posts {
    root test.Post
}
""".strip()

OPTIONAL_EDGE_CODE = """
class Lane {
    head_commit Commit?
}

class Commit {}

projection P {
    root test.Lane
    test.Lane::head_commit
}
""".strip()

ASSOCIATION_OPG_CODE = """
class Group {
    users User[] @UserGroupEdge many
}

class User { id String }

edge UserGroupEdge { status String }

projection P {
    root test.Group
    test.Group::users
}
""".strip()


def _relationship_by_attr(
    graph, *, source: str, attr_name: str, target: str
) -> ClassConfigRelationship:
    src = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config and n.class_config.name == source
    )
    tgt = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config and n.class_config.name == target
    )
    for node in graph.object_config_graph_nodes:
        rel = node.class_config_relationship
        if rel is None:
            continue
        if rel.class_config_id != src.id or rel.target_class_config_id != tgt.id:
            continue
        for ra in rel.class_config_relationship_attributes:
            if (
                ra.direction == ClassConfigRelationshipDirection.forward
                and ra.role == ClassConfigRelationshipAttributeRole.reference
                and ra.attribute_config_id is not None
            ):
                for link in src.class_config_attribute_configs:
                    if (
                        link.attribute_config
                        and link.attribute_config.id == ra.attribute_config_id
                    ):
                        if link.attribute_config.name == attr_name:
                            return rel
    raise KeyError((source, attr_name, target))


def _reified_source_relationship(graph, *, canonical_rel_id) -> ClassConfigRelationship:
    for node in graph.object_config_graph_nodes:
        rel = node.class_config_relationship
        if rel is None:
            continue
        if rel.reified_from_relationship_id != canonical_rel_id:
            continue
        if rel.reified_role == ClassConfigRelationshipReifiedRole.source_to_association:
            return rel
    raise KeyError(canonical_rel_id)


def test_opg_built_and_attached_to_ocg(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "opg.aware", CANONICAL_CODE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="opg",
        description="opg",
        fqn_prefix="pkg",
        file_codes=[("opg.aware", code)],
        namespace_by_code_id=ns,
    )
    graph = _runtime_graph_with_opgs(res.graph, namespace_by_code_id=ns)

    assert (
        graph.object_projection_graphs
    ), "Expected OPGs to be derived and attached during runtime OPG build"
    opg = next((g for g in graph.object_projection_graphs if g.name == "P"), None)
    assert opg is not None

    # Root node should exist for User
    root_nodes = [n for n in opg.object_projection_graph_nodes if n.is_root]
    assert len(root_nodes) == 1
    root = root_nodes[0]

    # Constructors should be derived from root class functions with `construct` verb
    constructors = opg.object_projection_graph_constructors
    assert constructors, "Expected constructors to be provisioned on the OPG instance"
    assert len(constructors) == 2
    assert {c.object_projection_graph_id for c in constructors} == {opg.id}
    assert {c.root_node_id for c in constructors} == {root.id}

    names = {
        c.function_constructor.function_config.name
        for c in constructors
        if c.function_constructor is not None
    }
    assert names == {"build", "build_with_actor"}

    # Edge multiplicity should be MANY due to User.posts being a collection
    assert (
        opg.object_projection_graph_edges
    ), "Expected at least one edge in the projection"
    assert (
        opg.object_projection_graph_edges[0].multiplicity
        == ObjectProjectionGraphEdgeMultiplicity.many
    )


def test_build_object_projection_graphs_excludes_root_reintroduced_by_external_dependency_closure(
    tmp_path: Path,
) -> None:
    from uuid import uuid4

    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.config.object_config_graph_relationship import (
        ObjectConfigGraphRelationship,
    )

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    root_code = _build_code(
        tmp_path,
        "history.aware",
        """
class Branch {
    fn build construct() -> Branch {
        \"\"\"Build a new Branch.\"\"\"
    }
}

projection P {
    root aware_history.branch.Branch
}
""".strip(),
    )
    root_ns, root_domains = _ns(
        fqn_prefix="aware_history",
        namespace="branch",
        code_ids=[root_code.id],
    )
    root_runtime = AwareToRuntimeTransformer(namespace_by_code_id=root_ns).transform(
        build_object_config_graph_from_code(
            name="history",
            description="history",
            fqn_prefix="aware_history",
            file_codes=[("history.aware", root_code)],
            namespace_by_code_id=root_ns,
        ).graph
    )

    sibling_runtime = ObjectConfigGraph(
        id=uuid4(),
        name="meta_sibling",
        description="meta_sibling",
        hash="sha256:test:meta_sibling",
        fqn_prefix="aware_meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
        object_config_graph_overlays=[],
        object_config_graph_annotations=[],
        object_config_graph_relationships=[],
    )
    sibling_runtime.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=sibling_runtime.id,
            target_object_config_graph_id=root_runtime.id,
            target_object_config_graph=root_runtime,
            class_config_relationships=[],
        )
    )

    branch_class_id = next(
        node.class_config.id
        for node in root_runtime.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "Branch"
    )
    opgs = build_object_projection_graphs(
        root_runtime, external_graphs=[sibling_runtime]
    )

    opg = next(g for g in opgs if g.name == "P")
    root_nodes = [n for n in opg.object_projection_graph_nodes if n.is_root]
    assert len(root_nodes) == 1
    assert root_nodes[0].class_config_id == branch_class_id
    assert opg.object_projection_graph_constructors


def test_opg_description_derived_from_projection_doc_comment(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "desc.aware",
        """
class Wallet {}

/// Wallet projection.
/// Holds balances and transactions.
projection Wallet {
    root test.Wallet
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )

    graph = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="desc",
            description="desc",
            fqn_prefix="pkg",
            file_codes=[("desc.aware", code)],
            namespace_by_code_id=ns,
        ).graph,
        namespace_by_code_id=ns,
    )

    opg = next((g for g in graph.object_projection_graphs if g.name == "Wallet"), None)
    assert opg is not None
    assert opg.description == "Wallet projection.\nHolds balances and transactions."


def test_opg_missing_relationship_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    bad = """
class User {
    posts Post[]
}
class Post {}

projection P {
    root test.User
    test.User::does_not_exist
}
""".strip()
    code = _build_code(tmp_path, "bad.aware", bad)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )

    built = build_object_config_graph_from_code(
        name="bad",
        description="bad",
        fqn_prefix="pkg",
        file_codes=[("bad.aware", code)],
        namespace_by_code_id=ns,
    )

    try:
        _runtime_graph_with_opgs(
            built.graph,
            namespace_by_code_id=ns,
        )
        assert (
            False
        ), "Expected runtime OPG build to fail due to missing relationship in projection declaration"
    except ValueError as e:
        assert "Relationship not found for projection edge" in str(e)


def test_opg_resolves_class_attached_relationship_without_relationship_node(
    tmp_path: Path,
) -> None:
    """
    API dependency graph artifacts may carry relationships on ClassConfig without
    embedding the relationship node in the local OCG node list.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "class_attached.aware", CANONICAL_CODE)
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="test",
        code_ids=[code.id],
    )
    built = build_object_config_graph_from_code(
        name="class_attached",
        description="class_attached",
        fqn_prefix="pkg",
        file_codes=[("class_attached.aware", code)],
        namespace_by_code_id=ns,
    )
    rel = _relationship_by_attr(
        built.graph,
        source="User",
        attr_name="posts",
        target="Post",
    )
    user = next(
        node.class_config
        for node in built.graph.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "User"
    )
    user.class_config_relationships = [rel]
    built.graph.object_config_graph_nodes = [
        node
        for node in built.graph.object_config_graph_nodes
        if node.class_config_relationship is None
    ]

    opgs = build_object_projection_graphs(built.graph)
    opg = next(graph for graph in opgs if graph.name == "P")

    assert any(
        edge.class_config_relationship_id == rel.id
        for edge in opg.object_projection_graph_edges
    )


def test_opg_hash_deterministic_across_annotation_order(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_a = _build_code(tmp_path, "a.aware", CANONICAL_CODE)
    ns_a, domains_a = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code_a.id]
    )
    graph_a = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="a",
            description="a",
            fqn_prefix="pkg",
            file_codes=[("a.aware", code_a)],
            namespace_by_code_id=ns_a,
        ).graph,
        namespace_by_code_id=ns_a,
    )
    opg_a = next(g for g in graph_a.object_projection_graphs if g.name == "P")

    # Same semantics, reversed annotation order
    flipped = """
class User {
    posts Post[]
}
class Post { title String }
projection P {
    test.User::posts
    root test.User
}
""".strip()
    code_b = _build_code(tmp_path, "b.aware", flipped)
    ns_b, domains_b = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code_b.id]
    )
    graph_b = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="b",
            description="b",
            fqn_prefix="pkg",
            file_codes=[("b.aware", code_b)],
            namespace_by_code_id=ns_b,
        ).graph,
        namespace_by_code_id=ns_b,
    )
    opg_b = next(g for g in graph_b.object_projection_graphs if g.name == "P")

    assert opg_a.projection_hash == opg_b.projection_hash


def test_opg_builder_resolves_association_to_reified_edge(tmp_path: Path) -> None:
    """
    OPG builder should resolve projection edges declared on canonical association relationships
    to the reified source->association runtime relationship.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "assoc.aware", ASSOCIATION_OPG_CODE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )
    res = build_object_config_graph_from_code(
        name="assoc",
        description="assoc",
        fqn_prefix="pkg",
        file_codes=[("assoc.aware", code)],
        namespace_by_code_id=ns,
    )

    runtime = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(res.graph)
    opgs = build_object_projection_graphs(runtime)
    opg = next(g for g in opgs if g.name == "P")

    canonical = _relationship_by_attr(
        runtime, source="Group", attr_name="users", target="User"
    )
    assert canonical.class_config_relationship_association_edge is not None
    assert canonical.reified_from_relationship_id is None

    reified = _reified_source_relationship(runtime, canonical_rel_id=canonical.id)
    assert any(
        edge.class_config_relationship_id == reified.id
        for edge in opg.object_projection_graph_edges
    )


def test_opg_builder_resolves_cross_schema_association_edge_target(
    tmp_path: Path,
) -> None:
    """
    Runtime output must preserve reified association->target edges when they cross schemas.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    package_source = """
class CodePackage {
    codes aware_code.code.Code[] @CodePackageCode
}

edge CodePackageCode {
    relative_path String key

    fn create construct(relative_path String key) -> CodePackageCode {
        let created_code = construct code.create(relative_path = relative_path)
    }
}

projection CodePackage {
    root aware_code.package.CodePackage
    aware_code.package.CodePackage::codes
    aware_code.package.CodePackageCode::code
}
""".strip()
    code_source = """
class Code {
    relative_path String key

    fn create construct(relative_path String key) -> Code {
    }
}
""".strip()
    package_code = _build_code(tmp_path, "package.aware", package_source)
    code_code = _build_code(tmp_path, "code.aware", code_source)
    ns = {
        package_code.id: NamespacePath(package="aware_code", namespace="package"),
        code_code.id: NamespacePath(package="aware_code", namespace="code"),
    }
    built = build_object_config_graph_from_code(
        name="aware_code",
        description="aware_code",
        fqn_prefix="aware_code",
        file_codes=[("package.aware", package_code), ("code.aware", code_code)],
        namespace_by_code_id=ns,
    )

    runtime = AwareToRuntimeTransformer(namespace_by_code_id=ns).transform(built.graph)
    opgs = build_object_projection_graphs(runtime)
    opg = next(graph for graph in opgs if graph.name == "CodePackage")

    code_package_code = next(
        node.class_config
        for node in runtime.object_config_graph_nodes
        if node.class_config and node.class_config.name == "CodePackageCode"
    )
    code = next(
        node.class_config
        for node in runtime.object_config_graph_nodes
        if node.class_config and node.class_config.name == "Code"
    )
    reified_target_relationship = None
    for node in runtime.object_config_graph_nodes:
        rel = node.class_config_relationship
        if rel is None:
            continue
        if (
            rel.class_config_id == code_package_code.id
            and rel.target_class_config_id == code.id
        ):
            reified_target_relationship = rel
            break
    for ocg_rel in runtime.object_config_graph_relationships:
        if reified_target_relationship is not None:
            break
        for rel in ocg_rel.class_config_relationships:
            if (
                rel.class_config_id == code_package_code.id
                and rel.target_class_config_id == code.id
            ):
                reified_target_relationship = rel
                break

    assert reified_target_relationship is not None
    assert any(
        edge.class_config_relationship_id == reified_target_relationship.id
        for edge in opg.object_projection_graph_edges
    )


def test_opg_builder_resolves_canonical_association_edge_target_without_runtime_derivation(
    tmp_path: Path,
) -> None:
    """
    Product API dependency materialization builds canonical dependency OPGs before
    runtime reification, so association edge endpoint members must still resolve.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    package_source = """
class CodePackage {
    codes aware_code.code.Code[] @CodePackageCode
}

edge CodePackageCode {
    relative_path String key
}

projection CodePackage {
    root aware_code.package.CodePackage
    aware_code.package.CodePackage::codes
    aware_code.package.CodePackageCode::code
}
""".strip()
    code_source = """
class Code {
    relative_path String key
}
""".strip()
    package_code = _build_code(tmp_path, "package.aware", package_source)
    code_code = _build_code(tmp_path, "code.aware", code_source)
    ns = {
        package_code.id: NamespacePath(
            package="aware_code",
            namespace="package",
        ),
        code_code.id: NamespacePath(
            package="aware_code",
            namespace="code",
        ),
    }
    built = build_object_config_graph_from_code(
        name="aware_code",
        description="aware_code",
        fqn_prefix="aware_code",
        file_codes=[("package.aware", package_code), ("code.aware", code_code)],
        namespace_by_code_id=ns,
    )

    opgs = build_object_projection_graphs(built.graph)
    opg = next(graph for graph in opgs if graph.name == "CodePackage")

    canonical = _relationship_by_attr(
        built.graph,
        source="CodePackage",
        attr_name="codes",
        target="Code",
    )
    expected_target_id = stable_reified_association_target_relationship_id(
        relationship_id=canonical.id,
    )

    assert any(
        edge.class_config_relationship_id == expected_target_id
        for edge in opg.object_projection_graph_edges
    )


def test_opg_cross_ocg_relationship_edge_resolves(tmp_path: Path) -> None:
    """
    Regression (canonical): cross-OCG relationship edges are returned detached (not embedded as RELATIONSHIP nodes),
    but the projection builder must still resolve them deterministically via the detached relationship map.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep = """
class Actor {
    // Attributes
    name String
}
""".strip()
    dep_code = _build_code(tmp_path, "dep.aware", dep)
    dep_ns, dep_domains = _ns(
        fqn_prefix="aware",
        namespace="identity.actor",
        code_ids=[dep_code.id],
    )
    dep_graph = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="aware",
        file_codes=[("dep.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    ).graph

    local = """
class AgentProcessThread {
    // Relationships
    actor aware.identity.actor.Actor
}

projection Agent {
    root agent.AgentProcessThread
    agent.AgentProcessThread::actor
}
""".strip()
    local_code = _build_code(tmp_path, "local.aware", local)
    local_ns, local_domains = _ns(
        fqn_prefix="aware_network",
        namespace="agent",
        code_ids=[local_code.id],
    )
    build_result = build_object_config_graph_from_code(
        name="local",
        description="local",
        fqn_prefix="aware_network",
        file_codes=[("local.aware", local_code)],
        namespace_by_code_id=local_ns,
        external_graphs=[dep_graph],
    )
    canonical_graph = build_result.graph
    dep_runtime = _runtime_graph_with_opgs(dep_graph, namespace_by_code_id=dep_ns)
    runtime_graph = _runtime_graph_with_opgs(
        build_result.graph,
        namespace_by_code_id=local_ns,
        external_graphs=[dep_runtime],
        cross_relationships_by_target_ocg=build_result.cross_relationships_by_target_ocg,
    )

    # Ensure the cross-OCG relationship is detached at build-time (not a relationship node in the source graph).
    apt_cc_id = next(
        n.class_config.id
        for n in canonical_graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "AgentProcessThread"
    )
    actor_cc_id = next(
        n.class_config.id
        for n in dep_graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Actor"
    )
    assert not any(
        n.type == ObjectConfigGraphNodeType.relationship
        for n in canonical_graph.object_config_graph_nodes
    )
    cross_rels = build_result.cross_relationships_by_target_ocg.get(dep_graph.id)
    assert cross_rels is not None
    assert len(cross_rels) == 1
    rel = cross_rels[0]
    assert rel.class_config_id == apt_cc_id
    assert rel.target_class_config_id == actor_cc_id

    # And the projection edge should resolve (no 'Relationship not found for projection edge').
    opg = next(
        (g for g in runtime_graph.object_projection_graphs if g.name == "Agent"), None
    )
    assert opg is not None
    assert any(
        e.class_config_relationship_id == rel.id
        for e in opg.object_projection_graph_edges
    )


def test_opg_resolves_cross_relationships_from_external_graph_relationships(
    tmp_path: Path,
) -> None:
    """
    Regression (canonical):
    - Downstream builds may include projection membership/edges that traverse relationships declared in a *dependency*
      graph (not the current build graph).
    - Those relationships are stored on dependency graphs via
      `ObjectConfigGraph.object_config_graph_relationships[].class_config_relationships`.
    - OPG builder must treat these as valid relationship sources when resolving PROJECT edges.

    This mirrors the Environment "Environment" projection traversing:
        aware_meta.graph.instance.ObjectInstanceGraphBranch::branch -> aware_history.branch.Branch
    """
    from uuid import uuid4

    from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
        ObjectProjectionGraphBinding,
    )
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.config.object_config_graph_relationship import (
        ObjectConfigGraphRelationship,
    )

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    history_code = _build_code(
        tmp_path,
        "history.aware",
        """
class Branch {}
""".strip(),
    )
    history_ns, history_domains = _ns(
        fqn_prefix="aware_history",
        namespace="branch",
        code_ids=[history_code.id],
    )
    history_graph = build_object_config_graph_from_code(
        name="history",
        description="history",
        fqn_prefix="aware_history",
        file_codes=[("history.aware", history_code)],
        namespace_by_code_id=history_ns,
    ).graph

    meta_code = _build_code(
        tmp_path,
        "meta.aware",
        """
class ObjectInstanceGraphBranch {
    branch aware_history.branch.Branch
}
""".strip(),
    )
    meta_ns, meta_domains = _ns(
        fqn_prefix="aware_meta",
        namespace="graph.instance",
        code_ids=[meta_code.id],
    )
    meta_build = build_object_config_graph_from_code(
        name="meta",
        description="meta",
        fqn_prefix="aware_meta",
        file_codes=[("meta.aware", meta_code)],
        namespace_by_code_id=meta_ns,
        external_graphs=[history_graph],
    )
    meta_graph = meta_build.graph
    cross_rels = meta_build.cross_relationships_by_target_ocg.get(history_graph.id)
    assert cross_rels is not None and len(cross_rels) == 1

    # Materialize cross-OCG relationships as they appear in persisted dependency artifacts.
    ocg_rel = ObjectConfigGraphRelationship(
        object_config_graph_id=meta_graph.id,
        target_object_config_graph_id=history_graph.id,
        target_object_config_graph=history_graph,
        class_config_relationships=[cross_rels[0]],
    )
    meta_graph.object_config_graph_relationships.append(ocg_rel)

    # Persist/load roundtrip must retain the relationship list (no excluded fields).
    meta_graph_json = meta_graph.model_dump_json(exclude_none=True, by_alias=True)
    meta_graph_loaded = ObjectConfigGraph.model_validate_json(meta_graph_json)
    assert any(
        r.class_config_relationships
        for r in meta_graph_loaded.object_config_graph_relationships
    ), "Expected persisted ObjectConfigGraphRelationship.class_config_relationships to survive roundtrip"

    decl_id = uuid4()
    bindings = [
        ObjectProjectionGraphBinding(
            id=uuid4(),
            object_projection_graph_declaration_id=decl_id,
            fqn_prefix="aware_meta",
            namespace="graph.instance",
            class_name="ObjectInstanceGraphBranch",
            attribute_name=None,
            target_projection_name=None,
            side=None,
        ),
        ObjectProjectionGraphBinding(
            id=uuid4(),
            object_projection_graph_declaration_id=decl_id,
            fqn_prefix="aware_meta",
            namespace="graph.instance",
            class_name="ObjectInstanceGraphBranch",
            attribute_name="branch",
            target_projection_name=None,
            side=None,
        ),
    ]

    local_graph = ObjectConfigGraph(
        id=uuid4(),
        name="local",
        description="local",
        hash="sha256:test:local",
        fqn_prefix="local",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
        object_config_graph_overlays=[],
        object_config_graph_annotations=[],
        object_config_graph_relationships=[],
    )

    opg = build_object_projection_graph(
        name="environment",
        description="environment",
        ocg=local_graph,
        projection_bindings=bindings,
        external_graphs=[meta_graph_loaded, history_graph],
        cross_relationships_by_target_ocg=None,
    )
    assert opg.object_projection_graph_edges
    assert any(
        e.class_config_relationship_id == cross_rels[0].id
        for e in opg.object_projection_graph_edges
    )


def test_opg_uses_persisted_external_class_fqn_without_domain_topology(
    tmp_path: Path,
) -> None:
    from uuid import uuid4

    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
    from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
        ObjectProjectionGraphBinding,
    )

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(
        tmp_path,
        "content_part_text.aware",
        """
class ContentPartText {
    value String
}
""".strip(),
    )
    dep_ns, dep_domains = _ns(
        fqn_prefix="aware_content",
        namespace="part",
        code_ids=[dep_code.id],
    )
    dep_graph = build_object_config_graph_from_code(
        name="content",
        description="content",
        fqn_prefix="aware_content",
        file_codes=[("content_part_text.aware", dep_code)],
        namespace_by_code_id=dep_ns,
    ).graph
    dep_runtime = dep_graph.model_copy(deep=True)

    dep_cc = next(
        n.class_config
        for n in dep_runtime.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "ContentPartText"
    )
    assert dep_cc.class_fqn == "aware_content.part.ContentPartText"

    decl_id = uuid4()
    bindings = [
        ObjectProjectionGraphBinding(
            id=uuid4(),
            object_projection_graph_declaration_id=decl_id,
            fqn_prefix="aware_content",
            namespace="part",
            class_name="ContentPartText",
            attribute_name=None,
            target_projection_name=None,
            side=None,
        )
    ]

    local_graph = ObjectConfigGraph(
        id=uuid4(),
        name="local",
        description="local",
        hash="sha256:test:local",
        fqn_prefix="local",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
        object_config_graph_overlays=[],
        object_config_graph_annotations=[],
        object_config_graph_relationships=[],
    )

    opg = build_object_projection_graph(
        name="content_part_text_projection",
        description="content_part_text_projection",
        ocg=local_graph,
        projection_bindings=bindings,
        external_graphs=[dep_runtime],
        cross_relationships_by_target_ocg=None,
    )

    root_nodes = [n for n in opg.object_projection_graph_nodes if n.is_root]
    assert len(root_nodes) == 1
    assert root_nodes[0].class_config_id == dep_cc.id


def test_opg_build_dedupes_identical_class_ids_across_graph_variants(
    tmp_path: Path,
) -> None:
    from uuid import uuid4

    from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
        ObjectProjectionGraphBinding,
    )

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "storage_bucket.aware",
        "class StorageBucket {\n    name String\n}\n",
    )
    ns, _domains = _ns(
        fqn_prefix="aware_storage",
        namespace="bucket",
        code_ids=[code.id],
    )
    built = build_object_config_graph_from_code(
        name="storage",
        description="storage",
        fqn_prefix="aware_storage",
        file_codes=[("storage_bucket.aware", code)],
        namespace_by_code_id=ns,
    )
    graph_variant = built.graph.model_copy(deep=True, update={"id": uuid4()})

    opg = build_object_projection_graph(
        name="storage",
        description="storage",
        ocg=built.graph,
        projection_bindings=[
            ObjectProjectionGraphBinding(
                id=uuid4(),
                object_projection_graph_declaration_id=uuid4(),
                fqn_prefix="aware_storage",
                namespace="bucket",
                class_name="StorageBucket",
                attribute_name=None,
                target_projection_name=None,
                side=None,
            )
        ],
        external_graphs=[graph_variant],
        cross_relationships_by_target_ocg=None,
    )

    assert len(opg.object_projection_graph_nodes) == 1
    storage_class = next(
        node.class_config
        for node in built.graph.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "StorageBucket"
    )
    assert (
        opg.object_projection_graph_nodes[0].class_config_id
        == storage_class.id
    )


def test_opg_handlers_dedup_identical_class_ids_across_graph_variants(
    tmp_path: Path,
) -> None:
    from uuid import uuid4

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "canonical.aware", CANONICAL_CODE)
    ns, _domains = _ns(
        fqn_prefix="pkg",
        namespace="test",
        code_ids=[code.id],
    )
    built = build_object_config_graph_from_code(
        name="canonical",
        description="canonical",
        fqn_prefix="pkg",
        file_codes=[("canonical.aware", code)],
        namespace_by_code_id=ns,
    )
    graph_variant = built.graph.model_copy(deep=True, update={"id": uuid4()})

    opgs = build_object_projection_graphs(
        built.graph,
        external_graphs=[graph_variant],
    )

    assert [opg.name for opg in opgs] == ["P"]


def test_opg_portal_relationships_are_provisioned_and_do_not_affect_membership(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "portal.aware", PORTAL_CODE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )
    graph = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="portal",
            description="portal",
            fqn_prefix="pkg",
            file_codes=[("portal.aware", code)],
            namespace_by_code_id=ns,
        ).graph,
        namespace_by_code_id=ns,
    )

    opg_users = next(g for g in graph.object_projection_graphs if g.name == "Users")
    opg_posts = next(g for g in graph.object_projection_graphs if g.name == "Posts")

    # Membership: users contains only User (no intra-projection edge for posts).
    user_cc_id = next(
        n.class_config.id
        for n in graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "User"
    )
    post_cc_id = next(
        n.class_config.id
        for n in graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Post"
    )
    assert {n.class_config_id for n in opg_users.object_projection_graph_nodes} == {
        user_cc_id
    }
    assert {n.class_config_id for n in opg_posts.object_projection_graph_nodes} == {
        post_cc_id
    }
    assert opg_users.object_projection_graph_edges == []

    # Portal: users.posts -> posts
    assert len(opg_users.object_projection_graph_relationships) == 1
    portal = opg_users.object_projection_graph_relationships[0]
    assert portal.object_projection_graph_id == opg_users.id
    assert portal.target_object_projection_graph_id == opg_posts.id

    # Relationship id must match the canonical ClassConfigRelationship(User.posts -> Post).
    expected_rel_id = next(
        n.class_config_relationship.id
        for n in graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.relationship
        and n.class_config_relationship is not None
        and n.class_config_relationship.class_config_id == user_cc_id
        and n.class_config_relationship.target_class_config_id == post_cc_id
    )
    assert portal.class_config_relationship_id == expected_rel_id

    # Node binding points to the correct member nodes on each side.
    assert portal.source_object_projection_graph_node_id == next(
        n.id
        for n in opg_users.object_projection_graph_nodes
        if n.class_config_id == user_cc_id
    )
    assert portal.target_object_projection_graph_node_id == next(
        n.id
        for n in opg_posts.object_projection_graph_nodes
        if n.class_config_id == post_cc_id
    )


def test_opg_portal_allows_external_target_projection(tmp_path: Path) -> None:
    """
    Portals may target projections defined in external graphs (cross-OCG).

    Example: economy.finance_entity -> identity lane.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    identity_code = _build_code(
        tmp_path,
        "identity.aware",
        """
class Identity {}

projection Identity {
    root identity.Identity
}
""".strip(),
    )
    identity_ns, identity_domains = _ns(
        fqn_prefix="aware_identity",
        namespace="identity",
        code_ids=[identity_code.id],
    )
    identity_graph = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="identity",
            description="identity",
            fqn_prefix="aware_identity",
            file_codes=[("identity.aware", identity_code)],
            namespace_by_code_id=identity_ns,
        ).graph,
        namespace_by_code_id=identity_ns,
    )
    identity_opg = next(
        g for g in identity_graph.object_projection_graphs if g.name == "Identity"
    )

    economy_code = _build_code(
        tmp_path,
        "economy.aware",
        """
class FinanceEntity {
    identity aware_identity.identity.Identity unique
}

projection FinanceEntity {
    root finance.FinanceEntity
    finance.FinanceEntity::identity aware_identity.Identity
}
""".strip(),
    )
    economy_ns, economy_domains = _ns(
        fqn_prefix="aware_economy",
        namespace="finance",
        code_ids=[economy_code.id],
    )
    economy_build = build_object_config_graph_from_code(
        name="economy",
        description="economy",
        fqn_prefix="aware_economy",
        file_codes=[("economy.aware", economy_code)],
        namespace_by_code_id=economy_ns,
        external_graphs=[identity_graph],
    )
    economy_graph = _runtime_graph_with_opgs(
        economy_build.graph,
        namespace_by_code_id=economy_ns,
        external_graphs=[identity_graph],
        cross_relationships_by_target_ocg=economy_build.cross_relationships_by_target_ocg,
    )

    finance_opg = next(
        g for g in economy_graph.object_projection_graphs if g.name == "FinanceEntity"
    )
    assert len(finance_opg.object_projection_graph_relationships) == 1
    portal = finance_opg.object_projection_graph_relationships[0]
    assert portal.object_projection_graph_id == finance_opg.id
    assert portal.target_object_projection_graph_id == identity_opg.id


def test_opg_portal_ignores_runtime_context_duplicate_target_projection(
    tmp_path: Path,
) -> None:
    from uuid import uuid4

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    identity_code = _build_code(
        tmp_path,
        "identity.aware",
        """
class Identity {}

projection Identity {
    root identity.Identity
}
""".strip(),
    )
    identity_ns, _identity_domains = _ns(
        fqn_prefix="aware_identity",
        namespace="identity",
        code_ids=[identity_code.id],
    )
    identity_graph = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="identity",
            description="identity",
            fqn_prefix="aware_identity",
            file_codes=[("identity.aware", identity_code)],
            namespace_by_code_id=identity_ns,
        ).graph,
        namespace_by_code_id=identity_ns,
    )
    runtime_context_variant = identity_graph.model_copy(
        deep=True,
        update={
            "id": uuid4(),
            "fqn_prefix": "aware.runtime_context",
            "object_config_graph_nodes": [],
            "object_config_graph_relationships": [],
        },
    )
    identity_opg = next(
        g for g in identity_graph.object_projection_graphs if g.name == "Identity"
    )

    economy_code = _build_code(
        tmp_path,
        "economy.aware",
        """
class FinanceEntity {
    identity aware_identity.identity.Identity unique
}

projection FinanceEntity {
    root finance.FinanceEntity
    finance.FinanceEntity::identity Identity
}
""".strip(),
    )
    economy_ns, _economy_domains = _ns(
        fqn_prefix="aware_economy",
        namespace="finance",
        code_ids=[economy_code.id],
    )
    economy_build = build_object_config_graph_from_code(
        name="economy",
        description="economy",
        fqn_prefix="aware_economy",
        file_codes=[("economy.aware", economy_code)],
        namespace_by_code_id=economy_ns,
        external_graphs=[identity_graph],
    )
    economy_graph = _runtime_graph_with_opgs(
        economy_build.graph,
        namespace_by_code_id=economy_ns,
        external_graphs=[identity_graph, runtime_context_variant],
        cross_relationships_by_target_ocg=economy_build.cross_relationships_by_target_ocg,
    )

    finance_opg = next(
        g for g in economy_graph.object_projection_graphs if g.name == "FinanceEntity"
    )
    assert len(finance_opg.object_projection_graph_relationships) == 1
    assert (
        finance_opg.object_projection_graph_relationships[
            0
        ].target_object_projection_graph_id
        == identity_opg.id
    )


def test_opg_portal_rejects_projection_suffix_alias_for_external_target(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    identity_code = _build_code(
        tmp_path,
        "identity.aware",
        """
class Identity {
    name String
}

projection Identity {
    root identity.Identity
}
""".strip(),
    )
    identity_ns, identity_domains = _ns(
        fqn_prefix="aware_identity",
        namespace="identity",
        code_ids=[identity_code.id],
    )
    identity_graph = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="identity",
            description="identity",
            fqn_prefix="aware_identity",
            file_codes=[("identity.aware", identity_code)],
            namespace_by_code_id=identity_ns,
        ).graph,
        namespace_by_code_id=identity_ns,
    )

    economy_code = _build_code(
        tmp_path,
        "economy_bad.aware",
        """
class FinanceEntity {
    identity aware_identity.identity.Identity unique
}

projection FinanceEntity {
    root finance.FinanceEntity
    finance.FinanceEntity::identity aware_identity.UnknownIdentity
}
""".strip(),
    )
    economy_ns, economy_domains = _ns(
        fqn_prefix="aware_economy",
        namespace="finance",
        code_ids=[economy_code.id],
    )
    economy_build = build_object_config_graph_from_code(
        name="economy_bad",
        description="economy_bad",
        fqn_prefix="aware_economy",
        file_codes=[("economy_bad.aware", economy_code)],
        namespace_by_code_id=economy_ns,
        external_graphs=[identity_graph],
    )

    with pytest.raises(ValueError, match="target projection not found"):
        _runtime_graph_with_opgs(
            economy_build.graph,
            namespace_by_code_id=economy_ns,
            external_graphs=[identity_graph],
            cross_relationships_by_target_ocg=economy_build.cross_relationships_by_target_ocg,
        )


def test_opg_portal_ambiguous_target_projection_requires_qualified_target(
    tmp_path: Path,
) -> None:
    """
    If multiple external graphs define the same target projection name, portal targets must be qualified
    by fqn_prefix (package) to keep resolution deterministic.
    """
    import pytest

    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    identity_code_a = _build_code(
        tmp_path,
        "identity_a.aware",
        """
class Identity {}

projection Identity {
    root identity.Identity
}
""".strip(),
    )
    ns_a, domains_a = _ns(
        fqn_prefix="aware_identity_a",
        namespace="identity",
        code_ids=[identity_code_a.id],
    )
    identity_graph_a = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="identity_a",
            description="identity_a",
            fqn_prefix="aware_identity_a",
            file_codes=[("identity_a.aware", identity_code_a)],
            namespace_by_code_id=ns_a,
        ).graph,
        namespace_by_code_id=ns_a,
    )

    identity_code_b = _build_code(
        tmp_path,
        "identity_b.aware",
        """
class Identity {}

projection Identity {
    root identity.Identity
}
""".strip(),
    )
    ns_b, domains_b = _ns(
        fqn_prefix="aware_identity_b",
        namespace="identity",
        code_ids=[identity_code_b.id],
    )
    identity_graph_b = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="identity_b",
            description="identity_b",
            fqn_prefix="aware_identity_b",
            file_codes=[("identity_b.aware", identity_code_b)],
            namespace_by_code_id=ns_b,
        ).graph,
        namespace_by_code_id=ns_b,
    )

    economy_code = _build_code(
        tmp_path,
        "economy_bad.aware",
        """
class FinanceEntity {
    identity aware_identity_a.identity.Identity unique
}

projection FinanceEntity {
    root finance.FinanceEntity
    finance.FinanceEntity::identity Identity
}
""".strip(),
    )
    economy_ns, economy_domains = _ns(
        fqn_prefix="aware_economy",
        namespace="finance",
        code_ids=[economy_code.id],
    )

    with pytest.raises(ValueError) as excinfo:
        built = build_object_config_graph_from_code(
            name="economy_bad",
            description="economy_bad",
            fqn_prefix="aware_economy",
            file_codes=[("economy_bad.aware", economy_code)],
            namespace_by_code_id=economy_ns,
            external_graphs=[identity_graph_a, identity_graph_b],
        )
        _runtime_graph_with_opgs(
            built.graph,
            namespace_by_code_id=economy_ns,
            external_graphs=[identity_graph_a, identity_graph_b],
        )
    assert "ambiguous target projection" in str(excinfo.value)


def test_opg_portal_qualified_target_projection_resolves_across_packages(
    tmp_path: Path,
) -> None:
    """
    Qualified targets should resolve deterministically across external graphs with colliding projection names.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    identity_code_a = _build_code(
        tmp_path,
        "identity_a.aware",
        """
class Identity {}

projection Identity {
    root identity.Identity
}
""".strip(),
    )
    ns_a, domains_a = _ns(
        fqn_prefix="aware_identity_a",
        namespace="identity",
        code_ids=[identity_code_a.id],
    )
    identity_graph_a = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="identity_a",
            description="identity_a",
            fqn_prefix="aware_identity_a",
            file_codes=[("identity_a.aware", identity_code_a)],
            namespace_by_code_id=ns_a,
        ).graph,
        namespace_by_code_id=ns_a,
    )
    identity_opg_a = next(
        g for g in identity_graph_a.object_projection_graphs if g.name == "Identity"
    )

    identity_code_b = _build_code(
        tmp_path,
        "identity_b.aware",
        """
class Identity {}

projection Identity {
    root identity.Identity
}
""".strip(),
    )
    ns_b, domains_b = _ns(
        fqn_prefix="aware_identity_b",
        namespace="identity",
        code_ids=[identity_code_b.id],
    )
    identity_graph_b = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="identity_b",
            description="identity_b",
            fqn_prefix="aware_identity_b",
            file_codes=[("identity_b.aware", identity_code_b)],
            namespace_by_code_id=ns_b,
        ).graph,
        namespace_by_code_id=ns_b,
    )

    economy_code = _build_code(
        tmp_path,
        "economy_ok.aware",
        """
class FinanceEntity {
    identity aware_identity_a.identity.Identity unique
}

projection FinanceEntity {
    root finance.FinanceEntity
    finance.FinanceEntity::identity aware_identity_a.Identity
}
""".strip(),
    )
    economy_ns, economy_domains = _ns(
        fqn_prefix="aware_economy",
        namespace="finance",
        code_ids=[economy_code.id],
    )
    economy_build = build_object_config_graph_from_code(
        name="economy_ok",
        description="economy_ok",
        fqn_prefix="aware_economy",
        file_codes=[("economy_ok.aware", economy_code)],
        namespace_by_code_id=economy_ns,
        external_graphs=[identity_graph_a, identity_graph_b],
    )
    economy_graph = _runtime_graph_with_opgs(
        economy_build.graph,
        namespace_by_code_id=economy_ns,
        external_graphs=[identity_graph_a, identity_graph_b],
        cross_relationships_by_target_ocg=economy_build.cross_relationships_by_target_ocg,
    )

    finance_opg = next(
        g for g in economy_graph.object_projection_graphs if g.name == "FinanceEntity"
    )
    assert len(finance_opg.object_projection_graph_relationships) == 1
    portal = finance_opg.object_projection_graph_relationships[0]
    assert portal.target_object_projection_graph_id == identity_opg_a.id


def test_opg_portal_class_style_target_resolves_same_name_projection(
    tmp_path: Path,
) -> None:
    """
    Regression:
    Portal target resolution is projection-context aware. A class-style token like
    `test.ConditionConfig` must resolve to projection `condition_config` even when
    class/projection names share the same base symbol.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "class_style_portal.aware",
        """
class ConditionConfig {}

class EventConfig {
    condition_config ConditionConfig
}

projection ConditionConfig {
    root test.ConditionConfig
}

projection EventConfig {
    root test.EventConfig
    test.EventConfig::condition_config test.ConditionConfig
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )
    graph = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="class_style_portal",
            description="class_style_portal",
            fqn_prefix="pkg",
            file_codes=[("class_style_portal.aware", code)],
            namespace_by_code_id=ns,
        ).graph,
        namespace_by_code_id=ns,
    )

    event_opg = next(
        g for g in graph.object_projection_graphs if g.name == "EventConfig"
    )
    condition_opg = next(
        g for g in graph.object_projection_graphs if g.name == "ConditionConfig"
    )

    assert len(event_opg.object_projection_graph_relationships) == 1
    portal = event_opg.object_projection_graph_relationships[0]
    assert portal.object_projection_graph_id == event_opg.id
    assert portal.target_object_projection_graph_id == condition_opg.id


def test_opg_hash_changes_when_portal_relationship_added(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_a = _build_code(tmp_path, "a.aware", PORTAL_CODE)
    ns_a, domains_a = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code_a.id]
    )
    graph_a = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="a",
            description="a",
            fqn_prefix="pkg",
            file_codes=[("a.aware", code_a)],
            namespace_by_code_id=ns_a,
        ).graph,
        namespace_by_code_id=ns_a,
    )
    users_a = next(g for g in graph_a.object_projection_graphs if g.name == "Users")
    posts_a = next(g for g in graph_a.object_projection_graphs if g.name == "Posts")

    # Same membership but no portal annotation.
    no_portal = """
class User { posts Post[] }
class Post { title String }
projection Users { root test.User }
projection Posts { root test.Post }
""".strip()
    code_b = _build_code(tmp_path, "b.aware", no_portal)
    ns_b, domains_b = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code_b.id]
    )
    graph_b = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="b",
            description="b",
            fqn_prefix="pkg",
            file_codes=[("b.aware", code_b)],
            namespace_by_code_id=ns_b,
        ).graph,
        namespace_by_code_id=ns_b,
    )
    users_b = next(g for g in graph_b.object_projection_graphs if g.name == "Users")
    posts_b = next(g for g in graph_b.object_projection_graphs if g.name == "Posts")

    assert users_a.projection_hash != users_b.projection_hash
    assert posts_a.projection_hash == posts_b.projection_hash


def test_opg_portal_missing_target_projection_raises(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    bad = """
class User { posts Post[] }
class Post { title String }
projection Users {
    root test.User
    test.User::posts Missing
}
""".strip()
    code = _build_code(tmp_path, "bad.aware", bad)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )

    try:
        built = build_object_config_graph_from_code(
            name="bad",
            description="bad",
            fqn_prefix="pkg",
            file_codes=[("bad.aware", code)],
            namespace_by_code_id=ns,
        )
        _runtime_graph_with_opgs(
            built.graph,
            namespace_by_code_id=ns,
        )
        assert (
            False
        ), "Expected runtime OPG build to fail due to missing target projection for portal annotation"
    except ValueError as e:
        assert "target projection" in str(e)


def test_opg_portal_hash_stable_across_target_projection_rename(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_a = _build_code(tmp_path, "a.aware", PORTAL_CODE)
    ns_a, domains_a = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code_a.id]
    )
    graph_a = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="a",
            description="a",
            fqn_prefix="pkg",
            file_codes=[("a.aware", code_a)],
            namespace_by_code_id=ns_a,
        ).graph,
        namespace_by_code_id=ns_a,
    )
    users_a = next(g for g in graph_a.object_projection_graphs if g.name == "Users")
    posts_a = next(g for g in graph_a.object_projection_graphs if g.name == "Posts")

    # Same portal semantics, renamed target projection label.
    portal_renamed = """
class User { posts Post[] }
class Post { title String }
projection Users {
    root test.User
    test.User::posts Posts2
}
projection Posts2 { root test.Post }
""".strip()
    code_b = _build_code(tmp_path, "b.aware", portal_renamed)
    ns_b, domains_b = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code_b.id]
    )
    graph_b = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="b",
            description="b",
            fqn_prefix="pkg",
            file_codes=[("b.aware", code_b)],
            namespace_by_code_id=ns_b,
        ).graph,
        namespace_by_code_id=ns_b,
    )
    users_b = next(g for g in graph_b.object_projection_graphs if g.name == "Users")
    posts_b = next(g for g in graph_b.object_projection_graphs if g.name == "Posts2")

    # Projection hashes are membership-driven; renaming the target projection should not change hashes.
    assert posts_a.projection_hash == posts_b.projection_hash
    assert users_a.projection_hash == users_b.projection_hash


def test_opg_optional_relationship_marks_edge_optional(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "optional.aware", OPTIONAL_EDGE_CODE)
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="test", code_ids=[code.id]
    )

    graph = _runtime_graph_with_opgs(
        build_object_config_graph_from_code(
            name="optional",
            description="optional",
            fqn_prefix="pkg",
            file_codes=[("optional.aware", code)],
            namespace_by_code_id=ns,
        ).graph,
        namespace_by_code_id=ns,
    )

    opg = next((g for g in graph.object_projection_graphs if g.name == "P"), None)
    assert opg is not None
    assert opg.object_projection_graph_edges
    edge = opg.object_projection_graph_edges[0]

    assert edge.multiplicity == ObjectProjectionGraphEdgeMultiplicity.one
    assert edge.include == ObjectProjectionGraphEdgeInclude.optional
