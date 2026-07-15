from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from aware_service_runtime.builder import (
    build_service_compile_plan,
    emit_service_compile_plan_artifact,
)
from aware_service_runtime.compile import compile_service_workspace
from aware_service_runtime.implementation_package import (
    ActivatedServicePackageBinding,
    PreparedServicePackageBinding,
    resolve_prepared_service_api_receipt_policy,
)
from aware_service_runtime.workspace import ServiceWorkspace
from aware_service_ontology.service.service_enums import ServiceOperationReceiptPolicy


def _write_service_toml(
    root: Path,
    *,
    service_ontology_mode: bool = False,
    include_host_activation_inputs: bool = False,
) -> Path:
    toml_path = root / "aware.service.toml"
    lines = [
        "aware_service = 1",
        "",
        "[service]",
        'package_name = "home-story-service"',
        'fqn_prefix = "aware_home_story_service"',
        "",
        "[build]",
        'sources_dir = "services/bindings"',
        'include_paths = ["**/*.aware"]',
    ]
    if service_ontology_mode:
        lines.append('compilation_mode = "service_ontology"')
    if include_host_activation_inputs:
        lines.extend(
            [
                "",
                "[host]",
                'service_surface = "service"',
                'activation_mode = "materialize_and_load_committed"',
                "materialize_on_start = true",
                "",
                "[[dependencies]]",
                'package_name = "home-story-api"',
                "version_number = 7",
                'kind = "api_service_protocol"',
            ]
        )
    _ = toml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return toml_path


def _write_service_source(root: Path) -> None:
    bindings = root / "services" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "home.services.aware").write_text(
        "\n".join(
            [
                "service home_story {",
                "    api home_story_api;",
                "    experience home_story;",
                "",
                "    operation open_door {",
                "        endpoint home_story_api.door.open;",
                "        price {",
                "            coin USD;",
                "            type fixed;",
                "            fixed_amount 2.5;",
                '            effective_from "2026-04-21T00:00:00Z";',
                "",
                "            policy {",
                "                fail_closed true;",
                "            }",
                "        }",
                "    }",
                "",
                "    operation status {",
                "        endpoint home_story_api.status.status;",
                "        receipt read_model;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_compile_service_workspace_returns_snapshot_only_for_raw_xor(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_service_toml(root)
    _write_service_source(root)

    result = compile_service_workspace(toml_path=toml_path, repo_root=root)

    assert result.snapshot.spec.service.package_name == "home-story-service"
    assert result.snapshot.source_files == (
        Path("services/bindings/home.services.aware"),
    )
    assert result.compile_plan is None
    assert result.compile_plan_artifact is None


def test_build_service_compile_plan_and_emit_artifact(tmp_path: Path) -> None:
    root = tmp_path
    toml_path = _write_service_toml(root, service_ontology_mode=True)
    _write_service_source(root)

    snapshot = ServiceWorkspace.from_toml(
        toml_path=toml_path, repo_root=root
    ).build_snapshot()
    plan = build_service_compile_plan(snapshot=snapshot)

    assert plan.schema_version == 1
    assert plan.package_name == "home-story-service"
    assert plan.fqn_prefix == "aware_home_story_service"
    assert plan.source_files == ("services/bindings/home.services.aware",)
    assert len(plan.service_ownership) == 1
    assert plan.service_ownership[0].name == "home_story"
    assert plan.service_configs[0].apis[0].api_ref == "home_story_api"
    assert plan.service_ownership[0].experiences[0].experience_ref == "home_story"
    assert plan.service_configs[0].experiences[0].experience_ref == "home_story"
    assert plan.service_configs[0].service_operation_configs[0].price is not None
    assert (
        plan.service_configs[0].service_operation_configs[0].admission_mode
        == "contract_required"
    )
    assert (
        plan.service_configs[0].service_operation_configs[0].price.coin_symbol == "USD"
    )
    assert plan.service_configs[0].service_operation_configs[
        0
    ].price.fixed_amount == Decimal("2.5")
    assert plan.service_configs[0].service_operation_configs[0].api_endpoints[
        0
    ].endpoint_ref == ("home_story_api.door.open")
    status_operation = next(
        operation
        for operation in plan.service_configs[0].service_operation_configs
        if operation.name == "status"
    )
    assert status_operation.admission_mode == "public_read"
    assert status_operation.receipt_policy == "read_model"

    artifact = emit_service_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=(root / "runtime"),
        repo_root=root,
    )

    assert artifact.path.exists()
    assert artifact.relpath == "runtime/service.compile_plan.json"
    assert len(artifact.hash_sha256) == 64
    payload = artifact.path.read_text(encoding="utf-8")
    assert '"service_ownership"' in payload
    assert '"service_configs"' in payload
    assert '"experience_ref": "home_story"' in payload
    assert '"coin_symbol": "USD"' in payload
    assert '"fixed_amount": "2.5"' in payload
    assert '"home_story_api.door.open"' in payload
    assert '"receipt_policy": "read_model"' in payload
    assert '"admission_mode": "public_read"' in payload


def test_compile_service_workspace_emits_plan_for_service_ontology(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_service_toml(
        root,
        service_ontology_mode=True,
        include_host_activation_inputs=True,
    )
    _write_service_source(root)

    result = compile_service_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
    )

    assert result.compile_plan is not None
    assert result.compile_plan_artifact is not None
    assert result.activation_plan is not None
    assert result.activation_plan_artifact is not None
    assert (
        result.compile_plan_artifact.relpath
        == ".aware/service/runtime/home-story-service/service.compile_plan.json"
    )
    assert result.activation_plan_artifact.relpath == (
        ".aware/service/runtime/home-story-service/service.activation_plan.json"
    )
    payload = result.compile_plan_artifact.path.read_text(encoding="utf-8")
    assert '"api_ref": "home_story_api"' in payload
    activation_payload = result.activation_plan_artifact.path.read_text(
        encoding="utf-8"
    )
    assert '"activation_mode": "materialize_and_load_committed"' in activation_payload
    assert '"service_surface": "service"' in activation_payload
    assert '"expected_hash_sha256"' not in activation_payload


def test_prepared_service_api_receipt_policy_uses_compile_plan_truth(
    tmp_path: Path,
) -> None:
    root = tmp_path
    toml_path = _write_service_toml(
        root,
        service_ontology_mode=True,
        include_host_activation_inputs=True,
    )
    _write_service_source(root)

    result = compile_service_workspace(
        toml_path=toml_path,
        repo_root=root,
        emit_compile_plan=True,
    )
    prepared = PreparedServicePackageBinding(
        compile_result=result,
        compile_plan_artifact_hash_sha256="sha256:test",
        dependencies=(),
        service_bindings={},
        service_endpoint_refs={},
        service_stream_endpoint_refs={},
        endpoint_dependencies={},
    )
    activated = ActivatedServicePackageBinding(
        prepared=prepared,
        service_ids_by_name={},
        service_subscriptions_by_name={},
        api_reference_branch_ids_by_api_name={},
    )

    assert (
        resolve_prepared_service_api_receipt_policy(
            activated=activated,
            service_name="home_story",
            endpoint_ref="home_story_api.status.status",
        )
        is ServiceOperationReceiptPolicy.read_model
    )
    assert (
        resolve_prepared_service_api_receipt_policy(
            activated=activated,
            service_name="home_story",
            endpoint_ref="home_story_api.door.open",
        )
        is ServiceOperationReceiptPolicy.committed
    )


def test_ontology_persistence_readiness_uses_preboot_receipt_policy(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    toml_path = _write_service_toml(repo_root, service_ontology_mode=True)
    _write_service_source(repo_root)
    result = compile_service_workspace(
        toml_path=toml_path,
        repo_root=repo_root,
        emit_compile_plan=True,
    )
    assert result.compile_plan is not None
    service_config = result.compile_plan.service_configs[0]
    ensure_ready = next(
        operation
        for operation in service_config.service_operation_configs
        if operation.name == "status"
    )

    assert ensure_ready.admission_mode == "public_read"
    assert ensure_ready.receipt_policy == "read_model"


def test_compile_home_story_sample_service_plan_includes_experience_attachment(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    toml_path = _write_service_toml(workspace_root, service_ontology_mode=True)
    _write_service_source(workspace_root)

    result = compile_service_workspace(
        toml_path=toml_path,
        repo_root=workspace_root,
        emit_compile_plan=True,
    )

    assert result.compile_plan is not None
    assert (
        result.compile_plan.service_ownership[0].experiences[0].experience_ref
        == "home_story"
    )
    assert (
        result.compile_plan.service_configs[0].experiences[0].experience_ref
        == "home_story"
    )
