from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import logging
import time
from typing import Protocol, cast
from uuid import UUID

from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_config_section_config_id,
)
from aware_code.types import JsonArray, JsonObject
from aware_environment_service_dto.environment import environment as environment_dto
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphResolveProjectionRequest,
    OntologyGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyRuntimeArtifactSet,
)
from aware_environment.branching import stable_environment_thread_branch_id
from aware_environment.environment.identity import environment_id_for_key
from aware_environment.environment.profile_runtime import (
    EnvironmentProfileTopologyRuntimeCatalog,
    build_environment_profile_topology_runtime_catalog,
)
from aware_environment.stable_ids import (
    stable_boot_process_id,
    stable_boot_thread_id,
    stable_environment_profile_config_id,
    stable_environment_profile_id,
    stable_process_config_id,
    stable_thread_config_id,
)
from aware_environment_ontology.stable_ids import (
    stable_thread_config_layout_config_id,
    stable_thread_config_object_projection_graph_id,
)
from aware_service_runtime.api_ingress.host_context import ServiceApiHostContext


logger = logging.getLogger(__name__)


class _OntologyGraphClient(Protocol):
    async def resolve_projection(
        self,
        request: OntologyGraphResolveProjectionRequest,
    ) -> OntologyGraphResolveProjectionResponse: ...


class _OntologyApiClient(Protocol):
    graph: _OntologyGraphClient


class _OntologyServiceApiClient(Protocol):
    ontology: _OntologyApiClient


@dataclass(frozen=True, slots=True)
class _ProfilePlanCounts:
    process_count: int
    thread_count: int
    projection_ref_count: int
    layout_count: int
    layout_section_count: int
    layout_section_projection_ref_count: int

    @property
    def invoke_function_count(self) -> int:
        return (
            2
            + self.process_count
            + self.thread_count
            + self.projection_ref_count
            + self.layout_count
            + self.layout_section_count
        )

    @property
    def resolve_projection_count(self) -> int:
        return self.projection_ref_count + self.layout_section_projection_ref_count

    @property
    def ontology_call_count(self) -> int:
        return self.invoke_function_count + self.resolve_projection_count


@dataclass(frozen=True, slots=True)
class EnvironmentOntologyProfileBackend:
    """Environment-owned installer for generic EnvironmentProfile topology."""

    ontology_api_client_provider: Callable[[], object | None] | None = None
    runtime_artifact_source_payloads: tuple[Mapping[str, object], ...] = ()
    host_environment_id_provider: Callable[[], UUID | None] | None = None
    host_environment_config_id_provider: Callable[[], UUID | None] | None = None
    host_environment_key: str | None = None

    async def upsert_environment_profile(
        self,
        *,
        request: environment_dto.UpsertEnvironmentProfileRequest,
        host_context: ServiceApiHostContext,
    ) -> environment_dto.UpsertEnvironmentProfileResponse:
        install_request = _hosted_environment_request(
            request=request,
            host_environment_id_provider=self.host_environment_id_provider,
            host_environment_config_id_provider=(
                self.host_environment_config_id_provider
            ),
            host_environment_key=self.host_environment_key,
        )
        plan = _build_profile_plan(request=install_request)
        process_id, thread_id, environment_branch_id, profile_config_branch_id = (
            _request_lanes(
                request=install_request,
                environment_profile_config_id=plan.environment_profile_config_id,
            )
        )
        plan_counts = _profile_plan_counts(plan=plan)
        install_started_at = time.perf_counter()
        logger.info(
            "Environment profile topology install started: "
            "profile_key=%s environment_id=%s caller_environment_id=%s "
            "environment_config_id=%s environment_profile_config_id=%s "
            "environment_profile_id=%s validate_only=%s topology_seed_count=%s "
            "process_count=%s thread_count=%s projection_ref_count=%s "
            "layout_count=%s layout_section_count=%s "
            "expected_invoke_function_count=%s "
            "expected_resolve_projection_count=%s expected_ontology_call_count=%s",
            plan.profile_key,
            install_request.environment_id,
            request.environment_id,
            plan.environment_config_id,
            plan.environment_profile_config_id,
            plan.environment_profile_id,
            bool(request.validate_only),
            len(request.topology_seeds),
            plan_counts.process_count,
            plan_counts.thread_count,
            plan_counts.projection_ref_count,
            plan_counts.layout_count,
            plan_counts.layout_section_count,
            plan_counts.invoke_function_count,
            plan_counts.resolve_projection_count,
            plan_counts.ontology_call_count,
        )
        if request.topology_seeds:
            _log_profile_install_finished(
                started_at=install_started_at,
                plan=plan,
                status="unsupported",
                counts=plan_counts,
            )
            return _upsert_response(
                request=install_request,
                plan=plan,
                status="unsupported",
                error=(
                    "environment_profile_topology_seed_install_requires_"
                    "environment_owned_seed_ontology"
                ),
                process_id=process_id,
                thread_id=thread_id,
                branch_id=environment_branch_id,
            )
        if request.validate_only:
            _log_profile_install_finished(
                started_at=install_started_at,
                plan=plan,
                status="planned",
                counts=plan_counts,
            )
            return _upsert_response(
                request=install_request,
                plan=plan,
                status="planned",
                process_id=process_id,
                thread_id=thread_id,
                branch_id=environment_branch_id,
            )

        ontology_client = _require_ontology_api_client(
            provider=self.ontology_api_client_provider,
        )
        catalog = _resolve_environment_profile_topology_catalog(
            artifact_source_payloads=self.runtime_artifact_source_payloads,
        )

        await _invoke_function(
            host_context=host_context,
            request=install_request,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=profile_config_branch_id,
            projection_hash=catalog.environment_profile_config_projection_hash,
            call_target=environment_dto.InvokeFunctionCallTarget.opg_constructor,
            object_id=None,
            object_projection_graph_id=(
                catalog.environment_profile_config_object_projection_graph_id
            ),
            function_id=catalog.profile_config_build_function_id,
            args=[
                plan.environment_config_id,
                plan.profile_key,
                install_request.profile.title,
                install_request.profile.description,
                install_request.profile.narrative,
            ],
            label=f"EnvironmentProfileConfig.build({plan.profile_key})",
        )

        await _invoke_function(
            host_context=host_context,
            request=install_request,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=environment_branch_id,
            projection_hash=catalog.environment_projection_hash,
            object_id=install_request.environment_id,
            object_projection_graph_id=catalog.environment_object_projection_graph_id,
            function_id=catalog.environment_apply_profile_function_id,
            args=[
                plan.environment_profile_config_id,
                install_request.profile.title,
                install_request.profile.description,
                "active",
                JsonObject(),
            ],
            label=f"Environment.apply_profile({plan.profile_key})",
        )

        for process_plan in plan.processes:
            process_spec = process_plan.spec
            await _invoke_function(
                host_context=host_context,
                request=install_request,
                process_id=process_id,
                thread_id=thread_id,
                branch_id=profile_config_branch_id,
                projection_hash=catalog.environment_profile_config_projection_hash,
                object_id=plan.environment_profile_config_id,
                object_projection_graph_id=(
                    catalog.environment_profile_config_object_projection_graph_id
                ),
                function_id=catalog.profile_config_create_process_config_function_id,
                args=[
                    process_spec.type,
                    process_plan.key,
                    process_spec.title,
                    process_spec.description,
                    process_spec.shape,
                    process_spec.position,
                    process_spec.is_default,
                    process_spec.narrative,
                    process_spec.intent,
                ],
                label=(
                    "EnvironmentProfileConfig.create_process_config("
                    f"{process_plan.key})"
                ),
            )
            for thread_plan in process_plan.threads:
                thread_spec = thread_plan.spec
                await _invoke_function(
                    host_context=host_context,
                    request=install_request,
                    process_id=process_id,
                    thread_id=thread_id,
                    branch_id=profile_config_branch_id,
                    projection_hash=catalog.environment_profile_config_projection_hash,
                    object_id=process_plan.process_config_id,
                    object_projection_graph_id=(
                        catalog.environment_profile_config_object_projection_graph_id
                    ),
                    function_id=catalog.process_create_thread_config_function_id,
                    args=[
                        thread_plan.key,
                        thread_spec.title,
                        thread_spec.description,
                        thread_spec.workspace_view_key,
                        thread_spec.position,
                        thread_spec.is_default,
                        thread_spec.narrative,
                        thread_spec.intent,
                        thread_spec.state_prompt_template,
                    ],
                    label=f"ProcessConfig.create_thread_config({thread_plan.key})",
                )
                for projection_plan in thread_plan.projections:
                    object_projection_graph_id = (
                        await _resolve_object_projection_graph_id(
                            ontology_client=ontology_client,
                            request=install_request,
                            ref=projection_plan.spec.object_projection_graph_ref,
                        )
                    )
                    await _invoke_function(
                        host_context=host_context,
                        request=install_request,
                        process_id=process_id,
                        thread_id=thread_id,
                        branch_id=profile_config_branch_id,
                        projection_hash=(
                            catalog.environment_profile_config_projection_hash
                        ),
                        object_id=thread_plan.thread_config_id,
                        object_projection_graph_id=(
                            catalog.environment_profile_config_object_projection_graph_id
                        ),
                        function_id=(
                            catalog.thread_add_object_projection_graph_function_id
                        ),
                        args=[
                            object_projection_graph_id,
                            projection_plan.spec.view_key,
                            projection_plan.spec.position,
                            projection_plan.spec.is_default,
                            projection_plan.spec.narrative,
                            projection_plan.spec.intent,
                        ],
                        label=(
                            "ThreadConfig.add_object_projection_graph("
                            f"{thread_plan.key}:{projection_plan.spec.object_projection_graph_ref})"
                        ),
                    )
                for layout_plan in thread_plan.layouts:
                    layout_spec = layout_plan.spec
                    await _invoke_function(
                        host_context=host_context,
                        request=install_request,
                        process_id=process_id,
                        thread_id=thread_id,
                        branch_id=profile_config_branch_id,
                        projection_hash=(
                            catalog.environment_profile_config_projection_hash
                        ),
                        object_id=thread_plan.thread_config_id,
                        object_projection_graph_id=(
                            catalog.environment_profile_config_object_projection_graph_id
                        ),
                        function_id=catalog.thread_add_layout_config_function_id,
                        args=[
                            layout_plan.layout_config_id,
                            layout_plan.key,
                            layout_spec.position,
                            layout_spec.narrative,
                            layout_spec.intent,
                        ],
                        label=(
                            "ThreadConfig.add_layout_config("
                            f"{thread_plan.key}:{layout_plan.key})"
                        ),
                    )
                    for section_plan in layout_plan.sections:
                        section_spec = section_plan.spec
                        object_projection_graph_id = (
                            await _resolve_object_projection_graph_id(
                                ontology_client=ontology_client,
                                request=install_request,
                                ref=section_spec.object_projection_graph_ref,
                            )
                            if section_spec.object_projection_graph_ref
                            else None
                        )
                        await _invoke_function(
                            host_context=host_context,
                            request=install_request,
                            process_id=process_id,
                            thread_id=thread_id,
                            branch_id=profile_config_branch_id,
                            projection_hash=(
                                catalog.environment_profile_config_projection_hash
                            ),
                            object_id=layout_plan.thread_layout_config_id,
                            object_projection_graph_id=(
                                catalog.environment_profile_config_object_projection_graph_id
                            ),
                            function_id=catalog.layout_add_section_function_id,
                            args=[
                                section_plan.layout_config_section_config_id,
                                object_projection_graph_id,
                                section_spec.key,
                                section_spec.position,
                                section_spec.is_default,
                                section_spec.narrative,
                                section_spec.intent,
                            ],
                            label=(
                                "ThreadConfigLayoutConfig.add_section("
                                f"{layout_plan.key}:{section_spec.section_key})"
                            ),
                        )

        response = _upsert_response(
            request=install_request,
            plan=plan,
            status="succeeded",
            process_id=process_id,
            thread_id=thread_id,
            branch_id=environment_branch_id,
        )
        _log_profile_install_finished(
            started_at=install_started_at,
            plan=plan,
            status=response.status,
            counts=plan_counts,
        )
        return response

    async def provision_environment_profile(
        self,
        *,
        request: environment_dto.ProvisionEnvironmentProfileRequest,
        host_context: ServiceApiHostContext,
    ) -> environment_dto.ProvisionEnvironmentProfileResponse:
        _ = host_context
        return environment_dto.ProvisionEnvironmentProfileResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=request.branch_id,
            projection_hash=request.projection_hash,
            status="unsupported",
            error=(
                "environment_profile_provision_requires_environment_owned_"
                "runtime_seed_ontology"
            ),
            environment_profile_id=request.environment_profile_id,
        )


@dataclass(frozen=True, slots=True)
class _LayoutSectionPlan:
    spec: environment_dto.EnvironmentProfileLayoutSectionSpec
    layout_config_section_config_id: UUID


@dataclass(frozen=True, slots=True)
class _LayoutPlan:
    spec: environment_dto.EnvironmentProfileLayoutConfigSpec
    layout_config_id: UUID
    thread_layout_config_id: UUID
    key: str
    sections: tuple[_LayoutSectionPlan, ...]


@dataclass(frozen=True, slots=True)
class _ProjectionPlan:
    spec: environment_dto.EnvironmentProfileProjectionSpec
    object_projection_graph_id: UUID | None


@dataclass(frozen=True, slots=True)
class _ThreadPlan:
    spec: environment_dto.EnvironmentProfileThreadConfigSpec
    key: str
    thread_config_id: UUID
    projections: tuple[_ProjectionPlan, ...]
    layouts: tuple[_LayoutPlan, ...]


@dataclass(frozen=True, slots=True)
class _ProcessPlan:
    spec: environment_dto.EnvironmentProfileProcessConfigSpec
    key: str
    process_config_id: UUID
    threads: tuple[_ThreadPlan, ...]


@dataclass(frozen=True, slots=True)
class _ProfilePlan:
    profile_key: str
    environment_config_id: UUID
    environment_profile_config_id: UUID
    environment_profile_id: UUID
    processes: tuple[_ProcessPlan, ...]


def _profile_plan_counts(*, plan: _ProfilePlan) -> _ProfilePlanCounts:
    thread_count = 0
    projection_ref_count = 0
    layout_count = 0
    layout_section_count = 0
    layout_section_projection_ref_count = 0
    for process in plan.processes:
        thread_count += len(process.threads)
        for thread in process.threads:
            projection_ref_count += len(thread.projections)
            layout_count += len(thread.layouts)
            for layout in thread.layouts:
                layout_section_count += len(layout.sections)
                layout_section_projection_ref_count += sum(
                    1
                    for section in layout.sections
                    if (section.spec.object_projection_graph_ref or "").strip()
                )
    return _ProfilePlanCounts(
        process_count=len(plan.processes),
        thread_count=thread_count,
        projection_ref_count=projection_ref_count,
        layout_count=layout_count,
        layout_section_count=layout_section_count,
        layout_section_projection_ref_count=layout_section_projection_ref_count,
    )


def _log_profile_install_finished(
    *,
    started_at: float,
    plan: _ProfilePlan,
    status: str,
    counts: _ProfilePlanCounts,
) -> None:
    logger.info(
        "Environment profile topology install finished: "
        "profile_key=%s environment_config_id=%s environment_profile_config_id=%s "
        "environment_profile_id=%s status=%s duration_s=%.6f "
        "process_count=%s thread_count=%s projection_ref_count=%s "
        "layout_count=%s layout_section_count=%s "
        "expected_invoke_function_count=%s "
        "expected_resolve_projection_count=%s expected_ontology_call_count=%s",
        plan.profile_key,
        plan.environment_config_id,
        plan.environment_profile_config_id,
        plan.environment_profile_id,
        status,
        time.perf_counter() - started_at,
        counts.process_count,
        counts.thread_count,
        counts.projection_ref_count,
        counts.layout_count,
        counts.layout_section_count,
        counts.invoke_function_count,
        counts.resolve_projection_count,
        counts.ontology_call_count,
    )


def _build_profile_plan(
    *,
    request: environment_dto.UpsertEnvironmentProfileRequest,
) -> _ProfilePlan:
    profile_key = _required_key(request.profile.key, "profile.key")
    environment_config_id = _required_uuid(
        request.environment_config_id,
        "environment_config_id",
    )
    environment_profile_config_id = stable_environment_profile_config_id(
        environment_config_id=environment_config_id,
        key=profile_key,
    )
    environment_profile_id = stable_environment_profile_id(
        environment_id=request.environment_id,
        profile_config_id=environment_profile_config_id,
    )
    process_plans: list[_ProcessPlan] = []
    seen_process_keys: set[str] = set()
    for process in request.profile.process_configs:
        process_key = _required_key(process.key, "profile.process_configs[].key")
        _remember_unique(process_key, seen_process_keys, "process config")
        process_config_id = stable_process_config_id(
            environment_profile_config_id=environment_profile_config_id,
            key=process_key,
        )
        thread_plans: list[_ThreadPlan] = []
        seen_thread_keys: set[str] = set()
        for thread in process.thread_configs:
            thread_key = _required_key(
                thread.key,
                "profile.process_configs[].thread_configs[].key",
            )
            _remember_unique(thread_key, seen_thread_keys, "thread config")
            thread_config_id = stable_thread_config_id(
                process_config_id=process_config_id,
                key=thread_key,
            )
            projection_plans = tuple(
                _ProjectionPlan(spec=projection, object_projection_graph_id=None)
                for projection in thread.projection_refs
            )
            layout_plans: list[_LayoutPlan] = []
            seen_layout_keys: set[str] = set()
            for layout in thread.layout_configs:
                layout_config_id = layout.layout_config_id
                layout_key = (layout.layout_key or "").strip()
                if layout_config_id is None:
                    layout_key = _required_key(
                        layout_key,
                        "profile.process_configs[].thread_configs[]."
                        "layout_configs[].layout_key",
                    )
                    layout_config_id = stable_layout_config_id(key=layout_key)
                layout_assoc_key = (layout.key or "").strip() or layout_key
                _remember_unique(layout_assoc_key, seen_layout_keys, "layout config")
                thread_layout_config_id = stable_thread_config_layout_config_id(
                    thread_config_id=thread_config_id,
                    layout_config_id=layout_config_id,
                )
                section_plans = tuple(
                    _LayoutSectionPlan(
                        spec=section,
                        layout_config_section_config_id=(
                            section.layout_config_section_config_id
                            or stable_layout_config_section_config_id(
                                layout_config_id=layout_config_id,
                                section_key=section.section_key,
                            )
                        ),
                    )
                    for section in layout.sections
                )
                layout_plans.append(
                    _LayoutPlan(
                        spec=layout,
                        layout_config_id=layout_config_id,
                        thread_layout_config_id=thread_layout_config_id,
                        key=layout_assoc_key,
                        sections=section_plans,
                    )
                )
            thread_plans.append(
                _ThreadPlan(
                    spec=thread,
                    key=thread_key,
                    thread_config_id=thread_config_id,
                    projections=projection_plans,
                    layouts=tuple(layout_plans),
                )
            )
        process_plans.append(
            _ProcessPlan(
                spec=process,
                key=process_key,
                process_config_id=process_config_id,
                threads=tuple(thread_plans),
            )
        )
    return _ProfilePlan(
        profile_key=profile_key,
        environment_config_id=environment_config_id,
        environment_profile_config_id=environment_profile_config_id,
        environment_profile_id=environment_profile_id,
        processes=tuple(process_plans),
    )


def _required_key(value: str | None, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _required_uuid(value: UUID | None, field_name: str) -> UUID:
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _remember_unique(value: str, seen: set[str], label: str) -> None:
    key = value.casefold()
    if key in seen:
        raise ValueError(f"Duplicate {label} key: {value!r}")
    seen.add(key)


def _request_lanes(
    *,
    request: environment_dto.UpsertEnvironmentProfileRequest,
    environment_profile_config_id: UUID,
) -> tuple[UUID, UUID, UUID, UUID]:
    process_id = request.process_id or stable_boot_process_id(
        environment_id=request.environment_id
    )
    thread_id = request.thread_id or stable_boot_thread_id(
        environment_id=request.environment_id
    )
    branch_id = request.branch_id or stable_environment_thread_branch_id(
        environment_id=request.environment_id,
        thread_id=thread_id,
    )
    return process_id, thread_id, branch_id, environment_profile_config_id


def _hosted_environment_request(
    *,
    request: environment_dto.UpsertEnvironmentProfileRequest,
    host_environment_id_provider: Callable[[], UUID | None] | None,
    host_environment_config_id_provider: Callable[[], UUID | None] | None,
    host_environment_key: str | None,
) -> environment_dto.UpsertEnvironmentProfileRequest:
    updates: dict[str, object] = {}
    host_environment_id = (
        host_environment_id_provider()
        if host_environment_id_provider is not None
        else None
    )
    if host_environment_id is not None:
        updates["environment_id"] = host_environment_id
    else:
        key = (host_environment_key or "").strip()
        if key:
            updates["environment_id"] = environment_id_for_key(environment_key=key)

    if request.environment_config_id is None:
        host_environment_config_id = (
            host_environment_config_id_provider()
            if host_environment_config_id_provider is not None
            else None
        )
        if host_environment_config_id is not None:
            updates["environment_config_id"] = host_environment_config_id

    if not updates:
        return request
    effective_updates = {
        key: value for key, value in updates.items() if getattr(request, key) != value
    }
    if not effective_updates:
        return request
    return request.model_copy(update=effective_updates)


def _upsert_response(
    *,
    request: environment_dto.UpsertEnvironmentProfileRequest,
    plan: _ProfilePlan,
    status: str,
    error: str | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    branch_id: UUID | None = None,
    projection_hash: str | None = None,
) -> environment_dto.UpsertEnvironmentProfileResponse:
    process_config_ids = [process.process_config_id for process in plan.processes]
    thread_config_ids = [
        thread.thread_config_id
        for process in plan.processes
        for thread in process.threads
    ]
    thread_projection_association_ids = [
        stable_thread_config_object_projection_graph_id(
            thread_config_id=thread.thread_config_id,
            object_projection_graph_id=projection.object_projection_graph_id,
        )
        for process in plan.processes
        for thread in process.threads
        for projection in thread.projections
        if projection.object_projection_graph_id is not None
    ]
    thread_layout_config_ids = [
        layout.thread_layout_config_id
        for process in plan.processes
        for thread in process.threads
        for layout in thread.layouts
    ]
    return environment_dto.UpsertEnvironmentProfileResponse(
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=process_id or request.process_id,
        thread_id=thread_id or request.thread_id,
        branch_id=branch_id or request.branch_id,
        projection_hash=projection_hash or request.projection_hash,
        status=status,
        error=error,
        environment_config_id=plan.environment_config_id,
        environment_profile_config_id=plan.environment_profile_config_id,
        environment_profile_id=plan.environment_profile_id,
        process_config_ids=_dedupe_ids(process_config_ids),
        thread_config_ids=_dedupe_ids(thread_config_ids),
        thread_projection_association_ids=_dedupe_ids(
            thread_projection_association_ids
        ),
        thread_layout_config_ids=_dedupe_ids(thread_layout_config_ids),
    )


def _require_ontology_api_client(
    *,
    provider: Callable[[], object | None] | None,
) -> _OntologyServiceApiClient:
    client = provider() if provider is not None else None
    if client is None:
        raise RuntimeError(
            "Environment profile install requires a configured Ontology service "
            "API route."
        )
    ontology = getattr(client, "ontology", None)
    if ontology is None:
        raise RuntimeError(
            "Configured Ontology service API client does not expose ontology."
        )
    if not hasattr(ontology, "graph"):
        raise RuntimeError(
            "Configured Ontology service API client must expose ontology.graph "
            "capabilities."
        )
    return cast(_OntologyServiceApiClient, client)


def _resolve_environment_profile_topology_catalog(
    *,
    artifact_source_payloads: Sequence[Mapping[str, object]],
) -> EnvironmentProfileTopologyRuntimeCatalog:
    source_payload = _select_environment_artifact_source_payload(
        artifact_source_payloads
    )
    artifact_set_payload = _artifact_set_payload(source_payload)
    if artifact_set_payload is None:
        raise RuntimeError(
            "Environment profile install requires a full Environment "
            "OntologyRuntimeArtifactSet payload with runtime projection descriptors."
        )
    return build_environment_profile_topology_runtime_catalog(
        artifact_set=OntologyRuntimeArtifactSet.model_validate(artifact_set_payload),
    )


def _select_environment_artifact_source_payload(
    artifact_source_payloads: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    matches: list[Mapping[str, object]] = []
    for payload in artifact_source_payloads:
        artifact_set = _artifact_set_payload(payload)
        if not artifact_set:
            continue
        package_name = str(artifact_set.get("package_name") or "").strip()
        fqn_prefix = str(artifact_set.get("fqn_prefix") or "").strip()
        if (
            package_name == "environment-ontology"
            or fqn_prefix == "aware_environment"
        ):
            matches.append(payload)
    if not matches:
        raise RuntimeError(
            "Environment profile install requires an Environment "
            "OntologyRuntimeArtifactSet source payload from the configured "
            "Ontology authority."
        )
    if len(matches) > 1:
        raise RuntimeError(
            "Environment profile install resolved multiple Environment "
            "OntologyRuntimeArtifactSet source payloads."
        )
    return matches[0]


def _artifact_set_payload(payload: Mapping[str, object]) -> Mapping[str, object] | None:
    direct = payload.get("ontology_runtime_artifact_set")
    if isinstance(direct, Mapping):
        return direct
    provider_payload = payload.get("provider_payload")
    if isinstance(provider_payload, Mapping):
        nested = provider_payload.get("ontology_runtime_artifact_set")
        if isinstance(nested, Mapping):
            return nested
    receipt = payload.get("receipt")
    if isinstance(receipt, Mapping):
        nested = receipt.get("ontology_runtime_artifact_set")
        if isinstance(nested, Mapping):
            return nested
    return None


async def _resolve_object_projection_graph_id(
    *,
    ontology_client: _OntologyServiceApiClient,
    request: environment_dto.UpsertEnvironmentProfileRequest,
    ref: str,
) -> UUID:
    normalized_ref = (ref or "").strip()
    if not normalized_ref:
        raise ValueError("object_projection_graph_ref is required")
    try:
        return UUID(normalized_ref)
    except ValueError:
        pass
    projection_name = (
        normalized_ref.rsplit(":", 1)[-1].strip()
        if ":" in normalized_ref
        else normalized_ref
    )
    started_at = time.perf_counter()
    logger.info(
        "Environment profile topology resolve_projection started: "
        "ref=%s projection_name=%s environment_id=%s actor_id=%s",
        normalized_ref,
        projection_name,
        request.environment_id,
        request.actor_id,
    )
    response = await ontology_client.ontology.graph.resolve_projection(
        OntologyGraphResolveProjectionRequest(
            actor_id=request.actor_id,
            projection_name=projection_name,
            include_available=True,
        )
    )
    duration_s = time.perf_counter() - started_at
    if (
        response.status.strip().casefold() not in {"succeeded", "success", "ok"}
        or response.object_projection_graph_id is None
    ):
        logger.error(
            "Environment profile topology resolve_projection failed: "
            "ref=%s projection_name=%s status=%s error=%s duration_s=%.6f",
            normalized_ref,
            projection_name,
            response.status,
            response.error,
            duration_s,
        )
        raise ValueError(
            "Could not resolve object_projection_graph_ref through Ontology "
            f"authority: {normalized_ref!r} ({response.error or response.status})"
        )
    logger.info(
        "Environment profile topology resolve_projection finished: "
        "ref=%s projection_name=%s object_projection_graph_id=%s "
        "projection_hash=%s duration_s=%.6f",
        normalized_ref,
        projection_name,
        response.object_projection_graph_id,
        response.projection_hash,
        duration_s,
    )
    return response.object_projection_graph_id


async def _invoke_function(
    *,
    host_context: ServiceApiHostContext,
    request: environment_dto.UpsertEnvironmentProfileRequest,
    process_id: UUID,
    thread_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID | None,
    object_projection_graph_id: UUID,
    function_id: UUID,
    args: Sequence[object],
    label: str,
    call_target: environment_dto.InvokeFunctionCallTarget = (
        environment_dto.InvokeFunctionCallTarget.instance
    ),
) -> None:
    graph_gateway = host_context.graph_gateway
    if graph_gateway is None:
        raise RuntimeError("Environment profile install requires a host graph gateway.")
    call_target_value = getattr(call_target, "value", str(call_target))
    invoke_request = environment_dto.InvokeFunctionRequest(
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        call_target=call_target,
        object_id=object_id,
        object_projection_graph_id=object_projection_graph_id,
        function_id=function_id,
        args=JsonArray(list(args)),
        kwargs=JsonObject(),
        commit=True,
        publish=False,
    )
    started_at = time.perf_counter()
    logger.info(
        "Environment profile topology invoke started: "
        "label=%s environment_id=%s branch_id=%s projection_hash=%s "
        "object_id=%s object_projection_graph_id=%s function_id=%s "
        "call_target=%s arg_count=%s",
        label,
        request.environment_id,
        branch_id,
        projection_hash,
        object_id,
        object_projection_graph_id,
        function_id,
        call_target_value,
        len(args),
    )
    try:
        response = await graph_gateway.invoke_function(request=invoke_request)
    except Exception:
        logger.exception(
            "Environment profile topology invoke raised: "
            "label=%s environment_id=%s branch_id=%s projection_hash=%s "
            "function_id=%s call_target=%s duration_s=%.6f",
            label,
            request.environment_id,
            branch_id,
            projection_hash,
            function_id,
            call_target_value,
            time.perf_counter() - started_at,
        )
        raise
    duration_s = time.perf_counter() - started_at
    status = str(getattr(response, "status", "") or "").strip().casefold()
    error = getattr(response, "error", None)
    if status not in {"succeeded", "success", "ok"} or error not in (None, ""):
        logger.error(
            "Environment profile topology invoke failed: "
            "label=%s status=%s error=%s commit_id=%s head_commit_id=%s "
            "duration_s=%.6f",
            label,
            status,
            error,
            getattr(response, "commit_id", None),
            getattr(response, "head_commit_id", None),
            duration_s,
        )
        raise RuntimeError(
            f"{label} failed during Environment profile install: "
            f"{error or status or 'unknown error'}"
        )
    logger.info(
        "Environment profile topology invoke finished: "
        "label=%s status=%s commit_id=%s head_commit_id=%s duration_s=%.6f",
        label,
        status,
        getattr(response, "commit_id", None),
        getattr(response, "head_commit_id", None),
        duration_s,
    )


def _dedupe_ids(ids: Sequence[UUID]) -> list[UUID]:
    seen: set[UUID] = set()
    result: list[UUID] = []
    for value in ids:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


__all__ = ["EnvironmentOntologyProfileBackend"]
