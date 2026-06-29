from __future__ import annotations

from pathlib import Path

from aware_content.builder import get_text
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.section.writer import CodeSectionWriter
from aware_orm.session.autobind import disable_autobind

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)

from dart_grammar.layout_strategy import DartLayoutStrategyTemplateMixin
from dart_grammar.renderer_materialization_opg import DartMaterializationOpgRenderer
from dart_grammar_test_support import make_class, make_class_node


def test_materialization_opg_registers_external_graph_materializations(tmp_path: Path) -> None:
    layout = DartLayoutStrategyTemplateMixin(
        base_dir=tmp_path,
        entity_template_paths={},
        import_root="aware_conversation_ontology",
    )
    renderer = DartMaterializationOpgRenderer(layout_strategy=layout)

    with disable_autobind():
        external_cls = make_class(name="ContentChainContent", package="aware_content")
        external_graph = ObjectConfigGraph(
            name="content_aware",
            description=None,
            hash="ext",
            fqn_prefix="aware_content",
            language=CodeLanguage.aware,
        )
        external_graph.object_config_graph_nodes = [
            make_class_node(object_config_graph_id=external_graph.id, class_config=external_cls)
        ]

        root_cls = make_class(name="Conversation", package="aware_conversation")
        graph = ObjectConfigGraph(
            name="conversation_aware",
            description=None,
            hash="local",
            fqn_prefix="aware_conversation",
            language=CodeLanguage.aware,
        )
        graph.object_config_graph_nodes = [make_class_node(object_config_graph_id=graph.id, class_config=root_cls)]

        opg = ObjectProjectionGraph(
            object_config_graph_id=graph.id,
            name="conversation",
            description=None,
            language=CodeLanguage.aware,
            projection_hash="ph",
        )
        opg.object_projection_graph_nodes = [
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg.id,
                class_config_id=root_cls.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg.id,
                class_config_id=external_cls.id,
                is_root=False,
            ),
        ]
        graph.object_projection_graphs = [opg]

    renderer.set_external_graphs([external_graph])
    renderer.bind_object_config_graph(graph)

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([], writer, schema="default")

    dart_source = get_text(code.content_part_text)
    assert "package:aware_content/_aware/materialization/materializers_opg.dart" in dart_source
    assert "registerContentMaterializations" in dart_source

    # Ensure external materializations are registered before local manifest bindings.
    assert dart_source.index("registerContentMaterializations") < dart_source.index(
        "registry.registerAll(oig_manifest.oigMaterializationManifest)"
    )


def test_materialization_opg_uses_external_owner_import_for_external_root(tmp_path: Path) -> None:
    layout = DartLayoutStrategyTemplateMixin(
        base_dir=tmp_path,
        entity_template_paths={},
        import_root="aware_environment_ontology",
    )
    renderer = DartMaterializationOpgRenderer(layout_strategy=layout)

    with disable_autobind():
        external_root_cls = make_class(
            name="CodeModule",
            package="aware_code",
            schema="module",
        )
        external_graph = ObjectConfigGraph(
            name="code_aware",
            description=None,
            hash="ext",
            fqn_prefix="aware_code",
            language=CodeLanguage.aware,
        )
        external_graph.object_config_graph_nodes = [
            make_class_node(object_config_graph_id=external_graph.id, class_config=external_root_cls)
        ]

        graph = ObjectConfigGraph(
            name="environment_aware",
            description=None,
            hash="local",
            fqn_prefix="aware_environment",
            language=CodeLanguage.aware,
        )

        opg = ObjectProjectionGraph(
            object_config_graph_id=graph.id,
            name="code_module",
            description=None,
            language=CodeLanguage.aware,
            projection_hash="ph",
        )
        opg.object_projection_graph_nodes = [
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg.id,
                class_config_id=external_root_cls.id,
                is_root=True,
            ),
        ]
        graph.object_projection_graphs = [opg]

    renderer.set_external_graphs([external_graph])
    renderer.bind_object_config_graph(graph)

    code = renderer.create_empty_code()
    with CodeSectionWriter(code, CodeSectionBuilderIndex(), indent_size=renderer.indent) as writer:
        renderer.emit_file([], writer, schema="default")

    dart_source = get_text(code.content_part_text)
    assert "package:aware_code_ontology/module/code_module.dart" in dart_source
    assert "package:aware_environment_ontology/default/code_module.dart" not in dart_source
