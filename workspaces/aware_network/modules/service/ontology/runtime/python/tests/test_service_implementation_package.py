from __future__ import annotations

import ast
import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
import json
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Any, Protocol, cast
from uuid import UUID, uuid4

import msgpack
import pytest
from pydantic import BaseModel
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_function_id,
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_graph_capability_function_id,
    stable_api_graph_capability_id,
    stable_api_graph_function_id,
    stable_api_graph_id,
    stable_api_id,
)
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_history.stable_ids import stable_branch_id
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_orm.session.session import Session
from aware_api_runtime.handlers._generated import (
    meta_handlers as api_meta_handlers,
)
from aware_service_ontology.service.service_enums import ServiceOperationStatus
from aware_service_ontology.stable_ids import (
    stable_service_config_api_id,
    stable_service_config_api_projection_id,
    stable_service_config_id,
    stable_service_id,
    stable_service_operation_config_api_endpoint_function_id,
    stable_service_operation_config_api_endpoint_id,
    stable_service_operation_config_id,
    stable_service_operation_id,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from _service_runtime_test_paths import REPO_ROOT


def _protocol_dependency_payload(*, digest: str) -> dict[str, object]:
    return {
        "package_name": "proof-home-api",
        "kind": "api_service_protocol",
        "service_package_provided_api_package_id": str(uuid4()),
        "api_package_id": str(uuid4()),
        "api_package_object_instance_graph_commit_id": str(uuid4()),
        "service_protocol_package_id": str(uuid4()),
        "service_protocol_code_package_id": str(uuid4()),
        "service_protocol_code_package_object_instance_graph_commit_id": str(uuid4()),
        "service_protocol_plan_hash_sha256": digest,
    }


_REPO_ROOT = REPO_ROOT
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_SERVICE_RUNTIME_ROOT_STR = str(
    _REPO_ROOT / "workspaces/aware_network/modules/service/ontology/runtime/python"
)
if _SERVICE_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _SERVICE_RUNTIME_ROOT_STR)
_API_RUNTIME_ROOT_STR = str(
    _REPO_ROOT / "workspaces/aware_kernel/modules/api/ontology/runtime/python"
)
if _API_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _API_RUNTIME_ROOT_STR)

_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)
_SERVICE_META_HANDLERS_ANY: Any = service_meta_handlers
_SERVICE_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _SERVICE_META_HANDLERS_ANY,
)
_SERVICE_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _SERVICE_META_HANDLERS_ANY,
)


def test_service_activation_lane_uses_service_owned_branch_identity() -> None:
    import aware_service_runtime.implementation_package as implementation_package

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:service",
    )

    resolved = implementation_package._service_activation_lane_for_name(
        lane=lane,
        lane_kind="Config",
        service_name="Aware_Identity",
    )
    repeated = implementation_package._service_activation_lane_for_name(
        lane=lane,
        lane_kind="config",
        service_name="aware_identity",
    )

    assert resolved == repeated
    assert resolved.branch_id != lane.branch_id
    assert resolved.projection_hash == lane.projection_hash

    source = Path(implementation_package.__file__).read_text(encoding="utf-8")
    assert "stable_" + "branch_id" not in source


def test_dependency_import_roots_include_api_dependency_code_packages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.implementation_package as implementation_package

    public_root = tmp_path / "public"
    protocol_root = tmp_path / "protocol"
    dto_root = tmp_path / "dto"
    for root in (public_root, protocol_root, dto_root):
        root.mkdir()
    dependency = implementation_package.ServicePackageDependencyBinding(
        package_name="provider-service-api",
        runtime_package_dir=tmp_path / "runtime",
        service_protocol_plan_path=tmp_path / "api.service_protocol_plan.json",
        service_protocol_plan_hash_sha256="sha256:proof",
        endpoint_refs=(),
    )
    monkeypatch.setattr(
        implementation_package,
        "resolve_api_service_protocol_package_roots",
        lambda **_: SimpleNamespace(
            public_package_root=public_root,
            service_protocol_package_root=protocol_root,
        ),
    )

    roots = implementation_package._dependency_import_roots(
        dependencies=(dependency,),
        runtime_python_roots=(dto_root, dto_root),
    )

    assert roots == (dto_root, public_root, protocol_root)


def test_protocol_dependency_artifact_resolves_from_committed_dependency_root(
    tmp_path: Path,
) -> None:
    import aware_service_runtime.implementation_package as implementation_package

    product_root = tmp_path / "product"
    dependency_root = tmp_path / "kernel-revision"
    runtime_dir = dependency_root / ".aware/api/runtime/proof-home-api"
    runtime_dir.mkdir(parents=True)
    plan_path = runtime_dir / "api.service_protocol_plan.json"
    plan_path.write_text('{"apis": []}\n', encoding="utf-8")
    digest = implementation_package._hash_json_artifact(plan_path)
    compile_result = SimpleNamespace(
        activation_plan=object(),
        snapshot=SimpleNamespace(spec_path=product_root / "aware.service.toml"),
    )

    dependencies = implementation_package._resolve_api_service_protocol_dependencies(
        repo_root=product_root,
        compile_result=compile_result,
        dependency_payloads=(_protocol_dependency_payload(digest=digest),),
        dependency_workspace_roots=(dependency_root,),
    )

    assert len(dependencies) == 1
    assert dependencies[0].runtime_package_dir == runtime_dir
    assert dependencies[0].service_protocol_plan_path == plan_path


def test_committed_binding_forwards_dependency_workspace_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.implementation_package as implementation_package

    dependency_root = tmp_path / "kernel-revision"
    compile_result = object()
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        implementation_package,
        "compile_committed_service_package_workspace",
        lambda **_: compile_result,
    )

    def _prepare(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        implementation_package,
        "_prepare_service_package_binding_from_compile_result",
        _prepare,
    )
    package_ref = SimpleNamespace(
        service_package=object(),
        materialized_workspace_root=tmp_path / "product-revision",
        dependency_payloads=(),
        dependency_workspace_roots=(dependency_root,),
        package_name="aware-proof-service",
    )

    implementation_package.prepare_committed_service_package_binding(
        package_ref=package_ref,
    )

    assert captured["compile_result"] is compile_result
    assert captured["dependency_workspace_roots"] == (dependency_root,)


@dataclass(frozen=True, slots=True)
class _MetaLaneIds:
    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    branch_id: UUID
    actor_id: UUID | None = None


def _service_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


def _build_service_meta_runtime(
    repo_root: Path,
    *,
    workspace_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=workspace_root,
        handler_modules=(
            _API_META_HANDLER_MODULE,
            _SERVICE_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _API_META_BOOTSTRAP_MODULE,
            _SERVICE_META_BOOTSTRAP_MODULE,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    return runtime


def _runtime_index(runtime: MetaGraphRuntime) -> MetaGraphRuntimeIndex:
    assert runtime.context is not None
    return runtime.context.index


def _write_dependency_runtime_ocg_snapshot(
    *,
    workspace_root: Path,
    ontology_toml_path: Path,
) -> ObjectConfigGraph:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=(ontology_toml_path,),
        workspace_root=workspace_root,
        aware_root=workspace_root / ".aware" / "dependency-runtime-proof",
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=(MetaGraphFunctionImplOwnership.authored),
        ),
    )
    assert runtime.context is not None
    package_root = ontology_toml_path.parent
    package = _RuntimeDependencyPackage(
        package_name="home-ontology",
        aware_toml_path=ontology_toml_path.resolve(),
        package_root=package_root.resolve(),
        spec=load_aware_toml_spec(toml_path=ontology_toml_path),
    )
    runtime_root = package.runtime_manifest_path.parent
    runtime_root.mkdir(parents=True, exist_ok=True)
    package.runtime_manifest_path.write_text(
        '{"ocg": {"snapshot": "ocg.snapshot.msgpack"}}\n',
        encoding="utf-8",
    )
    snapshot_payload = runtime.context.index.ocg.model_dump(
        mode="json",
        exclude_none=True,
    )
    (runtime_root / "ocg.snapshot.msgpack").write_bytes(
        msgpack.packb(
            snapshot_payload,
            use_bin_type=True,
        )
    )
    package.runtime_source_digest_path.parent.mkdir(parents=True, exist_ok=True)
    package.runtime_source_digest_path.write_text(
        _compute_runtime_dependency_source_digest(package=package),
        encoding="utf-8",
    )
    return runtime.context.index.ocg


from aware_api_runtime.compile import compile_api_workspace  # noqa: E402
from aware_api_runtime.dependencies.runtime_resolution import (  # noqa: E402
    _RuntimeDependencyPackage,
    _compute_runtime_dependency_source_digest,
)
from aware_api_runtime.invocation import (  # noqa: E402
    ResolvedApiInvocationEnvelope,
    build_resolved_api_invocation_envelope,
    resolve_api_invocation_ir,
)
from aware_api_runtime.models import (  # noqa: E402
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.invocation.materialization import (
    materialize_api_call,
)  # noqa: E402
from aware_api_runtime.compile_materialization.service import (  # noqa: E402
    materialize_api_compile_plan_ontology,
    resolve_source_owned_api_dto_export_accessible_graphs,
)
from aware_api_runtime.service_protocol import (  # noqa: E402
    build_api_service_dispatch_plan,
)
from aware_api_runtime.service_protocol.runtime import (  # noqa: E402
    ApiServiceDispatchPlan,
    ApiServiceProtocolExecution,
    ApiServiceProtocolEndpointBinding,
    LoadedApiServiceProtocolPackage,
)
from aware_meta.manifest.loader import load_aware_toml_spec  # noqa: E402
from aware_service_runtime.implementation_package import (  # noqa: E402
    _activate_prepared_service_package_binding,
    _materialize_service_subscriptions,
    _role_reference_branch_ids_for_activation,
    _resolve_generated_request_model_class,
    activate_service_package_binding,
    build_service_operation_request_for_api_dispatch,
    execute_activated_service_api_dispatch_request,
    prepare_service_package_binding,
)
from aware_service_runtime.builder import (  # noqa: E402
    ServiceCompilePlan,
)
from aware_service_runtime.models import (  # noqa: E402
    ServiceConfigApiPlan,
    ServiceConfigApiProjectionPlan,
    ServiceConfigPlan,
)
from aware_service_runtime.materialization.service import (  # noqa: E402
    stable_service_role_reference_branch_id,
)
from aware_service_runtime.api_ingress.execution_context import (  # noqa: E402
    ServiceApiExecutionBackend,
)
from aware_service_runtime.contracts import (  # noqa: E402
    ServiceOperationContext,
)


def test_service_implementation_package_has_no_direct_deprecated_runtime_imports() -> (
    None
):
    source_path = (
        _REPO_ROOT
        / "workspaces"
        / "aware_network"
        / "modules"
        / "service"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_service_runtime"
        / "implementation_package.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] == "aware_runtime":
                    offenders.append(f"{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] == "aware_runtime":
                offenders.append(f"{node.lineno}: from {node.module} import ...")

    assert offenders == []


class _OpenDoorEndpointBindingProtocol(Protocol):
    requests: list[object]

    async def open_door(
        self,
        request: BaseModel,
        execution: ApiServiceProtocolExecution,
    ) -> object | None: ...


class _HomeDevicesBindingProtocol(Protocol):
    open_door: _OpenDoorEndpointBindingProtocol


class _HomeStoryServiceBindingProtocol(Protocol):
    home_devices: _HomeDevicesBindingProtocol


class _OpenDoorExecutionBindingProtocol(ApiServiceProtocolExecution, Protocol):
    async def open(self, request: BaseModel) -> object | None: ...


class _ProofDispatchRequest(BaseModel):
    dry_run: bool


def test_role_reference_branch_ids_for_activation_derive_from_compile_plan_payload() -> (
    None
):
    explicit_branch_id = uuid4()
    fallback_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:service-config",
    )
    payload = {
        "service_configs": [
            {
                "name": "aware_identity",
                "service_operation_configs": [
                    {
                        "name": "resolve_role_assignments",
                        "role_requirements": [
                            {"role_ref": "identity.actor_reader"},
                        ],
                    },
                ],
                "contract_configs": [
                    {
                        "name": "actor_continuity",
                        "actor_role_grants": [
                            {"role_ref": "identity.actor_reader"},
                            {"role_ref": "identity.actor_writer"},
                        ],
                    },
                ],
            },
        ],
    }

    derived = _role_reference_branch_ids_for_activation(
        provided=None,
        payload=payload,
    )
    expected_reader_branch_id = stable_service_role_reference_branch_id(
        role_ref="identity.actor_reader",
    )
    expected_writer_branch_id = stable_service_role_reference_branch_id(
        role_ref="identity.actor_writer",
    )

    assert expected_reader_branch_id != fallback_lane.branch_id
    assert expected_writer_branch_id != fallback_lane.branch_id
    assert derived["identity.actor_reader"] == expected_reader_branch_id
    assert derived["identity.actor_writer"] == expected_writer_branch_id
    assert derived["IDENTITY.ACTOR_READER".casefold()] == expected_reader_branch_id

    provided = _role_reference_branch_ids_for_activation(
        provided={"identity.actor_reader": explicit_branch_id},
        payload=payload,
    )

    assert provided["identity.actor_reader"] == explicit_branch_id
    assert provided["IDENTITY.ACTOR_READER".casefold()] == explicit_branch_id
    assert "identity.actor_writer" not in provided


@pytest.mark.asyncio
async def test_activation_passes_derived_role_reference_branches_to_service_materializer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    compile_plan_path = tmp_path / "service.compile_plan.json"
    compile_plan_path.write_text(
        """
{
  "service_configs": [
    {
      "name": "aware_identity",
      "service_operation_configs": [
        {
          "name": "resolve_role_assignments",
          "role_requirements": [
            {"role_ref": "identity.actor_reader"}
          ]
        }
      ],
      "contract_configs": [
        {
          "name": "actor_continuity",
          "actor_role_grants": [
            {"role_ref": "identity.actor_reader"}
          ]
        }
      ]
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    captured_role_refs: dict[str, UUID] = {}

    async def _fake_materialize_service_definition_ontology(**kwargs: object) -> object:
        value = kwargs["role_reference_branch_ids_by_role_name"]
        assert isinstance(value, Mapping)
        captured_role_refs.update(cast(Mapping[str, UUID], value))
        return object()

    async def _fake_load_committed_service_ids_if_available(**_: object) -> None:
        return None

    async def _fake_materialize_service_instances(**_: object) -> Mapping[str, UUID]:
        return {"aware_identity": uuid4()}

    async def _fake_materialize_service_subscriptions(
        **_: object,
    ) -> Mapping[str, tuple[object, ...]]:
        return {}

    catchup_lanes: list[MaterializationLaneContext] = []

    async def _fake_ensure_service_activation_lane_projection_caught_up(
        **kwargs: object,
    ) -> object:
        catchup_lanes.append(cast(MaterializationLaneContext, kwargs["lane"]))
        return SimpleNamespace(commits_applied=1, skipped_reason=None)

    monkeypatch.setattr(
        implementation_package,
        "materialize_service_definition_ontology",
        _fake_materialize_service_definition_ontology,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_committed_service_ids_if_available",
        _fake_load_committed_service_ids_if_available,
    )
    monkeypatch.setattr(
        implementation_package,
        "_committed_lane_head_commit_id",
        lambda **_kwargs: _async_value(None),
    )
    monkeypatch.setattr(
        implementation_package,
        "_materialize_service_instances",
        _fake_materialize_service_instances,
    )
    monkeypatch.setattr(
        implementation_package,
        "_materialize_service_subscriptions",
        _fake_materialize_service_subscriptions,
    )
    monkeypatch.setattr(
        implementation_package,
        "_ensure_service_activation_lane_projection_caught_up",
        _fake_ensure_service_activation_lane_projection_caught_up,
    )

    branch_id = uuid4()
    lane = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash="sha256:service-config",
    )
    prepared = SimpleNamespace(
        compile_result=SimpleNamespace(
            activation_plan=SimpleNamespace(materialize_on_start=True),
            compile_plan=object(),
            compile_plan_artifact=SimpleNamespace(path=compile_plan_path),
        ),
        service_bindings={"aware_identity": object()},
    )

    await _activate_prepared_service_package_binding(
        prepared=cast(Any, prepared),
        runtime=object(),
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=None,
        service_config_lane=lane,
        service_lane=lane,
    )

    expected_branch_id = stable_service_role_reference_branch_id(
        role_ref="identity.actor_reader",
    )
    assert expected_branch_id != branch_id
    assert captured_role_refs["identity.actor_reader"] == expected_branch_id
    assert captured_role_refs["IDENTITY.ACTOR_READER".casefold()] == expected_branch_id
    assert len(catchup_lanes) == 2
    assert catchup_lanes[0].projection_hash == lane.projection_hash
    assert catchup_lanes[1].projection_hash == lane.projection_hash
    assert catchup_lanes[0].branch_id != catchup_lanes[1].branch_id


@pytest.mark.asyncio
async def test_activation_rematerializes_when_service_config_head_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    compile_plan_path = tmp_path / "service.compile_plan.json"
    compile_plan_path.write_text(
        '{"service_configs":[{"name":"aware_conversation"}]}\n',
        encoding="utf-8",
    )
    service_id = uuid4()
    materialized_lanes: list[MaterializationLaneContext] = []

    async def _fake_materialize_service_definition_ontology(
        **kwargs: object,
    ) -> object:
        materialized_lanes.append(cast(MaterializationLaneContext, kwargs["lane"]))
        return object()

    monkeypatch.setattr(
        implementation_package,
        "_load_committed_service_ids_if_available",
        lambda **_kwargs: _async_value({"aware_conversation": service_id}),
    )
    monkeypatch.setattr(
        implementation_package,
        "_committed_lane_head_commit_id",
        lambda **_kwargs: _async_value(None),
    )
    monkeypatch.setattr(
        implementation_package,
        "materialize_service_definition_ontology",
        _fake_materialize_service_definition_ontology,
    )
    monkeypatch.setattr(
        implementation_package,
        "_materialize_service_instances",
        lambda **_kwargs: _async_value({"aware_conversation": service_id}),
    )
    monkeypatch.setattr(
        implementation_package,
        "_ensure_service_activation_lane_projection_caught_up",
        lambda **_kwargs: _async_value(
            SimpleNamespace(commits_applied=1, skipped_reason=None)
        ),
    )
    monkeypatch.setattr(
        implementation_package,
        "_materialize_service_subscriptions",
        lambda **_kwargs: _async_value({}),
    )
    prepared = SimpleNamespace(
        compile_result=SimpleNamespace(
            activation_plan=SimpleNamespace(materialize_on_start=True),
            compile_plan=object(),
            compile_plan_artifact=SimpleNamespace(path=compile_plan_path),
        ),
        service_bindings={"aware_conversation": object()},
    )

    activated = await implementation_package._activate_prepared_service_package_binding(
        prepared=cast(Any, prepared),
        runtime=object(),
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=None,
        service_config_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="sha256:service-config",
        ),
        service_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="sha256:service",
        ),
    )

    assert activated.service_ids_by_name == {"aware_conversation": service_id}
    assert len(materialized_lanes) == 1
    assert (
        materialized_lanes[0]
        == activated.service_config_lanes_by_name["aware_conversation"]
    )


@pytest.mark.asyncio
async def test_read_only_activation_rejects_missing_service_config_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    compile_plan_path = tmp_path / "service.compile_plan.json"
    compile_plan_path.write_text(
        '{"service_configs":[{"name":"aware_conversation"}]}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_committed_service_ids_if_available",
        lambda **_kwargs: _async_value({"aware_conversation": uuid4()}),
    )
    monkeypatch.setattr(
        implementation_package,
        "_committed_lane_head_commit_id",
        lambda **_kwargs: _async_value(None),
    )
    prepared = SimpleNamespace(
        compile_result=SimpleNamespace(
            activation_plan=SimpleNamespace(materialize_on_start=True),
            compile_plan=object(),
            compile_plan_artifact=SimpleNamespace(path=compile_plan_path),
        ),
        service_bindings={"aware_conversation": object()},
    )

    with pytest.raises(
        implementation_package.ServiceActivationRequiresMaterialization,
        match="service_config_head_available=False service_head_available=True",
    ):
        await implementation_package._activate_prepared_service_package_binding(
            prepared=cast(Any, prepared),
            runtime=object(),
            index=cast(MetaGraphRuntimeIndex, object()),
            actor_id=None,
            service_config_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="sha256:service-config",
            ),
            service_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="sha256:service",
            ),
            allow_materialization=False,
        )


@pytest.mark.asyncio
async def test_committed_lane_head_uses_explicit_revision_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    mutable_root = tmp_path / "node-state"
    revision_root = tmp_path / "workspace-revision"
    branch_id = uuid4()
    commit_id = uuid4()
    projection_hash = "sha256:service-config"
    head_path = (
        revision_root
        / ".aware"
        / "oig"
        / str(branch_id)
        / projection_hash
        / "HEAD.json"
    )
    head_path.parent.mkdir(parents=True)
    head_path.write_text(
        json.dumps({"commit_id": str(commit_id)}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AWARE_ROOT", str(mutable_root))

    lane = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert (
        await implementation_package._committed_lane_head_commit_id(lane=lane) is None
    )
    assert (
        await implementation_package._committed_lane_head_commit_id(
            lane=lane,
            commit_store_root=revision_root,
        )
        == commit_id
    )


@pytest.mark.asyncio
async def test_non_materializing_activation_rejects_missing_service_config_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    compile_plan_path = tmp_path / "service.compile_plan.json"
    compile_plan_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        implementation_package,
        "_load_committed_service_ids_if_available",
        lambda **_kwargs: _async_value({"aware_conversation": uuid4()}),
    )
    monkeypatch.setattr(
        implementation_package,
        "_committed_lane_head_commit_id",
        lambda **_kwargs: _async_value(None),
    )
    prepared = SimpleNamespace(
        compile_result=SimpleNamespace(
            activation_plan=SimpleNamespace(materialize_on_start=False),
            compile_plan=object(),
            compile_plan_artifact=SimpleNamespace(path=compile_plan_path),
        ),
        service_bindings={"aware_conversation": object()},
    )

    with pytest.raises(
        implementation_package.ServiceActivationRequiresMaterialization,
        match="when materialize_on_start is false",
    ):
        await implementation_package._activate_prepared_service_package_binding(
            prepared=cast(Any, prepared),
            runtime=object(),
            index=cast(MetaGraphRuntimeIndex, object()),
            actor_id=None,
            service_config_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="sha256:service-config",
            ),
            service_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="sha256:service",
            ),
        )


@pytest.mark.asyncio
async def test_activation_reuses_only_when_both_lane_heads_are_committed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    compile_plan_path = tmp_path / "service.compile_plan.json"
    compile_plan_path.write_text(
        '{"service_configs":[{"name":"aware_conversation"}]}\n',
        encoding="utf-8",
    )
    service_id = uuid4()
    config_head_commit_id = uuid4()
    caught_up: list[tuple[MaterializationLaneContext, UUID]] = []

    async def _fake_catchup(**kwargs: object) -> object:
        caught_up.append(
            (
                cast(MaterializationLaneContext, kwargs["lane"]),
                cast(UUID, kwargs["head_commit_id"]),
            )
        )
        return SimpleNamespace(commits_applied=0, skipped_reason="already_current")

    async def _unexpected_materialization(**_kwargs: object) -> object:
        raise AssertionError("paired committed lanes must be reused")

    monkeypatch.setattr(
        implementation_package,
        "_load_committed_service_ids_if_available",
        lambda **_kwargs: _async_value({"aware_conversation": service_id}),
    )
    monkeypatch.setattr(
        implementation_package,
        "_committed_lane_head_commit_id",
        lambda **_kwargs: _async_value(config_head_commit_id),
    )
    monkeypatch.setattr(
        implementation_package,
        "_ensure_committed_service_lane_projection_caught_up",
        _fake_catchup,
    )
    monkeypatch.setattr(
        implementation_package,
        "materialize_service_definition_ontology",
        _unexpected_materialization,
    )
    monkeypatch.setattr(
        implementation_package,
        "_materialize_service_instances",
        _unexpected_materialization,
    )
    monkeypatch.setattr(
        implementation_package,
        "_materialize_service_subscriptions",
        lambda **_kwargs: _async_value({}),
    )
    prepared = SimpleNamespace(
        compile_result=SimpleNamespace(
            activation_plan=SimpleNamespace(materialize_on_start=True),
            compile_plan=object(),
            compile_plan_artifact=SimpleNamespace(path=compile_plan_path),
        ),
        service_bindings={"aware_conversation": object()},
    )

    activated = await implementation_package._activate_prepared_service_package_binding(
        prepared=cast(Any, prepared),
        runtime=object(),
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=None,
        service_config_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="sha256:service-config",
        ),
        service_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="sha256:service",
        ),
    )

    assert activated.service_ids_by_name == {"aware_conversation": service_id}
    assert caught_up == [
        (
            activated.service_config_lanes_by_name["aware_conversation"],
            config_head_commit_id,
        )
    ]


@pytest.mark.asyncio
async def test_activation_rejects_materialization_without_required_lane_heads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    compile_plan_path = tmp_path / "service.compile_plan.json"
    compile_plan_path.write_text(
        '{"service_configs":[{"name":"aware_conversation"}]}\n',
        encoding="utf-8",
    )
    service_id = uuid4()
    monkeypatch.setattr(
        implementation_package,
        "_load_committed_service_ids_if_available",
        lambda **_kwargs: _async_value(None),
    )
    monkeypatch.setattr(
        implementation_package,
        "_committed_lane_head_commit_id",
        lambda **_kwargs: _async_value(None),
    )
    monkeypatch.setattr(
        implementation_package,
        "materialize_service_definition_ontology",
        lambda **_kwargs: _async_value(object()),
    )
    monkeypatch.setattr(
        implementation_package,
        "_materialize_service_instances",
        lambda **_kwargs: _async_value({"aware_conversation": service_id}),
    )
    monkeypatch.setattr(
        implementation_package,
        "_ensure_service_activation_lane_projection_caught_up",
        lambda **_kwargs: _async_value(None),
    )
    prepared = SimpleNamespace(
        compile_result=SimpleNamespace(
            activation_plan=SimpleNamespace(materialize_on_start=True),
            compile_plan=object(),
            compile_plan_artifact=SimpleNamespace(path=compile_plan_path),
        ),
        service_bindings={"aware_conversation": object()},
    )

    with pytest.raises(
        RuntimeError,
        match="did not commit both required ServiceConfig/Service lane heads",
    ):
        await implementation_package._activate_prepared_service_package_binding(
            prepared=cast(Any, prepared),
            runtime=object(),
            index=cast(MetaGraphRuntimeIndex, object()),
            actor_id=None,
            service_config_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="sha256:service-config",
            ),
            service_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="sha256:service",
            ),
        )


async def _async_value(value: object) -> Any:
    return value


@pytest.mark.asyncio
async def test_committed_service_id_reuse_catches_up_projection_before_hydration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.implementation_package as implementation_package

    head_commit_id = uuid4()
    hydrated_service_id = uuid4()
    calls: list[tuple[str, object]] = []

    async def _fake_committed_lane_head_commit_id(**kwargs: object) -> UUID:
        calls.append(("head", kwargs["lane"]))
        return head_commit_id

    async def _fake_catchup(**kwargs: object) -> object:
        calls.append(("catchup", kwargs["head_commit_id"]))
        return SimpleNamespace(commits_applied=1, skipped_reason=None)

    async def _fake_load_committed_service_ids(**kwargs: object) -> Mapping[str, UUID]:
        calls.append(("hydrate", kwargs["lane"]))
        return {"aware_meta": hydrated_service_id}

    monkeypatch.setattr(
        implementation_package,
        "_committed_lane_head_commit_id",
        _fake_committed_lane_head_commit_id,
    )
    monkeypatch.setattr(
        implementation_package,
        "_ensure_committed_service_lane_projection_caught_up",
        _fake_catchup,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_committed_service_ids",
        _fake_load_committed_service_ids,
    )

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:service",
    )

    result = await implementation_package._load_committed_service_ids_if_available(
        index=cast(MetaGraphRuntimeIndex, object()),
        lane=lane,
        service_names=("aware_meta",),
    )

    assert result == {"aware_meta": hydrated_service_id}
    assert calls == [
        ("head", lane),
        ("catchup", head_commit_id),
        ("hydrate", lane),
    ]


@pytest.mark.asyncio
async def test_committed_service_projection_catchup_uses_activation_readiness_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.implementation_package as implementation_package

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:service",
    )
    head_commit_id = uuid4()
    captured: dict[str, object] = {}

    async def _fake_projection_readiness(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(commits_applied=1, skipped_reason=None)

    monkeypatch.setattr(
        implementation_package,
        "ensure_projection_readiness",
        _fake_projection_readiness,
    )

    result = await implementation_package._ensure_committed_service_lane_projection_caught_up(
        index=cast(MetaGraphRuntimeIndex, object()),
        lane=lane,
        head_commit_id=head_commit_id,
    )

    assert result.commits_applied == 1
    assert captured["index"] is not None
    requirement = captured["requirement"]
    assert requirement.name == "service.activation"
    assert requirement.branch_id == lane.branch_id
    assert requirement.projection_hash == lane.projection_hash
    assert requirement.head_commit_id == head_commit_id
    assert requirement.mode == "required_db"


@pytest.mark.asyncio
async def test_committed_service_projection_catchup_uses_typed_session_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_service_runtime.implementation_package as implementation_package

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:service",
    )
    head_commit_id = uuid4()
    projection_session = Session(branch_id=lane.branch_id, backend_name="noop")
    captured: dict[str, object] = {}
    resolved_lanes: list[MaterializationLaneContext] = []

    def _resolve_session(
        resolved_lane: MaterializationLaneContext,
    ) -> Session:
        resolved_lanes.append(resolved_lane)
        return projection_session

    async def _fake_projection_readiness(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(commits_applied=1, skipped_reason=None)

    monkeypatch.setattr(
        implementation_package,
        "ensure_projection_readiness",
        _fake_projection_readiness,
    )

    await implementation_package._ensure_committed_service_lane_projection_caught_up(
        index=cast(MetaGraphRuntimeIndex, object()),
        lane=lane,
        head_commit_id=head_commit_id,
        projection_session_resolver=_resolve_session,
    )

    assert resolved_lanes == [lane]
    assert captured["session"] is projection_session


def test_resolve_generated_request_model_class_uses_service_protocol_dto_ref(
    tmp_path: Path,
) -> None:
    public_root = tmp_path / "public"
    protocol_root = tmp_path / "protocol"
    public_package = public_root / "proof_public_api"
    protocol_package = protocol_root / "proof_public_protocol"
    dto_package = protocol_root / "proof_dto"
    public_package.mkdir(parents=True)
    protocol_package.mkdir(parents=True)
    dto_package.mkdir(parents=True)
    (public_package / "__init__.py").write_text("", encoding="utf-8")
    (protocol_package / "__init__.py").write_text("", encoding="utf-8")
    (dto_package / "__init__.py").write_text("", encoding="utf-8")
    (dto_package / "requests.py").write_text(
        "\n".join(
            [
                "from pydantic import BaseModel",
                "",
                "class ProofRequest(BaseModel):",
                "    value: str",
            ]
        ),
        encoding="utf-8",
    )
    (protocol_package / "protocols.py").write_text(
        "from proof_dto.requests import ProofRequest\n",
        encoding="utf-8",
    )

    loaded_package = LoadedApiServiceProtocolPackage(
        runtime_package_dir=tmp_path,
        public_package_root=public_root,
        service_protocol_package_root=protocol_root,
        public_package_import_root="proof_public_api",
        service_protocol_import_root="proof_public_protocol",
        endpoint_bindings={},
        runtime_fulfillment_bindings={},
    )

    async def _invoke(
        _handler: object,
        _request: BaseModel,
        _execution: object | None = None,
    ) -> None:
        return None

    endpoint_binding = ApiServiceProtocolEndpointBinding(
        endpoint_ref="proof.fetch",
        request_type_ref="proof_dto.ProofRequest",
        response_type_ref=None,
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=_invoke,
    )

    resolved = _resolve_generated_request_model_class(
        loaded_package=loaded_package,
        endpoint_binding=endpoint_binding,
    )

    assert resolved.__name__ == "ProofRequest"
    assert issubclass(resolved, BaseModel)


@pytest.mark.asyncio
async def test_build_activated_service_api_dispatch_plan_from_ingress_uses_api_dispatcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    ir = resolve_api_invocation_ir(
        api_ownership=_api_ownership_for_runtime(
            request_class_ref="aware_home_api.door.OpenDoor"
        ),
        endpoint_ref="home_devices.open_door.open_door",
        request_payload={"dry_run": False},
    )
    envelope = ResolvedApiInvocationEnvelope(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=uuid4(),
        request_hash="sha256:service-dispatcher-proof",
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
        api_name=ir.api_name,
        capability_name=ir.capability_name,
        endpoint_name=ir.endpoint_name,
        endpoint_ref=ir.endpoint_ref,
        discriminant=ir.discriminant,
        source_path=ir.source_path,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        request_class_ref=ir.request_class_ref,
        request_source_path=ir.request_source_path,
        response_class_ref=ir.response_class_ref,
        response_source_path=ir.response_source_path,
        stream=ir.stream,
        fulfillment_bindings=ir.fulfillment_bindings,
        description=ir.description,
    )
    expected_plan = SimpleNamespace(
        request_type_ref="aware_home_api.door.OpenDoor",
        request_object=_ProofDispatchRequest(dry_run=False),
    )
    captured: dict[str, object] = {}
    dependency = SimpleNamespace(
        runtime_package_dir=Path("/tmp/aware-api-runtime-proof"),
        service_protocol_plan_hash_sha256="sha256:service-protocol-plan",
    )

    async def _fake_dispatch_api_invocation(**kwargs: object) -> object:
        from aware_api_runtime.invocation.materialization.telemetry import (
            api_invocation_trace_phase,
        )

        captured["dispatch"] = kwargs
        with api_invocation_trace_phase(
            "api_invocation.materialize_api_call.create_api_call",
        ):
            pass
        return SimpleNamespace(
            envelope=envelope,
            materialized_call=SimpleNamespace(
                api_call=object(),
                request_class_config=object(),
            ),
        )

    async def _fake_build_api_service_dispatch_plan(**kwargs: object) -> object:
        captured["plan"] = kwargs
        return expected_plan

    monkeypatch.setattr(
        implementation_package,
        "_resolve_service_endpoint_dependency",
        lambda **_: dependency,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_dependency_api_invocation_manifest",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        implementation_package,
        "_build_api_invocation_ir_from_loaded_manifest",
        lambda **_: ir,
    )
    monkeypatch.setattr(
        implementation_package,
        "dispatch_api_invocation",
        _fake_dispatch_api_invocation,
    )
    monkeypatch.setattr(
        implementation_package,
        "build_api_service_dispatch_plan_from_materialized_call",
        _fake_build_api_service_dispatch_plan,
    )

    api_source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api",
    )
    api_call_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )
    call_key = uuid4()
    from aware_service_runtime.api_ingress.telemetry import (
        collect_service_api_trace_timings,
    )

    with collect_service_api_trace_timings() as timings:
        result = await implementation_package.build_activated_service_api_dispatch_plan_from_ingress(
            activated=cast(
                Any,
                SimpleNamespace(
                    prepared=object(),
                    api_reference_branch_ids_by_api_name={},
                ),
            ),
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            actor_id=uuid4(),
            api_source_lane=api_source_lane,
            api_call_lane=api_call_lane,
            service_name="aware_home",
            endpoint_ref="home_devices.open_door.open_door",
            discriminant="home_devices.open_door.open_door",
            request_payload={"dry_run": False},
            call_key=call_key,
        )

    assert result is expected_plan
    assert "service_host.api_ingress.dispatch_plan.resolve_dependency_s" in timings
    assert (
        "service_host.api_ingress.dispatch_plan.load_invocation_manifest_s" in timings
    )
    assert "service_host.api_ingress.dispatch_plan.build_invocation_ir_s" in timings
    assert "service_host.api_ingress.dispatch_plan.dispatch_api_invocation_s" in timings
    assert (
        "service_host.api_ingress.dispatch_plan."
        "api_invocation.materialize_api_call.create_api_call_s" in timings
    )
    assert (
        "service_host.api_ingress.dispatch_plan.build_from_materialized_call_s"
        in timings
    )
    assert "service_host.api_ingress.dispatch_plan.payload_field_guard_s" in timings
    dispatch_kwargs = cast(dict[str, object], captured["dispatch"])
    assert dispatch_kwargs["ir"] is ir
    assert dispatch_kwargs["call_key"] == call_key
    assert dispatch_kwargs["source_lane"] is api_source_lane
    resolved_target_lane = cast(
        MaterializationLaneContext, dispatch_kwargs["target_lane"]
    )
    assert resolved_target_lane.branch_id == api_source_lane.branch_id
    assert resolved_target_lane.projection_hash == api_call_lane.projection_hash
    plan_kwargs = cast(dict[str, object], captured["plan"])
    assert plan_kwargs["envelope"] is envelope
    assert plan_kwargs["runtime_package_dir"] == dependency.runtime_package_dir


@pytest.mark.asyncio
async def test_build_activated_service_api_dispatch_plan_endpoint_only_deferred(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    ir = resolve_api_invocation_ir(
        api_ownership=_api_ownership_for_runtime(
            request_class_ref="aware_home_api.door.OpenDoor",
            include_function=False,
        ),
        endpoint_ref="home_devices.open_door.open_door",
        request_payload={"dry_run": False},
    )
    envelope = ResolvedApiInvocationEnvelope(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=uuid4(),
        request_hash="sha256:service-deferred-proof",
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
        api_name=ir.api_name,
        capability_name=ir.capability_name,
        endpoint_name=ir.endpoint_name,
        endpoint_ref=ir.endpoint_ref,
        discriminant=ir.discriminant,
        source_path=ir.source_path,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        request_class_ref=ir.request_class_ref,
        request_source_path=ir.request_source_path,
        response_class_ref=ir.response_class_ref,
        response_source_path=ir.response_source_path,
        stream=ir.stream,
        fulfillment_bindings=ir.fulfillment_bindings,
        description=ir.description,
    )

    async def _fake_invoke(
        _handler: object,
        _request: BaseModel,
        _execution: ApiServiceProtocolExecution | None = None,
    ) -> object | None:
        return None

    expected_plan = ApiServiceDispatchPlan(
        envelope=envelope,
        public_package_import_root="aware_home_api",
        service_protocol_import_root="aware_home_service_protocol",
        endpoint_ref=envelope.endpoint_ref,
        api_name=envelope.api_name,
        capability_name=envelope.capability_name,
        endpoint_name=envelope.endpoint_name,
        request_type_ref="aware_home_api.door.OpenDoor",
        response_type_ref="aware_home_api.door.OpenDoorResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        request_object=_ProofDispatchRequest(dry_run=False),
        invoke=_fake_invoke,
    )
    captured: dict[str, object] = {}
    dependency = SimpleNamespace(
        runtime_package_dir=Path("/tmp/aware-api-runtime-proof"),
        service_protocol_plan_hash_sha256="sha256:service-protocol-plan",
    )

    async def _fail_dispatch_api_invocation(**_: object) -> object:
        raise AssertionError(
            "endpoint-only committed ingress must not pre-materialize ApiCall"
        )

    def _fake_deferred_dispatch_plan(**kwargs: object) -> object:
        captured["deferred"] = kwargs
        return expected_plan

    monkeypatch.setattr(
        implementation_package,
        "_resolve_service_endpoint_dependency",
        lambda **_: dependency,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_dependency_api_invocation_manifest",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        implementation_package,
        "_build_api_invocation_ir_from_loaded_manifest",
        lambda **_: ir,
    )
    monkeypatch.setattr(
        implementation_package,
        "should_use_compact_api_receipt_payload",
        lambda **_: True,
    )
    monkeypatch.setattr(
        implementation_package,
        "dispatch_api_invocation",
        _fail_dispatch_api_invocation,
    )
    monkeypatch.setattr(
        implementation_package,
        "build_api_service_dispatch_plan_from_invocation_ir",
        _fake_deferred_dispatch_plan,
    )

    api_source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api",
    )
    api_call_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )
    call_key = uuid4()
    from aware_service_runtime.api_ingress.telemetry import (
        collect_service_api_trace_timings,
    )

    with collect_service_api_trace_timings() as timings:
        result = await implementation_package.build_activated_service_api_dispatch_plan_from_ingress(
            activated=cast(
                Any,
                SimpleNamespace(
                    prepared=object(),
                    api_reference_branch_ids_by_api_name={},
                ),
            ),
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            actor_id=uuid4(),
            api_source_lane=api_source_lane,
            api_call_lane=api_call_lane,
            service_name="aware_home",
            endpoint_ref="home_devices.open_door.open_door",
            discriminant="home_devices.open_door.open_door",
            request_payload={"dry_run": False},
            call_key=call_key,
        )

    assert result is not expected_plan
    assert result.envelope.call_key == call_key
    assert result.request_object == expected_plan.request_object
    assert (
        "service_host.api_ingress.dispatch_plan.build_deferred_invocation_plan_s"
        in timings
    )
    assert (
        "service_host.api_ingress.dispatch_plan.dispatch_api_invocation_s"
        not in timings
    )
    deferred_kwargs = cast(dict[str, object], captured["deferred"])
    assert deferred_kwargs["ir"] is ir
    assert isinstance(deferred_kwargs["branch_id"], UUID)
    assert deferred_kwargs["branch_id"] != api_source_lane.branch_id
    assert deferred_kwargs["branch_id"] != api_call_lane.branch_id
    assert deferred_kwargs["projection_hash"] == api_call_lane.projection_hash


@pytest.mark.asyncio
async def test_build_activated_service_api_dispatch_plan_uses_committed_api_reference_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    implementation_package = import_module(
        "aware_service_runtime.implementation_package"
    )
    ir = resolve_api_invocation_ir(
        api_ownership=_api_ownership_for_runtime(
            request_class_ref="aware_home_api.door.OpenDoor"
        ),
        endpoint_ref="home_devices.open_door.open_door",
        request_payload={"dry_run": False},
    )
    envelope = ResolvedApiInvocationEnvelope(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=uuid4(),
        request_hash="sha256:service-dispatcher-api-reference-proof",
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
        api_name=ir.api_name,
        capability_name=ir.capability_name,
        endpoint_name=ir.endpoint_name,
        endpoint_ref=ir.endpoint_ref,
        discriminant=ir.discriminant,
        source_path=ir.source_path,
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        request_class_ref=ir.request_class_ref,
        request_source_path=ir.request_source_path,
        response_class_ref=ir.response_class_ref,
        response_source_path=ir.response_source_path,
        stream=ir.stream,
        fulfillment_bindings=ir.fulfillment_bindings,
        description=ir.description,
    )
    captured: dict[str, object] = {}
    dependency = SimpleNamespace(
        runtime_package_dir=Path("/tmp/aware-api-runtime-proof"),
        service_protocol_plan_hash_sha256="sha256:service-protocol-plan",
    )

    async def _fake_dispatch_api_invocation(**kwargs: object) -> object:
        captured["dispatch"] = kwargs
        return SimpleNamespace(
            envelope=envelope,
            materialized_call=SimpleNamespace(
                api_call=object(),
                request_class_config=object(),
            ),
        )

    async def _fake_build_api_service_dispatch_plan(**kwargs: object) -> object:
        _ = kwargs
        return SimpleNamespace(
            request_type_ref="aware_home_api.door.OpenDoor",
            request_object=_ProofDispatchRequest(dry_run=False),
        )

    monkeypatch.setattr(
        implementation_package,
        "_resolve_service_endpoint_dependency",
        lambda **_: dependency,
    )
    monkeypatch.setattr(
        implementation_package,
        "_load_dependency_api_invocation_manifest",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        implementation_package,
        "_build_api_invocation_ir_from_loaded_manifest",
        lambda **_: ir,
    )
    monkeypatch.setattr(
        implementation_package,
        "dispatch_api_invocation",
        _fake_dispatch_api_invocation,
    )
    monkeypatch.setattr(
        implementation_package,
        "build_api_service_dispatch_plan_from_materialized_call",
        _fake_build_api_service_dispatch_plan,
    )

    default_api_branch_id = uuid4()
    committed_api_reference_branch_id = uuid4()
    api_source_lane = MaterializationLaneContext(
        branch_id=default_api_branch_id,
        projection_hash="sha256:api",
    )
    api_call_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )

    _ = await implementation_package.build_activated_service_api_dispatch_plan_from_ingress(
        activated=cast(
            Any,
            SimpleNamespace(
                prepared=object(),
                api_reference_branch_ids_by_api_name={
                    "home_devices": committed_api_reference_branch_id,
                },
            ),
        ),
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        api_source_lane=api_source_lane,
        api_call_lane=api_call_lane,
        service_name="aware_home",
        endpoint_ref="home_devices.open_door.open_door",
        discriminant="home_devices.open_door.open_door",
        request_payload={"dry_run": False},
    )

    dispatch_kwargs = cast(dict[str, object], captured["dispatch"])
    resolved_source_lane = cast(
        MaterializationLaneContext, dispatch_kwargs["source_lane"]
    )
    assert resolved_source_lane.branch_id == committed_api_reference_branch_id
    assert resolved_source_lane.projection_hash == api_source_lane.projection_hash
    resolved_target_lane = cast(
        MaterializationLaneContext, dispatch_kwargs["target_lane"]
    )
    assert resolved_target_lane.branch_id == committed_api_reference_branch_id
    assert resolved_target_lane.projection_hash == api_call_lane.projection_hash


@pytest.mark.asyncio
async def test_materialize_service_subscriptions_resolves_branch_projection_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware_root"))
    service_id = uuid4()
    api_id = uuid4()
    api_graph_projection_id = uuid4()
    service_branch_id = uuid4()
    object_projection_graph_id = uuid4()

    fake_compile_plan = ServiceCompilePlan(
        schema_version=1,
        package_name="attention-service",
        fqn_prefix="aware_attention_service",
        source_files=(),
        service_ownership=(),
        service_configs=(
            ServiceConfigPlan(
                name="aware_attention",
                source_path="bindings/attention.services.aware",
                apis=(
                    ServiceConfigApiPlan(
                        api_ref="attention",
                        source_path="bindings/attention.services.aware",
                        api_projections=(
                            ServiceConfigApiProjectionPlan(
                                projection_ref="aware_attention.FocusScope",
                                source_path="bindings/attention.services.aware",
                            ),
                        ),
                    ),
                ),
                experiences=(),
                service_operation_configs=(),
            ),
        ),
    )
    prepared = SimpleNamespace(
        compile_result=SimpleNamespace(compile_plan=fake_compile_plan),
    )
    fake_runtime_index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=[
                SimpleNamespace(name="Api", projection_hash="sha256:api"),
            ]
        ),
        opg_by_id={
            object_projection_graph_id: SimpleNamespace(
                id=object_projection_graph_id,
                projection_hash="sha256:focus_scope",
            )
        },
    )

    async def _fake_hydrate_api_contexts(**_: object):  # type: ignore[no-untyped-def]
        return SimpleNamespace(
            apis_by_name={
                "attention": SimpleNamespace(id=api_id),
            },
            graph_projections_by_key={
                (uuid4(), "focus_scope"): SimpleNamespace(
                    id=api_graph_projection_id,
                    object_projection_graph_id=object_projection_graph_id,
                ),
            },
        )

    async def _fake_materialize_service_branch(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["service_id"] == service_id
        return SimpleNamespace(
            binding=SimpleNamespace(service_branch_id=service_branch_id),
        )

    monkeypatch.setattr(
        "aware_service_runtime.implementation_package._hydrate_committed_api_reference_contexts",
        _fake_hydrate_api_contexts,
    )
    monkeypatch.setattr(
        "aware_service_runtime.implementation_package._resolve_committed_api_graph_projection_id",
        lambda **_: api_graph_projection_id,
    )
    monkeypatch.setattr(
        "aware_service_runtime.implementation_package.materialize_service_branch",
        _fake_materialize_service_branch,
    )

    subscriptions = await _materialize_service_subscriptions(
        prepared=cast(Any, prepared),
        runtime=cast(Any, object()),
        index=cast(Any, fake_runtime_index),
        actor_id=None,
        service_config_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="sha256:service_config",
        ),
        service_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="sha256:service",
        ),
        service_ids_by_name={"aware_attention": service_id},
        service_config_lanes_by_name=None,
        service_lanes_by_name=None,
        api_reference_branch_ids_by_api_name=None,
    )

    resolved = subscriptions["aware_attention"]
    assert len(resolved) == 1
    assert resolved[0].service_branch_id == service_branch_id
    assert resolved[0].api_graph_projection_id == api_graph_projection_id
    assert resolved[0].projection_hash == "sha256:focus_scope"


async def _invoke_home_story_open_door(
    handler: object,
    request: BaseModel,
    execution: ApiServiceProtocolExecution | None = None,
) -> object | None:
    typed_handler = cast(_HomeStoryServiceBindingProtocol, handler)
    assert execution is not None
    typed_execution = cast(_OpenDoorExecutionBindingProtocol, execution)
    return await typed_handler.home_devices.open_door.open_door(
        request, typed_execution
    )


async def _invoke_home_story_open_door_with_execution(
    handler: object,
    request: BaseModel,
    execution: ApiServiceProtocolExecution | None = None,
) -> object | None:
    typed_handler = cast(_HomeStoryServiceBindingProtocol, handler)
    assert execution is not None
    typed_execution = cast(_OpenDoorExecutionBindingProtocol, execution)
    return await typed_handler.home_devices.open_door.open_door(
        request, typed_execution
    )


def _build_open_door_execution(
    backend: ServiceApiExecutionBackend,
) -> _OpenDoorExecutionBindingProtocol:
    class _Execution:
        def __init__(self, execution_backend: ServiceApiExecutionBackend) -> None:
            self._execution_backend = execution_backend

        async def open(self, request: BaseModel) -> object | None:
            return await self._execution_backend.invoke_fulfillment(
                fulfillment_name="open_door",
                request=request,
            )

    return _Execution(backend)


def _sample_value_for_primitive(base_type: CodePrimitiveBaseType) -> object | None:
    if base_type == CodePrimitiveBaseType.string:
        return "front-door"
    if base_type == CodePrimitiveBaseType.boolean:
        return True
    if base_type == CodePrimitiveBaseType.integer:
        return 7
    if base_type == CodePrimitiveBaseType.float:
        return 1.5
    if base_type == CodePrimitiveBaseType.uuid:
        return uuid4()
    return None


def _aware_type_for_primitive(base_type: CodePrimitiveBaseType) -> str:
    if base_type == CodePrimitiveBaseType.string:
        return "String"
    if base_type == CodePrimitiveBaseType.boolean:
        return "Bool"
    if base_type == CodePrimitiveBaseType.integer:
        return "Int"
    if base_type == CodePrimitiveBaseType.float:
        return "Float"
    if base_type == CodePrimitiveBaseType.uuid:
        return "UUID"
    raise AssertionError(
        f"Unsupported primitive base type for Service package proof: {base_type!r}"
    )


def _select_runtime_inline_request_contract(
    runtime_index,
) -> tuple[ClassConfig, str, CodePrimitiveBaseType, object]:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        if class_config.value_mode != ClassValueMode.inline_value:
            continue
        attribute_links = [
            link
            for link in sorted(
                class_config.class_config_attribute_configs,
                key=lambda item: item.position,
            )
            if link.attribute_config is not None
            and not link.attribute_config.is_virtual
        ]
        if len(attribute_links) != 1:
            continue
        attribute_config = attribute_links[0].attribute_config
        if attribute_config is None or not attribute_config.name:
            continue
        type_info = resolve_type_info(attribute_config)
        if (
            type_info.kind.value != "primitive"
            or type_info.is_collection
            or type_info.primitive_config is None
        ):
            continue
        primitive_type = CodePrimitiveType.model_validate(
            type_info.primitive_config.primitive_type
        )
        sample_value = _sample_value_for_primitive(primitive_type.base_type)
        if sample_value is None:
            continue
        return (
            class_config,
            attribute_config.name,
            primitive_type.base_type,
            sample_value,
        )

    raise AssertionError(
        "Expected one compiled inline_value ClassConfig with one supported primitive attribute"
    )


def _write_runtime_api_workspace(
    *,
    root: Path,
    request_attribute_name: str,
    request_attribute_type: str,
) -> tuple[Path, ObjectConfigGraph]:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "proof-home-api"',
                'fqn_prefix = "aware_proof_home_api"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-home-api-types"',
                "",
                "[[semantic_package_exports]]",
                'kind = "api_dto"',
                'package_name = "proof-home-api-types"',
                'manifest_path = "apis/types/proof/aware.toml"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    package_root = root / "apis" / "types" / "proof"
    (package_root / "aware" / "door").mkdir(parents=True, exist_ok=True)
    ontology_root = root / "modules" / "home" / "structure" / "ontology"
    (ontology_root / "aware" / "home").mkdir(parents=True, exist_ok=True)
    _ = (ontology_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_home"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "home.aware").write_text(
        "\n".join(
            [
                "class Home {",
                "    name String key",
                "    doors Door[]",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home" / "door.aware").write_text(
        "\n".join(
            [
                "class Door {",
                "    label String",
                "",
                "    fn open(",
                "        dry_run Bool = false",
                "    ) -> Bool {",
                '        """Open this door."""',
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (ontology_root / "aware" / "home_projection.aware").write_text(
        "\n".join(
            [
                "projection Home {",
                "    root home.Home",
                "    home.Home::doors",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "proof-home-api-types"',
                'fqn_prefix = "aware_proof_home_types"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_proof_home_types"',
                "",
                "[[dependencies]]",
                'package_name = "home-ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "aware" / "door" / "endpoints.aware").write_text(
        "\n".join(
            [
                "class OpenDoor {",
                f"    {request_attribute_name} {request_attribute_type}",
                "}",
                "",
                "class OpenDoorResult {",
                "    accepted Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "aware" / "bindings.aware").write_text(
        "\n".join(
            [
                "binding aware_proof_home_types aware_home {",
                "    map door_open_by_label door.OpenDoor home.Door.label {",
                "        template {",
                f'            "{{{request_attribute_name}}}"',
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    bindings = root / "apis" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "proof.apis.aware").write_text(
        "\n".join(
            [
                "api home_devices {",
                "    capability open_door {",
                "        endpoint open_door aware_proof_home_types.door.OpenDoor {",
                "            response aware_proof_home_types.door.OpenDoorResult;",
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home;",
                "        capability open_door {",
                "            function open aware_home.home.Door.open;",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    dependency_graph = _write_dependency_runtime_ocg_snapshot(
        workspace_root=root,
        ontology_toml_path=ontology_root / "aware.toml",
    )
    return toml_path, dependency_graph


def _api_ownership_for_runtime(
    *,
    request_class_ref: str,
    include_function: bool = True,
) -> tuple[APIOwnership, ...]:
    functions = (
        (
            APICapabilityEndpointFunctionOwnership(
                name="open",
                graph_target="aware_home",
                graph_capability_function_name="open",
                source_path="service-package-proof",
            ),
        )
        if include_function
        else ()
    )
    return (
        APIOwnership(
            name="home_devices",
            source_path="service-package-proof",
            capabilities=(
                APICapabilityOwnership(
                    name="open_door",
                    source_path="service-package-proof",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="open_door",
                            source_path="service-package-proof",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref=request_class_ref,
                                source_path="service-package-proof",
                            ),
                            functions=functions,
                            description="Open the proof home door.",
                        ),
                    ),
                    description="Door operations",
                ),
            ),
            graphs=(),
        ),
    )


def _write_service_workspace(
    *,
    root: Path,
) -> Path:
    toml_path = root / "aware.service.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "proof-home-service"',
                'fqn_prefix = "aware_proof_home_service"',
                "",
                "[build]",
                'sources_dir = "services/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "service_ontology"',
                "",
                "[host]",
                'service_surface = "service"',
                'activation_mode = "materialize_and_load_committed"',
                "materialize_on_start = true",
                "",
                "[implementation]",
                "",
                "[[implementation.packages]]",
                'package_name = "proof-home-service"',
                'language = "python"',
                'import_root = "aware_proof_home_service"',
                'package_root = "."',
                'manifest_path = "pyproject.toml"',
                'entrypoint = "aware_proof_home_service.service_bindings:build_service_bindings"',
                'role = "service_bindings"',
                'include_paths = ["aware_proof_home_service/**/*.py"]',
                'exclude_paths = ["aware_proof_home_service/**/__pycache__/**"]',
                "",
                "[[dependencies]]",
                'package_name = "proof-home-api"',
                'kind = "api_service_protocol"',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    bindings = root / "services" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    _ = (bindings / "home_story.services.aware").write_text(
        "\n".join(
            [
                "service home_story {",
                "    api home_devices {",
                "        projection Api;",
                "    }",
                "",
                "    operation open_door {",
                "        endpoint home_devices.open_door.open_door;",
                "        admission identity_required;",
                "        receipt committed;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    package_root = root / "aware_proof_home_service"
    package_root.mkdir(parents=True, exist_ok=True)
    _ = (root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "proof-home-service"',
                'version = "0.0.0"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    _ = (package_root / "__init__.py").write_text(
        '"""Proof Service package."""\n', encoding="utf-8"
    )
    _ = (package_root / "service_bindings.py").write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "from dataclasses import dataclass, field",
                "",
                "from aware_proof_home_protocol.protocols import HomeDevicesOpenDoorOpenDoorOpenRequest",
                "",
                "",
                "@dataclass(slots=True)",
                "class _OpenDoorEndpoint:",
                "    requests: list[object] = field(default_factory=list)",
                "",
                "    async def open_door(self, request: object, execution: object) -> None:",
                "        self.requests.append(request)",
                "        await execution.open(HomeDevicesOpenDoorOpenDoorOpenRequest())",
                "        return None",
                "",
                "",
                "@dataclass(slots=True)",
                "class _HomeDevicesApi:",
                "    open_door: _OpenDoorEndpoint = field(default_factory=_OpenDoorEndpoint)",
                "",
                "",
                "@dataclass(slots=True)",
                "class HomeStoryBinding:",
                "    home_devices: _HomeDevicesApi = field(default_factory=_HomeDevicesApi)",
                "",
                "",
                "def build_service_bindings() -> dict[str, object]:",
                '    return {"home_story": HomeStoryBinding()}',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _select_runtime_public_function_target(runtime_index) -> tuple[str, UUID]:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        class_fqn = (class_config.class_fqn or "").strip()
        if not class_fqn:
            continue
        for function_link in sorted(
            class_config.class_config_function_configs,
            key=lambda item: (item.position, str(item.id)),
        ):
            function_config = function_link.function_config
            function_link_id = function_link.id
            function_name = (
                (function_config.name or "").strip()
                if function_config is not None
                else ""
            )
            if (
                function_link_id is not None
                and function_config is not None
                and function_link.is_public
                and function_name
            ):
                return f"{class_fqn}.{function_name}", function_link_id
    raise AssertionError(
        "Expected one public runtime ClassConfigFunctionConfig for Service package proof"
    )


def _runtime_api_compile_plan_payload(
    *,
    runtime_index,
    request_class_config: ClassConfig,
    graph_function_target: str,
) -> dict[str, object]:
    graph_target = (runtime_index.ocg.fqn_prefix or "").strip() or (
        runtime_index.ocg.name or ""
    ).strip()
    if not graph_target:
        raise AssertionError("Expected runtime ObjectConfigGraph to expose a target")
    request_class_config_id = request_class_config.id
    if request_class_config_id is None:
        raise AssertionError("Expected request ClassConfig to expose a stable id")
    request_class_ref = (request_class_config.class_fqn or "").strip()
    if not request_class_ref:
        raise AssertionError("Expected request ClassConfig to expose a class_fqn")
    source_path = "service-package-proof"
    return {
        "schema_version": 1,
        "package_name": "proof-home-api",
        "fqn_prefix": "aware_proof_home_api",
        "source_files": [source_path],
        "api_ontology": [
            {
                "api": {
                    "name": "home_devices",
                    "description": None,
                    "source_path": source_path,
                },
                "capabilities": [
                    {
                        "api_name": "home_devices",
                        "name": "open_door",
                        "description": "Door operations",
                        "source_path": source_path,
                    },
                ],
                "capability_endpoints": [
                    {
                        "api_name": "home_devices",
                        "capability_name": "open_door",
                        "name": "open_door",
                        "description": "Open the proof home door.",
                        "source_path": source_path,
                    },
                ],
                "capability_endpoint_request_configs": [
                    {
                        "api_name": "home_devices",
                        "capability_name": "open_door",
                        "endpoint_name": "open_door",
                        "class_ref": request_class_ref,
                        "class_config_id": str(request_class_config_id),
                        "description": None,
                        "source_path": source_path,
                    },
                ],
                "capability_endpoint_response_configs": [],
                "capability_endpoint_stream_configs": [],
                "capability_endpoint_stream_event_configs": [],
                "capability_endpoint_functions": [
                    {
                        "api_name": "home_devices",
                        "capability_name": "open_door",
                        "endpoint_name": "open_door",
                        "name": "open",
                        "graph_target": graph_target,
                        "graph_capability_function_name": "open",
                        "source_path": source_path,
                    },
                ],
                "graphs": [
                    {
                        "api_name": "home_devices",
                        "target": graph_target,
                        "description": None,
                        "source_path": source_path,
                    },
                ],
                "graph_functions": [
                    {
                        "api_name": "home_devices",
                        "graph_target": graph_target,
                        "target": graph_function_target,
                        "source_path": source_path,
                    },
                ],
                "graph_projections": [
                    {
                        "api_name": "home_devices",
                        "graph_target": graph_target,
                        "target": "Api",
                        "description": None,
                        "source_path": source_path,
                    },
                ],
                "graph_capabilities": [
                    {
                        "api_name": "home_devices",
                        "graph_target": graph_target,
                        "capability_name": "open_door",
                        "description": None,
                        "source_path": source_path,
                    },
                ],
                "graph_capability_functions": [
                    {
                        "api_name": "home_devices",
                        "graph_target": graph_target,
                        "capability_name": "open_door",
                        "name": "open",
                        "target": graph_function_target,
                        "source_path": source_path,
                    },
                ],
            },
        ],
    }


async def _hydrate_committed_session(
    *,
    index,
    branch_id: UUID,
    projection_hash: str,
) -> Session:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert target_head is not None
    opg = index.opg_by_hash[projection_hash]
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=target_oig,
        branch_id=branch_id,
    )


@pytest.mark.asyncio
async def test_prepare_service_package_binding_invokes_home_story_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "proof_home_story_binding_workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    api_toml_path, dependency_graph = _write_runtime_api_workspace(
        root=workspace_root,
        request_attribute_name="segment_id",
        request_attribute_type="UUID",
    )

    monkeypatch.setenv(
        "AWARE_META_SERVICE_EVENT_STORE_ROOT",
        str(tmp_path / "meta-events-home-story"),
    )
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware-root-home-story"))
    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_home_story_binding"
    ) as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        runtime_index = _runtime_index(runtime)
        api_accessible_graphs = (
            await resolve_source_owned_api_dto_export_accessible_graphs(
                runtime=runtime,
                index=runtime_index,
                actor_id=uuid4(),
                branch_id=uuid4(),
                workspace_root=workspace_root,
                api_toml_path=api_toml_path,
                accessible_graphs=(dependency_graph,),
            )
        )
        compile_result = await asyncio.to_thread(
            compile_api_workspace,
            toml_path=api_toml_path,
            repo_root=workspace_root,
            materialize_service_protocol=True,
            dependency_graph_mode="meta_runtime",
            accessible_graphs=api_accessible_graphs,
        )
    public_package_materialization = compile_result.public_package_materialization
    assert public_package_materialization is not None
    monkeypatch.syspath_prepend(
        str(public_package_materialization.render_job.target.package_root)
    )
    for dto_result in compile_result.api_dto_package_materializations:
        monkeypatch.syspath_prepend(str(dto_result.package_root))
    service_toml_path = _write_service_workspace(
        root=workspace_root,
    )

    prepared = prepare_service_package_binding(
        toml_path=service_toml_path,
        repo_root=workspace_root,
        dependency_payloads=(
            _protocol_dependency_payload(
                digest=public_package_materialization.runtime_artifacts.service_protocol_plan.hash_sha256
            ),
        ),
    )

    assert tuple(sorted(prepared.service_bindings)) == ("home_story",)
    assert prepared.service_endpoint_refs["home_story"] == (
        "home_devices.open_door.open_door",
    )
    assert tuple(item.package_name for item in prepared.dependencies) == (
        "proof-home-api",
    )

    handler = cast(
        _HomeStoryServiceBindingProtocol,
        prepared.service_bindings["home_story"],
    )

    class _DoorRequest(BaseModel):
        segment_id: UUID

    class _DummyExecution:
        async def open(self, request: BaseModel) -> object:
            _ = request
            return type("_Response", (), {"value": object()})()

    segment_id = uuid4()
    response = await handler.home_devices.open_door.open_door(
        _DoorRequest.model_validate({"segment_id": segment_id}),
        _DummyExecution(),
    )
    assert response is None
    requests = handler.home_devices.open_door.requests
    assert len(requests) == 1
    first_request_payload = cast(BaseModel, requests[0]).model_dump()
    assert first_request_payload["segment_id"] == segment_id


@pytest.mark.asyncio
async def test_activate_service_package_binding_materializes_and_executes_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_service_implementation_package",
    ) as aware_root:
        runtime = _build_service_meta_runtime(
            repo_root,
            workspace_root=aware_root,
        )
        runtime_index = _runtime_index(runtime)
        (
            request_class_config,
            request_attribute_name,
            primitive_base_type,
            request_attribute_value,
        ) = _select_runtime_inline_request_contract(runtime_index)

        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )
        service_config_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ServiceConfig",
        )
        service_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="Service",
        )

        workspace_root = tmp_path / "proof_home_story_workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        api_toml_path, dependency_graph = _write_runtime_api_workspace(
            root=workspace_root,
            request_attribute_name=request_attribute_name,
            request_attribute_type=_aware_type_for_primitive(primitive_base_type),
        )
        api_accessible_graphs = (
            await resolve_source_owned_api_dto_export_accessible_graphs(
                runtime=runtime,
                index=runtime_index,
                actor_id=uuid4(),
                branch_id=uuid4(),
                workspace_root=workspace_root,
                api_toml_path=api_toml_path,
                accessible_graphs=(dependency_graph,),
            )
        )
        api_compile_result = await asyncio.to_thread(
            compile_api_workspace,
            toml_path=api_toml_path,
            repo_root=workspace_root,
            materialize_service_protocol=True,
            accessible_graphs=api_accessible_graphs,
        )
        public_package_materialization = (
            api_compile_result.public_package_materialization
        )
        service_protocol_materialization = (
            api_compile_result.service_protocol_materialization
        )
        assert public_package_materialization is not None
        assert service_protocol_materialization is not None
        monkeypatch.syspath_prepend(
            str(public_package_materialization.render_job.target.package_root)
        )
        for dto_result in api_compile_result.api_dto_package_materializations:
            monkeypatch.syspath_prepend(str(dto_result.package_root))
        service_toml_path = _write_service_workspace(
            root=workspace_root,
        )

        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()
        lane = _MetaLaneIds(
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=stable_branch_id(
                environment_id=environment_id,
                thread_id=thread_id,
            ),
            actor_id=uuid4(),
        )

        active_branch_id = lane.branch_id
        (
            graph_function_target,
            class_config_function_config_id,
        ) = _select_runtime_public_function_target(runtime_index)
        api_receipt = await materialize_api_compile_plan_ontology(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            lane=MaterializationLaneContext(
                branch_id=active_branch_id,
                projection_hash=api_projection_hash,
            ),
            compile_plan_payloads=(
                _runtime_api_compile_plan_payload(
                    runtime_index=runtime_index,
                    request_class_config=request_class_config,
                    graph_function_target=graph_function_target,
                ),
            ),
        )
        assert api_receipt is not None
        api_id = stable_api_id(name="home_devices")
        capability_id = stable_api_capability_id(
            api_id=api_id,
            name="open_door",
        )
        api_capability_endpoint_id = stable_api_capability_endpoint_id(
            api_capability_id=capability_id,
            name="open_door",
        )
        object_config_graph_id = runtime_index.ocg.id
        assert object_config_graph_id is not None
        api_graph_id = stable_api_graph_id(
            api_id=api_id,
            object_config_graph_id=object_config_graph_id,
        )
        api_graph_capability_id = stable_api_graph_capability_id(
            api_graph_id=api_graph_id,
            api_capability_id=capability_id,
        )
        api_graph_function_id = stable_api_graph_function_id(
            api_graph_id=api_graph_id,
            class_config_function_config_id=class_config_function_config_id,
        )
        api_graph_capability_function_id = stable_api_graph_capability_function_id(
            api_graph_capability_id=api_graph_capability_id,
            api_graph_function_id=api_graph_function_id,
            name="open",
        )
        api_capability_endpoint_function_id = (
            stable_api_capability_endpoint_function_id(
                api_capability_endpoint_id=api_capability_endpoint_id,
                api_graph_capability_function_id=api_graph_capability_function_id,
                name="open",
            )
        )

        activated = await activate_service_package_binding(
            toml_path=service_toml_path,
            repo_root=workspace_root,
            dependency_payloads=(
                _protocol_dependency_payload(
                    digest=public_package_materialization.runtime_artifacts.service_protocol_plan.hash_sha256
                ),
            ),
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            service_config_lane=MaterializationLaneContext(
                branch_id=active_branch_id,
                projection_hash=service_config_projection_hash,
            ),
            service_lane=MaterializationLaneContext(
                branch_id=active_branch_id,
                projection_hash=service_projection_hash,
            ),
            api_reference_branch_ids_by_api_name={
                "home_devices": active_branch_id,
            },
        )

        expected_service_config_id = stable_service_config_id(name="home_story")
        expected_service_id = stable_service_id(
            service_config_id=expected_service_config_id,
            name="home_story",
        )
        assert activated.service_ids_by_name["home_story"] == expected_service_id
        expected_service_config_api_id = stable_service_config_api_id(
            service_config_id=expected_service_config_id,
            api_id=api_id,
        )
        service_config_activation_lane = activated.service_config_lanes_by_name[
            "home_story"
        ]
        service_activation_lane = activated.service_lanes_by_name["home_story"]
        subscriptions = activated.service_subscriptions_by_name["home_story"]
        assert len(subscriptions) == 1
        assert subscriptions[0].branch_id == service_activation_lane.branch_id
        assert subscriptions[0].projection_hash in runtime_index.opg_by_hash
        assert subscriptions[0].service_branch_id is not None
        assert subscriptions[0].object_instance_graph_branch_id is not None

        expected_service_config_api_projection_id = (
            stable_service_config_api_projection_id(
                service_config_api_id=expected_service_config_api_id,
                api_graph_projection_id=subscriptions[0].api_graph_projection_id,
            )
        )
        assert (
            subscriptions[0].service_config_api_projection_id
            == expected_service_config_api_projection_id
        )
        expected_operation_config_id = stable_service_operation_config_id(
            service_config_id=expected_service_config_id,
            name="open_door",
        )
        expected_api_endpoint_id = stable_service_operation_config_api_endpoint_id(
            service_operation_config_id=expected_operation_config_id,
            service_config_api_id=expected_service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
        )

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
            ),
            endpoint_ref="home_devices.open_door.open_door",
            request_payload={request_attribute_name: request_attribute_value},
        )
        materialized_api_call = await materialize_api_call(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            source_lane=MaterializationLaneContext(
                branch_id=active_branch_id,
                projection_hash=api_projection_hash,
            ),
            target_lane=MaterializationLaneContext(
                branch_id=active_branch_id,
                projection_hash=api_call_projection_hash,
            ),
            ir=ir,
        )
        envelope = build_resolved_api_invocation_envelope(
            ir=ir,
            materialized_call=materialized_api_call.binding,
        )
        dispatch_plan = await build_api_service_dispatch_plan(
            index=runtime_index,
            envelope=envelope,
            runtime_package_dir=service_protocol_materialization.runtime_package_dir,
        )
        session = await _hydrate_committed_session(
            index=runtime_index,
            branch_id=service_config_activation_lane.branch_id,
            projection_hash=service_config_activation_lane.projection_hash,
        )

        class _RecordingExecutionBackend(ServiceApiExecutionBackend):
            async def invoke_fulfillment(
                self,
                *,
                fulfillment_name: str,
                request: BaseModel,
            ) -> object | None:
                assert fulfillment_name == "open"
                assert request.model_dump() == {"dry_run": False}
                return {"value": True}

        request = build_service_operation_request_for_api_dispatch(
            context=ServiceOperationContext(
                actor_id=lane.actor_id,
                branch_id=service_activation_lane.branch_id,
                projection_hash=service_activation_lane.projection_hash,
            ),
            service_name="home_story",
            operation_key="turn-home-story-001",
            dispatch_plan=dispatch_plan,
        )
        assert request.api_dispatch is not None
        assert (
            request.api_dispatch.envelope.request_hash
            == dispatch_plan.envelope.request_hash
        )

        with pytest.raises(
            RuntimeError, match="requires explicit host-owned execution routing"
        ):
            _ = await execute_activated_service_api_dispatch_request(
                activated=activated,
                runtime=runtime,
                index=runtime_index,
                session=session,
                actor_id=lane.actor_id,
                target_lane=MaterializationLaneContext(
                    branch_id=service_activation_lane.branch_id,
                    projection_hash=service_activation_lane.projection_hash,
                ),
                service_name="home_story",
                dispatch_request=request.api_dispatch,
            )

        executed = await execute_activated_service_api_dispatch_request(
            activated=activated,
            runtime=runtime,
            index=runtime_index,
            session=session,
            actor_id=lane.actor_id,
            target_lane=MaterializationLaneContext(
                branch_id=service_activation_lane.branch_id,
                projection_hash=service_activation_lane.projection_hash,
            ),
            service_name="home_story",
            dispatch_request=request.api_dispatch,
            execution_backend=_RecordingExecutionBackend(),
        )
        assert (
            executed.resolved_dispatch.dispatch_plan.envelope.request_hash
            == dispatch_plan.envelope.request_hash
        )

        expected_api_endpoint_function_binding_id = (
            stable_service_operation_config_api_endpoint_function_id(
                service_operation_config_api_endpoint_id=expected_api_endpoint_id,
                api_capability_endpoint_function_id=api_capability_endpoint_function_id,
            )
        )
        expected_service_operation_id = stable_service_operation_id(
            service_id=expected_service_id,
            service_operation_config_id=expected_operation_config_id,
            operation_key="turn-home-story-001",
        )

        assert (
            executed.materialized_operation.binding.service_operation_id
            == expected_service_operation_id
        )
        assert (
            executed.materialized_operation.service_operation.status
            == ServiceOperationStatus.queued
        )
        assert (
            executed.materialized_operation.service_operation.api_endpoint is not None
        )
        assert (
            executed.materialized_operation.service_operation.api_endpoint.id
            == expected_api_endpoint_id
        )
        assert len(executed.validated_fulfillment.bindings) == 1
        assert (
            executed.validated_fulfillment.bindings[
                0
            ].service_operation_config_api_endpoint_function_id
            == expected_api_endpoint_function_binding_id
        )
        assert executed.response_object is None
        handler = cast(
            _HomeStoryServiceBindingProtocol,
            activated.prepared.service_bindings["home_story"],
        )
        requests = handler.home_devices.open_door.requests
        assert len(requests) == 1
