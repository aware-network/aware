from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aware_meta_service_dto.graph.view.graph_view import (
    MetaGraphCanvasViewStateV1,
    MetaGraphResolveGraphViewResponse,
    MetaGraphSnapshot,
    MetaGraphViewRef,
    MetaGraphViewportStateV1,
)
from aware_service_runtime.api_ingress.view_fulfillment import (
    ServiceApiViewFulfillmentPlan,
)

META_GRAPH_CANVAS_PROVIDER_REF = (
    "aware_meta_service.view_state_providers.meta_graph_canvas_view_state"
)
META_GRAPH_CANVAS_API_VIEW_REF = "meta.graph_canvas"
META_GRAPH_CANVAS_PROJECTION_VIEW_KEY = "graph.canvas.v1"
META_GRAPH_CANVAS_STATE_MODEL_REF = (
    "aware_meta_service_dto.graph.view.MetaGraphCanvasViewStateV1"
)


class MetaGraphCanvasServiceFulfillmentEvidenceV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_kind: str = Field(default="meta_service")
    service_id: str | None = Field(default=None)
    api_view_id: str | None = Field(default=None)
    service_operation_config_api_view_id: str | None = Field(default=None)
    service_operation_config_id: str | None = Field(default=None)
    service_config_api_id: str | None = Field(default=None)
    service_contract_config_id: str | None = Field(default=None)
    service_contract_config_operation_grant_id: str | None = Field(default=None)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class MetaGraphCanvasV1ServiceProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    response: MetaGraphResolveGraphViewResponse | Mapping[str, Any] | None = None
    selected_identity: str | None = Field(default=None)
    viewport_state: MetaGraphViewportStateV1 | Mapping[str, Any] | None = None
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    fulfillment: MetaGraphCanvasServiceFulfillmentEvidenceV1 | Mapping[str, Any] = (
        Field(default_factory=MetaGraphCanvasServiceFulfillmentEvidenceV1)
    )
    provenance: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


def meta_graph_canvas_v1_provider_input(
    provider_context: object,
) -> MetaGraphCanvasV1ServiceProviderInput:
    assets = getattr(provider_context, "assets", None)
    response = (
        _context_value(provider_context, "response", "graph_response")
        or _context_value(assets, "response", "graph_response")
        or _context_value(
            assets,
            "meta_graph_response",
            "resolve_graph_view_response",
            "graph_view_response",
        )
        or _context_value(provider_context, "result")
    )
    return MetaGraphCanvasV1ServiceProviderInput(
        response=response,
        selected_identity=_optional_text(
            _context_value(provider_context, "selected_identity")
            or _context_value(assets, "selected_identity")
        ),
        viewport_state=(
            _context_value(provider_context, "viewport_state")
            or _context_value(assets, "viewport_state")
        ),
        summary=_optional_text(
            _context_value(provider_context, "summary")
            or _context_value(assets, "summary")
        ),
        error=_optional_text(
            _context_value(provider_context, "error") or _context_value(assets, "error")
        ),
        provenance={
            **_mapping_payload(getattr(provider_context, "provenance", None)),
            **_mapping_payload(_context_value(assets, "provenance")),
        },
    )


def meta_graph_canvas_view_state_from_response(
    response: MetaGraphResolveGraphViewResponse | Mapping[str, Any] | None,
    *,
    selected_identity: str | UUID | None = None,
    viewport_state: MetaGraphViewportStateV1 | Mapping[str, Any] | None = None,
    fulfillment_plan: ServiceApiViewFulfillmentPlan | None = None,
    fulfillment: (
        MetaGraphCanvasServiceFulfillmentEvidenceV1 | Mapping[str, Any] | None
    ) = None,
    summary: str | None = None,
    error: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> MetaGraphCanvasViewStateV1:
    if fulfillment_plan is not None and fulfillment is not None:
        raise ValueError("Pass either fulfillment_plan or fulfillment, not both.")
    return meta_graph_canvas_view_state_from_input(
        MetaGraphCanvasV1ServiceProviderInput(
            response=response,
            selected_identity=_optional_text(selected_identity),
            viewport_state=viewport_state,
            summary=summary,
            error=error,
            fulfillment=(
                _fulfillment_evidence_from_plan(fulfillment_plan)
                if fulfillment_plan is not None
                else _fulfillment_evidence(fulfillment)
            ),
            provenance=dict(provenance or {}),
        )
    )


def meta_graph_canvas_view_state_from_input(
    provider_input: MetaGraphCanvasV1ServiceProviderInput | Mapping[str, Any],
) -> MetaGraphCanvasViewStateV1:
    typed_input = MetaGraphCanvasV1ServiceProviderInput.model_validate(provider_input)
    response = _typed_response(typed_input.response)
    graph_snapshot = _snapshot_from_response(response)
    status = _state_status(response=response, error=typed_input.error)
    return MetaGraphCanvasViewStateV1(
        status=status,
        object_config_graph_ref=_ref_from_response(response, "object_config_graph_ref"),
        object_projection_graph_ref=_ref_from_response(
            response, "object_projection_graph_ref"
        ),
        object_instance_graph_ref=_ref_from_response(
            response, "object_instance_graph_ref"
        ),
        object_instance_graph_branch_ref=_ref_from_response(
            response, "object_instance_graph_branch_ref"
        ),
        object_instance_graph_commit_ref=_ref_from_response(
            response, "object_instance_graph_commit_ref"
        ),
        graph_snapshot=graph_snapshot,
        selected_identity=typed_input.selected_identity,
        viewport_state=_typed_viewport(typed_input.viewport_state),
        summary=(
            typed_input.summary
            or _optional_text(getattr(response, "summary", None))
            or graph_snapshot.summary
            or _summary(graph_snapshot=graph_snapshot)
        ),
        error=typed_input.error or _optional_text(getattr(response, "error", None)),
        provenance=_provenance_payload(
            typed_input=typed_input,
            response=response,
            graph_snapshot=graph_snapshot,
        ),
    )


def meta_graph_canvas_view_state(
    *,
    provider_input: MetaGraphCanvasV1ServiceProviderInput | Mapping[str, Any],
) -> MetaGraphCanvasViewStateV1:
    return meta_graph_canvas_view_state_from_input(provider_input)


setattr(
    meta_graph_canvas_view_state,
    "provider_input_resolver",
    meta_graph_canvas_v1_provider_input,
)


def _typed_response(
    value: MetaGraphResolveGraphViewResponse | Mapping[str, Any] | None,
) -> MetaGraphResolveGraphViewResponse | None:
    if value is None:
        return None
    if isinstance(value, MetaGraphResolveGraphViewResponse):
        return value
    if isinstance(value, Mapping):
        return MetaGraphResolveGraphViewResponse.model_validate(value)
    return None


def _snapshot_from_response(
    response: MetaGraphResolveGraphViewResponse | None,
) -> MetaGraphSnapshot:
    if response is None:
        return MetaGraphSnapshot()
    return MetaGraphSnapshot.model_validate(
        _model_payload(response.graph_snapshot) or {}
    )


def _ref_from_response(
    response: MetaGraphResolveGraphViewResponse | None,
    attr: str,
) -> MetaGraphViewRef | None:
    if response is None:
        return None
    payload = _model_payload(getattr(response, attr, None))
    if payload is None:
        return None
    return MetaGraphViewRef.model_validate(payload)


def _typed_viewport(
    value: MetaGraphViewportStateV1 | Mapping[str, Any] | None,
) -> MetaGraphViewportStateV1:
    if isinstance(value, MetaGraphViewportStateV1):
        return value
    if isinstance(value, Mapping):
        return MetaGraphViewportStateV1.model_validate(value)
    return MetaGraphViewportStateV1()


def _state_status(
    *,
    response: MetaGraphResolveGraphViewResponse | None,
    error: str | None,
) -> str:
    if error:
        return "error"
    if response is None:
        return "waiting"
    response_error = _optional_text(getattr(response, "error", None))
    response_status = _optional_text(getattr(response, "status", None)) or ""
    normalized_status = response_status.casefold()
    if response_error or normalized_status in {
        "failed",
        "invalid_request",
        "missing",
        "not_found",
    }:
        return "error"
    if normalized_status == "empty":
        return "empty"
    if normalized_status in {"succeeded", "ready"}:
        snapshot = _snapshot_from_response(response)
        return "ready" if snapshot.nodes or snapshot.edges else "empty"
    return normalized_status or "waiting"


def _fulfillment_evidence(
    value: MetaGraphCanvasServiceFulfillmentEvidenceV1 | Mapping[str, Any] | None,
) -> MetaGraphCanvasServiceFulfillmentEvidenceV1:
    if isinstance(value, MetaGraphCanvasServiceFulfillmentEvidenceV1):
        return value
    return MetaGraphCanvasServiceFulfillmentEvidenceV1.model_validate(value or {})


def _fulfillment_evidence_from_plan(
    plan: ServiceApiViewFulfillmentPlan,
) -> MetaGraphCanvasServiceFulfillmentEvidenceV1:
    access_evidence = plan.preflight.access_evidence
    return MetaGraphCanvasServiceFulfillmentEvidenceV1(
        service_id=_uuid_text(plan.service_id),
        api_view_id=_uuid_text(plan.api_view_id),
        service_operation_config_api_view_id=_uuid_text(
            plan.service_operation_config_api_view_id
        ),
        service_operation_config_id=_uuid_text(plan.service_operation_config_id),
        service_config_api_id=_uuid_text(plan.service_config_api_id),
        service_contract_config_id=(
            _uuid_text(access_evidence.service_contract_config_id)
            if access_evidence is not None
            else None
        ),
        service_contract_config_operation_grant_id=(
            _uuid_text(access_evidence.service_contract_config_operation_grant_id)
            if access_evidence is not None
            else None
        ),
    )


def _provenance_payload(
    *,
    typed_input: MetaGraphCanvasV1ServiceProviderInput,
    response: MetaGraphResolveGraphViewResponse | None,
    graph_snapshot: MetaGraphSnapshot,
) -> dict[str, Any]:
    payload = {
        "source_kind": "meta_service",
        "state_provider_ref": META_GRAPH_CANVAS_PROVIDER_REF,
        "api_view_ref": META_GRAPH_CANVAS_API_VIEW_REF,
        "view_ref": META_GRAPH_CANVAS_API_VIEW_REF,
        "projection_view_key": META_GRAPH_CANVAS_PROJECTION_VIEW_KEY,
        "state_model_ref": META_GRAPH_CANVAS_STATE_MODEL_REF,
        **_fulfillment_evidence(typed_input.fulfillment).to_json(),
        **_response_provenance(response),
        **typed_input.provenance,
    }
    payload["node_count"] = len(graph_snapshot.nodes)
    payload["edge_count"] = len(graph_snapshot.edges)
    return {key: value for key, value in payload.items() if value is not None}


def _response_provenance(
    response: MetaGraphResolveGraphViewResponse | None,
) -> dict[str, Any]:
    if response is None:
        return {}
    payload = _mapping_payload(getattr(response, "provenance", None))
    payload.update(
        {
            "meta_branch_id": _uuid_text(response.domain_branch_id),
            "meta_projection_hash": response.domain_projection_hash,
            "meta_commit_id": _uuid_text(response.domain_commit_id),
            "object_instance_graph_commit_id": _uuid_text(
                response.object_instance_graph_commit_id
            ),
            "object_instance_graph_id": _uuid_text(response.object_instance_graph_id),
            "object_instance_graph_identity_id": _uuid_text(
                response.object_instance_graph_identity_id
            ),
            "object_instance_graph_branch_id": _uuid_text(
                response.object_instance_graph_branch_id
            ),
        }
    )
    return payload


def _summary(*, graph_snapshot: MetaGraphSnapshot) -> str:
    node_count = len(graph_snapshot.nodes)
    edge_count = len(graph_snapshot.edges)
    if node_count or edge_count:
        return f"{node_count} Meta graph nodes, {edge_count} edges"
    return "No Meta graph snapshot available"


def _model_payload(value: object) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
        return dict(payload) if isinstance(payload, Mapping) else None
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _mapping_payload(value: object) -> dict[str, Any]:
    payload = _model_payload(value)
    return payload or {}


def _context_value(source: object, *names: str) -> object | None:
    if source is None:
        return None
    if isinstance(source, Mapping):
        for name in names:
            if name in source:
                return source[name]
        return None
    for name in names:
        value = getattr(source, name, None)
        if value is not None:
            return value
    return None


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "META_GRAPH_CANVAS_PROVIDER_REF",
    "META_GRAPH_CANVAS_API_VIEW_REF",
    "META_GRAPH_CANVAS_PROJECTION_VIEW_KEY",
    "META_GRAPH_CANVAS_STATE_MODEL_REF",
    "MetaGraphCanvasServiceFulfillmentEvidenceV1",
    "MetaGraphCanvasV1ServiceProviderInput",
    "meta_graph_canvas_v1_provider_input",
    "meta_graph_canvas_view_state",
    "meta_graph_canvas_view_state_from_input",
    "meta_graph_canvas_view_state_from_response",
]
