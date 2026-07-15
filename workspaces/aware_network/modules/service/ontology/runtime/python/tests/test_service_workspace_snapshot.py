from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from aware_code.types import JsonArray
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_service_ontology.service.service_package import ServicePackage
from aware_service_ontology.service.service_package_implementation_package import (
    ServicePackageImplementationPackage,
)
from aware_service_runtime.workspace import (
    build_service_workspace_snapshot_from_package,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_committed_snapshot_converts_workspace_relative_implementation_root(
    tmp_path: Path,
) -> None:
    service_root = tmp_path / "services" / "aware_home_devices"
    _write(service_root / "aware.service.toml", "aware_service = 1\n")
    _write(
        service_root / "bindings" / "aware_home_devices.services.aware",
        "service home_devices {}\n",
    )
    _write(
        service_root / "pyproject.toml",
        '[project]\nname = "aware-home-devices-service"\n',
    )
    _write(service_root / "aware_home_devices_service" / "__init__.py", "\n")

    service_package = ServicePackage.model_construct(
        id=uuid4(),
        name="aware-home-devices-service",
        fqn_prefix="aware_home_devices_service",
        version_number=1,
        title="Aware Home Devices Service",
        description=None,
        aware_service_version=1,
        manifest_relative_path="services/aware_home_devices/aware.service.toml",
        package_root="services/aware_home_devices",
        sources_root="services/aware_home_devices/bindings",
        include_paths=JsonArray(["**/*.aware"]),
        exclude_paths=JsonArray([]),
        force_fresh_scan=True,
        compilation_mode="service_ontology",
        service_surface="service",
        activation_mode="materialize_and_load_committed",
        materialize_on_start=True,
        dependencies=JsonArray([]),
        implementation_packages=[
            ServicePackageImplementationPackage.model_construct(
                id=uuid4(),
                service_package_id=uuid4(),
                code_package_id=uuid4(),
                package_name="aware-home-devices-service",
                language=CodeLanguage.python,
                import_root="aware_home_devices_service",
                manifest_relative_path="services/aware_home_devices/pyproject.toml",
                package_root="services/aware_home_devices",
                entrypoint=(
                    "aware_home_devices_service.service_bindings:"
                    "build_service_bindings"
                ),
                role="service_bindings",
                include_paths=JsonArray(["aware_home_devices_service/**/*.py"]),
                exclude_paths=JsonArray([]),
            )
        ],
    )

    snapshot = build_service_workspace_snapshot_from_package(
        service_package=service_package,
        materialized_workspace_root=tmp_path,
    )

    implementation_package = snapshot.spec.implementation.packages[0]
    assert snapshot.package_root == service_root.resolve()
    assert implementation_package.package_root == "."
    assert implementation_package.manifest_path == "pyproject.toml"
    assert snapshot.source_files == (
        Path("bindings/aware_home_devices.services.aware"),
    )


def test_committed_snapshot_preserves_dependency_route_authority_selector(
    tmp_path: Path,
) -> None:
    service_root = tmp_path / "services" / "aware_environment"
    _write(service_root / "aware.service.toml", "aware_service = 1\n")
    _write(
        service_root / "bindings" / "aware_environment.services.aware",
        "service aware_environment {}\n",
    )

    service_package = ServicePackage.model_construct(
        id=uuid4(),
        name="aware-environment-service",
        fqn_prefix="aware_environment_service",
        version_number=1,
        aware_service_version=1,
        manifest_relative_path="services/aware_environment/aware.service.toml",
        package_root="services/aware_environment",
        sources_root="services/aware_environment/bindings",
        include_paths=JsonArray(["**/*.aware"]),
        exclude_paths=JsonArray([]),
        force_fresh_scan=True,
        compilation_mode="service_ontology",
        service_surface="service",
        activation_mode="materialize_and_load_committed",
        materialize_on_start=True,
        dependencies=JsonArray(
            [
                {
                    "package_name": "ontology-service-api",
                    "version_number": 1,
                    "kind": "api_invocation",
                    "expected_hash_sha256": None,
                    "route_authority_selector": {
                        "provider_set_id": "kernel.ontology_authority.v1",
                        "workspace_deployment_channel": "stable",
                    },
                }
            ]
        ),
        implementation_packages=[],
    )

    snapshot = build_service_workspace_snapshot_from_package(
        service_package=service_package,
        materialized_workspace_root=tmp_path,
    )

    selector = snapshot.spec.dependencies[0].route_authority_selector
    assert selector is not None
    assert selector.to_payload() == {
        "provider_set_id": "kernel.ontology_authority.v1",
        "workspace_deployment_channel": "stable",
    }
