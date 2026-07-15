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
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry

# Python meta plugin (target language)
from python_grammar.meta_language_plugin import PYTHON_META_PLUGIN


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


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def test_reserved_keyword_overlays_generate_python_attribute_overlays(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(PYTHON_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "python_reserved_attr.aware",
        """
class User {
    from String
}
""".strip(),
    )
    ns, domains = _ns(fqn_prefix="pkg", namespace="default", code_ids=[code.id])
    graph = build_object_config_graph_from_code(
        name="reserved_overlays",
        description="reserved_overlays",
        fqn_prefix="pkg",
        file_codes=[("python_reserved_attr.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    py_overlay = next((ov for ov in graph.object_config_graph_overlays if ov.language == CodeLanguage.python), None)
    assert py_overlay is not None, "Expected a Python overlay to be generated for reserved attribute names"

    user_cls = next(
        (n.class_config for n in graph.object_config_graph_nodes if n.class_config and n.class_config.name == "User"),
        None,
    )
    assert user_cls is not None

    from_attr = next(
        (
            e.attribute_config
            for e in user_cls.class_config_attribute_configs
            if e.attribute_config and e.attribute_config.name == "from"
        ),
        None,
    )
    assert from_attr is not None

    overlays_by_attr_id = {o.attribute_config_id: o for o in py_overlay.attribute_config_overlays}
    from_ov = overlays_by_attr_id.get(from_attr.id)
    assert from_ov is not None
    assert from_ov.rendered_name == "from_"
    assert from_ov.wire_name == "from"


def test_reserved_keyword_overlays_generate_python_enum_option_overlays(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(PYTHON_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "python_reserved_enum_option.aware",
        """
enum ReservedNames {
    value
    name
    ok
}
""".strip(),
    )
    ns, domains = _ns(fqn_prefix="pkg", namespace="default", code_ids=[code.id])
    graph = build_object_config_graph_from_code(
        name="reserved_enum_option_overlays",
        description="reserved_enum_option_overlays",
        fqn_prefix="pkg",
        file_codes=[("python_reserved_enum_option.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    py_overlay = next((ov for ov in graph.object_config_graph_overlays if ov.language == CodeLanguage.python), None)
    assert py_overlay is not None, "Expected a Python overlay to be generated for reserved enum option names"

    enum_cfg = next(
        (
            n.enum_config
            for n in graph.object_config_graph_nodes
            if n.enum_config and n.enum_config.name == "ReservedNames"
        ),
        None,
    )
    assert enum_cfg is not None

    opts_by_value = {opt.value: opt for opt in enum_cfg.enum_options}
    value_opt = opts_by_value.get("value")
    name_opt = opts_by_value.get("name")
    assert value_opt is not None
    assert name_opt is not None

    overlays_by_opt_id = {o.enum_option_id: o for o in py_overlay.enum_option_overlays}
    value_ov = overlays_by_opt_id.get(value_opt.id)
    name_ov = overlays_by_opt_id.get(name_opt.id)
    assert value_ov is not None
    assert name_ov is not None
    assert value_ov.rendered_name == "value_"
    assert value_ov.wire_name == "value"
    assert name_ov.rendered_name == "name_"
    assert name_ov.wire_name == "name"
