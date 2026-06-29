from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan
from aware_code.semantic_provider_delta_events import (
    SEMANTIC_PROVIDER_DELTA_EVENT_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_EVENT_REPORT_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_READABLE_EVENT_CHAIN_CONTRACT_VERSION,
    SemanticProviderDeltaEvent,
    SemanticProviderDeltaEventReport,
    SemanticProviderDeltaReadableEventChain,
    semantic_provider_delta_events_from_payloads,
)


SEMANTIC_MATERIALIZATION_CAPABILITY = "materialize"
SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY = (
    "semantic_materialization_delta_adapter"
)
SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY = (
    "functional_delta_materialization"
)
SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY = "provider_delta_product_readiness"
SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.provider-delta-product-readiness.v1"
)
SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT = "materialize_delta"
SEMANTIC_FUNCTION_CALL_CONTEXT_KEY = "semantic_function_call_context"
SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY = (
    "semantic_function_call_context_by_provider"
)
SEMANTIC_SOURCE_SESSION_CONTEXT_KEY = "semantic_source_session_context"
SEMANTIC_SOURCE_SESSION_CONTEXT_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.source-session-context.v1"
)
SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND = "semantic_source_index"
SEMANTIC_MATERIALIZATION_EXECUTION_CONTEXT_KEY = (
    "semantic_materialization_execution_context"
)
SEMANTIC_MATERIALIZATION_LIFECYCLE_PROFILE_CONTEXT_KEY = (
    "semantic_materialization_lifecycle_profile"
)
SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY = (
    "semantic_materialization_target_manifest_paths"
)
SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_KEY = (
    "runtime_target_manifest_policy"
)
SEMANTIC_MATERIALIZATION_RUNTIME_TARGET_MANIFEST_POLICY_ISOLATE_TARGET_MANIFESTS = (
    "isolate_target_manifests"
)

SemanticMaterializationProgressCallback = Callable[[Mapping[str, object]], object]
SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY = (
    "language_materialization_targets"
)
SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY = (
    "language_materialization_tooling"
)
SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.language-tooling.v1"
)
SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY = "semantic_ontology_package_catalog"
SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA = (
    "aware.code.semantic-materialization.ontology-package-catalog.v1"
)
SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY = "execution_context_resolvers"
SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY = (
    "operation_execution_projection_name"
)
SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY = (
    "provider_delta_durable_execution_inputs"
)
SemanticPackageMaterializationMode = Literal[
    "noop",
    "delta",
    "full_rebuild",
    "failed",
]
SEMANTIC_PROVIDER_DELTA_BASELINE_REF_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.baseline-ref.v1"
)
SEMANTIC_PROVIDER_DELTA_BASELINE_RESOLUTION_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.baseline-resolution.v1"
)
SEMANTIC_PROVIDER_DELTA_LANE_STATE_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-lane-state.v1"
)
SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-request.v1"
)
SEMANTIC_PROVIDER_DELTA_ADAPTER_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-adapter.v1"
)
SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-result.v1"
)
SEMANTIC_PROVIDER_DELTA_HEAD_MOVE_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-head-move.v1"
)
SEMANTIC_PROVIDER_DELTA_REQUEST_BUNDLE_CONTRACT_VERSION = (
    "aware.workspace.semantic-materialization.provider-delta-request-bundle.v1"
)
SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.provider-delta-durable-execution-inputs.v1"
)
SEMANTIC_PROJECTION_PORTAL_POLICY_CONTRACT_VERSION = (
    "aware.code.semantic-materialization.projection-portal-policy.v1"
)
SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_REQUIRED_COMMON_FIELDS = (
    "semantic_branch_id",
    "semantic_projection_hash",
    "author_id",
)
SEMANTIC_PROVIDER_DELTA_BASELINE_REF_REQUIRED_FIELDS = (
    "source_object_instance_graph_commit_id",
    "semantic_branch_id",
    "semantic_projection_name",
    "semantic_package_id",
    "semantic_object_instance_graph_commit_id",
    "semantic_root_kind",
    "semantic_root_id",
    "semantic_root_object_instance_graph_commit_id",
)
SemanticProviderDeltaHeadMoveOperationFamily = Literal[
    "create",
    "update",
    "delete",
    "blocked",
    "upsert",
    "noop",
    "unknown",
]
SemanticProviderDeltaHeadMoveExecutableOperation = Literal[
    "create",
    "update",
    "delete",
]
SemanticProjectionPortalParticipation = Literal[
    "required",
    "optional",
    "selective",
    "created_in_plan",
]
SemanticProjectionPortalHydration = Literal[
    "none",
    "required",
    "selective",
    "created_in_plan",
]
_SEMANTIC_PROJECTION_PORTAL_PARTICIPATION_VALUES = frozenset(
    ("required", "optional", "selective", "created_in_plan")
)
_SEMANTIC_PROJECTION_PORTAL_HYDRATION_VALUES = frozenset(
    ("none", "required", "selective", "created_in_plan")
)
_SEMANTIC_PROJECTION_PORTAL_POLICY_RUNTIME_PROVENANCE_FIELDS = frozenset(
    (
        "baseline_commit_id",
        "baseline_ref",
        "branch_id",
        "commit_id",
        "head_commit_id",
        "head_refs",
        "lane_state",
        "object_instance_graph_id",
        "object_instance_graph_identity_id",
        "operation_branch_id",
        "projection_hash",
        "provider_delta_lane_state",
        "root_object_id",
        "semantic_branch_id",
        "semantic_object_instance_graph_commit_id",
        "semantic_projection_hash",
        "semantic_root_object_instance_graph_commit_id",
        "source_branch_id",
        "source_object_instance_graph_commit_id",
        "source_projection_hash",
        "target_branch_id",
        "target_object_instance_graph_commit_id",
        "target_projection_hash",
        "workspace_materialization_id",
        "workspace_revision_id",
    )
)


@dataclass(frozen=True, slots=True)
class SemanticProjectionPortalPolicyProjection:
    """Static projection participation declared by a semantic provider."""

    projection_name: str
    participation: SemanticProjectionPortalParticipation = "required"
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def model_validate(
        cls,
        value: object,
    ) -> "SemanticProjectionPortalPolicyProjection":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError(
                "Semantic projection portal policy projection must be a mapping."
            )
        _assert_no_projection_portal_policy_runtime_provenance(
            payload,
            context="projection",
        )
        participation = _optional_string(payload.get("participation")) or "required"
        if participation not in _SEMANTIC_PROJECTION_PORTAL_PARTICIPATION_VALUES:
            raise ValueError(
                "Semantic projection portal policy participation is invalid."
            )
        return cls(
            projection_name=_required_text(payload, "projection_name"),
            participation=cast(SemanticProjectionPortalParticipation, participation),
            metadata=dict(_mapping_payload(payload.get("metadata")) or {}),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "projection_name": self.projection_name,
            "participation": self.participation,
            "metadata": _json_safe_provider_input_value(dict(self.metadata)),
        }


@dataclass(frozen=True, slots=True)
class SemanticProjectionPortalPolicyPortal:
    """Static portal edge policy declared by a semantic provider."""

    policy_key: str
    source_projection: str
    source_path: str
    target_projection: str
    hydration: SemanticProjectionPortalHydration = "selective"
    operation_scope: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProjectionPortalPolicyPortal":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError(
                "Semantic projection portal policy portal must be a mapping."
            )
        _assert_no_projection_portal_policy_runtime_provenance(
            payload,
            context="portal",
        )
        hydration = _optional_string(payload.get("hydration")) or "selective"
        if hydration not in _SEMANTIC_PROJECTION_PORTAL_HYDRATION_VALUES:
            raise ValueError("Semantic projection portal policy hydration is invalid.")
        return cls(
            policy_key=_required_text(payload, "policy_key"),
            source_projection=_required_text(payload, "source_projection"),
            source_path=_required_text(payload, "source_path"),
            target_projection=_required_text(payload, "target_projection"),
            hydration=cast(SemanticProjectionPortalHydration, hydration),
            operation_scope=_string_tuple(payload.get("operation_scope")),
            metadata=dict(_mapping_payload(payload.get("metadata")) or {}),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "policy_key": self.policy_key,
            "source_projection": self.source_projection,
            "source_path": self.source_path,
            "target_projection": self.target_projection,
            "hydration": self.hydration,
            "operation_scope": list(self.operation_scope),
            "metadata": _json_safe_provider_input_value(dict(self.metadata)),
        }


@dataclass(frozen=True, slots=True)
class SemanticProjectionPortalPolicy:
    """Code-owned static policy for provider projection portal participation."""

    provider_key: str
    operation_family: str
    primary_projection: str
    semantic_owner: str | None = None
    projections: tuple[SemanticProjectionPortalPolicyProjection, ...] = ()
    portals: tuple[SemanticProjectionPortalPolicyPortal, ...] = ()
    contract_version: str = SEMANTIC_PROJECTION_PORTAL_POLICY_CONTRACT_VERSION
    policy_kind: Literal["semantic_projection_portal_policy"] = (
        "semantic_projection_portal_policy"
    )
    source: str = "semantic_contract"
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProjectionPortalPolicy":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Semantic projection portal policy must be a mapping.")
        _assert_no_projection_portal_policy_runtime_provenance(
            payload,
            context="policy",
        )
        return cls(
            contract_version=(
                _optional_string(payload.get("contract_version"))
                or SEMANTIC_PROJECTION_PORTAL_POLICY_CONTRACT_VERSION
            ),
            policy_kind="semantic_projection_portal_policy",
            source=_optional_string(payload.get("source")) or "semantic_contract",
            provider_key=_required_text(payload, "provider_key"),
            semantic_owner=_optional_string(payload.get("semantic_owner")),
            operation_family=_required_text(payload, "operation_family"),
            primary_projection=_required_text(payload, "primary_projection"),
            projections=tuple(
                SemanticProjectionPortalPolicyProjection.model_validate(item)
                for item in _sequence(payload.get("projections"))
            ),
            portals=tuple(
                SemanticProjectionPortalPolicyPortal.model_validate(item)
                for item in _sequence(payload.get("portals"))
            ),
            metadata=dict(_mapping_payload(payload.get("metadata")) or {}),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "contract_version": self.contract_version,
            "policy_kind": self.policy_kind,
            "source": self.source,
            "provider_key": self.provider_key,
            "semantic_owner": self.semantic_owner,
            "operation_family": self.operation_family,
            "primary_projection": self.primary_projection,
            "projections": [
                projection.model_dump(mode="json") for projection in self.projections
            ],
            "portals": [portal.model_dump(mode="json") for portal in self.portals],
            "metadata": _json_safe_provider_input_value(dict(self.metadata)),
        }

    def evidence_payload(self) -> dict[str, object]:
        return self.model_dump(mode="json")

    @property
    def projection_names(self) -> tuple[str, ...]:
        return tuple(projection.projection_name for projection in self.projections)

    @property
    def portal_policy_keys(self) -> tuple[str, ...]:
        return tuple(portal.policy_key for portal in self.portals)


@dataclass(frozen=True, slots=True)
class SemanticFunctionCallContext:
    current_semantic_object_ids: Mapping[str, str] = field(default_factory=dict)
    resolved_argument_ref_object_ids: Mapping[str, str] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "current_semantic_object_ids": dict(
                sorted(self.current_semantic_object_ids.items())
            ),
            "resolved_argument_ref_object_ids": dict(
                sorted(self.resolved_argument_ref_object_ids.items())
            ),
        }

    def merge(
        self,
        overlay: "SemanticFunctionCallContext",
    ) -> "SemanticFunctionCallContext":
        return SemanticFunctionCallContext(
            current_semantic_object_ids={
                **dict(self.current_semantic_object_ids),
                **dict(overlay.current_semantic_object_ids),
            },
            resolved_argument_ref_object_ids={
                **dict(self.resolved_argument_ref_object_ids),
                **dict(overlay.resolved_argument_ref_object_ids),
            },
        )

    @classmethod
    def from_payload(cls, payload: object) -> "SemanticFunctionCallContext":
        if not isinstance(payload, Mapping):
            return cls()
        return cls(
            current_semantic_object_ids=_normalized_string_map(
                payload.get("current_semantic_object_ids")
            ),
            resolved_argument_ref_object_ids=_normalized_string_map(
                payload.get("resolved_argument_ref_object_ids")
            ),
        )

    @classmethod
    def from_materialization_context(
        cls,
        context: Mapping[str, object],
        *,
        provider_key: str | None = None,
    ) -> "SemanticFunctionCallContext":
        base = cls.from_payload(context.get(SEMANTIC_FUNCTION_CALL_CONTEXT_KEY))
        if provider_key is None:
            return base
        provider_contexts = context.get(SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY)
        if not isinstance(provider_contexts, Mapping):
            return base
        provider_payload = provider_contexts.get(provider_key)
        return base.merge(cls.from_payload(provider_payload))


@dataclass(frozen=True, slots=True)
class SemanticSourceSessionCacheRef:
    """Provider-neutral cache ref for source/delta-derived indexes."""

    cache_kind: str
    cache_key: str
    signature: str | None = None
    source: str | None = None
    hit: bool | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "cache_kind": self.cache_kind,
            "cache_key": self.cache_key,
        }
        if self.signature is not None:
            payload["signature"] = self.signature
        if self.source is not None:
            payload["source"] = self.source
        if self.hit is not None:
            payload["hit"] = self.hit
        if self.evidence:
            payload["evidence"] = _json_safe_provider_input_value(
                dict(sorted(self.evidence.items()))
            )
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "SemanticSourceSessionCacheRef | None":
        mapping = _mapping_payload(payload)
        if mapping is None:
            return None
        cache_kind = _optional_string(mapping.get("cache_kind"))
        cache_key = _optional_string(mapping.get("cache_key"))
        if cache_kind is None or cache_key is None:
            return None
        return cls(
            cache_kind=cache_kind,
            cache_key=cache_key,
            signature=_optional_string(mapping.get("signature")),
            source=_optional_string(mapping.get("source")),
            hit=_optional_bool(mapping.get("hit")),
            evidence=dict(_mapping_payload(mapping.get("evidence")) or {}),
        )


@dataclass(frozen=True, slots=True)
class SemanticSourceSessionPackageContext:
    """Source package slice participating in a semantic source session."""

    package_name: str
    code_package_id: str | None = None
    package_root: str | None = None
    manifest_path: str | None = None
    semantic_provider_key: str | None = None
    semantic_owner: str | None = None
    delta_fingerprint: str | None = None
    source_files: tuple[str, ...] = ()
    cache_refs: tuple[SemanticSourceSessionCacheRef, ...] = ()
    evidence: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "package_name": self.package_name,
            "source_files": self.source_files,
            "cache_refs": tuple(
                cache_ref.evidence_payload() for cache_ref in self.cache_refs
            ),
        }
        if self.code_package_id is not None:
            payload["code_package_id"] = self.code_package_id
        if self.package_root is not None:
            payload["package_root"] = self.package_root
        if self.manifest_path is not None:
            payload["manifest_path"] = self.manifest_path
        if self.semantic_provider_key is not None:
            payload["semantic_provider_key"] = self.semantic_provider_key
        if self.semantic_owner is not None:
            payload["semantic_owner"] = self.semantic_owner
        if self.delta_fingerprint is not None:
            payload["delta_fingerprint"] = self.delta_fingerprint
        if self.evidence:
            payload["evidence"] = _json_safe_provider_input_value(
                dict(sorted(self.evidence.items()))
            )
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> "SemanticSourceSessionPackageContext | None":
        mapping = _mapping_payload(payload)
        if mapping is None:
            return None
        package_name = _optional_string(mapping.get("package_name"))
        if package_name is None:
            return None
        cache_refs = tuple(
            cache_ref
            for item in _sequence(mapping.get("cache_refs"))
            for cache_ref in (SemanticSourceSessionCacheRef.from_payload(item),)
            if cache_ref is not None
        )
        return cls(
            package_name=package_name,
            code_package_id=_optional_string(mapping.get("code_package_id")),
            package_root=_optional_string(mapping.get("package_root")),
            manifest_path=_optional_string(mapping.get("manifest_path")),
            semantic_provider_key=_optional_string(
                mapping.get("semantic_provider_key")
            ),
            semantic_owner=_optional_string(mapping.get("semantic_owner")),
            delta_fingerprint=_optional_string(mapping.get("delta_fingerprint")),
            source_files=_string_tuple(mapping.get("source_files")),
            cache_refs=cache_refs,
            evidence=dict(_mapping_payload(mapping.get("evidence")) or {}),
        )


@dataclass(frozen=True, slots=True)
class SemanticSourceSessionContext:
    """Code-owned source session envelope supplied by an environment."""

    source_session_id: str | None = None
    environment: str = "workspace"
    branch_key: str | None = None
    session_key: str | None = None
    source_delta_fingerprint: str | None = None
    lifecycle_stages: tuple[str, ...] = ()
    packages: tuple[SemanticSourceSessionPackageContext, ...] = ()
    cache_refs: tuple[SemanticSourceSessionCacheRef, ...] = ()
    evidence: Mapping[str, object] = field(default_factory=dict)
    contract_version: str = SEMANTIC_SOURCE_SESSION_CONTEXT_CONTRACT_VERSION
    context_kind: Literal["semantic_source_session_context"] = (
        "semantic_source_session_context"
    )

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "context_kind": self.context_kind,
            "contract_version": self.contract_version,
            "environment": self.environment,
            "lifecycle_stages": self.lifecycle_stages,
            "packages": tuple(package.evidence_payload() for package in self.packages),
            "cache_refs": tuple(
                cache_ref.evidence_payload() for cache_ref in self.cache_refs
            ),
        }
        if self.source_session_id is not None:
            payload["source_session_id"] = self.source_session_id
        if self.branch_key is not None:
            payload["branch_key"] = self.branch_key
        if self.session_key is not None:
            payload["session_key"] = self.session_key
        if self.source_delta_fingerprint is not None:
            payload["source_delta_fingerprint"] = self.source_delta_fingerprint
        if self.evidence:
            payload["evidence"] = _json_safe_provider_input_value(
                dict(sorted(self.evidence.items()))
            )
        return payload

    @classmethod
    def from_payload(cls, payload: object) -> "SemanticSourceSessionContext":
        mapping = _mapping_payload(payload)
        if mapping is None:
            return cls()
        packages = tuple(
            package
            for item in _sequence(mapping.get("packages"))
            for package in (SemanticSourceSessionPackageContext.from_payload(item),)
            if package is not None
        )
        cache_refs = tuple(
            cache_ref
            for item in _sequence(mapping.get("cache_refs"))
            for cache_ref in (SemanticSourceSessionCacheRef.from_payload(item),)
            if cache_ref is not None
        )
        return cls(
            contract_version=(
                _optional_string(mapping.get("contract_version"))
                or SEMANTIC_SOURCE_SESSION_CONTEXT_CONTRACT_VERSION
            ),
            source_session_id=_optional_string(mapping.get("source_session_id")),
            environment=_optional_string(mapping.get("environment")) or "workspace",
            branch_key=_optional_string(mapping.get("branch_key")),
            session_key=_optional_string(mapping.get("session_key")),
            source_delta_fingerprint=_optional_string(
                mapping.get("source_delta_fingerprint")
            ),
            lifecycle_stages=_string_tuple(mapping.get("lifecycle_stages")),
            packages=packages,
            cache_refs=cache_refs,
            evidence=dict(_mapping_payload(mapping.get("evidence")) or {}),
        )

    @classmethod
    def from_materialization_context(
        cls,
        context: Mapping[str, object],
    ) -> "SemanticSourceSessionContext":
        return cls.from_payload(context.get(SEMANTIC_SOURCE_SESSION_CONTEXT_KEY))


@dataclass(frozen=True, slots=True)
class SemanticLanguageMaterializationTarget:
    """Code-owned request payload for provider language materialization targets."""

    target_language_plugin_id: CodeLanguage
    output_root: Path
    import_root: str
    package_name: str
    materialization_source: str
    code_package_surface: str
    source_is_runtime: bool = False
    renderer_profile: str | None = None
    renderer_kind: str | None = None
    stable_ids_import_root: str | None = None
    stable_ids_ownership: str | None = None
    stable_ids_resolution_policy: str | None = None

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "target_language_plugin_id": self.target_language_plugin_id.value,
            "output_root": self.output_root.as_posix(),
            "import_root": self.import_root,
            "package_name": self.package_name,
            "materialization_source": self.materialization_source,
            "code_package_surface": self.code_package_surface,
        }
        if self.source_is_runtime:
            payload["source_is_runtime"] = True
        if self.renderer_profile is not None:
            payload["renderer_profile"] = self.renderer_profile
        if self.renderer_kind is not None:
            payload["renderer_kind"] = self.renderer_kind
        if self.stable_ids_import_root is not None:
            payload["stable_ids_import_root"] = self.stable_ids_import_root
        if self.stable_ids_ownership is not None:
            payload["stable_ids_ownership"] = self.stable_ids_ownership
        if self.stable_ids_resolution_policy is not None:
            payload["stable_ids_resolution_policy"] = self.stable_ids_resolution_policy
        return payload


def encode_semantic_function_call_context(
    context: SemanticFunctionCallContext,
) -> dict[str, object]:
    return context.evidence_payload()


def encode_semantic_function_call_context_by_provider(
    contexts: Mapping[str, SemanticFunctionCallContext],
) -> dict[str, object]:
    return {
        str(provider_key).strip(): context.evidence_payload()
        for provider_key, context in sorted(contexts.items())
        if str(provider_key).strip()
    }


def encode_semantic_source_session_context(
    context: SemanticSourceSessionContext,
) -> dict[str, object]:
    return context.evidence_payload()


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationExecutionContext:
    """Provider-declared semantic execution context passed by Workspace."""

    entries: Mapping[str, object] = field(default_factory=dict)
    provider_entries: Mapping[str, Mapping[str, object]] = field(default_factory=dict)

    def get(
        self, context_key: str, *, provider_key: str | None = None
    ) -> object | None:
        normalized_context_key = context_key.strip()
        if not normalized_context_key:
            return None
        if provider_key is not None and provider_key.strip():
            provider_payload = self.provider_entries.get(provider_key.strip())
            if (
                provider_payload is not None
                and normalized_context_key in provider_payload
            ):
                return provider_payload[normalized_context_key]
        return self.entries.get(normalized_context_key)

    def provider_context(
        self,
        provider_key: str,
    ) -> "SemanticPackageMaterializationExecutionContext":
        normalized_provider_key = provider_key.strip()
        provider_payload = (
            self.provider_entries.get(normalized_provider_key)
            if normalized_provider_key
            else None
        )
        if not provider_payload:
            return SemanticPackageMaterializationExecutionContext(
                entries=dict(self.entries),
            )
        return SemanticPackageMaterializationExecutionContext(
            entries={**dict(self.entries), **dict(provider_payload)},
            provider_entries={
                normalized_provider_key: dict(provider_payload),
            },
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "schema": "aware.semantic_materialization.execution_context.v1",
            "context_keys": tuple(sorted(str(key) for key in self.entries)),
            "provider_context_keys": {
                provider_key: tuple(sorted(str(key) for key in provider_payload))
                for provider_key, provider_payload in sorted(
                    self.provider_entries.items()
                )
            },
        }


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationExecutionContextRequest:
    """Generic request passed to provider-declared context resolvers."""

    provider_key: str
    semantic_owner: str
    context_key: str
    workspace_root: Path
    manifest_path: Path
    runtime: Any
    index: Any
    actor_id: UUID | None
    branch_id: UUID
    context: Mapping[str, object] = field(default_factory=dict)
    provider_payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaDurableExecutionInputs:
    """Code-owned durable input envelope for provider delta execution."""

    provider_key: str | None = None
    semantic_owner: str | None = None
    semantic_branch_id: str | None = None
    semantic_projection_hash: str | None = None
    semantic_projection_name: str | None = None
    author_id: str | None = None
    source_object_instance_graph_commit_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    semantic_package_id: str | None = None
    semantic_package_commit_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    object_instance_graph_identity_id: str | None = None
    object_instance_graph_id: str | None = None
    root_object_id: str | None = None
    commit_id: str | None = None
    operation_branch_id: str | None = None
    workspace_root: str | None = None
    contract_version: str = (
        SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_CONTRACT_VERSION
    )
    input_kind: Literal["semantic_provider_delta_durable_execution_inputs"] = (
        "semantic_provider_delta_durable_execution_inputs"
    )
    source: str = "workspace.provider_delta.operation_execution_context"
    provider_inputs: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def model_validate(
        cls,
        value: object,
    ) -> "SemanticProviderDeltaDurableExecutionInputs":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError(
                "Provider delta durable execution inputs must be a mapping."
            )
        provider_inputs = payload.get("provider_inputs")
        return cls(
            contract_version=(
                _optional_string(payload.get("contract_version"))
                or SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_CONTRACT_VERSION
            ),
            input_kind="semantic_provider_delta_durable_execution_inputs",
            source=(
                _optional_string(payload.get("source"))
                or "workspace.provider_delta.operation_execution_context"
            ),
            provider_key=_optional_string(payload.get("provider_key")),
            semantic_owner=_optional_string(payload.get("semantic_owner")),
            semantic_branch_id=_optional_string(payload.get("semantic_branch_id")),
            semantic_projection_hash=_optional_string(
                payload.get("semantic_projection_hash")
            ),
            semantic_projection_name=_optional_string(
                payload.get("semantic_projection_name")
            ),
            author_id=_optional_string(payload.get("author_id")),
            source_object_instance_graph_commit_id=_optional_string(
                payload.get("source_object_instance_graph_commit_id")
            ),
            semantic_object_instance_graph_commit_id=_optional_string(
                payload.get("semantic_object_instance_graph_commit_id")
            ),
            semantic_root_object_instance_graph_commit_id=_optional_string(
                payload.get("semantic_root_object_instance_graph_commit_id")
            ),
            semantic_package_id=_optional_string(payload.get("semantic_package_id")),
            semantic_package_commit_id=_optional_string(
                payload.get("semantic_package_commit_id")
            ),
            semantic_root_kind=_optional_string(payload.get("semantic_root_kind")),
            semantic_root_id=_optional_string(payload.get("semantic_root_id")),
            object_instance_graph_identity_id=_optional_string(
                payload.get("object_instance_graph_identity_id")
            ),
            object_instance_graph_id=_optional_string(
                payload.get("object_instance_graph_id")
            ),
            root_object_id=_optional_string(payload.get("root_object_id")),
            commit_id=_optional_string(payload.get("commit_id")),
            operation_branch_id=_optional_string(payload.get("operation_branch_id")),
            workspace_root=_optional_string(payload.get("workspace_root")),
            provider_inputs=(
                dict(provider_inputs) if isinstance(provider_inputs, Mapping) else {}
            ),
        )

    def missing_common_fields(self) -> tuple[str, ...]:
        payload = self.model_dump(mode="json")
        return tuple(
            field_name
            for field_name in (
                SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_REQUIRED_COMMON_FIELDS
            )
            if not _optional_string(payload.get(field_name))
        )

    def evidence_payload(self) -> dict[str, object]:
        missing_common_fields = self.missing_common_fields()
        return {
            "input_kind": self.input_kind,
            "contract_version": self.contract_version,
            "source": self.source,
            "provider_key": self.provider_key,
            "semantic_owner": self.semantic_owner,
            "available": not missing_common_fields,
            "missing_common_fields": missing_common_fields,
            "provider_input_keys": tuple(
                sorted(str(key) for key in self.provider_inputs)
            ),
        }

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        provider_inputs: Mapping[str, object]
        if mode == "json":
            provider_inputs = {
                str(key): _json_safe_provider_input_value(value)
                for key, value in sorted(
                    self.provider_inputs.items(),
                    key=lambda item: str(item[0]),
                )
            }
        else:
            provider_inputs = dict(self.provider_inputs)
        missing_common_fields = tuple(
            field_name
            for field_name in (
                SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_REQUIRED_COMMON_FIELDS
            )
            if not _optional_string(getattr(self, field_name))
        )
        return {
            "input_kind": self.input_kind,
            "contract_version": self.contract_version,
            "source": self.source,
            "provider_key": self.provider_key,
            "semantic_owner": self.semantic_owner,
            "semantic_branch_id": self.semantic_branch_id,
            "semantic_projection_hash": self.semantic_projection_hash,
            "semantic_projection_name": self.semantic_projection_name,
            "author_id": self.author_id,
            "source_object_instance_graph_commit_id": (
                self.source_object_instance_graph_commit_id
            ),
            "semantic_object_instance_graph_commit_id": (
                self.semantic_object_instance_graph_commit_id
            ),
            "semantic_root_object_instance_graph_commit_id": (
                self.semantic_root_object_instance_graph_commit_id
            ),
            "semantic_package_id": self.semantic_package_id,
            "semantic_package_commit_id": self.semantic_package_commit_id,
            "semantic_root_kind": self.semantic_root_kind,
            "semantic_root_id": self.semantic_root_id,
            "object_instance_graph_identity_id": (
                self.object_instance_graph_identity_id
            ),
            "object_instance_graph_id": self.object_instance_graph_id,
            "root_object_id": self.root_object_id,
            "commit_id": self.commit_id,
            "operation_branch_id": self.operation_branch_id,
            "workspace_root": self.workspace_root,
            "common_inputs_available": not missing_common_fields,
            "missing_common_fields": missing_common_fields,
            "provider_inputs": provider_inputs,
        }


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationRuntimeContextRequest:
    """Request passed to provider-owned runtime context resolvers."""

    provider_key: str
    semantic_owner: str
    workspace_root: Path
    repo_root: Path
    actor_id: UUID | None = None
    manifest_path: Path | None = None
    context: Mapping[str, object] = field(default_factory=dict)
    provider_payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationInput:
    """Provider-neutral materialization input emitted by another semantic package."""

    target_provider_key: str
    target_semantic_owner: str | None
    target_input_key: str
    package_key: str
    input_kind: str | None = None
    input_artifact_family: str | None = None
    input_artifact_role: str | None = None
    input_artifact_path: Path | None = None
    input_artifact_payload: Mapping[str, object] = field(default_factory=dict)
    producer_provider_key: str | None = None
    producer_semantic_owner: str | None = None
    producer_key: str | None = None
    output_key: str | None = None
    runtime_contract_version: str | None = None
    source_package_key: str | None = None
    source_manifest_path: str | None = None
    provider_payload: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "target_provider_key": self.target_provider_key,
            "target_semantic_owner": self.target_semantic_owner,
            "target_input_key": self.target_input_key,
            "package_key": self.package_key,
            "input_kind": self.input_kind,
            "input_artifact_family": self.input_artifact_family,
            "input_artifact_role": self.input_artifact_role,
            "input_artifact_path": (
                self.input_artifact_path.as_posix()
                if self.input_artifact_path is not None
                else None
            ),
            "producer_provider_key": self.producer_provider_key,
            "producer_semantic_owner": self.producer_semantic_owner,
            "producer_key": self.producer_key,
            "output_key": self.output_key,
            "runtime_contract_version": self.runtime_contract_version,
            "source_package_key": self.source_package_key,
            "source_manifest_path": self.source_manifest_path,
            "provider_payload": dict(self.provider_payload),
        }
        if self.input_artifact_payload:
            payload["input_artifact_payload"] = dict(self.input_artifact_payload)
        return payload


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationRequest:
    runtime: Any
    index: Any
    actor_id: UUID | None
    branch_id: UUID
    workspace_root: Path
    manifest_path: Path
    source_code_package_id: UUID | None = None
    context: Mapping[str, object] = field(default_factory=dict)
    code_package_delta: CodePackageDelta | None = None
    semantic_analysis: object | None = None
    change_preview: Mapping[str, object] = field(default_factory=dict)
    execution_context: SemanticPackageMaterializationExecutionContext | None = None
    materialization_input: SemanticPackageMaterializationInput | None = None
    progress_callback: SemanticMaterializationProgressCallback | None = None


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationBundle:
    package_key: str
    manifest_toml_path: Path
    semantic_package_id: UUID
    semantic_root_id: UUID
    semantic_branch_id: UUID | None = None
    semantic_head_commit_id: UUID | None = None
    semantic_object_instance_graph_commit_id: UUID | None = None
    semantic_root_object_instance_graph_commit_id: UUID | None = None
    semantic_root_kind: str | None = None
    semantic_projection_name: str | None = None
    semantic_projection_hash: str | None = None
    source_code_package_id: UUID | None = None
    source_object_instance_graph_commit_id: UUID | None = None
    experience_handle: str | None = None
    profiles: tuple[dict[str, object], ...] = ()
    semantic_packages: tuple[dict[str, object], ...] = ()
    runtime_code_package_refs: tuple[dict[str, object], ...] = ()
    implementation_code_packages: tuple[dict[str, object], ...] = ()
    environment_config_package_dependencies: tuple[dict[str, object], ...] = ()
    api_provider_sets: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class SemanticMaterializationBaselineRef:
    """Provider-neutral baseline identity resolved from durable receipt truth."""

    workspace_revision_id: str
    workspace_materialization_id: str
    workspace_materialization_index: int
    revision_code_package_id: str
    source_code_package_id: str
    source_object_instance_graph_commit_id: str
    revision_code_package_object_instance_graph_commit_id: str
    semantic_package_commit_id: str
    semantic_owner_module: str
    semantic_package_kind: str
    semantic_package_id: str
    contract_version: str = SEMANTIC_PROVIDER_DELTA_BASELINE_REF_CONTRACT_VERSION
    baseline_kind: str = "workspace_semantic_materialization_baseline"
    source: str = "workspace_semantic_package_commit_receipt"
    semantic_package_name: str | None = None
    semantic_contract_module: str | None = None
    semantic_contract_name: str | None = None
    semantic_contract_role: str | None = None
    semantic_contract_provider_key: str | None = None
    semantic_provider_key: str | None = None
    semantic_projection_name: str | None = None
    semantic_projection_hash: str | None = None
    semantic_branch_id: str | None = None
    semantic_object_instance_graph_commit_id: str = ""
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    manifest_path: str | None = None
    manifest_toml_path: str | None = None

    @classmethod
    def model_validate(cls, value: object) -> "SemanticMaterializationBaselineRef":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Semantic materialization baseline ref must be a mapping.")
        return cls(
            contract_version=(
                _optional_string(payload.get("contract_version"))
                or SEMANTIC_PROVIDER_DELTA_BASELINE_REF_CONTRACT_VERSION
            ),
            baseline_kind=(
                _optional_string(payload.get("baseline_kind"))
                or "workspace_semantic_materialization_baseline"
            ),
            source=(
                _optional_string(payload.get("source"))
                or "workspace_semantic_package_commit_receipt"
            ),
            workspace_revision_id=_required_text(payload, "workspace_revision_id"),
            workspace_materialization_id=_required_text(
                payload,
                "workspace_materialization_id",
            ),
            workspace_materialization_index=_nonnegative_int(
                payload.get("workspace_materialization_index")
            ),
            revision_code_package_id=_required_text(
                payload,
                "revision_code_package_id",
            ),
            source_code_package_id=_required_text(payload, "source_code_package_id"),
            source_object_instance_graph_commit_id=_required_text(
                payload,
                "source_object_instance_graph_commit_id",
            ),
            revision_code_package_object_instance_graph_commit_id=_required_text(
                payload,
                "revision_code_package_object_instance_graph_commit_id",
            ),
            semantic_package_commit_id=_required_text(
                payload,
                "semantic_package_commit_id",
            ),
            semantic_owner_module=_required_text(payload, "semantic_owner_module"),
            semantic_package_kind=_required_text(payload, "semantic_package_kind"),
            semantic_package_id=_required_text(payload, "semantic_package_id"),
            semantic_package_name=_optional_string(
                payload.get("semantic_package_name")
            ),
            semantic_contract_module=_optional_string(
                payload.get("semantic_contract_module")
            ),
            semantic_contract_name=_optional_string(
                payload.get("semantic_contract_name")
            ),
            semantic_contract_role=_optional_string(
                payload.get("semantic_contract_role")
            ),
            semantic_contract_provider_key=_optional_string(
                payload.get("semantic_contract_provider_key")
            ),
            semantic_provider_key=_optional_string(
                payload.get("semantic_provider_key")
            ),
            semantic_projection_name=_optional_string(
                payload.get("semantic_projection_name")
            ),
            semantic_projection_hash=_optional_string(
                payload.get("semantic_projection_hash")
            ),
            semantic_branch_id=_optional_string(payload.get("semantic_branch_id")),
            semantic_object_instance_graph_commit_id=_required_text(
                payload,
                "semantic_object_instance_graph_commit_id",
            ),
            semantic_root_kind=_optional_string(payload.get("semantic_root_kind")),
            semantic_root_id=_optional_string(payload.get("semantic_root_id")),
            semantic_root_object_instance_graph_commit_id=_optional_string(
                payload.get("semantic_root_object_instance_graph_commit_id")
            ),
            manifest_path=_optional_string(payload.get("manifest_path")),
            manifest_toml_path=_optional_string(payload.get("manifest_toml_path")),
        )

    def missing_required_fields(self) -> tuple[str, ...]:
        payload = self.model_dump(mode="json")
        return tuple(
            field_name
            for field_name in SEMANTIC_PROVIDER_DELTA_BASELINE_REF_REQUIRED_FIELDS
            if not _optional_string(payload.get(field_name))
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "contract_version": self.contract_version,
            "baseline_kind": self.baseline_kind,
            "source": self.source,
            "workspace_revision_id": self.workspace_revision_id,
            "workspace_materialization_id": self.workspace_materialization_id,
            "workspace_materialization_index": self.workspace_materialization_index,
            "revision_code_package_id": self.revision_code_package_id,
            "source_code_package_id": self.source_code_package_id,
            "source_object_instance_graph_commit_id": (
                self.source_object_instance_graph_commit_id
            ),
            "revision_code_package_object_instance_graph_commit_id": (
                self.revision_code_package_object_instance_graph_commit_id
            ),
            "semantic_package_commit_id": self.semantic_package_commit_id,
            "semantic_owner_module": self.semantic_owner_module,
            "semantic_package_kind": self.semantic_package_kind,
            "semantic_package_id": self.semantic_package_id,
            "semantic_package_name": self.semantic_package_name,
            "semantic_contract_module": self.semantic_contract_module,
            "semantic_contract_name": self.semantic_contract_name,
            "semantic_contract_role": self.semantic_contract_role,
            "semantic_contract_provider_key": self.semantic_contract_provider_key,
            "semantic_provider_key": self.semantic_provider_key,
            "semantic_projection_name": self.semantic_projection_name,
            "semantic_projection_hash": self.semantic_projection_hash,
            "semantic_branch_id": self.semantic_branch_id,
            "semantic_object_instance_graph_commit_id": (
                self.semantic_object_instance_graph_commit_id
            ),
            "semantic_root_kind": self.semantic_root_kind,
            "semantic_root_id": self.semantic_root_id,
            "semantic_root_object_instance_graph_commit_id": (
                self.semantic_root_object_instance_graph_commit_id
            ),
            "manifest_path": self.manifest_path,
            "manifest_toml_path": self.manifest_toml_path,
        }


@dataclass(frozen=True, slots=True)
class SemanticMaterializationBaselineResolution:
    """Provider-neutral baseline resolution envelope produced by Workspace."""

    status: Literal["resolved", "blocked"]
    reason: str
    contract_version: str = SEMANTIC_PROVIDER_DELTA_BASELINE_RESOLUTION_CONTRACT_VERSION
    resolution_kind: Literal["workspace_semantic_materialization_baseline"] = (
        "workspace_semantic_materialization_baseline"
    )
    available: bool = False
    evidence_complete: bool = False
    candidate_count: int = 0
    missing_required_fields: tuple[str, ...] = ()
    package: Mapping[str, object] = field(default_factory=dict)
    semantic_contract: Mapping[str, object] = field(default_factory=dict)
    receipt_resolution_reason: str | None = None
    baseline_ref: SemanticMaterializationBaselineRef | None = None

    @classmethod
    def model_validate(
        cls,
        value: object,
    ) -> "SemanticMaterializationBaselineResolution":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Semantic baseline resolution must be a mapping.")
        status = _required_text(payload, "status")
        if status not in {"resolved", "blocked"}:
            raise ValueError("Semantic baseline resolution status is invalid.")
        status_literal = cast(Literal["resolved", "blocked"], status)
        baseline_ref_payload = payload.get("baseline_ref")
        return cls(
            contract_version=(
                _optional_string(payload.get("contract_version"))
                or SEMANTIC_PROVIDER_DELTA_BASELINE_RESOLUTION_CONTRACT_VERSION
            ),
            resolution_kind="workspace_semantic_materialization_baseline",
            status=status_literal,
            reason=_required_text(payload, "reason"),
            available=payload.get("available") is True,
            evidence_complete=payload.get("evidence_complete") is True,
            candidate_count=_nonnegative_int(payload.get("candidate_count")),
            missing_required_fields=_string_tuple(
                payload.get("missing_required_fields")
            ),
            package=dict(_mapping_payload(payload.get("package")) or {}),
            semantic_contract=dict(
                _mapping_payload(payload.get("semantic_contract")) or {}
            ),
            receipt_resolution_reason=_optional_string(
                payload.get("receipt_resolution_reason")
            ),
            baseline_ref=(
                SemanticMaterializationBaselineRef.model_validate(baseline_ref_payload)
                if baseline_ref_payload is not None
                else None
            ),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "contract_version": self.contract_version,
            "resolution_kind": self.resolution_kind,
            "status": self.status,
            "reason": self.reason,
            "available": self.available,
            "evidence_complete": self.evidence_complete,
            "candidate_count": self.candidate_count,
            "missing_required_fields": list(self.missing_required_fields),
            "package": dict(self.package),
            "semantic_contract": dict(self.semantic_contract),
            "receipt_resolution_reason": self.receipt_resolution_reason,
            "baseline_ref": (
                self.baseline_ref.model_dump(mode="json")
                if self.baseline_ref is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaLaneState:
    """Provider-neutral semantic lane state resolved by Workspace."""

    status: Literal["existing_head", "empty_lane", "ambiguous", "blocked"]
    reason: str
    contract_version: str = SEMANTIC_PROVIDER_DELTA_LANE_STATE_CONTRACT_VERSION
    state_kind: Literal["workspace_provider_delta_lane_state"] = (
        "workspace_provider_delta_lane_state"
    )
    source: str = "workspace.semantic_materialization.lane_state"
    package: Mapping[str, object] = field(default_factory=dict)
    semantic_contract: Mapping[str, object] = field(default_factory=dict)
    baseline_ref: SemanticMaterializationBaselineRef | None = None
    evidence_complete: bool = False
    candidate_count: int = 0
    missing_required_fields: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    semantic_branch_id: str | None = None
    semantic_projection_name: str | None = None
    semantic_projection_hash: str | None = None
    semantic_package_id: str | None = None
    semantic_package_name: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    source_object_instance_graph_commit_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaLaneState":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Provider delta lane state must be a mapping.")
        status = _required_text(payload, "status")
        if status not in {"existing_head", "empty_lane", "ambiguous", "blocked"}:
            raise ValueError("Provider delta lane state status is invalid.")
        baseline_ref_payload = payload.get("baseline_ref")
        baseline_ref = (
            SemanticMaterializationBaselineRef.model_validate(baseline_ref_payload)
            if baseline_ref_payload is not None
            else None
        )
        return cls(
            contract_version=(
                _optional_string(payload.get("contract_version"))
                or SEMANTIC_PROVIDER_DELTA_LANE_STATE_CONTRACT_VERSION
            ),
            state_kind="workspace_provider_delta_lane_state",
            source=(
                _optional_string(payload.get("source"))
                or "workspace.semantic_materialization.lane_state"
            ),
            status=cast(
                Literal["existing_head", "empty_lane", "ambiguous", "blocked"],
                status,
            ),
            reason=_required_text(payload, "reason"),
            package=dict(_mapping_payload(payload.get("package")) or {}),
            semantic_contract=dict(
                _mapping_payload(payload.get("semantic_contract")) or {}
            ),
            baseline_ref=baseline_ref,
            evidence_complete=payload.get("evidence_complete") is True,
            candidate_count=_nonnegative_int(payload.get("candidate_count")),
            missing_required_fields=_string_tuple(
                payload.get("missing_required_fields")
            ),
            blockers=_string_tuple(payload.get("blockers")),
            semantic_branch_id=(
                _optional_string(payload.get("semantic_branch_id"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_branch_id",
                )
            ),
            semantic_projection_name=(
                _optional_string(payload.get("semantic_projection_name"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_projection_name",
                )
            ),
            semantic_projection_hash=(
                _optional_string(payload.get("semantic_projection_hash"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_projection_hash",
                )
            ),
            semantic_package_id=(
                _optional_string(payload.get("semantic_package_id"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_package_id",
                )
            ),
            semantic_package_name=(
                _optional_string(payload.get("semantic_package_name"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_package_name",
                )
            ),
            semantic_root_kind=(
                _optional_string(payload.get("semantic_root_kind"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_root_kind",
                )
            ),
            semantic_root_id=(
                _optional_string(payload.get("semantic_root_id"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_root_id",
                )
            ),
            source_object_instance_graph_commit_id=(
                _optional_string(payload.get("source_object_instance_graph_commit_id"))
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="source_object_instance_graph_commit_id",
                )
            ),
            semantic_object_instance_graph_commit_id=(
                _optional_string(
                    payload.get("semantic_object_instance_graph_commit_id")
                )
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_object_instance_graph_commit_id",
                )
            ),
            semantic_root_object_instance_graph_commit_id=(
                _optional_string(
                    payload.get("semantic_root_object_instance_graph_commit_id")
                )
                or _baseline_ref_text(
                    baseline_ref=baseline_ref,
                    field_name="semantic_root_object_instance_graph_commit_id",
                )
            ),
            metadata=dict(_mapping_payload(payload.get("metadata")) or {}),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "contract_version": self.contract_version,
            "state_kind": self.state_kind,
            "source": self.source,
            "status": self.status,
            "reason": self.reason,
            "package": dict(self.package),
            "semantic_contract": dict(self.semantic_contract),
            "baseline_ref": (
                self.baseline_ref.model_dump(mode="json")
                if self.baseline_ref is not None
                else None
            ),
            "evidence_complete": self.evidence_complete,
            "candidate_count": self.candidate_count,
            "missing_required_fields": list(self.missing_required_fields),
            "blockers": list(self.blockers),
            "semantic_branch_id": self.semantic_branch_id,
            "semantic_projection_name": self.semantic_projection_name,
            "semantic_projection_hash": self.semantic_projection_hash,
            "semantic_package_id": self.semantic_package_id,
            "semantic_package_name": self.semantic_package_name,
            "semantic_root_kind": self.semantic_root_kind,
            "semantic_root_id": self.semantic_root_id,
            "source_object_instance_graph_commit_id": (
                self.source_object_instance_graph_commit_id
            ),
            "semantic_object_instance_graph_commit_id": (
                self.semantic_object_instance_graph_commit_id
            ),
            "semantic_root_object_instance_graph_commit_id": (
                self.semantic_root_object_instance_graph_commit_id
            ),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaChangedPathHint:
    path: str
    change_kind: str | None = None
    classification: str | None = None
    package_relative_path: str | None = None
    language: str | None = None
    is_structural: bool | None = None
    path_role: str | None = None

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaChangedPathHint":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Provider delta changed path hint must be a mapping.")
        return cls(
            path=_required_text(payload, "path"),
            change_kind=_optional_string(payload.get("change_kind")),
            classification=_optional_string(payload.get("classification")),
            package_relative_path=_optional_string(
                payload.get("package_relative_path")
            ),
            language=_optional_string(payload.get("language")),
            is_structural=_optional_bool(payload.get("is_structural")),
            path_role=_optional_string(payload.get("path_role")),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "path": self.path,
            "change_kind": self.change_kind,
            "classification": self.classification,
            "package_relative_path": self.package_relative_path,
            "language": self.language,
            "is_structural": self.is_structural,
            "path_role": self.path_role,
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaCauseHints:
    changed_path_count: int = 0
    source_owned_path_count: int = 0
    generated_fallout_path_count: int = 0
    changed_path_classifications: Mapping[str, int] = field(default_factory=dict)
    top_changed_paths: tuple[SemanticProviderDeltaChangedPathHint, ...] = ()
    top_changed_path_limit: int = 0
    current_delta_fingerprint_available: bool = False
    previous_delta_fingerprint_available: bool = False

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaCauseHints":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value) or {}
        return cls(
            changed_path_count=_nonnegative_int(payload.get("changed_path_count")),
            source_owned_path_count=_nonnegative_int(
                payload.get("source_owned_path_count")
            ),
            generated_fallout_path_count=_nonnegative_int(
                payload.get("generated_fallout_path_count")
            ),
            changed_path_classifications=_string_int_mapping(
                payload.get("changed_path_classifications")
            ),
            top_changed_paths=tuple(
                SemanticProviderDeltaChangedPathHint.model_validate(item)
                for item in _sequence(payload.get("top_changed_paths"))
            ),
            top_changed_path_limit=_nonnegative_int(
                payload.get("top_changed_path_limit")
            ),
            current_delta_fingerprint_available=(
                payload.get("current_delta_fingerprint_available") is True
            ),
            previous_delta_fingerprint_available=(
                payload.get("previous_delta_fingerprint_available") is True
            ),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "changed_path_count": self.changed_path_count,
            "source_owned_path_count": self.source_owned_path_count,
            "generated_fallout_path_count": self.generated_fallout_path_count,
            "changed_path_classifications": dict(
                sorted(self.changed_path_classifications.items())
            ),
            "top_changed_paths": [
                path.model_dump(mode="json") for path in self.top_changed_paths
            ],
            "top_changed_path_limit": self.top_changed_path_limit,
            "current_delta_fingerprint_available": (
                self.current_delta_fingerprint_available
            ),
            "previous_delta_fingerprint_available": (
                self.previous_delta_fingerprint_available
            ),
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaPackageIdentity:
    package_name: str
    manifest_path: str
    workspace_manifest_kind: str | None = None
    source_code_package_id: str | None = None

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaPackageIdentity":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Provider delta package identity must be a mapping.")
        return cls(
            package_name=_required_text(payload, "package_name"),
            workspace_manifest_kind=_optional_string(
                payload.get("workspace_manifest_kind")
            ),
            manifest_path=_required_text(payload, "manifest_path"),
            source_code_package_id=_optional_string(
                payload.get("source_code_package_id")
            ),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "package_name": self.package_name,
            "workspace_manifest_kind": self.workspace_manifest_kind,
            "manifest_path": self.manifest_path,
            "source_code_package_id": self.source_code_package_id,
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaSemanticContract:
    module: str
    provider_key: str
    role: str
    name: str

    @classmethod
    def model_validate(
        cls,
        value: object,
    ) -> "SemanticProviderDeltaSemanticContract":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Provider delta semantic contract must be a mapping.")
        return cls(
            module=_required_text(payload, "module"),
            provider_key=_required_text(payload, "provider_key"),
            role=_required_text(payload, "role"),
            name=_required_text(payload, "name"),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "module": self.module,
            "provider_key": self.provider_key,
            "role": self.role,
            "name": self.name,
        }


SemanticProviderDeltaRequestRejectionReason = Literal[
    "delta_fingerprint_changed",
    "provider_evidence_changed",
]


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaRequest:
    package: SemanticProviderDeltaPackageIdentity
    semantic_contract: SemanticProviderDeltaSemanticContract
    current_delta_fingerprint: str
    code_package_delta: CodePackageDelta | None = None
    contract_version: str = SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION
    provider_delta_request_key: str = ""
    requested_mode: Literal["delta"] = "delta"
    rejection_reason: SemanticProviderDeltaRequestRejectionReason = (
        "delta_fingerprint_changed"
    )
    delta_cause_hints: SemanticProviderDeltaCauseHints = field(
        default_factory=SemanticProviderDeltaCauseHints
    )
    previous_materialization_evidence: Mapping[str, object] = field(
        default_factory=dict
    )
    baseline_ref: SemanticMaterializationBaselineRef | None = None
    provider_delta_lane_state: SemanticProviderDeltaLaneState | None = None
    baseline_source_object_instance_graph_commit_id: str | None = None
    baseline_semantic_object_instance_graph_commit_id: str | None = None
    baseline_semantic_root_object_instance_graph_commit_id: str | None = None

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaRequest":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Provider delta request must be a mapping.")
        baseline_ref = _semantic_provider_delta_baseline_ref_from_request_payload(
            payload
        )
        lane_state = _semantic_provider_delta_lane_state_from_request_payload(payload)
        normalized = _semantic_provider_delta_request_payload_with_baseline_refs(
            payload=payload,
            baseline_ref=baseline_ref,
        )
        package = SemanticProviderDeltaPackageIdentity.model_validate(
            normalized.get("package")
        )
        semantic_contract = SemanticProviderDeltaSemanticContract.model_validate(
            normalized.get("semantic_contract")
        )
        current_delta_fingerprint = _required_text(
            normalized,
            "current_delta_fingerprint",
        )
        raw_code_package_delta = normalized.get("code_package_delta")
        code_package_delta = (
            None
            if raw_code_package_delta is None
            else CodePackageDelta.model_validate(raw_code_package_delta)
        )
        request_key = build_semantic_provider_delta_request_key(
            package=package,
            semantic_contract=semantic_contract,
            current_delta_fingerprint=current_delta_fingerprint,
            baseline_source_object_instance_graph_commit_id=_optional_string(
                normalized.get("baseline_source_object_instance_graph_commit_id")
            ),
            baseline_semantic_object_instance_graph_commit_id=_optional_string(
                normalized.get("baseline_semantic_object_instance_graph_commit_id")
            ),
            baseline_semantic_root_object_instance_graph_commit_id=_optional_string(
                normalized.get("baseline_semantic_root_object_instance_graph_commit_id")
            ),
            baseline_ref=baseline_ref,
            provider_delta_lane_state=lane_state,
        )
        existing_key = _optional_string(normalized.get("provider_delta_request_key"))
        if existing_key is not None and existing_key != request_key:
            raise ValueError(
                "Provider delta request key does not match package, semantic "
                "contract, current delta fingerprint, and baseline identity."
            )
        rejection_reason = _semantic_provider_delta_request_rejection_reason(
            normalized.get("rejection_reason")
        )
        return cls(
            contract_version=(
                _optional_string(normalized.get("contract_version"))
                or SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION
            ),
            provider_delta_request_key=existing_key or request_key,
            requested_mode="delta",
            rejection_reason=rejection_reason,
            package=package,
            semantic_contract=semantic_contract,
            current_delta_fingerprint=current_delta_fingerprint,
            code_package_delta=code_package_delta,
            delta_cause_hints=SemanticProviderDeltaCauseHints.model_validate(
                normalized.get("delta_cause_hints")
            ),
            previous_materialization_evidence=dict(
                _mapping_payload(normalized.get("previous_materialization_evidence"))
                or {}
            ),
            baseline_ref=baseline_ref,
            provider_delta_lane_state=lane_state,
            baseline_source_object_instance_graph_commit_id=_optional_string(
                normalized.get("baseline_source_object_instance_graph_commit_id")
            ),
            baseline_semantic_object_instance_graph_commit_id=_optional_string(
                normalized.get("baseline_semantic_object_instance_graph_commit_id")
            ),
            baseline_semantic_root_object_instance_graph_commit_id=_optional_string(
                normalized.get("baseline_semantic_root_object_instance_graph_commit_id")
            ),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "contract_version": self.contract_version,
            "provider_delta_request_key": self.provider_delta_request_key,
            "requested_mode": self.requested_mode,
            "rejection_reason": self.rejection_reason,
            "package": self.package.model_dump(mode="json"),
            "semantic_contract": self.semantic_contract.model_dump(mode="json"),
            "current_delta_fingerprint": self.current_delta_fingerprint,
            "code_package_delta": (
                self.code_package_delta.model_dump(mode="json")
                if self.code_package_delta is not None
                else None
            ),
            "delta_cause_hints": self.delta_cause_hints.model_dump(mode="json"),
            "previous_materialization_evidence": dict(
                self.previous_materialization_evidence
            ),
            "baseline_ref": (
                self.baseline_ref.model_dump(mode="json")
                if self.baseline_ref is not None
                else None
            ),
            "provider_delta_lane_state": (
                self.provider_delta_lane_state.model_dump(mode="json")
                if self.provider_delta_lane_state is not None
                else None
            ),
            "baseline_source_object_instance_graph_commit_id": (
                self.baseline_source_object_instance_graph_commit_id
            ),
            "baseline_semantic_object_instance_graph_commit_id": (
                self.baseline_semantic_object_instance_graph_commit_id
            ),
            "baseline_semantic_root_object_instance_graph_commit_id": (
                self.baseline_semantic_root_object_instance_graph_commit_id
            ),
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaResult:
    status: Literal["succeeded", "failed", "fallback_required"]
    package: SemanticProviderDeltaPackageIdentity
    semantic_contract: SemanticProviderDeltaSemanticContract
    current_delta_fingerprint: str
    contract_version: str = SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
    applied_semantic_keys: tuple[str, ...] = ()
    skipped_semantic_keys: tuple[str, ...] = ()
    stale_semantic_keys: tuple[str, ...] = ()
    implementation_required: bool = False
    implementation_work_items: tuple[dict[str, object], ...] = ()
    fallback_reason: str | None = None
    commit_ref_contract: Mapping[str, object] = field(default_factory=dict)
    bundle_package: Mapping[str, object] = field(default_factory=dict)
    bundle_packages: tuple[dict[str, object], ...] = ()
    details: Mapping[str, object] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaResult":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Provider delta result must be a mapping.")
        status = _required_text(payload, "status")
        if status not in {"succeeded", "failed", "fallback_required"}:
            raise ValueError("Provider delta result status is invalid.")
        status_literal = cast(
            Literal["succeeded", "failed", "fallback_required"],
            status,
        )
        return cls(
            contract_version=(
                _optional_string(payload.get("contract_version"))
                or SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
            ),
            status=status_literal,
            package=SemanticProviderDeltaPackageIdentity.model_validate(
                payload.get("package")
            ),
            semantic_contract=SemanticProviderDeltaSemanticContract.model_validate(
                payload.get("semantic_contract")
            ),
            current_delta_fingerprint=_required_text(
                payload,
                "current_delta_fingerprint",
            ),
            applied_semantic_keys=_string_tuple(payload.get("applied_semantic_keys")),
            skipped_semantic_keys=_string_tuple(payload.get("skipped_semantic_keys")),
            stale_semantic_keys=_string_tuple(payload.get("stale_semantic_keys")),
            implementation_required=payload.get("implementation_required") is True,
            implementation_work_items=tuple(
                dict(item)
                for item in _sequence(payload.get("implementation_work_items"))
                if isinstance(item, Mapping)
            ),
            fallback_reason=_optional_string(payload.get("fallback_reason")),
            commit_ref_contract=dict(
                _mapping_payload(payload.get("commit_ref_contract")) or {}
            ),
            bundle_package=dict(_mapping_payload(payload.get("bundle_package")) or {}),
            bundle_packages=tuple(
                dict(item)
                for item in _sequence(payload.get("bundle_packages"))
                if isinstance(item, Mapping)
            ),
            details=dict(_mapping_payload(payload.get("details")) or {}),
            error=_optional_string(payload.get("error")),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "contract_version": self.contract_version,
            "status": self.status,
            "package": self.package.model_dump(mode="json"),
            "semantic_contract": self.semantic_contract.model_dump(mode="json"),
            "current_delta_fingerprint": self.current_delta_fingerprint,
            "applied_semantic_keys": list(self.applied_semantic_keys),
            "skipped_semantic_keys": list(self.skipped_semantic_keys),
            "stale_semantic_keys": list(self.stale_semantic_keys),
            "implementation_required": self.implementation_required,
            "implementation_work_items": [
                dict(item) for item in self.implementation_work_items
            ],
            "fallback_reason": self.fallback_reason,
            "commit_ref_contract": dict(self.commit_ref_contract),
            "bundle_package": dict(self.bundle_package),
            "bundle_packages": [dict(item) for item in self.bundle_packages],
            "details": dict(self.details),
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaRequestBundle:
    contract_version: str = SEMANTIC_PROVIDER_DELTA_REQUEST_BUNDLE_CONTRACT_VERSION
    bundle_kind: Literal["provider_delta_request_bundle"] = (
        "provider_delta_request_bundle"
    )
    request_contract_version: str = SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION
    adapter_contract_version: str = SEMANTIC_PROVIDER_DELTA_ADAPTER_CONTRACT_VERSION
    result_contract_version: str = SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
    production_execution_wired: bool = False
    request_count: int = 0
    provider_delta_request_keys: tuple[str, ...] = ()
    requests: tuple[SemanticProviderDeltaRequest, ...] = ()
    classifications: tuple[Mapping[str, object], ...] = ()
    adapter_plans: tuple[Mapping[str, object], ...] = ()
    dry_run_diagnostic_skeletons: tuple[Mapping[str, object], ...] = ()

    @classmethod
    def model_validate(cls, value: object) -> "SemanticProviderDeltaRequestBundle":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            raise ValueError("Provider delta request bundle must be a mapping.")
        requests = tuple(
            SemanticProviderDeltaRequest.model_validate(item)
            for item in _sequence(payload.get("requests"))
        )
        request_keys = tuple(request.provider_delta_request_key for request in requests)
        return cls(
            contract_version=(
                _optional_string(payload.get("contract_version"))
                or SEMANTIC_PROVIDER_DELTA_REQUEST_BUNDLE_CONTRACT_VERSION
            ),
            request_contract_version=(
                _optional_string(payload.get("request_contract_version"))
                or SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION
            ),
            adapter_contract_version=(
                _optional_string(payload.get("adapter_contract_version"))
                or SEMANTIC_PROVIDER_DELTA_ADAPTER_CONTRACT_VERSION
            ),
            result_contract_version=(
                _optional_string(payload.get("result_contract_version"))
                or SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
            ),
            production_execution_wired=(
                payload.get("production_execution_wired") is True
            ),
            request_count=len(requests),
            provider_delta_request_keys=request_keys,
            requests=requests,
            classifications=tuple(
                dict(item)
                for item in _sequence(payload.get("classifications"))
                if isinstance(item, Mapping)
            ),
            adapter_plans=tuple(
                dict(item)
                for item in _sequence(payload.get("adapter_plans"))
                if isinstance(item, Mapping)
            ),
            dry_run_diagnostic_skeletons=tuple(
                dict(item)
                for item in _sequence(payload.get("dry_run_diagnostic_skeletons"))
                if isinstance(item, Mapping)
            ),
        )

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return {
            "bundle_kind": self.bundle_kind,
            "contract_version": self.contract_version,
            "request_contract_version": self.request_contract_version,
            "adapter_contract_version": self.adapter_contract_version,
            "result_contract_version": self.result_contract_version,
            "production_execution_wired": self.production_execution_wired,
            "request_count": self.request_count,
            "provider_delta_request_keys": list(self.provider_delta_request_keys),
            "requests": [request.model_dump(mode="json") for request in self.requests],
            "classifications": [dict(item) for item in self.classifications],
            "adapter_plans": [dict(item) for item in self.adapter_plans],
            "dry_run_diagnostic_skeletons": [
                dict(item) for item in self.dry_run_diagnostic_skeletons
            ],
        }


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaHeadRefs:
    head_ref_status: Literal[
        "head_refs_unavailable",
        "head_refs_partial",
        "head_refs_available",
    ] = "head_refs_unavailable"
    source_object_instance_graph_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_projection_name: str | None = None
    semantic_package_id: str | None = None
    semantic_package_commit_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, value: object) -> "SemanticProviderDeltaHeadRefs":
        if isinstance(value, cls):
            return value
        payload = _mapping_payload(value)
        if payload is None:
            return cls()
        details = payload.get("details")
        return cls(
            head_ref_status=_semantic_provider_delta_head_ref_status(
                payload.get("head_ref_status")
            ),
            source_object_instance_graph_commit_id=_optional_string(
                payload.get("source_object_instance_graph_commit_id")
            ),
            semantic_branch_id=_optional_string(payload.get("semantic_branch_id")),
            semantic_projection_name=_optional_string(
                payload.get("semantic_projection_name")
            ),
            semantic_package_id=_optional_string(payload.get("semantic_package_id")),
            semantic_package_commit_id=_optional_string(
                payload.get("semantic_package_commit_id")
            ),
            semantic_object_instance_graph_commit_id=_optional_string(
                payload.get("semantic_object_instance_graph_commit_id")
            ),
            semantic_root_object_instance_graph_commit_id=_optional_string(
                payload.get("semantic_root_object_instance_graph_commit_id")
            ),
            details=dict(details) if isinstance(details, Mapping) else {},
        )

    def evidence_payload(self) -> dict[str, object]:
        return {
            "head_ref_status": self.head_ref_status,
            "source_object_instance_graph_commit_id": (
                self.source_object_instance_graph_commit_id
            ),
            "semantic_branch_id": self.semantic_branch_id,
            "semantic_projection_name": self.semantic_projection_name,
            "semantic_package_id": self.semantic_package_id,
            "semantic_package_commit_id": self.semantic_package_commit_id,
            "semantic_object_instance_graph_commit_id": (
                self.semantic_object_instance_graph_commit_id
            ),
            "semantic_root_object_instance_graph_commit_id": (
                self.semantic_root_object_instance_graph_commit_id
            ),
            "details": dict(self.details),
        }

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return self.evidence_payload()


@dataclass(frozen=True, slots=True)
class SemanticProviderDeltaHeadMovePlan:
    payload: Mapping[str, object]

    def evidence_payload(self) -> dict[str, object]:
        return dict(self.payload)

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        _ = mode
        return self.evidence_payload()


def build_semantic_provider_delta_head_move_plan(
    *,
    request: object,
    semantic_dirty_diff: Mapping[str, object],
    head_refs: SemanticProviderDeltaHeadRefs | Mapping[str, object] | None = None,
) -> SemanticProviderDeltaHeadMovePlan:
    request_payload = _mapping_payload(request) or _object_payload(request)
    package = _mapping_payload(request_payload.get("package")) or {}
    semantic_contract = _mapping_payload(request_payload.get("semantic_contract")) or {}
    current_delta_fingerprint = (
        _optional_string(request_payload.get("current_delta_fingerprint")) or ""
    )
    dirty_diff_fingerprint = _optional_string(
        semantic_dirty_diff.get("current_delta_fingerprint")
    )
    if (
        dirty_diff_fingerprint is not None
        and dirty_diff_fingerprint != current_delta_fingerprint
    ):
        raise ValueError(
            "Provider delta head move dirty diff fingerprint does not match request."
        )
    dirty_diff_status = _optional_string(semantic_dirty_diff.get("status"))
    dirty_entries = tuple(
        _semantic_provider_delta_head_move_dirty_entry(entry)
        for entry in _sequence(semantic_dirty_diff.get("semantic_dirty_entries"))
        if isinstance(entry, Mapping)
    )
    baseline_index_status = _optional_string(
        semantic_dirty_diff.get("baseline_index_compare_status")
    )
    baseline_index_compared = (
        baseline_index_status == "baseline_index_compared"
        and semantic_dirty_diff.get("baseline_index_compare_available") is True
    )
    dirty_diff_blocked = (
        dirty_diff_status == "semantic_dirty_diff_blocked"
        or semantic_dirty_diff.get("blocked") is True
        or semantic_dirty_diff.get("available") is False
    )
    blocked = dirty_diff_blocked or not baseline_index_compared
    planned_operations = (
        ()
        if blocked
        else tuple(
            operation
            for operation in (
                _semantic_provider_delta_head_move_operation_from_dirty_entry(entry)
                for entry in dirty_entries
            )
            if operation is not None
        )
    )
    normalized_head_refs = SemanticProviderDeltaHeadRefs.from_payload(head_refs)
    if normalized_head_refs.head_ref_status == "head_refs_available" and not blocked:
        status = "head_move_applied"
    elif blocked:
        status = "head_move_plan_blocked"
    else:
        status = "head_move_plan_ready"
    reason = _semantic_provider_delta_head_move_reason(
        semantic_dirty_diff=semantic_dirty_diff,
        dirty_diff_blocked=dirty_diff_blocked,
        baseline_index_compared=baseline_index_compared,
    )
    baseline_ref = _mapping_payload(request_payload.get("baseline_ref"))
    payload: dict[str, object] = {
        "plan_kind": "workspace_provider_delta_head_move",
        "contract_version": SEMANTIC_PROVIDER_DELTA_HEAD_MOVE_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "provider_delta_request_key": (
            _optional_string(request_payload.get("provider_delta_request_key"))
            or _semantic_provider_delta_request_key(
                package=package,
                semantic_contract=semantic_contract,
                current_delta_fingerprint=current_delta_fingerprint,
                request_payload=request_payload,
                baseline_ref=baseline_ref,
            )
        ),
        "package": dict(package),
        "semantic_contract": dict(semantic_contract),
        "current_delta_fingerprint": current_delta_fingerprint,
        "baseline_identity_source": _optional_string(
            semantic_dirty_diff.get("baseline_identity_source")
        )
        or "workspace.baseline_ref",
        "baseline_ref": dict(baseline_ref) if baseline_ref is not None else None,
        "baseline_commit_refs": (
            _semantic_provider_delta_head_move_baseline_commit_refs(
                request=request_payload,
                semantic_dirty_diff=semantic_dirty_diff,
            )
        ),
        "baseline_hydration_status": _optional_string(
            semantic_dirty_diff.get("baseline_hydration_status")
        ),
        "baseline_hydration_reason": _optional_string(
            semantic_dirty_diff.get("baseline_hydration_reason")
        ),
        "baseline_semantic_object_index_available": (
            semantic_dirty_diff.get("baseline_semantic_object_index_available") is True
        ),
        "baseline_semantic_object_index_status": _optional_string(
            semantic_dirty_diff.get("baseline_semantic_object_index_status")
        ),
        "baseline_semantic_object_index_count": _nonnegative_int(
            semantic_dirty_diff.get("baseline_semantic_object_index_count")
        ),
        "baseline_index_compare_available": baseline_index_compared,
        "baseline_index_compare_status": baseline_index_status,
        "baseline_index_compare_reason": _optional_string(
            semantic_dirty_diff.get("baseline_index_compare_reason")
        ),
        "semantic_dirty_diff_status": dirty_diff_status,
        "semantic_dirty_diff_reason": _optional_string(
            semantic_dirty_diff.get("reason")
        ),
        "dirty_entry_count": len(dirty_entries),
        "dirty_operation_counts": _string_int_mapping(
            semantic_dirty_diff.get("dirty_operation_counts")
        ),
        "baseline_compare_operation_counts": _string_int_mapping(
            semantic_dirty_diff.get("baseline_compare_operation_counts")
        ),
        "semantic_dirty_entries": list(dirty_entries),
        "planned_operation_count": len(planned_operations),
        "planned_operations": list(planned_operations),
        "head_refs": normalized_head_refs.evidence_payload(),
        "available": not blocked,
        "blocked": blocked,
        "blocked_status": _semantic_provider_delta_head_move_blocked_status(
            semantic_dirty_diff_status=dirty_diff_status,
            baseline_index_compare_status=baseline_index_status,
            dirty_diff_blocked=dirty_diff_blocked,
            baseline_index_compared=baseline_index_compared,
        ),
        "blocked_reason": reason if blocked else None,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }
    return SemanticProviderDeltaHeadMovePlan(payload=payload)


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationEmittedPackageOutput:
    """Provider result for a generated semantic package materialization request."""

    producer_provider_key: str
    producer_semantic_owner: str
    producer_key: str
    output_key: str
    target_provider_key: str
    target_input_key: str
    package_key: str
    target_semantic_owner: str | None = None
    target_package_family: str | None = None
    target_semantic_kind: str | None = None
    input_artifact_producer_key: str | None = None
    input_artifact_output_key: str | None = None
    input_artifact_family: str | None = None
    input_artifact_path: Path | None = None
    input_artifact_payload: Mapping[str, object] = field(default_factory=dict)
    runtime_contract_version: str | None = None
    source_package_key: str | None = None
    source_manifest_path: str | None = None
    provider_payload: Mapping[str, object] = field(default_factory=dict)

    def evidence_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "producer_provider_key": self.producer_provider_key,
            "producer_semantic_owner": self.producer_semantic_owner,
            "producer_key": self.producer_key,
            "output_key": self.output_key,
            "target_provider_key": self.target_provider_key,
            "target_semantic_owner": self.target_semantic_owner,
            "target_input_key": self.target_input_key,
            "target_package_family": self.target_package_family,
            "target_semantic_kind": self.target_semantic_kind,
            "package_key": self.package_key,
            "input_artifact_producer_key": self.input_artifact_producer_key,
            "input_artifact_output_key": self.input_artifact_output_key,
            "input_artifact_family": self.input_artifact_family,
            "input_artifact_path": (
                self.input_artifact_path.as_posix()
                if self.input_artifact_path is not None
                else None
            ),
            "runtime_contract_version": self.runtime_contract_version,
            "source_package_key": self.source_package_key,
            "source_manifest_path": self.source_manifest_path,
            "provider_payload": dict(self.provider_payload),
        }
        if self.input_artifact_payload:
            payload["input_artifact_payload"] = dict(self.input_artifact_payload)
        return payload


@dataclass(frozen=True, slots=True)
class SemanticPackageImplementationWorkItem:
    work_item_id: str
    title: str
    reason: str
    file_path: str | None = None
    symbol: str | None = None
    action: str = "edit"
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SemanticPackageMaterializationResult:
    details: Mapping[str, object]
    bundle_packages: tuple[SemanticPackageMaterializationBundle, ...]
    mode: SemanticPackageMaterializationMode = "full_rebuild"
    affected_semantic_keys: tuple[str, ...] = ()
    applied_semantic_keys: tuple[str, ...] = ()
    skipped_semantic_keys: tuple[str, ...] = ()
    stale_semantic_keys: tuple[str, ...] = ()
    implementation_required: bool = False
    implementation_work_items: tuple[SemanticPackageImplementationWorkItem, ...] = ()
    semantic_function_call_plans: tuple[SemanticCapabilityFunctionCallPlan, ...] = ()
    emitted_package_outputs: tuple[
        SemanticPackageMaterializationEmittedPackageOutput,
        ...,
    ] = ()
    fallback_reason: str | None = None
    commit_id: UUID | None = None
    head_commit_id: UUID | None = None
    semantic_packages: tuple[object, ...] = ()
    semantic_object_config_graphs: tuple[object, ...] = ()
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] = field(
        default_factory=dict
    )
    api_endpoint_catalog: Mapping[str, Mapping[str, tuple[str, ...]]] = field(
        default_factory=dict
    )
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID] = field(
        default_factory=dict
    )


def _normalized_string_map(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, str] = {}
    for key, raw_value in value.items():
        clean_key = str(key).strip()
        clean_value = str(raw_value).strip()
        if clean_key and clean_value:
            normalized[clean_key] = clean_value
    return normalized


def _semantic_provider_delta_head_move_dirty_entry(
    entry: Mapping[object, object],
) -> dict[str, object]:
    semantic_key = _optional_string(entry.get("semantic_key")) or _optional_string(
        entry.get("entry_key")
    )
    if semantic_key is None:
        raise ValueError("Provider delta dirty entry is missing semantic_key.")
    dirty_operation = _optional_string(entry.get("dirty_operation"))
    baseline_compare_operation = _optional_string(
        entry.get("baseline_compare_operation")
    )
    operation_family = _semantic_provider_delta_head_move_operation_family(
        baseline_compare_operation or dirty_operation
    )
    return {
        "entry_kind": "workspace_provider_delta_head_move_dirty_entry",
        "semantic_key": semantic_key,
        "operation_family": operation_family,
        "entry_key": _optional_string(entry.get("entry_key")),
        "source_delta_key": _optional_string(entry.get("source_delta_key")),
        "provider_entry_kind": _optional_string(entry.get("entry_kind")),
        "provider_dirty_operation": dirty_operation,
        "semantic_subject_type": _optional_string(entry.get("semantic_subject_type")),
        "ontology_subject_kind": _optional_string(entry.get("ontology_subject_kind")),
        "baseline_compare_status": _optional_string(
            entry.get("baseline_compare_status")
        ),
        "baseline_compare_operation": baseline_compare_operation,
        "baseline_object_matched": _optional_bool(entry.get("baseline_object_matched")),
        "baseline_object_id": _optional_string(entry.get("baseline_object_id")),
        "baseline_object_kind": _optional_string(entry.get("baseline_object_kind")),
        "baseline_object_instance_graph_commit_id": _optional_string(
            entry.get("baseline_object_instance_graph_commit_id")
        ),
        "target_semantic_object_id": _optional_string(
            entry.get("target_semantic_object_id")
        ),
        "source_refs": _mapping_list(entry.get("source_refs")),
        "provider_payload": {str(key): value for key, value in entry.items()},
    }


def _semantic_provider_delta_head_move_operation_from_dirty_entry(
    entry: Mapping[str, object],
) -> dict[str, object] | None:
    operation_family = _optional_string(entry.get("operation_family"))
    if operation_family not in {"create", "update", "delete"}:
        return None
    return {
        "operation_kind": "workspace_provider_delta_head_move_operation",
        "semantic_key": entry["semantic_key"],
        "operation_family": operation_family,
        "provider_dirty_operation": entry.get("provider_dirty_operation"),
        "source_entry_key": entry.get("entry_key"),
        "semantic_subject_type": entry.get("semantic_subject_type"),
        "ontology_subject_kind": entry.get("ontology_subject_kind"),
        "baseline_object_id": entry.get("baseline_object_id"),
        "baseline_object_kind": entry.get("baseline_object_kind"),
        "baseline_object_instance_graph_commit_id": (
            entry.get("baseline_object_instance_graph_commit_id")
        ),
        "target_semantic_object_id": entry.get("target_semantic_object_id"),
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
    }


def _semantic_provider_delta_head_move_operation_family(
    raw_operation: str | None,
) -> SemanticProviderDeltaHeadMoveOperationFamily:
    if raw_operation is None:
        return "unknown"
    operation = raw_operation.strip().lower()
    if operation == "blocked" or operation.endswith("_blocked"):
        return "blocked"
    if operation == "noop" or operation.endswith("_noop"):
        return "noop"
    if operation == "upsert" or operation.endswith("_upsert"):
        return "upsert"
    if operation == "create" or operation.endswith("_create"):
        return "create"
    if operation == "update" or operation.endswith("_update"):
        return "update"
    if operation == "delete" or operation.endswith("_delete"):
        return "delete"
    return "unknown"


def _semantic_provider_delta_head_move_reason(
    *,
    semantic_dirty_diff: Mapping[str, object],
    dirty_diff_blocked: bool,
    baseline_index_compared: bool,
) -> str:
    if dirty_diff_blocked:
        return (
            _optional_string(semantic_dirty_diff.get("reason"))
            or "provider_delta_dirty_diff_blocked"
        )
    if not baseline_index_compared:
        return (
            _optional_string(semantic_dirty_diff.get("baseline_index_compare_reason"))
            or _optional_string(
                semantic_dirty_diff.get("baseline_index_compare_status")
            )
            or "baseline_index_comparison_required"
        )
    return (
        _optional_string(semantic_dirty_diff.get("reason"))
        or "provider_delta_head_move_plan_ready"
    )


def _semantic_provider_delta_head_move_blocked_status(
    *,
    semantic_dirty_diff_status: str | None,
    baseline_index_compare_status: str | None,
    dirty_diff_blocked: bool,
    baseline_index_compared: bool,
) -> str | None:
    if dirty_diff_blocked:
        return semantic_dirty_diff_status or "semantic_dirty_diff_blocked"
    if not baseline_index_compared:
        return baseline_index_compare_status or "baseline_index_comparison_required"
    return None


def _semantic_provider_delta_head_move_baseline_commit_refs(
    *,
    request: Mapping[str, object],
    semantic_dirty_diff: Mapping[str, object],
) -> dict[str, object]:
    refs: dict[str, object] = {}
    for field_name, request_field in (
        (
            "source_object_instance_graph_commit_id",
            "baseline_source_object_instance_graph_commit_id",
        ),
        (
            "semantic_object_instance_graph_commit_id",
            "baseline_semantic_object_instance_graph_commit_id",
        ),
        (
            "semantic_root_object_instance_graph_commit_id",
            "baseline_semantic_root_object_instance_graph_commit_id",
        ),
    ):
        value = _optional_string(request.get(request_field)) or _optional_string(
            semantic_dirty_diff.get(f"baseline_{field_name}")
        )
        if value is not None:
            refs[field_name] = value
    return refs


def build_semantic_provider_delta_request_key(
    *,
    package: SemanticProviderDeltaPackageIdentity | Mapping[str, object] | object,
    semantic_contract: (
        SemanticProviderDeltaSemanticContract | Mapping[str, object] | object
    ),
    current_delta_fingerprint: str,
    baseline_source_object_instance_graph_commit_id: str | None = None,
    baseline_semantic_object_instance_graph_commit_id: str | None = None,
    baseline_semantic_root_object_instance_graph_commit_id: str | None = None,
    baseline_ref: (
        SemanticMaterializationBaselineRef | Mapping[str, object] | None
    ) = None,
    provider_delta_lane_state: (
        SemanticProviderDeltaLaneState | Mapping[str, object] | None
    ) = None,
) -> str:
    request_payload = {
        "baseline_source_object_instance_graph_commit_id": (
            baseline_source_object_instance_graph_commit_id
        ),
        "baseline_semantic_object_instance_graph_commit_id": (
            baseline_semantic_object_instance_graph_commit_id
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            baseline_semantic_root_object_instance_graph_commit_id
        ),
    }
    return _semantic_provider_delta_request_key(
        package=_mapping_payload(package) or _object_payload(package),
        semantic_contract=(
            _mapping_payload(semantic_contract) or _object_payload(semantic_contract)
        ),
        current_delta_fingerprint=current_delta_fingerprint,
        request_payload=request_payload,
        baseline_ref=_mapping_payload(baseline_ref),
        provider_delta_lane_state=_mapping_payload(provider_delta_lane_state),
    )


def _semantic_provider_delta_request_key(
    *,
    package: Mapping[str, object],
    semantic_contract: Mapping[str, object],
    current_delta_fingerprint: str,
    request_payload: Mapping[str, object],
    baseline_ref: Mapping[str, object] | None,
    provider_delta_lane_state: Mapping[str, object] | None = None,
) -> str:
    payload = {
        "package": {
            "package_name": _optional_string(package.get("package_name")),
            "workspace_manifest_kind": _optional_string(
                package.get("workspace_manifest_kind")
            ),
            "manifest_path": _optional_string(package.get("manifest_path")),
            "source_code_package_id": _optional_string(
                package.get("source_code_package_id")
            ),
        },
        "semantic_contract": {
            "module": _optional_string(semantic_contract.get("module")),
            "provider_key": _optional_string(semantic_contract.get("provider_key")),
            "role": _optional_string(semantic_contract.get("role")),
            "name": _optional_string(semantic_contract.get("name")),
        },
        "current_delta_fingerprint": current_delta_fingerprint.strip(),
        "baseline_oig_commit_refs": {
            "source_object_instance_graph_commit_id": _optional_string(
                request_payload.get("baseline_source_object_instance_graph_commit_id")
            ),
            "semantic_object_instance_graph_commit_id": _optional_string(
                request_payload.get("baseline_semantic_object_instance_graph_commit_id")
            ),
            "semantic_root_object_instance_graph_commit_id": _optional_string(
                request_payload.get(
                    "baseline_semantic_root_object_instance_graph_commit_id"
                )
            ),
        },
        "baseline_ref": _semantic_provider_delta_baseline_ref_key_payload(baseline_ref),
        "provider_delta_lane_state": (
            _semantic_provider_delta_lane_state_key_payload(provider_delta_lane_state)
        ),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "provider_delta_request:sha256:" + hashlib.sha256(encoded).hexdigest()


def _semantic_provider_delta_baseline_ref_key_payload(
    baseline_ref: Mapping[str, object] | None,
) -> dict[str, str | None] | None:
    if baseline_ref is None:
        return None
    try:
        baseline_ref = SemanticMaterializationBaselineRef.model_validate(
            baseline_ref
        ).model_dump(mode="json")
    except ValueError:
        pass
    return {
        field_name: _optional_string(baseline_ref.get(field_name))
        for field_name in (
            "contract_version",
            "workspace_revision_id",
            "workspace_materialization_id",
            "revision_code_package_id",
            "source_code_package_id",
            "source_object_instance_graph_commit_id",
            "semantic_package_commit_id",
            "semantic_package_id",
            "semantic_branch_id",
            "semantic_projection_name",
            "semantic_object_instance_graph_commit_id",
            "semantic_root_kind",
            "semantic_root_id",
            "semantic_root_object_instance_graph_commit_id",
        )
    }


def _semantic_provider_delta_lane_state_key_payload(
    lane_state: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if lane_state is None:
        return None
    try:
        lane_state = SemanticProviderDeltaLaneState.model_validate(
            lane_state
        ).model_dump(mode="json")
    except ValueError:
        pass
    return {
        "contract_version": _optional_string(lane_state.get("contract_version")),
        "status": _optional_string(lane_state.get("status")),
        "reason": _optional_string(lane_state.get("reason")),
        "semantic_branch_id": _optional_string(lane_state.get("semantic_branch_id")),
        "semantic_projection_name": _optional_string(
            lane_state.get("semantic_projection_name")
        ),
        "semantic_projection_hash": _optional_string(
            lane_state.get("semantic_projection_hash")
        ),
        "semantic_package_id": _optional_string(lane_state.get("semantic_package_id")),
        "semantic_root_kind": _optional_string(lane_state.get("semantic_root_kind")),
        "semantic_root_id": _optional_string(lane_state.get("semantic_root_id")),
    }


def _semantic_provider_delta_baseline_ref_from_request_payload(
    payload: Mapping[str, object],
) -> SemanticMaterializationBaselineRef | None:
    raw_ref = payload.get("baseline_ref")
    if raw_ref is None:
        lane_state = _mapping_payload(payload.get("provider_delta_lane_state"))
        if lane_state is not None:
            raw_ref = lane_state.get("baseline_ref")
    if raw_ref is None:
        evidence = payload.get("previous_materialization_evidence")
        if isinstance(evidence, Mapping):
            raw_ref = evidence.get("baseline_ref")
            if raw_ref is None:
                lane_state = _mapping_payload(evidence.get("provider_delta_lane_state"))
                if lane_state is not None:
                    raw_ref = lane_state.get("baseline_ref")
    if raw_ref is None:
        return None
    return SemanticMaterializationBaselineRef.model_validate(raw_ref)


def _semantic_provider_delta_lane_state_from_request_payload(
    payload: Mapping[str, object],
) -> SemanticProviderDeltaLaneState | None:
    raw_state = payload.get("provider_delta_lane_state")
    if raw_state is None:
        evidence = payload.get("previous_materialization_evidence")
        if isinstance(evidence, Mapping):
            raw_state = evidence.get("provider_delta_lane_state")
    if raw_state is None:
        return None
    return SemanticProviderDeltaLaneState.model_validate(raw_state)


def _baseline_ref_text(
    *,
    baseline_ref: SemanticMaterializationBaselineRef | None,
    field_name: str,
) -> str | None:
    if baseline_ref is None:
        return None
    return _optional_string(baseline_ref.model_dump(mode="json").get(field_name))


def _semantic_provider_delta_request_payload_with_baseline_refs(
    *,
    payload: Mapping[str, object],
    baseline_ref: SemanticMaterializationBaselineRef | None,
) -> dict[str, object]:
    evidence = payload.get("previous_materialization_evidence")
    evidence_mapping = evidence if isinstance(evidence, Mapping) else {}
    baseline_ref_payload = (
        baseline_ref.model_dump(mode="json") if baseline_ref is not None else None
    )
    updates: dict[str, str] = {}
    for target_field, evidence_field in (
        (
            "baseline_source_object_instance_graph_commit_id",
            "source_object_instance_graph_commit_id",
        ),
        (
            "baseline_semantic_object_instance_graph_commit_id",
            "semantic_object_instance_graph_commit_id",
        ),
        (
            "baseline_semantic_root_object_instance_graph_commit_id",
            "semantic_root_object_instance_graph_commit_id",
        ),
    ):
        if _optional_string(payload.get(target_field)) is not None:
            continue
        extracted = (
            _optional_string(baseline_ref_payload.get(evidence_field))
            if baseline_ref_payload is not None
            else None
        )
        if extracted is None:
            extracted = _semantic_provider_delta_baseline_ref_from_evidence(
                evidence=evidence_mapping,
                field_name=evidence_field,
            )
        if extracted is not None:
            updates[target_field] = extracted
    return {**dict(payload), **updates} if updates else dict(payload)


def _semantic_provider_delta_request_rejection_reason(
    value: object,
) -> SemanticProviderDeltaRequestRejectionReason:
    reason = _optional_string(value) or "delta_fingerprint_changed"
    if reason in {"delta_fingerprint_changed", "provider_evidence_changed"}:
        return cast(SemanticProviderDeltaRequestRejectionReason, reason)
    raise ValueError(f"Unsupported provider delta rejection reason {reason!r}.")


def _semantic_provider_delta_baseline_ref_from_evidence(
    *,
    evidence: Mapping[str, object],
    field_name: str,
) -> str | None:
    direct = _optional_string(evidence.get(field_name))
    if direct is not None:
        return direct
    commit_refs = evidence.get("commit_refs")
    if isinstance(commit_refs, Mapping):
        ref = _optional_string(commit_refs.get(field_name))
        if ref is not None:
            return ref
    bundle_package = evidence.get("bundle_package")
    if isinstance(bundle_package, Mapping):
        ref = _optional_string(bundle_package.get(field_name))
        if ref is not None:
            return ref
    for raw_bundle in _sequence(evidence.get("bundle_packages")):
        if not isinstance(raw_bundle, Mapping):
            continue
        ref = _optional_string(raw_bundle.get(field_name))
        if ref is not None:
            return ref
    return None


def _semantic_provider_delta_head_ref_status(
    value: object,
) -> Literal["head_refs_unavailable", "head_refs_partial", "head_refs_available"]:
    text = _optional_string(value)
    if text == "head_refs_partial":
        return "head_refs_partial"
    if text == "head_refs_available":
        return "head_refs_available"
    return "head_refs_unavailable"


def _mapping_payload(value: object) -> dict[str, object] | None:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return None


def _assert_no_projection_portal_policy_runtime_provenance(
    value: object,
    *,
    context: str,
) -> None:
    forbidden = tuple(
        sorted(_projection_portal_policy_runtime_provenance_fields(value))
    )
    if forbidden:
        fields = ", ".join(forbidden)
        raise ValueError(
            "Semantic projection portal policy must not carry runtime "
            f"provenance fields in {context}: {fields}."
        )


def _projection_portal_policy_runtime_provenance_fields(
    value: object,
) -> set[str]:
    fields: set[str] = set()
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            if key in _SEMANTIC_PROJECTION_PORTAL_POLICY_RUNTIME_PROVENANCE_FIELDS:
                fields.add(key)
            fields.update(_projection_portal_policy_runtime_provenance_fields(item))
        return fields
    for item in _sequence(value):
        fields.update(_projection_portal_policy_runtime_provenance_fields(item))
    return fields


def _object_payload(value: object) -> dict[str, object]:
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_text(mapping: Mapping[str, object], key: str) -> str:
    text = _optional_string(mapping.get(key))
    if text is None:
        raise ValueError(f"Semantic provider delta payload is missing {key!r}.")
    return text


def _optional_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _nonnegative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def _string_int_mapping(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, int] = {}
    for raw_key, raw_count in value.items():
        if (
            isinstance(raw_key, str)
            and raw_key.strip()
            and isinstance(raw_count, int)
            and not isinstance(raw_count, bool)
            and raw_count >= 0
        ):
            normalized[raw_key.strip()] = raw_count
    return normalized


def _string_tuple(value: object) -> tuple[str, ...]:
    return tuple(
        text
        for item in _sequence(value)
        for text in (_optional_string(item),)
        if text is not None
    )


def _mapping_list(value: object) -> list[dict[str, object]]:
    return [
        {str(key): item for key, item in item.items()}
        for item in _sequence(value)
        if isinstance(item, Mapping)
    ]


def _json_safe_provider_input_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe_provider_input_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe_provider_input_value(item) for item in value]
    if callable(value):
        return {
            "value_kind": "callable",
            "callable_type": type(value).__name__,
        }
    return {
        "value_kind": "object",
        "object_type": type(value).__name__,
    }


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


__all__ = [
    "SEMANTIC_MATERIALIZATION_CAPABILITY",
    "SEMANTIC_PROVIDER_DELTA_ADAPTER_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_BASELINE_REF_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_BASELINE_REF_REQUIRED_FIELDS",
    "SEMANTIC_PROVIDER_DELTA_BASELINE_RESOLUTION_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_KEY",
    "SEMANTIC_PROVIDER_DELTA_DURABLE_EXECUTION_INPUTS_REQUIRED_COMMON_FIELDS",
    "SEMANTIC_PROVIDER_DELTA_EVENT_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_EVENT_REPORT_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_HEAD_MOVE_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_LANE_STATE_CONTRACT_VERSION",
    "SEMANTIC_PROJECTION_PORTAL_POLICY_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_READABLE_EVENT_CHAIN_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_REQUEST_BUNDLE_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_REQUEST_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_RESULT_CONTRACT_VERSION",
    "SEMANTIC_MATERIALIZATION_EXECUTION_CONTEXT_KEY",
    "SEMANTIC_MATERIALIZATION_LIFECYCLE_PROFILE_CONTEXT_KEY",
    "SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY",
    "SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY",
    "SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTEXT_KEY",
    "SEMANTIC_LANGUAGE_MATERIALIZATION_TOOLING_CONTRACT_VERSION",
    "SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY",
    "SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA",
    "SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY",
    "SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY",
    "SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION",
    "SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY",
    "SEMANTIC_FUNCTION_CALL_CONTEXT_BY_PROVIDER_KEY",
    "SEMANTIC_FUNCTION_CALL_CONTEXT_KEY",
    "SEMANTIC_SOURCE_SESSION_CONTEXT_CONTRACT_VERSION",
    "SEMANTIC_SOURCE_SESSION_CONTEXT_KEY",
    "SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND",
    "SemanticMaterializationBaselineRef",
    "SemanticMaterializationBaselineResolution",
    "SemanticProviderDeltaCauseHints",
    "SemanticProviderDeltaChangedPathHint",
    "SemanticProviderDeltaDurableExecutionInputs",
    "SemanticProviderDeltaEvent",
    "SemanticProviderDeltaEventReport",
    "SemanticProviderDeltaHeadMoveExecutableOperation",
    "SemanticProviderDeltaHeadMoveOperationFamily",
    "SemanticProviderDeltaHeadMovePlan",
    "SemanticProviderDeltaHeadRefs",
    "SemanticProviderDeltaLaneState",
    "SemanticProviderDeltaPackageIdentity",
    "SemanticProjectionPortalHydration",
    "SemanticProjectionPortalParticipation",
    "SemanticProjectionPortalPolicy",
    "SemanticProjectionPortalPolicyPortal",
    "SemanticProjectionPortalPolicyProjection",
    "SemanticProviderDeltaReadableEventChain",
    "SemanticProviderDeltaRequest",
    "SemanticProviderDeltaRequestBundle",
    "SemanticProviderDeltaResult",
    "SemanticProviderDeltaSemanticContract",
    "SemanticPackageMaterializationExecutionContext",
    "SemanticPackageMaterializationExecutionContextRequest",
    "SemanticFunctionCallContext",
    "SemanticSourceSessionCacheRef",
    "SemanticSourceSessionContext",
    "SemanticSourceSessionPackageContext",
    "SemanticLanguageMaterializationTarget",
    "SemanticMaterializationProgressCallback",
    "SemanticPackageMaterializationMode",
    "SemanticPackageMaterializationBundle",
    "SemanticPackageMaterializationEmittedPackageOutput",
    "SemanticPackageMaterializationInput",
    "SemanticPackageImplementationWorkItem",
    "SemanticPackageMaterializationRequest",
    "SemanticPackageMaterializationResult",
    "build_semantic_provider_delta_head_move_plan",
    "build_semantic_provider_delta_request_key",
    "encode_semantic_function_call_context",
    "encode_semantic_function_call_context_by_provider",
    "encode_semantic_source_session_context",
    "semantic_provider_delta_events_from_payloads",
]
