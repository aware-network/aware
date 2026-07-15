from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_api_runtime.dependencies.runtime_resolution import (
    RuntimeImportActivationPlan as APIRuntimeImportActivationPlan,
)
from aware_api_runtime.dependencies.runtime_resolution import (
    RuntimeManifestResolution as APIRuntimeManifestResolution,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_service_runtime import runtime_resolution as service_runtime_resolution

_PROTOCOL_DEPENDENCY_PAYLOADS_BY_SERVICE_TOML: dict[
    Path,
    tuple[dict[str, object], ...],
] = {}


def _record_protocol_dependency(
    *,
    service_toml: Path,
    package_name: str,
    service_protocol_plan_hash_sha256: str,
) -> None:
    _PROTOCOL_DEPENDENCY_PAYLOADS_BY_SERVICE_TOML[service_toml.resolve()] = (
        {
            "package_name": package_name,
            "kind": "api_service_protocol",
            **_protocol_lock_coordinates(package_name),
            "service_protocol_plan_hash_sha256": (service_protocol_plan_hash_sha256),
        },
    )


def _resolve_service_protocol_runtime_manifest(**kwargs: object):
    toml_paths = tuple(
        Path(path).resolve()
        for path in kwargs.get("toml_paths", ())  # type: ignore[arg-type]
    )
    dependency_payloads = tuple(
        dependency
        for toml_path in toml_paths
        for dependency in _PROTOCOL_DEPENDENCY_PAYLOADS_BY_SERVICE_TOML.get(
            toml_path,
            (),
        )
    )
    return service_runtime_resolution.resolve_service_protocol_runtime_manifest(
        **kwargs,
        dependency_payloads=dependency_payloads,
    )


def _write_empty_db_schema_registry(manifest_path: Path) -> None:
    (manifest_path.parent / "db.schema.registry.json").write_text(
        json.dumps(
            {
                "schema_registry_version": 1,
                "environment_id": "00000000-0000-0000-0000-000000000001",
                "entries": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_service_toml_with_api_service_protocol_dependency(
    *,
    workspace_root: Path,
    service_key: str,
    api_package_name: str,
) -> Path:
    api_runtime_dir = workspace_root / ".aware" / "api" / "runtime" / api_package_name
    api_runtime_dir.mkdir(parents=True)
    api_toml = workspace_root / "apis" / service_key / "aware.api.toml"
    api_toml.parent.mkdir(parents=True)
    api_toml.write_text("aware_api = 1\n", encoding="utf-8")
    (api_runtime_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_toml_path": f"apis/{service_key}/aware.api.toml",
                "api_toml_relpath": f"apis/{service_key}/aware.api.toml",
                "api_package_name": api_package_name,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (api_runtime_dir / "api.compile_plan.json").write_text(
        json.dumps({"package_name": api_package_name}, sort_keys=True),
        encoding="utf-8",
    )
    service_protocol_plan = {"apis": [], "package_name": api_package_name}
    service_protocol_plan_path = api_runtime_dir / "api.service_protocol_plan.json"
    service_protocol_plan_path.write_text(
        json.dumps(service_protocol_plan, sort_keys=True),
        encoding="utf-8",
    )
    expected_hash = sha256(
        json.dumps(
            service_protocol_plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    service_toml = workspace_root / "services" / service_key / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    service_toml.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                f'package_name = "aware-{service_key}-service"',
                f'fqn_prefix = "aware_{service_key}_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "service_ontology"',
                "",
                "[[dependencies]]",
                f'package_name = "{api_package_name}"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _record_protocol_dependency(
        service_toml=service_toml,
        package_name=api_package_name,
        service_protocol_plan_hash_sha256=expected_hash,
    )
    return service_toml


def _write_service_toml_for_api_service_protocol_hash(
    *,
    workspace_root: Path,
    service_key: str,
    api_package_name: str,
    expected_hash: str,
) -> Path:
    service_toml = workspace_root / "services" / service_key / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    service_toml.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                f'package_name = "aware-{service_key}-service"',
                f'fqn_prefix = "aware_{service_key}_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "service_ontology"',
                "",
                "[[dependencies]]",
                f'package_name = "{api_package_name}"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _record_protocol_dependency(
        service_toml=service_toml,
        package_name=api_package_name,
        service_protocol_plan_hash_sha256=expected_hash,
    )
    return service_toml


def _write_api_service_protocol_runtime_artifacts(
    *,
    workspace_root: Path,
    service_key: str,
    api_package_name: str,
    python_root: Path,
    runtime_root: Path,
    aware_toml_path: Path,
) -> str:
    api_runtime_dir = workspace_root / ".aware" / "api" / "runtime" / api_package_name
    api_runtime_dir.mkdir(parents=True)
    api_toml = workspace_root / "apis" / service_key / "aware.api.toml"
    api_toml.parent.mkdir(parents=True)
    api_toml.write_text("aware_api = 1\n", encoding="utf-8")
    aware_toml_path.parent.mkdir(parents=True, exist_ok=True)
    aware_toml_path.write_text("aware = 1\n", encoding="utf-8")
    python_root.mkdir(parents=True, exist_ok=True)
    runtime_root.mkdir(parents=True, exist_ok=True)
    (api_runtime_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_toml_path": api_toml.relative_to(workspace_root).as_posix(),
                "api_toml_relpath": api_toml.relative_to(workspace_root).as_posix(),
                "api_package_name": api_package_name,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (api_runtime_dir / "api.compile_plan.json").write_text(
        json.dumps({"package_name": api_package_name}, sort_keys=True),
        encoding="utf-8",
    )
    service_protocol_plan = {"apis": [], "package_name": api_package_name}
    (api_runtime_dir / "api.service_protocol_plan.json").write_text(
        json.dumps(service_protocol_plan, sort_keys=True),
        encoding="utf-8",
    )
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=api_runtime_dir,
        repo_root=workspace_root,
        api_toml_relpath=api_toml.relative_to(workspace_root).as_posix(),
        package_name=api_package_name,
        dependency_packages=[
            {
                "package_name": "proof-ontology",
                "kind": "ontology",
                "aware_toml_relpath": aware_toml_path.relative_to(
                    workspace_root
                ).as_posix(),
                "package_root_relpath": aware_toml_path.parent.relative_to(
                    workspace_root
                ).as_posix(),
                "python_root_relpath": python_root.relative_to(
                    workspace_root
                ).as_posix(),
                "runtime_root_relpath": runtime_root.relative_to(
                    workspace_root
                ).as_posix(),
            }
        ],
    )
    return sha256(
        json.dumps(
            service_protocol_plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _write_api_runtime_semantics_artifact(
    *,
    api_runtime_dir: Path,
    repo_root: Path,
    api_toml_relpath: str,
    package_name: str,
    dependency_packages: list[dict[str, object]],
    registered_class_config_count: int = 1,
) -> Path:
    path = api_runtime_dir / "api.runtime_semantics.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "api.runtime_semantics",
                "api_package_name": package_name,
                "api_fqn_prefix": package_name.replace("-", "_"),
                "api_toml_relpath": api_toml_relpath,
                "api_package_root_relpath": str(Path(api_toml_relpath).parent),
                "accessible_dependency_graphs_relpath": (
                    f".aware/api/runtime/{package_name}/"
                    "api.accessible_dependency_graphs.json"
                ),
                "dependency_packages": dependency_packages,
                "registered_class_config_count": registered_class_config_count,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _ = repo_root
    return path


def test_service_protocol_api_reference_lane_inputs_are_typed_per_api() -> None:
    payload = {
        "package_name": "combo-service-api",
        "api_ontology": [
            {
                "api": {
                    "name": "workspace",
                    "source_path": "apis/workspace/bindings/workspace.apis.aware",
                },
                "capability_endpoint_request_configs": [
                    {
                        "api_name": "workspace",
                        "capability_name": "status",
                        "endpoint_name": "status",
                        "class_ref": "aware_workspace.StatusRequest",
                        "source_path": "apis/workspace/bindings/workspace.apis.aware",
                    }
                ],
                "capability_endpoint_functions": [
                    {
                        "api_name": "workspace",
                        "capability_name": "status",
                        "endpoint_name": "status",
                        "name": "read",
                        "graph_target": "workspace",
                        "graph_capability_function_name": "read_status",
                        "source_path": "apis/workspace/bindings/workspace.apis.aware",
                    }
                ],
                "graph_projections": [
                    {
                        "api_name": "workspace",
                        "graph_target": "workspace",
                        "target": "aware_workspace.status",
                        "source_path": "apis/workspace/bindings/workspace.apis.aware",
                    }
                ],
            },
            {
                "api": {
                    "name": "agent",
                    "source_path": "apis/agent/bindings/agent.apis.aware",
                },
                "capability_endpoint_request_configs": [
                    {
                        "api_name": "agent",
                        "capability_name": "session",
                        "endpoint_name": "start",
                        "class_ref": "aware_agent.StartSessionRequest",
                        "source_path": "apis/agent/bindings/agent.apis.aware",
                    }
                ],
            },
        ],
    }

    references = service_runtime_resolution.split_service_protocol_api_reference_lane_inputs(
        (
            service_runtime_resolution.ServiceProtocolApiReferenceMaterializationInput(
                package_name="combo-service-api",
                api_toml_path=Path("aware.api.toml"),
                api_compile_plan_path=Path("api.compile_plan.json"),
                compile_plan_payload=payload,
                accessible_graphs=(),
            ),
        )
    )

    assert [reference.api_name for reference in references] == ["agent", "workspace"]
    assert all(
        len(reference.compile_plan_payload["api_ontology"]) == 1
        for reference in references
    )
    assert references[0].endpoint_refs == frozenset({"agent.session.start"})
    assert references[0].projection_refs == frozenset()
    assert references[0].endpoint_function_refs == frozenset()
    assert references[1].projection_refs == frozenset({"aware_workspace.status"})
    assert references[1].endpoint_refs == frozenset({"workspace.status.status"})
    assert references[1].endpoint_function_refs == frozenset(
        {"workspace.status.status.read"}
    )


def test_service_protocol_api_reference_lane_identity_uses_graph_hash_metadata() -> (
    None
):
    payload = {
        "package_name": "workspace-service-api",
        "api_ontology": [
            {
                "api": {
                    "name": "workspace",
                    "source_path": "apis/workspace/bindings/workspace.apis.aware",
                }
            }
        ],
    }

    reference = service_runtime_resolution.split_service_protocol_api_reference_lane_inputs(
        (
            service_runtime_resolution.ServiceProtocolApiReferenceMaterializationInput(
                package_name="workspace-service-api",
                api_toml_path=Path("aware.api.toml"),
                api_compile_plan_path=Path("api.compile_plan.json"),
                compile_plan_payload=payload,
                accessible_graphs=(),
                accessible_graphs_hash="artifact-hash-proof",
            ),
        )
    )[
        0
    ]

    assert reference.branch_key.endswith("graphs:artifact-hash-proof")
    assert reference.accessible_graphs == ()


def test_service_protocol_runtime_resolution_uses_pinned_api_manifest(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    _ = (repo_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "proof"\n',
        encoding="utf-8",
    )
    service_toml = repo_root / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)

    api_runtime_dir = repo_root / ".aware" / "api" / "runtime" / "proof-service-api"
    api_runtime_dir.mkdir(parents=True)
    api_toml = repo_root / "apis" / "proof" / "aware.api.toml"
    api_toml.parent.mkdir(parents=True)
    api_toml.write_text("aware_api = 1\n", encoding="utf-8")
    (api_runtime_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_toml_path": api_toml.as_posix(),
                "api_package_name": "proof-service-api",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (api_runtime_dir / "api.compile_plan.json").write_text(
        json.dumps({"package_name": "proof-service-api"}, sort_keys=True),
        encoding="utf-8",
    )
    service_protocol_plan = {"apis": [], "package_name": "proof-service-api"}
    service_protocol_plan_path = api_runtime_dir / "api.service_protocol_plan.json"
    service_protocol_plan_path.write_text(
        json.dumps(service_protocol_plan, sort_keys=True),
        encoding="utf-8",
    )
    expected_hash = sha256(
        json.dumps(
            service_protocol_plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    service_toml.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "proof-service"',
                'fqn_prefix = "proof_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "service_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-service-api"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _record_protocol_dependency(
        service_toml=service_toml,
        package_name="proof-service-api",
        service_protocol_plan_hash_sha256=expected_hash,
    )

    api_python = repo_root / "api-python"
    api_python.mkdir()
    api_runtime = repo_root / "api-runtime"
    api_runtime.mkdir()
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=api_runtime_dir,
        repo_root=repo_root,
        api_toml_relpath="apis/proof/aware.api.toml",
        package_name="proof-service-api",
        dependency_packages=[
            {
                "package_name": "proof-ontology",
                "kind": "ontology",
                "aware_toml_relpath": "apis/proof/aware.api.toml",
                "package_root_relpath": "apis/proof",
                "python_root_relpath": api_python.as_posix(),
                "runtime_root_relpath": api_runtime.as_posix(),
            }
        ],
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        repo_root=repo_root,
        kernel_repo_root=repo_root,
    )

    assert result is not None
    assert result.manifest_path.exists()
    source_descriptor = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert source_descriptor["schema"] == "aware.service_protocol.runtime_sources.v1"
    assert source_descriptor["source"] == "ontology_runtime_artifacts"
    assert source_descriptor["runtime_bundle_manifest_paths"] == []
    assert result.runtime_resolution.module_manifest_paths == ()
    assert result.runtime_resolution.runtime_bundle_manifest_paths == ()
    assert result.runtime_resolution.environment_config_id is not None
    assert result.runtime_resolution.python_roots == (api_python.resolve(),)
    assert result.cache_status == "miss"
    assert result.cache_metadata_path is not None
    assert result.cache_metadata_path.is_file()
    assert tuple(item.package_name for item in result.api_dependencies) == (
        "proof-service-api",
    )

    cached = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        repo_root=repo_root,
        kernel_repo_root=repo_root,
    )

    assert cached is not None
    assert cached.cache_status == "hit"
    assert cached.cache_reason == "cache_valid"
    assert cached.runtime_resolution.module_manifest_paths == ()
    assert cached.runtime_resolution.runtime_bundle_manifest_paths == ()
    assert cached.runtime_resolution.python_roots == (api_python.resolve(),)
    assert cached.runtime_resolution.import_activation.roots == (
        api_python.resolve(),
        api_runtime.resolve(),
    )

    _write_api_runtime_semantics_artifact(
        api_runtime_dir=api_runtime_dir,
        repo_root=repo_root,
        api_toml_relpath="apis/proof/aware.api.toml",
        package_name="proof-service-api",
        dependency_packages=[
            {
                "package_name": "proof-ontology",
                "kind": "ontology",
                "aware_toml_relpath": "apis/proof/aware.api.toml",
                "package_root_relpath": "apis/proof",
                "python_root_relpath": api_python.as_posix(),
                "runtime_root_relpath": api_runtime.as_posix(),
            }
        ],
        registered_class_config_count=2,
    )
    refreshed = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        repo_root=repo_root,
        kernel_repo_root=repo_root,
    )

    assert refreshed is not None
    assert refreshed.cache_status == "miss"
    assert refreshed.cache_reason == "cache_key_mismatch"
    assert refreshed.runtime_resolution.import_activation.roots == (
        api_python.resolve(),
        api_runtime.resolve(),
    )


def test_service_protocol_runtime_resolution_loads_api_runtime_semantics_artifact(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    _ = (repo_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "proof"\n',
        encoding="utf-8",
    )
    service_toml = _write_service_toml_with_api_service_protocol_dependency(
        workspace_root=repo_root,
        service_key="proof",
        api_package_name="proof-service-api",
    )
    api_runtime_dir = repo_root / ".aware" / "api" / "runtime" / "proof-service-api"
    api_python = repo_root / "modules" / "proof" / "structure" / "ontology" / "python"
    api_runtime = repo_root / "modules" / "proof" / "runtime"
    api_python.mkdir(parents=True)
    api_runtime.mkdir(parents=True)
    (api_runtime_dir / "api.runtime_semantics.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "api.runtime_semantics",
                "api_package_name": "proof-service-api",
                "api_fqn_prefix": "proof_service_api",
                "api_toml_relpath": "apis/proof/aware.api.toml",
                "api_package_root_relpath": "apis/proof",
                "accessible_dependency_graphs_relpath": (
                    ".aware/api/runtime/proof-service-api/"
                    "api.accessible_dependency_graphs.json"
                ),
                "dependency_packages": [
                    {
                        "package_name": "proof-ontology",
                        "kind": "ontology",
                        "aware_toml_relpath": (
                            "modules/proof/structure/ontology/aware.toml"
                        ),
                        "package_root_relpath": ("modules/proof/structure/ontology"),
                        "python_root_relpath": (
                            "modules/proof/structure/ontology/python"
                        ),
                        "runtime_root_relpath": "modules/proof/runtime",
                    }
                ],
                "registered_class_config_count": 1,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        repo_root=repo_root,
        kernel_repo_root=repo_root,
    )

    assert result is not None
    assert result.cache_status == "miss"
    assert result.runtime_resolution.python_roots == (api_python.resolve(),)
    assert result.runtime_resolution.import_activation.roots == (
        api_python.resolve(),
        api_runtime.resolve(),
    )
    assert result.cache_metadata_path is not None
    cache_payload = json.loads(result.cache_metadata_path.read_text(encoding="utf-8"))
    assert (
        cache_payload["cache_key"]["api_runtime_resolutions"][0]["manifest_path"][
            "path"
        ]
        == (api_runtime_dir / "api.runtime_semantics.json").resolve().as_posix()
    )


def test_service_protocol_runtime_resolution_fails_without_api_runtime_semantics(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    (repo_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "proof"\n',
        encoding="utf-8",
    )
    service_toml = _write_service_toml_with_api_service_protocol_dependency(
        workspace_root=repo_root,
        service_key="proof",
        api_package_name="proof-service-api",
    )

    try:
        _resolve_service_protocol_runtime_manifest(
            toml_paths=(service_toml,),
            repo_root=repo_root,
            kernel_repo_root=repo_root,
        )
    except service_runtime_resolution.RuntimeRequirementsError as exc:
        assert "requires a prepared api.runtime_semantics.json artifact" in str(exc)
        assert "runtime_semantics_missing" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected missing API runtime semantics failure")


def test_service_protocol_runtime_resolution_requires_declared_root_context(
    tmp_path: Path,
) -> None:
    service_toml = tmp_path / "loose" / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    service_toml.write_text("aware_service = 1\n", encoding="utf-8")

    try:
        _resolve_service_protocol_runtime_manifest(
            toml_paths=(service_toml,),
            kernel_repo_root=tmp_path,
        )
    except service_runtime_resolution.RuntimeRequirementsError as exc:
        message = str(exc)
        assert "requires an explicit repo_root" in message
        assert "Repository-root discovery fallback is retired" in message
    else:  # pragma: no cover
        raise AssertionError("Expected missing Service runtime root-context failure")


def test_service_protocol_runtime_resolution_without_kernel_root_stays_in_workspace(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "aware_network"
    workspace_root.mkdir()
    (workspace_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "aware_network"\n',
        encoding="utf-8",
    )
    service_toml = _write_service_toml_with_api_service_protocol_dependency(
        workspace_root=workspace_root,
        service_key="proof",
        api_package_name="proof-service-api",
    )
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=(
            workspace_root / ".aware" / "api" / "runtime" / "proof-service-api"
        ),
        repo_root=workspace_root,
        api_toml_relpath="apis/proof/aware.api.toml",
        package_name="proof-service-api",
        dependency_packages=[],
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        use_cache=False,
    )

    assert result is not None
    assert result.manifest_path.is_relative_to(
        workspace_root / ".aware" / "service" / "runtime"
    )
    assert result.api_dependencies[0].repo_root == workspace_root.resolve()
    assert result.runtime_resolution.runtime_bundle_manifest_paths == ()


def test_service_protocol_runtime_resolution_uses_kernel_root_for_api_dependency(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspaces" / "aware_network"
    kernel_root = tmp_path / "workspaces" / "aware_kernel"
    workspace_root.mkdir(parents=True)
    kernel_root.mkdir(parents=True)
    (workspace_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "aware_network"\n',
        encoding="utf-8",
    )
    (kernel_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "aware_kernel"\n',
        encoding="utf-8",
    )
    expected_hash = _write_api_service_protocol_runtime_artifacts(
        workspace_root=kernel_root,
        service_key="ontology",
        api_package_name="ontology-service-api",
        python_root=kernel_root
        / "modules"
        / "ontology"
        / "apis"
        / "ontology"
        / "python",
        runtime_root=kernel_root / "modules" / "ontology" / "runtime" / "python",
        aware_toml_path=kernel_root
        / "modules"
        / "ontology"
        / "ontology"
        / "aware.ontology.toml",
    )
    service_toml = _write_service_toml_for_api_service_protocol_hash(
        workspace_root=workspace_root,
        service_key="ontology",
        api_package_name="ontology-service-api",
        expected_hash=expected_hash,
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        repo_root=workspace_root,
        kernel_repo_root=kernel_root,
        output_path=workspace_root
        / ".aware"
        / "service"
        / "runtime"
        / "ontology-service-runtime.json",
        use_cache=False,
    )

    assert result is not None
    assert result.cache_status == "disabled"
    assert len(result.api_dependencies) == 1
    dependency = result.api_dependencies[0]
    assert dependency.package_name == "ontology-service-api"
    assert dependency.repo_root == kernel_root.resolve()
    assert dependency.api_manifest_path.is_relative_to(kernel_root.resolve())
    assert result.runtime_resolution.python_roots == (
        (
            kernel_root / "modules" / "ontology" / "apis" / "ontology" / "python"
        ).resolve(),
    )


def test_service_protocol_runtime_resolution_uses_revision_runtime_semantics_without_source_api_toml(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspaces" / "aware_network"
    kernel_source_root = tmp_path / "checkouts" / "aware_kernel"
    kernel_revision_root = (
        tmp_path
        / "workspaces"
        / "aware_kernel"
        / ".aware"
        / "workspace"
        / "revision-filesystem-roots"
        / "proof"
        / "deployment-1"
    )
    workspace_root.mkdir(parents=True)
    kernel_source_root.mkdir(parents=True)
    kernel_revision_root.mkdir(parents=True)
    (workspace_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "aware_network"\n',
        encoding="utf-8",
    )
    revision_manifest = (
        kernel_revision_root
        / ".aware"
        / "workspace"
        / "revision-filesystem.manifest.json"
    )
    revision_manifest.parent.mkdir(parents=True)
    revision_manifest.write_text("{}", encoding="utf-8")

    api_runtime_dir = (
        kernel_revision_root / ".aware" / "api" / "runtime" / "ontology-service-api"
    )
    api_runtime_dir.mkdir(parents=True)
    source_api_toml = (
        kernel_source_root
        / "modules"
        / "ontology"
        / "apis"
        / "ontology"
        / "aware.api.toml"
    )
    source_api_toml.parent.mkdir(parents=True)
    source_api_toml.write_text("aware_api = 1\n", encoding="utf-8")
    api_toml_relpath = "modules/ontology/apis/ontology/aware.api.toml"
    (api_runtime_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_toml_path": source_api_toml.as_posix(),
                "api_toml_relpath": api_toml_relpath,
                "api_package_name": "ontology-service-api",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (api_runtime_dir / "api.compile_plan.json").write_text(
        json.dumps({"package_name": "ontology-service-api"}, sort_keys=True),
        encoding="utf-8",
    )
    service_protocol_plan = {"apis": [], "package_name": "ontology-service-api"}
    service_protocol_plan_path = api_runtime_dir / "api.service_protocol_plan.json"
    service_protocol_plan_path.write_text(
        json.dumps(service_protocol_plan, sort_keys=True),
        encoding="utf-8",
    )
    expected_hash = sha256(
        json.dumps(
            service_protocol_plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    python_root = (
        kernel_revision_root / "modules" / "ontology" / "apis" / "ontology" / "python"
    )
    runtime_root = kernel_revision_root / "modules" / "ontology" / "runtime" / "python"
    aware_toml = (
        kernel_revision_root
        / "modules"
        / "ontology"
        / "ontology"
        / "aware.ontology.toml"
    )
    python_root.mkdir(parents=True)
    runtime_root.mkdir(parents=True)
    aware_toml.parent.mkdir(parents=True)
    aware_toml.write_text("aware_ontology = 1\n", encoding="utf-8")
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=api_runtime_dir,
        repo_root=kernel_revision_root,
        api_toml_relpath=api_toml_relpath,
        package_name="ontology-service-api",
        dependency_packages=[
            {
                "package_name": "ontology-ontology",
                "kind": "ontology",
                "aware_toml_relpath": aware_toml.relative_to(
                    kernel_revision_root
                ).as_posix(),
                "package_root_relpath": aware_toml.parent.relative_to(
                    kernel_revision_root
                ).as_posix(),
                "python_root_relpath": python_root.relative_to(
                    kernel_revision_root
                ).as_posix(),
                "runtime_root_relpath": runtime_root.relative_to(
                    kernel_revision_root
                ).as_posix(),
            }
        ],
    )
    assert not (kernel_revision_root / api_toml_relpath).exists()
    service_toml = _write_service_toml_for_api_service_protocol_hash(
        workspace_root=workspace_root,
        service_key="ontology",
        api_package_name="ontology-service-api",
        expected_hash=expected_hash,
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        repo_root=workspace_root,
        kernel_repo_root=kernel_revision_root,
        use_cache=False,
    )

    assert result is not None
    assert result.api_dependencies[0].repo_root == kernel_revision_root.resolve()
    assert result.api_dependencies[0].api_toml_relpath == api_toml_relpath
    assert result.runtime_resolution.python_roots == (python_root.resolve(),)
    assert result.runtime_resolution.import_activation.roots == (
        python_root.resolve(),
        runtime_root.resolve(),
    )


def test_service_protocol_api_reference_inputs_use_declared_workspace_dependency_root(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspaces" / "aware_network"
    dependency_root = tmp_path / "workspaces" / "aware_kernel"
    workspace_root.mkdir(parents=True)
    dependency_root.mkdir(parents=True)
    (dependency_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "aware_kernel"\n',
        encoding="utf-8",
    )
    (workspace_root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "[workspace]",
                'handle = "aware_network"',
                "",
                "[[workspace.dependencies]]",
                'id = "aware_kernel"',
                'kind = "workspace"',
                'source = "workspace://aware_kernel"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    runtime_dir = _write_api_runtime_dependency_artifacts(
        dependency_root,
        package_name="proof-service-api",
        write_accessible_graphs=True,
    )
    api_toml_path = dependency_root / "source-not-present" / "aware.api.toml"
    api_toml_path.parent.mkdir(parents=True)
    api_toml_path.write_text("aware_api = 1\n", encoding="utf-8")
    expected_hash = _hash_json_file(runtime_dir / "api.service_protocol_plan.json")
    service_toml = workspace_root / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    service_toml.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-proof-service"',
                'fqn_prefix = "aware_proof_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "service_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-service-api"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    inputs = service_runtime_resolution.load_service_protocol_api_reference_materialization_inputs_from_dependencies(
        dependencies=(
            {
                "package_name": "proof-service-api",
                "kind": "api_service_protocol",
                **_protocol_lock_coordinates("proof-service-api"),
                "service_protocol_plan_hash_sha256": expected_hash,
            },
        ),
        repo_root=workspace_root,
    )

    assert len(inputs) == 1
    assert inputs[0].package_name == "proof-service-api"
    assert inputs[0].api_compile_plan_path.is_relative_to(dependency_root)
    assert [graph.name for graph in inputs[0].accessible_graphs] == ["home-api"]


def test_service_protocol_runtime_resolution_rejects_retired_core_selector(
    tmp_path: Path,
) -> None:
    service_toml = tmp_path / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    service_toml.write_text("aware_service = 1\n", encoding="utf-8")

    with pytest.raises(TypeError, match="unexpected keyword"):
        _resolve_service_protocol_runtime_manifest(
            toml_paths=(service_toml,),
            repo_root=tmp_path,
            kernel_repo_root=tmp_path,
            **{"core_" + "module_ids": ("api",)},
        )


def test_service_protocol_runtime_resolution_rejects_escaped_runtime_semantics_paths(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    kernel_root = tmp_path / "kernel"
    workspace_root.mkdir()
    kernel_root.mkdir()
    (workspace_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "proof"\n',
        encoding="utf-8",
    )
    service_toml = _write_service_toml_with_api_service_protocol_dependency(
        workspace_root=workspace_root,
        service_key="proof",
        api_package_name="proof-service-api",
    )
    api_runtime_dir = (
        workspace_root / ".aware" / "api" / "runtime" / "proof-service-api"
    )
    leaked_root = tmp_path / "targets" / "public" / "aware" / "modules" / "proof"
    leaked_python = leaked_root / "structure" / "ontology" / "python"
    leaked_runtime = leaked_root / "runtime"
    leaked_aware = leaked_root / "structure" / "ontology" / "aware.toml"
    leaked_python.mkdir(parents=True)
    leaked_runtime.mkdir(parents=True)
    leaked_aware.parent.mkdir(parents=True, exist_ok=True)
    leaked_aware.write_text("aware = 1\n", encoding="utf-8")
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=api_runtime_dir,
        repo_root=workspace_root,
        api_toml_relpath="apis/proof/aware.api.toml",
        package_name="proof-service-api",
        dependency_packages=[
            {
                "package_name": "proof-ontology",
                "kind": "ontology",
                "aware_toml_relpath": leaked_aware.as_posix(),
                "package_root_relpath": leaked_aware.parent.as_posix(),
                "python_root_relpath": leaked_python.as_posix(),
                "runtime_root_relpath": leaked_runtime.as_posix(),
            }
        ],
    )

    try:
        _resolve_service_protocol_runtime_manifest(
            toml_paths=(service_toml,),
            repo_root=workspace_root,
            kernel_repo_root=kernel_root,
        )
    except service_runtime_resolution.RuntimeRequirementsError as exc:
        message = str(exc)
        assert "escapes declared service runtime authority" in message
        assert "targets/public/aware" in message
    else:  # pragma: no cover
        raise AssertionError("Expected escaped API runtime semantics path failure")


def test_service_protocol_runtime_resolution_allows_declared_workspace_dependency_root(
    tmp_path: Path,
) -> None:
    checkout_root = tmp_path / "checkout"
    workspace_root = checkout_root / "workspaces" / "product"
    dependency_root = checkout_root / "workspaces" / "kernel_support"
    workspace_root.mkdir(parents=True)
    dependency_root.mkdir(parents=True)
    (dependency_root / "aware.workspace.toml").write_text(
        'aware = 1\n[workspace]\nhandle = "kernel_support"\n',
        encoding="utf-8",
    )
    (workspace_root / "aware.workspace.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "product"',
                "",
                "[[workspace.dependencies]]",
                'id = "kernel_support"',
                'kind = "workspace"',
                'source = "workspace://kernel_support"',
                'channel = "local"',
                'revision = "workspace-revision:local"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    service_toml = _write_service_toml_with_api_service_protocol_dependency(
        workspace_root=workspace_root,
        service_key="proof",
        api_package_name="proof-service-api",
    )
    api_runtime_dir = (
        workspace_root / ".aware" / "api" / "runtime" / "proof-service-api"
    )
    dependency_python = (
        dependency_root / "modules" / "support" / "ontology" / "structure" / "python"
    )
    dependency_runtime = dependency_root / "modules" / "support" / "runtime"
    dependency_aware = (
        dependency_root
        / "modules"
        / "support"
        / "ontology"
        / "structure"
        / "aware.toml"
    )
    dependency_python.mkdir(parents=True)
    dependency_runtime.mkdir(parents=True)
    dependency_aware.parent.mkdir(parents=True, exist_ok=True)
    dependency_aware.write_text("aware = 1\n", encoding="utf-8")
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=api_runtime_dir,
        repo_root=workspace_root,
        api_toml_relpath="apis/proof/aware.api.toml",
        package_name="proof-service-api",
        dependency_packages=[
            {
                "package_name": "support-ontology",
                "kind": "ontology",
                "aware_toml_relpath": dependency_aware.as_posix(),
                "package_root_relpath": dependency_aware.parent.as_posix(),
                "python_root_relpath": dependency_python.as_posix(),
                "runtime_root_relpath": dependency_runtime.as_posix(),
            }
        ],
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        repo_root=workspace_root,
        kernel_repo_root=checkout_root,
        use_cache=False,
    )

    assert result is not None
    assert result.runtime_resolution.python_roots == (dependency_python.resolve(),)
    assert result.runtime_resolution.import_activation.roots == (
        dependency_python.resolve(),
        dependency_runtime.resolve(),
    )


def test_service_runtime_resolution_has_no_structure_topology_import() -> None:
    source = Path(service_runtime_resolution.__file__).read_text(encoding="utf-8")

    assert "aware_structure.topology" not in source
    assert "load_aware_workspace_modules" not in source
    assert "aware_kernel" not in source


def test_service_protocol_runtime_resolution_uses_each_service_workspace_root(
    tmp_path: Path,
) -> None:
    kernel_root = tmp_path / "kernel"
    agent_root = tmp_path / "aware_agent"
    goal_root = tmp_path / "aware_coordination"
    for workspace_root, handle in (
        (kernel_root, "aware_kernel"),
        (agent_root, "aware_agent"),
        (goal_root, "aware_coordination"),
    ):
        workspace_root.mkdir()
        (workspace_root / "aware.workspace.toml").write_text(
            f'aware = 1\n[workspace]\nhandle = "{handle}"\n',
            encoding="utf-8",
        )

    agent_service_toml = _write_service_toml_with_api_service_protocol_dependency(
        workspace_root=agent_root,
        service_key="agent",
        api_package_name="agent-service-api",
    )
    goal_service_toml = _write_service_toml_with_api_service_protocol_dependency(
        workspace_root=goal_root,
        service_key="goal",
        api_package_name="goal-service-api",
    )
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=agent_root / ".aware" / "api" / "runtime" / "agent-service-api",
        repo_root=agent_root,
        api_toml_relpath="apis/agent/aware.api.toml",
        package_name="agent-service-api",
        dependency_packages=[],
    )
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=goal_root / ".aware" / "api" / "runtime" / "goal-service-api",
        repo_root=goal_root,
        api_toml_relpath="apis/goal/aware.api.toml",
        package_name="goal-service-api",
        dependency_packages=[],
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(agent_service_toml, goal_service_toml),
        kernel_repo_root=kernel_root,
        use_cache=False,
    )

    assert result is not None
    assert {
        dependency.package_name: dependency.repo_root
        for dependency in result.api_dependencies
    } == {
        "agent-service-api": agent_root.resolve(),
        "goal-service-api": goal_root.resolve(),
    }
    assert result.runtime_resolution.runtime_bundle_manifest_paths == ()
    assert result.runtime_resolution.import_activation.roots == ()


def test_service_protocol_runtime_cache_rejects_stale_db_schema_registry(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "environment.manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    sql_root = tmp_path / "sql"
    sql_root.mkdir()
    (sql_root / "001.sql").write_text("select 1;\n", encoding="utf-8")
    (tmp_path / "db.schema.registry.json").write_text(
        json.dumps(
            {
                "schema_registry_version": 1,
                "environment_id": "00000000-0000-0000-0000-000000000001",
                "entries": [
                    {
                        "package_kind": "ontology",
                        "backend_targets": ["postgres"],
                        "sql_root": sql_root.as_posix(),
                        "source_hash": "sha256:stale",
                        "source_label": "proof-ontology",
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    reason = service_runtime_resolution._cached_db_schema_registry_invalid_reason(
        manifest_path=manifest_path
    )

    assert reason == "db_schema_registry_source_hash_mismatch:proof-ontology"


def test_service_protocol_runtime_cache_key_tracks_api_runtime_resolution(
    tmp_path: Path,
) -> None:
    service_toml = tmp_path / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    service_toml.write_text("aware_service = 1\n", encoding="utf-8")
    api_manifest_path = (
        tmp_path / ".aware" / "api" / "runtime" / "proof" / "api.manifest.json"
    )
    api_manifest_path.parent.mkdir(parents=True)
    api_toml_path = tmp_path / "apis" / "proof" / "aware.api.toml"
    api_toml_path.parent.mkdir(parents=True)
    service_protocol_plan_path = api_manifest_path.with_name(
        "api.service_protocol_plan.json"
    )
    api_compile_plan_path = api_manifest_path.with_name("api.compile_plan.json")
    for path in (
        api_manifest_path,
        api_toml_path,
        service_protocol_plan_path,
        api_compile_plan_path,
    ):
        path.write_text("{}", encoding="utf-8")
    dependency = service_runtime_resolution.ServiceProtocolApiDependencyRuntime(
        package_name="proof-service-api",
        repo_root=tmp_path,
        api_manifest_path=api_manifest_path,
        api_toml_path=api_toml_path,
        service_protocol_plan_path=service_protocol_plan_path,
        service_protocol_plan_hash_sha256="0" * 64,
        api_compile_plan_path=api_compile_plan_path,
    )
    api_runtime_manifest = tmp_path / "api-runtime.environment.manifest.json"
    api_python_root = tmp_path / "api-python"
    api_runtime_manifest.write_text('{"version": 1}', encoding="utf-8")
    api_python_root.mkdir()
    api_resolution = APIRuntimeManifestResolution(
        manifest_path=api_runtime_manifest,
        module_ids=(),
        module_manifest_paths=(),
        python_roots=(api_python_root,),
        import_activation=APIRuntimeImportActivationPlan(roots=(api_python_root,)),
        environment_handle="workspace-api",
    )

    key_before = service_runtime_resolution._service_protocol_runtime_cache_key(
        toml_paths=(service_toml,),
        repo_root=tmp_path,
        kernel_repo_root=tmp_path,
        manifest_repo_root=tmp_path,
        dependencies=(dependency,),
        api_resolutions=(api_resolution,),
    )
    assert "core_" + "module_ids" not in key_before
    assert "core_" + "runtime_resolution" not in key_before
    assert (
        key_before["api_runtime_resolutions"][0]["runtime_bundle_manifest_paths"] == []
    )
    assert key_before["api_runtime_resolutions"][0]["environment_config_id"] is None
    api_runtime_manifest.write_text('{"version": 2}', encoding="utf-8")
    key_after = service_runtime_resolution._service_protocol_runtime_cache_key(
        toml_paths=(service_toml,),
        repo_root=tmp_path,
        kernel_repo_root=tmp_path,
        manifest_repo_root=tmp_path,
        dependencies=(dependency,),
        api_resolutions=(api_resolution,),
    )

    assert key_before != key_after


def test_service_protocol_runtime_cache_key_tracks_plan_file_bytes(
    tmp_path: Path,
) -> None:
    service_toml = tmp_path / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    service_toml.write_text("aware_service = 1\n", encoding="utf-8")
    api_manifest_path = (
        tmp_path / ".aware" / "api" / "runtime" / "proof" / "api.manifest.json"
    )
    api_manifest_path.parent.mkdir(parents=True)
    api_toml_path = tmp_path / "apis" / "proof" / "aware.api.toml"
    api_toml_path.parent.mkdir(parents=True)
    service_protocol_plan_path = api_manifest_path.with_name(
        "api.service_protocol_plan.json"
    )
    api_compile_plan_path = api_manifest_path.with_name("api.compile_plan.json")
    for path in (
        api_manifest_path,
        api_toml_path,
        api_compile_plan_path,
    ):
        path.write_text("{}", encoding="utf-8")
    service_protocol_plan_path.write_text(
        json.dumps({"apis": [], "package_name": "proof"}, indent=2),
        encoding="utf-8",
    )
    dependency = service_runtime_resolution.ServiceProtocolApiDependencyRuntime(
        package_name="proof-service-api",
        repo_root=tmp_path,
        api_manifest_path=api_manifest_path,
        api_toml_path=api_toml_path,
        service_protocol_plan_path=service_protocol_plan_path,
        service_protocol_plan_hash_sha256="0" * 64,
        api_compile_plan_path=api_compile_plan_path,
    )
    key_before = service_runtime_resolution._service_protocol_runtime_cache_key(
        toml_paths=(service_toml,),
        repo_root=tmp_path,
        kernel_repo_root=tmp_path,
        manifest_repo_root=tmp_path,
        dependencies=(dependency,),
        api_resolutions=(),
    )
    service_protocol_plan_path.write_text(
        json.dumps({"apis": [], "package_name": "proof"}, sort_keys=True),
        encoding="utf-8",
    )
    key_after = service_runtime_resolution._service_protocol_runtime_cache_key(
        toml_paths=(service_toml,),
        repo_root=tmp_path,
        kernel_repo_root=tmp_path,
        manifest_repo_root=tmp_path,
        dependencies=(dependency,),
        api_resolutions=(),
    )

    assert key_before != key_after


def test_service_protocol_runtime_resolution_rejects_pin_mismatch(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    service_toml = repo_root / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)
    api_runtime_dir = repo_root / ".aware" / "api" / "runtime" / "proof-service-api"
    api_runtime_dir.mkdir(parents=True)
    api_toml = repo_root / "apis" / "proof" / "aware.api.toml"
    api_toml.parent.mkdir(parents=True)
    api_toml.write_text("aware_api = 1\n", encoding="utf-8")
    (api_runtime_dir / "api.manifest.json").write_text(
        json.dumps({"api_toml_path": api_toml.as_posix()}),
        encoding="utf-8",
    )
    (api_runtime_dir / "api.compile_plan.json").write_text("{}", encoding="utf-8")
    (api_runtime_dir / "api.service_protocol_plan.json").write_text(
        json.dumps({"package_name": "proof-service-api"}),
        encoding="utf-8",
    )
    service_toml.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "proof-service"',
                'fqn_prefix = "proof_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "service_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-service-api"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _record_protocol_dependency(
        service_toml=service_toml,
        package_name="proof-service-api",
        service_protocol_plan_hash_sha256="0" * 64,
    )

    try:
        _resolve_service_protocol_runtime_manifest(
            toml_paths=(service_toml,),
            repo_root=repo_root,
            kernel_repo_root=repo_root,
        )
    except RuntimeError as exc:
        assert "pin mismatch" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected pin mismatch")


def test_service_protocol_runtime_resolution_uses_revision_filesystem_root(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision-root"
    revision_manifest_path = (
        revision_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    )
    revision_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    revision_manifest_path.write_text("{}", encoding="utf-8")
    service_toml = revision_root / "services" / "proof" / "aware.service.toml"
    service_toml.parent.mkdir(parents=True)

    api_runtime_dir = revision_root / ".aware" / "api" / "runtime" / "proof-service-api"
    api_runtime_dir.mkdir(parents=True)
    api_toml = revision_root / "apis" / "proof" / "aware.api.toml"
    api_toml.parent.mkdir(parents=True)
    api_toml.write_text("aware_api = 1\n", encoding="utf-8")
    (api_runtime_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_toml_path": "apis/proof/aware.api.toml",
                "api_package_name": "proof-service-api",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (api_runtime_dir / "api.compile_plan.json").write_text(
        json.dumps({"package_name": "proof-service-api"}, sort_keys=True),
        encoding="utf-8",
    )
    service_protocol_plan = {"apis": [], "package_name": "proof-service-api"}
    service_protocol_plan_path = api_runtime_dir / "api.service_protocol_plan.json"
    service_protocol_plan_path.write_text(
        json.dumps(service_protocol_plan, sort_keys=True),
        encoding="utf-8",
    )
    expected_hash = sha256(
        json.dumps(
            service_protocol_plan,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    service_toml.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "proof-service"',
                'fqn_prefix = "proof_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'compilation_mode = "service_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-service-api"',
                'kind = "api_service_protocol"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _record_protocol_dependency(
        service_toml=service_toml,
        package_name="proof-service-api",
        service_protocol_plan_hash_sha256=expected_hash,
    )
    _write_api_runtime_semantics_artifact(
        api_runtime_dir=api_runtime_dir,
        repo_root=revision_root,
        api_toml_relpath="apis/proof/aware.api.toml",
        package_name="proof-service-api",
        dependency_packages=[],
    )

    result = _resolve_service_protocol_runtime_manifest(
        toml_paths=(service_toml,),
        kernel_repo_root=tmp_path,
    )

    assert result is not None
    assert result.manifest_path.is_relative_to(
        tmp_path / ".aware" / "service" / "runtime"
    )
    assert result.runtime_resolution.runtime_bundle_manifest_paths == ()
    assert result.api_dependencies[0].repo_root == revision_root.resolve()


def test_committed_service_protocol_api_reference_inputs_use_runtime_graph_artifact(
    tmp_path: Path,
) -> None:
    runtime_dir = _write_api_runtime_dependency_artifacts(
        tmp_path,
        package_name="proof-service-api",
        write_accessible_graphs=True,
    )
    dependency = _api_service_protocol_dependency_payload(
        package_name="proof-service-api",
        service_protocol_plan_hash_sha256=_hash_json_file(
            runtime_dir / "api.service_protocol_plan.json"
        ),
    )

    inputs = service_runtime_resolution.load_service_protocol_api_reference_materialization_inputs_from_dependencies(
        dependencies=(dependency,),
        repo_root=tmp_path,
    )

    assert len(inputs) == 1
    assert inputs[0].package_name == "proof-service-api"
    assert [graph.name for graph in inputs[0].accessible_graphs] == ["home-api"]
    assert inputs[0].accessible_graphs_hash == _hash_json_file(
        runtime_dir / "api.accessible_dependency_graphs.json"
    )


def test_committed_service_protocol_api_reference_inputs_use_declared_dependency_root(
    tmp_path: Path,
) -> None:
    primary_root = tmp_path / "network-revision"
    dependency_root = tmp_path / "kernel-revision"
    primary_root.mkdir()
    runtime_dir = _write_api_runtime_dependency_artifacts(
        dependency_root,
        package_name="proof-service-api",
        write_accessible_graphs=True,
    )
    dependency = _api_service_protocol_dependency_payload(
        package_name="proof-service-api",
        service_protocol_plan_hash_sha256=_hash_json_file(
            runtime_dir / "api.service_protocol_plan.json"
        ),
    )

    inputs = service_runtime_resolution.load_service_protocol_api_reference_materialization_inputs_from_dependencies(
        dependencies=(dependency,),
        repo_root=primary_root,
        additional_repo_roots=(dependency_root,),
    )

    assert len(inputs) == 1
    assert inputs[0].package_name == "proof-service-api"
    assert [graph.name for graph in inputs[0].accessible_graphs] == ["home-api"]


def test_committed_service_protocol_api_reference_inputs_can_skip_runtime_graph_hydration(
    tmp_path: Path,
) -> None:
    runtime_dir = _write_api_runtime_dependency_artifacts(
        tmp_path,
        package_name="proof-service-api",
        write_accessible_graphs=True,
    )
    dependency = _api_service_protocol_dependency_payload(
        package_name="proof-service-api",
        service_protocol_plan_hash_sha256=_hash_json_file(
            runtime_dir / "api.service_protocol_plan.json"
        ),
    )

    inputs = service_runtime_resolution.load_service_protocol_api_reference_materialization_inputs_from_dependencies(
        dependencies=(dependency,),
        repo_root=tmp_path,
        hydrate_accessible_graphs=False,
    )

    assert len(inputs) == 1
    assert inputs[0].package_name == "proof-service-api"
    assert inputs[0].accessible_graphs == ()
    assert inputs[0].accessible_graphs_hash == _hash_json_file(
        runtime_dir / "api.accessible_dependency_graphs.json"
    )


def test_committed_service_protocol_api_reference_inputs_fail_without_graph_artifact(
    tmp_path: Path,
) -> None:
    runtime_dir = _write_api_runtime_dependency_artifacts(
        tmp_path,
        package_name="proof-service-api",
        write_accessible_graphs=False,
    )
    dependency = _api_service_protocol_dependency_payload(
        package_name="proof-service-api",
        service_protocol_plan_hash_sha256=_hash_json_file(
            runtime_dir / "api.service_protocol_plan.json"
        ),
    )

    try:
        service_runtime_resolution.load_service_protocol_api_reference_materialization_inputs_from_dependencies(
            dependencies=(dependency,),
            repo_root=tmp_path,
        )
    except FileNotFoundError as exc:
        assert "accessible dependency graph artifact is missing" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected missing accessible graph artifact failure")


def _write_api_runtime_dependency_artifacts(
    root: Path,
    *,
    package_name: str,
    write_accessible_graphs: bool,
) -> Path:
    runtime_dir = root / ".aware" / "api" / "runtime" / package_name
    runtime_dir.mkdir(parents=True)
    missing_api_toml = root / "source-not-present" / "aware.api.toml"
    (runtime_dir / "api.manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "api_toml_path": missing_api_toml.as_posix(),
                "api_package_name": package_name,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (runtime_dir / "api.compile_plan.json").write_text(
        json.dumps(
            {
                "schema_version": 9,
                "package_name": package_name,
                "api_ontology": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (runtime_dir / "api.service_protocol_plan.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": package_name,
                "apis": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    if write_accessible_graphs:
        graph = ObjectConfigGraph(
            name="home-api",
            hash="sha256:test-home-api",
            fqn_prefix="aware_home_api",
            language=CodeLanguage.aware,
        )
        (runtime_dir / "api.accessible_dependency_graphs.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "graphs": [graph.model_dump(mode="json")],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    return runtime_dir


def _api_service_protocol_dependency_payload(
    *,
    package_name: str,
    service_protocol_plan_hash_sha256: str,
) -> dict[str, object]:
    return {
        "package_name": package_name,
        "kind": "api_service_protocol",
        **_protocol_lock_coordinates(package_name),
        "service_protocol_plan_hash_sha256": service_protocol_plan_hash_sha256,
    }


def _protocol_lock_coordinates(package_name: str) -> dict[str, object]:
    return {
        field_name: str(uuid5(NAMESPACE_URL, f"test:{package_name}:{field_name}"))
        for field_name in (
            "service_package_provided_api_package_id",
            "api_package_id",
            "api_package_object_instance_graph_commit_id",
            "service_protocol_package_id",
            "service_protocol_code_package_id",
            "service_protocol_code_package_object_instance_graph_commit_id",
        )
    }


def _hash_json_file(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
