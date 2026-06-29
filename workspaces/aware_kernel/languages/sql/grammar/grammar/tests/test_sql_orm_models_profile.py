from pathlib import Path
from uuid import UUID, uuid4

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.runtime_derivation.schemas import (
    RuntimeObjectConfigGraphDerivationRequest,
)
from aware_meta.graph.config.runtime_derivation.clone import (
    clone_runtime_graph_for_language_transformer_handoff,
)
from aware_meta.graph.config.runtime_derivation.service import (
    RuntimeObjectConfigGraphDerivationService,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization.language_service import (
    LanguagePluginMaterializationRequest,
    materialize_object_config_graph_via_language_plugin,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.meta_language_plugin import SQL_META_PLUGIN
from sql_grammar.renderer_policy import SQLRenderPolicy
from sql_grammar.renderers.renderer import SqliteSQLRenderer
from sql_grammar.transformer_policy import SQLTransformPolicy
from sql_grammar.transformers.runtime_to_sql_transformer import RuntimeToSQLTransformer


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {cid: NamespacePath(package=fqn_prefix, namespace=namespace) for cid in code_ids}, []


def _build_graph(tmp_path: Path, content: str) -> tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(tmp_path, "state.aware", content.strip())
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id],
    )
    graph = build_object_config_graph_from_code(
        name="state",
        description="state",
        fqn_prefix="pkg",
        file_codes=[("state.aware", code)],
        namespace_by_code_id=ns,
    ).graph
    return graph, ns


def _lower_sql(
    graph: ObjectConfigGraph,
    ns: dict[UUID, NamespacePath],
    *,
    policy: SQLTransformPolicy,
) -> ObjectConfigGraph:
    runtime_graph = (
        RuntimeObjectConfigGraphDerivationService()
        .derive(RuntimeObjectConfigGraphDerivationRequest(source_graph=graph))
        .runtime_graph
    )
    transformer = RuntimeToSQLTransformer(namespace_by_code_id=ns)
    transformer.set_policy(policy)
    return transformer.transform(runtime_graph.model_copy(deep=True), code_primitive_type=None)


def _class_by_name(graph: ObjectConfigGraph, name: str) -> ClassConfig:
    for node in graph.object_config_graph_nodes:
        if (
            node.type == ObjectConfigGraphNodeType.class_
            and node.class_config is not None
            and node.class_config.name == name
        ):
            return node.class_config
    raise AssertionError(f"Class not found: {name}")


def _attr_names(cls: ClassConfig) -> set[str]:
    return {
        link.attribute_config.name for link in cls.class_config_attribute_configs if link.attribute_config is not None
    }


def test_sql_orm_models_transformer_skips_projection_lane_columns(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class LocalWorkspaceStatusBaseline {
    workspace_handle String key
    workspace_root String key
    source String = "local"
}
""",
    )

    projection_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.projection_default(),
    )
    projection_attrs = _attr_names(_class_by_name(projection_sql, "LocalWorkspaceStatusBaseline"))
    assert {"branch_id", "projection_hash", "id"} <= projection_attrs


def test_sql_transformer_shallow_handoff_preserves_source_runtime_attrs(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class LocalWorkspaceStatusBaseline {
    workspace_handle String key
    workspace_root String key
    source String = "local"
}
""",
    )
    runtime_graph = (
        RuntimeObjectConfigGraphDerivationService()
        .derive(RuntimeObjectConfigGraphDerivationRequest(source_graph=graph))
        .runtime_graph
    )
    runtime_cls = _class_by_name(runtime_graph, "LocalWorkspaceStatusBaseline")
    before_attrs = _attr_names(runtime_cls)
    handoff = clone_runtime_graph_for_language_transformer_handoff(runtime_graph)
    transformer = RuntimeToSQLTransformer(namespace_by_code_id=ns)
    transformer.set_policy(SQLTransformPolicy.projection_default())

    sql_graph = transformer.transform(handoff, code_primitive_type=None)

    assert _attr_names(runtime_cls) == before_attrs
    assert {"branch_id", "projection_hash", "id"} <= _attr_names(
        _class_by_name(sql_graph, "LocalWorkspaceStatusBaseline")
    )
    assert _class_by_name(handoff, "LocalWorkspaceStatusBaseline") is not runtime_cls

    model_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.orm_models_default(),
    )
    model_cls = _class_by_name(model_sql, "LocalWorkspaceStatusBaseline")
    model_attrs = _attr_names(model_cls)
    assert "id" in model_attrs
    assert "branch_id" not in model_attrs
    assert "projection_hash" not in model_attrs

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_policy(SQLRenderPolicy.orm_models_default())
    ddl = renderer._emit_table(model_cls, class_lookup={model_cls.id: model_cls})

    assert "branch_id" not in ddl
    assert "projection_hash" not in ddl
    assert "id TEXT NOT NULL" in ddl
    assert "workspace_handle TEXT NOT NULL" in ddl


def test_projection_renderer_does_not_emit_unary_unique_for_semantic_keys(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class ServiceOperationLike {
    service_operation_config_id String key
    operation_key String key
    explicit_label String unique
}
""",
    )
    projection_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.projection_default(),
    )
    cls = _class_by_name(projection_sql, "ServiceOperationLike")

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_policy(SQLRenderPolicy.projection_default())
    renderer.bind_object_config_graph(projection_sql)
    ddl = renderer._emit_table(cls, class_lookup={cls.id: cls})

    assert "service_operation_config_id TEXT NOT NULL UNIQUE" not in ddl
    assert "operation_key TEXT NOT NULL UNIQUE" not in ddl
    assert "PRIMARY KEY (branch_id, projection_hash, id)" in ddl
    assert "UNIQUE (branch_id, projection_hash, service_operation_config_id, operation_key)" in ddl
    assert "explicit_label TEXT NOT NULL UNIQUE" in ddl


def test_projection_renderer_scopes_child_semantic_keys_to_parent_fk(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class Parent {
    children Child[]
    name String key
}

class Child {
    call_key UUID key
    label String
}
""",
    )
    projection_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.projection_default(),
    )
    parent_cls = _class_by_name(projection_sql, "Parent")
    child_cls = _class_by_name(projection_sql, "Child")

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_policy(SQLRenderPolicy.projection_default())
    renderer.bind_object_config_graph(projection_sql)
    ddl = renderer._emit_table(
        child_cls,
        class_lookup={parent_cls.id: parent_cls, child_cls.id: child_cls},
    )

    assert "PRIMARY KEY (branch_id, projection_hash, id)" in ddl
    assert "UNIQUE (branch_id, projection_hash, parent_id, call_key)" in ddl
    assert (
        "FOREIGN KEY (branch_id, projection_hash, parent_id) REFERENCES parent(branch_id, projection_hash, id)" in ddl
    )


def test_sql_orm_models_renderer_uses_model_storage_fk_and_indexes(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class Organization {
    name String
}

class Member {
    email String
    org Organization
}

ann default.Member::email index
""",
    )
    model_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.orm_models_default(),
    )
    organization_cls = _class_by_name(model_sql, "Organization")
    member_cls = _class_by_name(model_sql, "Member")

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_policy(SQLRenderPolicy.orm_models_default())
    renderer.bind_object_config_graph(model_sql)
    ddl = renderer._emit_table(
        member_cls,
        class_lookup={
            organization_cls.id: organization_cls,
            member_cls.id: member_cls,
        },
    )
    index_sql = renderer._emit_indexes_for_table(member_cls)

    assert "branch_id" not in ddl
    assert "projection_hash" not in ddl
    assert "REFERENCES organization(id)" in ddl
    assert "branch_id" not in index_sql
    assert "projection_hash" not in index_sql
    assert " ON member (email);" in index_sql


def test_sql_orm_models_renderer_uses_storage_annotations_for_tuple_constraints(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class LocalWorkspaceFsCodeStatusPath {
    path_status_identity String key
    status_identity String
    path_key String
    root_relative_path String
    label String unique
}

ann default.LocalWorkspaceFsCodeStatusPath storage unique by_status_path status_identity path_key
ann default.LocalWorkspaceFsCodeStatusPath storage index by_status status_identity
""",
    )
    model_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.orm_models_default(),
    )
    status_path_cls = _class_by_name(model_sql, "LocalWorkspaceFsCodeStatusPath")

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_policy(SQLRenderPolicy.orm_models_default())
    renderer.bind_object_config_graph(model_sql)
    ddl = renderer._emit_table(status_path_cls, class_lookup={status_path_cls.id: status_path_cls})
    index_sql = renderer._emit_indexes_for_table(status_path_cls)

    assert "branch_id" not in ddl
    assert "projection_hash" not in ddl
    assert "PRIMARY KEY (id)" in ddl
    assert "path_status_identity TEXT NOT NULL UNIQUE" not in ddl
    assert "label TEXT NOT NULL UNIQUE" in ddl
    assert "CREATE UNIQUE INDEX" in index_sql
    assert " ON local_workspace_fs_code_status_path (status_identity, path_key);" in index_sql
    assert "CREATE INDEX" in index_sql
    assert " ON local_workspace_fs_code_status_path (status_identity);" in index_sql


def test_sql_orm_models_keeps_authored_branch_projection_fields_as_state_columns(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class LocalOigCommit {
    commit_id String key
}

class LocalOigCommitAction {
    commit LocalOigCommit
    branch_id String key
    projection_hash String key
    operation_label String key
}
""",
    )
    model_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.orm_models_default(),
    )
    commit_cls = _class_by_name(model_sql, "LocalOigCommit")
    action_cls = _class_by_name(model_sql, "LocalOigCommitAction")

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_policy(SQLRenderPolicy.orm_models_default())
    renderer.bind_object_config_graph(model_sql)
    ddl = renderer._emit_table(
        action_cls,
        class_lookup={
            commit_cls.id: commit_cls,
            action_cls.id: action_cls,
        },
    )

    assert "branch_id TEXT NOT NULL UNIQUE" not in ddl
    assert "projection_hash TEXT NOT NULL UNIQUE" not in ddl
    assert "branch_id TEXT NOT NULL" in ddl
    assert "projection_hash TEXT NOT NULL" in ddl
    assert "PRIMARY KEY (id)" in ddl
    assert "PRIMARY KEY (id, branch_id, projection_hash)" not in ddl
    assert "UNIQUE (branch_id, projection_hash" not in ddl
    assert "REFERENCES local_oig_commit(id)" in ddl


def test_sql_storage_index_names_ignore_transient_annotation_ids(
    tmp_path: Path,
) -> None:
    graph, ns = _build_graph(
        tmp_path,
        """
class LocalWorkspaceFsCodeStatusPath {
    path_status_identity String key
    status_identity String
    path_key String
}

ann default.LocalWorkspaceFsCodeStatusPath storage unique by_status_path status_identity path_key
ann default.LocalWorkspaceFsCodeStatusPath storage index by_status status_identity
""",
    )
    model_sql = _lower_sql(
        graph,
        ns,
        policy=SQLTransformPolicy.orm_models_default(),
    )
    status_path_cls = _class_by_name(model_sql, "LocalWorkspaceFsCodeStatusPath")

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_policy(SQLRenderPolicy.orm_models_default())
    renderer.bind_object_config_graph(model_sql)
    index_sql = renderer._emit_indexes_for_table(status_path_cls)

    for annotation in model_sql.object_config_graph_annotations:
        storage_view = getattr(annotation, "code_section_annotation_storage", None)
        if storage_view is not None:
            storage_view.id = uuid4()
            annotation.id = uuid4()

    rebound_renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    rebound_renderer.set_policy(SQLRenderPolicy.orm_models_default())
    rebound_renderer.bind_object_config_graph(model_sql)

    assert rebound_renderer._emit_indexes_for_table(status_path_cls) == index_sql


def test_sql_materialization_service_applies_orm_models_profile(tmp_path: Path) -> None:
    graph, _ns = _build_graph(
        tmp_path,
        """
class LocalWorkspaceStatusBaseline {
    workspace_handle String key
    workspace_root String key
}
""",
    )
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)
    output_root = tmp_path / "sqlite"

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=graph,
            target_language_plugin_id=CodeLanguage.sql,
            output_root=output_root,
            renderer_kind="sqlite",
            renderer_profile="orm_models",
            emit_files=True,
        )
    )

    assert result.renderer_profile == "orm_models"
    assert result.generated_files
    ddl = "\n".join((output_root / generated.path).read_text(encoding="utf-8") for generated in result.generated_files)
    assert "CREATE TABLE local_workspace_status_baseline" in ddl
    assert "branch_id" not in ddl
    assert "projection_hash" not in ddl
