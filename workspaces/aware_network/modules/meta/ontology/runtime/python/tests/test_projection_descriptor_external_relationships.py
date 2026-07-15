# @code-under-test: ../aware_meta/graph/projection/descriptor.py

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.projection.descriptor import get_natural_language_description
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)


def _build_code(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def test_projection_descriptor_resolves_detached_cross_ocg_relationships(
    tmp_path: Path,
) -> None:
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

    meta_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=meta_graph.id,
            target_object_config_graph_id=history_graph.id,
            class_config_relationships=[cross_rels[0]],
        )
    )

    meta_graph_loaded = ObjectConfigGraph.model_validate_json(
        meta_graph.model_dump_json(exclude_none=True, by_alias=True)
    )

    meta_branch_cc_id = next(
        n.class_config.id
        for n in meta_graph_loaded.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "ObjectInstanceGraphBranch"
    )
    history_branch_cc_id = next(
        n.class_config.id
        for n in history_graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Branch"
    )

    opg_id = uuid4()
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="environment",
        description=None,
        language=CodeLanguage.aware,
        projection_hash="sha256:test:env",
        object_config_graph_id=meta_graph_loaded.id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=meta_branch_cc_id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=history_branch_cc_id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=cross_rels[0].id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
                include=ObjectProjectionGraphEdgeInclude.required,
                multiplicity=ObjectProjectionGraphEdgeMultiplicity.one,
            )
        ],
    )

    description = get_natural_language_description(
        meta_graph_loaded,
        opg,
        external_graphs=[history_graph],
    )
    assert "ObjectInstanceGraphBranch" in description
    assert "Branch" in description
    assert f"relationship_id={cross_rels[0].id}" in description


def test_projection_descriptor_resolves_relationships_from_external_graph_nodes(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    ext_code = _build_code(
        tmp_path,
        "ext.aware",
        """
class Parent {
    child Child
}
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

    relationship = next(
        n.class_config_relationship
        for n in ext_graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.relationship
        and n.class_config_relationship is not None
    )
    parent_cc_id = next(
        n.class_config.id
        for n in ext_graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Parent"
    )
    child_cc_id = next(
        n.class_config.id
        for n in ext_graph.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.class_
        and n.class_config is not None
        and n.class_config.name == "Child"
    )

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

    opg_id = uuid4()
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="external",
        description=None,
        language=CodeLanguage.aware,
        projection_hash="sha256:test:external",
        object_config_graph_id=local_graph.id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cc_id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cc_id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=relationship.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
                include=ObjectProjectionGraphEdgeInclude.required,
                multiplicity=ObjectProjectionGraphEdgeMultiplicity.one,
            )
        ],
    )

    description = get_natural_language_description(
        local_graph, opg, external_graphs=[ext_graph]
    )
    assert "Parent" in description
    assert "Child" in description
    assert f"relationship_id={relationship.id}" in description
