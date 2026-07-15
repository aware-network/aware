from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from aware_orm.db.schema_registry import compute_sql_root_source_hash
from aware_service_runtime.host_contract import (
    ServiceHostContractBackendInput,
    ServiceHostContractTargetInput,
    ontology_authority_runtime_manifest_paths,
    ontology_runtime_artifact_sql_root_from_manifest_path,
    ontology_runtime_manifest_db_schema_hash,
    projection_runtime_requirements_for_semantic_contracts,
    resolve_service_host_contract_for_toml,
)
from aware_service_service_dto.host import (
    ServiceHostDbRequirementKind,
    ServiceHostProjectionRuntimeRequirementKind,
)
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT
from aware_api_runtime.semantic_contract import AWARE_API_SEMANTIC_CONTRACT
from aware_service_runtime.semantic_contract import AWARE_SERVICE_SEMANTIC_CONTRACT


def _write_service_toml(
    path: Path,
    *,
    entrypoint: str | None = None,
    ontology_package_name: str | None = None,
    object_config_graph_manifest: str | None = None,
) -> None:
    lines = [
        "aware_service = 1",
        "",
        "[service]",
        'package_name = "proof-service"',
        'fqn_prefix = "aware_proof_service"',
        "",
        "[build]",
        'sources_dir = "bindings"',
        'include_paths = ["**/*.aware"]',
        'compilation_mode = "service_ontology"',
        "",
        "[host]",
        'service_surface = "service"',
        "",
    ]
    if entrypoint is not None:
        lines.extend(
            [
                "[host.contract]",
                f'entrypoint = "{entrypoint}"',
                "",
            ]
        )
    lines.extend(
        [
            "[implementation]",
            "",
            "[[implementation.packages]]",
            'package_name = "proof-service"',
            'language = "python"',
            'import_root = "aware_proof_service"',
            'manifest_path = "pyproject.toml"',
            "",
        ]
    )
    if ontology_package_name is not None:
        lines.extend(
            [
                "[[ontology_packages]]",
                f'package_name = "{ontology_package_name}"',
                'fqn_prefix = "aware_proof"',
                'role = "replica"',
                "",
            ]
        )
    if object_config_graph_manifest is not None:
        lines.extend(
            [
                "[[object_config_graph_packages]]",
                f'manifest = "{object_config_graph_manifest}"',
                'role = "temporal_session_state"',
                'description = "Proof local state package."',
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_ontology_authority_module(
    *,
    repo_root: Path,
    module_name: str,
    package_name: str,
    fqn_prefix: str,
) -> Path:
    module_root = repo_root / "modules" / module_name
    source_root = module_root / "structure" / "ontology"
    ontology_toml_path = module_root / "aware.ontology.toml"
    source_manifest_path = source_root / "aware.toml"
    runtime_manifest_path = (
        source_root
        / ".aware"
        / "ontology"
        / "runtime"
        / "ontology.runtime.manifest.json"
    )
    ontology_toml_path.parent.mkdir(parents=True, exist_ok=True)
    source_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
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
    sql_file = source_root / "sql" / "schema" / "proof.sql"
    sql_file.parent.mkdir(parents=True, exist_ok=True)
    sql_file.write_text("CREATE TABLE proof (id UUID PRIMARY KEY NOT NULL);\n")
    db_schema_registry_path = runtime_manifest_path.parent / "db.schema.registry.json"
    db_schema_registry_path.write_text(
        json.dumps(
            {
                "schema_registry_version": 1,
                "environment_id": str(uuid4()),
                "entries": [
                    {
                        "source_label": "structure",
                        "package_kind": "ontology",
                        "backend_targets": ["postgres"],
                        "sql_root": (source_root / "sql").as_posix(),
                        "source_hash": compute_sql_root_source_hash(
                            sql_root=source_root / "sql"
                        ),
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runtime_manifest_path.write_text(
        json.dumps(
            {
                "package_name": package_name,
                "ocg": {
                    "hash": f"sha256:{package_name}:ocg",
                    "semantic_hash": f"sha256:{package_name}:semantic",
                },
                "db_schema_registry": {
                    "file": "db.schema.registry.json",
                    "hash": f"sha256:{package_name}:registry",
                    "status": "ready",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_manifest_path.resolve()


def test_ontology_authority_resolves_ontology_runtime_bundle_manifest(
    tmp_path: Path,
) -> None:
    runtime_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="service",
        package_name="service-ontology",
        fqn_prefix="aware_service",
    )

    assert runtime_manifest_path.match(
        "**/.aware/ontology/runtime/ontology.runtime.manifest.json"
    )
    assert ontology_authority_runtime_manifest_paths(
        package_names=("service-ontology",),
        authority_root=tmp_path,
    ) == (runtime_manifest_path,)


def test_ontology_authority_resolves_nested_workspace_module_manifest(
    tmp_path: Path,
) -> None:
    runtime_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="conversation/ontology",
        package_name="conversation-ontology",
        fqn_prefix="aware_conversation",
    )

    assert ontology_authority_runtime_manifest_paths(
        package_names=("conversation-ontology",),
        authority_root=tmp_path,
    ) == (runtime_manifest_path,)


def test_ontology_authority_resolves_revision_runtime_manifest(
    tmp_path: Path,
) -> None:
    sql_root = (
        tmp_path / "modules" / "service" / "ontology" / "structure" / "sql" / "schema"
    )
    sql_root.mkdir(parents=True)
    (sql_root / "proof.sql").write_text(
        "CREATE TABLE proof (id UUID PRIMARY KEY NOT NULL);\n",
        encoding="utf-8",
    )
    runtime_manifest_path = (
        tmp_path
        / ".aware"
        / "ontology"
        / "runtime"
        / "service-ontology"
        / "ontology.runtime.manifest.json"
    )
    runtime_manifest_path.parent.mkdir(parents=True)
    runtime_manifest_path.write_text(
        json.dumps(
            {
                "schema": "aware.workspace.revision_ontology_runtime_manifest.v1",
                "package_name": "service-ontology",
                "source_kind": "workspace_revision",
                "db_schema": {
                    "package_kind": "ontology",
                    "backend_targets": ["postgres"],
                    "sql_roots": [
                        {
                            "path": Path(
                                os.path.relpath(
                                    sql_root,
                                    start=runtime_manifest_path.parent,
                                )
                            ).as_posix(),
                            "path_mode": "manifest_relative",
                        }
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert ontology_authority_runtime_manifest_paths(
        package_names=("service-ontology",),
        authority_root=tmp_path,
    ) == (runtime_manifest_path.resolve(),)
    assert (
        ontology_runtime_artifact_sql_root_from_manifest_path(runtime_manifest_path)
        == sql_root.resolve()
    )
    assert ontology_runtime_manifest_db_schema_hash(runtime_manifest_path).startswith(
        "sha256:"
    )


def test_generic_contract_does_not_infer_db_requirement_from_runtime_manifest(
    tmp_path: Path,
) -> None:
    service_toml_path = tmp_path / "services" / "proof" / "aware.service.toml"
    _write_service_toml(service_toml_path)
    runtime_manifest_path = (
        tmp_path
        / "modules"
        / "environment"
        / "structure"
        / "ontology"
        / ".aware"
        / "environment"
        / "runtime"
        / "environment.manifest.json"
    )
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text(
        json.dumps({"environment": {"id": "proof"}, "ocg": {"hash": "sha256:abc"}}),
        encoding="utf-8",
    )

    response = resolve_service_host_contract_for_toml(
        service_toml_path=service_toml_path,
        target=ServiceHostContractTargetInput(
            runtime_manifest_path=runtime_manifest_path,
            artifact_root=tmp_path,
        ),
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )

    assert response.db_requirement_plan is not None
    assert response.db_requirement_plan.requirements == []


def test_host_contract_invokes_environment_provider_empty_db_contract(
    tmp_path: Path,
) -> None:
    service_toml_path = tmp_path / "services" / "environment" / "aware.service.toml"
    _write_service_toml(
        service_toml_path,
        entrypoint="aware_environment_service.host_contract:resolve_service_host_contract",
    )

    response = resolve_service_host_contract_for_toml(
        service_toml_path=service_toml_path,
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )

    assert response.db_requirement_plan is not None
    assert response.db_requirement_plan.requirements == []
    assert response.metadata["provider_key"] == "aware-environment-service"


def test_host_contract_generic_fallback_declares_ontology_replica(
    tmp_path: Path,
) -> None:
    service_toml_path = tmp_path / "services" / "consumer" / "aware.service.toml"
    _write_service_toml(
        service_toml_path,
        ontology_package_name="content-ontology",
    )

    response = resolve_service_host_contract_for_toml(
        service_toml_path=service_toml_path,
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )

    assert response.db_requirement_plan is not None
    requirements = response.db_requirement_plan.requirements
    assert len(requirements) == 1
    assert requirements[0].kind == ServiceHostDbRequirementKind.ontology_replica
    assert requirements[0].package_name == "content-ontology"
    assert requirements[0].authority is False
    assert response.projection_runtime_requirement_plan is not None
    assert response.projection_runtime_requirement_plan.requirements == []


def test_host_contract_semantic_projection_runtime_requirements_are_typed() -> None:
    requirements = projection_runtime_requirements_for_semantic_contracts(
        provider_key="aware-service-host",
        contracts=(
            AWARE_CODE_SEMANTIC_CONTRACT,
            AWARE_API_SEMANTIC_CONTRACT,
            AWARE_SERVICE_SEMANTIC_CONTRACT,
        ),
        kind=ServiceHostProjectionRuntimeRequirementKind.activation_projection,
        role="service_activation_projection",
    )

    assert requirements
    all_projection_names = {
        projection_name
        for requirement in requirements
        for projection_name in requirement.projection_names
    }
    assert {"CodePackage", "ApiPackage", "ServicePackage"} <= all_projection_names
    assert all(requirement.required is True for requirement in requirements)


def test_host_contract_generic_fallback_hashes_local_state_manifest(
    tmp_path: Path,
) -> None:
    service_toml_path = tmp_path / "services" / "meta" / "aware.service.toml"
    local_state_manifest = service_toml_path.parent / "db" / "aware.toml"
    local_state_sql = service_toml_path.parent / "db" / "sql" / "temporal.sql"
    local_state_manifest.parent.mkdir(parents=True, exist_ok=True)
    local_state_sql.parent.mkdir(parents=True, exist_ok=True)
    local_state_manifest.write_text("aware = 1\n", encoding="utf-8")
    local_state_sql.write_text(
        "CREATE TABLE temporal_session (id UUID PRIMARY KEY NOT NULL);\n",
        encoding="utf-8",
    )
    _write_service_toml(
        service_toml_path,
        object_config_graph_manifest="db/aware.toml",
    )

    response = resolve_service_host_contract_for_toml(
        service_toml_path=service_toml_path,
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )

    assert response.db_requirement_plan is not None
    requirements = response.db_requirement_plan.requirements
    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.kind == ServiceHostDbRequirementKind.local_state
    assert requirement.role == "temporal_session_state"
    assert requirement.manifest_paths == [local_state_manifest.resolve().as_posix()]
    assert requirement.db_schema_hash is not None
    assert requirement.db_schema_hash.startswith("sha256:")
    assert requirement.authority is False


def test_host_contract_ontology_provider_scopes_authority_package_manifests(
    tmp_path: Path,
) -> None:
    content_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="content",
        package_name="content-ontology",
        fqn_prefix="aware_content",
    )
    service_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="service",
        package_name="service-ontology",
        fqn_prefix="aware_service",
    )
    runtime_manifest_path = (
        tmp_path / ".aware" / "environment" / "runtime" / "environment.manifest.json"
    )
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text(
        json.dumps(
            {
                "ocg_hash": "sha256:kernel-composition",
                "modules": [
                    {
                        "module_id": "content",
                        "manifest_path": content_manifest_path.relative_to(
                            tmp_path
                        ).as_posix(),
                    },
                    {
                        "module_id": "service",
                        "manifest_path": service_manifest_path.relative_to(
                            tmp_path
                        ).as_posix(),
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    service_toml_path = tmp_path / "services" / "ontology" / "aware.service.toml"
    _write_service_toml(
        service_toml_path,
        entrypoint="aware_ontology_service.host_contract:resolve_service_host_contract",
    )

    response = resolve_service_host_contract_for_toml(
        service_toml_path=service_toml_path,
        target=ServiceHostContractTargetInput(
            runtime_manifest_path=runtime_manifest_path,
            authority_root=tmp_path,
            ontology_authority_package_names=("service-ontology",),
            implementation_toml_paths=(service_toml_path,),
        ),
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )

    assert response.db_requirement_plan is not None
    requirements = response.db_requirement_plan.requirements
    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.kind == ServiceHostDbRequirementKind.ontology_authority
    assert requirement.package_names == ["service-ontology"]
    assert requirement.manifest_paths == [service_manifest_path.as_posix()]
    assert requirement.sql_roots == [
        service_manifest_path.parents[3].joinpath("sql").as_posix()
    ]
    assert content_manifest_path.as_posix() not in requirement.manifest_paths
    assert requirement.db_schema_hash
    assert requirement.db_schema_hash != "sha256:kernel-composition"


def test_host_contract_node_ontology_manifest_authority_is_explicit(
    tmp_path: Path,
) -> None:
    content_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="content",
        package_name="content-ontology",
        fqn_prefix="aware_content",
    )
    service_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="service",
        package_name="service-ontology",
        fqn_prefix="aware_service",
    )
    runtime_manifest_path = (
        tmp_path / ".aware" / "service" / "runtime" / "environment.manifest.json"
    )
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text(
        json.dumps(
            {
                "ocg_hash": "sha256:service-protocol-shell",
                "modules": [
                    {
                        "module_id": "content",
                        "manifest_path": content_manifest_path.relative_to(
                            tmp_path
                        ).as_posix(),
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    service_toml_path = tmp_path / "services" / "ontology" / "aware.service.toml"
    _write_service_toml(
        service_toml_path,
        entrypoint="aware_ontology_service.host_contract:resolve_service_host_contract",
    )

    response = resolve_service_host_contract_for_toml(
        service_toml_path=service_toml_path,
        target=ServiceHostContractTargetInput(
            runtime_manifest_path=runtime_manifest_path,
            authority_root=tmp_path,
            ontology_authority_source_kind="node_ontology_manifest",
            ontology_authority_package_names=(
                "content-ontology",
                "service-ontology",
            ),
            implementation_toml_paths=(service_toml_path,),
        ),
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )

    assert response.db_requirement_plan is not None
    requirements = response.db_requirement_plan.requirements
    assert len(requirements) == 1
    requirement = requirements[0]
    assert requirement.kind == ServiceHostDbRequirementKind.ontology_authority
    assert requirement.package_names == ["content-ontology", "service-ontology"]
    assert requirement.manifest_paths == [
        content_manifest_path.as_posix(),
        service_manifest_path.as_posix(),
    ]


def test_host_contract_ontology_authority_ignores_composition_advertisement(
    tmp_path: Path,
) -> None:
    content_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="content",
        package_name="content-ontology",
        fqn_prefix="aware_content",
    )
    service_manifest_path = _write_ontology_authority_module(
        repo_root=tmp_path,
        module_name="service",
        package_name="service-ontology",
        fqn_prefix="aware_service",
    )
    runtime_manifest_path = (
        tmp_path / ".aware" / "environment" / "runtime" / "environment.manifest.json"
    )
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_manifest_path.write_text(
        json.dumps(
            {
                "ocg_hash": "sha256:kernel-composition",
                "modules": [
                    {
                        "module_id": "content",
                        "manifest_path": content_manifest_path.relative_to(
                            tmp_path
                        ).as_posix(),
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    service_toml_path = tmp_path / "services" / "ontology" / "aware.service.toml"
    _write_service_toml(
        service_toml_path,
        entrypoint="aware_ontology_service.host_contract:resolve_service_host_contract",
    )

    response = resolve_service_host_contract_for_toml(
        service_toml_path=service_toml_path,
        target=ServiceHostContractTargetInput(
            runtime_manifest_path=runtime_manifest_path,
            authority_root=tmp_path,
            ontology_authority_package_names=(
                "content-ontology",
                "service-ontology",
            ),
            implementation_toml_paths=(service_toml_path,),
        ),
        backend=ServiceHostContractBackendInput(
            persistence_backend="db",
            adapter="postgres",
            database_url_present=True,
        ),
    )

    assert response.db_requirement_plan is not None
    requirement = response.db_requirement_plan.requirements[0]
    assert requirement.kind == ServiceHostDbRequirementKind.ontology_authority
    assert requirement.manifest_paths == [
        content_manifest_path.as_posix(),
        service_manifest_path.as_posix(),
    ]
