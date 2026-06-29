from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Mapping, Protocol, cast
from uuid import UUID

from pydantic import BaseModel

from aware_api_ontology.api.api_call import ApiCall
from aware_meta.class_.inline_value_instance import (
    resolve_inline_value_instance_attributes,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
    AttributeTypeDescriptorRole,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.enum.enum_option import EnumOption
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.session import Session
from aware_utils.string_transform import to_snake_case

from ..ontology_graph.ontology import APIOntologyPlan, decode_api_ontology_plan_payload
from ..invocation import ResolvedApiInvocationEnvelope
from ..invocation.materialization.pydantic_class_config_closure import (
    pydantic_class_configs_by_id_for_ref,
)


class ApiServiceProtocolExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ApiServiceProtocolExecution(Protocol):
    pass


ApiServiceProtocolInvoker = Callable[
    [object, BaseModel, ApiServiceProtocolExecution | None],
    Awaitable[object | None],
]
ApiServiceProtocolStreamInvoker = Callable[
    [object, BaseModel, ApiServiceProtocolExecution | None],
    AsyncIterator[object],
]
ApiServiceProtocolExecutionFactory = Callable[
    [ApiServiceProtocolExecutionBackend],
    ApiServiceProtocolExecution,
]
type _FulfillmentBindingKey = tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    call_target_kind: str | None
    exact_output_field_name: str | None
    method_name: str
    request_type_ref: str
    response_type_ref: str


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolEndpointBinding:
    # Generated service protocol packages are a Python symbol catalog only.
    # Endpoint/request fulfillment semantics remain API-owned runtime truth
    # on the envelope and committed ontology rails.
    endpoint_ref: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ApiServiceProtocolExecutionFactory | None
    stream_invoke: ApiServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ApiServiceProtocolFulfillmentBinding, ...]
    invoke: ApiServiceProtocolInvoker


@dataclass(frozen=True, slots=True)
class LoadedApiServiceProtocolPackage:
    runtime_package_dir: Path
    public_package_root: Path
    service_protocol_package_root: Path
    public_package_import_root: str
    service_protocol_import_root: str
    endpoint_bindings: Mapping[str, ApiServiceProtocolEndpointBinding]
    runtime_fulfillment_bindings: Mapping[
        _FulfillmentBindingKey, "_PlannedFulfillmentBinding"
    ]


@dataclass(frozen=True, slots=True)
class RematerializedApiCall:
    envelope: ResolvedApiInvocationEnvelope
    api_call: ApiCall
    request_model: InlineValueInstance
    request_class_config: ClassConfig


@dataclass(frozen=True, slots=True)
class DecodedApiServiceProtocolRequest:
    envelope: ResolvedApiInvocationEnvelope
    endpoint_binding: ApiServiceProtocolEndpointBinding
    api_call: ApiCall
    request_model: InlineValueInstance
    request_class_config: ClassConfig
    request_payload: Mapping[str, object]
    request_object: BaseModel


@dataclass(frozen=True, slots=True)
class ApiServiceDispatchPlan:
    envelope: ResolvedApiInvocationEnvelope
    public_package_import_root: str
    service_protocol_import_root: str
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ApiServiceProtocolExecutionFactory | None
    stream_invoke: ApiServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ApiServiceDispatchFulfillmentBinding, ...]
    request_object: BaseModel
    invoke: ApiServiceProtocolInvoker


@dataclass(frozen=True, slots=True)
class ApiServiceDispatchFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    graph_function_runtime_target: str
    call_target_kind: str | None
    exact_output_field_name: str | None
    method_name: str
    request_type_ref: str
    response_type_ref: str
    source_path: str
    api_capability_endpoint_function_id: UUID | None = None
    instance_target_plan: ApiServiceDispatchInstanceTargetPlan | None = None


@dataclass(frozen=True, slots=True)
class ApiServiceDispatchInstanceTargetPlan:
    graph_target: str
    projection_hash: str
    target_class_config_id: UUID
    key_attribute_name: str
    key_attribute_id: UUID
    key_value: object
    binding_ref: str
    parent_class: str
    relationship_attribute: str
    source_path: str


@dataclass(frozen=True, slots=True)
class _PlannedFulfillmentBinding:
    graph_function_python_ref: str
    graph_function_runtime_target: str
    call_target_kind: str | None
    exact_output_field_name: str | None


class _GeneratedEndpointBinding(Protocol):
    endpoint_ref: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ApiServiceProtocolExecutionFactory | None
    stream_invoke: ApiServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[_GeneratedFulfillmentBinding, ...]
    invoke: ApiServiceProtocolInvoker


class _GeneratedProtocolsModule(Protocol):
    PUBLIC_PACKAGE_IMPORT_ROOT: str
    ENDPOINT_BINDINGS: Mapping[str, _GeneratedEndpointBinding]


class _GeneratedFulfillmentBinding(Protocol):
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    call_target_kind: str | None
    exact_output_field_name: str | None
    method_name: str
    request_type_ref: str
    response_type_ref: str


@dataclass(frozen=True, slots=True)
class ResolvedApiGeneratedPackageRoots:
    runtime_package_dir: Path
    public_package_root: Path
    service_protocol_package_root: Path
    public_package_import_root: str
    service_protocol_import_root: str


def load_api_service_protocol_package(
    *,
    runtime_package_dir: str | Path,
) -> LoadedApiServiceProtocolPackage:
    roots = resolve_api_service_protocol_package_roots(
        runtime_package_dir=runtime_package_dir
    )

    with _scoped_generated_package_imports(
        package_roots=(roots.public_package_root, roots.service_protocol_package_root),
        import_roots=(
            roots.public_package_import_root,
            roots.service_protocol_import_root,
        ),
    ):
        protocols_module = cast(
            _GeneratedProtocolsModule,
            cast(
                object, import_module(f"{roots.service_protocol_import_root}.protocols")
            ),
        )
        bindings = _load_endpoint_bindings(
            protocols_module=protocols_module,
            expected_public_package_import_root=roots.public_package_import_root,
        )

    return LoadedApiServiceProtocolPackage(
        runtime_package_dir=roots.runtime_package_dir,
        public_package_root=roots.public_package_root,
        service_protocol_package_root=roots.service_protocol_package_root,
        public_package_import_root=roots.public_package_import_root,
        service_protocol_import_root=roots.service_protocol_import_root,
        endpoint_bindings=bindings,
        runtime_fulfillment_bindings=_load_runtime_fulfillment_bindings(
            runtime_root=roots.runtime_package_dir
        ),
    )


def resolve_api_service_protocol_package_roots(
    *,
    runtime_package_dir: str | Path,
) -> ResolvedApiGeneratedPackageRoots:
    runtime_root = Path(runtime_package_dir).expanduser().resolve()
    manifest = _load_runtime_manifest(runtime_root=runtime_root)
    artifact_public_package_root = (
        runtime_root / "public_package" / "python" / "package"
    ).resolve()
    artifact_service_protocol_package_root = (
        runtime_root / "service_protocol" / "python" / "package"
    ).resolve()
    if (
        artifact_public_package_root.exists()
        or artifact_service_protocol_package_root.exists()
    ):
        public_package_root = artifact_public_package_root
        service_protocol_package_root = artifact_service_protocol_package_root
        public_package_import_root = _resolve_single_import_root(
            package_root=public_package_root,
            label="public package",
        )
        service_protocol_import_root = _resolve_single_import_root(
            package_root=service_protocol_package_root,
            label="service protocol package",
        )
    elif manifest is not None:
        api_toml_path = _resolve_runtime_manifest_path(
            manifest=manifest,
            runtime_root=runtime_root,
            key="api_toml_path",
            relpath_key="api_toml_relpath",
        )
        api_fqn_prefix = _require_manifest_str(manifest=manifest, key="api_fqn_prefix")
        api_package_name = _require_manifest_str(
            manifest=manifest, key="api_package_name"
        )
        package_root = _resolve_runtime_manifest_package_root(
            manifest=manifest,
            runtime_root=runtime_root,
            api_toml_path=api_toml_path,
        )
        public_package_import_root = _derive_public_import_root(
            fqn_prefix=api_fqn_prefix,
            package_name=api_package_name,
        )
        service_protocol_import_root = _derive_service_protocol_import_root(
            fqn_prefix=api_fqn_prefix,
            package_name=api_package_name,
        )
        public_package_root = (
            package_root / "python" / public_package_import_root
        ).resolve()
        service_protocol_package_root = (
            package_root / "python" / service_protocol_import_root
        ).resolve()
    else:
        public_package_root = (
            runtime_root / "public_package" / "python" / "package"
        ).resolve()
        service_protocol_package_root = (
            runtime_root / "service_protocol" / "python" / "package"
        ).resolve()
        public_package_import_root = _resolve_single_import_root(
            package_root=public_package_root,
            label="public package",
        )
        service_protocol_import_root = _resolve_single_import_root(
            package_root=service_protocol_package_root,
            label="service protocol package",
        )

    if not public_package_root.exists():
        raise RuntimeError(
            "API service protocol package runtime requires generated public package roots for runtime_package_dir: "
            f"{public_package_root}"
        )
    if not service_protocol_package_root.exists():
        raise RuntimeError(
            "API service protocol package runtime requires generated service protocol roots for runtime_package_dir: "
            f"{service_protocol_package_root}"
        )

    return ResolvedApiGeneratedPackageRoots(
        runtime_package_dir=runtime_root,
        public_package_root=public_package_root,
        service_protocol_package_root=service_protocol_package_root,
        public_package_import_root=public_package_import_root,
        service_protocol_import_root=service_protocol_import_root,
    )


async def rematerialize_committed_api_call(
    *,
    index: MetaGraphRuntimeIndex,
    envelope: ResolvedApiInvocationEnvelope,
) -> RematerializedApiCall:
    opg = index.opg_by_hash.get(envelope.projection_hash)
    if opg is None:
        raise RuntimeError(
            "API service protocol package runtime could not resolve api_call projection from commit-backed envelope: "
            f"projection_hash={envelope.projection_hash}"
        )

    oig, _ = await CachedLaneMaterializer().get(
        branch_id=envelope.branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=envelope.commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    scratch = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=envelope.branch_id,
    )

    api_call = scratch.imap_get(ApiCall, envelope.api_call_id)
    if api_call is None:
        raise RuntimeError(
            "API service protocol package runtime could not re-materialize committed ApiCall from envelope: "
            f"api_call_id={envelope.api_call_id}"
        )

    request_model = api_call.request_model
    if request_model is None:
        request_model = scratch.imap_get(InlineValueInstance, envelope.request_model_id)
    if request_model is None:
        raise RuntimeError(
            "API service protocol package runtime could not re-materialize committed ApiCall.request_model from envelope: "
            f"request_model_id={envelope.request_model_id}"
        )

    request_class_config = index.class_configs_by_id.get(
        envelope.request_class_config_id
    )
    if request_class_config is None:
        raise RuntimeError(
            "API service protocol package runtime could not resolve request ClassConfig from envelope: "
            f"request_class_config_id={envelope.request_class_config_id}"
        )
    if request_model.class_config_id != request_class_config.id:
        raise RuntimeError(
            "API service protocol package runtime re-materialized request model with mismatched ClassConfig: "
            f"request_model.class_config_id={request_model.class_config_id} "
            f"request_class_config_id={request_class_config.id}"
        )

    return RematerializedApiCall(
        envelope=envelope,
        api_call=api_call,
        request_model=request_model,
        request_class_config=request_class_config,
    )


async def decode_committed_api_call_request(
    *,
    index: MetaGraphRuntimeIndex,
    envelope: ResolvedApiInvocationEnvelope,
    runtime_package_dir: str | Path,
) -> DecodedApiServiceProtocolRequest:
    loaded_package = load_api_service_protocol_package(
        runtime_package_dir=runtime_package_dir
    )
    return await _decode_committed_api_call_request_from_loaded_package(
        index=index,
        envelope=envelope,
        loaded_package=loaded_package,
    )


async def build_api_service_dispatch_plan(
    *,
    index: MetaGraphRuntimeIndex,
    envelope: ResolvedApiInvocationEnvelope,
    runtime_package_dir: str | Path,
) -> ApiServiceDispatchPlan:
    loaded_package = load_api_service_protocol_package(
        runtime_package_dir=runtime_package_dir
    )
    decoded_request = await _decode_committed_api_call_request_from_loaded_package(
        index=index,
        envelope=envelope,
        loaded_package=loaded_package,
    )
    return _build_api_service_dispatch_plan_from_decoded_request(
        index=index,
        decoded_request=decoded_request,
        loaded_package=loaded_package,
        runtime_package_dir=runtime_package_dir,
    )


async def build_api_service_dispatch_plan_from_materialized_call(
    *,
    index: MetaGraphRuntimeIndex,
    envelope: ResolvedApiInvocationEnvelope,
    api_call: ApiCall,
    request_class_config: ClassConfig,
    runtime_package_dir: str | Path,
    request_payload_override: Mapping[str, object] | None = None,
) -> ApiServiceDispatchPlan:
    loaded_package = load_api_service_protocol_package(
        runtime_package_dir=runtime_package_dir
    )
    decoded_request = _decode_materialized_api_call_request_from_loaded_package(
        index=index,
        envelope=envelope,
        loaded_package=loaded_package,
        api_call=api_call,
        request_class_config=request_class_config,
        request_payload_override=request_payload_override,
    )
    return _build_api_service_dispatch_plan_from_decoded_request(
        index=index,
        decoded_request=decoded_request,
        loaded_package=loaded_package,
        runtime_package_dir=runtime_package_dir,
    )


def _build_api_service_dispatch_plan_from_decoded_request(
    *,
    index: MetaGraphRuntimeIndex,
    decoded_request: DecodedApiServiceProtocolRequest,
    loaded_package: LoadedApiServiceProtocolPackage,
    runtime_package_dir: str | Path,
) -> ApiServiceDispatchPlan:
    return ApiServiceDispatchPlan(
        envelope=decoded_request.envelope,
        public_package_import_root=loaded_package.public_package_import_root,
        service_protocol_import_root=loaded_package.service_protocol_import_root,
        endpoint_ref=decoded_request.envelope.endpoint_ref,
        api_name=decoded_request.envelope.api_name,
        capability_name=decoded_request.envelope.capability_name,
        endpoint_name=decoded_request.envelope.endpoint_name,
        request_type_ref=decoded_request.endpoint_binding.request_type_ref,
        response_type_ref=decoded_request.endpoint_binding.response_type_ref,
        stream_event_type_refs=decoded_request.endpoint_binding.stream_event_type_refs,
        execution_protocol_ref=decoded_request.endpoint_binding.execution_protocol_ref,
        build_execution=decoded_request.endpoint_binding.build_execution,
        stream_invoke=decoded_request.endpoint_binding.stream_invoke,
        fulfillment_bindings=resolve_api_service_dispatch_instance_target_plans(
            index=index,
            runtime_package_dir=runtime_package_dir,
            endpoint_ref=decoded_request.envelope.endpoint_ref,
            request_class_ref=decoded_request.envelope.request_class_ref,
            request_class_config_id=decoded_request.request_class_config.id,
            request_object=decoded_request.request_object,
            fulfillment_bindings=_build_dispatch_fulfillment_bindings(
                envelope=decoded_request.envelope,
                endpoint_binding=decoded_request.endpoint_binding,
                runtime_fulfillment_bindings=loaded_package.runtime_fulfillment_bindings,
            ),
        ),
        request_object=decoded_request.request_object,
        invoke=decoded_request.endpoint_binding.invoke,
    )


def resolve_api_service_dispatch_instance_target_plans(
    *,
    index: MetaGraphRuntimeIndex,
    runtime_package_dir: str | Path,
    endpoint_ref: str,
    request_class_ref: str,
    request_class_config_id: UUID,
    request_object: BaseModel,
    fulfillment_bindings: tuple[ApiServiceDispatchFulfillmentBinding, ...],
) -> tuple[ApiServiceDispatchFulfillmentBinding, ...]:
    if not fulfillment_bindings:
        return ()

    updated_bindings: list[ApiServiceDispatchFulfillmentBinding] = []
    for binding in fulfillment_bindings:
        if binding.instance_target_plan is not None:
            updated_bindings.append(binding)
            continue
        if (binding.call_target_kind or "").strip().casefold() == "constructor":
            updated_bindings.append(binding)
            continue
        if (binding.call_target_kind or "").strip().casefold() == "opg_read":
            raise RuntimeError(
                "API service protocol package runtime no longer resolves ontology projection-read target plans. "
                "Expose this endpoint through a service-owned view/read model instead: "
                f"endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )

        updated_bindings.append(binding)

    return tuple(updated_bindings)


async def resolve_api_service_instance_target_object_id(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    instance_target_plan: ApiServiceDispatchInstanceTargetPlan,
) -> UUID:
    scratch = await _hydrate_committed_projection_session(
        index=index,
        branch_id=branch_id,
        projection_hash=instance_target_plan.projection_hash,
        error_context="API service protocol package runtime instance-target resolution",
    )
    matches: list[UUID] = []
    for obj in scratch.imap_all_objects():
        if not isinstance(obj, ORMModel) or obj.id is None:
            continue
        class_config = obj.get_class_config()
        if (
            class_config is None
            or class_config.id != instance_target_plan.target_class_config_id
        ):
            continue
        if (
            getattr(obj, instance_target_plan.key_attribute_name, None)
            != instance_target_plan.key_value
        ):
            continue
        matches.append(obj.id)

    if not matches:
        raise RuntimeError(
            "API service protocol package runtime could not resolve one concrete instance target on the requested lane: "
            f"binding_ref={instance_target_plan.binding_ref!r} "
            f"projection_hash={instance_target_plan.projection_hash!r} "
            f"key_attribute={instance_target_plan.key_attribute_name!r} "
            f"key_value={instance_target_plan.key_value!r}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            "API service protocol package runtime resolved multiple concrete instance targets for one binding key on the "
            "requested lane: "
            f"binding_ref={instance_target_plan.binding_ref!r} "
            f"projection_hash={instance_target_plan.projection_hash!r} "
            f"key_attribute={instance_target_plan.key_attribute_name!r} "
            f"key_value={instance_target_plan.key_value!r}"
        )
    return matches[0]


def decode_inline_value_instance_to_mapping_strict(
    *,
    inline_value_instance: InlineValueInstance,
    class_config: ClassConfig,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> Mapping[str, object]:
    resolved_attributes = resolve_inline_value_instance_attributes(
        inline_value_instance=inline_value_instance,
        class_config=class_config,
        class_configs_by_id=class_configs_by_id,
    )
    values: dict[str, object] = {}
    for resolved in resolved_attributes:
        attribute_name = (resolved.attribute_config.name or "").strip()
        if not attribute_name:
            raise RuntimeError(
                "API service protocol package runtime requires non-empty AttributeConfig.name during InlineValueInstance decode: "
                f"class_config_id={class_config.id} attribute_id={resolved.attribute.id}"
            )
        descriptor = resolved.attribute_config.type_descriptor
        if descriptor is None:
            raise RuntimeError(
                "API service protocol package runtime requires AttributeConfig.type_descriptor via OCG portal during decode: "
                f"class_config_id={class_config.id} attribute_config_id={resolved.attribute_config.id}"
            )
        values[attribute_name] = _decode_attribute_value_strict(
            resolved.attribute.value_root,
            descriptor=descriptor,
            class_configs_by_id=class_configs_by_id,
        )
    return values


async def _decode_committed_api_call_request_from_loaded_package(
    *,
    index: MetaGraphRuntimeIndex,
    envelope: ResolvedApiInvocationEnvelope,
    loaded_package: LoadedApiServiceProtocolPackage,
) -> DecodedApiServiceProtocolRequest:
    endpoint_binding = _resolve_endpoint_binding_for_envelope(
        envelope=envelope,
        loaded_package=loaded_package,
    )
    rematerialized = await rematerialize_committed_api_call(
        index=index,
        envelope=envelope,
    )
    request_class_configs_by_id = _request_class_configs_by_id_for_decode(
        index=index,
        request_class_config=rematerialized.request_class_config,
        request_type_ref=endpoint_binding.request_type_ref,
    )
    request_payload = decode_inline_value_instance_to_mapping_strict(
        inline_value_instance=rematerialized.request_model,
        class_config=rematerialized.request_class_config,
        class_configs_by_id=request_class_configs_by_id,
    )
    request_model_cls = _resolve_request_model_class(
        loaded_package=loaded_package,
        endpoint_binding=endpoint_binding,
    )
    request_object = request_model_cls.model_validate(dict(request_payload))
    return DecodedApiServiceProtocolRequest(
        envelope=envelope,
        endpoint_binding=endpoint_binding,
        api_call=rematerialized.api_call,
        request_model=rematerialized.request_model,
        request_class_config=rematerialized.request_class_config,
        request_payload=request_payload,
        request_object=request_object,
    )


def _decode_materialized_api_call_request_from_loaded_package(
    *,
    index: MetaGraphRuntimeIndex,
    envelope: ResolvedApiInvocationEnvelope,
    loaded_package: LoadedApiServiceProtocolPackage,
    api_call: ApiCall,
    request_class_config: ClassConfig,
    request_payload_override: Mapping[str, object] | None = None,
) -> DecodedApiServiceProtocolRequest:
    endpoint_binding = _resolve_endpoint_binding_for_envelope(
        envelope=envelope,
        loaded_package=loaded_package,
    )
    if api_call.id != envelope.api_call_id:
        raise RuntimeError(
            "API service protocol package runtime received materialized ApiCall with mismatched envelope identity: "
            f"api_call_id={api_call.id} envelope_api_call_id={envelope.api_call_id}"
        )
    if api_call.request_model_id != envelope.request_model_id:
        raise RuntimeError(
            "API service protocol package runtime received materialized ApiCall with mismatched request model identity: "
            f"api_call.request_model_id={api_call.request_model_id} "
            f"envelope_request_model_id={envelope.request_model_id}"
        )
    if request_class_config.id != envelope.request_class_config_id:
        raise RuntimeError(
            "API service protocol package runtime received materialized request ClassConfig with mismatched envelope identity: "
            f"request_class_config_id={request_class_config.id} "
            f"envelope_request_class_config_id={envelope.request_class_config_id}"
        )
    request_model = api_call.request_model
    if request_model is None:
        raise RuntimeError(
            "API service protocol package runtime materialized dispatch fast path requires ApiCall.request_model "
            "to be present before request decode."
        )
    if request_model.class_config_id != request_class_config.id:
        raise RuntimeError(
            "API service protocol package runtime received materialized request model with mismatched ClassConfig: "
            f"request_model.class_config_id={request_model.class_config_id} "
            f"request_class_config_id={request_class_config.id}"
        )
    request_model_cls = _resolve_request_model_class(
        loaded_package=loaded_package,
        endpoint_binding=endpoint_binding,
    )
    if request_payload_override is None:
        request_class_configs_by_id = _request_class_configs_by_id_for_decode(
            index=index,
            request_class_config=request_class_config,
            request_type_ref=endpoint_binding.request_type_ref,
        )
        request_payload = decode_inline_value_instance_to_mapping_strict(
            inline_value_instance=request_model,
            class_config=request_class_config,
            class_configs_by_id=request_class_configs_by_id,
        )
    else:
        request_payload = dict(request_payload_override)
    request_object = request_model_cls.model_validate(dict(request_payload))
    return DecodedApiServiceProtocolRequest(
        envelope=envelope,
        endpoint_binding=endpoint_binding,
        api_call=api_call,
        request_model=request_model,
        request_class_config=request_class_config,
        request_payload=request_payload,
        request_object=request_object,
    )


def _request_class_configs_by_id_for_decode(
    *,
    index: MetaGraphRuntimeIndex,
    request_class_config: ClassConfig,
    request_type_ref: str,
) -> dict[UUID, ClassConfig]:
    return pydantic_class_configs_by_id_for_ref(
        base_class_configs_by_id=index.class_configs_by_id,
        root_class_config=request_class_config,
        class_ref=request_type_ref,
    )


def _resolve_endpoint_binding_for_envelope(
    *,
    envelope: ResolvedApiInvocationEnvelope,
    loaded_package: LoadedApiServiceProtocolPackage,
) -> ApiServiceProtocolEndpointBinding:
    endpoint_binding = loaded_package.endpoint_bindings.get(envelope.endpoint_ref)
    if endpoint_binding is None:
        raise RuntimeError(
            "API service protocol package runtime could not resolve service protocol binding for ApiCall envelope: "
            f"endpoint_ref={envelope.endpoint_ref}"
        )
    if endpoint_binding.endpoint_ref != envelope.endpoint_ref:
        raise RuntimeError(
            "API service protocol package runtime resolved mismatched endpoint binding from compiled service protocol: "
            f"expected={envelope.endpoint_ref!r} got={endpoint_binding.endpoint_ref!r}"
        )
    return endpoint_binding


def _resolve_request_model_class(
    *,
    loaded_package: LoadedApiServiceProtocolPackage,
    endpoint_binding: ApiServiceProtocolEndpointBinding,
) -> type[BaseModel]:
    class_name = _class_name_from_ref(endpoint_binding.request_type_ref)
    with _scoped_generated_package_imports(
        package_roots=(
            loaded_package.public_package_root,
            loaded_package.service_protocol_package_root,
        ),
        import_roots=(
            loaded_package.public_package_import_root,
            loaded_package.service_protocol_import_root,
        ),
    ):
        for module_name in _request_model_module_candidates(
            loaded_package=loaded_package,
            request_type_ref=endpoint_binding.request_type_ref,
            class_name=class_name,
        ):
            try:
                module = import_module(module_name)
            except ModuleNotFoundError:
                continue
            model_cls = getattr(module, class_name, None)
            if isinstance(model_cls, type) and issubclass(model_cls, BaseModel):
                return model_cls
    module_name = to_snake_case(class_name)
    raise RuntimeError(
        "API service protocol package runtime could not resolve generated request model class from compiled public package "
        "or service protocol DTO refs: "
        f"request_type_ref={endpoint_binding.request_type_ref!r} "
        f"legacy_module={loaded_package.public_package_import_root}.models.{module_name} "
        f"class_name={class_name}"
    )


def _request_model_module_candidates(
    *,
    loaded_package: LoadedApiServiceProtocolPackage,
    request_type_ref: str,
    class_name: str,
) -> tuple[str, ...]:
    normalized_ref = str(request_type_ref or "").strip()
    candidates: list[str] = []
    if "." in normalized_ref:
        candidates.append(normalized_ref.rsplit(".", 1)[0])
    candidates.append(f"{loaded_package.service_protocol_import_root}.protocols")
    candidates.append(
        f"{loaded_package.public_package_import_root}.models.{to_snake_case(class_name)}"
    )
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def _resolve_single_import_root(*, package_root: Path, label: str) -> str:
    candidates = sorted(
        child.name
        for child in package_root.iterdir()
        if child.is_dir() and (child / "__init__.py").exists()
    )
    if len(candidates) != 1:
        raise RuntimeError(
            f"API service protocol package runtime expected exactly one import root under {label}: "
            f"path={package_root} candidates={candidates}"
        )
    return candidates[0]


def _load_runtime_manifest(*, runtime_root: Path) -> Mapping[str, object] | None:
    manifest_path = (runtime_root / "api.manifest.json").resolve()
    if not manifest_path.exists():
        return None
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"API Product runtime manifest must be a JSON object: {manifest_path}"
        )
    return cast(Mapping[str, object], payload)


def _require_manifest_str(*, manifest: Mapping[str, object], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"API Product runtime manifest requires non-empty string field {key!r}."
        )
    return value.strip()


def _require_manifest_path(*, manifest: Mapping[str, object], key: str) -> Path:
    return (
        Path(_require_manifest_str(manifest=manifest, key=key)).expanduser().resolve()
    )


def _resolve_runtime_manifest_path(
    *,
    manifest: Mapping[str, object],
    runtime_root: Path,
    key: str,
    relpath_key: str,
) -> Path:
    workspace_root = _workspace_root_from_runtime_root(runtime_root=runtime_root)
    raw_relpath = manifest.get(relpath_key)
    if isinstance(raw_relpath, str) and raw_relpath.strip():
        relpath = Path(raw_relpath.strip())
        if relpath.is_absolute():
            return relpath.expanduser().resolve()
        return (workspace_root / relpath).resolve()
    raw_path = Path(_require_manifest_str(manifest=manifest, key=key)).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()
    return (workspace_root / raw_path).resolve()


def _resolve_runtime_manifest_package_root(
    *,
    manifest: Mapping[str, object],
    runtime_root: Path,
    api_toml_path: Path,
) -> Path:
    workspace_root = _workspace_root_from_runtime_root(runtime_root=runtime_root)
    raw_relpath = manifest.get("api_package_root_relpath")
    if isinstance(raw_relpath, str) and raw_relpath.strip():
        relpath = Path(raw_relpath.strip())
        if relpath.is_absolute():
            return relpath.expanduser().resolve()
        return (workspace_root / relpath).resolve()
    return api_toml_path.parent.resolve()


def _workspace_root_from_runtime_root(*, runtime_root: Path) -> Path:
    resolved = runtime_root.expanduser().resolve()
    if (
        resolved.parent.name == "runtime"
        and resolved.parent.parent.name == "api"
        and resolved.parent.parent.parent.name == ".aware"
    ):
        return resolved.parent.parent.parent.parent.resolve()
    return resolved.parent.resolve()


def _derive_public_import_root(*, fqn_prefix: str, package_name: str) -> str:
    token = (fqn_prefix or package_name).strip().replace("-", "_")
    return token or "aware_api_public_package"


def _derive_service_protocol_import_root(*, fqn_prefix: str, package_name: str) -> str:
    token = _derive_public_import_root(fqn_prefix=fqn_prefix, package_name=package_name)
    if token.endswith("_api"):
        token = token[: -len("_api")]
    token = token.strip("_")
    return f"{token}_protocol" if token else "aware_api_protocol"


@contextmanager
def _scoped_generated_package_imports(
    *,
    package_roots: tuple[Path, ...],
    import_roots: tuple[str, ...],
):
    normalized_package_roots = tuple(
        root.expanduser().resolve() for root in package_roots
    )
    _evict_conflicting_import_root_modules(
        import_roots=import_roots,
        package_roots=normalized_package_roots,
    )
    with _scoped_sys_path(normalized_package_roots):
        yield


def _load_endpoint_bindings(
    *,
    protocols_module: _GeneratedProtocolsModule,
    expected_public_package_import_root: str,
) -> Mapping[str, ApiServiceProtocolEndpointBinding]:
    public_package_import_root = protocols_module.PUBLIC_PACKAGE_IMPORT_ROOT
    if public_package_import_root != expected_public_package_import_root:
        raise RuntimeError(
            "API service protocol package runtime resolved mismatched public package import root from compiled service protocol: "
            f"expected={expected_public_package_import_root!r} got={public_package_import_root!r}"
        )

    raw_bindings = protocols_module.ENDPOINT_BINDINGS

    bindings: dict[str, ApiServiceProtocolEndpointBinding] = {}
    for endpoint_ref, raw_binding in raw_bindings.items():
        if not isinstance(endpoint_ref, str) or not endpoint_ref.strip():
            raise RuntimeError(
                "Compiled service protocol endpoint bindings must use non-empty string keys"
            )
        binding_endpoint_ref = str(raw_binding.endpoint_ref).strip()
        if binding_endpoint_ref != endpoint_ref.strip():
            raise RuntimeError(
                "Compiled service protocol endpoint binding must echo its endpoint_ref key: "
                f"key={endpoint_ref!r} value={binding_endpoint_ref!r}"
            )
        bindings[endpoint_ref] = ApiServiceProtocolEndpointBinding(
            endpoint_ref=binding_endpoint_ref,
            request_type_ref=str(raw_binding.request_type_ref),
            response_type_ref=(
                str(raw_response_type_ref)
                if (raw_response_type_ref := raw_binding.response_type_ref) is not None
                else None
            ),
            stream_event_type_refs=tuple(
                str(item) for item in raw_binding.stream_event_type_refs
            ),
            execution_protocol_ref=(
                str(raw_execution_protocol_ref)
                if (raw_execution_protocol_ref := raw_binding.execution_protocol_ref)
                is not None
                else None
            ),
            build_execution=_require_execution_factory(
                endpoint_ref=endpoint_ref,
                build_execution=raw_binding.build_execution,
            ),
            stream_invoke=_require_endpoint_stream_invoke(
                endpoint_ref=endpoint_ref,
                stream_event_type_refs=tuple(
                    str(item) for item in raw_binding.stream_event_type_refs
                ),
                stream_invoke=raw_binding.stream_invoke,
            ),
            fulfillment_bindings=tuple(
                _require_fulfillment_binding(
                    endpoint_ref=endpoint_ref,
                    raw_binding=item,
                )
                for item in raw_binding.fulfillment_bindings
            ),
            invoke=_require_endpoint_invoke(
                endpoint_ref=endpoint_ref,
                invoke=raw_binding.invoke,
            ),
        )
    return bindings


def _build_dispatch_fulfillment_bindings(
    *,
    envelope: ResolvedApiInvocationEnvelope,
    endpoint_binding: ApiServiceProtocolEndpointBinding,
    runtime_fulfillment_bindings: Mapping[
        _FulfillmentBindingKey, _PlannedFulfillmentBinding
    ],
) -> tuple[ApiServiceDispatchFulfillmentBinding, ...]:
    package_bindings_by_key = {
        (
            binding.name.strip(),
            binding.graph_target.strip(),
            binding.graph_capability_function_name.strip(),
        ): binding
        for binding in endpoint_binding.fulfillment_bindings
    }
    dispatch_bindings: list[ApiServiceDispatchFulfillmentBinding] = []
    for envelope_binding in envelope.fulfillment_bindings:
        key = (
            envelope_binding.name.strip(),
            envelope_binding.graph_target.strip(),
            envelope_binding.graph_capability_function_name.strip(),
        )
        package_binding = package_bindings_by_key.get(key)
        if package_binding is None:
            raise RuntimeError(
                "API service protocol package runtime could not resolve execution metadata for one envelope fulfillment binding: "
                f"endpoint_ref={envelope.endpoint_ref!r} "
                f"fulfillment_name={envelope_binding.name!r} "
                f"graph_target={envelope_binding.graph_target!r} "
                f"graph_capability_function_name={envelope_binding.graph_capability_function_name!r}"
            )
        planned_key = _fulfillment_binding_key(
            endpoint_ref=envelope.endpoint_ref,
            name=envelope_binding.name,
            graph_target=envelope_binding.graph_target,
            graph_capability_function_name=envelope_binding.graph_capability_function_name,
        )
        planned_binding = runtime_fulfillment_bindings.get(planned_key)
        if planned_binding is None:
            raise RuntimeError(
                "API service protocol package runtime could not resolve exact runtime callable metadata "
                "for one envelope fulfillment binding: "
                f"endpoint_ref={envelope.endpoint_ref!r} "
                f"fulfillment_name={envelope_binding.name!r} "
                f"graph_target={envelope_binding.graph_target!r} "
                f"graph_capability_function_name={envelope_binding.graph_capability_function_name!r}"
            )
        if (
            planned_binding.graph_function_python_ref
            != package_binding.graph_function_python_ref
        ):
            raise RuntimeError(
                "API service protocol package runtime detected mismatched package symbol vs compiled "
                "plan metadata for one fulfillment binding: "
                f"endpoint_ref={envelope.endpoint_ref!r} "
                f"fulfillment_name={envelope_binding.name!r} "
                f"package_graph_function_python_ref={package_binding.graph_function_python_ref!r} "
                f"planned_graph_function_python_ref={planned_binding.graph_function_python_ref!r}"
            )
        dispatch_bindings.append(
            ApiServiceDispatchFulfillmentBinding(
                name=envelope_binding.name,
                graph_target=envelope_binding.graph_target,
                graph_capability_function_name=envelope_binding.graph_capability_function_name,
                graph_function_python_ref=package_binding.graph_function_python_ref,
                graph_function_runtime_target=planned_binding.graph_function_runtime_target,
                call_target_kind=planned_binding.call_target_kind,
                exact_output_field_name=planned_binding.exact_output_field_name,
                method_name=package_binding.method_name,
                request_type_ref=package_binding.request_type_ref,
                response_type_ref=package_binding.response_type_ref,
                source_path=envelope_binding.source_path,
                api_capability_endpoint_function_id=envelope_binding.api_capability_endpoint_function_id,
            )
        )
    return tuple(dispatch_bindings)


def _load_runtime_fulfillment_bindings(
    *,
    runtime_root: Path,
) -> Mapping[_FulfillmentBindingKey, _PlannedFulfillmentBinding]:
    artifact_path = (runtime_root / "api.service_protocol_plan.json").resolve()
    if not artifact_path.exists():
        raise RuntimeError(
            "API service protocol package runtime requires a compiled service protocol plan artifact under runtime_package_dir: "
            f"{artifact_path}"
        )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(
            "API service protocol package runtime requires api.service_protocol_plan.json to contain a top-level object."
        )

    raw_apis = payload.get("apis", [])
    if not isinstance(raw_apis, list):
        raise RuntimeError(
            "API service protocol package runtime requires api.service_protocol_plan.json to export an 'apis' list."
        )

    bindings: dict[_FulfillmentBindingKey, _PlannedFulfillmentBinding] = {}
    for raw_api in raw_apis:
        if not isinstance(raw_api, dict):
            raise RuntimeError(
                "API service protocol package runtime requires 'apis' entries to be objects."
            )
        raw_capabilities = raw_api.get("capabilities", [])
        if not isinstance(raw_capabilities, list):
            raise RuntimeError(
                "API service protocol package runtime requires 'capabilities' entries to be lists."
            )
        for raw_capability in raw_capabilities:
            if not isinstance(raw_capability, dict):
                raise RuntimeError(
                    "API service protocol package runtime requires capability entries to be objects."
                )
            raw_endpoints = raw_capability.get("endpoints", [])
            if not isinstance(raw_endpoints, list):
                raise RuntimeError(
                    "API service protocol package runtime requires endpoint entries to be lists."
                )
            for raw_endpoint in raw_endpoints:
                if not isinstance(raw_endpoint, dict):
                    raise RuntimeError(
                        "API service protocol package runtime requires endpoint plan entries to be objects."
                    )
                endpoint_ref = _require_string_field(
                    row=raw_endpoint,
                    field_name="endpoint_ref",
                    context="api.service_protocol_plan.endpoints[]",
                )
                raw_fulfillment_bindings = raw_endpoint.get("fulfillment_bindings", [])
                if not isinstance(raw_fulfillment_bindings, list):
                    raise RuntimeError(
                        "API service protocol package runtime requires fulfillment_bindings to be lists "
                        "in api.service_protocol_plan.json."
                    )
                for raw_binding in raw_fulfillment_bindings:
                    if not isinstance(raw_binding, dict):
                        raise RuntimeError(
                            "API service protocol package runtime requires fulfillment binding entries to be objects."
                        )
                    key = _fulfillment_binding_key(
                        endpoint_ref=endpoint_ref,
                        name=_require_string_field(
                            row=raw_binding,
                            field_name="name",
                            context="api.service_protocol_plan.fulfillment_bindings[]",
                        ),
                        graph_target=_require_string_field(
                            row=raw_binding,
                            field_name="graph_target",
                            context="api.service_protocol_plan.fulfillment_bindings[]",
                        ),
                        graph_capability_function_name=_require_string_field(
                            row=raw_binding,
                            field_name="graph_capability_function_name",
                            context="api.service_protocol_plan.fulfillment_bindings[]",
                        ),
                    )
                    bindings[key] = _PlannedFulfillmentBinding(
                        graph_function_python_ref=_require_string_field(
                            row=raw_binding,
                            field_name="graph_function_python_ref",
                            context="api.service_protocol_plan.fulfillment_bindings[]",
                        ),
                        graph_function_runtime_target=_require_string_field(
                            row=raw_binding,
                            field_name="graph_function_runtime_target",
                            context="api.service_protocol_plan.fulfillment_bindings[]",
                        ),
                        call_target_kind=_optional_string_field(
                            row=raw_binding,
                            field_name="call_target_kind",
                        ),
                        exact_output_field_name=_optional_string_field(
                            row=raw_binding,
                            field_name="exact_output_field_name",
                        ),
                    )
    return bindings


def _resolve_api_ontology_plan_for_endpoint(
    *,
    runtime_package_dir: str | Path,
    endpoint_ref: str,
) -> APIOntologyPlan:
    payload = _load_api_compile_payload(runtime_package_dir=runtime_package_dir)
    raw_plans = payload.get("api_ontology")
    if not isinstance(raw_plans, list):
        raise RuntimeError(
            "API service protocol package runtime requires api.compile_plan.json to export an 'api_ontology' list."
        )
    plan_payloads = [
        cast(Mapping[str, object], item)
        for item in raw_plans
        if isinstance(item, Mapping)
    ]
    if len(plan_payloads) != len(raw_plans):
        raise RuntimeError(
            "API service protocol package runtime requires api_ontology[] plan entries to be objects."
        )
    plans = decode_api_ontology_plan_payload(payload=plan_payloads)
    api_name, _, _ = endpoint_ref.strip().partition(".")
    matches = [plan for plan in plans if plan.api.name == api_name]
    if not matches:
        raise RuntimeError(
            "API service protocol package runtime could not resolve api_ontology compile-plan payload for endpoint_ref: "
            f"{endpoint_ref!r}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            "API service protocol package runtime found ambiguous api_ontology compile-plan payloads for endpoint_ref: "
            f"{endpoint_ref!r}"
        )
    return matches[0]


def _load_api_compile_payload(
    *,
    runtime_package_dir: str | Path,
) -> Mapping[str, object]:
    runtime_root = Path(runtime_package_dir).expanduser().resolve()
    artifact_path = (runtime_root / "api.compile_plan.json").resolve()
    if not artifact_path.exists():
        raise RuntimeError(
            "API service protocol package runtime requires api.compile_plan.json under runtime_package_dir to resolve "
            f"instance-target metadata: {artifact_path}"
        )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(
            "API service protocol package runtime requires api.compile_plan.json to contain a top-level object."
        )
    return cast(Mapping[str, object], payload)


def _split_endpoint_ref(*, endpoint_ref: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in endpoint_ref.strip().split(".")]
    if len(parts) != 3 or any(not part for part in parts):
        raise RuntimeError(
            "API service protocol package runtime requires endpoint_ref to use exact api.capability.endpoint form: "
            f"{endpoint_ref!r}"
        )
    return parts[0], parts[1], parts[2]


def _projection_target_matches(*, projection_name: str | None, target: str) -> bool:
    projection_tokens = _projection_target_tokens(projection_name)
    return any(
        token in projection_tokens for token in _projection_target_tokens(target)
    )


def _projection_target_tokens(value: str | None) -> set[str]:
    raw = (value or "").strip()
    if not raw:
        return set()
    values = {raw}
    values.add(raw.rsplit(".", 1)[-1])
    if ".default." in raw:
        values.add(raw.replace(".default.", "."))
    tokens: set[str] = set()
    for item in values:
        token = item.strip()
        if not token:
            continue
        leaf = token.rsplit(".", 1)[-1]
        candidates = {token, leaf}
        for candidate in candidates:
            normalized = candidate.strip()
            if not normalized:
                continue
            tokens.add(normalized)
    return {token for token in tokens if token}


async def _hydrate_committed_projection_session(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    error_context: str,
) -> Session:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(f"{error_context} requires a committed lane head.")

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} could not resolve projection hash {projection_hash!r}."
        )

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


def _fulfillment_binding_key(
    *,
    endpoint_ref: str,
    name: str,
    graph_target: str,
    graph_capability_function_name: str,
) -> _FulfillmentBindingKey:
    return (
        endpoint_ref.strip(),
        name.strip(),
        graph_target.strip(),
        graph_capability_function_name.strip(),
    )


def _require_string_field(
    *,
    row: Mapping[str, object],
    field_name: str,
    context: str,
) -> str:
    value = row.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            "API service protocol package runtime requires a non-empty string field in api.service_protocol_plan.json: "
            f"context={context!r} field={field_name!r}"
        )
    return value


def _optional_string_field(
    *,
    row: Mapping[str, object],
    field_name: str,
) -> str | None:
    value = row.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeError(
            "API service protocol package runtime requires optional string metadata fields to remain strings in "
            "api.service_protocol_plan.json: "
            f"field={field_name!r}"
        )
    return value


def _evict_conflicting_import_root_modules(
    *,
    import_roots: tuple[str, ...],
    package_roots: tuple[Path, ...],
) -> None:
    for module_name, module in tuple(sys.modules.items()):
        if not isinstance(module_name, str):
            continue
        if not _module_name_matches_any_import_root(module_name, import_roots):
            continue
        if module is None:
            continue
        if _module_is_loaded_from_package_roots(
            module=module,
            package_roots=package_roots,
        ):
            continue
        sys.modules.pop(module_name, None)


def _module_is_loaded_from_package_roots(
    *,
    module: ModuleType,
    package_roots: tuple[Path, ...],
) -> bool:
    locations = _module_source_locations(module=module)
    if not locations:
        return False
    return any(
        _path_is_within_root(location=location, root=package_root)
        for location in locations
        for package_root in package_roots
    )


def _module_source_locations(*, module: ModuleType) -> tuple[Path, ...]:
    locations: list[Path] = []
    module_file = getattr(module, "__file__", None)
    if isinstance(module_file, str) and module_file:
        locations.append(Path(module_file).expanduser().resolve())
    module_path = getattr(module, "__path__", None)
    if module_path is not None:
        for entry in module_path:
            if isinstance(entry, str) and entry:
                locations.append(Path(entry).expanduser().resolve())
    deduped: list[Path] = []
    seen: set[Path] = set()
    for location in locations:
        if location in seen:
            continue
        seen.add(location)
        deduped.append(location)
    return tuple(deduped)


def _path_is_within_root(*, location: Path, root: Path) -> bool:
    try:
        location.relative_to(root)
    except ValueError:
        return False
    return True


def _module_name_matches_any_import_root(
    module_name: str, import_roots: tuple[str, ...]
) -> bool:
    return any(
        module_name == import_root or module_name.startswith(f"{import_root}.")
        for import_root in import_roots
    )


def _require_endpoint_invoke(
    *,
    endpoint_ref: str,
    invoke: object,
) -> ApiServiceProtocolInvoker:
    if not callable(invoke):
        raise RuntimeError(
            "Compiled service protocol endpoint binding must export callable invoke(...) "
            f"for endpoint_ref={endpoint_ref!r}"
        )
    return cast(ApiServiceProtocolInvoker, invoke)


def _require_endpoint_stream_invoke(
    *,
    endpoint_ref: str,
    stream_event_type_refs: tuple[str, ...],
    stream_invoke: object | None,
) -> ApiServiceProtocolStreamInvoker | None:
    if not stream_event_type_refs:
        if stream_invoke is None:
            return None
        if not callable(stream_invoke):
            raise RuntimeError(
                "Compiled service protocol endpoint binding must export callable stream_invoke(...) "
                f"for endpoint_ref={endpoint_ref!r}"
            )
        return cast(ApiServiceProtocolStreamInvoker, stream_invoke)
    if stream_invoke is None:
        raise RuntimeError(
            "Compiled service protocol endpoint binding must export callable stream_invoke(...) "
            f"for streamed endpoint_ref={endpoint_ref!r}"
        )
    if not callable(stream_invoke):
        raise RuntimeError(
            "Compiled service protocol endpoint binding must export callable stream_invoke(...) "
            f"for streamed endpoint_ref={endpoint_ref!r}"
        )
    return cast(ApiServiceProtocolStreamInvoker, stream_invoke)


def _require_execution_factory(
    *,
    endpoint_ref: str,
    build_execution: object | None,
) -> ApiServiceProtocolExecutionFactory | None:
    if build_execution is None:
        return None
    if not callable(build_execution):
        raise RuntimeError(
            "Compiled service protocol endpoint binding must export callable build_execution(...) "
            f"for endpoint_ref={endpoint_ref!r}"
        )
    return cast(ApiServiceProtocolExecutionFactory, build_execution)


def _require_fulfillment_binding(
    *,
    endpoint_ref: str,
    raw_binding: _GeneratedFulfillmentBinding,
) -> ApiServiceProtocolFulfillmentBinding:
    name = str(raw_binding.name)
    graph_target = str(raw_binding.graph_target)
    graph_capability_function_name = str(raw_binding.graph_capability_function_name)
    graph_function_python_ref = str(raw_binding.graph_function_python_ref)
    raw_call_target_kind = getattr(raw_binding, "call_target_kind", None)
    call_target_kind = (
        str(raw_call_target_kind).strip() if raw_call_target_kind is not None else None
    )
    if call_target_kind == "":
        call_target_kind = None
    raw_exact_output_field_name = getattr(raw_binding, "exact_output_field_name", None)
    exact_output_field_name = (
        str(raw_exact_output_field_name).strip()
        if raw_exact_output_field_name is not None
        else None
    )
    if exact_output_field_name == "":
        exact_output_field_name = None
    method_name = str(raw_binding.method_name)
    request_type_ref = str(raw_binding.request_type_ref)
    response_type_ref = str(raw_binding.response_type_ref)

    if (
        not name.strip()
        or not graph_target.strip()
        or not graph_capability_function_name.strip()
    ):
        raise RuntimeError(
            "Compiled service protocol fulfillment binding must use non-empty semantic identifiers: "
            f"endpoint_ref={endpoint_ref!r}"
        )
    if not graph_function_python_ref.strip():
        raise RuntimeError(
            "Compiled service protocol fulfillment binding must export graph_function_python_ref: "
            f"endpoint_ref={endpoint_ref!r} fulfillment_name={name!r}"
        )
    if (
        not method_name.strip()
        or not request_type_ref.strip()
        or not response_type_ref.strip()
    ):
        raise RuntimeError(
            "Compiled service protocol fulfillment binding must export typed execution metadata: "
            f"endpoint_ref={endpoint_ref!r} fulfillment_name={name!r}"
        )
    return ApiServiceProtocolFulfillmentBinding(
        name=name,
        graph_target=graph_target,
        graph_capability_function_name=graph_capability_function_name,
        graph_function_python_ref=graph_function_python_ref,
        call_target_kind=call_target_kind,
        exact_output_field_name=exact_output_field_name,
        method_name=method_name,
        request_type_ref=request_type_ref,
        response_type_ref=response_type_ref,
    )


def _decode_attribute_value_strict(
    value: AttributeValue,
    *,
    descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> object:
    kind = descriptor.kind
    if kind == AttributeTypeDescriptorKind.primitive:
        return _decode_primitive_value(value)
    if kind == AttributeTypeDescriptorKind.enum:
        return _decode_enum_value(value, descriptor=descriptor)
    if kind == AttributeTypeDescriptorKind.class_:
        return _decode_class_value(
            value, descriptor=descriptor, class_configs_by_id=class_configs_by_id
        )
    if kind == AttributeTypeDescriptorKind.collection:
        return _decode_collection_value(
            value, descriptor=descriptor, class_configs_by_id=class_configs_by_id
        )
    if kind == AttributeTypeDescriptorKind.mapping:
        return _decode_mapping_value(
            value, descriptor=descriptor, class_configs_by_id=class_configs_by_id
        )
    if kind == AttributeTypeDescriptorKind.tuple:
        return _decode_tuple_value(
            value, descriptor=descriptor, class_configs_by_id=class_configs_by_id
        )
    if kind == AttributeTypeDescriptorKind.union:
        return _decode_union_value(
            value, descriptor=descriptor, class_configs_by_id=class_configs_by_id
        )
    raise RuntimeError(
        f"Unsupported AttributeTypeDescriptorKind during strict decode: {kind!r}"
    )


def _decode_primitive_value(value: AttributeValue) -> object:
    payload = value.primitive_value
    if isinstance(payload, dict) and set(payload.keys()) == {"value"}:
        return payload.get("value")
    return payload


def _decode_enum_value(
    value: AttributeValue,
    *,
    descriptor: AttributeTypeDescriptor,
) -> object:
    enum_option = value.enum_option
    if enum_option is not None:
        return _enum_option_value(enum_option)

    enum_option_id = value.enum_option_id
    if enum_option_id is None:
        raise RuntimeError(
            "API service protocol package runtime requires enum_option or enum_option_id for ENUM descriptor decode"
        )

    enum_config = descriptor.enum_config
    if enum_config is None:
        return enum_option_id

    for option in list(enum_config.enum_options or ()):
        if option.id == enum_option_id:
            return _enum_option_value(option)
    return enum_option_id


def _decode_class_value(
    value: AttributeValue,
    *,
    descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> object:
    class_config = descriptor.class_config
    if (
        class_config is None
        and class_configs_by_id is not None
        and descriptor.class_config_id is not None
    ):
        class_config = class_configs_by_id.get(descriptor.class_config_id)
    value_mode = (
        class_config.value_mode
        if class_config is not None
        else ClassValueMode.graph_ref
    )

    if value_mode == ClassValueMode.inline_value:
        inline_value_instance = value.inline_value_instance
        if inline_value_instance is None:
            raise RuntimeError(
                "API service protocol package runtime requires inline_value_instance for inline class payload decode"
            )
        if class_config is None:
            raise RuntimeError(
                "API service protocol package runtime requires ClassConfig portal truth for inline class payload decode"
            )
        return decode_inline_value_instance_to_mapping_strict(
            inline_value_instance=inline_value_instance,
            class_config=class_config,
            class_configs_by_id=class_configs_by_id,
        )

    class_instance = value.class_instance
    if class_instance is not None and class_instance.id is not None:
        return class_instance.id
    if value.class_instance_id is None:
        raise RuntimeError(
            "API service protocol package runtime requires class_instance_id for graph_ref class payload decode"
        )
    return value.class_instance_id


def _decode_collection_value(
    value: AttributeValue,
    *,
    descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> object:
    element_descriptor = _pick_role_child(
        descriptor, AttributeTypeDescriptorRole.element
    )
    if element_descriptor is None:
        raise RuntimeError(
            "API service protocol package runtime requires ELEMENT descriptor child for collection decode"
        )
    element_links = [
        link
        for link in _sorted_child_links(value.child_links)
        if link.role == AttributeTypeDescriptorRole.element
    ]
    items = [
        _decode_attribute_value_strict(
            link.child,
            descriptor=element_descriptor,
            class_configs_by_id=class_configs_by_id,
        )
        for link in element_links
    ]
    if descriptor.collection_kind == AttributeCollectionType.single:
        if len(items) > 1:
            raise RuntimeError(
                "API service protocol package runtime expected at most one child for SINGLE collection decode"
            )
        return items[0] if items else None
    if descriptor.collection_kind == AttributeCollectionType.set:
        return list(items)
    return items


def _decode_mapping_value(
    value: AttributeValue,
    *,
    descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> object:
    key_descriptor = _pick_role_child(descriptor, AttributeTypeDescriptorRole.key)
    value_descriptor = _pick_role_child(descriptor, AttributeTypeDescriptorRole.value_)
    if key_descriptor is None or value_descriptor is None:
        raise RuntimeError(
            "API service protocol package runtime requires KEY/VALUE descriptor children for mapping decode"
        )
    grouped: dict[str, dict[AttributeTypeDescriptorRole, AttributeValue]] = {}
    for link in _sorted_child_links(value.child_links):
        identity_key = (link.identity_key or "").strip()
        if not identity_key:
            raise RuntimeError(
                "API service protocol package runtime requires identity_key for MAPPING value decode"
            )
        grouped.setdefault(identity_key, {})[link.role] = link.child

    decoded: dict[object, object] = {}
    for identity_key, entry in grouped.items():
        key_child = entry.get(AttributeTypeDescriptorRole.key)
        value_child = entry.get(AttributeTypeDescriptorRole.value_)
        if key_child is None or value_child is None:
            raise RuntimeError(
                "API service protocol package runtime requires paired KEY/VALUE children for MAPPING decode: "
                f"identity_key={identity_key!r}"
            )
        decoded_key = _decode_attribute_value_strict(
            key_child,
            descriptor=key_descriptor,
            class_configs_by_id=class_configs_by_id,
        )
        decoded_value = _decode_attribute_value_strict(
            value_child,
            descriptor=value_descriptor,
            class_configs_by_id=class_configs_by_id,
        )
        decoded[decoded_key] = decoded_value
    return decoded


def _decode_tuple_value(
    value: AttributeValue,
    *,
    descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> object:
    member_descriptors = _member_descriptors(descriptor)
    members = [
        link
        for link in _sorted_child_links(value.child_links)
        if link.role == AttributeTypeDescriptorRole.member
    ]
    decoded_members: list[object] = []
    for link in members:
        if link.position is None or link.position not in member_descriptors:
            raise RuntimeError(
                "API service protocol package runtime requires tuple MEMBER positions to align with descriptor truth"
            )
        decoded_members.append(
            _decode_attribute_value_strict(
                link.child,
                descriptor=member_descriptors[link.position],
                class_configs_by_id=class_configs_by_id,
            )
        )
    return tuple(decoded_members)


def _decode_union_value(
    value: AttributeValue,
    *,
    descriptor: AttributeTypeDescriptor,
    class_configs_by_id: Mapping[UUID, ClassConfig] | None,
) -> object:
    member_descriptors = _member_descriptors(descriptor)
    members = [
        link
        for link in _sorted_child_links(value.child_links)
        if link.role == AttributeTypeDescriptorRole.member
    ]
    if len(members) != 1:
        raise RuntimeError(
            "API service protocol package runtime requires exactly one selected MEMBER child for UNION decode"
        )
    selected = members[0]
    if selected.position is None or selected.position not in member_descriptors:
        raise RuntimeError(
            "API service protocol package runtime requires selected UNION MEMBER to align with descriptor truth"
        )
    return _decode_attribute_value_strict(
        selected.child,
        descriptor=member_descriptors[selected.position],
        class_configs_by_id=class_configs_by_id,
    )


def _sorted_child_links(
    child_links: list[AttributeValueLink],
) -> list[AttributeValueLink]:
    return sorted(
        list(child_links or []),
        key=lambda link: (
            str(link.role.value),
            link.position if link.position is not None else 10_000,
            str(link.identity_key or ""),
            str(link.id),
        ),
    )


def _enum_option_value(enum_option: EnumOption) -> str:
    value = (enum_option.value or "").strip()
    if not value:
        raise RuntimeError(
            "API service protocol package runtime requires EnumOption.value during strict decode"
        )
    return value


def _pick_role_child(
    descriptor: AttributeTypeDescriptor,
    role: AttributeTypeDescriptorRole,
) -> AttributeTypeDescriptor | None:
    for link in descriptor.child_links or []:
        if link.role == role:
            return link.child
    return None


def _member_descriptors(
    descriptor: AttributeTypeDescriptor,
) -> dict[int, AttributeTypeDescriptor]:
    members: dict[int, AttributeTypeDescriptor] = {}
    for link in descriptor.child_links or []:
        if link.role != AttributeTypeDescriptorRole.member or link.position is None:
            continue
        members[link.position] = link.child
    return dict(sorted(members.items(), key=lambda item: item[0]))


def _class_name_from_ref(class_ref: str) -> str:
    normalized = str(class_ref or "").strip()
    if not normalized or "." not in normalized:
        raise RuntimeError(
            "API service protocol package runtime requires dotted request_type_ref to resolve generated request model class: "
            f"{class_ref!r}"
        )
    class_name = normalized.rsplit(".", 1)[-1].strip()
    if not class_name:
        raise RuntimeError(
            "API service protocol package runtime resolved empty class name from request_type_ref: "
            f"{class_ref!r}"
        )
    return class_name


@contextmanager
def _scoped_sys_path(paths: tuple[Path, ...]):
    inserted: list[str] = []
    try:
        for path in paths:
            normalized = str(path.resolve())
            if normalized not in sys.path:
                sys.path.insert(0, normalized)
                inserted.append(normalized)
        yield
    finally:
        for normalized in reversed(inserted):
            try:
                sys.path.remove(normalized)
            except ValueError:
                pass


__all__ = [
    "ApiServiceDispatchFulfillmentBinding",
    "ApiServiceDispatchInstanceTargetPlan",
    "ApiServiceDispatchPlan",
    "ApiServiceProtocolExecution",
    "ApiServiceProtocolExecutionBackend",
    "ApiServiceProtocolExecutionFactory",
    "ApiServiceProtocolFulfillmentBinding",
    "ApiServiceProtocolEndpointBinding",
    "ResolvedApiGeneratedPackageRoots",
    "DecodedApiServiceProtocolRequest",
    "LoadedApiServiceProtocolPackage",
    "RematerializedApiCall",
    "build_api_service_dispatch_plan",
    "build_api_service_dispatch_plan_from_materialized_call",
    "decode_committed_api_call_request",
    "decode_inline_value_instance_to_mapping_strict",
    "load_api_service_protocol_package",
    "resolve_api_service_dispatch_instance_target_plans",
    "resolve_api_service_instance_target_object_id",
    "resolve_api_service_protocol_package_roots",
    "rematerialize_committed_api_call",
]
