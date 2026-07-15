from __future__ import annotations

from pathlib import Path

from aware_meta.materialization import (
    LanguageMaterializationArtifactLifecycleBuildRequest,
    LanguageMaterializationArtifactKind,
    LanguageMaterializationArtifactTracker,
    LanguageMaterializationProducerStep,
    LanguageMaterializationStageability,
    build_language_materialization_artifact_lifecycle,
    language_materialization_classify_output_artifact_kind,
    language_materialization_direct_write_mutation_record,
    language_materialization_artifact_mutation_record,
    language_materialization_snapshot_file,
)


def test_language_materialization_artifact_tracker_builds_package_lifecycle(
    tmp_path: Path,
) -> None:
    aware_root = tmp_path / "workspace"
    package_root = aware_root / "modules" / "demo" / "python"
    source_file = package_root / "aware_demo" / "device.py"
    tracker = LanguageMaterializationArtifactTracker()

    tracker.record_direct_write(
        path=source_file,
        producer_step=LanguageMaterializationProducerStep.package_build,
        artifact_kind=language_materialization_classify_output_artifact_kind(
            source_file
        ),
        package_name="demo-ontology",
        ownership_receipt={"producer_provider_key": "aware_meta"},
    )
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("class Device:\n    pass\n", encoding="utf-8")

    result = tracker.build_result(
        aware_root=aware_root,
        materialization_output_root=package_root,
        package_roots_by_name={"demo-ontology": package_root},
        package_import_roots={"demo-ontology": "aware_demo"},
        warning_count=2,
    )

    assert len(result.artifact_changes) == 1
    change = result.artifact_changes[0]
    assert change.repo_rel_path == Path("modules/demo/python/aware_demo/device.py")
    assert change.materialization_rel_path == Path("aware_demo/device.py")
    assert change.package_rel_path == Path("aware_demo/device.py")
    assert change.package_name == "demo-ontology"
    assert change.artifact_kind is LanguageMaterializationArtifactKind.source_code
    assert change.producer_step is LanguageMaterializationProducerStep.package_build
    assert change.stageability is LanguageMaterializationStageability.stage
    assert change.ownership_receipt == {"producer_provider_key": "aware_meta"}

    assert len(result.package_outcomes) == 1
    package_outcome = result.package_outcomes[0]
    assert package_outcome.package_name == "demo-ontology"
    assert package_outcome.output_root == Path("modules/demo/python")
    assert package_outcome.import_root == "aware_demo"
    assert package_outcome.artifact_change_refs == (
        Path("modules/demo/python/aware_demo/device.py"),
    )
    assert result.summary.changes_total == 1
    assert result.summary.changes_by_kind == {"create": 1}
    assert result.summary.changes_by_producer_step == {"package_build": 1}
    assert result.summary.changes_by_stageability == {"stage": 1}
    assert result.summary.package_count == 1
    assert result.summary.warning_count == 2


def test_language_materialization_artifact_tracker_marks_internal_artifacts_skip(
    tmp_path: Path,
) -> None:
    aware_root = tmp_path / "workspace"
    internal_file = aware_root / ".aware" / "materializations" / "manifest.json"
    tracker = LanguageMaterializationArtifactTracker()

    tracker.record_direct_write(
        path=internal_file,
        producer_step=LanguageMaterializationProducerStep.manifest_write,
        artifact_kind=LanguageMaterializationArtifactKind.manifest,
    )
    internal_file.parent.mkdir(parents=True, exist_ok=True)
    internal_file.write_text('{"ok": true}\n', encoding="utf-8")

    result = tracker.build_result(
        aware_root=aware_root,
        materialization_output_root=aware_root / ".aware" / "materializations",
        package_roots_by_name={},
        package_import_roots={},
    )

    assert len(result.artifact_changes) == 1
    change = result.artifact_changes[0]
    assert change.stageability is LanguageMaterializationStageability.skip
    assert change.stageability_reason == (
        "internal compiler/runtime artifact outside canonical staging output"
    )
    assert result.summary.changes_by_stageability == {"skip": 1}


def test_language_materialization_artifact_tracker_detects_deletes(
    tmp_path: Path,
) -> None:
    aware_root = tmp_path / "workspace"
    package_root = aware_root / "package"
    stale_file = package_root / "stale.py"
    stale_file.parent.mkdir(parents=True, exist_ok=True)
    stale_file.write_text("stale = True\n", encoding="utf-8")
    before = language_materialization_snapshot_file(stale_file)
    stale_file.unlink()

    tracker = LanguageMaterializationArtifactTracker()
    tracker.remember_mutation(
        path=stale_file,
        before=before,
        producer_step=LanguageMaterializationProducerStep.stale_prune,
        artifact_kind=LanguageMaterializationArtifactKind.source_code,
        package_name="demo",
    )

    result = tracker.build_result(
        aware_root=aware_root,
        materialization_output_root=package_root,
        package_roots_by_name={"demo": package_root},
        package_import_roots={"demo": None},
    )

    assert len(result.artifact_changes) == 1
    change = result.artifact_changes[0]
    assert change.change_kind.value == "delete"
    assert change.hash_before is not None
    assert change.hash_after is None
    assert result.summary.changes_by_kind == {"delete": 1}


def test_build_language_materialization_artifact_lifecycle_from_records(
    tmp_path: Path,
) -> None:
    aware_root = tmp_path / "workspace"
    package_root = aware_root / "package"
    source_file = package_root / "demo.py"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    direct_record = language_materialization_direct_write_mutation_record(
        path=source_file,
        producer_step=LanguageMaterializationProducerStep.package_build,
        artifact_kind=LanguageMaterializationArtifactKind.source_code,
        package_name="demo",
    )
    source_file.write_text("value = 1\n", encoding="utf-8")

    stale_file = package_root / "stale.py"
    stale_file.write_text("stale = True\n", encoding="utf-8")
    stale_before = language_materialization_snapshot_file(stale_file)
    stale_file.unlink()

    result = build_language_materialization_artifact_lifecycle(
        LanguageMaterializationArtifactLifecycleBuildRequest(
            aware_root=aware_root,
            materialization_output_root=package_root,
            package_roots_by_name={"demo": package_root},
            package_import_roots={"demo": None},
            mutation_records=(
                direct_record,
                language_materialization_artifact_mutation_record(
                    path=stale_file,
                    before=stale_before,
                    producer_step=LanguageMaterializationProducerStep.stale_prune,
                    artifact_kind=LanguageMaterializationArtifactKind.source_code,
                    package_name="demo",
                ),
            ),
            warning_count=1,
        )
    )

    assert result.summary.changes_by_kind == {"create": 1, "delete": 1}
    assert result.summary.warning_count == 1
    assert result.package_outcomes[0].artifact_change_refs == (
        Path("package/demo.py"),
        Path("package/stale.py"),
    )
