from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_sdk_runtime.semantic_contract import (
    AWARE_MODULE_SEMANTIC_CONTRACT,
    SDK_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    SDK_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    SDK_MATERIALIZATION_REQUIRED_PROJECTIONS,
    SDK_MATERIALIZATION_RUNTIME,
    SDK_MATERIALIZATION_RUNTIME_CONTEXT,
    SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
    SDK_PROVIDER_PACKAGE_ROLE,
)
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_code_sdk import code_semantic_generated_code_package_declarations
from aware_sdk_runtime.manifest.loader import load_aware_sdk_toml_spec
from aware_sdk_runtime.semantic_package import (
    SDK_WORKSPACE_MATERIALIZATION_ORDER,
    register_semantic_package_providers,
    sdk_semantic_package_metadata,
)
from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import SemanticPackageRegistry
from aware_code_ontology.code.code_enums import CodeLanguage


def test_sdk_semantic_contract_declares_package_roles_and_lanes() -> None:
    contract = AWARE_MODULE_SEMANTIC_CONTRACT

    assert contract.provider_key == "aware_sdk"
    provider_role = contract.package_role_for(role=SDK_PROVIDER_PACKAGE_ROLE)
    assert provider_role is not None
    assert provider_role.contract == "aware.semantic_provider"
    assert SEMANTIC_MATERIALIZATION_CAPABILITY in provider_role.capabilities
    assert provider_role.owns_manifest_kinds == ("aware_sdk_toml",)
    assert (
        contract.capability_participation_for(
            capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        )
        == SDK_MATERIALIZATION_CAPABILITY_PARTICIPATION
    )
    assert (
        contract.capability_execution_policy_for(
            capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        )
        == SDK_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY
    )
    materialization_policy = SDK_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY[0]
    assert materialization_policy.callable_module == (
        "aware_sdk_runtime.materialization.workspace_provider"
    )
    assert materialization_policy.callable_name == "materialize"
    assert materialization_policy.priority == SDK_WORKSPACE_MATERIALIZATION_ORDER

    runtime_context = SDK_MATERIALIZATION_RUNTIME_CONTEXT[0]
    assert runtime_context.semantic_owner == SDK_PROVIDER_PACKAGE_ROLE
    assert runtime_context.callable_module == (
        "aware_sdk_runtime.materialization.runtime_context"
    )
    assert runtime_context.callable_name == (
        "build_sdk_workspace_materialization_runtime_context"
    )
    assert runtime_context.required is True
    assert runtime_context.provider_payload is not None
    assert runtime_context.provider_payload["runtime_ontology_package_names"] == (
        SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )

    runtime = SDK_MATERIALIZATION_RUNTIME[0]
    assert runtime.semantic_owner == SDK_PROVIDER_PACKAGE_ROLE
    assert (
        runtime.runtime_ontology_package_names
        == SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
    )
    assert runtime.lane_projection_name == "SdkPackage"
    assert runtime.required_projection_names == SDK_MATERIALIZATION_REQUIRED_PROJECTIONS
    assert runtime.include_package_dependency_closure is True

    lane_keys = {lane.lane_key for lane in contract.syntax_lanes}
    assert {
        "aware_sdk.sdk_config",
        "aware_sdk.api",
        "aware_sdk.operation",
        "aware_sdk.endpoint",
    } <= lane_keys


def test_sdk_semantic_package_provider_resolves_aware_sdk_toml() -> None:
    SemanticPackageRegistry.clear()
    register_semantic_package_providers()

    code_package = CodePackageInfo(
        name="workspace-sdk",
        root_path=Path("sdks/workspace_client"),
        manifest_path=Path("sdks/workspace_client/aware.sdk.toml"),
        language=CodeLanguage.aware,
        metadata={
            "manifest_kind": "aware_sdk_toml",
            "fqn_prefix": "workspace_sdk",
            "package_kind": "sdk",
        },
    )

    descriptors = SemanticPackageRegistry.resolve(code_package)

    assert len(descriptors) == 1
    descriptor = descriptors[0]
    assert descriptor.provider_key == "aware_sdk"
    assert descriptor.family == "sdk"
    assert descriptor.semantic_kind == "sdk_package"
    assert descriptor.metadata["workspace_materialization_order"] == (
        SDK_WORKSPACE_MATERIALIZATION_ORDER
    )
    assert descriptor.metadata["workspace_materialization_branch"] == "semantic"
    assert descriptor.metadata["workspace_materialization_commit"] is True
    assert descriptor.metadata["semantic_projection_name"] == "SdkPackage"
    assert descriptor.capability_participation == (
        AWARE_MODULE_SEMANTIC_CONTRACT.capability_participation
    )


def test_sdk_semantic_package_metadata_declares_python_public_package(
    tmp_path: Path,
) -> None:
    sdk_root = tmp_path / "modules" / "code" / "sdks" / "code"
    manifest_path = sdk_root / "aware" / "aware.sdk.toml"
    package_root = sdk_root / "python"
    source_root = package_root / "aware_code_sdk"
    source_root.mkdir(parents=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "\n".join(
            (
                "aware_sdk = 1",
                "",
                "[sdk]",
                'package_name = "code-sdk"',
                'fqn_prefix = "aware_code_sdk"',
                "",
                "[build]",
                'sources_dir = "."',
                "",
                "[targets.python]",
                'root_dir = "python"',
                "",
                "[targets.python.public_package]",
                'package_dir = "aware_code_sdk"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (package_root / "pyproject.toml").write_text(
        "\n".join(
            (
                "[project]",
                'name = "aware-code-sdk"',
                'version = "0.1.0"',
                "",
            )
        ),
        encoding="utf-8",
    )

    spec = load_aware_sdk_toml_spec(toml_path=manifest_path)
    metadata = sdk_semantic_package_metadata(
        workspace_root=tmp_path,
        package_root=manifest_path.parent,
        manifest_path=manifest_path,
        manifest_spec=spec,
    )

    assert metadata["package_root"] == "modules/code/sdks/code"
    assert metadata["language_materialization_targets"] == [
        {
            "role": "public_package",
            "language": "python",
            "output_dir": "python",
            "import_root": "aware_code_sdk",
            "package_name": "aware-code-sdk",
            "materialization_source": "sdk",
            "code_package_surface": "sdk",
        }
    ]
    declarations = code_semantic_generated_code_package_declarations(
        source_manifest_path="modules/code/sdks/code/aware/aware.sdk.toml",
        semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
        semantic_package_metadata=metadata,
    )

    assert len(declarations) == 1
    declaration = declarations[0]
    assert declaration.package_name == "aware-code-sdk"
    assert declaration.package_root == "modules/code/sdks/code/python"
    assert declaration.manifest_path == (
        "modules/code/sdks/code/python/pyproject.toml"
    )
    assert declaration.sources_root == "aware_code_sdk"
    assert declaration.code_package_surface == "sdk"


def test_sdk_runtime_context_resolver_excludes_sdk_manifest_from_meta_graph(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_sdk_runtime.materialization.runtime_context as runtime_context

    workspace_root = tmp_path / "workspace"
    repo_root = tmp_path / "kernel"
    sdk_manifest_path = workspace_root / "sdks" / "demo" / "aware" / "aware.sdk.toml"
    sdk_ontology_manifest_path = (
        repo_root / "modules" / "sdk" / "structure" / "ontology" / "aware.toml"
    )
    workspace_root.mkdir()
    repo_root.mkdir()
    captured: dict[str, object] = {}
    environment_id = uuid4()

    class _Runtime:
        context = SimpleNamespace(
            index=object(),
            phase_timings_s={},
            package_timings=(),
            runtime_graphs=(),
            source_graphs=(),
            projection_hash_for_name=lambda _name: "sha256:test",
        )

    def _resolve_paths(
        _request: SemanticPackageMaterializationRuntimeContextRequest,
    ) -> tuple[Path, ...]:
        return (sdk_ontology_manifest_path,)

    def _build_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        return _Runtime()

    monkeypatch.setattr(
        runtime_context,
        "resolve_workspace_required_projection_package_manifest_paths",
        _resolve_paths,
    )
    monkeypatch.setattr(
        runtime_context,
        "build_meta_graph_runtime_for_aware_package_manifests",
        _build_runtime,
    )

    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_sdk",
        semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=sdk_manifest_path,
        context={"required_projection_names": ("SdkPackage",)},
    )

    resolved = runtime_context.build_sdk_workspace_materialization_runtime_context(
        request
    )

    assert resolved is not None
    assert resolved.environment_id == environment_id
    assert captured["workspace_root"] == workspace_root
    assert captured["package_manifest_paths"] == (sdk_ontology_manifest_path,)
