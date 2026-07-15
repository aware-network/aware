from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_runtime.invocation import (
    ApiInvocationIR,
    ApiInvocationRuntimeProtocol,
    ApiInvocationSourceCommit,
    dispatch_api_invocation,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_orm.session.session import Session

from ._meta_hydration import hydrate_committed_lane_session, hydrate_oig_commit_session
from .models import (
    ResolvedSkillExecutionStep,
    SkillStepApiCallInput,
    SkillStepApiCallMaterialization,
)


_TApiOrm = TypeVar("_TApiOrm", Api, ApiCapability, ApiCapabilityEndpoint)


@dataclass(frozen=True, slots=True)
class _ResolvedEndpointInvocationContract:
    api_name: str
    request_class_config_id: UUID
    request_class_ref: str
    request_source_path: str


async def materialize_skill_step_api_call(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    api_source_lane: MaterializationLaneContext,
    api_call_lane: MaterializationLaneContext,
    step: ResolvedSkillExecutionStep,
    step_input: SkillStepApiCallInput,
    api_source_commit: ApiInvocationSourceCommit | None = None,
    commit: bool = True,
    publish: bool = False,
) -> SkillStepApiCallMaterialization:
    if step_input.skill_config_step_id != step.skill_config_step_id:
        raise RuntimeError(
            "Skill step API call input does not match planned SkillConfigStep: "
            f"input_step_id={step_input.skill_config_step_id} "
            f"planned_step_id={step.skill_config_step_id}"
        )

    contract = await _resolve_endpoint_invocation_contract(
        index=index,
        api_source_lane=api_source_lane,
        step=step,
        api_source_commit=api_source_commit,
    )
    ir = ApiInvocationIR(
        api_name=contract.api_name,
        capability_name=step.capability_name,
        endpoint_name=step.endpoint_requirement_name,
        endpoint_ref=".".join(
            (contract.api_name, step.capability_name, step.endpoint_requirement_name)
        ),
        discriminant=".".join(
            (contract.api_name, step.capability_name, step.endpoint_requirement_name)
        ),
        source_path=f"skill_config_step:{step.skill_config_step_id}",
        request_payload=step_input.request_payload,
        request_class_ref=contract.request_class_ref,
        request_class_config_id=contract.request_class_config_id,
        request_source_path=contract.request_source_path,
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(),
        description=step_input.description,
        api_capability_endpoint_id=step.api_capability_endpoint_id,
    )
    dispatched_invocation = await dispatch_api_invocation(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        source_lane=api_source_lane,
        target_lane=api_call_lane,
        ir=ir,
        source_commit=api_source_commit,
        call_key=step_input.call_key,
        commit=commit,
        publish=publish,
    )
    envelope = dispatched_invocation.envelope
    if envelope.api_capability_endpoint_id != step.api_capability_endpoint_id:
        raise RuntimeError(
            "Skill step materialized ApiCall for the wrong API endpoint: "
            f"step_endpoint_id={step.api_capability_endpoint_id} "
            f"api_call_endpoint_id={envelope.api_capability_endpoint_id}"
        )
    return SkillStepApiCallMaterialization(
        skill_config_step_id=step.skill_config_step_id,
        api_call_id=envelope.api_call_id,
        api_capability_endpoint_id=envelope.api_capability_endpoint_id,
        call_key=envelope.call_key,
        request_hash=envelope.request_hash,
        request_model_id=envelope.request_model_id,
        request_class_config_id=envelope.request_class_config_id,
        branch_id=envelope.branch_id,
        projection_hash=envelope.projection_hash,
        commit_id=envelope.commit_id,
        head_commit_id=envelope.head_commit_id,
    )


async def _resolve_endpoint_invocation_contract(
    *,
    index: MetaGraphRuntimeIndex,
    api_source_lane: MaterializationLaneContext,
    step: ResolvedSkillExecutionStep,
    api_source_commit: ApiInvocationSourceCommit | None = None,
) -> _ResolvedEndpointInvocationContract:
    session = (
        await _hydrate_api_source_commit_session(
            index=index,
            api_source_commit=api_source_commit,
        )
        if api_source_commit is not None
        else await hydrate_committed_lane_session(
            index=index,
            lane=api_source_lane,
            error_context="Skill API call materialization",
        )
    )
    endpoint = _required_imap(
        session=session,
        orm_class=ApiCapabilityEndpoint,
        object_id=step.api_capability_endpoint_id,
        context="Skill API call materialization endpoint",
    )
    if (endpoint.name or "").strip() != step.endpoint_requirement_name:
        raise RuntimeError(
            "Skill API call materialization resolved endpoint name mismatch: "
            f"step_name={step.endpoint_requirement_name!r} endpoint_name={endpoint.name!r}"
        )

    capability = _required_imap(
        session=session,
        orm_class=ApiCapability,
        object_id=endpoint.api_capability_id,
        context="Skill API call materialization capability",
    )
    if (capability.name or "").strip() != step.capability_name:
        raise RuntimeError(
            "Skill API call materialization resolved capability name mismatch: "
            f"step_capability={step.capability_name!r} api_capability={capability.name!r}"
        )

    api = _required_imap(
        session=session,
        orm_class=Api,
        object_id=capability.api_id,
        context="Skill API call materialization API",
    )
    request_config = _resolve_endpoint_request_config(
        session=session, endpoint=endpoint
    )
    class_config_id = request_config.class_config_id
    class_config = index.class_configs_by_id.get(class_config_id)
    class_ref = (
        (class_config.class_fqn or "").strip()
        if class_config is not None and class_config.class_fqn is not None
        else ""
    )
    if not class_ref:
        class_ref = f"class_config:{class_config_id}"
    return _ResolvedEndpointInvocationContract(
        api_name=(api.name or "").strip(),
        request_class_config_id=class_config_id,
        request_class_ref=class_ref,
        request_source_path=f"api_endpoint:{endpoint.id}:request_config:{request_config.id}",
    )


async def _hydrate_api_source_commit_session(
    *,
    index: MetaGraphRuntimeIndex,
    api_source_commit: ApiInvocationSourceCommit,
) -> Session:
    return await hydrate_oig_commit_session(
        index=index,
        branch_id=api_source_commit.branch_id,
        projection_hash=api_source_commit.projection_hash,
        commit_id=api_source_commit.commit_id,
        object_instance_graph_id=api_source_commit.object_instance_graph_id,
        error_context="Skill API call materialization",
    )


def _resolve_endpoint_request_config(
    *,
    session: Session,
    endpoint: ApiCapabilityEndpoint,
) -> ApiCapabilityEndpointRequestConfig:
    request_config = endpoint.request_config
    if isinstance(request_config, ApiCapabilityEndpointRequestConfig):
        return request_config
    matches = [
        obj
        for obj in session.imap_all_objects()
        if isinstance(obj, ApiCapabilityEndpointRequestConfig)
        and obj.api_capability_endpoint_id == endpoint.id
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Skill API call materialization requires one committed endpoint request config: "
            f"endpoint_id={endpoint.id} found={len(matches)}"
        )
    return matches[0]


def _required_imap(
    *,
    session: Session,
    orm_class: type[_TApiOrm],
    object_id: UUID,
    context: str,
) -> _TApiOrm:
    obj = session.imap_get(orm_class, object_id)
    if obj is None:
        raise RuntimeError(
            f"{context} could not resolve {orm_class.__name__} {object_id}."
        )
    return obj


__all__ = ["materialize_skill_step_api_call"]
