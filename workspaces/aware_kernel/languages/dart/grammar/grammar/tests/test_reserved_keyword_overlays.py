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

# Dart meta plugin (target language)
from dart_grammar.meta_language_plugin import DART_META_PLUGIN


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


def test_reserved_keyword_overlays_generate_dart_enum_option_overlays(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(DART_META_PLUGIN)

    code = _build_code(
        tmp_path,
        "dart_reserved_enum.aware",
        """
enum DartKeywordCase {
    class
    enum
    ok
}
""".strip(),
    )
    ns = _namespace_by_code_id(
        fqn_prefix="pkg", domain="dom", schema="default", code_ids=[code.id]
    )
    graph = build_object_config_graph_from_code(
        name="reserved_overlays",
        description="reserved_overlays",
        fqn_prefix="pkg",
        file_codes=[("dart_reserved_enum.aware", code)],
        namespace_by_code_id=ns,
    ).graph

    dart_overlay = next((ov for ov in graph.object_config_graph_overlays if ov.language == CodeLanguage.dart), None)
    assert dart_overlay is not None, "Expected a Dart overlay to be generated for reserved enum options"

    enum_cfg = next(
        (
            n.enum_config
            for n in graph.object_config_graph_nodes
            if n.enum_config is not None and n.enum_config.name == "DartKeywordCase"
        ),
        None,
    )
    assert enum_cfg is not None

    opt_by_value = {o.value: o for o in enum_cfg.enum_options}
    overlays_by_opt_id = {o.enum_option_id: o for o in dart_overlay.enum_option_overlays}

    enum_opt = opt_by_value["enum"]
    enum_ov = overlays_by_opt_id.get(enum_opt.id)
    assert enum_ov is not None
    assert enum_ov.rendered_name == "enum_"
    assert enum_ov.wire_name == "enum"

    class_opt = opt_by_value["class"]
    class_ov = overlays_by_opt_id.get(class_opt.id)
    assert class_ov is not None
    assert class_ov.rendered_name == "class_"
    assert class_ov.wire_name == "class"
