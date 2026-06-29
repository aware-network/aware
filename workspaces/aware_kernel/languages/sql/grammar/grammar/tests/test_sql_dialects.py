from pathlib import Path
from uuid import UUID

from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization import RuntimeToLanguageLoweringCache
import aware_meta.materialization.language_service as language_service
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)

from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.meta_language_plugin import SQL_META_PLUGIN
from sql_grammar.renderers.renderer import SQLRenderer, SqliteSQLRenderer


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
    return {cid: NamespacePath(package=fqn_prefix, namespace=namespace) for cid in code_ids}, []


def _descriptor_link(
    *,
    parent: AttributeTypeDescriptor,
    child: AttributeTypeDescriptor,
    role: Role,
    position: int = 0,
) -> AttributeTypeDescriptorLink:
    return AttributeTypeDescriptorLink(
        attribute_type_descriptor_id=parent.id,
        child=child,
        child_id=child.id,
        role=role,
        position=position,
    )


def test_sql_dialects_render_enum_and_enum_columns_consistently(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "dialects.aware",
        """
enum From {
    a
    b
}

class Foo {
    id UUID
    kind From
}
""".strip(),
    )
    ns, domains = _ns(fqn_prefix="pkg", namespace="default", code_ids=[code.id])
    graph = build_object_config_graph_from_code(
        name="dialects",
        description="dialects",
        fqn_prefix="pkg",
        file_codes=[("dialects.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    sql_overlay = next((ov for ov in graph.object_config_graph_overlays if ov.language == CodeLanguage.sql), None)
    assert sql_overlay is not None

    enum_from = next(
        (n.enum_config for n in graph.object_config_graph_nodes if n.enum_config and n.enum_config.name == "From"),
        None,
    )
    assert enum_from is not None

    foo_cls = next(
        (n.class_config for n in graph.object_config_graph_nodes if n.class_config and n.class_config.name == "Foo"),
        None,
    )
    assert foo_cls is not None

    # Postgres: enum type is materialized; enum columns reference the overlay-resolved type name.
    pg = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    pg.set_language_overlay(sql_overlay)
    enum_ddl = pg._emit_enum(enum_from)
    assert "CREATE TYPE from_ AS ENUM" in enum_ddl
    ddl = pg._emit_table(foo_cls, class_lookup={foo_cls.id: foo_cls})
    assert "kind from_" in ddl

    # SQLite: enums are comments only; enum columns are stored as TEXT.
    sqlite = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    sqlite.set_language_overlay(sql_overlay)
    enum_ddl = sqlite._emit_enum(enum_from)
    assert "CREATE TYPE" not in enum_ddl
    assert "-- enum from_" in enum_ddl
    ddl = sqlite._emit_table(foo_cls, class_lookup={foo_cls.id: foo_cls})
    assert "id TEXT" in ddl
    assert "kind TEXT" in ddl


def test_sql_dialects_render_collection_primitive_columns(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "dialects_collection.aware",
        """
class Foo {
    id UUID
    tags String[]
}
""".strip(),
    )
    ns, domains = _ns(fqn_prefix="pkg", namespace="default", code_ids=[code.id])
    graph = build_object_config_graph_from_code(
        name="dialects_collection",
        description="dialects_collection",
        fqn_prefix="pkg",
        file_codes=[("dialects_collection.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    foo_cls = next(
        (n.class_config for n in graph.object_config_graph_nodes if n.class_config and n.class_config.name == "Foo"),
        None,
    )
    assert foo_cls is not None

    pg = SQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    ddl = pg._emit_table(foo_cls, class_lookup={foo_cls.id: foo_cls})
    assert "tags TEXT[] NOT NULL" in ddl
    assert "tags TEXT[] NOT NULL UNIQUE" not in ddl

    sqlite = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    ddl = sqlite._emit_table(foo_cls, class_lookup={foo_cls.id: foo_cls})
    assert "tags TEXT NOT NULL" in ddl
    assert "tags TEXT NOT NULL UNIQUE" not in ddl


def test_sql_renderer_handles_cyclic_mapping_descriptor_as_json_column(tmp_path: Path) -> None:
    descriptor = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    descriptor.child_links.append(_descriptor_link(parent=descriptor, child=descriptor, role=Role.value_))
    attr = AttributeConfig(
        owner_key="pkg.dom.default.Foo",
        name="payload",
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
        is_required=True,
    )
    cls = ClassConfig(class_fqn="pkg.dom.default.Foo", name="Foo", class_config_attribute_configs=[])
    cls.class_config_attribute_configs.append(
        ClassConfigAttributeConfig(
            class_config_id=cls.id,
            attribute_config=attr,
            attribute_config_id=attr.id,
            position=0,
        )
    )

    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(tmp_path))
    schema = renderer.describe_table_schema(cls)
    ddl = renderer._emit_table(cls, class_lookup={cls.id: cls})

    assert schema.columns == ("payload",)
    assert schema.json_columns == ("payload",)
    assert "payload TEXT NOT NULL" in ddl


def test_sql_runtime_to_language_handles_cyclic_descriptor_hash(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "cyclic_runtime_to_sql.aware",
        """
class Foo {
    id UUID
    payload String
}
""".strip(),
    )
    ns, domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id],
    )
    graph = build_object_config_graph_from_code(
        name="cyclic_runtime_to_sql",
        description="cyclic_runtime_to_sql",
        fqn_prefix="pkg",
        file_codes=[("cyclic_runtime_to_sql.aware", code)],
        namespace_by_code_id=ns,
    ).graph
    graph.object_projection_graphs = [
        ObjectProjectionGraph(
            name="FooProjection",
            language=CodeLanguage.aware,
            projection_hash="foo-projection",
            object_config_graph_id=graph.id,
        )
    ]

    foo_cls = next(
        (
            n.class_config
            for n in graph.object_config_graph_nodes
            if n.class_config and n.class_config.name == "Foo"
        ),
        None,
    )
    assert foo_cls is not None
    payload_attr = next(
        (
            edge.attribute_config
            for edge in foo_cls.class_config_attribute_configs
            if edge.attribute_config is not None
            and edge.attribute_config.name == "payload"
        ),
        None,
    )
    assert payload_attr is not None
    descriptor = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    descriptor.child_links.append(
        _descriptor_link(parent=descriptor, child=descriptor, role=Role.value_)
    )
    payload_attr.type_descriptor = descriptor
    payload_attr.type_descriptor_id = descriptor.id

    steps = []
    sql_graph, _ = language_service._lower_runtime_graph_to_language(
        graph,
        CodeLanguage.sql,
        renderer_profile="orm_runtime",
        external_runtime_graphs=(),
        runtime_to_language_cache=RuntimeToLanguageLoweringCache(),
        steps=steps,
    )

    assert sql_graph.language == CodeLanguage.sql
    assert sql_graph.hash
    assert [opg.projection_hash for opg in sql_graph.object_projection_graphs] == [
        "foo-projection"
    ]
    assert sql_graph.object_projection_graphs[0] is not graph.object_projection_graphs[0]
    step_names = {step.name for step in steps}
    assert "runtime_to_language.primary.transform" in step_names
    assert "runtime_to_language.primary.cache_store" in step_names
