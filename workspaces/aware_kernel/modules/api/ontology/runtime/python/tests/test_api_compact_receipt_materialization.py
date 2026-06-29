from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from aware_api_ontology.api.api_call import ApiCall
from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
from aware_api_ontology.api.api_call_outcome import ApiCallOutcome
from aware_api_ontology.stable_ids import stable_api_call_id
from aware_api_runtime.invocation import resolve_api_invocation_ir
from aware_api_runtime.models import (
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.invocation.materialization.context import (
    current_api_call_materialization_input,
    current_api_call_outcome_materialization_input,
)
from aware_api_runtime.request_hash import compute_api_request_hash_from_mapping
from aware_meta.materialization import MaterializationLaneContext
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id


def _api_ownership_for_runtime(*, request_class_ref: str) -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name="workspace",
            source_path="runtime-proof",
            capabilities=(
                APICapabilityOwnership(
                    name="materialize",
                    source_path="runtime-proof",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="materialize",
                            source_path="runtime-proof",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref=request_class_ref,
                                source_path="runtime-proof",
                            ),
                        ),
                    ),
                ),
            ),
            graphs=(),
        ),
    )


def _lane(
    *, projection_hash: str = "api-call-projection"
) -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash=projection_hash,
    )


class _HeadlessStore:
    async def head(self, **_: object) -> None:
        return None


class _RuntimeLane:
    def __init__(self) -> None:
        self.last_commit_id = uuid4()
        self.last_head_commit_id = uuid4()

    def activate(self, *, commit: bool, publish: bool) -> object:
        assert commit is True
        assert publish is False

        class _Activation:
            def __enter__(self) -> None:
                return None

            def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
                return False

        return _Activation()


class _Runtime:
    def __init__(self) -> None:
        self.lane = _RuntimeLane()

    def bind(self, **_: object) -> _RuntimeLane:
        return self.lane


class _FakeHandlerSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def imap_get(self, *_: object) -> None:
        return None

    def imap_add(self, value: object) -> None:
        self.added.append(value)


@pytest.mark.asyncio
async def test_compact_api_call_receipt_hashes_nested_payload_without_graph_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    request_class_config = ClassConfig.model_construct(
        id=uuid4(),
        name="WorkspaceMaterializeRequest",
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
    )
    endpoint_id = uuid4()
    captured: dict[str, object] = {}

    async def _resolve_contract(**_: object) -> object:
        return call_mod._ResolvedApiEndpointRequestContract(
            endpoint_id=endpoint_id,
            request_class_config=request_class_config,
            fulfillment_bindings=(),
            endpoint=None,
        )

    async def _create_api_call(
        *,
        api_capability_endpoint_id: UUID,
        call_key: UUID,
        request_class_config_id: UUID,
        description: str | None = None,
    ) -> ApiCall:
        materialization_input = current_api_call_materialization_input()
        assert materialization_input is not None
        captured["request_payload"] = dict(materialization_input.request_payload)
        request_model_id = stable_inline_value_instance_id(
            class_config_id=request_class_config_id,
            owner_key=call_key,
        )
        return ApiCall.model_construct(
            id=stable_api_call_id(
                api_capability_endpoint_id=api_capability_endpoint_id,
                call_key=call_key,
            ),
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=call_key,
            request_model_id=request_model_id,
            request_model=InlineValueInstance.model_construct(
                id=request_model_id,
                class_config_id=request_class_config_id,
            ),
            request_hash="sha256:empty-receipt-anchor",
            description=description,
        )

    def _fail_full_closure(**_: object) -> dict[UUID, ClassConfig]:
        raise AssertionError(
            "compact receipt must not build full DTO ClassConfig closure"
        )

    payload = {
        "operation": "materialize",
        "code_package_deltas": [
            {
                "package_name": "content-ontology",
                "paths": [
                    {
                        "relative_path": "part/content_part_text_editor_patch.aware",
                        "content_after": "schema_version Int = 1",
                    }
                ],
            }
        ],
    }
    runtime = _Runtime()
    monkeypatch.setattr(call_mod, "FSCommitStore", lambda: _HeadlessStore())
    monkeypatch.setattr(
        call_mod,
        "_resolve_api_endpoint_request_contract",
        _resolve_contract,
    )
    monkeypatch.setattr(
        call_mod,
        "_request_class_configs_by_id_for_materialization",
        _fail_full_closure,
    )
    monkeypatch.setattr(
        call_mod.ApiCall,
        "create_via_api_capability_endpoint",
        staticmethod(_create_api_call),
    )

    result = await call_mod.materialize_api_call(
        runtime=runtime,
        index=cast(
            Any,
            SimpleNamespace(
                opg_by_hash={"api-call-projection": SimpleNamespace(name="ApiCall")},
                class_configs_by_id={request_class_config.id: request_class_config},
            ),
        ),
        actor_id=None,
        source_lane=_lane(projection_hash="api-projection"),
        target_lane=_lane(),
        ir=resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=(
                    "aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest"
                )
            ),
            endpoint_ref="workspace.materialize.materialize",
            request_payload=payload,
        ),
        commit=True,
        publish=False,
        receipt_projection_backend="fs",
    )

    assert captured["request_payload"] == {}
    assert result.binding.request_hash == compute_api_request_hash_from_mapping(
        payload=payload
    )
    assert result.binding.commit_id == runtime.lane.last_commit_id
    assert result.binding.head_commit_id == runtime.lane.last_head_commit_id


@pytest.mark.asyncio
async def test_compact_api_call_handler_builds_request_anchor_from_context_class_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_api_runtime.handlers.impl.api import api_call as handler_mod
    from aware_api_runtime.invocation.materialization.context import (
        scoped_api_call_materialization_input,
    )

    request_class_config = ClassConfig.model_construct(
        id=uuid4(),
        name="WorkspaceMaterializeRequest",
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
        value_mode=ClassValueMode.inline_value,
    )
    call_key = uuid4()
    session = _FakeHandlerSession()
    monkeypatch.setattr(handler_mod, "current_handler_session", lambda: session)

    with scoped_api_call_materialization_input(
        request_payload={},
        request_class_config=request_class_config,
        request_class_configs_by_id=None,
    ):
        api_call = await handler_mod.create_via_api_capability_endpoint(
            api_capability_endpoint_id=uuid4(),
            call_key=call_key,
            request_class_config_id=UUID(str(request_class_config.id)),
            description="compact request anchor",
        )

    assert api_call.request_model_id == stable_inline_value_instance_id(
        class_config_id=UUID(str(request_class_config.id)),
        owner_key=call_key,
    )
    assert api_call.request_model is not None
    assert api_call.request_model.class_config_id == request_class_config.id
    assert api_call.request_model.class_config is request_class_config
    assert api_call.request_model.inline_value_instance_attributes == []
    assert api_call.request_hash


@pytest.mark.asyncio
async def test_flat_api_call_receipt_keeps_full_request_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    request_class_config = ClassConfig.model_construct(
        id=uuid4(),
        name="WorkspaceStatusRequest",
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceStatusRequest",
    )
    endpoint_id = uuid4()
    captured: dict[str, object] = {}

    async def _resolve_contract(**_: object) -> object:
        return call_mod._ResolvedApiEndpointRequestContract(
            endpoint_id=endpoint_id,
            request_class_config=request_class_config,
            fulfillment_bindings=(),
            endpoint=None,
        )

    async def _create_api_call(
        *,
        api_capability_endpoint_id: UUID,
        call_key: UUID,
        request_class_config_id: UUID,
        description: str | None = None,
    ) -> ApiCall:
        materialization_input = current_api_call_materialization_input()
        assert materialization_input is not None
        captured["request_payload"] = dict(materialization_input.request_payload)
        request_model_id = stable_inline_value_instance_id(
            class_config_id=request_class_config_id,
            owner_key=call_key,
        )
        return ApiCall.model_construct(
            id=stable_api_call_id(
                api_capability_endpoint_id=api_capability_endpoint_id,
                call_key=call_key,
            ),
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=call_key,
            request_model_id=request_model_id,
            request_model=InlineValueInstance.model_construct(
                id=request_model_id,
                class_config_id=request_class_config_id,
            ),
            request_hash="sha256:full-receipt",
            description=description,
        )

    monkeypatch.setattr(call_mod, "FSCommitStore", lambda: _HeadlessStore())
    monkeypatch.setattr(
        call_mod,
        "_resolve_api_endpoint_request_contract",
        _resolve_contract,
    )
    monkeypatch.setattr(
        call_mod,
        "_request_class_configs_by_id_for_materialization",
        lambda **_: {request_class_config.id: request_class_config},
    )
    monkeypatch.setattr(
        call_mod.ApiCall,
        "create_via_api_capability_endpoint",
        staticmethod(_create_api_call),
    )

    result = await call_mod.materialize_api_call(
        runtime=_Runtime(),
        index=cast(
            Any,
            SimpleNamespace(
                opg_by_hash={"api-call-projection": SimpleNamespace(name="ApiCall")},
                class_configs_by_id={request_class_config.id: request_class_config},
            ),
        ),
        actor_id=None,
        source_lane=_lane(projection_hash="api-projection"),
        target_lane=_lane(),
        ir=resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=(
                    "aware_workspace_service_dto.workspace.WorkspaceStatusRequest"
                )
            ),
            endpoint_ref="workspace.materialize.materialize",
            request_payload={"workspace_root": "workspaces/aware_kernel"},
        ),
        commit=True,
        publish=False,
        receipt_projection_backend="fs",
    )

    assert captured["request_payload"] == {"workspace_root": "workspaces/aware_kernel"}
    assert result.binding.request_hash == "sha256:full-receipt"


@pytest.mark.asyncio
async def test_compact_api_call_outcome_receipt_skips_response_payload_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod

    api_call_id = uuid4()
    api_call = ApiCall.model_construct(
        id=api_call_id,
        api_capability_endpoint_id=uuid4(),
        request_model_id=uuid4(),
        request_model=None,
        call_key=uuid4(),
        request_hash="sha256:request",
        outcome=None,
    )
    outcome = ApiCallOutcome.model_construct(
        id=uuid4(),
        api_call_id=api_call_id,
        response_model_id=None,
        response_model=None,
        status=ApiCallOutcomeStatus.succeeded,
        error=None,
    )

    async def _create_outcome(
        self: ApiCall,
        *,
        status: ApiCallOutcomeStatus,
        error: str | None,
    ) -> ApiCallOutcome:
        assert self is api_call
        materialization_input = current_api_call_outcome_materialization_input()
        assert materialization_input is not None
        assert materialization_input.response_payload is None
        assert materialization_input.response_class_configs_by_id is None
        assert status is ApiCallOutcomeStatus.succeeded
        assert error is None
        self.outcome = outcome
        return outcome

    async def _ensure_projected(**_: object) -> None:
        return None

    def _fail_response_closure(**_: object) -> dict[UUID, ClassConfig]:
        raise AssertionError("compact outcome must not build response DTO closure")

    runtime = _Runtime()
    monkeypatch.setattr(ApiCall, "create_outcome", _create_outcome)
    monkeypatch.setattr(
        outcome_mod,
        "_ensure_api_call_lane_projected_for_db_outcome_receipt",
        _ensure_projected,
    )
    monkeypatch.setattr(
        outcome_mod,
        "_response_class_configs_by_id_for_materialization",
        _fail_response_closure,
    )

    result = await outcome_mod.materialize_api_call_outcome(
        runtime=runtime,
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        actor_id=None,
        target_lane=_lane(),
        api_call_id=api_call_id,
        api_call_hint=api_call,
        status=ApiCallOutcomeStatus.succeeded,
        response_payload={
            "code_package_artifact_refs": [
                {
                    "path": "modules/content/generated.py",
                    "digest": "sha256:artifact",
                }
            ]
        },
        response_class_config=ClassConfig.model_construct(
            id=uuid4(),
            name="WorkspaceMaterializeResponse",
            class_fqn=(
                "aware_workspace_service_dto.workspace.WorkspaceMaterializeResponse"
            ),
        ),
        commit=True,
        publish=False,
    )

    assert result.api_call is api_call
    assert result.api_call_outcome is outcome
    assert result.binding.response_model_id is None
    assert result.binding.commit_id == runtime.lane.last_commit_id
