"""SQL-owned producers for declared materialization outputs."""

from __future__ import annotations

import json
from pathlib import Path

from aware_code.language.plugin import CodeLanguageMaterializationOutputDescriptor
from aware_meta.language_plugin import (
    MetaLanguageDeclaredOutputProducedFile,
    MetaLanguageDeclaredOutputProducerRequest,
    MetaLanguageDeclaredOutputProducerResult,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

from sql_grammar.layout_strategy import SQLLayoutStrategyNamespace
from sql_grammar.renderer_policy import SQLRenderPolicy
from sql_grammar.renderers.renderer import SqliteSQLRenderer


SQLITE_ORM_SCHEMA_CONTRACT_OUTPUT_KEY = "sql.sqlite_orm_schema_contract"
SQLITE_ORM_SCHEMA_CONTRACT_PAYLOAD_SCHEMA = "aware.orm.local_state.sqlite.schema_contract.v1"
SQLITE_ORM_SCHEMA_CONTRACT_PATH = "_aware/sqlite_orm_schema_contract.json"

SQL_MATERIALIZATION_ARTIFACT_OUTPUTS = (
    CodeLanguageMaterializationOutputDescriptor(
        output_key=SQLITE_ORM_SCHEMA_CONTRACT_OUTPUT_KEY,
        description="SQLite ORM local-state schema contract descriptor.",
        output_kind="manifest",
        artifact_role="local_state_schema_contract",
        path_templates=(SQLITE_ORM_SCHEMA_CONTRACT_PATH,),
        producer_step="schema_contract_write",
        required_for=("workspace_revision", "runtime_index", "environment_config"),
        renderer_profiles=("orm_models",),
        renderer_kinds=("sqlite",),
        materialization_sources=("ontology",),
        required=True,
    ),
)


def produce_sql_declared_outputs(
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> MetaLanguageDeclaredOutputProducerResult:
    produced_files: list[MetaLanguageDeclaredOutputProducedFile] = []
    produced_output_keys: set[str] = set()
    for descriptor in request.descriptors:
        if not _descriptor_applies_to_request(descriptor=descriptor, request=request):
            continue
        if descriptor.output_key != SQLITE_ORM_SCHEMA_CONTRACT_OUTPUT_KEY:
            continue
        content = (
            json.dumps(
                _sqlite_orm_schema_contract_payload(request=request),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        for path in _descriptor_paths(descriptor=descriptor, request=request):
            produced_files.append(
                MetaLanguageDeclaredOutputProducedFile(
                    output_key=descriptor.output_key,
                    path=path,
                    content_text=content,
                    output_kind=descriptor.output_kind,
                    artifact_role=descriptor.artifact_role,
                    producer_step=descriptor.producer_step,
                )
            )
        produced_output_keys.add(descriptor.output_key)
    return MetaLanguageDeclaredOutputProducerResult(
        produced_files=tuple(produced_files),
        metrics={
            "sql_declared_output_count": len(produced_files),
            "sql_declared_output_key_count": len(produced_output_keys),
            "sql_declared_output_keys": tuple(sorted(produced_output_keys)),
        },
    )


def _sqlite_orm_schema_contract_payload(
    *,
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> dict[str, object]:
    renderer = SqliteSQLRenderer(layout_strategy=SQLLayoutStrategyNamespace(request.output_root))
    renderer.set_policy(SQLRenderPolicy.orm_models_default())
    renderer.bind_object_config_graph(request.language_graph)
    tables = tuple(
        renderer.describe_table_schema(class_config) for class_config in _persistent_classes(request.language_graph)
    )
    return {
        "schema": SQLITE_ORM_SCHEMA_CONTRACT_PAYLOAD_SCHEMA,
        "schema_contract": _schema_contract_id(request),
        "schema_version": _schema_version(request),
        "source_graph_ref": request.source_graph.hash or str(request.source_graph.id),
        "runtime_graph_ref": request.runtime_graph.hash or str(request.runtime_graph.id),
        "language_graph_ref": request.language_graph.hash or str(request.language_graph.id),
        "package_name": request.package_name,
        "import_root": request.import_root,
        "renderer_profile": request.renderer_profile,
        "renderer_kind": request.renderer_kind,
        "materialization_source": request.materialization_source,
        "schema_paths": tuple(path.as_posix() for path in sorted(request.generated_file_paths)),
        "tables": tuple(
            {
                "table": table.table_name,
                "columns": table.columns,
                "json_columns": table.json_columns,
                "storage_indexes": tuple(
                    {
                        "name": index.name,
                        "unique": index.unique,
                        "columns": index.columns,
                    }
                    for index in table.storage_indexes
                ),
            }
            for table in tables
        ),
    }


def _persistent_classes(graph: ObjectConfigGraph) -> tuple[ClassConfig, ...]:
    classes: list[ClassConfig] = []
    for node in graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        if node.class_config.value_mode != ClassValueMode.graph_ref:
            continue
        classes.append(node.class_config)
    return tuple(sorted(classes, key=lambda cls: cls.name))


def _schema_contract_id(request: MetaLanguageDeclaredOutputProducerRequest) -> str:
    raw = request.profile_inputs.get("sqlite_schema_contract")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    base = (
        request.source_graph.fqn_prefix
        or request.language_graph.fqn_prefix
        or request.import_root
        or request.package_name
        or "local_state"
    )
    return f"{base}.sqlite.orm_schema"


def _schema_version(request: MetaLanguageDeclaredOutputProducerRequest) -> int:
    raw = request.profile_inputs.get("sqlite_schema_version")
    if isinstance(raw, bool):
        return 1
    if isinstance(raw, int) and raw > 0:
        return raw
    return 1


def _descriptor_applies_to_request(
    *,
    descriptor: CodeLanguageMaterializationOutputDescriptor,
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> bool:
    if descriptor.renderer_profiles and request.renderer_profile not in descriptor.renderer_profiles:
        return False
    if descriptor.renderer_kinds and request.renderer_kind not in descriptor.renderer_kinds:
        return False
    if descriptor.materialization_sources and request.materialization_source not in descriptor.materialization_sources:
        return False
    return True


def _descriptor_paths(
    *,
    descriptor: CodeLanguageMaterializationOutputDescriptor,
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> tuple[Path, ...]:
    import_root = request.import_root or request.package_name or ""
    return tuple(
        Path(
            template.format(
                import_root=import_root,
                package_name=request.package_name or "",
                language="sql",
            )
        )
        for template in descriptor.path_templates
    )


__all__ = [
    "SQLITE_ORM_SCHEMA_CONTRACT_OUTPUT_KEY",
    "SQLITE_ORM_SCHEMA_CONTRACT_PATH",
    "SQLITE_ORM_SCHEMA_CONTRACT_PAYLOAD_SCHEMA",
    "SQL_MATERIALIZATION_ARTIFACT_OUTPUTS",
    "produce_sql_declared_outputs",
]
