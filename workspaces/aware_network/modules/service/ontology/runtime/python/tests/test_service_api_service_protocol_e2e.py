from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, cast, get_args, get_origin
from uuid import UUID, uuid4

import msgpack
import pytest
from pydantic import BaseModel
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code.types import JsonObject
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_api_runtime.compile_materialization.service import (
    resolve_source_owned_api_dto_export_accessible_graphs,
)
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    MetaGraphRuntimeIndex,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.testing import IsolatedMetaAwareRoot, LaneIds
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_orm.session.session import Session
from aware_service_ontology.service.service_enums import ServiceOperationStatus
from aware_service_ontology.stable_ids import (
    stable_service_config_api_id,
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

from aware_api_runtime.compile import compile_api_workspace
from aware_api_runtime.dependencies.runtime_resolution import (
    _RuntimeDependencyPackage,
    _compute_runtime_dependency_source_digest,
)
from aware_api_runtime.invocation import (
    build_resolved_api_invocation_envelope,
    resolve_api_invocation_ir,
)
from aware_api_runtime.models import (
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.invocation.materialization import materialize_api_call
from aware_api_runtime.service_protocol import (
    build_api_service_dispatch_plan,
    load_api_service_protocol_package,
)
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_service_runtime.api_ingress.execution_context import (
    ServiceApiExecutionBackend,
)
from aware_service_runtime.api_ingress.execution import (
    execute_service_api_dispatch_plan,
)
from aware_service_runtime.implementation_package import (
    load_committed_service_lane_session,
)
from aware_service_runtime.ontology.materialization import (
    materialize_service,
    materialize_service_config,
    materialize_service_config_api,
    materialize_service_operation_config,
    materialize_service_operation_config_api_endpoint,
    materialize_service_operation_config_api_endpoint_function,
)

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


def _service_api_service_protocol_package_manifest_paths(
    repo_root: Path,
) -> tuple[Path, ...]:
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


def _build_service_api_service_protocol_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_api_service_protocol_package_manifest_paths(
            repo_root
        ),
        workspace_root=repo_root,
        aware_root=aware_root,
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


async def _compile_api_workspace_in_thread(
    *,
    toml_path: Path,
    repo_root: Path,
    materialize_service_protocol: bool = False,
    dependency_graph_mode: str = "meta_runtime",
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    kernel_repo_root: Path | None = None,
):
    return await asyncio.to_thread(
        compile_api_workspace,
        toml_path=toml_path,
        repo_root=repo_root,
        materialize_service_protocol=materialize_service_protocol,
        dependency_graph_mode=dependency_graph_mode,
        accessible_graphs=accessible_graphs,
        kernel_repo_root=kernel_repo_root,
    )


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
        f"Unsupported primitive base type for service-protocol proof: {base_type!r}"
    )


def _resolve_model_class(
    *,
    type_ref: str,
    service_protocol_import_root: str | None = None,
) -> type[BaseModel]:
    module_ref, _, class_name = type_ref.rpartition(".")
    if not module_ref or not class_name:
        raise AssertionError(f"Expected dotted type_ref, got {type_ref!r}")
    if module_ref == "protocols" and service_protocol_import_root is not None:
        module_ref = f"{service_protocol_import_root}.protocols"
    module = import_module(module_ref)
    model_cls = getattr(module, class_name, None)
    assert isinstance(model_cls, type)
    assert issubclass(model_cls, BaseModel)
    return cast(type[BaseModel], model_cls)


def _evict_import_root(import_root: str) -> None:
    for module_name in tuple(sys.modules):
        if module_name == import_root or module_name.startswith(f"{import_root}."):
            sys.modules.pop(module_name, None)


def _prepend_generated_package_root(
    syspath_prepend: Callable[[str], None],
    *,
    package_root: Path,
    import_root: str,
) -> None:
    _evict_import_root(import_root)
    syspath_prepend(str(package_root))


def _sample_value_for_annotation(annotation: object) -> object:
    origin = get_origin(annotation)
    if origin is not None:
        if origin is list:
            return []
        if origin is dict:
            return {}
        if origin is tuple:
            return ()
        union_args = [item for item in get_args(annotation) if item is not type(None)]
        if union_args:
            return _sample_value_for_annotation(union_args[0])
    if annotation is str:
        return "sample"
    if annotation is bool:
        return True
    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is UUID:
        return uuid4()
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.model_validate(_build_model_payload(annotation))
    return None


def _build_model_payload(model_cls: type[BaseModel]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field_name, field_info in model_cls.model_fields.items():
        if not field_info.is_required():
            continue
        payload[field_name] = _sample_value_for_annotation(field_info.annotation)
    return payload


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
    include_stream: bool = False,
) -> tuple[Path, ObjectConfigGraph]:
    toml_path = root / "aware.api.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "proof-api"',
                'fqn_prefix = "aware_proof_api"',
                "",
                "[build]",
                'sources_dir = "apis/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "api_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "proof-api-types"',
                "",
                "[[semantic_package_exports]]",
                'kind = "api_dto"',
                'package_name = "proof-api-types"',
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
                'package_name = "proof-api-types"',
                'fqn_prefix = "aware_proof_types"',
                'kind = "api"',
                "",
                "[build]",
                'environment_slug = "aware_proof_types"',
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
                "class OpenRequest {",
                f"    {request_attribute_name} {request_attribute_type}",
                "}",
                "",
                "class OpenResult {",
                "    accepted Bool",
                "}",
                "",
                "class OpenSnapshot {",
                "    accepted Bool",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    binding_name = f"open_request_by_{request_attribute_name}"
    _ = (package_root / "aware" / "bindings.aware").write_text(
        "\n".join(
            [
                "binding aware_proof_types aware_home {",
                f"    map {binding_name} door.OpenRequest home.Door.label {{",
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
                "api openai {",
                "    capability door {",
                "        endpoint open aware_proof_types.door.OpenRequest {",
                "            response aware_proof_types.door.OpenResult;",
                *(
                    [
                        "            stream server {",
                        "                event snapshot aware_proof_types.door.OpenSnapshot;",
                        "            }",
                    ]
                    if include_stream
                    else []
                ),
                "        }",
                "    }",
                "    graph aware_home {",
                "        projection aware_home.Home {",
                "        }",
                "        capability door {",
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


def _api_ownership_for_runtime(*, request_class_ref: str) -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name="openai",
            source_path="service-protocol-proof",
            capabilities=(
                APICapabilityOwnership(
                    name="door",
                    source_path="service-protocol-proof",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="open",
                            source_path="service-protocol-proof",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref=request_class_ref,
                                source_path="service-protocol-proof",
                            ),
                            functions=(
                                APICapabilityEndpointFunctionOwnership(
                                    name="open",
                                    graph_target="aware_home",
                                    graph_capability_function_name="open",
                                    source_path="service-protocol-proof",
                                ),
                            ),
                            description="Open the proof door.",
                        ),
                    ),
                    description="Door operations",
                ),
            ),
            graphs=(),
        ),
    )


def _select_runtime_function_config_id(runtime_index) -> UUID:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        for function_link in sorted(
            class_config.class_config_function_configs,
            key=lambda item: (item.position, str(item.id)),
        ):
            if function_link.function_config_id is not None:
                return function_link.function_config_id
    raise AssertionError(
        "Expected one runtime ClassConfigFunctionConfig for Service service-protocol E2E proof"
    )


@pytest.mark.asyncio
async def test_execute_service_api_dispatch_plan_runs_typed_service_protocol_handler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)

    import aware_service_ontology  # noqa: F401
    import aware_api_ontology  # noqa: F401

    service_config_name = "compiler"
    service_name = "workspace_compiler"
    operation_config_name = "compile_module"
    operation_key = "turn-typed-001"

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_api_service_protocol_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
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

        workspace_root = tmp_path / "service_protocol_workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        toml_path, dependency_graph = _write_runtime_api_workspace(
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
                api_toml_path=toml_path,
                accessible_graphs=(dependency_graph,),
            )
        )
        compile_result = await _compile_api_workspace_in_thread(
            toml_path=toml_path,
            repo_root=workspace_root,
            materialize_service_protocol=True,
            accessible_graphs=api_accessible_graphs,
        )
        service_protocol_materialization = (
            compile_result.service_protocol_materialization
        )
        assert service_protocol_materialization is not None
        runtime_package_dir = service_protocol_materialization.runtime_package_dir
        syspath_prepend(
            str(runtime_package_dir / "public_package" / "python" / "package")
        )
        for dto_result in compile_result.api_dto_package_materializations:
            _prepend_generated_package_root(
                syspath_prepend,
                package_root=dto_result.package_root,
                import_root=dto_result.import_root,
            )
        syspath_prepend(
            str(runtime_package_dir / "service_protocol" / "python" / "package")
        )
        loaded_package = load_api_service_protocol_package(
            runtime_package_dir=runtime_package_dir
        )
        open_result_module = import_module("aware_proof_types.door.endpoints")
        open_result_type = cast(
            type[BaseModel], getattr(open_result_module, "OpenResult")
        )
        protocols_module = import_module(
            f"{loaded_package.service_protocol_import_root}.protocols"
        )
        generated_endpoint_binding = cast(
            Any,
            getattr(protocols_module, "ENDPOINT_BINDINGS")["openai.door.open"],
        )
        generated_fulfillment_binding = cast(
            Any, generated_endpoint_binding.fulfillment_bindings[0]
        )
        execution_request_type = _resolve_model_class(
            type_ref=str(generated_fulfillment_binding.request_type_ref),
            service_protocol_import_root=loaded_package.service_protocol_import_root,
        )
        execution_response_type = _resolve_model_class(
            type_ref=str(generated_fulfillment_binding.response_type_ref),
            service_protocol_import_root=loaded_package.service_protocol_import_root,
        )

        recorded_requests: list[BaseModel] = []
        recorded_execution_requests: list[BaseModel] = []
        recorded_execution_responses: list[BaseModel] = []

        class _DoorHandler:
            async def open(self, request: BaseModel, execution: object) -> BaseModel:
                recorded_requests.append(request)
                execution_request = execution_request_type.model_validate(
                    _build_model_payload(execution_request_type)
                )
                recorded_execution_requests.append(execution_request)
                execution_response = await cast(Any, execution).open(execution_request)
                assert isinstance(execution_response, execution_response_type)
                recorded_execution_responses.append(cast(BaseModel, execution_response))
                return open_result_type.model_validate({"accepted": True})

        class _OpenAIApiHandler:
            def __init__(self) -> None:
                self.door = _DoorHandler()

        class _RootProductBHandler:
            def __init__(self) -> None:
                self.openai = _OpenAIApiHandler()

        lane = LaneIds(
            branch_id=uuid4(),
            actor_id=uuid4(),
        )
        assert lane.branch_id is not None
        assert lane.actor_id is not None
        active_branch_id = lane.branch_id
        endpoint_ref = "openai.door.open"
        api_snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=lane.actor_id,
            branch_id=active_branch_id,
            projection_hash=api_projection_hash,
            api_name="openai",
            endpoint_refs=(endpoint_ref,),
            endpoint_request_class_config_ids={
                endpoint_ref: request_class_config.id,
            },
            endpoint_fulfillment_names={endpoint_ref: ("open",)},
            api_graph_function_config_id=_select_runtime_function_config_id(
                runtime_index
            ),
        )
        assert api_snapshot.api.id is not None
        api_id = api_snapshot.api.id
        api_capability_endpoint_id = api_snapshot.endpoint_ids_by_ref[endpoint_ref]
        api_capability_endpoint_function_id = api_snapshot.endpoint_function_ids_by_ref[
            endpoint_ref
        ]["open"]

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
            ),
            endpoint_ref="openai.door.open",
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
            runtime_package_dir=runtime_package_dir,
        )

        expected_service_config_id = stable_service_config_id(name=service_config_name)
        expected_service_id = stable_service_id(
            service_config_id=expected_service_config_id,
            name=service_name,
        )
        expected_operation_config_id = stable_service_operation_config_id(
            service_config_id=expected_service_config_id,
            name=operation_config_name,
        )
        expected_service_config_api_id = stable_service_config_api_id(
            service_config_id=expected_service_config_id,
            api_id=api_id,
        )
        expected_api_endpoint_id = stable_service_operation_config_api_endpoint_id(
            service_operation_config_id=expected_operation_config_id,
            service_config_api_id=expected_service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
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
            operation_key=operation_key,
        )

        service_config_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
        )
        service_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_projection_hash,
        )

        materialized_service_config = await materialize_service_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            name=service_config_name,
            description="Compiler service catalog",
        )
        assert (
            materialized_service_config.binding.service_config_id
            == expected_service_config_id
        )

        materialized_service_api = await materialize_service_config_api(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            api_id=api_id,
            description="Shared API bridge",
        )
        assert (
            materialized_service_api.binding.service_config_api_id
            == expected_service_config_api_id
        )

        materialized_operation_config = await materialize_service_operation_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            name=operation_config_name,
            description="Compile one module",
            admission_mode="public_read",
        )
        assert (
            materialized_operation_config.binding.service_operation_config_id
            == expected_operation_config_id
        )

        materialized_api_endpoint = (
            await materialize_service_operation_config_api_endpoint(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_config_lane,
                service_operation_config_id=expected_operation_config_id,
                service_config_api_id=expected_service_config_api_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
                description="Public endpoint binding",
            )
        )
        assert (
            materialized_api_endpoint.binding.service_operation_config_api_endpoint_id
            == expected_api_endpoint_id
        )

        materialized_api_endpoint_function = (
            await materialize_service_operation_config_api_endpoint_function(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_config_lane,
                service_operation_config_api_endpoint_id=expected_api_endpoint_id,
                api_capability_endpoint_function_id=api_capability_endpoint_function_id,
                description="Allowed API fulfillment",
            )
        )
        assert (
            materialized_api_endpoint_function.binding.service_operation_config_api_endpoint_function_id
            == expected_api_endpoint_function_binding_id
        )

        materialized_service = await materialize_service(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_lane,
            service_config_id=expected_service_config_id,
            name=service_name,
            description="Primary compiler service instance",
        )
        assert materialized_service.binding.service_id == expected_service_id

        service_config_head = await FSCommitStore().head(
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
        )
        assert service_config_head is not None
        assert service_config_head.get("commit_id") is not None

        opg = runtime_index.opg_by_hash[service_config_projection_hash]
        service_config_oig, _ = await CachedLaneMaterializer().get(
            branch_id=active_branch_id,
            ocg=runtime_index.ocg,
            opg=opg,
            commit_id=UUID(str(service_config_head["commit_id"])),
            oig_id=(
                UUID(str(service_config_head["object_instance_graph_id"]))
                if service_config_head.get("object_instance_graph_id")
                else None
            ),
            attribute_configs_by_id=runtime_index.attribute_configs_by_id,
            class_configs_by_id=runtime_index.class_configs_by_id,
        )
        scratch = reify_oig_session(
            index=runtime_index,
            opg=opg,
            oig=service_config_oig,
            branch_id=active_branch_id,
        )

        handler = _RootProductBHandler()

        recorded_execution_fulfillment_names: list[str] = []

        class _RecordingExecutionBackend(ServiceApiExecutionBackend):
            async def invoke_fulfillment(
                self,
                *,
                fulfillment_name: str,
                request: BaseModel,
            ) -> object | None:
                recorded_execution_fulfillment_names.append(fulfillment_name)
                assert isinstance(request, execution_request_type)
                return execution_response_type.model_validate(
                    _build_model_payload(execution_response_type)
                )

        executed = await execute_service_api_dispatch_plan(
            runtime=runtime,
            index=runtime_index,
            session=scratch,
            actor_id=lane.actor_id,
            target_lane=MaterializationLaneContext(
                branch_id=active_branch_id,
                projection_hash=service_projection_hash,
            ),
            dispatch_plan=dispatch_plan,
            service_id=expected_service_id,
            operation_key=operation_key,
            handler=handler,
            execution_context=cast(JsonObject, {"source": "service-protocol-proof"}),
            execution_backend=_RecordingExecutionBackend(),
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
            executed.materialized_operation.service_operation.service_operation_config
            is not None
        )
        assert (
            executed.materialized_operation.service_operation.service_operation_config.id
            == expected_operation_config_id
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
            ].api_capability_endpoint_function_id
            == api_capability_endpoint_function_id
        )
        assert (
            executed.validated_fulfillment.bindings[
                0
            ].service_operation_config_api_endpoint_function_id
            == expected_api_endpoint_function_binding_id
        )
        assert (
            executed.fulfillment_execution_plan.service_operation_id
            == expected_service_operation_id
        )
        assert (
            executed.fulfillment_execution_plan.service_operation_config_api_endpoint_id
            == expected_api_endpoint_id
        )
        assert executed.fulfillment_execution_plan.endpoint_ref == "openai.door.open"
        assert len(executed.fulfillment_execution_plan.bindings) == 1
        assert (
            executed.fulfillment_execution_plan.bindings[
                0
            ].service_operation_config_api_endpoint_function_id
            == expected_api_endpoint_function_binding_id
        )
        assert (
            executed.fulfillment_execution_plan.bindings[
                0
            ].api_capability_endpoint_function_id
            == api_capability_endpoint_function_id
        )
        assert (
            executed.fulfillment_execution_plan.bindings[0].graph_target == "aware_home"
        )
        assert (
            executed.fulfillment_execution_plan.bindings[
                0
            ].graph_capability_function_name
            == "open"
        )
        assert executed.execution_object is not None
        assert isinstance(executed.response_object, open_result_type)
        response_object = cast(BaseModel, executed.response_object)
        assert response_object.model_dump()["accepted"] is True

        assert len(recorded_requests) == 1
        request_object = recorded_requests[0]
        assert request_object is dispatch_plan.request_object
        typed_request_object = cast(BaseModel, request_object)
        assert (
            typed_request_object.model_dump()[request_attribute_name]
            == request_attribute_value
        )
        assert len(recorded_execution_requests) == 1
        assert len(recorded_execution_responses) == 1
        assert recorded_execution_fulfillment_names == ["open"]


@pytest.mark.asyncio
async def test_execute_service_api_dispatch_plan_streams_typed_api_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)

    import aware_service_ontology  # noqa: F401
    import aware_api_ontology  # noqa: F401

    service_config_name = "compiler"
    service_name = "workspace_compiler"
    operation_config_name = "compile_module"
    operation_key = "turn-stream-001"

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_stream", persistence_backend="fs"
    ):
        runtime = _build_service_api_service_protocol_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root_stream",
        )
        runtime_index = _runtime_index(runtime)
        (
            request_class_config,
            request_attribute_name,
            primitive_base_type,
            request_attribute_value,
        ) = _select_runtime_inline_request_contract(runtime_index)

        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        service_config_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ServiceConfig",
        )
        service_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="Service",
        )

        workspace_root = tmp_path / "service_protocol_stream_workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        toml_path, dependency_graph = _write_runtime_api_workspace(
            root=workspace_root,
            request_attribute_name=request_attribute_name,
            request_attribute_type=_aware_type_for_primitive(primitive_base_type),
            include_stream=True,
        )
        api_accessible_graphs = (
            await resolve_source_owned_api_dto_export_accessible_graphs(
                runtime=runtime,
                index=runtime_index,
                actor_id=uuid4(),
                branch_id=uuid4(),
                workspace_root=workspace_root,
                api_toml_path=toml_path,
                accessible_graphs=(dependency_graph,),
            )
        )
        compile_result = await _compile_api_workspace_in_thread(
            toml_path=toml_path,
            repo_root=workspace_root,
            materialize_service_protocol=True,
            accessible_graphs=api_accessible_graphs,
        )
        service_protocol_materialization = (
            compile_result.service_protocol_materialization
        )
        assert service_protocol_materialization is not None
        runtime_package_dir = service_protocol_materialization.runtime_package_dir
        syspath_prepend(
            str(runtime_package_dir / "public_package" / "python" / "package")
        )
        for dto_result in compile_result.api_dto_package_materializations:
            _prepend_generated_package_root(
                syspath_prepend,
                package_root=dto_result.package_root,
                import_root=dto_result.import_root,
            )
        syspath_prepend(
            str(runtime_package_dir / "service_protocol" / "python" / "package")
        )
        loaded_package = load_api_service_protocol_package(
            runtime_package_dir=runtime_package_dir
        )
        open_result_module = import_module("aware_proof_types.door.endpoints")
        open_result_type = cast(
            type[BaseModel], getattr(open_result_module, "OpenResult")
        )
        open_snapshot_module = import_module("aware_proof_types.door.endpoints")
        open_snapshot_type = cast(
            type[BaseModel], getattr(open_snapshot_module, "OpenSnapshot")
        )
        protocols_module = import_module(
            f"{loaded_package.service_protocol_import_root}.protocols"
        )
        generated_endpoint_binding = cast(
            Any,
            getattr(protocols_module, "ENDPOINT_BINDINGS")["openai.door.open"],
        )
        generated_fulfillment_binding = cast(
            Any, generated_endpoint_binding.fulfillment_bindings[0]
        )
        execution_request_type = _resolve_model_class(
            type_ref=str(generated_fulfillment_binding.request_type_ref),
            service_protocol_import_root=loaded_package.service_protocol_import_root,
        )
        execution_response_type = _resolve_model_class(
            type_ref=str(generated_fulfillment_binding.response_type_ref),
            service_protocol_import_root=loaded_package.service_protocol_import_root,
        )

        recorded_requests: list[BaseModel] = []
        recorded_stream_requests: list[BaseModel] = []
        recorded_execution_fulfillment_names: list[str] = []
        recorded_stream_events: list[BaseModel] = []

        class _DoorHandler:
            async def open(self, request: BaseModel, execution: object) -> BaseModel:
                recorded_requests.append(request)
                execution_request = execution_request_type.model_validate(
                    _build_model_payload(execution_request_type)
                )
                _ = await cast(Any, execution).open(execution_request)
                return open_result_type.model_validate({"accepted": True})

            def stream_open(self, request: BaseModel, execution: object):
                recorded_stream_requests.append(request)
                assert execution is not None

                async def _stream():
                    event = open_snapshot_type.model_validate({"accepted": True})
                    recorded_stream_events.append(event)
                    yield event

                return _stream()

        handler = cast(
            object, SimpleNamespace(openai=SimpleNamespace(door=_DoorHandler()))
        )

        lane = LaneIds(
            branch_id=uuid4(),
            actor_id=uuid4(),
        )
        assert lane.branch_id is not None
        assert lane.actor_id is not None
        active_branch_id = lane.branch_id
        endpoint_ref = "openai.door.open"
        api_snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=lane.actor_id,
            branch_id=active_branch_id,
            projection_hash=api_projection_hash,
            api_name="openai",
            endpoint_refs=(endpoint_ref,),
            endpoint_request_class_config_ids={
                endpoint_ref: request_class_config.id,
            },
            endpoint_fulfillment_names={endpoint_ref: ("open",)},
            api_graph_function_config_id=_select_runtime_function_config_id(
                runtime_index
            ),
        )
        assert api_snapshot.api.id is not None
        api_id = api_snapshot.api.id
        api_capability_endpoint_id = api_snapshot.endpoint_ids_by_ref[endpoint_ref]
        api_capability_endpoint_function_id = api_snapshot.endpoint_function_ids_by_ref[
            endpoint_ref
        ]["open"]

        expected_service_config_id = stable_service_config_id(name=service_config_name)
        service_config_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
        )
        service_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_projection_hash,
        )
        materialized_service_config = await materialize_service_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            name=service_config_name,
        )
        assert (
            materialized_service_config.binding.service_config_id
            == expected_service_config_id
        )

        materialized_service_config_api = await materialize_service_config_api(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            api_id=api_id,
        )
        materialized_operation_config = await materialize_service_operation_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            name=operation_config_name,
            admission_mode="public_read",
        )
        expected_operation_config_id = stable_service_operation_config_id(
            service_config_id=expected_service_config_id,
            name=operation_config_name,
        )
        assert (
            materialized_operation_config.binding.service_operation_config_id
            == expected_operation_config_id
        )

        materialized_api_endpoint = await materialize_service_operation_config_api_endpoint(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_operation_config_id=expected_operation_config_id,
            service_config_api_id=materialized_service_config_api.binding.service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
        )
        expected_api_endpoint_id = stable_service_operation_config_api_endpoint_id(
            service_operation_config_id=expected_operation_config_id,
            service_config_api_id=materialized_service_config_api.binding.service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
        )
        expected_api_endpoint_function_binding_id = (
            stable_service_operation_config_api_endpoint_function_id(
                service_operation_config_api_endpoint_id=expected_api_endpoint_id,
                api_capability_endpoint_function_id=api_capability_endpoint_function_id,
            )
        )
        assert (
            materialized_api_endpoint.binding.service_operation_config_api_endpoint_id
            == expected_api_endpoint_id
        )

        materialized_service = await materialize_service(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_lane,
            service_config_id=expected_service_config_id,
            name=service_name,
        )
        expected_service_id = stable_service_id(
            service_config_id=expected_service_config_id,
            name=service_name,
        )
        assert materialized_service.binding.service_id == expected_service_id

        materialized_api_endpoint_function = (
            await materialize_service_operation_config_api_endpoint_function(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_config_lane,
                service_operation_config_api_endpoint_id=expected_api_endpoint_id,
                api_capability_endpoint_function_id=api_capability_endpoint_function_id,
                description="Allowed API fulfillment",
            )
        )
        assert (
            materialized_api_endpoint_function.binding.service_operation_config_api_endpoint_function_id
            == expected_api_endpoint_function_binding_id
        )

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
            ),
            endpoint_ref="openai.door.open",
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

        scratch = cast(
            Session,
            await load_committed_service_lane_session(
                index=runtime_index,
                lane=service_config_lane,
                error_context="Service API stream Dispatch proof",
            ),
        )

        class _RecordingExecutionBackend(ServiceApiExecutionBackend):
            async def invoke_fulfillment(
                self,
                *,
                fulfillment_name: str,
                request: BaseModel,
            ) -> object | None:
                recorded_execution_fulfillment_names.append(fulfillment_name)
                assert isinstance(request, execution_request_type)
                return execution_response_type.model_validate(
                    _build_model_payload(execution_response_type)
                )

        streamed_events: list[object] = []

        async def _record_stream_event(event: object) -> None:
            streamed_events.append(event)

        executed = await execute_service_api_dispatch_plan(
            runtime=runtime,
            index=runtime_index,
            session=scratch,
            actor_id=lane.actor_id,
            target_lane=MaterializationLaneContext(
                branch_id=active_branch_id,
                projection_hash=service_projection_hash,
            ),
            dispatch_plan=dispatch_plan,
            service_id=expected_service_id,
            operation_key=operation_key,
            handler=handler,
            execution_context=cast(
                JsonObject, {"source": "service-protocol-stream-proof"}
            ),
            execution_backend=_RecordingExecutionBackend(),
            stream_requested=True,
            stream_event_sink=_record_stream_event,
        )

        assert executed.execution_object is not None
        assert isinstance(executed.response_object, open_result_type)
        assert (
            cast(BaseModel, executed.response_object).model_dump()["accepted"] is True
        )
        assert len(recorded_requests) == 1
        assert len(recorded_stream_requests) == 1
        assert recorded_execution_fulfillment_names == ["open"]
        assert len(streamed_events) == 1
        assert isinstance(streamed_events[0], open_snapshot_type)
        assert cast(BaseModel, streamed_events[0]).model_dump()["accepted"] is True
        assert len(recorded_stream_events) == 1
