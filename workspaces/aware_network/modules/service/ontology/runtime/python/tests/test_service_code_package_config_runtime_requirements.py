from __future__ import annotations

from aware_api_runtime.semantic_contract import AWARE_API_SEMANTIC_CONTRACT
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT
from aware_service_runtime.host_contract import (
    ServiceHostProjectionRuntimeRequirementKind,
    projection_runtime_requirements_for_semantic_contracts,
)
from aware_service_runtime.semantic_contract import AWARE_SERVICE_SEMANTIC_CONTRACT


def test_service_activation_requires_code_package_config_projection() -> None:
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

    all_projection_names = {
        projection_name
        for requirement in requirements
        for projection_name in requirement.projection_names
    }

    assert {
        "ApiCall",
        "CodePackageConfig",
        "Service",
        "ServiceConfig",
    } <= all_projection_names


def test_service_runtime_scopes_code_package_config_to_code_ontology() -> None:
    runtime = AWARE_SERVICE_SEMANTIC_CONTRACT.materialization_runtime_for()[0]
    projection_packages = {
        package.package_name: package.projection_names
        for package in runtime.runtime_projection_packages
    }

    assert projection_packages["code-ontology"] == (
        "CodePackage",
        "CodePackageConfig",
    )
    assert projection_packages["api-ontology"] == ("ApiPackage",)
    assert projection_packages["service-ontology"] == (
        "Service",
        "ServiceConfig",
        "ServicePackage",
    )
