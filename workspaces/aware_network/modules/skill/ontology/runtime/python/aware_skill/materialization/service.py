from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from aware_api_runtime.invocation import ApiInvocationRuntimeProtocol
from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.stable_ids import stable_api_package_id
from aware_code.stable_ids import stable_code_package_id
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_skill.manifest import AwareSkillDependencyKind, AwareSkillTomlSpec
from aware_skill_ontology.skill.skill_package import SkillPackage
from aware_skill_ontology.skill.skill_package_api_package import SkillPackageApiPackage
from aware_skill_ontology.stable_ids import stable_skill_config_id

from aware_skill.compile import compile_skill_workspace
from aware_skill.models import (
    SkillConfigApiEndpointPlan,
    SkillConfigApiPlan,
    SkillConfigPlan,
    SkillConfigStepPlan,
)
from aware_skill.ontology.materialization import (
    materialize_skill_config,
    materialize_skill_config_api,
    materialize_skill_config_api_endpoint,
    materialize_skill_config_step,
    materialize_skill_package,
    materialize_skill_package_api_package,
)
from aware_skill.ontology.materialization._lane_hydration import (
    hydrate_committed_lane_object,
    hydrate_committed_lane_session,
)


@dataclass(frozen=True, slots=True)
class SkillDefinitionMaterializationSpec:
    package_name: str
    fqn_prefix: str
    source_path: str
    skill_config: SkillConfigPlan


@dataclass(frozen=True, slots=True)
class SkillPackageMaterializationSpec:
    skill_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareSkillTomlSpec
    package_name: str
    skill_name: str
    skill_source_path: str
    source_files: tuple[str, ...]
    compile_plan_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class SkillPackageFromManifestMaterializationResult:
    skill_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareSkillTomlSpec
    skill_config_id: UUID
    skill_package: SkillPackage
    skill_source_path: str
    source_files: tuple[str, ...]
    source_code_package_id: UUID | None
    skill_config_object_instance_graph_commit_id: UUID | None
    skill_package_api_packages: tuple[SkillPackageApiPackage, ...]
    definition_receipt: MaterializationRunReceipt | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None


@dataclass(frozen=True, slots=True)
class _CommittedAPIReferenceContext:
    lane: MaterializationLaneContext
    apis_by_name: Mapping[str, Api]
    capabilities_by_key: Mapping[tuple[UUID, str], ApiCapability]
    endpoints_by_key: Mapping[tuple[UUID, str], ApiCapabilityEndpoint]


def load_skill_compile_plan_payloads(*, repo_root: Path) -> list[dict[str, object]]:
    runtime_root = (repo_root / ".aware" / "skill" / "runtime").resolve()
    if not runtime_root.exists() or not runtime_root.is_dir():
        return []

    payloads: list[dict[str, object]] = []
    for compile_plan_path in sorted(runtime_root.glob("*/skill.compile_plan.json")):
        if not compile_plan_path.is_file():
            continue
        try:
            payload_obj = cast(
                object,
                json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}"),
            )
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise RuntimeError(
                f"Invalid Skill compile plan at {compile_plan_path}: {exc}"
            ) from exc
        payload_map = _expect_mapping(
            payload_obj, field_name=f"{compile_plan_path}:root"
        )
        payloads.append(dict(payload_map))
    return payloads


def resolve_skill_package_materialization_spec(
    *,
    skill_toml_path: Path,
    workspace_root: Path,
) -> SkillPackageMaterializationSpec:
    resolved_skill_toml_path = skill_toml_path.resolve()
    resolved_workspace_root = workspace_root.resolve()
    compile_result = compile_skill_workspace(
        toml_path=resolved_skill_toml_path,
        repo_root=resolved_workspace_root,
        emit_compile_plan=False,
    )
    compile_plan = compile_result.compile_plan
    if compile_plan is None:
        raise RuntimeError(
            "Skill package materialization requires aware.skill.toml [build].compilation_mode = "
            "`skill_ontology`: " + str(resolved_skill_toml_path)
        )

    compile_plan_payload = _encode_skill_compile_plan_payload(
        package_name=compile_plan.package_name,
        fqn_prefix=compile_plan.fqn_prefix,
        skill_configs=compile_plan.skill_configs,
    )
    specs = resolve_skill_definition_materialization_specs(
        compile_plan_payloads=(compile_plan_payload,),
    )
    if len(specs) != 1:
        discovered_skill_names = sorted(item.skill_config.name for item in specs)
        raise RuntimeError(
            "Skill package materialization v0 requires exactly one canonical `skill` declaration per "
            "aware.skill.toml package: "
            + f"skill_toml_path={resolved_skill_toml_path} discovered={discovered_skill_names!r}"
        )

    skill_spec = specs[0]
    return SkillPackageMaterializationSpec(
        skill_toml_path=resolved_skill_toml_path,
        workspace_root=resolved_workspace_root,
        manifest_spec=compile_result.snapshot.spec,
        package_name=compile_plan.package_name,
        skill_name=skill_spec.skill_config.name,
        skill_source_path=skill_spec.source_path,
        source_files=compile_plan.source_files,
        compile_plan_payload=compile_plan_payload,
    )


async def materialize_skill_package_from_manifest(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID,
    thread_id: UUID,
    branch_id: UUID,
    workspace_root: Path,
    skill_toml_path: Path,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None = None,
) -> SkillPackageFromManifestMaterializationResult:
    spec = resolve_skill_package_materialization_spec(
        skill_toml_path=skill_toml_path,
        workspace_root=workspace_root,
    )
    skill_config_projection_hash = _resolve_canonical_skill_config_projection_hash(
        index
    )
    skill_config_lane = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=skill_config_projection_hash,
    )
    definition_receipt = await materialize_skill_definition_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=skill_config_lane,
        compile_plan_payloads=(spec.compile_plan_payload,),
        api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
    )
    skill_config_object_instance_graph_commit_id = (
        await _skill_config_object_instance_graph_commit_id_from_definition_receipt(
            branch_id=skill_config_lane.branch_id,
            projection_hash=skill_config_lane.projection_hash,
            definition_receipt=definition_receipt,
        )
    )
    if skill_config_object_instance_graph_commit_id is None:
        raise RuntimeError(
            "Skill package materialization requires a committed SkillConfig semantic root "
            f"before building SkillPackage: skill_name={spec.skill_name!r}"
        )
    skill_config_id = stable_skill_config_id(name=spec.skill_name)
    skill_package_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="SkillPackage",
    )
    skill_package_lane = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=skill_package_projection_hash,
    )
    source_code_package_id = stable_code_package_id(
        package_name=spec.package_name,
        language=CodeLanguage.aware.value,
    )
    skill_package_result = await materialize_skill_package(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        target_lane=skill_package_lane,
        name=spec.skill_name,
        skill_config_id=skill_config_id,
        skill_config_object_instance_graph_commit_id=skill_config_object_instance_graph_commit_id,
        source_code_package_id=source_code_package_id,
    )
    skill_package_api_packages: list[SkillPackageApiPackage] = []
    package_commit_id = skill_package_result.binding.commit_id
    package_head_commit_id = skill_package_result.binding.head_commit_id
    for dependency in spec.manifest_spec.dependencies:
        if dependency.kind not in (
            AwareSkillDependencyKind.api,
            AwareSkillDependencyKind.api_package,
        ):
            continue
        edge_result = await materialize_skill_package_api_package(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            target_lane=skill_package_lane,
            skill_package_id=skill_package_result.binding.skill_package_id,
            api_package_id=stable_api_package_id(name=dependency.package_name),
        )
        skill_package_api_packages.append(edge_result.skill_package_api_package)
        package_commit_id = edge_result.binding.commit_id
        package_head_commit_id = edge_result.binding.head_commit_id

    skill_package = await hydrate_committed_lane_object(
        index=index,
        target_lane=skill_package_lane,
        orm_class=SkillPackage,
        object_id=skill_package_result.binding.skill_package_id,
        error_context="SkillPackage manifest materialization",
    )
    return SkillPackageFromManifestMaterializationResult(
        skill_toml_path=spec.skill_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        skill_config_id=skill_config_id,
        skill_package=skill_package,
        skill_source_path=spec.skill_source_path,
        source_files=spec.source_files,
        source_code_package_id=source_code_package_id,
        skill_config_object_instance_graph_commit_id=skill_config_object_instance_graph_commit_id,
        skill_package_api_packages=tuple(skill_package_api_packages),
        definition_receipt=definition_receipt,
        package_commit_id=package_commit_id,
        package_head_commit_id=package_head_commit_id,
    )


async def materialize_skill_definition_ontology(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None = None,
) -> MaterializationRunReceipt | None:
    specs = resolve_skill_definition_materialization_specs(
        compile_plan_payloads=compile_plan_payloads
    )
    if not specs:
        return None

    skill_config_projection_hash = _resolve_canonical_skill_config_projection_hash(
        index
    )
    if lane.projection_hash != skill_config_projection_hash:
        raise RuntimeError(
            "Skill compile-plan ontology materialization requires the skill_config projection lane"
        )

    api_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="Api",
    )
    api_context = await _hydrate_committed_api_reference_contexts(
        index=index,
        lanes=_resolve_api_reference_lanes(
            lane=lane,
            projection_hash=api_projection_hash,
            specs=specs,
            api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        ),
    )
    plan = build_skill_definition_materialization_plan(lane=lane, specs=specs)

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = decode_skill_definition_materialization_step_payload(step.payload)
        return await _materialize_skill_definition_spec(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            lane=plan.lane,
            api_context=api_context,
            spec=spec,
        )

    return await MaterializationExecutor().run(plan=plan, runner=_runner)


def resolve_skill_definition_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[SkillDefinitionMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    specs_by_key: dict[tuple[str, str, str], SkillDefinitionMaterializationSpec] = {}
    for payload in compile_plan_payloads:
        package_name = _expect_string(
            payload.get("package_name"), field_name="package_name"
        )
        fqn_prefix = (
            _expect_optional_string(payload.get("fqn_prefix"), field_name="fqn_prefix")
            or ""
        )
        raw_skill_configs = _expect_list(
            payload.get("skill_configs", ()), field_name="skill_configs"
        )
        for raw_skill_config in raw_skill_configs:
            skill_config = _decode_skill_config_plan(
                _expect_mapping(raw_skill_config, field_name="skill_configs[]")
            )
            spec = SkillDefinitionMaterializationSpec(
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                source_path=skill_config.source_path,
                skill_config=skill_config,
            )
            key = (
                spec.package_name.casefold(),
                spec.skill_config.name.casefold(),
                spec.source_path,
            )
            existing = specs_by_key.get(key)
            if existing is not None and existing != spec:
                raise RuntimeError(
                    "Invalid Skill compile plan: duplicate skill config entries disagree "
                    + f"(package_name={package_name!r}, skill={skill_config.name!r}, "
                    + f"source_path={skill_config.source_path!r})"
                )
            specs_by_key[key] = spec

    return tuple(
        sorted(
            specs_by_key.values(),
            key=lambda item: (
                item.package_name.casefold(),
                item.skill_config.name.casefold(),
                item.source_path,
            ),
        )
    )


def build_skill_definition_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[SkillDefinitionMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"skill:{spec.package_name}:{spec.skill_config.name}",
            step_kind="skill.definition.ontology",
            payload=encode_skill_definition_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="skill",
        pipeline_id="skill.compile_plan.ontology",
        lane=lane,
        steps=steps,
    )


def encode_skill_definition_materialization_step_payload(
    *,
    spec: SkillDefinitionMaterializationSpec,
) -> dict[str, object]:
    return {
        "package_name": spec.package_name,
        "fqn_prefix": spec.fqn_prefix,
        "source_path": spec.source_path,
        "skill_config": _encode_skill_config_plan(spec.skill_config),
    }


def decode_skill_definition_materialization_step_payload(
    payload: Mapping[str, object],
) -> SkillDefinitionMaterializationSpec:
    mapping = _expect_mapping(payload, field_name="skill_definition_step")
    package_name = _expect_string(
        mapping.get("package_name"), field_name="package_name"
    )
    fqn_prefix = (
        _expect_optional_string(mapping.get("fqn_prefix"), field_name="fqn_prefix")
        or ""
    )
    source_path = _expect_string(mapping.get("source_path"), field_name="source_path")
    skill_config = _decode_skill_config_plan(
        _expect_mapping(mapping.get("skill_config"), field_name="skill_config")
    )
    if skill_config.source_path != source_path:
        raise RuntimeError(
            "Invalid Skill materialization step payload: source_path does not match nested skill_config.source_path"
        )
    return SkillDefinitionMaterializationSpec(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_path=source_path,
        skill_config=skill_config,
    )


async def _materialize_skill_definition_spec(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    api_context: _CommittedAPIReferenceContext,
    spec: SkillDefinitionMaterializationSpec,
) -> MaterializationStepResult:
    skill_config_result = await materialize_skill_config(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        target_lane=lane,
        name=spec.skill_config.name,
        description=spec.skill_config.description,
    )

    skill_config_id = skill_config_result.binding.skill_config_id
    last_commit_id = skill_config_result.binding.commit_id
    last_head_commit_id = skill_config_result.binding.head_commit_id

    skill_config_api_ids_by_ref: dict[str, UUID] = {}
    for api_plan in spec.skill_config.apis:
        api_id = _resolve_committed_api_id(
            api_context=api_context, api_ref=api_plan.api_ref
        )
        materialized_api = await materialize_skill_config_api(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            target_lane=lane,
            skill_config_id=skill_config_id,
            api_id=api_id,
            description=None,
        )
        skill_config_api_ids_by_ref[api_plan.api_ref] = (
            materialized_api.binding.skill_config_api_id
        )
        last_commit_id = materialized_api.binding.commit_id
        last_head_commit_id = materialized_api.binding.head_commit_id

    endpoint_ids_by_name: dict[str, UUID] = {}
    for endpoint_plan in spec.skill_config.api_endpoints:
        skill_config_api_id = skill_config_api_ids_by_ref.get(endpoint_plan.api_ref)
        if skill_config_api_id is None:
            raise RuntimeError(
                "Invalid Skill compile plan: endpoint references an unmaterialized skill_config_api "
                + f"(skill={spec.skill_config.name!r}, api_ref={endpoint_plan.api_ref!r}, "
                + f"endpoint_ref={endpoint_plan.endpoint_ref!r})"
            )
        api_endpoint_id = _resolve_committed_api_endpoint_id(
            api_context=api_context,
            endpoint_ref=endpoint_plan.endpoint_ref,
        )
        materialized_endpoint = await materialize_skill_config_api_endpoint(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            target_lane=lane,
            skill_config_api_id=skill_config_api_id,
            api_endpoint_id=api_endpoint_id,
            capability_name=endpoint_plan.capability_name,
            name=endpoint_plan.name,
            description=endpoint_plan.description,
        )
        endpoint_ids_by_name[endpoint_plan.name.casefold()] = (
            materialized_endpoint.binding.skill_config_api_endpoint_id
        )
        last_commit_id = materialized_endpoint.binding.commit_id
        last_head_commit_id = materialized_endpoint.binding.head_commit_id

    for step_plan in spec.skill_config.steps:
        skill_config_api_endpoint_id = endpoint_ids_by_name.get(
            step_plan.endpoint_name.casefold()
        )
        if skill_config_api_endpoint_id is None:
            raise RuntimeError(
                "Invalid Skill compile plan: step references an unmaterialized endpoint "
                + f"(skill={spec.skill_config.name!r}, step={step_plan.position}, "
                + f"endpoint_name={step_plan.endpoint_name!r})"
            )
        materialized_step = await materialize_skill_config_step(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            target_lane=lane,
            skill_config_id=skill_config_id,
            position=step_plan.position,
            skill_config_api_endpoint_id=skill_config_api_endpoint_id,
            instruction=step_plan.instruction,
        )
        last_commit_id = materialized_step.binding.commit_id
        last_head_commit_id = materialized_step.binding.head_commit_id

    return MaterializationStepResult(
        details={
            "package_name": spec.package_name,
            "skill_name": spec.skill_config.name,
            "source_path": spec.source_path,
            "skill_config_id": str(skill_config_id),
            "skill_config_api_count": len(spec.skill_config.apis),
            "skill_config_api_endpoint_count": len(spec.skill_config.api_endpoints),
            "skill_config_step_count": len(spec.skill_config.steps),
        },
        commit_id=last_commit_id,
        head_commit_id=last_head_commit_id,
    )


async def _hydrate_committed_api_reference_context(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
) -> _CommittedAPIReferenceContext:
    session = await hydrate_committed_lane_session(
        index=index, lane=lane, error_context="API ref resolution"
    )

    apis_by_name: dict[str, Api] = {}
    capabilities_by_key: dict[tuple[UUID, str], ApiCapability] = {}
    endpoints_by_key: dict[tuple[UUID, str], ApiCapabilityEndpoint] = {}

    for obj in session.imap_all_objects():
        if isinstance(obj, Api):
            if obj.id is None:
                continue
            key = (obj.name or "").casefold().strip()
            _insert_unique_ref(
                refs=apis_by_name,
                key=key,
                value=obj,
                error_context=f"duplicate committed Api name {obj.name!r}",
            )
        elif isinstance(obj, ApiCapability):
            if obj.id is None:
                continue
            key = (obj.api_id, (obj.name or "").casefold().strip())
            _insert_unique_ref(
                refs=capabilities_by_key,
                key=key,
                value=obj,
                error_context=f"duplicate committed ApiCapability name {obj.name!r}",
            )
        elif isinstance(obj, ApiCapabilityEndpoint):
            key = (obj.api_capability_id, (obj.name or "").casefold().strip())
            _insert_unique_ref(
                refs=endpoints_by_key,
                key=key,
                value=obj,
                error_context=f"duplicate committed ApiCapabilityEndpoint name {obj.name!r}",
            )

    return _CommittedAPIReferenceContext(
        lane=lane,
        apis_by_name=apis_by_name,
        capabilities_by_key=capabilities_by_key,
        endpoints_by_key=endpoints_by_key,
    )


async def _hydrate_committed_api_reference_contexts(
    *,
    index: MetaGraphRuntimeIndex,
    lanes: Sequence[MaterializationLaneContext],
) -> _CommittedAPIReferenceContext:
    if not lanes:
        raise RuntimeError(
            "API ref resolution requires at least one committed API reference lane."
        )

    merged_apis_by_name: dict[str, Api] = {}
    merged_capabilities_by_key: dict[tuple[UUID, str], ApiCapability] = {}
    merged_endpoints_by_key: dict[tuple[UUID, str], ApiCapabilityEndpoint] = {}
    seen_lane_keys: set[tuple[UUID, str]] = set()
    representative_lane = lanes[0]

    for lane in lanes:
        lane_key = (lane.branch_id, lane.projection_hash)
        if lane_key in seen_lane_keys:
            continue
        seen_lane_keys.add(lane_key)

        lane_context = await _hydrate_committed_api_reference_context(
            index=index, lane=lane
        )
        for key, value in lane_context.apis_by_name.items():
            _insert_unique_ref(
                refs=merged_apis_by_name,
                key=key,
                value=value,
                error_context=f"duplicate committed Api name {value.name!r}",
            )
        for key, value in lane_context.capabilities_by_key.items():
            _insert_unique_ref(
                refs=merged_capabilities_by_key,
                key=key,
                value=value,
                error_context=f"duplicate committed ApiCapability name {value.name!r}",
            )
        for key, value in lane_context.endpoints_by_key.items():
            _insert_unique_ref(
                refs=merged_endpoints_by_key,
                key=key,
                value=value,
                error_context=f"duplicate committed ApiCapabilityEndpoint name {value.name!r}",
            )

    return _CommittedAPIReferenceContext(
        lane=representative_lane,
        apis_by_name=merged_apis_by_name,
        capabilities_by_key=merged_capabilities_by_key,
        endpoints_by_key=merged_endpoints_by_key,
    )


def _resolve_committed_api_id(
    *,
    api_context: _CommittedAPIReferenceContext,
    api_ref: str,
) -> UUID:
    key = (api_ref or "").casefold().strip()
    api = api_context.apis_by_name.get(key)
    if api is None:
        raise RuntimeError(
            "Skill compile-plan materialization could not resolve committed Api "
            + f"for api_ref={api_ref!r}."
        )
    api_id = api.id
    if api_id is None:
        raise RuntimeError(f"Committed Api is missing id for api_ref={api_ref!r}.")
    return api_id


def _resolve_committed_api_endpoint_id(
    *,
    api_context: _CommittedAPIReferenceContext,
    endpoint_ref: str,
) -> UUID:
    api_name, capability_name, endpoint_name = _split_endpoint_ref(
        endpoint_ref=endpoint_ref
    )
    api_id = _resolve_committed_api_id(api_context=api_context, api_ref=api_name)
    capability = api_context.capabilities_by_key.get(
        (api_id, capability_name.casefold().strip())
    )
    if capability is None:
        raise RuntimeError(
            "Skill compile-plan materialization could not resolve committed ApiCapability "
            + f"for endpoint_ref={endpoint_ref!r}."
        )
    capability_id = capability.id
    if capability_id is None:
        raise RuntimeError(
            f"Committed ApiCapability is missing id for endpoint_ref={endpoint_ref!r}."
        )
    endpoint = api_context.endpoints_by_key.get(
        (capability_id, endpoint_name.casefold().strip())
    )
    if endpoint is None:
        raise RuntimeError(
            "Skill compile-plan materialization could not resolve committed ApiCapabilityEndpoint "
            + f"for endpoint_ref={endpoint_ref!r}."
        )
    endpoint_id = endpoint.id
    if endpoint_id is None:
        raise RuntimeError(
            f"Committed ApiCapabilityEndpoint is missing id for endpoint_ref={endpoint_ref!r}."
        )
    return endpoint_id


def _resolve_api_reference_lanes(
    *,
    lane: MaterializationLaneContext,
    projection_hash: str,
    specs: Sequence[SkillDefinitionMaterializationSpec],
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None,
) -> tuple[MaterializationLaneContext, ...]:
    api_refs = tuple(
        sorted(
            {
                api_plan.api_ref.strip()
                for spec in specs
                for api_plan in spec.skill_config.apis
                if api_plan.api_ref.strip()
            }
        )
    )
    if not api_refs:
        return (_build_peer_lane(lane=lane, projection_hash=projection_hash),)

    return tuple(
        _build_peer_lane(
            lane=lane,
            projection_hash=projection_hash,
            branch_id=(
                api_reference_branch_ids_by_api_name.get(api_ref)
                if api_reference_branch_ids_by_api_name is not None
                else None
            ),
        )
        for api_ref in api_refs
    )


def _find_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    target = (projection_name or "").strip()
    matches = tuple(
        sorted(
            str(projection_hash)
            for projection_hash, opg in index.opg_by_hash.items()
            if (opg.name or "").strip() == target
        )
    )
    if len(matches) != 1:
        raise ValueError(
            f"Expected one Skill runtime projection named {projection_name!r}, got {matches!r}"
        )
    return matches[0]


def _resolve_canonical_skill_config_projection_hash(
    index: MetaGraphRuntimeIndex,
) -> str:
    candidate_hashes = tuple(
        projection_hash
        for projection_hash, opg in index.opg_by_hash.items()
        if (opg.name or "").strip() == "SkillConfig"
    )
    if not candidate_hashes:
        raise ValueError("Unknown projection 'SkillConfig'")

    required_class_names = frozenset(
        {
            "SkillConfig",
            "SkillConfigApi",
            "SkillConfigApiEndpoint",
            "SkillConfigStep",
        }
    )
    matches: list[str] = []
    candidate_descriptors: list[str] = []
    for projection_hash in candidate_hashes:
        opg = index.opg_by_hash[projection_hash]
        class_names = frozenset(
            index.class_configs_by_id[node.class_config_id].name
            for node in (cast(Any, opg).object_projection_graph_nodes or ())
        )
        candidate_descriptors.append(f"{projection_hash}:{sorted(class_names)!r}")
        if required_class_names.issubset(class_names):
            matches.append(projection_hash)

    if len(matches) != 1:
        raise ValueError(
            "Expected one canonical Skill-owned projection hash for 'SkillConfig', "
            f"got matches={matches!r}, candidates={candidate_descriptors!r}"
        )
    return matches[0]


async def _skill_config_object_instance_graph_commit_id_from_definition_receipt(
    *,
    branch_id: UUID,
    projection_hash: str,
    definition_receipt: MaterializationRunReceipt | None,
) -> UUID | None:
    if definition_receipt is None or not definition_receipt.steps:
        return None
    domain_commit_id = definition_receipt.steps[-1].commit_id
    if domain_commit_id is None:
        return None
    domain_commit = await FSCommitStore().get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_id,
    )
    if domain_commit is None:
        return None
    return stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=domain_commit.object_instance_graph_identity_id,
        commit_id=domain_commit_id,
    )


def _build_peer_lane(
    *,
    lane: MaterializationLaneContext,
    projection_hash: str,
    branch_id: UUID | None = None,
) -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=branch_id or lane.branch_id,
        projection_hash=projection_hash,
    )


def _split_endpoint_ref(*, endpoint_ref: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in endpoint_ref.split(".")]
    if len(parts) != 3 or any(not part for part in parts):
        raise RuntimeError(
            f"Invalid Skill compile plan endpoint_ref {endpoint_ref!r}: expected <api>.<capability>.<endpoint>"
        )
    return parts[0], parts[1], parts[2]


def _insert_unique_ref(
    *,
    refs: dict[Any, Any],
    key: Any,
    value: Any,
    error_context: str,
) -> None:
    if not key:
        return
    existing = refs.get(key)
    if existing is not None and existing != value:
        raise RuntimeError(error_context)
    refs[key] = value


def _encode_skill_compile_plan_payload(
    *,
    package_name: str,
    fqn_prefix: str,
    skill_configs: Sequence[SkillConfigPlan],
) -> dict[str, object]:
    return {
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "skill_configs": [_encode_skill_config_plan(item) for item in skill_configs],
    }


def _encode_skill_config_plan(plan: SkillConfigPlan) -> dict[str, object]:
    return {
        "name": plan.name,
        "source_path": plan.source_path,
        "description": plan.description,
        "apis": [_encode_skill_config_api_plan(row) for row in plan.apis],
        "api_endpoints": [
            _encode_skill_config_api_endpoint_plan(row) for row in plan.api_endpoints
        ],
        "steps": [_encode_skill_config_step_plan(row) for row in plan.steps],
    }


def _encode_skill_config_api_plan(plan: SkillConfigApiPlan) -> dict[str, object]:
    return {
        "api_ref": plan.api_ref,
        "source_path": plan.source_path,
    }


def _encode_skill_config_api_endpoint_plan(
    plan: SkillConfigApiEndpointPlan,
) -> dict[str, object]:
    return {
        "name": plan.name,
        "endpoint_ref": plan.endpoint_ref,
        "api_ref": plan.api_ref,
        "capability_name": plan.capability_name,
        "source_path": plan.source_path,
        "description": plan.description,
    }


def _encode_skill_config_step_plan(plan: SkillConfigStepPlan) -> dict[str, object]:
    return {
        "position": plan.position,
        "endpoint_name": plan.endpoint_name,
        "endpoint_ref": plan.endpoint_ref,
        "api_ref": plan.api_ref,
        "instruction": plan.instruction,
        "source_path": plan.source_path,
    }


def _decode_skill_config_plan(payload: Mapping[str, object]) -> SkillConfigPlan:
    return SkillConfigPlan(
        name=_expect_string(payload.get("name"), field_name="skill_config.name"),
        source_path=_expect_string(
            payload.get("source_path"), field_name="skill_config.source_path"
        ),
        description=_expect_optional_string(
            payload.get("description"), field_name="skill_config.description"
        ),
        apis=tuple(
            _decode_skill_config_api_plan(
                _expect_mapping(item, field_name="skill_config.apis[]")
            )
            for item in _expect_list(
                payload.get("apis", ()), field_name="skill_config.apis"
            )
        ),
        api_endpoints=tuple(
            _decode_skill_config_api_endpoint_plan(
                _expect_mapping(item, field_name="skill_config.api_endpoints[]")
            )
            for item in _expect_list(
                payload.get("api_endpoints", ()),
                field_name="skill_config.api_endpoints",
            )
        ),
        steps=tuple(
            _decode_skill_config_step_plan(
                _expect_mapping(item, field_name="skill_config.steps[]")
            )
            for item in _expect_list(
                payload.get("steps", ()), field_name="skill_config.steps"
            )
        ),
    )


def _decode_skill_config_api_plan(payload: Mapping[str, object]) -> SkillConfigApiPlan:
    return SkillConfigApiPlan(
        api_ref=_expect_string(
            payload.get("api_ref"), field_name="skill_config_api.api_ref"
        ),
        source_path=_expect_string(
            payload.get("source_path"), field_name="skill_config_api.source_path"
        ),
    )


def _decode_skill_config_api_endpoint_plan(
    payload: Mapping[str, object]
) -> SkillConfigApiEndpointPlan:
    return SkillConfigApiEndpointPlan(
        name=_expect_string(
            payload.get("name"), field_name="skill_config_api_endpoint.name"
        ),
        endpoint_ref=_expect_string(
            payload.get("endpoint_ref"),
            field_name="skill_config_api_endpoint.endpoint_ref",
        ),
        api_ref=_expect_string(
            payload.get("api_ref"), field_name="skill_config_api_endpoint.api_ref"
        ),
        capability_name=_expect_string(
            payload.get("capability_name"),
            field_name="skill_config_api_endpoint.capability_name",
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="skill_config_api_endpoint.source_path",
        ),
        description=_expect_optional_string(
            payload.get("description"),
            field_name="skill_config_api_endpoint.description",
        ),
    )


def _decode_skill_config_step_plan(
    payload: Mapping[str, object]
) -> SkillConfigStepPlan:
    return SkillConfigStepPlan(
        position=_expect_int(
            payload.get("position"), field_name="skill_config_step.position"
        ),
        endpoint_name=_expect_string(
            payload.get("endpoint_name"), field_name="skill_config_step.endpoint_name"
        ),
        endpoint_ref=_expect_string(
            payload.get("endpoint_ref"), field_name="skill_config_step.endpoint_ref"
        ),
        api_ref=_expect_string(
            payload.get("api_ref"), field_name="skill_config_step.api_ref"
        ),
        instruction=_expect_string(
            payload.get("instruction"), field_name="skill_config_step.instruction"
        ),
        source_path=_expect_string(
            payload.get("source_path"), field_name="skill_config_step.source_path"
        ),
    )


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"Expected {field_name} to be an object")
    return cast(Mapping[str, object], value)


def _expect_list(value: object, *, field_name: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RuntimeError(f"Expected {field_name} to be a list")
    return cast(Sequence[object], value)


def _expect_string(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Expected {field_name} to be a non-empty string")
    return value


def _expect_optional_string(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuntimeError(f"Expected {field_name} to be a string or null")
    return value


def _expect_int(value: object, *, field_name: str) -> int:
    if not isinstance(value, int):
        raise RuntimeError(f"Expected {field_name} to be an int")
    return value


__all__ = [
    "SkillDefinitionMaterializationSpec",
    "SkillPackageFromManifestMaterializationResult",
    "SkillPackageMaterializationSpec",
    "build_skill_definition_materialization_plan",
    "decode_skill_definition_materialization_step_payload",
    "encode_skill_definition_materialization_step_payload",
    "load_skill_compile_plan_payloads",
    "materialize_skill_definition_ontology",
    "materialize_skill_package_from_manifest",
    "resolve_skill_definition_materialization_specs",
    "resolve_skill_package_materialization_spec",
]
