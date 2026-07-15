from __future__ import annotations

from pathlib import Path
import tomllib


_REPO_ROOT = Path(__file__).resolve().parents[4]


def _environment_api_root() -> Path:
    return _REPO_ROOT / "apis" / "environment"


def test_environment_api_declares_product_ab_generation_targets() -> None:
    payload = tomllib.loads(
        (_environment_api_root() / "aware.api.toml").read_text(encoding="utf-8")
    )

    assert payload["api"]["package_name"] == "environment-service-api"
    assert payload["api"]["fqn_prefix"] == "aware_environment_service_api"
    assert payload["targets"]["python"]["public_package"]["package_dir"] == (
        "aware_environment_service_api"
    )
    assert payload["targets"]["python"]["service_protocol"]["package_dir"] == (
        "aware_environment_service_protocol"
    )
    assert payload["dependencies"] == [{"package_name": "environment-service-dto"}]
    assert payload["semantic_package_exports"] == [
        {
            "kind": "api_dto",
            "package_name": "environment-service-dto",
            "manifest_path": "dto/aware.toml",
        }
    ]


def test_environment_api_lifts_canonical_runtime_operations() -> None:
    source = (
        _environment_api_root() / "bindings" / "environment.apis.aware"
    ).read_text(encoding="utf-8")

    legacy_environment_dto_import = ".".join(("aware_comms", "models", "environment"))
    assert f"{legacy_environment_dto_import}." not in source

    for endpoint in (
        "fetch_capabilities",
        "describe_environment_config",
        "describe_environment",
        "describe_environment_topology",
        "describe_environment_status",
        "ensure_ready",
        "get_lane_head",
        "get_object_instance_graph_commit",
        "resolve_runtime_refs",
        "configure_service_api_dependency_routes",
        "ensure_environment_ontology_runtime",
        "upsert_environment_profile",
        "provision_environment_profile",
        "invoke_function",
    ):
        assert f"endpoint {endpoint} " in source

    assert "NetworkOperation" not in source
    assert "environment_experience" not in source
    assert "apply_environment_experience_programs" not in source
    assert "apply_program_ref" not in source
    assert "submit_program_turn" not in source
    assert "run_program" not in source
    assert "get_turn_execution" not in source


def test_environment_api_references_api_owned_environment_dto_refs() -> None:
    source = (
        _environment_api_root() / "bindings" / "environment.apis.aware"
    ).read_text(encoding="utf-8")

    for dto_ref in (
        "aware_environment_service_dto.environment.FetchCapabilitiesRequest",
        "aware_environment_service_dto.environment.FetchCapabilitiesResponse",
        "aware_environment_service_dto.environment.DescribeEnvironmentConfigRequest",
        "aware_environment_service_dto.environment.DescribeEnvironmentConfigResponse",
        "aware_environment_service_dto.environment.DescribeEnvironmentRequest",
        "aware_environment_service_dto.environment.DescribeEnvironmentResponse",
        "aware_environment_service_dto.environment.DescribeEnvironmentTopologyRequest",
        "aware_environment_service_dto.environment.DescribeEnvironmentTopologyResponse",
        "aware_environment_service_dto.environment.DescribeEnvironmentStatusRequest",
        "aware_environment_service_dto.environment.DescribeEnvironmentStatusResponse",
        "aware_environment_service_dto.environment.EnsureReadyRequest",
        "aware_environment_service_dto.environment.EnsureReadyResponse",
        "aware_environment_service_dto.environment.GetLaneHeadRequest",
        "aware_environment_service_dto.environment.GetLaneHeadResponse",
        "aware_environment_service_dto.environment.GetObjectInstanceGraphCommitRequest",
        "aware_environment_service_dto.environment.GetObjectInstanceGraphCommitResponse",
        "aware_environment_service_dto.environment.ResolveRuntimeRefsRequest",
        "aware_environment_service_dto.environment.ResolveRuntimeRefsResponse",
        "aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesRequest",
        "aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesResponse",
        "aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeRequest",
        "aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeResponse",
        "aware_environment_service_dto.environment.UpsertEnvironmentProfileRequest",
        "aware_environment_service_dto.environment.UpsertEnvironmentProfileResponse",
        "aware_environment_service_dto.environment.ProvisionEnvironmentProfileRequest",
        "aware_environment_service_dto.environment.ProvisionEnvironmentProfileResponse",
        "aware_environment_service_dto.environment.InvokeFunctionRequest",
        "aware_environment_service_dto.environment.InvokeFunctionResponse",
    ):
        assert dto_ref in source

    for forbidden_ref in (
        "aware_environment_service_dto.environment.ApplyProgramRefRequest",
        "aware_environment_service_dto.environment.ApplyProgramRefResponse",
        "aware_environment_service_dto.environment.SubmitProgramTurnRequest",
        "aware_environment_service_dto.environment.SubmitProgramTurnResponse",
        "aware_environment_service_dto.environment.RunProgramRequest",
        "aware_environment_service_dto.environment.RunProgramResponse",
        "aware_environment_service_dto.environment.GetTurnExecutionRequest",
        "aware_environment_service_dto.environment.GetTurnExecutionResponse",
    ):
        assert forbidden_ref not in source


def test_environment_dto_does_not_reach_structure_api() -> None:
    payload = tomllib.loads(
        (_environment_api_root() / "dto" / "aware.toml").read_text(encoding="utf-8")
    )
    dependencies = [
        dependency["package_name"] for dependency in payload.get("dependencies", [])
    ]
    assert "structure-api" not in dependencies

    source = (
        _environment_api_root() / "dto" / "aware" / "environment" / "environment.aware"
    ).read_text(encoding="utf-8")

    compiler_operation = (
        _environment_api_root()
        / "dto"
        / "aware"
        / "environment"
        / "compiler_service_operation.aware"
    )
    assert "aware_structure_api" not in source
    assert source.count("bundle_release_identity JsonObject?") == 3
    assert not compiler_operation.exists()
