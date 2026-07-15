from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_invoke_sdk_operation_from_catalog_uses_declared_handler_ref() -> None:
    from aware_sdk_runtime.operation_invocation import (
        invoke_sdk_operation_from_catalog,
    )

    result = await invoke_sdk_operation_from_catalog(
        operation_ref="test_sdk.read_status",
        request_payload={"value": 7},
        context={"source": "unit"},
        extra_provider_refs=(f"{__name__}:get_test_sdk_operation_catalog",),
    )

    assert result == {
        "operation_ref": "test_sdk.read_status",
        "request_payload": {"value": 7},
        "context": {"source": "unit"},
    }


def get_test_sdk_operation_catalog() -> dict[str, object]:
    return {
        "catalog_contract": "aware.sdk_operation_catalog.v0",
        "sdk_name": "test_sdk",
        "package_name": "test-sdk",
        "operations": [
            {
                "operation_ref": "test_sdk.read_status",
                "endpoint_refs": ["test.status.status"],
                "effect": "read",
                "handler_ref": f"{__name__}:dispatch_test_sdk_operation",
                "requires_confirmation": False,
            }
        ],
    }


async def dispatch_test_sdk_operation(
    *,
    operation_ref: str,
    request_payload: dict[str, object],
    context: dict[str, object],
    timeout_s: float | None = None,
) -> dict[str, object]:
    _ = timeout_s
    return {
        "operation_ref": operation_ref,
        "request_payload": dict(request_payload),
        "context": dict(context),
    }


def test_materialize_sdk_operation_catalog_from_compile_plan(
    tmp_path: Path,
) -> None:
    from aware_sdk_runtime.operation_catalog import (
        SDK_OPERATION_CATALOG_CONTRACT,
        SDK_OPERATION_CATALOG_SOURCE,
        materialize_sdk_operation_catalog_from_toml,
    )

    sdk_toml_path = _create_workspace_sdk_package(tmp_path)

    catalog = materialize_sdk_operation_catalog_from_toml(
        toml_path=sdk_toml_path,
        repo_root=tmp_path,
    )

    assert catalog["catalog_contract"] == SDK_OPERATION_CATALOG_CONTRACT
    assert catalog["catalog_source"] == SDK_OPERATION_CATALOG_SOURCE
    assert catalog["sdk_name"] == "workspace_sdk"
    assert catalog["package_name"] == "workspace-sdk"
    assert catalog["version_number"] == 7
    assert catalog["source_files"] == ["workspace_sdk.aware"]
    assert catalog["feature_contracts"] == {
        "delta_event_policy": "aware.sdk_delta_event_policy.v0"
    }
    assert catalog["catalog_features"] == [
        {
            "feature_key": "delta_event_policy",
            "contract": "aware.sdk_delta_event_policy.v0",
            "source": "aware_sdk_runtime.features.delta_event_policy",
        }
    ]
    operations = _operation_by_ref(catalog)

    load_status = operations["workspace_sdk.load_status"]
    assert load_status["description"] == "Load current Workspace status."
    assert load_status["source_path"] == "workspace_sdk.aware"
    assert load_status["endpoint_refs"] == ["workspace.status.status"]
    assert load_status["effect"] == "read"
    assert load_status["effect_source"] == "sdk_surface_method"
    assert load_status["method_family"] == "retrieve"
    assert load_status["mutation_scope"] == "none"
    assert load_status["confirmation_policy"] == "none"
    assert load_status["execution_mode"] == "request_response"
    assert load_status["runtime_binding_kind"] == "local_handler"
    assert load_status["surface_refs"] == ["workspace_sdk.local_status"]
    assert load_status["requires_confirmation"] is False
    assert load_status["stability"] == "canonical"
    assert load_status["handler_ref"] is None
    assert load_status["delta_event_policy"] == {
        "contract": "aware.sdk_delta_event_policy.v0",
        "feature_key": "delta_event_policy",
        "policy_source": "aware_sdk_runtime.features.delta_event_policy",
        "policy_ref": "workspace_sdk.load_status.delta_event_policy",
        "operation_role": "observe_status",
        "delta_policy_ref": "aware.delta.observe",
        "semantic_event_policy_ref": "aware.semantic_event.observe",
        "source_projection_policy_ref": "code.source_projection.observe",
        "filesystem_policy_ref": "filesystem.no_apply",
        "surface_method_refs": ["workspace_sdk.local_status.retrieve"],
        "code_capability_requirements": [],
        "renderer_owned": False,
    }
    assert catalog["surfaces"] == [
        {
            "surface_ref": "workspace_sdk.local_status",
            "sdk_name": "workspace_sdk",
            "surface_name": "local_status",
            "description": "Local Workspace status surface.",
            "delta_event_policy_refs": ["workspace_sdk.load_status.delta_event_policy"],
            "methods": [
                {
                    "method_ref": "workspace_sdk.local_status.retrieve",
                    "surface_ref": "workspace_sdk.local_status",
                    "sdk_name": "workspace_sdk",
                    "surface_name": "local_status",
                    "method_name": "retrieve",
                    "operation_ref": "workspace_sdk.load_status",
                    "operation_name": "load_status",
                    "method_family": "retrieve",
                    "effect": "read",
                    "mutation_scope": "none",
                    "confirmation_policy": "none",
                    "execution_mode": "request_response",
                    "runtime_binding_kind": "local_handler",
                    "source_path": "workspace_sdk.aware",
                    "description": "Read current Workspace status.",
                    "delta_event_policy_ref": (
                        "workspace_sdk.load_status.delta_event_policy"
                    ),
                }
            ],
        }
    ]
    assert load_status["endpoint_details"] == [
        {
            "name": "status",
            "endpoint_ref": "workspace.status.status",
            "api_ref": "workspace",
            "capability_name": "status",
            "source_path": "workspace_sdk.aware",
            "order": 1,
            "role": "primary",
            "required": True,
            "description": None,
        }
    ]

    materialize = operations["workspace_sdk.materialize_workspace"]
    assert materialize["endpoint_refs"] == ["workspace.materialize.materialize"]
    assert materialize["effect"] == "write"
    assert materialize["effect_source"] == "inferred_operation_name"
    assert materialize["requires_confirmation"] is True
    materialize_policy = materialize["delta_event_policy"]
    assert isinstance(materialize_policy, dict)
    assert materialize_policy["operation_role"] == "materialize_delta"
    assert materialize_policy["source_projection_policy_ref"] == (
        "code.source_projection.resolve_package_delta"
    )
    assert materialize_policy["filesystem_policy_ref"] == (
        "filesystem.apply_code_package_delta"
    )
    assert materialize_policy["code_capability_requirements"] == [
        {
            "capability_ref": "code.source_projection.resolve_package_delta",
            "authority": "aware_code.section_segment_registry",
            "required": True,
        },
        {
            "capability_ref": "code.section_segment_capability_registry",
            "authority": "aware_code.section_segment_registry",
            "required": True,
        },
    ]


def test_materialize_sdk_operation_catalog_includes_dependencies(
    tmp_path: Path,
) -> None:
    from aware_sdk_runtime.operation_catalog import (
        materialize_sdk_operation_catalog_from_toml,
    )

    sdk_toml_path = _create_aware_dev_sdk_package(tmp_path)

    catalog = materialize_sdk_operation_catalog_from_toml(
        toml_path=sdk_toml_path,
        repo_root=tmp_path,
    )

    operation = _operation_by_ref(catalog)["aware_dev_sdk.publish"]
    assert operation["endpoint_refs"] == ["workspace.publish.publish"]
    assert operation["sdk_operation_dependency_refs"] == [
        "workspace_sdk.materialize_workspace"
    ]
    assert operation["sdk_operation_dependencies"] == [
        {
            "target_operation_ref": "workspace_sdk.materialize_workspace",
            "target_sdk_name": "workspace_sdk",
            "target_operation_name": "materialize_workspace",
            "target_package_name": "workspace-sdk",
            "source_path": "aware_dev_sdk.aware",
            "order": 1,
            "role": "dependency",
            "required": True,
            "description": None,
        }
    ]


def test_emit_sdk_operation_catalog_artifact(tmp_path: Path) -> None:
    from aware_sdk_runtime.operation_catalog import (
        SDK_OPERATION_CATALOG_ARTIFACT_NAME,
        emit_sdk_operation_catalog_artifact,
        materialize_sdk_operation_catalog_from_toml,
    )

    sdk_toml_path = _create_workspace_sdk_package(tmp_path)
    catalog = materialize_sdk_operation_catalog_from_toml(
        toml_path=sdk_toml_path,
        repo_root=tmp_path,
    )

    artifact = emit_sdk_operation_catalog_artifact(
        catalog_payload=catalog,
        runtime_package_dir=tmp_path / ".aware" / "sdk" / "runtime" / "workspace-sdk",
        repo_root=tmp_path,
    )

    assert artifact.path.name == SDK_OPERATION_CATALOG_ARTIFACT_NAME
    assert artifact.relpath == (
        ".aware/sdk/runtime/workspace-sdk/sdk.operation_catalog.json"
    )
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert payload == catalog
    assert len(artifact.hash_sha256) == 64


def _operation_by_ref(catalog: dict[str, object]) -> dict[str, dict[str, object]]:
    operations = catalog["operations"]
    assert isinstance(operations, list)
    return {
        str(operation["operation_ref"]): operation
        for operation in operations
        if isinstance(operation, dict)
    }


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(text, encoding="utf-8")


def _create_workspace_sdk_package(tmp_path: Path) -> Path:
    package_root = tmp_path / "sdks" / "workspace" / "aware"
    _write(
        package_root / "aware.sdk.toml",
        """
aware_sdk = 1

[sdk]
package_name = "workspace-sdk"
fqn_prefix = "aware_workspace_sdk"
version_number = 7

[build]
sources_dir = "."
include_paths = ["*.aware"]
compilation_mode = "sdk_ontology"
""",
    )
    _write(
        package_root / "workspace_sdk.aware",
        """\
sdk workspace_sdk {
    "Workspace SDK."
    api workspace;

    surface local_status {
        "Local Workspace status surface."
        method retrieve {
            "Read current Workspace status."
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
        "Load current Workspace status."
        endpoint workspace.status.status;
    }

    operation materialize_workspace {
        "Materialize a Workspace checkout."
        endpoint workspace.materialize.materialize;
    }
}
""",
    )
    return package_root / "aware.sdk.toml"


def _create_aware_dev_sdk_package(tmp_path: Path) -> Path:
    package_root = tmp_path / "sdks" / "aware_dev" / "aware"
    _write(
        package_root / "aware.sdk.toml",
        """
aware_sdk = 1

[sdk]
package_name = "aware-dev-sdk"
fqn_prefix = "aware_dev_sdk"
version_number = 1

[build]
sources_dir = "."
include_paths = ["*.aware"]
compilation_mode = "sdk_ontology"

[[dependencies]]
kind = "sdk_package"
package_name = "workspace-sdk"
version_number = 1
""",
    )
    _write(
        package_root / "aware_dev_sdk.aware",
        """\
sdk aware_dev_sdk {
    "Developer SDK."
    api workspace;

    operation publish {
        "Publish through Workspace materialization."
        endpoint workspace.publish.publish;
        operation workspace_sdk.materialize_workspace;
    }
}
""",
    )
    return package_root / "aware.sdk.toml"
