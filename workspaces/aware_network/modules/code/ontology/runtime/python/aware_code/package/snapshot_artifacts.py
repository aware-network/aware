from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast
from uuid import UUID

from aware_code.package.artifact_delta_plan import artifact_identity_key
from aware_code.package.artifact_delta_plan import (
    code_package_artifact_ref_signature_hash,
)
from aware_code.package.artifact_delta_plan import CodePackageArtifactCurrentStateIndex
from aware_code.package.snapshot_contract import (
    CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
)
from aware_code.package.snapshot_json import optional_text, stable_json_hash
from aware_code_ontology.package.code_package_artifact import CodePackageArtifactRef
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span


def code_package_artifact_state_index_from_refs(
    *,
    code_package_id: UUID,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> dict[str, object]:
    with commit_perf_span(
        phase="code_package.artifact_state_index.full_rows",
        category="code_package.artifact_state_index",
        metadata={"artifact_count": len(code_package_artifact_refs)},
    ):
        artifacts = [
            artifact_state_row_from_ref(
                code_package_id=code_package_id,
                artifact_ref=artifact_ref,
            )
            for artifact_ref in sorted(
                code_package_artifact_refs,
                key=lambda item: (item.output_key, item.artifact_key),
            )
        ]
    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
        "code_package_id": str(code_package_id),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    with commit_perf_span(
        phase="code_package.artifact_state_index.signature_hash",
        category="code_package.artifact_state_index",
        metadata={"artifact_count": len(artifacts)},
    ):
        payload["signature_hash"] = artifact_state_index_signature_hash(
            code_package_id=code_package_id,
            artifacts=artifacts,
        )
    return payload


def code_package_artifact_state_index_from_current_state(
    *,
    code_package_id: UUID,
    current_state: CodePackageArtifactCurrentStateIndex,
) -> dict[str, object]:
    if current_state.code_package_id not in {None, str(code_package_id)}:
        raise RuntimeError(
            "CodePackage artifact state targets a different package: "
            f"expected={code_package_id} actual={current_state.code_package_id}"
        )
    artifacts = [row.to_payload() for row in current_state.artifacts]
    if len({str(row["identity_key"]) for row in artifacts}) != len(artifacts):
        raise RuntimeError("CodePackage artifact state contains duplicate identities")
    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
        "code_package_id": str(code_package_id),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    payload["signature_hash"] = artifact_state_index_signature_hash(
        code_package_id=code_package_id,
        artifacts=artifacts,
    )
    return payload


_CODE_PACKAGE_ARTIFACT_STATE_ROW_LEGACY_KEYS = frozenset(
    {
        "output_key",
        "artifact_key",
        "identity_key",
        "signature_hash",
        "status",
        "digest",
        "relative_path",
        "uri",
        "media_type",
        "artifact_family",
        "artifact_role",
        "producer_key",
    }
)
_CODE_PACKAGE_ARTIFACT_STATE_ROW_KEYS = frozenset(
    (*_CODE_PACKAGE_ARTIFACT_STATE_ROW_LEGACY_KEYS, "artifact_ref")
)


def code_package_artifact_state_index_from_refs_delta(
    *,
    code_package_id: UUID,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
    previous_snapshot_index_payload: Mapping[str, object] | None,
    changed_relative_paths: frozenset[str],
) -> dict[str, object] | None:
    if not changed_relative_paths or previous_snapshot_index_payload is None:
        return None
    previous_state = previous_snapshot_index_payload.get("artifact_state_index")
    if not isinstance(previous_state, Mapping):
        return None
    if previous_state.get("schema") != CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA:
        return None
    if previous_state.get("code_package_id") != str(code_package_id):
        return None
    raw_previous_artifacts = previous_state.get("artifacts")
    if not isinstance(raw_previous_artifacts, list):
        return None
    if previous_state.get("artifact_count") != len(code_package_artifact_refs):
        return None
    if len(raw_previous_artifacts) != len(code_package_artifact_refs):
        return None

    with commit_perf_span(
        phase="code_package.artifact_state_index.delta_rows",
        category="code_package.artifact_state_index",
        metadata={
            "artifact_count": len(code_package_artifact_refs),
            "changed_path_count": len(changed_relative_paths),
        },
    ):
        artifacts: list[dict[str, object]] = []
        current_identity_keys: set[str] = set()
        current_relative_paths: set[str] = set()
        sorted_current_refs = sorted(
            code_package_artifact_refs,
            key=lambda item: (item.output_key, item.artifact_key),
        )
        for artifact_ref, raw_previous_row in zip(
            sorted_current_refs,
            raw_previous_artifacts,
            strict=True,
        ):
            previous_row = validated_code_package_artifact_state_row(raw_previous_row)
            if previous_row is None:
                return None
            output_key = (artifact_ref.output_key or "").strip()
            artifact_key = (artifact_ref.artifact_key or "").strip()
            relative_path = optional_text(artifact_ref.relative_path)
            if not output_key or not artifact_key or relative_path is None:
                return None
            identity_key = artifact_identity_key(
                output_key=output_key,
                artifact_key=artifact_key,
            )
            if identity_key in current_identity_keys:
                return None
            current_identity_keys.add(identity_key)
            current_relative_paths.add(relative_path)
            if previous_row.get("identity_key") != identity_key:
                return None
            if previous_row.get("relative_path") != relative_path:
                return None

            if relative_path in changed_relative_paths:
                artifacts.append(
                    artifact_state_row_from_ref(
                        code_package_id=code_package_id,
                        artifact_ref=artifact_ref,
                    )
                )
                continue

            if "artifact_ref" not in previous_row:
                artifacts.append(
                    artifact_state_row_from_ref(
                        code_package_id=code_package_id,
                        artifact_ref=artifact_ref,
                    )
                )
                continue

            artifacts.append(previous_row)

    if not changed_relative_paths.issubset(current_relative_paths):
        return None

    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
        "code_package_id": str(code_package_id),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    with commit_perf_span(
        phase="code_package.artifact_state_index.signature_hash",
        category="code_package.artifact_state_index",
        metadata={"artifact_count": len(artifacts)},
    ):
        payload["signature_hash"] = artifact_state_index_signature_hash(
            code_package_id=code_package_id,
            artifacts=artifacts,
        )
    return payload


def artifact_state_index_signature_hash(
    *,
    code_package_id: UUID,
    artifacts: Sequence[Mapping[str, object]],
) -> str:
    return stable_json_hash(
        {
            "schema": CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
            "code_package_id": str(code_package_id),
            "artifact_count": len(artifacts),
            "artifact_signatures": [
                {
                    "identity_key": str(row["identity_key"]),
                    "signature_hash": str(row["signature_hash"]),
                }
                for row in artifacts
            ],
        }
    )


def validated_code_package_artifact_state_row(
    raw_row: object,
) -> dict[str, object] | None:
    if not isinstance(raw_row, Mapping):
        return None
    if isinstance(raw_row, dict) and all(isinstance(key, str) for key in raw_row):
        row = cast(dict[str, object], raw_row)
    else:
        row = {
            str(key): value for key, value in raw_row.items() if isinstance(key, str)
        }
    if set(row) not in {
        _CODE_PACKAGE_ARTIFACT_STATE_ROW_LEGACY_KEYS,
        _CODE_PACKAGE_ARTIFACT_STATE_ROW_KEYS,
    }:
        return None
    output_key = row.get("output_key")
    artifact_key = row.get("artifact_key")
    identity_key = row.get("identity_key")
    relative_path = row.get("relative_path")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (output_key, artifact_key, identity_key, relative_path)
    ):
        return None
    if identity_key != artifact_identity_key(
        output_key=str(output_key),
        artifact_key=str(artifact_key),
    ):
        return None
    return row


def artifact_state_row_from_ref(
    *,
    code_package_id: UUID,
    artifact_ref: CodePackageArtifactRef,
) -> dict[str, object]:
    if artifact_ref.code_package_id != code_package_id:
        raise RuntimeError(
            "CodePackage artifact state index ref targets a different package: "
            f"expected={code_package_id} actual={artifact_ref.code_package_id}"
        )
    output_key = (artifact_ref.output_key or "").strip()
    artifact_key = (artifact_ref.artifact_key or "").strip()
    if not output_key:
        raise RuntimeError("CodePackage artifact state index ref missing output_key")
    if not artifact_key:
        raise RuntimeError("CodePackage artifact state index ref missing artifact_key")
    return {
        "output_key": output_key,
        "artifact_key": artifact_key,
        "identity_key": artifact_identity_key(
            output_key=output_key,
            artifact_key=artifact_key,
        ),
        "signature_hash": code_package_artifact_ref_signature_hash(
            artifact_ref=artifact_ref
        ),
        "status": str(getattr(artifact_ref.status, "value", artifact_ref.status)),
        "digest": optional_text(artifact_ref.digest),
        "relative_path": optional_text(artifact_ref.relative_path),
        "uri": optional_text(artifact_ref.uri),
        "media_type": optional_text(artifact_ref.media_type),
        "artifact_family": optional_text(artifact_ref.artifact_family),
        "artifact_role": optional_text(artifact_ref.artifact_role),
        "producer_key": optional_text(artifact_ref.producer_key),
        "artifact_ref": artifact_ref.model_dump(mode="json", exclude_none=True),
    }
