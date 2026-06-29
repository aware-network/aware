from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_constructor import (
    ObjectProjectionGraphConstructor,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code

from dart_grammar.transformers.runtime_to_dart_transformer import RuntimeToDartTransformer


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        code_key=name,
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _namespace_by_code_id(
    *, fqn_prefix: str, domain: str, schema: str, code_ids: list[UUID]
) -> dict[UUID, NamespacePath]:
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=f"{domain}.{schema}")
        for cid in code_ids
    }


CODE = """
class Identity {
    fn signup construct(public_key String) -> Identity {
        \"\"\"Genesis constructor.\"\"\"
    }
}

class Human {
    fn create_human construct(actor_id UUID) -> Human {
        \"\"\"Internal constructor (not an OPG constructor).\"\"\"
    }
}

projection Identity {
    root default.Identity
}
""".strip()


def test_runtime_to_dart_transformer_drops_non_opg_constructors(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "identity.aware", CODE)
    ns = _namespace_by_code_id(
        fqn_prefix="pkg", domain="dom", schema="default", code_ids=[code.id]
    )

    res = build_object_config_graph_from_code(
        name="identity",
        description="identity",
        fqn_prefix="pkg",
        file_codes=[("identity.aware", code)],
        namespace_by_code_id=ns,
    )
    ocg = res.graph

    identity_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "Identity"
    )
    human_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "Human"
    )

    assert any((l.function_config.name == "signup") for l in identity_cc.class_config_function_configs)
    assert any((l.function_config.name == "create_human") for l in human_cc.class_config_function_configs)
    signup_link = next(l for l in identity_cc.class_config_function_configs if l.function_config.name == "signup")
    opg = ObjectProjectionGraph(
        object_config_graph_id=ocg.id,
        name="Identity",
        description="Identity projection",
        language=CodeLanguage.aware,
        projection_hash="test",
    )
    root_node = ObjectProjectionGraphNode(
        object_projection_graph_id=opg.id,
        class_config_id=identity_cc.id,
        class_config=identity_cc,
        is_root=True,
    )
    opg.object_projection_graph_nodes.append(root_node)
    opg.object_projection_graph_constructors.append(
        ObjectProjectionGraphConstructor(
            object_projection_graph_id=opg.id,
            root_node_id=root_node.id,
            root_node=root_node,
            function_constructor_id=signup_link.id,
            function_constructor=signup_link,
        )
    )
    ocg.object_projection_graphs = [opg]

    transformed = RuntimeToDartTransformer().transform(ocg)
    assert transformed is ocg

    identity_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "Identity"
    )
    human_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config is not None and n.class_config.name == "Human"
    )

    identity_names = [l.function_config.name for l in identity_cc.class_config_function_configs]
    human_names = [l.function_config.name for l in human_cc.class_config_function_configs]

    assert "signup" in identity_names
    assert "create_human" not in human_names
    function_names_after = [
        n.function_config.name
        for n in ocg.object_config_graph_nodes
        if n.type == ObjectConfigGraphNodeType.function and n.function_config is not None
    ]
    assert "create_human" not in function_names_after
