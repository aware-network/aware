from pathlib import Path
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code

from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.transformers.runtime_to_sql_transformer import RuntimeToSQLTransformer


def _build_code(tmp_path: Path, rel_path: str, content: str):
    path = tmp_path / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def test_sql_layout_uses_template_paths_for_enum_grouping(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "structure/repository/repository_delta.aware",
        """
enum RepositoryTextPatchOp {
    delete
    insert
    replace
}

class RepositoryDelta {
    id UUID
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="structure.repository", code_ids=[code.id]
    )
    graph = build_object_config_graph_from_code(
        name="repo-delta",
        description="repo-delta",
        fqn_prefix="pkg",
        file_codes=[("structure/repository/repository_delta.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    entity_template_paths: dict[str, Path] = {}
    for node in graph.object_config_graph_nodes:
        layouts = node.layouts or []
        if not layouts or not layouts[0].relative_path:
            continue
        rel = Path(layouts[0].relative_path).with_suffix(".sql")
        if node.enum_config is not None:
            entity_template_paths[str(node.enum_config.id)] = rel
        if node.class_config is not None:
            entity_template_paths[str(node.class_config.id)] = rel

    enum_config = next(
        (
            n.enum_config
            for n in graph.object_config_graph_nodes
            if n.enum_config and n.enum_config.name == "RepositoryTextPatchOp"
        ),
        None,
    )
    assert enum_config is not None

    layout = SQLLayoutStrategyNamespace(
        tmp_path, entity_template_paths=entity_template_paths
    )
    layout.bind_graph(graph)
    assert layout.get_enum_file_path(enum_config) == Path(
        "structure/repository/repository_delta.sql"
    )


def test_sql_layout_prefers_ocg_node_layout_before_namespace_fallback(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "conversation/conversation.aware",
        """
class Conversation {
    id UUID
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="aware_conversation",
        namespace="default",
        code_ids=[code.id],
    )
    graph = build_object_config_graph_from_code(
        name="conversation",
        description="conversation",
        fqn_prefix="aware_conversation",
        file_codes=[("conversation/conversation.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    class_config = next(
        (
            node.class_config
            for node in graph.object_config_graph_nodes
            if node.class_config is not None
        ),
        None,
    )
    assert class_config is not None

    layout = SQLLayoutStrategyNamespace(tmp_path)
    layout.bind_graph(graph)

    assert layout.get_class_file_path(class_config) == Path(
        "conversation/conversation.sql"
    )


def test_sql_layout_anchors_synthetic_join_tables_to_source_layout(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    project_code = _build_code(
        tmp_path,
        "project/project.aware",
        """
class Project {
    id UUID
    tasks Task[] many
}
""".strip(),
    )
    task_code = _build_code(
        tmp_path,
        "task/task.aware",
        """
class Task {
    id UUID
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="aware_workflow",
        namespace="default",
        code_ids=[project_code.id, task_code.id],
    )
    graph = build_object_config_graph_from_code(
        name="workflow",
        description="workflow",
        fqn_prefix="aware_workflow",
        file_codes=[
            ("project/project.aware", project_code),
            ("task/task.aware", task_code),
        ],
        namespace_by_code_id=ns,
    ).graph

    transformer = RuntimeToSQLTransformer(namespace_by_code_id=ns)
    sql_graph = transformer.transform(graph)
    layout = SQLLayoutStrategyNamespace(
        tmp_path,
        generated_ocg_node_manifest=transformer.get_generated_ocg_node_manifest(),
    )
    layout.bind_graph(sql_graph)

    join_class = next(
        (
            node.class_config
            for node in sql_graph.object_config_graph_nodes
            if node.class_config is not None
            and node.class_config.name == "ProjectTaskJoin"
        ),
        None,
    )
    assert join_class is not None

    assert layout.get_class_file_path(join_class) == Path(
        "project/project_task_join.sql"
    )
