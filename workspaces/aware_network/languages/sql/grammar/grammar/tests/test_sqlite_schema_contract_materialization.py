from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization.language_service import (
    LanguagePluginMaterializationRequest,
    materialize_object_config_graph_via_language_plugin,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from sql_grammar.materialization_outputs import (
    SQLITE_ORM_SCHEMA_CONTRACT_OUTPUT_KEY,
    SQLITE_ORM_SCHEMA_CONTRACT_PATH,
    SQLITE_ORM_SCHEMA_CONTRACT_PAYLOAD_SCHEMA,
)
from sql_grammar.meta_language_plugin import SQL_META_PLUGIN


def _build_code(tmp_path: Path, name: str, content: str) -> Code:
    path = tmp_path / name
    _ = path.write_text(content, encoding="utf-8")
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _build_graph(tmp_path: Path, content: str) -> ObjectConfigGraph:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(tmp_path, "state.aware", content.strip())
    namespace_by_code_id: dict[UUID, NamespacePath] = {
        code.id: NamespacePath(package="pkg", namespace="default")
    }
    return build_object_config_graph_from_code(
        name="state",
        description="state",
        fqn_prefix="pkg",
        file_codes=[("state.aware", code)],
        namespace_by_code_id=namespace_by_code_id,
    ).graph


def test_sqlite_orm_schema_contract_materializes_for_orm_models_profile(
    tmp_path: Path,
) -> None:
    graph = _build_graph(
        tmp_path,
        """
class LocalStateRecord {
    record_identity String key
    payload JsonObject = {}
    count Int = 0
}

ann default.LocalStateRecord storage unique by_identity record_identity
""",
    )
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)
    output_root = tmp_path / "sqlite"

    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=graph,
            target_language_plugin_id=CodeLanguage.sql,
            output_root=output_root,
            package_name="local-state-sqlite",
            import_root="local_state_sqlite",
            materialization_source="ontology",
            renderer_kind="sqlite",
            renderer_profile="orm_models",
            emit_files=True,
        )
    )

    contract_path = output_root / SQLITE_ORM_SCHEMA_CONTRACT_PATH
    assert contract_path.is_file()
    assert Path(SQLITE_ORM_SCHEMA_CONTRACT_PATH) in {generated_file.path for generated_file in result.generated_files}
    declared_by_key = {item.output_key: item for item in result.plugin_declared_outputs}
    assert declared_by_key[SQLITE_ORM_SCHEMA_CONTRACT_OUTPUT_KEY].status == "materialized"

    payload = cast(dict[str, Any], json.loads(contract_path.read_text(encoding="utf-8")))
    assert payload["schema"] == SQLITE_ORM_SCHEMA_CONTRACT_PAYLOAD_SCHEMA
    assert payload["schema_contract"] == "pkg.sqlite.orm_schema"
    assert payload["schema_version"] == 1
    assert payload["renderer_profile"] == "orm_models"
    assert payload["renderer_kind"] == "sqlite"
    assert payload["materialization_source"] == "ontology"

    tables = cast(list[dict[str, Any]], payload["tables"])
    table = tables[0]
    assert table["table"] == "local_state_record"
    assert table["columns"] == ["id", "record_identity", "payload", "count"]
    assert table["json_columns"] == ["payload"]
    assert table["storage_indexes"] == [
        {
            "columns": ["record_identity"],
            "name": table["storage_indexes"][0]["name"],
            "unique": True,
        }
    ]
