from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID, NAMESPACE_URL, uuid5

from pydantic import ValidationError

from aware_attention_ontology.stable_ids import (
    stable_layout_config_id,
    stable_layout_config_section_config_id,
)
from aware_code.types.json import JsonValue
from aware_environment_ontology import stable_ids as environment_stable_ids
from aware_environment_service_dto.environment.environment import (
    EnvironmentProfileInstallSpec,
    EnvironmentProfileLayoutConfigSpec,
    EnvironmentProfileLayoutSectionSpec,
    EnvironmentProfileProcessConfigSpec,
    EnvironmentProfileProjectionSpec,
    EnvironmentProfileThreadConfigSpec,
    InvokeFunctionResponse,
    UpsertEnvironmentProfileRequest,
    UpsertEnvironmentProfileResponse,
)
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.environment_profile.runtime_support import (
    invoke_support,
    ocg_support,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.compile_plan_payloads import (
    _EnvironmentProfileMaterializationStepPayload,
    _EnvironmentProfileProcessMaterializationPayload,
    _EnvironmentProfileThreadLayoutMaterializationPayload,
    _EnvironmentProfileThreadLayoutSectionMaterializationPayload,
    _EnvironmentProfileThreadMaterializationPayload,
    _EnvironmentProfileThreadProjectionMaterializationPayload,
    _EnvironmentProfileViewEventTransitionMaterializationPayload,
    _expect_list,
    _expect_mapping,
    _format_step_payload_validation_error,
    _required_step_payload_token,
    load_experience_compile_plan_payloads,
)
from aware_experience.materialization.lane_state import (
    reset_generated_projection_lane as _reset_generated_projection_lane,
)
from aware_experience.program.registry_index import find_repo_root
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_utils.logging import logger


class RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...

    @property
    def invoker(self) -> object: ...


class BindMetaGraphRuntimeLane(Protocol):
    def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        branch_id: UUID,
        projection: str,
        actor_id: UUID | None,
    ) -> object: ...


class ProjectionExperienceCatalogLoader(Protocol):
    async def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        branch_ids: Sequence[UUID],
    ) -> Mapping[str, object]: ...


class ConstructorEnvironmentFunctionInvoker(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        function_id: UUID,
        args: list[JsonValue],
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
    ) -> InvokeFunctionResponse: ...


class EnvironmentProfileSpecResolver(Protocol):
    def __call__(
        self,
        *,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        external_projection_keys_by_experience_name: Mapping[str, str] | None = None,
    ) -> tuple[EnvironmentProfileMaterializationSpec, ...]: ...


class LaneHeadCommitIdResolver(Protocol):
    async def __call__(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
    ) -> UUID | None: ...


class LaneRootHydrator(Protocol):
    async def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        branch_id: UUID,
        projection_hash: str,
        root_id: UUID,
        root_type: type[Any],
    ) -> Any | None: ...


class CommitStoreFactory(Protocol):
    def __call__(self) -> FSCommitStore: ...


class EnvironmentProfileUpsertOperation(Protocol):
    async def __call__(
        self,
        request: UpsertEnvironmentProfileRequest,
    ) -> UpsertEnvironmentProfileResponse: ...


class EnvironmentProfileApiSurface(Protocol):
    upsert_environment_profile: EnvironmentProfileUpsertOperation


class EnvironmentApiSurface(Protocol):
    profile: EnvironmentProfileApiSurface


class EnvironmentApiClient(Protocol):
    environment: EnvironmentApiSurface


@dataclass(frozen=True, slots=True)
class EnvironmentProfileMaterializationDependencies:
    commit_store_factory: CommitStoreFactory
    load_projection_experience_catalog: ProjectionExperienceCatalogLoader
    invoke_constructor_environment_function: ConstructorEnvironmentFunctionInvoker
    lane_head_commit_id: LaneHeadCommitIdResolver
    hydrate_lane_root_from_head: LaneRootHydrator
    resolve_specs: EnvironmentProfileSpecResolver


_EXPERIENCE_PROFILE_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/environment-profile/snapshot-commit/v1",
)
_EXPERIENCE_PROFILE_EVENT_CONFIG_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://experience/environment-profile/event-config-snapshot-commit/v1",
)
_ENVIRONMENT_EXPERIENCE_PROJECTION_NAME = "EnvironmentExperience"
_ENVIRONMENT_EXPERIENCE_PROFILE_CONFIG_PROJECTION_NAME = (
    "EnvironmentExperienceProfileConfig"
)


@dataclass(frozen=True, slots=True)
class _EnvironmentExperienceRootEnsureResult:
    commit_id: UUID | None
    head_commit_id: UUID | None


@dataclass(frozen=True, slots=True)
class _ThreadConfigRootEnsureResult:
    thread_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None


@dataclass(frozen=True, slots=True)
class EnvironmentProfileThreadProjectionMaterializationSpec:
    projection_experience_name: str
    projection_key: str
    source_path: str
    view_key: str | None = None
    position: int | None = None
    is_default: bool = False
    narrative: str | None = None
    intent: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentProfileThreadLayoutSectionMaterializationSpec:
    section_key: str
    projection_experience_name: str
    projection_key: str
    view_key: str
    source_path: str
    key: str | None = None
    section_graph_binding_key: str | None = None
    position: int | None = None
    is_default: bool = False
    narrative: str | None = None
    intent: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentProfileThreadLayoutMaterializationSpec:
    layout_key: str
    layout_config_id: UUID
    source_path: str
    key: str | None = None
    position: int | None = None
    is_default: bool = False
    narrative: str | None = None
    intent: str | None = None
    sections: tuple[EnvironmentProfileThreadLayoutSectionMaterializationSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class EnvironmentProfileThreadMaterializationSpec:
    key: str
    thread_key: str
    source_path: str
    title: str | None = None
    description: str | None = None
    workspace_view_key: str | None = None
    position: int | None = None
    is_default: bool = False
    narrative: str | None = None
    intent: str | None = None
    state_prompt_template: str | None = None
    projection_experiences: tuple[
        EnvironmentProfileThreadProjectionMaterializationSpec, ...
    ] = ()
    layout_configs: tuple[EnvironmentProfileThreadLayoutMaterializationSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class EnvironmentProfileProcessMaterializationSpec:
    type: str
    key: str
    process_key: str
    source_path: str
    title: str | None = None
    description: str | None = None
    shape: str | None = None
    position: int | None = None
    is_bootstrap_default: bool = False
    narrative: str | None = None
    intent: str | None = None
    thread_configs: tuple[EnvironmentProfileThreadMaterializationSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class EnvironmentProfileViewEventTransitionMaterializationSpec:
    key: str
    source_projection_experience_name: str
    source_view_key: str
    trigger_event_config_ref: str
    target_projection_experience_name: str
    target_section_graph_binding_key: str
    source_path: str
    name: str | None = None
    rationale: str | None = None
    idempotency_policy: str | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentProfileMaterializationSpec:
    fqn_prefix: str
    experience_name: str
    key: str
    source_path: str
    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    process_configs: tuple[EnvironmentProfileProcessMaterializationSpec, ...] = ()
    view_event_transitions: tuple[
        EnvironmentProfileViewEventTransitionMaterializationSpec, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class _EnvironmentProfileProjectionCatalogFilterResult:
    spec: EnvironmentProfileMaterializationSpec
    skipped_thread_projection_count: int = 0
    skipped_thread_layout_count: int = 0
    skipped_thread_layout_section_count: int = 0
    skipped_view_event_transition_count: int = 0
    skipped_projection_refs: tuple[str, ...] = ()


def resolve_environment_profile_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    external_projection_keys_by_experience_name: Mapping[str, str] | None = None,
) -> tuple[EnvironmentProfileMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    projection_key_by_experience_name: dict[str, str] = {}
    for experience_name, projection_key in (
        external_projection_keys_by_experience_name or {}
    ).items():
        normalized_experience_name = (experience_name or "").strip().casefold()
        normalized_projection_key = (projection_key or "").strip()
        if not normalized_experience_name or not normalized_projection_key:
            raise RuntimeError(
                "Environment profile materialization received an invalid external projection ownership entry"
            )
        existing_projection_key = projection_key_by_experience_name.get(
            normalized_experience_name
        )
        if (
            existing_projection_key is not None
            and existing_projection_key != normalized_projection_key
        ):
            raise RuntimeError(
                "Environment profile materialization found conflicting projection keys for "
                + f"projection experience {experience_name!r}"
            )
        projection_key_by_experience_name[normalized_experience_name] = (
            normalized_projection_key
        )
    for payload in compile_plan_payloads:
        projection_rows = _expect_list(
            payload.get("projection_experience_ownership", []),
            field_name="projection_experience_ownership",
        )
        for projection_obj in projection_rows:
            projection_row = _expect_mapping(
                projection_obj, field_name="projection_experience_ownership[]"
            )
            projection_experience_name = _required_step_payload_token(
                projection_row.get("name")
            )
            projection_key = _required_step_payload_token(
                projection_row.get("projection")
            )
            normalized_projection_experience_name = (
                projection_experience_name.casefold()
            )
            existing_projection_key = projection_key_by_experience_name.get(
                normalized_projection_experience_name
            )
            if (
                existing_projection_key is not None
                and existing_projection_key != projection_key
            ):
                raise RuntimeError(
                    "Environment profile materialization found conflicting projection keys for "
                    + f"projection experience {projection_experience_name!r}"
                )
            projection_key_by_experience_name[normalized_projection_experience_name] = (
                projection_key
            )

    specs: list[EnvironmentProfileMaterializationSpec] = []
    seen_profile_keys: set[tuple[str, str]] = set()

    for payload in compile_plan_payloads:
        profile_rows = _expect_list(
            payload.get("environment_profile_ownership", []),
            field_name="environment_profile_ownership",
        )
        if not profile_rows:
            continue
        fqn_prefix = _required_step_payload_token(payload.get("fqn_prefix"))

        for profile_obj in profile_rows:
            profile_row = _expect_mapping(
                profile_obj, field_name="environment_profile_ownership[]"
            )
            experience_name = _required_step_payload_token(
                profile_row.get("experience_name")
            )
            profile_key = _required_step_payload_token(profile_row.get("key"))
            source_path = _required_step_payload_token(profile_row.get("source_path"))
            dedupe_key = (fqn_prefix.casefold(), profile_key.casefold())
            if dedupe_key in seen_profile_keys:
                raise RuntimeError(
                    "Environment profile materialization found duplicate profile keys under one experience root "
                    + f"(fqn_prefix={fqn_prefix!r}, profile_key={profile_key!r})"
                )
            seen_profile_keys.add(dedupe_key)

            process_specs: list[EnvironmentProfileProcessMaterializationSpec] = []
            process_rows = _expect_list(
                profile_row.get("process_configs", []),
                field_name="environment_profile_ownership[].process_configs",
            )
            for process_obj in process_rows:
                process_row = _expect_mapping(
                    process_obj,
                    field_name="environment_profile_ownership[].process_configs[]",
                )
                thread_specs: list[EnvironmentProfileThreadMaterializationSpec] = []
                thread_rows = _expect_list(
                    process_row.get("thread_configs", []),
                    field_name="environment_profile_ownership[].process_configs[].thread_configs",
                )
                for thread_obj in thread_rows:
                    thread_row = _expect_mapping(
                        thread_obj,
                        field_name="environment_profile_ownership[].process_configs[].thread_configs[]",
                    )
                    thread_projection_specs: list[
                        EnvironmentProfileThreadProjectionMaterializationSpec
                    ] = []
                    thread_projection_rows = _expect_list(
                        thread_row.get("projection_experiences", []),
                        field_name=(
                            "environment_profile_ownership[].process_configs[].thread_configs[]."
                            "projection_experiences"
                        ),
                    )
                    for thread_projection_obj in thread_projection_rows:
                        thread_projection_row = _expect_mapping(
                            thread_projection_obj,
                            field_name=(
                                "environment_profile_ownership[].process_configs[].thread_configs[]."
                                "projection_experiences[]"
                            ),
                        )
                        projection_experience_name = _required_step_payload_token(
                            thread_projection_row.get("projection_experience_name")
                            or thread_projection_row.get("experience_name")
                        )
                        projection_key = projection_key_by_experience_name.get(
                            projection_experience_name.casefold()
                        )
                        if projection_key is None:
                            raise RuntimeError(
                                "Environment profile materialization could not resolve projection ownership for "
                                + f"experience {projection_experience_name!r}; available ownership names="
                                + repr(
                                    tuple(
                                        sorted(projection_key_by_experience_name)[:12]
                                    )
                                )
                            )
                        thread_projection_specs.append(
                            EnvironmentProfileThreadProjectionMaterializationSpec(
                                projection_experience_name=projection_experience_name,
                                projection_key=projection_key,
                                source_path=_required_step_payload_token(
                                    thread_projection_row.get("source_path")
                                ),
                                view_key=cast(
                                    str | None, thread_projection_row.get("view_key")
                                ),
                                position=cast(
                                    int | None, thread_projection_row.get("position")
                                ),
                                is_default=bool(
                                    thread_projection_row.get("is_default", False)
                                ),
                                narrative=cast(
                                    str | None, thread_projection_row.get("narrative")
                                ),
                                intent=cast(
                                    str | None, thread_projection_row.get("intent")
                                ),
                            )
                        )

                    thread_layout_specs: list[
                        EnvironmentProfileThreadLayoutMaterializationSpec
                    ] = []
                    thread_layout_rows = _expect_list(
                        thread_row.get("layout_configs", []),
                        field_name=(
                            "environment_profile_ownership[].process_configs[].thread_configs[]."
                            "layout_configs"
                        ),
                    )
                    for thread_layout_obj in thread_layout_rows:
                        thread_layout_row = _expect_mapping(
                            thread_layout_obj,
                            field_name=(
                                "environment_profile_ownership[].process_configs[].thread_configs[]."
                                "layout_configs[]"
                            ),
                        )
                        layout_key = _required_step_payload_token(
                            thread_layout_row.get("layout_key")
                        )
                        layout_config_id_raw = thread_layout_row.get("layout_config_id")
                        layout_config_id = (
                            UUID(str(layout_config_id_raw))
                            if layout_config_id_raw is not None
                            else stable_layout_config_id(key=layout_key)
                        )
                        layout_section_specs: list[
                            EnvironmentProfileThreadLayoutSectionMaterializationSpec
                        ] = []
                        layout_section_rows = _expect_list(
                            thread_layout_row.get("sections", []),
                            field_name=(
                                "environment_profile_ownership[].process_configs[].thread_configs[]."
                                "layout_configs[].sections"
                            ),
                        )
                        for layout_section_obj in layout_section_rows:
                            layout_section_row = _expect_mapping(
                                layout_section_obj,
                                field_name=(
                                    "environment_profile_ownership[].process_configs[].thread_configs[]."
                                    "layout_configs[].sections[]"
                                ),
                            )
                            section_projection_experience_name = (
                                _required_step_payload_token(
                                    layout_section_row.get("projection_experience_name")
                                )
                            )
                            section_projection_key = (
                                projection_key_by_experience_name.get(
                                    section_projection_experience_name.casefold()
                                )
                            )
                            if section_projection_key is None:
                                raise RuntimeError(
                                    "Environment profile materialization could not resolve projection ownership for "
                                    + f"layout section experience {section_projection_experience_name!r}; "
                                    + "available ownership names="
                                    + repr(
                                        tuple(
                                            sorted(projection_key_by_experience_name)[
                                                :12
                                            ]
                                        )
                                    )
                                )
                            layout_section_specs.append(
                                EnvironmentProfileThreadLayoutSectionMaterializationSpec(
                                    section_key=_required_step_payload_token(
                                        layout_section_row.get("section_key")
                                    ),
                                    projection_experience_name=section_projection_experience_name,
                                    projection_key=section_projection_key,
                                    view_key=_required_step_payload_token(
                                        layout_section_row.get("view_key")
                                    ),
                                    source_path=_required_step_payload_token(
                                        layout_section_row.get("source_path")
                                    ),
                                    key=cast(str | None, layout_section_row.get("key")),
                                    section_graph_binding_key=cast(
                                        str | None,
                                        layout_section_row.get(
                                            "section_graph_binding_key"
                                        ),
                                    ),
                                    position=cast(
                                        int | None, layout_section_row.get("position")
                                    ),
                                    is_default=bool(
                                        layout_section_row.get("is_default", False)
                                    ),
                                    narrative=cast(
                                        str | None, layout_section_row.get("narrative")
                                    ),
                                    intent=cast(
                                        str | None, layout_section_row.get("intent")
                                    ),
                                )
                            )
                        thread_layout_specs.append(
                            EnvironmentProfileThreadLayoutMaterializationSpec(
                                layout_key=layout_key,
                                layout_config_id=layout_config_id,
                                source_path=_required_step_payload_token(
                                    thread_layout_row.get("source_path")
                                ),
                                key=cast(str | None, thread_layout_row.get("key")),
                                position=cast(
                                    int | None, thread_layout_row.get("position")
                                ),
                                is_default=bool(
                                    thread_layout_row.get("is_default", False)
                                ),
                                narrative=cast(
                                    str | None, thread_layout_row.get("narrative")
                                ),
                                intent=cast(
                                    str | None, thread_layout_row.get("intent")
                                ),
                                sections=tuple(layout_section_specs),
                            )
                        )

                    thread_specs.append(
                        EnvironmentProfileThreadMaterializationSpec(
                            key=_required_step_payload_token(thread_row.get("key")),
                            thread_key=_required_step_payload_token(
                                thread_row.get("thread_key")
                            ),
                            source_path=_required_step_payload_token(
                                thread_row.get("source_path")
                            ),
                            title=cast(str | None, thread_row.get("title")),
                            description=cast(str | None, thread_row.get("description")),
                            workspace_view_key=cast(
                                str | None, thread_row.get("workspace_view_key")
                            ),
                            position=cast(int | None, thread_row.get("position")),
                            is_default=bool(thread_row.get("is_default", False)),
                            narrative=cast(str | None, thread_row.get("narrative")),
                            intent=cast(str | None, thread_row.get("intent")),
                            state_prompt_template=cast(
                                str | None, thread_row.get("state_prompt_template")
                            ),
                            projection_experiences=tuple(thread_projection_specs),
                            layout_configs=tuple(thread_layout_specs),
                        )
                    )

                process_specs.append(
                    EnvironmentProfileProcessMaterializationSpec(
                        type=_required_step_payload_token(process_row.get("type")),
                        key=_required_step_payload_token(process_row.get("key")),
                        process_key=_required_step_payload_token(
                            process_row.get("process_key")
                        ),
                        source_path=_required_step_payload_token(
                            process_row.get("source_path")
                        ),
                        title=cast(str | None, process_row.get("title")),
                        description=cast(str | None, process_row.get("description")),
                        shape=cast(str | None, process_row.get("shape")),
                        position=cast(int | None, process_row.get("position")),
                        is_bootstrap_default=bool(
                            process_row.get("is_bootstrap_default", False)
                        ),
                        narrative=cast(str | None, process_row.get("narrative")),
                        intent=cast(str | None, process_row.get("intent")),
                        thread_configs=tuple(thread_specs),
                    )
                )

            transition_specs: list[
                EnvironmentProfileViewEventTransitionMaterializationSpec
            ] = []
            transition_rows = _expect_list(
                profile_row.get("view_event_transitions", []),
                field_name="environment_profile_ownership[].view_event_transitions",
            )
            for transition_obj in transition_rows:
                transition_row = _expect_mapping(
                    transition_obj,
                    field_name="environment_profile_ownership[].view_event_transitions[]",
                )
                trigger_event_config_ref = _required_step_payload_token(
                    transition_row.get("trigger_event_config_ref")
                    or transition_row.get("trigger_event_ref")
                )
                transition_specs.append(
                    EnvironmentProfileViewEventTransitionMaterializationSpec(
                        key=_required_step_payload_token(transition_row.get("key")),
                        source_projection_experience_name=_required_step_payload_token(
                            transition_row.get("source_projection_experience_name")
                        ),
                        source_view_key=_required_step_payload_token(
                            transition_row.get("source_view_key")
                        ),
                        trigger_event_config_ref=trigger_event_config_ref,
                        target_projection_experience_name=_required_step_payload_token(
                            transition_row.get("target_projection_experience_name")
                        ),
                        target_section_graph_binding_key=_required_step_payload_token(
                            transition_row.get("target_section_graph_binding_key")
                        ),
                        source_path=_required_step_payload_token(
                            transition_row.get("source_path")
                        ),
                        name=cast(str | None, transition_row.get("name")),
                        rationale=cast(str | None, transition_row.get("rationale")),
                        idempotency_policy=cast(
                            str | None, transition_row.get("idempotency_policy")
                        ),
                    )
                )

            specs.append(
                EnvironmentProfileMaterializationSpec(
                    fqn_prefix=fqn_prefix,
                    experience_name=experience_name,
                    key=profile_key,
                    source_path=source_path,
                    title=cast(str | None, profile_row.get("title")),
                    description=cast(str | None, profile_row.get("description")),
                    narrative=cast(str | None, profile_row.get("narrative")),
                    process_configs=tuple(process_specs),
                    view_event_transitions=tuple(
                        sorted(
                            transition_specs,
                            key=lambda item: (
                                item.key.casefold(),
                                item.source_path,
                            ),
                        )
                    ),
                )
            )

    specs.sort(key=lambda item: (item.fqn_prefix.casefold(), item.key.casefold()))
    return tuple(specs)


def build_environment_profile_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[EnvironmentProfileMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"environment_profile:{spec.experience_name}:{spec.key}",
            step_kind="experience.environment_profile",
            payload=encode_environment_profile_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.environment_profile",
        lane=lane,
        steps=steps,
    )


def encode_environment_profile_materialization_step_payload(
    *,
    spec: EnvironmentProfileMaterializationSpec,
) -> dict[str, object]:
    payload = _EnvironmentProfileMaterializationStepPayload(
        fqn_prefix=spec.fqn_prefix,
        experience_name=spec.experience_name,
        key=spec.key,
        source_path=spec.source_path,
        title=spec.title,
        description=spec.description,
        narrative=spec.narrative,
        process_configs=tuple(
            _EnvironmentProfileProcessMaterializationPayload(
                type=process_spec.type,
                key=process_spec.key,
                process_key=process_spec.process_key,
                source_path=process_spec.source_path,
                title=process_spec.title,
                description=process_spec.description,
                shape=process_spec.shape,
                position=process_spec.position,
                is_bootstrap_default=process_spec.is_bootstrap_default,
                narrative=process_spec.narrative,
                intent=process_spec.intent,
                thread_configs=tuple(
                    _EnvironmentProfileThreadMaterializationPayload(
                        key=thread_spec.key,
                        thread_key=thread_spec.thread_key,
                        source_path=thread_spec.source_path,
                        title=thread_spec.title,
                        description=thread_spec.description,
                        workspace_view_key=thread_spec.workspace_view_key,
                        position=thread_spec.position,
                        is_default=thread_spec.is_default,
                        narrative=thread_spec.narrative,
                        intent=thread_spec.intent,
                        state_prompt_template=thread_spec.state_prompt_template,
                        projection_experiences=tuple(
                            _EnvironmentProfileThreadProjectionMaterializationPayload(
                                projection_experience_name=projection_spec.projection_experience_name,
                                projection_key=projection_spec.projection_key,
                                source_path=projection_spec.source_path,
                                view_key=projection_spec.view_key,
                                position=projection_spec.position,
                                is_default=projection_spec.is_default,
                                narrative=projection_spec.narrative,
                                intent=projection_spec.intent,
                            )
                            for projection_spec in thread_spec.projection_experiences
                        ),
                        layout_configs=tuple(
                            _EnvironmentProfileThreadLayoutMaterializationPayload(
                                layout_key=layout_spec.layout_key,
                                layout_config_id=layout_spec.layout_config_id,
                                source_path=layout_spec.source_path,
                                key=layout_spec.key,
                                position=layout_spec.position,
                                is_default=layout_spec.is_default,
                                narrative=layout_spec.narrative,
                                intent=layout_spec.intent,
                                sections=tuple(
                                    _EnvironmentProfileThreadLayoutSectionMaterializationPayload(
                                        section_key=section_spec.section_key,
                                        projection_experience_name=section_spec.projection_experience_name,
                                        projection_key=section_spec.projection_key,
                                        view_key=section_spec.view_key,
                                        source_path=section_spec.source_path,
                                        key=section_spec.key,
                                        section_graph_binding_key=section_spec.section_graph_binding_key,
                                        position=section_spec.position,
                                        is_default=section_spec.is_default,
                                        narrative=section_spec.narrative,
                                        intent=section_spec.intent,
                                    )
                                    for section_spec in layout_spec.sections
                                ),
                            )
                            for layout_spec in thread_spec.layout_configs
                        ),
                    )
                    for thread_spec in process_spec.thread_configs
                ),
            )
            for process_spec in spec.process_configs
        ),
        view_event_transitions=tuple(
            _EnvironmentProfileViewEventTransitionMaterializationPayload(
                key=transition_spec.key,
                source_projection_experience_name=(
                    transition_spec.source_projection_experience_name
                ),
                source_view_key=transition_spec.source_view_key,
                trigger_event_config_ref=transition_spec.trigger_event_config_ref,
                target_projection_experience_name=(
                    transition_spec.target_projection_experience_name
                ),
                target_section_graph_binding_key=(
                    transition_spec.target_section_graph_binding_key
                ),
                source_path=transition_spec.source_path,
                name=transition_spec.name,
                rationale=transition_spec.rationale,
                idempotency_policy=transition_spec.idempotency_policy,
            )
            for transition_spec in spec.view_event_transitions
        ),
    )
    return cast(dict[str, object], payload.model_dump(mode="json"))


def decode_environment_profile_materialization_step_payload(
    payload: Mapping[str, object],
) -> EnvironmentProfileMaterializationSpec:
    try:
        step_payload = _EnvironmentProfileMaterializationStepPayload.model_validate(
            payload
        )
    except ValidationError as exc:
        raise RuntimeError(
            _format_step_payload_validation_error(exc=exc, prefix="environment_profile")
        ) from exc

    return EnvironmentProfileMaterializationSpec(
        fqn_prefix=step_payload.fqn_prefix,
        experience_name=step_payload.experience_name,
        key=step_payload.key,
        source_path=step_payload.source_path,
        title=step_payload.title,
        description=step_payload.description,
        narrative=step_payload.narrative,
        process_configs=tuple(
            EnvironmentProfileProcessMaterializationSpec(
                type=process_payload.type,
                key=process_payload.key,
                process_key=process_payload.process_key,
                source_path=process_payload.source_path,
                title=process_payload.title,
                description=process_payload.description,
                shape=process_payload.shape,
                position=process_payload.position,
                is_bootstrap_default=process_payload.is_bootstrap_default,
                narrative=process_payload.narrative,
                intent=process_payload.intent,
                thread_configs=tuple(
                    EnvironmentProfileThreadMaterializationSpec(
                        key=thread_payload.key,
                        thread_key=thread_payload.thread_key,
                        source_path=thread_payload.source_path,
                        title=thread_payload.title,
                        description=thread_payload.description,
                        workspace_view_key=thread_payload.workspace_view_key,
                        position=thread_payload.position,
                        is_default=thread_payload.is_default,
                        narrative=thread_payload.narrative,
                        intent=thread_payload.intent,
                        state_prompt_template=thread_payload.state_prompt_template,
                        projection_experiences=tuple(
                            EnvironmentProfileThreadProjectionMaterializationSpec(
                                projection_experience_name=projection_payload.projection_experience_name,
                                projection_key=projection_payload.projection_key,
                                source_path=projection_payload.source_path,
                                view_key=projection_payload.view_key,
                                position=projection_payload.position,
                                is_default=projection_payload.is_default,
                                narrative=projection_payload.narrative,
                                intent=projection_payload.intent,
                            )
                            for projection_payload in thread_payload.projection_experiences
                        ),
                        layout_configs=tuple(
                            EnvironmentProfileThreadLayoutMaterializationSpec(
                                layout_key=layout_payload.layout_key,
                                layout_config_id=(
                                    layout_payload.layout_config_id
                                    or stable_layout_config_id(
                                        key=layout_payload.layout_key
                                    )
                                ),
                                source_path=layout_payload.source_path,
                                key=layout_payload.key,
                                position=layout_payload.position,
                                is_default=layout_payload.is_default,
                                narrative=layout_payload.narrative,
                                intent=layout_payload.intent,
                                sections=tuple(
                                    EnvironmentProfileThreadLayoutSectionMaterializationSpec(
                                        section_key=section_payload.section_key,
                                        projection_experience_name=section_payload.projection_experience_name,
                                        projection_key=section_payload.projection_key,
                                        view_key=section_payload.view_key,
                                        source_path=section_payload.source_path,
                                        key=section_payload.key,
                                        section_graph_binding_key=section_payload.section_graph_binding_key,
                                        position=section_payload.position,
                                        is_default=section_payload.is_default,
                                        narrative=section_payload.narrative,
                                        intent=section_payload.intent,
                                    )
                                    for section_payload in layout_payload.sections
                                ),
                            )
                            for layout_payload in thread_payload.layout_configs
                        ),
                    )
                    for thread_payload in process_payload.thread_configs
                ),
            )
            for process_payload in step_payload.process_configs
        ),
        view_event_transitions=tuple(
            EnvironmentProfileViewEventTransitionMaterializationSpec(
                key=transition_payload.key,
                source_projection_experience_name=(
                    transition_payload.source_projection_experience_name
                ),
                source_view_key=transition_payload.source_view_key,
                trigger_event_config_ref=transition_payload.trigger_event_config_ref,
                target_projection_experience_name=(
                    transition_payload.target_projection_experience_name
                ),
                target_section_graph_binding_key=(
                    transition_payload.target_section_graph_binding_key
                ),
                source_path=transition_payload.source_path,
                name=transition_payload.name,
                rationale=transition_payload.rationale,
                idempotency_policy=transition_payload.idempotency_policy,
            )
            for transition_payload in step_payload.view_event_transitions
        ),
    )


async def materialize_experience_environment_profile_ontology(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_id: UUID,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
    prefer_snapshot_materialization: bool = False,
    allow_unresolved_projection_experiences: bool = False,
    environment_api_client: EnvironmentApiClient | None = None,
    dependencies: EnvironmentProfileMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    _ = prefer_snapshot_materialization
    external_projection_keys_by_experience_name: dict[str, str] = {}
    if projection_reference_branch_ids_by_name:
        reference_catalog = await dependencies.load_projection_experience_catalog(
            index=index,
            branch_ids=tuple(
                dict.fromkeys(projection_reference_branch_ids_by_name.values())
            ),
        )
        external_projection_keys_by_experience_name = (
            _projection_keys_by_experience_name_from_catalog(
                index=index,
                catalog=reference_catalog,
            )
        )
    specs = dependencies.resolve_specs(
        compile_plan_payloads=compile_plan_payloads,
        external_projection_keys_by_experience_name=(
            external_projection_keys_by_experience_name
        ),
    )
    if not specs:
        return None
    if environment_api_client is None:
        raise RuntimeError(
            "Experience environment profile materialization requires an "
            "Environment API client; Environment owns profile topology install."
        )
    return await _materialize_experience_environment_profile_via_environment_api(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        specs=specs,
        projection_reference_branch_ids_by_name=(
            projection_reference_branch_ids_by_name
        ),
        allow_unresolved_projection_experiences=allow_unresolved_projection_experiences,
        environment_api_client=environment_api_client,
        dependencies=dependencies,
    )


def _projection_keys_by_experience_name_from_catalog(
    *,
    index: MetaGraphRuntimeIndex,
    catalog: Mapping[str, object],
) -> dict[str, str]:
    projection_keys_by_opgi_id: dict[UUID, str] = {}
    for projection_key, (opgi_id, _view_keys) in ocg_support.build_opgi_index(
        index=index
    ).items():
        normalized_projection_key = (projection_key or "").strip()
        if not normalized_projection_key:
            continue
        existing_projection_key = projection_keys_by_opgi_id.get(opgi_id)
        if (
            existing_projection_key is not None
            and existing_projection_key != normalized_projection_key
        ):
            raise RuntimeError(
                "Environment profile materialization found conflicting runtime projection keys for "
                + f"ObjectProjectionGraphIdentity {opgi_id}"
            )
        projection_keys_by_opgi_id[opgi_id] = normalized_projection_key

    projections_by_name = cast(
        Mapping[str, ProjectionExperience],
        catalog.get("projections_by_name", {}),
    )
    projection_keys_by_experience_name: dict[str, str] = {}
    for projection_experience in projections_by_name.values():
        experience_name = (projection_experience.name or "").strip()
        if not experience_name:
            continue
        projection_key = projection_keys_by_opgi_id.get(
            projection_experience.object_projection_graph_identity_id
        )
        if projection_key is None:
            continue
        normalized_experience_name = experience_name.casefold()
        existing_projection_key = projection_keys_by_experience_name.get(
            normalized_experience_name
        )
        if (
            existing_projection_key is not None
            and existing_projection_key != projection_key
        ):
            raise RuntimeError(
                "Environment profile materialization found conflicting committed projection ownership for "
                + f"experience {experience_name!r}"
            )
        projection_keys_by_experience_name[normalized_experience_name] = projection_key
    return projection_keys_by_experience_name


async def _materialize_experience_environment_profile_via_environment_api(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    environment_id: UUID,
    process_id: UUID | None,
    thread_id: UUID | None,
    specs: Sequence[EnvironmentProfileMaterializationSpec],
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None,
    allow_unresolved_projection_experiences: bool,
    environment_api_client: EnvironmentApiClient,
    dependencies: EnvironmentProfileMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    environment_experience_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name=_ENVIRONMENT_EXPERIENCE_PROJECTION_NAME,
    )
    environment_experience_profile_config_projection_hash = (
        ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name=_ENVIRONMENT_EXPERIENCE_PROFILE_CONFIG_PROJECTION_NAME,
        )
    )
    environment_experience_build_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_experience.EnvironmentExperience"
        ),
        function_name="build",
    )
    environment_experience_create_profile_config_fn_id = (
        ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix=(
                "aware_experience_ontology.environment."
                "environment_experience.EnvironmentExperience"
            ),
            function_name="create_profile_config",
        )
    )
    environment_experience_create_profile_fn_id = (
        ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix=(
                "aware_experience_ontology.environment."
                "environment_experience.EnvironmentExperience"
            ),
            function_name="create_profile",
        )
    )
    profile_add_process_config_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_experience_profile_config."
            "EnvironmentExperienceProfileConfig"
        ),
        function_name="add_process_config",
    )
    process_add_thread_config_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_experience_process_config.EnvironmentExperienceProcessConfig"
        ),
        function_name="add_thread_config",
    )
    profile_add_projection_experience_fn_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix=(
            "aware_experience_ontology.environment."
            "environment_experience_profile_config."
            "EnvironmentExperienceProfileConfig"
        ),
        function_name="add_projection_experience",
    )
    environment_experience_profile_config_opg = index.opg_by_hash.get(
        environment_experience_profile_config_projection_hash
    )
    if environment_experience_profile_config_opg is None:
        raise RuntimeError(
            "Experience environment profile materialization missing "
            "EnvironmentExperienceProfileConfig OPG: "
            f"projection_hash={environment_experience_profile_config_projection_hash}"
        )
    environment_experience_profile_config_build_fn_id = (
        ocg_support.resolve_single_opg_constructor_function_id(
            index=index,
            object_projection_graph_id=environment_experience_profile_config_opg.id,
        )
    )

    environment_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=environment_experience_projection_hash,
    )
    plan = build_environment_profile_materialization_plan(
        lane=environment_lane,
        specs=specs,
    )

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = decode_environment_profile_materialization_step_payload(step.payload)
        if spec.view_event_transitions:
            raise RuntimeError(
                "Experience view-event transition materialization must remain "
                "Experience-owned and is not part of Environment profile topology "
                f"install: experience={spec.experience_name!r} profile={spec.key!r}"
            )
        profile_branch_id = derive_experience_reference_branch_id(
            base_branch_id=plan.lane.branch_id,
            experience_name=spec.experience_name,
        )
        environment_profile_response = await _upsert_environment_profile_via_api(
            environment_api_client=environment_api_client,
            actor_id=actor_id,
            environment_id=environment_id,
            spec=spec,
        )
        _assert_environment_profile_upsert_succeeded(
            response=environment_profile_response,
            spec=spec,
        )
        environment_profile_config_id, environment_profile_id = (
            _require_environment_profile_identity(
                response=environment_profile_response,
                spec=spec,
            )
        )
        environment_experience_id = (
            experience_stable_ids.stable_environment_experience_id(
                fqn_prefix=spec.fqn_prefix
            )
        )
        environment_experience_profile_config_id = (
            experience_stable_ids.stable_environment_experience_profile_config_id(
                environment_experience_id=environment_experience_id,
                environment_profile_config_id=environment_profile_config_id,
                key=spec.key,
            )
        )
        environment_experience_profile_id = (
            experience_stable_ids.stable_environment_experience_profile_id(
                environment_experience_id=environment_experience_id,
                profile_config_id=environment_experience_profile_config_id,
                environment_profile_id=environment_profile_id,
            )
        )
        root_result = await _ensure_environment_experience_profile_lane_root(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            lane=MaterializationLaneContext(
                branch_id=profile_branch_id,
                projection_hash=plan.lane.projection_hash,
            ),
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            function_id=environment_experience_build_fn_id,
            spec=spec,
            dependencies=dependencies,
        )
        profile_lane = MaterializationLaneContext(
            branch_id=profile_branch_id,
            projection_hash=environment_experience_profile_config_projection_hash,
        )
        create_profile_config_result = (
            await invoke_support.invoke_instance_environment_function(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                environment_id=environment_id,
                process_id=process_id,
                thread_id=thread_id,
                branch_id=profile_branch_id,
                projection_hash=plan.lane.projection_hash,
                object_id=environment_experience_id,
                function_id=environment_experience_create_profile_config_fn_id,
                args=[
                    str(environment_profile_config_id),
                    spec.key,
                    None,
                    spec.title,
                    spec.description,
                    spec.narrative,
                ],
                commit=True,
            )
        )
        invoke_support.assert_invoke_succeeded(
            response=create_profile_config_result,
            label=f"EnvironmentExperience.create_profile_config({spec.key})",
        )
        create_profile_result = (
            await invoke_support.invoke_instance_environment_function(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                environment_id=environment_id,
                process_id=process_id,
                thread_id=thread_id,
                branch_id=profile_branch_id,
                projection_hash=plan.lane.projection_hash,
                object_id=environment_experience_id,
                function_id=environment_experience_create_profile_fn_id,
                args=[
                    str(environment_experience_profile_config_id),
                    str(environment_profile_id),
                    "active",
                    spec.title,
                    spec.description,
                    {},
                ],
                commit=True,
            )
        )
        invoke_support.assert_invoke_succeeded(
            response=create_profile_result,
            label=f"EnvironmentExperience.create_profile({spec.key})",
        )
        profile_root_result = (
            await _ensure_environment_experience_profile_config_branch_root(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane=profile_lane,
                environment_id=environment_id,
                process_id=process_id,
                thread_id=thread_id,
                function_id=environment_experience_profile_config_build_fn_id,
                spec=spec,
                environment_experience_id=environment_experience_id,
                environment_profile_config_id=environment_profile_config_id,
                dependencies=dependencies,
            )
        )

        projection_catalog = await dependencies.load_projection_experience_catalog(
            index=index,
            branch_ids=_environment_profile_projection_catalog_branch_ids(
                base_branch_id=plan.lane.branch_id,
                spec=spec,
                projection_reference_branch_ids_by_name=(
                    projection_reference_branch_ids_by_name
                ),
            ),
        )
        catalog_filter = _EnvironmentProfileProjectionCatalogFilterResult(spec=spec)
        if allow_unresolved_projection_experiences:
            catalog_filter = _filter_environment_profile_spec_for_projection_catalog(
                spec=spec,
                catalog=projection_catalog,
            )
            spec = catalog_filter.spec

        seen_projection_experience_ids: set[UUID] = set()
        last_commit_id = profile_root_result.commit_id or root_result.commit_id
        last_head_commit_id = (
            profile_root_result.head_commit_id or root_result.head_commit_id
        )
        process_count = 0
        thread_count = 0
        thread_projection_count = 0
        thread_layout_count = 0
        thread_layout_section_count = 0
        for process_spec in spec.process_configs:
            process_count += 1
            process_config_id = environment_stable_ids.stable_process_config_id(
                environment_profile_config_id=environment_profile_config_id,
                key=process_spec.key,
            )
            add_process_result = (
                await invoke_support.invoke_instance_environment_function(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    environment_id=environment_id,
                    process_id=process_id,
                    thread_id=thread_id,
                    branch_id=profile_branch_id,
                    projection_hash=profile_lane.projection_hash,
                    object_id=environment_experience_profile_config_id,
                    function_id=profile_add_process_config_fn_id,
                    args=[
                        process_config_id,
                        process_spec.key,
                        process_spec.title,
                        process_spec.description,
                        process_spec.position,
                        process_spec.narrative,
                        process_spec.intent,
                    ],
                    commit=True,
                )
            )
            invoke_support.assert_invoke_succeeded(
                response=add_process_result,
                label=(
                    "EnvironmentExperienceProfileConfig.add_process_config("
                    f"{process_spec.key})"
                ),
            )
            process_bridge_id = (
                experience_stable_ids.stable_environment_experience_process_config_id(
                    environment_experience_profile_config_id=(
                        environment_experience_profile_config_id
                    ),
                    process_config_id=process_config_id,
                    key=process_spec.key,
                )
            )
            for thread_spec in process_spec.thread_configs:
                thread_count += 1
                thread_config_id = environment_stable_ids.stable_thread_config_id(
                    process_config_id=process_config_id,
                    key=thread_spec.key,
                )
                add_thread_result = (
                    await invoke_support.invoke_instance_environment_function(
                        runtime=runtime,
                        index=index,
                        actor_id=actor_id,
                        environment_id=environment_id,
                        process_id=process_id,
                        thread_id=thread_id,
                        branch_id=profile_branch_id,
                        projection_hash=profile_lane.projection_hash,
                        object_id=process_bridge_id,
                        function_id=process_add_thread_config_fn_id,
                        args=[
                            thread_config_id,
                            thread_spec.key,
                            thread_spec.title,
                            thread_spec.description,
                            thread_spec.position,
                            thread_spec.narrative,
                            thread_spec.intent,
                        ],
                        commit=True,
                    )
                )
                invoke_support.assert_invoke_succeeded(
                    response=add_thread_result,
                    label=(
                        "EnvironmentExperienceProcessConfig.add_thread_config("
                        f"{process_spec.key}:{thread_spec.key})"
                    ),
                )
                for projection_spec in thread_spec.projection_experiences:
                    projection_experience_id = (
                        _resolve_projection_experience_id_for_reference(
                            catalog=projection_catalog,
                            projection_ref=projection_spec.projection_experience_name,
                            context=(
                                "Environment profile bridge projection "
                                "materialization"
                            ),
                        )
                    )
                    if projection_experience_id in seen_projection_experience_ids:
                        continue
                    seen_projection_experience_ids.add(projection_experience_id)
                    add_projection_result = (
                        await invoke_support.invoke_instance_environment_function(
                            runtime=runtime,
                            index=index,
                            actor_id=actor_id,
                            environment_id=environment_id,
                            process_id=process_id,
                            thread_id=thread_id,
                            branch_id=profile_branch_id,
                            projection_hash=profile_lane.projection_hash,
                            object_id=environment_experience_profile_config_id,
                            function_id=profile_add_projection_experience_fn_id,
                            args=[projection_experience_id],
                            commit=True,
                        )
                    )
                    invoke_support.assert_invoke_succeeded(
                        response=add_projection_result,
                        label=(
                            "EnvironmentExperienceProfileConfig.add_projection_experience("
                            f"{projection_spec.projection_experience_name})"
                        ),
                    )
                    thread_projection_count += 1
                thread_layout_count += len(thread_spec.layout_configs)
                thread_layout_section_count += sum(
                    len(layout.sections) for layout in thread_spec.layout_configs
                )

        return MaterializationStepResult(
            details={
                "fqn_prefix": spec.fqn_prefix,
                "experience_name": spec.experience_name,
                "profile_key": spec.key,
                "environment_profile_config_id": str(environment_profile_config_id),
                "environment_experience_profile_config_id": str(
                    environment_experience_profile_config_id
                ),
                "environment_experience_profile_id": str(
                    environment_experience_profile_id
                ),
                "environment_profile_id": str(environment_profile_id),
                "process_count": process_count,
                "thread_count": thread_count,
                "thread_projection_count": thread_projection_count,
                "thread_layout_count": thread_layout_count,
                "thread_layout_section_count": thread_layout_section_count,
                "profile_branch_id": str(profile_branch_id),
                "topology_owner": "environment",
                "bridge_owner": "experience",
                "skipped_unresolved_projection_refs": list(
                    catalog_filter.skipped_projection_refs
                ),
            },
            commit_id=last_commit_id,
            head_commit_id=last_head_commit_id,
        )

    executor = MaterializationExecutor()
    return await executor.run(plan=plan, runner=_runner)


async def _upsert_environment_profile_via_api(
    *,
    environment_api_client: EnvironmentApiClient,
    actor_id: UUID | None,
    environment_id: UUID,
    spec: EnvironmentProfileMaterializationSpec,
) -> UpsertEnvironmentProfileResponse:
    request = UpsertEnvironmentProfileRequest(
        actor_id=actor_id,
        environment_id=environment_id,
        profile=EnvironmentProfileInstallSpec(
            key=spec.key,
            title=spec.title,
            description=spec.description,
            narrative=spec.narrative,
            process_configs=[
                EnvironmentProfileProcessConfigSpec(
                    key=process.key,
                    type=process.type,
                    title=process.title,
                    description=process.description,
                    shape=process.shape,
                    position=process.position,
                    is_default=process.is_bootstrap_default,
                    narrative=process.narrative,
                    intent=process.intent,
                    thread_configs=[
                        EnvironmentProfileThreadConfigSpec(
                            key=thread.key,
                            title=thread.title,
                            description=thread.description,
                            workspace_view_key=thread.workspace_view_key,
                            position=thread.position,
                            is_default=thread.is_default,
                            narrative=thread.narrative,
                            intent=thread.intent,
                            state_prompt_template=thread.state_prompt_template,
                            projection_refs=[
                                EnvironmentProfileProjectionSpec(
                                    object_projection_graph_ref=(
                                        projection.projection_key
                                    ),
                                    view_key=projection.view_key,
                                    position=projection.position,
                                    is_default=projection.is_default,
                                    narrative=projection.narrative,
                                    intent=projection.intent,
                                )
                                for projection in thread.projection_experiences
                            ],
                            layout_configs=[
                                EnvironmentProfileLayoutConfigSpec(
                                    layout_key=layout.layout_key,
                                    layout_config_id=layout.layout_config_id,
                                    key=layout.key,
                                    position=layout.position,
                                    narrative=layout.narrative,
                                    intent=layout.intent,
                                    sections=[
                                        EnvironmentProfileLayoutSectionSpec(
                                            section_key=section.section_key,
                                            layout_config_section_config_id=(
                                                stable_layout_config_section_config_id(
                                                    layout_config_id=(
                                                        layout.layout_config_id
                                                    ),
                                                    section_key=section.section_key,
                                                )
                                            ),
                                            object_projection_graph_ref=(
                                                section.projection_key
                                            ),
                                            view_key=section.view_key,
                                            key=section.key,
                                            position=section.position,
                                            is_default=section.is_default,
                                            narrative=section.narrative,
                                            intent=section.intent,
                                        )
                                        for section in layout.sections
                                    ],
                                )
                                for layout in thread.layout_configs
                            ],
                        )
                        for thread in process.thread_configs
                    ],
                )
                for process in spec.process_configs
            ],
        ),
        validate_only=False,
    )
    return await environment_api_client.environment.profile.upsert_environment_profile(
        request
    )


def _assert_environment_profile_upsert_succeeded(
    *,
    response: UpsertEnvironmentProfileResponse,
    spec: EnvironmentProfileMaterializationSpec,
) -> None:
    status = (response.status or "").strip().casefold()
    if status not in {"succeeded", "success", "ok"} or response.error:
        raise RuntimeError(
            "Environment profile API install failed for Experience profile "
            f"{spec.experience_name}:{spec.key}: {response.error or response.status}"
        )


def _require_environment_profile_identity(
    *,
    response: UpsertEnvironmentProfileResponse,
    spec: EnvironmentProfileMaterializationSpec,
) -> tuple[UUID, UUID]:
    if response.environment_profile_config_id is None:
        raise RuntimeError(
            "Environment profile API install omitted EnvironmentProfileConfig identity "
            f"for Experience profile {spec.experience_name}:{spec.key}"
        )
    if response.environment_profile_id is None:
        raise RuntimeError(
            "Environment profile API install omitted applied EnvironmentProfile identity "
            f"for Experience profile {spec.experience_name}:{spec.key}"
        )
    return response.environment_profile_config_id, response.environment_profile_id


def _has_planned_threads(*, planned_processes: Sequence[Mapping[str, object]]) -> bool:
    for process_plan in planned_processes:
        threads = process_plan.get("threads")
        if isinstance(threads, list) and threads:
            return True
    return False


async def materialize_experience_compile_plan_environment_profiles(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
    environment_id: UUID,
    environment_api_client: EnvironmentApiClient,
    dependencies: EnvironmentProfileMaterializationDependencies,
) -> MaterializationRunReceipt | None:
    if not _has_planned_threads(planned_processes=planned_processes):
        return None

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_environment_profile_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_id=environment_id,
        compile_plan_payloads=compile_plan_payloads,
        environment_api_client=environment_api_client,
        dependencies=dependencies,
    )


def _optional_uuid_from_mapping(
    mapping: Mapping[str, object] | None, key: str
) -> UUID | None:
    if mapping is None:
        return None
    raw = mapping.get(key)
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw)
    return None


def _environment_profile_projection_catalog_branch_ids(
    *,
    base_branch_id: UUID,
    spec: EnvironmentProfileMaterializationSpec,
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
) -> tuple[UUID, ...]:
    refs: list[str] = [spec.experience_name]
    for process in spec.process_configs:
        for thread in process.thread_configs:
            refs.extend(
                projection.projection_experience_name
                for projection in thread.projection_experiences
            )
            for layout in thread.layout_configs:
                refs.extend(
                    section.projection_experience_name for section in layout.sections
                )
    for transition in spec.view_event_transitions:
        refs.append(transition.source_projection_experience_name)
        refs.append(transition.target_projection_experience_name)

    branch_ids: list[UUID] = [base_branch_id]
    seen: set[UUID] = {base_branch_id}
    explicit_branch_ids_by_name = {
        name.casefold().strip(): branch_id
        for name, branch_id in (projection_reference_branch_ids_by_name or {}).items()
        if name.strip()
    }
    for ref in refs:
        normalized_ref = (ref or "").strip()
        if not normalized_ref:
            continue
        candidate_refs = [normalized_ref]
        suffix_ref = normalized_ref.rsplit(":", 1)[-1].strip()
        if suffix_ref and suffix_ref != normalized_ref:
            candidate_refs.append(suffix_ref)
        for candidate_ref in candidate_refs:
            explicit_branch_id = explicit_branch_ids_by_name.get(
                candidate_ref.casefold()
            )
            if explicit_branch_id is not None and explicit_branch_id not in seen:
                seen.add(explicit_branch_id)
                branch_ids.append(explicit_branch_id)
            branch_id = derive_experience_reference_branch_id(
                base_branch_id=base_branch_id,
                experience_name=candidate_ref,
            )
            if branch_id in seen:
                continue
            seen.add(branch_id)
            branch_ids.append(branch_id)
    return tuple(branch_ids)


def _filter_environment_profile_spec_for_projection_catalog(
    *,
    spec: EnvironmentProfileMaterializationSpec,
    catalog: Mapping[str, object],
) -> _EnvironmentProfileProjectionCatalogFilterResult:
    skipped_refs: set[str] = set()
    skipped_thread_projection_count = 0
    skipped_thread_layout_count = 0
    skipped_thread_layout_section_count = 0
    skipped_view_event_transition_count = 0

    def _has_projection(projection_ref: str) -> bool:
        projection = _projection_experience_for_reference_or_none(
            catalog=catalog,
            projection_ref=projection_ref,
            context="Environment profile unresolved projection filtering",
        )
        if projection is None or projection.id is None:
            token = (projection_ref or "").strip()
            if token:
                skipped_refs.add(token)
            return False
        return True

    process_specs: list[EnvironmentProfileProcessMaterializationSpec] = []
    for process in spec.process_configs:
        thread_specs: list[EnvironmentProfileThreadMaterializationSpec] = []
        for thread in process.thread_configs:
            projection_specs = tuple(
                projection
                for projection in thread.projection_experiences
                if _has_projection(projection.projection_experience_name)
            )
            skipped_thread_projection_count += len(thread.projection_experiences) - len(
                projection_specs
            )

            layout_specs: list[EnvironmentProfileThreadLayoutMaterializationSpec] = []
            for layout in thread.layout_configs:
                section_specs = tuple(
                    section
                    for section in layout.sections
                    if _has_projection(section.projection_experience_name)
                )
                skipped_thread_layout_section_count += len(layout.sections) - len(
                    section_specs
                )
                if layout.sections and not section_specs:
                    skipped_thread_layout_count += 1
                    continue
                layout_specs.append(replace(layout, sections=section_specs))

            thread_specs.append(
                replace(
                    thread,
                    projection_experiences=projection_specs,
                    layout_configs=tuple(layout_specs),
                )
            )
        process_specs.append(replace(process, thread_configs=tuple(thread_specs)))

    transition_specs = tuple(
        transition
        for transition in spec.view_event_transitions
        if _has_projection(transition.source_projection_experience_name)
        and _has_projection(transition.target_projection_experience_name)
    )
    skipped_view_event_transition_count = len(spec.view_event_transitions) - len(
        transition_specs
    )

    return _EnvironmentProfileProjectionCatalogFilterResult(
        spec=replace(
            spec,
            process_configs=tuple(process_specs),
            view_event_transitions=transition_specs,
        ),
        skipped_thread_projection_count=skipped_thread_projection_count,
        skipped_thread_layout_count=skipped_thread_layout_count,
        skipped_thread_layout_section_count=skipped_thread_layout_section_count,
        skipped_view_event_transition_count=skipped_view_event_transition_count,
        skipped_projection_refs=tuple(sorted(skipped_refs, key=str.casefold)),
    )


def _resolve_projection_experience_id_for_reference(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
    context: str,
) -> UUID:
    projection = _resolve_projection_experience_for_reference(
        catalog=catalog,
        projection_ref=projection_ref,
        context=context,
    )
    if projection.id is None:
        raise RuntimeError(
            f"{context} requires ProjectionExperience.id "
            + f"(projection_ref={projection_ref!r})"
        )
    return projection.id


def _resolve_projection_experience_for_reference(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
    context: str,
) -> ProjectionExperience:
    projection = _projection_experience_for_reference_or_none(
        catalog=catalog,
        projection_ref=projection_ref,
        context=context,
    )
    if projection is not None:
        return projection
    raise RuntimeError(
        f"{context} could not resolve ProjectionExperience "
        + f"(projection_ref={projection_ref!r})"
    )


def _projection_experience_for_reference_or_none(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
    context: str,
) -> ProjectionExperience | None:
    normalized_ref = (projection_ref or "").strip().casefold()
    projections_by_name = cast(
        Mapping[str, ProjectionExperience], catalog["projections_by_name"]
    )
    projection = projections_by_name.get(normalized_ref)
    if projection is not None:
        return projection
    suffix_matches = [
        item
        for key, item in projections_by_name.items()
        if key.rsplit(":", 1)[-1] == normalized_ref
    ]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        raise RuntimeError(
            f"{context} resolved projection ambiguously "
            + f"(projection_ref={projection_ref!r})"
        )
    return None


def _resolve_projection_experience_view_for_transition(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
    view_key: str,
) -> ProjectionExperienceView:
    projection = _resolve_projection_experience_for_reference(
        catalog=catalog,
        projection_ref=projection_ref,
        context="Environment profile transition source materialization",
    )
    if projection.id is None:
        raise RuntimeError(
            "Environment profile transition source projection is missing id "
            + f"(projection_ref={projection_ref!r})"
        )
    views_by_projection_and_name = cast(
        Mapping[tuple[UUID, str], ProjectionExperienceView],
        catalog["views_by_projection_and_name"],
    )
    view = views_by_projection_and_name.get((projection.id, view_key.casefold()))
    if view is None:
        raise RuntimeError(
            "Environment profile transition could not resolve source ProjectionExperienceView "
            + f"(projection_ref={projection_ref!r}, view_key={view_key!r})"
        )
    return view


def _resolve_projection_experience_section_graph_binding_for_transition(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
    binding_key: str,
) -> ProjectionExperienceSectionGraphBinding:
    projection = _resolve_projection_experience_for_reference(
        catalog=catalog,
        projection_ref=projection_ref,
        context="Environment profile transition target materialization",
    )
    if projection.id is None:
        raise RuntimeError(
            "Environment profile transition target projection is missing id "
            + f"(projection_ref={projection_ref!r})"
        )
    bindings_by_projection_and_key = cast(
        Mapping[tuple[UUID, str], ProjectionExperienceSectionGraphBinding],
        catalog["section_graph_bindings_by_projection_and_key"],
    )
    binding = bindings_by_projection_and_key.get(
        (projection.id, binding_key.casefold())
    )
    if binding is None:
        raise RuntimeError(
            "Environment profile transition could not resolve target "
            + "ProjectionExperienceSectionGraphBinding "
            + f"(projection_ref={projection_ref!r}, binding_key={binding_key!r})"
        )
    return binding


async def _ensure_environment_experience_profile_lane_root(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    function_id: UUID,
    spec: EnvironmentProfileMaterializationSpec,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    dependencies: EnvironmentProfileMaterializationDependencies,
) -> _EnvironmentExperienceRootEnsureResult:
    existing_head_commit_id = await dependencies.lane_head_commit_id(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if existing_head_commit_id is not None:
        expected_root_id = experience_stable_ids.stable_environment_experience_id(
            fqn_prefix=spec.fqn_prefix
        )
        try:
            existing_root = await dependencies.hydrate_lane_root_from_head(
                index=index,
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
                root_id=expected_root_id,
                root_type=EnvironmentExperience,
            )
        except Exception as exc:
            logger.warning(
                "Environment profile materialization reset generated profile lane "
                "because existing root could not hydrate: "
                "branch_id=%s projection_hash=%s fqn_prefix=%s profile_key=%s error=%s",
                lane.branch_id,
                lane.projection_hash,
                spec.fqn_prefix,
                spec.key,
                exc,
            )
            _reset_generated_projection_lane(
                store=dependencies.commit_store_factory(),
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
            )
        else:
            if (
                existing_root is not None
                and existing_root.fqn_prefix == spec.fqn_prefix
                and existing_root.title == spec.title
                and existing_root.description == spec.description
            ):
                return _EnvironmentExperienceRootEnsureResult(
                    commit_id=None,
                    head_commit_id=existing_head_commit_id,
                )

            _reset_generated_projection_lane(
                store=dependencies.commit_store_factory(),
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
            )
            logger.warning(
                "Environment profile materialization reset generated profile lane "
                "because existing root did not match source contract: "
                "branch_id=%s projection_hash=%s fqn_prefix=%s profile_key=%s",
                lane.branch_id,
                lane.projection_hash,
                spec.fqn_prefix,
                spec.key,
            )

    result = await dependencies.invoke_constructor_environment_function(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        function_id=function_id,
        args=[spec.fqn_prefix, spec.title, spec.description],
    )
    invoke_support.assert_invoke_succeeded(
        response=result,
        label=(
            "EnvironmentExperience.build"
            + f"({spec.fqn_prefix}:{spec.experience_name}:{spec.key})"
        ),
    )
    return _EnvironmentExperienceRootEnsureResult(
        commit_id=result.commit_id,
        head_commit_id=result.object_instance_graph_commit_id,
    )


async def _ensure_environment_experience_profile_config_branch_root(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    function_id: UUID,
    spec: EnvironmentProfileMaterializationSpec,
    environment_experience_id: UUID,
    environment_profile_config_id: UUID,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    dependencies: EnvironmentProfileMaterializationDependencies,
) -> _EnvironmentExperienceRootEnsureResult:
    existing_head_commit_id = await dependencies.lane_head_commit_id(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    expected_profile_config_id = (
        experience_stable_ids.stable_environment_experience_profile_config_id(
            environment_experience_id=environment_experience_id,
            environment_profile_config_id=environment_profile_config_id,
            key=spec.key,
        )
    )
    if existing_head_commit_id is not None:
        try:
            existing_root = await dependencies.hydrate_lane_root_from_head(
                index=index,
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
                root_id=expected_profile_config_id,
                root_type=EnvironmentExperienceProfileConfig,
            )
        except Exception as exc:
            logger.warning(
                "Environment profile materialization reset generated profile-config branch "
                "because existing profile-config root could not hydrate: "
                "branch_id=%s projection_hash=%s profile_config_id=%s error=%s",
                lane.branch_id,
                lane.projection_hash,
                expected_profile_config_id,
                exc,
            )
            _reset_generated_projection_lane(
                store=dependencies.commit_store_factory(),
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
            )
        else:
            if (
                existing_root is not None
                and existing_root.environment_experience_id == environment_experience_id
                and existing_root.environment_profile_config_id
                == environment_profile_config_id
                and existing_root.key == spec.key
                and existing_root.title == spec.title
                and existing_root.description == spec.description
                and existing_root.narrative == spec.narrative
            ):
                return _EnvironmentExperienceRootEnsureResult(
                    commit_id=None,
                    head_commit_id=existing_head_commit_id,
                )

            _reset_generated_projection_lane(
                store=dependencies.commit_store_factory(),
                branch_id=lane.branch_id,
                projection_hash=lane.projection_hash,
            )
            logger.warning(
                "Environment profile materialization reset generated profile-config branch "
                "because existing profile-config root did not match source contract: "
                "branch_id=%s projection_hash=%s profile_config_id=%s",
                lane.branch_id,
                lane.projection_hash,
                expected_profile_config_id,
            )

    result = await dependencies.invoke_constructor_environment_function(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        function_id=function_id,
        args=[
            str(environment_profile_config_id),
            spec.key,
            None,
            spec.title,
            spec.description,
            spec.narrative,
        ],
    )
    invoke_support.assert_invoke_succeeded(
        response=result,
        label=(
            "EnvironmentExperienceProfileConfig.build_via_environment_experience"
            + f"({spec.fqn_prefix}:{spec.experience_name}:{spec.key})"
        ),
    )
    return _EnvironmentExperienceRootEnsureResult(
        commit_id=result.commit_id,
        head_commit_id=result.object_instance_graph_commit_id,
    )


async def _ensure_thread_config_lane_root(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    function_id: UUID,
    process_config_id: UUID,
    thread_spec: EnvironmentProfileThreadMaterializationSpec,
    dependencies: EnvironmentProfileMaterializationDependencies,
) -> _ThreadConfigRootEnsureResult:
    thread_config_id = environment_stable_ids.stable_thread_config_id(
        process_config_id=process_config_id,
        key=thread_spec.key,
    )
    store = dependencies.commit_store_factory()
    existing_head = cast(
        Mapping[str, object] | None,
        await store.head(
            branch_id=lane.branch_id,
            projection_hash=lane.projection_hash,
        ),
    )
    existing_commit_id = _optional_uuid_from_mapping(existing_head, "commit_id")
    if existing_commit_id is not None:
        existing_root_id = _optional_uuid_from_mapping(existing_head, "root_object_id")
        if existing_root_id == thread_config_id:
            return _ThreadConfigRootEnsureResult(
                thread_config_id=thread_config_id,
                commit_id=None,
                head_commit_id=(
                    _optional_uuid_from_mapping(
                        existing_head,
                        "object_instance_graph_commit_id",
                    )
                    or existing_commit_id
                ),
            )

        _reset_generated_projection_lane(
            store=store,
            branch_id=lane.branch_id,
            projection_hash=lane.projection_hash,
        )
        logger.warning(
            "Environment profile materialization reset generated thread_config lane "
            "because existing root did not match source contract: "
            "branch_id=%s projection_hash=%s process_config_id=%s thread_key=%s",
            lane.branch_id,
            lane.projection_hash,
            process_config_id,
            thread_spec.key,
        )

    result = await dependencies.invoke_constructor_environment_function(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        function_id=function_id,
        args=[
            str(process_config_id),
            thread_spec.key,
            thread_spec.title,
            thread_spec.description,
            thread_spec.workspace_view_key,
            thread_spec.position,
            thread_spec.narrative,
            thread_spec.intent,
            thread_spec.state_prompt_template,
        ],
    )
    invoke_support.assert_invoke_succeeded(
        response=result,
        label=f"ThreadConfig.build_via_process_config({process_config_id}:{thread_spec.key})",
    )
    return _ThreadConfigRootEnsureResult(
        thread_config_id=thread_config_id,
        commit_id=result.commit_id,
        head_commit_id=result.object_instance_graph_commit_id,
    )
