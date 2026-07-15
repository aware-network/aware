from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from aware_code.semantic_function_call_execution import (
    SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY,
)
from aware_code.semantic_graph_execution import (
    SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY,
    SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY,
)
from aware_code.semantic_materialization import (
    SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY,
    SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    SemanticMaterializationBaselineRef,
    SemanticFunctionCallContext,
    SemanticProviderDeltaDurableExecutionInputs,
)
from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_graph import ApiGraph
from aware_code_ontology.code.code import Code
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_meta.runtime import decode_oig_attribute_value
from aware_api_runtime.source.compiler import load_api_ownership_from_source_texts
from aware_api_runtime.source.semantic_analysis import (
    semantic_deltas_for_api_ownership,
)
from aware_api_runtime.semantic_functions.execution import (
    API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY,
)


API_BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-hydration-preflight.v1"
)
API_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-semantic-object-index.v3"
)
API_BASELINE_ROOT_HYDRATION_REF_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-root-hydration-ref.v1"
)
API_BASELINE_ROOT_OIG_PROJECTION_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-root-oig-projection.v1"
)
API_BASELINE_SOURCE_HYDRATION_REF_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-source-hydration-ref.v1"
)
API_BASELINE_SOURCE_OIG_PROJECTION_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-source-oig-projection.v1"
)
API_BASELINE_ROOT_SOURCE_MERGE_CONTRACT_VERSION = (
    "aware.api.provider-delta.baseline-root-source-merge.v1"
)
API_DURABLE_EXECUTION_INPUTS_PREFLIGHT_CONTRACT_VERSION = (
    "aware.api.provider-delta-durable-execution-inputs-preflight.v1"
)
API_BASELINE_COMMIT_REF_FIELDS = (
    "baseline_source_object_instance_graph_commit_id",
    "baseline_semantic_object_instance_graph_commit_id",
    "baseline_semantic_root_object_instance_graph_commit_id",
)
API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS = (
    "source_object_instance_graph_commit_id",
    "semantic_branch_id",
    "semantic_projection_name",
    "semantic_package_id",
    "semantic_object_instance_graph_commit_id",
    "semantic_root_kind",
    "semantic_root_id",
    "semantic_root_object_instance_graph_commit_id",
)
API_PROVIDER_KEY = "aware_api"
API_ROOT_KIND = "api"
API_ROOT_PROJECTION_NAME = "Api"
API_SOURCE_ROOT_KIND = "code_package"
API_SOURCE_ROOT_PROJECTION_NAME = "CodePackage"


@dataclass(frozen=True, slots=True)
class ApiDeltaBaselineRootHydrationRefResolution:
    status: Literal["ready", "blocked"]
    reason: str
    source_ref: SemanticMaterializationBaselineRef | None = None
    hydration_ref: SemanticMaterializationBaselineRef | None = None
    blockers: tuple[str, ...] = ()
    contract_version: str = API_BASELINE_ROOT_HYDRATION_REF_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        source_ref_payload = (
            self.source_ref.model_dump(mode="json")
            if self.source_ref is not None
            else None
        )
        hydration_ref_payload = (
            self.hydration_ref.model_dump(mode="json")
            if self.hydration_ref is not None
            else None
        )
        return {
            "resolution_kind": "api_provider_delta_baseline_root_hydration_ref",
            "contract_version": self.contract_version,
            "status": self.status,
            "reason": self.reason,
            "ready": self.status == "ready",
            "blocked": self.status == "blocked",
            "blockers": self.blockers,
            "source_projection_name": (
                None
                if source_ref_payload is None
                else source_ref_payload.get("semantic_projection_name")
            ),
            "source_object_instance_graph_commit_id": (
                None
                if source_ref_payload is None
                else source_ref_payload.get("semantic_object_instance_graph_commit_id")
            ),
            "hydration_projection_name": (
                None
                if hydration_ref_payload is None
                else hydration_ref_payload.get("semantic_projection_name")
            ),
            "hydration_object_instance_graph_commit_id": (
                None
                if hydration_ref_payload is None
                else hydration_ref_payload.get(
                    "semantic_object_instance_graph_commit_id"
                )
            ),
            "semantic_root_kind": (
                None
                if source_ref_payload is None
                else source_ref_payload.get("semantic_root_kind")
            ),
            "semantic_root_id": (
                None
                if source_ref_payload is None
                else source_ref_payload.get("semantic_root_id")
            ),
            "semantic_root_object_instance_graph_commit_id": (
                None
                if source_ref_payload is None
                else source_ref_payload.get(
                    "semantic_root_object_instance_graph_commit_id"
                )
            ),
            "hydration_baseline_ref": hydration_ref_payload,
        }


@dataclass(frozen=True, slots=True)
class ApiDeltaBaselineRootOigProjection:
    status: Literal["ready", "blocked"]
    reason: str
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]]
    blockers: tuple[str, ...] = ()
    api_count: int = 0
    capability_count: int = 0
    endpoint_count: int = 0
    request_config_count: int = 0
    graph_count: int = 0
    contract_version: str = API_BASELINE_ROOT_OIG_PROJECTION_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        return {
            "projection_kind": "api_provider_delta_baseline_root_oig_projection",
            "contract_version": self.contract_version,
            "status": self.status,
            "reason": self.reason,
            "ready": self.status == "ready",
            "blocked": self.status == "blocked",
            "blockers": self.blockers,
            "api_count": self.api_count,
            "capability_count": self.capability_count,
            "endpoint_count": self.endpoint_count,
            "request_config_count": self.request_config_count,
            "graph_count": self.graph_count,
            "baseline_semantic_object_index_count": len(
                self.baseline_semantic_object_index
            ),
            "baseline_semantic_object_index_keys": tuple(
                sorted(self.baseline_semantic_object_index)
            ),
        }


@dataclass(frozen=True, slots=True)
class ApiDeltaBaselineSourceHydrationRefResolution:
    status: Literal["ready", "blocked"]
    reason: str
    source_ref: SemanticMaterializationBaselineRef | None = None
    hydration_ref: SemanticMaterializationBaselineRef | None = None
    blockers: tuple[str, ...] = ()
    contract_version: str = API_BASELINE_SOURCE_HYDRATION_REF_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        hydration_ref_payload = (
            self.hydration_ref.model_dump(mode="json")
            if self.hydration_ref is not None
            else None
        )
        return {
            "resolution_kind": ("api_provider_delta_baseline_source_hydration_ref"),
            "contract_version": self.contract_version,
            "status": self.status,
            "reason": self.reason,
            "ready": self.status == "ready",
            "blocked": self.status == "blocked",
            "blockers": self.blockers,
            "source_code_package_id": (
                None
                if self.source_ref is None
                else self.source_ref.source_code_package_id
            ),
            "source_object_instance_graph_commit_id": (
                None
                if self.source_ref is None
                else self.source_ref.source_object_instance_graph_commit_id
            ),
            "hydration_projection_name": (
                None
                if hydration_ref_payload is None
                else hydration_ref_payload.get("semantic_projection_name")
            ),
            "hydration_object_instance_graph_commit_id": (
                None
                if hydration_ref_payload is None
                else hydration_ref_payload.get(
                    "semantic_object_instance_graph_commit_id"
                )
            ),
            "hydration_baseline_ref": hydration_ref_payload,
        }


@dataclass(frozen=True, slots=True)
class ApiDeltaBaselineSourceOigProjection:
    status: Literal["ready", "blocked"]
    reason: str
    baseline_semantic_payload_index: Mapping[str, Mapping[str, object]]
    blockers: tuple[str, ...] = ()
    source_path_count: int = 0
    api_count: int = 0
    capability_count: int = 0
    endpoint_count: int = 0
    contract_version: str = API_BASELINE_SOURCE_OIG_PROJECTION_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        return {
            "projection_kind": (
                "api_provider_delta_baseline_source_code_package_oig_projection"
            ),
            "contract_version": self.contract_version,
            "status": self.status,
            "reason": self.reason,
            "ready": self.status == "ready",
            "blocked": self.status == "blocked",
            "blockers": self.blockers,
            "source_path_count": self.source_path_count,
            "api_count": self.api_count,
            "capability_count": self.capability_count,
            "endpoint_count": self.endpoint_count,
            "baseline_semantic_payload_index_count": len(
                self.baseline_semantic_payload_index
            ),
            "baseline_semantic_payload_index_keys": tuple(
                sorted(self.baseline_semantic_payload_index)
            ),
        }


@dataclass(frozen=True, slots=True)
class ApiDeltaBaselineRootSourceMerge:
    status: Literal["ready", "blocked"]
    reason: str
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]]
    blockers: tuple[str, ...] = ()
    missing_root_identity_keys: tuple[str, ...] = ()
    missing_source_payload_keys: tuple[str, ...] = ()
    contract_version: str = API_BASELINE_ROOT_SOURCE_MERGE_CONTRACT_VERSION

    def evidence_payload(self) -> dict[str, object]:
        return {
            "merge_kind": "api_provider_delta_baseline_root_source_merge",
            "contract_version": self.contract_version,
            "status": self.status,
            "reason": self.reason,
            "ready": self.status == "ready",
            "blocked": self.status == "blocked",
            "blockers": self.blockers,
            "missing_root_identity_keys": self.missing_root_identity_keys,
            "missing_source_payload_keys": self.missing_source_payload_keys,
            "baseline_semantic_object_index_count": len(
                self.baseline_semantic_object_index
            ),
            "baseline_semantic_object_index_keys": tuple(
                sorted(self.baseline_semantic_object_index)
            ),
        }


@dataclass(frozen=True, slots=True)
class _ApiDeltaBaselineOigRow:
    object_id: str
    values: Mapping[str, object]


def api_delta_root_baseline_hydration_ref_resolution(
    *,
    baseline_ref: Mapping[str, object],
) -> ApiDeltaBaselineRootHydrationRefResolution:
    try:
        source_ref = SemanticMaterializationBaselineRef.model_validate(baseline_ref)
    except ValueError:
        return ApiDeltaBaselineRootHydrationRefResolution(
            status="blocked",
            reason="api_provider_delta_baseline_root_hydration_ref_invalid",
            blockers=("api_provider_delta_baseline_root_hydration_ref_invalid",),
        )

    blockers: list[str] = []
    if _optional_text(source_ref.semantic_root_kind) != API_ROOT_KIND:
        blockers.append("api_provider_delta_baseline_root_kind_must_be_api")
    if _optional_text(source_ref.semantic_root_id) is None:
        blockers.append("api_provider_delta_baseline_root_id_required")
    root_commit_id = _optional_text(
        source_ref.semantic_root_object_instance_graph_commit_id
    )
    if root_commit_id is None:
        blockers.append("api_provider_delta_baseline_root_oig_commit_required")
    if blockers:
        return ApiDeltaBaselineRootHydrationRefResolution(
            status="blocked",
            reason=blockers[0],
            source_ref=source_ref,
            blockers=tuple(blockers),
        )
    if root_commit_id is None:
        raise AssertionError("validated API root OIG commit unexpectedly missing")

    hydration_ref = replace(
        source_ref,
        source="aware_api.provider_delta.baseline_root_hydration_ref",
        semantic_projection_name=API_ROOT_PROJECTION_NAME,
        semantic_projection_hash=None,
        semantic_object_instance_graph_commit_id=root_commit_id,
    )
    return ApiDeltaBaselineRootHydrationRefResolution(
        status="ready",
        reason="api_provider_delta_baseline_root_hydration_ref_ready",
        source_ref=source_ref,
        hydration_ref=hydration_ref,
    )


def api_delta_source_baseline_hydration_ref_resolution(
    *,
    baseline_ref: Mapping[str, object],
) -> ApiDeltaBaselineSourceHydrationRefResolution:
    try:
        source_ref = SemanticMaterializationBaselineRef.model_validate(baseline_ref)
    except ValueError:
        return ApiDeltaBaselineSourceHydrationRefResolution(
            status="blocked",
            reason="api_provider_delta_baseline_source_hydration_ref_invalid",
            blockers=("api_provider_delta_baseline_source_hydration_ref_invalid",),
        )

    blockers: list[str] = []
    source_code_package_id = _optional_text(source_ref.source_code_package_id)
    if source_code_package_id is None:
        blockers.append("api_provider_delta_baseline_source_code_package_id_required")
    source_commit_id = _optional_text(source_ref.source_object_instance_graph_commit_id)
    if source_commit_id is None:
        blockers.append("api_provider_delta_baseline_source_oig_commit_required")
    if blockers:
        return ApiDeltaBaselineSourceHydrationRefResolution(
            status="blocked",
            reason=blockers[0],
            source_ref=source_ref,
            blockers=tuple(blockers),
        )
    if source_code_package_id is None or source_commit_id is None:
        raise AssertionError("validated API source baseline identity missing")

    hydration_ref = replace(
        source_ref,
        source="aware_api.provider_delta.baseline_source_hydration_ref",
        semantic_projection_name=API_SOURCE_ROOT_PROJECTION_NAME,
        semantic_projection_hash=None,
        semantic_object_instance_graph_commit_id=source_commit_id,
        semantic_root_kind=API_SOURCE_ROOT_KIND,
        semantic_root_id=source_code_package_id,
        semantic_root_object_instance_graph_commit_id=source_commit_id,
    )
    return ApiDeltaBaselineSourceHydrationRefResolution(
        status="ready",
        reason="api_provider_delta_baseline_source_hydration_ref_ready",
        source_ref=source_ref,
        hydration_ref=hydration_ref,
    )


def api_delta_baseline_semantic_object_index_from_root_oig(
    *,
    oig: object,
    baseline_ref: SemanticMaterializationBaselineRef,
) -> ApiDeltaBaselineRootOigProjection:
    rows_by_kind, row_blockers = _api_delta_baseline_oig_rows(oig=oig)
    root_id = _optional_text(baseline_ref.semantic_root_id)
    if root_id is None:
        row_blockers.append("api_provider_delta_baseline_root_id_required")
    api_rows = tuple(
        row
        for row in rows_by_kind["api"]
        if root_id is not None and row.object_id == root_id
    )
    if len(api_rows) != 1:
        row_blockers.append(
            "api_provider_delta_baseline_root_oig_requires_exact_api_root"
        )
    if row_blockers:
        return _api_delta_blocked_root_oig_projection(
            blockers=tuple(row_blockers),
            rows_by_kind=rows_by_kind,
        )

    (api_row,) = api_rows
    api_name = _optional_text(api_row.values.get("name"))
    if api_name is None:
        return _api_delta_blocked_root_oig_projection(
            blockers=("api_provider_delta_baseline_api_name_required",),
            rows_by_kind=rows_by_kind,
        )
    capabilities = tuple(
        row
        for row in rows_by_kind["api_capability"]
        if _optional_text(row.values.get("api_id")) == api_row.object_id
    )
    capability_ids = frozenset(row.object_id for row in capabilities)
    endpoints = tuple(
        row
        for row in rows_by_kind["api_capability_endpoint"]
        if _optional_text(row.values.get("api_capability_id")) in capability_ids
    )
    endpoint_ids = frozenset(row.object_id for row in endpoints)
    request_configs = tuple(
        row
        for row in rows_by_kind["api_capability_endpoint_request_config"]
        if _optional_text(row.values.get("api_capability_endpoint_id")) in endpoint_ids
    )
    api_graphs = tuple(
        row
        for row in rows_by_kind["api_graph"]
        if _optional_text(row.values.get("api_id")) == api_row.object_id
    )
    blockers = _api_delta_baseline_root_structure_blockers(
        capabilities=capabilities,
        endpoints=endpoints,
    )
    if blockers:
        return _api_delta_blocked_root_oig_projection(
            blockers=blockers,
            rows_by_kind=rows_by_kind,
        )

    endpoint_count_by_capability_id: dict[str, int] = {}
    entries: dict[str, dict[str, object]] = {}
    api_semantic_key = f"api:{api_name}"
    entries[api_semantic_key] = _api_delta_baseline_index_entry(
        semantic_key=api_semantic_key,
        object_id=api_row.object_id,
        object_kind="api",
        baseline_ref=baseline_ref,
        payload={
            "name": api_name,
            "description": api_row.values.get("description"),
            "capability_count": len(capabilities),
            "graph_count": len(api_graphs),
        },
    )
    capability_name_by_id: dict[str, str] = {}
    for capability in capabilities:
        capability_name = _optional_text(capability.values.get("name"))
        if capability_name is None:
            raise AssertionError("validated API capability name unexpectedly missing")
        capability_name_by_id[capability.object_id] = capability_name
        endpoint_count_by_capability_id[capability.object_id] = sum(
            1
            for endpoint in endpoints
            if _optional_text(endpoint.values.get("api_capability_id"))
            == capability.object_id
        )
        capability_key = f"{api_semantic_key}/capability:{capability_name}"
        if capability_key in entries:
            return _api_delta_blocked_root_oig_projection(
                blockers=(
                    "api_provider_delta_baseline_duplicate_capability_semantic_key",
                ),
                rows_by_kind=rows_by_kind,
            )
        entries[capability_key] = _api_delta_baseline_index_entry(
            semantic_key=capability_key,
            object_id=capability.object_id,
            object_kind="api_capability",
            baseline_ref=baseline_ref,
            payload={
                "api_name": api_name,
                "name": capability_name,
                "description": capability.values.get("description"),
                "endpoint_count": endpoint_count_by_capability_id[capability.object_id],
            },
        )
    for endpoint in endpoints:
        capability_id = _optional_text(endpoint.values.get("api_capability_id"))
        capability_name = capability_name_by_id.get(capability_id or "")
        endpoint_name = _optional_text(endpoint.values.get("name"))
        if capability_name is None or endpoint_name is None:
            raise AssertionError(
                "validated API endpoint structure unexpectedly missing"
            )
        endpoint_key = (
            f"{api_semantic_key}/capability:{capability_name}"
            f"/endpoint:{endpoint_name}"
        )
        if endpoint_key in entries:
            return _api_delta_blocked_root_oig_projection(
                blockers=(
                    "api_provider_delta_baseline_duplicate_endpoint_semantic_key",
                ),
                rows_by_kind=rows_by_kind,
            )
        entries[endpoint_key] = _api_delta_baseline_index_entry(
            semantic_key=endpoint_key,
            object_id=endpoint.object_id,
            object_kind="api_capability_endpoint",
            baseline_ref=baseline_ref,
            payload={
                "api_name": api_name,
                "capability_name": capability_name,
                "name": endpoint_name,
                "description": endpoint.values.get("description"),
            },
        )
    return ApiDeltaBaselineRootOigProjection(
        status="ready",
        reason="api_provider_delta_baseline_root_oig_projected",
        baseline_semantic_object_index=dict(sorted(entries.items())),
        api_count=1,
        capability_count=len(capabilities),
        endpoint_count=len(endpoints),
        request_config_count=len(request_configs),
        graph_count=len(api_graphs),
    )


def api_delta_baseline_semantic_payload_index_from_source_code_package_oig(
    *,
    oig: object,
    baseline_ref: SemanticMaterializationBaselineRef,
) -> ApiDeltaBaselineSourceOigProjection:
    rows_by_kind, row_blockers = _api_delta_source_oig_rows(oig=oig)
    root_id = _optional_text(baseline_ref.semantic_root_id)
    code_package_rows = tuple(
        row
        for row in rows_by_kind["code_package"]
        if root_id is not None and row.object_id == root_id
    )
    if len(code_package_rows) != 1:
        row_blockers.append(
            "api_provider_delta_baseline_source_requires_exact_code_package_root"
        )
    if row_blockers:
        return _api_delta_blocked_source_oig_projection(
            blockers=tuple(row_blockers),
        )
    (code_package_row,) = code_package_rows
    package_root = _optional_text(code_package_row.values.get("package_root"))
    if package_root is None:
        return _api_delta_blocked_source_oig_projection(
            blockers=("api_provider_delta_baseline_source_package_root_required",),
        )

    source_texts: dict[Path, str] = {}
    blockers: list[str] = []
    package_code_rows = tuple(
        row
        for row in rows_by_kind["code_package_code"]
        if _optional_text(row.values.get("code_package_id"))
        == code_package_row.object_id
    )
    code_rows_by_package_code_id: dict[str, list[_ApiDeltaBaselineOigRow]] = {}
    for code_row in rows_by_kind["code"]:
        package_code_id = _optional_text(code_row.values.get("code_package_code_id"))
        if package_code_id is not None:
            code_rows_by_package_code_id.setdefault(package_code_id, []).append(
                code_row
            )
    text_rows_by_id = {row.object_id: row for row in rows_by_kind["content_part_text"]}
    for package_code_row in package_code_rows:
        relative_path = _optional_text(package_code_row.values.get("relative_path"))
        path_role = _api_delta_enum_text(package_code_row.values.get("path_role"))
        if path_role != "authored_source":
            continue
        if relative_path is None:
            blockers.append("api_provider_delta_baseline_source_relative_path_required")
            continue
        code_rows = tuple(
            code_rows_by_package_code_id.get(package_code_row.object_id, ())
        )
        if len(code_rows) != 1:
            blockers.append("api_provider_delta_baseline_source_requires_exact_code")
            continue
        (code_row,) = code_rows
        code_relative_path = _optional_text(code_row.values.get("relative_path"))
        if code_relative_path != relative_path:
            blockers.append("api_provider_delta_baseline_source_code_path_mismatch")
            continue
        language = _api_delta_enum_text(code_row.values.get("language"))
        if language != "aware":
            continue
        content_part_text_id = _optional_text(
            code_row.values.get("content_part_text_id")
        )
        text_row = text_rows_by_id.get(content_part_text_id or "")
        if text_row is None:
            blockers.append("api_provider_delta_baseline_source_content_text_required")
            continue
        inline_text = text_row.values.get("inline_text")
        if not isinstance(inline_text, str):
            blockers.append("api_provider_delta_baseline_source_inline_text_required")
            continue
        source_path = Path(relative_path)
        if source_path in source_texts:
            blockers.append(
                "api_provider_delta_baseline_source_duplicate_relative_path"
            )
            continue
        source_texts[source_path] = inline_text
    if not source_texts:
        blockers.append("api_provider_delta_baseline_source_aware_text_required")
    if blockers:
        return _api_delta_blocked_source_oig_projection(
            blockers=tuple(blockers),
            source_path_count=len(source_texts),
        )

    try:
        api_ownership = load_api_ownership_from_source_texts(
            package_root=Path(package_root),
            source_texts=source_texts,
        )
    except ValueError:
        return _api_delta_blocked_source_oig_projection(
            blockers=("api_provider_delta_baseline_source_api_parse_failed",),
            source_path_count=len(source_texts),
        )
    semantic_deltas = semantic_deltas_for_api_ownership(
        api_ownership=api_ownership,
    )
    object_kind_by_subject_type = {
        "aware_api.Api": "api",
        "aware_api.ApiCapability": "api_capability",
        "aware_api.ApiCapabilityEndpoint": "api_capability_endpoint",
    }
    entries: dict[str, dict[str, object]] = {}
    for delta in semantic_deltas:
        semantic_key = _optional_text(delta.semantic_key)
        object_kind = object_kind_by_subject_type.get(str(delta.subject_type))
        payload = delta.after_payload
        if (
            semantic_key is None
            or object_kind is None
            or not isinstance(payload, Mapping)
        ):
            return _api_delta_blocked_source_oig_projection(
                blockers=(
                    "api_provider_delta_baseline_source_semantic_payload_invalid",
                ),
                source_path_count=len(source_texts),
            )
        if semantic_key in entries:
            return _api_delta_blocked_source_oig_projection(
                blockers=("api_provider_delta_baseline_source_duplicate_semantic_key",),
                source_path_count=len(source_texts),
            )
        entries[semantic_key] = {
            "semantic_key": semantic_key,
            "object_kind": object_kind,
            "source": "aware_api.provider_delta.hydrated_source_code_package_oig",
            "source_refs": tuple(delta.source_refs),
            "payload": dict(payload),
        }
    return ApiDeltaBaselineSourceOigProjection(
        status="ready",
        reason="api_provider_delta_baseline_source_code_package_oig_projected",
        baseline_semantic_payload_index=dict(sorted(entries.items())),
        source_path_count=len(source_texts),
        api_count=len(api_ownership),
        capability_count=sum(len(api.capabilities) for api in api_ownership),
        endpoint_count=sum(
            len(capability.endpoints)
            for api in api_ownership
            for capability in api.capabilities
        ),
    )


def api_delta_baseline_semantic_object_index_from_root_and_source(
    *,
    root_projection: ApiDeltaBaselineRootOigProjection,
    source_projection: ApiDeltaBaselineSourceOigProjection,
    root_ref: SemanticMaterializationBaselineRef,
    source_ref: SemanticMaterializationBaselineRef,
) -> ApiDeltaBaselineRootSourceMerge:
    blockers: list[str] = []
    if root_projection.status != "ready":
        blockers.append("api_provider_delta_baseline_root_projection_required")
    if source_projection.status != "ready":
        blockers.append("api_provider_delta_baseline_source_projection_required")
    root_keys = frozenset(root_projection.baseline_semantic_object_index)
    source_keys = frozenset(source_projection.baseline_semantic_payload_index)
    missing_root_identity_keys = tuple(sorted(source_keys - root_keys))
    missing_source_payload_keys = tuple(sorted(root_keys - source_keys))
    if missing_root_identity_keys:
        blockers.append("api_provider_delta_baseline_source_keys_missing_root_identity")
    if missing_source_payload_keys:
        blockers.append("api_provider_delta_baseline_root_keys_missing_source_payload")
    if blockers:
        return ApiDeltaBaselineRootSourceMerge(
            status="blocked",
            reason=blockers[0],
            baseline_semantic_object_index={},
            blockers=tuple(blockers),
            missing_root_identity_keys=missing_root_identity_keys,
            missing_source_payload_keys=missing_source_payload_keys,
        )

    entries: dict[str, dict[str, object]] = {}
    for semantic_key in sorted(root_keys):
        root_entry = root_projection.baseline_semantic_object_index[semantic_key]
        source_entry = source_projection.baseline_semantic_payload_index[semantic_key]
        root_kind = _optional_text(root_entry.get("object_kind"))
        source_kind = _optional_text(source_entry.get("object_kind"))
        object_id = _optional_text(root_entry.get("object_id"))
        source_payload = source_entry.get("payload")
        if (
            root_kind is None
            or root_kind != source_kind
            or object_id is None
            or not isinstance(source_payload, Mapping)
        ):
            return ApiDeltaBaselineRootSourceMerge(
                status="blocked",
                reason="api_provider_delta_baseline_root_source_entry_mismatch",
                baseline_semantic_object_index={},
                blockers=("api_provider_delta_baseline_root_source_entry_mismatch",),
            )
        entries[semantic_key] = {
            "semantic_key": semantic_key,
            "object_id": object_id,
            "object_kind": root_kind,
            "object_instance_graph_commit_id": (
                root_ref.semantic_object_instance_graph_commit_id
            ),
            "source_object_instance_graph_commit_id": (
                source_ref.semantic_object_instance_graph_commit_id
            ),
            "source": (
                "aware_api.provider_delta.hydrated_source_code_package_and_api_root_oig"
            ),
            "identity_source": "aware_api.provider_delta.hydrated_api_root_oig",
            "payload_source": (
                "aware_api.provider_delta.hydrated_source_code_package_oig"
            ),
            "source_refs": tuple(source_entry.get("source_refs") or ()),
            "payload": dict(source_payload),
        }
    return ApiDeltaBaselineRootSourceMerge(
        status="ready",
        reason="api_provider_delta_baseline_root_source_merged",
        baseline_semantic_object_index=entries,
    )


def _api_delta_source_oig_rows(
    *,
    oig: object,
) -> tuple[dict[str, list[_ApiDeltaBaselineOigRow]], list[str]]:
    model_types_by_kind = {
        "code_package": CodePackage,
        "code_package_code": CodePackageCode,
        "code": Code,
        "content_part_text": ContentPartText,
    }
    entity_metadata = {
        str(model_type.get_class_config().id): (
            kind,
            _api_delta_entity_field_names_by_id(model_type=model_type),
        )
        for kind, model_type in model_types_by_kind.items()
    }
    rows_by_kind: dict[str, list[_ApiDeltaBaselineOigRow]] = {
        kind: [] for kind in model_types_by_kind
    }
    blockers: list[str] = []
    for class_instance in tuple(_object_value(oig, "class_instances") or ()):
        metadata = entity_metadata.get(
            _optional_text(_object_value(class_instance, "class_config_id")) or ""
        )
        if metadata is None:
            continue
        kind, field_names_by_id = metadata
        object_id = _optional_text(_object_value(class_instance, "source_object_id"))
        if object_id is None:
            blockers.append(
                f"api_provider_delta_baseline_source_{kind}_source_object_id_required"
            )
            continue
        values: dict[str, object] = {}
        for attribute in _api_delta_class_instance_attributes(
            class_instance=class_instance,
        ):
            field_name = field_names_by_id.get(
                _optional_text(_object_value(attribute, "attribute_config_id")) or ""
            )
            if field_name is not None:
                values[field_name] = _api_delta_attribute_primitive_value(
                    attribute=attribute,
                )
        rows_by_kind[kind].append(
            _ApiDeltaBaselineOigRow(object_id=object_id, values=values)
        )
    return rows_by_kind, blockers


def _api_delta_blocked_source_oig_projection(
    *,
    blockers: tuple[str, ...],
    source_path_count: int = 0,
) -> ApiDeltaBaselineSourceOigProjection:
    unique_blockers = tuple(dict.fromkeys(blockers))
    return ApiDeltaBaselineSourceOigProjection(
        status="blocked",
        reason=(
            unique_blockers[0]
            if unique_blockers
            else "api_provider_delta_baseline_source_oig_projection_blocked"
        ),
        baseline_semantic_payload_index={},
        blockers=unique_blockers,
        source_path_count=source_path_count,
    )


def _api_delta_enum_text(value: object) -> str | None:
    enum_value = getattr(value, "value", value)
    return _optional_text(enum_value)


def _api_delta_baseline_oig_rows(
    *,
    oig: object,
) -> tuple[dict[str, list[_ApiDeltaBaselineOigRow]], list[str]]:
    model_types_by_kind = {
        "api": Api,
        "api_capability": ApiCapability,
        "api_capability_endpoint": ApiCapabilityEndpoint,
        "api_capability_endpoint_request_config": (ApiCapabilityEndpointRequestConfig),
        "api_graph": ApiGraph,
    }
    entity_metadata = {
        str(model_type.get_class_config().id): (
            kind,
            _api_delta_entity_field_names_by_id(model_type=model_type),
        )
        for kind, model_type in model_types_by_kind.items()
    }
    rows_by_kind: dict[str, list[_ApiDeltaBaselineOigRow]] = {
        kind: [] for kind in model_types_by_kind
    }
    blockers: list[str] = []
    for class_instance in tuple(_object_value(oig, "class_instances") or ()):
        metadata = entity_metadata.get(
            _optional_text(_object_value(class_instance, "class_config_id")) or ""
        )
        if metadata is None:
            continue
        kind, field_names_by_id = metadata
        object_id = _optional_text(_object_value(class_instance, "source_object_id"))
        if object_id is None:
            blockers.append(
                f"api_provider_delta_baseline_{kind}_source_object_id_required"
            )
            continue
        values: dict[str, object] = {}
        for attribute in _api_delta_class_instance_attributes(
            class_instance=class_instance,
        ):
            field_name = field_names_by_id.get(
                _optional_text(_object_value(attribute, "attribute_config_id")) or ""
            )
            if field_name is None:
                continue
            values[field_name] = _api_delta_attribute_primitive_value(
                attribute=attribute,
            )
        rows_by_kind[kind].append(
            _ApiDeltaBaselineOigRow(
                object_id=object_id,
                values=values,
            )
        )
    return rows_by_kind, blockers


def _api_delta_entity_field_names_by_id(
    *,
    model_type: type[object],
) -> dict[str, str]:
    entity = model_type.get_class_config()  # type: ignore[attr-defined]
    fields: dict[str, str] = {}
    for binding in tuple(getattr(entity, "field_bindings", ()) or ()):
        field = getattr(binding, "field", None)
        field_id = _optional_text(getattr(field, "id", None))
        field_name = _optional_text(getattr(field, "name", None))
        if field_id is not None and field_name is not None:
            fields[field_id] = field_name
    return fields


def _api_delta_class_instance_attributes(
    *,
    class_instance: object,
) -> tuple[object, ...]:
    attributes: list[object] = list(
        tuple(_object_value(class_instance, "attributes") or ())
    )
    for edge in tuple(_object_value(class_instance, "class_instance_attributes") or ()):
        attribute = _object_value(edge, "attribute")
        if attribute is not None:
            attributes.append(attribute)
    deduped: dict[str, object] = {}
    for attribute in attributes:
        attribute_id = _optional_text(_object_value(attribute, "id"))
        key = attribute_id or str(id(attribute))
        deduped.setdefault(key, attribute)
    return tuple(deduped.values())


def _api_delta_attribute_primitive_value(*, attribute: object) -> object:
    value_root = _object_value(attribute, "value_root")
    try:
        return decode_oig_attribute_value(value_root)  # type: ignore[arg-type]
    except (AttributeError, TypeError, ValueError):
        pass
    primitive = _object_value(value_root, "primitive_value")
    if isinstance(primitive, Mapping):
        for key in ("value", "text", "string_value"):
            if key in primitive:
                return primitive[key]
        return None
    return primitive


def _api_delta_baseline_root_structure_blockers(
    *,
    capabilities: tuple[_ApiDeltaBaselineOigRow, ...],
    endpoints: tuple[_ApiDeltaBaselineOigRow, ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if any(_optional_text(row.values.get("name")) is None for row in capabilities):
        blockers.append("api_provider_delta_baseline_capability_name_required")
    if any(_optional_text(row.values.get("name")) is None for row in endpoints):
        blockers.append("api_provider_delta_baseline_endpoint_name_required")
    return tuple(dict.fromkeys(blockers))


def _api_delta_baseline_index_entry(
    *,
    semantic_key: str,
    object_id: str,
    object_kind: str,
    baseline_ref: SemanticMaterializationBaselineRef,
    payload: Mapping[str, object],
) -> dict[str, object]:
    return {
        "semantic_key": semantic_key,
        "object_id": object_id,
        "object_kind": object_kind,
        "object_instance_graph_commit_id": (
            baseline_ref.semantic_object_instance_graph_commit_id
        ),
        "source": "aware_api.provider_delta.hydrated_api_root_oig",
        "payload": dict(payload),
    }


def _api_delta_blocked_root_oig_projection(
    *,
    blockers: tuple[str, ...],
    rows_by_kind: Mapping[str, list[_ApiDeltaBaselineOigRow]],
) -> ApiDeltaBaselineRootOigProjection:
    unique_blockers = tuple(dict.fromkeys(blockers))
    return ApiDeltaBaselineRootOigProjection(
        status="blocked",
        reason=(
            unique_blockers[0]
            if unique_blockers
            else "api_provider_delta_baseline_root_oig_projection_blocked"
        ),
        baseline_semantic_object_index={},
        blockers=unique_blockers,
        api_count=len(rows_by_kind["api"]),
        capability_count=len(rows_by_kind["api_capability"]),
        endpoint_count=len(rows_by_kind["api_capability_endpoint"]),
        request_config_count=len(
            rows_by_kind["api_capability_endpoint_request_config"]
        ),
        graph_count=len(rows_by_kind["api_graph"]),
    )


def _object_value(value: object, key: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def api_delta_baseline_hydration_preflight(
    *,
    request: object,
) -> dict[str, object]:
    baseline_refs = api_delta_baseline_commit_refs(request=request)
    baseline_ref = api_delta_baseline_ref_payload(request=request)
    missing_fields = tuple(
        field_name
        for field_name in API_BASELINE_COMMIT_REF_FIELDS
        if not baseline_refs.get(field_name)
    )
    missing_baseline_ref_fields = api_delta_baseline_ref_missing_required_fields(
        baseline_ref=baseline_ref,
    )
    context = api_delta_operation_execution_context(request=request)
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    current_object_count = len(function_call_context.current_semantic_object_ids)
    baseline_semantic_object_index = (
        api_delta_previous_materialization_baseline_semantic_object_index(
            request=request,
        )
    )
    current_head_context_sources = api_delta_current_head_context_sources(
        request=request,
    )
    resolved_argument_ref_count = len(
        function_call_context.resolved_argument_ref_object_ids
    )
    durable_execution_inputs_preflight = api_delta_durable_execution_inputs_preflight(
        request=request
    )
    commit_backed_baseline_available = not missing_fields
    baseline_ref_hydrator_ready = (
        baseline_ref is not None and not missing_baseline_ref_fields
    )
    current_head_context_available = current_object_count > 0
    status = api_delta_baseline_hydration_status(
        commit_backed_baseline_available=commit_backed_baseline_available,
        baseline_ref_available=baseline_ref is not None,
        baseline_ref_hydrator_ready=baseline_ref_hydrator_ready,
        current_head_context_available=current_head_context_available,
    )
    return {
        "preflight_kind": "api_provider_delta_baseline_hydration_preflight",
        "contract_version": API_BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION,
        "status": status,
        "reason": api_delta_baseline_hydration_reason(status=status),
        "source": "workspace.provider_delta_request",
        "baseline_identity_source": "workspace.baseline_ref",
        "commit_backed_baseline_available": commit_backed_baseline_available,
        "baseline_ref_available": baseline_ref is not None,
        "baseline_ref_hydrator_ready": baseline_ref_hydrator_ready,
        "current_head_context_available": current_head_context_available,
        "current_head_context_sources": current_head_context_sources,
        "current_semantic_object_id_count": current_object_count,
        "baseline_semantic_object_index_available": bool(
            baseline_semantic_object_index
        ),
        "baseline_semantic_object_index_count": len(baseline_semantic_object_index),
        "resolved_argument_ref_object_id_count": resolved_argument_ref_count,
        "durable_execution_inputs_preflight": durable_execution_inputs_preflight,
        "durable_execution_inputs_status": (
            durable_execution_inputs_preflight["status"]
        ),
        "shared_execution_inputs_contract_available": (
            durable_execution_inputs_preflight[
                "shared_execution_inputs_contract_available"
            ]
        ),
        "would_persist": False,
        "did_persist": False,
        "did_hydrate": current_head_context_available,
        "required_fields": API_BASELINE_COMMIT_REF_FIELDS,
        "missing_required_fields": missing_fields,
        "baseline_commit_refs": baseline_refs,
        "baseline_ref_required_fields": API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS,
        "baseline_ref_missing_required_fields": missing_baseline_ref_fields,
        "baseline_ref": baseline_ref,
    }


def api_delta_baseline_hydration_status(
    *,
    commit_backed_baseline_available: bool,
    baseline_ref_available: bool,
    baseline_ref_hydrator_ready: bool,
    current_head_context_available: bool,
) -> str:
    if current_head_context_available:
        return "current_head_context_available"
    if not commit_backed_baseline_available:
        return "baseline_context_missing"
    if not baseline_ref_available:
        return "baseline_ref_missing"
    if not baseline_ref_hydrator_ready:
        return "baseline_ref_incomplete"
    return "current_head_context_missing"


def api_delta_baseline_hydration_reason(*, status: str) -> str:
    reasons = {
        "baseline_context_missing": (
            "api_provider_delta_baseline_hydration_requires_commit_backed_baseline"
        ),
        "baseline_ref_incomplete": (
            "api_provider_delta_baseline_ref_missing_required_hydration_fields"
        ),
        "baseline_ref_missing": (
            "api_provider_delta_baseline_hydration_requires_workspace_baseline_ref"
        ),
        "current_head_context_available": (
            "api_provider_delta_baseline_current_head_context_available"
        ),
        "current_head_context_missing": (
            "api_provider_delta_baseline_current_head_context_not_hydrated"
        ),
    }
    return reasons.get(
        status,
        "api_provider_delta_baseline_hydration_status_unknown",
    )


def api_delta_baseline_commit_refs(*, request: object) -> dict[str, object]:
    baseline_ref = api_delta_baseline_ref_payload(request=request)
    return {
        "baseline_source_object_instance_graph_commit_id": (
            _optional_text(
                getattr(
                    request, "baseline_source_object_instance_graph_commit_id", None
                )
            )
            or (
                _optional_text(
                    baseline_ref.get("source_object_instance_graph_commit_id")
                )
                if baseline_ref is not None
                else None
            )
        ),
        "baseline_semantic_object_instance_graph_commit_id": (
            _optional_text(
                getattr(
                    request,
                    "baseline_semantic_object_instance_graph_commit_id",
                    None,
                )
            )
            or (
                _optional_text(
                    baseline_ref.get("semantic_object_instance_graph_commit_id")
                )
                if baseline_ref is not None
                else None
            )
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            _optional_text(
                getattr(
                    request,
                    "baseline_semantic_root_object_instance_graph_commit_id",
                    None,
                )
            )
            or (
                _optional_text(
                    baseline_ref.get("semantic_root_object_instance_graph_commit_id")
                )
                if baseline_ref is not None
                else None
            )
        ),
    }


def api_delta_baseline_ref_payload(
    *,
    request: object,
) -> dict[str, object] | None:
    raw_ref = getattr(request, "baseline_ref", None)
    if raw_ref is None:
        evidence = getattr(request, "previous_materialization_evidence", None)
        if isinstance(evidence, Mapping):
            raw_ref = evidence.get("baseline_ref")
    payload = _model_payload(raw_ref)
    return payload or None


def api_delta_baseline_ref_missing_required_fields(
    *,
    baseline_ref: Mapping[str, object] | None,
) -> tuple[str, ...]:
    if baseline_ref is None:
        return API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS
    return tuple(
        field_name
        for field_name in API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS
        if _optional_text(baseline_ref.get(field_name)) is None
    )


def api_delta_current_semantic_object_ids(*, request: object) -> dict[str, str]:
    context = api_delta_operation_execution_context(request=request)
    current_object_ids = api_delta_context_current_semantic_object_ids(context=context)
    for (
        semantic_key,
        entry,
    ) in api_delta_previous_materialization_baseline_semantic_object_index(
        request=request,
    ).items():
        object_id = _optional_text(entry.get("object_id"))
        if object_id is not None:
            current_object_ids.setdefault(semantic_key, object_id)
    return dict(sorted(current_object_ids.items()))


def api_delta_previous_materialization_baseline_semantic_object_index(
    *,
    request: object,
) -> dict[str, dict[str, object]]:
    evidence = api_delta_request_value(
        request=request,
        key="previous_materialization_evidence",
    )
    if not isinstance(evidence, Mapping):
        return {}
    for field_name in (
        "baseline_semantic_object_index",
        "api_semantic_object_index",
    ):
        index = _api_delta_semantic_object_index(evidence.get(field_name))
        if index:
            return index
    return {}


def api_delta_resolved_argument_ref_object_ids(
    *,
    request: object,
) -> dict[str, str]:
    context = api_delta_operation_execution_context(request=request)
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    return api_delta_string_map(function_call_context.resolved_argument_ref_object_ids)


def api_delta_context_current_semantic_object_ids(
    *,
    context: Mapping[str, object],
) -> dict[str, str]:
    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    return {
        semantic_key: object_id
        for semantic_key, object_id in (
            (
                _optional_text(raw_key),
                _optional_text(raw_value),
            )
            for raw_key, raw_value in (
                function_call_context.current_semantic_object_ids.items()
            )
        )
        if semantic_key is not None and object_id is not None
    }


def api_delta_current_head_context_sources(*, request: object) -> tuple[str, ...]:
    sources: list[str] = []
    if api_delta_previous_materialization_current_semantic_object_ids(
        request=request,
    ):
        sources.append("previous_materialization_evidence")
    raw_context = api_delta_raw_operation_execution_context(request=request)
    if api_delta_context_current_semantic_object_ids(context=raw_context):
        sources.append("semantic_function_call_context")
    return tuple(sources)


def api_delta_previous_materialization_current_semantic_object_ids(
    *,
    request: object,
) -> dict[str, str]:
    evidence = api_delta_request_value(
        request=request,
        key="previous_materialization_evidence",
    )
    if not isinstance(evidence, Mapping):
        return {}
    current_objects = evidence.get("current_semantic_object_ids")
    if not isinstance(current_objects, Mapping):
        return {}
    return api_delta_string_map(current_objects)


def api_delta_previous_evidence_current_object_count(
    *,
    evidence: Mapping[str, object],
) -> int:
    raw_count = evidence.get("current_semantic_object_id_count")
    if isinstance(raw_count, int):
        return max(raw_count, 0)
    current_objects = evidence.get("current_semantic_object_ids")
    if isinstance(current_objects, Mapping):
        return len(current_objects)
    return 0


def api_delta_operation_execution_context(
    *,
    request: object,
) -> Mapping[str, object]:
    raw_context = api_delta_raw_operation_execution_context(request=request)
    context: dict[str, object] = (
        dict(raw_context) if isinstance(raw_context, Mapping) else {}
    )
    _api_delta_merge_previous_materialization_context(
        context=context,
        request=request,
    )
    durable_execution_inputs = api_delta_request_value(
        request=request,
        key=SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    )
    if durable_execution_inputs is not None:
        context.setdefault(
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
            durable_execution_inputs,
        )
    raw_config = context.get(SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY)
    if isinstance(raw_config, Mapping):
        config_payload = dict(raw_config)
        config_payload["enabled"] = True
    else:
        config_payload = {"enabled": True}
    context[SEMANTIC_FUNCTION_CALL_EXECUTION_CONFIG_KEY] = config_payload
    return context


def api_delta_raw_operation_execution_context(
    *,
    request: object,
) -> Mapping[str, object]:
    raw_context = getattr(request, "semantic_function_call_execution_context", None)
    if not isinstance(raw_context, Mapping):
        raw_context = getattr(request, "context", None)
    return raw_context if isinstance(raw_context, Mapping) else {}


def api_delta_durable_execution_inputs_preflight(
    *,
    request: object,
) -> dict[str, object]:
    payload = api_delta_durable_execution_inputs_payload(request=request)
    provider_inputs = _model_payload(payload.get("provider_inputs"))
    api_backend_provider_input_available = (
        api_delta_api_execution_backend_provider_input_source(
            provider_inputs=provider_inputs,
        )
        is not None
    )
    if not payload:
        status = "durable_execution_inputs_unavailable"
        missing_common_fields: tuple[str, ...] = ()
        normalized_payload: Mapping[str, object] = {}
    else:
        normalized = SemanticProviderDeltaDurableExecutionInputs.model_validate(payload)
        normalized_payload = normalized.model_dump(mode="python")
        missing_common_fields = normalized.missing_common_fields()
        status = (
            "durable_execution_inputs_ready"
            if not missing_common_fields
            else "durable_execution_inputs_partial"
        )
    return {
        "preflight_kind": "api_provider_delta_durable_execution_inputs_preflight",
        "contract_version": API_DURABLE_EXECUTION_INPUTS_PREFLIGHT_CONTRACT_VERSION,
        "status": status,
        "reason": api_delta_durable_execution_inputs_reason(status=status),
        "available": bool(payload),
        "blocked": False,
        "shared_execution_inputs_key": (
            SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY
        ),
        "shared_execution_inputs_contract_available": bool(payload),
        "shared_execution_inputs_contract_version": _optional_text(
            normalized_payload.get("contract_version")
        ),
        "common_inputs_available": status == "durable_execution_inputs_ready",
        "missing_common_fields": missing_common_fields,
        "provider_input_keys": tuple(sorted(str(key) for key in provider_inputs)),
        "api_execution_backend_provider_input_available": (
            api_backend_provider_input_available
        ),
        "api_execution_backend_provider_input_source": (
            api_delta_api_execution_backend_provider_input_source(
                provider_inputs=provider_inputs,
            )
        ),
        "provider_key": _optional_text(normalized_payload.get("provider_key")),
        "semantic_owner": _optional_text(normalized_payload.get("semantic_owner")),
        "semantic_branch_id": _optional_text(
            normalized_payload.get("semantic_branch_id")
        ),
        "semantic_projection_hash": _optional_text(
            normalized_payload.get("semantic_projection_hash")
        ),
        "semantic_projection_name": _optional_text(
            normalized_payload.get("semantic_projection_name")
        ),
        "author_id": _optional_text(normalized_payload.get("author_id")),
        "would_execute": False,
        "would_persist": False,
        "did_execute": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def api_delta_api_execution_backend_provider_input_source(
    *,
    provider_inputs: Mapping[str, object],
) -> str | None:
    if API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY in provider_inputs:
        return API_SEMANTIC_FUNCTION_CALL_EXECUTION_BACKEND_CONTEXT_KEY
    provider_backends = provider_inputs.get(
        SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY
    )
    if isinstance(provider_backends, Mapping) and "aware_api" in provider_backends:
        return f"{SEMANTIC_GRAPH_EXECUTION_BACKEND_BY_PROVIDER_CONTEXT_KEY}.aware_api"
    if SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY in provider_inputs:
        return SEMANTIC_GRAPH_EXECUTION_BACKEND_CONTEXT_KEY
    return None


def api_delta_durable_execution_inputs_reason(*, status: str) -> str:
    return {
        "durable_execution_inputs_ready": (
            "api_provider_delta_durable_execution_inputs_ready"
        ),
        "durable_execution_inputs_partial": (
            "api_provider_delta_durable_execution_inputs_partial"
        ),
        "durable_execution_inputs_unavailable": (
            "api_provider_delta_durable_execution_inputs_unavailable"
        ),
    }.get(status, "api_provider_delta_durable_execution_inputs_status_unknown")


def api_delta_durable_execution_inputs_payload(
    *,
    request: object,
) -> dict[str, object]:
    value = api_delta_request_value(
        request=request,
        key=SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY,
    )
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="python")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return {}


def api_delta_request_value(*, request: object, key: str) -> object | None:
    if isinstance(request, Mapping):
        value = request.get(key)
        if value is not None:
            return value
    value = getattr(request, key, None)
    if value is not None:
        return value
    for context_name in ("semantic_function_call_execution_context", "context"):
        context = getattr(request, context_name, None)
        if isinstance(context, Mapping):
            value = context.get(key)
            if value is not None:
                return value
    return None


def api_delta_string_map(value: Mapping[object, object]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = _optional_text(raw_key)
        item = _optional_text(raw_value)
        if key is not None and item is not None:
            normalized[key] = item
    return normalized


def _api_delta_semantic_object_index(
    value: object,
) -> dict[str, dict[str, object]]:
    if not isinstance(value, Mapping):
        return {}
    entries: dict[str, dict[str, object]] = {}
    for raw_semantic_key, raw_entry in value.items():
        semantic_key = _optional_text(raw_semantic_key)
        entry = _model_payload(raw_entry)
        if semantic_key is None or _optional_text(entry.get("object_id")) is None:
            continue
        entries[semantic_key] = entry
    return dict(sorted(entries.items()))


def _api_delta_merge_previous_materialization_context(
    *,
    context: dict[str, object],
    request: object,
) -> None:
    previous_object_ids = (
        api_delta_previous_materialization_current_semantic_object_ids(
            request=request,
        )
    )
    if not previous_object_ids:
        return
    previous_context = SemanticFunctionCallContext(
        current_semantic_object_ids=previous_object_ids,
    )
    explicit_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    merged_context = previous_context.merge(explicit_context)
    provider_contexts = _model_payload(
        context.get(SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY)
    )
    provider_contexts[API_PROVIDER_KEY] = merged_context.evidence_payload()
    context[SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY] = provider_contexts


def _model_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    if hasattr(value, "__dict__"):
        return {str(key): item for key, item in vars(value).items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "API_BASELINE_COMMIT_REF_FIELDS",
    "API_BASELINE_HYDRATION_PREFLIGHT_CONTRACT_VERSION",
    "API_BASELINE_REF_HYDRATOR_REQUIRED_FIELDS",
    "API_BASELINE_ROOT_HYDRATION_REF_CONTRACT_VERSION",
    "API_BASELINE_ROOT_OIG_PROJECTION_CONTRACT_VERSION",
    "API_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION",
    "API_DURABLE_EXECUTION_INPUTS_PREFLIGHT_CONTRACT_VERSION",
    "API_ROOT_KIND",
    "API_ROOT_PROJECTION_NAME",
    "ApiDeltaBaselineRootHydrationRefResolution",
    "ApiDeltaBaselineRootOigProjection",
    "api_delta_baseline_commit_refs",
    "api_delta_baseline_hydration_preflight",
    "api_delta_baseline_hydration_reason",
    "api_delta_baseline_hydration_status",
    "api_delta_baseline_semantic_object_index_from_root_oig",
    "api_delta_baseline_ref_missing_required_fields",
    "api_delta_baseline_ref_payload",
    "api_delta_context_current_semantic_object_ids",
    "api_delta_current_head_context_sources",
    "api_delta_current_semantic_object_ids",
    "api_delta_durable_execution_inputs_payload",
    "api_delta_durable_execution_inputs_preflight",
    "api_delta_durable_execution_inputs_reason",
    "api_delta_operation_execution_context",
    "api_delta_previous_evidence_current_object_count",
    "api_delta_previous_materialization_baseline_semantic_object_index",
    "api_delta_previous_materialization_current_semantic_object_ids",
    "api_delta_resolved_argument_ref_object_ids",
    "api_delta_root_baseline_hydration_ref_resolution",
    "api_delta_raw_operation_execution_context",
    "api_delta_request_value",
    "api_delta_string_map",
]
