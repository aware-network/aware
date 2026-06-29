from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, cast
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code.semantic_materialization import (
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from _sdk_runtime_test_paths import REPO_ROOT
from aware_sdk_runtime.materialization.runtime_context import (
    build_sdk_workspace_materialization_runtime_context,
)
from aware_sdk_runtime.materialization import (
    service as sdk_materialization_service,
    workspace_provider as sdk_workspace_provider,
)
from aware_sdk_runtime.semantic_contract import (
    SDK_MATERIALIZATION_REQUIRED_PROJECTIONS,
    SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES,
    SDK_PROVIDER_PACKAGE_ROLE,
)

if TYPE_CHECKING:
    from aware_meta.runtime.graph_context import (
        MetaGraphRuntimeIndexSnapshot,
        MetaWorkspaceMaterializationRuntimeContext,
    )
    from aware_orm.session.session import Session


def test_sdk_materialization_product_sources_use_meta_runtime_boundary() -> None:
    repo_root = REPO_ROOT
    source_paths = (
        repo_root
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "sdk"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_sdk_runtime"
        / "materialization"
        / "service.py",
        repo_root
        / "workspaces"
        / "aware_kernel"
        / "modules"
        / "sdk"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_sdk_runtime"
        / "materialization"
        / "workspace_provider.py",
    )

    for source_path in source_paths:
        source = source_path.read_text(encoding="utf-8")
        assert "from aware_runtime" not in source
        assert "import aware_runtime" not in source
        assert "RuntimeHarness" not in source
        assert "AwareRuntimeIndex" not in source
        assert "hydrate_orm_graph_from_oig" not in source


def test_declared_sdk_language_targets_have_package_roots() -> None:
    repo_root = REPO_ROOT
    manifests = _selected_workspace_sdk_manifest_paths(repo_root=repo_root)
    workspace_manifest = (
        repo_root
        / "workspaces"
        / "aware_workspace"
        / "sdks"
        / "workspace"
        / "aware"
        / "aware.sdk.toml"
    )
    assert workspace_manifest in manifests
    assert all(
        "sdks" not in path.relative_to(repo_root).parts[:1] for path in manifests
    )

    missing: list[str] = []
    for manifest_path in manifests:
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        raw_targets = payload.get("targets")
        if not isinstance(raw_targets, dict):
            continue
        sdk_root = (
            manifest_path.parent.parent
            if manifest_path.parent.name == "aware"
            else manifest_path.parent
        )
        raw_python = raw_targets.get("python")
        if isinstance(raw_python, dict):
            missing.extend(
                _missing_declared_python_sdk_target_paths(
                    manifest_path=manifest_path,
                    sdk_root=sdk_root,
                    target=raw_python,
                    fqn_prefix=_sdk_fqn_prefix(payload=payload),
                )
            )
        raw_dart = raw_targets.get("dart")
        if isinstance(raw_dart, dict):
            missing.extend(
                _missing_declared_dart_sdk_target_paths(
                    manifest_path=manifest_path,
                    sdk_root=sdk_root,
                    target=raw_dart,
                    fqn_prefix=_sdk_fqn_prefix(payload=payload),
                )
            )

    assert missing == []


def _selected_workspace_sdk_manifest_paths(*, repo_root: Path) -> tuple[Path, ...]:
    kernel_manifests = tuple(
        sorted(
            repo_root.glob(
                "workspaces/aware_kernel/modules/*/sdks/*/aware/aware.sdk.toml"
            )
        )
    )
    workspace_manifest = (
        repo_root
        / "workspaces"
        / "aware_workspace"
        / "sdks"
        / "workspace"
        / "aware"
        / "aware.sdk.toml"
    )
    return (*kernel_manifests, workspace_manifest)


def _isolate_test_aware_root(
    *,
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
) -> None:
    monkeypatch.setenv("AWARE_ROOT", str(root))
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "fs")
    monkeypatch.delenv("DATABASE_URL", raising=False)


def _build_sdk_test_runtime_context(
    *,
    workspace_root: Path,
    repo_root: Path,
    manifest_path: Path,
    environment_id: UUID,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> "MetaWorkspaceMaterializationRuntimeContext":
    context = build_sdk_workspace_materialization_runtime_context(
        SemanticPackageMaterializationRuntimeContextRequest(
            provider_key="aware_sdk",
            semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
            workspace_root=workspace_root,
            repo_root=repo_root,
            actor_id=None,
            manifest_path=manifest_path,
            context={
                "required_projection_names": SDK_MATERIALIZATION_REQUIRED_PROJECTIONS,
            },
            provider_payload={
                "runtime_ontology_package_names": (
                    SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
                ),
            },
        )
    )
    assert context is not None
    return context


def test_sdk_implementation_code_source_scan_excludes_generated_cache_dirs(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "python"
    source_root = package_root / "aware_demo_sdk"
    source_root.mkdir(parents=True)
    tests_root = package_root / "tests"
    tests_root.mkdir()
    (package_root / "pyproject.toml").write_text(
        '[project]\nname = "aware-demo-sdk"\n',
        encoding="utf-8",
    )
    (package_root / "README.md").write_text("demo\n", encoding="utf-8")
    (source_root / "client.py").write_text(
        "class Client:\n    pass\n", encoding="utf-8"
    )
    (tests_root / "test_client.py").write_text(
        "def test_client():\n    pass\n", encoding="utf-8"
    )
    nested_cache = (
        source_root / "workspaces" / "aware_workspace" / ".aware" / "workspace" / "sdk"
    )
    nested_cache.mkdir(parents=True)
    (nested_cache / "directory_cache.msgpack").write_bytes(b"\x83binary")
    nested_generated = source_root / "_aware" / "generated.py"
    nested_generated.parent.mkdir()
    nested_generated.write_text("generated = True\n", encoding="utf-8")
    venv_cache = package_root / ".venv" / "lib" / "python.py"
    venv_cache.parent.mkdir(parents=True)
    venv_cache.write_text("ignored = True\n", encoding="utf-8")

    target = sdk_materialization_service.SdkImplementationCodePackageTarget(
        language=CodeLanguage.python,
        package_name="aware-demo-sdk",
        import_root="aware_demo_sdk",
        package_root=package_root,
        manifest_path=package_root / "pyproject.toml",
        sources_root=source_root,
        manifest_kind="pyproject_toml",
        role="public_package",
        include_paths=(
            "pyproject.toml",
            "README.md",
            "aware_demo_sdk/**/*",
            "tests/**/*.py",
        ),
        exclude_paths=(),
    )

    relative_paths = tuple(
        path.relative_to(package_root).as_posix()
        for path in sdk_materialization_service._implementation_code_source_files(
            target=target
        )
    )

    assert relative_paths == (
        "README.md",
        "aware_demo_sdk/client.py",
        "pyproject.toml",
        "tests/test_client.py",
    )


def _sdk_fqn_prefix(*, payload: dict[str, object]) -> str:
    sdk = payload.get("sdk")
    assert isinstance(sdk, dict)
    fqn_prefix = sdk.get("fqn_prefix")
    assert isinstance(fqn_prefix, str)
    return fqn_prefix


def _missing_declared_python_sdk_target_paths(
    *,
    manifest_path: Path,
    sdk_root: Path,
    target: dict[str, object],
    fqn_prefix: str,
) -> list[str]:
    language_root = sdk_root / _target_string(
        target=target,
        key="root_dir",
        default="python",
    )
    public_package = _target_public_package(target=target)
    package_root = language_root / _target_string(
        target=public_package,
        key="root_dir",
        default=".",
    )
    package_dir = _target_string(
        target=public_package,
        key="package_dir",
        default=fqn_prefix,
    )
    checks = (
        ("targets.python.root_dir", language_root),
        ("targets.python.pyproject_toml", package_root / "pyproject.toml"),
        (
            "targets.python.public_package.package_dir",
            package_root / package_dir,
        ),
    )
    return _missing_target_paths(manifest_path=manifest_path, checks=checks)


def _missing_declared_dart_sdk_target_paths(
    *,
    manifest_path: Path,
    sdk_root: Path,
    target: dict[str, object],
    fqn_prefix: str,
) -> list[str]:
    language_root = sdk_root / _target_string(
        target=target,
        key="root_dir",
        default="dart",
    )
    public_package = _target_public_package(target=target)
    package_dir = _target_string(
        target=public_package,
        key="package_dir",
        default=fqn_prefix,
    )
    package_root = language_root / _target_string(
        target=public_package,
        key="root_dir",
        default=package_dir,
    )
    checks = (
        ("targets.dart.root_dir", language_root),
        ("targets.dart.pubspec_yaml", package_root / "pubspec.yaml"),
        ("targets.dart.lib", package_root / "lib"),
    )
    return _missing_target_paths(manifest_path=manifest_path, checks=checks)


def _target_public_package(*, target: dict[str, object]) -> dict[str, object]:
    public_package = target.get("public_package")
    assert isinstance(public_package, dict)
    return public_package


def _target_string(
    *,
    target: dict[str, object],
    key: str,
    default: str,
) -> str:
    value = target.get(key, default)
    assert isinstance(value, str)
    normalized = value.strip()
    return normalized or default


def _missing_target_paths(
    *,
    manifest_path: Path,
    checks: tuple[tuple[str, Path], ...],
) -> list[str]:
    return [
        f"{manifest_path.relative_to(REPO_ROOT).as_posix()}: "
        f"{label} missing {path.as_posix()}"
        for label, path in checks
        if not path.exists()
    ]


class _FailClosedSemanticRuntime:
    @property
    def invoker(self) -> object:
        return _FailClosedSemanticInvoker()


class _FailClosedSemanticInvoker:
    async def invoke_function_with_index(self, **_: object) -> object:
        raise AssertionError(
            "SDK Workspace materialization must not route through RuntimeHarness"
        )


@pytest.mark.asyncio
async def test_sdk_workspace_provider_reports_full_rebuild_fallback_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_code_package_id = uuid4()
    package_commit_id = uuid4()
    package_head_commit_id = uuid4()
    sdk_config_commit_id = uuid4()
    sdk_config_oig_commit_id = uuid4()
    api_package_id = uuid4()
    sdk_package_dependency_id = uuid4()
    implementation_python_code_package_id = uuid4()
    implementation_python_branch_id = uuid4()
    implementation_python_oig_commit_id = uuid4()
    implementation_python_domain_commit_id = uuid4()
    owned_ocg_package_id = uuid4()
    owned_ocg_id = uuid4()
    owned_ocg_branch_id = uuid4()
    owned_ocg_source_code_package_id = uuid4()
    owned_ocg_package_head_commit_id = uuid4()
    owned_ocg_package_oig_commit_id = uuid4()
    owned_ocg_root_oig_commit_id = uuid4()

    async def _fake_materialize_sdk_package_from_manifest(**_: object):
        return SimpleNamespace(
            sdk_toml_path=tmp_path / "aware.sdk.toml",
            workspace_root=tmp_path,
            sdk_config=SimpleNamespace(name="demo_sdk", id=uuid4()),
            sdk_package=SimpleNamespace(name="demo-sdk", id=uuid4()),
            source_code_package_id=source_code_package_id,
            sdk_source_path="demo_sdk.aware",
            source_files=("demo_sdk.aware",),
            phase_timings_s={},
            sdk_config_commit_id=sdk_config_commit_id,
            sdk_config_object_instance_graph_commit_id=sdk_config_oig_commit_id,
            package_commit_id=package_commit_id,
            package_head_commit_id=package_head_commit_id,
            api_package_ids=(api_package_id,),
            implementation_code_package_ids=(implementation_python_code_package_id,),
            implementation_code_package_refs=(
                {
                    "code_package_id": implementation_python_code_package_id,
                    "source_code_package_id": implementation_python_code_package_id,
                    "branch_id": implementation_python_branch_id,
                    "domain_commit_id": implementation_python_domain_commit_id,
                    "object_instance_graph_commit_id": (
                        implementation_python_oig_commit_id
                    ),
                    "package_name": "aware-demo-sdk",
                    "language": "python",
                    "manifest_relative_path": "python/pyproject.toml",
                    "package_root": "python",
                    "sources_root": "python/aware_demo_sdk",
                    "fqn_prefix": "aware_demo_sdk",
                    "role": "public_package",
                    "include_paths": ["pyproject.toml", "aware_demo_sdk/**/*"],
                    "exclude_paths": [],
                    "entrypoint": None,
                },
            ),
            sdk_package_dependency_ids=(sdk_package_dependency_id,),
            object_config_graph_packages=(
                SimpleNamespace(
                    manifest_path=tmp_path / "db" / "aware.toml",
                    manifest_relative_path="db/aware.toml",
                    role="local_state",
                    package_name="demo-sdk-db",
                    package_fqn_prefix="demo_sdk_local",
                    package_kind="state",
                    object_config_graph_package_id=owned_ocg_package_id,
                    object_config_graph_id=owned_ocg_id,
                    package_branch_id=owned_ocg_branch_id,
                    source_code_package_id=owned_ocg_source_code_package_id,
                    object_config_graph_package_commit_id=uuid4(),
                    object_config_graph_package_head_commit_id=(
                        owned_ocg_package_head_commit_id
                    ),
                    object_config_graph_package_object_instance_graph_commit_id=(
                        owned_ocg_package_oig_commit_id
                    ),
                    object_config_graph_commit_id=uuid4(),
                    object_config_graph_head_commit_id=uuid4(),
                    object_config_graph_object_instance_graph_commit_id=(
                        owned_ocg_root_oig_commit_id
                    ),
                ),
            ),
        )

    monkeypatch.setattr(
        sdk_workspace_provider,
        "materialize_sdk_package_from_manifest",
        _fake_materialize_sdk_package_from_manifest,
    )
    request = SemanticPackageMaterializationRequest(
        runtime=object(),
        index=object(),
        actor_id=None,
        branch_id=uuid4(),
        workspace_root=tmp_path,
        manifest_path=tmp_path / "aware.sdk.toml",
        change_preview={"affected_semantic_keys": ("sdk:demo_sdk",)},
    )

    result = await sdk_workspace_provider.materialize(request)

    assert result.mode == "full_rebuild"
    assert result.affected_semantic_keys == ("sdk:demo_sdk",)
    assert result.applied_semantic_keys == ("sdk:demo_sdk",)
    assert result.fallback_reason is not None
    assert "not implemented delta materialization" in result.fallback_reason
    assert result.commit_id == package_commit_id
    assert result.head_commit_id == package_head_commit_id
    assert len(result.bundle_packages) == 1
    bundle = result.bundle_packages[0]
    assert bundle.package_key == "demo-sdk"
    assert bundle.semantic_head_commit_id == package_head_commit_id
    assert bundle.semantic_object_instance_graph_commit_id == package_head_commit_id
    assert bundle.semantic_root_object_instance_graph_commit_id == (
        sdk_config_oig_commit_id
    )
    assert bundle.semantic_root_kind == "sdk_config"
    assert bundle.source_code_package_id == source_code_package_id
    assert result.details["api_package_ids"] == [str(api_package_id)]
    assert result.details["implementation_code_package_ids"] == [
        str(implementation_python_code_package_id)
    ]
    implementation_packages = cast(
        list[dict[str, object]],
        result.details["implementation_code_packages"],
    )
    assert implementation_packages[0]["package_name"] == ("aware-demo-sdk")
    assert implementation_packages[0]["language"] == "python"
    assert result.details["sdk_package_dependency_ids"] == [
        str(sdk_package_dependency_id)
    ]
    assert bundle.runtime_code_package_refs == (
        {
            "role": "sdk_implementation_package",
            "source_code_package_id": implementation_python_code_package_id,
            "source_object_instance_graph_commit_id": (
                implementation_python_oig_commit_id
            ),
            "package_name": "aware-demo-sdk",
            "manifest_relative_path": "python/pyproject.toml",
            "package_root": "python",
            "sources_root": "python/aware_demo_sdk",
            "language": "python",
        },
    )
    assert result.details["object_config_graph_packages"] == [
        {
            "manifest_path": (tmp_path / "db" / "aware.toml").as_posix(),
            "manifest_relative_path": "db/aware.toml",
            "role": "local_state",
            "package_name": "demo-sdk-db",
            "package_fqn_prefix": "demo_sdk_local",
            "package_kind": "state",
            "code_package_surface": "structure",
            "object_config_graph_package_id": str(owned_ocg_package_id),
            "object_config_graph_id": str(owned_ocg_id),
            "package_branch_id": str(owned_ocg_branch_id),
            "source_code_package_id": str(owned_ocg_source_code_package_id),
            "object_config_graph_package_head_commit_id": str(
                owned_ocg_package_head_commit_id
            ),
            "object_config_graph_package_object_instance_graph_commit_id": str(
                owned_ocg_package_oig_commit_id
            ),
            "object_config_graph_object_instance_graph_commit_id": str(
                owned_ocg_root_oig_commit_id
            ),
        }
    ]
    assert result.details["emitted_owned_object_config_graph_package_count"] == 1
    assert len(result.emitted_package_outputs) == 1
    output = result.emitted_package_outputs[0]
    assert output.producer_provider_key == "aware_sdk"
    assert output.target_provider_key == "aware_meta"
    assert output.target_input_key == "aware_meta.object_config_graph_package_manifest"
    assert output.package_key == "demo-sdk-db"
    assert output.input_artifact_path == tmp_path / "db" / "aware.toml"
    assert output.input_artifact_payload["package_name"] == "demo-sdk-db"
    assert output.input_artifact_payload["fqn_prefix"] == "demo_sdk_local"
    assert output.input_artifact_payload["package_kind"] == "state"
    assert output.input_artifact_payload["code_package_surface"] == "structure"
    assert output.input_artifact_payload["package_root"] == "db"
    assert "code_package_surface" not in output.provider_payload
    assert output.input_artifact_payload["object_instance_graph_commit_id"] == str(
        owned_ocg_package_oig_commit_id
    )


@pytest.mark.asyncio
async def test_interface_sdk_materialization_provider_commits_language_packages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = repo_root
    sdk_toml_path = repo_root / "sdks" / "interface" / "aware" / "aware.sdk.toml"
    _isolate_test_aware_root(
        monkeypatch=monkeypatch,
        root=tmp_path / "aware_root_sdk_package_materialization",
    )

    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    branch_id = uuid4()
    runtime_context = _build_sdk_test_runtime_context(
        workspace_root=workspace_root,
        repo_root=repo_root,
        manifest_path=sdk_toml_path,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
    )
    index = runtime_context.index

    from aware_api_ontology.stable_ids import (  # noqa: WPS433
        stable_api_capability_endpoint_id,
        stable_api_capability_id,
        stable_api_id,
        stable_api_package_id,
    )
    from aware_sdk_runtime.materialization import (  # noqa: WPS433
        resolve_sdk_package_materialization_spec,
    )
    from aware_sdk_runtime.materialization.workspace_provider import (  # noqa: WPS433
        materialize,
    )
    from aware_sdk_ontology.sdk.sdk_config import SdkConfig  # noqa: WPS433
    from aware_sdk_ontology.sdk.sdk_operation_api_capability_endpoint import (  # noqa: WPS433
        SdkOperationApiCapabilityEndpoint,
    )
    from aware_sdk_ontology.sdk.sdk_package import SdkPackage  # noqa: WPS433
    from aware_sdk_ontology.sdk.sdk_package_dependency import (  # noqa: WPS433
        SdkPackageDependency,
    )
    from aware_sdk_ontology.sdk.sdk_package_implementation_package import (  # noqa: WPS433
        SdkPackageImplementationPackage,
    )
    from aware_sdk_ontology.stable_ids import (  # noqa: WPS433
        stable_sdk_config_id,
        stable_sdk_package_id,
        stable_sdk_package_implementation_package_id,
    )

    spec = resolve_sdk_package_materialization_spec(
        sdk_toml_path=sdk_toml_path,
        workspace_root=workspace_root,
    )
    assert spec.package_name == "interface-sdk"
    assert spec.package_fqn_prefix == "aware_interface_sdk"
    assert spec.sdk_config_name == "interface_sdk"
    assert spec.sdk_source_path == "interface_sdk.aware"
    assert spec.source_files == ("interface_sdk.aware",)

    request = SemanticPackageMaterializationRequest(
        runtime=runtime_context.runtime,
        index=index,
        actor_id=runtime_context.actor_id,
        branch_id=branch_id,
        workspace_root=workspace_root,
        manifest_path=sdk_toml_path,
        change_preview={"affected_semantic_keys": ("sdk:interface_sdk",)},
    )
    result = await materialize(request)

    sdk_config_id = stable_sdk_config_id(name="interface_sdk")
    sdk_package_id = stable_sdk_package_id(name="interface-sdk")
    interface_api_id = stable_api_id(name="interface")
    get_state_capability_id = stable_api_capability_id(
        api_id=interface_api_id,
        name="get_interface_state",
    )
    get_state_endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=get_state_capability_id,
        name="get_interface_state",
    )
    interface_api_package_id = stable_api_package_id(
        name="interface-service-api",
    )
    source_code_package_config_id = _source_code_package_config_id(
        manifest_kind="aware_sdk_toml",
        surface="sdk",
    )
    source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name="interface-sdk",
        language=CodeLanguage.aware.value,
    )
    python_code_package_config_id = _source_code_package_config_id(
        manifest_kind="pyproject_toml",
        surface="sdk",
    )
    python_code_package_id = stable_code_package_id(
        code_package_config_id=python_code_package_config_id,
        package_name="aware-interface-sdk",
        language=CodeLanguage.python.value,
    )
    dart_code_package_config_id = _source_code_package_config_id(
        manifest_kind="pubspec_yaml",
        surface="sdk",
    )
    dart_code_package_id = stable_code_package_id(
        code_package_config_id=dart_code_package_config_id,
        package_name="aware_interface_sdk",
        language=CodeLanguage.dart.value,
    )
    python_bridge_id = stable_sdk_package_implementation_package_id(
        sdk_package_id=sdk_package_id,
        code_package_id=python_code_package_id,
    )
    dart_bridge_id = stable_sdk_package_implementation_package_id(
        sdk_package_id=sdk_package_id,
        code_package_id=dart_code_package_id,
    )

    assert result.mode == "full_rebuild"
    assert result.affected_semantic_keys == ("sdk:interface_sdk",)
    assert result.applied_semantic_keys == ("sdk:interface_sdk",)
    assert result.commit_id is not None
    assert result.head_commit_id is not None
    assert result.details["sdk_config_id"] == str(sdk_config_id)
    assert result.details["sdk_package_id"] == str(sdk_package_id)
    assert result.details["source_code_package_id"] == str(source_code_package_id)
    assert result.details["source_files"] == ["interface_sdk.aware"]
    assert result.details["api_package_ids"] == [str(interface_api_package_id)]
    assert result.details["implementation_code_package_ids"] == [
        str(python_code_package_id),
        str(dart_code_package_id),
    ]
    assert result.details["sdk_package_dependency_ids"] == []
    assert len(result.bundle_packages) == 1
    bundle = result.bundle_packages[0]
    assert bundle.package_key == "interface-sdk"
    assert bundle.semantic_package_id == sdk_package_id
    assert bundle.semantic_root_id == sdk_config_id
    assert bundle.semantic_branch_id == branch_id
    assert bundle.semantic_root_kind == "sdk_config"
    assert bundle.source_code_package_id == source_code_package_id
    assert bundle.semantic_root_object_instance_graph_commit_id is not None
    assert [ref["package_name"] for ref in bundle.runtime_code_package_refs] == [
        "aware-interface-sdk",
        "aware_interface_sdk",
    ]

    sdk_config_projection_hash = runtime_context.projection_hash_for_name("SdkConfig")
    sdk_package_projection_hash = runtime_context.projection_hash_for_name("SdkPackage")
    code_package_projection_hash = runtime_context.projection_hash_for_name(
        "CodePackage"
    )

    sdk_config_session = await _hydrate_projection_session(
        index=index,
        branch_id=branch_id,
        projection_hash=sdk_config_projection_hash,
    )
    sdk_config = sdk_config_session.imap_get(SdkConfig, sdk_config_id)
    assert sdk_config is not None
    assert sdk_config.name == "interface_sdk"
    operation_names = {operation.name for operation in sdk_config.operations}
    assert "get_interface_state" in operation_names
    endpoint_bindings = [
        obj
        for obj in sdk_config_session.imap_all_objects()
        if isinstance(obj, SdkOperationApiCapabilityEndpoint)
    ]
    assert any(
        binding.endpoint_ref == "interface.get_interface_state.get_interface_state"
        and binding.api_capability_endpoint_id == get_state_endpoint_id
        for binding in endpoint_bindings
    )

    sdk_package_session = await _hydrate_projection_session(
        index=index,
        branch_id=branch_id,
        projection_hash=sdk_package_projection_hash,
    )
    sdk_package = sdk_package_session.imap_get(SdkPackage, sdk_package_id)
    assert sdk_package is not None
    assert sdk_package.name == "interface-sdk"
    assert sdk_package.sdk_config_id == sdk_config_id
    assert sdk_package.source_code_package_id == source_code_package_id
    assert sdk_package.sdk_config_object_instance_graph_commit_id == (
        bundle.semantic_root_object_instance_graph_commit_id
    )
    assert sdk_package.fqn_prefix == "aware_interface_sdk"
    assert sdk_package.manifest_relative_path == ("sdks/interface/aware/aware.sdk.toml")
    assert sdk_package.package_root == "sdks/interface/aware"
    assert sdk_package.sources_root == "sdks/interface/aware"
    assert list(sdk_package.include_paths) == ["*.aware"]
    assert sdk_package.compilation_mode == "sdk_ontology"
    assert list(sdk_package.dependencies) == [
        {
            "kind": "api_package",
            "package_name": "interface-service-api",
            "version_number": 1,
        }
    ]
    assert dict(sdk_package.targets) == {
        "python": {
            "root_dir": "python",
            "public_package": {
                "package_dir": "aware_interface_sdk",
                "root_dir": None,
            },
        },
        "dart": {
            "root_dir": "dart",
            "public_package": {
                "package_dir": "aware_interface_sdk",
                "root_dir": None,
            },
        },
    }
    dependency_bindings = [
        obj
        for obj in sdk_package_session.imap_all_objects()
        if isinstance(obj, SdkPackageDependency)
    ]
    assert dependency_bindings == []
    python_bridge = sdk_package_session.imap_get(
        SdkPackageImplementationPackage,
        python_bridge_id,
    )
    assert python_bridge is not None
    assert python_bridge.code_package_id == python_code_package_id
    assert python_bridge.package_name == "aware-interface-sdk"
    assert python_bridge.language == CodeLanguage.python
    assert python_bridge.import_root == "aware_interface_sdk"
    assert python_bridge.manifest_relative_path == (
        "sdks/interface/python/pyproject.toml"
    )
    assert python_bridge.package_root == "sdks/interface/python"
    dart_bridge = sdk_package_session.imap_get(
        SdkPackageImplementationPackage,
        dart_bridge_id,
    )
    assert dart_bridge is not None
    assert dart_bridge.code_package_id == dart_code_package_id
    assert dart_bridge.package_name == "aware_interface_sdk"
    assert dart_bridge.language == CodeLanguage.dart
    assert dart_bridge.import_root == "aware_interface_sdk"
    assert dart_bridge.manifest_relative_path == (
        "sdks/interface/dart/aware_interface_sdk/pubspec.yaml"
    )
    assert dart_bridge.package_root == "sdks/interface/dart/aware_interface_sdk"
    assert {row.code_package_id for row in sdk_package.implementation_packages} == {
        dart_code_package_id,
        python_code_package_id,
    }

    code_package_session = await _hydrate_projection_session(
        index=index,
        branch_id=branch_id,
        projection_hash=code_package_projection_hash,
    )
    code_package = code_package_session.imap_get(
        CodePackage,
        source_code_package_id,
    )
    assert code_package is not None
    assert code_package.package_name == "interface-sdk"
    assert code_package.language == CodeLanguage.aware
    assert code_package.surface == "sdk"
    assert code_package.manifest_relative_path == (
        "sdks/interface/aware/aware.sdk.toml"
    )
    assert code_package.package_root == "sdks/interface/aware"
    assert code_package.sources_root == "sdks/interface/aware"

    implementation_packages = cast(
        list[dict[str, object]],
        result.details["implementation_code_packages"],
    )
    implementation_details = {
        str(item["package_name"]): item for item in implementation_packages
    }
    python_code_session = await _hydrate_projection_session(
        index=index,
        branch_id=UUID(str(implementation_details["aware-interface-sdk"]["branch_id"])),
        projection_hash=code_package_projection_hash,
    )
    python_code_package = python_code_session.imap_get(
        CodePackage,
        python_code_package_id,
    )
    assert python_code_package is not None
    assert python_code_package.package_name == "aware-interface-sdk"
    assert python_code_package.language == CodeLanguage.python
    assert python_code_package.manifest_relative_path == (
        "sdks/interface/python/pyproject.toml"
    )
    assert python_code_package.package_root == "sdks/interface/python"
    assert python_code_package.sources_root == (
        "sdks/interface/python/aware_interface_sdk"
    )

    dart_code_session = await _hydrate_projection_session(
        index=index,
        branch_id=UUID(str(implementation_details["aware_interface_sdk"]["branch_id"])),
        projection_hash=code_package_projection_hash,
    )
    dart_code_package = dart_code_session.imap_get(
        CodePackage,
        dart_code_package_id,
    )
    assert dart_code_package is not None
    assert dart_code_package.package_name == "aware_interface_sdk"
    assert dart_code_package.language == CodeLanguage.dart
    assert dart_code_package.manifest_relative_path == (
        "sdks/interface/dart/aware_interface_sdk/pubspec.yaml"
    )
    assert dart_code_package.package_root == ("sdks/interface/dart/aware_interface_sdk")
    assert dart_code_package.sources_root == (
        "sdks/interface/dart/aware_interface_sdk/lib"
    )


@pytest.mark.asyncio
async def test_sdk_package_materialization_commits_sdk_package_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    package_root = tmp_path / "demo_sdk_package"
    package_root.mkdir()
    sdk_toml_path = package_root / "aware.sdk.toml"
    sdk_source_path = package_root / "demo_sdk.aware"
    pinned_oig_commit_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    expected_hash = "b" * 64
    sdk_toml_path.write_text(
        f"""
aware_sdk = 1

[sdk]
package_name = "demo-sdk"
fqn_prefix = "demo_sdk"
version_number = 1
title = "Demo SDK"

[build]
sources_dir = "."
include_paths = ["*.aware"]
exclude_paths = []
force_fresh_scan = false
compilation_mode = "sdk_ontology"

[[dependencies]]
kind = "api_package"
package_name = "workspace-service-api"
version_number = 1

[[dependencies]]
kind = "sdk_package"
package_name = "workspace-sdk"
version_number = 7
object_instance_graph_commit_id = "{pinned_oig_commit_id}"
expected_hash_sha256 = "{expected_hash}"
""",
        encoding="utf-8",
    )
    sdk_source_path.write_text(
        """
sdk demo_sdk {
    api workspace;

    operation load_status {
        endpoint workspace.status.status;
    }

    operation composed_status {
        endpoint workspace.status.status;
        operation workspace_sdk.load_status;
    }
}
""",
        encoding="utf-8",
    )
    _isolate_test_aware_root(
        monkeypatch=monkeypatch,
        root=tmp_path / "aware_root_sdk_dependency_materialization",
    )

    runtime_context = _build_sdk_test_runtime_context(
        workspace_root=package_root,
        repo_root=repo_root,
        manifest_path=sdk_toml_path,
        environment_id=uuid4(),
    )
    index = runtime_context.index

    from aware_sdk_runtime.materialization.workspace_provider import (  # noqa: WPS433
        materialize,
    )
    from aware_sdk_ontology.sdk.sdk_package import SdkPackage  # noqa: WPS433
    from aware_sdk_ontology.sdk.sdk_package_dependency import (  # noqa: WPS433
        SdkPackageDependency,
    )
    from aware_sdk_ontology.sdk.sdk_operation_dependency import (  # noqa: WPS433
        SdkOperationDependency,
    )
    from aware_sdk_ontology.stable_ids import (  # noqa: WPS433
        stable_sdk_config_id,
        stable_sdk_operation_dependency_id,
        stable_sdk_operation_id,
        stable_sdk_package_dependency_id,
        stable_sdk_package_id,
    )

    branch_id = uuid4()
    request = SemanticPackageMaterializationRequest(
        runtime=runtime_context.runtime,
        index=index,
        actor_id=runtime_context.actor_id,
        branch_id=branch_id,
        workspace_root=package_root,
        manifest_path=sdk_toml_path,
        change_preview={"affected_semantic_keys": ("sdk:demo_sdk",)},
    )
    result = await materialize(request)

    sdk_config_id = stable_sdk_config_id(name="demo_sdk")
    sdk_package_id = stable_sdk_package_id(name="demo-sdk")
    target_sdk_package_id = stable_sdk_package_id(name="workspace-sdk")
    sdk_package_dependency_id = stable_sdk_package_dependency_id(
        sdk_package_id=sdk_package_id,
        target_sdk_package_id=target_sdk_package_id,
    )

    assert result.details["sdk_config_id"] == str(sdk_config_id)
    assert result.details["sdk_package_id"] == str(sdk_package_id)
    assert result.details["sdk_package_dependency_ids"] == [str(target_sdk_package_id)]

    sdk_package_projection_hash = runtime_context.projection_hash_for_name("SdkPackage")
    sdk_package_session = await _hydrate_projection_session(
        index=index,
        branch_id=branch_id,
        projection_hash=sdk_package_projection_hash,
    )
    sdk_package = sdk_package_session.imap_get(SdkPackage, sdk_package_id)
    assert sdk_package is not None
    assert list(sdk_package.dependencies) == [
        {
            "kind": "api_package",
            "package_name": "workspace-service-api",
            "version_number": 1,
        },
        {
            "expected_hash_sha256": expected_hash,
            "kind": "sdk_package",
            "object_instance_graph_commit_id": str(pinned_oig_commit_id),
            "package_name": "workspace-sdk",
            "version_number": 7,
        },
    ]
    dependency = sdk_package_session.imap_get(
        SdkPackageDependency,
        sdk_package_dependency_id,
    )
    assert dependency is not None
    assert dependency.target_sdk_package_id == target_sdk_package_id
    assert dependency.target_package_name == "workspace-sdk"
    assert dependency.target_sdk_package_object_instance_graph_commit_id == (
        pinned_oig_commit_id
    )
    assert dependency.target_version_number == 7
    assert dependency.expected_hash_sha256 == expected_hash
    assert [row.id for row in sdk_package.sdk_package_dependencies] == [dependency.id]

    sdk_config_projection_hash = runtime_context.projection_hash_for_name("SdkConfig")
    sdk_config_session = await _hydrate_projection_session(
        index=index,
        branch_id=branch_id,
        projection_hash=sdk_config_projection_hash,
    )
    source_operation_id = stable_sdk_operation_id(
        sdk_config_id=sdk_config_id,
        name="composed_status",
    )
    target_operation_id = stable_sdk_operation_id(
        sdk_config_id=stable_sdk_config_id(name="workspace_sdk"),
        name="load_status",
    )
    operation_dependency_id = stable_sdk_operation_dependency_id(
        sdk_operation_id=source_operation_id,
        target_sdk_operation_id=target_operation_id,
    )
    operation_dependency = sdk_config_session.imap_get(
        SdkOperationDependency,
        operation_dependency_id,
    )
    assert operation_dependency is not None
    assert operation_dependency.target_sdk_operation_id == target_operation_id
    assert operation_dependency.target_operation_ref == "workspace_sdk.load_status"
    assert operation_dependency.target_sdk_name == "workspace_sdk"
    assert operation_dependency.target_operation_name == "load_status"
    assert operation_dependency.target_package_name == "workspace-sdk"


@pytest.mark.asyncio
async def test_sdk_package_materialization_commits_owned_ocg_packages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    sdk_root = tmp_path / "demo_sdk"
    aware_root = sdk_root / "aware"
    db_root = sdk_root / "db"
    db_source_root = db_root / "aware" / "status"
    aware_root.mkdir(parents=True)
    db_source_root.mkdir(parents=True)
    sdk_toml_path = aware_root / "aware.sdk.toml"
    sdk_source_path = aware_root / "demo_sdk.aware"
    db_toml_path = db_root / "aware.toml"
    db_source_path = db_source_root / "local_status_baseline.aware"
    sdk_toml_path.write_text(
        """
aware_sdk = 1

[sdk]
package_name = "demo-sdk"
fqn_prefix = "demo_sdk"
version_number = 1
title = "Demo SDK"

[build]
sources_dir = "."
include_paths = ["*.aware"]
exclude_paths = []
force_fresh_scan = false
compilation_mode = "sdk_ontology"

[[object_config_graph_packages]]
manifest = "db/aware.toml"
role = "local_state"
description = "Demo SDK-owned local status store."

[[dependencies]]
kind = "api_package"
package_name = "workspace-service-api"
version_number = 1
""",
        encoding="utf-8",
    )
    sdk_source_path.write_text(
        """
sdk demo_sdk {
    api workspace;

    operation status {
        endpoint workspace.status.status;
    }
}
""",
        encoding="utf-8",
    )
    db_toml_path.write_text(
        """
aware = 1

[package]
package_name = "demo-sdk-db"
fqn_prefix = "demo_sdk_local"
kind = "state"
version_number = 1
title = "Demo SDK DB"

[build]
environment_slug = "demo_sdk_db"

[[language_materializations]]
role = "local_state_sqlite"
language = "sql"
output_dir = "sqlite"
import_root = "demo_sdk_local_sqlite"
package_name = "demo-sdk-db-sqlite"
materialization_source = "ontology"
renderer_kind = "sqlite"
renderer_profile = "orm_models"
stable_ids_import_root = "demo_sdk_local_ontology"
""",
        encoding="utf-8",
    )
    db_source_path.write_text(
        """
class LocalStatusBaseline {
    workspace_handle String key
    workspace_root String key
    workspace_revision_id String?
}
""",
        encoding="utf-8",
    )
    _isolate_test_aware_root(
        monkeypatch=monkeypatch,
        root=tmp_path / "aware_root_sdk_owned_ocg_materialization",
    )

    runtime_context = _build_sdk_test_runtime_context(
        workspace_root=sdk_root,
        repo_root=repo_root,
        manifest_path=sdk_toml_path,
        environment_id=uuid4(),
    )
    index = runtime_context.index

    from aware_meta_ontology.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_id,
        stable_object_config_graph_package_id,
    )
    from aware_sdk_runtime.materialization.workspace_provider import (  # noqa: WPS433
        materialize,
    )
    from aware_sdk_ontology.sdk.sdk_package import SdkPackage  # noqa: WPS433
    from aware_sdk_ontology.sdk.sdk_package_object_config_graph_package import (  # noqa: WPS433
        SdkPackageObjectConfigGraphPackage,
    )
    from aware_sdk_ontology.stable_ids import (  # noqa: WPS433
        stable_sdk_config_id,
        stable_sdk_package_id,
        stable_sdk_package_object_config_graph_package_id,
    )

    branch_id = uuid4()
    request = SemanticPackageMaterializationRequest(
        runtime=runtime_context.runtime,
        index=index,
        actor_id=runtime_context.actor_id,
        branch_id=branch_id,
        workspace_root=sdk_root,
        manifest_path=sdk_toml_path,
        change_preview={"affected_semantic_keys": ("sdk:demo_sdk",)},
    )
    result = await materialize(request)

    sdk_config_id = stable_sdk_config_id(name="demo_sdk")
    sdk_package_id = stable_sdk_package_id(name="demo-sdk")
    object_config_graph_package_id = stable_object_config_graph_package_id(
        package_name="demo-sdk-db",
        fqn_prefix="demo_sdk_local",
    )
    object_config_graph_id = stable_object_config_graph_id(
        fqn_prefix="demo_sdk_local",
        language=CodeLanguage.aware.value,
    )
    owned_source_code_package_config_id = (
        sdk_materialization_service._sdk_owned_aware_toml_code_package_config_id(
            package_kind="state",
        )
    )
    owned_source_code_package_id = stable_code_package_id(
        code_package_config_id=owned_source_code_package_config_id,
        package_name="demo-sdk-db",
        language=CodeLanguage.aware.value,
    )
    sdk_package_ocg_package_id = stable_sdk_package_object_config_graph_package_id(
        sdk_package_id=sdk_package_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )

    assert len(result.bundle_packages) == 1
    assert result.details["sdk_config_id"] == str(sdk_config_id)
    assert result.details["sdk_package_id"] == str(sdk_package_id)
    assert result.details["object_config_graph_packages"] == [
        {
            "manifest_path": db_toml_path.as_posix(),
            "manifest_relative_path": "db/aware.toml",
            "role": "local_state",
            "package_name": "demo-sdk-db",
            "package_fqn_prefix": "demo_sdk_local",
            "package_kind": "state",
            "code_package_surface": "structure",
            "object_config_graph_package_id": str(object_config_graph_package_id),
            "object_config_graph_id": str(object_config_graph_id),
            "package_branch_id": None,
            "source_code_package_id": str(owned_source_code_package_id),
            "object_config_graph_package_head_commit_id": None,
            "object_config_graph_package_object_instance_graph_commit_id": None,
            "object_config_graph_object_instance_graph_commit_id": None,
            "language_materialization_targets": [
                {
                    "role": "local_state_sqlite",
                    "language": "sql",
                    "output_dir": "sqlite",
                    "import_root": "demo_sdk_local_sqlite",
                    "package_name": "demo-sdk-db-sqlite",
                    "materialization_source": "ontology",
                    "renderer_kind": "sqlite",
                    "renderer_profile": "orm_models",
                    "stable_ids_import_root": "demo_sdk_local_ontology",
                }
            ],
        }
    ]
    assert len(result.emitted_package_outputs) == 1
    output = result.emitted_package_outputs[0]
    assert output.package_key == "demo-sdk-db"
    assert output.input_artifact_path == db_toml_path
    assert output.source_package_key == "demo-sdk"
    assert output.source_manifest_path == "aware/aware.sdk.toml"
    assert output.target_provider_key == "aware_meta"
    assert output.target_input_key == "aware_meta.object_config_graph_package_manifest"
    assert output.input_artifact_payload == {
        "aware_toml_path": db_toml_path.as_posix(),
        "fqn_prefix": "demo_sdk_local",
        "manifest_kind": "aware_toml",
        "manifest_relative_path": "db/aware.toml",
        "package_kind": "state",
        "code_package_surface": "structure",
        "package_name": "demo-sdk-db",
        "package_root": "db",
        "role": "local_state",
        "language_materialization_targets": [
            {
                "role": "local_state_sqlite",
                "language": "sql",
                "output_dir": "sqlite",
                "import_root": "demo_sdk_local_sqlite",
                "package_name": "demo-sdk-db-sqlite",
                "materialization_source": "ontology",
                "renderer_kind": "sqlite",
                "renderer_profile": "orm_models",
                "stable_ids_import_root": "demo_sdk_local_ontology",
            }
        ],
    }
    assert "code_package_surface" not in output.provider_payload

    sdk_package_projection_hash = runtime_context.projection_hash_for_name("SdkPackage")
    sdk_package_session = await _hydrate_projection_session(
        index=index,
        branch_id=branch_id,
        projection_hash=sdk_package_projection_hash,
    )
    sdk_package = sdk_package_session.imap_get(SdkPackage, sdk_package_id)
    assert sdk_package is not None
    assert sdk_package.sdk_config_id == sdk_config_id
    owned_ref = sdk_package_session.imap_get(
        SdkPackageObjectConfigGraphPackage,
        sdk_package_ocg_package_id,
    )
    assert owned_ref is not None
    assert owned_ref.object_config_graph_package_id == (object_config_graph_package_id)
    assert owned_ref.manifest_relative_path == "db/aware.toml"
    assert owned_ref.role == "local_state"
    assert owned_ref.package_kind == "state"
    assert owned_ref.object_config_graph_package_object_instance_graph_commit_id is None
    assert owned_ref.description == "Demo SDK-owned local status store."
    assert [
        row.object_config_graph_package_id
        for row in sdk_package.object_config_graph_packages
    ] == [object_config_graph_package_id]


async def _hydrate_projection_session(
    *,
    index: "MetaGraphRuntimeIndexSnapshot",
    branch_id: UUID,
    projection_hash: str,
) -> Session:
    from aware_meta.graph.instance.commit.fs_store import FSCommitStore
    from aware_meta.graph.instance.commit.materializer import OIGMaterializer
    from aware_meta.runtime.oig_model_reifier import reify_oig_session

    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id") is not None
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


def _source_code_package_config_id(
    *,
    manifest_kind: str,
    surface: str,
) -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind=manifest_kind,
            surface=surface,
        ),
    )
