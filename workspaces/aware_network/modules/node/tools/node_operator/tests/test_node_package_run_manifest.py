from __future__ import annotations

import json
from pathlib import Path
import stat
import sys
import tempfile
import tomllib
from uuid import NAMESPACE_URL, uuid5

import msgpack
import pytest

from aware_node_operator import direct_interface_local, node_package_run_manifest
from aware_node_operator.node_package_run_manifest import (
    NodePackageEnvironmentProfileMount,
    NodeOntologyLocalBootstrapRequest,
    NodePackageEnvironmentTarget,
    NodePackageOntologyTarget,
    NodePackageRunManifestRequest,
    NodePackageRuntimeSource,
    NodePackageServiceCodePackage,
    NodePackageServiceTarget,
    node_package_runtime_source_from_workspace_deployment_payload,
    prepare_node_ontology_local_bootstrap,
    prepare_node_package_run_manifest,
)
from aware_node_operator.service_host_refs import (
    ServiceHostImplementationPackageRefInput,
)
from aware_service_runtime.service_api_dependency_routes import (
    ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY,
    ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "aware.repo.toml").is_file():
            return parent
    raise RuntimeError("Could not resolve repository root")


REPO_ROOT = _repo_root()


def _seed_runtime_manifest(repo_root: Path) -> Path:
    path = (
        repo_root / ".aware" / "environment" / "runtime" / "environment.manifest.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"environment": {"id": "a4204ee7-4d24-5072-bdf8-41a0f0b43068"}})
        + "\n",
        encoding="utf-8",
    )
    return path.resolve()


def _seed_ontology_runtime_manifest(
    repo_root: Path,
    *,
    package_name: str = "environment-ontology",
    fqn_prefix: str = "aware_environment",
    module_name: str = "environment",
    projection_name: str = "Environment",
    projection_hash: str = "environment.projection",
    class_name: str | None = None,
    function_names: tuple[str, ...] = ("build",),
    constructor_function_name: str = "build",
) -> Path:
    ontology_toml_path = repo_root / "modules" / module_name / "aware.ontology.toml"
    source_manifest_path = (
        repo_root / "modules" / module_name / "structure" / "ontology" / "aware.toml"
    )
    runtime_dir = source_manifest_path.parent / ".aware" / "ontology" / "runtime"
    opg_dir = runtime_dir / "opgs"
    opg_dir.mkdir(parents=True, exist_ok=True)
    source_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    ontology_toml_path.parent.mkdir(parents=True, exist_ok=True)
    ontology_toml_path.write_text(
        "\n".join(
            [
                "aware_ontology = 1",
                "",
                "[ontology]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                'source_manifest = "structure/ontology/aware.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    source_manifest_path.write_text("aware = 1\n", encoding="utf-8")

    ocg_id = str(uuid5(NAMESPACE_URL, f"{package_name}:ocg"))
    opg_id = str(uuid5(NAMESPACE_URL, f"{package_name}:{projection_name}:opg"))
    ocg_hash = f"sha256:{module_name}-ocg"
    root_node_id = str(uuid5(NAMESPACE_URL, f"{package_name}:{projection_name}:root"))
    class_config_id = str(
        uuid5(NAMESPACE_URL, f"{package_name}:{projection_name}:class")
    )
    resolved_class_name = class_name or projection_name
    function_specs = tuple(
        (
            str(uuid5(NAMESPACE_URL, f"{package_name}:{projection_name}:{name}:edge")),
            str(
                uuid5(
                    NAMESPACE_URL,
                    f"{package_name}:{projection_name}:{name}:function",
                )
            ),
            name,
        )
        for name in function_names
    )
    constructor_edge_id = next(
        (
            edge_id
            for edge_id, _function_id, name in function_specs
            if name == constructor_function_name
        ),
        function_specs[0][0],
    )
    constructor_function_id = next(
        (
            function_id
            for _edge_id, function_id, name in function_specs
            if name == constructor_function_name
        ),
        function_specs[0][1],
    )
    (runtime_dir / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(
            {
                "object_config_graph_nodes": [
                    {
                        "id": root_node_id,
                        "class_config": {
                            "id": class_config_id,
                            "name": resolved_class_name,
                            "class_fqn": (
                                f"{fqn_prefix}.default.{resolved_class_name}"
                            ),
                            "class_config_function_configs": [
                                {
                                    "id": edge_id,
                                    "function_config": {
                                        "id": function_id,
                                        "name": name,
                                        "description": (
                                            f"{resolved_class_name}.{name}"
                                        ),
                                        "kind": (
                                            "constructor"
                                            if function_id == constructor_function_id
                                            else "method"
                                        ),
                                    },
                                }
                                for edge_id, function_id, name in function_specs
                            ],
                        },
                    }
                ]
            },
            use_bin_type=True,
        )
    )
    (opg_dir / f"{projection_hash}.json").write_text(
        json.dumps(
            {
                "id": opg_id,
                "name": projection_name,
                "projection_hash": projection_hash,
                "object_config_graph_id": ocg_id,
                "supports_virtual_build": True,
                "object_projection_graph_nodes": [
                    {
                        "id": root_node_id,
                        "class_config_id": class_config_id,
                        "is_root": True,
                    }
                ],
                "object_projection_graph_constructors": [
                    {
                        "function_constructor_id": constructor_edge_id,
                        "root_node_id": root_node_id,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest_path = runtime_dir / "ontology.runtime.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "environment": {
                    "id": ocg_id,
                    "title": "Environment",
                    "canonical_language": "aware",
                },
                "ocg": {
                    "canonical_id": ocg_id,
                    "hash": ocg_hash,
                    "snapshot": "ocg.snapshot.msgpack",
                },
                "opg_index": {
                    "entries": [
                        {
                            "model": projection_name,
                            "projection_hash": projection_hash,
                            "file": f"opgs/{projection_hash}.json",
                        }
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    sql_root = source_manifest_path.parent / "sql"
    sql_root.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "db.schema.registry.json").write_text(
        json.dumps(
            {
                "schema_registry_version": 1,
                "environment_id": ocg_id,
                "entries": [
                    {
                        "backend_targets": ["postgres"],
                        "package_kind": "ontology",
                        "source_hash": "sha256:source",
                        "source_label": "ontology",
                        "sql_root": sql_root.as_posix(),
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest_path.resolve()


def test_workspace_deployment_payload_lowers_to_revision_runtime_source() -> None:
    payload = {
        "node_selection": {
            "selector_key": "kernel-services-node",
            "target_ref": "kernel-services-node",
            "node_config_id": "f0358d2d-ff54-4a49-8a65-88e64764d7ef",
            "package_selection": {
                "package_name": "kernel-services-node",
                "semantic_package_id": "3390bd4a-21af-48f1-b05d-d84842d6c6d2",
            },
        },
        "runtime_inputs": [
            {
                "runtime_kind": "service",
                "target_name": "aware-hub-service",
                "package_selection": {"package_name": "aware-hub-service"},
            },
            {
                "runtime_kind": "interface",
                "target_name": "aware-control-interface",
                "package_selection": {"package_name": "aware-control-interface"},
            },
        ],
    }

    source = node_package_runtime_source_from_workspace_deployment_payload(payload)

    assert source.source_kind == "workspace_revision"
    assert source.package_name == "kernel-services-node"
    assert source.config_name == "kernel-services-node"
    assert str(source.node_package_id) == "3390bd4a-21af-48f1-b05d-d84842d6c6d2"
    assert str(source.node_config_id) == "f0358d2d-ff54-4a49-8a65-88e64764d7ef"
    assert [target.service_name for target in source.service_targets] == [
        "aware-hub-service"
    ]
    assert [target.interface_name for target in source.interface_targets] == [
        "aware-control-interface"
    ]


def test_prepare_node_package_run_manifest_revision_mode_rejects_default_service_registry(
    tmp_path: Path,
) -> None:
    source = NodePackageRuntimeSource(
        package_name="kernel-services-node",
        config_name="kernel-services-node",
        source_kind="workspace_revision",
        service_targets=(NodePackageServiceTarget(service_name="aware_ontology"),),
    )

    with pytest.raises(RuntimeError, match="could not resolve Service targets"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=REPO_ROOT,
                workspace_root=REPO_ROOT,
                run_dir=tmp_path / "run",
                source=source,
                allow_default_service_toml_registry=False,
                require_live_runtime=False,
            )
        )


def _seed_service_toml(
    repo_root: Path,
    relpath: str,
    *,
    package_name: str,
    fqn_prefix: str,
    provided_api_package: str | None = None,
    dependencies: tuple[tuple[str, str], ...] = (),
) -> Path:
    path = repo_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "bindings").mkdir(parents=True, exist_ok=True)
    lines = [
        "aware_service = 1",
        "",
        "[service]",
        f'package_name = "{package_name}"',
        f'fqn_prefix = "{fqn_prefix}"',
        "",
        "[build]",
        'sources_dir = "bindings"',
        'compilation_mode = "service_ontology"',
        "",
        "[[dependencies]]",
        f'package_name = "{provided_api_package or f"{package_name}-api"}"',
        'kind = "api_service_protocol"',
        'expected_hash_sha256 = "' + ("a" * 64) + '"',
        "",
    ]
    for dependency_package_name, dependency_kind in dependencies:
        lines.extend(
            [
                "[[dependencies]]",
                f'package_name = "{dependency_package_name}"',
                f'kind = "{dependency_kind}"',
                "",
            ]
        )
    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    return path.resolve()


def _seed_experience_toml(
    repo_root: Path,
    relpath: str,
    *,
    package_name: str,
    fqn_prefix: str,
) -> Path:
    path = repo_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    (path.parent / "bindings").mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                "",
                "[build]",
                'environment_handle = "aware-kernel-runtime"',
                'sources_dir = "bindings"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path.resolve()


def test_local_experience_refs_expand_declared_cross_workspace_dependencies(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    conversation_toml = _seed_experience_toml(
        repo_root,
        "experiences/conversations/aware.experience.toml",
        package_name="aware-conversations",
        fqn_prefix="aware_conversations",
    )
    memory_toml = _seed_experience_toml(
        repo_root,
        "workspaces/aware_network/modules/memory/experiences/aware-memory/aware.experience.toml",
        package_name="aware-memory",
        fqn_prefix="aware_memory",
    )
    module_toml = memory_toml.parents[2] / "aware.module.toml"
    module_toml.write_text(
        "\n".join(
            (
                "aware = 1",
                "",
                "[[packages]]",
                'kind = "experience"',
                'manifest = "experiences/aware-memory/aware.experience.toml"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    conversation_toml.write_text(
        conversation_toml.read_text(encoding="utf-8")
        + "\n[[dependencies]]\n"
        + 'package_name = "aware-memory"\n'
        + 'kind = "experience_package"\n',
        encoding="utf-8",
    )

    resolved = direct_interface_local._experience_toml_paths_for_refs(
        repo_root=repo_root,
        experience_refs=("aware-conversations",),
    )

    assert resolved == tuple(sorted((conversation_toml, memory_toml)))


def test_local_experience_refs_resolve_workspace_revision_module_root(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "workspace-revision"
    experience_toml = _seed_experience_toml(
        repo_root,
        "modules/identity/experiences/aware_identity/aware.experience.toml",
        package_name="identity-default",
        fqn_prefix="aware_identity_experience_default",
    )

    resolved = direct_interface_local._experience_toml_paths_for_refs(
        repo_root=repo_root,
        experience_refs=("identity-default",),
    )

    assert resolved == (experience_toml,)


def _seed_identity_module_experience_package(repo_root: Path) -> Path:
    module_root = repo_root / "workspaces/aware_network/modules/identity"
    module_root.mkdir(parents=True, exist_ok=True)
    module_toml = module_root / "aware.module.toml"
    module_toml.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "identity_experience"',
                'kind = "experience"',
                'manifest = "experiences/aware_identity/aware.experience.toml"',
                'visibility = "module"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return module_toml.resolve()


def _kernel_environment_source() -> NodePackageRuntimeSource:
    return NodePackageRuntimeSource(
        package_name="kernel-environment-node",
        config_name="kernel_environment_host",
        source_kind="node_package",
        environment_targets=(
            NodePackageEnvironmentTarget(
                environment_handle="aware-kernel-runtime",
                profile_mounts=(),
            ),
        ),
        service_targets=(
            NodePackageServiceTarget(service_name="aware_environment"),
            NodePackageServiceTarget(service_name="aware_meta"),
        ),
        ontology_targets=(NodePackageOntologyTarget(package_name="storage-ontology"),),
    )


def _kernel_ontologies_manifest_source() -> NodePackageRuntimeSource:
    return NodePackageRuntimeSource(
        package_name="kernel-ontologies-node",
        config_name="kernel_ontologies_host",
        source_kind="node_ontology_manifest",
        ontology_targets=(
            NodePackageOntologyTarget(package_name="storage-ontology"),
            NodePackageOntologyTarget(package_name="service-ontology"),
        ),
        service_targets=(NodePackageServiceTarget(service_name="aware_ontology"),),
    )


def _kernel_ontologies_source() -> NodePackageRuntimeSource:
    return NodePackageRuntimeSource(
        package_name="kernel-ontologies-node",
        config_name="kernel_ontologies_host",
        source_kind="node_package",
        service_targets=(NodePackageServiceTarget(service_name="aware_ontology"),),
        ontology_targets=(
            NodePackageOntologyTarget(package_name="storage-ontology"),
            NodePackageOntologyTarget(package_name="content-ontology"),
            NodePackageOntologyTarget(package_name="code-ontology"),
            NodePackageOntologyTarget(package_name="history-ontology"),
            NodePackageOntologyTarget(package_name="meta-ontology"),
            NodePackageOntologyTarget(package_name="ontology-ontology"),
            NodePackageOntologyTarget(package_name="environment-ontology"),
            NodePackageOntologyTarget(package_name="api-ontology"),
            NodePackageOntologyTarget(package_name="service-ontology"),
            NodePackageOntologyTarget(package_name="node-ontology"),
        ),
    )


def _source_local_ontology_provider_refs_json(
    package_names: tuple[str, ...] = ("storage-ontology", "service-ontology"),
) -> str:
    return json.dumps(
        [
            {
                "provider_node_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "provider_node_base_url": "ws://127.0.0.1:8951",
                "provider_node_runtime_source": {
                    "source_kind": "node_ontology_manifest",
                    "environment_targets": [],
                    "ontology_targets": [
                        {"package_name": package_name} for package_name in package_names
                    ],
                },
                "service_package_ref": {
                    "package_name": "aware-ontology-service",
                    "provided_api_packages": [
                        {"api_package_name": "ontology-service-api"},
                    ],
                },
            }
        ]
    )


def test_prepare_node_package_run_manifest_writes_source_neutral_contract(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    environment_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=_kernel_environment_source(),
            runtime_manifest_path=runtime_manifest_path,
            auth_token="secret-token",
            require_live_runtime=False,
            environment_port_ready_timeout_s=12.5,
        )
    )

    assert plan.node_package == "kernel-environment-node"
    assert plan.node_config == "kernel_environment_host"
    assert plan.source_kind == "node_package"
    assert [target.package_name for target in plan.ontology_targets] == [
        "storage-ontology",
    ]
    assert plan.environment_targets[0].profile_mounts == ()
    assert plan.service_toml_paths == (environment_toml, meta_toml)
    assert plan.experience_toml_paths == ()
    assert plan.interface_host_config_paths == ()
    assert plan.runtime_manifest_path == runtime_manifest_path
    assert plan.node_env["AWARE_NODE_RUN_MANIFEST_PATH"] == (
        plan.node_run_manifest_path.as_posix()
    )
    assert plan.node_env["AWARE_NODE_BOOT_KERNEL"] == "1"
    assert plan.node_env["AWARE_NODE_PROVISION_MODE"] == "subprocess"
    assert plan.node_env["AWARE_AUTH_TOKEN"] == "secret-token"
    assert plan.node_env["AWARE_NODE_ENVIRONMENT_PORT_READY_TIMEOUT_S"] == "12.5"
    assert "AWARE_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH" not in plan.node_env
    assert plan.node_command_path.stat().st_mode & stat.S_IXUSR

    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
    )
    assert service_payload["implementation_packages"]["toml_paths"] == [
        environment_toml.as_posix(),
        meta_toml.as_posix(),
    ]
    assert "runtime_manifest_path" not in service_payload["app"]
    assert service_payload["artifact"]["root"] == repo_root.resolve().as_posix()
    assert service_payload["environment"]["api_endpoint"] == "http://127.0.0.1:8911"

    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == "aware.node.run_manifest.v1"
    assert manifest["node_package"] == "kernel-environment-node"
    assert manifest["display_name"] == "kernel_environment_host"
    assert manifest["environment_manifest_path"] == runtime_manifest_path.as_posix()
    assert manifest["hosted_services"][0]["bootstrap_config_path"] == (
        plan.service_host_config_path.as_posix()  # type: ignore[union-attr]
    )
    assert manifest["hosted_interfaces"] == []
    assert manifest["readiness"]["hosted_service_ready_timeout_s"] == 12.5
    assert manifest["readiness"]["hosted_interface_ready_timeout_s"] == 12.5
    assert manifest["readiness"]["hosted_service_request_timeout_s"] == (
        node_package_run_manifest.DEFAULT_NODE_PACKAGE_HOSTED_SERVICE_REQUEST_TIMEOUT_S
    )
    assert manifest["provenance"]["source_kind"] == "node_package"
    assert manifest["provenance"]["artifact_refs_json"] is not None

    receipt = json.loads(plan.receipt_path.read_text(encoding="utf-8"))
    assert receipt["node_package"] == "kernel-environment-node"
    assert receipt["source_kind"] == "node_package"
    assert receipt["workspace_revision_deployment_payload_env_present"] is False
    assert receipt["node_env"]["AWARE_AUTH_TOKEN"] == "<redacted>"


def test_prepare_node_package_run_manifest_installs_only_explicit_service_code_packages(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _seed_runtime_manifest(repo_root)
    experience_toml = _seed_experience_toml(
        repo_root,
        "experiences/workspace/aware.experience.toml",
        package_name="aware-workspace-experience",
        fqn_prefix="aware_workspace_experience",
    )
    experience_service_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/experience/services/experience/aware.service.toml",
        package_name="aware-experience-service",
        fqn_prefix="aware_experience_service",
        provided_api_package="experience-service-api",
    )
    bare_source = NodePackageRuntimeSource(
        package_name="kernel-services-node",
        config_name="kernel_services_host",
        source_kind="node_package",
        service_targets=(NodePackageServiceTarget(service_name="aware_experience"),),
    )

    bare_plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "bare",
            source=bare_source,
            require_live_runtime=False,
        )
    )

    assert bare_plan.service_toml_paths == (experience_service_toml,)
    assert bare_plan.experience_toml_paths == ()

    activated_source = NodePackageRuntimeSource(
        package_name="kernel-services-node",
        config_name="kernel_services_host",
        source_kind="node_package",
        service_targets=(
            NodePackageServiceTarget(
                service_name="aware_experience",
                code_packages=(
                    NodePackageServiceCodePackage(
                        slot_key="experience",
                        package_name="aware-workspace-experience",
                    ),
                ),
            ),
        ),
    )

    activated_plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "activated",
            source=activated_source,
            require_live_runtime=False,
        )
    )

    assert activated_plan.service_toml_paths == (experience_service_toml,)
    assert activated_plan.experience_toml_paths == (experience_toml,)
    assert activated_plan.to_payload()["service_code_packages"] == [
        {
            "service_name": "aware_experience",
            "slot_key": "experience",
            "package_name": "aware-workspace-experience",
            "language": "aware",
        }
    ]


def test_prepare_node_package_run_manifest_carries_local_runtime_artifact_refs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    environment_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=_kernel_environment_source(),
            service_toml_paths=(environment_toml, meta_toml),
            runtime_manifest_path=runtime_manifest_path,
            auth_token="secret-token",
            require_live_runtime=True,
        )
    )

    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    artifact_refs = json.loads(manifest["provenance"]["artifact_refs_json"])

    assert len(artifact_refs) == 1
    artifact_ref = artifact_refs[0]
    assert artifact_ref["artifact_family"] == "ontology_runtime_artifact_set"
    assert artifact_ref["artifact_role"] == "runtime_artifact_set"
    assert artifact_ref["package_name"] == "environment-ontology"
    artifact_set = artifact_ref["receipt"]["ontology_runtime_artifact_set"]
    artifact_roles = {
        artifact["artifact_role"] for artifact in artifact_set["artifacts"]
    }
    assert "runtime_bundle_manifest" in artifact_roles
    assert "db_schema_registry" in artifact_roles
    assert "ontology_package" in artifact_roles
    assert "source_code_package" in artifact_roles
    assert "object_config_graph_package" in artifact_roles
    assert "environment_runtime_manifest" not in artifact_roles
    provenance = artifact_set["provenance"]
    assert provenance["ontology_package_id"]
    assert provenance["source_code_package_id"]
    assert provenance["object_config_graph_package_id"]
    assert provenance["ontology_package_commit_id"] is None
    assert artifact_set["metadata"]["object_config_graph_hash"] == (
        "sha256:environment-ocg"
    )
    runtime_bundle_artifact = next(
        artifact
        for artifact in artifact_set["artifacts"]
        if artifact["artifact_role"] == "runtime_bundle_manifest"
    )
    assert runtime_bundle_artifact["runtime_contract_version"] == (
        "aware.ontology.runtime_bundle_manifest.v1"
    )
    assert runtime_bundle_artifact["digest"].startswith("sha256:")
    assert runtime_bundle_artifact["workspace_relative_path"].endswith(
        ".aware/ontology/runtime/ontology.runtime.manifest.json"
    )
    descriptor = artifact_set["runtime_projection_descriptors"][0]
    assert descriptor["projection_name"] == "Environment"
    assert descriptor["projection_hash"] == "environment.projection"
    assert descriptor["constructor_function_id"]
    descriptor_functions = {
        function["name"]: function
        for function in descriptor["metadata"]["capability_functions"]
    }
    assert descriptor_functions["build"]["id"] == descriptor["constructor_function_id"]
    assert descriptor_functions["build"]["is_constructor"] is True
    assert (
        plan.node_env["AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON"]
        == manifest["provenance"]["artifact_refs_json"]
    )


def test_prepare_node_package_run_manifest_exports_profile_mount_source_artifact(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    source = NodePackageRuntimeSource(
        package_name="kernel-environment-node",
        config_name="kernel_environment_host",
        source_kind="node_package",
        environment_targets=(
            NodePackageEnvironmentTarget(
                environment_handle="kernel",
                profile_mounts=(
                    NodePackageEnvironmentProfileMount(
                        package_name="aware-control-environment-profile",
                        profile_key="control.default",
                        mount_key="control.default",
                        mode="system",
                        position=0,
                    ),
                ),
            ),
        ),
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=source,
            runtime_manifest_path=runtime_manifest_path,
            require_live_runtime=False,
        )
    )

    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    artifact_refs = json.loads(manifest["provenance"]["artifact_refs_json"])
    node_source_refs = [
        item
        for item in artifact_refs
        if item["artifact_family"] == "aware.node.runtime_source"
    ]

    assert len(node_source_refs) == 1
    node_source = node_source_refs[0]["provider_payload"]["node_runtime_source"]
    assert node_source["environment_targets"] == [
        {
            "environment_handle": "kernel",
            "profile_mounts": [
                {
                    "mount_key": "control.default",
                    "mode": "system",
                    "package_name": "aware-control-environment-profile",
                    "position": 0,
                    "profile_key": "control.default",
                }
            ],
        }
    ]


def test_prepare_node_package_run_manifest_rejects_structure_environment_manifest(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_runtime_manifest(repo_root)
    environment_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
    )

    with pytest.raises(RuntimeError, match="Structure Environment runtime manifests"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=repo_root,
                run_dir=tmp_path / "run",
                source=_kernel_environment_source(),
                service_toml_paths=(environment_toml, meta_toml),
                runtime_manifest_path=runtime_manifest_path,
                auth_token="secret-token",
                require_live_runtime=True,
            )
        )


def test_prepare_node_package_run_manifest_rejects_environment_target_without_ontology_runtime_artifacts(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _seed_runtime_manifest(repo_root)
    environment_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
    )

    with pytest.raises(RuntimeError, match="source-local Ontology provider refs"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=repo_root,
                run_dir=tmp_path / "run",
                source=_kernel_environment_source(),
                service_toml_paths=(environment_toml, meta_toml),
                auth_token="secret-token",
                require_live_runtime=True,
            )
        )


def test_prepare_node_package_run_manifest_supports_ontology_service_only_node(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    ontology_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml",
        package_name="aware-ontology-service",
        fqn_prefix="aware_ontology_service",
        provided_api_package="ontology-service-api",
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=_kernel_ontologies_source(),
            require_live_runtime=False,
        )
    )

    assert plan.runtime_manifest_path is None
    assert plan.environment_targets == ()
    assert plan.service_toml_paths == (ontology_toml,)
    assert plan.node_env["AWARE_NODE_BOOT_KERNEL"] == "0"
    assert "AWARE_NODE_ENVIRONMENT_CONFIG_MANIFESTS" not in plan.node_env
    assert "AWARE_NODE_PROVISION_MODE" not in plan.node_env

    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
    )
    assert service_payload["app"] == {}
    assert "environment" not in service_payload
    assert service_payload["implementation_packages"]["toml_paths"] == [
        ontology_toml.as_posix(),
    ]

    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert "environment_manifest_path" not in manifest
    assert "environment_api_endpoint" not in manifest
    assert manifest["readiness"]["hosted_service_ready_timeout_s"] == 420.0
    assert manifest["readiness"]["hosted_interface_ready_timeout_s"] == 420.0
    assert manifest["hosted_services"][0]["bootstrap_config_path"] == (
        plan.service_host_config_path.as_posix()  # type: ignore[union-attr]
    )
    assert manifest["provenance"]["artifact_refs_json"] is None


def test_prepare_node_package_run_manifest_writes_committed_service_package_refs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    ontology_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml",
        package_name="aware-ontology-service",
        fqn_prefix="aware_ontology_service",
        provided_api_package="ontology-service-api",
    )
    service_ref = ServiceHostImplementationPackageRefInput(
        family_key="service",
        package_kind="service",
        package_name="aware-ontology-service",
        semantic_package_id=str(
            uuid5(NAMESPACE_URL, "aware.test/service-package/ontology")
        ),
        semantic_object_instance_graph_commit_id=str(
            uuid5(NAMESPACE_URL, "aware.test/service-package/ontology/oig")
        ),
        semantic_root_kind="service_package",
        semantic_root_id=str(uuid5(NAMESPACE_URL, "aware.test/service-package/root")),
        semantic_root_object_instance_graph_commit_id=str(
            uuid5(NAMESPACE_URL, "aware.test/service-config/root/oig")
        ),
        source_code_package_id=str(
            uuid5(NAMESPACE_URL, "aware.test/service-package/source-code")
        ),
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=_kernel_ontologies_source(),
            service_toml_paths=(ontology_toml,),
            service_package_refs=(service_ref,),
            require_live_runtime=False,
        )
    )

    assert plan.service_toml_paths == (ontology_toml,)
    assert plan.service_package_refs == (service_ref,)
    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
    )
    implementation_payload = service_payload["implementation_packages"]
    assert "toml_paths" not in implementation_payload
    assert implementation_payload["package_refs"] == [service_ref.to_payload()]

    plan_payload = plan.to_payload()
    assert plan_payload["service_toml_paths"] == [ontology_toml.as_posix()]
    assert plan_payload["service_package_refs"] == [service_ref.to_payload()]


def test_prepare_node_package_run_manifest_omits_empty_ontology_authority_config(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    identity_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/identity/services/identity/aware.service.toml",
        package_name="aware-identity-service",
        fqn_prefix="aware_identity_service",
        provided_api_package="identity-service-api",
    )
    source = NodePackageRuntimeSource(
        package_name="kernel-services-node",
        config_name="kernel_services_host",
        source_kind="node_package",
        service_targets=(NodePackageServiceTarget(service_name="aware_identity"),),
        ontology_targets=(),
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=source,
            require_live_runtime=False,
        )
    )

    assert plan.service_toml_paths == (identity_toml,)
    assert plan.service_host_config_path is not None
    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")
    )
    assert "ontology_authority" not in service_payload


def test_prepare_node_package_run_manifest_rejects_runtime_auth_without_environment(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml",
        package_name="aware-ontology-service",
        fqn_prefix="aware_ontology_service",
        provided_api_package="ontology-service-api",
    )

    with pytest.raises(RuntimeError, match="runtime auth token issuance"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=repo_root,
                run_dir=tmp_path / "run",
                source=_kernel_ontologies_source(),
                issue_runtime_auth_token=True,
                require_live_runtime=True,
            )
        )


def test_prepare_node_package_run_manifest_fails_closed_for_unknown_service(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    source = NodePackageRuntimeSource(
        package_name="broken-node",
        config_name="broken_host",
        environment_targets=_kernel_environment_source().environment_targets,
        service_targets=(NodePackageServiceTarget(service_name="aware_missing"),),
    )

    with pytest.raises(RuntimeError, match="aware_missing"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=repo_root,
                run_dir=tmp_path / "run",
                source=source,
                runtime_manifest_path=runtime_manifest_path,
                require_live_runtime=False,
            )
        )


def test_prepare_node_package_run_manifest_adds_local_api_provider_closure(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    environment_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
        provided_api_package="environment-service-api",
        dependencies=(
            ("meta-service-api", "api_invocation"),
            ("experience-service-api", "api_invocation"),
        ),
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
        provided_api_package="meta-service-api",
    )
    experience_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/experience/services/experience/aware.service.toml",
        package_name="aware-experience-service",
        fqn_prefix="aware_experience_service",
        provided_api_package="experience-service-api",
        dependencies=(("attention-service-api", "api_invocation"),),
    )
    attention_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/attention/services/attention/aware.service.toml",
        package_name="aware-attention-service",
        fqn_prefix="aware_attention_service",
        provided_api_package="attention-service-api",
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=_kernel_environment_source(),
            runtime_manifest_path=runtime_manifest_path,
            auth_token="secret-token",
            require_live_runtime=False,
        )
    )

    assert plan.service_toml_paths == (
        environment_toml,
        meta_toml,
        experience_toml,
        attention_toml,
    )
    assert [target.service_name for target in plan.service_targets] == [
        "aware_environment",
        "aware_meta",
    ]


def test_prepare_node_package_run_manifest_uses_remote_api_provider_refs_for_closure(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    environment_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
        provided_api_package="environment-service-api",
        dependencies=(
            ("meta-service-api", "api_invocation"),
            ("ontology-service-api", "api_invocation"),
        ),
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
        provided_api_package="meta-service-api",
    )
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml",
        package_name="aware-ontology-service",
        fqn_prefix="aware_ontology_service",
        provided_api_package="ontology-service-api",
    )

    remote_refs_json = json.dumps(
        [
            {
                "provider_node_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "provider_node_base_url": "ws://127.0.0.1:8951",
                "service_package_ref": {
                    "package_name": "aware-ontology-service",
                    "provided_api_packages": [
                        {"api_package_name": "ontology-service-api"},
                    ],
                },
            }
        ]
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=_kernel_environment_source(),
            auth_token="secret-token",
            runtime_manifest_path=runtime_manifest_path,
            remote_service_api_provider_refs_json=remote_refs_json,
            require_live_runtime=False,
        )
    )

    assert plan.service_toml_paths == (environment_toml, meta_toml)
    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
    )
    assert service_payload["implementation_packages"]["toml_paths"] == [
        environment_toml.as_posix(),
        meta_toml.as_posix(),
    ]
    assert service_payload["environment"]["api_endpoint"] == "http://127.0.0.1:8911"
    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert manifest["route_inputs"]["remote_service_api_provider_refs_json"] == (
        remote_refs_json
    )


def test_prepare_node_package_run_manifest_lowers_remote_environment_provider_to_service_host_endpoint(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _seed_runtime_manifest(repo_root)
    identity_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/identity/services/identity/aware.service.toml",
        package_name="aware-identity-service",
        fqn_prefix="aware_identity_service",
        provided_api_package="identity-service-api",
        dependencies=(("environment-service-api", "api_invocation"),),
    )
    identity_toml.write_text(
        identity_toml.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "[[ontology_packages]]",
                'package_name = "identity-ontology"',
                'fqn_prefix = "aware_identity"',
                'role = "replica"',
                'requirement_mode = "required"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    experience_toml = _seed_experience_toml(
        repo_root,
        "workspaces/aware_network/modules/identity/experiences/aware_identity/aware.experience.toml",
        package_name="identity-default",
        fqn_prefix="aware_identity_experience_default",
    )
    _seed_identity_module_experience_package(repo_root)
    remote_refs_json = json.dumps(
        [
            {
                "provider_node_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "provider_node_base_url": "ws://127.0.0.1:8962",
                "request_timeout_s": 77.0,
                "service_package_ref": {
                    "package_name": "aware-environment-service",
                    "provided_api_packages": [
                        {"api_package_name": "environment-service-api"},
                    ],
                },
                "hosted_service_advertisement": {
                    "service_name": "aware_environment",
                    "service_package_names": ["aware-environment-service"],
                    "endpoint_refs": [
                        "environment.ready.ensure_ready",
                    ],
                },
            }
        ]
    )
    source = NodePackageRuntimeSource(
        package_name="kernel-services-node",
        config_name="kernel_services_host",
        source_kind="node_package",
        service_targets=(
            NodePackageServiceTarget(
                service_name="aware_identity",
                code_packages=(
                    NodePackageServiceCodePackage(
                        slot_key="experience",
                        package_name="identity-default",
                    ),
                ),
            ),
        ),
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=source,
            remote_service_api_provider_refs_json=remote_refs_json,
            require_live_runtime=False,
        )
    )

    assert plan.environment_targets == ()
    assert plan.service_toml_paths == (identity_toml,)
    assert plan.experience_toml_paths == (experience_toml,)
    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
    )
    assert service_payload["implementation_packages"]["toml_paths"] == [
        identity_toml.as_posix(),
    ]
    assert service_payload["reference_packages"]["experience_toml_paths"] == [
        experience_toml.as_posix(),
    ]
    replica_dir = (tmp_path / "run" / "service" / "ontology-replica").resolve()
    assert service_payload["ontology_replica"] == {
        "state_db_path": (replica_dir / "state.sqlite").as_posix(),
        "projection_db_path": (replica_dir / "projection.sqlite").as_posix(),
    }
    assert service_payload["environment"]["api_endpoint"] == "ws://127.0.0.1:8962"
    assert service_payload["environment"]["request_timeout_s"] == 77.0
    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert "environment_manifest_path" not in manifest
    assert "environment_api_endpoint" not in manifest
    assert manifest["route_inputs"]["remote_service_api_provider_refs_json"] == (
        remote_refs_json
    )


def test_prepare_node_package_run_manifest_rejects_ambiguous_remote_environment_provider_endpoints(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _seed_runtime_manifest(repo_root)
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/identity/services/identity/aware.service.toml",
        package_name="aware-identity-service",
        fqn_prefix="aware_identity_service",
        provided_api_package="identity-service-api",
        dependencies=(("environment-service-api", "api_invocation"),),
    )
    _seed_experience_toml(
        repo_root,
        "workspaces/aware_network/modules/identity/experiences/aware_identity/aware.experience.toml",
        package_name="identity-default",
        fqn_prefix="aware_identity_experience_default",
    )
    _seed_identity_module_experience_package(repo_root)
    remote_refs_json = json.dumps(
        [
            {
                "provider_node_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "provider_node_base_url": "ws://127.0.0.1:8962",
                "service_package_ref": {
                    "package_name": "aware-environment-service",
                    "provided_api_packages": [
                        {"api_package_name": "environment-service-api"},
                    ],
                },
            },
            {
                "provider_node_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "provider_node_base_url": "ws://127.0.0.1:9962",
                "service_package_ref": {
                    "package_name": "aware-environment-service",
                    "provided_api_packages": [
                        {"api_package_name": "environment-service-api"},
                    ],
                },
            },
        ]
    )
    source = NodePackageRuntimeSource(
        package_name="kernel-services-node",
        config_name="kernel_services_host",
        source_kind="node_package",
        service_targets=(
            NodePackageServiceTarget(
                service_name="aware_identity",
                code_packages=(
                    NodePackageServiceCodePackage(
                        slot_key="experience",
                        package_name="identity-default",
                    ),
                ),
            ),
        ),
    )

    with pytest.raises(RuntimeError, match="ambiguous"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=repo_root,
                run_dir=tmp_path / "run",
                source=source,
                remote_service_api_provider_refs_json=remote_refs_json,
                require_live_runtime=False,
            )
        )


def test_prepare_node_package_run_manifest_resolves_source_local_environment_artifact_refs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    _seed_ontology_runtime_manifest(
        repo_root,
        package_name="network-ontology",
        fqn_prefix="aware_network",
        module_name="network",
        projection_name="NetworkNode",
        projection_hash="network-node.projection",
        class_name="NetworkNode",
        function_names=("register", "upsert_environment", "attach_service"),
        constructor_function_name="register",
    )
    _seed_ontology_runtime_manifest(
        repo_root,
        package_name="identity-ontology",
        fqn_prefix="aware_identity",
        module_name="identity",
        projection_name="Identity",
        projection_hash="identity.projection",
        class_name="Identity",
        function_names=("build",),
    )
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
        provided_api_package="environment-service-api",
        dependencies=(
            ("meta-service-api", "api_invocation"),
            ("ontology-service-api", "api_invocation"),
        ),
    )
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
        provided_api_package="meta-service-api",
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=tmp_path / "run",
            source=_kernel_environment_source(),
            auth_token="secret-token",
            remote_service_api_provider_refs_json=(
                _source_local_ontology_provider_refs_json(
                    (
                        "storage-ontology",
                        "environment-ontology",
                        "network-ontology",
                        "identity-ontology",
                    )
                )
            ),
            require_live_runtime=False,
        )
    )

    assert plan.runtime_manifest_path == runtime_manifest_path
    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
    )
    assert "runtime_manifest_path" not in service_payload["app"]
    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    artifact_refs = json.loads(manifest["provenance"]["artifact_refs_json"])
    artifact_refs_by_package = {
        artifact_ref["package_name"]: artifact_ref for artifact_ref in artifact_refs
    }
    assert set(artifact_refs_by_package) == {
        "environment-ontology",
        "network-ontology",
    }
    artifact_set = artifact_refs_by_package["environment-ontology"]["receipt"][
        "ontology_runtime_artifact_set"
    ]
    assert artifact_set["runtime_projection_descriptors"][0]["projection_name"] == (
        "Environment"
    )
    network_artifact_set = artifact_refs_by_package["network-ontology"]["receipt"][
        "ontology_runtime_artifact_set"
    ]
    network_descriptor = network_artifact_set["runtime_projection_descriptors"][0]
    assert network_descriptor["projection_name"] == "NetworkNode"
    network_capability_functions = {
        function["name"]: function
        for function in network_descriptor["metadata"]["capability_functions"]
    }
    assert set(network_capability_functions) == {
        "attach_service",
        "register",
        "upsert_environment",
    }
    assert network_capability_functions["attach_service"]["is_constructor"] is False
    assert network_capability_functions["register"]["is_constructor"] is True
    provenance = artifact_set["provenance"]
    assert provenance["ontology_package_id"]
    assert provenance["source_code_package_id"]
    assert provenance["object_config_graph_package_id"]
    assert provenance["ontology_package_commit_id"] is None
    assert artifact_set["metadata"]["object_config_graph_hash"] == (
        "sha256:environment-ocg"
    )
    runtime_bundle_manifest = next(
        artifact
        for artifact in artifact_set["artifacts"]
        if artifact["artifact_role"] == "runtime_bundle_manifest"
    )
    assert runtime_bundle_manifest["digest"].startswith("sha256:")
    db_schema_registry = next(
        artifact
        for artifact in artifact_set["artifacts"]
        if artifact["artifact_role"] == "db_schema_registry"
    )
    assert db_schema_registry["digest"].startswith("sha256:")
    assert db_schema_registry["workspace_relative_path"].endswith(
        ".aware/ontology/runtime/db.schema.registry.json"
    )
    assert db_schema_registry["provider_payload"]["sql_roots"] == [
        (repo_root / "modules" / "environment" / "structure" / "ontology" / "sql")
        .resolve()
        .as_posix()
    ]
    assert (
        plan.node_env["AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON"]
        == manifest["provenance"]["artifact_refs_json"]
    )


def test_prepare_node_package_run_manifest_rejects_ontology_runtime_without_ocg_hash(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    payload = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    payload["ocg"].pop("hash")
    runtime_manifest_path.write_text(
        json.dumps(payload) + "\n",
        encoding="utf-8",
    )
    environment_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
    )
    meta_toml = _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
    )

    with pytest.raises(RuntimeError, match="require ocg.hash"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=repo_root,
                run_dir=tmp_path / "run",
                source=_kernel_environment_source(),
                service_toml_paths=(environment_toml, meta_toml),
                runtime_manifest_path=runtime_manifest_path,
                auth_token="secret-token",
                require_live_runtime=True,
            )
        )


def test_prepare_node_package_run_manifest_rejects_source_local_structure_environment_manifest(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_runtime_manifest(repo_root)
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
        provided_api_package="environment-service-api",
        dependencies=(
            ("meta-service-api", "api_invocation"),
            ("ontology-service-api", "api_invocation"),
        ),
    )
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
        provided_api_package="meta-service-api",
    )

    with pytest.raises(RuntimeError, match="Structure Environment runtime manifests"):
        prepare_node_package_run_manifest(
            NodePackageRunManifestRequest(
                repo_root=repo_root,
                run_dir=tmp_path / "run",
                source=_kernel_environment_source(),
                auth_token="secret-token",
                remote_service_api_provider_refs_json=(
                    _source_local_ontology_provider_refs_json(
                        ("storage-ontology", "environment-ontology")
                    )
                ),
                require_live_runtime=False,
                runtime_manifest_path=runtime_manifest_path,
            )
        )


def test_prepare_node_package_run_manifest_exports_source_local_provider_refs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    workspace_root = tmp_path / "coordination-workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml",
        package_name="aware-ontology-service",
        fqn_prefix="aware_ontology_service",
        provided_api_package="ontology-service-api",
    )

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            workspace_root=workspace_root,
            run_dir=tmp_path / "run",
            source=_kernel_ontologies_manifest_source(),
            require_live_runtime=False,
            hosted_service_request_timeout_s=77.0,
        )
    )

    provider_refs = json.loads(plan.service_api_provider_refs_json)
    assert len(provider_refs) == 1
    provider_ref = provider_refs[0]
    assert provider_ref["provider_node_base_url"] == "ws://127.0.0.1:8911"
    assert provider_ref["provider_node_package"] == "kernel-ontologies-node"
    assert provider_ref["request_timeout_s"] == 77.0
    assert provider_ref["service_package_ref"]["package_name"] == (
        "aware-ontology-service"
    )
    advertisement = provider_ref["hosted_service_advertisement"]
    assert advertisement["service_package_id"] == (
        provider_ref["service_package_ref"]["service_package_id"]
    )
    assert advertisement["service_name"] == "aware_ontology"
    assert advertisement["service_package_names"] == ["aware-ontology-service"]
    assert advertisement["host_id"] == "aware_service_service"
    assert advertisement["protocol_version"] == "1"
    assert "ontology.graph.resolve_projection" in advertisement["endpoint_refs"]
    assert "ontology.graph.get_lane_head" in advertisement["endpoint_refs"]
    assert "ontology.graph.invoke_function" in advertisement["endpoint_refs"]
    assert provider_ref["provider_node_runtime_source"]["source_kind"] == (
        "node_ontology_manifest"
    )
    assert provider_ref["provider_node_runtime_source"]["ontology_targets"] == [
        {"package_name": "storage-ontology"},
        {"package_name": "service-ontology"},
    ]
    assert provider_ref["provider_node_runtime_source"]["environment_targets"] == []
    assert provider_ref["authority"] == {
        "metadata": {
            ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY: {
                "schema": ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
                "source_kind": "node_ontology_manifest",
                "ontology_package_names": [
                    "service-ontology",
                    "storage-ontology",
                ],
                "ontology_targets": [
                    {"package_name": "service-ontology"},
                    {"package_name": "storage-ontology"},
                ],
            }
        }
    }
    payload = plan.to_payload()
    assert (
        payload["service_api_provider_refs_json"] == plan.service_api_provider_refs_json
    )
    assert plan.service_host_config_path is not None
    service_host_payload = tomllib.loads(plan.service_host_config_path.read_text())
    assert service_host_payload["artifact"]["root"] == repo_root.resolve().as_posix()
    assert service_host_payload["ontology_authority"]["source_kind"] == (
        "node_ontology_manifest"
    )
    assert service_host_payload["ontology_authority"]["root"] == (
        repo_root.resolve().as_posix()
    )
    assert service_host_payload["ontology_authority"]["package_names"] == [
        "storage-ontology",
        "service-ontology",
    ]
    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert manifest["provenance"]["workspace_root"] == (
        workspace_root.resolve().as_posix()
    )


def test_kernel_ontologies_host_provider_refs_include_service_portal_closure(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    plan = prepare_node_ontology_local_bootstrap(
        NodeOntologyLocalBootstrapRequest(
            repo_root=repo_root,
            node_toml_path=(
                repo_root / "nodes" / "kernel_ontologies_host" / "aware.node.toml"
            ),
            run_dir=tmp_path / "run",
            require_live_runtime=False,
        )
    )

    ontology_targets = {target.package_name for target in plan.ontology_targets}
    assert {
        "api-ontology",
        "attention-ontology",
        "economy-ontology",
        "experience-ontology",
        "identity-ontology",
        "interface-ontology",
        "network-ontology",
        "reactivity-ontology",
        "service-ontology",
    } <= ontology_targets

    provider_refs = json.loads(plan.service_api_provider_refs_json)
    provider_ontology_targets = {
        target["package_name"]
        for target in provider_refs[0]["provider_node_runtime_source"][
            "ontology_targets"
        ]
    }
    assert ontology_targets == provider_ontology_targets
    catalog = provider_refs[0]["authority"]["metadata"][
        ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY
    ]
    assert catalog["schema"] == ONTOLOGY_AUTHORITY_CATALOG_SCHEMA
    assert set(catalog["ontology_package_names"]) == ontology_targets


def test_aware_network_ontology_authority_node_uses_module_owned_node_package(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    plan = prepare_node_ontology_local_bootstrap(
        NodeOntologyLocalBootstrapRequest(
            repo_root=repo_root,
            node_toml_path=(
                repo_root
                / "workspaces"
                / "aware_network"
                / "modules"
                / "node"
                / "nodes"
                / "aware_network_ontology_authority"
                / "aware.node.toml"
            ),
            run_dir=tmp_path / "run",
            require_live_runtime=False,
        )
    )

    ontology_targets = {target.package_name for target in plan.ontology_targets}
    assert {
        "api-ontology",
        "attention-ontology",
        "code-ontology",
        "content-ontology",
        "economy-ontology",
        "environment-ontology",
        "experience-ontology",
        "history-ontology",
        "hub-ontology",
        "identity-ontology",
        "interface-ontology",
        "meta-ontology",
        "network-ontology",
        "node-ontology",
        "ontology-ontology",
        "reactivity-ontology",
        "sdk-ontology",
        "service-ontology",
        "skill-ontology",
        "storage-ontology",
    } == ontology_targets

    provider_refs = json.loads(plan.service_api_provider_refs_json)
    provider_ref = provider_refs[0]
    assert provider_ref["provider_node_package"] == (
        "aware-network-ontology-authority-node"
    )
    provider_ontology_targets = {
        target["package_name"]
        for target in provider_ref["provider_node_runtime_source"]["ontology_targets"]
    }
    assert provider_ontology_targets == ontology_targets
    catalog = provider_ref["authority"]["metadata"][
        ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY
    ]
    assert catalog["schema"] == ONTOLOGY_AUTHORITY_CATALOG_SCHEMA
    assert set(catalog["ontology_package_names"]) == ontology_targets

    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert manifest["node_package"] == "aware-network-ontology-authority-node"
    assert manifest["provenance"]["source_kind"] == "node_ontology_manifest"


def test_kernel_services_host_activates_identity_default_experience_package(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    service_toml_paths = tuple(
        repo_root / relative_path
        for relative_path in (
            "workspaces/aware_network/modules/attention/services/attention/aware.service.toml",
            "workspaces/aware_network/modules/economy/services/economy/aware.service.toml",
            "workspaces/aware_network/modules/experience/services/experience/aware.service.toml",
            "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
            "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml",
            "workspaces/aware_network/modules/hub/services/hub/aware.service.toml",
            "workspaces/aware_network/modules/identity/services/identity/aware.service.toml",
            "workspaces/aware_network/modules/network/services/network/aware.service.toml",
            "workspaces/aware_network/modules/reactivity/services/reactivity/aware.service.toml",
        )
    )

    plan = prepare_node_ontology_local_bootstrap(
        NodeOntologyLocalBootstrapRequest(
            repo_root=repo_root,
            node_toml_path=(
                repo_root / "nodes" / "kernel_services_host" / "aware.node.toml"
            ),
            run_dir=tmp_path / "run",
            service_toml_paths=service_toml_paths,
            remote_service_api_provider_refs_json="[]",
            require_live_runtime=False,
        )
    )
    identity_experience_toml = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "identity"
        / "experiences"
        / "aware_identity"
        / "aware.experience.toml"
    )

    assert plan.experience_toml_paths == (identity_experience_toml,)
    assert plan.to_payload()["service_code_packages"] == [
        {
            "service_name": "aware_identity",
            "slot_key": "experience",
            "package_name": "identity-default",
            "language": "aware",
        }
    ]
    assert plan.service_host_config_path is not None
    service_host_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")
    )
    assert service_host_payload["reference_packages"]["experience_toml_paths"] == [
        identity_experience_toml.resolve().as_posix()
    ]


def test_kernel_interface_host_uses_remote_provider_refs_without_local_service_host(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    remote_refs_json = json.dumps(
        [
            {
                "provider_node_base_url": "ws://127.0.0.1:8963",
                "service_package_ref": {
                    "provided_api_packages": [
                        {"api_package_name": "experience-service-api"},
                    ],
                },
            },
        ]
    )

    plan = prepare_node_ontology_local_bootstrap(
        NodeOntologyLocalBootstrapRequest(
            repo_root=repo_root,
            node_toml_path=(
                repo_root / "nodes" / "kernel_interface_host" / "aware.node.toml"
            ),
            run_dir=tmp_path / "run",
            port=8964,
            remote_service_api_provider_refs_json=remote_refs_json,
            interface_package_names_by_target={
                "aware_control": "aware-control-interface",
            },
            require_live_runtime=False,
        )
    )

    assert plan.service_host_config_path is None
    assert plan.service_toml_paths == ()
    assert len(plan.interface_host_config_paths) == 1
    interface_payload = tomllib.loads(
        plan.interface_host_config_paths[0].read_text(encoding="utf-8")
    )
    assert interface_payload["app"]["namespace"] == "aware_control"
    assert interface_payload["app"]["endpoint"] == "ws://127.0.0.1:8964"
    assert interface_payload["app"]["state_home"] == (
        plan.interface_host_config_paths[0].parent.as_posix()
    )
    assert interface_payload["interface_package"]["package_name"] == (
        "aware-control-interface"
    )
    assert "local_service_host" not in interface_payload
    assert len(plan.interface_control_socket_paths[0].as_posix()) < 108

    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert manifest["hosted_services"] == []
    assert manifest["hosted_interfaces"][0]["bootstrap_config_path"] == (
        plan.interface_host_config_paths[0].as_posix()
    )
    assert manifest["route_inputs"]["remote_service_api_provider_refs_json"] == (
        remote_refs_json
    )
    assert manifest["provenance"]["source_kind"] == "node_ontology_manifest"
    assert (
        plan.to_payload()["source_local_ontology_composition_bridge"]["used"] is False
    )


def test_kernel_interface_host_requires_service_route_source(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    with pytest.raises(
        RuntimeError,
        match="local ServiceHost config or remote Service API provider refs",
    ):
        prepare_node_ontology_local_bootstrap(
            NodeOntologyLocalBootstrapRequest(
                repo_root=repo_root,
                node_toml_path=(
                    repo_root / "nodes" / "kernel_interface_host" / "aware.node.toml"
                ),
                run_dir=tmp_path / "run",
                interface_package_names_by_target={
                    "aware_control": "aware-control-interface",
                },
                require_live_runtime=False,
            )
        )


def test_prepare_node_package_run_manifest_keeps_service_socket_path_short(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
        provided_api_package="environment-service-api",
        dependencies=(("meta-service-api", "api_invocation"),),
    )
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
        provided_api_package="meta-service-api",
    )
    run_dir = tmp_path / (
        "aware-node-env-ontology-live-e2e-20260603-"
        "environment-consumer-with-a-long-operator-run-name"
    )
    kernel_revision_root = tmp_path / "kernel-revision-root"
    kernel_revision_root.mkdir()

    plan = prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            run_dir=run_dir,
            source=_kernel_environment_source(),
            runtime_manifest_path=runtime_manifest_path,
            kernel_workspace_revision_root=kernel_revision_root,
            auth_token="secret-token",
            require_live_runtime=False,
        )
    )

    assert plan.service_socket_path is not None
    assert plan.service_host_config_path == (
        run_dir.resolve() / "service" / "aware.service-host.toml"
    )
    service_payload = tomllib.loads(
        plan.service_host_config_path.read_text(encoding="utf-8")
    )
    assert service_payload["app"]["kernel_repo_root"] == (
        kernel_revision_root.resolve().as_posix()
    )
    socket_path = Path(service_payload["ipc"]["socket_path"])
    assert socket_path == plan.service_socket_path
    assert socket_path.name == "kernel_environment_host.sock"
    assert socket_path.parent.parent == (
        Path(tempfile.gettempdir()) / "aware-service-ipc"
    )
    assert run_dir.resolve().as_posix() not in socket_path.as_posix()
    assert len(socket_path.as_posix()) < 100
    manifest_payload = json.loads(
        plan.node_run_manifest_path.read_text(encoding="utf-8")
    )
    assert manifest_payload["hosted_services"][0]["launch_command"] == [
        "python",
        "-m",
        "aware_service_service",
    ]
    node_command_text = plan.node_command_path.read_text(encoding="utf-8")
    assert "uv run --project" in node_command_text
    assert "python -m aware_node_service.app" in node_command_text
    assert sys.executable not in node_command_text
    assert sys.executable not in json.dumps(manifest_payload)


def test_prepare_node_ontology_local_bootstrap_delegates_through_package_truth(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    runtime_manifest_path = _seed_ontology_runtime_manifest(repo_root)
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        package_name="aware-environment-service",
        fqn_prefix="aware_environment_service",
    )
    _seed_service_toml(
        repo_root,
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
        package_name="aware-meta-service",
        fqn_prefix="aware_meta_service",
    )
    node_toml_path = repo_root / "nodes" / "kernel_environment_host" / "aware.node.toml"
    node_toml_path.parent.mkdir(parents=True, exist_ok=True)
    node_toml_path.write_text(
        "\n".join(
            [
                "aware_node = 1",
                "",
                "[node]",
                'package_name = "kernel-environment-node"',
                'fqn_prefix = "aware_kernel_environment_node"',
                "",
                "[build]",
                'sources_dir = "nodes"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                'compilation_mode = "node_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "aware-environment-service"',
                'kind = "service_package"',
                "",
                "[[dependencies]]",
                'package_name = "aware-meta-service"',
                'kind = "service_package"',
                "",
                "[[dependencies]]",
                'package_name = "storage-ontology"',
                'kind = "ontology_package"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    node_source_path = node_toml_path.parent / "nodes" / "kernel_environment_host.aware"
    node_source_path.parent.mkdir(parents=True, exist_ok=True)
    node_source_path.write_text(
        "\n".join(
            [
                "node kernel_environment_host {",
                "    environment aware-kernel-runtime {",
                "    }",
                "    ontology storage-ontology;",
                "    service aware_environment",
                "    service aware_meta",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    plan = prepare_node_ontology_local_bootstrap(
        NodeOntologyLocalBootstrapRequest(
            repo_root=repo_root,
            node_toml_path=node_toml_path,
            run_dir=tmp_path / "run",
            auth_token="secret-token",
            runtime_manifest_path=runtime_manifest_path,
            remote_service_api_provider_refs_json=(
                '[{"service_package_ref":{"package_name":"aware-ontology-service"}}]'
            ),
            require_live_runtime=False,
        )
    )

    assert plan.node_package == "kernel-environment-node"
    assert plan.node_config == "kernel_environment_host"
    assert plan.source_kind == "node_ontology_manifest"
    assert [target.package_name for target in plan.ontology_targets] == [
        "storage-ontology",
    ]
    assert [target.service_name for target in plan.service_targets] == [
        "aware_environment",
        "aware_meta",
    ]
    manifest = json.loads(plan.node_run_manifest_path.read_text(encoding="utf-8"))
    assert manifest["provenance"]["source_kind"] == "node_ontology_manifest"
    assert manifest["provenance"]["artifact_refs_json"] is not None
    assert manifest["route_inputs"]["remote_service_api_provider_refs_json"] == (
        '[{"service_package_ref":{"package_name":"aware-ontology-service"}}]'
    )
    node_env = (plan.run_dir / "env" / "node.env").read_text(encoding="utf-8")
    assert "AWARE_NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON=" in node_env
