from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY,
)
from aware_meta.materialization import service as meta_service
from aware_meta.materialization import workspace_provider


def test_meta_workspace_materialize_compile_parity_receipt_is_complete(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    request = _request(
        tmp_path,
        targets=(
            _target(
                materialization_source="ontology",
                import_root="aware_demo_ontology",
                output_root="modules/demo/structure/ontology/python",
                renderer_profile="orm_runtime",
                stable_ids_ownership="compiler",
                stable_ids_resolution_policy="class_strict",
            ),
            _target(
                materialization_source="runtime_handlers",
                import_root="aware_demo",
                output_root="modules/demo/runtime/aware_demo",
                renderer_kind="runtime_handlers_meta",
                source_is_runtime=True,
                code_package_surface="runtime",
            ),
        ),
    )

    receipt = workspace_provider._leaf_compile_parity_receipts(  # noqa: SLF001
        request=request,
        leaf_result=leaf_result,
        lifecycle_receipts=({"schema": "lifecycle"},),
        materialization_index_receipts=(
            {
                "receipt_kind": ("object_config_graph_package_materialization_index"),
                "cache_status": "fingerprint_reuse",
            },
        ),
        artifact_ownership_receipts=_complete_artifact_receipts(),
        post_step_receipts=_post_step_receipts(
            tmp_path,
            (
                ("ontology", "modules/demo/structure/ontology/python"),
                ("runtime_handlers", "modules/demo/runtime/aware_demo"),
            ),
        ),
    )[0]

    assert receipt["schema"] == (
        "aware.meta.workspace_materialize.compile_parity_receipt.v1"
    )
    assert receipt["receipt_kind"] == ("meta_workspace_materialize_compile_parity")
    assert receipt["status"] == "compile_equivalent"
    assert receipt["env_artifacts_required"] is False
    assert receipt["missing_required_artifact_roles"] == ()
    assert receipt["missing_required_post_step_tools"] == ()
    assert receipt["post_step_receipt_count"] == 2
    assert receipt["source_code_package_id"] == str(leaf_result.code_package.id)
    assert receipt["source_object_instance_graph_commit_id"] == str(
        leaf_result.code_package_object_instance_graph_commit_id
    )
    package_oig_commit_id = (
        leaf_result.object_config_graph_package_object_instance_graph_commit_id
    )
    assert receipt[
        "object_config_graph_package_object_instance_graph_commit_id"
    ] == str(package_oig_commit_id)
    assert receipt["language_materialization_target_count"] == 2
    language_targets = cast(
        tuple[dict[str, object], ...],
        receipt["language_materialization_targets"],
    )
    assert language_targets[0]["stable_ids_ownership"] == "compiler"
    assert language_targets[0]["stable_ids_resolution_policy"] == "class_strict"
    assert "python.meta_runtime_handlers_provider" in cast(
        tuple[str, ...],
        receipt["available_output_keys"],
    )
    assert (
        cast(dict[str, int], receipt["artifact_role_counts"])[
            "materialization_index_receipt"
        ]
        == 1
    )
    assert isinstance(receipt["digest"], str)
    assert str(receipt["receipt_id"]).startswith("sha256:")


def test_meta_workspace_materialized_language_package_surface_includes_code_package_truth(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    materialized_package = (
        leaf_result.object_config_graph_package.language_materializations[
            0
        ].materialized_packages[0]
    )
    generated_ref = _generated_code_package_ref(
        leaf_result=leaf_result,
        code_package_id=materialized_package.code_package_id,
        package_name=materialized_package.package_name,
        package_root=materialized_package.package_root,
    )

    materialized_packages = workspace_provider._materialized_language_packages_from_leaf_result(  # noqa: SLF001
        leaf_result=leaf_result,
        generated_code_package_refs=(generated_ref,),
    )

    assert len(materialized_packages) == 1
    row = materialized_packages[0]
    assert row["schema"] == (
        "aware.meta.object_config_graph_package.materialized_language_package.v1"
    )
    assert row["status"] == "materialized"
    assert row["code_package_id"] == str(materialized_package.code_package_id)
    assert (
        row["code_package_head_commit_id"]
        == generated_ref["code_package_head_commit_id"]
    )
    assert row["code_package_object_instance_graph_commit_id"] == str(
        materialized_package.code_package_object_instance_graph_commit_id
    )
    assert row["package_name"] == "aware-demo-ontology"
    assert row["package_root"] == "modules/demo/structure/ontology/python"
    assert row["code_package_surface"] == "structure"
    assert row["code_package_config_key"] == "python.structure"
    assert row["code_package_config_id"] == generated_ref["code_package_config_id"]
    assert row["manifest_kind"] == "pyproject_toml"
    assert row["manifest_relative_path"] == (
        "modules/demo/structure/ontology/python/pyproject.toml"
    )

    bundles = workspace_provider._bundle_packages_from_leaf_result(  # noqa: SLF001
        leaf_result=leaf_result,
        workspace_root=tmp_path,
        materialized_language_packages=materialized_packages,
    )

    assert len(bundles) == 1
    assert len(bundles[0].semantic_packages) == 1
    semantic_package = bundles[0].semantic_packages[0]
    assert semantic_package["module_name"] == "demo"
    assert semantic_package["manifest_relative_path"] == (
        "modules/demo/structure/ontology/aware.toml"
    )
    assert semantic_package["materialized_language_packages"] == materialized_packages

    receipt = workspace_provider._leaf_compile_parity_receipts(  # noqa: SLF001
        request=_request(
            tmp_path,
            targets=(
                _target(
                    materialization_source="ontology",
                    import_root="aware_demo_ontology",
                    output_root="modules/demo/structure/ontology/python",
                    renderer_profile="orm_runtime",
                ),
            ),
        ),
        leaf_result=leaf_result,
        lifecycle_receipts=({"schema": "lifecycle"},),
        materialization_index_receipts=(
            {
                "receipt_kind": ("object_config_graph_package_materialization_index"),
            },
        ),
        artifact_ownership_receipts=_complete_artifact_receipts(),
        post_step_receipts=_post_step_receipts(
            tmp_path,
            (("ontology", "modules/demo/structure/ontology/python"),),
        ),
        materialized_language_packages=materialized_packages,
    )[0]

    assert receipt["materialized_language_package_count"] == 1
    assert receipt["materialized_language_packages"] == materialized_packages


def test_meta_workspace_materialized_language_package_uses_generated_ref_truth(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    language_materialization = (
        leaf_result.object_config_graph_package.language_materializations[0]
    )
    materialized_package = language_materialization.materialized_packages[0]
    generated_ref = _generated_code_package_ref(
        leaf_result=leaf_result,
        code_package_id=materialized_package.code_package_id,
        package_name=materialized_package.package_name,
        package_root=materialized_package.package_root,
    )
    language_materialization.materialized_packages = ()

    materialized_packages = workspace_provider._materialized_language_packages_from_leaf_result(  # noqa: SLF001
        leaf_result=leaf_result,
        generated_code_package_refs=(generated_ref,),
    )

    assert len(materialized_packages) == 1
    row = materialized_packages[0]
    assert row["code_package_id"] == generated_ref["code_package_id"]
    assert row["code_package_surface"] == "structure"
    assert row["code_package_config_key"] == "python.structure"
    assert row["code_package_config_id"] == generated_ref["code_package_config_id"]
    assert row["manifest_kind"] == "pyproject_toml"
    assert row["manifest_relative_path"] == generated_ref["manifest_relative_path"]
    assert row["package_root"] == generated_ref["package_root"]
    assert row["status"] == "materialized"


def test_meta_workspace_ownership_receipt_uses_generated_code_package_truth(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "modules/demo/structure/ontology/python"
    artifact_path = package_root / "aware_demo_ontology/_aware/binding.msgpack"
    generated_ref = {
        "code_package_id": str(uuid4()),
        "code_package_config_key": "meta.generated.python.structure",
        "code_package_config_id": str(uuid4()),
        "code_package_surface": "structure",
        "manifest_kind": "pyproject_toml",
        "manifest_relative_path": (
            "modules/demo/structure/ontology/python/pyproject.toml"
        ),
        "package_root": "modules/demo/structure/ontology/python",
        "sources_root": "modules/demo/structure/ontology/python/aware_demo_ontology",
        "package_name": "aware-demo-ontology",
    }

    receipts = workspace_provider._language_ownership_receipts_with_generated_code_package_truth(  # noqa: SLF001
        ownership_receipts=({"path": artifact_path.as_posix()},),
        generated_code_package_refs=(generated_ref,),
        workspace_root=tmp_path,
    )

    assert receipts == (
        {
            "path": artifact_path.as_posix(),
            "code_package_id": generated_ref["code_package_id"],
            "code_package_config_key": generated_ref["code_package_config_key"],
            "code_package_config_id": generated_ref["code_package_config_id"],
            "code_package_surface": "structure",
            "manifest_kind": "pyproject_toml",
            "manifest_relative_path": generated_ref["manifest_relative_path"],
            "package_root": generated_ref["package_root"],
            "sources_root": generated_ref["sources_root"],
            "code_package_name": "aware-demo-ontology",
        },
    )


def test_meta_language_materialization_realization_aliases_declared_code_package_id() -> (
    None
):
    object_config_graph_package_id = uuid4()
    actual_code_package_id = uuid4()
    declared_code_package_id = uuid4()
    generated_code_package_oig_commit_id = uuid4()

    realizations = meta_service._language_materialization_package_realizations_by_code_package_id(  # noqa: SLF001
        generated_code_package_refs=(
            {
                "schema": "aware.meta.language_materialization.code_package_ref.v1",
                "object_config_graph_package_id": str(object_config_graph_package_id),
                "declared_code_package_id": str(declared_code_package_id),
                "code_package_id": str(actual_code_package_id),
                "code_package_commit_id": str(uuid4()),
                "code_package_head_commit_id": str(uuid4()),
                "code_package_object_instance_graph_commit_id": str(
                    generated_code_package_oig_commit_id
                ),
                "package_name": "aware-demo-ontology",
            },
        ),
        object_config_graph_package_id=object_config_graph_package_id,
    )

    assert (
        realizations[actual_code_package_id] == realizations[declared_code_package_id]
    )
    assert (
        meta_service._language_materialization_package_realization_count(
            realizations
        )  # noqa: SLF001
        == 1
    )


def test_meta_language_materialization_realization_receipt_rehydrates_complete_refs(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    package = leaf_result.object_config_graph_package
    materialized_package = package.language_materializations[0].materialized_packages[0]
    generated_ref = _generated_code_package_ref(
        leaf_result=leaf_result,
        code_package_id=materialized_package.code_package_id,
        package_name=materialized_package.package_name,
        package_root=materialized_package.package_root,
    )
    receipt = (
        meta_service._materialization_index_receipt_with_realization(  # noqa: SLF001
            receipt={
                "cache_key": {
                    "source_manifest_hash": "source",
                    "dependency_signature": "deps",
                }
            },
            object_config_graph_package_id=package.id,
            object_config_graph_package_head_commit_id=(
                leaf_result.object_config_graph_package_head_commit_id
            ),
            object_config_graph_package_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
            realization_count=1,
            generated_code_package_refs=(generated_ref,),
        )
    )

    realizations, status = (
        meta_service._language_materialization_package_realizations_from_reuse_receipt(  # noqa: SLF001
            receipt=receipt,
            object_config_graph_package_id=package.id,
            object_config_graph_package_head_commit_id=(
                leaf_result.object_config_graph_package_head_commit_id
            ),
            object_config_graph_package_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
        )
    )

    assert status == "complete"
    assert tuple(realizations) == (materialized_package.code_package_id,)
    assert realizations[materialized_package.code_package_id] == generated_ref


def test_meta_language_materialization_realization_receipt_rejects_stale_or_incomplete_evidence(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    package = leaf_result.object_config_graph_package
    materialized_package = package.language_materializations[0].materialized_packages[0]
    generated_ref = _generated_code_package_ref(
        leaf_result=leaf_result,
        code_package_id=materialized_package.code_package_id,
        package_name=materialized_package.package_name,
        package_root=materialized_package.package_root,
    )
    receipt = (
        meta_service._materialization_index_receipt_with_realization(  # noqa: SLF001
            receipt={},
            object_config_graph_package_id=package.id,
            object_config_graph_package_head_commit_id=(
                leaf_result.object_config_graph_package_head_commit_id
            ),
            object_config_graph_package_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
            realization_count=1,
            generated_code_package_refs=(generated_ref,),
        )
    )

    realizations, status = (
        meta_service._language_materialization_package_realizations_from_reuse_receipt(  # noqa: SLF001
            receipt=receipt,
            object_config_graph_package_id=package.id,
            object_config_graph_package_head_commit_id=uuid4(),
            object_config_graph_package_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
        )
    )

    assert realizations == {}
    assert status == "object_config_graph_package_head_commit_id_mismatch"

    incomplete_ref = dict(generated_ref)
    incomplete_ref.pop("code_package_head_commit_id")
    incomplete_receipt = (
        meta_service._materialization_index_receipt_with_realization(  # noqa: SLF001
            receipt={},
            object_config_graph_package_id=package.id,
            object_config_graph_package_head_commit_id=(
                leaf_result.object_config_graph_package_head_commit_id
            ),
            object_config_graph_package_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
            realization_count=1,
            generated_code_package_refs=(incomplete_ref,),
        )
    )
    realizations, status = (
        meta_service._language_materialization_package_realizations_from_reuse_receipt(  # noqa: SLF001
            receipt=incomplete_receipt,
            object_config_graph_package_id=package.id,
            object_config_graph_package_head_commit_id=(
                leaf_result.object_config_graph_package_head_commit_id
            ),
            object_config_graph_package_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
        )
    )

    assert realizations == {}
    assert status == "realization_count_mismatch"


def test_meta_language_materialization_realization_persists_reuse_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    result = meta_service.ObjectConfigGraphPackageLeafMaterializationResult(
        aware_toml_path=leaf_result.aware_toml_path,
        package_branch_id=leaf_result.package_branch_id,
        code_package=leaf_result.code_package,
        source_manifest_kind="aware_toml",
        object_config_graph_package=leaf_result.object_config_graph_package,
        object_config_graph=leaf_result.object_config_graph,
        owned_file_paths=(),
        code_package_commit_id=None,
        code_package_head_commit_id=leaf_result.code_package_head_commit_id,
        code_package_object_instance_graph_commit_id=(
            leaf_result.code_package_object_instance_graph_commit_id
        ),
        object_config_graph_commit_id=None,
        object_config_graph_head_commit_id=(
            leaf_result.object_config_graph_head_commit_id
        ),
        object_config_graph_object_instance_graph_commit_id=(
            leaf_result.object_config_graph_object_instance_graph_commit_id
        ),
        object_config_graph_package_commit_id=None,
        object_config_graph_package_head_commit_id=(
            leaf_result.object_config_graph_package_head_commit_id
        ),
        object_config_graph_package_object_instance_graph_commit_id=(
            leaf_result.object_config_graph_package_object_instance_graph_commit_id
        ),
        phase_timings_s={},
        code_package_build_runtime_telemetry={},
        code_package_build_invoke_perf_ms={},
        code_package_upsert_runtime_telemetry={},
        code_package_upsert_invoke_perf_ms={},
        semantic_commit_strategy="fingerprint_reuse",
        semantic_commit_fallback_reset=False,
        semantic_commit_phase_timings_s={},
        materialization_index_receipt={
            "cache_key": {
                "source_manifest_hash": "source-hash",
                "dependency_signature": "dependency-signature",
            }
        },
    )
    observed: dict[str, object] = {}

    def _record_reuse_cache(**kwargs: object) -> None:
        observed["reuse_cache"] = kwargs

    def _record_projection_index(**kwargs: object) -> None:
        observed["projection_index"] = kwargs

    monkeypatch.setattr(
        meta_service,
        "_write_object_config_graph_package_reuse_cache",
        _record_reuse_cache,
    )
    monkeypatch.setattr(
        meta_service,
        "_record_runtime_package_projection_index",
        _record_projection_index,
    )

    persisted = (
        meta_service._persist_language_materialization_reuse_evidence(  # noqa: SLF001
            result=result,
            workspace_root=tmp_path,
        )
    )

    reuse_cache = cast(dict[str, object], observed["reuse_cache"])
    projection_index = cast(dict[str, object], observed["projection_index"])
    assert reuse_cache["result"] is result
    assert reuse_cache["source_manifest_hash"] == "source-hash"
    assert reuse_cache["dependency_signature"] == "dependency-signature"
    assert projection_index["result"] is result
    assert projection_index["workspace_root"] == tmp_path
    assert (
        persisted.phase_timings_s[
            "persist_language_materialization_reuse_evidence.write_reuse_cache"
        ]
        >= 0.0
    )
    assert (
        persisted.phase_timings_s[
            "persist_language_materialization_reuse_evidence.record_projection_index"
        ]
        >= 0.0
    )


def test_meta_workspace_language_reuse_evidence_covers_context_owned_targets(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    package = leaf_result.object_config_graph_package
    materialized_package = package.language_materializations[0].materialized_packages[0]
    ontology_ref = _generated_code_package_ref(
        leaf_result=leaf_result,
        code_package_id=materialized_package.code_package_id,
        package_name="aware-demo-ontology",
        package_root=materialized_package.package_root,
    )
    runtime_ref = {
        **ontology_ref,
        "declared_code_package_id": str(uuid4()),
        "code_package_id": str(uuid4()),
        "code_package_commit_id": str(uuid4()),
        "code_package_head_commit_id": str(uuid4()),
        "code_package_object_instance_graph_commit_id": str(uuid4()),
        "declared_package_name": "aware-demo",
        "package_name": "aware-demo",
        "materialization_source": "runtime_handlers",
        "renderer_profile": None,
        "renderer_kind": "runtime_handlers_meta",
    }
    leaf_result.materialization_index_receipt = (
        meta_service._materialization_index_receipt_with_realization(  # noqa: SLF001
            receipt={},
            object_config_graph_package_id=package.id,
            object_config_graph_package_head_commit_id=(
                leaf_result.object_config_graph_package_head_commit_id
            ),
            object_config_graph_package_object_instance_graph_commit_id=(
                leaf_result.object_config_graph_package_object_instance_graph_commit_id
            ),
            realization_count=2,
            generated_code_package_refs=(ontology_ref, runtime_ref),
        )
    )
    request = _request(
        tmp_path,
        targets=(
            _target(
                materialization_source="ontology",
                import_root="aware_demo_ontology",
                output_root="modules/demo/structure/ontology/python",
                renderer_profile="orm_runtime",
            ),
            _target(
                materialization_source="runtime_handlers",
                import_root="aware_demo",
                output_root="modules/demo/runtime/aware_demo",
                renderer_kind="runtime_handlers_meta",
                source_is_runtime=True,
                code_package_surface="runtime",
            ),
        ),
    )

    evidence = workspace_provider.object_config_graph_package_language_reuse_evidence(
        request=request,
        leaf_result=leaf_result,
    )

    assert evidence["status"] == "complete"
    assert evidence["reason"] == "workspace_language_targets_realized"
    assert evidence["target_count"] == 2
    assert evidence["package_count"] == 2
    materialized_rows = cast(
        tuple[dict[str, object], ...],
        evidence["materialized_language_packages"],
    )
    assert {row["code_package_id"] for row in materialized_rows} == {
        ontology_ref["code_package_id"],
        runtime_ref["code_package_id"],
    }


def test_meta_workspace_materialize_compile_parity_reports_missing_roles(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    request = _request(
        tmp_path,
        targets=(
            _target(
                materialization_source="runtime_handlers",
                import_root="aware_demo",
                output_root="modules/demo/runtime/aware_demo",
                renderer_kind="runtime_handlers_meta",
                source_is_runtime=True,
                code_package_surface="runtime",
            ),
        ),
    )

    receipt = workspace_provider._leaf_compile_parity_receipts(  # noqa: SLF001
        request=request,
        leaf_result=leaf_result,
        lifecycle_receipts=({"schema": "lifecycle"},),
        materialization_index_receipts=(
            {
                "receipt_kind": ("object_config_graph_package_materialization_index"),
            },
        ),
        artifact_ownership_receipts=(
            _artifact_receipt(
                output_key="language_materialization_lifecycle_receipt",
                artifact_role="lifecycle_receipt",
            ),
            _artifact_receipt(
                output_key="language_package",
                artifact_role="package",
                package_name="aware-demo",
            ),
            _artifact_receipt(
                output_key="generated_language_files",
                artifact_role="source_code",
            ),
        ),
        post_step_receipts=_post_step_receipts(
            tmp_path,
            (("runtime_handlers", "modules/demo/runtime/aware_demo"),),
        ),
    )[0]

    assert receipt["status"] == "incomplete"
    assert receipt["missing_required_artifact_roles"] == (
        "meta_runtime_handler_provider",
    )
    assert receipt["env_artifacts_required"] is False


def test_meta_workspace_materialize_compile_parity_requires_post_steps(
    tmp_path: Path,
) -> None:
    leaf_result = _leaf_result(tmp_path)
    request = _request(
        tmp_path,
        targets=(
            _target(
                materialization_source="runtime_handlers",
                import_root="aware_demo",
                output_root="modules/demo/runtime/aware_demo",
                renderer_kind="runtime_handlers_meta",
                source_is_runtime=True,
                code_package_surface="runtime",
            ),
        ),
    )

    receipt = workspace_provider._leaf_compile_parity_receipts(  # noqa: SLF001
        request=request,
        leaf_result=leaf_result,
        lifecycle_receipts=({"schema": "lifecycle"},),
        materialization_index_receipts=(
            {
                "receipt_kind": ("object_config_graph_package_materialization_index"),
            },
        ),
        artifact_ownership_receipts=_complete_artifact_receipts(),
    )[0]

    assert receipt["status"] == "incomplete"
    missing = cast(
        tuple[dict[str, object], ...],
        receipt["missing_required_post_step_tools"],
    )
    assert missing[0]["tool_id"] == "python.format.black"
    assert missing[0]["materialization_source"] == "runtime_handlers"


def _request(
    workspace_root: Path,
    *,
    targets: tuple[dict[str, object], ...],
) -> object:
    return SimpleNamespace(
        workspace_root=workspace_root,
        context={
            SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY: targets,
        },
    )


def _target(
    *,
    materialization_source: str,
    import_root: str,
    output_root: str,
    renderer_profile: str | None = None,
    renderer_kind: str | None = None,
    source_is_runtime: bool = False,
    code_package_surface: str = "structure",
    stable_ids_ownership: str | None = None,
    stable_ids_resolution_policy: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "target_language_plugin_id": "python",
        "output_root": output_root,
        "import_root": import_root,
        "package_name": import_root.replace("_", "-"),
        "materialization_source": materialization_source,
        "code_package_surface": code_package_surface,
        "source_is_runtime": source_is_runtime,
    }
    if renderer_profile is not None:
        payload["renderer_profile"] = renderer_profile
    if renderer_kind is not None:
        payload["renderer_kind"] = renderer_kind
    if stable_ids_ownership is not None:
        payload["stable_ids_ownership"] = stable_ids_ownership
    if stable_ids_resolution_policy is not None:
        payload["stable_ids_resolution_policy"] = stable_ids_resolution_policy
    return payload


def _leaf_result(tmp_path: Path) -> object:
    aware_toml_path = (
        tmp_path / "modules" / "demo" / "structure" / "ontology" / "aware.toml"
    )
    materialized_code_package_id = uuid4()
    materialized_code_package_oig_commit_id = uuid4()
    return SimpleNamespace(
        aware_toml_path=aware_toml_path,
        package_branch_id=uuid4(),
        code_package=SimpleNamespace(
            id=uuid4(),
            package_root="modules/demo/structure/ontology",
            sources_root="modules/demo/structure/ontology/aware",
        ),
        code_package_head_commit_id=uuid4(),
        code_package_object_instance_graph_commit_id=uuid4(),
        object_config_graph=SimpleNamespace(id=uuid4()),
        object_config_graph_head_commit_id=uuid4(),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
        object_config_graph_package=SimpleNamespace(
            id=uuid4(),
            package_name="demo-ontology",
            fqn_prefix="aware_demo",
            language_materializations=(
                SimpleNamespace(
                    id=uuid4(),
                    target_key="demo-ontology:ontology",
                    language="python",
                    output_dir="modules/demo/structure/ontology/python",
                    import_root="aware_demo_ontology",
                    package_name="aware-demo-ontology",
                    materialization_source="ontology",
                    renderer_profile="orm_runtime",
                    renderer_kind=None,
                    materialized_packages=(
                        SimpleNamespace(
                            code_package_id=materialized_code_package_id,
                            package_output_key="language_package",
                            package_name="aware-demo-ontology",
                            language="python",
                            output_dir="modules/demo/structure/ontology/python",
                            package_root="modules/demo/structure/ontology/python",
                            sources_root="aware_demo_ontology",
                            import_root="aware_demo_ontology",
                            materialization_source="ontology",
                            renderer_kind=None,
                            renderer_profile="orm_runtime",
                            object_config_graph_object_instance_graph_commit_id=uuid4(),
                            code_package_object_instance_graph_commit_id=(
                                materialized_code_package_oig_commit_id
                            ),
                            status="materialized",
                        ),
                    ),
                ),
            ),
        ),
        object_config_graph_package_object_instance_graph_commit_id=uuid4(),
        object_config_graph_package_head_commit_id=uuid4(),
        semantic_commit_strategy="fingerprint_reuse",
        semantic_commit_fallback_reset=False,
    )


def _generated_code_package_ref(
    *,
    leaf_result: object,
    code_package_id: UUID,
    package_name: str,
    package_root: str,
) -> dict[str, object]:
    return {
        "schema": "aware.meta.language_materialization.code_package_ref.v1",
        "target_language_plugin_id": "python",
        "materialization_source": "ontology",
        "renderer_profile": "orm_runtime",
        "renderer_kind": None,
        "object_config_graph_package_id": str(
            leaf_result.object_config_graph_package.id
        ),
        "declared_package_name": package_name,
        "object_config_graph_object_instance_graph_commit_id": str(
            leaf_result.object_config_graph_object_instance_graph_commit_id
        ),
        "code_package_id": str(code_package_id),
        "code_package_branch_id": str(uuid4()),
        "code_package_commit_id": str(uuid4()),
        "code_package_head_commit_id": str(uuid4()),
        "code_package_object_instance_graph_commit_id": str(uuid4()),
        "package_name": package_name,
        "package_root": package_root,
        "sources_root": "aware_demo_ontology",
        "code_package_surface": "structure",
        "code_package_config_key": "python.structure",
        "code_package_config_id": str(uuid4()),
        "manifest_kind": "pyproject_toml",
        "manifest_relative_path": f"{package_root}/pyproject.toml",
        "path_count": 4,
    }


def _complete_artifact_receipts() -> tuple[dict[str, object], ...]:
    return (
        _artifact_receipt(
            output_key="language_materialization_lifecycle_receipt",
            artifact_role="lifecycle_receipt",
        ),
        _artifact_receipt(
            output_key="language_package",
            artifact_role="package",
            package_name="aware-demo-ontology",
        ),
        _artifact_receipt(
            output_key="generated_language_files",
            artifact_role="source_code",
        ),
        _artifact_receipt(
            output_key="python.models_manifest",
            artifact_role="runtime_model_index",
        ),
        _artifact_receipt(
            output_key="python.orm_graph_binding",
            artifact_role="runtime_binding_snapshot",
        ),
        _artifact_receipt(
            output_key="python.bootstrap_manifest",
            artifact_role="package_bootstrap",
        ),
        _artifact_receipt(
            output_key="python.ocg_node_paths",
            artifact_role="dependency_import_resolution",
        ),
        _artifact_receipt(
            output_key="python.meta_runtime_handlers_provider",
            artifact_role="meta_runtime_handler_provider",
        ),
    )


def _artifact_receipt(
    *,
    output_key: str,
    artifact_role: str,
    package_name: str | None = None,
) -> dict[str, object]:
    artifact_key = f"python:{output_key}:{uuid4()}"
    return {
        "producer_provider_key": "aware_meta",
        "semantic_owner": "aware_meta.object_config_graph",
        "producer_key": ("aware_meta.object_config_graph.language_materialization"),
        "output_key": output_key,
        "artifact_key": artifact_key,
        "artifact_family": "ocg_language_materialization",
        "artifact_role": artifact_role,
        "output_kind": "generated_file",
        "target_language_plugin_id": "python",
        "status": "available",
        "package_name": package_name,
        "source_code_package_id": str(UUID(int=1)),
    }


def _post_step_receipts(
    workspace_root: Path,
    targets: tuple[tuple[str, str], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "schema": ("aware.meta.language_materialization.post_step_receipt.v1"),
            "tool_id": "python.format.black",
            "target_language_plugin_id": "python",
            "status": "succeeded",
            "backend": "python_api",
            "role": "formatter",
            "output_root": (workspace_root / output_root).resolve().as_posix(),
            "package_name": "aware-demo",
            "materialization_source": materialization_source,
            "source": "default",
            "target_count": 1,
            "changed_path_count": 0,
        }
        for materialization_source, output_root in targets
    )
