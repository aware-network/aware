from __future__ import annotations

import asyncio
import base64
import bisect
import hashlib
import json
import logging
import os
import stat
import time
from collections import OrderedDict
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import cast

from aware_local_service_runtime import (
    JsonObject,
    LocalCallRequest,
    LocalCallResult,
    LocalCallStatus,
    LocalCapabilityContext,
    LocalCapabilityDescriptor,
    LocalFailure,
    LocalFailureCode,
    LocalInvocableOperationCatalog,
    LocalInvocableOperationDescriptor,
    LocalInvocationApprovalKind,
    LocalOperationEffectClass,
    LocalObservationEnvelope,
    LocalObservationGap,
    LocalObservationGapReason,
    LocalObservationKind,
    LocalObservationReplay,
)

from .change_evidence import (
    WORKSPACE_REPOSITORY_EVIDENCE_GAP_OBSERVER_BASELINE_UNAVAILABLE,
    WORKSPACE_REPOSITORY_EVIDENCE_GAP_EXACT_TRANSITION_UNAVAILABLE,
    RepositoryEvidencePosture,
    RepositoryEvidenceResolutionState,
    RepositoryEvidenceCoordinateKind,
    RepositoryMutationKind,
    WorkspaceRepositoryChangeEvidence,
    WorkspaceRepositoryEvidenceCoordinate,
    WorkspaceRepositoryExternalEvidenceRef,
    repository_change_evidence_ref,
)
from .change_evidence_codec import (
    repository_authorized_mutation_payload,
    repository_change_evidence_from_payload,
    repository_change_evidence_payload,
    repository_content_delta_resolution_payload,
    repository_delta_capture_payload,
    repository_diff_page_payload,
    repository_diff_request_from_payload,
    repository_external_evidence_from_payload,
    repository_mutation_request_from_payload,
)
from .change_evidence_resolver import (
    WorkspaceRepositoryChangeEvidenceResolver,
    WorkspaceRepositoryEvidenceResolverError,
)
from .composition import (
    LocalCheckoutWorkspaceCompositionProvider,
    WorkspaceCompositionFailure,
)
from .contracts import (
    ObservationRuntimeState,
    RepositoryObservationChange,
    RepositoryPathQuery,
    RepositorySnapshotEntry,
    WorkspaceRepositoryObservationBatch,
    WorkspaceRepositoryObservationGap,
    WorkspaceRepositoryObservationHealth,
    WorkspaceRepositoryObservationSnapshot,
    WorkspaceRepositoryQuerySnapshot,
)
from .observation import (
    WORKSPACE_BACKGROUND_POLL_POLICY,
    WorkspaceRepositoryObservationSession,
)
from .repository_access import (
    DEFAULT_REPOSITORY_CHILD_PAGE_MAX_ENTRIES,
    MAX_REPOSITORY_PATH_SEARCH_EXAMINED,
    MAX_REPOSITORY_PATH_SEARCH_RESULTS,
    WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF,
    WORKSPACE_REPOSITORY_ACCESS_READINESS_CONTRACT_REF,
    WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF,
    WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
    RepositoryAccessReadinessState,
    RepositoryEntryKind,
    RepositoryObservationCoordinate,
    WorkspaceRepositoryAccessReadiness,
    WorkspaceRepositoryPathSearchRequest,
    repository_children_page_payload,
    repository_descriptor_payload,
    repository_entry_ref,
    repository_path_search_page,
)
from .repository_delta_resident import WorkspaceRepositoryDeltaResident
from .repository_delta import repository_delta_scope_selection
from .repository_diff import WorkspaceRepositoryOperationalDiffProvider
from .repository_mutation import (
    WorkspaceRepositoryMutationCoordinator,
    WorkspaceRepositoryMutationRequest,
    WorkspaceRepositoryTextReplacement,
)

logger = logging.getLogger(__name__)

WORKSPACE_LOCAL_SERVICE_CAPABILITY = "workspace.repository"
WORKSPACE_SOURCE_CHANGES_TOPIC = "source_changes"
WORKSPACE_LOCAL_SERVICE_SCHEMA = "aware.workspace.repository.local-service.v1"
WORKSPACE_LOCAL_SERVICE_SCHEMA_DIGEST = (
    "sha256:" + hashlib.sha256(WORKSPACE_LOCAL_SERVICE_SCHEMA.encode()).hexdigest()
)
DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES = 128 * 1024
DEFAULT_WORKSPACE_SOURCE_DOCUMENT_MAX_BYTES = 4 * 1024 * 1024
DEFAULT_WORKSPACE_SNAPSHOT_PAGE_MAX_ENTRIES = 128
DEFAULT_WORKSPACE_SNAPSHOT_PAGE_MAX_BYTES = 512 * 1024
DEFAULT_WORKSPACE_SNAPSHOT_PAGE_MAX_PATH_CHARS = 16_384
DEFAULT_WORKSPACE_SNAPSHOT_PAGE_RETENTION_SECONDS = 60.0
DEFAULT_WORKSPACE_SNAPSHOT_PAGE_RETAINED_COORDINATES = 16
WORKSPACE_AGENT_SNAPSHOT_PAGE_MAX_ENTRIES = 16
WORKSPACE_AGENT_SOURCE_READ_MAX_BYTES = 16 * 1024
WORKSPACE_AGENT_SOURCE_MUTATION_MAX_BYTES = 256 * 1024
WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA_REF = (
    "aware://workspace.repository/snapshot-page/request/v1"
)
WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA_REF = (
    "aware://workspace.repository/read-source/request/v1"
)
WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA_REF = (
    "aware://workspace.repository/mutate-source/request/v1"
)


def _observer_gap_evidence(
    external: WorkspaceRepositoryExternalEvidenceRef,
    *,
    repository_binding_ref: str,
    reason: str,
) -> WorkspaceRepositoryChangeEvidence:
    """Publish an explicit observer gap without inventing a repository delta."""

    evidence_key = f"external:{external.evidence_ref}"
    return WorkspaceRepositoryChangeEvidence(
        evidence_ref=repository_change_evidence_ref(
            repository_binding_ref=repository_binding_ref,
            evidence_key=evidence_key,
        ),
        evidence_key=evidence_key,
        revision=0,
        repository_binding_ref=repository_binding_ref,
        posture=RepositoryEvidencePosture.GAP,
        resolution_state=RepositoryEvidenceResolutionState.GAP,
        observed_at=external.observed_at,
        external_evidence_refs=(external.evidence_ref,),
        reason=reason,
        resolved_at=max(datetime.now(UTC), external.observed_at),
    )


_SNAPSHOT_COORDINATE_PROPERTIES: JsonObject = {
    "expected_binding_key": {"type": "string", "minLength": 1},
    "expected_epoch": {"type": "string", "minLength": 1},
    "expected_cursor": {"type": "integer", "minimum": 0},
    "expected_snapshot_digest": {"type": "string", "minLength": 1},
}
_WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA: JsonObject = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "after_path": {
            "type": ["string", "null"],
            "minLength": 1,
            "maxLength": 4096,
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": WORKSPACE_AGENT_SNAPSHOT_PAGE_MAX_ENTRIES,
        },
        **_SNAPSHOT_COORDINATE_PROPERTIES,
    },
    "required": ["after_path", "limit"],
    "additionalProperties": False,
    "oneOf": [
        {
            "properties": {"after_path": {"type": "null"}},
            "not": {
                "anyOf": [
                    {"required": [name]} for name in _SNAPSHOT_COORDINATE_PROPERTIES
                ]
            },
        },
        {
            "properties": {
                "after_path": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 4096,
                }
            },
            "required": [
                "expected_binding_key",
                "expected_epoch",
                "expected_cursor",
                "expected_snapshot_digest",
            ],
        },
    ],
}
_WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA: JsonObject = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "path": {"type": "string", "minLength": 1, "maxLength": 4096},
        "expected_epoch": {"type": "string", "minLength": 1},
        "expected_cursor": {"type": "integer", "minimum": 0},
        "expected_snapshot_digest": {"type": "string", "minLength": 1},
        "encoding": {"enum": ["utf-8", "base64"]},
        "max_bytes": {
            "type": "integer",
            "minimum": 1,
            "maximum": WORKSPACE_AGENT_SOURCE_READ_MAX_BYTES,
        },
    },
    "required": [
        "path",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
        "encoding",
        "max_bytes",
    ],
    "additionalProperties": False,
}
_WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA: JsonObject = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "mutation_kind": {"enum": ["create", "update", "delete"]},
        "path": {"type": "string", "minLength": 1, "maxLength": 4096},
        "expected_epoch": {"type": "string", "minLength": 1},
        "expected_cursor": {"type": "integer", "minimum": 0},
        "expected_snapshot_digest": {"type": "string", "minLength": 1},
        "expected_exists": {"type": "boolean"},
        "expected_content_digest": {
            "type": ["string", "null"],
            "pattern": "^sha256:[0-9a-f]{64}$",
        },
        "encoding": {"enum": ["utf-8", "base64", None]},
        "content": {
            "type": ["string", "null"],
            "maxLength": 4 * ((WORKSPACE_AGENT_SOURCE_MUTATION_MAX_BYTES + 2) // 3),
        },
        "text_replacements": {
            "type": "array",
            "minItems": 1,
            "maxItems": 64,
            "items": {
                "type": "object",
                "properties": {
                    "old_text": {"type": "string", "minLength": 1},
                    "new_text": {"type": "string"},
                },
                "required": ["old_text", "new_text"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "mutation_kind",
        "path",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
        "expected_exists",
        "expected_content_digest",
        "encoding",
        "content",
    ],
    "additionalProperties": False,
    "oneOf": [
        {
            "properties": {
                "mutation_kind": {"const": "create"},
                "expected_exists": {"const": False},
                "expected_content_digest": {"type": "null"},
                "encoding": {"enum": ["utf-8", "base64"]},
                "content": {"type": "string"},
            },
            "not": {"required": ["text_replacements"]},
        },
        {
            "properties": {
                "mutation_kind": {"const": "update"},
                "expected_exists": {"const": True},
                "expected_content_digest": {"type": "string"},
                "encoding": {"enum": ["utf-8", "base64"]},
                "content": {"type": "string"},
            },
            "not": {"required": ["text_replacements"]},
        },
        {
            "properties": {
                "mutation_kind": {"const": "update"},
                "expected_exists": {"const": True},
                "expected_content_digest": {"type": "string"},
                "encoding": {"type": "null"},
                "content": {"type": "null"},
            },
            "required": ["text_replacements"],
        },
        {
            "properties": {
                "mutation_kind": {"const": "delete"},
                "expected_exists": {"const": True},
                "expected_content_digest": {"type": "string"},
                "encoding": {"type": "null"},
                "content": {"type": "null"},
            },
            "not": {"required": ["text_replacements"]},
        },
    ],
}


def _schema_digest(value: JsonObject) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA_DIGEST = _schema_digest(
    _WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA
)
WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA_DIGEST = _schema_digest(
    _WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA
)
WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA_DIGEST = _schema_digest(
    _WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA
)
WORKSPACE_AGENT_MUTATION_PREVIEW_OPERATION_CATALOG = LocalInvocableOperationCatalog(
    (
        LocalInvocableOperationDescriptor(
            capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
            operation_key="mutate_source",
            semantic_version="0.2.0",
            summary=(
                "Create, replace, text-edit, or delete one bounded source path "
                "through exact Workspace coordinate-and-digest CAS mutation."
            ),
            request_schema_ref=WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA_REF,
            request_schema_digest=(WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA_DIGEST),
            response_schema_ref=(
                "aware://workspace.repository/authorized-mutation/response/v1"
            ),
            response_schema_digest=(
                "sha256:"
                + hashlib.sha256(
                    b"aware.workspace.repository.authorized-mutation.response.v1"
                ).hexdigest()
            ),
            authority_kinds=("local_uncommitted",),
            effect_class=LocalOperationEffectClass.AUTHORITY_BOUND_MUTATION,
            approval_kind=LocalInvocationApprovalKind.AUTHORITY_RECEIPT,
            idempotency_required=True,
            receipt_schema_ref=("aware://workspace.repository/mutation-receipt/v1"),
            receipt_schema_digest=(
                "sha256:"
                + hashlib.sha256(
                    b"aware.workspace.repository.mutation-receipt.v1"
                ).hexdigest()
            ),
            result_observation_topics=(WORKSPACE_SOURCE_CHANGES_TOPIC,),
            metadata={
                "recommended_tool_name": "workspace_mutate_source",
                "stability": "preview",
            },
        ),
        LocalInvocableOperationDescriptor(
            capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
            operation_key="read_source",
            semantic_version="1.0.0",
            summary=(
                "Read one indexed repository path under exact Workspace snapshot "
                "coordinates and a bounded byte limit."
            ),
            request_schema_ref=WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA_REF,
            request_schema_digest=WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA_DIGEST,
            response_schema_ref=(
                "aware://workspace.repository/read-source/response/v1"
            ),
            response_schema_digest=(
                "sha256:"
                + hashlib.sha256(
                    b"aware.workspace.repository.read-source.response.v1"
                ).hexdigest()
            ),
            authority_kinds=("local_uncommitted",),
            metadata={"recommended_tool_name": "workspace_read_source"},
        ),
        LocalInvocableOperationDescriptor(
            capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
            operation_key="snapshot_page",
            semantic_version="1.0.0",
            summary=(
                "List one bounded page from the maintained Workspace repository "
                "snapshot with exact continuation coordinates."
            ),
            request_schema_ref=WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA_REF,
            request_schema_digest=(WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA_DIGEST),
            response_schema_ref=(
                "aware://workspace.repository/snapshot-page/response/v1"
            ),
            response_schema_digest=(
                "sha256:"
                + hashlib.sha256(
                    b"aware.workspace.repository.snapshot-page.response.v1"
                ).hexdigest()
            ),
            authority_kinds=("local_uncommitted",),
            metadata={"recommended_tool_name": "workspace_snapshot_page"},
        ),
    )
)
WORKSPACE_AGENT_INVOCABLE_OPERATION_CATALOG = LocalInvocableOperationCatalog(
    tuple(
        descriptor
        for descriptor in WORKSPACE_AGENT_MUTATION_PREVIEW_OPERATION_CATALOG.operations
        if descriptor.operation_key != "mutate_source"
    )
)


def workspace_agent_invocable_request_schema(operation_key: str) -> JsonObject:
    if operation_key == "read_source":
        return deepcopy(_WORKSPACE_AGENT_READ_SOURCE_REQUEST_SCHEMA)
    if operation_key == "mutate_source":
        return deepcopy(_WORKSPACE_AGENT_MUTATE_SOURCE_REQUEST_SCHEMA)
    if operation_key == "snapshot_page":
        return deepcopy(_WORKSPACE_AGENT_SNAPSHOT_PAGE_REQUEST_SCHEMA)
    raise KeyError(f"Unknown Workspace Agent operation: {operation_key}")


class WorkspaceLocalSourceReadError(RuntimeError):
    def __init__(
        self,
        code: LocalFailureCode,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class WorkspaceLocalSnapshotPageError(RuntimeError):
    def __init__(
        self,
        code: LocalFailureCode,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class WorkspaceRepositoryLocalServiceParticipant:
    """Local Service adapter over one Workspace-owned maintained session."""

    def __init__(
        self,
        session: WorkspaceRepositoryObservationSession,
        *,
        mutation_coordinator: WorkspaceRepositoryMutationCoordinator | None = None,
        diff_provider: WorkspaceRepositoryOperationalDiffProvider | None = None,
        evidence_resolver: WorkspaceRepositoryChangeEvidenceResolver | None = None,
        delta_resident: WorkspaceRepositoryDeltaResident | None = None,
        background: bool = True,
        source_read_max_bytes: int = DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES,
        snapshot_page_retention_seconds: float = (
            DEFAULT_WORKSPACE_SNAPSHOT_PAGE_RETENTION_SECONDS
        ),
        snapshot_page_retained_coordinates: int = (
            DEFAULT_WORKSPACE_SNAPSHOT_PAGE_RETAINED_COORDINATES
        ),
    ) -> None:
        if (
            mutation_coordinator is not None
            and mutation_coordinator.session is not session
        ):
            raise ValueError("Workspace mutation coordinator session differs")
        if (mutation_coordinator is None) != (diff_provider is None):
            raise ValueError(
                "Workspace mutation coordinator and diff provider must be paired"
            )
        if evidence_resolver is not None and evidence_resolver.session is not session:
            raise ValueError("Workspace evidence resolver session differs")
        if delta_resident is not None and delta_resident.session is not session:
            raise ValueError("Workspace delta resident session differs")
        if not 0 < source_read_max_bytes <= DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES:
            raise ValueError(
                "Workspace source read budget must be positive and JSON-safe"
            )
        if snapshot_page_retention_seconds <= 0:
            raise ValueError("Workspace snapshot page retention must be positive")
        if snapshot_page_retained_coordinates <= 0:
            raise ValueError(
                "Workspace retained snapshot coordinate count must be positive"
            )
        self._session = session
        self._mutation_coordinator = mutation_coordinator
        self._diff_provider = diff_provider
        self._evidence_resolver = evidence_resolver
        self._delta_resident = delta_resident
        self._background = background
        self._source_read_max_bytes = source_read_max_bytes
        self._snapshot_page_retention_seconds = snapshot_page_retention_seconds
        self._snapshot_page_retained_coordinates = snapshot_page_retained_coordinates
        self._retained_page_snapshots: OrderedDict[
            tuple[str, str, int, str],
            tuple[float, WorkspaceRepositoryObservationSnapshot],
        ] = OrderedDict()
        self._configured = False
        self._initialization_task: asyncio.Task[None] | None = None

    @property
    def descriptor(self) -> LocalCapabilityDescriptor:
            return LocalCapabilityDescriptor(
            capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
            semantic_version="1.0.0",
            implementation_version="aware-workspace-runtime-0.1.0",
            contract_schema_digest=WORKSPACE_LOCAL_SERVICE_SCHEMA_DIGEST,
            request_schema_ref=f"aware://{WORKSPACE_LOCAL_SERVICE_SCHEMA}/request",
            response_schema_ref=f"aware://{WORKSPACE_LOCAL_SERVICE_SCHEMA}/response",
            observation_schema_ref=(
                f"aware://{WORKSPACE_LOCAL_SERVICE_SCHEMA}/observation"
            ),
            authority_kinds=("local_uncommitted",),
            metadata=cast(
                JsonObject,
                {
                    "topics": [WORKSPACE_SOURCE_CHANGES_TOPIC],
                "repository_observer_owner": "workspace",
                "background_observation": self._background,
                "background_poll_policy": WORKSPACE_BACKGROUND_POLL_POLICY,
                "background_poll_minimum_interval_seconds": (
                    self._session.poll_interval
                ),
                "background_poll_maximum_duty_cycle": (
                    self._session.max_background_poll_duty_cycle
                ),
                "repository_access_contract_ref": (
                    WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF
                ),
                "repository_access_readiness_contract_ref": (
                    WORKSPACE_REPOSITORY_ACCESS_READINESS_CONTRACT_REF
                ),
                "repository_visibility_policy_ref": (
                    WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF
                ),
                "repository_visibility_policy_version": (
                    self._session.binding.filter_version
                ),
                "repository_path_search_contract_ref": (
                    WORKSPACE_REPOSITORY_PATH_SEARCH_CONTRACT_REF
                ),
                    "repository_change_operations": (
                    (
                        [
                            "repository_correlate_external",
                            "repository_observe_paths",
                        ]
                        if self._evidence_resolver
                        else []
                    )
                    + (
                        []
                        if self._mutation_coordinator is None
                        else [
                            "repository_mutate",
                            "repository_mutation_receipts_describe",
                            "repository_diff",
                        ]
                    )
                    + (
                        []
                        if self._delta_resident is None
                        else [
                            "repository_delta_prepare",
                            "repository_delta_status",
                            "repository_delta_resolve_evidence",
                        ]
                    )
                    ),
                },
            ),
        )

    @property
    def invocable_operation_catalog(self) -> LocalInvocableOperationCatalog:
        return WORKSPACE_AGENT_MUTATION_PREVIEW_OPERATION_CATALOG

    async def configure(self, context: LocalCapabilityContext) -> None:
        admission = context.admission.get("workspace_repository_binding")
        if not isinstance(admission, dict):
            raise TypeError("Workspace repository binding admission is required")
        binding_key = admission.get("binding_key")
        if binding_key != self._session.binding.binding_key:
            raise ValueError("Workspace repository binding admission does not match")
        self._configured = True

    async def start(self) -> None:
        if not self._configured:
            raise RuntimeError("Workspace participant is not configured")
        self._retained_page_snapshots.clear()
        await self._session.admit()
        if self._background and (
            self._initialization_task is None or self._initialization_task.done()
        ):
            self._initialization_task = asyncio.create_task(
                self._initialize_observation(),
                name="workspace-repository-observation-initialize",
            )

    async def stop(self) -> None:
        initialization = self._initialization_task
        self._initialization_task = None
        if initialization is not None and not initialization.done():
            initialization.cancel()
            try:
                await initialization
            except asyncio.CancelledError:
                pass
        try:
            if self._delta_resident is not None:
                await self._delta_resident.stop()
            await self._session.stop()
        finally:
            self._retained_page_snapshots.clear()

    async def _initialize_observation(self) -> None:
        try:
            await self._session.start(background=True)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.warning(
                "Workspace repository observation initialization failed; "
                "explicit reads may retry",
                exc_info=error,
            )

    def _repository_access_readiness(
        self, payload: JsonObject
    ) -> WorkspaceRepositoryAccessReadiness:
        preparation_ref = cast(str, payload["preparation_ref"])
        workspace_grant_ref = cast(str, payload["workspace_grant_ref"])
        if self._session.observation_initialized:
            descriptor = {
                "grant_ref": cast(str, payload["repository_grant_ref"]),
                "display_name": cast(str, payload["display_name"]),
                "display_path": cast(str, payload["display_path"]),
                **repository_descriptor_payload(
                    self._session.current_snapshot,
                    self._session.binding,
                ),
            }
            return WorkspaceRepositoryAccessReadiness(
                preparation_ref=preparation_ref,
                workspace_grant_ref=workspace_grant_ref,
                revision=1,
                state=RepositoryAccessReadinessState.READY,
                descriptor=descriptor,
                failure_code=None,
                failure_message=None,
                retryable=False,
                observe_after_milliseconds=None,
            )
        initialization = self._initialization_task
        health = self._session.health
        if (
            initialization is not None
            and initialization.done()
            and health.state is ObservationRuntimeState.DEGRADED
        ):
            return WorkspaceRepositoryAccessReadiness(
                preparation_ref=preparation_ref,
                workspace_grant_ref=workspace_grant_ref,
                revision=1,
                state=RepositoryAccessReadinessState.FAILED,
                descriptor=None,
                failure_code="workspace_repository_initialization_failed",
                failure_message="Workspace repository observation could not initialize.",
                retryable=False,
                observe_after_milliseconds=None,
            )
        return WorkspaceRepositoryAccessReadiness(
            preparation_ref=preparation_ref,
            workspace_grant_ref=workspace_grant_ref,
            revision=0,
            state=RepositoryAccessReadinessState.INITIALIZING,
            descriptor=None,
            failure_code=None,
            failure_message=None,
            retryable=False,
            observe_after_milliseconds=250,
        )

    async def call(self, request: LocalCallRequest) -> LocalCallResult:
        if request.capability_key != WORKSPACE_LOCAL_SERVICE_CAPABILITY:
            return _invalid(request, "Workspace capability key does not match")
        if request.authority_kind != "local_uncommitted":
            return _invalid(
                request,
                "Workspace local participant requires local_uncommitted authority",
            )
        if request.operation_key in {
            "repository_prepare",
            "repository_access_readiness",
        }:
            expected_keys = {
                "preparation_ref",
                "workspace_grant_ref",
                "repository_grant_ref",
                "display_name",
                "display_path",
            }
            if set(request.payload) != expected_keys or any(
                not isinstance(request.payload[key], str) or not request.payload[key]
                for key in expected_keys
            ):
                return _invalid(request, "repository readiness payload is invalid")
            if (
                request.operation_key == "repository_prepare"
                and not self._session.observation_initialized
                and self._initialization_task is None
            ):
                self._initialization_task = asyncio.create_task(
                    self._initialize_observation(),
                    name="workspace-repository-observation-prepare",
                )
            readiness = self._repository_access_readiness(request.payload)
            payload = cast(JsonObject, readiness.to_payload())
            if readiness.state is RepositoryAccessReadinessState.READY:
                return _success(
                    request,
                    payload,
                    snapshot=self._session.current_snapshot,
                )
            return _success_unobserved(request, payload)
        if request.operation_key == "snapshot":
            if request.payload:
                return _invalid(request, "snapshot payload must be empty")
            snapshot = await self._full_snapshot()
            return _success(request, _snapshot_payload(snapshot), snapshot=snapshot)
        if request.operation_key == "repository_delta_prepare":
            resident = self._delta_resident
            if resident is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository delta capture is unavailable",
                    retryable=False,
                )
            if set(request.payload) != {
                "selected_paths",
                "context_refs",
                "selection_kind",
            }:
                return _invalid(request, "repository_delta_prepare payload keys differ")
            raw_paths = request.payload["selected_paths"]
            raw_contexts = request.payload["context_refs"]
            selection_kind = request.payload["selection_kind"]
            if (
                not isinstance(raw_paths, list)
                or not raw_paths
                or any(not isinstance(path, str) or not path for path in raw_paths)
                or not isinstance(raw_contexts, list)
                or any(
                    not isinstance(context, str) or not context
                    for context in raw_contexts
                )
                or selection_kind not in {"exact", "scope"}
            ):
                return _invalid(request, "repository delta selection is invalid")
            try:
                selected_paths = tuple(cast(list[str], raw_paths))
                if selection_kind == "scope":
                    snapshot = await self._full_snapshot()
                    selected_paths = repository_delta_scope_selection(
                        selected_paths,
                        observed_paths=tuple(entry.path for entry in snapshot.entries),
                    )
                captures = await resident.prepare_batch(
                    selected_paths=selected_paths,
                    context_refs=tuple(raw_contexts),
                )
            except (TypeError, ValueError, RuntimeError) as error:
                return _invalid(request, str(error))
            return _success(
                request,
                {
                    "captures": [
                        cast(JsonObject, repository_delta_capture_payload(capture))
                        for capture in captures
                    ],
                    "resident": _delta_resident_payload(resident),
                },
                snapshot=self._session.current_snapshot,
            )
        if request.operation_key == "repository_delta_status":
            resident = self._delta_resident
            if resident is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository delta capture is unavailable",
                    retryable=False,
                )
            if set(request.payload) != {"capture_ref"}:
                return _invalid(request, "repository_delta_status payload keys differ")
            capture_ref = request.payload["capture_ref"]
            if capture_ref is not None and (
                not isinstance(capture_ref, str) or not capture_ref
            ):
                return _invalid(request, "capture_ref must be null or non-empty")
            capture = (
                None
                if capture_ref is None
                else resident.store.resolve_capture(capture_ref)
            )
            payload: JsonObject = {
                "capture": (
                    None
                    if capture is None
                    else cast(JsonObject, repository_delta_capture_payload(capture))
                ),
                "resident": _delta_resident_payload(resident),
            }
            if not self._session.observation_initialized:
                return _success_unobserved(request, payload)
            return _success(request, payload, snapshot=self._session.current_snapshot)
        if request.operation_key == "repository_delta_resolve_evidence":
            resident = self._delta_resident
            if resident is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository delta capture is unavailable",
                    retryable=False,
                )
            if set(request.payload) != {"evidence", "context_refs"}:
                return _invalid(
                    request, "repository_delta_resolve_evidence payload keys differ"
                )
            raw_contexts = request.payload["context_refs"]
            if not isinstance(raw_contexts, list) or any(
                not isinstance(context, str) or not context for context in raw_contexts
            ):
                return _invalid(request, "repository delta contexts are invalid")
            try:
                evidence = repository_change_evidence_from_payload(
                    request.payload["evidence"]
                )
                resolution = resident.resolve_evidence(
                    evidence,
                    context_refs=tuple(raw_contexts),
                )
            except (TypeError, ValueError) as error:
                return _invalid(request, str(error))
            payload = cast(
                JsonObject, repository_content_delta_resolution_payload(resolution)
            )
            if not self._session.observation_initialized:
                return _success_unobserved(request, payload)
            return _success(request, payload, snapshot=self._session.current_snapshot)
        if request.operation_key == "snapshot_page":
            await self._full_snapshot()
            snapshot = self._snapshot_for_page(request.payload)
            try:
                payload = _snapshot_page_payload(snapshot, request.payload)
            except WorkspaceLocalSnapshotPageError as error:
                return _failure(
                    request,
                    code=error.code,
                    message=str(error),
                    retryable=error.retryable,
                )
            self._retain_snapshot_for_page(snapshot, payload)
            return _success(request, payload, snapshot=snapshot)
        if request.operation_key == "repository_descriptor":
            if request.payload:
                return _invalid(request, "repository_descriptor payload must be empty")
            snapshot = await self._full_snapshot()
            return _success(
                request,
                cast(
                    JsonObject,
                    repository_descriptor_payload(snapshot, self._session.binding),
                ),
                snapshot=snapshot,
            )
        if request.operation_key == "repository_children":
            snapshot = await self._full_snapshot()
            try:
                values = _repository_children_request(request.payload, snapshot)
                payload = repository_children_page_payload(
                    snapshot,
                    self._session.binding,
                    parent_path=cast(str, values["parent_path"]),
                    continuation_ref=cast(str | None, values["continuation_ref"]),
                    limit=cast(int, values["limit"]),
                )
            except (ValueError, WorkspaceLocalSnapshotPageError) as error:
                code = (
                    error.code
                    if isinstance(error, WorkspaceLocalSnapshotPageError)
                    else LocalFailureCode.INVALID_REQUEST
                )
                return _failure(
                    request,
                    code=code,
                    message=str(error),
                    retryable=(
                        error.retryable
                        if isinstance(error, WorkspaceLocalSnapshotPageError)
                        else False
                    ),
                )
            return _success(request, cast(JsonObject, payload), snapshot=snapshot)
        if request.operation_key == "repository_search_paths":
            snapshot = await self._full_snapshot()
            try:
                search_request = _repository_path_search_request(request.payload)
                page = repository_path_search_page(
                    snapshot,
                    self._session.binding,
                    search_request,
                )
            except (ValueError, WorkspaceLocalSnapshotPageError) as error:
                stale = isinstance(error, ValueError) and "stale" in str(error)
                code = (
                    error.code
                    if isinstance(error, WorkspaceLocalSnapshotPageError)
                    else (
                        LocalFailureCode.CONFLICT
                        if stale
                        else LocalFailureCode.INVALID_REQUEST
                    )
                )
                return _failure(
                    request,
                    code=code,
                    message=str(error),
                    retryable=(
                        error.retryable
                        if isinstance(error, WorkspaceLocalSnapshotPageError)
                        else stale
                    ),
                )
            return _success(
                request,
                cast(JsonObject, page.to_payload()),
                snapshot=snapshot,
            )
        if request.operation_key == "health":
            if request.payload:
                return _invalid(request, "health payload must be empty")
            snapshot = await self._full_snapshot()
            return _success(
                request,
                _health_payload(self._session.health),
                snapshot=snapshot,
            )
        if request.operation_key == "poll":
            if request.payload:
                return _invalid(request, "poll payload must be empty")
            await self._full_snapshot()
            batch = await self._session.poll_once()
            snapshot = self._session.current_snapshot
            return _success(
                request,
                {
                    "changed": batch is not None,
                    "batch": None if batch is None else _batch_payload(batch),
                },
                snapshot=snapshot,
            )
        if request.operation_key == "repository_observe_paths":
            if set(request.payload) != {"selected_paths"}:
                return _invalid(request, "repository_observe_paths payload keys differ")
            raw_paths = request.payload["selected_paths"]
            if (
                not isinstance(raw_paths, list)
                or not raw_paths
                or any(not isinstance(path, str) or not path for path in raw_paths)
            ):
                return _invalid(
                    request, "repository_observe_paths selection is invalid"
                )
            await self._full_snapshot()
            try:
                batch = await self._session.observe_paths_once(
                    tuple(cast(list[str], raw_paths))
                )
            except ValueError as error:
                return _invalid(request, str(error))
            snapshot = self._session.current_snapshot
            return _success(
                request,
                {
                    "changed": batch is not None,
                    "batch": None if batch is None else _batch_payload(batch),
                },
                snapshot=snapshot,
            )
        if request.operation_key == "composition":
            if request.payload:
                return _invalid(request, "composition payload must be empty")
            snapshot = await self._full_snapshot()
            try:
                composition = LocalCheckoutWorkspaceCompositionProvider().describe(
                    self._session.binding.root_path
                )
            except WorkspaceCompositionFailure as error:
                return _failure(
                    request,
                    code=LocalFailureCode.INVALID_REQUEST,
                    message=str(error),
                )
            return _success(
                request,
                {"composition": cast(JsonObject, composition)},
                snapshot=snapshot,
            )
        if request.operation_key == "read_source":
            try:
                await self._full_snapshot()
                payload, snapshot = await asyncio.to_thread(
                    self._read_source, request.payload
                )
            except WorkspaceLocalSourceReadError as error:
                return _failure(
                    request,
                    code=error.code,
                    message=str(error),
                    retryable=error.retryable,
                )
            return _success(request, payload, snapshot=snapshot)
        if request.operation_key == "repository_read_source":
            try:
                await self._full_snapshot()
                payload, snapshot = await asyncio.to_thread(
                    self._repository_read_source, request.payload
                )
            except WorkspaceLocalSourceReadError as error:
                return _failure(
                    request,
                    code=error.code,
                    message=str(error),
                    retryable=error.retryable,
                )
            return _success(request, payload, snapshot=snapshot)
        if request.operation_key == "repository_mutate":
            coordinator = self._mutation_coordinator
            if coordinator is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository mutation is unavailable",
                    retryable=False,
                )
            try:
                await self._full_snapshot()
                mutation_request = repository_mutation_request_from_payload(
                    request.payload
                )
                result = await coordinator.mutate(mutation_request)
            except (TypeError, ValueError) as error:
                return _invalid(request, str(error))
            return _success(
                request,
                cast(JsonObject, repository_authorized_mutation_payload(result)),
                snapshot=self._session.current_snapshot,
            )
        if request.operation_key == "repository_mutation_receipts_describe":
            coordinator = self._mutation_coordinator
            if coordinator is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository mutation receipts are unavailable",
                    retryable=False,
                )
            if set(request.payload) != {"mutation_receipt_refs"}:
                return _invalid(
                    request,
                    "Mutation receipt description payload is invalid",
                )
            raw_refs = request.payload.get("mutation_receipt_refs")
            if not isinstance(raw_refs, list) or any(
                not isinstance(item, str) for item in raw_refs
            ):
                return _invalid(request, "Mutation receipt refs must be text")
            try:
                resolution = await coordinator.resolve_receipts(
                    tuple(cast(list[str], raw_refs))
                )
            except ValueError as error:
                return _invalid(request, str(error))
            return _success(
                request,
                cast(
                    JsonObject,
                    {
                        "repository_binding_ref": self._session.binding.binding_key,
                        "requested_receipt_refs": list(
                            resolution.requested_receipt_refs
                        ),
                        "resolved": [
                            repository_authorized_mutation_payload(item)
                            for item in resolution.resolved
                        ],
                        "missing_receipt_refs": list(
                            resolution.missing_receipt_refs
                        ),
                        "store_error": coordinator.result_store_error,
                    },
                ),
                snapshot=self._session.current_snapshot,
            )
        if request.operation_key == "mutate_source":
            coordinator = self._mutation_coordinator
            if coordinator is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository mutation is unavailable",
                    retryable=False,
                )
            try:
                await self._full_snapshot()
                mutation_request = _agent_source_mutation_request(
                    request,
                    session=self._session,
                )
                result = await coordinator.mutate(mutation_request)
            except (TypeError, ValueError) as error:
                return _invalid(request, str(error))
            return _success(
                request,
                cast(JsonObject, repository_authorized_mutation_payload(result)),
                snapshot=self._session.current_snapshot,
            )
        if request.operation_key == "repository_diff":
            provider = self._diff_provider
            if provider is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository diff is unavailable",
                    retryable=False,
                )
            try:
                diff_request = repository_diff_request_from_payload(request.payload)
                page = provider.diff(diff_request)
            except (TypeError, ValueError) as error:
                return _invalid(request, str(error))
            return _success(
                request,
                cast(JsonObject, repository_diff_page_payload(page)),
                snapshot=self._session.current_snapshot,
            )
        if request.operation_key == "repository_correlate_external":
            resolver = self._evidence_resolver
            if resolver is None:
                return _failure(
                    request,
                    code=LocalFailureCode.DEPENDENCY_UNAVAILABLE,
                    message="Workspace repository evidence correlation is unavailable",
                    retryable=False,
                )
            required_payload_keys = {
                "external_evidence",
                "wait_timeout_milliseconds",
            }
            allowed_payload_keys = required_payload_keys | {"observation_completed"}
            if not required_payload_keys.issubset(request.payload) or not set(
                request.payload
            ).issubset(allowed_payload_keys):
                return _invalid(
                    request,
                    "repository_correlate_external payload keys differ",
                )
            raw_timeout = request.payload["wait_timeout_milliseconds"]
            observation_completed = request.payload.get("observation_completed", False)
            if not isinstance(observation_completed, bool):
                return _invalid(request, "observation_completed must be boolean")
            if raw_timeout is not None and (
                not isinstance(raw_timeout, int)
                or isinstance(raw_timeout, bool)
                or raw_timeout < 0
                or raw_timeout > 30_000
            ):
                return _invalid(
                    request,
                    "wait_timeout_milliseconds must be null or between 0 and 30000",
                )
            try:
                external = repository_external_evidence_from_payload(
                    request.payload["external_evidence"]
                )
                baseline_observed_at = self._session.baseline_observed_at
                external_precedes_baseline = (
                    baseline_observed_at is None
                    or external.observed_at <= baseline_observed_at
                )
                evidence = (
                    _observer_gap_evidence(
                        external,
                        repository_binding_ref=cast(
                            str, self._session.binding.binding_key
                        ),
                        reason=(
                            WORKSPACE_REPOSITORY_EVIDENCE_GAP_OBSERVER_BASELINE_UNAVAILABLE
                        ),
                    )
                    if external_precedes_baseline
                    else await resolver.correlate_external(
                        external,
                        wait_timeout=(
                            None if raw_timeout is None else raw_timeout / 1000
                        ),
                    )
                )
                if (
                    observation_completed
                    and evidence.posture is RepositoryEvidencePosture.PROVIDER_REPORTED
                ):
                    evidence = _observer_gap_evidence(
                        external,
                        repository_binding_ref=cast(
                            str, self._session.binding.binding_key
                        ),
                        reason=(
                            WORKSPACE_REPOSITORY_EVIDENCE_GAP_EXACT_TRANSITION_UNAVAILABLE
                        ),
                    )
            except (
                TypeError,
                ValueError,
                WorkspaceRepositoryEvidenceResolverError,
            ) as error:
                return _invalid(request, str(error))
            evidence_payload = cast(
                JsonObject, repository_change_evidence_payload(evidence)
            )
            if not self._session.observation_initialized:
                return _success_unobserved(request, evidence_payload)
            return _success(
                request,
                evidence_payload,
                snapshot=self._session.current_snapshot,
            )
        if request.operation_key == "read_source_chunk":
            try:
                await self._full_snapshot()
                payload, snapshot = await asyncio.to_thread(
                    self._read_source_chunk, request.payload
                )
            except WorkspaceLocalSourceReadError as error:
                return _failure(
                    request,
                    code=error.code,
                    message=str(error),
                    retryable=error.retryable,
                )
            return _success(request, payload, snapshot=snapshot)
        if request.operation_key == "repository_query":
            try:
                query, after_path, limit, expected_coordinate = (
                    _repository_query_request(request.payload)
                )
                if after_path is None:
                    snapshot = await self._session.query(query)
                else:
                    snapshot = self._session.query_snapshot(query.query_ref)
                    if (
                        snapshot.query_digest != query.query_digest
                        or expected_coordinate
                        != (
                            snapshot.binding_key,
                            snapshot.epoch,
                            snapshot.cursor,
                            snapshot.query_digest,
                            snapshot.snapshot_digest,
                        )
                    ):
                        raise ValueError(
                            "repository_query continuation coordinate is stale"
                        )
            except (TypeError, ValueError) as error:
                return _invalid(request, str(error))
            return _success(
                request,
                _repository_query_payload(
                    snapshot,
                    after_path=after_path,
                    limit=limit,
                ),
                snapshot=snapshot,
            )
        if request.operation_key == "repository_query_read_source":
            try:
                payload, snapshot = await asyncio.to_thread(
                    self._repository_query_read_source,
                    request.payload,
                )
            except WorkspaceLocalSourceReadError as error:
                return _failure(
                    request,
                    code=error.code,
                    message=str(error),
                    retryable=error.retryable,
                )
            return _success(request, payload, snapshot=snapshot)
        if request.operation_key == "repository_query_read_source_chunk":
            try:
                payload, snapshot = await asyncio.to_thread(
                    self._repository_query_read_source_chunk,
                    request.payload,
                )
            except WorkspaceLocalSourceReadError as error:
                return _failure(
                    request,
                    code=error.code,
                    message=str(error),
                    retryable=error.retryable,
                )
            return _success(request, payload, snapshot=snapshot)
        if request.operation_key == "acknowledge":
            try:
                await self._full_snapshot()
                values = _acknowledgement_payload(request.payload)
                checkpoint = self._session.acknowledge(**values)
            except (TypeError, ValueError) as error:
                return _invalid(request, str(error))
            snapshot = self._session.current_snapshot
            return _success(
                request,
                {
                    "consumer_key": checkpoint.consumer_key,
                    "epoch": checkpoint.epoch,
                    "cursor": checkpoint.cursor,
                    "accepted_at": checkpoint.accepted_at.isoformat(),
                    "projection_digest": checkpoint.projection_digest,
                },
                snapshot=snapshot,
            )
        return _invalid(
            request, f"Unsupported Workspace operation: {request.operation_key}"
        )

    async def _full_snapshot(self) -> WorkspaceRepositoryObservationSnapshot:
        return await self._session.start(background=self._background)

    def _snapshot_for_page(
        self, payload: JsonObject
    ) -> WorkspaceRepositoryObservationSnapshot:
        now = time.monotonic()
        self._prune_retained_page_snapshots(now)
        if payload.get("after_path") is None:
            return self._session.current_snapshot
        coordinate = _requested_snapshot_coordinate(payload)
        if coordinate is not None:
            retained = self._retained_page_snapshots.get(coordinate)
            if retained is not None:
                _expires_at, snapshot = retained
                self._retained_page_snapshots[coordinate] = (
                    now + self._snapshot_page_retention_seconds,
                    snapshot,
                )
                self._retained_page_snapshots.move_to_end(coordinate)
                return snapshot
        return self._session.current_snapshot

    def _retain_snapshot_for_page(
        self,
        snapshot: WorkspaceRepositoryObservationSnapshot,
        page: JsonObject,
    ) -> None:
        coordinate = _snapshot_coordinate(snapshot)
        if page["complete"] is True:
            self._retained_page_snapshots.pop(coordinate, None)
            return
        now = time.monotonic()
        self._prune_retained_page_snapshots(now)
        self._retained_page_snapshots[coordinate] = (
            now + self._snapshot_page_retention_seconds,
            snapshot,
        )
        self._retained_page_snapshots.move_to_end(coordinate)
        while (
            len(self._retained_page_snapshots)
            > self._snapshot_page_retained_coordinates
        ):
            self._retained_page_snapshots.popitem(last=False)

    def _prune_retained_page_snapshots(self, now: float) -> None:
        expired = [
            coordinate
            for coordinate, (expires_at, _snapshot) in (
                self._retained_page_snapshots.items()
            )
            if expires_at <= now
        ]
        for coordinate in expired:
            self._retained_page_snapshots.pop(coordinate, None)

    def _read_source(
        self, payload: JsonObject
    ) -> tuple[JsonObject, WorkspaceRepositoryObservationSnapshot]:
        values = _source_read_payload(payload)
        snapshot = self._session.current_snapshot
        if (
            values["expected_epoch"] != snapshot.epoch
            or values["expected_cursor"] != snapshot.cursor
            or values["expected_snapshot_digest"] != snapshot.snapshot_digest
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source snapshot is stale",
                retryable=True,
            )
        relative_path = cast(str, values["path"])
        entry = next(
            (item for item in snapshot.entries if item.path == relative_path), None
        )
        if entry is None:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source is not present in the current snapshot",
                retryable=True,
            )
        maximum = min(cast(int, values["max_bytes"]), self._source_read_max_bytes)
        if entry.size_bytes > maximum:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                "Workspace source exceeds the bounded read budget",
            )
        content, after = _read_confined_bytes(
            root=self._session.binding.root_path,
            relative_path=relative_path,
            maximum=maximum,
            entry=entry,
        )
        encoding = cast(str, values["encoding"])
        if encoding == "utf-8":
            try:
                encoded_content = content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise WorkspaceLocalSourceReadError(
                    LocalFailureCode.INVALID_REQUEST,
                    "Workspace source is not valid UTF-8",
                ) from error
        else:
            encoded_content = base64.b64encode(content).decode("ascii")
        return (
            {
                "authority_kind": "local_uncommitted",
                "binding_key": snapshot.binding_key,
                "epoch": snapshot.epoch,
                "cursor": snapshot.cursor,
                "snapshot_digest": snapshot.snapshot_digest,
                "path": relative_path,
                "size_bytes": len(content),
                "modified_ns": after.st_mtime_ns,
                "content_digest": f"sha256:{hashlib.sha256(content).hexdigest()}",
                "encoding": encoding,
                "content": encoded_content,
            },
            snapshot,
        )

    def _repository_query_read_source(
        self, payload: JsonObject
    ) -> tuple[JsonObject, WorkspaceRepositoryQuerySnapshot]:
        values = _repository_query_source_read_payload(payload)
        query_ref = cast(str, values["query_ref"])
        try:
            snapshot = self._session.query_snapshot(query_ref)
        except RuntimeError as error:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace repository query snapshot is unavailable",
                retryable=True,
            ) from error
        if (
            values["expected_epoch"] != snapshot.epoch
            or values["expected_cursor"] != snapshot.cursor
            or values["expected_query_digest"] != snapshot.query_digest
            or values["expected_snapshot_digest"] != snapshot.snapshot_digest
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace repository query source snapshot is stale",
                retryable=True,
            )
        relative_path = cast(str, values["path"])
        entry = next(
            (item for item in snapshot.entries if item.path == relative_path), None
        )
        if entry is None:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source is not present in the exact query snapshot",
                retryable=True,
            )
        maximum = min(cast(int, values["max_bytes"]), self._source_read_max_bytes)
        if entry.size_bytes > maximum:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                "Workspace source exceeds the bounded read budget",
            )
        content, after = _read_confined_bytes(
            root=self._session.binding.root_path,
            relative_path=relative_path,
            maximum=maximum,
            entry=entry,
        )
        try:
            encoded_content = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                "Workspace source is not valid UTF-8",
            ) from error
        return (
            {
                "authority_kind": "local_uncommitted",
                "binding_key": snapshot.binding_key,
                "epoch": snapshot.epoch,
                "cursor": snapshot.cursor,
                "query_ref": snapshot.query_ref,
                "query_digest": snapshot.query_digest,
                "snapshot_digest": snapshot.snapshot_digest,
                "path": relative_path,
                "size_bytes": len(content),
                "modified_ns": after.st_mtime_ns,
                "content_digest": f"sha256:{hashlib.sha256(content).hexdigest()}",
                "encoding": "utf-8",
                "content": encoded_content,
            },
            snapshot,
        )

    def _repository_query_read_source_chunk(
        self, payload: JsonObject
    ) -> tuple[JsonObject, WorkspaceRepositoryQuerySnapshot]:
        values = _repository_query_source_chunk_read_payload(payload)
        query_ref = cast(str, values["query_ref"])
        try:
            snapshot = self._session.query_snapshot(query_ref)
        except RuntimeError as error:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace repository query snapshot is unavailable",
                retryable=True,
            ) from error
        if (
            values["expected_binding_key"] != snapshot.binding_key
            or values["expected_epoch"] != snapshot.epoch
            or values["expected_cursor"] != snapshot.cursor
            or values["expected_query_digest"] != snapshot.query_digest
            or values["expected_snapshot_digest"] != snapshot.snapshot_digest
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace repository query source snapshot is stale",
                retryable=True,
            )
        relative_path = cast(str, values["path"])
        entry = next(
            (item for item in snapshot.entries if item.path == relative_path), None
        )
        if entry is None:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source is not present in the exact query snapshot",
                retryable=True,
            )
        maximum_document = cast(int, values["max_document_bytes"])
        if entry.size_bytes > maximum_document:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                "Workspace source exceeds the bounded document budget",
            )
        content, after = _read_confined_bytes(
            root=self._session.binding.root_path,
            relative_path=relative_path,
            maximum=maximum_document,
            entry=entry,
        )
        content_digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        expected_digest = cast(str | None, values["expected_content_digest"])
        if expected_digest is not None and expected_digest != content_digest:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source content changed between query chunks",
                retryable=True,
            )
        offset = cast(int, values["offset_bytes"])
        chunk_index = cast(int, values["chunk_index"])
        maximum_chunk = min(
            cast(int, values["chunk_size_bytes"]), self._source_read_max_bytes
        )
        if (
            offset != chunk_index * maximum_chunk
            or offset > len(content)
            or (offset == len(content) and len(content) != 0)
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                "Workspace source query chunk coordinate is invalid",
            )
        chunk = content[offset : offset + maximum_chunk]
        next_offset = offset + len(chunk)
        return (
            {
                "authority_kind": "local_uncommitted",
                "binding_key": snapshot.binding_key,
                "epoch": snapshot.epoch,
                "cursor": snapshot.cursor,
                "query_ref": snapshot.query_ref,
                "query_digest": snapshot.query_digest,
                "snapshot_digest": snapshot.snapshot_digest,
                "path": relative_path,
                "document_size_bytes": len(content),
                "modified_ns": after.st_mtime_ns,
                "content_digest": content_digest,
                "chunk_index": chunk_index,
                "offset_bytes": offset,
                "chunk_size_bytes": len(chunk),
                "chunk_size_limit_bytes": maximum_chunk,
                "next_offset_bytes": next_offset,
                "complete": next_offset == len(content),
                "encoding": "base64",
                "content": base64.b64encode(chunk).decode("ascii"),
            },
            snapshot,
        )

    def _repository_read_source(
        self, payload: JsonObject
    ) -> tuple[JsonObject, WorkspaceRepositoryObservationSnapshot]:
        values = _repository_source_read_payload(payload)
        snapshot = self._session.current_snapshot
        if (
            values["expected_binding_key"] != snapshot.binding_key
            or values["expected_epoch"] != snapshot.epoch
            or values["expected_cursor"] != snapshot.cursor
            or values["expected_snapshot_digest"] != snapshot.snapshot_digest
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace repository source snapshot is stale",
                retryable=True,
            )
        path = cast(str, values["path"])
        expected_entry_ref = repository_entry_ref(
            binding_ref=snapshot.binding_key,
            snapshot_digest=snapshot.snapshot_digest,
            path=path,
            kind=RepositoryEntryKind.REGULAR_FILE,
        )
        if values["entry_ref"] != expected_entry_ref:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace repository source entry identity is stale",
                retryable=True,
            )
        source_payload, exact_snapshot = self._read_source(
            {
                "path": path,
                "expected_epoch": snapshot.epoch,
                "expected_cursor": snapshot.cursor,
                "expected_snapshot_digest": snapshot.snapshot_digest,
                "encoding": values["encoding"],
                "max_bytes": values["max_bytes"],
            }
        )
        encoding = cast(str, values["encoding"])
        source_payload.update(
            {
                "contract_ref": WORKSPACE_REPOSITORY_ACCESS_CONTRACT_REF,
                "entry_ref": expected_entry_ref,
                "coordinate": {
                    "repository_binding_ref": snapshot.binding_key,
                    "epoch": snapshot.epoch,
                    "cursor": snapshot.cursor,
                    "snapshot_digest": snapshot.snapshot_digest,
                    "visibility_policy_ref": (
                        WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF
                    ),
                    "visibility_policy_version": (self._session.binding.filter_version),
                },
                "media_type": (
                    "text/plain; charset=utf-8"
                    if encoding == "utf-8"
                    else "application/octet-stream"
                ),
                "content_classification": ("text" if encoding == "utf-8" else "binary"),
                "complete": True,
            }
        )
        return source_payload, exact_snapshot

    def _read_source_chunk(
        self, payload: JsonObject
    ) -> tuple[JsonObject, WorkspaceRepositoryObservationSnapshot]:
        values = _source_chunk_read_payload(payload)
        snapshot = self._session.current_snapshot
        if (
            values["expected_binding_key"] != snapshot.binding_key
            or values["expected_epoch"] != snapshot.epoch
            or values["expected_cursor"] != snapshot.cursor
            or values["expected_snapshot_digest"] != snapshot.snapshot_digest
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source snapshot is stale",
                retryable=True,
            )
        relative_path = cast(str, values["path"])
        entry = next(
            (item for item in snapshot.entries if item.path == relative_path), None
        )
        if entry is None:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source is not present in the current snapshot",
                retryable=True,
            )
        maximum_document = cast(int, values["max_document_bytes"])
        if entry.size_bytes > maximum_document:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                "Workspace source exceeds the bounded document budget",
            )
        content, after = _read_confined_bytes(
            root=self._session.binding.root_path,
            relative_path=relative_path,
            maximum=maximum_document,
            entry=entry,
        )
        content_digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        expected_digest = cast(str | None, values["expected_content_digest"])
        if expected_digest is not None and expected_digest != content_digest:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source content changed between chunks",
                retryable=True,
            )
        offset = cast(int, values["offset_bytes"])
        chunk_index = cast(int, values["chunk_index"])
        maximum_chunk = min(
            cast(int, values["chunk_size_bytes"]), self._source_read_max_bytes
        )
        if (
            offset != chunk_index * maximum_chunk
            or offset > len(content)
            or (offset == len(content) and len(content) != 0)
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                "Workspace source chunk coordinate is invalid",
            )
        chunk = content[offset : offset + maximum_chunk]
        next_offset = offset + len(chunk)
        return (
            {
                "authority_kind": "local_uncommitted",
                "binding_key": snapshot.binding_key,
                "epoch": snapshot.epoch,
                "cursor": snapshot.cursor,
                "snapshot_digest": snapshot.snapshot_digest,
                "path": relative_path,
                "document_size_bytes": len(content),
                "modified_ns": after.st_mtime_ns,
                "content_digest": content_digest,
                "chunk_index": chunk_index,
                "offset_bytes": offset,
                "chunk_size_bytes": len(chunk),
                "chunk_size_limit_bytes": maximum_chunk,
                "next_offset_bytes": next_offset,
                "complete": next_offset == len(content),
                "encoding": "base64",
                "content": base64.b64encode(chunk).decode("ascii"),
            },
            snapshot,
        )

    async def replay_observations(
        self,
        *,
        topic_key: str,
        requested_epoch: str | None,
        after_cursor: int,
    ) -> LocalObservationReplay:
        if topic_key != WORKSPACE_SOURCE_CHANGES_TOPIC:
            raise ValueError(f"Unsupported Workspace observation topic: {topic_key}")
        replay = await self._session.replay(
            after_cursor=after_cursor,
            epoch=requested_epoch,
        )
        gap = None if replay.gap is None else _gap(replay.gap)
        envelopes = tuple(_batch_envelope(batch) for batch in replay.batches)
        return LocalObservationReplay(
            epoch=replay.epoch,
            after_cursor=replay.after_cursor,
            current_cursor=replay.current_cursor,
            envelopes=envelopes,
            gap=gap,
        )


def _success(
    request: LocalCallRequest,
    payload: JsonObject,
    *,
    snapshot: WorkspaceRepositoryObservationSnapshot | WorkspaceRepositoryQuerySnapshot,
) -> LocalCallResult:
    return LocalCallResult(
        capability_key=request.capability_key,
        operation_key=request.operation_key,
        correlation_id=request.correlation_id,
        status=LocalCallStatus.SUCCEEDED,
        payload=payload,
        participant_receipt={
            "authority_kind": "local_uncommitted",
            "binding_key": snapshot.binding_key,
            "epoch": snapshot.epoch,
            "cursor": snapshot.cursor,
            "snapshot_digest": snapshot.snapshot_digest,
        },
    )


def _success_unobserved(
    request: LocalCallRequest,
    payload: JsonObject,
) -> LocalCallResult:
    """Return provider-reported evidence without an invented observer receipt."""

    return LocalCallResult(
        capability_key=request.capability_key,
        operation_key=request.operation_key,
        correlation_id=request.correlation_id,
        status=LocalCallStatus.SUCCEEDED,
        payload=payload,
    )


def _repository_query_request(
    payload: JsonObject,
) -> tuple[
    RepositoryPathQuery,
    str | None,
    int,
    tuple[str, str, int, str, str] | None,
]:
    base = {
        "query_ref",
        "prefixes",
        "maximum_depth",
        "maximum_entries",
        "maximum_examined",
        "suffixes",
        "after_path",
        "limit",
    }
    coordinate_fields = {
        "expected_binding_key",
        "expected_epoch",
        "expected_cursor",
        "expected_query_digest",
        "expected_snapshot_digest",
    }
    if not base.issubset(payload) or not set(payload).issubset(
        base | coordinate_fields
    ):
        raise TypeError("repository_query payload fields are invalid")
    query_ref = payload.get("query_ref")
    prefixes = payload.get("prefixes")
    maximum_depth = payload.get("maximum_depth")
    maximum_entries = payload.get("maximum_entries")
    maximum_examined = payload.get("maximum_examined")
    suffixes = payload.get("suffixes")
    after_path = payload.get("after_path")
    limit = payload.get("limit")
    if not isinstance(query_ref, str) or not query_ref or len(query_ref) > 128:
        raise TypeError("repository_query query_ref is invalid")
    if (
        not isinstance(prefixes, list)
        or not prefixes
        or len(prefixes) > 16
        or any(not isinstance(value, str) for value in prefixes)
    ):
        raise TypeError("repository_query prefixes are invalid")
    if (
        not isinstance(suffixes, list)
        or len(suffixes) > 16
        or any(not isinstance(value, str) for value in suffixes)
    ):
        raise TypeError("repository_query suffixes are invalid")
    if (
        not isinstance(maximum_depth, int)
        or isinstance(maximum_depth, bool)
        or not 0 <= maximum_depth <= 32
        or not isinstance(maximum_entries, int)
        or isinstance(maximum_entries, bool)
        or not 1 <= maximum_entries <= 20_000
        or not isinstance(maximum_examined, int)
        or isinstance(maximum_examined, bool)
        or not maximum_entries <= maximum_examined <= 100_000
    ):
        raise TypeError("repository_query budgets are invalid")
    if after_path is not None and (not isinstance(after_path, str) or not after_path):
        raise TypeError("repository_query after_path is invalid")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 128:
        raise TypeError("repository_query page limit is invalid")
    query = RepositoryPathQuery(
        query_ref=query_ref,
        prefixes=tuple(cast(list[str], prefixes)),
        maximum_depth=maximum_depth,
        maximum_entries=maximum_entries,
        maximum_examined=maximum_examined,
        suffixes=tuple(cast(list[str], suffixes)),
    )
    if after_path is None:
        if coordinate_fields & set(payload):
            raise TypeError("repository_query first page cannot carry coordinates")
        expected_coordinate = None
    else:
        if not coordinate_fields.issubset(payload):
            raise TypeError("repository_query continuation requires coordinates")
        if (
            any(
                not isinstance(payload[field], str) or not payload[field]
                for field in (
                    "expected_binding_key",
                    "expected_epoch",
                    "expected_query_digest",
                    "expected_snapshot_digest",
                )
            )
            or not isinstance(payload["expected_cursor"], int)
            or isinstance(payload["expected_cursor"], bool)
            or cast(int, payload["expected_cursor"]) < 0
        ):
            raise TypeError("repository_query continuation coordinates are invalid")
        expected_coordinate = (
            cast(str, payload["expected_binding_key"]),
            cast(str, payload["expected_epoch"]),
            cast(int, payload["expected_cursor"]),
            cast(str, payload["expected_query_digest"]),
            cast(str, payload["expected_snapshot_digest"]),
        )
    return query, cast(str | None, after_path), limit, expected_coordinate


def _repository_query_payload(
    snapshot: WorkspaceRepositoryQuerySnapshot,
    *,
    after_path: str | None,
    limit: int,
) -> JsonObject:
    paths = [entry.path for entry in snapshot.entries]
    start = 0
    if after_path is not None:
        start = bisect.bisect_right(paths, after_path)
        if start == 0 or paths[start - 1] != after_path:
            raise ValueError(
                "repository_query continuation is not in the exact query snapshot"
            )
    selected = snapshot.entries[start : start + limit]
    complete = start + len(selected) >= len(snapshot.entries)
    return {
        "authority_kind": "local_uncommitted",
        "binding_key": snapshot.binding_key,
        "epoch": snapshot.epoch,
        "cursor": snapshot.cursor,
        "query_ref": snapshot.query_ref,
        "query_digest": snapshot.query_digest,
        "observed_at": snapshot.observed_at.isoformat(),
        "snapshot_digest": snapshot.snapshot_digest,
        "entry_count": len(snapshot.entries),
        "returned_count": len(selected),
        "after_path": after_path,
        "next_after_path": None if complete else selected[-1].path,
        "complete": complete,
        "examined_count": snapshot.examined_count,
        "truncated": snapshot.truncated,
        "inaccessible_count": snapshot.inaccessible_count,
        "changed_paths": list(snapshot.changed_paths),
        "entries": [_entry_payload(entry) for entry in selected],
    }


def _repository_query_source_read_payload(payload: JsonObject) -> JsonObject:
    required = {
        "query_ref",
        "path",
        "expected_epoch",
        "expected_cursor",
        "expected_query_digest",
        "expected_snapshot_digest",
    }
    optional = {"max_bytes"}
    if not required.issubset(payload) or not set(payload).issubset(required | optional):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_query_read_source payload fields are invalid",
        )
    string_fields = (
        "query_ref",
        "path",
        "expected_epoch",
        "expected_query_digest",
        "expected_snapshot_digest",
    )
    if any(
        not isinstance(payload.get(field), str) or not payload.get(field)
        for field in string_fields
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_query_read_source coordinates are invalid",
        )
    cursor = payload.get("expected_cursor")
    if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor < 0:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_query_read_source cursor is invalid",
        )
    try:
        canonical_path = PurePosixPath(cast(str, payload["path"]))
        if (
            canonical_path.is_absolute()
            or canonical_path.as_posix() != payload["path"]
            or any(part in {"", ".", ".."} for part in canonical_path.parts)
        ):
            raise ValueError
    except (TypeError, ValueError):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_query_read_source path is not confined",
        ) from None
    maximum = payload.get("max_bytes", DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES)
    if (
        not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or not 0 < maximum <= DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_query_read_source max_bytes is invalid",
        )
    return {**payload, "max_bytes": maximum}


def _repository_query_source_chunk_read_payload(
    payload: JsonObject,
) -> dict[str, object]:
    required = {
        "query_ref",
        "path",
        "expected_binding_key",
        "expected_epoch",
        "expected_cursor",
        "expected_query_digest",
        "expected_snapshot_digest",
        "expected_content_digest",
        "offset_bytes",
        "chunk_index",
        "chunk_size_bytes",
        "max_document_bytes",
    }
    if set(payload) != required:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_query_read_source_chunk payload fields are invalid",
        )
    common = _repository_query_source_read_payload(
        {
            "query_ref": payload["query_ref"],
            "path": payload["path"],
            "expected_epoch": payload["expected_epoch"],
            "expected_cursor": payload["expected_cursor"],
            "expected_query_digest": payload["expected_query_digest"],
            "expected_snapshot_digest": payload["expected_snapshot_digest"],
            "max_bytes": payload["chunk_size_bytes"],
        }
    )
    binding_key = payload["expected_binding_key"]
    expected_digest = payload["expected_content_digest"]
    offset = payload["offset_bytes"]
    chunk_index = payload["chunk_index"]
    chunk_size = payload["chunk_size_bytes"]
    maximum_document = payload["max_document_bytes"]
    if not isinstance(binding_key, str) or not binding_key:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "expected_binding_key must be a non-empty string",
        )
    if expected_digest is not None and (
        not isinstance(expected_digest, str)
        or not expected_digest.startswith("sha256:")
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "expected_content_digest must be a sha256 digest or null",
        )
    for name, value in (("offset_bytes", offset), ("chunk_index", chunk_index)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                f"{name} must be a non-negative integer",
            )
    if (
        not isinstance(chunk_size, int)
        or isinstance(chunk_size, bool)
        or not 0 < chunk_size <= DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "chunk_size_bytes exceeds the bounded source-read ceiling",
        )
    if (
        not isinstance(maximum_document, int)
        or isinstance(maximum_document, bool)
        or not 0 < maximum_document <= DEFAULT_WORKSPACE_SOURCE_DOCUMENT_MAX_BYTES
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "max_document_bytes exceeds the bounded document ceiling",
        )
    return {
        **common,
        "expected_binding_key": binding_key,
        "expected_content_digest": expected_digest,
        "offset_bytes": offset,
        "chunk_index": chunk_index,
        "chunk_size_bytes": chunk_size,
        "max_document_bytes": maximum_document,
    }


def _invalid(request: LocalCallRequest, message: str) -> LocalCallResult:
    return _failure(
        request,
        code=LocalFailureCode.INVALID_REQUEST,
        message=message,
    )


def _failure(
    request: LocalCallRequest,
    *,
    code: LocalFailureCode,
    message: str,
    retryable: bool = False,
) -> LocalCallResult:
    return LocalCallResult(
        capability_key=request.capability_key,
        operation_key=request.operation_key,
        correlation_id=request.correlation_id,
        status=LocalCallStatus.FAILED,
        failure=LocalFailure(code, message, retryable=retryable),
    )


def _snapshot_payload(snapshot: WorkspaceRepositoryObservationSnapshot) -> JsonObject:
    return {
        "authority_kind": "local_uncommitted",
        "binding_key": snapshot.binding_key,
        "epoch": snapshot.epoch,
        "cursor": snapshot.cursor,
        "observed_at": snapshot.observed_at.isoformat(),
        "snapshot_digest": snapshot.snapshot_digest,
        "entries": [_entry_payload(entry) for entry in snapshot.entries],
    }


def _snapshot_coordinate(
    snapshot: WorkspaceRepositoryObservationSnapshot,
) -> tuple[str, str, int, str]:
    return (
        snapshot.binding_key,
        snapshot.epoch,
        snapshot.cursor,
        snapshot.snapshot_digest,
    )


def _requested_snapshot_coordinate(
    payload: JsonObject,
) -> tuple[str, str, int, str] | None:
    binding = payload.get("expected_binding_key")
    epoch = payload.get("expected_epoch")
    cursor = payload.get("expected_cursor")
    digest = payload.get("expected_snapshot_digest")
    if (
        not isinstance(binding, str)
        or not isinstance(epoch, str)
        or not isinstance(cursor, int)
        or isinstance(cursor, bool)
        or not isinstance(digest, str)
    ):
        return None
    return binding, epoch, cursor, digest


def _snapshot_page_payload(
    snapshot: WorkspaceRepositoryObservationSnapshot,
    request_payload: JsonObject,
) -> JsonObject:
    coordinate_fields = {
        "expected_binding_key",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
    }
    allowed = coordinate_fields | {"after_path", "limit"}
    if set(request_payload) - allowed or not {"after_path", "limit"} <= set(
        request_payload
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "snapshot_page payload fields are invalid",
        )

    after_path = request_payload["after_path"]
    limit = request_payload["limit"]
    supplied_coordinates = coordinate_fields & set(request_payload)
    if supplied_coordinates and supplied_coordinates != coordinate_fields:
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "snapshot_page coordinates must be supplied together",
        )
    if after_path is not None and not supplied_coordinates:
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "snapshot_page continuation requires exact snapshot coordinates",
        )
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not (0 < limit <= DEFAULT_WORKSPACE_SNAPSHOT_PAGE_MAX_ENTRIES)
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "snapshot_page limit must be an integer from 1 through 128",
        )
    if after_path is not None:
        if not isinstance(after_path, str) or not after_path:
            raise WorkspaceLocalSnapshotPageError(
                LocalFailureCode.INVALID_REQUEST,
                "snapshot_page after_path must be null or a non-empty string",
            )
        normalized = PurePosixPath(after_path)
        if (
            normalized.is_absolute()
            or after_path != normalized.as_posix()
            or "\\" in after_path
            or any(part in {"", ".", ".."} for part in normalized.parts)
        ):
            raise WorkspaceLocalSnapshotPageError(
                LocalFailureCode.INVALID_REQUEST,
                "snapshot_page after_path must be a normalized relative path",
            )

    if supplied_coordinates:
        expected_binding = request_payload["expected_binding_key"]
        expected_epoch = request_payload["expected_epoch"]
        expected_cursor = request_payload["expected_cursor"]
        expected_digest = request_payload["expected_snapshot_digest"]
        if (
            not isinstance(expected_binding, str)
            or not isinstance(expected_epoch, str)
            or not isinstance(expected_cursor, int)
            or isinstance(expected_cursor, bool)
            or not isinstance(expected_digest, str)
        ):
            raise WorkspaceLocalSnapshotPageError(
                LocalFailureCode.INVALID_REQUEST,
                "snapshot_page coordinates have invalid types",
            )
        if (
            expected_binding != snapshot.binding_key
            or expected_epoch != snapshot.epoch
            or expected_cursor != snapshot.cursor
            or expected_digest != snapshot.snapshot_digest
        ):
            raise WorkspaceLocalSnapshotPageError(
                LocalFailureCode.CONFLICT,
                "Workspace snapshot changed before page continuation",
                retryable=True,
            )

    paths = tuple(entry.path for entry in snapshot.entries)
    start = 0
    if after_path is not None:
        start = bisect.bisect_left(paths, after_path)
        if start >= len(paths) or paths[start] != after_path:
            raise WorkspaceLocalSnapshotPageError(
                LocalFailureCode.INVALID_REQUEST,
                "snapshot_page after_path is not present in the exact snapshot",
            )
        start += 1
    selected_payloads: list[JsonObject] = []
    selected_entries: list[RepositorySnapshotEntry] = []
    encoded_entries_bytes = 2
    for entry in snapshot.entries[start : start + limit]:
        if len(entry.path) > DEFAULT_WORKSPACE_SNAPSHOT_PAGE_MAX_PATH_CHARS:
            raise WorkspaceLocalSnapshotPageError(
                LocalFailureCode.PROVIDER_FAILURE,
                "Workspace snapshot entry path exceeds the Local Service text budget",
            )
        entry_payload = _entry_payload(entry)
        encoded_entry_bytes = len(
            json.dumps(
                entry_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        candidate_bytes = (
            encoded_entries_bytes
            + encoded_entry_bytes
            + (1 if selected_payloads else 0)
        )
        if candidate_bytes > DEFAULT_WORKSPACE_SNAPSHOT_PAGE_MAX_BYTES:
            break
        selected_entries.append(entry)
        selected_payloads.append(entry_payload)
        encoded_entries_bytes = candidate_bytes
    if not selected_entries and start < len(snapshot.entries):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.PROVIDER_FAILURE,
            "Workspace snapshot entry exceeds the bounded page payload",
        )
    complete = start + len(selected_entries) >= len(snapshot.entries)
    return {
        "authority_kind": "local_uncommitted",
        "binding_key": snapshot.binding_key,
        "epoch": snapshot.epoch,
        "cursor": snapshot.cursor,
        "observed_at": snapshot.observed_at.isoformat(),
        "snapshot_digest": snapshot.snapshot_digest,
        "entry_count": len(snapshot.entries),
        "returned_count": len(selected_entries),
        "after_path": after_path,
        "next_after_path": (
            None if complete or not selected_entries else selected_entries[-1].path
        ),
        "complete": complete,
        "entries": selected_payloads,
    }


def _entry_payload(entry: RepositorySnapshotEntry) -> JsonObject:
    return {
        "path": entry.path,
        "size_bytes": entry.size_bytes,
        "modified_ns": entry.modified_ns,
        "content_digest": entry.content_digest,
    }


def _change_payload(change: RepositoryObservationChange) -> JsonObject:
    return {
        "kind": change.kind.value,
        "path": change.path,
        "entry": None if change.entry is None else _entry_payload(change.entry),
    }


def _batch_payload(batch: WorkspaceRepositoryObservationBatch) -> JsonObject:
    return {
        "binding_key": batch.binding_key,
        "epoch": batch.epoch,
        "cursor": batch.cursor,
        "observed_at": batch.observed_at.isoformat(),
        "before_snapshot_digest": batch.before_snapshot_digest,
        "after_snapshot_digest": batch.after_snapshot_digest,
        "changes": [_change_payload(change) for change in batch.changes],
        "coalesced": batch.coalesced,
    }


def _health_payload(health: WorkspaceRepositoryObservationHealth) -> JsonObject:
    return {
        "state": health.state.value,
        "epoch": health.epoch,
        "cursor": health.cursor,
        "files_tracked": health.files_tracked,
        "journal_size": health.journal_size,
        "consecutive_failures": health.consecutive_failures,
        "last_error": health.last_error,
        "last_observed_at": (
            None
            if health.last_observed_at is None
            else health.last_observed_at.isoformat()
        ),
    }


def _delta_resident_payload(
    resident: WorkspaceRepositoryDeltaResident,
) -> JsonObject:
    snapshot = resident.snapshot()
    store = snapshot.store
    store_metrics = store.metrics
    capture = snapshot.capture
    return {
        "repository_binding_ref": snapshot.repository_binding_ref,
        "state": snapshot.state.value,
        "epoch": snapshot.epoch,
        "observed_cursor": snapshot.observed_cursor,
        "last_error": snapshot.last_error,
        "store": {
            "retained_body_count": store.retained_body_count,
            "retained_body_bytes": store.retained_body_bytes,
            "retained_capture_count": store.retained_capture_count,
            "retained_delta_count": store.retained_delta_count,
            "body_hash_count": store_metrics.body_hash_count,
            "body_read_count": store_metrics.body_read_count,
            "body_read_bytes": store_metrics.body_read_bytes,
            "body_write_count": store_metrics.body_write_count,
            "body_write_bytes": store_metrics.body_write_bytes,
            "index_write_count": store_metrics.index_write_count,
            "evicted_body_count": store_metrics.evicted_body_count,
            "evicted_capture_count": store_metrics.evicted_capture_count,
            "evicted_delta_count": store_metrics.evicted_delta_count,
        },
        "capture": {
            "preparation_count": capture.preparation_count,
            "observed_batch_count": capture.observed_batch_count,
            "no_change_count": capture.no_change_count,
            "selected_body_read_count": capture.selected_body_read_count,
            "selected_body_read_bytes": capture.selected_body_read_bytes,
            "changed_body_read_count": capture.changed_body_read_count,
            "changed_body_read_bytes": capture.changed_body_read_bytes,
            "unstable_body_count": capture.unstable_body_count,
            "over_budget_body_count": capture.over_budget_body_count,
        },
    }


def _batch_envelope(
    batch: WorkspaceRepositoryObservationBatch,
) -> LocalObservationEnvelope:
    return LocalObservationEnvelope(
        capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
        topic_key=WORKSPACE_SOURCE_CHANGES_TOPIC,
        epoch=batch.epoch,
        cursor=batch.cursor,
        kind=LocalObservationKind.DELTA,
        observed_at=batch.observed_at,
        authority_kind="local_uncommitted",
        payload=_batch_payload(batch),
        source_correlation={
            "binding_key": batch.binding_key,
            "before_snapshot_digest": batch.before_snapshot_digest,
            "after_snapshot_digest": batch.after_snapshot_digest,
        },
    )


def _snapshot_envelope(
    snapshot: WorkspaceRepositoryObservationSnapshot,
) -> LocalObservationEnvelope:
    return LocalObservationEnvelope(
        capability_key=WORKSPACE_LOCAL_SERVICE_CAPABILITY,
        topic_key=WORKSPACE_SOURCE_CHANGES_TOPIC,
        epoch=snapshot.epoch,
        cursor=snapshot.cursor,
        kind=LocalObservationKind.SNAPSHOT,
        observed_at=snapshot.observed_at,
        authority_kind="local_uncommitted",
        payload=_snapshot_payload(snapshot),
        source_correlation={
            "binding_key": snapshot.binding_key,
            "snapshot_digest": snapshot.snapshot_digest,
        },
    )


def _gap(gap: WorkspaceRepositoryObservationGap) -> LocalObservationGap:
    return LocalObservationGap(
        reason=LocalObservationGapReason(gap.reason.value),
        requested_epoch=gap.requested_epoch,
        available_epoch=gap.available_epoch,
        requested_after_cursor=gap.requested_after_cursor,
        oldest_available_cursor=gap.oldest_available_cursor,
        current_cursor=gap.current_cursor,
        reset_snapshot=_snapshot_envelope(gap.reset_snapshot),
    )


def _acknowledgement_payload(payload: JsonObject) -> dict[str, object]:
    allowed = {"consumer_key", "epoch", "cursor", "projection_digest"}
    if set(payload) - allowed or not {"consumer_key", "epoch", "cursor"} <= set(
        payload
    ):
        raise ValueError("acknowledge payload fields are invalid")
    consumer_key = payload["consumer_key"]
    epoch = payload["epoch"]
    cursor = payload["cursor"]
    projection_digest = payload.get("projection_digest")
    if not isinstance(consumer_key, str) or not isinstance(epoch, str):
        raise TypeError("consumer_key and epoch must be strings")
    if not isinstance(cursor, int) or isinstance(cursor, bool):
        raise TypeError("cursor must be an integer")
    if projection_digest is not None and not isinstance(projection_digest, str):
        raise TypeError("projection_digest must be a string or null")
    return {
        "consumer_key": consumer_key,
        "epoch": epoch,
        "cursor": cursor,
        "projection_digest": cast(str | None, projection_digest),
    }


def _agent_source_mutation_request(
    request: LocalCallRequest,
    *,
    session: WorkspaceRepositoryObservationSession,
) -> WorkspaceRepositoryMutationRequest:
    required = {
        "mutation_kind",
        "path",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
        "expected_exists",
        "expected_content_digest",
        "encoding",
        "content",
    }
    allowed = required | {"text_replacements"}
    if set(request.payload) - allowed or not required <= set(request.payload):
        raise ValueError("mutate_source payload fields are invalid")
    idempotency_key = request.idempotency_key
    if idempotency_key is None:
        raise ValueError("mutate_source requires Local Service idempotency")
    mutation_kind = RepositoryMutationKind(request.payload["mutation_kind"])
    path = request.payload["path"]
    epoch = request.payload["expected_epoch"]
    cursor = request.payload["expected_cursor"]
    snapshot_digest = request.payload["expected_snapshot_digest"]
    expected_exists = request.payload["expected_exists"]
    expected_digest = request.payload["expected_content_digest"]
    encoding = request.payload["encoding"]
    encoded_content = request.payload["content"]
    replacement_values = request.payload.get("text_replacements")
    if not isinstance(path, str) or not path:
        raise ValueError("mutate_source path must be a non-empty string")
    if not isinstance(epoch, str) or not epoch:
        raise ValueError("mutate_source expected_epoch must be non-empty")
    if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor < 0:
        raise ValueError("mutate_source expected_cursor must be non-negative")
    if not isinstance(snapshot_digest, str) or not snapshot_digest:
        raise ValueError("mutate_source snapshot digest must be non-empty")
    if not isinstance(expected_exists, bool):
        raise ValueError("mutate_source expected_exists must be boolean")
    if expected_digest is not None and not isinstance(expected_digest, str):
        raise ValueError("mutate_source expected digest must be text or null")
    if mutation_kind is RepositoryMutationKind.DELETE:
        if (
            encoding is not None
            or encoded_content is not None
            or replacement_values is not None
        ):
            raise ValueError("mutate_source delete cannot carry content")
        content = None
        replacements: tuple[WorkspaceRepositoryTextReplacement, ...] = ()
    elif replacement_values is not None:
        if (
            mutation_kind is not RepositoryMutationKind.UPDATE
            or encoding is not None
            or encoded_content is not None
            or not isinstance(replacement_values, list)
            or not 0 < len(replacement_values) <= 64
        ):
            raise ValueError("mutate_source text replacements are invalid")
        parsed_replacements: list[WorkspaceRepositoryTextReplacement] = []
        for value in replacement_values:
            if not isinstance(value, dict) or set(value) != {"old_text", "new_text"}:
                raise ValueError("mutate_source text replacement fields are invalid")
            old_text = value["old_text"]
            new_text = value["new_text"]
            if not isinstance(old_text, str) or not isinstance(new_text, str):
                raise ValueError("mutate_source text replacements must be text")
            parsed_replacements.append(
                WorkspaceRepositoryTextReplacement(
                    old_text=old_text,
                    new_text=new_text,
                )
            )
        replacements = tuple(parsed_replacements)
        content = None
    else:
        if not isinstance(encoded_content, str) or encoding not in {"utf-8", "base64"}:
            raise ValueError("mutate_source content and encoding are required")
        if encoding == "utf-8":
            content = encoded_content.encode("utf-8")
        else:
            try:
                content = base64.b64decode(encoded_content, validate=True)
            except ValueError as error:
                raise ValueError(
                    "mutate_source content must be canonical base64"
                ) from error
            if base64.b64encode(content).decode("ascii") != encoded_content:
                raise ValueError("mutate_source content must be canonical base64")
        if len(content) > WORKSPACE_AGENT_SOURCE_MUTATION_MAX_BYTES:
            raise ValueError("mutate_source content exceeds the bounded byte limit")
        replacements = ()
    binding_ref = session.binding.binding_key
    if binding_ref is None:
        raise ValueError("mutate_source repository binding is unavailable")
    observation = RepositoryObservationCoordinate(
        repository_binding_ref=binding_ref,
        epoch=epoch,
        cursor=cursor,
        snapshot_digest=snapshot_digest,
        visibility_policy_ref=WORKSPACE_REPOSITORY_VISIBILITY_POLICY_REF,
        visibility_policy_version=session.binding.filter_version,
    )
    return WorkspaceRepositoryMutationRequest(
        operation_ref=request.correlation_id,
        idempotency_key=idempotency_key,
        mutation_kind=mutation_kind,
        expected_coordinate=WorkspaceRepositoryEvidenceCoordinate(
            kind=RepositoryEvidenceCoordinateKind.OBSERVATION,
            repository_binding_ref=binding_ref,
            state_digest=snapshot_digest,
            observation=observation,
        ),
        target_path=path,
        expected_exists=expected_exists,
        expected_content_digest=cast(str | None, expected_digest),
        content=content,
        text_replacements=replacements,
        maximum_bytes=WORKSPACE_AGENT_SOURCE_MUTATION_MAX_BYTES,
    )


def _source_read_payload(payload: JsonObject) -> dict[str, object]:
    required = {
        "path",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
        "encoding",
    }
    allowed = required | {"max_bytes"}
    if set(payload) - allowed or not required <= set(payload):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "read_source payload fields are invalid",
        )

    relative_path = payload["path"]
    epoch = payload["expected_epoch"]
    cursor = payload["expected_cursor"]
    snapshot_digest = payload["expected_snapshot_digest"]
    encoding = payload["encoding"]
    maximum = payload.get("max_bytes", DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES)

    if not isinstance(relative_path, str) or not relative_path:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "read_source path must be a non-empty string",
        )
    path = PurePosixPath(relative_path)
    if (
        path.is_absolute()
        or relative_path != path.as_posix()
        or "\\" in relative_path
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "read_source path must be canonical and repository-relative",
        )
    if not isinstance(epoch, str) or not epoch:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "expected_epoch must be a non-empty string",
        )
    if not isinstance(cursor, int) or isinstance(cursor, bool) or cursor < 0:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "expected_cursor must be a non-negative integer",
        )
    if not isinstance(snapshot_digest, str) or not snapshot_digest:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "expected_snapshot_digest must be a non-empty string",
        )
    if encoding not in {"utf-8", "base64"}:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "encoding must be utf-8 or base64",
        )
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum <= 0:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "max_bytes must be a positive integer",
        )
    return {
        "path": relative_path,
        "expected_epoch": epoch,
        "expected_cursor": cursor,
        "expected_snapshot_digest": snapshot_digest,
        "encoding": encoding,
        "max_bytes": maximum,
    }


def _repository_children_request(
    payload: JsonObject,
    snapshot: WorkspaceRepositoryObservationSnapshot,
) -> dict[str, object]:
    required = {
        "parent_path",
        "continuation_ref",
        "limit",
        "expected_binding_key",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
    }
    if set(payload) != required:
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_children payload fields are invalid",
        )
    parent_path = payload["parent_path"]
    continuation_ref = payload["continuation_ref"]
    limit = payload["limit"]
    binding = payload["expected_binding_key"]
    epoch = payload["expected_epoch"]
    cursor = payload["expected_cursor"]
    digest = payload["expected_snapshot_digest"]
    if not isinstance(parent_path, str):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_children parent_path must be a string",
        )
    if continuation_ref is not None and (
        not isinstance(continuation_ref, str) or not continuation_ref
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_children continuation_ref must be non-empty or null",
        )
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 0 < limit <= DEFAULT_REPOSITORY_CHILD_PAGE_MAX_ENTRIES
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_children limit must be from 1 through 128",
        )
    if (
        not isinstance(binding, str)
        or not binding
        or not isinstance(epoch, str)
        or not epoch
        or not isinstance(cursor, int)
        or isinstance(cursor, bool)
        or cursor < 0
        or not isinstance(digest, str)
        or not digest
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_children coordinates are invalid",
        )
    if (
        binding != snapshot.binding_key
        or epoch != snapshot.epoch
        or cursor != snapshot.cursor
        or digest != snapshot.snapshot_digest
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.CONFLICT,
            "Workspace repository catalog coordinate is stale",
            retryable=True,
        )
    return {
        "parent_path": parent_path,
        "continuation_ref": continuation_ref,
        "limit": limit,
    }


def _repository_path_search_request(
    payload: JsonObject,
) -> WorkspaceRepositoryPathSearchRequest:
    required = {
        "query_ref",
        "query",
        "continuation_ref",
        "maximum_results",
        "maximum_examined",
        "expected_binding_key",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
        "expected_visibility_policy_ref",
        "expected_visibility_policy_version",
    }
    if set(payload) != required:
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_search_paths payload fields are invalid",
        )
    query_ref = payload["query_ref"]
    query = payload["query"]
    continuation_ref = payload["continuation_ref"]
    maximum_results = payload["maximum_results"]
    maximum_examined = payload["maximum_examined"]
    binding = payload["expected_binding_key"]
    epoch = payload["expected_epoch"]
    cursor = payload["expected_cursor"]
    digest = payload["expected_snapshot_digest"]
    policy_ref = payload["expected_visibility_policy_ref"]
    policy_version = payload["expected_visibility_policy_version"]
    if (
        not isinstance(query_ref, str)
        or not query_ref
        or not isinstance(query, str)
        or not query.strip()
        or (
            continuation_ref is not None
            and (not isinstance(continuation_ref, str) or not continuation_ref)
        )
        or not isinstance(maximum_results, int)
        or isinstance(maximum_results, bool)
        or not 0 < maximum_results <= MAX_REPOSITORY_PATH_SEARCH_RESULTS
        or not isinstance(maximum_examined, int)
        or isinstance(maximum_examined, bool)
        or maximum_examined < maximum_results
        or maximum_examined > MAX_REPOSITORY_PATH_SEARCH_EXAMINED
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_search_paths query or budgets are invalid",
        )
    if (
        not isinstance(binding, str)
        or not binding
        or not isinstance(epoch, str)
        or not epoch
        or not isinstance(cursor, int)
        or isinstance(cursor, bool)
        or cursor < 0
        or not isinstance(digest, str)
        or not digest
        or not isinstance(policy_ref, str)
        or not policy_ref
        or not isinstance(policy_version, str)
        or not policy_version
    ):
        raise WorkspaceLocalSnapshotPageError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_search_paths coordinate is invalid",
        )
    return WorkspaceRepositoryPathSearchRequest(
        query_ref=query_ref,
        query=query,
        continuation_ref=cast(str | None, continuation_ref),
        maximum_results=maximum_results,
        maximum_examined=maximum_examined,
        expected_coordinate=RepositoryObservationCoordinate(
            repository_binding_ref=binding,
            epoch=epoch,
            cursor=cursor,
            snapshot_digest=digest,
            visibility_policy_ref=policy_ref,
            visibility_policy_version=policy_version,
        ),
    )


def _repository_source_read_payload(payload: JsonObject) -> dict[str, object]:
    required = {
        "entry_ref",
        "path",
        "expected_binding_key",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
        "encoding",
        "max_bytes",
    }
    if set(payload) != required:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_read_source payload fields are invalid",
        )
    values = _source_read_payload(
        {
            "path": payload["path"],
            "expected_epoch": payload["expected_epoch"],
            "expected_cursor": payload["expected_cursor"],
            "expected_snapshot_digest": payload["expected_snapshot_digest"],
            "encoding": payload["encoding"],
            "max_bytes": payload["max_bytes"],
        }
    )
    entry_ref = payload["entry_ref"]
    binding = payload["expected_binding_key"]
    if not isinstance(entry_ref, str) or not entry_ref:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_read_source entry_ref must be non-empty",
        )
    if not isinstance(binding, str) or not binding:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "repository_read_source binding coordinate must be non-empty",
        )
    return {
        **values,
        "entry_ref": entry_ref,
        "expected_binding_key": binding,
    }


def _source_chunk_read_payload(payload: JsonObject) -> dict[str, object]:
    required = {
        "path",
        "expected_binding_key",
        "expected_epoch",
        "expected_cursor",
        "expected_snapshot_digest",
        "expected_content_digest",
        "offset_bytes",
        "chunk_index",
        "chunk_size_bytes",
        "max_document_bytes",
    }
    if set(payload) != required:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "read_source_chunk payload fields are invalid",
        )
    common = _source_read_payload(
        {
            "path": payload["path"],
            "expected_epoch": payload["expected_epoch"],
            "expected_cursor": payload["expected_cursor"],
            "expected_snapshot_digest": payload["expected_snapshot_digest"],
            "encoding": "base64",
            "max_bytes": payload["chunk_size_bytes"],
        }
    )
    binding_key = payload["expected_binding_key"]
    expected_digest = payload["expected_content_digest"]
    offset = payload["offset_bytes"]
    chunk_index = payload["chunk_index"]
    chunk_size = payload["chunk_size_bytes"]
    maximum_document = payload["max_document_bytes"]
    if not isinstance(binding_key, str) or not binding_key:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "expected_binding_key must be a non-empty string",
        )
    if expected_digest is not None and (
        not isinstance(expected_digest, str)
        or not expected_digest.startswith("sha256:")
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "expected_content_digest must be a sha256 digest or null",
        )
    for name, value in (("offset_bytes", offset), ("chunk_index", chunk_index)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.INVALID_REQUEST,
                f"{name} must be a non-negative integer",
            )
    if (
        not isinstance(chunk_size, int)
        or isinstance(chunk_size, bool)
        or not 0 < chunk_size <= DEFAULT_WORKSPACE_SOURCE_READ_MAX_BYTES
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "chunk_size_bytes exceeds the bounded source-read ceiling",
        )
    if (
        not isinstance(maximum_document, int)
        or isinstance(maximum_document, bool)
        or not 0 < maximum_document <= DEFAULT_WORKSPACE_SOURCE_DOCUMENT_MAX_BYTES
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INVALID_REQUEST,
            "max_document_bytes exceeds the bounded document ceiling",
        )
    return {
        **common,
        "expected_binding_key": binding_key,
        "expected_content_digest": expected_digest,
        "offset_bytes": offset,
        "chunk_index": chunk_index,
        "chunk_size_bytes": chunk_size,
        "max_document_bytes": maximum_document,
    }


def _read_confined_bytes(
    *,
    root: os.PathLike[str],
    relative_path: str,
    maximum: int,
    entry: RepositorySnapshotEntry,
) -> tuple[bytes, os.stat_result]:
    if not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.INTERNAL_FAILURE,
            "Secure confined source reads are unavailable on this platform",
        )
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        current = os.open(root, directory_flags)
        descriptors.append(current)
        parts = PurePosixPath(relative_path).parts
        for part in parts[:-1]:
            current = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(current)
        source = os.open(parts[-1], file_flags, dir_fd=current)
        descriptors.append(source)
        before = os.fstat(source)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size != entry.size_bytes
            or before.st_mtime_ns != entry.modified_ns
        ):
            raise WorkspaceLocalSourceReadError(
                LocalFailureCode.CONFLICT,
                "Workspace source metadata changed after observation",
                retryable=True,
            )
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(source, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(source)
    except WorkspaceLocalSourceReadError:
        raise
    except OSError as error:
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.CONFLICT,
            "Workspace source is unavailable, changed, or contains a symlink",
            retryable=True,
        ) from error
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    if (
        len(content) != entry.size_bytes
        or len(content) > maximum
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
    ):
        raise WorkspaceLocalSourceReadError(
            LocalFailureCode.CONFLICT,
            "Workspace source changed during read",
            retryable=True,
        )
    return content, after
