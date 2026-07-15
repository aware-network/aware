from pathlib import Path
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.class_.code_section_class_base import CodeSectionClassBase

# Meta Ontology

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Aware Kernel Meta
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.fqn_resolver import NamespacePath


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


def test_cross_ocg_inheritance_emits_augment_not_keyerror(tmp_path: Path) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    dep_code = _build_code(tmp_path, "dep.aware", "class Base { id String }\n")
    dep_ns, dep_domains = _ns(
        fqn_prefix="dep_pkg",
        namespace="dep_schema",
        code_ids=[dep_code.id],
    )
    dep_res = build_object_config_graph_from_code(
        name="dep",
        description="dep",
        fqn_prefix="dep_pkg",
        file_codes=[("dep", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    local_code = _build_code(tmp_path, "local.aware", "class Child { name String }\n")
    # Inject a base edge referencing the external class by full FQN
    child_cs = None
    for sec in local_code.code_sections:
        if (
            sec.code_section_class is not None
            and sec.code_section_class.name == "Child"
        ):
            child_cs = sec.code_section_class
            break
    assert child_cs is not None

    child_cs.code_section_class_bases.append(
        CodeSectionClassBase(
            code_section_class_id=child_cs.id,
            base_ref="dep_pkg.dep_schema.Base",
            is_augment=False,
            segment_id=None,
            segment=None,
        )
    )

    local_ns, local_domains = _ns(
        fqn_prefix="main_pkg",
        namespace="main_schema",
        code_ids=[local_code.id],
    )
    local_res = build_object_config_graph_from_code(
        name="local",
        description="local",
        fqn_prefix="main_pkg",
        file_codes=[("local", local_code)],
        namespace_by_code_id=local_ns,
        external_graphs=[dep_res.graph],
    )

    # Should emit cross-class augment rather than crashing.
    assert dep_res.graph.id in local_res.cross_class_configs_by_target_ocg
    aug_map = local_res.cross_class_configs_by_target_ocg[dep_res.graph.id]
    assert aug_map, "Expected at least one augmented object in dependency graph"
