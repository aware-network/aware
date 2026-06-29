from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Literal
from uuid import UUID

from aware_code_ontology.package.code_package_artifact import CodePackageArtifactRef


CODE_PACKAGE_ARTIFACT_DELTA_PLAN_SCHEMA = (
    "aware.code.package.artifact_delta_plan.v1"
)
CODE_PACKAGE_ARTIFACT_DELTA_PLAN_REF_KEY = "code_package_artifact_delta_plan"
ArtifactOperationKind = Literal[
    "create",
    "refresh",
    "upsert",
    "noop_existing",
    "delete",
]


@dataclass(frozen=True, slots=True)
class CodePackageArtifactCurrentStateRow:
    output_key: str
    artifact_key: str
    identity_key: str
    signature_hash: str
    status: str | None = None
    digest: str | None = None
    relative_path: str | None = None
    uri: str | None = None
    media_type: str | None = None
    artifact_family: str | None = None
    artifact_role: str | None = None
    producer_key: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> CodePackageArtifactCurrentStateRow | None:
        output_key = _optional_text(payload.get("output_key"))
        artifact_key = _optional_text(payload.get("artifact_key"))
        signature_hash = _optional_text(payload.get("signature_hash"))
        if output_key is None or artifact_key is None or signature_hash is None:
            return None
        identity_key = _optional_text(payload.get("identity_key")) or (
            artifact_identity_key(output_key=output_key, artifact_key=artifact_key)
        )
        return cls(
            output_key=output_key,
            artifact_key=artifact_key,
            identity_key=identity_key,
            signature_hash=signature_hash,
            status=_optional_text(payload.get("status")),
            digest=_optional_text(payload.get("digest")),
            relative_path=_optional_text(payload.get("relative_path")),
            uri=_optional_text(payload.get("uri")),
            media_type=_optional_text(payload.get("media_type")),
            artifact_family=_optional_text(payload.get("artifact_family")),
            artifact_role=_optional_text(payload.get("artifact_role")),
            producer_key=_optional_text(payload.get("producer_key")),
        )

    def to_payload(self) -> dict[str, object]:
        return _without_none(
            {
                "output_key": self.output_key,
                "artifact_key": self.artifact_key,
                "identity_key": self.identity_key,
                "signature_hash": self.signature_hash,
                "status": self.status,
                "digest": self.digest,
                "relative_path": self.relative_path,
                "uri": self.uri,
                "media_type": self.media_type,
                "artifact_family": self.artifact_family,
                "artifact_role": self.artifact_role,
                "producer_key": self.producer_key,
            }
        )


@dataclass(frozen=True, slots=True)
class CodePackageArtifactCurrentStateIndex:
    status: str
    artifacts: tuple[CodePackageArtifactCurrentStateRow, ...]
    code_package_id: str | None = None
    snapshot_fingerprint: str | None = None
    source_snapshot_fingerprint: str | None = None
    head_commit_id: str | None = None
    object_instance_graph_commit_id: str | None = None
    graph_hash_post: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object] | None,
    ) -> CodePackageArtifactCurrentStateIndex | None:
        if payload is None:
            return None
        raw_artifacts = payload.get("artifacts")
        if not isinstance(raw_artifacts, list):
            return None
        rows = tuple(
            row
            for item in raw_artifacts
            if isinstance(item, Mapping)
            if (row := CodePackageArtifactCurrentStateRow.from_payload(item))
            is not None
        )
        return cls(
            status=_optional_text(payload.get("current_state_status")) or "hydrated",
            artifacts=rows,
            code_package_id=_optional_text(payload.get("code_package_id")),
            snapshot_fingerprint=_optional_text(payload.get("snapshot_fingerprint")),
            source_snapshot_fingerprint=_optional_text(
                payload.get("source_snapshot_fingerprint")
            ),
            head_commit_id=_optional_text(payload.get("head_commit_id")),
            object_instance_graph_commit_id=_optional_text(
                payload.get("object_instance_graph_commit_id")
            ),
            graph_hash_post=_optional_text(payload.get("graph_hash_post")),
        )

    @property
    def rows_by_identity_key(
        self,
    ) -> dict[str, CodePackageArtifactCurrentStateRow]:
        return {row.identity_key: row for row in self.artifacts}

    def to_payload(self) -> dict[str, object]:
        return _without_none(
            {
                "current_state_status": self.status,
                "code_package_id": self.code_package_id,
                "snapshot_fingerprint": self.snapshot_fingerprint,
                "source_snapshot_fingerprint": self.source_snapshot_fingerprint,
                "head_commit_id": self.head_commit_id,
                "object_instance_graph_commit_id": (
                    self.object_instance_graph_commit_id
                ),
                "graph_hash_post": self.graph_hash_post,
                "artifact_count": len(self.artifacts),
                "artifacts": [row.to_payload() for row in self.artifacts],
            }
        )


@dataclass(frozen=True, slots=True)
class CodePackageArtifactAuthoritativeScope:
    code_package_id: str
    output_key: str
    producer_key: str | None = None
    artifact_family: str | None = None
    artifact_role: str | None = None

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> CodePackageArtifactAuthoritativeScope | None:
        code_package_id = _optional_text(payload.get("code_package_id"))
        output_key = _optional_text(payload.get("output_key"))
        if code_package_id is None or output_key is None:
            return None
        return cls(
            code_package_id=code_package_id,
            output_key=output_key,
            producer_key=_optional_text(payload.get("producer_key")),
            artifact_family=_optional_text(payload.get("artifact_family")),
            artifact_role=_optional_text(payload.get("artifact_role")),
        )

    def matches(self, row: CodePackageArtifactCurrentStateRow) -> bool:
        return (
            row.output_key == self.output_key
            and _optional_match(self.producer_key, row.producer_key)
            and _optional_match(self.artifact_family, row.artifact_family)
            and _optional_match(self.artifact_role, row.artifact_role)
        )

    def to_payload(self) -> dict[str, object]:
        return _without_none(
            {
                "code_package_id": self.code_package_id,
                "output_key": self.output_key,
                "producer_key": self.producer_key,
                "artifact_family": self.artifact_family,
                "artifact_role": self.artifact_role,
            }
        )


@dataclass(frozen=True, slots=True)
class CodePackageArtifactOperationCounts:
    create: int = 0
    refresh: int = 0
    upsert: int = 0
    noop_existing: int = 0
    delete: int = 0

    def plus(
        self,
        other: CodePackageArtifactOperationCounts,
    ) -> CodePackageArtifactOperationCounts:
        return CodePackageArtifactOperationCounts(
            create=self.create + other.create,
            refresh=self.refresh + other.refresh,
            upsert=self.upsert + other.upsert,
            noop_existing=self.noop_existing + other.noop_existing,
            delete=self.delete + other.delete,
        )

    def increment(
        self,
        operation: ArtifactOperationKind,
    ) -> CodePackageArtifactOperationCounts:
        return CodePackageArtifactOperationCounts(
            create=self.create + int(operation == "create"),
            refresh=self.refresh + int(operation == "refresh"),
            upsert=self.upsert + int(operation == "upsert"),
            noop_existing=(
                self.noop_existing + int(operation == "noop_existing")
            ),
            delete=self.delete + int(operation == "delete"),
        )

    def to_payload(self) -> dict[str, int]:
        return {
            "create": self.create,
            "refresh": self.refresh,
            "upsert": self.upsert,
            "noop_existing": self.noop_existing,
            "delete": self.delete,
        }

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object] | None,
    ) -> CodePackageArtifactOperationCounts:
        if payload is None:
            return cls()
        return cls(
            create=_int_payload(payload.get("create")),
            refresh=_int_payload(payload.get("refresh")),
            upsert=_int_payload(payload.get("upsert")),
            noop_existing=_int_payload(payload.get("noop_existing")),
            delete=_int_payload(payload.get("delete")),
        )


@dataclass(frozen=True, slots=True)
class CodePackageArtifactDeltaOperation:
    operation: ArtifactOperationKind
    code_package_id: str
    output_key: str
    artifact_key: str
    identity_key: str
    signature_hash: str
    status: str | None = None
    digest: str | None = None
    relative_path: str | None = None
    classification: str | None = None
    reason: str | None = None
    ordinal: int | None = None
    current_signature_hash: str | None = None

    def to_payload(self) -> dict[str, object]:
        return _without_none(
            {
                "operation": self.operation,
                "classification": self.classification,
                "reason": self.reason,
                "code_package_id": self.code_package_id,
                "output_key": self.output_key,
                "artifact_key": self.artifact_key,
                "identity_key": self.identity_key,
                "signature_hash": self.signature_hash,
                "current_signature_hash": self.current_signature_hash,
                "status": self.status,
                "digest": self.digest,
                "relative_path": self.relative_path,
                "ordinal": self.ordinal,
            }
        )

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> CodePackageArtifactDeltaOperation | None:
        operation = _operation_kind(payload.get("operation"))
        code_package_id = _optional_text(payload.get("code_package_id"))
        output_key = _optional_text(payload.get("output_key"))
        artifact_key = _optional_text(payload.get("artifact_key"))
        signature_hash = _optional_text(payload.get("signature_hash"))
        if (
            operation is None
            or code_package_id is None
            or output_key is None
            or artifact_key is None
            or signature_hash is None
        ):
            return None
        identity_key = _optional_text(payload.get("identity_key")) or (
            artifact_identity_key(output_key=output_key, artifact_key=artifact_key)
        )
        return cls(
            operation=operation,
            code_package_id=code_package_id,
            output_key=output_key,
            artifact_key=artifact_key,
            identity_key=identity_key,
            signature_hash=signature_hash,
            status=_optional_text(payload.get("status")),
            digest=_optional_text(payload.get("digest")),
            relative_path=_optional_text(payload.get("relative_path")),
            classification=_optional_text(payload.get("classification")),
            reason=_optional_text(payload.get("reason")),
            ordinal=_optional_int(payload.get("ordinal")),
            current_signature_hash=_optional_text(
                payload.get("current_signature_hash")
            ),
        )


@dataclass(frozen=True, slots=True)
class CodePackageArtifactDeltaPlan:
    status: str
    classification_policy: str
    current_state_status: str
    current_artifact_count: int
    artifact_ref_count: int
    unique_artifact_ref_count: int
    code_package_ids: tuple[str, ...]
    operation_counts: CodePackageArtifactOperationCounts
    operations: tuple[CodePackageArtifactDeltaOperation, ...]
    next_action: str
    authoritative_scopes: tuple[CodePackageArtifactAuthoritativeScope, ...] = ()

    @property
    def all_operations_noop_existing(self) -> bool:
        return bool(self.operations) and all(
            operation.operation == "noop_existing" for operation in self.operations
        )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": CODE_PACKAGE_ARTIFACT_DELTA_PLAN_SCHEMA,
            "status": self.status,
            "classification_policy": self.classification_policy,
            "current_state_status": self.current_state_status,
            "current_artifact_count": self.current_artifact_count,
            "artifact_ref_count": self.artifact_ref_count,
            "unique_artifact_ref_count": self.unique_artifact_ref_count,
            "code_package_count": len(self.code_package_ids),
            "code_package_ids": list(self.code_package_ids),
            "authoritative_scope_count": len(self.authoritative_scopes),
            "authoritative_scopes": [
                scope.to_payload() for scope in self.authoritative_scopes
            ],
            "operation_counts": self.operation_counts.to_payload(),
            "operations": [operation.to_payload() for operation in self.operations],
            "next_action": self.next_action,
        }
        payload["signature_hash"] = _stable_json_hash(payload)
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, object],
    ) -> CodePackageArtifactDeltaPlan | None:
        raw_operations = payload.get("operations")
        if not isinstance(raw_operations, list):
            return None
        operations = tuple(
            operation
            for item in raw_operations
            if isinstance(item, Mapping)
            if (
                operation := CodePackageArtifactDeltaOperation.from_payload(item)
            )
            is not None
        )
        raw_package_ids = payload.get("code_package_ids")
        package_ids = (
            tuple(str(item) for item in raw_package_ids if item)
            if isinstance(raw_package_ids, list)
            else ()
        )
        raw_authoritative_scopes = payload.get("authoritative_scopes")
        authoritative_scopes = (
            tuple(
                scope
                for item in raw_authoritative_scopes
                if isinstance(item, Mapping)
                if (
                    scope := CodePackageArtifactAuthoritativeScope.from_payload(
                        item,
                    )
                )
                is not None
            )
            if isinstance(raw_authoritative_scopes, list)
            else ()
        )
        raw_operation_counts = payload.get("operation_counts")
        return cls(
            status=_optional_text(payload.get("status")) or "empty",
            classification_policy=(
                _optional_text(payload.get("classification_policy"))
                or "not_hydrated"
            ),
            current_state_status=(
                _optional_text(payload.get("current_state_status"))
                or "not_hydrated"
            ),
            current_artifact_count=_int_payload(
                payload.get("current_artifact_count")
            ),
            artifact_ref_count=_int_payload(payload.get("artifact_ref_count")),
            unique_artifact_ref_count=_int_payload(
                payload.get("unique_artifact_ref_count")
            ),
            code_package_ids=package_ids,
            operation_counts=CodePackageArtifactOperationCounts.from_payload(
                raw_operation_counts
                if isinstance(raw_operation_counts, Mapping)
                else None
            ),
            operations=operations,
            authoritative_scopes=authoritative_scopes,
            next_action=(
                _optional_text(payload.get("next_action"))
                or "hydrate_current_code_package_artifact_state_for_create_refresh_delete"
            ),
        )


def code_package_artifact_delta_plan_from_package_plans(
    *,
    package_plans: tuple[CodePackageArtifactDeltaPlan, ...],
) -> CodePackageArtifactDeltaPlan:
    plans = tuple(plan for plan in package_plans if plan.status != "empty")
    operations = tuple(
        operation for plan in plans for operation in plan.operations
    )
    authoritative_scopes = tuple(
        scope for plan in plans for scope in plan.authoritative_scopes
    )
    package_ids = tuple(
        sorted({package_id for plan in plans for package_id in plan.code_package_ids})
    )
    operation_counts = CodePackageArtifactOperationCounts()
    for plan in plans:
        operation_counts = operation_counts.plus(plan.operation_counts)
    policies = {plan.classification_policy for plan in plans}
    state_statuses = {plan.current_state_status for plan in plans}
    artifact_ref_count = sum(plan.artifact_ref_count for plan in plans)
    return CodePackageArtifactDeltaPlan(
        status="planned" if artifact_ref_count else "empty",
        classification_policy=_combined_text(policies),
        current_state_status=_combined_text(state_statuses),
        current_artifact_count=sum(plan.current_artifact_count for plan in plans),
        artifact_ref_count=artifact_ref_count,
        unique_artifact_ref_count=sum(
            plan.unique_artifact_ref_count for plan in plans
        ),
        code_package_ids=package_ids,
        operation_counts=operation_counts,
        operations=operations,
        next_action=_combined_next_action(policies),
        authoritative_scopes=authoritative_scopes,
    )


def code_package_artifact_delta_plan_from_refs(
    *,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
    current_artifact_state: CodePackageArtifactCurrentStateIndex | None = None,
    authoritative_scopes: tuple[
        CodePackageArtifactAuthoritativeScope,
        ...,
    ] = (),
) -> CodePackageArtifactDeltaPlan:
    final_refs_by_key: dict[tuple[str, str, str], CodePackageArtifactDeltaOperation] = {}
    operations: list[CodePackageArtifactDeltaOperation] = []
    current_rows_by_key = (
        current_artifact_state.rows_by_identity_key
        if current_artifact_state is not None
        else {}
    )
    for ordinal, artifact_ref in enumerate(code_package_artifact_refs):
        code_package_id = _required_code_package_artifact_ref_package_id(
            artifact_ref=artifact_ref,
        )
        output_key = str(artifact_ref.output_key or "").strip()
        artifact_key = str(artifact_ref.artifact_key or "").strip()
        if not output_key or not artifact_key:
            raise RuntimeError(
                "CodePackageArtifactDeltaPlan requires output_key and "
                "artifact_key for package-owned artifact refs"
            )
        identity_key = artifact_identity_key(
            output_key=output_key,
            artifact_key=artifact_key,
        )
        signature_hash = code_package_artifact_ref_signature_hash(
            artifact_ref=artifact_ref,
        )
        operation_key = (str(code_package_id), output_key, artifact_key)
        previous = final_refs_by_key.get(operation_key)
        if previous is not None:
            operations.append(
                CodePackageArtifactDeltaOperation(
                    operation="noop_existing",
                    reason=(
                        "duplicate_incoming_ref"
                        if previous.signature_hash == signature_hash
                        else "superseded_incoming_ref"
                    ),
                    code_package_id=str(code_package_id),
                    output_key=output_key,
                    artifact_key=artifact_key,
                    identity_key=identity_key,
                    signature_hash=signature_hash,
                    ordinal=ordinal,
                )
            )
        final_refs_by_key[operation_key] = CodePackageArtifactDeltaOperation(
            operation="upsert",
            code_package_id=str(code_package_id),
            output_key=output_key,
            artifact_key=artifact_key,
            identity_key=identity_key,
            signature_hash=signature_hash,
            status=str(getattr(artifact_ref.status, "value", artifact_ref.status)),
            digest=artifact_ref.digest,
            relative_path=artifact_ref.relative_path,
        )
    final_operations = tuple(
        final_refs_by_key[key]
        for key in sorted(
            final_refs_by_key,
            key=lambda item: (item[0], item[1], item[2]),
        )
    )
    classified_operations = tuple(
        _classified_artifact_operation(
            operation=operation,
            current_rows_by_key=current_rows_by_key,
            current_state_hydrated=current_artifact_state is not None,
        )
        for operation in final_operations
    )
    delete_operations = _delete_artifact_operations_from_authoritative_scopes(
        desired_identity_keys=frozenset(
            operation.identity_key for operation in final_operations
        ),
        current_artifact_state=current_artifact_state,
        authoritative_scopes=authoritative_scopes,
    )
    all_operations = (*operations, *classified_operations, *delete_operations)
    operation_counts = CodePackageArtifactOperationCounts()
    for operation in all_operations:
        operation_counts = operation_counts.increment(operation.operation)
    current_state_hydrated = current_artifact_state is not None
    return CodePackageArtifactDeltaPlan(
        status=(
            "planned"
            if code_package_artifact_refs or delete_operations
            else "empty"
        ),
        classification_policy=(
            "current_code_package_artifact_state"
            if current_state_hydrated
            else "upsert_without_current_artifact_state"
        ),
        current_state_status=(
            current_artifact_state.status
            if current_artifact_state is not None
            else "not_hydrated"
        ),
        current_artifact_count=(
            len(current_artifact_state.artifacts)
            if current_artifact_state is not None
            else 0
        ),
        artifact_ref_count=len(code_package_artifact_refs),
        unique_artifact_ref_count=len(final_operations),
        code_package_ids=tuple(
            sorted({operation.code_package_id for operation in all_operations})
        ),
        operation_counts=operation_counts,
        operations=all_operations,
        next_action=(
            "apply_classified_code_package_artifact_delta_plan"
            if current_state_hydrated
            else "hydrate_current_code_package_artifact_state_for_create_refresh_delete"
        ),
        authoritative_scopes=authoritative_scopes,
    )


def artifact_identity_key(*, output_key: str, artifact_key: str) -> str:
    return json.dumps(
        [output_key, artifact_key],
        separators=(",", ":"),
        sort_keys=True,
    )


def _classified_artifact_operation(
    *,
    operation: CodePackageArtifactDeltaOperation,
    current_rows_by_key: Mapping[str, CodePackageArtifactCurrentStateRow],
    current_state_hydrated: bool,
) -> CodePackageArtifactDeltaOperation:
    if not current_state_hydrated:
        return _replace_operation(
            operation=operation,
            operation_kind="upsert",
            classification="create_or_refresh_requires_current_state",
        )
    current = current_rows_by_key.get(operation.identity_key)
    if current is None:
        return _replace_operation(
            operation=operation,
            operation_kind="create",
            classification="missing_from_current_artifact_state",
        )
    if current.signature_hash == operation.signature_hash:
        return _replace_operation(
            operation=operation,
            operation_kind="noop_existing",
            classification="current_signature_match",
            current_signature_hash=current.signature_hash,
        )
    return _replace_operation(
        operation=operation,
        operation_kind="refresh",
        classification="current_signature_changed",
        current_signature_hash=current.signature_hash,
    )


def _replace_operation(
    *,
    operation: CodePackageArtifactDeltaOperation,
    operation_kind: ArtifactOperationKind,
    classification: str,
    current_signature_hash: str | None = None,
) -> CodePackageArtifactDeltaOperation:
    return CodePackageArtifactDeltaOperation(
        operation=operation_kind,
        code_package_id=operation.code_package_id,
        output_key=operation.output_key,
        artifact_key=operation.artifact_key,
        identity_key=operation.identity_key,
        signature_hash=operation.signature_hash,
        status=operation.status,
        digest=operation.digest,
        relative_path=operation.relative_path,
        classification=classification,
        reason=operation.reason,
        ordinal=operation.ordinal,
        current_signature_hash=current_signature_hash,
    )


def _delete_artifact_operations_from_authoritative_scopes(
    *,
    desired_identity_keys: frozenset[str],
    current_artifact_state: CodePackageArtifactCurrentStateIndex | None,
    authoritative_scopes: tuple[
        CodePackageArtifactAuthoritativeScope,
        ...,
    ],
) -> tuple[CodePackageArtifactDeltaOperation, ...]:
    if current_artifact_state is None or not authoritative_scopes:
        return ()
    code_package_id = current_artifact_state.code_package_id
    if code_package_id is None:
        return ()
    operations: list[CodePackageArtifactDeltaOperation] = []
    for row in sorted(
        current_artifact_state.artifacts,
        key=lambda item: (item.output_key, item.artifact_key),
    ):
        if row.identity_key in desired_identity_keys:
            continue
        if not any(scope.matches(row) for scope in authoritative_scopes):
            continue
        operations.append(
            CodePackageArtifactDeltaOperation(
                operation="delete",
                code_package_id=code_package_id,
                output_key=row.output_key,
                artifact_key=row.artifact_key,
                identity_key=row.identity_key,
                signature_hash=row.signature_hash,
                status=row.status,
                digest=row.digest,
                relative_path=row.relative_path,
                classification="missing_from_authoritative_artifact_scope",
                current_signature_hash=row.signature_hash,
            )
        )
    return tuple(operations)


def _combined_text(values: set[str]) -> str:
    if not values:
        return "not_hydrated"
    if len(values) == 1:
        return next(iter(values))
    return "mixed"


def _combined_next_action(policies: set[str]) -> str:
    if policies == {"current_code_package_artifact_state"}:
        return "apply_classified_code_package_artifact_delta_plan"
    return "hydrate_current_code_package_artifact_state_for_create_refresh_delete"


def _required_code_package_artifact_ref_package_id(
    *,
    artifact_ref: CodePackageArtifactRef,
) -> UUID:
    code_package_id = artifact_ref.code_package_id
    if code_package_id is None:
        raise RuntimeError(
            "CodePackageArtifactDeltaPlan requires code_package_id for "
            "package-owned artifact identity: "
            f"artifact_key={artifact_ref.artifact_key!r}"
        )
    return code_package_id


def _operation_kind(value: object) -> ArtifactOperationKind | None:
    if value == "create":
        return "create"
    if value == "refresh":
        return "refresh"
    if value == "upsert":
        return "upsert"
    if value == "noop_existing":
        return "noop_existing"
    if value == "delete":
        return "delete"
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def _int_payload(value: object) -> int:
    return _optional_int(value) or 0


def code_package_artifact_ref_signature_hash(
    *,
    artifact_ref: CodePackageArtifactRef,
) -> str:
    payload = artifact_ref.model_dump(mode="json", exclude_none=True)
    return _stable_json_hash(payload)


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _optional_match(expected: str | None, actual: str | None) -> bool:
    return expected is None or expected == actual


def _without_none(payload: Mapping[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None}


def _stable_json_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "CODE_PACKAGE_ARTIFACT_DELTA_PLAN_REF_KEY",
    "CODE_PACKAGE_ARTIFACT_DELTA_PLAN_SCHEMA",
    "CodePackageArtifactAuthoritativeScope",
    "CodePackageArtifactCurrentStateIndex",
    "CodePackageArtifactCurrentStateRow",
    "CodePackageArtifactDeltaOperation",
    "CodePackageArtifactDeltaPlan",
    "CodePackageArtifactOperationCounts",
    "artifact_identity_key",
    "code_package_artifact_ref_signature_hash",
    "code_package_artifact_delta_plan_from_package_plans",
    "code_package_artifact_delta_plan_from_refs",
]
