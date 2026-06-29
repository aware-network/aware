from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from aware_meta.runtime import (
    MetaGraphCommitIndex,
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationKind,
    MetaGraphImplementationPolicy,
    MetaGraphRuntimeContext,
    MetaGraphRuntimeIndex,
    MetaGraphRuntimeIndexView,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    MetaOIGAssertions,
    materialize_meta_runtime_lane_head,
)
from aware_sdk_runtime.handlers._generated import meta_handlers as sdk_meta_handlers
from _sdk_runtime_test_paths import REPO_ROOT, SDK_PACKAGE_MANIFEST_PATHS


_SDK_META_HANDLERS_ANY: Any = sdk_meta_handlers
_SDK_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SDK_META_HANDLERS_ANY,
)
_SDK_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SDK_META_HANDLERS_ANY,
)


@dataclass(frozen=True, slots=True)
class IsolatedMetaAwareRoot:
    root: Path
    persistence_backend: str = "fs"
    database_url: str | None = None
    _env_overrides: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __enter__(self) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        (root / ".aware").mkdir(parents=True, exist_ok=True)
        env_overrides = {
            "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
            "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)
        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_PERSISTENCE_BACKEND"] = self.persistence_backend
        if self.database_url is None:
            _ = os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.database_url
        return root

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        for key, previous in self._env_overrides.items():
            if previous is None:
                _ = os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _sdk_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return SDK_PACKAGE_MANIFEST_PATHS


def _build_sdk_meta_runtime(repo_root: Path, *, workspace_root: Path):
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_sdk_package_manifest_paths(repo_root),
        workspace_root=workspace_root,
        handler_modules=(_SDK_META_HANDLER_MODULE,),
        bootstrap_modules=(_SDK_META_BOOTSTRAP_MODULE,),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _implementation_kind(
    context: MetaGraphRuntimeContext,
    *,
    owner_key: str,
    function_name: str,
) -> MetaGraphImplementationKind:
    view = MetaGraphRuntimeIndexView(
        index=cast(MetaGraphCommitIndex, cast(object, context.index)),
        implementation_policy=context.implementation_policy,
    )
    for descriptor in view.implementation_descriptors_by_id.values():
        function_config = descriptor.function_config
        if (
            function_config.owner_key == owner_key
            and function_config.name == function_name
        ):
            return descriptor.kind
    raise AssertionError(f"Function descriptor not found: {owner_key}.{function_name}")


def _has_meta_handler(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in sdk_meta_handlers.AWARE_META_GRAPH_HANDLERS
    )


def _has_empty_lane_bootstrap(*, owner_key: str, function_name: str) -> bool:
    return any(
        key.owner_key == owner_key and key.function_name == function_name
        for key in sdk_meta_handlers.AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS
    )


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


@pytest.mark.asyncio
async def test_sdk_config_projection_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_api_ontology  # noqa: F401
    import aware_sdk_ontology  # noqa: F401
    from aware_api_ontology.stable_ids import (
        stable_api_call_id,
        stable_api_capability_endpoint_id,
        stable_api_capability_id,
        stable_api_id,
    )
    from aware_sdk_ontology.sdk.sdk_config import SdkConfig
    from aware_sdk_ontology.stable_ids import (
        stable_sdk_config_id,
        stable_sdk_operation_api_capability_endpoint_id,
        stable_sdk_operation_call_id,
        stable_sdk_operation_dependency_id,
        stable_sdk_operation_id,
    )

    sdk_config_id = stable_sdk_config_id(name="workspace_sdk")
    operation_id = stable_sdk_operation_id(
        sdk_config_id=sdk_config_id,
        name="read_status",
    )
    workspace_api_id = stable_api_id(name="workspace")
    status_capability_id = stable_api_capability_id(
        api_id=workspace_api_id,
        name="status",
    )
    status_endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=status_capability_id,
        name="status",
    )
    operation_endpoint_id = stable_sdk_operation_api_capability_endpoint_id(
        sdk_operation_id=operation_id,
        name="status",
        api_capability_endpoint_id=status_endpoint_id,
    )
    target_sdk_config_id = stable_sdk_config_id(name="workspace_sdk")
    target_operation_id = stable_sdk_operation_id(
        sdk_config_id=target_sdk_config_id,
        name="load_status",
    )
    operation_dependency_id = stable_sdk_operation_dependency_id(
        sdk_operation_id=operation_id,
        target_sdk_operation_id=target_operation_id,
    )
    call_key = uuid5(NAMESPACE_URL, "sdk://tests/config/call")
    api_call_id = stable_api_call_id(
        api_capability_endpoint_id=status_endpoint_id,
        call_key=call_key,
    )
    operation_call_id = stable_sdk_operation_call_id(
        sdk_operation_id=operation_id,
        call_key=call_key,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_sdk_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        assert _has_meta_handler(
            owner_key="aware_sdk.default.sdk.SdkOperation",
            function_name="create_call",
        )
        assert _has_empty_lane_bootstrap(
            owner_key="aware_sdk.default.sdk.SdkOperationCall",
            function_name="create_via_sdk_operation",
        )
        assert (
            _implementation_kind(
                context,
                owner_key="aware_sdk.default.sdk.SdkOperation",
                function_name="create_call",
            )
            is MetaGraphImplementationKind.language_handler
        )
        lane = runtime.bind(
            projection="SdkConfig",
            branch_id=uuid5(NAMESPACE_URL, "sdk://tests/config/branch"),
        )
        with lane.activate(commit=True, publish=False):
            sdk_config = await SdkConfig.build(
                name="workspace_sdk",
                title="Workspace SDK",
                description="Canonical Workspace SDK operation proof.",
            )

        with lane.activate(commit=True, publish=False):
            operation = await sdk_config.add_operation(
                name="read_status",
                title="Read Workspace status",
                description="Read Workspace status through the canonical API contract.",
                implementation_ref="python:aware_workspace_sdk.WorkspaceSdk.status",
            )

        with lane.activate(commit=True, publish=False):
            await operation.bind_api_capability_endpoint(
                name="status",
                api_capability_endpoint_id=status_endpoint_id,
                endpoint_ref="workspace.status.status",
                role="primary",
                order=1,
                required=True,
            )

        with lane.activate(commit=True, publish=False):
            await operation.bind_sdk_operation_dependency(
                target_sdk_operation_id=target_operation_id,
                target_operation_ref="workspace_sdk.load_status",
                target_sdk_name="workspace_sdk",
                target_operation_name="load_status",
                target_package_name="workspace-sdk",
                role="dependency",
                order=1,
                required=True,
                description="Workspace SDK operation dependency.",
            )

        with lane.activate(commit=True, publish=False):
            await operation.create_call(
                call_key=call_key,
                request_hash="sha256:workspace-status-request",
                description="Workspace status SDK dispatch.",
                context_hash="sha256:workspace-status-context",
                status="succeeded",
                api_call_id=api_call_id,
            )

        assert sdk_config.id == sdk_config_id
        assert operation.id == operation_id
        assert lane.last_response is not None
        assert lane.last_response.root_object_id == sdk_config_id
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(sdk_config_id)
    assertions.expect_instance(sdk_config_id)
    assertions.expect_instance(operation_id)
    assertions.expect_instance(operation_endpoint_id)
    assertions.expect_instance(operation_dependency_id)
    assertions.expect_instance(operation_call_id)
    assertions.expect_edge(
        source_id=sdk_config_id,
        target_id=operation_id,
        relationship_name="operations",
    )
    assertions.expect_edge(
        source_id=operation_id,
        target_id=operation_endpoint_id,
        relationship_name="api_capability_endpoints",
    )
    assertions.expect_edge(
        source_id=operation_id,
        target_id=operation_dependency_id,
        relationship_name="sdk_operation_dependencies",
    )
    assertions.expect_edge(
        source_id=operation_id,
        target_id=operation_call_id,
        relationship_name="sdk_operation_calls",
    )
    assertions.expect_primitive(
        instance_id=operation_id,
        field_name="implementation_ref",
        expected="python:aware_workspace_sdk.WorkspaceSdk.status",
    )
    assertions.expect_primitive(
        instance_id=operation_endpoint_id,
        field_name="endpoint_ref",
        expected="workspace.status.status",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=operation_endpoint_id,
        field_name="api_capability_endpoint_id",
        expected=status_endpoint_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=operation_dependency_id,
        field_name="target_sdk_operation_id",
        expected=target_operation_id,
    )
    assertions.expect_primitive(
        instance_id=operation_dependency_id,
        field_name="target_operation_ref",
        expected="workspace_sdk.load_status",
    )
    assertions.expect_primitive(
        instance_id=operation_dependency_id,
        field_name="target_package_name",
        expected="workspace-sdk",
    )
    assertions.expect_primitive(
        instance_id=operation_call_id,
        field_name="request_hash",
        expected="sha256:workspace-status-request",
    )
    assertions.expect_primitive(
        instance_id=operation_call_id,
        field_name="context_hash",
        expected="sha256:workspace-status-context",
    )
    assertions.expect_primitive(
        instance_id=operation_call_id,
        field_name="description",
        expected="Workspace status SDK dispatch.",
    )
    assertions.expect_primitive(
        instance_id=operation_call_id,
        field_name="status",
        expected="succeeded",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=operation_call_id,
        field_name="api_call_id",
        expected=api_call_id,
    )


@pytest.mark.asyncio
async def test_sdk_package_projection_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_sdk_ontology  # noqa: F401
    from aware_api_ontology.stable_ids import stable_api_package_id
    from aware_code.types import JsonArray, JsonObject
    from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id
    from aware_sdk_ontology.sdk.sdk_package import SdkPackage
    from aware_sdk_ontology.stable_ids import (
        stable_sdk_config_id,
        stable_sdk_package_api_package_id,
        stable_sdk_package_dependency_id,
        stable_sdk_package_id,
        stable_sdk_package_object_config_graph_package_id,
    )

    sdk_config_id = stable_sdk_config_id(name="workspace_sdk")
    sdk_package_id = stable_sdk_package_id(name="workspace-sdk")
    api_package_id = stable_api_package_id(name="workspace-service-api")
    target_sdk_package_id = stable_sdk_package_id(name="hub-sdk")
    object_config_graph_package_id = stable_object_config_graph_package_id(
        package_name="workspace-sdk-db",
        fqn_prefix="aware_workspace_sdk_local",
    )
    target_oig_commit_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    object_config_graph_package_oig_commit_id = UUID(
        "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    )
    expected_hash = "c" * 64
    object_config_graph_package_expected_hash = "d" * 64
    package_api_package_id = stable_sdk_package_api_package_id(
        sdk_package_id=sdk_package_id,
        api_package_id=api_package_id,
    )
    package_ocg_package_id = stable_sdk_package_object_config_graph_package_id(
        sdk_package_id=sdk_package_id,
        object_config_graph_package_id=object_config_graph_package_id,
    )
    package_dependency_id = stable_sdk_package_dependency_id(
        sdk_package_id=sdk_package_id,
        target_sdk_package_id=target_sdk_package_id,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_sdk_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            projection="SdkPackage",
            branch_id=uuid5(NAMESPACE_URL, "sdk://tests/package/branch"),
        )
        with lane.activate(commit=True, publish=False):
            sdk_package = await SdkPackage.build(
                name="workspace-sdk",
                sdk_config_id=sdk_config_id,
                fqn_prefix="aware_workspace_sdk",
                version_number=1,
                title="Workspace SDK",
                description="Canonical Workspace SDK package proof.",
                aware_sdk_version=1,
                manifest_relative_path="sdks/workspace/aware/aware.sdk.toml",
                package_root="sdks/workspace/aware",
                sources_root=".",
                include_paths=JsonArray(["*.aware"]),
                exclude_paths=JsonArray([]),
                force_fresh_scan=False,
                compilation_mode="sdk_ontology",
                dependencies=JsonArray(
                    [
                        {
                            "kind": "api_package",
                            "package_name": "workspace-service-api",
                        }
                    ]
                ),
                targets=JsonObject(
                    {
                        "python": {
                            "root_dir": "python",
                            "public_package": {
                                "package_dir": "aware_workspace_sdk",
                            },
                        }
                    }
                ),
            )

        with lane.activate(commit=True, publish=False):
            await sdk_package.attach_api_package(
                api_package_id=api_package_id,
                description="Workspace service API package consumed by the Workspace SDK.",
            )

        with lane.activate(commit=True, publish=False):
            await sdk_package.attach_object_config_graph_package(
                object_config_graph_package_id=object_config_graph_package_id,
                manifest_relative_path="sdks/workspace/db/aware.toml",
                role="local_state",
                package_kind="state",
                object_config_graph_package_object_instance_graph_commit_id=(
                    object_config_graph_package_oig_commit_id
                ),
                expected_hash_sha256=object_config_graph_package_expected_hash,
                description="Workspace SDK-owned local state package.",
            )

        with lane.activate(commit=True, publish=False):
            await sdk_package.attach_sdk_package_dependency(
                target_sdk_package_id=target_sdk_package_id,
                target_package_name="hub-sdk",
                target_sdk_package_object_instance_graph_commit_id=(
                    target_oig_commit_id
                ),
                target_version_number=2,
                expected_hash_sha256=expected_hash,
                description="Hub SDK package consumed by the Workspace SDK.",
            )

        assert sdk_package.id == sdk_package_id
        assert sdk_package.package_root == "sdks/workspace/aware"
        assert sdk_package.sources_root == "."
        assert lane.last_response is not None
        assert lane.last_response.root_object_id == sdk_package_id
        oig = await materialize_meta_runtime_lane_head(
            runtime=runtime,
            lane=lane,
        )

    assertions = MetaOIGAssertions(
        oig=oig,
        index=cast(MetaGraphRuntimeIndex, cast(object, context.index)),
    )
    assertions.expect_root(sdk_package_id)
    assertions.expect_instance(sdk_package_id)
    assertions.expect_instance(package_api_package_id)
    assertions.expect_instance(package_ocg_package_id)
    assertions.expect_instance(package_dependency_id)
    assertions.expect_edge(
        source_id=sdk_package_id,
        target_id=package_api_package_id,
        relationship_name="api_packages",
    )
    assertions.expect_edge(
        source_id=sdk_package_id,
        target_id=package_ocg_package_id,
        relationship_name="object_config_graph_packages",
    )
    assertions.expect_edge(
        source_id=sdk_package_id,
        target_id=package_dependency_id,
        relationship_name="sdk_package_dependencies",
    )
    assertions.expect_primitive(
        instance_id=sdk_package_id,
        field_name="manifest_relative_path",
        expected="sdks/workspace/aware/aware.sdk.toml",
    )
    assertions.expect_primitive(
        instance_id=sdk_package_id,
        field_name="compilation_mode",
        expected="sdk_ontology",
    )
    assertions.expect_primitive(
        instance_id=sdk_package_id,
        field_name="include_paths",
        expected=["*.aware"],
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=sdk_package_id,
        field_name="sdk_config_id",
        expected=sdk_config_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=package_api_package_id,
        field_name="api_package_id",
        expected=api_package_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=package_dependency_id,
        field_name="target_sdk_package_id",
        expected=target_sdk_package_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=package_ocg_package_id,
        field_name="object_config_graph_package_id",
        expected=object_config_graph_package_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=package_ocg_package_id,
        field_name="object_config_graph_package_object_instance_graph_commit_id",
        expected=object_config_graph_package_oig_commit_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=package_dependency_id,
        field_name="target_sdk_package_object_instance_graph_commit_id",
        expected=target_oig_commit_id,
    )
    assertions.expect_primitive(
        instance_id=package_ocg_package_id,
        field_name="manifest_relative_path",
        expected="sdks/workspace/db/aware.toml",
    )
    assertions.expect_primitive(
        instance_id=package_ocg_package_id,
        field_name="role",
        expected="local_state",
    )
    assertions.expect_primitive(
        instance_id=package_ocg_package_id,
        field_name="package_kind",
        expected="state",
    )
    assertions.expect_primitive(
        instance_id=package_ocg_package_id,
        field_name="expected_hash_sha256",
        expected=object_config_graph_package_expected_hash,
    )
    assertions.expect_primitive(
        instance_id=package_dependency_id,
        field_name="target_package_name",
        expected="hub-sdk",
    )
    assertions.expect_primitive(
        instance_id=package_dependency_id,
        field_name="target_version_number",
        expected=2,
    )
    assertions.expect_primitive(
        instance_id=package_dependency_id,
        field_name="expected_hash_sha256",
        expected=expected_hash,
    )


def test_sdk_module_proof_uses_meta_generated_handler_contract(tmp_path: Path) -> None:
    generated_source = Path(sdk_meta_handlers.__file__).read_text()
    assert "aware" + "_runtime" not in generated_source
    assert _has_meta_handler(
        owner_key="aware_sdk.default.sdk.SdkConfig",
        function_name="build",
    )
    assert _has_meta_handler(
        owner_key="aware_sdk.default.sdk.SdkConfig",
        function_name="add_operation",
    )
    assert _has_meta_handler(
        owner_key="aware_sdk.default.sdk.SdkPackage",
        function_name="attach_sdk_package_dependency",
    )
    assert _has_empty_lane_bootstrap(
        owner_key="aware_sdk.default.sdk.SdkConfig",
        function_name="build",
    )

    repo_root = REPO_ROOT
    with IsolatedMetaAwareRoot(tmp_path / "aware_root") as aware_root:
        runtime = _build_sdk_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        context = runtime.context
        assert context is not None
        assert (
            _implementation_kind(
                context,
                owner_key="aware_sdk.default.sdk.SdkConfig",
                function_name="build",
            )
            is MetaGraphImplementationKind.language_handler
        )
        assert (
            _implementation_kind(
                context,
                owner_key="aware_sdk.default.sdk.SdkPackage",
                function_name="attach_sdk_package_dependency",
            )
            is MetaGraphImplementationKind.language_handler
        )
