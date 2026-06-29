from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.class_.inline_value_instance.builder import (
    build_inline_value_instance_from_mapping,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta.class_.inline_value_instance import (
    resolve_inline_value_instance_attributes,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.oig_value_decoder import decode_oig_attribute_value
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from _api_runtime_test_paths import (
    API_META_PACKAGE_MANIFEST_PATHS,
    API_META_PYTHON_ROOTS,
    REPO_ROOT,
)

from aware_api_runtime.invocation import (
    build_resolved_api_invocation_envelope,
    resolve_api_invocation_ir,
)
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_api_runtime.request_hash import (
    compute_api_request_hash_from_inline_value_instance,
)
from aware_api_runtime.models import (
    APICapabilityEndpointFunctionOwnership,
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.invocation.materialization import materialize_api_call
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
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


@dataclass(frozen=True, slots=True)
class ApiMetaRuntimeLane:
    branch_id: UUID
    actor_id: UUID | None = None


def _api_ownership_for_runtime(*, request_class_ref: str) -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name="openai-api",
            source_path="runtime-proof",
            capabilities=(
                APICapabilityOwnership(
                    name="door",
                    source_path="runtime-proof",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="open",
                            source_path="runtime-proof",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref=request_class_ref,
                                source_path="runtime-proof",
                            ),
                            functions=(
                                APICapabilityEndpointFunctionOwnership(
                                    name="open",
                                    graph_target="aware_home",
                                    graph_capability_function_name="open",
                                    source_path="runtime-proof",
                                ),
                            ),
                            description="Open the API proof door.",
                        ),
                    ),
                    description="Door operations",
                ),
            ),
            graphs=(),
        ),
    )


def _api_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PACKAGE_MANIFEST_PATHS


def _api_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PYTHON_ROOTS


def _prepend_api_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _api_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_api_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_api_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_API_META_HANDLER_MODULE,),
        bootstrap_modules=(_API_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def _pydantic_class_config_by_name(*, package_prefix: str, name: str) -> ClassConfig:
    from aware_utils.pydantic.class_config_registry import (
        iter_pydantic_package_class_config_payloads,
        register_pydantic_package_class_configs,
    )

    register_pydantic_package_class_configs(package_prefix=package_prefix)
    for entry in iter_pydantic_package_class_config_payloads(
        package_prefix=package_prefix,
    ):
        class_config = ClassConfig.model_validate(entry.payload)
        if class_config.name == name:
            return class_config
    raise AssertionError(f"Missing ClassConfig {package_prefix}.{name}")


def test_api_invocation_receipt_modules_do_not_import_deprecated_runtime() -> None:
    repo_root = REPO_ROOT
    module_paths = (
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/invocation/materialization/call.py",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/invocation/materialization/call_outcome.py",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/invocation/dispatcher.py",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/invocation/ingress.py",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/handlers/impl/api/api_capability_endpoint.py",
    )

    for module_path in module_paths:
        source = module_path.read_text(encoding="utf-8")
        assert "aware_runtime" not in source, module_path
        assert "bind_runtime_lane" not in source, module_path
        assert "hydrate_orm_graph_from_oig" not in source, module_path
        assert "FunctionCallInvoker" not in source, module_path


def test_api_call_request_materialization_closes_imported_dto_class_configs() -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod
    from aware_code_service_dto.code.features.package_delta import CodePackageDelta

    request_class_config = _pydantic_class_config_by_name(
        package_prefix="aware_workspace_service_dto",
        name="WorkspaceMaterializeRequest",
    )
    code_package_delta_class_config = _pydantic_class_config_by_name(
        package_prefix="aware_code_service_dto",
        name="CodePackageDelta",
    )

    class_configs_by_id = call_mod._request_class_configs_by_id_for_materialization(
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        request_class_config=request_class_config,
        request_class_ref="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
    )

    assert code_package_delta_class_config.id is not None
    assert class_configs_by_id[code_package_delta_class_config.id].value_mode == (
        ClassValueMode.inline_value
    )
    request_model = build_inline_value_instance_from_mapping(
        owner_key=uuid4(),
        class_config=request_class_config,
        values={
            "operation": "materialize",
            "workspace_root": "workspaces/aware_kernel",
            "code_package_deltas": [
                CodePackageDelta(
                    package_name="content-ontology",
                    paths=[],
                ).model_dump(mode="json")
            ],
        },
        class_configs_by_id=class_configs_by_id,
    )

    assert request_model.class_config_id == request_class_config.id


@pytest.mark.asyncio
async def test_api_call_constructor_returns_generated_bootstrap_root_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.handlers.impl.api.api_call as api_call_mod
    import aware_api_runtime.invocation.materialization.call as call_mod
    from aware_api_ontology.stable_ids import stable_api_call_id
    from aware_api_runtime.invocation.materialization.context import (
        scoped_api_call_materialization_input,
    )

    request_class_config = _pydantic_class_config_by_name(
        package_prefix="aware_workspace_service_dto",
        name="WorkspaceMaterializeRequest",
    )
    class_configs_by_id = call_mod._request_class_configs_by_id_for_materialization(
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        request_class_config=request_class_config,
        request_class_ref="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
    )

    class _Session:
        def imap_get(self, *_args: object, **_kwargs: object) -> object | None:
            return None

        def imap_add(self, _value: object) -> None:
            return None

    monkeypatch.setattr(api_call_mod, "current_handler_session", lambda: _Session())
    endpoint_id = uuid4()
    call_key = uuid4()

    with scoped_api_call_materialization_input(
        request_payload={
            "operation": "materialize",
            "workspace_root": "workspaces/aware_kernel",
            "code_package_deltas": [],
        },
        request_class_config=request_class_config,
        request_class_configs_by_id=class_configs_by_id,
    ):
        api_call = await api_call_mod.create_via_api_capability_endpoint(
            api_capability_endpoint_id=endpoint_id,
            call_key=call_key,
            request_class_config_id=request_class_config.id,
            description="Materialize Content ontology.",
        )

    assert api_call.id == stable_api_call_id(
        api_capability_endpoint_id=endpoint_id,
        call_key=call_key,
    )
    assert api_call.call_key == call_key
    assert api_call.request_hash


@pytest.mark.asyncio
async def test_api_call_create_outcome_attaches_owned_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.handlers.impl.api.api_call as api_call_mod
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
    from aware_api_ontology.api.api_call_outcome import ApiCallOutcome

    api_call_id = uuid4()
    api_call = ApiCall.model_construct(
        id=api_call_id,
        api_capability_endpoint_id=uuid4(),
        request_model_id=uuid4(),
        request_model=None,
        call_key=uuid4(),
        description=None,
        request_hash="sha256:test",
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

    async def _build_via_api_call(**kwargs: object) -> ApiCallOutcome:
        assert kwargs["api_call_id"] == api_call_id
        return outcome

    monkeypatch.setattr(
        api_call_mod.ApiCallOutcome,
        "build_via_api_call",
        _build_via_api_call,
    )

    created = await api_call_mod.create_outcome(
        api_call=api_call,
        status=ApiCallOutcomeStatus.succeeded,
        error=None,
    )

    assert created is outcome
    assert api_call.outcome is outcome


@pytest.mark.asyncio
async def test_api_call_outcome_materialization_returns_created_outcome_without_rehydrating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
    from aware_api_ontology.api.api_call_outcome import ApiCallOutcome

    api_call_id = uuid4()
    response_model_id = uuid4()
    commit_id = uuid4()
    head_commit_id = uuid4()
    target_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-call-projection",
    )
    outcome = ApiCallOutcome.model_construct(
        id=uuid4(),
        api_call_id=api_call_id,
        response_model_id=response_model_id,
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
        assert status is ApiCallOutcomeStatus.succeeded
        assert error is None
        self.outcome = outcome
        return outcome

    api_call = ApiCall.model_construct(
        id=api_call_id,
        api_capability_endpoint_id=uuid4(),
        request_model_id=uuid4(),
        request_model=None,
        call_key=uuid4(),
        description=None,
        request_hash="sha256:test",
        outcome=outcome,
    )
    hydrate_calls = 0

    async def _hydrate_materialized_api_call(**_: object) -> ApiCall:
        nonlocal hydrate_calls
        hydrate_calls += 1
        if hydrate_calls > 1:
            raise AssertionError(
                "ApiCallOutcome must not rehydrate the full api_call lane after commit"
            )
        return api_call

    async def _ensure_projected(**_: object) -> None:
        return None

    class _RuntimeLane:
        last_commit_id = commit_id
        last_head_commit_id = head_commit_id

        def activate(
            self,
            *,
            commit: bool,
            publish: bool,
        ) -> object:
            assert commit is True
            assert publish is False

            class _Activation:
                def __enter__(self) -> None:
                    return None

                def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
                    return False

            return _Activation()

    class _Runtime:
        async def bind(self, **_: object) -> _RuntimeLane:
            return _RuntimeLane()

    monkeypatch.setattr(
        ApiCall,
        "create_outcome",
        _create_outcome,
    )
    monkeypatch.setattr(
        outcome_mod,
        "_hydrate_materialized_api_call",
        _hydrate_materialized_api_call,
    )
    monkeypatch.setattr(
        outcome_mod,
        "_ensure_api_call_lane_projected_for_db_outcome_receipt",
        _ensure_projected,
    )
    monkeypatch.setattr(
        outcome_mod,
        "_response_class_configs_by_id_for_materialization",
        lambda **_: {},
    )

    result = await outcome_mod.materialize_api_call_outcome(
        runtime=_Runtime(),
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        actor_id=None,
        target_lane=target_lane,
        api_call_id=api_call_id,
        response_class_config=ClassConfig.model_construct(
            id=uuid4(),
            name="Response",
            class_fqn="proof.Response",
        ),
    )

    assert hydrate_calls == 1
    assert result.api_call is api_call
    assert result.api_call_outcome is outcome
    assert api_call.outcome is outcome
    assert result.binding.api_call_outcome_id == outcome.id
    assert result.binding.response_model_id == response_model_id
    assert result.binding.commit_id == commit_id
    assert result.binding.head_commit_id == head_commit_id


@pytest.mark.asyncio
async def test_api_call_outcome_materialization_uses_api_call_hint_without_lane_hydration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_call_enums import ApiCallOutcomeStatus
    from aware_api_ontology.api.api_call_outcome import ApiCallOutcome

    api_call_id = uuid4()
    outcome = ApiCallOutcome.model_construct(
        id=uuid4(),
        api_call_id=api_call_id,
        response_model_id=None,
        response_model=None,
        status=ApiCallOutcomeStatus.succeeded,
        error=None,
    )
    api_call = ApiCall.model_construct(
        id=api_call_id,
        api_capability_endpoint_id=uuid4(),
        request_model_id=uuid4(),
        request_model=None,
        call_key=uuid4(),
        description=None,
        request_hash="sha256:test",
        outcome=None,
    )
    target_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-call-projection",
    )

    async def _create_outcome(
        self: ApiCall,
        *,
        status: ApiCallOutcomeStatus,
        error: str | None,
    ) -> ApiCallOutcome:
        assert self is api_call
        assert status is ApiCallOutcomeStatus.succeeded
        assert error is None
        self.outcome = outcome
        return outcome

    async def _hydrate_materialized_api_call(**_: object) -> ApiCall:
        raise AssertionError("ApiCall hint should avoid committed lane hydration")

    async def _ensure_projected(**_: object) -> None:
        return None

    class _RuntimeLane:
        last_commit_id = uuid4()
        last_head_commit_id = uuid4()

        def activate(
            self,
            *,
            commit: bool,
            publish: bool,
        ) -> object:
            assert commit is True
            assert publish is False

            class _Activation:
                def __enter__(self) -> None:
                    return None

                def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
                    return False

            return _Activation()

    class _Runtime:
        def bind(self, **_: object) -> _RuntimeLane:
            return _RuntimeLane()

    monkeypatch.setattr(ApiCall, "create_outcome", _create_outcome)
    monkeypatch.setattr(
        outcome_mod,
        "_hydrate_materialized_api_call",
        _hydrate_materialized_api_call,
    )
    monkeypatch.setattr(
        outcome_mod,
        "_ensure_api_call_lane_projected_for_db_outcome_receipt",
        _ensure_projected,
    )
    monkeypatch.setattr(
        outcome_mod,
        "_response_class_configs_by_id_for_materialization",
        lambda **_: {},
    )

    result = await outcome_mod.materialize_api_call_outcome(
        runtime=_Runtime(),
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        actor_id=None,
        target_lane=target_lane,
        api_call_id=api_call_id,
        api_call_hint=api_call,
        response_class_config=ClassConfig.model_construct(
            id=uuid4(),
            name="Response",
            class_fqn="proof.Response",
        ),
    )

    assert result.api_call is api_call
    assert result.api_call_outcome is outcome
    assert api_call.outcome is outcome
    assert result.binding.api_call_outcome_id == outcome.id


@pytest.mark.asyncio
async def test_api_call_outcome_db_receipt_catches_up_committed_lane_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-call-projection",
    )
    calls: list[dict[str, object]] = []

    async def _fake_ensure_projection_readiness(**kwargs: object) -> object:
        calls.append(dict(kwargs))
        return SimpleNamespace(
            status="ready",
            skipped_reason=None,
            commits_applied=1,
            head_commit_id=uuid4(),
        )

    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "db")
    monkeypatch.setattr(
        outcome_mod,
        "ensure_projection_readiness",
        _fake_ensure_projection_readiness,
    )

    result = await outcome_mod._ensure_api_call_lane_projected_for_db_outcome_receipt(
        index=cast(Any, SimpleNamespace()),
        target_lane=lane,
        commit=True,
    )

    assert result is not None
    assert result.status == "ready"
    assert len(calls) == 1
    requirement = calls[0]["requirement"]
    assert requirement.name == "api_call_outcome.read_model_receipt"
    assert requirement.branch_id == lane.branch_id
    assert requirement.projection_hash == lane.projection_hash
    assert requirement.mode == "required_db"


@pytest.mark.asyncio
async def test_api_call_outcome_projection_catchup_skips_without_explicit_db_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod

    calls: list[dict[str, object]] = []

    async def _fake_ensure_projection_readiness(**kwargs: object) -> object:
        calls.append(dict(kwargs))
        return SimpleNamespace(
            status="skipped", skipped_reason="mode:off", commits_applied=0
        )

    monkeypatch.delenv("AWARE_PERSISTENCE_BACKEND", raising=False)
    monkeypatch.setattr(
        outcome_mod,
        "ensure_projection_readiness",
        _fake_ensure_projection_readiness,
    )

    result = await outcome_mod._ensure_api_call_lane_projected_for_db_outcome_receipt(
        index=cast(Any, SimpleNamespace()),
        target_lane=MaterializationLaneContext(
            branch_id=uuid4(),
            projection_hash="api-call-projection",
        ),
        commit=True,
    )

    assert result is not None
    assert result.status == "skipped"
    assert calls[0]["index"] is None
    assert calls[0]["requirement"].mode == "off"


@pytest.mark.asyncio
async def test_db_api_call_materialization_uses_api_call_receipt_lane(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance

    source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-projection",
    )
    target_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-call-projection",
    )
    endpoint_id = uuid4()
    request_class_config = ClassConfig.model_construct(
        id=uuid4(),
        class_fqn="proof.Request",
        name="Request",
    )
    request_model_id = uuid4()
    api_call_id = uuid4()
    captured: dict[str, object] = {}

    class _RuntimeLane:
        last_commit_id = uuid4()
        last_head_commit_id = uuid4()

        def activate(self, *, commit: bool, publish: bool):
            captured["activate_commit"] = commit
            captured["activate_publish"] = publish

            class _Activation:
                def __enter__(self):
                    return None

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Activation()

    class _Runtime:
        async def bind(self, **kwargs: object) -> _RuntimeLane:
            captured["bound_branch_id"] = kwargs["branch_id"]
            captured["bound_projection"] = kwargs["projection"]
            return _RuntimeLane()

    async def _fake_resolve_contract(**kwargs: object) -> object:
        captured["require_endpoint"] = kwargs["require_endpoint"]
        return call_mod._ResolvedApiEndpointRequestContract(
            endpoint_id=endpoint_id,
            request_class_config=request_class_config,
            fulfillment_bindings=(),
            endpoint=None,
        )

    async def _fake_create_call(
        self: ApiCapabilityEndpoint,
        *,
        call_key: UUID,
        description: str | None = None,
    ) -> ApiCall:
        _ = self, call_key, description
        raise AssertionError(
            "Commit-backed ApiCall handoff must not use the endpoint wrapper"
        )

    async def _fake_create_via_api_capability_endpoint(
        *,
        api_capability_endpoint_id: UUID,
        call_key: UUID,
        request_class_config_id: UUID,
        description: str | None = None,
    ) -> ApiCall:
        captured["api_call_constructor"] = {
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "call_key": call_key,
            "request_class_config_id": request_class_config_id,
            "description": description,
        }
        return ApiCall.model_construct(
            id=api_call_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=call_key,
            request_model_id=request_model_id,
            request_model=InlineValueInstance.model_construct(
                id=request_model_id,
                class_config_id=request_class_config.id,
            ),
            request_hash="sha256:test",
        )

    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "fs")
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware-root"))
    monkeypatch.setattr(
        call_mod,
        "_resolve_api_endpoint_request_contract",
        _fake_resolve_contract,
    )
    monkeypatch.setattr(ApiCapabilityEndpoint, "create_call", _fake_create_call)
    monkeypatch.setattr(
        call_mod.ApiCall,
        "create_via_api_capability_endpoint",
        staticmethod(_fake_create_via_api_capability_endpoint),
    )
    index = SimpleNamespace(
        opg_by_hash={
            source_lane.projection_hash: SimpleNamespace(name="RuntimeApiDispatch"),
            target_lane.projection_hash: SimpleNamespace(name="ApiCall"),
        },
        class_configs_by_id={request_class_config.id: request_class_config},
    )
    call_key = uuid4()

    result = await call_mod.materialize_api_call(
        runtime=_Runtime(),
        index=cast(Any, index),
        actor_id=None,
        source_lane=source_lane,
        target_lane=target_lane,
        ir=resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(request_class_ref="proof.Request"),
            endpoint_ref="openai-api.door.open",
            request_payload={"label": "front-door"},
        ),
        call_key=call_key,
        commit=True,
        publish=False,
        receipt_projection_backend="db",
    )

    assert captured["require_endpoint"] is False
    assert captured["bound_branch_id"] == target_lane.branch_id
    assert captured["bound_projection"] == target_lane.projection_hash
    assert captured["api_call_constructor"] == {
        "api_capability_endpoint_id": endpoint_id,
        "call_key": call_key,
        "request_class_config_id": request_class_config.id,
        "description": "Open the API proof door.",
    }
    assert result.binding.branch_id == target_lane.branch_id
    assert result.binding.projection_hash == target_lane.projection_hash


@pytest.mark.asyncio
async def test_endpoint_create_call_preserves_materialization_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.handlers.impl.api.api_capability_endpoint as endpoint_mod
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_api_ontology.api.api_capability_endpoint_request_config import (
        ApiCapabilityEndpointRequestConfig,
    )
    from aware_api_runtime.invocation.materialization.context import (
        current_api_call_materialization_input,
        scoped_api_call_materialization_input,
    )
    from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance

    request_class_config = ClassConfig.model_construct(
        id=uuid4(),
        name="Request",
        class_fqn="proof.Request",
    )
    endpoint = ApiCapabilityEndpoint.model_construct(
        id=uuid4(),
        request_config=ApiCapabilityEndpointRequestConfig.model_construct(
            id=uuid4(),
            class_config_id=request_class_config.id,
            class_config=None,
        ),
    )
    request_model_id = uuid4()
    captured: dict[str, object] = {}

    async def _fake_create_via_api_capability_endpoint(
        *,
        api_capability_endpoint_id: UUID,
        call_key: UUID,
        request_class_config_id: UUID,
        description: str | None = None,
    ) -> ApiCall:
        materialization_input = current_api_call_materialization_input()
        assert materialization_input is not None
        captured["request_payload"] = dict(materialization_input.request_payload)
        captured["request_class_config"] = materialization_input.request_class_config
        captured["request_class_configs_by_id"] = (
            materialization_input.request_class_configs_by_id
        )
        return ApiCall.model_construct(
            id=uuid4(),
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=call_key,
            request_model_id=request_model_id,
            request_model=InlineValueInstance.model_construct(
                id=request_model_id,
                class_config_id=request_class_config_id,
            ),
            request_hash="sha256:test",
            description=description,
        )

    monkeypatch.setattr(
        endpoint_mod.ApiCall,
        "create_via_api_capability_endpoint",
        staticmethod(_fake_create_via_api_capability_endpoint),
    )
    class_configs_by_id = {request_class_config.id: request_class_config}

    with scoped_api_call_materialization_input(
        request_payload={"label": "front-door"},
        request_class_config=request_class_config,
        request_class_configs_by_id=class_configs_by_id,
    ):
        await endpoint_mod.create_call(
            endpoint,
            call_key=uuid4(),
            description="Open the API proof door.",
        )

    assert captured["request_payload"] == {"label": "front-door"}
    assert captured["request_class_config"] is request_class_config
    assert captured["request_class_configs_by_id"] is class_configs_by_id


@pytest.mark.asyncio
async def test_endpoint_create_call_resolves_request_class_config_from_handler_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.handlers.impl.api.api_capability_endpoint as endpoint_mod
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_api_ontology.api.api_capability_endpoint_request_config import (
        ApiCapabilityEndpointRequestConfig,
    )

    request_class_config = ClassConfig.model_construct(
        id=uuid4(),
        name="Request",
        class_fqn="proof.Request",
    )
    endpoint = ApiCapabilityEndpoint.model_construct(
        id=uuid4(),
        request_config=ApiCapabilityEndpointRequestConfig.model_construct(
            id=uuid4(),
            class_config_id=request_class_config.id,
            class_config=None,
        ),
    )
    captured: dict[str, object] = {}

    class _Session:
        def imap_get(self, model_type: object, object_id: UUID) -> object | None:
            captured["imap_get"] = (model_type, object_id)
            return None

        def imap_add(self, value: object) -> None:
            captured["imap_add"] = value

    async def _fake_create_via_api_capability_endpoint(
        *,
        api_capability_endpoint_id: UUID,
        call_key: UUID,
        request_class_config_id: UUID,
        description: str | None = None,
    ) -> ApiCall:
        captured["api_capability_endpoint_id"] = api_capability_endpoint_id
        captured["request_class_config_id"] = request_class_config_id
        captured["description"] = description
        return ApiCall.model_construct(
            id=uuid4(),
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=call_key,
            request_model_id=uuid4(),
            request_hash="sha256:test",
            description=description,
        )

    monkeypatch.setattr(endpoint_mod, "current_handler_session", lambda: _Session())
    monkeypatch.setattr(
        endpoint_mod,
        "current_handler_index",
        lambda: SimpleNamespace(
            class_configs_by_id={request_class_config.id: request_class_config}
        ),
    )
    monkeypatch.setattr(
        endpoint_mod.ApiCall,
        "create_via_api_capability_endpoint",
        staticmethod(_fake_create_via_api_capability_endpoint),
    )

    await endpoint_mod.create_call(
        endpoint,
        call_key=uuid4(),
        description="Open the API proof door.",
    )

    assert captured["imap_get"] == (ClassConfig, request_class_config.id)
    assert captured["imap_add"] is request_class_config
    assert captured["api_capability_endpoint_id"] == endpoint.id
    assert captured["request_class_config_id"] == request_class_config.id
    assert captured["description"] == "Open the API proof door."


@pytest.mark.asyncio
async def test_endpoint_create_call_rejects_mismatched_materialization_class_config() -> (
    None
):
    import aware_api_runtime.handlers.impl.api.api_capability_endpoint as endpoint_mod
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_api_ontology.api.api_capability_endpoint_request_config import (
        ApiCapabilityEndpointRequestConfig,
    )
    from aware_api_runtime.invocation.materialization.context import (
        scoped_api_call_materialization_input,
    )

    request_class_config_id = uuid4()
    request_class_config = ClassConfig.model_construct(
        id=uuid4(),
        name="Request",
        class_fqn="proof.Request",
    )
    endpoint = ApiCapabilityEndpoint.model_construct(
        id=uuid4(),
        request_config=ApiCapabilityEndpointRequestConfig.model_construct(
            id=uuid4(),
            class_config_id=request_class_config_id,
            class_config=None,
        ),
    )

    with scoped_api_call_materialization_input(
        request_payload={},
        request_class_config=request_class_config,
        request_class_configs_by_id={request_class_config.id: request_class_config},
    ):
        with pytest.raises(ValueError, match="mismatched request ClassConfig"):
            await endpoint_mod.create_call(
                endpoint,
                call_key=uuid4(),
                description="Open the API proof door.",
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
        "Expected one runtime ClassConfigFunctionConfig for API graph materialization proof"
    )


def _select_runtime_inline_request_contract(
    runtime_index,
) -> tuple[ClassConfig, str, object]:
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
        return class_config, attribute_config.name, sample_value

    raise AssertionError(
        "Expected one compiled inline_value ClassConfig with a single supported primitive attribute"
    )


@pytest.mark.asyncio
async def test_api_call_request_contract_explicit_endpoint_id_uses_committed_api_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    api_id = stable_api_id(name="home-devices")
    api_capability_id = stable_api_capability_id(api_id=api_id, name="door")
    endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=api_capability_id,
        name="open",
    )
    request_class_config_id = uuid4()
    request_class_config = cast(
        ClassConfig,
        cast(
            object,
            SimpleNamespace(
                id=request_class_config_id,
                class_fqn="aware_home_api.door.OpenDoor",
            ),
        ),
    )
    request_config = SimpleNamespace(
        class_config_id=request_class_config_id,
        class_config=request_class_config,
    )
    endpoint = SimpleNamespace(
        id=endpoint_id,
        name="open",
        api_capability_id=api_capability_id,
        request_config=request_config,
    )
    source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-projection",
    )
    source_commit_id = uuid4()
    ir = call_mod.ApiInvocationIR(
        api_name="home-devices",
        capability_name="door",
        endpoint_name="open",
        endpoint_ref="home-devices.door.open",
        discriminant="home-devices.door.open",
        source_path="skill_config_step:proof",
        request_payload={"door": "front"},
        request_class_ref="aware_home_api.door.OpenDoor",
        request_class_config_id=request_class_config_id,
        request_source_path="api_endpoint:request",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(),
        api_capability_endpoint_id=endpoint_id,
    )

    class _Store:
        async def head(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["branch_id"] == source_lane.branch_id
            assert kwargs["projection_hash"] == source_lane.projection_hash
            return {"commit_id": str(source_commit_id)}

    async def _hydrate_source_api_endpoint(**kwargs: object) -> object:
        assert kwargs["source_branch_id"] == source_lane.branch_id
        assert kwargs["source_projection_hash"] == source_lane.projection_hash
        assert kwargs["source_commit_id"] == source_commit_id
        assert kwargs["endpoint_id"] == endpoint_id
        return endpoint

    def _fast_path_must_not_run(**_: object) -> object:
        raise AssertionError(
            "explicit endpoint id must bypass the verified-IR fast path"
        )

    monkeypatch.setattr(call_mod, "FSCommitStore", lambda: _Store())
    monkeypatch.setattr(
        call_mod,
        "_hydrate_source_api_endpoint",
        _hydrate_source_api_endpoint,
    )
    monkeypatch.setattr(
        call_mod,
        "_resolve_verified_ir_endpoint_request_contract",
        _fast_path_must_not_run,
    )

    contract = await call_mod._resolve_api_endpoint_request_contract(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={request_class_config_id: request_class_config},
            ),
        ),
        source_lane=source_lane,
        ir=ir,
        source_commit=None,
    )

    assert contract.endpoint_id == endpoint_id
    assert contract.request_class_config is request_class_config
    assert contract.fulfillment_bindings == ()


@pytest.mark.asyncio
async def test_api_call_request_contract_can_use_verified_invocation_ir_without_source_lane_hydration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    request_class_config_id = uuid4()
    request_class_config = cast(
        ClassConfig,
        cast(
            object,
            SimpleNamespace(
                id=request_class_config_id,
            ),
        ),
    )
    source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-projection",
    )
    source_commit_id = uuid4()
    ir = call_mod.ApiInvocationIR(
        api_name="workspace",
        capability_name="semantic_source",
        endpoint_name="semantic_source",
        endpoint_ref="workspace.semantic_source.semantic_source",
        discriminant="workspace.semantic_source.semantic_source",
        source_path="apis/workspace/bindings/workspace.apis.aware",
        request_payload={"workspace_root": "/tmp/workspace"},
        request_class_ref="aware_workspace_service_dto.workspace.WorkspaceSemanticSourceRequest",
        request_class_config_id=request_class_config_id,
        request_source_path="apis/workspace/bindings/workspace.apis.aware",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(),
    )

    class _Store:
        async def head(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["branch_id"] == source_lane.branch_id
            assert kwargs["projection_hash"] == source_lane.projection_hash
            return {"commit_id": str(source_commit_id)}

    class _Materializer:
        async def get(self, **kwargs):  # type: ignore[no-untyped-def]
            _ = kwargs
            raise AssertionError(
                "verified invocation IR must not hydrate the API source lane"
            )

    monkeypatch.setattr(call_mod, "FSCommitStore", lambda: _Store())
    monkeypatch.setattr(call_mod, "CachedLaneMaterializer", lambda: _Materializer())

    contract = await call_mod._resolve_api_endpoint_request_contract(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={request_class_config_id: request_class_config},
            ),
        ),
        source_lane=source_lane,
        ir=ir,
        source_commit=None,
    )

    api_id = stable_api_id(name="workspace")
    capability_id = stable_api_capability_id(
        api_id=api_id,
        name="semantic_source",
    )
    expected_endpoint_id = stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name="semantic_source",
    )
    assert contract.endpoint_id == expected_endpoint_id
    assert contract.request_class_config is request_class_config
    assert contract.fulfillment_bindings == ()


@pytest.mark.asyncio
async def test_api_call_request_contract_fast_path_can_use_orm_registry_class_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    request_class_config_id = uuid4()
    request_class_config = cast(
        ClassConfig,
        cast(
            object,
            SimpleNamespace(
                id=request_class_config_id,
            ),
        ),
    )
    source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-projection",
    )
    ir = call_mod.ApiInvocationIR(
        api_name="workspace",
        capability_name="semantic_source",
        endpoint_name="semantic_source",
        endpoint_ref="workspace.semantic_source.semantic_source",
        discriminant="workspace.semantic_source.semantic_source",
        source_path="apis/workspace/bindings/workspace.apis.aware",
        request_payload={"workspace_root": "/tmp/workspace"},
        request_class_ref="aware_workspace_service_dto.workspace.WorkspaceSemanticSourceRequest",
        request_class_config_id=request_class_config_id,
        request_source_path="apis/workspace/bindings/workspace.apis.aware",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(),
    )

    class _Store:
        async def head(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["branch_id"] == source_lane.branch_id
            assert kwargs["projection_hash"] == source_lane.projection_hash
            return {"commit_id": str(uuid4())}

    class _Materializer:
        async def get(self, **kwargs):  # type: ignore[no-untyped-def]
            _ = kwargs
            raise AssertionError(
                "verified invocation IR must not hydrate the API source lane"
            )

    class _RequestModel:
        @staticmethod
        def get_class_config() -> ClassConfig:
            return request_class_config

    monkeypatch.setattr(call_mod, "FSCommitStore", lambda: _Store())
    monkeypatch.setattr(call_mod, "CachedLaneMaterializer", lambda: _Materializer())
    monkeypatch.setattr(
        call_mod.ORMModelRegistry,
        "get_class_by_class_config_id",
        staticmethod(
            lambda class_config_id: (
                _RequestModel if class_config_id == request_class_config_id else None
            )
        ),
    )

    contract = await call_mod._resolve_api_endpoint_request_contract(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={},
            ),
        ),
        source_lane=source_lane,
        ir=ir,
        source_commit=None,
    )

    assert contract.request_class_config is request_class_config


@pytest.mark.asyncio
async def test_api_call_request_contract_fast_path_can_use_registered_dto_class_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    request_class_config_id = uuid4()
    request_class_config = ClassConfig(
        id=request_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceSemanticSourceRequest",
        name="WorkspaceSemanticSourceRequest",
        value_mode=ClassValueMode.inline_value,
    )
    source_lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="api-projection",
    )
    ir = call_mod.ApiInvocationIR(
        api_name="workspace",
        capability_name="semantic_source",
        endpoint_name="semantic_source",
        endpoint_ref="workspace.semantic_source.semantic_source",
        discriminant="workspace.semantic_source.semantic_source",
        source_path="apis/workspace/bindings/workspace.apis.aware",
        request_payload={"workspace_root": "/tmp/workspace"},
        request_class_ref="aware_workspace_service_dto.workspace.WorkspaceSemanticSourceRequest",
        request_class_config_id=None,
        request_source_path="apis/workspace/bindings/workspace.apis.aware",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(),
    )
    registered_packages: list[str] = []

    class _Store:
        async def head(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["branch_id"] == source_lane.branch_id
            assert kwargs["projection_hash"] == source_lane.projection_hash
            return {"commit_id": str(uuid4())}

    class _Materializer:
        async def get(self, **kwargs):  # type: ignore[no-untyped-def]
            _ = kwargs
            raise AssertionError(
                "verified invocation IR must not hydrate the API source lane"
            )

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 1

    monkeypatch.setattr(call_mod, "FSCommitStore", lambda: _Store())
    monkeypatch.setattr(call_mod, "CachedLaneMaterializer", lambda: _Materializer())
    monkeypatch.setattr(
        call_mod, "register_pydantic_package_class_configs", _register_package
    )
    package_entries = (
        SimpleNamespace(
            source="aware_workspace_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=request_class_config.model_dump(mode="json"),
        ),
    )
    monkeypatch.setattr(
        call_mod,
        "iter_pydantic_package_class_config_payloads",
        lambda *, package_prefix: package_entries,
    )
    monkeypatch.setattr(
        call_mod,
        "iter_registered_class_config_payloads",
        lambda: package_entries,
    )

    contract = await call_mod._resolve_api_endpoint_request_contract(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={},
            ),
        ),
        source_lane=source_lane,
        ir=ir,
        source_commit=None,
    )

    assert "aware_workspace_service_dto" in registered_packages
    assert contract.request_class_config.id == request_class_config_id


def test_api_call_materialization_includes_registered_nested_dto_class_configs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod
    import aware_api_runtime.invocation.materialization.pydantic_class_config_closure as closure_mod

    request_class_config_id = uuid4()
    nested_class_config_id = uuid4()
    request_class_config = ClassConfig(
        id=request_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
        name="WorkspaceMaterializeRequest",
        value_mode=ClassValueMode.inline_value,
    )
    nested_class_config = ClassConfig(
        id=nested_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceWorkflowRun",
        name="WorkspaceWorkflowRun",
        value_mode=ClassValueMode.inline_value,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 2

    monkeypatch.setattr(
        closure_mod, "register_pydantic_package_class_configs", _register_package
    )
    package_entries = (
        SimpleNamespace(
            source="aware_workspace_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=request_class_config.model_dump(mode="json"),
        ),
        SimpleNamespace(
            source="aware_workspace_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=nested_class_config.model_dump(mode="json"),
        ),
    )
    monkeypatch.setattr(
        closure_mod,
        "iter_pydantic_package_class_config_payloads",
        lambda *, package_prefix: package_entries,
    )

    class_configs_by_id = call_mod._request_class_configs_by_id_for_materialization(
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        request_class_config=request_class_config,
        request_class_ref="aware_workspace_service_dto.workspace.WorkspaceMaterializeRequest",
    )

    assert "aware_workspace_service_dto" in registered_packages
    assert class_configs_by_id[request_class_config_id] == request_class_config
    assert class_configs_by_id[nested_class_config_id] == nested_class_config


def test_api_call_request_contract_prefers_registered_dto_over_runtime_index_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    request_class_config_id = uuid4()
    request_class_config = ClassConfig(
        id=request_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.identity.IdentitySignupViaProfileRequest",
        name="IdentitySignupViaProfileRequest",
        value_mode=ClassValueMode.inline_value,
    )
    stale_runtime_request_class_config = ClassConfig(
        id=request_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn=request_class_config.class_fqn,
        name=request_class_config.name,
        value_mode=ClassValueMode.graph_ref,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 1

    monkeypatch.setattr(
        call_mod, "register_pydantic_package_class_configs", _register_package
    )
    monkeypatch.setattr(
        call_mod,
        "get_registered_class_config_payload",
        lambda *, class_config_id: (
            request_class_config.model_dump(mode="json")
            if class_config_id == str(request_class_config_id)
            else None
        ),
    )

    ir = call_mod.ApiInvocationIR(
        api_name="identity",
        capability_name="signup_via_profile",
        endpoint_name="signup_via_profile",
        endpoint_ref="identity.signup_via_profile.signup_via_profile",
        discriminant="identity.signup_via_profile.signup_via_profile",
        source_path="apis/identity/bindings/identity.apis.aware",
        request_payload={},
        request_class_ref="aware_identity_service_dto.identity.IdentitySignupViaProfileRequest",
        request_class_config_id=request_class_config_id,
        request_source_path="apis/identity/bindings/identity.apis.aware",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(),
    )

    resolved = call_mod._resolve_verified_ir_request_class_config(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={
                    request_class_config_id: stale_runtime_request_class_config,
                },
            ),
        ),
        ir=ir,
    )

    assert registered_packages == ["aware_identity_service_dto"]
    assert resolved == request_class_config


def test_api_call_materialization_prefers_registered_nested_dto_over_runtime_index_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod
    import aware_api_runtime.invocation.materialization.pydantic_class_config_closure as closure_mod

    request_class_config_id = uuid4()
    nested_class_config_id = uuid4()

    nested_label_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    nested_label_cfg = AttributeConfig(
        owner_key="aware_identity_service_dto.default.profile.CreateProfileRequest",
        name="label",
        is_required=True,
        type_descriptor=nested_label_desc,
        type_descriptor_id=nested_label_desc.id,
    )
    nested_class_config = ClassConfig(
        id=nested_class_config_id,
        class_config_attribute_configs=[
            ClassConfigAttributeConfig(
                class_config_id=nested_class_config_id,
                attribute_config=nested_label_cfg,
                attribute_config_id=nested_label_cfg.id,
                name=nested_label_cfg.name,
                position=0,
            )
        ],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.profile.CreateProfileRequest",
        name="CreateProfileRequest",
        value_mode=ClassValueMode.inline_value,
    )
    stale_runtime_nested_class_config = ClassConfig(
        id=nested_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.profile.CreateProfileRequest",
        name="CreateProfileRequest",
        value_mode=ClassValueMode.graph_ref,
    )
    nested_request_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config_id=nested_class_config_id,
    )
    nested_request_cfg = AttributeConfig(
        owner_key="aware_identity_service_dto.default.identity.IdentitySignupViaProfileRequest",
        name="create_profile_request",
        is_required=True,
        type_descriptor=nested_request_desc,
        type_descriptor_id=nested_request_desc.id,
    )
    request_class_config = ClassConfig(
        id=request_class_config_id,
        class_config_attribute_configs=[
            ClassConfigAttributeConfig(
                class_config_id=request_class_config_id,
                attribute_config=nested_request_cfg,
                attribute_config_id=nested_request_cfg.id,
                name=nested_request_cfg.name,
                position=0,
            )
        ],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.identity.IdentitySignupViaProfileRequest",
        name="IdentitySignupViaProfileRequest",
        value_mode=ClassValueMode.inline_value,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 2

    monkeypatch.setattr(
        closure_mod, "register_pydantic_package_class_configs", _register_package
    )
    package_entries = (
        SimpleNamespace(
            source="aware_identity_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=request_class_config.model_dump(mode="json"),
        ),
        SimpleNamespace(
            source="aware_identity_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=nested_class_config.model_dump(mode="json"),
        ),
    )
    monkeypatch.setattr(
        closure_mod,
        "iter_pydantic_package_class_config_payloads",
        lambda *, package_prefix: package_entries,
    )
    monkeypatch.setattr(
        closure_mod,
        "get_registered_class_config_payload",
        lambda *, class_config_id: (
            nested_class_config.model_dump(mode="json")
            if class_config_id == str(nested_class_config_id)
            else None
        ),
    )

    class_configs_by_id = call_mod._request_class_configs_by_id_for_materialization(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={
                    nested_class_config_id: stale_runtime_nested_class_config,
                },
            ),
        ),
        request_class_config=request_class_config,
        request_class_ref="aware_identity_service_dto.identity.IdentitySignupViaProfileRequest",
    )

    assert registered_packages == ["aware_identity_service_dto"]
    assert (
        class_configs_by_id[nested_class_config_id].value_mode
        == ClassValueMode.inline_value
    )
    request_model = build_inline_value_instance_from_mapping(
        owner_key=uuid4(),
        class_config=request_class_config,
        values={"create_profile_request": {"label": "front-door"}},
        class_configs_by_id=class_configs_by_id,
    )
    attributes = resolve_inline_value_instance_attributes(
        inline_value_instance=request_model,
        class_config=request_class_config,
    )
    assert attributes[0].attribute.value_root.inline_value_instance is not None


def test_api_call_request_contract_prefers_package_snapshot_over_global_registry_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call as call_mod

    request_class_config_id = uuid4()
    request_class_config = ClassConfig(
        id=request_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.identity.IdentitySignupViaProfileRequest",
        name="IdentitySignupViaProfileRequest",
        value_mode=ClassValueMode.inline_value,
    )
    stale_global_request_class_config = ClassConfig(
        id=request_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn=request_class_config.class_fqn,
        name=request_class_config.name,
        value_mode=ClassValueMode.graph_ref,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 1

    monkeypatch.setattr(
        call_mod, "register_pydantic_package_class_configs", _register_package
    )
    monkeypatch.setattr(
        call_mod,
        "iter_pydantic_package_class_config_payloads",
        lambda *, package_prefix: (
            SimpleNamespace(
                source="aware_identity_service_dto/_aware/ocg.binding.snapshot.msgpack",
                payload=request_class_config.model_dump(mode="json"),
            ),
        ),
    )
    monkeypatch.setattr(
        call_mod,
        "get_registered_class_config_payload",
        lambda *, class_config_id: (
            stale_global_request_class_config.model_dump(mode="json")
            if class_config_id == str(request_class_config_id)
            else None
        ),
    )

    ir = call_mod.ApiInvocationIR(
        api_name="identity",
        capability_name="signup_via_profile",
        endpoint_name="signup_via_profile",
        endpoint_ref="identity.signup_via_profile.signup_via_profile",
        discriminant="identity.signup_via_profile.signup_via_profile",
        source_path="apis/identity/bindings/identity.apis.aware",
        request_payload={},
        request_class_ref="aware_identity_service_dto.identity.IdentitySignupViaProfileRequest",
        request_class_config_id=request_class_config_id,
        request_source_path="apis/identity/bindings/identity.apis.aware",
        response_class_ref=None,
        response_source_path=None,
        stream=None,
        fulfillment_bindings=(),
    )

    resolved = call_mod._resolve_verified_ir_request_class_config(
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        ir=ir,
    )

    assert registered_packages == ["aware_identity_service_dto"]
    assert resolved == request_class_config


def test_api_call_outcome_materialization_includes_registered_nested_dto_class_configs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod
    import aware_api_runtime.invocation.materialization.pydantic_class_config_closure as closure_mod

    response_class_config_id = uuid4()
    nested_class_config_id = uuid4()
    response_class_config = ClassConfig(
        id=response_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceMaterializeResponse",
        name="WorkspaceMaterializeResponse",
        value_mode=ClassValueMode.inline_value,
    )
    nested_class_config = ClassConfig(
        id=nested_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_workspace_service_dto.workspace.WorkspaceMaterializeResult",
        name="WorkspaceMaterializeResult",
        value_mode=ClassValueMode.inline_value,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 2

    monkeypatch.setattr(
        closure_mod, "register_pydantic_package_class_configs", _register_package
    )
    package_entries = (
        SimpleNamespace(
            source="aware_workspace_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=response_class_config.model_dump(mode="json"),
        ),
        SimpleNamespace(
            source="aware_workspace_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=nested_class_config.model_dump(mode="json"),
        ),
    )
    monkeypatch.setattr(
        closure_mod,
        "iter_pydantic_package_class_config_payloads",
        lambda *, package_prefix: package_entries,
    )

    class_configs_by_id = outcome_mod._response_class_configs_by_id_for_materialization(
        index=cast(Any, SimpleNamespace(class_configs_by_id={})),
        response_class_config=response_class_config,
    )

    assert "aware_workspace_service_dto" in registered_packages
    assert class_configs_by_id[response_class_config_id] == response_class_config
    assert class_configs_by_id[nested_class_config_id] == nested_class_config


def test_api_call_outcome_materialization_prefers_registered_nested_dto_over_runtime_index_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod
    import aware_api_runtime.invocation.materialization.pydantic_class_config_closure as closure_mod

    response_class_config_id = uuid4()
    nested_class_config_id = uuid4()
    response_class_config = ClassConfig(
        id=response_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.identity.IdentityAdmissionReceipt",
        name="IdentityAdmissionReceipt",
        value_mode=ClassValueMode.inline_value,
    )
    nested_class_config = ClassConfig(
        id=nested_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.identity.IdentityAdmissionActor",
        name="IdentityAdmissionActor",
        value_mode=ClassValueMode.inline_value,
    )
    stale_runtime_nested_class_config = ClassConfig(
        id=nested_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn=nested_class_config.class_fqn,
        name=nested_class_config.name,
        value_mode=ClassValueMode.graph_ref,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 2

    package_entries = (
        SimpleNamespace(
            source="aware_identity_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=response_class_config.model_dump(mode="json"),
        ),
        SimpleNamespace(
            source="aware_identity_service_dto/_aware/ocg.binding.snapshot.msgpack",
            payload=nested_class_config.model_dump(mode="json"),
        ),
    )
    monkeypatch.setattr(
        closure_mod, "register_pydantic_package_class_configs", _register_package
    )
    monkeypatch.setattr(
        closure_mod,
        "iter_pydantic_package_class_config_payloads",
        lambda *, package_prefix: package_entries,
    )
    monkeypatch.setattr(
        closure_mod,
        "get_registered_class_config_payload",
        lambda *, class_config_id: (
            nested_class_config.model_dump(mode="json")
            if class_config_id == str(nested_class_config_id)
            else None
        ),
    )

    class_configs_by_id = outcome_mod._response_class_configs_by_id_for_materialization(
        index=cast(
            Any,
            SimpleNamespace(
                class_configs_by_id={
                    nested_class_config_id: stale_runtime_nested_class_config,
                },
            ),
        ),
        response_class_config=response_class_config,
    )

    assert registered_packages == ["aware_identity_service_dto"]
    assert (
        class_configs_by_id[nested_class_config_id].value_mode
        == ClassValueMode.inline_value
    )


def test_api_call_outcome_prefers_registered_response_contract_over_runtime_hint_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import aware_api_runtime.invocation.materialization.call_outcome as outcome_mod

    response_class_config_id = uuid4()
    response_class_config = ClassConfig(
        id=response_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn="aware_identity_service_dto.default.identity.IdentityAdmissionReceipt",
        name="IdentityAdmissionReceipt",
        value_mode=ClassValueMode.inline_value,
    )
    stale_runtime_response_class_config = ClassConfig(
        id=response_class_config_id,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
        class_fqn=response_class_config.class_fqn,
        name=response_class_config.name,
        value_mode=ClassValueMode.graph_ref,
    )
    registered_packages: list[str] = []

    def _register_package(*, package_prefix: str) -> int:
        registered_packages.append(package_prefix)
        return 1

    monkeypatch.setattr(
        outcome_mod, "register_pydantic_package_class_configs", _register_package
    )
    monkeypatch.setattr(
        outcome_mod,
        "iter_pydantic_package_class_config_payloads",
        lambda *, package_prefix: (
            SimpleNamespace(
                source="aware_identity_service_dto/_aware/ocg.binding.snapshot.msgpack",
                payload=response_class_config.model_dump(mode="json"),
            ),
        ),
    )
    monkeypatch.setattr(
        outcome_mod,
        "get_registered_class_config_payload",
        lambda *, class_config_id: (
            response_class_config.model_dump(mode="json")
            if class_config_id == str(response_class_config_id)
            else None
        ),
    )

    resolved = outcome_mod._resolve_registered_pydantic_response_class_config(
        response_class_config_id=response_class_config_id,
        response_class_config_hint=stale_runtime_response_class_config,
    )

    assert registered_packages == ["aware_identity_service_dto"]
    assert resolved == response_class_config


@pytest.mark.asyncio
async def test_materialize_api_call_reads_api_lane_and_writes_api_call_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_api_ontology  # noqa: F401

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        runtime_index = runtime_context.index
        lane = ApiMetaRuntimeLane(
            branch_id=uuid4(),
        )
        request_class_config, _, _ = _select_runtime_inline_request_contract(
            runtime_index
        )
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )
        class_config_id = request_class_config.id
        assert class_config_id is not None
        api_snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=lane.actor_id,
            branch_id=lane.branch_id,
            projection_hash=api_projection_hash,
            api_name="openai-api",
            endpoint_refs=("openai-api.door.open",),
            endpoint_request_class_config_ids={
                "openai-api.door.open": class_config_id,
            },
            endpoint_fulfillment_names={"openai-api.door.open": ("open",)},
            api_graph_function_config_id=_select_runtime_function_config_id(
                runtime_index
            ),
        )
        endpoint_id = api_snapshot.endpoint_ids_by_ref["openai-api.door.open"]
        branch_id = lane.branch_id
        endpoint_function_id = api_snapshot.endpoint_function_ids_by_ref[
            "openai-api.door.open"
        ]["open"]

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
            ),
            endpoint_ref="openai-api.door.open",
            request_payload={},
        )

        source_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        target_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_call_projection_hash,
        )

        result = await materialize_api_call(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            source_lane=source_lane,
            target_lane=target_lane,
            ir=ir,
        )

        assert result.binding.api_capability_endpoint_id == endpoint_id
        assert result.binding.request_class_config_id == class_config_id
        request_model = result.api_call.request_model
        assert request_model is not None
        assert (
            result.binding.request_hash
            == compute_api_request_hash_from_inline_value_instance(
                inline_value_instance=request_model,
                class_config=request_class_config,
                class_configs_by_id=runtime_index.class_configs_by_id,
            )
        )
        assert result.binding.request_model_id.int != 0
        assert result.binding.commit_id == result.last_commit_id
        assert result.binding.head_commit_id == result.last_head_commit_id
        assert result.binding.branch_id == branch_id
        assert result.binding.projection_hash == api_call_projection_hash
        assert result.last_commit_id is not None
        assert result.last_head_commit_id is not None

        envelope = build_resolved_api_invocation_envelope(
            ir=ir,
            materialized_call=result.binding,
        )
        assert envelope.api_call_id == result.binding.api_call_id
        assert envelope.api_capability_endpoint_id == endpoint_id
        assert envelope.request_hash == result.binding.request_hash
        assert envelope.commit_id == result.last_commit_id
        assert envelope.head_commit_id == result.last_head_commit_id
        assert envelope.branch_id == branch_id
        assert envelope.projection_hash == api_call_projection_hash
        assert envelope.request_class_config_id == class_config_id
        assert len(envelope.fulfillment_bindings) == 1
        assert (
            envelope.fulfillment_bindings[0].api_capability_endpoint_function_id
            == endpoint_function_id
        )

        api_call_head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=api_call_projection_hash,
        )
        assert api_call_head is not None
        assert api_call_head.get("commit_id")
        assert api_call_head.get("object_instance_graph_id")


@pytest.mark.asyncio
async def test_materialize_api_call_lowers_non_empty_payload_into_inline_value_instance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_api_ontology  # noqa: F401

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        runtime_index = runtime_context.index
        request_class_config, request_attribute_name, request_attribute_value = (
            _select_runtime_inline_request_contract(runtime_index)
        )
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )

        lane = ApiMetaRuntimeLane(
            branch_id=uuid4(),
        )
        class_config_id = request_class_config.id
        assert class_config_id is not None
        api_snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=lane.actor_id,
            branch_id=lane.branch_id,
            projection_hash=api_projection_hash,
            api_name="openai-api",
            endpoint_refs=("openai-api.door.open",),
            endpoint_request_class_config_ids={
                "openai-api.door.open": class_config_id,
            },
            endpoint_fulfillment_names={"openai-api.door.open": ("open",)},
            api_graph_function_config_id=_select_runtime_function_config_id(
                runtime_index
            ),
        )
        assert api_snapshot.endpoint_ids_by_ref["openai-api.door.open"]
        branch_id = lane.branch_id

        ir = resolve_api_invocation_ir(
            api_ownership=(
                APIOwnership(
                    name="openai-api",
                    source_path="runtime-proof",
                    capabilities=(
                        APICapabilityOwnership(
                            name="door",
                            source_path="runtime-proof",
                            endpoints=(
                                APICapabilityEndpointOwnership(
                                    name="open",
                                    source_path="runtime-proof",
                                    request_config=APICapabilityEndpointRequestConfigOwnership(
                                        class_ref=str(
                                            request_class_config.class_fqn or ""
                                        ),
                                        source_path="runtime-proof",
                                    ),
                                ),
                            ),
                        ),
                    ),
                    graphs=(),
                ),
            ),
            endpoint_ref="openai-api.door.open",
            request_payload={request_attribute_name: request_attribute_value},
        )
        source_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        target_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_call_projection_hash,
        )

        result = await materialize_api_call(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            source_lane=source_lane,
            target_lane=target_lane,
            ir=ir,
        )

        request_model = result.api_call.request_model
        assert request_model is not None
        assert request_model.class_config_id == request_class_config.id
        request_attributes = resolve_inline_value_instance_attributes(
            inline_value_instance=request_model,
            class_config=request_class_config,
        )
        assert len(request_attributes) == 1
        assert request_attributes[0].attribute_config.name == request_attribute_name
        assert (
            decode_oig_attribute_value(
                request_attributes[0].attribute.value_root,
                class_configs_by_id=runtime_index.class_configs_by_id,
            )
            == request_attribute_value
        )
