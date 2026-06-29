from __future__ import annotations

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
from aware_meta.graph.package.materialization import (
    MetaObjectConfigGraphPackageMaterializationReceipt,
)
from aware_meta.graph.projection.stable_ids import stable_object_projection_graph_id


def _build_code(tmp_path: Path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(
    *,
    fqn_prefix: str,
    namespace: str,
    code_ids: list[UUID],
):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace)
        for cid in code_ids
    }, []


def test_meta_package_materialization_receipt_records_ocgi_opgi_and_observables(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(
        tmp_path,
        "package_materialization.aware",
        (
            "class Identity {\n"
            "}\n"
            "\n"
            "projection Identity is_branchable {\n"
            "    root Identity\n"
            "    view onboarding {\n"
            "        view welcome construct default {\n"
            '            """Welcome view."""\n'
            "        }\n"
            "    }\n"
            "}\n"
        ),
    )
    namespace_by_code_id, domains = _ns(
        fqn_prefix="meta_pkg",
        namespace="main",
        code_ids=[code.id],
    )

    result = build_object_config_graph_from_code(
        name="meta_pkg_graph",
        description="meta_pkg_graph",
        fqn_prefix="meta_pkg",
        file_codes=[("package_materialization.aware", code)],
        namespace_by_code_id=namespace_by_code_id,
    )

    receipt = result.package_materialization_receipt
    assert isinstance(receipt, MetaObjectConfigGraphPackageMaterializationReceipt)
    assert receipt.object_config_graph_id == result.graph.id
    assert receipt.object_config_graph_hash == result.graph.hash
    assert receipt.layout_hash == result.graph.layout_hash
    assert receipt.object_config_graph_identity is not None
    assert (
        receipt.object_config_graph_identity.object_config_graph_identity_id
        == result.graph.object_config_graph_identity_id
    )

    projection_records = {
        record.projection_name: record for record in receipt.projection_identities
    }
    assert set(projection_records) == {"Identity"}
    identity_projection_id = stable_object_projection_graph_id(
        object_config_graph_id=result.graph.id,
        name="Identity",
    )
    identity_record = projection_records["Identity"]
    assert identity_record.object_projection_graph_id == identity_projection_id
    assert identity_record.is_branchable is True

    observable_records = {record.key: record for record in receipt.observables}
    assert set(observable_records) == {"Identity:onboarding.welcome"}
    welcome = observable_records["Identity:onboarding.welcome"]
    assert welcome.observable_key == "onboarding.welcome"
    assert welcome.kind == "construct"
    assert welcome.is_default is True

    opgi = result.graph.object_config_graph_identity.object_projection_graph_identities[
        0
    ]
    assert opgi.id == identity_record.object_projection_graph_identity_id
    assert (
        opgi.object_projection_graph_observables[0].id
        == welcome.object_projection_graph_observable_id
    )


def test_meta_package_materialization_ownership_boundaries_are_explicit() -> None:
    config_builder_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/config/builder.py"
    ).read_text(encoding="utf-8")
    package_materialization_source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/graph/package/materialization.py"
    ).read_text(encoding="utf-8")

    assert "from aware_meta.graph.config.materialization" not in config_builder_source
    assert "from aware_meta.graph.projection.compiler" not in config_builder_source
    assert (
        "from aware_meta.graph.projection.materialization" not in config_builder_source
    )
    assert "ProjectionDeclaration" not in config_builder_source
    assert "compile_object_config_graph_events" not in config_builder_source
    assert "compile_object_config_graph_projections" in package_materialization_source
    assert "materialize_object_config_graph_identity" in package_materialization_source
    assert "materialize_projection_identities" in package_materialization_source
