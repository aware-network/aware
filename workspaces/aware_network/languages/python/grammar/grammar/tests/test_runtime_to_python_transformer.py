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
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_meta.graph.config.runtime_derivation.clone import (
    clone_runtime_graph_for_language_transformer_handoff,
)
from aware_meta.graph.projection.portal_index import build_portal_closure_context
from python_grammar.transformers.runtime_to_python_transformer import (
    RuntimeToPythonTransformer,
)


def _build_code(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    _ = path.write_text(content)
    return build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


PORTAL_CODE = """
class Target {
    title String
}

class Package {
    target Target
}

ann test.Package::target load eager

projection Packages {
    root test.Package
    test.Package::target Targets
}

projection Targets {
    root test.Target
}
""".strip()


def _build_runtime_portal_graph(tmp_path: Path):
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(tmp_path, "portal.aware", PORTAL_CODE)
    namespace_by_code_id, domains = _ns(
        fqn_prefix="pkg",
        namespace="test",
        code_ids=[code.id],
    )
    source = build_object_config_graph_from_code(
        name="portal",
        description="portal",
        fqn_prefix="pkg",
        file_codes=[("portal.aware", code)],
        namespace_by_code_id=namespace_by_code_id,
    ).graph
    runtime = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id
    ).transform(source)
    runtime.object_projection_graphs = build_object_projection_graphs(runtime)
    return runtime


def _package_portal_attrs(runtime):
    package_class = next(
        node.class_config
        for node in runtime.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "Package"
    )
    target_attr = next(
        link.attribute_config
        for link in package_class.class_config_attribute_configs
        if link.attribute_config.name == "target"
    )
    target_fk_attr = next(
        link.attribute_config
        for link in package_class.class_config_attribute_configs
        if link.attribute_config.name == "target_id"
    )
    return target_attr, target_fk_attr


def test_runtime_to_python_transformer_lowers_cross_projection_portal_ref_to_nullable(
    tmp_path: Path,
) -> None:
    runtime = _build_runtime_portal_graph(tmp_path)
    target_attr, target_fk_attr = _package_portal_attrs(runtime)

    assert target_attr.is_required is True
    assert target_attr.exclude_serialization is False
    assert target_fk_attr.is_required is False

    transformed = RuntimeToPythonTransformer().transform(runtime)

    assert transformed is runtime
    assert target_attr.is_required is False
    assert target_attr.exclude_serialization is False
    assert target_fk_attr.is_required is True


def test_runtime_to_python_transformer_shallow_handoff_preserves_source_portal_attrs(
    tmp_path: Path,
) -> None:
    runtime = _build_runtime_portal_graph(tmp_path)
    source_target_attr, source_target_fk_attr = _package_portal_attrs(runtime)
    handoff = clone_runtime_graph_for_language_transformer_handoff(runtime)
    handoff_target_attr, handoff_target_fk_attr = _package_portal_attrs(handoff)

    transformed = RuntimeToPythonTransformer().transform(handoff)

    assert transformed is handoff
    assert source_target_attr.is_required is True
    assert source_target_fk_attr.is_required is False
    assert handoff_target_attr.is_required is False
    assert handoff_target_fk_attr.is_required is True
    assert handoff_target_attr is not source_target_attr
    assert handoff_target_fk_attr is not source_target_fk_attr


def test_runtime_to_python_transformer_accepts_prepared_portal_closure_context(
    tmp_path: Path,
) -> None:
    runtime = _build_runtime_portal_graph(tmp_path)
    target_attr, target_fk_attr = _package_portal_attrs(runtime)
    closure_context = build_portal_closure_context(runtime)

    transformed = RuntimeToPythonTransformer(
        portal_closure_context=closure_context,
    ).transform(runtime)

    assert closure_context.graph_count == 1
    assert transformed is runtime
    assert target_attr.is_required is False
    assert target_fk_attr.is_required is True
