from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from pydantic import BaseModel

from aware_code.types import (
    JsonArray,
    JsonObject,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)

from aware_service_runtime.api_ingress.graph_execution import (
    ServiceApiGraphExecutionBinding,
    ServiceApiGraphExecutionPlan,
)
from aware_service_runtime.api_ingress.target_resolution import (
    ResolvedServiceApiGraphFunctionTarget,
    resolve_service_api_constructor_projection,
    resolve_service_api_execution_binding,
    resolve_service_api_graph_function_target,
    service_graph_catalog,
)
from aware_service_runtime.api_ingress.telemetry import (
    await_with_service_api_trace,
    service_api_trace_phase,
)
from aware_service_runtime.contracts import (
    ServiceGraphCatalog,
    ServiceGraphContextLike,
    ServiceGraphGateway,
    ServiceOperationContext,
)


@dataclass(frozen=True, slots=True)
class GatewayBackedServiceApiExecutionBackend:
    execution_plan: ServiceApiGraphExecutionPlan
    graph_context: ServiceGraphContextLike
    graph_gateway: ServiceGraphGateway
    operation_context: ServiceOperationContext

    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None:
        trace_fields = {
            "endpoint_ref": self.execution_plan.endpoint_ref,
            "fulfillment_name": fulfillment_name,
        }
        with service_api_trace_phase(
            "graph_gateway.resolve_execution_binding",
            **trace_fields,
        ):
            binding = _resolve_execution_binding(
                execution_plan=self.execution_plan,
                fulfillment_name=fulfillment_name,
            )
        trace_fields["graph_function_runtime_target"] = (
            binding.graph_function_runtime_target
        )
        graph_context = self.graph_context
        graph_catalog = service_graph_catalog(graph_context)
        with service_api_trace_phase(
            "graph_context.resolve_graph_function_target",
            **trace_fields,
        ):
            resolved_target = resolve_service_api_graph_function_target(
                graph_context=graph_context,
                graph_function_runtime_target=binding.graph_function_runtime_target,
                execution_label="Service graph gateway execution",
            )
        invoke_request = await await_with_service_api_trace(
            _build_invoke_function_request(
                execution_plan=self.execution_plan,
                binding=binding,
                request=request,
                operation_context=self.operation_context,
                graph_context=graph_context,
            ),
            phase="graph_gateway.build_invoke_function_request",
            fields=trace_fields,
        )
        response = await await_with_service_api_trace(
            self.graph_gateway.invoke_function(
                request=invoke_request,
                graph_context=graph_context,
            ),
            phase="graph_gateway.invoke_function",
            fields=trace_fields,
            call_target=invoke_request.call_target.value,
            branch_id=str(invoke_request.domain_branch_id),
            projection_hash=invoke_request.domain_projection_hash,
            object_id=str(invoke_request.target_object_id),
            function_id=str(invoke_request.function_id),
        )
        status = str(response.status).strip().lower()
        if status != "succeeded":
            raise RuntimeError(
                "Service graph gateway execution failed for validated fulfillment binding: "
                f"endpoint_ref={self.execution_plan.endpoint_ref!r} "
                f"fulfillment_name={binding.name!r} "
                f"graph_function_runtime_target={binding.graph_function_runtime_target!r} "
                f"status={response.status!r} error={response.error!r}"
            )
        exact_output_field_name = _resolve_binding_exact_output_field_name(
            binding=binding,
            resolved_target=resolved_target,
        )
        instance_target_plan = binding.instance_target_plan
        if (
            exact_output_field_name is not None
            and invoke_request.call_target
            is MetaGraphFunctionCallTarget.opg_constructor
        ):
            constructor_object_id = _resolve_constructor_output_object_id(
                root_object_id=response.root_object_id,
                payload=response.payload,
            )
            constructor_projection_hash = (
                response.domain_projection_hash or invoke_request.domain_projection_hash
            )
            if constructor_object_id is not None:
                if not constructor_projection_hash:
                    raise RuntimeError(
                        "Service graph gateway execution could not resolve committed constructor projection hash "
                        "for exact output hydration: "
                        f"endpoint_ref={self.execution_plan.endpoint_ref!r} "
                        f"fulfillment_name={binding.name!r}"
                    )
                exact_output = await await_with_service_api_trace(
                    _hydrate_exact_instance_output_orm_model(
                        graph_catalog=graph_catalog,
                        branch_id=response.domain_branch_id
                        or self.operation_context.branch_id,
                        projection_hash=constructor_projection_hash,
                        object_id=constructor_object_id,
                        resolved_target=resolved_target,
                        execution_plan=self.execution_plan,
                        binding=binding,
                    ),
                    phase="graph_gateway.hydrate_constructor_exact_output",
                    fields=trace_fields,
                    object_id=str(constructor_object_id),
                    projection_hash=constructor_projection_hash,
                )
                return {exact_output_field_name: exact_output}
        if (
            exact_output_field_name is not None
            and invoke_request.call_target is MetaGraphFunctionCallTarget.instance
            and invoke_request.target_object_id is not None
            and instance_target_plan is not None
        ):
            exact_output = await await_with_service_api_trace(
                _hydrate_exact_instance_output_orm_model(
                    graph_catalog=graph_catalog,
                    branch_id=self.operation_context.branch_id,
                    projection_hash=instance_target_plan.projection_hash,
                    object_id=invoke_request.target_object_id,
                    resolved_target=resolved_target,
                    execution_plan=self.execution_plan,
                    binding=binding,
                ),
                phase="graph_gateway.hydrate_instance_exact_output",
                fields=trace_fields,
                object_id=str(invoke_request.target_object_id),
                projection_hash=instance_target_plan.projection_hash,
            )
            return {exact_output_field_name: exact_output}
        if (
            invoke_request.call_target is MetaGraphFunctionCallTarget.instance
            and invoke_request.target_object_id is not None
            and instance_target_plan is not None
            and _is_minimal_same_instance_receipt(
                payload=response.payload,
                object_id=invoke_request.target_object_id,
            )
        ):
            exact_output = await await_with_service_api_trace(
                _hydrate_committed_instance_receipt_output(
                    graph_catalog=graph_catalog,
                    branch_id=self.operation_context.branch_id,
                    projection_hash=instance_target_plan.projection_hash,
                    object_id=invoke_request.target_object_id,
                    execution_plan=self.execution_plan,
                    binding=binding,
                ),
                phase="graph_gateway.hydrate_committed_instance_receipt_output",
                fields=trace_fields,
                object_id=str(invoke_request.target_object_id),
                projection_hash=instance_target_plan.projection_hash,
            )
            return exact_output
        if response.payload is None:
            return {}
        return response.payload


def build_gateway_service_api_execution_backend(
    *,
    execution_plan: ServiceApiGraphExecutionPlan,
    graph_context: ServiceGraphContextLike,
    graph_gateway: ServiceGraphGateway,
    operation_context: ServiceOperationContext,
) -> GatewayBackedServiceApiExecutionBackend:
    return GatewayBackedServiceApiExecutionBackend(
        execution_plan=execution_plan,
        graph_context=graph_context,
        graph_gateway=graph_gateway,
        operation_context=operation_context,
    )


async def _build_invoke_function_request(
    *,
    execution_plan: ServiceApiGraphExecutionPlan,
    binding: ServiceApiGraphExecutionBinding,
    request: object,
    operation_context: ServiceOperationContext,
    graph_context: ServiceGraphContextLike,
) -> MetaGraphInvokeFunctionRequest:
    request_kwargs = _encode_request_kwargs(request=request)
    resolved_target = resolve_service_api_graph_function_target(
        graph_context=graph_context,
        graph_function_runtime_target=binding.graph_function_runtime_target,
        execution_label="Service graph gateway execution",
    )
    actor_id = _require_actor_id(
        actor_id=operation_context.actor_id,
        endpoint_ref=execution_plan.endpoint_ref,
        fulfillment_name=binding.name,
    )
    if _binding_declares_constructor(
        binding=binding,
        resolved_target=resolved_target,
    ):
        projection = resolve_service_api_constructor_projection(
            graph_context=graph_context,
            class_config_id=resolved_target.class_config.id,
            function_constructor_link_id=resolved_target.function_link.id,
            graph_function_runtime_target=binding.graph_function_runtime_target,
            execution_label="Service graph gateway execution",
            allow_class_only_fallback=(
                (binding.call_target_kind or "").strip().casefold() == "constructor"
            ),
        )
        return MetaGraphInvokeFunctionRequest(
            actor_id=actor_id,
            domain_branch_id=None,
            domain_projection_hash=projection.projection_hash,
            call_target=MetaGraphFunctionCallTarget.opg_constructor,
            target_object_id=None,
            object_projection_graph_id=projection.id,
            function_id=resolved_target.function_config.id,
            args=cast(JsonArray, []),
            kwargs=cast(JsonObject, request_kwargs),
            commit=True,
            publish=False,
        )

    if (binding.call_target_kind or "").strip().casefold() == "opg_read" or (
        resolved_target.function_config.verb or ""
    ).strip().casefold() == "read":
        raise RuntimeError(
            "Service graph gateway no longer invokes ontology projection reads. "
            "Expose this endpoint through a service-owned view/read model instead: "
            f"endpoint_ref={execution_plan.endpoint_ref!r} "
            f"fulfillment_name={binding.name!r} "
            f"graph_function_runtime_target={binding.graph_function_runtime_target!r}"
        )

    instance_target_plan = binding.instance_target_plan
    if instance_target_plan is None:
        raise RuntimeError(
            "Service graph gateway execution cannot invoke instance targets yet because concrete "
            "lane/object identity is not resolved on this API-Service boundary: "
            f"endpoint_ref={execution_plan.endpoint_ref!r} "
            f"fulfillment_name={binding.name!r} "
            f"graph_function_runtime_target={binding.graph_function_runtime_target!r}"
        )
    from aware_api_runtime.service_protocol import (
        resolve_api_service_instance_target_object_id,
    )

    object_id = await resolve_api_service_instance_target_object_id(
        index=service_graph_catalog(graph_context),
        branch_id=operation_context.branch_id,
        instance_target_plan=instance_target_plan,
    )
    return MetaGraphInvokeFunctionRequest(
        actor_id=actor_id,
        domain_branch_id=operation_context.branch_id,
        domain_projection_hash=instance_target_plan.projection_hash,
        call_target=MetaGraphFunctionCallTarget.instance,
        target_object_id=object_id,
        object_projection_graph_id=None,
        function_id=resolved_target.function_config.id,
        args=cast(JsonArray, []),
        kwargs=cast(JsonObject, request_kwargs),
        commit=True,
        publish=False,
    )


def _require_actor_id(
    *,
    actor_id: UUID | None,
    endpoint_ref: str,
    fulfillment_name: str,
) -> UUID:
    if actor_id is None:
        raise RuntimeError(
            "Service graph gateway execution requires actor_id for committing "
            "MetaGraph function invocation: "
            f"endpoint_ref={endpoint_ref!r} fulfillment_name={fulfillment_name!r}"
        )
    return actor_id


def _encode_request_kwargs(*, request: object) -> dict[str, object]:
    if isinstance(request, BaseModel):
        encoded = request.model_dump(mode="json")
        return dict(encoded)
    raise TypeError(
        "Service graph gateway execution requires a typed BaseModel request object from the "
        "compiled service protocol."
    )


def _resolve_execution_binding(
    *,
    execution_plan: ServiceApiGraphExecutionPlan,
    fulfillment_name: str,
) -> ServiceApiGraphExecutionBinding:
    return resolve_service_api_execution_binding(
        execution_plan=execution_plan,
        fulfillment_name=fulfillment_name,
        execution_label="Service graph gateway execution",
    )


def _binding_declares_constructor(
    *,
    binding: ServiceApiGraphExecutionBinding,
    resolved_target: ResolvedServiceApiGraphFunctionTarget,
) -> bool:
    call_target_kind = (binding.call_target_kind or "").strip().casefold()
    if call_target_kind == "constructor":
        return True
    if call_target_kind == "instance":
        return False
    return bool(resolved_target.function_link.is_constructor)


def _resolve_binding_exact_output_field_name(
    *,
    binding: ServiceApiGraphExecutionBinding,
    resolved_target: ResolvedServiceApiGraphFunctionTarget,
) -> str | None:
    exact_output_field_name = (binding.exact_output_field_name or "").strip()
    if exact_output_field_name:
        return exact_output_field_name
    return _resolve_exact_instance_output_field_name(
        resolved_target=resolved_target,
    )


def _resolve_exact_instance_output_field_name(
    *,
    resolved_target: ResolvedServiceApiGraphFunctionTarget,
) -> str | None:
    output_edges = sorted(
        (
            edge
            for edge in resolved_target.function_config.function_config_attribute_configs
            if _field_binding_role(edge) == "output"
            and edge.attribute_config is not None
        ),
        key=lambda item: (item.position, str(item.id)),
    )
    if len(output_edges) != 1:
        return None
    output_attr = output_edges[0].attribute_config
    if output_attr is None or not (output_attr.name or "").strip():
        return None
    value_type = getattr(output_attr, "value_type", None)
    if value_type is None or bool(getattr(value_type, "is_collection", False)):
        return None
    output_class_config_id = getattr(value_type, "entity_id", None)
    if output_class_config_id is None:
        return None
    if output_class_config_id != resolved_target.class_config.id:
        return None
    return str(output_attr.name).strip()


def _field_binding_role(edge: object) -> str:
    return str(getattr(edge, "binding_role", "") or "").rsplit(".", 1)[-1].casefold()


def _resolve_constructor_output_object_id(
    *,
    root_object_id: UUID | None,
    payload: object,
) -> UUID | None:
    if root_object_id is not None:
        return root_object_id
    return _extract_payload_object_id(payload=payload)


def _extract_payload_object_id(*, payload: object) -> UUID | None:
    if isinstance(payload, Mapping):
        payload_map = cast(Mapping[object, object], payload)
        raw_id = payload_map.get("id")
        if raw_id is not None:
            try:
                return UUID(str(raw_id))
            except Exception:
                pass
        if set(str(key) for key in payload_map.keys()) == {"value"}:
            return _extract_payload_object_id(payload=payload_map.get("value"))
    return None


async def _hydrate_exact_instance_output_orm_model(
    *,
    graph_catalog: ServiceGraphCatalog,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    resolved_target: ResolvedServiceApiGraphFunctionTarget,
    execution_plan: ServiceApiGraphExecutionPlan,
    binding: ServiceApiGraphExecutionBinding,
) -> ORMModel:
    orm_class = ORMModelRegistry.get_class_by_class_config_id(
        resolved_target.class_config.id
    )
    if orm_class is None or not issubclass(orm_class, ORMModel):
        raise RuntimeError(
            "Service graph gateway execution could not resolve ORM class for exact instance output: "
            f"class_config_id={resolved_target.class_config.id}"
        )
    orm_model = await _hydrate_committed_projection_model(
        graph_catalog=graph_catalog,
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_id=object_id,
        model_type=cast(type[ORMModel], orm_class),
        error_context="Service graph gateway execution",
    )
    return cast(ORMModel, orm_model)


async def _hydrate_committed_instance_receipt_output(
    *,
    graph_catalog: ServiceGraphCatalog,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    execution_plan: ServiceApiGraphExecutionPlan,
    binding: ServiceApiGraphExecutionBinding,
) -> ORMModel:
    orm_model = await _hydrate_committed_projection_model(
        graph_catalog=graph_catalog,
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_id=object_id,
        model_type=None,
        error_context="Service graph gateway execution",
    )
    _ = execution_plan
    _ = binding
    return orm_model


async def _hydrate_committed_projection_model(
    *,
    graph_catalog: ServiceGraphCatalog,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    model_type: type[ORMModel] | None,
    error_context: str,
) -> ORMModel:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(f"{error_context} requires a committed target lane head.")

    opg = graph_catalog.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} could not resolve projection hash {projection_hash!r}."
        )

    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=graph_catalog.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=graph_catalog.attribute_configs_by_id,
        class_configs_by_id=graph_catalog.class_configs_by_id,
    )
    resolved_model_type = model_type or _resolve_oig_model_type_by_source_object_id(
        graph_catalog=graph_catalog,
        oig=target_oig,
        object_id=object_id,
        error_context=error_context,
    )
    orm_model = reify_oig_root_model(
        index=cast(MetaGraphRuntimeIndex, cast(object, graph_catalog)),
        opg=opg,
        oig=target_oig,
        model_type=resolved_model_type,
        root_id=object_id,
        branch_id=branch_id,
    )
    if orm_model is None:
        raise RuntimeError(
            f"{error_context} could not hydrate committed target object: "
            f"projection_hash={projection_hash!r} object_id={object_id}"
        )
    return orm_model


def _resolve_oig_model_type_by_source_object_id(
    *,
    graph_catalog: ServiceGraphCatalog,
    oig: object,
    object_id: UUID,
    error_context: str,
) -> type[ORMModel]:
    for class_instance in tuple(getattr(oig, "class_instances", ()) or ()):
        if getattr(class_instance, "source_object_id", None) != object_id:
            continue
        orm_class = ORMModelRegistry.get_class_by_class_config_id(
            getattr(class_instance, "class_config_id", None)
        )
        if orm_class is None or not issubclass(orm_class, ORMModel):
            raise RuntimeError(
                f"{error_context} could not resolve ORM class for committed target object: "
                f"class_config_id={getattr(class_instance, 'class_config_id', None)}"
            )
        return cast(type[ORMModel], orm_class)
    raise RuntimeError(
        f"{error_context} could not resolve committed target object in OIG: "
        f"object_id={object_id} object_config_graph_id={graph_catalog.ocg.id}"
    )


def _is_minimal_same_instance_receipt(
    *,
    payload: object,
    object_id: UUID,
) -> bool:
    if _is_minimal_same_instance_payload(
        payload=payload,
        object_id=object_id,
    ):
        return True
    if not isinstance(payload, Mapping):
        return False
    payload_map = cast(Mapping[object, object], payload)
    if set(str(key) for key in payload_map.keys()) != {"value"}:
        return False
    return _is_minimal_same_instance_payload(
        payload=payload_map.get("value"),
        object_id=object_id,
    )


def _is_minimal_same_instance_payload(
    *,
    payload: object,
    object_id: UUID,
) -> bool:
    if not isinstance(payload, Mapping):
        return False
    payload_map = cast(Mapping[object, object], payload)
    raw_id = payload_map.get("id")
    if raw_id is None:
        return False
    try:
        payload_id = UUID(str(raw_id))
    except Exception:
        return False
    return payload_id == object_id and set(str(key) for key in payload_map.keys()) == {
        "id"
    }


__all__ = [
    "GatewayBackedServiceApiExecutionBackend",
    "build_gateway_service_api_execution_backend",
]
