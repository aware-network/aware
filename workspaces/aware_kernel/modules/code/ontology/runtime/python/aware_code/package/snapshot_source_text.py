from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from uuid import UUID

from aware_code_ontology.code.code_plan import CodeContentPlan
from aware_code_ontology.code.code_plan import CodePackagePathRole
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_code.package.snapshot_contract import (
    CODE_PACKAGE_SOURCE_TEXT_HASH_INDEX_SCHEMA,
    CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
)
from aware_code.package.snapshot_json import stable_json_hash
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span


@dataclass(frozen=True, slots=True)
class CodePackageSourceSnapshotFingerprintResult:
    source_snapshot_fingerprint: str
    source_text_hash_index: Mapping[str, object]
    delta_hit: bool


def code_package_text_source_snapshot_fingerprint(
    *,
    package_name: str,
    code_package_config_id: UUID,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    source_texts_by_relative_path: Mapping[str, str],
    source_plans_by_relative_path: Mapping[str, CodeContentPlan],
    unparsed_texts_by_relative_path: Mapping[str, str],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
) -> str:
    return code_package_text_source_snapshot_fingerprint_result(
        code_package_config_id=code_package_config_id,
        package_name=package_name,
        language=language,
        surface=surface,
        manifest_kind=manifest_kind,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
        source_texts_by_relative_path=source_texts_by_relative_path,
        source_plans_by_relative_path=source_plans_by_relative_path,
        unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
        path_roles_by_relative_path=path_roles_by_relative_path,
        previous_snapshot_index_payload=None,
        changed_relative_paths=frozenset(),
    ).source_snapshot_fingerprint


def code_package_text_source_snapshot_fingerprint_result(
    *,
    package_name: str,
    code_package_config_id: UUID,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    source_texts_by_relative_path: Mapping[str, str],
    source_plans_by_relative_path: Mapping[str, CodeContentPlan],
    unparsed_texts_by_relative_path: Mapping[str, str],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
    previous_snapshot_index_payload: Mapping[str, object] | None,
    changed_relative_paths: frozenset[str],
) -> CodePackageSourceSnapshotFingerprintResult:
    with commit_perf_span(
        phase="code_package.source_text_fingerprint.hash_index_previous",
        category="code_package.source_text_fingerprint",
        metadata={
            "changed_path_count": len(changed_relative_paths),
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path),
            "previous_snapshot_index": previous_snapshot_index_payload is not None,
        },
    ):
        source_text_hash_index = code_package_source_text_hash_index_from_previous(
            source_texts_by_relative_path=source_texts_by_relative_path,
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
            previous_snapshot_index_payload=previous_snapshot_index_payload,
            changed_relative_paths=changed_relative_paths,
        )
    delta_hit = source_text_hash_index is not None
    if source_text_hash_index is None:
        with commit_perf_span(
            phase="code_package.source_text_fingerprint.hash_index_full",
            category="code_package.source_text_fingerprint",
            metadata={
                "source_text_count": len(source_texts_by_relative_path),
                "unparsed_text_count": len(unparsed_texts_by_relative_path),
            },
        ):
            source_text_hash_index = code_package_source_text_hash_index_from_inputs(
                source_texts_by_relative_path=source_texts_by_relative_path,
                unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
            )
    with commit_perf_span(
        phase="code_package.source_text_fingerprint.from_hash_index",
        category="code_package.source_text_fingerprint",
        metadata={
            "delta_hit": delta_hit,
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path),
        },
    ):
        source_snapshot_fingerprint = (
            code_package_text_source_snapshot_fingerprint_from_hash_index(
                code_package_config_id=code_package_config_id,
                package_name=package_name,
                language=language,
                surface=surface,
                manifest_kind=manifest_kind,
                manifest_relative_path=manifest_relative_path,
                package_root=package_root,
                sources_root=sources_root,
                fqn_prefix=fqn_prefix,
                source_text_hash_index=source_text_hash_index,
                source_plans_by_relative_path=source_plans_by_relative_path,
                path_roles_by_relative_path=path_roles_by_relative_path,
            )
        )
    return CodePackageSourceSnapshotFingerprintResult(
        source_snapshot_fingerprint=source_snapshot_fingerprint,
        source_text_hash_index=source_text_hash_index,
        delta_hit=delta_hit,
    )


def code_package_text_source_snapshot_fingerprint_from_hash_index(
    *,
    package_name: str,
    code_package_config_id: UUID,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    source_text_hash_index: Mapping[str, object],
    source_plans_by_relative_path: Mapping[str, CodeContentPlan],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
) -> str:
    source_text_hash_index_signature_hash = source_text_hash_index.get(
        "signature_hash",
    )
    if not isinstance(source_text_hash_index_signature_hash, str):
        source_text_hash_index_signature_hash = stable_json_hash(
            {
                str(key): value
                for key, value in source_text_hash_index.items()
                if key != "signature_hash"
            },
        )
    payload = {
        "v": CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
        "fingerprint_kind": "code_package_text_source_snapshot",
        "code_package_config_id": str(code_package_config_id),
        "package_name": (package_name or "").strip(),
        "language": _enum_value(language),
        "surface": surface,
        "manifest_kind": manifest_kind,
        "manifest_relative_path": (manifest_relative_path or "").strip(),
        "package_root": (package_root or "").strip(),
        "sources_root": (sources_root or "").strip() or None,
        "fqn_prefix": (fqn_prefix or "").strip() or None,
        "source_text_hash_index_signature_hash": source_text_hash_index_signature_hash,
        "source_plans": _plan_mapping_payload(source_plans_by_relative_path),
        "path_roles": {
            key: _enum_value(value)
            for key, value in sorted(path_roles_by_relative_path.items())
        },
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def code_package_source_text_hash_index_from_inputs(
    *,
    source_texts_by_relative_path: Mapping[str, str],
    unparsed_texts_by_relative_path: Mapping[str, str],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_SOURCE_TEXT_HASH_INDEX_SCHEMA,
        "source_text_count": len(source_texts_by_relative_path),
        "unparsed_text_count": len(unparsed_texts_by_relative_path),
        "source_texts": _source_text_hash_rows_from_texts(
            source_texts_by_relative_path,
        ),
        "unparsed_texts": _source_text_hash_rows_from_texts(
            unparsed_texts_by_relative_path,
        ),
    }
    payload["signature_hash"] = stable_json_hash(payload)
    return payload


def code_package_source_text_hash_index_from_previous(
    *,
    source_texts_by_relative_path: Mapping[str, str],
    unparsed_texts_by_relative_path: Mapping[str, str],
    previous_snapshot_index_payload: Mapping[str, object] | None,
    changed_relative_paths: frozenset[str],
) -> dict[str, object] | None:
    if not changed_relative_paths or previous_snapshot_index_payload is None:
        return None
    with commit_perf_span(
        phase="code_package.source_text_hash_index.previous_payload",
        category="code_package.source_text_hash_index",
        metadata={"changed_path_count": len(changed_relative_paths)},
    ):
        previous_index = code_package_source_text_hash_index_from_index_payload(
            previous_snapshot_index_payload,
        )
    if previous_index is None:
        return None
    with commit_perf_span(
        phase="code_package.source_text_hash_index.previous_rows_by_path",
        category="code_package.source_text_hash_index",
        metadata={
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path),
        },
    ):
        previous_source_rows = _source_text_hash_rows_by_path(
            previous_index.get("source_texts"),
        )
        previous_unparsed_rows = _source_text_hash_rows_by_path(
            previous_index.get("unparsed_texts"),
        )
    if previous_source_rows is None or previous_unparsed_rows is None:
        return None
    with commit_perf_span(
        phase="code_package.source_text_hash_index.current_path_sets",
        category="code_package.source_text_hash_index",
        metadata={
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path),
        },
    ):
        current_source_paths = {str(key) for key in source_texts_by_relative_path}
        current_unparsed_paths = {str(key) for key in unparsed_texts_by_relative_path}
    if set(previous_source_rows) != current_source_paths:
        return None
    if set(previous_unparsed_rows) != current_unparsed_paths:
        return None
    if not changed_relative_paths.issubset(
        current_source_paths | current_unparsed_paths,
    ):
        return None

    with commit_perf_span(
        phase="code_package.source_text_hash_index.reuse_rows",
        category="code_package.source_text_hash_index",
        metadata={
            "changed_path_count": len(changed_relative_paths),
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path),
        },
    ):
        source_rows = _source_text_hash_rows_reusing_previous(
            texts_by_relative_path=source_texts_by_relative_path,
            previous_rows_by_path=previous_source_rows,
            changed_relative_paths=changed_relative_paths,
        )
        unparsed_rows = _source_text_hash_rows_reusing_previous(
            texts_by_relative_path=unparsed_texts_by_relative_path,
            previous_rows_by_path=previous_unparsed_rows,
            changed_relative_paths=changed_relative_paths,
        )
    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_SOURCE_TEXT_HASH_INDEX_SCHEMA,
        "source_text_count": len(source_rows),
        "unparsed_text_count": len(unparsed_rows),
        "source_texts": source_rows,
        "unparsed_texts": unparsed_rows,
    }
    with commit_perf_span(
        phase="code_package.source_text_hash_index.signature_hash",
        category="code_package.source_text_hash_index",
        metadata={
            "source_text_count": len(source_rows),
            "unparsed_text_count": len(unparsed_rows),
        },
    ):
        payload["signature_hash"] = stable_json_hash(payload)
    return payload


def code_package_source_text_hash_index_from_index_payload(
    payload: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if payload is None:
        return None
    raw_index = payload.get("source_text_hash_index")
    if not isinstance(raw_index, Mapping):
        return None
    if raw_index.get("schema") != CODE_PACKAGE_SOURCE_TEXT_HASH_INDEX_SCHEMA:
        return None
    with commit_perf_span(
        phase="code_package.source_text_hash_index.validate_rows",
        category="code_package.source_text_hash_index",
    ):
        source_rows = _validated_source_text_hash_rows(raw_index.get("source_texts"))
        unparsed_rows = _validated_source_text_hash_rows(
            raw_index.get("unparsed_texts")
        )
    if source_rows is None or unparsed_rows is None:
        return None
    if raw_index.get("source_text_count") != len(source_rows):
        return None
    if raw_index.get("unparsed_text_count") != len(unparsed_rows):
        return None
    result: dict[str, object] = {
        "schema": CODE_PACKAGE_SOURCE_TEXT_HASH_INDEX_SCHEMA,
        "source_text_count": len(source_rows),
        "unparsed_text_count": len(unparsed_rows),
        "source_texts": source_rows,
        "unparsed_texts": unparsed_rows,
    }
    with commit_perf_span(
        phase="code_package.source_text_hash_index.validate_signature_hash",
        category="code_package.source_text_hash_index",
        metadata={
            "source_text_count": len(source_rows),
            "unparsed_text_count": len(unparsed_rows),
        },
    ):
        result["signature_hash"] = stable_json_hash(result)
    if raw_index.get("signature_hash") != result["signature_hash"]:
        return None
    return result


_SOURCE_TEXT_HASH_ROW_KEYS = frozenset({"relative_path", "content_sha256"})


def _source_text_hash_rows_from_texts(
    texts_by_relative_path: Mapping[str, str],
) -> list[dict[str, str]]:
    return [
        {
            "relative_path": str(relative_path),
            "content_sha256": _source_text_content_sha256(content_text),
        }
        for relative_path, content_text in sorted(texts_by_relative_path.items())
    ]


def _source_text_hash_rows_reusing_previous(
    *,
    texts_by_relative_path: Mapping[str, str],
    previous_rows_by_path: Mapping[str, Mapping[str, object]],
    changed_relative_paths: frozenset[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for relative_path, content_text in sorted(texts_by_relative_path.items()):
        path = str(relative_path)
        if path in changed_relative_paths:
            rows.append(
                {
                    "relative_path": path,
                    "content_sha256": _source_text_content_sha256(content_text),
                },
            )
            continue
        previous_row = previous_rows_by_path[path]
        rows.append(
            {
                "relative_path": path,
                "content_sha256": str(previous_row["content_sha256"]),
            },
        )
    return rows


def _validated_source_text_hash_rows(
    raw_rows: object,
) -> list[dict[str, str]] | None:
    if not isinstance(raw_rows, list):
        return None
    rows: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for raw_row in raw_rows:
        row = _validated_source_text_hash_row(raw_row)
        if row is None:
            return None
        relative_path = row["relative_path"]
        if relative_path in seen_paths:
            return None
        seen_paths.add(relative_path)
        rows.append(row)
    return sorted(rows, key=lambda item: item["relative_path"])


def _validated_source_text_hash_row(raw_row: object) -> dict[str, str] | None:
    if not isinstance(raw_row, Mapping):
        return None
    row = {str(key): value for key, value in raw_row.items() if isinstance(key, str)}
    if set(row) != _SOURCE_TEXT_HASH_ROW_KEYS:
        return None
    relative_path = row.get("relative_path")
    content_sha256 = row.get("content_sha256")
    if not isinstance(relative_path, str) or not relative_path.strip():
        return None
    if (
        not isinstance(content_sha256, str)
        or len(content_sha256) != 64
        or any(char not in "0123456789abcdef" for char in content_sha256)
    ):
        return None
    return {
        "relative_path": relative_path,
        "content_sha256": content_sha256,
    }


def _source_text_hash_rows_by_path(
    raw_rows: object,
) -> dict[str, dict[str, str]] | None:
    rows = _validated_source_text_hash_rows(raw_rows)
    if rows is None:
        return None
    return {row["relative_path"]: row for row in rows}


def _source_text_content_sha256(content_text: str) -> str:
    return hashlib.sha256(content_text.encode("utf-8")).hexdigest()


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _plan_mapping_payload(
    value: Mapping[str, CodeContentPlan],
) -> list[dict[str, object]]:
    return [
        {
            "relative_path": str(relative_path),
            "content_plan": plan.model_dump(mode="json", exclude_none=True),
        }
        for relative_path, plan in sorted(value.items())
    ]
