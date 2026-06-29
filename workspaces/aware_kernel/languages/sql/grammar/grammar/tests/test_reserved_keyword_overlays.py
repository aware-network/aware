from pathlib import Path
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Meta Ontology

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Runtime
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.runtime_derivation.clone import (
    clone_runtime_graph_for_language_transformer_handoff,
)
from aware_meta.graph.config.runtime_derivation.schemas import (
    RuntimeObjectConfigGraphDerivationRequest,
)
from aware_meta.graph.config.runtime_derivation.service import (
    RuntimeObjectConfigGraphDerivationService,
)
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry

# SQL meta plugin (target language)
from sql_grammar.meta_language_plugin import SQL_META_PLUGIN
from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.renderers.renderer import SQLRenderer
from aware_grammar.meta_language_plugin import AWARE_META_PLUGIN
from sql_grammar.transformers.runtime_to_sql_transformer import RuntimeToSQLTransformer


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


def _derive_sql_graph(
    *,
    graph,
    namespace_by_code_id: dict[UUID, NamespacePath],
):
    runtime_graph = (
        RuntimeObjectConfigGraphDerivationService()
        .derive(RuntimeObjectConfigGraphDerivationRequest(source_graph=graph))
        .runtime_graph
    )
    transformer = RuntimeToSQLTransformer(namespace_by_code_id=namespace_by_code_id)
    return transformer.transform(
        clone_runtime_graph_for_language_transformer_handoff(runtime_graph),
        code_primitive_type=None,
    )


def test_reserved_keyword_overlays_generate_sql_class_and_column_overlays(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "sql_reserved.aware",
        """
class From {
    id UUID
    from String
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    graph = build_object_config_graph_from_code(
        name="reserved_overlays",
        description="reserved_overlays",
        fqn_prefix="pkg",
        file_codes=[("sql_reserved.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    sql_overlay = next(
        (
            ov
            for ov in graph.object_config_graph_overlays
            if ov.language == CodeLanguage.sql
        ),
        None,
    )
    assert (
        sql_overlay is not None
    ), "Expected a SQL overlay to be generated for reserved identifiers"

    from_cls = next(
        (
            n.class_config
            for n in graph.object_config_graph_nodes
            if n.class_config and n.class_config.name == "From"
        ),
        None,
    )
    assert from_cls is not None

    from_attr = next(
        (
            e.attribute_config
            for e in from_cls.class_config_attribute_configs
            if e.attribute_config and e.attribute_config.name == "from"
        ),
        None,
    )
    assert from_attr is not None

    class_overlays_by_id = {
        o.class_config_id: o for o in sql_overlay.class_config_overlays
    }
    class_ov = class_overlays_by_id.get(from_cls.id)
    assert class_ov is not None
    assert class_ov.rendered_name == "from_"

    attr_overlays_by_id = {
        o.attribute_config_id: o for o in sql_overlay.attribute_config_overlays
    }
    attr_ov = attr_overlays_by_id.get(from_attr.id)
    assert attr_ov is not None
    assert attr_ov.rendered_name == "from_"

    # End-to-end: SQL renderer consumes overlays (no renderer-side renaming logic).
    renderer = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_language_overlay(sql_overlay)
    ddl = renderer._emit_table(from_cls, class_lookup={from_cls.id: from_cls})
    assert "CREATE TABLE from_ (" in ddl
    assert "from_ TEXT" in ddl


def test_reserved_keyword_overlays_apply_to_fk_references(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(AWARE_META_PLUGIN)
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "sql_reserved_fk.aware",
        """
class Enum {
    id UUID
}

class EnumChange {
    id UUID
    enum Enum
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    graph = build_object_config_graph_from_code(
        name="reserved_overlays_fk",
        description="reserved_overlays_fk",
        fqn_prefix="pkg",
        file_codes=[("sql_reserved_fk.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    derived = _derive_sql_graph(
        graph=graph,
        namespace_by_code_id=ns,
    )

    sql_overlay = next(
        (
            ov
            for ov in derived.object_config_graph_overlays
            if ov.language == CodeLanguage.sql
        ),
        None,
    )
    assert (
        sql_overlay is not None
    ), "Expected a SQL overlay to be generated for reserved identifiers"

    enum_cls = next(
        (
            n.class_config
            for n in derived.object_config_graph_nodes
            if n.class_config and n.class_config.name == "Enum"
        ),
        None,
    )
    assert enum_cls is not None

    enum_change_cls = next(
        (
            n.class_config
            for n in derived.object_config_graph_nodes
            if n.class_config and n.class_config.name == "EnumChange"
        ),
        None,
    )
    assert enum_change_cls is not None

    renderer = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_language_overlay(sql_overlay)
    ddl = renderer._emit_table(
        enum_change_cls,
        class_lookup={enum_cls.id: enum_cls, enum_change_cls.id: enum_change_cls},
    )
    assert "CREATE TABLE enum_change (" in ddl
    # Lane-scoped SQL tables use a composite PK/FK:
    #   (branch_id, projection_hash, id)
    # Reserved identifier overlays must still apply to FK references.
    assert "REFERENCES enum_(branch_id, projection_hash, id)" in ddl


def test_reserved_keyword_overlays_rename_window_table(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "sql_reserved_window.aware",
        """
class Window {
    id UUID
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    graph = build_object_config_graph_from_code(
        name="reserved_window",
        description="reserved_window",
        fqn_prefix="pkg",
        file_codes=[("sql_reserved_window.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    sql_overlay = next(
        (
            ov
            for ov in graph.object_config_graph_overlays
            if ov.language == CodeLanguage.sql
        ),
        None,
    )
    assert (
        sql_overlay is not None
    ), "Expected a SQL overlay to be generated for reserved identifiers"

    window_cls = next(
        (
            n.class_config
            for n in graph.object_config_graph_nodes
            if n.class_config and n.class_config.name == "Window"
        ),
        None,
    )
    assert window_cls is not None

    class_overlays_by_id = {
        o.class_config_id: o for o in sql_overlay.class_config_overlays
    }
    class_ov = class_overlays_by_id.get(window_cls.id)
    assert class_ov is not None
    assert class_ov.rendered_name == "window_"

    renderer = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_language_overlay(sql_overlay)
    ddl = renderer._emit_table(window_cls, class_lookup={window_cls.id: window_cls})
    assert "CREATE TABLE window_ (" in ddl


def test_reserved_keyword_overlays_rename_transaction_table(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "sql_reserved_transaction.aware",
        """
class Transaction {
    id UUID
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg", namespace="default", code_ids=[code.id]
    )
    graph = build_object_config_graph_from_code(
        name="reserved_transaction",
        description="reserved_transaction",
        fqn_prefix="pkg",
        file_codes=[("sql_reserved_transaction.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    sql_overlay = next(
        (
            ov
            for ov in graph.object_config_graph_overlays
            if ov.language == CodeLanguage.sql
        ),
        None,
    )
    assert (
        sql_overlay is not None
    ), "Expected a SQL overlay to be generated for reserved identifiers"

    tx_cls = next(
        (
            n.class_config
            for n in graph.object_config_graph_nodes
            if n.class_config and n.class_config.name == "Transaction"
        ),
        None,
    )
    assert tx_cls is not None

    class_overlays_by_id = {
        o.class_config_id: o for o in sql_overlay.class_config_overlays
    }
    class_ov = class_overlays_by_id.get(tx_cls.id)
    assert class_ov is not None
    assert class_ov.rendered_name == "transaction_"

    renderer = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    renderer.set_language_overlay(sql_overlay)
    ddl = renderer._emit_table(tx_cls, class_lookup={tx_cls.id: tx_cls})
    assert "CREATE TABLE transaction_ (" in ddl
