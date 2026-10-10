# pyright: reportConstantRedefinition=false, reportImportCycles=false
"""Dormant sequential executor for one admitted semantic materialization graph."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from threading import RLock
from typing import Never, cast
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticBody,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_local_service_runtime import JsonObject, LocalOperationalStateRecord

from .materialization_operation import (
    WorkspaceMaterializeOperation,
    WorkspaceMaterializeOperationAdmission,
    _admit_workspace_semantic_materialization_graph_node_execution,
    _revoke_workspace_semantic_materialization_graph_node_execution,
)
from .materialization_session import (
    WorkspaceMaterializationSessionAppendRequestV3,
    WorkspaceMaterializationSessionAuthorityGrade,
    WorkspaceMaterializationSessionEventV3,
    WorkspaceMaterializationSessionHead,
    WorkspaceMaterializationSessionHeadV2,
    WorkspaceMaterializationSessionJournal,
    WorkspaceMaterializationSessionSourceEvidenceV3,
    _create_graph_v2_session_append_request,
    _create_graph_v2_session_source_evidence,
)
from .semantic_dependency_graph import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3,
    WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2,
    WorkspaceFulfilledDependencyProductV3,
    WorkspaceSemanticMaterializationGraphEdge,
    WorkspaceSemanticMaterializationGraphPlanResult,
    WorkspaceSemanticMaterializationGraphResultV3,
    WorkspaceSemanticMaterializationNodeExecutionBinding,
    WorkspaceSemanticMaterializationNodeResultEvidenceV3,
    WorkspaceSemanticMaterializationResultCounterEntryV2,
    WorkspaceSemanticMaterializationTerminalEvidenceContextV3,
    WorkspaceSemanticMaterializationTerminalFailureV3,
    WorkspaceSemanticPackageHeadObservation,
    _coordinator_fulfilled_product_wire,
    _create_coordinator_fulfilled_dependency_product_v2,
    _create_coordinator_graph_result_v2,
    _create_coordinator_node_result_evidence_v2,
)
from .semantic_materialization_publication import (
    WorkspaceSemanticMaterializationHeadRereadEvidenceV3,
)

WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_HEAD_V1 = (
    "aware.workspace.semantic-materialization-production-cutover-head.v1"
)
WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_NAMESPACE_V1 = (
    WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_HEAD_V1
)
WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_KEY_V1 = "current"
_CUTOVER_DIGEST_DOMAIN = (
    b"aware.workspace.semantic-materialization-production-cutover-head.v1\x00"
)


@dataclass(frozen=True, slots=True)
class _WorkspaceMaterializationProductionWriterEvidenceV1:
    managed_release_channel_revision: int
    managed_release_channel_pointer_digest: str
    current_release_set_digest: str
    writer_release_set_digests: tuple[str, ...]
    managed_provider_generation_lineage_ref: str
    managed_release_authority_evidence_digest: str

    def __post_init__(self) -> None:
        _cutover_positive(self.managed_release_channel_revision, "channel_revision")
        _cutover_digest(self.managed_release_channel_pointer_digest, "pointer_digest")
        _cutover_digest(self.current_release_set_digest, "current_release_set_digest")
        _cutover_ref(
            self.managed_provider_generation_lineage_ref,
            "managed_provider_generation_lineage_ref",
            512,
        )
        _cutover_digest(
            self.managed_release_authority_evidence_digest,
            "managed_release_authority_evidence_digest",
        )
        if (
            type(self.writer_release_set_digests) is not tuple
            or not self.writer_release_set_digests
        ):
            raise TypeError("writer release-set digests must be a nonempty exact tuple")
        values = tuple(
            _cutover_digest(item, "writer_release_set_digest")
            for item in self.writer_release_set_digests
        )
        if values != tuple(sorted(set(values), key=str.encode)):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "writer release-set digests must be unique canonical order"
            )
        if self.current_release_set_digest not in values:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "current release set is absent from writer closure"
            )


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializationProductionCutoverHeadV1:
    contract: str
    workspace_authority_root_ref: str
    workspace_authority_root_digest: str
    cutover_epoch: str
    revision: int
    predecessor_head_digest: str | None
    writer_generation: str
    managed_release_channel_revision: int
    managed_release_channel_pointer_digest: str
    current_release_set_digest: str
    writer_release_set_digests: tuple[str, ...]
    managed_provider_generation_lineage_ref: str
    managed_release_authority_evidence_digest: str
    head_digest: str

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_HEAD_V1:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "cutover head contract differs"
            )
        _cutover_ref(
            self.workspace_authority_root_ref, "workspace_authority_root_ref", 512
        )
        _cutover_digest(
            self.workspace_authority_root_digest, "workspace_authority_root_digest"
        )
        _cutover_ref(self.cutover_epoch, "cutover_epoch", 128)
        revision = _cutover_positive(self.revision, "revision")
        if revision == 1:
            if self.predecessor_head_digest is not None:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "genesis cutover head must have typed-empty predecessor"
                )
        elif self.predecessor_head_digest is None:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "successor cutover head requires predecessor digest"
            )
        if self.predecessor_head_digest is not None:
            _cutover_digest(self.predecessor_head_digest, "predecessor_head_digest")
        if self.writer_generation != "graph_v2":
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "cutover writer generation differs"
            )
        evidence = _WorkspaceMaterializationProductionWriterEvidenceV1(
            managed_release_channel_revision=self.managed_release_channel_revision,
            managed_release_channel_pointer_digest=self.managed_release_channel_pointer_digest,
            current_release_set_digest=self.current_release_set_digest,
            writer_release_set_digests=self.writer_release_set_digests,
            managed_provider_generation_lineage_ref=self.managed_provider_generation_lineage_ref,
            managed_release_authority_evidence_digest=self.managed_release_authority_evidence_digest,
        )
        evidence.__post_init__()
        if self.head_digest != _cutover_head_digest(self._body_without_digest()):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "cutover head digest differs"
            )

    def _body_without_digest(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "workspace_authority_root_ref": self.workspace_authority_root_ref,
            "workspace_authority_root_digest": self.workspace_authority_root_digest,
            "cutover_epoch": self.cutover_epoch,
            "revision": self.revision,
            "predecessor_head_digest": self.predecessor_head_digest,
            "writer_generation": self.writer_generation,
            "managed_release_channel_revision": self.managed_release_channel_revision,
            "managed_release_channel_pointer_digest": self.managed_release_channel_pointer_digest,
            "current_release_set_digest": self.current_release_set_digest,
            "writer_release_set_digests": list(self.writer_release_set_digests),
            "managed_provider_generation_lineage_ref": self.managed_provider_generation_lineage_ref,
            "managed_release_authority_evidence_digest": self.managed_release_authority_evidence_digest,
        }

    def to_wire(self) -> bytes:
        self.__post_init__()
        return _cutover_canonical_bytes(
            {**self._body_without_digest(), "head_digest": self.head_digest}
        )

    def to_state(self) -> JsonObject:
        return cast(JsonObject, json.loads(self.to_wire()))


def _create_workspace_materialization_production_writer_evidence_v1(
    *,
    managed_release_channel_revision: int,
    managed_release_channel_pointer_digest: str,
    current_release_set_digest: str,
    writer_release_set_digests: tuple[str, ...],
    managed_provider_generation_lineage_ref: str,
    managed_release_authority_evidence_digest: str,
) -> _WorkspaceMaterializationProductionWriterEvidenceV1:
    """Type-only adapter target; production provenance is retained by Local Dev."""

    return _WorkspaceMaterializationProductionWriterEvidenceV1(
        managed_release_channel_revision=managed_release_channel_revision,
        managed_release_channel_pointer_digest=managed_release_channel_pointer_digest,
        current_release_set_digest=current_release_set_digest,
        writer_release_set_digests=writer_release_set_digests,
        managed_provider_generation_lineage_ref=managed_provider_generation_lineage_ref,
        managed_release_authority_evidence_digest=managed_release_authority_evidence_digest,
    )


def _create_workspace_materialization_production_cutover_head_v1(
    *,
    workspace_authority_root_ref: str,
    workspace_authority_root_digest: str,
    cutover_epoch: str,
    revision: int,
    predecessor_head_digest: str | None,
    writer_evidence: _WorkspaceMaterializationProductionWriterEvidenceV1,
) -> WorkspaceMaterializationProductionCutoverHeadV1:
    if type(writer_evidence) is not _WorkspaceMaterializationProductionWriterEvidenceV1:
        raise TypeError("cutover writer evidence must be exact")
    writer_evidence.__post_init__()
    body = {
        "contract": WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_HEAD_V1,
        "workspace_authority_root_ref": workspace_authority_root_ref,
        "workspace_authority_root_digest": workspace_authority_root_digest,
        "cutover_epoch": cutover_epoch,
        "revision": revision,
        "predecessor_head_digest": predecessor_head_digest,
        "writer_generation": "graph_v2",
        "managed_release_channel_revision": writer_evidence.managed_release_channel_revision,
        "managed_release_channel_pointer_digest": writer_evidence.managed_release_channel_pointer_digest,
        "current_release_set_digest": writer_evidence.current_release_set_digest,
        "writer_release_set_digests": writer_evidence.writer_release_set_digests,
        "managed_provider_generation_lineage_ref": writer_evidence.managed_provider_generation_lineage_ref,
        "managed_release_authority_evidence_digest": writer_evidence.managed_release_authority_evidence_digest,
    }
    return WorkspaceMaterializationProductionCutoverHeadV1(
        contract=WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_HEAD_V1,
        workspace_authority_root_ref=workspace_authority_root_ref,
        workspace_authority_root_digest=workspace_authority_root_digest,
        cutover_epoch=cutover_epoch,
        revision=revision,
        predecessor_head_digest=predecessor_head_digest,
        writer_generation="graph_v2",
        managed_release_channel_revision=(
            writer_evidence.managed_release_channel_revision
        ),
        managed_release_channel_pointer_digest=(
            writer_evidence.managed_release_channel_pointer_digest
        ),
        current_release_set_digest=writer_evidence.current_release_set_digest,
        writer_release_set_digests=writer_evidence.writer_release_set_digests,
        managed_provider_generation_lineage_ref=(
            writer_evidence.managed_provider_generation_lineage_ref
        ),
        managed_release_authority_evidence_digest=(
            writer_evidence.managed_release_authority_evidence_digest
        ),
        head_digest=_cutover_head_digest(
            {
                **body,
                "writer_release_set_digests": list(
                    writer_evidence.writer_release_set_digests
                ),
            }
        ),
    )


def decode_workspace_materialization_production_cutover_successor(
    wire: bytes,
    *,
    predecessor_record: LocalOperationalStateRecord | None,
    workspace_authority_root_ref: str,
    workspace_authority_root_digest: str,
    cutover_epoch: str,
    writer_evidence: _WorkspaceMaterializationProductionWriterEvidenceV1,
) -> WorkspaceMaterializationProductionCutoverHeadV1:
    """Authenticate genesis/one successor against the exact current record."""

    if predecessor_record is None:
        revision = 1
        predecessor_digest = None
    else:
        predecessor = _cutover_head_from_record(predecessor_record)
        if (
            predecessor.workspace_authority_root_ref != workspace_authority_root_ref
            or predecessor.workspace_authority_root_digest
            != workspace_authority_root_digest
            or predecessor.cutover_epoch != cutover_epoch
        ):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "cutover predecessor authority context differs"
            )
        revision = predecessor_record.revision + 1
        predecessor_digest = predecessor.head_digest
    expected = _create_workspace_materialization_production_cutover_head_v1(
        workspace_authority_root_ref=workspace_authority_root_ref,
        workspace_authority_root_digest=workspace_authority_root_digest,
        cutover_epoch=cutover_epoch,
        revision=revision,
        predecessor_head_digest=predecessor_digest,
        writer_evidence=writer_evidence,
    )
    if type(wire) is not bytes or wire != expected.to_wire():
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover successor wire differs from contextual derivation"
        )
    return expected


def observe_workspace_materialization_production_cutover_head(
    record: LocalOperationalStateRecord,
    *,
    workspace_authority_root_ref: str,
    workspace_authority_root_digest: str,
    cutover_epoch: str,
    writer_evidence: _WorkspaceMaterializationProductionWriterEvidenceV1,
) -> WorkspaceMaterializationProductionCutoverHeadV1:
    """Observe only the current record; no predecessor/history read is claimed."""

    if type(writer_evidence) is not _WorkspaceMaterializationProductionWriterEvidenceV1:
        raise TypeError("cutover writer evidence must be exact")
    writer_evidence.__post_init__()
    head = _cutover_head_from_record(record)
    if (
        head.workspace_authority_root_ref != workspace_authority_root_ref
        or head.workspace_authority_root_digest != workspace_authority_root_digest
        or head.cutover_epoch != cutover_epoch
        or head.managed_release_channel_revision
        != writer_evidence.managed_release_channel_revision
        or head.managed_release_channel_pointer_digest
        != writer_evidence.managed_release_channel_pointer_digest
        or head.current_release_set_digest != writer_evidence.current_release_set_digest
        or head.writer_release_set_digests != writer_evidence.writer_release_set_digests
        or head.managed_provider_generation_lineage_ref
        != writer_evidence.managed_provider_generation_lineage_ref
        or head.managed_release_authority_evidence_digest
        != writer_evidence.managed_release_authority_evidence_digest
    ):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover current head differs from fresh writer evidence"
        )
    return head


def _cutover_head_from_record(
    record: LocalOperationalStateRecord,
) -> WorkspaceMaterializationProductionCutoverHeadV1:
    if type(record) is not LocalOperationalStateRecord:
        raise TypeError("cutover state record must be exact")
    record.__post_init__()
    if (
        record.namespace != WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_NAMESPACE_V1
        or record.key != WORKSPACE_MATERIALIZATION_PRODUCTION_CUTOVER_KEY_V1
        or record.value is None
    ):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover state coordinate differs"
        )
    if not isinstance(record.value, Mapping):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover stored value must be an exact object"
        )
    root = cast(Mapping[str, object], record.value)
    wire = _cutover_canonical_bytes(root)
    expected_fields = {
        "contract",
        "workspace_authority_root_ref",
        "workspace_authority_root_digest",
        "cutover_epoch",
        "revision",
        "predecessor_head_digest",
        "writer_generation",
        "managed_release_channel_revision",
        "managed_release_channel_pointer_digest",
        "current_release_set_digest",
        "writer_release_set_digests",
        "managed_provider_generation_lineage_ref",
        "managed_release_authority_evidence_digest",
        "head_digest",
    }
    if set(root) != expected_fields:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover stored fields differ"
        )
    writer_values = root["writer_release_set_digests"]
    if not isinstance(writer_values, Sequence) or isinstance(
        writer_values, (str, bytes)
    ):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover writer closure must be an exact stored sequence"
        )
    head = WorkspaceMaterializationProductionCutoverHeadV1(
        contract=_cutover_text(root["contract"], "contract"),
        workspace_authority_root_ref=_cutover_text(
            root["workspace_authority_root_ref"], "workspace_authority_root_ref"
        ),
        workspace_authority_root_digest=_cutover_text(
            root["workspace_authority_root_digest"], "workspace_authority_root_digest"
        ),
        cutover_epoch=_cutover_text(root["cutover_epoch"], "cutover_epoch"),
        revision=_cutover_positive(root["revision"], "revision"),
        predecessor_head_digest=None
        if root["predecessor_head_digest"] is None
        else _cutover_text(root["predecessor_head_digest"], "predecessor_head_digest"),
        writer_generation=_cutover_text(root["writer_generation"], "writer_generation"),
        managed_release_channel_revision=_cutover_positive(
            root["managed_release_channel_revision"], "managed_release_channel_revision"
        ),
        managed_release_channel_pointer_digest=_cutover_text(
            root["managed_release_channel_pointer_digest"],
            "managed_release_channel_pointer_digest",
        ),
        current_release_set_digest=_cutover_text(
            root["current_release_set_digest"], "current_release_set_digest"
        ),
        writer_release_set_digests=tuple(
            _cutover_text(item, "writer_release_set_digest") for item in writer_values
        ),
        managed_provider_generation_lineage_ref=_cutover_text(
            root["managed_provider_generation_lineage_ref"],
            "managed_provider_generation_lineage_ref",
        ),
        managed_release_authority_evidence_digest=_cutover_text(
            root["managed_release_authority_evidence_digest"],
            "managed_release_authority_evidence_digest",
        ),
        head_digest=_cutover_text(root["head_digest"], "head_digest"),
    )
    normalized_wire = _cutover_canonical_bytes(
        {**head._body_without_digest(), "head_digest": head.head_digest}
    )
    if head.revision != record.revision or normalized_wire != wire:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover state revision or canonical wire differs"
        )
    return head


def _cutover_head_digest(body: dict[str, object]) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            _CUTOVER_DIGEST_DOMAIN + _cutover_canonical_bytes(body)
        ).hexdigest()
    )


def _cutover_canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _cutover_decode_object(wire: bytes) -> dict[str, object]:
    if type(wire) is not bytes or not wire:
        raise TypeError("cutover wire must be exact nonempty bytes")

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "cutover wire contains duplicate key"
                )
            result[key] = value
        return result

    try:
        root = json.loads(
            wire.decode(),
            object_pairs_hook=pairs,
            parse_float=lambda _value: (_ for _ in ()).throw(ValueError()),
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover wire is not strict JSON"
        ) from error
    if type(root) is not dict or _cutover_canonical_bytes(root) != wire:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "cutover wire is not a canonical object"
        )
    return cast(dict[str, object], root)


def _cutover_text(value: object, field: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            f"cutover {field} must be exact nonempty text"
        )
    return value


def _cutover_ref(value: object, field: str, maximum_bytes: int) -> str:
    text = _cutover_text(value, field)
    if len(text.encode()) > maximum_bytes:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            f"cutover {field} exceeds its bound"
        )
    return text


def _cutover_digest(value: object, field: str) -> str:
    text = _cutover_text(value, field)
    if len(text) != 71 or not text.startswith("sha256:"):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            f"cutover {field} must be sha256"
        )
    try:
        int(text[7:], 16)
    except ValueError as error:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            f"cutover {field} must be sha256"
        ) from error
    if text != text.lower():
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            f"cutover {field} must use lowercase hex"
        )
    return text


def _cutover_positive(value: object, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            f"cutover {field} must be a positive exact integer"
        )
    return value


class WorkspaceSemanticMaterializationGraphExecutionError(RuntimeError):
    """The graph coordinator rejected authority or exact execution context."""


class _CoordinatorTerminalFailure(Exception):
    def __init__(
        self, failure: WorkspaceSemanticMaterializationTerminalFailureV3
    ) -> None:
        self.failure = failure
        super().__init__(failure.failure_code)


@dataclass(frozen=True, slots=True)
class WorkspaceSemanticMaterializationNodePreparation:
    graph_execution_binding_digest: ContentDigest
    node_execution_binding: WorkspaceSemanticMaterializationNodeExecutionBinding
    workspace_session_ref: str
    participant_ref: str
    authority_grade: WorkspaceMaterializationSessionAuthorityGrade
    expected_package_head_revision: int
    expected_session_head_revision: int
    expected_session_cursor: int
    expected_predecessor_event_digest: ContentDigest | None
    ordered_fulfilled_products: tuple[WorkspaceFulfilledDependencyProductV3, ...]
    ordered_dependency_bodies: tuple[SemanticBody, ...]

    def __post_init__(self) -> None:
        if type(self.graph_execution_binding_digest) is not ContentDigest:
            raise TypeError("preparation graph binding digest must be exact")
        if (
            type(self.node_execution_binding)
            is not WorkspaceSemanticMaterializationNodeExecutionBinding
        ):
            raise TypeError("preparation node binding must be exact")
        if (
            type(self.authority_grade)
            is not WorkspaceMaterializationSessionAuthorityGrade
        ):
            raise TypeError("preparation authority grade must be nominal")
        if type(self.ordered_fulfilled_products) is not tuple or any(
            type(item) is not WorkspaceFulfilledDependencyProductV3
            for item in self.ordered_fulfilled_products
        ):
            raise TypeError("preparation fulfilled products must be exact")
        if type(self.ordered_dependency_bodies) is not tuple or any(
            type(item) is not SemanticBody for item in self.ordered_dependency_bodies
        ):
            raise TypeError("preparation dependency bodies must be exact")
        for body in self.ordered_dependency_bodies:
            body.__post_init__()
        for value in (
            self.expected_package_head_revision,
            self.expected_session_head_revision,
            self.expected_session_cursor,
        ):
            if type(value) is not int or value < 0:
                raise TypeError(
                    "preparation revisions and cursor must be nonnegative ints"
                )


@dataclass(frozen=True, slots=True)
class _WorkspaceSemanticMaterializationGraphHostPorts:
    head_reader: Callable[
        [str, str], WorkspaceSemanticMaterializationHeadRereadEvidenceV3 | None
    ]
    body_reader: Callable[[SemanticValueCoordinate], SemanticBody | None]
    operation_preparer: Callable[
        [WorkspaceSemanticMaterializationNodePreparation],
        Awaitable[
            tuple[WorkspaceMaterializeOperation, WorkspaceMaterializeOperationAdmission]
        ],
    ]
    session_journal: WorkspaceMaterializationSessionJournal
    cutover_fence_reader: (
        Callable[[str], WorkspaceMaterializationProductionCutoverHeadV1] | None
    ) = None

    def __post_init__(self) -> None:
        if type(self.session_journal) is not WorkspaceMaterializationSessionJournal:
            raise TypeError("graph host session journal must be exact")
        for value in (self.head_reader, self.body_reader, self.operation_preparer):
            if not callable(value):
                raise TypeError("graph host ports must be callable")
        if self.cutover_fence_reader is not None and not callable(
            self.cutover_fence_reader
        ):
            raise TypeError("graph host cutover fence reader must be callable")


@dataclass(slots=True)
class _GraphExecutionState:
    admitted_plan_result: WorkspaceSemanticMaterializationGraphPlanResult
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult
    plan_wire: bytes
    workspace_session_ref: str
    epoch: str
    participant_ref: str
    actor_ref: str
    workflow_session_ref: str
    materialization_attempt_ref: str
    branch_baseline_ref: str
    branch_baseline_digest: ContentDigest
    branch_baseline_grade: str
    operation_ref: str
    operation_digest: ContentDigest
    authority_grade: WorkspaceMaterializationSessionAuthorityGrade
    expected_session_head_revision: int
    expected_session_cursor: int
    expected_predecessor_event_digest: ContentDigest | None
    ports: _WorkspaceSemanticMaterializationGraphHostPorts
    owner: object
    status: str = "fresh"
    completed_results: tuple[
        WorkspaceSemanticMaterializationNodeResultEvidenceV3, ...
    ] = ()
    completed_products: tuple[WorkspaceFulfilledDependencyProductV3, ...] = ()
    completed_session_head_revision: int = 0
    completed_session_cursor: int = 0
    completed_predecessor_event_digest: ContentDigest | None = None
    revision_preparation_process_id: int | None = None
    revision_preparation_incarnation: object | None = None
    revision_preparation_result: object | None = None
    revision_preparation_result_wire: bytes | None = None
    revision_preparation_admission: object | None = None
    revision_preparation_admission_wire: bytes | None = None
    revision_preparation_capability: object | None = None


@dataclass(frozen=True, slots=True)
class _GraphExecutionRecoveryEvidence:
    """Coordinator-owned evidence for one exact post-loss graph re-execution."""

    prior_process_id: int
    prior_incarnation: object
    operation_authority_digest: str
    plan_wire: bytes
    plan_body_sha256: str
    execution_context_digest: str
    graph_digest: str
    execution_binding_digest: str
    prior_graph_result_digest: str
    prior_graph_admission_digest: str


_EXECUTIONS: WeakKeyDictionary[
    AdmittedWorkspaceSemanticMaterializationGraphExecution, _GraphExecutionState
] = WeakKeyDictionary()
_EXECUTIONS_LOCK = RLock()


def _graph_execution_recovery_context_digest(state: _GraphExecutionState) -> str:
    body = canonical_json_bytes(
        {
            "actor_ref": state.actor_ref,
            "authority_grade": state.authority_grade.value,
            "branch_baseline_digest": state.branch_baseline_digest.value,
            "branch_baseline_grade": state.branch_baseline_grade,
            "branch_baseline_ref": state.branch_baseline_ref,
            "epoch": state.epoch,
            "expected_predecessor_event_digest": (
                None
                if state.expected_predecessor_event_digest is None
                else state.expected_predecessor_event_digest.value
            ),
            "expected_session_cursor": state.expected_session_cursor,
            "expected_session_head_revision": (
                state.expected_session_head_revision
            ),
            "materialization_attempt_ref": state.materialization_attempt_ref,
            "operation_ref": state.operation_ref,
            "participant_ref": state.participant_ref,
            "workflow_session_ref": state.workflow_session_ref,
            "workspace_session_ref": state.workspace_session_ref,
        }
    )
    return ContentDigest.of_bytes(
        b"aware.workspace.graph-execution-recovery-context.v1\x00" + body
    ).value


def _recovery_key(
    *,
    operation_authority_digest: str,
    plan_wire: bytes,
    execution_context_digest: str,
) -> tuple[str, str, str]:
    return (
        operation_authority_digest,
        ContentDigest.of_bytes(plan_wire).value,
        execution_context_digest,
    )


def _completed_graph_recovery_evidence(
    state: _GraphExecutionState,
    *,
    prior_process_id: int,
    prior_incarnation: object,
) -> _GraphExecutionRecoveryEvidence | None:
    """Retain only a fully authenticated completed execution across process loss."""

    from .revision_preparation_admission import (
        WorkspaceMaterializationGraphExecutionAdmissionCapability,
    )
    from .revision_preparation_contracts import (
        WorkspaceMaterializationGraphExecutionAdmission,
    )

    admission = state.revision_preparation_admission
    result = state.revision_preparation_result
    capability = state.revision_preparation_capability
    if (
        state.status != "completed"
        or state.revision_preparation_process_id != prior_process_id
        or state.revision_preparation_incarnation is not prior_incarnation
        or type(admission) is not WorkspaceMaterializationGraphExecutionAdmission
        or type(capability)
        is not WorkspaceMaterializationGraphExecutionAdmissionCapability
        or type(result) is not WorkspaceSemanticMaterializationGraphResultV3
        or state.plan_wire
        != canonical_json_bytes(state.admitted_plan_result.to_wire())
        or state.revision_preparation_result_wire
        != canonical_json_bytes(result.to_wire())
        or state.revision_preparation_admission_wire != admission.canonical_bytes()
        or admission.operation_authority_digest != state.operation_digest.value
        or admission.plan_body_sha256
        != ContentDigest.of_bytes(state.plan_wire).value
        or admission.plan_body_size_bytes != len(state.plan_wire)
        or admission.graph_result_digest != result.result_digest.value
        or result.graph_digest != state.plan_result.graph.graph_digest
        or result.execution_binding_digest
        != state.plan_result.graph_execution_binding.binding_digest
    ):
        return None
    return _GraphExecutionRecoveryEvidence(
        prior_process_id=prior_process_id,
        prior_incarnation=prior_incarnation,
        operation_authority_digest=state.operation_digest.value,
        plan_wire=state.plan_wire,
        plan_body_sha256=admission.plan_body_sha256,
        execution_context_digest=_graph_execution_recovery_context_digest(state),
        graph_digest=result.graph_digest.value,
        execution_binding_digest=result.execution_binding_digest.value,
        prior_graph_result_digest=result.result_digest.value,
        prior_graph_admission_digest=admission.admission_digest,
    )


def _create_graph_execution_recovery_registry():  # type: ignore[no-untyped-def]
    """Keep loss records outside caller-authored graph or portable values."""

    process_id = os.getpid()
    incarnation = object()
    records: dict[tuple[str, str, str], _GraphExecutionRecoveryEvidence] = {}
    claims: WeakKeyDictionary[
        AdmittedWorkspaceSemanticMaterializationGraphExecution,
        _GraphExecutionRecoveryEvidence,
    ] = WeakKeyDictionary()

    def synchronize() -> tuple[int, object, bool]:
        nonlocal process_id, incarnation, records, claims
        current_process_id = os.getpid()
        if current_process_id == process_id:
            return process_id, incarnation, False
        recovered: dict[tuple[str, str, str], _GraphExecutionRecoveryEvidence] = {}
        ambiguous: set[tuple[str, str, str]] = set()
        for state in tuple(_EXECUTIONS.values()):
            try:
                evidence = _completed_graph_recovery_evidence(
                    state,
                    prior_process_id=process_id,
                    prior_incarnation=incarnation,
                )
            except (
                TypeError,
                ValueError,
                WorkspaceSemanticMaterializationGraphExecutionError,
            ):
                evidence = None
            if evidence is None:
                continue
            key = _recovery_key(
                operation_authority_digest=evidence.operation_authority_digest,
                plan_wire=evidence.plan_wire,
                execution_context_digest=evidence.execution_context_digest,
            )
            prior = recovered.get(key)
            if prior is None:
                recovered[key] = evidence
            elif prior != evidence:
                ambiguous.add(key)
        for key in ambiguous:
            recovered.pop(key, None)
        process_id = current_process_id
        incarnation = object()
        records = recovered
        claims = WeakKeyDictionary()
        return process_id, incarnation, True

    def claim(
        execution: AdmittedWorkspaceSemanticMaterializationGraphExecution,
        *,
        operation_authority_digest: str,
        plan_wire: bytes,
        execution_context_digest: str,
    ) -> None:
        evidence = records.pop(
            _recovery_key(
                operation_authority_digest=operation_authority_digest,
                plan_wire=plan_wire,
                execution_context_digest=execution_context_digest,
            ),
            None,
        )
        if evidence is not None:
            claims[execution] = evidence

    def lookup(
        execution: AdmittedWorkspaceSemanticMaterializationGraphExecution,
    ) -> _GraphExecutionRecoveryEvidence | None:
        return claims.get(execution)

    return synchronize, claim, lookup


(
    _synchronize_graph_execution_recovery_registry,
    _claim_graph_execution_recovery,
    _lookup_graph_execution_recovery,
) = _create_graph_execution_recovery_registry()


def _rotate_graph_execution_incarnation_after_process_loss() -> None:
    global _EXECUTIONS
    global _EXECUTIONS_LOCK
    _process_id, _incarnation, changed = (
        _synchronize_graph_execution_recovery_registry()
    )
    if not changed:
        return
    _EXECUTIONS_LOCK = RLock()
    with _EXECUTIONS_LOCK:
        _EXECUTIONS = WeakKeyDictionary()


def _current_graph_execution_incarnation() -> tuple[int, object]:
    """Return the OS-observed coordinator incarnation."""

    _rotate_graph_execution_incarnation_after_process_loss()
    process_id, incarnation, _changed = (
        _synchronize_graph_execution_recovery_registry()
    )
    return process_id, incarnation


def _is_exact_graph_reexecution_after_process_loss(
    *,
    execution: AdmittedWorkspaceSemanticMaterializationGraphExecution,
    state: _GraphExecutionState,
    result: WorkspaceSemanticMaterializationGraphResultV3,
    process_id: int,
    incarnation: object,
) -> bool:
    """Authenticate a claimed replay against one coordinator-retained loss record."""

    evidence = _lookup_graph_execution_recovery(execution)
    if evidence is None:
        return False
    if type(evidence) is not _GraphExecutionRecoveryEvidence:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "graph recovery evidence is foreign"
        )
    try:
        prior_result_digest = ContentDigest(evidence.prior_graph_result_digest)
        prior_admission_digest = ContentDigest(evidence.prior_graph_admission_digest)
    except (TypeError, ValueError) as error:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "graph recovery evidence digest is invalid"
        ) from error
    if (
        type(evidence.prior_process_id) is not int
        or evidence.prior_process_id == process_id
        or evidence.prior_incarnation is incarnation
        or evidence.operation_authority_digest != state.operation_digest.value
        or evidence.plan_wire != state.plan_wire
        or evidence.plan_body_sha256
        != ContentDigest.of_bytes(state.plan_wire).value
        or evidence.execution_context_digest
        != _graph_execution_recovery_context_digest(state)
        or evidence.graph_digest != state.plan_result.graph.graph_digest.value
        or evidence.execution_binding_digest
        != state.plan_result.graph_execution_binding.binding_digest.value
        or result.graph_digest.value != evidence.graph_digest
        or result.execution_binding_digest.value
        != evidence.execution_binding_digest
        or prior_result_digest.value != evidence.prior_graph_result_digest
        or prior_admission_digest.value != evidence.prior_graph_admission_digest
    ):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "graph execution differs from its process-loss recovery evidence"
        )
    return True


_register_at_fork = getattr(os, "register_at_fork", None)
if callable(_register_at_fork):
    _register_at_fork(after_in_child=_rotate_graph_execution_incarnation_after_process_loss)


class AdmittedWorkspaceSemanticMaterializationGraphExecution:
    """Nonserializable authority for exactly one immutable graph traversal."""

    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls) -> AdmittedWorkspaceSemanticMaterializationGraphExecution:  # noqa: PYI034
        raise TypeError("graph execution admission is Workspace-constructed only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("graph execution admission is sealed")

    def __copy__(self) -> Never:
        raise TypeError("graph execution admission is not copyable")

    def __deepcopy__(self, memo: object) -> Never:
        del memo
        raise TypeError("graph execution admission is not copyable")

    def __reduce__(self) -> Never:
        raise TypeError("graph execution admission is not serializable")


def _issue_workspace_semantic_materialization_graph_execution_core(
    *,
    plan_result: WorkspaceSemanticMaterializationGraphPlanResult,
    workspace_session_ref: str,
    epoch: str,
    participant_ref: str,
    actor_ref: str,
    workflow_session_ref: str,
    materialization_attempt_ref: str,
    branch_baseline_ref: str,
    branch_baseline_digest: ContentDigest,
    branch_baseline_grade: str,
    operation_ref: str,
    operation_digest: ContentDigest,
    authority_grade: WorkspaceMaterializationSessionAuthorityGrade,
    expected_session_head_revision: int,
    expected_session_cursor: int,
    expected_predecessor_event_digest: ContentDigest | None,
    ports: _WorkspaceSemanticMaterializationGraphHostPorts,
    owner: object,
) -> AdmittedWorkspaceSemanticMaterializationGraphExecution:
    """Shared exact construction after a test or production nominal preflight."""

    if type(plan_result) is not WorkspaceSemanticMaterializationGraphPlanResult:
        raise TypeError("graph execution plan must be exact")
    if type(branch_baseline_digest) is not ContentDigest:
        raise TypeError("graph execution baseline digest must be exact")
    if type(operation_digest) is not ContentDigest:
        raise TypeError("graph execution operation digest must be exact")
    if type(authority_grade) is not WorkspaceMaterializationSessionAuthorityGrade:
        raise TypeError("graph execution authority grade must be nominal")
    if type(ports) is not _WorkspaceSemanticMaterializationGraphHostPorts:
        raise TypeError("graph execution host ports must be exact")
    if (
        type(expected_session_head_revision) is not int
        or expected_session_head_revision < 0
    ):
        raise TypeError("graph execution session revision must be nonnegative int")
    if type(expected_session_cursor) is not int or expected_session_cursor < 0:
        raise TypeError("graph execution session cursor must be nonnegative int")
    if (expected_predecessor_event_digest is None) != (
        expected_session_head_revision == 0 and expected_session_cursor == 0
    ):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "graph execution session predecessor differs"
        )
    plan_result.__post_init__()
    plan_wire = canonical_json_bytes(plan_result.to_wire())
    admission = object.__new__(AdmittedWorkspaceSemanticMaterializationGraphExecution)
    _current_graph_execution_incarnation()
    with _EXECUTIONS_LOCK:
        state = _GraphExecutionState(
            admitted_plan_result=plan_result,
            plan_result=copy.deepcopy(plan_result),
            plan_wire=plan_wire,
            workspace_session_ref=workspace_session_ref,
            epoch=epoch,
            participant_ref=participant_ref,
            actor_ref=actor_ref,
            workflow_session_ref=workflow_session_ref,
            materialization_attempt_ref=materialization_attempt_ref,
            branch_baseline_ref=branch_baseline_ref,
            branch_baseline_digest=branch_baseline_digest,
            branch_baseline_grade=branch_baseline_grade,
            operation_ref=operation_ref,
            operation_digest=operation_digest,
            authority_grade=authority_grade,
            expected_session_head_revision=expected_session_head_revision,
            expected_session_cursor=expected_session_cursor,
            expected_predecessor_event_digest=expected_predecessor_event_digest,
            ports=ports,
            owner=owner,
            completed_session_head_revision=expected_session_head_revision,
            completed_session_cursor=expected_session_cursor,
            completed_predecessor_event_digest=expected_predecessor_event_digest,
        )
        _EXECUTIONS[admission] = state
        _claim_graph_execution_recovery(
            admission,
            operation_authority_digest=operation_digest.value,
            plan_wire=plan_wire,
            execution_context_digest=_graph_execution_recovery_context_digest(state),
        )
    return admission


def _issue_workspace_semantic_materialization_graph_execution_for_test(
    **values: object,
) -> AdmittedWorkspaceSemanticMaterializationGraphExecution:
    """Retained isolated test issuer; never used by the production host."""

    issuer = cast(
        Callable[..., AdmittedWorkspaceSemanticMaterializationGraphExecution],
        _issue_workspace_semantic_materialization_graph_execution_core,
    )
    return issuer(**values)


class _AdmittedWorkspaceSemanticMaterializationProductionGraphHost:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable]

    def __new__(cls):  # type: ignore[no-untyped-def]
        raise TypeError("production graph host admission is module-issued only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("production graph host admission is sealed")

    def __reduce__(self) -> Never:
        raise TypeError("production graph host admission is not serializable")


@dataclass(slots=True)
class _ProductionGraphHostState:
    owner: object
    ports: _WorkspaceSemanticMaterializationGraphHostPorts
    liveness: Callable[[], bool]
    live: bool = True


_PRODUCTION_GRAPH_HOSTS: WeakKeyDictionary[
    _AdmittedWorkspaceSemanticMaterializationProductionGraphHost,
    _ProductionGraphHostState,
] = WeakKeyDictionary()
_PRODUCTION_GRAPH_HOSTS_LOCK = RLock()


def _issue_workspace_semantic_materialization_production_graph_host(
    *,
    owner: object,
    ports: _WorkspaceSemanticMaterializationGraphHostPorts,
    liveness: Callable[[], bool],
) -> _AdmittedWorkspaceSemanticMaterializationProductionGraphHost:
    if type(ports) is not _WorkspaceSemanticMaterializationGraphHostPorts:
        raise TypeError("production graph-host ports must be exact")
    ports.__post_init__()
    if ports.cutover_fence_reader is None:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "production graph host requires cutover fence reader"
        )
    if not callable(liveness) or liveness() is not True:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "production graph host is not live"
        )
    admission = object.__new__(
        _AdmittedWorkspaceSemanticMaterializationProductionGraphHost
    )
    with _PRODUCTION_GRAPH_HOSTS_LOCK:
        _PRODUCTION_GRAPH_HOSTS[admission] = _ProductionGraphHostState(
            owner=owner, ports=ports, liveness=liveness
        )
    return admission


def _revoke_workspace_semantic_materialization_production_graph_host(
    admission: _AdmittedWorkspaceSemanticMaterializationProductionGraphHost,
    *,
    owner: object,
) -> None:
    if (
        type(admission)
        is not _AdmittedWorkspaceSemanticMaterializationProductionGraphHost
    ):
        raise TypeError("production graph-host admission must be exact")
    with _PRODUCTION_GRAPH_HOSTS_LOCK:
        state = _PRODUCTION_GRAPH_HOSTS.get(admission)
        if state is None or state.owner is not owner:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "production graph-host owner differs"
            )
        state.live = False
        _PRODUCTION_GRAPH_HOSTS.pop(admission, None)


def _issue_workspace_semantic_materialization_graph_execution_production(
    host_admission: _AdmittedWorkspaceSemanticMaterializationProductionGraphHost,
    *,
    owner: object,
    **values: object,
) -> AdmittedWorkspaceSemanticMaterializationGraphExecution:
    if (
        type(host_admission)
        is not _AdmittedWorkspaceSemanticMaterializationProductionGraphHost
    ):
        raise TypeError("production graph-host admission must be exact")
    with _PRODUCTION_GRAPH_HOSTS_LOCK:
        state = _PRODUCTION_GRAPH_HOSTS.get(host_admission)
    if (
        state is None
        or not state.live
        or state.owner is not owner
        or state.liveness() is not True
        or values.get("ports") is not state.ports
    ):
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "production graph-host admission is absent or moved"
        )
    fence_reader = state.ports.cutover_fence_reader
    if fence_reader is None:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "production graph-host cutover fence reader is absent"
        )
    observed = fence_reader("graph_issuance")
    if type(observed) is not WorkspaceMaterializationProductionCutoverHeadV1:
        raise TypeError("production graph issuance fence is foreign")
    observed.__post_init__()
    issuer = cast(
        Callable[..., AdmittedWorkspaceSemanticMaterializationGraphExecution],
        _issue_workspace_semantic_materialization_graph_execution_core,
    )
    return issuer(owner=owner, **values)


def _execution_state(
    admission: AdmittedWorkspaceSemanticMaterializationGraphExecution,
) -> _GraphExecutionState:
    if type(admission) is not AdmittedWorkspaceSemanticMaterializationGraphExecution:
        raise TypeError("graph execution admission must be exact")
    _current_graph_execution_incarnation()
    with _EXECUTIONS_LOCK:
        state = _EXECUTIONS.get(admission)
    if state is None:
        raise WorkspaceSemanticMaterializationGraphExecutionError(
            "graph execution admission is not registered"
        )
    return state


def _revoke_workspace_semantic_materialization_graph_execution(
    admission: AdmittedWorkspaceSemanticMaterializationGraphExecution,
    *,
    owner: object,
) -> None:
    state = _execution_state(admission)
    with _EXECUTIONS_LOCK:
        if state.owner is not owner:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "graph execution owner differs"
            )
        if state.status in {"completed", "terminal_failed", "revoked"}:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "graph execution is already terminal"
            )
        state.status = "revoked"


def _result_counters(
    plan: WorkspaceSemanticMaterializationGraphPlanResult,
    node_results: tuple[WorkspaceSemanticMaterializationNodeResultEvidenceV3, ...],
    products: tuple[WorkspaceFulfilledDependencyProductV3, ...],
    terminal: WorkspaceSemanticMaterializationTerminalFailureV3 | None = None,
) -> tuple[WorkspaceSemanticMaterializationResultCounterEntryV2, ...]:
    entries = () if terminal is None else terminal.ordered_evidence_entries
    entry_kinds = {item.evidence_kind for item in entries}
    values = {
        "dependency_body_observation_count": len(products)
        + int(bool(entry_kinds & {"body", "observed_body"})),
        "dependency_head_observation_count": (2 * len(products))
        + (
            len(entry_kinds & {"head_h1", "head_h2"})
            if terminal is not None
            and terminal.terminal_stage
            in {"dependency_head_reread", "dependency_body_read"}
            else 0
        ),
        "edge_count": len(plan.graph.edges),
        "executed_count": sum(item.outcome == "executed" for item in node_results),
        "fulfilled_product_count": len(products),
        "node_count": len(plan.graph.nodes),
        "package_head_observation_count": len(node_results)
        + int(bool(entry_kinds & {"package_result", "package_reuse"})),
        "publication_count": sum(item.outcome == "executed" for item in node_results)
        + int({"publication_receipt", "package_result"} <= entry_kinds),
        "reused_count": sum(item.outcome == "reused" for item in node_results),
        "session_event_count": len(node_results)
        + int("session_event_positive" in entry_kinds),
    }
    return tuple(
        WorkspaceSemanticMaterializationResultCounterEntryV2(
            counter=key, value=values[key]
        )
        for key in WORKSPACE_SEMANTIC_MATERIALIZATION_RESULT_COUNTERS_V2
    )


class WorkspaceSemanticMaterializationGraphCoordinator:
    """Traverse one admitted graph in its immutable topological order."""

    async def execute(
        self,
        admission: AdmittedWorkspaceSemanticMaterializationGraphExecution,
        *,
        owner: object,
    ) -> WorkspaceSemanticMaterializationGraphResultV3:
        if type(self) is not WorkspaceSemanticMaterializationGraphCoordinator:
            raise TypeError("graph coordinator must be exact")
        state = _execution_state(admission)
        with _EXECUTIONS_LOCK:
            if state.owner is not owner:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "graph execution owner differs"
                )
            if state.status not in {"fresh", "interrupted_resumable"}:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "graph execution admission is busy or consumed"
                )
            resuming = state.status == "interrupted_resumable"
            state.status = "running"

        plan = state.plan_result
        results = list(state.completed_results) if resuming else []
        result_wires: list[dict[str, object]] = []
        all_products = list(state.completed_products) if resuming else []
        node_by_digest = {item.node_digest: item for item in plan.graph.nodes}
        binding_by_digest = {
            item.node_digest: item
            for item in plan.graph_execution_binding.ordered_node_bindings
        }
        edge_by_consumer_resolution = {
            (item.consumer_node_digest, item.target_resolution_digest): item
            for item in plan.graph.edges
        }
        if resuming:
            result_wires = self._validate_resumable_prefix(state)
        session_revision = state.completed_session_head_revision
        session_cursor = state.completed_session_cursor
        predecessor = state.completed_predecessor_event_digest
        try:
            for binding in plan.graph_execution_binding.ordered_node_bindings[
                len(results) :
            ]:
                products, bodies = self._fulfill_dependencies(
                    state,
                    binding,
                    binding_by_digest=binding_by_digest,
                    edge_by_consumer_resolution=edge_by_consumer_resolution,
                )
                planned_head = self._planned_head(node_by_digest, binding)
                if planned_head.state == "current":
                    closure = cast(
                        ContentDigest,
                        planned_head.historical_execution_input_closure_digest,
                    )
                    package_head = state.ports.head_reader(
                        binding.package.package_ref, "package_reuse"
                    )
                    if package_head is None:
                        raise WorkspaceSemanticMaterializationGraphExecutionError(
                            "planned current package head disappeared"
                        )
                    self._validate_reuse_head(
                        binding, planned_head, closure, package_head
                    )
                    source = _create_graph_v2_session_source_evidence(
                        disposition="reused",
                        head_reread_evidence=package_head,
                        publication_receipt=None,
                    )
                    append = _create_graph_v2_session_append_request(
                        workspace_session_ref=state.workspace_session_ref,
                        epoch=state.epoch,
                        participant_ref=state.participant_ref,
                        actor_ref=state.actor_ref,
                        workflow_session_ref=state.workflow_session_ref,
                        materialization_attempt_ref=state.materialization_attempt_ref,
                        branch_baseline_ref=state.branch_baseline_ref,
                        branch_baseline_digest=state.branch_baseline_digest,
                        branch_baseline_grade=state.branch_baseline_grade,
                        package_ref=binding.package.package_ref,
                        operation_ref=state.operation_ref,
                        operation_digest=state.operation_digest,
                        source_evidence=source,
                        expected_session_head_revision=session_revision,
                        expected_cursor=session_cursor,
                        expected_predecessor_event_digest=predecessor,
                    )
                    self._reread_cutover_fence(state, "session_append")
                    append_result = state.ports.session_journal._append_graph_v2(
                        request=append
                    )
                    result, result_wire = _create_coordinator_node_result_evidence_v2(
                        plan_result=plan,
                        binding=binding,
                        outcome="reused",
                        execution_input_closure_digest=closure,
                        ordered_fulfilled_products=products,
                        package_head_reread_evidence=package_head,
                        publication_receipt=None,
                        session_source_evidence=source,
                        session_event_reread_evidence=append_result.reread_evidence,
                        session_fanout_receipt=append_result.receipt,
                    )
                else:
                    preparation = WorkspaceSemanticMaterializationNodePreparation(
                        graph_execution_binding_digest=plan.graph_execution_binding.binding_digest,
                        node_execution_binding=binding,
                        workspace_session_ref=state.workspace_session_ref,
                        participant_ref=state.participant_ref,
                        authority_grade=state.authority_grade,
                        expected_package_head_revision=(
                            0
                            if planned_head.predecessor_head_revision is None
                            else planned_head.predecessor_head_revision
                        ),
                        expected_session_head_revision=session_revision,
                        expected_session_cursor=session_cursor,
                        expected_predecessor_event_digest=predecessor,
                        ordered_fulfilled_products=products,
                        ordered_dependency_bodies=bodies,
                    )
                    self._reread_cutover_fence(state, "operation_admission")
                    (
                        operation,
                        operation_admission,
                    ) = await state.ports.operation_preparer(preparation)
                    self._validate_prepared_operation(
                        state=state,
                        binding=binding,
                        preparation=preparation,
                        operation=operation,
                        operation_admission=operation_admission,
                    )
                    closure = ContentDigest(
                        operation_admission.request.execution_input_closure_digest
                    )

                    def reread_session_append_fence() -> None:
                        self._reread_cutover_fence(state, "session_append")

                    node_admission = (
                        _admit_workspace_semantic_materialization_graph_node_execution(
                            graph_execution_admission=admission,
                            plan_result=plan,
                            node_binding=binding,
                            execution_input_closure_digest=closure,
                            operation=operation,
                            operation_admission=operation_admission,
                            session_append_fence_rereader=(reread_session_append_fence),
                            owner=owner,
                        )
                    )
                    try:
                        executed = await operation._execute_graph_v2(node_admission)
                    finally:
                        _revoke_workspace_semantic_materialization_graph_node_execution(
                            node_admission
                        )
                    append_result = executed.session_append_result
                    result, result_wire = _create_coordinator_node_result_evidence_v2(
                        plan_result=plan,
                        binding=binding,
                        outcome="executed",
                        execution_input_closure_digest=closure,
                        ordered_fulfilled_products=products,
                        package_head_reread_evidence=executed.package_head_reread_evidence,
                        publication_receipt=executed.publication_receipt,
                        session_source_evidence=executed.session_source_evidence,
                        session_event_reread_evidence=append_result.reread_evidence,
                        session_fanout_receipt=append_result.receipt,
                    )
                results.append(result)
                result_wires.append(result_wire)
                all_products.extend(products)
                session_revision = append_result.receipt.head_revision
                session_cursor = append_result.head.cursor
                predecessor = append_result.head.event_digest
                with _EXECUTIONS_LOCK:
                    state.completed_results = tuple(results)
                    state.completed_products = tuple(all_products)
                    state.completed_session_head_revision = session_revision
                    state.completed_session_cursor = session_cursor
                    state.completed_predecessor_event_digest = predecessor
        except _CoordinatorTerminalFailure as terminal_error:
            failure = terminal_error.failure
            node_results = tuple(results)
            fulfilled = (
                tuple(all_products) + failure.ordered_completed_fulfilled_products
            )
            result = WorkspaceSemanticMaterializationGraphResultV3.create(
                plan_result=plan,
                status="failed",
                ordered_node_results=node_results,
                terminal_failure=failure,
                ordered_fulfilled_products=fulfilled,
                counter_entries=_result_counters(
                    plan, node_results, fulfilled, terminal=failure
                ),
            )
            with _EXECUTIONS_LOCK:
                state.status = "terminal_failed"
            return result
        except asyncio.CancelledError:
            with _EXECUTIONS_LOCK:
                state.status = "interrupted_resumable"
            raise
        except Exception:
            with _EXECUTIONS_LOCK:
                state.status = "interrupted_resumable"
            raise

        node_results = tuple(results)
        fulfilled = tuple(all_products)
        result = _create_coordinator_graph_result_v2(
            plan_result=plan,
            ordered_node_results=node_results,
            ordered_node_wires=tuple(result_wires),
            ordered_fulfilled_products=fulfilled,
            counter_entries=_result_counters(plan, node_results, fulfilled),
        )
        result_wire = canonical_json_bytes(
            {
                "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_GRAPH_RESULT_V3,
                "counter_entries": [
                    {"counter": item.counter, "value": item.value}
                    for item in result.counter_entries
                ],
                "execution_binding_digest": result.execution_binding_digest.value,
                "graph_digest": result.graph_digest.value,
                "ordered_fulfilled_products": [
                    _coordinator_fulfilled_product_wire(item) for item in fulfilled
                ],
                "ordered_node_results": list(result_wires),
                "result_digest": result.result_digest.value,
                "status": "succeeded",
                "terminal_failure": None,
            }
        )
        from .revision_preparation_admission import (
            WorkspaceMaterializationGraphExecutionAdmissionCapability,
        )
        from .revision_preparation_contracts import (
            WorkspaceMaterializationGraphExecutionAdmission,
        )

        process_id, incarnation = _current_graph_execution_incarnation()
        reexecuted_after_process_loss = (
            _is_exact_graph_reexecution_after_process_loss(
                execution=admission,
                state=state,
                result=result,
                process_id=process_id,
                incarnation=incarnation,
            )
        )
        graph_admission = WorkspaceMaterializationGraphExecutionAdmission.create(
            disposition="admitted",
            operation_authority_digest=state.operation_digest.value,
            execution_provenance_lifecycle=(
                "reexecuted_after_process_loss"
                if reexecuted_after_process_loss
                else "same_process_execution"
            ),
            plan_body_sha256=ContentDigest.of_bytes(state.plan_wire).value,
            plan_body_size_bytes=len(state.plan_wire),
            graph_result_body_sha256=ContentDigest.of_bytes(result_wire).value,
            graph_result_body_size_bytes=len(result_wire),
            graph_result_digest=result.result_digest.value,
        )
        graph_capability = object.__new__(
            WorkspaceMaterializationGraphExecutionAdmissionCapability
        )
        with _EXECUTIONS_LOCK:
            if state.status != "running" or state.owner is not owner:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "graph execution changed before completion admission"
                )
            state.revision_preparation_process_id = process_id
            state.revision_preparation_incarnation = incarnation
            state.revision_preparation_result = result
            state.revision_preparation_result_wire = result_wire
            state.revision_preparation_admission = graph_admission
            state.revision_preparation_admission_wire = graph_admission.canonical_bytes()
            state.revision_preparation_capability = graph_capability
            state.status = "completed"
        return result

    @staticmethod
    def _reread_cutover_fence(
        state: _GraphExecutionState, stage: str
    ) -> WorkspaceMaterializationProductionCutoverHeadV1 | None:
        reader = state.ports.cutover_fence_reader
        if reader is None:
            return None
        observed = reader(stage)
        if type(observed) is not WorkspaceMaterializationProductionCutoverHeadV1:
            raise TypeError("production cutover fence reader returned a foreign value")
        observed.__post_init__()
        return observed

    @staticmethod
    def _validate_resumable_prefix(
        state: _GraphExecutionState,
    ) -> list[dict[str, object]]:
        """Freshly bind an interrupted prefix to durable package/session state."""

        results = state.completed_results
        bindings = state.plan_result.graph_execution_binding.ordered_node_bindings
        if len(results) > len(bindings) or tuple(
            item.node_digest for item in results
        ) != tuple(item.node_digest for item in bindings[: len(results)]):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable completed prefix differs from the admitted plan"
            )
        wires: list[dict[str, object]] = []
        for binding, result in zip(bindings[: len(results)], results, strict=True):
            result.__post_init__()
            fresh_head = state.ports.head_reader(
                binding.package.package_ref,
                "package_result" if result.outcome == "executed" else "package_reuse",
            )
            if (
                type(fresh_head)
                is not WorkspaceSemanticMaterializationHeadRereadEvidenceV3
            ):
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable package head is absent or foreign"
                )
            fresh_head.__post_init__()
            if canonical_json_bytes(fresh_head.to_wire()) != canonical_json_bytes(
                result.package_head_reread_evidence.to_wire()
            ):
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable package head differs from completed evidence"
                )
            event = state.ports.session_journal._reread_graph_v2_event(
                result.session_event_reread_evidence.event.event_digest
            )
            if event is None or canonical_json_bytes(
                event.to_wire()
            ) != canonical_json_bytes(
                result.session_event_reread_evidence.event.to_wire()
            ):
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable session event differs from completed evidence"
                )
            wires.append(result.to_wire())

        observed_session = state.ports.session_journal._read_graph_resume_head(
            state.workspace_session_ref
        )
        expected_revision = state.completed_session_head_revision
        expected_cursor = state.completed_session_cursor
        expected_predecessor = state.completed_predecessor_event_digest
        if observed_session is None:
            if (
                expected_revision != 0
                or expected_cursor != 0
                or expected_predecessor is not None
            ):
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable session head is absent"
                )
            return wires

        revision, head = observed_session
        if revision == expected_revision:
            if type(head) is WorkspaceMaterializationSessionHead:
                exact_baseline = (
                    head.workspace_session_ref == state.workspace_session_ref
                    and head.epoch == state.epoch
                    and head.authority_grade == state.authority_grade.value
                    and head.cursor == expected_cursor
                    and ContentDigest(head.event_digest) == expected_predecessor
                )
            elif type(head) is WorkspaceMaterializationSessionHeadV2:
                exact_baseline = (
                    head.workspace_session_ref == state.workspace_session_ref
                    and head.epoch == state.epoch
                    and head.cursor == expected_cursor
                    and head.event_digest == expected_predecessor
                )
            else:
                raise TypeError("resumable session head must be exact V1 or V2")
            if not exact_baseline:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable session head differs from completed prefix"
                )
        elif revision == expected_revision + 1 and len(results) < len(bindings):
            if type(head) is not WorkspaceMaterializationSessionHeadV2:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable pending session head is not graph V2"
                )
            pending = state.ports.session_journal._reread_graph_v2_event(
                head.event_digest
            )
            if pending is None:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable pending event is absent"
                )
            WorkspaceSemanticMaterializationGraphCoordinator._validate_pending_event(
                state=state,
                binding=bindings[len(results)],
                revision=revision,
                head=head,
                pending=pending,
            )
        else:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable session revision advanced outside the prefix"
            )
        return wires

    @staticmethod
    def _validate_pending_event(
        *,
        state: _GraphExecutionState,
        binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
        revision: int,
        head: WorkspaceMaterializationSessionHeadV2,
        pending: WorkspaceMaterializationSessionEventV3,
    ) -> None:
        """Authenticate one persisted next-node event before any host operation access."""

        if type(binding) is not WorkspaceSemanticMaterializationNodeExecutionBinding:
            raise TypeError("resumable pending binding must be exact")
        if type(head) is not WorkspaceMaterializationSessionHeadV2:
            raise TypeError("resumable pending head must be exact V2")
        if type(pending) is not WorkspaceMaterializationSessionEventV3:
            raise TypeError("resumable pending event must be exact V2")
        request = pending.append_request
        source = pending.source_evidence
        if type(request) is not WorkspaceMaterializationSessionAppendRequestV3:
            raise TypeError("resumable pending request must be exact V2")
        if type(source) is not WorkspaceMaterializationSessionSourceEvidenceV3:
            raise TypeError("resumable pending source must be exact V2")
        pending.__post_init__()
        head.__post_init__()
        expected_disposition = "executed"
        for node in state.plan_result.graph.nodes:
            if node.node_digest == binding.node_digest:
                expected_disposition = (
                    "reused" if node.head_observation.state == "current" else "executed"
                )
                break
        else:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable pending node is absent from the admitted graph"
            )
        exact_request = (
            revision == state.completed_session_head_revision + 1
            and head.workspace_session_ref == state.workspace_session_ref
            and head.epoch == state.epoch
            and head.cursor == state.completed_session_cursor + 1
            and head.event_digest == pending.event_digest
            and request.workspace_session_ref == state.workspace_session_ref
            and request.epoch == state.epoch
            and request.participant_ref == state.participant_ref
            and request.actor_ref == state.actor_ref
            and request.workflow_session_ref == state.workflow_session_ref
            and request.materialization_attempt_ref == state.materialization_attempt_ref
            and request.branch_baseline_ref == state.branch_baseline_ref
            and request.branch_baseline_digest == state.branch_baseline_digest
            and request.branch_baseline_grade == state.branch_baseline_grade
            and request.operation_ref == state.operation_ref
            and request.operation_digest == state.operation_digest
            and request.package_ref == binding.package.package_ref
            and request.expected_session_head_revision
            == state.completed_session_head_revision
            and request.expected_cursor == state.completed_session_cursor
            and request.expected_predecessor_event_digest
            == state.completed_predecessor_event_digest
            and source.disposition == expected_disposition
        )
        if not exact_request:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable pending event differs from next graph node authority"
            )
        WorkspaceSemanticMaterializationGraphCoordinator._validate_pending_source_semantics(
            binding=binding,
            planned=node.head_observation,
            source=source,
        )
        observed_source_head = state.ports.head_reader(
            binding.package.package_ref,
            source.head_reread_evidence.observation_role,
        )
        if (
            type(observed_source_head)
            is not WorkspaceSemanticMaterializationHeadRereadEvidenceV3
        ):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable pending package head is absent or foreign"
            )
        observed_source_head.__post_init__()
        if canonical_json_bytes(observed_source_head.to_wire()) != canonical_json_bytes(
            source.head_reread_evidence.to_wire()
        ):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable pending source head differs from persisted evidence"
            )

    @staticmethod
    def _validate_pending_source_semantics(
        *,
        binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
        planned: WorkspaceSemanticPackageHeadObservation,
        source: WorkspaceMaterializationSessionSourceEvidenceV3,
    ) -> None:
        """Apply the admitted node-result/reuse law before pending operation retry."""

        if type(source) is not WorkspaceMaterializationSessionSourceEvidenceV3:
            raise TypeError("resumable pending source must be exact V2")
        if type(planned) is not WorkspaceSemanticPackageHeadObservation:
            raise TypeError("resumable pending head observation must be exact")
        planned.__post_init__()
        source.__post_init__()
        source_head = source.head_reread_evidence
        required_results = {
            (item.role, item.contract) for item in binding.required_result_products
        }
        if (
            source_head.package != binding.package
            or source_head.source_identity_digest
            != binding.package_entry.source_identity_digest
            or source_head.code_intent_digest != binding.code_intent.intent_digest
            or source_head.code_match_digest != binding.code_match.match_digest
            or source_head.planning_input_digest != binding.planning_input_digest
            or (
                source_head.result_coordinate.role,
                source_head.result_coordinate.contract,
            )
            not in required_results
        ):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable pending source differs from next graph node semantics"
            )
        if planned.state == "current":
            closure = planned.historical_execution_input_closure_digest
            if type(closure) is not ContentDigest:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "resumable reusable node lacks exact historical closure"
                )
            WorkspaceSemanticMaterializationGraphCoordinator._validate_reuse_head(
                binding, planned, closure, source_head
            )
            return

        receipt = source.publication_receipt
        if receipt is None:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable executed node lacks publication receipt"
            )
        expected_prior_revision = (
            0
            if planned.predecessor_head_revision is None
            else planned.predecessor_head_revision
        )
        if (
            planned.state not in {"missing", "stale"}
            or source.disposition != "executed"
            or source_head.observation_role != "package_result"
            or receipt.request.expected_head_revision != expected_prior_revision
            or receipt.prior_head_revision != expected_prior_revision
            or receipt.head_revision != planned.expected_post_revision
            or source_head.materialization_head_revision
            != planned.expected_post_revision
            or receipt.request.package != binding.package
            or receipt.request.source_identity_digest
            != binding.package_entry.source_identity_digest
            or receipt.request.code_intent_digest != binding.code_intent.intent_digest
            or receipt.request.code_match_digest != binding.code_match.match_digest
            or receipt.request.planning_input_digest != binding.planning_input_digest
            or (
                receipt.request.result_coordinate.role,
                receipt.request.result_coordinate.contract,
            )
            not in required_results
        ):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "resumable pending publication differs from next graph node semantics"
            )

    @staticmethod
    def _planned_head(node_by_digest, binding):  # type: ignore[no-untyped-def]
        node = node_by_digest.get(binding.node_digest)
        if node is None:
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "graph node binding is absent"
            )
        return node.head_observation

    @staticmethod
    def _fulfill_dependencies(
        state: _GraphExecutionState,
        binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
        *,
        binding_by_digest: dict[
            ContentDigest, WorkspaceSemanticMaterializationNodeExecutionBinding
        ],
        edge_by_consumer_resolution: dict[
            tuple[ContentDigest, ContentDigest],
            WorkspaceSemanticMaterializationGraphEdge,
        ],
    ) -> tuple[
        tuple[WorkspaceFulfilledDependencyProductV3, ...], tuple[SemanticBody, ...]
    ]:
        products: list[WorkspaceFulfilledDependencyProductV3] = []
        bodies: list[SemanticBody] = []
        plan = state.plan_result
        for resolution in binding.incoming_target_resolutions:
            edge = edge_by_consumer_resolution.get(
                (binding.node_digest, resolution.resolution_digest)
            )
            if edge is None:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "dependency edge differs from execution binding"
                )
            target = binding_by_digest.get(edge.target_node_digest)
            if target is None:
                raise WorkspaceSemanticMaterializationGraphExecutionError(
                    "dependency target binding is absent"
                )
            h1 = state.ports.head_reader(target.package.package_ref, "dependency_h1")
            if h1 is None:
                raise _CoordinatorTerminalFailure(
                    WorkspaceSemanticMaterializationTerminalFailureV3.create(
                        plan_result=plan,
                        terminal_node_digest=binding.node_digest,
                        terminal_stage="dependency_head_reread",
                        failure_code="target_head_absent",
                        ordered_completed_fulfilled_products=tuple(products),
                        evidence_context=WorkspaceSemanticMaterializationTerminalEvidenceContextV3(
                            target_resolution=resolution
                        ),
                    )
                )
            if type(h1) is not WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
                raise TypeError("dependency H1 reader returned a foreign value")
            h1.__post_init__()
            body = state.ports.body_reader(h1.result_coordinate)
            if body is None:
                raise _CoordinatorTerminalFailure(
                    WorkspaceSemanticMaterializationTerminalFailureV3.create(
                        plan_result=plan,
                        terminal_node_digest=binding.node_digest,
                        terminal_stage="dependency_body_read",
                        failure_code="body_absent",
                        ordered_completed_fulfilled_products=tuple(products),
                        evidence_context=WorkspaceSemanticMaterializationTerminalEvidenceContextV3(
                            target_resolution=resolution,
                            head_h1=h1,
                            body_coordinate=h1.result_coordinate,
                        ),
                    )
                )
            if type(body) is not SemanticBody:
                raise TypeError("dependency body reader returned a foreign value")
            try:
                body.__post_init__()
                body_matches = canonical_json_bytes(
                    body.coordinate.to_wire()
                ) == canonical_json_bytes(h1.result_coordinate.to_wire())
            except (TypeError, ValueError):
                body_matches = False
            if not body_matches:
                raise _CoordinatorTerminalFailure(
                    WorkspaceSemanticMaterializationTerminalFailureV3.create(
                        plan_result=plan,
                        terminal_node_digest=binding.node_digest,
                        terminal_stage="dependency_body_read",
                        failure_code="body_invalid",
                        ordered_completed_fulfilled_products=tuple(products),
                        evidence_context=WorkspaceSemanticMaterializationTerminalEvidenceContextV3(
                            target_resolution=resolution,
                            head_h1=h1,
                            body_coordinate=h1.result_coordinate,
                            observed_body=body.canonical_body,
                        ),
                    )
                )
            h2 = state.ports.head_reader(target.package.package_ref, "dependency_h2")
            if h2 is None:
                raise _CoordinatorTerminalFailure(
                    WorkspaceSemanticMaterializationTerminalFailureV3.create(
                        plan_result=plan,
                        terminal_node_digest=binding.node_digest,
                        terminal_stage="dependency_head_reread",
                        failure_code="target_head_disappeared",
                        ordered_completed_fulfilled_products=tuple(products),
                        evidence_context=WorkspaceSemanticMaterializationTerminalEvidenceContextV3(
                            target_resolution=resolution,
                            head_h1=h1,
                            body=body.canonical_body,
                        ),
                    )
                )
            if type(h2) is not WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
                raise TypeError("dependency H2 reader returned a foreign value")
            h2.__post_init__()
            try:
                product = _create_coordinator_fulfilled_dependency_product_v2(
                    plan_result=plan,
                    consumer_binding=binding,
                    target_binding=target,
                    target_resolution=resolution,
                    head_h1=h1,
                    head_h2=h2,
                    consumed_body_coordinate=body.coordinate,
                )
            except Exception as error:
                raise _CoordinatorTerminalFailure(
                    WorkspaceSemanticMaterializationTerminalFailureV3.create(
                        plan_result=plan,
                        terminal_node_digest=binding.node_digest,
                        terminal_stage="dependency_head_reread",
                        failure_code="target_head_moved",
                        ordered_completed_fulfilled_products=tuple(products),
                        evidence_context=WorkspaceSemanticMaterializationTerminalEvidenceContextV3(
                            target_resolution=resolution,
                            head_h1=h1,
                            body=body.canonical_body,
                            head_h2=h2,
                        ),
                    )
                ) from error
            products.append(product)
            bodies.append(body)
        return tuple(products), tuple(bodies)

    @staticmethod
    def _validate_prepared_operation(
        *,
        state: _GraphExecutionState,
        binding: WorkspaceSemanticMaterializationNodeExecutionBinding,
        preparation: WorkspaceSemanticMaterializationNodePreparation,
        operation: WorkspaceMaterializeOperation,
        operation_admission: WorkspaceMaterializeOperationAdmission,
    ) -> None:
        if type(operation) is not WorkspaceMaterializeOperation:
            raise TypeError("prepared graph operation must be exact")
        if type(operation_admission) is not WorkspaceMaterializeOperationAdmission:
            raise TypeError("prepared graph operation admission must be exact")
        request = operation_admission.request
        profile = binding.code_match.selected_binding.profile_declaration
        if (
            request.workspace_session_ref != state.workspace_session_ref
            or request.epoch != state.epoch
            or request.participant_ref != state.participant_ref
            or request.actor_ref != state.actor_ref
            or request.workflow_session_ref != state.workflow_session_ref
            or request.materialization_attempt_ref != state.materialization_attempt_ref
            or request.branch_baseline_ref != state.branch_baseline_ref
            or request.branch_baseline_digest != state.branch_baseline_digest.value
            or request.branch_baseline_grade != state.branch_baseline_grade
            or request.package_ref != binding.package.package_ref
            or request.package_kind != binding.package.package_kind
            or request.manifest_digest != binding.package.manifest_digest.value
            or request.source_authority_ref
            != binding.package_entry.source_authority_ref
            or request.source_authority_digest
            != binding.package_entry.source_authority_digest.value
            or request.operation_ref != state.operation_ref
            or request.operation_digest != state.operation_digest.value
            or request.profile_ref != profile.profile_ref
            or request.profile_digest != profile.digest.value
            or request.expected_materialization_head_revision
            != preparation.expected_package_head_revision
            or request.expected_session_head_revision
            != preparation.expected_session_head_revision
            or request.expected_session_cursor != preparation.expected_session_cursor
            or (
                None
                if request.expected_predecessor_event_digest is None
                else ContentDigest(request.expected_predecessor_event_digest)
            )
            != preparation.expected_predecessor_event_digest
        ):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "prepared operation differs from graph-node preparation"
            )

    @staticmethod
    def _validate_reuse_head(binding, planned, closure, head):  # type: ignore[no-untyped-def]
        if type(head) is not WorkspaceSemanticMaterializationHeadRereadEvidenceV3:
            raise TypeError("reuse head must be exact")
        if (
            head.observation_role != "package_reuse"
            or head.package != binding.package
            or head.source_identity_digest
            != binding.package_entry.source_identity_digest
            or head.code_intent_digest != binding.code_intent.intent_digest
            or head.code_match_digest != binding.code_match.match_digest
            or head.planning_input_digest != binding.planning_input_digest
            or head.execution_input_closure_digest != closure
            or head.execution_input_closure_digest
            != planned.historical_execution_input_closure_digest
            or head.materialization_head_revision != planned.predecessor_head_revision
            or head.materialization_head_digest != planned.predecessor_head_digest
        ):
            raise WorkspaceSemanticMaterializationGraphExecutionError(
                "planned current head is not exactly reusable"
            )


__all__ = [
    "AdmittedWorkspaceSemanticMaterializationGraphExecution",
    "WorkspaceSemanticMaterializationGraphCoordinator",
    "WorkspaceSemanticMaterializationGraphExecutionError",
    "WorkspaceSemanticMaterializationNodePreparation",
]
