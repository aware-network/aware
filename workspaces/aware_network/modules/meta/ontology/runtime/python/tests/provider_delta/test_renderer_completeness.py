from __future__ import annotations

from aware_code_service_dto.code.features.generated_materialization_delta import (
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaResult,
    CodeGeneratedMaterializationTargetRef,
)
from aware_code_service_dto.code.features.package_common import CodePackagePathRole
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_types import JsonObject
from aware_meta.materialization.deltas.renderer_completeness import (
    compare_generated_materialization_package_delta_final_state,
    compare_generated_materialization_package_delta_path_content_map,
    compare_generated_materialization_path_content_map,
    generated_materialization_evidence_manifest_from_results,
    generated_materialization_final_path_content_map_from_package_deltas,
    generated_materialization_package_delta_from_path_content_map,
    generated_materialization_path_content_map_from_package_deltas,
    generated_materialization_path_content_map_from_results,
)


def test_renderer_completeness_accepts_matching_code_package_delta_results() -> None:
    expected_by_path = {
        "controls.sql": "CREATE TABLE remote_control();\n",
        "devices.sql": "CREATE TABLE local_device();\n",
    }

    comparison = compare_generated_materialization_path_content_map(
        expected_by_path=expected_by_path,
        delta_results=(
            _result(("controls.sql", "CREATE TABLE remote_control();\n")),
            _result(("devices.sql", "CREATE TABLE local_device();\n")),
        ),
    )

    assert comparison.equivalent is True
    assert comparison.diagnostics == ()
    assert comparison.actual_by_path == expected_by_path


def test_renderer_completeness_reports_path_map_drift() -> None:
    comparison = compare_generated_materialization_path_content_map(
        expected_by_path={
            "controls.sql": "expected controls\n",
            "devices.sql": "expected devices\n",
            "empty.sql": "expected empty\n",
        },
        delta_results=(
            _result(
                ("controls.sql", "actual controls\n"),
                ("extra.sql", "actual extra\n"),
                ("empty.sql", None),
            ),
        ),
    )

    assert comparison.equivalent is False
    assert comparison.mismatched_paths == ("controls.sql",)
    assert comparison.unexpected_paths == ("extra.sql",)
    assert comparison.missing_paths == ("devices.sql", "empty.sql")
    assert comparison.missing_content_text_paths == ("empty.sql",)
    assert comparison.diagnostics == (
        "missing_content_text_paths:empty.sql",
        "missing_paths:devices.sql,empty.sql",
        "unexpected_paths:extra.sql",
        "mismatched_paths:controls.sql",
    )


def test_renderer_completeness_reports_duplicate_delta_paths() -> None:
    path_map = generated_materialization_path_content_map_from_results(
        (
            _result(
                ("schema.sql", "first\n"),
                ("schema.sql", "second\n"),
            ),
        )
    )

    assert path_map.clean is False
    assert path_map.duplicate_paths == ("schema.sql",)
    assert path_map.content_text_by_path == {"schema.sql": "second\n"}


def test_renderer_completeness_accepts_resolved_code_package_deltas() -> None:
    package_delta = CodePackageDelta(
        package_name="content-ontology-python",
        paths=[
            CodePackageDeltaPath(
                relative_path="home/controls.py",
                kind=CodePackageDeltaKind.update,
                content_text="class RemoteControl: pass\n",
            ),
            CodePackageDeltaPath(
                relative_path="devices/local.py",
                kind=CodePackageDeltaKind.update,
                content_text="class LocalDevice: pass\n",
            ),
        ],
    )

    comparison = compare_generated_materialization_package_delta_path_content_map(
        expected_by_path={
            "home/controls.py": "class RemoteControl: pass\n",
            "devices/local.py": "class LocalDevice: pass\n",
        },
        package_deltas=(package_delta,),
    )
    path_map = generated_materialization_path_content_map_from_package_deltas(
        (package_delta,),
    )

    assert comparison.equivalent is True
    assert comparison.actual_by_path == comparison.expected_by_path
    assert path_map.clean is True
    assert path_map.package_delta_path_count == 2


def test_renderer_completeness_builds_package_delta_from_path_content_map() -> None:
    package_delta = generated_materialization_package_delta_from_path_content_map(
        package_name="content-ontology-python",
        content_text_by_path={
            "part/content_part.py": "class ContentPart: pass\n",
            "content/content.py": "class Content: pass\n",
        },
    )
    path_map = generated_materialization_path_content_map_from_package_deltas(
        (package_delta,),
    )

    assert package_delta.package_name == "content-ontology-python"
    assert [path.relative_path for path in package_delta.paths] == [
        "content/content.py",
        "part/content_part.py",
    ]
    assert [_enum_value(path.kind) for path in package_delta.paths] == [
        "update",
        "update",
    ]
    assert [_enum_value(path.path_role) for path in package_delta.paths] == [
        "generated_code",
        "generated_code",
    ]
    assert path_map.clean is True
    assert path_map.package_delta_path_count == 2
    assert path_map.content_text_by_path == {
        "content/content.py": "class Content: pass\n",
        "part/content_part.py": "class ContentPart: pass\n",
    }


def test_renderer_completeness_applies_ordered_package_deltas_to_final_state() -> None:
    baseline_by_path = {
        "home/controls.py": "class TvChannel: pass\n",
        "devices/removed.py": "class Removed: pass\n",
    }
    package_deltas = (
        CodePackageDelta(
            package_name="content-ontology-python",
            paths=[
                CodePackageDeltaPath(
                    relative_path="home/controls.py",
                    kind=CodePackageDeltaKind.update,
                    content_text="class RemoteControl: pass\nclass TvChannel: pass\n",
                ),
            ],
        ),
        CodePackageDelta(
            package_name="content-ontology-python",
            paths=[
                CodePackageDeltaPath(
                    relative_path="home/controls.py",
                    kind=CodePackageDeltaKind.update,
                    content_text=(
                        "class RemoteControl:\n"
                        "    remote_id: str\n"
                        "class TvChannel: pass\n"
                    ),
                ),
                CodePackageDeltaPath(
                    relative_path="devices/new.py",
                    kind=CodePackageDeltaKind.create,
                    content_text="class NewDevice: pass\n",
                ),
                CodePackageDeltaPath(
                    relative_path="devices/removed.py",
                    kind=CodePackageDeltaKind.delete,
                ),
            ],
        ),
    )

    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path={
            "home/controls.py": (
                "class RemoteControl:\n"
                "    remote_id: str\n"
                "class TvChannel: pass\n"
            ),
            "devices/new.py": "class NewDevice: pass\n",
        },
        baseline_by_path=baseline_by_path,
        package_deltas=package_deltas,
    )
    final_state = generated_materialization_final_path_content_map_from_package_deltas(
        baseline_by_path=baseline_by_path,
        package_deltas=package_deltas,
    )

    assert comparison.equivalent is True
    assert comparison.actual_by_path == comparison.expected_by_path
    assert final_state.clean is True
    assert final_state.deleted_paths == ("devices/removed.py",)
    assert final_state.package_delta_path_count == 4


def test_renderer_completeness_reports_final_state_delta_application_diagnostics() -> (
    None
):
    unsupported_path = CodePackageDeltaPath.model_construct(
        relative_path="unsupported.py",
        kind="move",
        content_text="unsupported\n",
    )
    package_delta = CodePackageDelta(
        package_name="content-ontology-python",
        paths=[
            CodePackageDeltaPath(
                relative_path="missing.py",
                kind=CodePackageDeltaKind.update,
                content_text=None,
            ),
            unsupported_path,
        ],
    )

    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path={"missing.py": "new\n", "unsupported.py": "unsupported\n"},
        baseline_by_path={"missing.py": "old\n"},
        package_deltas=(package_delta,),
    )

    assert comparison.equivalent is False
    assert comparison.missing_content_text_paths == ("missing.py",)
    assert comparison.unsupported_path_kind_paths == ("unsupported.py",)
    assert comparison.missing_paths == ("unsupported.py",)
    assert comparison.mismatched_paths == ("missing.py",)
    assert comparison.diagnostics == (
        "missing_content_text_paths:missing.py",
        "unsupported_path_kind_paths:unsupported.py",
        "missing_paths:unsupported.py",
        "mismatched_paths:missing.py",
    )


def test_renderer_completeness_manifest_summarizes_artifact_evidence() -> None:
    result = CodeGeneratedMaterializationDeltaResult(
        provider_key="aware_meta",
        semantic_owner="aware_meta.ocg",
        available=True,
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        entries=[
            CodeGeneratedMaterializationDeltaEntry(
                entry_key="runtime-model",
                mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
                target=CodeGeneratedMaterializationTargetRef(
                    target_language="alpha",
                    package_name="content-alpha",
                    renderer_profile="orm_runtime",
                    materialization_source="semantic_contract",
                    artifact_family="ocg_language_materialization",
                    artifact_role="runtime_model",
                    output_key="alpha.runtime_model",
                ),
                artifact_family="ocg_language_materialization",
                artifact_role="runtime_model",
                artifact_key="alpha.runtime_model",
                package_delta=CodePackageDelta(
                    package_name="content-alpha",
                    paths=[
                        CodePackageDeltaPath(
                            relative_path="generated/device.alpha",
                            kind=CodePackageDeltaKind.update,
                            content_text="device runtime model\n",
                            path_role=CodePackagePathRole.generated_code,
                            metadata=JsonObject({"delta_form": "source_artifact"}),
                        ),
                    ],
                ),
            ),
            CodeGeneratedMaterializationDeltaEntry(
                entry_key="schema-migration",
                mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
                target=CodeGeneratedMaterializationTargetRef(
                    target_language="beta",
                    package_name="content-beta",
                    renderer_profile="orm_runtime",
                    materialization_source="semantic_contract",
                    artifact_family="ocg_language_materialization",
                    output_key="beta.schema_migration",
                ),
                artifact_family="ocg_language_materialization",
                artifact_key="beta.schema_migration",
                package_delta=CodePackageDelta(
                    package_name="content-beta",
                    paths=[
                        CodePackageDeltaPath(
                            relative_path="migrations/add_device.beta",
                            kind=CodePackageDeltaKind.create,
                            content_text="add device column\n",
                            path_role=CodePackagePathRole.generated_code,
                            metadata=JsonObject(
                                {
                                    "artifact_role": "schema_migration",
                                    "delta_form": "migration_artifact",
                                },
                            ),
                        ),
                    ],
                    metadata=JsonObject({"delta_form": "migration_artifact"}),
                ),
            ),
            CodeGeneratedMaterializationDeltaEntry(
                entry_key="section-only",
                mode=CodeGeneratedMaterializationDeltaMode.section_delta_ready,
                target=CodeGeneratedMaterializationTargetRef(
                    target_language="gamma",
                    renderer_profile="orm_runtime",
                    materialization_source="semantic_contract",
                ),
            ),
        ],
    )

    manifest = generated_materialization_evidence_manifest_from_results((result,))
    payload = manifest.evidence_payload()

    assert manifest.result_count == 1
    assert manifest.entry_count == 3
    assert manifest.package_delta_entry_count == 2
    assert manifest.non_package_delta_entry_count == 1
    assert manifest.package_delta_path_count == 2
    assert manifest.artifact_path_count == 2
    assert manifest.missing_content_text_path_count == 0
    assert manifest.missing_artifact_role_count == 0
    assert manifest.artifact_family_counts == {"ocg_language_materialization": 2}
    assert manifest.artifact_role_counts == {
        "runtime_model": 1,
        "schema_migration": 1,
    }
    assert manifest.delta_form_counts == {
        "migration_artifact": 1,
        "source_artifact": 1,
    }
    assert manifest.path_kind_counts == {"create": 1, "update": 1}
    assert manifest.path_role_counts == {"generated_code": 2}
    assert payload["contract_version"] == (
        "aware.meta.generated-materialization-evidence-manifest.v1"
    )
    assert payload["artifact_role_counts"] == manifest.artifact_role_counts
    assert payload["artifact_paths"] == (
        {
            "provider_key": "aware_meta",
            "semantic_owner": "aware_meta.ocg",
            "result_mode": "package_delta_ready",
            "entry_mode": "package_delta_ready",
            "package_name": "content-alpha",
            "target_language": "alpha",
            "renderer_profile": "orm_runtime",
            "materialization_source": "semantic_contract",
            "artifact_family": "ocg_language_materialization",
            "artifact_role": "runtime_model",
            "artifact_key": "alpha.runtime_model",
            "relative_path": "generated/device.alpha",
            "path_kind": "update",
            "path_role": "generated_code",
            "delta_form": "source_artifact",
            "has_content_text": True,
        },
        {
            "provider_key": "aware_meta",
            "semantic_owner": "aware_meta.ocg",
            "result_mode": "package_delta_ready",
            "entry_mode": "package_delta_ready",
            "package_name": "content-beta",
            "target_language": "beta",
            "renderer_profile": "orm_runtime",
            "materialization_source": "semantic_contract",
            "artifact_family": "ocg_language_materialization",
            "artifact_role": "schema_migration",
            "artifact_key": "beta.schema_migration",
            "relative_path": "migrations/add_device.beta",
            "path_kind": "create",
            "path_role": "generated_code",
            "delta_form": "migration_artifact",
            "has_content_text": True,
        },
    )


def _result(
    *paths: tuple[str, str | None],
) -> CodeGeneratedMaterializationDeltaResult:
    return CodeGeneratedMaterializationDeltaResult(
        provider_key="aware_meta",
        semantic_owner="aware_meta.ocg",
        available=True,
        mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
        entries=[
            CodeGeneratedMaterializationDeltaEntry(
                mode=CodeGeneratedMaterializationDeltaMode.package_delta_ready,
                target=CodeGeneratedMaterializationTargetRef(
                    target_language="sql",
                    renderer_profile="orm_runtime",
                ),
                package_delta=CodePackageDelta(
                    package_name="content-ontology-sql",
                    paths=[
                        CodePackageDeltaPath(
                            relative_path=relative_path,
                            kind=CodePackageDeltaKind.create,
                            content_text=content_text,
                        )
                        for relative_path, content_text in paths
                    ],
                ),
            ),
        ],
    )


def _enum_value(value: object) -> object:
    raw_value = getattr(value, "value", None)
    return raw_value if raw_value is not None else value
