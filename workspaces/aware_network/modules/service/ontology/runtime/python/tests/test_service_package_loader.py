from __future__ import annotations

import pytest
from aware_service_runtime.manifest.loader import (
    AwareServiceTomlError,
    load_aware_service_toml_spec_from_text,
)
from aware_service_runtime.manifest.spec import (
    AwareServiceCompilationMode,
    AwareServiceDependencyKind,
    AwareServiceHostActivationMode,
)


def test_loader_defaults_compilation_mode_to_raw_xor() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"
""",
        toml_path="aware.service.toml",
    )

    assert spec.build.compilation_mode == AwareServiceCompilationMode.raw_xor


def test_loader_defaults_host_activation_inputs() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"
""",
        toml_path="aware.service.toml",
    )

    assert spec.host.service_surface == "service"
    assert (
        spec.host.activation_mode
        == AwareServiceHostActivationMode.materialize_and_load_committed
    )
    assert spec.host.materialize_on_start is True


def test_loader_accepts_service_ontology_compilation_mode() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"
compilation_mode = "service_ontology"
""",
        toml_path="aware.service.toml",
    )

    assert spec.build.compilation_mode == AwareServiceCompilationMode.service_ontology


def test_loader_accepts_host_and_api_service_protocol_intent() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"

[host]
service_surface = "service"
activation_mode = "materialize_and_load_committed"
materialize_on_start = true

[[dependencies]]
package_name = "home-story-api"
version_number = 3
kind = "api_service_protocol"
""",
        toml_path="aware.service.toml",
    )

    assert spec.dependencies[0].kind == AwareServiceDependencyKind.api_service_protocol
    assert spec.dependencies[0].expected_hash_sha256 is None


def test_loader_accepts_node_host_service_surface() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "aware-node-service"
fqn_prefix = "aware_node_service"

[build]
sources_dir = "bindings"

[host]
service_surface = "node_host"
activation_mode = "materialize_and_load_committed"
materialize_on_start = false
""",
        toml_path="aware.service.toml",
    )

    assert spec.host.service_surface == "node_host"
    assert spec.host.materialize_on_start is False


def test_loader_accepts_api_invocation_dependency_without_hash() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "environment-service"
fqn_prefix = "environment_service"

[build]
sources_dir = "services"

[[dependencies]]
package_name = "environment-service-api"
kind = "api_service_protocol"

[[dependencies]]
package_name = "meta-service-api"
version_number = 1
kind = "api_invocation"
""",
        toml_path="aware.service.toml",
    )

    assert spec.dependencies[0].kind == AwareServiceDependencyKind.api_service_protocol
    assert spec.dependencies[1].kind == AwareServiceDependencyKind.api_invocation
    assert spec.dependencies[1].package_name == "meta-service-api"
    assert spec.dependencies[1].expected_hash_sha256 is None


def test_loader_accepts_api_invocation_route_authority_selector() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "environment-service"
fqn_prefix = "environment_service"

[build]
sources_dir = "services"

[[dependencies]]
package_name = "ontology-service-api"
version_number = 1
kind = "api_invocation"
route_authority_selector = { provider_set_id = "kernel.ontology_authority.v1", workspace_deployment_channel = "stable" }
""",
        toml_path="aware.service.toml",
    )

    selector = spec.dependencies[0].route_authority_selector
    assert selector is not None
    assert selector.to_payload() == {
        "provider_set_id": "kernel.ontology_authority.v1",
        "workspace_deployment_channel": "stable",
    }


def test_loader_rejects_route_authority_selector_on_protocol_provider_dependency() -> (
    None
):
    with pytest.raises(AwareServiceTomlError, match="api_invocation"):
        _ = load_aware_service_toml_spec_from_text(
            toml_text="""
aware_service = 1

[service]
package_name = "ontology-service"
fqn_prefix = "ontology_service"

[build]
sources_dir = "services"

[[dependencies]]
package_name = "ontology-service-api"
kind = "api_service_protocol"
route_authority_selector = { provider_set_id = "kernel.ontology_authority.v1" }
""",
            toml_path="aware.service.toml",
        )


def test_loader_rejects_unknown_compilation_mode() -> None:
    with pytest.raises(AwareServiceTomlError, match="compilation_mode"):
        _ = load_aware_service_toml_spec_from_text(
            toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"
compilation_mode = "future_magic"
""",
            toml_path="aware.service.toml",
        )


def test_loader_rejects_authored_api_service_protocol_hash() -> None:
    with pytest.raises(AwareServiceTomlError, match="derived lock truth"):
        _ = load_aware_service_toml_spec_from_text(
            toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"

[[dependencies]]
package_name = "home-story-api"
kind = "api_service_protocol"
expected_hash_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
""",
            toml_path="aware.service.toml",
        )


def test_loader_rejects_invalid_dependency_hash() -> None:
    with pytest.raises(AwareServiceTomlError, match="sha256"):
        _ = load_aware_service_toml_spec_from_text(
            toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"

[[dependencies]]
package_name = "home-story-api"
kind = "api_service_protocol"
expected_hash_sha256 = "not-a-real-hash"
""",
            toml_path="aware.service.toml",
        )


def test_loader_rejects_parent_traversal_sources_dir() -> None:
    with pytest.raises(AwareServiceTomlError, match="sources_dir"):
        _ = load_aware_service_toml_spec_from_text(
            toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "../services"
""",
            toml_path="aware.service.toml",
        )


def test_loader_preserves_force_fresh_scan_false() -> None:
    spec = load_aware_service_toml_spec_from_text(
        toml_text="""
aware_service = 1

[service]
package_name = "demo-service"
fqn_prefix = "demo_service"

[build]
sources_dir = "services"
force_fresh_scan = false
""",
        toml_path="aware.service.toml",
    )

    assert spec.build.force_fresh_scan is False
