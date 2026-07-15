from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from time import perf_counter
import tomllib
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_graph import ApiGraph
from aware_api_ontology.api.api_graph_projection import ApiGraphProjection
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_function import (
    ApiCapabilityEndpointFunction,
)
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_config import (
    ApiCapabilityEndpointStreamConfig,
)
from aware_api_ontology.api.api_view import ApiView
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_ontology.api.api_package_language_package import (
    ApiPackageLanguagePackage,
)
from aware_api_ontology.stable_ids import stable_api_package_id
from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_code.types import JsonArray
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage

from aware_code_ontology.stable_ids import stable_code_package_id
from aware_types import canonical_decimal_text, decimal_value
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_service_runtime.manifest.spec import (
    AwareServiceImplementationLanguage,
    AwareServiceTomlImplementationPackageSpec,
    AwareServiceTomlSpec,
)
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
    stable_object_instance_graph_commit_id,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_ontology_ontology.stable_ids import stable_ontology_package_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.session import Session
from aware_meta.materialization import (
    MaterializationExecutor,
    MaterializationLaneContext,
    MaterializationPlan,
    MaterializationRunReceipt,
    MaterializationStep,
    MaterializationStepResult,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.service.service_enums import (
    ServiceContractKind,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)
from aware_service_ontology.service.service_package import ServicePackage
from aware_service_ontology.stable_ids import (
    stable_service_api_provider_set_id,
    stable_service_config_api_id,
    stable_service_config_id,
    stable_service_operation_config_id,
    stable_service_package_id,
)

from aware_service_runtime.builder import (
    ServiceActivationProtocolLock,
    build_service_activation_plan,
    emit_service_activation_plan_artifact,
)
from aware_service_runtime.compile import compile_service_workspace
from aware_service_runtime.models import (
    ServiceContractConfigActorRoleGrantPlan,
    ServiceContractConfigOperationGrantPlan,
    ServiceContractConfigPlan,
    ServiceConfigCodePackageConfigPlan,
    ServiceConfigApiProjectionPlan,
    ServiceConfigApiPlan,
    ServiceConfigExperiencePlan,
    ServiceConfigPlan,
    ServiceInlinePriceDefinition,
    ServiceOperationConfigApiEndpointPlan,
    ServiceOperationConfigApiViewPlan,
    ServiceOperationConfigPlan,
    ServiceOperationConfigRoleRequirementPlan,
)
from aware_service_runtime.ontology.materialization._lane_hydration import (
    bind_service_runtime_lane,
    hydrate_committed_lane_object,
)
from aware_service_runtime.materialization.snapshot_commit import (
    ServiceDefinitionActorRoleGrantSnapshot,
    ServiceDefinitionApiSnapshot,
    ServiceDefinitionCodePackageConfigSnapshot,
    ServiceDefinitionContractSnapshot,
    ServiceDefinitionEndpointFunctionSnapshot,
    ServiceDefinitionEndpointSnapshot,
    ServiceDefinitionExperienceSnapshot,
    ServiceDefinitionApiViewSnapshot,
    ServiceDefinitionOperationGrantSnapshot,
    ServiceDefinitionOperationSnapshot,
    ServiceDefinitionRoleRequirementSnapshot,
    ServicePackageApiPackageSnapshot,
    ServicePackageImplementationSnapshot,
    ServicePackageOntologyPackageSnapshot,
    ServicePackageObjectConfigGraphPackageSnapshot,
    commit_service_api_provider_set_snapshot,
    commit_role_config_reference_snapshot,
    commit_service_config_definition_snapshot,
    commit_service_instance_snapshot,
    commit_service_package_manifest_snapshot,
)
from aware_service_runtime.workspace_dependency_roots import (
    api_service_protocol_dependency_roots,
)
from aware_utils.logging import logger

if TYPE_CHECKING:
    from aware_identity_ontology.role.role_config import RoleConfig


class _RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...

    @property
    def invoker(self) -> object: ...


def _bind_runtime_lane(**kwargs: Any) -> Any:
    return bind_service_runtime_lane(**kwargs)


_THydrated = TypeVar("_THydrated", bound=ORMModel)


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


def _source_code_package_config_id(
    *,
    manifest_kind: str,
    surface: str,
) -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind=manifest_kind,
            surface=surface,
        )
    )


@contextmanager
def _record_phase(phase_timings_s: dict[str, float], phase_name: str) -> Iterator[None]:
    started_at = perf_counter()
    logger.info("Service package materialization phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "Service package materialization phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


def _resolve_canonical_service_config_projection_hash(
    index: MetaGraphRuntimeIndex,
) -> str:
    candidate_hashes = tuple(
        projection_hash
        for projection_hash, opg in index.opg_by_hash.items()
        if (opg.name or "").strip() == "ServiceConfig"
    )
    if not candidate_hashes:
        raise ValueError("Unknown projection 'ServiceConfig'")

    required_class_names = frozenset(
        {
            "ServiceConfig",
            "ServiceConfigApi",
            "ServiceConfigApiProjection",
            "ServiceConfigCodePackageConfig",
            "ServiceConfigExperience",
            "ServiceContractConfig",
            "ServiceContractConfigActorRoleGrant",
            "ServiceContractConfigOperationGrant",
            "ServiceOperationConfigApiEndpoint",
            "ServiceOperationConfigApiEndpointFunction",
            "ServiceOperationConfigApiView",
            "ServiceOperationConfigRoleRequirement",
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
            "Expected one canonical Service-owned projection hash for 'ServiceConfig', "
            f"got matches={matches!r}, candidates={candidate_descriptors!r}"
        )
    return matches[0]


def _resolve_canonical_service_projection_hash(index: MetaGraphRuntimeIndex) -> str:
    candidate_hashes = tuple(
        projection_hash
        for projection_hash, opg in index.opg_by_hash.items()
        if (opg.name or "").strip() == "Service"
    )
    if not candidate_hashes:
        raise ValueError("Unknown projection 'Service'")

    required_class_names = frozenset(
        {
            "Service",
            "ServiceBranch",
            "ServiceOperation",
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
            "Expected one canonical Service-owned projection hash for 'Service', "
            f"got matches={matches!r}, candidates={candidate_descriptors!r}"
        )
    return matches[0]


@dataclass(frozen=True, slots=True)
class ServiceDefinitionMaterializationSpec:
    package_name: str
    fqn_prefix: str
    source_path: str
    service_config: ServiceConfigPlan


@dataclass(frozen=True, slots=True)
class ServicePackageMaterializationSpec:
    service_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareServiceTomlSpec
    package_name: str
    service_name: str
    service_source_path: str
    source_files: tuple[str, ...]
    compile_plan_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class _ServicePackageDependencyMaterialization:
    dependencies: JsonArray


@dataclass(frozen=True, slots=True)
class ServiceOwnedObjectConfigGraphPackageMaterialization:
    manifest_path: Path
    manifest_relative_path: str
    role: str
    package_name: str
    package_fqn_prefix: str
    package_kind: str
    object_config_graph_package_id: UUID
    object_config_graph_id: UUID
    package_branch_id: UUID | None
    source_code_package_id: UUID | None
    object_config_graph_package_commit_id: UUID | None
    object_config_graph_package_head_commit_id: UUID | None
    object_config_graph_package_object_instance_graph_commit_id: UUID | None
    object_config_graph_commit_id: UUID | None
    object_config_graph_head_commit_id: UUID | None
    object_config_graph_object_instance_graph_commit_id: UUID | None
    language_materialization_targets: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceActivationLaneMaterialization:
    service_name: str
    service_config_id: UUID
    service_id: UUID
    service_config_branch_id: UUID
    service_config_projection_hash: str
    service_config_head_commit_id: UUID
    service_config_object_instance_graph_commit_id: UUID
    service_branch_id: UUID
    service_projection_hash: str
    service_head_commit_id: UUID
    service_object_instance_graph_commit_id: UUID


@dataclass(frozen=True, slots=True)
class ServicePackageMaterializationResult:
    service_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareServiceTomlSpec
    service_config: ServiceConfig
    service_package: ServicePackage
    service_source_path: str
    source_files: tuple[str, ...]
    source_code_package_id: UUID | None
    implementation_code_package_ids: tuple[UUID, ...]
    implementation_code_package_refs: tuple[dict[str, object], ...]
    object_config_graph_packages: tuple[
        ServiceOwnedObjectConfigGraphPackageMaterialization, ...
    ]
    api_provider_set_refs: tuple[dict[str, object], ...]
    api_provider_set_commit_id: UUID | None
    api_provider_set_head_commit_id: UUID | None
    definition_commit_id: UUID | None
    definition_head_commit_id: UUID | None
    service_config_object_instance_graph_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None
    package_object_instance_graph_commit_id: UUID | None
    activation_lanes: tuple[ServiceActivationLaneMaterialization, ...]
    phase_timings_s: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class _CommittedAPIReferenceContext:
    lane: MaterializationLaneContext
    apis_by_name: Mapping[str, Api]
    graphs_by_api_id: Mapping[UUID, tuple[ApiGraph, ...]]
    graph_projections_by_key: Mapping[tuple[UUID, str], ApiGraphProjection]
    capabilities_by_key: Mapping[tuple[UUID, str], ApiCapability]
    endpoints_by_key: Mapping[tuple[UUID, str], ApiCapabilityEndpoint]
    api_views_by_ref: Mapping[str, ApiView]
    api_views_by_api_id_and_name: Mapping[tuple[UUID, str], ApiView]
    endpoint_functions_by_endpoint_id: Mapping[
        UUID, tuple[ApiCapabilityEndpointFunction, ...]
    ]
    endpoint_stream_modes_by_endpoint_id: Mapping[UUID, str]


@dataclass(frozen=True, slots=True)
class _CommittedPriceReferenceContext:
    lane: MaterializationLaneContext
    price_ids_by_name: Mapping[str, UUID]


@dataclass(frozen=True, slots=True)
class _CommittedExperienceReferenceContext:
    lane: MaterializationLaneContext
    experiences_by_name: Mapping[str, ProjectionExperience]


@dataclass(frozen=True, slots=True)
class _CommittedRoleReferenceContext:
    lane: MaterializationLaneContext
    role_configs_by_name: Mapping[str, "RoleConfig"]


@dataclass(frozen=True, slots=True)
class _ImplementationCodePackageMaterializationRef:
    code_package: CodePackage
    branch_id: UUID
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID

    def to_payload(self) -> dict[str, object]:
        return {
            "code_package_id": self.code_package.id,
            "branch_id": self.branch_id,
            "domain_commit_id": self.domain_commit_id,
            "object_instance_graph_commit_id": self.object_instance_graph_commit_id,
            "package_name": self.code_package.package_name,
            "language": self.code_package.language.value,
            "manifest_relative_path": self.code_package.manifest_relative_path,
            "package_root": self.code_package.package_root,
            "sources_root": self.code_package.sources_root,
            "fqn_prefix": self.code_package.fqn_prefix,
        }


@dataclass(frozen=True, slots=True)
class _ServiceApiProviderSetSyncResult:
    provider_set_refs: tuple[dict[str, object], ...]
    domain_commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None


def load_service_compile_plan_payloads(*, repo_root: Path) -> list[dict[str, object]]:
    runtime_root = (repo_root / ".aware" / "service" / "runtime").resolve()
    if not runtime_root.exists() or not runtime_root.is_dir():
        return []

    payloads: list[dict[str, object]] = []
    for compile_plan_path in sorted(runtime_root.glob("*/service.compile_plan.json")):
        if not compile_plan_path.is_file():
            continue
        try:
            payload_obj = cast(
                object,
                json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}"),
            )
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise RuntimeError(
                f"Invalid Service compile plan at {compile_plan_path}: {exc}"
            ) from exc
        payload_map = _expect_mapping(
            payload_obj, field_name=f"{compile_plan_path}:root"
        )
        payloads.append(dict(payload_map))
    return payloads


def resolve_service_package_materialization_spec(
    *,
    service_toml_path: Path,
    workspace_root: Path,
) -> ServicePackageMaterializationSpec:
    resolved_service_toml_path = service_toml_path.resolve()
    resolved_workspace_root = workspace_root.resolve()
    compile_result = compile_service_workspace(
        toml_path=resolved_service_toml_path,
        repo_root=resolved_workspace_root,
        emit_compile_plan=False,
    )
    compile_plan = compile_result.compile_plan
    if compile_plan is None:
        raise RuntimeError(
            "Service package materialization requires aware.service.toml [build].compilation_mode = "
            "`service_ontology`: " + str(resolved_service_toml_path)
        )

    compile_plan_payload = _encode_service_compile_plan_payload(
        package_name=compile_plan.package_name,
        fqn_prefix=compile_plan.fqn_prefix,
        service_configs=compile_plan.service_configs,
    )
    specs = resolve_service_definition_materialization_specs(
        compile_plan_payloads=(compile_plan_payload,),
    )
    if len(specs) != 1:
        discovered_service_names = sorted(item.service_config.name for item in specs)
        raise RuntimeError(
            "Service package materialization v0 requires exactly one canonical `service` declaration per "
            "aware.service.toml package: "
            + f"service_toml_path={resolved_service_toml_path} discovered={discovered_service_names!r}"
        )

    service_spec = specs[0]
    return ServicePackageMaterializationSpec(
        service_toml_path=resolved_service_toml_path,
        workspace_root=resolved_workspace_root,
        manifest_spec=compile_result.snapshot.spec,
        package_name=compile_plan.package_name,
        service_name=service_spec.service_config.name,
        service_source_path=service_spec.source_path,
        source_files=compile_plan.source_files,
        compile_plan_payload=compile_plan_payload,
    )


async def materialize_service_package_from_manifest(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    service_toml_path: Path,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None = None,
    api_reference_commit_store_roots_by_api_name: Mapping[str, Path] | None = None,
    api_reference_accessible_graphs: Sequence[ObjectConfigGraph] = (),
    experience_reference_branch_ids_by_experience_name: (
        Mapping[str, UUID] | None
    ) = None,
    experience_reference_commit_store_root: Path | None = None,
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None = None,
    price_reference_branch_ids_by_package_name: Mapping[str, UUID] | None = None,
) -> ServicePackageMaterializationResult:
    materialization_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    with _record_phase(phase_timings_s, "resolve_service_package_materialization_spec"):
        spec = resolve_service_package_materialization_spec(
            service_toml_path=service_toml_path,
            workspace_root=workspace_root,
        )
    with _record_phase(phase_timings_s, "compile_service_workspace"):
        compile_result = compile_service_workspace(
            toml_path=service_toml_path,
            repo_root=workspace_root,
            emit_compile_plan=True,
        )
    snapshot = compile_result.snapshot
    sources_root = (snapshot.package_root / snapshot.spec.build.sources_dir).resolve()
    manifest_relative_path = _relative_to(
        path=spec.service_toml_path,
        root=spec.workspace_root,
        label="aware.service.toml",
    )
    package_root_relative = _relative_to(
        path=snapshot.package_root,
        root=spec.workspace_root,
        label="package_root",
    )
    sources_root_relative = _relative_to(
        path=sources_root,
        root=spec.workspace_root,
        label="sources_root",
    )
    source_code_package_config_id = _source_code_package_config_id(
        manifest_kind="aware_service_toml",
        surface="service",
    )
    expected_source_code_package_id = stable_code_package_id(
        code_package_config_id=source_code_package_config_id,
        package_name=spec.package_name,
        language=CodeLanguage.aware.value,
    )
    service_config_projection_hash = _resolve_canonical_service_config_projection_hash(
        index
    )
    service_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ServicePackage",
    )
    code_package_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="CodePackage",
    )
    service_config_lane = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=service_config_projection_hash,
    )
    service_config_id = stable_service_config_id(name=spec.service_name)
    with _record_phase(phase_timings_s, "maybe_hydrate_service_config_from_head"):
        service_config = await _maybe_hydrate_committed_lane_object(
            index=index,
            target_lane=service_config_lane,
            orm_class=ServiceConfig,
            object_id=service_config_id,
        )
    definition_commit_id: UUID | None = None
    definition_head_commit_id: UUID | None = None
    service_config_domain_head_commit_id: UUID | None = None
    if service_config is None:
        with _record_phase(phase_timings_s, "materialize_service_definition_ontology"):
            definition_receipt = await materialize_service_definition_ontology(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane=service_config_lane,
                compile_plan_payloads=(spec.compile_plan_payload,),
                api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
                api_reference_accessible_graphs=api_reference_accessible_graphs,
                experience_reference_branch_ids_by_experience_name=(
                    experience_reference_branch_ids_by_experience_name
                ),
                experience_reference_commit_store_root=(
                    experience_reference_commit_store_root
                ),
                role_reference_branch_ids_by_role_name=role_reference_branch_ids_by_role_name,
                price_reference_branch_ids_by_package_name=(
                    price_reference_branch_ids_by_package_name
                ),
            )
        if definition_receipt is None or not definition_receipt.steps:
            raise RuntimeError(
                "Service package materialization requires committed ServiceConfig definition truth: "
                + str(spec.service_toml_path)
            )
        with _record_phase(phase_timings_s, "hydrate_service_config_from_head"):
            service_config = await hydrate_committed_lane_object(
                index=index,
                target_lane=service_config_lane,
                orm_class=ServiceConfig,
                object_id=service_config_id,
                error_context="Service package materialization",
            )
        last_definition_step = definition_receipt.steps[-1]
        definition_commit_id = last_definition_step.commit_id
        definition_head_commit_id = last_definition_step.head_commit_id
        service_config_domain_head_commit_id = last_definition_step.commit_id
    if service_config_domain_head_commit_id is None:
        service_config_domain_head_commit_id = await _committed_lane_head_commit_id(
            service_config_lane
        )
    with _record_phase(
        phase_timings_s, "resolve_service_config_semantic_root_commit_id"
    ):
        service_config_oig_commit_id = (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=branch_id,
                projection_hash=service_config_projection_hash,
                domain_commit_id=service_config_domain_head_commit_id,
            )
            if service_config_domain_head_commit_id is not None
            else None
        )
    if (
        service_config_domain_head_commit_id is None
        or service_config_oig_commit_id is None
    ):
        raise RuntimeError(
            "Service package materialization requires a committed ServiceConfig semantic root "
            f"before building ServicePackage: service_name={spec.service_name!r}"
        )

    code_package_lane_context = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=code_package_projection_hash,
    )
    manifest_package_relative_path = _relative_to(
        path=spec.service_toml_path,
        root=snapshot.package_root,
        label="aware.service.toml package-relative path",
    )
    source_texts_by_relative_path: dict[str, str] = {}
    with _record_phase(
        phase_timings_s,
        f"read_source_text:{manifest_package_relative_path}",
    ):
        source_texts_by_relative_path[manifest_package_relative_path] = (
            spec.service_toml_path.read_text(encoding="utf-8")
        )
    for source_file in snapshot.source_files:
        source_path = (snapshot.package_root / source_file).resolve()
        with _record_phase(
            phase_timings_s, f"read_source_text:{source_file.as_posix()}"
        ):
            source_texts_by_relative_path[source_file.as_posix()] = (
                source_path.read_text(encoding="utf-8")
            )
    with _record_phase(phase_timings_s, "commit_code_package_sources_snapshot"):
        code_package_snapshot = await commit_code_package_text_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=source_code_package_config_id,
            package_name=spec.package_name,
            language=CodeLanguage.aware,
            surface="service",
            manifest_kind="aware_service_toml",
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=(spec.manifest_spec.service.fqn_prefix or "").strip() or None,
            source_texts_by_relative_path=source_texts_by_relative_path,
        )
    with _record_phase(phase_timings_s, "hydrate_code_package_from_head"):
        code_package = await hydrate_committed_lane_object(
            index=index,
            target_lane=code_package_lane_context,
            orm_class=CodePackage,
            object_id=expected_source_code_package_id,
            error_context="Service package materialization",
        )
    if code_package.id != code_package_snapshot.code_package.id:
        raise RuntimeError(
            "Service source CodePackage snapshot hydrated unexpected package id: "
            f"expected={code_package_snapshot.code_package.id} actual={code_package.id}"
        )
    with _record_phase(phase_timings_s, "upsert_implementation_code_packages"):
        implementation_code_package_refs = await _upsert_implementation_code_packages(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            code_package_projection_hash=code_package_projection_hash,
            workspace_root=spec.workspace_root,
            service_package_root=snapshot.package_root,
            implementation_specs=tuple(snapshot.spec.implementation.packages),
        )
    implementation_code_packages = tuple(
        item.code_package for item in implementation_code_package_refs
    )

    service_package_lane_context = MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=service_package_projection_hash,
    )
    service_package_id = stable_service_package_id(name=spec.package_name)
    service_package_fqn_prefix = (
        snapshot.spec.service.fqn_prefix or ""
    ).strip() or None
    service_package_include_paths = JsonArray(snapshot.spec.build.include_paths)
    service_package_exclude_paths = JsonArray(snapshot.spec.build.exclude_paths)
    service_package_compilation_mode = cast(
        str, _enum_value(snapshot.spec.build.compilation_mode)
    )
    service_package_activation_mode = cast(
        str, _enum_value(snapshot.spec.host.activation_mode)
    )
    service_package_dependency_materialization = (
        _service_package_dependency_materialization(
            spec=snapshot.spec,
            workspace_root=spec.workspace_root,
            include_protocol_runtime_hash=False,
        )
    )
    service_package_dependencies = (
        service_package_dependency_materialization.dependencies
    )
    implementation_package_snapshots = _service_package_implementation_snapshots(
        implementation_specs=tuple(snapshot.spec.implementation.packages),
        code_packages=implementation_code_packages,
    )
    with _record_phase(
        phase_timings_s,
        "materialize_service_owned_object_config_graph_packages",
    ):
        (
            owned_object_config_graph_packages,
            object_config_graph_package_snapshots,
        ) = await _materialize_service_owned_object_config_graph_packages(
            workspace_root=spec.workspace_root,
            service_package_root=snapshot.package_root,
            manifest_spec=snapshot.spec,
        )
    with _record_phase(phase_timings_s, "resolve_api_protocol_package_locks"):
        provided_api_package_snapshots, required_api_package_snapshots = (
            await _service_package_api_package_snapshots(
                index=index,
                spec=snapshot.spec,
                workspace_root=spec.workspace_root,
                api_reference_branch_ids_by_api_name=(
                    api_reference_branch_ids_by_api_name
                ),
                api_reference_commit_store_roots_by_api_name=(
                    api_reference_commit_store_roots_by_api_name
                ),
            )
        )
    ontology_package_snapshots = _service_package_ontology_package_snapshots(
        snapshot.spec
    )
    with _record_phase(phase_timings_s, "commit_service_package_manifest_snapshot"):
        service_package_snapshot = await commit_service_package_manifest_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=service_package_projection_hash,
            name=spec.package_name,
            service_config_id=service_config.id,
            service_config_object_instance_graph_commit_id=service_config_oig_commit_id,
            source_code_package_id=code_package.id,
            fqn_prefix=service_package_fqn_prefix,
            version_number=snapshot.spec.service.version_number,
            title=snapshot.spec.service.title,
            description=snapshot.spec.service.description,
            aware_service_version=snapshot.spec.aware_service,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            include_paths=service_package_include_paths,
            exclude_paths=service_package_exclude_paths,
            force_fresh_scan=snapshot.spec.build.force_fresh_scan,
            compilation_mode=service_package_compilation_mode,
            service_surface=snapshot.spec.host.service_surface,
            activation_mode=service_package_activation_mode,
            materialize_on_start=snapshot.spec.host.materialize_on_start,
            dependencies=service_package_dependencies,
            implementation_packages=implementation_package_snapshots,
            ontology_packages=ontology_package_snapshots,
            object_config_graph_packages=object_config_graph_package_snapshots,
            provided_api_packages=provided_api_package_snapshots,
            required_api_packages=required_api_package_snapshots,
        )
    service_package = service_package_snapshot.service_package
    if service_package.id != service_package_id:
        raise RuntimeError(
            "Service package materialization resolved ServicePackage with unexpected id: "
            + f"package_name={spec.package_name!r} expected={service_package_id} actual={service_package.id}"
        )
    if service_package.service_config_id != service_config.id:
        raise RuntimeError(
            "Service package materialization resolved ServicePackage with unexpected service_config_id: "
            + "package_name="
            + f"{spec.package_name!r} expected={service_config.id} actual={service_package.service_config_id}"
        )
    with _record_phase(phase_timings_s, "hydrate_service_package_from_head"):
        hydrated_service_package = await hydrate_committed_lane_object(
            index=index,
            target_lane=service_package_lane_context,
            orm_class=ServicePackage,
            object_id=service_package_id,
            error_context="Service package materialization",
        )
    with _record_phase(phase_timings_s, "validate_service_package"):
        if hydrated_service_package.source_code_package_id != code_package.id:
            raise RuntimeError(
                "Service package materialization resolved ServicePackage with unexpected "
                + "source_code_package_id: "
                + f"package_name={spec.package_name!r} expected={code_package.id} "
                + f"actual={hydrated_service_package.source_code_package_id}"
            )
        if (
            hydrated_service_package.service_config_object_instance_graph_commit_id
            != service_config_oig_commit_id
        ):
            raise RuntimeError(
                "Service package materialization resolved ServicePackage with unexpected "
                + "service_config_object_instance_graph_commit_id: "
                + f"package_name={spec.package_name!r} expected={service_config_oig_commit_id} "
                + "actual="
                + f"{hydrated_service_package.service_config_object_instance_graph_commit_id}"
            )
        _validate_implementation_package_bridges(
            service_package=hydrated_service_package,
            implementation_code_packages=implementation_code_packages,
        )
    with _record_phase(phase_timings_s, "sync_service_api_provider_sets"):
        api_provider_set_sync = await _sync_service_api_provider_sets(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            service_package=hydrated_service_package,
            spec=snapshot.spec,
        )
    with _record_phase(phase_timings_s, "materialize_service_activation_lanes"):
        activation_lanes = await _materialize_service_activation_lanes(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            service_name=spec.service_name,
            compile_plan_payload=spec.compile_plan_payload,
            api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
            api_reference_accessible_graphs=api_reference_accessible_graphs,
            experience_reference_branch_ids_by_experience_name=(
                experience_reference_branch_ids_by_experience_name
            ),
            experience_reference_commit_store_root=(
                experience_reference_commit_store_root
            ),
            role_reference_branch_ids_by_role_name=(
                role_reference_branch_ids_by_role_name
            ),
            price_reference_branch_ids_by_package_name=(
                price_reference_branch_ids_by_package_name
            ),
        )
    phase_timings_s["total"] = _round_duration_s(
        perf_counter() - materialization_started_at
    )
    service_package_domain_commit_id = service_package_snapshot.commit_id
    package_object_instance_graph_commit_id = (
        service_package_snapshot.object_instance_graph_commit_id
    )
    compile_plan_artifact = compile_result.compile_plan_artifact
    if compile_plan_artifact is None:
        raise RuntimeError(
            "Service package materialization requires an emitted compile-plan "
            "artifact before committing its activation lock."
        )
    with _record_phase(phase_timings_s, "emit_committed_service_activation_plan"):
        provided_bridges_by_api_package_id = {
            bridge.api_package_id: bridge
            for bridge in hydrated_service_package.provided_api_packages
        }
        activation_protocol_locks: list[ServiceActivationProtocolLock] = []
        for protocol_snapshot in provided_api_package_snapshots:
            bridge = provided_bridges_by_api_package_id.get(
                protocol_snapshot.api_package_id
            )
            if bridge is None or bridge.id is None:
                raise RuntimeError(
                    "Committed Service activation lock could not resolve its "
                    "ServicePackageProvidedApiPackage identity: "
                    f"api_package_id={protocol_snapshot.api_package_id}"
                )
            required_lock_values = (
                protocol_snapshot.package_name,
                protocol_snapshot.api_package_object_instance_graph_commit_id,
                protocol_snapshot.service_protocol_package_id,
                protocol_snapshot.service_protocol_code_package_id,
                protocol_snapshot.service_protocol_code_package_object_instance_graph_commit_id,
                protocol_snapshot.service_protocol_plan_hash_sha256,
            )
            if any(value is None for value in required_lock_values):
                raise RuntimeError(
                    "Committed Service activation protocol lock snapshot is incomplete: "
                    f"api_package_id={protocol_snapshot.api_package_id}"
                )
            activation_protocol_locks.append(
                ServiceActivationProtocolLock(
                    package_name=cast(str, protocol_snapshot.package_name),
                    service_package_provided_api_package_id=bridge.id,
                    api_package_id=protocol_snapshot.api_package_id,
                    api_package_object_instance_graph_commit_id=cast(
                        UUID,
                        protocol_snapshot.api_package_object_instance_graph_commit_id,
                    ),
                    service_protocol_package_id=cast(
                        UUID, protocol_snapshot.service_protocol_package_id
                    ),
                    service_protocol_code_package_id=cast(
                        UUID, protocol_snapshot.service_protocol_code_package_id
                    ),
                    service_protocol_code_package_object_instance_graph_commit_id=cast(
                        UUID,
                        protocol_snapshot.service_protocol_code_package_object_instance_graph_commit_id,
                    ),
                    service_protocol_plan_hash_sha256=cast(
                        str, protocol_snapshot.service_protocol_plan_hash_sha256
                    ),
                )
            )
        committed_activation_plan = build_service_activation_plan(
            snapshot=compile_result.snapshot,
            compile_plan_artifact=compile_plan_artifact,
            service_package=hydrated_service_package,
            service_package_object_instance_graph_commit_id=(
                package_object_instance_graph_commit_id
            ),
            protocol_locks=tuple(activation_protocol_locks),
        )
        emit_service_activation_plan_artifact(
            plan=committed_activation_plan,
            runtime_package_dir=compile_plan_artifact.path.parent,
            repo_root=compile_result.snapshot.repo_root,
        )

    return ServicePackageMaterializationResult(
        service_toml_path=spec.service_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        service_config=service_config,
        service_package=hydrated_service_package,
        service_source_path=spec.service_source_path,
        source_files=spec.source_files,
        source_code_package_id=hydrated_service_package.source_code_package_id,
        implementation_code_package_ids=tuple(
            ref.code_package.id
            for ref in implementation_code_package_refs
            if ref.code_package.id is not None
        ),
        implementation_code_package_refs=tuple(
            ref.to_payload() for ref in implementation_code_package_refs
        ),
        object_config_graph_packages=owned_object_config_graph_packages,
        api_provider_set_refs=api_provider_set_sync.provider_set_refs,
        api_provider_set_commit_id=api_provider_set_sync.domain_commit_id,
        api_provider_set_head_commit_id=(
            api_provider_set_sync.object_instance_graph_commit_id
        ),
        definition_commit_id=definition_commit_id,
        definition_head_commit_id=definition_head_commit_id,
        service_config_object_instance_graph_commit_id=(
            hydrated_service_package.service_config_object_instance_graph_commit_id
        ),
        package_commit_id=service_package_domain_commit_id,
        package_head_commit_id=service_package_snapshot.head_commit_id,
        package_object_instance_graph_commit_id=(
            package_object_instance_graph_commit_id
        ),
        activation_lanes=activation_lanes,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
    )


def service_activation_lane(
    *,
    projection_hash: str,
    lane_kind: str,
    service_name: str,
) -> MaterializationLaneContext:
    normalized_name = service_name.strip()
    if not normalized_name:
        raise RuntimeError("Service activation requires non-empty service_name.")
    normalized_kind = lane_kind.strip()
    if not normalized_kind:
        raise RuntimeError("Service activation requires non-empty lane_kind.")
    return MaterializationLaneContext(
        branch_id=uuid5(
            NAMESPACE_URL,
            (
                "aware://service/runtime/activation-branch/v1/"
                f"{normalized_kind.casefold()}/{normalized_name.casefold()}"
            ),
        ),
        projection_hash=projection_hash,
    )


async def _materialize_service_activation_lanes(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_name: str,
    compile_plan_payload: Mapping[str, object],
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None,
    api_reference_accessible_graphs: Sequence[ObjectConfigGraph],
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID] | None,
    experience_reference_commit_store_root: Path | None,
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None,
    price_reference_branch_ids_by_package_name: Mapping[str, UUID] | None,
) -> tuple[ServiceActivationLaneMaterialization, ...]:
    service_config_projection_hash = _resolve_canonical_service_config_projection_hash(
        index
    )
    service_projection_hash = _resolve_canonical_service_projection_hash(index)
    service_config_lane = service_activation_lane(
        projection_hash=service_config_projection_hash,
        lane_kind="service-config",
        service_name=service_name,
    )
    service_lane = service_activation_lane(
        projection_hash=service_projection_hash,
        lane_kind="service",
        service_name=service_name,
    )
    receipt = await materialize_service_definition_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=service_config_lane,
        compile_plan_payloads=(compile_plan_payload,),
        api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        api_reference_accessible_graphs=api_reference_accessible_graphs,
        experience_reference_branch_ids_by_experience_name=(
            experience_reference_branch_ids_by_experience_name
        ),
        experience_reference_commit_store_root=(experience_reference_commit_store_root),
        role_reference_branch_ids_by_role_name=role_reference_branch_ids_by_role_name,
        price_reference_branch_ids_by_package_name=(
            price_reference_branch_ids_by_package_name
        ),
    )
    if receipt is None:
        raise RuntimeError(
            "Service package materialization produced no ServiceConfig activation lane."
        )
    service_config_head_commit_id = await _committed_lane_head_commit_id(
        service_config_lane
    )
    if service_config_head_commit_id is None:
        raise RuntimeError(
            "Service package materialization produced no committed ServiceConfig "
            f"activation HEAD: service={service_name!r}."
        )
    service_config_oig_commit_id = (
        await _object_instance_graph_commit_id_from_domain_commit(
            branch_id=service_config_lane.branch_id,
            projection_hash=service_config_lane.projection_hash,
            domain_commit_id=service_config_head_commit_id,
        )
    )
    if service_config_oig_commit_id is None:
        raise RuntimeError(
            "Service package materialization produced no ServiceConfig activation "
            f"OIG commit: service={service_name!r}."
        )
    service_config_id = stable_service_config_id(name=service_name)
    service_snapshot = await commit_service_instance_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=service_lane.branch_id,
        projection_hash=service_lane.projection_hash,
        service_config_id=service_config_id,
        name=service_name,
        description=None,
    )
    service_id = service_snapshot.service.id
    if service_id is None:
        raise RuntimeError(
            "Service package materialization produced Service activation without id."
        )
    return (
        ServiceActivationLaneMaterialization(
            service_name=service_name,
            service_config_id=service_config_id,
            service_id=service_id,
            service_config_branch_id=service_config_lane.branch_id,
            service_config_projection_hash=service_config_lane.projection_hash,
            service_config_head_commit_id=service_config_head_commit_id,
            service_config_object_instance_graph_commit_id=(
                service_config_oig_commit_id
            ),
            service_branch_id=service_lane.branch_id,
            service_projection_hash=service_lane.projection_hash,
            service_head_commit_id=service_snapshot.head_commit_id,
            service_object_instance_graph_commit_id=(
                service_snapshot.object_instance_graph_commit_id
            ),
        ),
    )


async def _materialize_service_owned_object_config_graph_packages(
    *,
    workspace_root: Path,
    service_package_root: Path,
    manifest_spec: AwareServiceTomlSpec,
) -> tuple[
    tuple[ServiceOwnedObjectConfigGraphPackageMaterialization, ...],
    tuple[ServicePackageObjectConfigGraphPackageSnapshot, ...],
]:
    service_root = service_package_root.resolve()
    materializations: list[ServiceOwnedObjectConfigGraphPackageMaterialization] = []
    snapshots: list[ServicePackageObjectConfigGraphPackageSnapshot] = []
    for declared_package in manifest_spec.object_config_graph_packages:
        declared_manifest_path = (service_root / declared_package.manifest).resolve()
        _assert_path_within(
            base=service_root,
            candidate=declared_manifest_path,
            label="object_config_graph_packages.manifest",
        )
        if not declared_manifest_path.exists():
            raise FileNotFoundError(
                "Service-owned ObjectConfigGraphPackage manifest not found: "
                f"{declared_manifest_path}"
            )
        if not declared_manifest_path.is_file():
            raise RuntimeError(
                "Service-owned ObjectConfigGraphPackage manifest must be a file: "
                f"{declared_manifest_path}"
            )

        child_spec = load_aware_toml_spec(toml_path=declared_manifest_path)
        manifest_relative_path = _relative_to(
            path=declared_manifest_path,
            root=workspace_root,
            label="service_owned_object_config_graph_package",
        )
        object_config_graph_package_oig_commit_id = _optional_uuid_from_manifest_pin(
            declared_oig_commit_id=(declared_package.object_instance_graph_commit_id),
            manifest_path=declared_manifest_path,
        )
        role = (declared_package.role or "").strip() or "local_state"
        package_kind = cast(str, _enum_value(child_spec.package.kind))
        object_config_graph_package_id = stable_object_config_graph_package_id(
            package_name=child_spec.package.package_name,
            fqn_prefix=child_spec.package.fqn_prefix,
        )
        object_config_graph_id = stable_object_config_graph_id(
            fqn_prefix=child_spec.package.fqn_prefix,
            language=CodeLanguage.aware.value,
        )
        source_code_package_config_id = _source_code_package_config_id(
            manifest_kind="aware_ontology_toml",
            surface="structure",
        )
        source_code_package_id = stable_code_package_id(
            code_package_config_id=source_code_package_config_id,
            package_name=child_spec.package.package_name,
            language=CodeLanguage.aware.value,
        )
        materializations.append(
            ServiceOwnedObjectConfigGraphPackageMaterialization(
                manifest_path=declared_manifest_path,
                manifest_relative_path=manifest_relative_path,
                role=role,
                package_name=child_spec.package.package_name,
                package_fqn_prefix=child_spec.package.fqn_prefix,
                package_kind=package_kind,
                language_materialization_targets=(
                    _aware_toml_materialization_targets_payload(
                        child_spec.language_materializations
                    )
                ),
                object_config_graph_package_id=object_config_graph_package_id,
                object_config_graph_id=object_config_graph_id,
                package_branch_id=None,
                source_code_package_id=source_code_package_id,
                object_config_graph_package_commit_id=None,
                object_config_graph_package_head_commit_id=None,
                object_config_graph_package_object_instance_graph_commit_id=(
                    object_config_graph_package_oig_commit_id
                ),
                object_config_graph_commit_id=None,
                object_config_graph_head_commit_id=None,
                object_config_graph_object_instance_graph_commit_id=None,
            )
        )
        snapshots.append(
            ServicePackageObjectConfigGraphPackageSnapshot(
                object_config_graph_package_id=object_config_graph_package_id,
                manifest_relative_path=manifest_relative_path,
                role=role,
                package_kind=package_kind,
                object_config_graph_package_object_instance_graph_commit_id=(
                    object_config_graph_package_oig_commit_id
                ),
                expected_hash_sha256=declared_package.expected_hash_sha256,
                description=declared_package.description,
            )
        )
    return tuple(materializations), tuple(snapshots)


def _aware_toml_materialization_targets_payload(
    targets: Sequence[object],
) -> tuple[dict[str, object], ...]:
    payload: list[dict[str, object]] = []
    for target in targets:
        row: dict[str, object] = {
            "role": str(getattr(target, "role")),
            "language": str(getattr(target, "language")),
            "output_dir": str(getattr(target, "output_dir")),
            "import_root": str(getattr(target, "import_root")),
            "package_name": str(getattr(target, "package_name")),
            "materialization_source": str(getattr(target, "materialization_source")),
        }
        renderer_kind = getattr(target, "renderer_kind")
        if renderer_kind is not None:
            row["renderer_kind"] = str(renderer_kind)
        renderer_profile = getattr(target, "renderer_profile")
        if renderer_profile is not None:
            row["renderer_profile"] = str(renderer_profile)
        stable_ids_import_root = getattr(target, "stable_ids_import_root")
        if stable_ids_import_root is not None:
            row["stable_ids_import_root"] = str(stable_ids_import_root)
        stable_ids_resolution_policy = getattr(target, "stable_ids_resolution_policy")
        if stable_ids_resolution_policy is not None:
            row["stable_ids_resolution_policy"] = str(stable_ids_resolution_policy)
        if bool(getattr(target, "source_is_runtime")):
            row["source_is_runtime"] = True
        payload.append(row)
    return tuple(payload)


def _optional_uuid_from_manifest_pin(
    *,
    declared_oig_commit_id: str | None,
    manifest_path: Path,
) -> UUID | None:
    if declared_oig_commit_id is None:
        return None
    try:
        return UUID(declared_oig_commit_id)
    except ValueError as exc:
        raise RuntimeError(
            "Service-owned ObjectConfigGraphPackage OIG pin is not a UUID: "
            f"manifest_path={manifest_path} value={declared_oig_commit_id!r}"
        ) from exc


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Service package materialization path resolved outside workspace root: "
            + f"label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    relative_text = relative.as_posix()
    return relative_text or "."


def _assert_path_within(*, base: Path, candidate: Path, label: str) -> None:
    resolved_base = base.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as exc:
        raise RuntimeError(
            "Service package materialization path resolved outside service "
            f"package root: label={label} root={resolved_base} "
            f"path={resolved_candidate}"
        ) from exc


def _enum_value(value: object) -> object:
    enum_value = getattr(value, "value", None)
    return enum_value if enum_value is not None else value


def _service_package_dependencies_payload(
    *,
    spec: AwareServiceTomlSpec,
    workspace_root: Path,
) -> JsonArray:
    return resolve_service_package_dependency_payloads(
        spec=spec,
        workspace_root=workspace_root,
    )


def resolve_service_package_dependency_payloads(
    *,
    spec: AwareServiceTomlSpec,
    workspace_root: Path,
) -> JsonArray:
    return _service_package_dependency_materialization(
        spec=spec,
        workspace_root=workspace_root,
        include_protocol_runtime_hash=True,
    ).dependencies


def _service_package_dependency_materialization(
    *,
    spec: AwareServiceTomlSpec,
    workspace_root: Path,
    include_protocol_runtime_hash: bool,
) -> _ServicePackageDependencyMaterialization:
    dependencies: list[dict[str, object]] = []
    for dependency in spec.dependencies:
        if (
            _enum_value(getattr(dependency, "kind", None)) == "api_service_protocol"
            and not include_protocol_runtime_hash
        ):
            continue
        dependencies.append(
            _service_package_dependency_payload(
                dependency=dependency,
                workspace_root=workspace_root,
                include_protocol_runtime_hash=include_protocol_runtime_hash,
            )
        )
    return _ServicePackageDependencyMaterialization(
        dependencies=JsonArray(dependencies),
    )


def _service_package_dependency_payload(
    *,
    dependency: object,
    workspace_root: Path,
    include_protocol_runtime_hash: bool,
) -> dict[str, object]:
    kind = _enum_value(getattr(dependency, "kind", None))
    package_name = str(getattr(dependency, "package_name", "") or "").strip()
    protocol_plan_digest: str | None = None
    normalized_expected_hash_sha256: str | None = None
    if kind == "api_service_protocol" and include_protocol_runtime_hash:
        artifact = _api_service_protocol_artifact_hash(
            workspace_root=workspace_root,
            package_name=package_name,
        )
        if artifact is None:
            raise RuntimeError(
                "Service materialization requires the API service protocol plan "
                f"artifact: package_name={package_name!r}"
            )
        protocol_plan_digest = artifact.hash_sha256
    elif kind != "api_service_protocol":
        expected_hash_sha256 = getattr(dependency, "expected_hash_sha256", None)
        normalized_expected_hash_sha256 = (
            str(expected_hash_sha256).strip()
            if expected_hash_sha256 is not None
            else None
        )
    payload: dict[str, object] = {
        "package_name": package_name,
        "version_number": getattr(dependency, "version_number", None),
        "kind": kind,
    }
    if normalized_expected_hash_sha256 is not None:
        payload["expected_hash_sha256"] = normalized_expected_hash_sha256
    if protocol_plan_digest is not None:
        payload["service_protocol_plan_hash_sha256"] = protocol_plan_digest
    route_authority_selector = getattr(dependency, "route_authority_selector", None)
    if route_authority_selector is not None:
        selector_payload = route_authority_selector.to_payload()
        if selector_payload:
            payload["route_authority_selector"] = selector_payload
    return payload


@dataclass(frozen=True, slots=True)
class _ApiServiceProtocolArtifactHash:
    path: Path
    hash_sha256: str


def _api_service_protocol_artifact_hash(
    *,
    workspace_root: Path,
    package_name: str,
) -> _ApiServiceProtocolArtifactHash | None:
    if not package_name:
        return None
    for dependency_root in api_service_protocol_dependency_roots(workspace_root):
        artifact_path = (
            dependency_root
            / ".aware"
            / "api"
            / "runtime"
            / package_name
            / "api.service_protocol_plan.json"
        )
        if not artifact_path.is_file():
            continue
        payload = json.loads(artifact_path.read_text(encoding="utf-8") or "{}")
        if not isinstance(payload, dict):
            raise RuntimeError(
                "Service package materialization expected API service-protocol "
                f"artifact JSON object: {artifact_path}"
            )
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return _ApiServiceProtocolArtifactHash(
            path=artifact_path,
            hash_sha256=sha256(canonical).hexdigest(),
        )
    return None


async def _upsert_implementation_code_packages(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    code_package_projection_hash: str,
    workspace_root: Path,
    service_package_root: Path,
    implementation_specs: tuple[AwareServiceTomlImplementationPackageSpec, ...],
) -> tuple[_ImplementationCodePackageMaterializationRef, ...]:
    del runtime
    code_package_refs: list[_ImplementationCodePackageMaterializationRef] = []
    for implementation_spec in implementation_specs:
        code_language = _implementation_language_to_code_language(
            implementation_spec.language
        )
        code_package_config_id = _source_code_package_config_id(
            manifest_kind="pyproject_toml",
            surface="service",
        )
        expected_code_package_id = stable_code_package_id(
            code_package_config_id=code_package_config_id,
            package_name=implementation_spec.package_name,
            language=code_language.value,
        )
        implementation_branch_id = _implementation_code_package_branch_id(
            code_package_id=expected_code_package_id,
        )
        code_package_lane_context = MaterializationLaneContext(
            branch_id=implementation_branch_id,
            projection_hash=code_package_projection_hash,
        )
        implementation_package_root = (
            service_package_root / implementation_spec.package_root
        ).resolve()
        _assert_dir_within(
            root=service_package_root,
            path=implementation_package_root,
            label="implementation.package_root",
        )
        implementation_manifest_path = (
            implementation_package_root / implementation_spec.manifest_path
        ).resolve()
        _assert_file_within(
            root=implementation_package_root,
            path=implementation_manifest_path,
            label="implementation.manifest_path",
        )
        implementation_sources_root = (
            implementation_package_root
            / implementation_spec.import_root.replace(".", "/")
        ).resolve()
        _assert_dir_within(
            root=implementation_package_root,
            path=implementation_sources_root,
            label="implementation.import_root",
        )
        package_root_relative = _relative_to(
            path=implementation_package_root,
            root=workspace_root,
            label="implementation.package_root",
        )
        manifest_relative_path = _relative_to(
            path=implementation_manifest_path,
            root=workspace_root,
            label="implementation.manifest_path",
        )
        sources_root_relative = _relative_to(
            path=implementation_sources_root,
            root=workspace_root,
            label="implementation.import_root",
        )
        unparsed_texts_by_relative_path = _implementation_code_package_unparsed_texts(
            implementation_package_root=implementation_package_root,
            implementation_manifest_path=implementation_manifest_path,
            implementation_spec=implementation_spec,
        )
        snapshot_commit = await commit_code_package_text_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=implementation_branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=code_package_config_id,
            package_name=implementation_spec.package_name,
            language=code_language,
            surface="service",
            manifest_kind="pyproject_toml",
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=implementation_spec.import_root,
            source_texts_by_relative_path={},
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
        )
        hydrated_code_package = await hydrate_committed_lane_object(
            index=index,
            target_lane=code_package_lane_context,
            orm_class=CodePackage,
            object_id=expected_code_package_id,
            error_context="Service implementation package materialization",
        )
        domain_commit_id = snapshot_commit.commit_id
        if domain_commit_id is None:
            raise RuntimeError(
                "Service implementation CodePackage materialization did not commit: "
                f"code_package_id={expected_code_package_id}"
            )
        code_package_refs.append(
            _ImplementationCodePackageMaterializationRef(
                code_package=hydrated_code_package,
                branch_id=implementation_branch_id,
                domain_commit_id=domain_commit_id,
                object_instance_graph_commit_id=(
                    snapshot_commit.object_instance_graph_commit_id
                ),
            )
        )
    return tuple(code_package_refs)


def _implementation_code_package_branch_id(
    *,
    code_package_id: UUID,
) -> UUID:
    return _stable_service_materialization_branch_id(
        namespace="code-package",
        value=str(code_package_id),
    )


def _service_api_provider_set_branch_id(
    *,
    provider_set_id: UUID,
) -> UUID:
    return _stable_service_materialization_branch_id(
        namespace="service-api-provider-set",
        value=str(provider_set_id),
    )


def _stable_service_materialization_branch_id(
    *,
    namespace: str,
    value: str,
) -> UUID:
    normalized_namespace = (namespace or "").casefold().strip()
    normalized_value = (value or "").casefold().strip()
    if not normalized_namespace or not normalized_value:
        raise RuntimeError(
            "Service materialization branch identity requires non-empty namespace "
            "and value."
        )
    return uuid5(
        NAMESPACE_URL,
        (
            "aware://service/runtime/materialization-branch/v1/"
            f"{normalized_namespace}/{normalized_value}"
        ),
    )


def _implementation_language_to_code_language(
    language: AwareServiceImplementationLanguage,
) -> CodeLanguage:
    if language == AwareServiceImplementationLanguage.python:
        return CodeLanguage.python
    raise RuntimeError(f"Unsupported service implementation language: {language!r}")


def _implementation_code_source_files(
    *,
    package_root: Path,
    implementation_spec: AwareServiceTomlImplementationPackageSpec,
) -> tuple[Path, ...]:
    include_paths = implementation_spec.include_paths or [
        implementation_spec.import_root.replace(".", "/") + "/**/*.py"
    ]
    files_by_rel: dict[str, Path] = {}
    for include_path in include_paths:
        pattern = (include_path or "").strip()
        if not pattern:
            continue
        for candidate in package_root.glob(pattern):
            if not candidate.is_file() or candidate.suffix != ".py":
                continue
            resolved = candidate.resolve()
            _assert_file_within(
                root=package_root,
                path=resolved,
                label="implementation.include_paths",
            )
            rel_path = resolved.relative_to(package_root).as_posix()
            if _is_path_excluded(
                rel_path=rel_path,
                exclude_patterns=implementation_spec.exclude_paths,
            ):
                continue
            files_by_rel[rel_path] = resolved
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _implementation_code_package_unparsed_texts(
    *,
    implementation_package_root: Path,
    implementation_manifest_path: Path,
    implementation_spec: AwareServiceTomlImplementationPackageSpec,
) -> dict[str, str]:
    texts: dict[str, str] = {
        implementation_manifest_path.relative_to(
            implementation_package_root
        ).as_posix(): implementation_manifest_path.read_text(encoding="utf-8")
    }
    for support_file in _implementation_package_support_files(
        implementation_package_root=implementation_package_root,
        implementation_manifest_path=implementation_manifest_path,
    ):
        relative_path = support_file.relative_to(implementation_package_root).as_posix()
        texts.setdefault(relative_path, support_file.read_text(encoding="utf-8"))
    for source_file in _implementation_code_source_files(
        package_root=implementation_package_root,
        implementation_spec=implementation_spec,
    ):
        relative_path = source_file.relative_to(implementation_package_root).as_posix()
        texts[relative_path] = source_file.read_text(encoding="utf-8")
    return texts


def _implementation_package_support_files(
    *,
    implementation_package_root: Path,
    implementation_manifest_path: Path,
) -> tuple[Path, ...]:
    try:
        manifest = tomllib.loads(
            implementation_manifest_path.read_text(encoding="utf-8")
        )
    except tomllib.TOMLDecodeError:
        return ()
    support_paths = _pyproject_package_support_paths(manifest=manifest)
    support_files: dict[str, Path] = {}
    for support_path in support_paths:
        candidates = (
            sorted(implementation_package_root.glob(support_path))
            if any(character in support_path for character in "*?[]")
            else [implementation_package_root / support_path]
        )
        for candidate in candidates:
            if not candidate.is_file() or candidate.is_symlink():
                continue
            resolved = candidate.resolve()
            _assert_file_within(
                root=implementation_package_root,
                path=resolved,
                label="implementation.pyproject_support_file",
            )
            relative_path = resolved.relative_to(implementation_package_root).as_posix()
            support_files[relative_path] = resolved
    return tuple(support_files[key] for key in sorted(support_files))


def _pyproject_package_support_paths(
    *,
    manifest: Mapping[str, object],
) -> tuple[str, ...]:
    paths: list[str] = []
    project = manifest.get("project")
    if isinstance(project, Mapping):
        readme = project.get("readme")
        if isinstance(readme, str):
            paths.append(readme)
        elif isinstance(readme, Mapping):
            readme_file = readme.get("file")
            if isinstance(readme_file, str):
                paths.append(readme_file)
    wheel = _nested_mapping(
        manifest,
        ("tool", "hatch", "build", "targets", "wheel"),
    )
    include = wheel.get("include")
    if isinstance(include, list):
        paths.extend(item for item in include if isinstance(item, str))
    normalized: list[str] = []
    for path in paths:
        text = path.strip().strip("/")
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def _nested_mapping(
    mapping: Mapping[str, object],
    path: tuple[str, ...],
) -> Mapping[str, object]:
    current: object = mapping
    for key in path:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(key)
    return current if isinstance(current, Mapping) else {}


def _is_path_excluded(*, rel_path: str, exclude_patterns: Sequence[str]) -> bool:
    token = PurePosixPath(rel_path)
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


def _assert_file_within(*, root: Path, path: Path, label: str) -> None:
    resolved = path.resolve()
    _assert_within(root=root, path=resolved, label=label)
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} must resolve to a file: {resolved}")


def _assert_dir_within(*, root: Path, path: Path, label: str) -> None:
    resolved = path.resolve()
    _assert_within(root=root, path=resolved, label=label)
    if not resolved.is_dir():
        raise NotADirectoryError(f"{label} must resolve to a directory: {resolved}")


def _assert_within(*, root: Path, path: Path, label: str) -> None:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if resolved_path == resolved_root or resolved_root in resolved_path.parents:
        return
    raise RuntimeError(
        "Service package materialization path resolved outside declared root: "
        f"label={label} root={resolved_root} path={resolved_path}"
    )


def _service_package_implementation_snapshots(
    *,
    implementation_specs: tuple[AwareServiceTomlImplementationPackageSpec, ...],
    code_packages: tuple[CodePackage, ...],
) -> tuple[ServicePackageImplementationSnapshot, ...]:
    code_packages_by_name = {
        (code_package.package_name, code_package.language): code_package
        for code_package in code_packages
    }
    snapshots: list[ServicePackageImplementationSnapshot] = []
    for implementation_spec in implementation_specs:
        code_language = _implementation_language_to_code_language(
            implementation_spec.language
        )
        code_package = code_packages_by_name.get(
            (implementation_spec.package_name, code_language)
        )
        if code_package is None or code_package.id is None:
            raise RuntimeError(
                "Service implementation package bridge requires a materialized CodePackage: "
                f"package_name={implementation_spec.package_name!r} language={code_language.value!r}"
            )
        snapshots.append(
            ServicePackageImplementationSnapshot(
                code_package_id=code_package.id,
                package_name=implementation_spec.package_name,
                language=code_language,
                import_root=implementation_spec.import_root,
                manifest_relative_path=code_package.manifest_relative_path,
                package_root=code_package.package_root,
                entrypoint=implementation_spec.entrypoint,
                role=implementation_spec.role.value,
                include_paths=JsonArray(implementation_spec.include_paths),
                exclude_paths=JsonArray(implementation_spec.exclude_paths),
            )
        )
    return tuple(snapshots)


def _validate_implementation_package_bridges(
    *,
    service_package: ServicePackage,
    implementation_code_packages: tuple[CodePackage, ...],
) -> None:
    expected_ids = {
        code_package.id
        for code_package in implementation_code_packages
        if code_package.id is not None
    }
    attached_ids = {
        bridge.code_package_id for bridge in service_package.implementation_packages
    }
    missing = expected_ids - attached_ids
    if missing:
        raise RuntimeError(
            "ServicePackage implementation package bridge hydration is incomplete: "
            f"service_package_id={service_package.id} "
            f"missing_code_package_ids={sorted(str(item) for item in missing)}"
        )


async def _service_package_api_package_snapshots(
    *,
    index: MetaGraphRuntimeIndex,
    spec: AwareServiceTomlSpec,
    workspace_root: Path,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None,
    api_reference_commit_store_roots_by_api_name: Mapping[str, Path] | None,
) -> tuple[
    tuple[ServicePackageApiPackageSnapshot, ...],
    tuple[ServicePackageApiPackageSnapshot, ...],
]:
    provided: list[ServicePackageApiPackageSnapshot] = []
    required: list[ServicePackageApiPackageSnapshot] = []
    for dependency in spec.dependencies:
        dependency_kind = str(_enum_value(dependency.kind))
        if dependency_kind not in {"api_service_protocol", "api_invocation"}:
            continue
        package_name = dependency.package_name.strip()
        if not package_name:
            continue
        api_package_id = stable_api_package_id(name=package_name)
        if dependency_kind == "api_service_protocol":
            branch_id = (
                api_reference_branch_ids_by_api_name.get(package_name)
                if api_reference_branch_ids_by_api_name is not None
                else None
            )
            if branch_id is None:
                raise RuntimeError(
                    "ServicePackage protocol lock could not resolve the committed "
                    f"API package branch: package_name={package_name!r}"
                )
            api_package_projection_hash = find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="ApiPackage",
            )
            api_package_lane = MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_package_projection_hash,
            )
            commit_store_root = (
                api_reference_commit_store_roots_by_api_name.get(package_name)
                if api_reference_commit_store_roots_by_api_name is not None
                else None
            )
            commit_store = (
                FSCommitStore(root_dir=commit_store_root)
                if commit_store_root is not None
                else None
            )
            api_package = await _maybe_hydrate_committed_lane_object(
                index=index,
                target_lane=api_package_lane,
                orm_class=ApiPackage,
                object_id=api_package_id,
                commit_store=commit_store,
            )
            if api_package is None:
                raise RuntimeError(
                    "ServicePackage protocol lock could not hydrate committed "
                    f"ApiPackage: package_name={package_name!r} "
                    f"api_package_id={api_package_id} branch_id={branch_id}"
                )
            if api_package.name != package_name:
                raise RuntimeError(
                    "ServicePackage protocol lock hydrated an ApiPackage with a "
                    "different package name: "
                    f"expected={package_name!r} actual={api_package.name!r}"
                )
            domain_commit_id = await _committed_lane_head_commit_id(
                api_package_lane,
                commit_store=commit_store,
            )
            if domain_commit_id is None:
                raise RuntimeError(
                    "ServicePackage protocol lock requires a committed ApiPackage "
                    f"head: package_name={package_name!r}"
                )
            api_package_oig_commit_id = (
                await _object_instance_graph_commit_id_from_domain_commit(
                    branch_id=branch_id,
                    projection_hash=api_package_projection_hash,
                    domain_commit_id=domain_commit_id,
                    commit_store=commit_store,
                )
            )
            if api_package_oig_commit_id is None:
                raise RuntimeError(
                    "ServicePackage protocol lock could not resolve the ApiPackage "
                    f"OIG commit: package_name={package_name!r}"
                )
            protocol_packages = tuple(
                language_package
                for language_package in api_package.language_packages
                if isinstance(language_package, ApiPackageLanguagePackage)
                and language_package.output_key == "python.service_protocol_package"
            )
            if len(protocol_packages) != 1:
                raise RuntimeError(
                    "ServicePackage protocol lock requires exactly one API-owned "
                    "python.service_protocol_package output: "
                    f"package_name={package_name!r} "
                    f"candidates={[item.output_key for item in api_package.language_packages]!r}"
                )
            protocol_package = protocol_packages[0]
            if protocol_package.api_package_id != api_package.id:
                raise RuntimeError(
                    "ServicePackage protocol lock selected a language package from "
                    "a different ApiPackage: "
                    f"expected={api_package.id} "
                    f"actual={protocol_package.api_package_id}"
                )
            if protocol_package.object_instance_graph_commit_id is None:
                raise RuntimeError(
                    "ServicePackage protocol lock selected an API language package "
                    "without an exact CodePackage commit pin: "
                    f"service_protocol_package_id={protocol_package.id}"
                )
            artifact = _api_service_protocol_artifact_hash(
                workspace_root=workspace_root,
                package_name=package_name,
            )
            if artifact is None:
                raise RuntimeError(
                    "ServicePackage protocol lock requires the materialized API "
                    f"service protocol plan: package_name={package_name!r}"
                )
            provided.append(
                ServicePackageApiPackageSnapshot(
                    api_package_id=api_package_id,
                    package_name=package_name,
                    api_package_object_instance_graph_commit_id=(
                        api_package_oig_commit_id
                    ),
                    service_protocol_package_id=protocol_package.id,
                    service_protocol_code_package_id=(protocol_package.code_package_id),
                    service_protocol_code_package_object_instance_graph_commit_id=(
                        protocol_package.object_instance_graph_commit_id
                    ),
                    service_protocol_plan_hash_sha256=artifact.hash_sha256,
                    description=(
                        "Service API protocol dependency provided by this ServicePackage."
                    ),
                )
            )
            continue
        required.append(
            ServicePackageApiPackageSnapshot(
                api_package_id=api_package_id,
                description=(
                    "Service API invocation dependency required by this ServicePackage."
                ),
            )
        )
    return tuple(provided), tuple(required)


def _service_package_ontology_package_snapshots(
    spec: AwareServiceTomlSpec,
) -> tuple[ServicePackageOntologyPackageSnapshot, ...]:
    snapshots: list[ServicePackageOntologyPackageSnapshot] = []
    for ontology_package in spec.ontology_packages:
        package_name = ontology_package.package_name.strip()
        fqn_prefix = ontology_package.fqn_prefix.strip()
        if not package_name or not fqn_prefix:
            continue
        snapshots.append(
            ServicePackageOntologyPackageSnapshot(
                ontology_package_id=stable_ontology_package_id(
                    name=package_name,
                    fqn_prefix=fqn_prefix,
                ),
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                role=ontology_package.role,
                requirement_mode=ontology_package.requirement_mode,
                ontology_package_object_instance_graph_commit_id=(
                    UUID(ontology_package.object_instance_graph_commit_id)
                    if ontology_package.object_instance_graph_commit_id is not None
                    else None
                ),
                expected_hash_sha256=ontology_package.expected_hash_sha256,
                description=ontology_package.description,
            )
        )
    return tuple(snapshots)


async def _sync_service_api_provider_sets(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    service_package: ServicePackage,
    spec: AwareServiceTomlSpec,
) -> _ServiceApiProviderSetSyncResult:
    del runtime
    if not spec.api_provider_sets:
        return _ServiceApiProviderSetSyncResult(
            provider_set_refs=(),
            domain_commit_id=None,
            object_instance_graph_commit_id=None,
        )
    if service_package.id is None:
        raise RuntimeError(
            "Service API provider-set sync requires committed ServicePackage.id"
        )

    provider_set_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ServiceApiProviderSet",
    )
    provider_set_refs: list[dict[str, object]] = []
    last_provider_set_domain_commit_id: UUID | None = None
    last_provider_set_oig_commit_id: UUID | None = None
    for provider_set_spec in spec.api_provider_sets:
        provider_set_key = provider_set_spec.key.strip()
        provider_set_id = stable_service_api_provider_set_id(
            key=provider_set_key,
        )
        provider_set_branch_id = _service_api_provider_set_branch_id(
            provider_set_id=provider_set_id,
        )
        provider_set_snapshot = await commit_service_api_provider_set_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=provider_set_branch_id,
            projection_hash=provider_set_projection_hash,
            key=provider_set_key,
            title=provider_set_spec.title,
            description=provider_set_spec.description,
            version_number=spec.service.version_number,
            service_package_id=service_package.id,
            membership_key=provider_set_spec.membership_key,
            membership_description=(
                provider_set_spec.description
                or "ServicePackage participates in this API provider set."
            ),
        )
        membership = provider_set_snapshot.membership
        provider_set_domain_commit_id = provider_set_snapshot.commit_id
        provider_set_oig_commit_id = (
            provider_set_snapshot.object_instance_graph_commit_id
        )
        last_provider_set_domain_commit_id = provider_set_domain_commit_id
        last_provider_set_oig_commit_id = provider_set_oig_commit_id
        provider_set_refs.append(
            {
                "provider_set_key": provider_set_key,
                "provider_set_id": provider_set_id,
                "provider_set_branch_id": provider_set_branch_id,
                "provider_set_commit_id": provider_set_domain_commit_id,
                "provider_set_object_instance_graph_commit_id": (
                    provider_set_oig_commit_id
                ),
                "service_package_id": service_package.id,
                "service_package_name": service_package.name,
                "membership_id": membership.id,
                "membership_key": provider_set_spec.membership_key,
                "title": provider_set_spec.title,
                "description": provider_set_spec.description,
            }
        )
    return _ServiceApiProviderSetSyncResult(
        provider_set_refs=tuple(provider_set_refs),
        domain_commit_id=last_provider_set_domain_commit_id,
        object_instance_graph_commit_id=last_provider_set_oig_commit_id,
    )


async def materialize_service_compile_plan_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    workspace_root: Path | None = None,
) -> MaterializationRunReceipt | None:
    _ = runtime
    if workspace_root is None:
        raise RuntimeError(
            "Service compile-plan ontology materialization requires explicit "
            "workspace_root; runtime.manifest_path root discovery is retired."
        )
    compile_plan_payloads = load_service_compile_plan_payloads(
        repo_root=workspace_root.resolve()
    )
    if not compile_plan_payloads:
        return None
    return await materialize_service_definition_ontology(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        lane=lane,
        compile_plan_payloads=compile_plan_payloads,
    )


async def materialize_service_definition_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    compile_plan_payloads: Sequence[Mapping[str, object]],
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None = None,
    api_reference_accessible_graphs: Sequence[ObjectConfigGraph] = (),
    experience_reference_branch_ids_by_experience_name: (
        Mapping[str, UUID] | None
    ) = None,
    experience_reference_commit_store_root: Path | None = None,
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None = None,
    price_reference_branch_ids_by_package_name: Mapping[str, UUID] | None = None,
) -> MaterializationRunReceipt | None:
    specs = resolve_service_definition_materialization_specs(
        compile_plan_payloads=compile_plan_payloads
    )
    if not specs:
        return None

    service_config_projection_hash = _resolve_canonical_service_config_projection_hash(
        index
    )
    if lane.projection_hash != service_config_projection_hash:
        raise RuntimeError(
            "Service compile-plan ontology materialization requires the service_config projection lane"
        )

    api_projection_hash = find_meta_graph_projection_hash_by_name(
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
        accessible_graphs=api_reference_accessible_graphs,
    )
    experience_context: _CommittedExperienceReferenceContext | None = None
    if _service_specs_require_experience_context(specs=specs):
        projection_experience_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperience",
        )
        experience_context = await _hydrate_committed_experience_reference_contexts(
            index=index,
            lanes=_resolve_experience_reference_lanes(
                lane=lane,
                projection_hash=projection_experience_projection_hash,
                specs=specs,
                experience_reference_branch_ids_by_experience_name=(
                    experience_reference_branch_ids_by_experience_name
                ),
            ),
            commit_store=(
                FSCommitStore(root_dir=experience_reference_commit_store_root)
                if experience_reference_commit_store_root is not None
                else None
            ),
        )
    role_context: _CommittedRoleReferenceContext | None = None
    if _service_specs_require_role_context(specs=specs):
        role_config_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="RoleConfig",
        )
        role_reference_lane_pairs = _resolve_role_reference_lane_pairs(
            lane=lane,
            projection_hash=role_config_projection_hash,
            specs=specs,
            role_reference_branch_ids_by_role_name=role_reference_branch_ids_by_role_name,
        )
        await _ensure_committed_role_reference_lanes(
            index=index,
            actor_id=actor_id,
            role_reference_lane_pairs=role_reference_lane_pairs,
        )
        role_context = await _hydrate_committed_role_reference_contexts(
            index=index,
            lanes=tuple(lane for _, lane in role_reference_lane_pairs),
        )
    price_context: _CommittedPriceReferenceContext | None = None
    if any(
        operation.price_ref is not None
        for spec in specs
        for operation in spec.service_config.service_operation_configs
    ):
        price_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="Price",
        )
        price_reference_branch_id = _resolve_price_reference_branch_id(
            price_reference_branch_ids_by_package_name=(
                price_reference_branch_ids_by_package_name
            ),
        )
        price_context = await _hydrate_committed_price_reference_context(
            index=index,
            lane=MaterializationLaneContext(
                branch_id=price_reference_branch_id,
                projection_hash=price_projection_hash,
            ),
        )
    plan = build_service_definition_materialization_plan(lane=lane, specs=specs)

    async def _runner(
        *, plan: MaterializationPlan, step: MaterializationStep
    ) -> MaterializationStepResult:
        spec = decode_service_definition_materialization_step_payload(step.payload)
        return await _materialize_service_definition_spec(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            lane=plan.lane,
            api_context=api_context,
            experience_context=experience_context,
            role_context=role_context,
            price_context=price_context,
            spec=spec,
        )

    return await MaterializationExecutor().run(plan=plan, runner=_runner)


def resolve_service_definition_materialization_specs(
    *,
    compile_plan_payloads: Sequence[Mapping[str, object]],
) -> tuple[ServiceDefinitionMaterializationSpec, ...]:
    if not compile_plan_payloads:
        return ()

    specs_by_key: dict[tuple[str, str, str], ServiceDefinitionMaterializationSpec] = {}
    for payload in compile_plan_payloads:
        package_name = _expect_string(
            payload.get("package_name"), field_name="package_name"
        )
        fqn_prefix = (
            _expect_optional_string(payload.get("fqn_prefix"), field_name="fqn_prefix")
            or ""
        )
        raw_service_configs = _expect_list(
            payload.get("service_configs", ()), field_name="service_configs"
        )
        for raw_service_config in raw_service_configs:
            service_config = _decode_service_config_plan(
                _expect_mapping(raw_service_config, field_name="service_configs[]")
            )
            spec = ServiceDefinitionMaterializationSpec(
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                source_path=service_config.source_path,
                service_config=service_config,
            )
            key = (
                spec.package_name.casefold(),
                spec.service_config.name.casefold(),
                spec.source_path,
            )
            existing = specs_by_key.get(key)
            if existing is not None and existing != spec:
                raise RuntimeError(
                    "Invalid Service compile plan: duplicate service config entries disagree "
                    + f"(package_name={package_name!r}, service={service_config.name!r}, "
                    + f"source_path={service_config.source_path!r})"
                )
            specs_by_key[key] = spec

    return tuple(
        sorted(
            specs_by_key.values(),
            key=lambda item: (
                item.package_name.casefold(),
                item.service_config.name.casefold(),
                item.source_path,
            ),
        )
    )


def build_service_definition_materialization_plan(
    *,
    lane: MaterializationLaneContext,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
) -> MaterializationPlan:
    steps = tuple(
        MaterializationStep(
            step_id=f"service:{spec.package_name}:{spec.service_config.name}",
            step_kind="service.definition.ontology",
            payload=encode_service_definition_materialization_step_payload(spec=spec),
            commit_requested=True,
        )
        for spec in specs
    )
    return MaterializationPlan(
        module_id="service",
        pipeline_id="service.compile_plan.ontology",
        lane=lane,
        steps=steps,
    )


def encode_service_definition_materialization_step_payload(
    *,
    spec: ServiceDefinitionMaterializationSpec,
) -> dict[str, object]:
    return {
        "package_name": spec.package_name,
        "fqn_prefix": spec.fqn_prefix,
        "source_path": spec.source_path,
        "service_config": _encode_service_config_plan(spec.service_config),
    }


def decode_service_definition_materialization_step_payload(
    payload: Mapping[str, object],
) -> ServiceDefinitionMaterializationSpec:
    mapping = _expect_mapping(payload, field_name="service_definition_step")
    package_name = _expect_string(
        mapping.get("package_name"), field_name="package_name"
    )
    fqn_prefix = (
        _expect_optional_string(mapping.get("fqn_prefix"), field_name="fqn_prefix")
        or ""
    )
    source_path = _expect_string(mapping.get("source_path"), field_name="source_path")
    service_config = _decode_service_config_plan(
        _expect_mapping(mapping.get("service_config"), field_name="service_config")
    )
    if service_config.source_path != source_path:
        raise RuntimeError(
            "Invalid Service materialization step payload: source_path does not match nested service_config.source_path"
        )
    return ServiceDefinitionMaterializationSpec(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_path=source_path,
        service_config=service_config,
    )


async def _materialize_service_definition_spec(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    api_context: _CommittedAPIReferenceContext,
    experience_context: _CommittedExperienceReferenceContext | None,
    role_context: _CommittedRoleReferenceContext | None,
    price_context: _CommittedPriceReferenceContext | None,
    spec: ServiceDefinitionMaterializationSpec,
) -> MaterializationStepResult:
    del runtime
    service_config_id = stable_service_config_id(name=spec.service_config.name)
    service_config_api_snapshots: list[ServiceDefinitionApiSnapshot] = []
    service_config_api_ids_by_ref: dict[str, UUID] = {}
    service_config_api_ids_by_api_id: dict[UUID, UUID] = {}
    for api_plan in spec.service_config.apis:
        api_id = _resolve_committed_api_id(
            api_context=api_context, api_ref=api_plan.api_ref
        )
        service_config_api_id = stable_service_config_api_id(
            service_config_id=service_config_id,
            api_id=api_id,
        )
        service_config_api_ids_by_ref[api_plan.api_ref] = service_config_api_id
        service_config_api_ids_by_api_id[api_id] = service_config_api_id
        api_graph_projection_ids: list[UUID] = []
        for projection_plan in api_plan.api_projections:
            api_graph_projection_ids.append(
                _resolve_committed_api_graph_projection_id(
                    api_context=api_context,
                    api_ref=api_plan.api_ref,
                    projection_ref=projection_plan.projection_ref,
                )
            )
        service_config_api_snapshots.append(
            ServiceDefinitionApiSnapshot(
                api_id=api_id,
                api_graph_projection_ids=tuple(api_graph_projection_ids),
            )
        )

    service_config_experience_snapshots: list[ServiceDefinitionExperienceSnapshot] = []
    for experience_plan in spec.service_config.experiences:
        if experience_context is None:
            raise RuntimeError(
                "Invalid Service compile plan: service experience binding requires committed projection_experience "
                + f"context (service={spec.service_config.name!r}, "
                + f"experience_ref={experience_plan.experience_ref!r})"
            )
        service_config_experience_snapshots.append(
            ServiceDefinitionExperienceSnapshot(
                projection_experience_id=_resolve_committed_projection_experience_id(
                    experience_context=experience_context,
                    experience_ref=experience_plan.experience_ref,
                )
            )
        )

    service_config_code_package_config_snapshots = tuple(
        ServiceDefinitionCodePackageConfigSnapshot(
            slot_key=plan.slot_key,
            code_package_config_id=plan.code_package_config_id,
            cardinality=plan.cardinality,
            required=plan.required,
        )
        for plan in spec.service_config.code_package_configs
    )

    price_binding_count = 0
    service_operation_config_ids_by_name: dict[str, UUID] = {}
    operation_snapshots: list[ServiceDefinitionOperationSnapshot] = []
    for operation_plan in spec.service_config.service_operation_configs:
        price_id = None
        if operation_plan.price is not None:
            raise RuntimeError(
                "Service clean-rail definition snapshot does not support inline "
                "price materialization yet; price truth must be committed by the "
                "Economy semantic package and referenced by price_ref."
            )
        elif operation_plan.price_ref is not None:
            if price_context is None:
                raise RuntimeError(
                    "Invalid Service compile plan: operation price_ref requires committed price context "
                    + f"(service={spec.service_config.name!r}, operation={operation_plan.name!r})"
                )
            price_id = _resolve_committed_price_id(
                price_context=price_context,
                price_ref=operation_plan.price_ref,
            )
        if price_id is not None:
            price_binding_count += 1
        service_operation_config_id = stable_service_operation_config_id(
            service_config_id=service_config_id,
            name=operation_plan.name,
        )
        service_operation_config_ids_by_name[operation_plan.name.casefold()] = (
            service_operation_config_id
        )

        view_snapshots: list[ServiceDefinitionApiViewSnapshot] = []
        for view_plan in operation_plan.api_views:
            api_view = _resolve_committed_api_view(
                api_context=api_context,
                view_ref=view_plan.view_ref,
            )
            api_view_id = api_view.id
            if api_view_id is None:
                raise RuntimeError(
                    "Committed ApiView is missing id "
                    + f"(service={spec.service_config.name!r}, operation={operation_plan.name!r}, "
                    + f"view_ref={view_plan.view_ref!r})"
                )
            service_config_api_id = service_config_api_ids_by_api_id.get(
                api_view.api_id
            )
            if service_config_api_id is None:
                raise RuntimeError(
                    "Invalid Service compile plan: API view binding references an API that is not "
                    + "declared by this ServiceConfig "
                    + f"(service={spec.service_config.name!r}, operation={operation_plan.name!r}, "
                    + f"view_ref={view_plan.view_ref!r})"
                )
            view_snapshots.append(
                ServiceDefinitionApiViewSnapshot(
                    service_config_api_id=service_config_api_id,
                    api_view_id=api_view_id,
                )
            )

        role_requirement_snapshots: list[ServiceDefinitionRoleRequirementSnapshot] = []
        for role_requirement_plan in operation_plan.role_requirements:
            if role_context is None:
                raise RuntimeError(
                    "Invalid Service compile plan: operation role requirement requires committed "
                    + "role_config context "
                    + f"(service={spec.service_config.name!r}, operation={operation_plan.name!r}, "
                    + f"role_ref={role_requirement_plan.role_ref!r})"
                )
            role_requirement_snapshots.append(
                ServiceDefinitionRoleRequirementSnapshot(
                    role_config_id=_resolve_committed_role_config_id(
                        role_context=role_context,
                        role_ref=role_requirement_plan.role_ref,
                    ),
                    access_scope=role_requirement_plan.access_scope,
                    scope_kind=role_requirement_plan.scope_kind,
                    scope_ref=role_requirement_plan.scope_ref,
                    class_instance_identity_required=(
                        role_requirement_plan.class_instance_identity_required
                    ),
                    role_assignment_binding_required=(
                        role_requirement_plan.role_assignment_binding_required
                    ),
                ),
            )

        endpoint_snapshots: list[ServiceDefinitionEndpointSnapshot] = []
        endpoint_stream_modes: list[str | None] = []
        for endpoint_plan in operation_plan.api_endpoints:
            service_config_api_id = service_config_api_ids_by_ref.get(
                endpoint_plan.api_ref
            )
            if service_config_api_id is None:
                raise RuntimeError(
                    "Invalid Service compile plan: endpoint binding references an unmaterialized service_config_api "
                    + f"(service={spec.service_config.name!r}, api_ref={endpoint_plan.api_ref!r}, "
                    + f"endpoint_ref={endpoint_plan.endpoint_ref!r})"
                )
            api_capability_endpoint = _resolve_committed_api_endpoint(
                api_context=api_context,
                endpoint_ref=endpoint_plan.endpoint_ref,
            )
            api_capability_endpoint_id = api_capability_endpoint.id
            if api_capability_endpoint_id is None:
                raise RuntimeError(
                    "Committed ApiCapabilityEndpoint is missing id for endpoint_ref="
                    + f"{endpoint_plan.endpoint_ref!r}."
                )
            endpoint_stream_modes.append(
                api_context.endpoint_stream_modes_by_endpoint_id.get(
                    api_capability_endpoint_id
                )
            )
            endpoint_function_snapshots: list[
                ServiceDefinitionEndpointFunctionSnapshot
            ] = []
            for (
                api_endpoint_function
            ) in api_context.endpoint_functions_by_endpoint_id.get(
                api_capability_endpoint_id,
                (),
            ):
                api_endpoint_function_id = api_endpoint_function.id
                if api_endpoint_function_id is None:
                    raise RuntimeError(
                        "Committed ApiCapabilityEndpointFunction is missing id for endpoint_ref="
                        + f"{endpoint_plan.endpoint_ref!r}."
                    )
                endpoint_function_snapshots.append(
                    ServiceDefinitionEndpointFunctionSnapshot(
                        api_capability_endpoint_function_id=(api_endpoint_function_id)
                    )
                )

            endpoint_snapshots.append(
                ServiceDefinitionEndpointSnapshot(
                    service_config_api_id=service_config_api_id,
                    api_capability_endpoint_id=api_capability_endpoint_id,
                    endpoint_functions=tuple(endpoint_function_snapshots),
                )
            )
        receipt_policy = _decode_service_operation_receipt_policy(
            operation_plan.receipt_policy,
            field_name=(
                "service_config.service_operation_configs"
                f"[{operation_plan.name}].receipt_policy"
            ),
        )
        planned_fulfillment_kind = _decode_service_operation_fulfillment_kind(
            operation_plan.fulfillment_kind,
            field_name=(
                "service_config.service_operation_configs"
                f"[{operation_plan.name}].fulfillment_kind"
            ),
        )
        fulfillment_kind = _resolve_committed_service_operation_fulfillment_kind(
            service_name=spec.service_config.name,
            operation_name=operation_plan.name,
            planned_kind=planned_fulfillment_kind,
            receipt_policy=receipt_policy,
            endpoint_stream_modes=tuple(endpoint_stream_modes),
            has_api_views=bool(view_snapshots),
        )
        operation_snapshots.append(
            ServiceDefinitionOperationSnapshot(
                name=operation_plan.name,
                price_id=price_id,
                admission_mode=_decode_service_operation_admission_mode(
                    operation_plan.admission_mode,
                    field_name=(
                        "service_config.service_operation_configs"
                        f"[{operation_plan.name}].admission_mode"
                    ),
                ),
                receipt_policy=receipt_policy,
                fulfillment_kind=fulfillment_kind,
                settlement_policy=_decode_service_operation_settlement_policy(
                    operation_plan.settlement_policy,
                    field_name=(
                        "service_config.service_operation_configs"
                        f"[{operation_plan.name}].settlement_policy"
                    ),
                ),
                endpoints=tuple(endpoint_snapshots),
                api_views=tuple(view_snapshots),
                role_requirements=tuple(role_requirement_snapshots),
            )
        )

    contract_snapshots: list[ServiceDefinitionContractSnapshot] = []
    for contract_config_plan in spec.service_config.contract_configs:
        projection_experience_id = None
        if contract_config_plan.projection_experience_ref is not None:
            if experience_context is None:
                raise RuntimeError(
                    "Invalid Service compile plan: contract projection_experience requires committed "
                    + "projection_experience context "
                    + f"(service={spec.service_config.name!r}, contract={contract_config_plan.name!r}, "
                    + f"experience_ref={contract_config_plan.projection_experience_ref!r})"
                )
            projection_experience_id = _resolve_committed_projection_experience_id(
                experience_context=experience_context,
                experience_ref=contract_config_plan.projection_experience_ref,
            )

        operation_grant_snapshots: list[ServiceDefinitionOperationGrantSnapshot] = []
        for operation_grant_plan in contract_config_plan.operation_grants:
            granted_operation_config_id = _resolve_local_service_operation_config_id(
                service_operation_config_ids_by_name=service_operation_config_ids_by_name,
                service_name=spec.service_config.name,
                operation_ref=operation_grant_plan.operation_ref,
            )
            operation_grant_snapshots.append(
                ServiceDefinitionOperationGrantSnapshot(
                    service_operation_config_id=granted_operation_config_id,
                    access_scope=operation_grant_plan.access_scope,
                )
            )

        actor_role_grant_snapshots: list[ServiceDefinitionActorRoleGrantSnapshot] = []
        for actor_role_grant_plan in contract_config_plan.actor_role_grants:
            if role_context is None:
                raise RuntimeError(
                    "Invalid Service compile plan: contract actor_role grant requires committed "
                    + "role_config context "
                    + f"(service={spec.service_config.name!r}, contract={contract_config_plan.name!r}, "
                    + f"role_ref={actor_role_grant_plan.role_ref!r})"
                )
            role_config_id = _resolve_committed_role_config_id(
                role_context=role_context,
                role_ref=actor_role_grant_plan.role_ref,
            )
            actor_role_grant_snapshots.append(
                ServiceDefinitionActorRoleGrantSnapshot(
                    role_config_id=role_config_id,
                    scope_kind=actor_role_grant_plan.scope_kind,
                    scope_ref=actor_role_grant_plan.scope_ref,
                    access_scope=actor_role_grant_plan.access_scope,
                    class_instance_identity_required=(
                        actor_role_grant_plan.class_instance_identity_required
                    ),
                    role_assignment_binding_required=(
                        actor_role_grant_plan.role_assignment_binding_required
                    ),
                )
            )
        contract_snapshots.append(
            ServiceDefinitionContractSnapshot(
                name=contract_config_plan.name,
                default_kind=_decode_service_contract_kind(
                    contract_config_plan.default_kind,
                    field_name=(
                        "service_config.contract_configs"
                        f"[{contract_config_plan.name}].default_kind"
                    ),
                ),
                projection_experience_id=projection_experience_id,
                operation_grants=tuple(operation_grant_snapshots),
                actor_role_grants=tuple(actor_role_grant_snapshots),
            )
        )

    snapshot_commit = await commit_service_config_definition_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        name=spec.service_config.name,
        apis=tuple(service_config_api_snapshots),
        experiences=tuple(service_config_experience_snapshots),
        code_package_configs=service_config_code_package_config_snapshots,
        operations=tuple(operation_snapshots),
        contract_configs=tuple(contract_snapshots),
    )

    service_config_api_projection_count = sum(
        len(item.api_graph_projection_ids) for item in service_config_api_snapshots
    )
    endpoint_binding_count = sum(
        len(operation.endpoints) for operation in operation_snapshots
    )
    endpoint_function_binding_count = sum(
        len(endpoint.endpoint_functions)
        for operation in operation_snapshots
        for endpoint in operation.endpoints
    )
    operation_api_view_binding_count = sum(
        len(operation.api_views) for operation in operation_snapshots
    )
    operation_role_requirement_binding_count = sum(
        len(operation.role_requirements) for operation in operation_snapshots
    )
    contract_config_operation_grant_count = sum(
        len(contract.operation_grants) for contract in contract_snapshots
    )
    contract_config_actor_role_grant_count = sum(
        len(contract.actor_role_grants) for contract in contract_snapshots
    )

    return MaterializationStepResult(
        details={
            "package_name": spec.package_name,
            "service_name": spec.service_config.name,
            "source_path": spec.source_path,
            "service_config_id": str(service_config_id),
            "service_config_api_count": len(spec.service_config.apis),
            "service_config_api_projection_count": service_config_api_projection_count,
            "service_config_experience_count": len(service_config_experience_snapshots),
            "service_config_code_package_config_count": len(
                service_config_code_package_config_snapshots
            ),
            "service_operation_config_count": len(
                spec.service_config.service_operation_configs
            ),
            "service_operation_price_binding_count": price_binding_count,
            "service_operation_api_view_binding_count": operation_api_view_binding_count,
            "service_operation_role_requirement_binding_count": (
                operation_role_requirement_binding_count
            ),
            "service_operation_endpoint_binding_count": endpoint_binding_count,
            "service_operation_endpoint_function_binding_count": (
                endpoint_function_binding_count
            ),
            "service_contract_config_count": len(contract_snapshots),
            "service_contract_config_operation_grant_count": (
                contract_config_operation_grant_count
            ),
            "service_contract_config_actor_role_grant_count": (
                contract_config_actor_role_grant_count
            ),
        },
        commit_id=snapshot_commit.commit_id,
        head_commit_id=snapshot_commit.head_commit_id,
    )


async def _hydrate_committed_api_reference_context(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    commit_store: FSCommitStore | None = None,
) -> _CommittedAPIReferenceContext:
    session = await _hydrate_committed_lane_session(
        index=index,
        lane=lane,
        error_context="API ref resolution",
        commit_store=commit_store,
    )
    accessible_projection_tokens_by_id = _accessible_projection_lookup_tokens_by_id(
        accessible_graphs
    )

    apis_by_name: dict[str, Api] = {}
    graphs_by_api_id: dict[UUID, list[ApiGraph]] = {}
    graph_projections_by_key: dict[tuple[UUID, str], ApiGraphProjection] = {}
    capabilities_by_key: dict[tuple[UUID, str], ApiCapability] = {}
    endpoints_by_key: dict[tuple[UUID, str], ApiCapabilityEndpoint] = {}
    api_views_by_ref: dict[str, ApiView] = {}
    api_views_by_api_id_and_name: dict[tuple[UUID, str], ApiView] = {}
    endpoint_functions_by_endpoint_id: dict[
        UUID, list[ApiCapabilityEndpointFunction]
    ] = {}
    request_configs_by_endpoint_id: dict[UUID, ApiCapabilityEndpointRequestConfig] = {}
    stream_configs_by_request_config_id: dict[
        UUID, ApiCapabilityEndpointStreamConfig
    ] = {}
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
            _insert_committed_api_endpoint_refs(
                endpoints_by_key=endpoints_by_key,
                endpoint=obj,
            )
        elif isinstance(obj, ApiCapabilityEndpointRequestConfig):
            if obj.id is None:
                continue
            request_configs_by_endpoint_id[obj.api_capability_endpoint_id] = obj
        elif isinstance(obj, ApiCapabilityEndpointStreamConfig):
            request_config_id = obj.api_capability_endpoint_request_config_id
            if obj.id is None or request_config_id is None:
                continue
            stream_configs_by_request_config_id[request_config_id] = obj
        elif isinstance(obj, ApiView):
            _insert_committed_api_view_refs(
                api_views_by_ref=api_views_by_ref,
                api_views_by_api_id_and_name=api_views_by_api_id_and_name,
                api_view=obj,
            )
        elif isinstance(obj, ApiCapabilityEndpointFunction):
            if obj.id is None:
                continue
            endpoint_functions_by_endpoint_id.setdefault(
                obj.api_capability_endpoint_id,
                [],
            ).append(obj)
        elif isinstance(obj, ApiGraph):
            if obj.id is None:
                continue
            graphs_by_api_id.setdefault(obj.api_id, []).append(obj)
        elif isinstance(obj, ApiGraphProjection):
            projection_id = obj.id
            api_graph_id = getattr(obj, "api_graph_id", None)
            object_projection_graph = getattr(obj, "ObjectProjectionGraph", None)
            object_projection_graph_id = getattr(
                obj,
                "object_projection_graph_id",
                None,
            )
            if projection_id is None or api_graph_id is None:
                continue
            projection_name = (
                getattr(object_projection_graph, "name", None)
                if object_projection_graph is not None
                else None
            )
            if projection_name is None and object_projection_graph_id is not None:
                indexed_projection = index.opg_by_id.get(object_projection_graph_id)
                if indexed_projection is not None:
                    projection_name = indexed_projection.name
            tokens = list(_projection_lookup_tokens(projection_name or ""))
            if object_projection_graph_id is not None:
                tokens.extend(
                    accessible_projection_tokens_by_id.get(
                        UUID(str(object_projection_graph_id)),
                        (),
                    )
                )
            for token in tuple(dict.fromkeys(tokens)):
                _insert_unique_ref(
                    refs=graph_projections_by_key,
                    key=(api_graph_id, token),
                    value=obj,
                    error_context=(
                        "duplicate committed ApiGraphProjection lookup token "
                        + f"{token!r} for api_graph_id={api_graph_id}"
                    ),
                )

    for capability in capabilities_by_key.values():
        capability_id = capability.id
        if capability_id is None:
            continue
        for endpoint in capability.api_capability_endpoints or ():
            if not isinstance(endpoint, ApiCapabilityEndpoint):
                continue
            _insert_committed_api_endpoint_refs(
                endpoints_by_key=endpoints_by_key,
                endpoint=endpoint,
                parent_api_capability_id=capability_id,
            )

    endpoint_stream_modes_by_endpoint_id: dict[UUID, str] = {}
    for endpoint_id, request_config in request_configs_by_endpoint_id.items():
        stream_config = request_config.stream_config
        if stream_config is None and request_config.id is not None:
            stream_config = stream_configs_by_request_config_id.get(request_config.id)
        if stream_config is None:
            continue
        raw_stream_mode = getattr(
            stream_config.stream_mode,
            "value",
            stream_config.stream_mode,
        )
        stream_mode = str(raw_stream_mode or "").strip().casefold()
        if stream_mode not in {"server", "client", "bidirectional"}:
            raise RuntimeError(
                "Committed ApiCapabilityEndpoint has unsupported stream mode "
                + f"for endpoint_id={endpoint_id}: {raw_stream_mode!r}."
            )
        endpoint_stream_modes_by_endpoint_id[endpoint_id] = stream_mode

    return _CommittedAPIReferenceContext(
        lane=lane,
        apis_by_name=apis_by_name,
        graphs_by_api_id={
            api_id: tuple(graphs) for api_id, graphs in graphs_by_api_id.items()
        },
        graph_projections_by_key=graph_projections_by_key,
        capabilities_by_key=capabilities_by_key,
        endpoints_by_key=endpoints_by_key,
        api_views_by_ref=api_views_by_ref,
        api_views_by_api_id_and_name=api_views_by_api_id_and_name,
        endpoint_functions_by_endpoint_id={
            endpoint_id: tuple(
                sorted(
                    functions,
                    key=lambda item: (
                        (item.name or "").casefold().strip(),
                        str(item.id),
                    ),
                )
            )
            for endpoint_id, functions in endpoint_functions_by_endpoint_id.items()
        },
        endpoint_stream_modes_by_endpoint_id=endpoint_stream_modes_by_endpoint_id,
    )


def _insert_committed_api_endpoint_refs(
    *,
    endpoints_by_key: dict[tuple[UUID, str], ApiCapabilityEndpoint],
    endpoint: ApiCapabilityEndpoint,
    parent_api_capability_id: UUID | None = None,
) -> None:
    endpoint_name = (endpoint.name or "").casefold().strip()
    if not endpoint_name:
        return
    capability_ids: list[UUID] = []
    endpoint_capability_id = getattr(endpoint, "api_capability_id", None)
    if endpoint_capability_id is not None:
        capability_ids.append(UUID(str(endpoint_capability_id)))
    if parent_api_capability_id is not None:
        parent_id = UUID(str(parent_api_capability_id))
        if parent_id not in capability_ids:
            capability_ids.append(parent_id)
    for capability_id in capability_ids:
        _insert_unique_ref(
            refs=endpoints_by_key,
            key=(capability_id, endpoint_name),
            value=endpoint,
            error_context=(
                f"duplicate committed ApiCapabilityEndpoint name {endpoint.name!r}"
            ),
        )


def _insert_committed_api_view_refs(
    *,
    api_views_by_ref: dict[str, ApiView],
    api_views_by_api_id_and_name: dict[tuple[UUID, str], ApiView],
    api_view: ApiView,
) -> None:
    if api_view.id is None:
        return
    view_ref = (api_view.view_ref or "").casefold().strip()
    if view_ref:
        _insert_unique_ref(
            refs=api_views_by_ref,
            key=view_ref,
            value=api_view,
            error_context=f"duplicate committed ApiView view_ref {api_view.view_ref!r}",
        )
    view_name = (api_view.name or "").casefold().strip()
    if view_name:
        _insert_unique_ref(
            refs=api_views_by_api_id_and_name,
            key=(api_view.api_id, view_name),
            value=api_view,
            error_context=f"duplicate committed ApiView name {api_view.name!r}",
        )


async def _hydrate_committed_api_reference_contexts(
    *,
    index: MetaGraphRuntimeIndex,
    lanes: Sequence[MaterializationLaneContext],
    accessible_graphs: Sequence[ObjectConfigGraph] = (),
    commit_store: FSCommitStore | None = None,
) -> _CommittedAPIReferenceContext:
    if not lanes:
        raise RuntimeError(
            "API ref resolution requires at least one committed API reference lane."
        )

    merged_apis_by_name: dict[str, Api] = {}
    merged_graphs_by_api_id: dict[UUID, list[ApiGraph]] = {}
    merged_graph_projections_by_key: dict[tuple[UUID, str], ApiGraphProjection] = {}
    merged_capabilities_by_key: dict[tuple[UUID, str], ApiCapability] = {}
    merged_endpoints_by_key: dict[tuple[UUID, str], ApiCapabilityEndpoint] = {}
    merged_api_views_by_ref: dict[str, ApiView] = {}
    merged_api_views_by_api_id_and_name: dict[tuple[UUID, str], ApiView] = {}
    merged_endpoint_functions_by_endpoint_id: dict[
        UUID, list[ApiCapabilityEndpointFunction]
    ] = {}
    merged_endpoint_stream_modes_by_endpoint_id: dict[UUID, str] = {}
    seen_lane_keys: set[tuple[UUID, str]] = set()
    representative_lane = lanes[0]

    for lane in lanes:
        lane_key = (lane.branch_id, lane.projection_hash)
        if lane_key in seen_lane_keys:
            continue
        seen_lane_keys.add(lane_key)

        lane_context = await _hydrate_committed_api_reference_context(
            index=index,
            lane=lane,
            accessible_graphs=accessible_graphs,
            commit_store=commit_store,
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
        for key, value in lane_context.api_views_by_ref.items():
            _insert_unique_ref(
                refs=merged_api_views_by_ref,
                key=key,
                value=value,
                error_context=f"duplicate committed ApiView view_ref {value.view_ref!r}",
            )
        for key, value in lane_context.api_views_by_api_id_and_name.items():
            _insert_unique_ref(
                refs=merged_api_views_by_api_id_and_name,
                key=key,
                value=value,
                error_context=f"duplicate committed ApiView name {value.name!r}",
            )
        for (
            endpoint_id,
            functions,
        ) in lane_context.endpoint_functions_by_endpoint_id.items():
            bucket = merged_endpoint_functions_by_endpoint_id.setdefault(
                endpoint_id, []
            )
            for endpoint_function in functions:
                if any(existing.id == endpoint_function.id for existing in bucket):
                    continue
                bucket.append(endpoint_function)
        for (
            endpoint_id,
            stream_mode,
        ) in lane_context.endpoint_stream_modes_by_endpoint_id.items():
            existing_stream_mode = merged_endpoint_stream_modes_by_endpoint_id.get(
                endpoint_id
            )
            if existing_stream_mode is not None and existing_stream_mode != stream_mode:
                raise RuntimeError(
                    "Conflicting committed ApiCapabilityEndpoint stream modes "
                    + f"for endpoint_id={endpoint_id}: "
                    + f"{existing_stream_mode!r} != {stream_mode!r}."
                )
            merged_endpoint_stream_modes_by_endpoint_id[endpoint_id] = stream_mode
        for api_id, graphs in lane_context.graphs_by_api_id.items():
            bucket = merged_graphs_by_api_id.setdefault(api_id, [])
            for graph in graphs:
                if any(existing.id == graph.id for existing in bucket):
                    continue
                bucket.append(graph)
        for key, value in lane_context.graph_projections_by_key.items():
            _insert_unique_ref(
                refs=merged_graph_projections_by_key,
                key=key,
                value=value,
                error_context=(
                    "duplicate committed ApiGraphProjection lookup token "
                    + f"{key[1]!r} for api_graph_id={key[0]}"
                ),
            )

    return _CommittedAPIReferenceContext(
        lane=representative_lane,
        apis_by_name=merged_apis_by_name,
        graphs_by_api_id={
            api_id: tuple(graphs) for api_id, graphs in merged_graphs_by_api_id.items()
        },
        graph_projections_by_key=merged_graph_projections_by_key,
        capabilities_by_key=merged_capabilities_by_key,
        endpoints_by_key=merged_endpoints_by_key,
        api_views_by_ref=merged_api_views_by_ref,
        api_views_by_api_id_and_name=merged_api_views_by_api_id_and_name,
        endpoint_functions_by_endpoint_id={
            endpoint_id: tuple(
                sorted(
                    functions,
                    key=lambda item: (
                        (item.name or "").casefold().strip(),
                        str(item.id),
                    ),
                )
            )
            for endpoint_id, functions in merged_endpoint_functions_by_endpoint_id.items()
        },
        endpoint_stream_modes_by_endpoint_id=(
            merged_endpoint_stream_modes_by_endpoint_id
        ),
    )


async def _hydrate_committed_experience_reference_context(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    commit_store: FSCommitStore | None = None,
) -> _CommittedExperienceReferenceContext:
    session = await _hydrate_committed_lane_session(
        index=index,
        lane=lane,
        error_context="ProjectionExperience ref resolution",
        commit_store=commit_store,
    )
    experiences_by_name: dict[str, ProjectionExperience] = {}

    for obj in session.imap_all_objects():
        if isinstance(obj, ProjectionExperience):
            if obj.id is None:
                continue
            name = (obj.name or "").strip()
            if not name:
                continue
            _insert_unique_ref(
                refs=experiences_by_name,
                key=name.casefold(),
                value=obj,
                error_context=f"duplicate committed ProjectionExperience name {name!r}",
            )

    return _CommittedExperienceReferenceContext(
        lane=lane,
        experiences_by_name=experiences_by_name,
    )


async def _hydrate_committed_experience_reference_contexts(
    *,
    index: MetaGraphRuntimeIndex,
    lanes: Sequence[MaterializationLaneContext],
    commit_store: FSCommitStore | None = None,
) -> _CommittedExperienceReferenceContext:
    if not lanes:
        raise RuntimeError(
            "ProjectionExperience ref resolution requires at least one committed experience reference lane."
        )

    merged_experiences_by_name: dict[str, ProjectionExperience] = {}
    seen_lane_keys: set[tuple[UUID, str]] = set()
    representative_lane = lanes[0]

    for lane in lanes:
        lane_key = (lane.branch_id, lane.projection_hash)
        if lane_key in seen_lane_keys:
            continue
        seen_lane_keys.add(lane_key)

        lane_context = await _hydrate_committed_experience_reference_context(
            index=index,
            lane=lane,
            commit_store=commit_store,
        )
        for key, value in lane_context.experiences_by_name.items():
            _insert_unique_ref(
                refs=merged_experiences_by_name,
                key=key,
                value=value,
                error_context=f"duplicate committed ProjectionExperience name {value.name!r}",
            )

    return _CommittedExperienceReferenceContext(
        lane=representative_lane,
        experiences_by_name=merged_experiences_by_name,
    )


async def _hydrate_committed_role_reference_context(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
) -> _CommittedRoleReferenceContext:
    from aware_identity_ontology.role.role_config import RoleConfig

    session = await _hydrate_committed_lane_session(
        index=index,
        lane=lane,
        error_context="RoleConfig ref resolution",
    )
    role_configs_by_name: dict[str, RoleConfig] = {}

    for obj in session.imap_all_objects():
        if not _is_committed_role_config_object(
            obj,
            role_config_type=RoleConfig,
        ):
            continue
        role_config = cast(RoleConfig, obj)
        if role_config.id is None:
            continue
        name = (role_config.name or "").strip()
        if not name:
            continue
        _insert_unique_ref(
            refs=role_configs_by_name,
            key=name.casefold(),
            value=role_config,
            error_context=f"duplicate committed RoleConfig name {name!r}",
        )

    return _CommittedRoleReferenceContext(
        lane=lane,
        role_configs_by_name=role_configs_by_name,
    )


def _is_committed_role_config_object(
    obj: object,
    *,
    role_config_type: type[object],
) -> bool:
    if isinstance(obj, role_config_type):
        return True
    obj_type = obj.__class__
    return (
        obj_type.__name__ == "RoleConfig"
        and obj_type.__module__.endswith(".role.role_config")
        and isinstance(getattr(obj, "id", None), UUID)
        and isinstance(getattr(obj, "name", None), str)
    )


async def _hydrate_committed_role_reference_contexts(
    *,
    index: MetaGraphRuntimeIndex,
    lanes: Sequence[MaterializationLaneContext],
) -> _CommittedRoleReferenceContext:
    if not lanes:
        raise RuntimeError(
            "RoleConfig ref resolution requires at least one committed role_config reference lane."
        )

    merged_role_configs_by_name: dict[str, RoleConfig] = {}
    seen_lane_keys: set[tuple[UUID, str]] = set()
    representative_lane = lanes[0]

    for lane in lanes:
        lane_key = (lane.branch_id, lane.projection_hash)
        if lane_key in seen_lane_keys:
            continue
        seen_lane_keys.add(lane_key)

        lane_context = await _hydrate_committed_role_reference_context(
            index=index,
            lane=lane,
        )
        for key, value in lane_context.role_configs_by_name.items():
            _insert_unique_ref(
                refs=merged_role_configs_by_name,
                key=key,
                value=value,
                error_context=f"duplicate committed RoleConfig name {value.name!r}",
            )

    return _CommittedRoleReferenceContext(
        lane=representative_lane,
        role_configs_by_name=merged_role_configs_by_name,
    )


async def _ensure_committed_role_reference_lanes(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    role_reference_lane_pairs: Sequence[tuple[str, MaterializationLaneContext]],
) -> None:
    if not role_reference_lane_pairs:
        return

    refs_by_lane_key: dict[
        tuple[UUID, str], tuple[MaterializationLaneContext, set[str]]
    ] = {}
    for role_ref, lane in role_reference_lane_pairs:
        normalized_ref = (role_ref or "").casefold().strip()
        if not normalized_ref:
            continue
        lane_key = (lane.branch_id, lane.projection_hash)
        lane_entry = refs_by_lane_key.get(lane_key)
        if lane_entry is None:
            lane_entry = (lane, set())
            refs_by_lane_key[lane_key] = lane_entry
        lane_entry[1].add(normalized_ref)

    for lane, role_refs in refs_by_lane_key.values():
        existing_context: _CommittedRoleReferenceContext | None = None
        if await _committed_lane_has_head(lane=lane):
            existing_context = await _hydrate_committed_role_reference_context(
                index=index,
                lane=lane,
            )
        missing_role_refs = tuple(
            sorted(
                role_ref
                for role_ref in role_refs
                if existing_context is None
                or not _role_context_resolves_ref(
                    role_context=existing_context,
                    role_ref=role_ref,
                )
            )
        )
        if not missing_role_refs:
            continue
        await _commit_role_config_reference_roots(
            index=index,
            actor_id=actor_id,
            lane=lane,
            role_refs=missing_role_refs,
        )


async def _committed_lane_has_head(*, lane: MaterializationLaneContext) -> bool:
    target_head = await FSCommitStore().head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    return target_head is not None and bool(target_head.get("commit_id"))


def _role_context_resolves_ref(
    *,
    role_context: _CommittedRoleReferenceContext,
    role_ref: str,
) -> bool:
    try:
        _ = _resolve_committed_role_config_id(
            role_context=role_context,
            role_ref=role_ref,
        )
    except RuntimeError as exc:
        if "could not resolve committed RoleConfig" in str(exc):
            return False
        raise
    return True


async def _commit_role_config_reference_roots(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    role_refs: Sequence[str],
) -> None:
    _ = await commit_role_config_reference_snapshot(
        index=index,
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
        actor_id=actor_id,
        role_refs=role_refs,
    )


async def _hydrate_committed_price_reference_context(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
) -> _CommittedPriceReferenceContext:
    from aware_economy_ontology.price.price import Price

    session = await _hydrate_committed_lane_session(
        index=index, lane=lane, error_context="Price ref resolution"
    )
    price_ids_by_name: dict[str, UUID] = {}

    for obj in session.imap_all_objects():
        if not isinstance(obj, Price) or obj.id is None:
            continue
        name = (obj.name or "").strip()
        if not name:
            continue
        _insert_unique_ref(
            refs=price_ids_by_name,
            key=name.casefold(),
            value=obj.id,
            error_context=f"duplicate committed Price name {name!r}",
        )

    return _CommittedPriceReferenceContext(
        lane=lane,
        price_ids_by_name=price_ids_by_name,
    )


def _resolve_price_reference_branch_id(
    *,
    price_reference_branch_ids_by_package_name: Mapping[str, UUID] | None,
) -> UUID:
    branches = {
        branch_id
        for package_name, branch_id in (
            price_reference_branch_ids_by_package_name or {}
        ).items()
        if package_name.strip()
    }
    if not branches:
        raise RuntimeError(
            "Service price_ref requires one committed Economy semantic-package dependency branch."
        )
    if len(branches) != 1:
        raise RuntimeError(
            "Service price_ref Economy semantic-package authority is ambiguous: "
            f"branches={sorted(str(item) for item in branches)!r}"
        )
    return next(iter(branches))


async def _hydrate_committed_lane_session(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    error_context: str,
    commit_store: FSCommitStore | None = None,
) -> Session:
    store = commit_store or FSCommitStore()
    target_head = await store.head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(f"{error_context} requires a committed lane head.")

    opg = index.opg_by_hash.get(lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} could not resolve projection hash {lane.projection_hash!r}."
        )

    target_oig, _ = await CachedLaneMaterializer(commits=store).get(
        branch_id=lane.branch_id,
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
        branch_id=lane.branch_id,
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
            "Service compile-plan materialization could not resolve committed Api "
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
    endpoint = _resolve_committed_api_endpoint(
        api_context=api_context,
        endpoint_ref=endpoint_ref,
    )
    endpoint_id = endpoint.id
    if endpoint_id is None:
        raise RuntimeError(
            f"Committed ApiCapabilityEndpoint is missing id for endpoint_ref={endpoint_ref!r}."
        )
    return endpoint_id


def _resolve_committed_api_endpoint(
    *,
    api_context: _CommittedAPIReferenceContext,
    endpoint_ref: str,
) -> ApiCapabilityEndpoint:
    api_name, capability_name, endpoint_name = _split_endpoint_ref(
        endpoint_ref=endpoint_ref
    )
    api_id = _resolve_committed_api_id(api_context=api_context, api_ref=api_name)
    capability = api_context.capabilities_by_key.get(
        (api_id, capability_name.casefold().strip())
    )
    if capability is None:
        raise RuntimeError(
            "Service compile-plan materialization could not resolve committed ApiCapability "
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
            "Service compile-plan materialization could not resolve committed ApiCapabilityEndpoint "
            + f"for endpoint_ref={endpoint_ref!r}."
        )
    return endpoint


def _resolve_committed_api_view(
    *,
    api_context: _CommittedAPIReferenceContext,
    view_ref: str,
) -> ApiView:
    view = api_context.api_views_by_ref.get(view_ref.casefold().strip())
    if view is None:
        raise RuntimeError(
            "Service compile-plan materialization could not resolve committed ApiView "
            + f"for view_ref={view_ref!r}."
        )
    return view


def _resolve_committed_api_graph_projection_id(
    *,
    api_context: _CommittedAPIReferenceContext,
    api_ref: str,
    projection_ref: str,
) -> UUID:
    api_id = _resolve_committed_api_id(api_context=api_context, api_ref=api_ref)
    graphs = api_context.graphs_by_api_id.get(api_id, ())
    if not graphs:
        raise RuntimeError(
            "Service compile-plan materialization could not resolve committed ApiGraph "
            + f"for api_ref={api_ref!r} while binding projection_ref={projection_ref!r}."
        )

    matches: list[ApiGraphProjection] = []
    for graph in graphs:
        graph_id = graph.id
        if graph_id is None:
            continue
        for token in _projection_lookup_tokens(projection_ref):
            projection = api_context.graph_projections_by_key.get((graph_id, token))
            if projection is not None and projection not in matches:
                matches.append(projection)

    if len(matches) != 1:
        raise RuntimeError(
            "Service compile-plan materialization could not resolve one committed ApiGraphProjection "
            + f"for api_ref={api_ref!r} projection_ref={projection_ref!r} matches="
            + f"{[projection.id for projection in matches]!r}."
        )
    projection_id = matches[0].id
    if projection_id is None:
        raise RuntimeError(
            f"Committed ApiGraphProjection is missing id for api_ref={api_ref!r} projection_ref={projection_ref!r}."
        )
    return projection_id


def _resolve_committed_projection_experience_id(
    *,
    experience_context: _CommittedExperienceReferenceContext,
    experience_ref: str,
) -> UUID:
    experience = experience_context.experiences_by_name.get(
        (experience_ref or "").casefold().strip()
    )
    if experience is None:
        raise RuntimeError(
            "Service compile-plan materialization could not resolve committed ProjectionExperience "
            + f"for experience_ref={experience_ref!r}."
        )
    experience_id = experience.id
    if experience_id is None:
        raise RuntimeError(
            f"Committed ProjectionExperience is missing id for experience_ref={experience_ref!r}."
        )
    return experience_id


def _resolve_committed_role_config_id(
    *,
    role_context: _CommittedRoleReferenceContext,
    role_ref: str,
) -> UUID:
    normalized_ref = (role_ref or "").casefold().strip()
    role_config = role_context.role_configs_by_name.get(normalized_ref)
    if role_config is None:
        suffix = normalized_ref.split(".")[-1]
        matches = [
            candidate
            for key, candidate in role_context.role_configs_by_name.items()
            if key == suffix or key.endswith("." + suffix)
        ]
        if len(matches) == 1:
            role_config = matches[0]
        elif len(matches) > 1:
            raise RuntimeError(
                "Service compile-plan materialization found ambiguous committed RoleConfig "
                + f"matches for role_ref={role_ref!r}."
            )
    if role_config is None:
        raise RuntimeError(
            "Service compile-plan materialization could not resolve committed RoleConfig "
            + f"for role_ref={role_ref!r}."
        )
    role_config_id = role_config.id
    if role_config_id is None:
        raise RuntimeError(
            f"Committed RoleConfig is missing id for role_ref={role_ref!r}."
        )
    return role_config_id


def _resolve_local_service_operation_config_id(
    *,
    service_operation_config_ids_by_name: Mapping[str, UUID],
    service_name: str,
    operation_ref: str,
) -> UUID:
    normalized_ref = (operation_ref or "").casefold().strip()
    tokens = [normalized_ref]
    suffix = normalized_ref.split(".")[-1]
    if suffix and suffix not in tokens:
        tokens.append(suffix)
    for token in tokens:
        operation_config_id = service_operation_config_ids_by_name.get(token)
        if operation_config_id is not None:
            return operation_config_id
    raise RuntimeError(
        "Service compile-plan materialization could not resolve local ServiceOperationConfig "
        + f"for service={service_name!r} operation_ref={operation_ref!r}."
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


def stable_service_role_reference_branch_id(
    *,
    role_ref: str,
) -> UUID:
    normalized_ref = (role_ref or "").casefold().strip()
    if not normalized_ref:
        raise RuntimeError("RoleConfig reference lane requires non-empty role_ref.")
    return _stable_service_materialization_branch_id(
        namespace="role-config-reference",
        value=normalized_ref,
    )


def _projection_lookup_tokens(projection_ref: str) -> tuple[str, ...]:
    raw = (projection_ref or "").strip()
    if not raw:
        return ()
    tail = raw.rsplit(".", 1)[-1]
    return tuple(dict.fromkeys((raw, tail)))


def _accessible_projection_lookup_tokens_by_id(
    accessible_graphs: Sequence[ObjectConfigGraph],
) -> dict[UUID, tuple[str, ...]]:
    tokens_by_id: dict[UUID, tuple[str, ...]] = {}
    for graph in accessible_graphs:
        graph_tokens = tuple(
            token.strip()
            for token in (
                getattr(graph, "fqn_prefix", None),
                getattr(graph, "name", None),
            )
            if isinstance(token, str) and token.strip()
        )
        for opg in getattr(graph, "object_projection_graphs", None) or ():
            opg_id = getattr(opg, "id", None)
            opg_name = (getattr(opg, "name", None) or "").strip()
            if opg_id is None or not opg_name:
                continue
            projection_tokens: list[str] = list(_projection_lookup_tokens(opg_name))
            for graph_token in graph_tokens:
                projection_tokens.extend(
                    _projection_lookup_tokens(f"{graph_token}.{opg_name}")
                )
            tokens_by_id[UUID(str(opg_id))] = tuple(
                dict.fromkeys(token for token in projection_tokens if token)
            )
    return tokens_by_id


def _resolve_api_reference_lanes(
    *,
    lane: MaterializationLaneContext,
    projection_hash: str,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None,
) -> tuple[MaterializationLaneContext, ...]:
    api_refs = tuple(
        sorted(
            {
                api_plan.api_ref.strip()
                for spec in specs
                for api_plan in spec.service_config.apis
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


def _resolve_experience_reference_lanes(
    *,
    lane: MaterializationLaneContext,
    projection_hash: str,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID] | None,
) -> tuple[MaterializationLaneContext, ...]:
    experience_refs = tuple(sorted(_service_spec_experience_refs(specs=specs)))
    if not experience_refs:
        return (_build_peer_lane(lane=lane, projection_hash=projection_hash),)

    normalized_branch_ids_by_experience_name = (
        {
            name.casefold().strip(): branch_id
            for name, branch_id in experience_reference_branch_ids_by_experience_name.items()
            if name.strip()
        }
        if experience_reference_branch_ids_by_experience_name is not None
        else None
    )

    return tuple(
        _build_peer_lane(
            lane=lane,
            projection_hash=projection_hash,
            branch_id=(
                _resolve_reference_branch_id(
                    reference=experience_ref,
                    branch_ids_by_ref=normalized_branch_ids_by_experience_name,
                )
                if normalized_branch_ids_by_experience_name is not None
                else None
            ),
        )
        for experience_ref in experience_refs
    )


def _resolve_role_reference_lanes(
    *,
    lane: MaterializationLaneContext,
    projection_hash: str,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None,
) -> tuple[MaterializationLaneContext, ...]:
    role_reference_lane_pairs = _resolve_role_reference_lane_pairs(
        lane=lane,
        projection_hash=projection_hash,
        specs=specs,
        role_reference_branch_ids_by_role_name=role_reference_branch_ids_by_role_name,
    )
    if not role_reference_lane_pairs:
        return (_build_peer_lane(lane=lane, projection_hash=projection_hash),)
    return tuple(lane for _, lane in role_reference_lane_pairs)


def _resolve_role_reference_lane_pairs(
    *,
    lane: MaterializationLaneContext,
    projection_hash: str,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None,
) -> tuple[tuple[str, MaterializationLaneContext], ...]:
    role_refs = tuple(sorted(_service_spec_role_refs(specs=specs)))
    if not role_refs:
        return ()

    normalized_branch_ids_by_role_name = (
        {
            name.casefold().strip(): branch_id
            for name, branch_id in role_reference_branch_ids_by_role_name.items()
            if name.strip()
        }
        if role_reference_branch_ids_by_role_name is not None
        else None
    )

    return tuple(
        (
            role_ref,
            _build_peer_lane(
                lane=lane,
                projection_hash=projection_hash,
                branch_id=(
                    (
                        _resolve_reference_branch_id(
                            reference=role_ref,
                            branch_ids_by_ref=normalized_branch_ids_by_role_name,
                        )
                        if normalized_branch_ids_by_role_name is not None
                        else None
                    )
                    or stable_service_role_reference_branch_id(
                        role_ref=role_ref,
                    )
                ),
            ),
        )
        for role_ref in role_refs
    )


def _resolve_reference_branch_id(
    *,
    reference: str,
    branch_ids_by_ref: Mapping[str, UUID],
) -> UUID | None:
    normalized_ref = reference.casefold().strip()
    if normalized_ref in branch_ids_by_ref:
        return branch_ids_by_ref[normalized_ref]
    suffix = normalized_ref.split(".")[-1]
    return branch_ids_by_ref.get(suffix)


def _service_specs_require_experience_context(
    *,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
) -> bool:
    return bool(_service_spec_experience_refs(specs=specs))


def _service_specs_require_role_context(
    *,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
) -> bool:
    return bool(_service_spec_role_refs(specs=specs))


def _service_spec_experience_refs(
    *,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
) -> set[str]:
    refs: set[str] = set()
    for spec in specs:
        service_config_experience_refs = _service_config_experience_refs(
            service_config=spec.service_config,
        )
        refs.update(service_config_experience_refs)
        for contract_config_plan in spec.service_config.contract_configs:
            if contract_config_plan.projection_experience_ref is not None:
                experience_ref = contract_config_plan.projection_experience_ref.strip()
                if experience_ref:
                    refs.add(experience_ref)
    return refs


def _service_config_experience_refs(
    *,
    service_config: ServiceConfigPlan,
) -> tuple[str, ...]:
    refs = {
        experience_plan.experience_ref.strip()
        for experience_plan in service_config.experiences
        if experience_plan.experience_ref.strip()
    }
    refs.update(
        contract_config.projection_experience_ref.strip()
        for contract_config in service_config.contract_configs
        if contract_config.projection_experience_ref is not None
        and contract_config.projection_experience_ref.strip()
    )
    return tuple(sorted(refs))


def _service_spec_role_refs(
    *,
    specs: Sequence[ServiceDefinitionMaterializationSpec],
) -> set[str]:
    refs: set[str] = set()
    for spec in specs:
        for operation_plan in spec.service_config.service_operation_configs:
            for role_requirement in operation_plan.role_requirements:
                if role_requirement.role_ref.strip():
                    refs.add(role_requirement.role_ref.strip())
        for contract_config_plan in spec.service_config.contract_configs:
            for actor_role_grant in contract_config_plan.actor_role_grants:
                if actor_role_grant.role_ref.strip():
                    refs.add(actor_role_grant.role_ref.strip())
    return refs


def _split_endpoint_ref(*, endpoint_ref: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in endpoint_ref.split(".")]
    if len(parts) != 3 or any(not part for part in parts):
        raise RuntimeError(
            f"Invalid Service compile plan endpoint_ref {endpoint_ref!r}: expected <api>.<capability>.<endpoint>"
        )
    return parts[0], parts[1], parts[2]


def _encode_service_compile_plan_payload(
    *,
    package_name: str,
    fqn_prefix: str,
    service_configs: Sequence[ServiceConfigPlan],
) -> dict[str, object]:
    return {
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "service_configs": [
            _encode_service_config_plan(item) for item in service_configs
        ],
    }


async def _materialize_service_operation_inline_price(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane: MaterializationLaneContext,
    spec: ServiceDefinitionMaterializationSpec,
    operation_plan: ServiceOperationConfigPlan,
) -> UUID:
    if operation_plan.price is None:
        raise RuntimeError(
            "Inline Service price materialization requires operation_plan.price"
        )

    from aware_economy.catalog.coins import DEFAULT_COIN_DECLARATIONS
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.price.price import Price
    from aware_economy_ontology.price.price_enums import PriceType
    from aware_economy_ontology.price.price_schedule import PriceSchedule
    from aware_economy_ontology.price.pricing_policy import PricingPolicy
    from aware_economy_ontology.stable_ids import (
        stable_coin_id,
        stable_price_id,
        stable_price_schedule_id,
        stable_pricing_policy_id,
    )

    price = operation_plan.price
    coin_symbol = price.coin_symbol.upper()
    declarations_by_symbol = {
        declaration.symbol.upper(): declaration
        for declaration in DEFAULT_COIN_DECLARATIONS
    }
    declaration = declarations_by_symbol.get(coin_symbol)
    if declaration is None:
        raise RuntimeError(
            "Service inline price requires a known canonical coin declaration: "
            + f"service={spec.service_config.name!r} operation={operation_plan.name!r} coin_symbol={coin_symbol!r}"
        )

    price_name = _build_service_operation_price_name(
        spec=spec, operation_name=operation_plan.name
    )
    policy_name = f"{price_name}.policy"
    schedule_name = f"{price_name}.schedule"
    effective_from = _parse_iso_datetime_text(
        price.effective_from,
        field_name="effective_from",
        service_name=spec.service_config.name,
        operation_name=operation_plan.name,
    )
    effective_until = (
        _parse_iso_datetime_text(
            price.effective_until,
            field_name="effective_until",
            service_name=spec.service_config.name,
            operation_name=operation_plan.name,
        )
        if price.effective_until is not None
        else None
    )
    price_type_enum = (
        PriceType.fixed if price.price_type == "fixed" else PriceType.dynamic
    )

    coin_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index, projection_name="Coin"
    )
    price_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index, projection_name="Price"
    )
    pricing_policy_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="PricingPolicy",
    )

    coin_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=coin_projection_hash,
    )
    coin_id = stable_coin_id(symbol=declaration.symbol)
    existing_coin = await _maybe_hydrate_committed_lane_object(
        index=index,
        target_lane=coin_lane,
        orm_class=Coin,
        object_id=coin_id,
    )
    if existing_coin is None:
        runtime_lane = _bind_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=lane.branch_id,
            projection=coin_projection_hash,
            actor_id=actor_id,
        )
        with runtime_lane.activate(
            commit=True,
            publish=False,
            hydrate_portal_targets=False,
        ):
            _ = await Coin.build(
                symbol=declaration.symbol,
                name=declaration.name,
                type=declaration.type,
                decimals=declaration.decimals,
            )
    elif (
        (existing_coin.symbol or "").strip().upper() != declaration.symbol.upper()
        or (existing_coin.name or "").strip() != declaration.name
        or existing_coin.type != declaration.type
        or existing_coin.decimals != declaration.decimals
    ):
        raise RuntimeError(
            "Service inline price found conflicting committed Coin definition: "
            + f"coin_symbol={coin_symbol!r}"
        )

    price_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=price_projection_hash,
    )
    price_id = stable_price_id(
        coin_id=coin_id,
        name=price_name,
        type=price.price_type,
    )
    existing_price = await _maybe_hydrate_committed_lane_object(
        index=index,
        target_lane=price_lane,
        orm_class=Price,
        object_id=price_id,
    )
    if existing_price is None:
        runtime_lane = _bind_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=lane.branch_id,
            projection=price_projection_hash,
            actor_id=actor_id,
        )
        with runtime_lane.activate(
            commit=True,
            publish=False,
            hydrate_portal_targets=False,
        ):
            _ = await Price.build(
                coin_id=coin_id,
                name=price_name,
                type=price_type_enum,
            )
    elif (
        existing_price.coin_id != coin_id
        or (existing_price.name or "").strip() != price_name
        or getattr(existing_price.type, "value", str(existing_price.type))
        != price.price_type
    ):
        raise RuntimeError(
            "Service inline price found conflicting committed Price definition: "
            + f"price_name={price_name!r}"
        )

    pricing_policy_lane = MaterializationLaneContext(
        branch_id=lane.branch_id,
        projection_hash=pricing_policy_projection_hash,
    )
    pricing_policy_id = stable_pricing_policy_id(name=policy_name, version=1)
    existing_policy = await _maybe_hydrate_committed_lane_object(
        index=index,
        target_lane=pricing_policy_lane,
        orm_class=PricingPolicy,
        object_id=pricing_policy_id,
    )
    if existing_policy is None:
        runtime_lane = _bind_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=lane.branch_id,
            projection=pricing_policy_projection_hash,
            actor_id=actor_id,
        )
        with runtime_lane.activate(
            commit=True,
            publish=False,
            hydrate_portal_targets=False,
        ):
            _ = await PricingPolicy.build(
                name=policy_name,
                version=1,
                fail_closed=price.policy_fail_closed,
            )
    elif (
        (existing_policy.name or "").strip() != policy_name
        or existing_policy.version != 1
        or existing_policy.fail_closed != price.policy_fail_closed
    ):
        raise RuntimeError(
            "Service inline price found conflicting committed PricingPolicy definition: "
            + f"policy_name={policy_name!r}"
        )

    price_schedule_id = stable_price_schedule_id(
        price_id=price_id,
        pricing_policy_id=pricing_policy_id,
        name=schedule_name,
        version=1,
    )
    existing_schedule = await _maybe_hydrate_committed_lane_object(
        index=index,
        target_lane=price_lane,
        orm_class=PriceSchedule,
        object_id=price_schedule_id,
    )
    if existing_schedule is None:
        runtime_lane = _bind_runtime_lane(
            runtime=runtime,
            index=index,
            branch_id=lane.branch_id,
            projection=price_projection_hash,
            actor_id=actor_id,
        )
        price_ref = Price.model_construct(id=price_id)
        with runtime_lane.activate(
            commit=True,
            publish=False,
            hydrate_portal_targets=False,
        ):
            _ = await price_ref.create_price_schedule(
                pricing_policy_id=pricing_policy_id,
                name=schedule_name,
                version=1,
                effective_from=effective_from,
                effective_until=effective_until,
                fixed_amount=price.fixed_amount,
                markup_percentage=price.markup_percentage,
            )
    elif (
        existing_schedule.price_id != price_id
        or existing_schedule.pricing_policy_id != pricing_policy_id
        or (existing_schedule.name or "").strip() != schedule_name
        or existing_schedule.version != 1
        or existing_schedule.effective_from != effective_from
        or existing_schedule.effective_until != effective_until
        or existing_schedule.fixed_amount != price.fixed_amount
        or existing_schedule.markup_percentage != price.markup_percentage
    ):
        raise RuntimeError(
            "Service inline price found conflicting committed PriceSchedule definition: "
            + f"schedule_name={schedule_name!r}"
        )

    return price_id


def _build_service_operation_price_name(
    *,
    spec: ServiceDefinitionMaterializationSpec,
    operation_name: str,
) -> str:
    root = (spec.fqn_prefix or spec.package_name or spec.service_config.name).strip()
    return f"{root}.{spec.service_config.name}.{operation_name}"


def _parse_iso_datetime_text(
    value: str,
    *,
    field_name: str,
    service_name: str,
    operation_name: str,
) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(
            "Service inline price requires ISO-8601 timestamps: "
            + f"service={service_name!r} operation={operation_name!r} field={field_name!r} value={value!r}"
        ) from exc


async def _maybe_hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    orm_class: type[_THydrated],
    object_id: UUID,
    commit_store: FSCommitStore | None = None,
) -> _THydrated | None:
    store = commit_store or FSCommitStore()
    target_head = await store.head(
        branch_id=target_lane.branch_id,
        projection_hash=target_lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return None

    opg = index.opg_by_hash.get(target_lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Service materialization missing projection hash {target_lane.projection_hash!r}."
        )

    target_oig, _ = await CachedLaneMaterializer(commits=store).get(
        branch_id=target_lane.branch_id,
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

    scratch = reify_oig_session(
        index=index,
        opg=opg,
        oig=target_oig,
        branch_id=target_lane.branch_id,
    )
    return scratch.imap_get(orm_class, object_id)


async def _committed_lane_head_commit_id(
    lane: MaterializationLaneContext,
    *,
    commit_store: FSCommitStore | None = None,
) -> UUID | None:
    target_head = await (commit_store or FSCommitStore()).head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if target_head is None:
        return None
    raw = target_head.get("commit_id")
    if isinstance(raw, UUID):
        return raw
    if isinstance(raw, str) and raw.strip():
        return UUID(raw)
    return None


async def _object_instance_graph_commit_id_from_domain_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
    commit_store: FSCommitStore | None = None,
) -> UUID | None:
    domain_commit = await (commit_store or FSCommitStore()).get_commit(
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


def _encode_service_config_plan(plan: ServiceConfigPlan) -> dict[str, object]:
    return {
        "name": plan.name,
        "source_path": plan.source_path,
        "apis": [_encode_service_config_api_plan(row) for row in plan.apis],
        "experiences": [
            _encode_service_config_experience_plan(row) for row in plan.experiences
        ],
        "code_package_configs": [
            _encode_service_config_code_package_config_plan(row)
            for row in plan.code_package_configs
        ],
        "service_operation_configs": [
            _encode_service_operation_config_plan(row)
            for row in plan.service_operation_configs
        ],
        "contract_configs": [
            _encode_service_contract_config_plan(row) for row in plan.contract_configs
        ],
    }


def _encode_service_config_api_plan(plan: ServiceConfigApiPlan) -> dict[str, object]:
    return {
        "api_ref": plan.api_ref,
        "source_path": plan.source_path,
        "api_projections": [
            _encode_service_config_api_projection_plan(row)
            for row in plan.api_projections
        ],
    }


def _encode_service_config_api_projection_plan(
    plan: ServiceConfigApiProjectionPlan,
) -> dict[str, object]:
    return {
        "projection_ref": plan.projection_ref,
        "source_path": plan.source_path,
    }


def _encode_service_config_experience_plan(
    plan: ServiceConfigExperiencePlan,
) -> dict[str, object]:
    return {
        "experience_ref": plan.experience_ref,
        "source_path": plan.source_path,
    }


def _encode_service_config_code_package_config_plan(
    plan: ServiceConfigCodePackageConfigPlan,
) -> dict[str, object]:
    return {
        "slot_key": plan.slot_key,
        "manifest_kind": plan.manifest_kind,
        "surface": plan.surface,
        "code_package_config_key": plan.code_package_config_key,
        "code_package_config_id": str(plan.code_package_config_id),
        "cardinality": plan.cardinality,
        "required": plan.required,
        "source_path": plan.source_path,
    }


def _encode_service_operation_config_plan(
    plan: ServiceOperationConfigPlan,
) -> dict[str, object]:
    return {
        "name": plan.name,
        "source_path": plan.source_path,
        "admission_mode": plan.admission_mode,
        "fulfillment_kind": plan.fulfillment_kind,
        "receipt_policy": plan.receipt_policy,
        "settlement_policy": plan.settlement_policy,
        "price": _encode_inline_price_definition(plan.price),
        "price_ref": plan.price_ref,
        "api_endpoints": [
            _encode_service_operation_config_api_endpoint_plan(row)
            for row in plan.api_endpoints
        ],
        "api_views": [
            _encode_service_operation_config_api_view_plan(row)
            for row in plan.api_views
        ],
        "role_requirements": [
            _encode_service_operation_config_role_requirement_plan(row)
            for row in plan.role_requirements
        ],
    }


def _encode_service_operation_config_api_view_plan(
    plan: ServiceOperationConfigApiViewPlan,
) -> dict[str, object]:
    return {
        "view_ref": plan.view_ref,
        "source_path": plan.source_path,
    }


def _encode_service_operation_config_role_requirement_plan(
    plan: ServiceOperationConfigRoleRequirementPlan,
) -> dict[str, object]:
    return {
        "role_ref": plan.role_ref,
        "access_scope": plan.access_scope,
        "scope_kind": plan.scope_kind,
        "scope_ref": plan.scope_ref,
        "class_instance_identity_required": plan.class_instance_identity_required,
        "role_assignment_binding_required": plan.role_assignment_binding_required,
        "source_path": plan.source_path,
    }


def _encode_service_operation_config_api_endpoint_plan(
    plan: ServiceOperationConfigApiEndpointPlan,
) -> dict[str, object]:
    return {
        "endpoint_ref": plan.endpoint_ref,
        "api_ref": plan.api_ref,
        "source_path": plan.source_path,
    }


def _encode_service_contract_config_plan(
    plan: ServiceContractConfigPlan,
) -> dict[str, object]:
    return {
        "name": plan.name,
        "source_path": plan.source_path,
        "default_kind": plan.default_kind,
        "projection_experience_ref": plan.projection_experience_ref,
        "operation_grants": [
            _encode_service_contract_config_operation_grant_plan(row)
            for row in plan.operation_grants
        ],
        "actor_role_grants": [
            _encode_service_contract_config_actor_role_grant_plan(row)
            for row in plan.actor_role_grants
        ],
    }


def _encode_service_contract_config_operation_grant_plan(
    plan: ServiceContractConfigOperationGrantPlan,
) -> dict[str, object]:
    return {
        "operation_ref": plan.operation_ref,
        "access_scope": plan.access_scope,
        "source_path": plan.source_path,
    }


def _encode_service_contract_config_actor_role_grant_plan(
    plan: ServiceContractConfigActorRoleGrantPlan,
) -> dict[str, object]:
    return {
        "role_ref": plan.role_ref,
        "access_scope": plan.access_scope,
        "scope_kind": plan.scope_kind,
        "scope_ref": plan.scope_ref,
        "class_instance_identity_required": plan.class_instance_identity_required,
        "role_assignment_binding_required": plan.role_assignment_binding_required,
        "source_path": plan.source_path,
    }


def _decode_service_config_plan(payload: Mapping[str, object]) -> ServiceConfigPlan:
    name = _expect_string(payload.get("name"), field_name="service_config.name")
    source_path = _expect_string(
        payload.get("source_path"), field_name="service_config.source_path"
    )
    apis = tuple(
        _decode_service_config_api_plan(
            _expect_mapping(item, field_name="service_config.apis[]")
        )
        for item in _expect_list(
            payload.get("apis", ()), field_name="service_config.apis"
        )
    )
    experiences = tuple(
        _decode_service_config_experience_plan(
            _expect_mapping(item, field_name="service_config.experiences[]")
        )
        for item in _expect_list(
            payload.get("experiences", ()), field_name="service_config.experiences"
        )
    )
    code_package_configs = tuple(
        _decode_service_config_code_package_config_plan(
            _expect_mapping(
                item,
                field_name="service_config.code_package_configs[]",
            )
        )
        for item in _expect_list(
            payload.get("code_package_configs", ()),
            field_name="service_config.code_package_configs",
        )
    )
    service_operation_configs = tuple(
        _decode_service_operation_config_plan(
            _expect_mapping(
                item, field_name="service_config.service_operation_configs[]"
            )
        )
        for item in _expect_list(
            payload.get("service_operation_configs", ()),
            field_name="service_config.service_operation_configs",
        )
    )
    contract_configs = tuple(
        _decode_service_contract_config_plan(
            _expect_mapping(item, field_name="service_config.contract_configs[]")
        )
        for item in _expect_list(
            payload.get("contract_configs", ()),
            field_name="service_config.contract_configs",
        )
    )
    return ServiceConfigPlan(
        name=name,
        source_path=source_path,
        apis=apis,
        experiences=experiences,
        code_package_configs=code_package_configs,
        service_operation_configs=service_operation_configs,
        contract_configs=contract_configs,
    )


def _decode_service_config_api_plan(
    payload: Mapping[str, object]
) -> ServiceConfigApiPlan:
    return ServiceConfigApiPlan(
        api_ref=_expect_string(
            payload.get("api_ref"), field_name="service_config_api.api_ref"
        ),
        source_path=_expect_string(
            payload.get("source_path"), field_name="service_config_api.source_path"
        ),
        api_projections=tuple(
            _decode_service_config_api_projection_plan(
                _expect_mapping(item, field_name="service_config_api.api_projections[]")
            )
            for item in _expect_list(
                payload.get("api_projections", ()),
                field_name="service_config_api.api_projections",
            )
        ),
    )


def _decode_service_config_api_projection_plan(
    payload: Mapping[str, object],
) -> ServiceConfigApiProjectionPlan:
    return ServiceConfigApiProjectionPlan(
        projection_ref=_expect_string(
            payload.get("projection_ref"),
            field_name="service_config_api_projection.projection_ref",
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_config_api_projection.source_path",
        ),
    )


def _decode_service_config_experience_plan(
    payload: Mapping[str, object]
) -> ServiceConfigExperiencePlan:
    return ServiceConfigExperiencePlan(
        experience_ref=_expect_string(
            payload.get("experience_ref"),
            field_name="service_config_experience.experience_ref",
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_config_experience.source_path",
        ),
    )


def _decode_service_config_code_package_config_plan(
    payload: Mapping[str, object]
) -> ServiceConfigCodePackageConfigPlan:
    return ServiceConfigCodePackageConfigPlan(
        slot_key=_expect_string(
            payload.get("slot_key"),
            field_name="service_config_code_package_config.slot_key",
        ),
        manifest_kind=_expect_string(
            payload.get("manifest_kind"),
            field_name="service_config_code_package_config.manifest_kind",
        ),
        surface=_expect_string(
            payload.get("surface"),
            field_name="service_config_code_package_config.surface",
        ),
        code_package_config_key=_expect_string(
            payload.get("code_package_config_key"),
            field_name="service_config_code_package_config.code_package_config_key",
        ),
        code_package_config_id=UUID(
            _expect_string(
                payload.get("code_package_config_id"),
                field_name="service_config_code_package_config.code_package_config_id",
            )
        ),
        cardinality=_expect_optional_string(
            payload.get("cardinality"),
            field_name="service_config_code_package_config.cardinality",
        )
        or "many",
        required=_expect_optional_bool(
            payload.get("required"),
            field_name="service_config_code_package_config.required",
            default=False,
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_config_code_package_config.source_path",
        ),
    )


def _decode_service_operation_config_plan(
    payload: Mapping[str, object]
) -> ServiceOperationConfigPlan:
    return ServiceOperationConfigPlan(
        name=_expect_string(
            payload.get("name"), field_name="service_operation_config.name"
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_operation_config.source_path",
        ),
        admission_mode=_expect_optional_string(
            payload.get("admission_mode"),
            field_name="service_operation_config.admission_mode",
        )
        or "contract_required",
        fulfillment_kind=_expect_optional_string(
            payload.get("fulfillment_kind"),
            field_name="service_operation_config.fulfillment_kind",
        )
        or "coordination",
        receipt_policy=_expect_optional_string(
            payload.get("receipt_policy"),
            field_name="service_operation_config.receipt_policy",
        )
        or "committed",
        settlement_policy=_expect_optional_string(
            payload.get("settlement_policy"),
            field_name="service_operation_config.settlement_policy",
        )
        or "none",
        price=_decode_inline_price_definition(
            payload.get("price"),
            field_name="service_operation_config.price",
        ),
        price_ref=_expect_optional_string(
            payload.get("price_ref"), field_name="service_operation_config.price_ref"
        ),
        api_endpoints=tuple(
            _decode_service_operation_config_api_endpoint_plan(
                _expect_mapping(
                    item, field_name="service_operation_config.api_endpoints[]"
                )
            )
            for item in _expect_list(
                payload.get("api_endpoints", ()),
                field_name="service_operation_config.api_endpoints",
            )
        ),
        api_views=tuple(
            _decode_service_operation_config_api_view_plan(
                _expect_mapping(
                    item,
                    field_name="service_operation_config.api_views[]",
                )
            )
            for item in _expect_list(
                payload.get("api_views", ()),
                field_name="service_operation_config.api_views",
            )
        ),
        role_requirements=tuple(
            _decode_service_operation_config_role_requirement_plan(
                _expect_mapping(
                    item,
                    field_name="service_operation_config.role_requirements[]",
                )
            )
            for item in _expect_list(
                payload.get("role_requirements", ()),
                field_name="service_operation_config.role_requirements",
            )
        ),
    )


def _decode_service_operation_config_api_view_plan(
    payload: Mapping[str, object],
) -> ServiceOperationConfigApiViewPlan:
    return ServiceOperationConfigApiViewPlan(
        view_ref=_expect_string(
            payload.get("view_ref"),
            field_name="service_operation_config_api_view.view_ref",
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_operation_config_api_view.source_path",
        ),
    )


def _decode_service_operation_config_role_requirement_plan(
    payload: Mapping[str, object],
) -> ServiceOperationConfigRoleRequirementPlan:
    return ServiceOperationConfigRoleRequirementPlan(
        role_ref=_expect_string(
            payload.get("role_ref"),
            field_name="service_operation_config_role_requirement.role_ref",
        ),
        access_scope=_expect_optional_string(
            payload.get("access_scope"),
            field_name="service_operation_config_role_requirement.access_scope",
        )
        or "operation",
        scope_kind=_expect_optional_string(
            payload.get("scope_kind"),
            field_name="service_operation_config_role_requirement.scope_kind",
        )
        or "operation",
        scope_ref=_expect_optional_string(
            payload.get("scope_ref"),
            field_name="service_operation_config_role_requirement.scope_ref",
        )
        or "default",
        class_instance_identity_required=_expect_optional_bool(
            payload.get("class_instance_identity_required"),
            field_name="service_operation_config_role_requirement.class_instance_identity_required",
            default=False,
        ),
        role_assignment_binding_required=_expect_optional_bool(
            payload.get("role_assignment_binding_required"),
            field_name="service_operation_config_role_requirement.role_assignment_binding_required",
            default=True,
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_operation_config_role_requirement.source_path",
        ),
    )


def _decode_service_contract_config_plan(
    payload: Mapping[str, object],
) -> ServiceContractConfigPlan:
    return ServiceContractConfigPlan(
        name=_expect_string(
            payload.get("name"), field_name="service_contract_config.name"
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_contract_config.source_path",
        ),
        default_kind=_expect_optional_string(
            payload.get("default_kind"),
            field_name="service_contract_config.default_kind",
        )
        or "subscription",
        projection_experience_ref=_expect_optional_string(
            payload.get("projection_experience_ref"),
            field_name="service_contract_config.projection_experience_ref",
        ),
        operation_grants=tuple(
            _decode_service_contract_config_operation_grant_plan(
                _expect_mapping(
                    item,
                    field_name="service_contract_config.operation_grants[]",
                )
            )
            for item in _expect_list(
                payload.get("operation_grants", ()),
                field_name="service_contract_config.operation_grants",
            )
        ),
        actor_role_grants=tuple(
            _decode_service_contract_config_actor_role_grant_plan(
                _expect_mapping(
                    item,
                    field_name="service_contract_config.actor_role_grants[]",
                )
            )
            for item in _expect_list(
                payload.get("actor_role_grants", ()),
                field_name="service_contract_config.actor_role_grants",
            )
        ),
    )


def _decode_service_contract_config_operation_grant_plan(
    payload: Mapping[str, object],
) -> ServiceContractConfigOperationGrantPlan:
    return ServiceContractConfigOperationGrantPlan(
        operation_ref=_expect_string(
            payload.get("operation_ref"),
            field_name="service_contract_config_operation_grant.operation_ref",
        ),
        access_scope=_expect_optional_string(
            payload.get("access_scope"),
            field_name="service_contract_config_operation_grant.access_scope",
        )
        or "operation",
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_contract_config_operation_grant.source_path",
        ),
    )


def _decode_service_contract_config_actor_role_grant_plan(
    payload: Mapping[str, object],
) -> ServiceContractConfigActorRoleGrantPlan:
    return ServiceContractConfigActorRoleGrantPlan(
        role_ref=_expect_string(
            payload.get("role_ref"),
            field_name="service_contract_config_actor_role_grant.role_ref",
        ),
        access_scope=_expect_optional_string(
            payload.get("access_scope"),
            field_name="service_contract_config_actor_role_grant.access_scope",
        )
        or "service",
        scope_kind=_expect_optional_string(
            payload.get("scope_kind"),
            field_name="service_contract_config_actor_role_grant.scope_kind",
        )
        or "service",
        scope_ref=_expect_optional_string(
            payload.get("scope_ref"),
            field_name="service_contract_config_actor_role_grant.scope_ref",
        )
        or "default",
        class_instance_identity_required=_expect_optional_bool(
            payload.get("class_instance_identity_required"),
            field_name="service_contract_config_actor_role_grant.class_instance_identity_required",
            default=False,
        ),
        role_assignment_binding_required=_expect_optional_bool(
            payload.get("role_assignment_binding_required"),
            field_name="service_contract_config_actor_role_grant.role_assignment_binding_required",
            default=True,
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_contract_config_actor_role_grant.source_path",
        ),
    )


def _encode_inline_price_definition(
    price: ServiceInlinePriceDefinition | None,
) -> dict[str, object] | None:
    if price is None:
        return None
    return {
        "coin_symbol": price.coin_symbol,
        "price_type": price.price_type,
        "effective_from": price.effective_from,
        "fixed_amount": (
            canonical_decimal_text(price.fixed_amount)
            if price.fixed_amount is not None
            else None
        ),
        "markup_percentage": (
            canonical_decimal_text(price.markup_percentage)
            if price.markup_percentage is not None
            else None
        ),
        "effective_until": price.effective_until,
        "policy_fail_closed": price.policy_fail_closed,
    }


def _decode_inline_price_definition(
    value: object,
    *,
    field_name: str,
) -> ServiceInlinePriceDefinition | None:
    if value is None:
        return None
    payload = _expect_mapping(value, field_name=field_name)
    return ServiceInlinePriceDefinition(
        coin_symbol=_expect_string(
            payload.get("coin_symbol"), field_name=f"{field_name}.coin_symbol"
        ),
        price_type=_expect_string(
            payload.get("price_type"), field_name=f"{field_name}.price_type"
        ),
        effective_from=_expect_string(
            payload.get("effective_from"), field_name=f"{field_name}.effective_from"
        ),
        fixed_amount=_expect_optional_decimal(
            payload.get("fixed_amount"), field_name=f"{field_name}.fixed_amount"
        ),
        markup_percentage=_expect_optional_decimal(
            payload.get("markup_percentage"),
            field_name=f"{field_name}.markup_percentage",
        ),
        effective_until=_expect_optional_string(
            payload.get("effective_until"),
            field_name=f"{field_name}.effective_until",
        ),
        policy_fail_closed=_expect_optional_bool(
            payload.get("policy_fail_closed"),
            field_name=f"{field_name}.policy_fail_closed",
            default=True,
        ),
    )


def _decode_service_operation_config_api_endpoint_plan(
    payload: Mapping[str, object],
) -> ServiceOperationConfigApiEndpointPlan:
    return ServiceOperationConfigApiEndpointPlan(
        endpoint_ref=_expect_string(
            payload.get("endpoint_ref"),
            field_name="service_operation_config_api_endpoint.endpoint_ref",
        ),
        api_ref=_expect_string(
            payload.get("api_ref"),
            field_name="service_operation_config_api_endpoint.api_ref",
        ),
        source_path=_expect_string(
            payload.get("source_path"),
            field_name="service_operation_config_api_endpoint.source_path",
        ),
    )


def _expect_list(value: object, *, field_name: str) -> Sequence[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return value
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} must be a list"
    )


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} must be an object"
    )


def _expect_string(value: object, *, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} must be a non-empty string"
    )


def _expect_optional_string(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} must be a non-empty string or null"
    )


def _expect_optional_decimal(value: object, *, field_name: str) -> Decimal | None:
    if value is None:
        return None
    try:
        return decimal_value(value, field_name=field_name)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid Service compile plan payload: {field_name} must be canonical decimal text or null"
        ) from exc


def _expect_optional_bool(value: object, *, field_name: str, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} must be a boolean or null"
    )


def _resolve_committed_price_id(
    *,
    price_context: _CommittedPriceReferenceContext,
    price_ref: str,
) -> UUID:
    key = (price_ref or "").casefold().strip()
    price_id = price_context.price_ids_by_name.get(key)
    if price_id is None:
        raise RuntimeError(
            "Service compile-plan materialization could not resolve committed Price "
            + f"for price_ref={price_ref!r}."
        )
    return price_id


def _decode_service_operation_admission_mode(
    value: str,
    *,
    field_name: str,
) -> str:
    normalized = (value or "").strip().casefold()
    if normalized in {
        "contract_and_permit_required",
        "contract_required",
        "identity_required",
        "metered_settlement_required",
        "public_read",
    }:
        return normalized
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} has unsupported admission mode {value!r}"
    )


def _decode_service_operation_settlement_policy(
    value: str,
    *,
    field_name: str,
) -> ServiceOperationSettlementPolicy:
    normalized = (value or "").strip().casefold()
    if normalized == "none":
        return ServiceOperationSettlementPolicy.none
    if normalized == "reserve_before_execute":
        return ServiceOperationSettlementPolicy.reserve_before_execute
    if normalized == "reserve_and_finalize":
        return ServiceOperationSettlementPolicy.reserve_and_finalize
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} has unsupported settlement policy {value!r}"
    )


def _decode_service_operation_receipt_policy(
    value: str,
    *,
    field_name: str,
) -> ServiceOperationReceiptPolicy:
    normalized = (value or "").strip().casefold()
    if normalized == "committed":
        return ServiceOperationReceiptPolicy.committed
    if normalized == "read_model":
        return ServiceOperationReceiptPolicy.read_model
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} has unsupported receipt policy {value!r}"
    )


def _resolve_committed_service_operation_fulfillment_kind(
    *,
    service_name: str,
    operation_name: str,
    planned_kind: ServiceOperationFulfillmentKind,
    receipt_policy: ServiceOperationReceiptPolicy,
    endpoint_stream_modes: tuple[str | None, ...],
    has_api_views: bool,
) -> ServiceOperationFulfillmentKind:
    if not endpoint_stream_modes or not any(
        stream_mode is not None for stream_mode in endpoint_stream_modes
    ):
        return planned_kind
    if any(stream_mode is None for stream_mode in endpoint_stream_modes):
        raise RuntimeError(
            "Service operation cannot mix streaming and unary API endpoints: "
            + f"service={service_name!r} operation={operation_name!r}."
        )
    if has_api_views:
        raise RuntimeError(
            "Service streaming operation cannot also bind an API view: "
            + f"service={service_name!r} operation={operation_name!r}."
        )
    if receipt_policy is ServiceOperationReceiptPolicy.read_model:
        raise RuntimeError(
            "Service streaming operation cannot use read_model receipt policy: "
            + f"service={service_name!r} operation={operation_name!r}."
        )
    if planned_kind is ServiceOperationFulfillmentKind.view:
        raise RuntimeError(
            "Service streaming operation cannot compile from view fulfillment: "
            + f"service={service_name!r} operation={operation_name!r}."
        )
    return ServiceOperationFulfillmentKind.actuation


def _decode_service_operation_fulfillment_kind(
    value: str,
    *,
    field_name: str,
) -> ServiceOperationFulfillmentKind:
    normalized = (value or "").strip().casefold()
    if normalized == "actuation":
        return ServiceOperationFulfillmentKind.actuation
    if normalized == "coordination":
        return ServiceOperationFulfillmentKind.coordination
    if normalized == "view":
        return ServiceOperationFulfillmentKind.view
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} has unsupported fulfillment kind {value!r}"
    )


def _decode_service_contract_kind(
    value: str,
    *,
    field_name: str,
) -> ServiceContractKind:
    normalized = (value or "").strip().casefold()
    if normalized == "metered":
        return ServiceContractKind.metered
    if normalized == "one_time":
        return ServiceContractKind.one_time
    if normalized == "subscription":
        return ServiceContractKind.subscription
    raise RuntimeError(
        f"Invalid Service compile plan payload: {field_name} has unsupported contract kind {value!r}"
    )


def _insert_unique_ref[
    TKey, TValue
](*, refs: dict[TKey, TValue], key: TKey, value: TValue, error_context: str,) -> None:
    existing = refs.get(key)
    if existing is not None and existing != value:
        raise RuntimeError(f"API ref resolution found {error_context}.")
    refs[key] = value


__all__ = [
    "ServiceDefinitionMaterializationSpec",
    "ServicePackageMaterializationResult",
    "ServicePackageMaterializationSpec",
    "build_service_definition_materialization_plan",
    "decode_service_definition_materialization_step_payload",
    "encode_service_definition_materialization_step_payload",
    "load_service_compile_plan_payloads",
    "materialize_service_compile_plan_ontology",
    "materialize_service_definition_ontology",
    "materialize_service_package_from_manifest",
    "resolve_service_definition_materialization_specs",
    "resolve_service_package_dependency_payloads",
    "resolve_service_package_materialization_spec",
]
