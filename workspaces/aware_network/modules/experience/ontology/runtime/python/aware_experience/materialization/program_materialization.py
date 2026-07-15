from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import ValidationError

from aware_code.types.json import JsonArray, JsonObject, JsonValue
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.environment_profile.runtime_support import ocg_support
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.compile_plan_payloads import (
    _ProgramMaterializationStepPayload,
    _expect_list,
    _expect_mapping,
    _expect_nonempty_text,
    _format_step_payload_validation_error,
    load_experience_compile_plan_payloads,
)
from aware_experience.materialization.snapshot_commit import (
    ExperienceProgramActorConfigSnapshot,
    ExperienceProgramImplActivationFieldBindingSnapshot,
    ExperienceProgramImplInstructionSnapshot,
    ExperienceProgramImplInvokeAttributeSnapshot,
    ExperienceProgramImplOutcomeFieldBindingSnapshot,
    ExperienceProgramImplReceiptFieldBindingSnapshot,
    ExperienceProgramInputSnapshot,
    ExperienceProgramPortNodeIdentitySnapshot,
    ExperienceProgramPortNodeSnapshot,
    ExperienceProgramPortSnapshot,
    commit_actor_config_snapshot,
    commit_program_config_snapshot,
    commit_program_impl_snapshot,
)
from aware_experience.program.language import (
    InvocationPlan,
    PlanActionContinuationActivationFieldBinding,
    PlanActionContinuationOutcomeFieldBinding,
    PlanActionContinuationReceiptFieldBinding,
    PlanCall,
    PlanExpectEventConfig,
    PlanExpr,
    PlanInput,
    PlanIntentActionConfig,
    PlanInvoke,
    PlanLet,
    PlanLocalRef,
    PlanPortContract,
    PlanPortProjectionNodeContract,
    PlanSymbolRef,
    decode_invocation_plan_artifact,
)
from aware_experience.program.static_expression import (
    resolve_program_static_uuid_from_plan,
)
from aware_experience.program.registry_index import find_repo_root
from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInstructionType,
    ProgramImplInvokeTargetKind,
)
from aware_experience_ontology.program.program_enums import ProgramBranchBindingMode
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex


class RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...


class PhaseRecorder(Protocol):
    def __call__(
        self,
        phase_timings_s: dict[str, float] | None,
        phase_name: str,
    ) -> AbstractContextManager[None]: ...


class ProjectionExperienceCatalogLoader(Protocol):
    async def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        branch_ids: Sequence[UUID],
    ) -> Mapping[str, object]: ...


class _FunctionConfigLike(Protocol):
    function_config_attribute_configs: Sequence[Any]


@dataclass(frozen=True, slots=True)
class ProgramMaterializationDependencies:
    phase_recorder: PhaseRecorder
    load_projection_experience_catalog: ProjectionExperienceCatalogLoader


@dataclass(frozen=True, slots=True)
class ProgramMaterializationSpec:
    ref: str
    name: str
    path: str
    dependencies: tuple[str, ...]
    required_symbols: tuple[str, ...]
    optional_symbols: tuple[str, ...]
    invocation_plan_artifact: Mapping[str, object]
    program_config_plan_artifact: Mapping[str, object] | None = None
    program_apply_calls_artifact: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _ProgramPortSnapshotResolution:
    snapshots: tuple[ExperienceProgramPortSnapshot, ...]
    port_ids_by_key: dict[str, UUID]
    port_node_ids_by_ref: dict[str, UUID]


def resolve_program_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ProgramMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    specs_by_ref: dict[str, ProgramMaterializationSpec] = {}
    for payload in compile_plan_payloads:
        program_rows = _expect_list(
            payload.get("program_ownership", []), field_name="program_ownership"
        )
        for program_obj in program_rows:
            program_row = _expect_mapping(program_obj, field_name="program_ownership[]")
            invocation_artifact_raw = program_row.get("invocation_plan_artifact")
            if invocation_artifact_raw is None:
                continue
            invocation_artifact = _expect_mapping(
                invocation_artifact_raw,
                field_name="program_ownership[].invocation_plan_artifact",
            )
            program_config_artifact_raw = program_row.get(
                "program_config_plan_artifact"
            )
            program_apply_artifact_raw = program_row.get("program_apply_calls_artifact")
            spec = ProgramMaterializationSpec(
                ref=_expect_nonempty_text(
                    program_row.get("ref"), field_name="program_ownership[].ref"
                ),
                name=_expect_nonempty_text(
                    program_row.get("name"), field_name="program_ownership[].name"
                ),
                path=_expect_nonempty_text(
                    program_row.get("path"), field_name="program_ownership[].path"
                ),
                dependencies=tuple(
                    _expect_nonempty_text(
                        item, field_name="program_ownership[].dependencies[]"
                    )
                    for item in _expect_list(
                        program_row.get("dependencies", []),
                        field_name="program_ownership[].dependencies",
                    )
                ),
                required_symbols=tuple(
                    _expect_nonempty_text(
                        item, field_name="program_ownership[].required_symbols[]"
                    )
                    for item in _expect_list(
                        program_row.get("required_symbols", []),
                        field_name="program_ownership[].required_symbols",
                    )
                ),
                optional_symbols=tuple(
                    _expect_nonempty_text(
                        item, field_name="program_ownership[].optional_symbols[]"
                    )
                    for item in _expect_list(
                        program_row.get("optional_symbols", []),
                        field_name="program_ownership[].optional_symbols",
                    )
                ),
                invocation_plan_artifact=dict(invocation_artifact),
                program_config_plan_artifact=(
                    dict(
                        _expect_mapping(
                            program_config_artifact_raw,
                            field_name="program_ownership[].program_config_plan_artifact",
                        )
                    )
                    if program_config_artifact_raw is not None
                    else None
                ),
                program_apply_calls_artifact=(
                    dict(
                        _expect_mapping(
                            program_apply_artifact_raw,
                            field_name="program_ownership[].program_apply_calls_artifact",
                        )
                    )
                    if program_apply_artifact_raw is not None
                    else None
                ),
            )
            key = spec.ref.casefold()
            existing = specs_by_ref.get(key)
            if existing is not None and existing != spec:
                raise RuntimeError(
                    "Invalid experience compile plan: duplicate program ownership entries disagree "
                    + f"(ref={spec.ref!r})"
                )
            specs_by_ref[key] = spec

    return tuple(sorted(specs_by_ref.values(), key=lambda item: item.ref.casefold()))


def build_program_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ProgramMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"program:{spec.ref}",
            step_kind="experience.program",
            payload=encode_program_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="experience",
        pipeline_id="experience.compile_plan.program",
        lane=lane,
        steps=steps,
    )


def encode_program_materialization_step_payload(
    *,
    spec: ProgramMaterializationSpec,
) -> dict[str, object]:
    payload = _ProgramMaterializationStepPayload(
        ref=spec.ref,
        name=spec.name,
        path=spec.path,
        dependencies=spec.dependencies,
        required_symbols=spec.required_symbols,
        optional_symbols=spec.optional_symbols,
        invocation_plan_artifact=dict(spec.invocation_plan_artifact),
        program_config_plan_artifact=(
            dict(spec.program_config_plan_artifact)
            if spec.program_config_plan_artifact is not None
            else None
        ),
        program_apply_calls_artifact=(
            dict(spec.program_apply_calls_artifact)
            if spec.program_apply_calls_artifact is not None
            else None
        ),
    )
    return cast(dict[str, object], payload.model_dump(mode="json"))


def decode_program_materialization_step_payload(
    payload: Mapping[str, object],
) -> ProgramMaterializationSpec:
    try:
        step_payload = _ProgramMaterializationStepPayload.model_validate(payload)
    except ValidationError as exc:
        raise RuntimeError(
            _format_step_payload_validation_error(exc=exc, prefix="program")
        ) from exc
    return ProgramMaterializationSpec(
        ref=step_payload.ref,
        name=step_payload.name,
        path=step_payload.path,
        dependencies=step_payload.dependencies,
        required_symbols=step_payload.required_symbols,
        optional_symbols=step_payload.optional_symbols,
        invocation_plan_artifact=step_payload.invocation_plan_artifact,
        program_config_plan_artifact=step_payload.program_config_plan_artifact,
        program_apply_calls_artifact=step_payload.program_apply_calls_artifact,
    )


async def materialize_experience_program_ontology(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    dependencies: ProgramMaterializationDependencies,
    phase_timings_s: dict[str, float] | None = None,
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
) -> tuple[MaterializationRunReceipt | None, MaterializationRunReceipt | None]:
    with dependencies.phase_recorder(
        phase_timings_s,
        "experience_program.resolve_program_materialization_specs",
    ):
        specs = resolve_program_materialization_specs(
            compile_plan_payloads=compile_plan_payloads
        )
    if not specs:
        return (None, None)

    with dependencies.phase_recorder(
        phase_timings_s,
        "experience_program.resolve_projection_hashes_and_plan",
    ):
        program_config_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="ProgramConfig",
        )
        program_impl_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="ProgramImpl",
        )
        program_lane = MaterializationLaneContext(
            branch_id=lane.branch_id,
            projection_hash=program_config_projection_hash,
        )
        plan = build_program_materialization_plan(lane=program_lane, specs=specs)

    async def _config_runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = decode_program_materialization_step_payload(step.payload)
        invocation_plan = decode_invocation_plan_artifact(spec.invocation_plan_artifact)
        actor_configs_by_alias = await _materialize_program_actor_configs(
            index=index,
            actor_id=actor_id,
            lane=plan.lane,
            invocation_plan=invocation_plan,
        )
        program_config_id = experience_stable_ids.stable_program_config_id(
            key=spec.name
        )
        input_snapshots = _program_input_snapshots(
            invocation_plan=invocation_plan,
        )
        port_resolution = await _resolve_program_port_snapshots(
            index=index,
            lane=plan.lane,
            program_config_id=program_config_id,
            ports=invocation_plan.ports,
            projection_reference_branch_ids_by_name=(
                projection_reference_branch_ids_by_name
            ),
            dependencies=dependencies,
        )
        config_commit = await commit_program_config_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=plan.lane.branch_id,
            projection_hash=plan.lane.projection_hash,
            key=spec.name,
            title=spec.name,
            description=f"Experience program {spec.ref}",
            narrative=None,
            intent="experience.program",
            is_default=False,
            inputs=input_snapshots,
            actor_configs=tuple(actor_configs_by_alias.values()),
            ports=port_resolution.snapshots,
        )

        return MaterializationStepResult(
            details={
                "ref": spec.ref,
                "name": spec.name,
                "program_config_id": str(config_commit.program_config.id),
                "input_count": len(input_snapshots),
                "actor_count": len(actor_configs_by_alias),
                "port_count": len(port_resolution.port_ids_by_key),
            },
            commit_id=config_commit.commit_id,
            head_commit_id=config_commit.head_commit_id,
        )

    async def _impl_runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = decode_program_materialization_step_payload(step.payload)
        invocation_plan = decode_invocation_plan_artifact(spec.invocation_plan_artifact)
        program_config_id = experience_stable_ids.stable_program_config_id(
            key=spec.name
        )
        program_impl_lane = MaterializationLaneContext(
            branch_id=plan.lane.branch_id,
            projection_hash=program_impl_projection_hash,
        )
        port_resolution = await _resolve_program_port_snapshots(
            index=index,
            lane=program_impl_lane,
            program_config_id=program_config_id,
            ports=invocation_plan.ports,
            projection_reference_branch_ids_by_name=(
                projection_reference_branch_ids_by_name
            ),
            dependencies=dependencies,
        )
        instructions = _program_impl_instruction_snapshots(
            index=index,
            program_config_id=program_config_id,
            invocation_plan=invocation_plan,
            port_ids_by_key=port_resolution.port_ids_by_key,
            port_node_ids_by_ref=port_resolution.port_node_ids_by_ref,
        )
        impl_commit = await commit_program_impl_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=program_impl_lane.branch_id,
            projection_hash=program_impl_lane.projection_hash,
            program_config_id=program_config_id,
            key=spec.name,
            instructions=instructions,
        )

        return MaterializationStepResult(
            details={
                "ref": spec.ref,
                "name": spec.name,
                "program_config_id": str(program_config_id),
                "program_impl_id": str(impl_commit.program_impl.id),
                "instruction_count": len(instructions),
            },
            commit_id=impl_commit.commit_id,
            head_commit_id=impl_commit.head_commit_id,
        )

    with dependencies.phase_recorder(
        phase_timings_s,
        "experience_program.config.run",
    ):
        config_receipt = await MaterializationExecutor().run(
            plan=plan, runner=_config_runner
        )
    with dependencies.phase_recorder(
        phase_timings_s,
        "experience_program.impl.run",
    ):
        impl_receipt = await MaterializationExecutor().run(
            plan=plan, runner=_impl_runner
        )
    return (config_receipt, impl_receipt)


async def materialize_experience_compile_plan_programs(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    planned_processes: Sequence[Mapping[str, object]],
    dependencies: ProgramMaterializationDependencies,
) -> tuple[MaterializationRunReceipt | None, MaterializationRunReceipt | None]:
    if not _has_planned_threads(planned_processes=planned_processes):
        return (None, None)

    repo_root = find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_experience_compile_plan_payloads(repo_root=repo_root)
    return await materialize_experience_program_ontology(
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
        dependencies=dependencies,
    )


def _has_planned_threads(*, planned_processes: Sequence[Mapping[str, object]]) -> bool:
    for process_plan in planned_processes:
        threads = process_plan.get("threads")
        if isinstance(threads, list) and threads:
            return True
    return False


async def _materialize_program_actor_configs(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    invocation_plan: InvocationPlan,
) -> dict[str, ExperienceProgramActorConfigSnapshot]:
    if not invocation_plan.actors:
        return {}

    actor_projection_hash = ocg_support.find_projection_hash_by_name(
        index=index,
        projection_name="ActorConfig",
    )
    actor_configs_by_alias: dict[str, ExperienceProgramActorConfigSnapshot] = {}
    for actor_contract in invocation_plan.actors:
        alias = (actor_contract.key or "").strip()
        actor_key = (actor_contract.actor or "").strip()
        if not alias or not actor_key:
            raise RuntimeError(
                "Program materialization requires non-empty actor alias and key"
            )
        actor_commit = await commit_actor_config_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=lane.branch_id,
            projection_hash=actor_projection_hash,
            key=actor_key,
        )
        actor_configs_by_alias[alias] = ExperienceProgramActorConfigSnapshot(
            alias=alias,
            actor_config_id=actor_commit.actor_config.id,
            actor_key=actor_key,
        )
    return actor_configs_by_alias


async def _resolve_program_port_snapshots(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    program_config_id: UUID,
    ports: Sequence[PlanPortContract],
    dependencies: ProgramMaterializationDependencies,
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
) -> _ProgramPortSnapshotResolution:
    if not ports:
        return _ProgramPortSnapshotResolution(
            snapshots=(),
            port_ids_by_key={},
            port_node_ids_by_ref={},
        )

    catalog = await dependencies.load_projection_experience_catalog(
        index=index,
        branch_ids=_program_projection_catalog_branch_ids(
            base_branch_id=lane.branch_id,
            ports=ports,
            projection_reference_branch_ids_by_name=(
                projection_reference_branch_ids_by_name
            ),
        ),
    )
    port_ids_by_key: dict[str, UUID] = {}
    port_node_ids_by_ref: dict[str, UUID] = {}
    snapshots: list[ExperienceProgramPortSnapshot] = []
    for port in ports:
        port_key = (port.key or "").strip()
        if not port_key:
            raise RuntimeError("Program port materialization requires port key")
        program_config_port_id = experience_stable_ids.stable_program_config_port_id(
            program_config_id=program_config_id,
            key=port_key,
        )
        projection = _resolve_projection_experience_for_program_port(
            catalog=catalog,
            projection_ref=port.projection,
        )
        if projection.id is None:
            raise RuntimeError(
                "Program port materialization requires ProjectionExperience.id"
            )
        node_snapshots: list[ExperienceProgramPortNodeSnapshot] = []
        for node_contract in port.projection_nodes:
            node_snapshot = _resolve_program_port_node_snapshot(
                catalog=catalog,
                projection=projection,
                node_contract=node_contract,
            )
            node_snapshots.append(node_snapshot)
            port_node_id = experience_stable_ids.stable_program_config_port_projection_experience_node_id(
                program_config_port_id=program_config_port_id,
                projection_experience_node_id=(
                    node_snapshot.projection_experience_node_id
                ),
                key=node_snapshot.key,
            )
            _remember_program_port_node_ref(
                ids_by_ref=port_node_ids_by_ref,
                ref=node_snapshot.key,
                port_node_id=port_node_id,
            )
            _remember_program_port_node_ref(
                ids_by_ref=port_node_ids_by_ref,
                ref=f"program.port.{port_key}.projection_node.{node_snapshot.key}",
                port_node_id=port_node_id,
            )
            if len(node_snapshots) == 1:
                _remember_program_port_node_ref(
                    ids_by_ref=port_node_ids_by_ref,
                    ref=port_key,
                    port_node_id=port_node_id,
                )
                _remember_program_port_node_ref(
                    ids_by_ref=port_node_ids_by_ref,
                    ref=f"program.port.{port_key}.projection_node",
                    port_node_id=port_node_id,
                )
        snapshots.append(
            ExperienceProgramPortSnapshot(
                projection_id=projection.id,
                key=port_key,
                intent=port.intent,
                branch_binding_mode=ProgramBranchBindingMode.reference,
                nodes=tuple(node_snapshots),
            )
        )
        port_ids_by_key[port_key] = program_config_port_id
    return _ProgramPortSnapshotResolution(
        snapshots=tuple(snapshots),
        port_ids_by_key=port_ids_by_key,
        port_node_ids_by_ref=port_node_ids_by_ref,
    )


def _remember_program_port_node_ref(
    *,
    ids_by_ref: dict[str, UUID],
    ref: str,
    port_node_id: UUID,
) -> None:
    normalized_ref = (ref or "").strip()
    if not normalized_ref:
        return
    existing = ids_by_ref.get(normalized_ref)
    if existing is not None and existing != port_node_id:
        raise RuntimeError(
            "Program port node materialization encountered ambiguous node ref "
            + f"{normalized_ref!r}"
        )
    ids_by_ref[normalized_ref] = port_node_id


def _resolve_program_port_node_snapshot(
    *,
    catalog: Mapping[str, object],
    projection: ProjectionExperience,
    node_contract: PlanPortProjectionNodeContract,
) -> ExperienceProgramPortNodeSnapshot:
    if projection.id is None:
        raise RuntimeError("Program port node materialization requires projection id")
    node_key = (node_contract.node or "").strip()
    if not node_key:
        raise RuntimeError("Program port node materialization requires node ref")
    identity_key = (getattr(node_contract, "identity", None) or "").strip() or None
    nodes_by_projection_and_key = cast(
        Mapping[tuple[UUID, str], ProjectionExperienceNode],
        catalog["nodes_by_projection_and_key"],
    )
    projection_node = nodes_by_projection_and_key.get(
        (projection.id, node_key.casefold())
    )
    if projection_node is None or projection_node.id is None:
        raise RuntimeError(
            "Program port node materialization could not resolve ProjectionExperienceNode "
            + f"(projection={projection.name!r}, node={node_key!r})"
        )
    node_snapshot_key = (node_contract.key or "").strip()
    if not node_snapshot_key:
        raise RuntimeError("Program port node materialization requires node key")
    identity_snapshot: ExperienceProgramPortNodeIdentitySnapshot | None = None
    if identity_key:
        identities_by_node_and_key = cast(
            Mapping[tuple[UUID, str], ProjectionExperienceNodeIdentity],
            catalog["identities_by_node_and_key"],
        )
        projection_node_identity = identities_by_node_and_key.get(
            (projection_node.id, identity_key.casefold())
        )
        if projection_node_identity is None or projection_node_identity.id is None:
            raise RuntimeError(
                "Program port node materialization could not resolve "
                + "ProjectionExperienceNodeIdentity "
                + f"(projection={projection.name!r}, node={node_key!r}, identity={identity_key!r})"
            )
        identity_snapshot = ExperienceProgramPortNodeIdentitySnapshot(
            projection_experience_node_identity_id=projection_node_identity.id,
            key=node_snapshot_key,
        )
    return ExperienceProgramPortNodeSnapshot(
        projection_experience_node_id=projection_node.id,
        key=node_snapshot_key,
        identity=identity_snapshot,
    )


def _program_projection_catalog_branch_ids(
    *,
    base_branch_id: UUID,
    ports: Sequence[PlanPortContract],
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
) -> tuple[UUID, ...]:
    branch_ids: list[UUID] = [base_branch_id]
    seen: set[UUID] = {base_branch_id}
    explicit_branch_ids_by_name = {
        name.casefold().strip(): branch_id
        for name, branch_id in (projection_reference_branch_ids_by_name or {}).items()
        if name.strip()
    }
    for port in ports:
        projection_ref = (port.projection or "").strip()
        if not projection_ref:
            continue
        candidate_refs = [projection_ref]
        suffix_ref = projection_ref.rsplit(":", 1)[-1].strip()
        if suffix_ref and suffix_ref != projection_ref:
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


def _resolve_projection_experience_for_program_port(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
) -> ProjectionExperience:
    projection = _projection_experience_for_reference_or_none(
        catalog=catalog,
        projection_ref=projection_ref,
    )
    if projection is not None:
        return projection
    raise RuntimeError(
        "Program port materialization could not resolve ProjectionExperience "
        + f"(projection_ref={projection_ref!r})"
    )


def _projection_experience_for_reference_or_none(
    *,
    catalog: Mapping[str, object],
    projection_ref: str,
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
            "Program port materialization resolved projection ambiguously "
            + f"(projection_ref={projection_ref!r})"
        )
    return None


def _program_input_source_to_string(expr: PlanExpr) -> str:
    if isinstance(expr, PlanSymbolRef):
        source = (expr.name or "").strip()
    elif isinstance(expr, str):
        source = expr.strip()
    else:
        raise RuntimeError(
            "Program input materialization requires source to be a symbol/string"
        )
    if not source:
        raise RuntimeError("Program input materialization requires non-empty source")
    return source


def _program_expr_to_json_object(expr: PlanExpr) -> JsonObject:
    return cast(JsonObject, _program_expr_to_json_value(expr))


def _json_object_value(payload: Mapping[str, object]) -> JsonValue:
    return cast(JsonValue, JsonObject(cast(dict[str, JsonValue], dict(payload))))


def _json_array_value(items: Sequence[JsonValue]) -> JsonValue:
    return cast(JsonValue, JsonArray(items))


def _program_expr_to_json_value(expr: PlanExpr) -> JsonValue:
    if isinstance(expr, PlanSymbolRef):
        return _json_object_value({"$expr": "symbol_ref", "name": expr.name})
    if isinstance(expr, PlanLocalRef):
        return _json_object_value({"$expr": "local_ref", "name": expr.name})
    if isinstance(expr, PlanCall):
        payload: dict[str, object] = {
            "$expr": "call",
            "target": expr.target,
            "args": _json_array_value(
                tuple(
                    _json_object_value(
                        {
                            "name": arg.name,
                            "value": _program_expr_to_json_value(arg.value),
                        }
                    )
                    for arg in expr.args
                )
            ),
        }
        if expr.object_expr is not None:
            payload["object_expr"] = _program_expr_to_json_value(expr.object_expr)
        return _json_object_value(payload)
    if isinstance(expr, list):
        return _json_object_value(
            {
                "$expr": "literal",
                "value": _json_array_value(
                    tuple(
                        _program_expr_to_json_value(cast(PlanExpr, item))
                        for item in expr
                    )
                ),
            }
        )
    if isinstance(expr, dict):
        return _json_object_value(
            {
                "$expr": "literal",
                "value": _json_object_value(
                    {
                        str(key): _program_expr_to_json_value(cast(PlanExpr, value))
                        for key, value in expr.items()
                    }
                ),
            }
        )
    return _json_object_value({"$expr": "literal", "value": cast(JsonValue, expr)})


def _program_input_snapshots(
    *,
    invocation_plan: InvocationPlan,
) -> tuple[ExperienceProgramInputSnapshot, ...]:
    snapshots: list[ExperienceProgramInputSnapshot] = []
    for position, step_item in enumerate(invocation_plan.steps):
        if not isinstance(step_item, PlanInput):
            continue
        snapshots.append(
            ExperienceProgramInputSnapshot(
                name=step_item.name,
                source=_program_input_source_to_string(step_item.source),
                required=step_item.required,
                position=position,
                attribute_type_ref=step_item.type_ref or "any",
                default_expr=(
                    _program_expr_to_json_object(step_item.default)
                    if step_item.default is not None
                    else None
                ),
            )
        )
    return tuple(snapshots)


def _program_impl_instruction_snapshots(
    *,
    index: MetaGraphRuntimeIndex,
    program_config_id: UUID,
    invocation_plan: InvocationPlan,
    port_ids_by_key: Mapping[str, UUID],
    port_node_ids_by_ref: Mapping[str, UUID],
) -> tuple[ExperienceProgramImplInstructionSnapshot, ...]:
    input_config_ids_by_name = _program_input_config_ids_by_name(
        program_config_id=program_config_id,
        invocation_plan=invocation_plan,
    )
    program_impl_id = experience_stable_ids.stable_program_impl_id(
        program_config_id=program_config_id,
        key=invocation_plan.name,
    )
    intent_ids_by_key: dict[str, UUID] = {}
    intent_sequences_by_key: dict[str, int] = {}
    for sequence, step_item in enumerate(invocation_plan.steps):
        if not isinstance(step_item, PlanIntentActionConfig):
            continue
        continuation_key = (step_item.continuation_key or "").strip()
        if not continuation_key:
            continue
        if continuation_key in intent_ids_by_key:
            raise RuntimeError(
                "Program materialization duplicate continuation intent key "
                + repr(continuation_key)
            )
        instruction_id = experience_stable_ids.stable_program_impl_instruction_id(
            program_impl_id=program_impl_id,
            sequence=sequence,
        )
        intent_ids_by_key[continuation_key] = (
            experience_stable_ids.stable_program_impl_instruction_intent_id(
                program_impl_instruction_id=instruction_id,
            )
        )
        intent_sequences_by_key[continuation_key] = sequence

    activation_bindings_by_target: dict[
        str, list[ExperienceProgramImplActivationFieldBindingSnapshot]
    ] = {}
    outcome_bindings_by_target: dict[
        str, list[ExperienceProgramImplOutcomeFieldBindingSnapshot]
    ] = {}
    receipt_bindings_by_target: dict[
        str, list[ExperienceProgramImplReceiptFieldBindingSnapshot]
    ] = {}
    claimed_target_attributes: set[tuple[str, UUID]] = set()
    for binding in invocation_plan.action_continuation_bindings:
        target_key = binding.target_intent_key
        if target_key not in intent_ids_by_key:
            raise RuntimeError(
                "Program materialization continuation target intent missing "
                + repr(target_key)
            )
        target_attribute_id = resolve_program_static_uuid_from_plan(
            binding.target_request_attribute_config_ref,
            plan=invocation_plan,
            label=f"continuation.{target_key}.target_request_attribute_config_id",
        )
        target_claim = (target_key, target_attribute_id)
        if target_claim in claimed_target_attributes:
            raise RuntimeError(
                "Program materialization continuation target attribute is ambiguous "
                + f"(target={target_key!r} attribute={target_attribute_id})"
            )
        claimed_target_attributes.add(target_claim)
        if isinstance(binding, PlanActionContinuationActivationFieldBinding):
            activation_bindings_by_target.setdefault(target_key, []).append(
                ExperienceProgramImplActivationFieldBindingSnapshot(
                    source_input_key=binding.source_input_key,
                    source_class_config_id=resolve_program_static_uuid_from_plan(
                        binding.source_class_config_ref,
                        plan=invocation_plan,
                        label=(f"continuation.{target_key}.source_class_config_id"),
                    ),
                    source_attribute_config_id=resolve_program_static_uuid_from_plan(
                        binding.source_attribute_config_ref,
                        plan=invocation_plan,
                        label=(f"continuation.{target_key}.source_attribute_config_id"),
                    ),
                    target_request_attribute_config_id=target_attribute_id,
                    required=binding.required,
                    position=binding.position,
                )
            )
            continue
        source_key = binding.source_intent_key
        source_intent_id = intent_ids_by_key.get(source_key)
        if source_intent_id is None:
            raise RuntimeError(
                "Program materialization continuation source intent missing "
                + repr(source_key)
            )
        if intent_sequences_by_key[source_key] >= intent_sequences_by_key[target_key]:
            raise RuntimeError(
                "Program materialization continuation source must precede target "
                + f"(source={source_key!r} target={target_key!r})"
            )
        if isinstance(binding, PlanActionContinuationOutcomeFieldBinding):
            outcome_bindings_by_target.setdefault(target_key, []).append(
                ExperienceProgramImplOutcomeFieldBindingSnapshot(
                    source_program_impl_instruction_intent_id=source_intent_id,
                    source_response_attribute_config_id=(
                        resolve_program_static_uuid_from_plan(
                            binding.source_response_attribute_config_ref,
                            plan=invocation_plan,
                            label=(
                                f"continuation.{source_key}.source_response_attribute_config_id"
                            ),
                        )
                    ),
                    target_request_attribute_config_id=target_attribute_id,
                    required=binding.required,
                    position=binding.position,
                )
            )
            continue
        if isinstance(binding, PlanActionContinuationReceiptFieldBinding):
            receipt_bindings_by_target.setdefault(target_key, []).append(
                ExperienceProgramImplReceiptFieldBindingSnapshot(
                    source_program_impl_instruction_intent_id=source_intent_id,
                    source_receipt_class_config_id=resolve_program_static_uuid_from_plan(
                        binding.source_receipt_class_config_ref,
                        plan=invocation_plan,
                        label=(
                            f"continuation.{source_key}.source_receipt_class_config_id"
                        ),
                    ),
                    source_receipt_attribute_config_id=(
                        resolve_program_static_uuid_from_plan(
                            binding.source_receipt_attribute_config_ref,
                            plan=invocation_plan,
                            label=(
                                f"continuation.{source_key}.source_receipt_attribute_config_id"
                            ),
                        )
                    ),
                    target_request_attribute_config_id=target_attribute_id,
                    required=binding.required,
                    position=binding.position,
                )
            )
            continue
        raise RuntimeError(
            "Program materialization unsupported continuation binding type "
            + type(binding).__name__
        )
    instructions: list[ExperienceProgramImplInstructionSnapshot] = []
    for sequence, step_item in enumerate(invocation_plan.steps):
        if isinstance(step_item, PlanInput):
            input_config_id = input_config_ids_by_name.get(step_item.name)
            if input_config_id is None:
                raise RuntimeError(
                    "Program materialization missing input config id "
                    + f"for input={step_item.name!r}"
                )
            instructions.append(
                ExperienceProgramImplInstructionSnapshot(
                    instruction_type=ProgramImplInstructionType.input,
                    sequence=sequence,
                    program_config_input_config_id=input_config_id,
                )
            )
            continue
        if isinstance(step_item, PlanLet):
            instructions.append(
                ExperienceProgramImplInstructionSnapshot(
                    instruction_type=ProgramImplInstructionType.let,
                    sequence=sequence,
                    name=step_item.name,
                    value_expr=_program_expr_to_json_object(step_item.value),
                )
            )
            continue
        if isinstance(step_item, PlanInvoke) and step_item.call.target == "bind":
            bind_port_key, bind_view_key, bind_is_active = _decode_bind_step(
                step_item.call
            )
            program_config_port_id = port_ids_by_key.get(bind_port_key)
            if program_config_port_id is None:
                raise RuntimeError(
                    "Program materialization bind references unknown port "
                    + f"{bind_port_key!r}"
                )
            instructions.append(
                ExperienceProgramImplInstructionSnapshot(
                    instruction_type=ProgramImplInstructionType.bind,
                    sequence=sequence,
                    program_config_port_id=program_config_port_id,
                    view_key=bind_view_key,
                    is_active=bind_is_active,
                )
            )
            continue
        if isinstance(step_item, PlanExpectEventConfig):
            instructions.append(
                ExperienceProgramImplInstructionSnapshot(
                    instruction_type=ProgramImplInstructionType.expect,
                    sequence=sequence,
                    event_config_id=_uuid_from_expr(step_item.ref),
                    required=step_item.required,
                )
            )
            continue
        if isinstance(step_item, PlanIntentActionConfig):
            continuation_key = (step_item.continuation_key or "").strip() or None
            instructions.append(
                ExperienceProgramImplInstructionSnapshot(
                    instruction_type=ProgramImplInstructionType.intent,
                    sequence=sequence,
                    action_config_id=resolve_program_static_uuid_from_plan(
                        step_item.action_ref,
                        plan=invocation_plan,
                        label=f"intent.{continuation_key or sequence}.action_config_id",
                    ),
                    event_config_id=resolve_program_static_uuid_from_plan(
                        step_item.event_ref,
                        plan=invocation_plan,
                        label=f"intent.{continuation_key or sequence}.event_config_id",
                    ),
                    continuation_key=continuation_key,
                    api_capability_endpoint_id=(
                        resolve_program_static_uuid_from_plan(
                            step_item.api_capability_endpoint_ref,
                            plan=invocation_plan,
                            label=f"intent.{continuation_key}.api_capability_endpoint_id",
                        )
                        if continuation_key is not None
                        else None
                    ),
                    request_class_config_id=(
                        resolve_program_static_uuid_from_plan(
                            step_item.request_class_config_ref,
                            plan=invocation_plan,
                            label=f"intent.{continuation_key}.request_class_config_id",
                        )
                        if continuation_key is not None
                        else None
                    ),
                    response_class_config_id=(
                        resolve_program_static_uuid_from_plan(
                            step_item.response_class_config_ref,
                            plan=invocation_plan,
                            label=f"intent.{continuation_key}.response_class_config_id",
                        )
                        if continuation_key is not None
                        else None
                    ),
                    activation_field_bindings=tuple(
                        activation_bindings_by_target.get(continuation_key or "", ())
                    ),
                    outcome_field_bindings=tuple(
                        outcome_bindings_by_target.get(continuation_key or "", ())
                    ),
                    receipt_field_bindings=tuple(
                        receipt_bindings_by_target.get(continuation_key or "", ())
                    ),
                )
            )
            continue
        if isinstance(step_item, PlanInvoke):
            instructions.append(
                _program_invoke_instruction_snapshot(
                    index=index,
                    program_config_id=program_config_id,
                    sequence=sequence,
                    step_item=step_item,
                    port_node_ids_by_ref=port_node_ids_by_ref,
                )
            )
            continue
        raise RuntimeError(
            "Program materialization encountered unsupported step type "
            + f"{type(step_item).__name__}"
        )
    return tuple(instructions)


def _program_invoke_instruction_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    program_config_id: UUID,
    sequence: int,
    step_item: PlanInvoke,
    port_node_ids_by_ref: Mapping[str, UUID],
) -> ExperienceProgramImplInstructionSnapshot:
    class_ref, function_name = _split_program_invoke_target(step_item.call.target)
    function_config_id = ocg_support.resolve_public_function_id(
        index=index,
        class_name_suffix=class_ref,
        function_name=function_name,
    )
    actor_alias = (step_item.actor or "").strip()
    if not actor_alias:
        raise RuntimeError(
            "Program invoke materialization requires an actor alias "
            + f"(target={step_item.call.target!r})"
        )
    port_node_id = _program_invoke_port_node_id(
        call=step_item.call,
        port_node_ids_by_ref=port_node_ids_by_ref,
    )
    target_kind = (
        ProgramImplInvokeTargetKind.construct
        if _is_constructor_function(index=index, function_config_id=function_config_id)
        else ProgramImplInvokeTargetKind.instance
    )
    return ExperienceProgramImplInstructionSnapshot(
        instruction_type=ProgramImplInstructionType.invoke,
        sequence=sequence,
        function_config_id=function_config_id,
        program_config_actor_config_id=(
            experience_stable_ids.stable_program_config_actor_config_id(
                program_config_id=program_config_id,
                alias=actor_alias,
            )
        ),
        program_config_port_projection_experience_node_id=port_node_id,
        target_kind=target_kind,
        invoke_attributes=_program_invoke_attribute_snapshots(
            index=index,
            function_config_id=function_config_id,
            call=step_item.call,
        ),
    )


def _split_program_invoke_target(target: str) -> tuple[str, str]:
    normalized = (target or "").strip()
    class_ref, separator, function_name = normalized.rpartition(".")
    if not separator or not class_ref or not function_name:
        raise RuntimeError(
            "Program invoke target must be <class-ref>.<function-name>: " + repr(target)
        )
    return class_ref, function_name


def _program_invoke_port_node_id(
    *,
    call: PlanCall,
    port_node_ids_by_ref: Mapping[str, UUID],
) -> UUID:
    object_expr = call.object_expr
    if not isinstance(object_expr, PlanSymbolRef):
        raise RuntimeError(
            "Program invoke materialization requires object_expr as a program port node symbol"
        )
    symbol = (object_expr.name or "").strip()
    port_node_id = port_node_ids_by_ref.get(symbol)
    if port_node_id is None:
        raise RuntimeError(
            "Program invoke references unknown port projection node: "
            + f"object_expr={symbol!r}"
        )
    return port_node_id


def _program_invoke_attribute_snapshots(
    *,
    index: MetaGraphRuntimeIndex,
    function_config_id: UUID,
    call: PlanCall,
) -> tuple[ExperienceProgramImplInvokeAttributeSnapshot, ...]:
    attribute_ids_by_name = _function_input_attribute_config_ids_by_name(
        index=index,
        function_config_id=function_config_id,
    )
    snapshots: list[ExperienceProgramImplInvokeAttributeSnapshot] = []
    for position, arg in enumerate(call.args):
        arg_name = (arg.name or "").strip()
        if not arg_name:
            raise RuntimeError("Program invoke argument requires non-empty name")
        attribute_config_id = attribute_ids_by_name.get(arg_name.casefold())
        if attribute_config_id is None:
            raise RuntimeError(
                "Program invoke argument could not resolve function input "
                + f"attribute: function_config_id={function_config_id} arg={arg_name!r}"
            )
        snapshots.append(
            ExperienceProgramImplInvokeAttributeSnapshot(
                attribute_config_id=attribute_config_id,
                value_expr=_program_expr_to_json_object(arg.value),
                position=position,
            )
        )
    return tuple(snapshots)


def _function_input_attribute_config_ids_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    function_config_id: UUID,
) -> dict[str, UUID]:
    function_config = _function_config_by_id(
        index=index,
        function_config_id=function_config_id,
    )
    if function_config is not None:
        result: dict[str, UUID] = {}
        for link in function_config.function_config_attribute_configs:
            if getattr(link.type, "value", link.type) != "input":
                continue
            name = (link.name or "").strip()
            attribute_config_id = getattr(link, "attribute_config_id", None)
            if attribute_config_id is None and link.attribute_config is not None:
                attribute_config_id = link.attribute_config.id
            if name and attribute_config_id is not None:
                result[name.casefold()] = attribute_config_id
        return result
    raise RuntimeError(
        "Program invoke could not resolve FunctionConfig in OCG: "
        + str(function_config_id)
    )


def _function_config_by_id(
    *,
    index: MetaGraphRuntimeIndex,
    function_config_id: UUID,
) -> _FunctionConfigLike | None:
    for node in index.ocg.object_config_graph_nodes:
        function_config = getattr(node, "function_config", None)
        if function_config is not None and function_config.id == function_config_id:
            return cast(_FunctionConfigLike, function_config)
    for class_config in index.class_configs_by_id.values():
        for link in class_config.class_config_function_configs:
            link_function_config_id = getattr(link, "function_config_id", None)
            function_config = getattr(link, "function_config", None)
            if link_function_config_id is None and function_config is not None:
                link_function_config_id = function_config.id
            if (
                link_function_config_id == function_config_id
                and function_config is not None
            ):
                return cast(_FunctionConfigLike, function_config)
    return None


def _is_constructor_function(
    *,
    index: MetaGraphRuntimeIndex,
    function_config_id: UUID,
) -> bool:
    for class_config in index.class_configs_by_id.values():
        for link in class_config.class_config_function_configs:
            link_function_config_id = getattr(link, "function_config_id", None)
            if link_function_config_id is None and link.function_config is not None:
                link_function_config_id = link.function_config.id
            if link_function_config_id == function_config_id:
                return bool(link.is_constructor)
    return False


def _program_input_config_ids_by_name(
    *,
    program_config_id: UUID,
    invocation_plan: InvocationPlan,
) -> dict[str, UUID]:
    input_config_ids_by_name: dict[str, UUID] = {}
    for step_item in invocation_plan.steps:
        if not isinstance(step_item, PlanInput):
            continue
        input_config_ids_by_name[step_item.name] = (
            experience_stable_ids.stable_program_config_input_config_id(
                program_config_id=program_config_id,
                name=step_item.name,
                source=_program_input_source_to_string(step_item.source),
            )
        )
    return input_config_ids_by_name


def _decode_bind_step(call: PlanCall) -> tuple[str, str, bool]:
    port_key: str | None = None
    view_key: str | None = None
    is_active = True
    for arg in call.args:
        arg_name = (arg.name or "").strip()
        if arg_name == "port":
            if not isinstance(arg.value, PlanSymbolRef):
                raise RuntimeError("Program bind port arg must be a symbol ref")
            symbol = (arg.value.name or "").strip()
            if not symbol.startswith("program.port."):
                raise RuntimeError("Program bind port arg must use program.port.<key>")
            port_key = symbol.removeprefix("program.port.").split(".", 1)[0]
            continue
        if arg_name == "view_key":
            view_key = str(arg.value or "").strip()
            continue
        if arg_name == "is_active":
            is_active = bool(arg.value)
            continue
    if not port_key or not view_key:
        raise RuntimeError("Program bind instruction requires port and view_key")
    return port_key, view_key, is_active


def _uuid_from_expr(expr: PlanExpr) -> UUID:
    if isinstance(expr, str):
        return UUID(expr)
    if isinstance(expr, PlanSymbolRef):
        return UUID(expr.name)
    raise RuntimeError(
        "Program materialization expected UUID literal/symbol for instruction ref"
    )


__all__ = [
    "ProgramMaterializationDependencies",
    "ProgramMaterializationSpec",
    "build_program_materialization_plan",
    "decode_program_materialization_step_payload",
    "encode_program_materialization_step_payload",
    "materialize_experience_compile_plan_programs",
    "materialize_experience_program_ontology",
    "resolve_program_materialization_specs",
    "_program_projection_catalog_branch_ids",
]
