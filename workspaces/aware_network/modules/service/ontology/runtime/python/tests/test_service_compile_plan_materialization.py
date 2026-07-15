from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import (
    MaterializationLaneContext,
    MaterializationRunReceipt,
)
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
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_identity_ontology.stable_ids import stable_role_config_id
from aware_orm.session.session import Session
from aware_service_ontology.service.service_enums import (
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_id,
    stable_service_operation_config_id,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from _service_runtime_test_paths import REPO_ROOT
from aware_service_runtime.builder import (
    emit_service_compile_plan_artifact,
)
from aware_service_runtime.compile import compile_service_workspace
from aware_service_runtime.materialization.service import (
    _hydrate_committed_role_reference_context,
    _resolve_canonical_service_config_projection_hash,
    _resolve_committed_role_config_id,
    build_service_definition_materialization_plan,
    decode_service_definition_materialization_step_payload,
    load_service_compile_plan_payloads,
    materialize_service_compile_plan_ontology,
    materialize_service_definition_ontology,
    resolve_service_definition_materialization_specs,
    stable_service_role_reference_branch_id,
)
from aware_service_runtime.materialization import service as service_materialization

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


def test_service_materialization_uses_service_owned_branch_identities() -> None:
    source = Path(service_materialization.__file__).read_text(encoding="utf-8")
    assert "aware_history.stable_ids" not in source
    assert "stable_" + "branch_id" not in source
    assert stable_service_role_reference_branch_id(
        role_ref="Identity.Actor_Reader"
    ) == stable_service_role_reference_branch_id(role_ref="identity.actor_reader")


def _service_compile_plan_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
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


def _build_service_compile_plan_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_compile_plan_package_manifest_paths(repo_root),
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


def _seed_boot_environment(*, environment_id: UUID) -> tuple[UUID, UUID, UUID]:
    from aware_history.stable_ids import stable_branch_id

    process_id = uuid4()
    thread_id = uuid4()
    boot_branch_id = stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )
    return process_id, thread_id, boot_branch_id


async def _hydrate_committed_session(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> Session:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert target_head is not None
    assert target_head.get("commit_id") is not None
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


def _resolve_class_config_id_by_fqn_suffix(
    index: MetaGraphRuntimeIndex,
    *,
    class_fqn_suffix: str,
) -> UUID:
    for class_config in index.class_configs_by_id.values():
        if (class_config.class_fqn or "").endswith(class_fqn_suffix):
            return class_config.id
    raise AssertionError(f"Missing ClassConfig with suffix {class_fqn_suffix!r}")


def _select_runtime_function_config_id(index: MetaGraphRuntimeIndex) -> UUID:
    class_configs = sorted(
        index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        for function_link in sorted(
            class_config.class_config_function_configs,
            key=lambda item: (item.position, str(item.id)),
        ):
            if function_link.function_config_id is not None:
                return function_link.function_config_id
    raise AssertionError("Expected one runtime FunctionConfig for API snapshot setup")


def _write_service_workspace(
    root: Path,
    *,
    include_contract_surface: bool = False,
) -> Path:
    return _write_service_workspace_fixture(
        root,
        include_contract_surface=include_contract_surface,
    )


def _write_service_workspace_fixture(
    root: Path,
    *,
    include_contract_surface: bool = False,
    include_role_requirement: bool = False,
    include_price: bool = True,
    receipt_policy: str | None = None,
) -> Path:
    toml_path = root / "aware.service.toml"
    _ = toml_path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "compiler-service"',
                'fqn_prefix = "aware_compiler_service"',
                "",
                "[build]",
                'sources_dir = "services/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "service_ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    bindings = root / "services" / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    source_lines = [
        "service compiler {",
        "    api api_anchor",
    ]
    if include_contract_surface:
        source_lines.extend(
            [
                "    experience actor_identity",
                "",
            ]
        )
    else:
        source_lines.append("")
    source_lines.extend(
        [
            "    operation projection_resolution {",
            "        endpoint api_anchor.projection_resolution.projection_resolution",
        ]
    )
    if receipt_policy is not None:
        source_lines.append(f"        receipt {receipt_policy}")
    if include_price:
        source_lines.extend(
            [
                "        price {",
                "            coin USD",
                "            type fixed",
                "            fixed_amount 2.5",
                '            effective_from "2026-04-21T00:00:00Z"',
                "        }",
            ]
        )
    if include_contract_surface:
        source_lines.extend(
            [
                "        view api_anchor.roles",
                "        role identity.actor_reader {",
                "            access operation",
                "            scope operation projection_resolution",
                "            class_instance_identity_required true",
                "            role_assignment_binding_required true",
                "        }",
            ]
        )
    elif include_role_requirement:
        source_lines.extend(
            [
                "        role identity.actor_reader {",
                "            access operation",
                "            scope operation projection_resolution",
                "            class_instance_identity_required true",
                "            role_assignment_binding_required true",
                "        }",
            ]
        )
    source_lines.extend(
        [
            "    }",
        ]
    )
    if include_contract_surface:
        source_lines.extend(
            [
                "",
                "    contract actor_subscription {",
                "        kind subscription",
                "        projection_experience actor_identity",
                "        grant operation projection_resolution {",
                "            access operation",
                "        }",
                "        grant actor_role identity.actor_reader {",
                "            access service",
                "            scope service default",
                "            class_instance_identity_required false",
                "            role_assignment_binding_required true",
                "        }",
                "    }",
            ]
        )
    source_lines.extend(["}", ""])
    _ = (bindings / "compiler.services.aware").write_text(
        "\n".join(source_lines),
        encoding="utf-8",
    )
    return toml_path


def _build_service_compile_payload(
    tmp_path: Path,
    *,
    include_contract_surface: bool = False,
    include_role_requirement: bool = False,
    include_price: bool = True,
    receipt_policy: str | None = None,
    stream_mode: str | None = None,
) -> dict[str, object]:
    package_root = tmp_path / "compiler_service_workspace"
    package_root.mkdir(parents=True, exist_ok=True)
    toml_path = _write_service_workspace_fixture(
        package_root,
        include_contract_surface=include_contract_surface,
        include_role_requirement=include_role_requirement,
        include_price=include_price,
        receipt_policy=receipt_policy,
    )
    if stream_mode is not None:
        api_runtime_dir = (
            package_root / ".aware" / "api" / "runtime" / "api-anchor-service-api"
        )
        api_runtime_dir.mkdir(parents=True, exist_ok=True)
        _ = (api_runtime_dir / "api.compile_plan.json").write_text(
            json.dumps(
                {
                    "api_ontology": [
                        {
                            "capability_endpoint_stream_configs": [
                                {
                                    "api_name": "api_anchor",
                                    "capability_name": "projection_resolution",
                                    "endpoint_name": "projection_resolution",
                                    "stream_mode": stream_mode,
                                }
                            ]
                        }
                    ]
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    compile_result = compile_service_workspace(
        toml_path=toml_path, repo_root=package_root
    )
    if compile_result.compile_plan is None:
        raise AssertionError(
            "Service compile result must include a compile plan in service_ontology mode"
        )

    _ = emit_service_compile_plan_artifact(
        plan=compile_result.compile_plan,
        runtime_package_dir=package_root
        / ".aware"
        / "service"
        / "runtime"
        / "compiler-service",
        repo_root=package_root,
    )
    payloads = load_service_compile_plan_payloads(repo_root=package_root)
    if len(payloads) != 1:
        raise AssertionError(
            f"Expected one Service compile payload, got {len(payloads)}"
        )
    return payloads[0]


@pytest.mark.asyncio
async def test_materialize_service_compile_plan_requires_explicit_workspace_root(
    tmp_path: Path,
) -> None:
    runtime = SimpleNamespace(manifest_path=tmp_path / "runtime.manifest.json")

    with pytest.raises(RuntimeError, match="explicit workspace_root"):
        await materialize_service_compile_plan_ontology(
            runtime=runtime,
            index=cast(MetaGraphRuntimeIndex, object()),
            actor_id=None,
            lane=cast(MaterializationLaneContext, object()),
        )


@pytest.mark.asyncio
async def test_materialize_service_compile_plan_loads_from_explicit_workspace_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    runtime_dir = workspace_root / ".aware" / "service" / "runtime" / "proof-service"
    runtime_dir.mkdir(parents=True)
    compile_plan_payload = {"package_name": "proof-service", "service_configs": []}
    (runtime_dir / "service.compile_plan.json").write_text(
        json.dumps(compile_plan_payload, sort_keys=True),
        encoding="utf-8",
    )
    runtime = SimpleNamespace(manifest_path=tmp_path / "ignored" / "runtime.json")
    captured: dict[str, object] = {}
    expected_receipt = cast(MaterializationRunReceipt, object())

    async def _materialize_service_definition_ontology(**kwargs: object) -> object:
        captured.update(kwargs)
        return expected_receipt

    monkeypatch.setattr(
        service_materialization,
        "materialize_service_definition_ontology",
        _materialize_service_definition_ontology,
    )

    result = await materialize_service_compile_plan_ontology(
        runtime=runtime,
        index=cast(MetaGraphRuntimeIndex, object()),
        actor_id=None,
        lane=cast(MaterializationLaneContext, object()),
        workspace_root=workspace_root,
    )

    assert result is expected_receipt
    assert captured["runtime"] is runtime
    assert captured["compile_plan_payloads"] == [compile_plan_payload]


async def _materialize_committed_api_definition(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    api_lane: MaterializationLaneContext,
    stream_mode: str | None = None,
) -> None:
    endpoint_ref = "api_anchor.projection_resolution.projection_resolution"
    await commit_api_reference_snapshot(
        index=index,
        branch_id=api_lane.branch_id,
        projection_hash=api_lane.projection_hash,
        actor_id=actor_id,
        api_name="api_anchor",
        endpoint_refs=(endpoint_ref,),
        endpoint_request_class_config_ids={
            endpoint_ref: _resolve_class_config_id_by_fqn_suffix(
                index,
                class_fqn_suffix="aware_api.api.Api",
            )
        },
        endpoint_stream_modes=(
            {endpoint_ref: stream_mode} if stream_mode is not None else None
        ),
        endpoint_fulfillment_names={endpoint_ref: ("projection_resolution",)},
        api_graph_function_config_id=_select_runtime_function_config_id(index),
    )


def test_service_materialization_specs_and_plan_from_compile_payload(
    tmp_path: Path,
) -> None:
    payload = _build_service_compile_payload(
        tmp_path,
        include_contract_surface=True,
        receipt_policy="read_model",
    )
    specs = resolve_service_definition_materialization_specs(
        compile_plan_payloads=[payload]
    )
    assert len(specs) == 1

    spec = specs[0]
    assert spec.package_name == "compiler-service"
    assert spec.source_path == "services/bindings/compiler.services.aware"
    assert spec.service_config.name == "compiler"
    assert len(spec.service_config.apis) == 1
    assert spec.service_config.apis[0].api_ref == "api_anchor"
    assert len(spec.service_config.experiences) == 1
    assert spec.service_config.experiences[0].experience_ref == "actor_identity"
    assert len(spec.service_config.service_operation_configs) == 1
    operation_config = spec.service_config.service_operation_configs[0]
    assert operation_config.name == "projection_resolution"
    assert operation_config.admission_mode == "contract_required"
    assert operation_config.fulfillment_kind == "view"
    assert operation_config.receipt_policy == "read_model"
    assert operation_config.price is not None
    assert operation_config.price.coin_symbol == "USD"
    assert operation_config.price.fixed_amount == Decimal("2.5")
    assert operation_config.api_endpoints[0].endpoint_ref == (
        "api_anchor.projection_resolution.projection_resolution"
    )
    assert tuple(view.view_ref for view in operation_config.api_views) == (
        "api_anchor.roles",
    )
    assert tuple(role.role_ref for role in operation_config.role_requirements) == (
        "identity.actor_reader",
    )
    assert operation_config.role_requirements[0].access_scope == "operation"
    assert operation_config.role_requirements[0].scope_kind == "operation"
    assert operation_config.role_requirements[0].scope_ref == "projection_resolution"
    assert (
        operation_config.role_requirements[0].class_instance_identity_required is True
    )
    assert (
        operation_config.role_requirements[0].role_assignment_binding_required is True
    )

    assert len(spec.service_config.contract_configs) == 1
    contract_config = spec.service_config.contract_configs[0]
    assert contract_config.name == "actor_subscription"
    assert contract_config.default_kind == "subscription"
    assert contract_config.projection_experience_ref == "actor_identity"
    assert tuple(grant.operation_ref for grant in contract_config.operation_grants) == (
        "projection_resolution",
    )
    assert contract_config.operation_grants[0].access_scope == "operation"
    assert tuple(grant.role_ref for grant in contract_config.actor_role_grants) == (
        "identity.actor_reader",
    )
    assert contract_config.actor_role_grants[0].access_scope == "service"
    assert contract_config.actor_role_grants[0].scope_kind == "service"
    assert contract_config.actor_role_grants[0].scope_ref == "default"
    assert (
        contract_config.actor_role_grants[0].class_instance_identity_required is False
    )
    assert contract_config.actor_role_grants[0].role_assignment_binding_required is True

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="service_config_projection_hash",
    )
    plan = build_service_definition_materialization_plan(lane=lane, specs=specs)
    assert plan.module_id == "service"
    assert plan.pipeline_id == "service.compile_plan.ontology"
    assert len(plan.steps) == 1
    assert plan.steps[0].step_kind == "service.definition.ontology"

    decoded = decode_service_definition_materialization_step_payload(
        plan.steps[0].payload
    )
    assert decoded == spec


@pytest.mark.asyncio
async def test_service_materialization_executes_commit_backed_definition_path(
    tmp_path: Path,
) -> None:
    service_payload = _build_service_compile_payload(
        tmp_path,
        include_price=False,
        receipt_policy="read_model",
    )
    repo_root = REPO_ROOT

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_compile_plan_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        index = _runtime_index(runtime)
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        service_config_projection_hash = (
            _resolve_canonical_service_config_projection_hash(index)
        )

        environment_id = uuid4()
        branch_id = uuid4()

        boot_process_id, boot_thread_id, _boot_branch_id = _seed_boot_environment(
            environment_id=environment_id
        )

        api_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        service_config_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )

        await _materialize_committed_api_definition(
            index=index,
            actor_id=None,
            api_lane=api_lane,
        )
        service_receipt = await materialize_service_definition_ontology(
            runtime=runtime,
            index=index,
            actor_id=None,
            lane=service_config_lane,
            compile_plan_payloads=[service_payload],
        )
        assert service_receipt is not None
        assert service_receipt.status == "succeeded"
        assert len(service_receipt.steps) == 1

        step = service_receipt.steps[0]
        assert step.status == "succeeded"
        assert step.commit_id is not None
        assert step.head_commit_id is not None
        assert step.details["package_name"] == "compiler-service"
        assert step.details["service_name"] == "compiler"
        assert (
            step.details["source_path"] == "services/bindings/compiler.services.aware"
        )
        assert step.details["service_config_id"] == str(
            stable_service_config_id(name="compiler")
        )
        assert step.details["service_config_api_count"] == 1
        assert step.details["service_config_api_projection_count"] == 0
        assert step.details["service_operation_config_count"] == 1
        assert step.details["service_operation_price_binding_count"] == 0
        assert step.details["service_operation_endpoint_binding_count"] == 1
        service_operation_config_id = stable_service_operation_config_id(
            service_config_id=stable_service_config_id(name="compiler"),
            name="projection_resolution",
        )
        scratch = await _hydrate_committed_session(
            index=index,
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )
        operation_config = scratch.imap_get(
            ServiceOperationConfig,
            service_operation_config_id,
        )
        assert operation_config is not None
        assert operation_config.fulfillment_kind is ServiceOperationFulfillmentKind.view


@pytest.mark.asyncio
async def test_service_materialization_strengthens_committed_stream_endpoint_to_actuation(
    tmp_path: Path,
) -> None:
    service_payload = _build_service_compile_payload(
        tmp_path,
        include_price=False,
        stream_mode="server",
    )
    repo_root = REPO_ROOT
    aware_root = tmp_path / "aware_root_stream_actuation"

    with IsolatedMetaAwareRoot(aware_root, persistence_backend="fs"):
        runtime = _build_service_compile_plan_meta_runtime(
            repo_root,
            aware_root=aware_root,
        )
        index = _runtime_index(runtime)
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        service_config_projection_hash = (
            _resolve_canonical_service_config_projection_hash(index)
        )
        environment_id = uuid4()
        branch_id = uuid4()
        boot_process_id, boot_thread_id, _boot_branch_id = _seed_boot_environment(
            environment_id=environment_id
        )
        api_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        service_config_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )

        await _materialize_committed_api_definition(
            index=index,
            actor_id=None,
            api_lane=api_lane,
            stream_mode="server",
        )
        receipt = await materialize_service_definition_ontology(
            runtime=runtime,
            index=index,
            actor_id=None,
            lane=service_config_lane,
            compile_plan_payloads=[service_payload],
        )
        assert receipt is not None
        assert receipt.status == "succeeded"

        operation_config_id = stable_service_operation_config_id(
            service_config_id=stable_service_config_id(name="compiler"),
            name="projection_resolution",
        )
        scratch = await _hydrate_committed_session(
            index=index,
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )
        operation_config = scratch.imap_get(
            ServiceOperationConfig,
            operation_config_id,
        )
        assert operation_config is not None
        assert (
            operation_config.fulfillment_kind
            is ServiceOperationFulfillmentKind.actuation
        )


def test_service_materialization_rejects_mixed_stream_and_unary_operation() -> None:
    with pytest.raises(RuntimeError, match="mix streaming and unary"):
        service_materialization._resolve_committed_service_operation_fulfillment_kind(
            service_name="compiler",
            operation_name="mixed",
            planned_kind=ServiceOperationFulfillmentKind.coordination,
            receipt_policy=ServiceOperationReceiptPolicy.committed,
            endpoint_stream_modes=("server", None),
            has_api_views=False,
        )


def test_service_materialization_rejects_read_model_stream_operation() -> None:
    with pytest.raises(RuntimeError, match="cannot use read_model"):
        service_materialization._resolve_committed_service_operation_fulfillment_kind(
            service_name="compiler",
            operation_name="stream_view",
            planned_kind=ServiceOperationFulfillmentKind.view,
            receipt_policy=ServiceOperationReceiptPolicy.read_model,
            endpoint_stream_modes=("server",),
            has_api_views=False,
        )


@pytest.mark.asyncio
async def test_service_materialization_ensures_committed_role_config_refs(
    tmp_path: Path,
) -> None:
    service_payload = _build_service_compile_payload(
        tmp_path,
        include_role_requirement=True,
        include_price=False,
    )
    repo_root = REPO_ROOT

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_role_config_refs",
        persistence_backend="fs",
    ):
        runtime = _build_service_compile_plan_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root_role_config_refs",
        )
        index = _runtime_index(runtime)
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Api",
        )
        role_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="RoleConfig",
        )
        service_config_projection_hash = (
            _resolve_canonical_service_config_projection_hash(index)
        )

        environment_id = uuid4()
        branch_id = uuid4()
        boot_process_id, boot_thread_id, _boot_branch_id = _seed_boot_environment(
            environment_id=environment_id
        )
        api_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        service_config_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=service_config_projection_hash,
        )
        role_lane = MaterializationLaneContext(
            branch_id=stable_service_role_reference_branch_id(
                role_ref="identity.actor_reader",
            ),
            projection_hash=role_projection_hash,
        )

        await _materialize_committed_api_definition(
            index=index,
            actor_id=None,
            api_lane=api_lane,
        )
        assert role_lane.branch_id != service_config_lane.branch_id
        assert (
            await FSCommitStore().head(
                branch_id=role_lane.branch_id,
                projection_hash=role_projection_hash,
            )
            is None
        )

        receipt = await materialize_service_definition_ontology(
            runtime=runtime,
            index=index,
            actor_id=None,
            lane=service_config_lane,
            compile_plan_payloads=[service_payload],
        )

        assert receipt is not None
        assert receipt.status == "succeeded"
        role_context = await _hydrate_committed_role_reference_context(
            index=index,
            lane=role_lane,
        )
        assert _resolve_committed_role_config_id(
            role_context=role_context,
            role_ref="identity.actor_reader",
        ) == stable_role_config_id(name="identity.actor_reader")


@pytest.mark.asyncio
async def test_role_reference_context_hydrates_semantic_role_config_replica(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_materialization = __import__(
        "aware_service_runtime.materialization.service",
        fromlist=["_hydrate_committed_role_reference_context"],
    )
    role_config_id = stable_role_config_id(name="identity.actor_reader")
    replica_type = type(
        "RoleConfig",
        (),
        {"__module__": "aware_identity_ontology.role.role_config"},
    )
    replica = replica_type()
    replica.id = role_config_id
    replica.name = "identity.actor_reader"

    class _ReplicaSession:
        def imap_all_objects(self) -> tuple[object, ...]:
            return (replica,)

    async def _fake_hydrate_committed_lane_session(**_: object) -> _ReplicaSession:
        return _ReplicaSession()

    monkeypatch.setattr(
        service_materialization,
        "_hydrate_committed_lane_session",
        _fake_hydrate_committed_lane_session,
    )

    lane = MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="sha256:role-config",
    )

    role_context = await _hydrate_committed_role_reference_context(
        index=cast(MetaGraphRuntimeIndex, object()),
        lane=lane,
    )

    assert (
        _resolve_committed_role_config_id(
            role_context=role_context,
            role_ref="identity.actor_reader",
        )
        == role_config_id
    )
