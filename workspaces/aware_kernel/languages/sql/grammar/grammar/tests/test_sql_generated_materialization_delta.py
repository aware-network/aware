from __future__ import annotations

from pathlib import Path
from typing import cast

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_delta import CodePackageDeltaKind
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedRendererDeltaOperationKind,
)
from aware_meta.materialization.deltas.feature_contracts import (
    MetaProviderDeltaGeneratedMaterializationContext,
)
from aware_meta.materialization.deltas.feature_registry import (
    generated_materialization_feature_results_from_typed_operation,
)
from aware_meta.materialization.deltas.generated_materialization import (
    provider_delta_generated_materialization_stage,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationTargetHint,
)
from aware_meta.materialization.deltas.renderer_completeness import (
    compare_generated_materialization_package_delta_final_state,
    compare_generated_materialization_path_content_map,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.materialization.language_service import (
    LanguagePluginMaterializationRequest,
    materialize_object_config_graph_via_language_plugin,
)
from sql_grammar.meta_language_plugin import SQL_META_PLUGIN
from sql_grammar.renderer_delta_orm_runtime import (
    SQL_ORM_GENERATED_DELTA_RENDERER_NAME,
    SQL_ORM_MATERIALIZATION_SOURCE,
    SQL_ORM_RENDERER_PROFILE,
    SQL_ORM_SOURCE_ARTIFACT_PAYLOAD_KEY,
    SQL_ORM_SOURCE_RENDERER_KIND,
    SQL_ORM_SOURCE_RENDERER_PROFILE,
    SqlOrmRuntimeGeneratedDeltaRenderer,
    build_sql_orm_source_artifact_payload,
)
from test_sql_orm_models_profile import _build_code, _build_graph, _ns


def test_sql_plugin_exposes_orm_runtime_generated_delta_renderer() -> None:
    renderers = SQL_META_PLUGIN.get_generated_delta_renderers(
        profile=SQL_ORM_RENDERER_PROFILE,
    )

    assert tuple(renderers) == (SQL_ORM_GENERATED_DELTA_RENDERER_NAME,)
    renderer = renderers[SQL_ORM_GENERATED_DELTA_RENDERER_NAME]
    assert renderer.renderer_profile == SQL_ORM_RENDERER_PROFILE
    assert renderer.materialization_source == SQL_ORM_MATERIALIZATION_SOURCE


def test_sql_orm_class_create_delta_emits_package_delta_source_artifact(
    tmp_path: Path,
) -> None:
    payload, expected_content, relative_path = _sql_source_artifact_payload(tmp_path)
    operation = _typed_operation(
        _class_create_operation(
            relative_path=relative_path,
            source_artifact_payload=payload,
        )
    )

    evidence = (
        SqlOrmRuntimeGeneratedDeltaRenderer().render_generated_materialization_delta(
            MetaLanguageGeneratedMaterializationDeltaRenderRequest(
                operation=operation,
                context=MetaLanguageGeneratedMaterializationDeltaContext(
                    package_name="content-ontology-sql",
                    package_root="/tmp/content-ontology-sql",
                    sources_root="sql",
                    target_language="sql",
                    renderer_profile=SQL_ORM_RENDERER_PROFILE,
                    materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                    product_intent="orm_runtime",
                    target_hints=(
                        MetaLanguageGeneratedMaterializationTargetHint(
                            descriptor_key="orm_runtime",
                            capability_key=SQL_ORM_GENERATED_DELTA_RENDERER_NAME,
                            target_language="sql",
                            renderer_profile=SQL_ORM_RENDERER_PROFILE,
                            materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                            owner_key="content.default.RemoteControl",
                            relative_path=relative_path,
                        ),
                    ),
                ),
            )
        )
    )

    assert evidence.handled is True
    assert evidence.reason == "sql_orm_runtime_source_artifact_generated_delta_rendered"
    assert evidence.delta_request is not None
    assert evidence.result is not None
    assert evidence.delta_request.product_intent == "orm_runtime"
    assert evidence.delta_request.targets[0].target_language == "sql"
    assert evidence.delta_request.targets[0].renderer_profile == "orm_runtime"
    assert (
        evidence.delta_request.targets[0].materialization_source
        == "ontology_orm_models"
    )
    assert evidence.delta_request.targets[0].relative_path == relative_path
    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.package_delta_ready
    )

    [entry] = evidence.result.entries
    assert entry.mode is CodeGeneratedMaterializationDeltaMode.package_delta_ready
    assert entry.relative_path == relative_path
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.relative_path == relative_path
    assert path.kind is CodePackageDeltaKind.create
    assert path.language is not None
    assert path.language.value == "sql"
    assert path.path_role is CodePackagePathRole.generated_code
    assert path.content_text == expected_content
    assert "CREATE TABLE remote_control" in path.content_text

    [renderer_operation] = entry.renderer_operations
    assert (
        renderer_operation.kind
        is CodeGeneratedRendererDeltaOperationKind.replace_section
    )
    assert renderer_operation.renderer_key == "sql.orm.class.source_artifact"
    assert renderer_operation.renderer_profile == "orm_runtime"
    assert renderer_operation.content_text == path.content_text
    assert renderer_operation.diagnostics == [
        "sql_orm_source_artifact_render_equivalent",
        "sql_orm_source_artifact_delta_first_not_migration",
    ]


def test_sql_orm_class_create_delta_matches_full_source_container_render(
    tmp_path: Path,
) -> None:
    payload, expected_content, relative_path = _sql_source_artifact_payload(
        tmp_path,
        content="""
enum RemoteMode {
    tv
    stereo
}

class RemoteControl {
    remote_id String key
    label String
    mode RemoteMode
}

class RemoteButton {
    button_id String key
    label String
}
""",
    )
    operation = _typed_operation(
        _class_create_operation(
            relative_path=relative_path,
            source_artifact_payload=payload,
        )
    )

    evidence = (
        SqlOrmRuntimeGeneratedDeltaRenderer().render_generated_materialization_delta(
            MetaLanguageGeneratedMaterializationDeltaRenderRequest(
                operation=operation,
                context=MetaLanguageGeneratedMaterializationDeltaContext(
                    package_name="content-ontology-sql",
                    package_root="/tmp/content-ontology-sql",
                    sources_root="sql",
                    target_language="sql",
                    renderer_profile=SQL_ORM_RENDERER_PROFILE,
                    materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                    product_intent="orm_runtime",
                    target_hints=(
                        MetaLanguageGeneratedMaterializationTargetHint(
                            descriptor_key="orm_runtime",
                            capability_key=SQL_ORM_GENERATED_DELTA_RENDERER_NAME,
                            target_language="sql",
                            renderer_profile=SQL_ORM_RENDERER_PROFILE,
                            materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                            owner_key="content.default.RemoteControl",
                            relative_path=relative_path,
                        ),
                    ),
                ),
            )
        )
    )

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.relative_path == relative_path
    assert path.content_text == expected_content
    assert "-- enum remote_mode:" in path.content_text
    assert "CREATE TABLE remote_control" in path.content_text
    assert "CREATE TABLE remote_button" in path.content_text


def test_sql_orm_class_create_deltas_match_full_package_render(
    tmp_path: Path,
) -> None:
    package = _sql_package_source_artifacts(
        tmp_path,
        files={
            "controls.aware": """
enum RemoteMode {
    tv
    stereo
}

class RemoteControl {
    remote_id String key
    label String
    mode RemoteMode
}
""",
            "devices.aware": """
class LocalDevice {
    device_id String key
    hostname String
}
""",
        },
        owner_by_relative_path={
            "controls.sql": ("content.default.RemoteControl", "RemoteControl"),
            "devices.sql": ("content.default.LocalDevice", "LocalDevice"),
        },
    )
    expected_by_path = package["expected_by_path"]
    payload_by_path = package["payload_by_path"]
    owner_by_path = package["owner_by_path"]

    delta_results = []
    for relative_path in sorted(expected_by_path):
        owner_key, class_name = owner_by_path[relative_path]
        operation = _typed_operation(
            _class_create_operation(
                class_fqn=owner_key,
                class_name=class_name,
                relative_path=relative_path,
                source_artifact_payload=payload_by_path[relative_path],
            )
        )
        evidence = SqlOrmRuntimeGeneratedDeltaRenderer().render_generated_materialization_delta(
            MetaLanguageGeneratedMaterializationDeltaRenderRequest(
                operation=operation,
                context=MetaLanguageGeneratedMaterializationDeltaContext(
                    package_name="content-ontology-sql",
                    package_root="/tmp/content-ontology-sql",
                    sources_root="sql",
                    target_language="sql",
                    renderer_profile=SQL_ORM_RENDERER_PROFILE,
                    materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                    product_intent="orm_runtime",
                    target_hints=(
                        MetaLanguageGeneratedMaterializationTargetHint(
                            descriptor_key="orm_runtime",
                            capability_key=SQL_ORM_GENERATED_DELTA_RENDERER_NAME,
                            target_language="sql",
                            renderer_profile=SQL_ORM_RENDERER_PROFILE,
                            materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                            owner_key=owner_key,
                            relative_path=relative_path,
                        ),
                    ),
                ),
            )
        )

        assert evidence.handled is True
        assert evidence.result is not None
        delta_results.append(evidence.result)

    comparison = compare_generated_materialization_path_content_map(
        expected_by_path=expected_by_path,
        delta_results=delta_results,
    )

    assert comparison.equivalent, comparison.summary()
    delta_by_path = comparison.actual_by_path
    assert sorted(delta_by_path) == ["controls.sql", "devices.sql"]
    assert "-- enum remote_mode:" in delta_by_path["controls.sql"]
    assert "CREATE TABLE remote_control" in delta_by_path["controls.sql"]
    assert "CREATE TABLE local_device" in delta_by_path["devices.sql"]


def test_sql_orm_class_update_delta_matches_full_package_final_state(
    tmp_path: Path,
) -> None:
    baseline_package = _sql_package_source_artifacts(
        tmp_path / "baseline",
        files={
            "controls.aware": """
class RemoteControl {
    remote_id String key
    label String
}
""",
        },
        owner_by_relative_path={
            "controls.sql": ("pkg.default.RemoteControl", "RemoteControl"),
        },
    )
    target_package = _sql_package_source_artifacts(
        tmp_path / "target",
        files={
            "controls.aware": """
class RemoteControl {
    remote_id String key
    label Int
    nickname String
}
""",
        },
        owner_by_relative_path={
            "controls.sql": ("pkg.default.RemoteControl", "RemoteControl"),
        },
    )
    operation = _typed_operation(
        _class_update_operation(
            class_fqn="pkg.default.RemoteControl",
            class_name="RemoteControl",
            relative_path="controls.sql",
            source_artifact_payload=target_package["payload_by_path"]["controls.sql"],
        )
    )
    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.kind is CodePackageDeltaKind.update
    assert path.relative_path == "controls.sql"
    assert path.content_text == target_package["expected_by_path"]["controls.sql"]

    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], target_package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], baseline_package["expected_by_path"]),
        package_deltas=(entry.package_delta,),
    )

    assert comparison.equivalent, comparison.summary()


def test_sql_orm_class_delete_delta_matches_full_package_final_state(
    tmp_path: Path,
) -> None:
    baseline_package = _sql_package_source_artifacts(
        tmp_path / "baseline",
        files={
            "controls.aware": """
class RemoteControl {
    remote_id String key
    label String
}
""",
        },
        owner_by_relative_path={
            "controls.sql": ("pkg.default.RemoteControl", "RemoteControl"),
        },
    )
    operation = _typed_operation(
        _class_delete_operation(
            class_fqn="pkg.default.RemoteControl",
            class_name="RemoteControl",
            relative_path="controls.sql",
        )
    )
    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.kind is CodePackageDeltaKind.delete
    assert path.relative_path == "controls.sql"
    assert path.content_text is None
    assert entry.renderer_operations[0].diagnostics == [
        "sql_orm_source_artifact_render_equivalent",
        "sql_orm_source_artifact_delta_first_not_migration",
    ]

    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path={},
        baseline_by_path=cast(dict[str, str], baseline_package["expected_by_path"]),
        package_deltas=(entry.package_delta,),
    )

    assert comparison.equivalent, comparison.summary()


def test_sql_orm_enum_create_uses_typed_source_container_payload(
    tmp_path: Path,
) -> None:
    payload, expected_content, relative_path = _sql_source_artifact_payload(
        tmp_path,
        content="""
enum RemoteMode {
    tv
    stereo
}

class RemoteControl {
    remote_id String key
    mode RemoteMode
}
""",
    )
    operation = _typed_operation(
        _enum_create_operation(
            relative_path=relative_path,
            source_artifact_payload=payload,
        )
    )

    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.kind is CodePackageDeltaKind.create
    assert path.content_text == expected_content
    assert "-- enum remote_mode:" in expected_content


def test_sql_orm_relationship_create_uses_typed_source_container_payload(
    tmp_path: Path,
) -> None:
    payload, expected_content, relative_path = _sql_source_artifact_payload(tmp_path)
    operation = _typed_operation(
        _relationship_create_operation(
            relative_path=relative_path,
            source_artifact_payload=payload,
        )
    )

    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.kind is CodePackageDeltaKind.create
    assert path.content_text == expected_content


def test_sql_orm_attribute_create_optional_delta_emits_migration_artifact() -> None:
    operation = _typed_operation(
        _attribute_create_operation(
            owner_key="pkg.default.RemoteControl",
            attribute_name="nickname",
            primitive_base_type="string",
            is_required=False,
        )
    )
    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert (
        evidence.reason
        == "sql_orm_runtime_attribute_migration_generated_delta_rendered"
    )
    assert evidence.result is not None
    assert (
        evidence.result.mode
        is CodeGeneratedMaterializationDeltaMode.package_delta_ready
    )
    [entry] = evidence.result.entries
    assert entry.artifact_role == "sql_orm_migration"
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.kind is CodePackageDeltaKind.create
    assert path.path_role is CodePackagePathRole.generated_code
    assert path.relative_path.startswith("migrations/")
    assert path.relative_path.endswith(".sql")
    assert path.metadata is not None
    assert path.metadata["artifact_role"] == "sql_orm_migration"
    assert path.content_text == (
        'ALTER TABLE "remote_control" ADD COLUMN "nickname" TEXT;\n'
    )
    [renderer_operation] = entry.renderer_operations
    assert renderer_operation.renderer_key == "sql.orm.attribute.migration"
    assert renderer_operation.diagnostics == [
        "sql_orm_migration_artifact_ready",
        "sql_orm_migration_attribute_create_add_column",
    ]


def test_sql_orm_attribute_create_required_delta_uses_empty_table_guard() -> None:
    operation = _typed_operation(
        _attribute_create_operation(
            owner_key="pkg.default.RemoteControl",
            attribute_name="serial_number",
            primitive_base_type="string",
            is_required=True,
        )
    )
    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.content_text is not None
    assert 'ALTER TABLE "remote_control" ADD COLUMN "serial_number" TEXT NOT NULL;' in (
        path.content_text
    )
    assert "RAISE EXCEPTION" in path.content_text
    assert entry.renderer_operations[0].diagnostics == [
        "sql_orm_migration_artifact_ready",
        "sql_orm_migration_attribute_create_add_column",
        "sql_orm_migration_required_add_empty_table_guard",
    ]


def test_sql_orm_attribute_delete_delta_emits_drop_column_migration_artifact() -> None:
    operation = _typed_operation(
        _attribute_delete_operation(
            owner_key="pkg.default.RemoteControl",
            attribute_name="legacy_label",
            primitive_base_type="string",
        )
    )
    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.content_text == (
        'ALTER TABLE "remote_control" DROP COLUMN IF EXISTS "legacy_label";\n'
    )
    assert entry.renderer_operations[0].diagnostics == [
        "sql_orm_migration_artifact_ready",
        "sql_orm_migration_attribute_delete_drop_column",
    ]


def test_sql_orm_attribute_required_to_optional_update_emits_drop_not_null() -> None:
    operation = _typed_operation(
        _attribute_type_update_operation(
            owner_key="pkg.default.RemoteControl",
            attribute_name="label",
            baseline_primitive_base_type="string",
            current_primitive_base_type="string",
            baseline_is_required=True,
            current_is_required=False,
        )
    )
    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.content_text == (
        'ALTER TABLE "remote_control" ALTER COLUMN "label" DROP NOT NULL;\n'
    )
    assert entry.renderer_operations[0].diagnostics == [
        "sql_orm_migration_artifact_ready",
        "sql_orm_migration_attribute_update_drop_not_null",
    ]


def test_sql_orm_attribute_type_update_emits_failfast_migration_artifact() -> None:
    operation = _typed_operation(
        _attribute_type_update_operation(
            owner_key="pkg.default.RemoteControl",
            attribute_name="label",
            baseline_primitive_base_type="string",
            current_primitive_base_type="integer",
            baseline_is_required=True,
            current_is_required=True,
        )
    )
    evidence = _render_sql_orm_generated_delta(operation)

    assert evidence.handled is True
    assert evidence.result is not None
    [entry] = evidence.result.entries
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.content_text is not None
    assert "RAISE EXCEPTION" in path.content_text
    assert "unsupported SQL attribute update migration: remote_control.label" in (
        path.content_text
    )
    assert entry.renderer_operations[0].diagnostics == [
        "sql_orm_migration_artifact_ready",
        "sql_orm_migration_unsupported_attribute_update",
        "sql_orm_migration_failfast",
    ]


def test_meta_generated_materialization_dispatch_routes_to_real_sql_plugin(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _register_sql_plugin(monkeypatch)
    payload, _expected_content, relative_path = _sql_source_artifact_payload(tmp_path)

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(
            _class_create_operation(
                relative_path=relative_path,
                source_artifact_payload=payload,
            )
        ),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="content-ontology-sql",
            package_root="/tmp/content-ontology-sql",
            sources_root="sql",
            target_language="sql",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.delta_request is not None
    assert result.result is not None
    assert (
        result.result.mode is CodeGeneratedMaterializationDeltaMode.package_delta_ready
    )
    assert result.delta_request.targets[0].relative_path == relative_path
    assert result.entry_count == 1
    assert result.renderer_operation_count == 1


def test_meta_generated_materialization_dispatch_routes_sql_migration_artifact(
    monkeypatch,
) -> None:
    _register_sql_plugin(monkeypatch)

    [result] = generated_materialization_feature_results_from_typed_operation(
        operation=_typed_operation(
            _attribute_create_operation(
                owner_key="pkg.default.RemoteControl",
                attribute_name="nickname",
                primitive_base_type="string",
                is_required=False,
            )
        ),
        context=MetaProviderDeltaGeneratedMaterializationContext(
            package_name="content-ontology-sql",
            package_root="/tmp/content-ontology-sql",
            sources_root="sql",
            target_language="sql",
        ),
    )

    assert result.status == "generated_materialization_projected"
    assert result.reason == "meta_generated_materialization_language_plugin_rendered"
    assert result.result is not None
    assert (
        result.result.mode is CodeGeneratedMaterializationDeltaMode.package_delta_ready
    )
    [entry] = result.result.entries
    assert entry.artifact_role == "sql_orm_migration"
    assert entry.package_delta is not None
    [path] = entry.package_delta.paths
    assert path.relative_path.startswith("migrations/")
    assert path.metadata is not None
    assert path.metadata["artifact_role"] == "sql_orm_migration"
    assert path.content_text == (
        'ALTER TABLE "remote_control" ADD COLUMN "nickname" TEXT;\n'
    )
    assert result.entry_count == 1
    assert result.renderer_operation_count == 1


def test_provider_delta_generated_materialization_stage_reports_sql_package_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _register_sql_plugin(monkeypatch)
    payload, expected_content, relative_path = _sql_source_artifact_payload(tmp_path)

    stage = provider_delta_generated_materialization_stage(
        package_payload={
            "package_name": "content-ontology-sql",
            "target_language": "sql",
        },
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-sql-generated-delta",
        provider_delta_semantic_change_report=_semantic_change_report(),
        provider_delta_typed_operation_plan=_typed_operation_plan(
            _class_create_operation(
                relative_path=relative_path,
                source_artifact_payload=payload,
            )
        ),
        code_package_delta={
            "package_name": "content-ontology-sql",
            "package_root": tmp_path.as_posix(),
            "sources_root": "sql",
            "target_language": "sql",
            "paths": (
                {
                    "relative_path": relative_path,
                    "language": "sql",
                },
            ),
        },
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["ready"] is True
    assert stage["projected"] is True
    assert stage["typed_operation_count"] == 1
    assert stage["feature_result_count"] == 1
    assert stage["target_count"] == 1
    assert stage["entry_count"] == 1
    assert stage["renderer_operation_count"] == 1
    assert stage["expected_generated_output_count"] == 1
    assert stage["fulfilled_generated_output_count"] == 1

    results = cast(tuple[dict[str, object], ...], stage["results"])
    assert results[0]["mode"] == "package_delta_ready"
    entries = cast(list[dict[str, object]], results[0]["entries"])
    assert entries[0]["mode"] == "package_delta_ready"
    package_delta = cast(dict[str, object], entries[0]["package_delta"])
    paths = cast(list[dict[str, object]], package_delta["paths"])
    assert paths[0]["relative_path"] == relative_path
    assert paths[0]["kind"] == "create"
    assert paths[0]["language"] == "sql"
    assert cast(str, paths[0]["content_text"]) == expected_content


def test_provider_delta_generated_materialization_stage_reports_sql_migration_artifact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _register_sql_plugin(monkeypatch)
    operation = _attribute_create_operation(
        owner_key="pkg.default.RemoteControl",
        attribute_name="nickname",
        primitive_base_type="string",
        is_required=False,
    )
    stage = provider_delta_generated_materialization_stage(
        package_payload={
            "package_name": "content-ontology-sql",
            "target_language": "sql",
        },
        manifest_path=tmp_path / "aware.toml",
        current_delta_fingerprint="sha256:test-sql-migration-delta",
        provider_delta_semantic_change_report=_semantic_change_report(),
        provider_delta_typed_operation_plan=_typed_operation_plan(operation),
        code_package_delta={
            "package_name": "content-ontology-sql",
            "package_root": tmp_path.as_posix(),
            "sources_root": "sql",
            "target_language": "sql",
        },
    )

    assert stage["status"] == "generated_materialization_ready"
    assert stage["ready"] is True
    assert stage["projected"] is True
    assert stage["typed_operation_count"] == 1
    assert stage["feature_result_count"] == 1
    assert stage["target_count"] == 1
    assert stage["entry_count"] == 1
    assert stage["renderer_operation_count"] == 1
    assert stage["expected_generated_output_count"] == 1
    assert stage["fulfilled_generated_output_count"] == 1
    assert stage["missing_generated_output_count"] == 0
    assert stage["unsupported_generated_output_count"] == 0
    assert stage["generated_materialization_artifact_path_count"] == 1
    assert stage["generated_materialization_artifact_family_counts"] == {
        "ocg_language_materialization": 1,
    }
    assert stage["generated_materialization_artifact_role_counts"] == {
        "sql_orm_migration": 1,
    }
    assert stage["generated_materialization_delta_form_counts"] == {
        "migration_artifact": 1,
    }
    assert stage["generated_materialization_path_kind_counts"] == {"create": 1}
    assert stage["generated_materialization_path_role_counts"] == {
        "generated_code": 1,
    }

    expectations = cast(tuple[dict[str, object], ...], stage["expectations"])
    assert expectations[0]["expectation"] == "required"
    assert expectations[0]["fulfillment"] == "fulfilled"
    manifest = cast(
        dict[str, object],
        stage["generated_materialization_evidence_manifest"],
    )
    assert manifest["contract_version"] == (
        "aware.meta.generated-materialization-evidence-manifest.v1"
    )
    assert manifest["result_count"] == 1
    assert manifest["entry_count"] == 1
    assert manifest["package_delta_entry_count"] == 1
    assert manifest["package_delta_path_count"] == 1
    assert manifest["non_package_delta_entry_count"] == 0
    artifact_paths = cast(tuple[dict[str, object], ...], manifest["artifact_paths"])
    assert len(artifact_paths) == 1
    assert artifact_paths[0]["artifact_role"] == "sql_orm_migration"
    assert artifact_paths[0]["delta_form"] == "migration_artifact"
    assert artifact_paths[0]["path_kind"] == "create"
    assert artifact_paths[0]["path_role"] == "generated_code"
    results = cast(tuple[dict[str, object], ...], stage["results"])
    assert results[0]["mode"] == "package_delta_ready"
    entries = cast(list[dict[str, object]], results[0]["entries"])
    assert entries[0]["artifact_role"] == "sql_orm_migration"
    package_delta = cast(dict[str, object], entries[0]["package_delta"])
    paths = cast(list[dict[str, object]], package_delta["paths"])
    assert paths[0]["relative_path"].startswith("migrations/")
    assert cast(dict[str, object], paths[0]["metadata"])["artifact_role"] == (
        "sql_orm_migration"
    )
    assert cast(str, paths[0]["content_text"]) == (
        'ALTER TABLE "remote_control" ADD COLUMN "nickname" TEXT;\n'
    )


def _register_sql_plugin(monkeypatch) -> None:
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_plugins",
        {CodeLanguage.sql: SQL_META_PLUGIN},
    )
    monkeypatch.setattr(
        MetaLanguagePluginRegistry,
        "_supported_languages",
        {CodeLanguage.sql},
    )


def _typed_operation(payload: dict[str, object]) -> MetaProviderDeltaTypedOperation:
    operation = MetaProviderDeltaTypedOperation.from_payload(payload)
    assert operation is not None
    return operation


def _render_sql_orm_generated_delta(operation: MetaProviderDeltaTypedOperation):
    target = _operation_orm_runtime_target(operation)
    owner_key = cast(str, target["owner_key"])
    relative_path = cast(str, target["relative_path"])
    return SqlOrmRuntimeGeneratedDeltaRenderer().render_generated_materialization_delta(
        MetaLanguageGeneratedMaterializationDeltaRenderRequest(
            operation=operation,
            context=MetaLanguageGeneratedMaterializationDeltaContext(
                package_name="content-ontology-sql",
                package_root="/tmp/content-ontology-sql",
                sources_root="sql",
                target_language="sql",
                renderer_profile=SQL_ORM_RENDERER_PROFILE,
                materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                product_intent="orm_runtime",
                target_hints=(
                    MetaLanguageGeneratedMaterializationTargetHint(
                        descriptor_key="orm_runtime",
                        capability_key=SQL_ORM_GENERATED_DELTA_RENDERER_NAME,
                        target_language="sql",
                        renderer_profile=SQL_ORM_RENDERER_PROFILE,
                        materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
                        owner_key=owner_key,
                        relative_path=relative_path,
                    ),
                ),
            ),
        )
    )


def _operation_orm_runtime_target(
    operation: MetaProviderDeltaTypedOperation,
) -> dict[str, object]:
    generated_materialization = operation.current.get("generated_materialization")
    assert isinstance(generated_materialization, dict)
    targets = generated_materialization.get("targets")
    assert isinstance(targets, dict)
    target = targets.get("orm_runtime")
    assert isinstance(target, dict)
    return target


def _sql_source_artifact_payload(
    tmp_path: Path,
    *,
    content: str = """
class RemoteControl {
    remote_id String key
    label String
    firmware_version String unique
}
""",
) -> tuple[dict[str, object], str, str]:
    graph, _ns = _build_graph(
        tmp_path,
        content,
    )
    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)
    output_root = tmp_path / "sqlite"
    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=graph,
            target_language_plugin_id=CodeLanguage.sql,
            output_root=output_root,
            renderer_kind=SQL_ORM_SOURCE_RENDERER_KIND,
            renderer_profile=SQL_ORM_SOURCE_RENDERER_PROFILE,
            emit_files=True,
        )
    )
    assert len(result.generated_files) == 1
    [generated] = result.generated_files
    expected_content = (output_root / generated.path).read_text(encoding="utf-8")
    payload = build_sql_orm_source_artifact_payload(
        language_graph=result.language_graph,
        relative_path=generated.path.as_posix(),
        renderer_kind=SQL_ORM_SOURCE_RENDERER_KIND,
        source_renderer_profile=SQL_ORM_SOURCE_RENDERER_PROFILE,
        materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
        generated_ocg_node_manifest=result.generated_ocg_node_manifest,
        external_language_graphs=result.language_external_graphs,
        owner_key="content.default.RemoteControl",
    )
    assert payload is not None
    return (
        payload.evidence_payload(),
        expected_content,
        generated.path.as_posix(),
    )


def _sql_package_source_artifacts(
    tmp_path: Path,
    *,
    files: dict[str, str],
    owner_by_relative_path: dict[str, tuple[str, str]],
) -> dict[str, dict[str, object]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    file_codes = tuple(
        (relative_path, _build_code(tmp_path, relative_path, content.strip()))
        for relative_path, content in sorted(files.items())
    )
    ns, _domains = _ns(
        fqn_prefix="pkg",
        namespace="default",
        code_ids=[code.id for _relative_path, code in file_codes],
    )
    graph = build_object_config_graph_from_code(
        name="package",
        description="package",
        fqn_prefix="pkg",
        file_codes=list(file_codes),
        namespace_by_code_id=ns,
    ).graph

    MetaLanguagePluginRegistry.register(SQL_META_PLUGIN)
    output_root = tmp_path / "sqlite_package"
    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=graph,
            target_language_plugin_id=CodeLanguage.sql,
            output_root=output_root,
            renderer_kind=SQL_ORM_SOURCE_RENDERER_KIND,
            renderer_profile=SQL_ORM_SOURCE_RENDERER_PROFILE,
            emit_files=True,
        )
    )
    expected_by_path = {
        generated.path.as_posix(): (output_root / generated.path).read_text(
            encoding="utf-8"
        )
        for generated in result.generated_files
    }
    assert expected_by_path
    assert set(expected_by_path) == set(owner_by_relative_path)

    payload_by_path: dict[str, object] = {}
    for relative_path, (owner_key, class_name) in owner_by_relative_path.items():
        payload = build_sql_orm_source_artifact_payload(
            language_graph=result.language_graph,
            relative_path=relative_path,
            renderer_kind=SQL_ORM_SOURCE_RENDERER_KIND,
            source_renderer_profile=SQL_ORM_SOURCE_RENDERER_PROFILE,
            materialization_source=SQL_ORM_MATERIALIZATION_SOURCE,
            generated_ocg_node_manifest=result.generated_ocg_node_manifest,
            external_language_graphs=result.language_external_graphs,
            owner_key=owner_key,
        )
        assert payload is not None, class_name
        payload_by_path[relative_path] = payload.evidence_payload()

    return {
        "expected_by_path": expected_by_path,
        "payload_by_path": payload_by_path,
        "owner_by_path": dict(owner_by_relative_path),
    }


def _class_create_operation(
    *,
    class_fqn: str = "content.default.RemoteControl",
    class_name: str = "RemoteControl",
    relative_path: str = "schema/remote_control.sql",
    source_artifact_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    semantic_key = f"ocg:content/node:{class_fqn}"
    current: dict[str, object] = {
        "semantic_key": semantic_key,
        "object_kind": "class",
        "class_fqn": class_fqn,
        "class_name": class_name,
        "name": class_name,
        "entity_name": class_name,
        "description": "Remote control config.",
        "generated_materialization": _sql_orm_runtime_targets(
            relative_path,
            owner_key=class_fqn,
        ),
    }
    if source_artifact_payload is not None:
        current[SQL_ORM_SOURCE_ARTIFACT_PAYLOAD_KEY] = source_artifact_payload
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.class.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {"object": {}},
        "current": current,
    }


def _class_update_operation(
    *,
    class_fqn: str = "content.default.RemoteControl",
    class_name: str = "RemoteControl",
    relative_path: str = "schema/remote_control.sql",
    source_artifact_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    semantic_key = f"ocg:content/node:{class_fqn}"
    current: dict[str, object] = {
        "semantic_key": semantic_key,
        "object_kind": "class",
        "class_fqn": class_fqn,
        "class_name": class_name,
        "name": class_name,
        "entity_name": class_name,
        "description": "Remote control config.",
        "generated_materialization": _sql_orm_runtime_targets(
            relative_path,
            owner_key=class_fqn,
        ),
    }
    if source_artifact_payload is not None:
        current[SQL_ORM_SOURCE_ARTIFACT_PAYLOAD_KEY] = source_artifact_payload
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.update:{semantic_key}",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.class.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {
            "object": {
                "class_fqn": class_fqn,
                "class_name": class_name,
                "name": class_name,
            },
        },
        "current": current,
    }


def _class_delete_operation(
    *,
    class_fqn: str = "content.default.RemoteControl",
    class_name: str = "RemoteControl",
    relative_path: str = "schema/remote_control.sql",
) -> dict[str, object]:
    semantic_key = f"ocg:content/node:{class_fqn}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.class.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {
            "object": {
                "class_fqn": class_fqn,
                "class_name": class_name,
                "name": class_name,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "class",
            "class_fqn": class_fqn,
            "class_name": class_name,
            "name": class_name,
            "entity_name": class_name,
            "generated_materialization": _sql_orm_runtime_targets(
                relative_path,
                owner_key=class_fqn,
            ),
        },
    }


def _enum_create_operation(
    *,
    enum_fqn: str = "content.default.RemoteMode",
    enum_name: str = "RemoteMode",
    relative_path: str,
    source_artifact_payload: dict[str, object],
) -> dict[str, object]:
    semantic_key = f"ocg:content/node:{enum_fqn}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.enum.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "enum",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "enum",
            "enum_fqn": enum_fqn,
            "enum_name": enum_name,
            "name": enum_name,
            SQL_ORM_SOURCE_ARTIFACT_PAYLOAD_KEY: source_artifact_payload,
            "generated_materialization": _sql_orm_runtime_targets(
                relative_path,
                owner_key=enum_fqn,
            ),
        },
    }


def _relationship_create_operation(
    *,
    source_class_fqn: str = "content.default.RemoteControl",
    target_class_fqn: str = "content.default.RemoteDevice",
    relationship_key: str = "devices",
    relative_path: str,
    source_artifact_payload: dict[str, object],
) -> dict[str, object]:
    semantic_key = (
        f"ocg:content/node:{source_class_fqn}/relationship:{relationship_key}"
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.relationship.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.relationship.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfigRelationship",
        "ontology_subject_kind": "relationship",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "relationship",
            "source_class_fqn": source_class_fqn,
            "target_class_fqn": target_class_fqn,
            "relationship_key": relationship_key,
            SQL_ORM_SOURCE_ARTIFACT_PAYLOAD_KEY: source_artifact_payload,
            "generated_materialization": _sql_orm_runtime_targets(
                relative_path,
                owner_key=source_class_fqn,
            ),
        },
    }


def _attribute_create_operation(
    *,
    owner_key: str,
    attribute_name: str,
    primitive_base_type: str,
    is_required: bool,
    relative_path: str = "schema/remote_control.sql",
) -> dict[str, object]:
    semantic_key = f"ocg:content/node:{owner_key}/attribute:{attribute_name}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:content/node:{owner_key}",
            "attribute_name": attribute_name,
            "attribute_signature": _attribute_signature_payload(
                owner_key=owner_key,
                attribute_name=attribute_name,
                primitive_base_type=primitive_base_type,
                is_required=is_required,
            ),
            "generated_materialization": _sql_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }


def _attribute_delete_operation(
    *,
    owner_key: str,
    attribute_name: str,
    primitive_base_type: str,
    relative_path: str = "schema/remote_control.sql",
    is_required: bool = True,
) -> dict[str, object]:
    semantic_key = f"ocg:content/node:{owner_key}/attribute:{attribute_name}"
    baseline_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=primitive_base_type,
        is_required=is_required,
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.attribute.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {
            "object": {
                "owner_key": owner_key,
                "owner_semantic_key": f"ocg:content/node:{owner_key}",
                "attribute_name": attribute_name,
                "attribute_signature": baseline_signature,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:content/node:{owner_key}",
            "attribute_name": attribute_name,
            "generated_materialization": _sql_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }


def _attribute_type_update_operation(
    *,
    owner_key: str,
    attribute_name: str,
    baseline_primitive_base_type: str,
    current_primitive_base_type: str,
    baseline_is_required: bool,
    current_is_required: bool,
    relative_path: str = "schema/remote_control.sql",
) -> dict[str, object]:
    semantic_key = f"ocg:content/node:{owner_key}/attribute:{attribute_name}"
    baseline_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=baseline_primitive_base_type,
        is_required=baseline_is_required,
    )
    current_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=current_primitive_base_type,
        is_required=current_is_required,
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.update:{semantic_key}:type",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": ("schema/remote_control.aware",),
        "baseline": {
            "object": {
                "attribute_name": attribute_name,
                "attribute_signature": baseline_signature,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:content/node:{owner_key}",
            "attribute_name": attribute_name,
            "attribute_signature": current_signature,
            "generated_materialization": _sql_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }


def _attribute_signature_payload(
    *,
    owner_key: str,
    attribute_name: str,
    primitive_base_type: str,
    is_required: bool,
) -> dict[str, object]:
    return {
        "owner_key": owner_key,
        "name": attribute_name,
        "description": f"{attribute_name} field.",
        "is_required": is_required,
        "is_public": True,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": primitive_base_type,
        },
    }


def _sql_orm_runtime_targets(
    relative_path: str,
    *,
    owner_key: str = "content.default.RemoteControl",
) -> dict[str, object]:
    return {
        "targets": {
            "orm_runtime": {
                "descriptor_key": "orm_runtime",
                "capability_key": SQL_ORM_GENERATED_DELTA_RENDERER_NAME,
                "target_language": "sql",
                "renderer_profile": SQL_ORM_RENDERER_PROFILE,
                "materialization_source": SQL_ORM_MATERIALIZATION_SOURCE,
                "source_renderer_profile": SQL_ORM_SOURCE_RENDERER_PROFILE,
                "renderer_kind": SQL_ORM_SOURCE_RENDERER_KIND,
                "product_intent": "orm_runtime",
                "owner_key": owner_key,
                "target_key": f"sql_orm:{owner_key}",
                "relative_path": relative_path,
                "artifact_family": "ocg_language_materialization",
                "artifact_role": "sql_orm_source_artifact",
            },
        },
    }


def _typed_operation_plan(payload: dict[str, object]) -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "reason": "test_sql_generated_materialization_delta",
        "typed_operations": (payload,),
        "blocked_operations": (),
    }


def _semantic_change_report() -> dict[str, object]:
    return {
        "status": "semantic_change_report_ready",
        "reason": "test_sql_generated_materialization_delta",
        "available": True,
        "blocked": False,
        "semantic_world_change_event_count": 1,
        "semantic_world_change_count": 1,
        "minimal_readable_semantic_change_chain": {
            "status": "readable_semantic_change_chain_ready",
            "reason": "test_sql_generated_materialization_delta",
            "blocked": False,
            "source_change_count": 1,
            "change_count": 1,
            "line_count": 1,
            "lines": ("SQL generated-materialization source artifact delta.",),
            "markdown": "- SQL generated-materialization source artifact delta.",
            "plain_text": "SQL generated-materialization source artifact delta.",
        },
    }
