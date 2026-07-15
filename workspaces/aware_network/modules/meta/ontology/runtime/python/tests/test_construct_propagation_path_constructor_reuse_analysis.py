from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.transformers.aware_to_runtime_transformer import (
    AwareToRuntimeTransformer,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.relationship_analysis import analyze_relationships
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)


SOURCE = """
class Root {
    branches Branch[]

    fn create_root (
        branch_id UUID,
        lane_id UUID,
    ) -> Branch {
        let ensured_branch = construct branches.create_with_lane_and_branch(
            branch_id = branch_id,
            lane_id = lane_id,
        )
    }
}

class Branch {
    lanes Lane[]
    rels BranchRelationship[]

    branch_id UUID key

    fn create_with_lane_and_branch construct (
        branch_id UUID key,
        lane_id UUID,
    ) -> Branch {
        let created_lane = construct lanes.create(
            lane_id = lane_id,
        )
    }

    fn attach_lane (
        lane_id UUID,
    ) -> Lane {
        let attached_lane = construct lanes.create(
            lane_id = lane_id,
        )
    }

    fn attach_rel (
        target_branch_id UUID,
    ) -> BranchRelationship {
        let attached = construct rels.create(
            target_branch_id = target_branch_id,
        )
    }
}

class Lane {
    lane_id UUID key

    fn create construct (
        lane_id UUID key,
    ) -> Lane {
    }
}

class BranchRelationship {
    target_branch Branch key

    fn create construct (
        target_branch_id UUID key,
    ) -> BranchRelationship {
    }
}
""".strip()


def _build_graph(tmp_path: Path) -> tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]:
    file_path = tmp_path / "path_constructor_reuse_analysis.aware"
    file_path.write_text(SOURCE, encoding="utf-8")
    code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(file_path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    namespace_by_code_id = {
        code.id: NamespacePath(package="pkg", namespace="dom.sch"),
    }
    result = build_object_config_graph_from_code(
        name="path_constructor_reuse_analysis",
        description="path_constructor_reuse_analysis",
        fqn_prefix="pkg",
        file_codes=[(str(file_path), code)],
        namespace_by_code_id=namespace_by_code_id,
    )
    return result.graph, namespace_by_code_id


def test_relationship_analysis_accepts_runtime_graph_when_path_constructors_are_reused(
    tmp_path: Path,
) -> None:
    graph, namespace_by_code_id = _build_graph(tmp_path)

    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id,
        relationship_loading_config=None,
    ).transform(graph)

    analyses = analyze_relationships(runtime, namespace_by_code_id=namespace_by_code_id)
    by_signature = {
        (analysis.source_class.name, analysis.forward_reference_attr.name): analysis
        for analysis in analyses
    }

    assert ("Root", "branches") in by_signature
    assert ("Branch", "lanes") in by_signature
    assert ("Branch", "rels") in by_signature
    assert by_signature[("Branch", "lanes")].construct_target_class is not None
    assert by_signature[("Branch", "lanes")].construct_target_class.name == "Lane"
