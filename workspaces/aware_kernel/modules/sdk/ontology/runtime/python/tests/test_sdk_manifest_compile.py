# pyright: reportImplicitRelativeImport=false
from __future__ import annotations

import json
from pathlib import Path

import pytest

from _sdk_runtime_test_paths import REPO_ROOT


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(text, encoding="utf-8")


def _create_sdk_package(
    tmp_path: Path, *, compilation_mode: str = "sdk_ontology"
) -> Path:
    package_root = tmp_path / "sdks" / "workspace_client"
    _write(
        package_root / "aware.sdk.toml",
        f"""
aware_sdk = 1

[sdk]
package_name = "workspace-sdk"
fqn_prefix = "workspace_sdk"

[build]
sources_dir = "sdks"
compilation_mode = "{compilation_mode}"
""",
    )
    _write(
        package_root / "sdks" / "workspace_client.aware",
        """\
sdk workspace_client {
    "Workspace local SDK."
    api workspace;

    surface local_status {
        "Local status surface."
        method retrieve {
            "Read current local status."
            operation load_status;
            method_family retrieve;
            effect read;
            mutation_scope none;
            confirmation_policy none;
            execution_mode request_response;
            runtime_binding_kind local_handler;
        }
    }

    operation load_status {
        "Load status."
        endpoint workspace.status.get;
    }
}
""",
    )
    return package_root / "aware.sdk.toml"


def _create_composed_sdk_package(tmp_path: Path) -> Path:
    package_root = tmp_path / "sdks" / "aware_dev"
    _write(
        package_root / "aware.sdk.toml",
        """
aware_sdk = 1

[sdk]
package_name = "aware-dev-sdk"
fqn_prefix = "aware_dev_sdk"

[build]
sources_dir = "sdks"
compilation_mode = "sdk_ontology"

[[dependencies]]
kind = "sdk_package"
package_name = "workspace-sdk"
version_number = 1
""",
    )
    _write(
        package_root / "sdks" / "aware_dev_sdk.aware",
        """\
sdk aware_dev_sdk {
    "Developer SDK."
    api workspace;

    operation publish_workspace {
        "Publish through Workspace after local materialization."
        endpoint workspace.publish.publish;
        operation workspace_sdk.materialize_workspace;
    }
}
""",
    )
    return package_root / "aware.sdk.toml"


def test_compile_sdk_workspace_builds_ontology_mode_plan(tmp_path: Path) -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    sdk_toml_path = _create_sdk_package(tmp_path)

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=tmp_path,
        emit_compile_plan=True,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "workspace-sdk"
    assert result.compile_plan.fqn_prefix == "workspace_sdk"
    assert result.compile_plan.source_files == ("sdks/workspace_client.aware",)

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "workspace_client"
    assert sdk_config.apis[0].api_ref == "workspace"
    operation = sdk_config.operations[0]
    assert operation.name == "load_status"
    endpoint = operation.api_endpoints[0]
    assert endpoint.name == "get"
    assert endpoint.endpoint_ref == "workspace.status.get"
    assert endpoint.api_ref == "workspace"
    assert endpoint.capability_name == "status"
    assert endpoint.order == 1
    assert operation.sdk_operation_dependencies == ()
    surface = sdk_config.surfaces[0]
    assert surface.name == "local_status"
    method = surface.methods[0]
    assert method.name == "retrieve"
    assert method.operation_ref == "workspace_client.load_status"
    assert method.operation_name == "load_status"
    assert method.method_family == "retrieve"
    assert method.effect == "read"
    assert method.mutation_scope == "none"
    assert method.confirmation_policy == "none"
    assert method.execution_mode == "request_response"
    assert method.runtime_binding_kind == "local_handler"

    assert result.compile_plan_artifact is not None
    payload = json.loads(result.compile_plan_artifact.path.read_text(encoding="utf-8"))
    assert (
        payload["sdk_configs"][0]["operations"][0]["api_endpoints"][0]["endpoint_ref"]
        == "workspace.status.get"
    )
    assert (
        payload["sdk_configs"][0]["surfaces"][0]["methods"][0]["operation_ref"]
        == "workspace_client.load_status"
    )


def test_compile_sdk_workspace_builds_operation_dependency_plan(
    tmp_path: Path,
) -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    sdk_toml_path = _create_composed_sdk_package(tmp_path)

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=tmp_path,
        emit_compile_plan=True,
    )

    assert result.compile_plan is not None
    operation = result.compile_plan.sdk_configs[0].operations[0]
    assert operation.name == "publish_workspace"
    assert operation.api_endpoints[0].endpoint_ref == "workspace.publish.publish"
    dependency = operation.sdk_operation_dependencies[0]
    assert dependency.target_operation_ref == "workspace_sdk.materialize_workspace"
    assert dependency.target_sdk_name == "workspace_sdk"
    assert dependency.target_operation_name == "materialize_workspace"
    assert dependency.target_package_name == "workspace-sdk"
    assert dependency.order == 1

    assert result.compile_plan_artifact is not None
    payload = json.loads(result.compile_plan_artifact.path.read_text(encoding="utf-8"))
    payload_dependency = payload["sdk_configs"][0]["operations"][0][
        "sdk_operation_dependencies"
    ][0]
    assert payload_dependency["target_operation_ref"] == (
        "workspace_sdk.materialize_workspace"
    )
    assert payload_dependency["target_package_name"] == "workspace-sdk"


def test_compile_sdk_workspace_raw_mode_skips_compile_plan(tmp_path: Path) -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    sdk_toml_path = _create_sdk_package(tmp_path, compilation_mode="raw_xor")

    result = compile_sdk_workspace(toml_path=sdk_toml_path, repo_root=tmp_path)

    assert result.compile_plan is None
    assert result.compile_plan_artifact is None


def test_compile_sdk_workspace_rejects_undeclared_endpoint_api(tmp_path: Path) -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    sdk_toml_path = _create_sdk_package(tmp_path)
    source_path = sdk_toml_path.parent / "sdks" / "workspace_client.aware"
    _write(
        source_path,
        """\
sdk workspace_client {
    api workspace;

    operation load_status {
        endpoint identity.status.get;
    }
}
""",
    )

    with pytest.raises(ValueError, match="undeclared api endpoint"):
        _ = compile_sdk_workspace(toml_path=sdk_toml_path, repo_root=tmp_path)


def test_compile_sdk_workspace_rejects_undeclared_operation_dependency(
    tmp_path: Path,
) -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    sdk_toml_path = _create_sdk_package(tmp_path)
    source_path = sdk_toml_path.parent / "sdks" / "workspace_client.aware"
    _write(
        source_path,
        """\
sdk workspace_client {
    api workspace;

    operation publish_workspace {
        endpoint workspace.publish.publish;
        operation workspace_sdk.materialize_workspace;
    }
}
""",
    )

    with pytest.raises(ValueError, match="not declared"):
        _ = compile_sdk_workspace(toml_path=sdk_toml_path, repo_root=tmp_path)


def test_compile_sdk_workspace_rejects_unknown_surface_operation(
    tmp_path: Path,
) -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    sdk_toml_path = _create_sdk_package(tmp_path)
    source_path = sdk_toml_path.parent / "sdks" / "workspace_client.aware"
    _write(
        source_path,
        """\
sdk workspace_client {
    api workspace;

    surface local_status {
        method retrieve {
            operation missing_status;
            method_family retrieve;
        }
    }

    operation load_status {
        endpoint workspace.status.get;
    }
}
""",
    )

    with pytest.raises(ValueError, match="unknown local operation"):
        _ = compile_sdk_workspace(toml_path=sdk_toml_path, repo_root=tmp_path)


def test_compile_sdk_workspace_rejects_invalid_method_family(
    tmp_path: Path,
) -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    sdk_toml_path = _create_sdk_package(tmp_path)
    source_path = sdk_toml_path.parent / "sdks" / "workspace_client.aware"
    _write(
        source_path,
        """\
sdk workspace_client {
    api workspace;

    surface local_status {
        method status {
            operation load_status;
            method_family status;
        }
    }

    operation load_status {
        endpoint workspace.status.get;
    }
}
""",
    )

    with pytest.raises(ValueError, match="invalid method_family"):
        _ = compile_sdk_workspace(toml_path=sdk_toml_path, repo_root=tmp_path)


def test_compile_workspace_aware_sdk_source_builds_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = (
        repo_root
        / "workspaces"
        / "aware_workspace"
        / "sdks"
        / "workspace"
        / "aware"
        / "aware.sdk.toml"
    )

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "workspace-sdk"
    assert result.compile_plan.fqn_prefix == "aware_workspace_sdk"
    assert result.compile_plan.source_files == ("workspace_sdk.aware",)
    dependencies = {
        (
            dependency.kind.value,
            dependency.package_name,
            dependency.version_number,
        )
        for dependency in result.snapshot.spec.dependencies
    }
    assert ("sdk_package", "filesystem-sdk", 1) in dependencies

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "workspace_sdk"
    assert sdk_config.apis[0].api_ref == "workspace"

    operations = {operation.name: operation for operation in sdk_config.operations}
    assert {
        "load_status",
        "load_semantic_source",
        "materialize_workspace",
        "build_workspace",
        "test_revision",
    } <= set(operations)
    assert operations["load_status"].api_endpoints[0].endpoint_ref == (
        "workspace.status.status"
    )
    assert operations["load_status"].api_endpoints[0].capability_name == ("status")
    assert operations["load_semantic_source"].api_endpoints[0].endpoint_ref == (
        "workspace.semantic_source.semantic_source"
    )
    assert operations["build_workspace"].api_endpoints[0].endpoint_ref == (
        "workspace.build.build"
    )


def test_compile_filesystem_aware_sdk_source_builds_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = (
        repo_root
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "filesystem"
        / "sdks"
        / "filesystem"
        / "aware"
        / "aware.sdk.toml"
    )

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "filesystem-sdk"
    assert result.compile_plan.fqn_prefix == "aware_file_system_sdk"
    assert result.compile_plan.source_files == ("filesystem_sdk.aware",)
    dependencies = {
        (
            dependency.kind.value,
            dependency.package_name,
            dependency.version_number,
        )
        for dependency in result.snapshot.spec.dependencies
    }
    assert dependencies == {
        ("api_package", "file-system-service-api", 1),
        ("api_package", "code-service-api", 1),
    }

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "filesystem_sdk"
    assert sdk_config.apis[0].api_ref == "filesystem"

    operations = {operation.name: operation for operation in sdk_config.operations}
    assert set(operations) == {
        "verify_root",
        "scan_snapshot",
        "collect_delta",
        "apply_delta",
        "resolve_backend_capabilities",
    }
    assert operations["verify_root"].api_endpoints[0].endpoint_ref == (
        "filesystem.root.verify"
    )
    assert operations["scan_snapshot"].api_endpoints[0].endpoint_ref == (
        "filesystem.snapshot.scan"
    )
    assert operations["collect_delta"].api_endpoints[0].endpoint_ref == (
        "filesystem.delta.collect"
    )
    assert operations["apply_delta"].api_endpoints[0].endpoint_ref == (
        "filesystem.delta.apply"
    )
    assert operations["resolve_backend_capabilities"].api_endpoints[0].endpoint_ref == (
        "filesystem.backend.capabilities"
    )


def test_compile_skill_aware_sdk_source_builds_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = repo_root / "sdks" / "skill" / "aware" / "aware.sdk.toml"

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "skill-sdk"
    assert result.compile_plan.fqn_prefix == "aware_skill_sdk"
    assert result.compile_plan.source_files == ("skill_sdk.aware",)

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "skill_sdk"
    assert sdk_config.apis[0].api_ref == "skill"
    operation = sdk_config.operations[0]
    assert operation.name == "invoke_skill"
    endpoint = operation.api_endpoints[0]
    assert endpoint.endpoint_ref == "skill.invoke.invoke"
    assert endpoint.api_ref == "skill"
    assert endpoint.capability_name == "invoke"
    assert endpoint.name == "invoke"


def test_compile_agent_aware_sdk_source_builds_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = (
        repo_root
        / "workspaces"
        / "aware_agent"
        / "modules"
        / "agent"
        / "sdks"
        / "agent"
        / "aware"
        / "aware.sdk.toml"
    )

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "agent-sdk"
    assert result.compile_plan.fqn_prefix == "aware_agent_sdk"
    assert result.compile_plan.source_files == ("agent_sdk.aware",)

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "agent_sdk"
    assert sdk_config.apis[0].api_ref == "agent"

    operations = {operation.name: operation for operation in sdk_config.operations}
    assert {
        "start_session",
        "send_input",
        "subscribe_session",
        "cancel_session",
        "get_session",
    } <= set(operations)
    assert operations["start_session"].api_endpoints[0].endpoint_ref == (
        "agent.start_session.start_session"
    )
    assert operations["send_input"].api_endpoints[0].endpoint_ref == (
        "agent.send_session_input.send_session_input"
    )
    assert operations["subscribe_session"].api_endpoints[0].endpoint_ref == (
        "agent.subscribe_session.subscribe_session"
    )
    assert operations["cancel_session"].api_endpoints[0].endpoint_ref == (
        "agent.cancel_session.cancel_session"
    )
    assert operations["get_session"].api_endpoints[0].endpoint_ref == (
        "agent.get_session.get_session"
    )


def test_compile_network_aware_sdk_source_builds_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = repo_root / "sdks" / "network" / "aware.sdk.toml"

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "network-sdk"
    assert result.compile_plan.fqn_prefix == "aware_network_sdk"
    assert result.compile_plan.source_files == ("aware/network_sdk.aware",)

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "network_sdk"
    assert sdk_config.apis[0].api_ref == "network"

    operations = {operation.name: operation for operation in sdk_config.operations}
    assert set(operations) == {
        "register_node",
        "upsert_peer",
        "list_peers",
        "publish_hosted_service",
        "list_hosted_services",
        "resolve_hosted_service_routes",
    }
    assert operations["register_node"].api_endpoints[0].endpoint_ref == (
        "network.node.register"
    )
    assert operations["resolve_hosted_service_routes"].api_endpoints[
        0
    ].endpoint_ref == ("network.route.resolve_hosted_service_routes")


def test_compile_environment_aware_sdk_source_builds_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = repo_root / "sdks" / "environment" / "aware" / "aware.sdk.toml"

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "environment-sdk"
    assert result.compile_plan.fqn_prefix == "aware_environment_sdk"
    assert result.compile_plan.source_files == ("environment_sdk.aware",)

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "environment_sdk"
    assert sdk_config.apis[0].api_ref == "environment"

    operations = {operation.name: operation for operation in sdk_config.operations}
    assert {
        "ensure_ready",
        "invoke_function",
        "run_program",
        "describe_environment_status",
    } <= set(operations)
    assert operations["ensure_ready"].api_endpoints[0].endpoint_ref == (
        "environment.ready.ensure_ready"
    )
    assert operations["invoke_function"].api_endpoints[0].endpoint_ref == (
        "environment.function_call.invoke_function"
    )


def test_compile_hub_aware_sdk_source_builds_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = repo_root / "sdks" / "hub" / "aware.sdk.toml"

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "hub-sdk"
    assert result.compile_plan.fqn_prefix == "aware_hub_sdk"
    assert result.compile_plan.source_files == ("aware/hub_sdk.aware",)

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "hub_sdk"
    assert sdk_config.apis[0].api_ref == "hub"

    operations = {operation.name: operation for operation in sdk_config.operations}
    assert {
        "discover_public_map",
        "discover_code_package_channel_heads",
        "publish_code_package",
        "resolve_deployment_artifact",
    } <= set(operations)
    assert operations["discover_public_map"].api_endpoints[0].endpoint_ref == (
        "hub.public_map.discover"
    )
    assert operations["resolve_deployment_artifact"].api_endpoints[0].endpoint_ref == (
        "hub.deployment_artifact.resolve"
    )


def test_compile_aware_dev_sdk_source_builds_product_compile_plan() -> None:
    from aware_sdk_runtime.compile import compile_sdk_workspace

    repo_root = REPO_ROOT
    sdk_toml_path = (
        repo_root
        / "workspaces"
        / "aware_dev"
        / "modules"
        / "dev"
        / "sdks"
        / "aware_dev"
        / "aware"
        / "aware.sdk.toml"
    )

    result = compile_sdk_workspace(
        toml_path=sdk_toml_path,
        repo_root=repo_root,
        emit_compile_plan=True,
    )

    assert result.compile_plan is not None
    assert result.compile_plan.package_name == "aware-dev-sdk"
    assert result.compile_plan.fqn_prefix == "aware_dev_sdk"
    assert result.compile_plan.source_files == ("aware_dev_sdk.aware",)

    sdk_config = result.compile_plan.sdk_configs[0]
    assert sdk_config.name == "aware_dev_sdk"
    assert tuple(api.api_ref for api in sdk_config.apis) == (
        "agent",
        "dev",
        "economy",
        "identity",
        "workspace",
    )

    operations = {operation.name: operation for operation in sdk_config.operations}
    assert len(operations) == 34
    assert {
        "economy_ensure_finance_entity",
        "init",
        "session_join",
        "session_status",
        "status",
        "whoami",
        "workspace_build",
        "workspace_commit",
        "workspace_materialize",
        "workspace_publish",
        "workspace_status",
        "workspace_verify",
    }.issubset(operations)
    assert tuple(
        endpoint.endpoint_ref for endpoint in operations["init"].api_endpoints
    ) == ("dev.ensure_dev_session_routes.ensure_dev_session_routes",)
    assert tuple(
        endpoint.endpoint_ref for endpoint in operations["status"].api_endpoints
    ) == ("dev.get_dev_session_status.get_dev_session_status",)
    assert tuple(
        endpoint.endpoint_ref for endpoint in operations["session_join"].api_endpoints
    ) == ("dev.join_dev_session.join_dev_session",)
    assert operations["init"].sdk_operation_dependencies == ()
    assert tuple(
        dependency.target_operation_ref
        for dependency in operations["workspace_status"].sdk_operation_dependencies
    ) == (
        "workspace_sdk.describe_remote_delta_status",
        "workspace_sdk.load_materialized_language_package_summary",
        "workspace_sdk.load_status",
        "workspace_sdk.materialize_source_delta_status_plan",
    )
    assert tuple(
        dependency.target_package_name
        for dependency in operations["workspace_status"].sdk_operation_dependencies
    ) == ("workspace-sdk", "workspace-sdk", "workspace-sdk", "workspace-sdk")
    assert tuple(
        dependency.target_operation_ref
        for dependency in operations["whoami"].sdk_operation_dependencies
    ) == (
        "agent_sdk.ensure_local_agent_operator_context",
        "identity_sdk.ensure_local_identity_admission",
    )
    assert tuple(
        dependency.target_package_name
        for dependency in operations["whoami"].sdk_operation_dependencies
    ) == ("agent-sdk", "identity-sdk")
    assert tuple(
        dependency.target_operation_ref
        for dependency in operations["workspace_commit"].sdk_operation_dependencies
    ) == ("workspace_sdk.commit_workspace_revision",)
    assert tuple(
        dependency.target_operation_ref
        for dependency in operations["workspace_build"].sdk_operation_dependencies
    ) == ("workspace_sdk.build_verified_materialization",)
    assert tuple(
        dependency.target_operation_ref
        for dependency in operations["workspace_publish"].sdk_operation_dependencies
    ) == ("workspace_sdk.publish_local_head",)

    assert result.compile_plan_artifact is not None
    payload = json.loads(result.compile_plan_artifact.path.read_text(encoding="utf-8"))
    payload_operations = {
        operation["name"]: operation
        for operation in payload["sdk_configs"][0]["operations"]
    }
    assert payload_operations["workspace_materialize"][
        "sdk_operation_dependencies"
    ] == [
        {
            "description": None,
            "order": 1,
            "required": True,
            "role": "dependency",
            "source_path": "aware_dev_sdk.aware",
            "target_operation_name": "describe_remote_delta_status",
            "target_operation_ref": "workspace_sdk.describe_remote_delta_status",
            "target_package_name": "workspace-sdk",
            "target_sdk_name": "workspace_sdk",
        },
        {
            "description": None,
            "order": 2,
            "required": True,
            "role": "dependency",
            "source_path": "aware_dev_sdk.aware",
            "target_operation_name": "evaluate_semantic_workflow_materialization_attempt",
            "target_operation_ref": "workspace_sdk.evaluate_semantic_workflow_materialization_attempt",
            "target_package_name": "workspace-sdk",
            "target_sdk_name": "workspace_sdk",
        },
        {
            "description": None,
            "order": 3,
            "required": True,
            "role": "dependency",
            "source_path": "aware_dev_sdk.aware",
            "target_operation_name": "materialize_and_apply_delta",
            "target_operation_ref": "workspace_sdk.materialize_and_apply_delta",
            "target_package_name": "workspace-sdk",
            "target_sdk_name": "workspace_sdk",
        },
    ]
