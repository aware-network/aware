from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from aware_code.package.snapshot_contract import (
    CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA,
    CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
    CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
)
from aware_code.package.snapshot_json import (
    atomic_write_json,
    head_string,
    head_uuid,
    read_json_object_or_none,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.perf_trace import commit_perf_span


CODE_PACKAGE_TEXT_SNAPSHOT_SECTION_BUNDLE_SCHEMA = (
    "aware.code.package.text_snapshot_index_sections.v1"
)
CODE_PACKAGE_SOURCE_OBJECT_STATE_SECTION_SCHEMA = (
    "aware.code.package.source_object_state_section.v1"
)
CODE_PACKAGE_SOURCE_OBJECT_PATH_SHARD_SCHEMA = (
    "aware.code.package.source_object_path_shard.v1"
)
_SOURCE_OBJECT_PATH_SHARD_COUNT = 64


def code_package_text_snapshot_index_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
) -> Path:
    return (
        store.aware_root
        / ".aware"
        / "oig"
        / str(branch_id)
        / projection_hash
        / "indexes"
        / "code_package_text_snapshots"
        / f"{code_package_id}.json"
    )


def code_package_text_snapshot_index_sections_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
) -> Path:
    path = code_package_text_snapshot_index_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    )
    return path.with_suffix(".sections.json")


def code_package_text_snapshot_source_object_section_manifest_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    head_commit_id: UUID,
) -> Path:
    return (
        code_package_text_snapshot_index_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
        ).parent
        / "source_object_sections"
        / str(code_package_id)
        / str(head_commit_id)
        / "manifest.json"
    )


def code_package_text_snapshot_source_object_section_shard_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    head_commit_id: UUID,
    shard_index: int,
) -> Path:
    return (
        code_package_text_snapshot_source_object_section_manifest_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            head_commit_id=head_commit_id,
        ).parent
        / "path_shards"
        / f"{shard_index:02d}.json"
    )


async def code_package_text_snapshot_index_hit(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    snapshot_fingerprint: str,
) -> dict[str, object] | None:
    path = code_package_text_snapshot_index_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    )
    payload = read_json_object_or_none(path)
    if payload is None:
        return None
    if payload.get("v") != CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
        return None
    if payload.get("snapshot_fingerprint") != snapshot_fingerprint:
        return None
    if payload.get("code_package_id") != str(code_package_id):
        return None
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    if head is None:
        return None
    if head_string(head, "commit_id") != payload.get("head_commit_id"):
        return None
    if head_string(head, "graph_hash_post") != payload.get("graph_hash_post"):
        return None
    if head_string(head, "object_instance_graph_commit_id") != payload.get(
        "object_instance_graph_commit_id"
    ):
        return None
    if head_string(head, "object_instance_graph_id") != payload.get(
        "object_instance_graph_id"
    ):
        return None
    return payload


def code_package_text_snapshot_index_payload_hit(
    *,
    payload: Mapping[str, object] | None,
    code_package_id: UUID,
    snapshot_fingerprint: str,
) -> dict[str, object] | None:
    if payload is None:
        return None
    if payload.get("v") != CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
        return None
    if payload.get("snapshot_fingerprint") != snapshot_fingerprint:
        return None
    if payload.get("code_package_id") != str(code_package_id):
        return None
    return {str(key): value for key, value in payload.items() if isinstance(key, str)}


async def load_current_code_package_text_snapshot_index_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
) -> dict[str, object] | None:
    store = FSCommitStore()
    _head, payload = (
        await load_current_code_package_text_snapshot_index_payload_with_head(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
        )
    )
    return payload


async def load_current_code_package_text_snapshot_index_payload_with_head(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    include_sections: bool = True,
    include_source_object_index: bool = True,
) -> tuple[Mapping[str, object] | None, dict[str, object] | None]:
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    with commit_perf_span(
        phase="code_package.snapshot_index.read_root",
        category="code_package.snapshot_index",
        metadata={"include_sections": include_sections},
    ):
        payload = read_json_object_or_none(
            code_package_text_snapshot_index_path(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                code_package_id=code_package_id,
            )
        )
    if payload is None:
        return head, None
    with commit_perf_span(
        phase="code_package.snapshot_index.validate_root",
        category="code_package.snapshot_index",
        metadata={"include_sections": include_sections},
    ):
        if not _snapshot_index_payload_matches_head(
            payload=payload,
            head=head,
            code_package_id=code_package_id,
        ):
            return head, None
        if not await _snapshot_index_head_commit_record_readable(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            head=head,
        ):
            return head, None
    result = {str(key): value for key, value in payload.items() if isinstance(key, str)}
    if include_sections and "section_bundle_ref" in result:
        with commit_perf_span(
            phase="code_package.snapshot_index.load_sections",
            category="code_package.snapshot_index",
        ):
            sections = _load_code_package_text_snapshot_index_sections(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                code_package_id=code_package_id,
                root_payload=result,
                include_source_object_index=include_source_object_index,
            )
        if sections is None:
            return head, None
        result.update(sections)
    return head, result


def write_code_package_text_snapshot_index(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    snapshot_fingerprint: str,
    source_snapshot_fingerprint: str,
    commit_id: UUID,
    head_commit_id: UUID,
    object_instance_graph_commit_id: UUID,
    object_instance_graph_id: UUID,
    graph_hash_post: str,
    object_count: int,
    change_count: int,
    artifact_state_index: Mapping[str, object],
    state_snapshot_metadata: Mapping[str, object],
    source_object_state_index: Mapping[str, object],
    source_text_hash_index: Mapping[str, object] | None = None,
) -> None:
    with commit_perf_span(
        phase="code_package.snapshot_commit.write_snapshot_index",
        category="code_package.snapshot_commit",
        metadata={
            "object_count": object_count,
            "change_count": change_count,
        },
    ):
        with commit_perf_span(
            phase="code_package.snapshot_index.build_payload",
            category="code_package.snapshot_index",
            metadata={
                "object_count": object_count,
                "change_count": change_count,
            },
        ):
            section_payload: dict[str, object] = {
                "schema": CODE_PACKAGE_TEXT_SNAPSHOT_SECTION_BUNDLE_SCHEMA,
                "v": CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
                "code_package_id": str(code_package_id),
                "head_commit_id": str(head_commit_id),
                "artifact_state_index": dict(artifact_state_index),
            }
            source_object_state_index_ref = (
                _write_code_package_source_object_state_section(
                    store=store,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    code_package_id=code_package_id,
                    head_commit_id=head_commit_id,
                    source_object_state_index=source_object_state_index,
                )
            )
            section_payload["source_object_state_index_ref"] = (
                source_object_state_index_ref
            )
            if source_text_hash_index is not None:
                section_payload["source_text_hash_index"] = dict(source_text_hash_index)
            payload: dict[str, object] = {
                "v": CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
                "snapshot_fingerprint": snapshot_fingerprint,
                "source_snapshot_fingerprint": source_snapshot_fingerprint,
                "code_package_id": str(code_package_id),
                "commit_id": str(commit_id),
                "head_commit_id": str(head_commit_id),
                "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
                "object_instance_graph_id": str(object_instance_graph_id),
                "graph_hash_post": graph_hash_post,
                "object_count": object_count,
                "change_count": change_count,
                "state_snapshot": dict(state_snapshot_metadata),
                "section_bundle_ref": {
                    "schema": CODE_PACKAGE_TEXT_SNAPSHOT_SECTION_BUNDLE_SCHEMA,
                    "path": code_package_text_snapshot_index_sections_path(
                        store=store,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        code_package_id=code_package_id,
                    ).name,
                },
            }
        path = code_package_text_snapshot_index_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
        )
        section_path = code_package_text_snapshot_index_sections_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
        )
        with commit_perf_span(
            phase="code_package.snapshot_index.write_sections",
            category="code_package.snapshot_index",
            metadata={
                "object_count": object_count,
                "change_count": change_count,
            },
        ):
            atomic_write_json(
                section_path,
                section_payload,
                sort_keys=False,
                phase_prefix="code_package.snapshot_index.write_sections",
                category="code_package.snapshot_index",
                metadata={
                    "object_count": object_count,
                    "change_count": change_count,
                },
            )
        with commit_perf_span(
            phase="code_package.snapshot_index.write_payload",
            category="code_package.snapshot_index",
            metadata={
                "object_count": object_count,
                "change_count": change_count,
            },
        ):
            atomic_write_json(
                path,
                payload,
                sort_keys=False,
                phase_prefix="code_package.snapshot_index.write_payload",
                category="code_package.snapshot_index",
                metadata={
                    "object_count": object_count,
                    "change_count": change_count,
                },
            )


def _snapshot_index_payload_matches_head(
    *,
    payload: Mapping[str, object],
    head: Mapping[str, object] | None,
    code_package_id: UUID,
) -> bool:
    if payload.get("v") != CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
        return False
    if payload.get("code_package_id") != str(code_package_id):
        return False
    if head is None:
        return False
    if head_string(head, "commit_id") != payload.get("head_commit_id"):
        return False
    if head_string(head, "graph_hash_post") != payload.get("graph_hash_post"):
        return False
    if head_string(head, "object_instance_graph_commit_id") != payload.get(
        "object_instance_graph_commit_id"
    ):
        return False
    if head_string(head, "object_instance_graph_id") != payload.get(
        "object_instance_graph_id"
    ):
        return False
    return True


async def _snapshot_index_head_commit_record_readable(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    head: Mapping[str, object] | None,
) -> bool:
    head_commit_id = head_uuid(head, "commit_id")
    if head_commit_id is None:
        return False
    get_commit_health_metadata = getattr(store, "get_commit_health_metadata", None)
    if get_commit_health_metadata is not None:
        health = await get_commit_health_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
        if health is not None:
            return (
                health.commit_id == head_commit_id
                and health.graph_hash_post == head_string(head, "graph_hash_post")
                and str(health.object_instance_graph_id)
                == head_string(head, "object_instance_graph_id")
            )
    get_commit_record = getattr(store, "get_commit_record", None)
    if get_commit_record is None:
        return True
    return (
        await get_commit_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
        is not None
    )


def _load_code_package_text_snapshot_index_sections(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    root_payload: Mapping[str, object],
    include_source_object_index: bool,
) -> dict[str, object] | None:
    raw_ref = root_payload.get("section_bundle_ref")
    if not isinstance(raw_ref, Mapping):
        return None
    ref = {str(key): value for key, value in raw_ref.items() if isinstance(key, str)}
    if ref.get("schema") != CODE_PACKAGE_TEXT_SNAPSHOT_SECTION_BUNDLE_SCHEMA:
        return None
    if (
        ref.get("path")
        != code_package_text_snapshot_index_sections_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
        ).name
    ):
        return None
    with commit_perf_span(
        phase="code_package.snapshot_index.read_sections",
        category="code_package.snapshot_index",
    ):
        payload = read_json_object_or_none(
            code_package_text_snapshot_index_sections_path(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                code_package_id=code_package_id,
            )
        )
    if payload is None:
        return None
    with commit_perf_span(
        phase="code_package.snapshot_index.validate_sections",
        category="code_package.snapshot_index",
    ):
        if payload.get("schema") != CODE_PACKAGE_TEXT_SNAPSHOT_SECTION_BUNDLE_SCHEMA:
            return None
        if payload.get("v") != CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
            return None
        if payload.get("code_package_id") != str(code_package_id):
            return None
        if payload.get("head_commit_id") != root_payload.get("head_commit_id"):
            return None
        result: dict[str, object] = {}
        for key in ("artifact_state_index", "source_text_hash_index"):
            value = payload.get(key)
            if value is not None:
                result[key] = value
        source_object_ref = payload.get("source_object_state_index_ref")
        if isinstance(source_object_ref, Mapping):
            result["source_object_state_index_ref"] = {
                str(key): value
                for key, value in source_object_ref.items()
                if isinstance(key, str)
            }
            if include_source_object_index:
                source_object_index = (
                    load_code_package_text_snapshot_source_object_state_index_from_ref(
                        store=store,
                        branch_id=branch_id,
                        projection_hash=projection_hash,
                        code_package_id=code_package_id,
                        snapshot_index_payload={**root_payload, **result},
                    )
                )
                if source_object_index is not None:
                    result["source_object_state_index"] = source_object_index
        else:
            value = payload.get("source_object_state_index")
            if value is not None:
                result["source_object_state_index"] = value
        if "artifact_state_index" not in result:
            return None
        if (
            "source_object_state_index" not in result
            and "source_object_state_index_ref" not in result
        ):
            return None
    return result


def load_code_package_text_snapshot_source_object_state_index_selected(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    snapshot_index_payload: Mapping[str, object],
    relative_paths: frozenset[str],
) -> dict[str, object] | None:
    return load_code_package_text_snapshot_source_object_state_index_from_ref(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        snapshot_index_payload=snapshot_index_payload,
        relative_paths=relative_paths,
    )


def load_code_package_text_snapshot_source_object_state_index_from_ref(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    snapshot_index_payload: Mapping[str, object],
    relative_paths: frozenset[str] | None = None,
) -> dict[str, object] | None:
    raw_ref = snapshot_index_payload.get("source_object_state_index_ref")
    if not isinstance(raw_ref, Mapping):
        return None
    ref = {str(key): value for key, value in raw_ref.items() if isinstance(key, str)}
    if ref.get("schema") != CODE_PACKAGE_SOURCE_OBJECT_STATE_SECTION_SCHEMA:
        return None
    manifest_path = _source_object_ref_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        ref=ref,
    )
    if manifest_path is None:
        return None
    with commit_perf_span(
        phase="code_package.snapshot_index.source_object_section.read_manifest",
        category="code_package.snapshot_index",
        metadata={
            "selected_path_count": 0 if relative_paths is None else len(relative_paths)
        },
    ):
        manifest = read_json_object_or_none(manifest_path)
    if manifest is None:
        return None
    manifest_payload = {
        str(key): value for key, value in manifest.items() if isinstance(key, str)
    }
    if not _source_object_section_manifest_matches(
        manifest=manifest_payload,
        root_payload=snapshot_index_payload,
        code_package_id=code_package_id,
    ):
        return None
    if relative_paths is None:
        selected_paths = None
        shard_index_values = tuple(range(_SOURCE_OBJECT_PATH_SHARD_COUNT))
    else:
        selected_paths = {
            relative_path.strip().strip("/")
            for relative_path in relative_paths
            if relative_path.strip().strip("/")
        }
        if not selected_paths:
            return None
        shard_index_values = tuple(
            sorted(
                {
                    _source_object_path_shard_index(relative_path)
                    for relative_path in selected_paths
                }
            )
        )
    path_rows: list[dict[str, object]] = []
    objects_by_id: dict[str, dict[str, object]] = {}
    for raw_item in (manifest_payload.get("root_object"),):
        if isinstance(raw_item, Mapping):
            root_row = {
                str(key): value
                for key, value in raw_item.items()
                if isinstance(key, str)
            }
            source_object_id = root_row.get("source_object_id")
            if isinstance(source_object_id, str):
                objects_by_id[source_object_id] = root_row
    try:
        with commit_perf_span(
            phase="code_package.snapshot_index.source_object_section.read_path_shards",
            category="code_package.snapshot_index",
            metadata={
                "selected_path_count": (
                    0 if selected_paths is None else len(selected_paths)
                ),
                "shard_count": len(shard_index_values),
            },
        ):
            for shard_index in shard_index_values:
                shard_payload = _load_source_object_path_shard(
                    store=store,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    code_package_id=code_package_id,
                    manifest=manifest_payload,
                    shard_index=int(shard_index),
                )
                if shard_payload is None:
                    continue
                for item in shard_payload:
                    relative_path = (
                        str(item.get("relative_path", "")).strip().strip("/")
                    )
                    if not relative_path:
                        return None
                    if (
                        selected_paths is not None
                        and relative_path not in selected_paths
                    ):
                        continue
                    raw_source_object_ids = item.get("source_object_ids")
                    raw_objects = item.get("objects")
                    if not isinstance(raw_source_object_ids, list) or not isinstance(
                        raw_objects,
                        list,
                    ):
                        return None
                    path_rows.append(
                        {
                            "relative_path": relative_path,
                            "source_object_ids": [
                                str(UUID(str(source_object_id)))
                                for source_object_id in raw_source_object_ids
                            ],
                        }
                    )
                    for raw_object in raw_objects:
                        if not isinstance(raw_object, Mapping):
                            return None
                        object_row = {
                            str(key): value
                            for key, value in raw_object.items()
                            if isinstance(key, str)
                        }
                        source_object_id = object_row.get("source_object_id")
                        if not isinstance(source_object_id, str):
                            return None
                        objects_by_id[str(UUID(source_object_id))] = object_row
    except Exception:
        return None
    if (
        selected_paths is not None
        and {str(row["relative_path"]) for row in path_rows} != selected_paths
    ):
        return None
    source_index_schema = str(
        manifest_payload.get("source_index_schema")
        or CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
    )
    selected = selected_paths is not None
    schema = (
        CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA
        if selected
        else source_index_schema
    )
    payload: dict[str, object] = {
        "schema": schema,
        "object_count": _payload_int_value(manifest_payload.get("object_count")),
        "objects": [row for _source_object_id, row in sorted(objects_by_id.items())],
        "path_source_object_index": sorted(
            path_rows,
            key=lambda item: str(item["relative_path"]),
        ),
    }
    if schema == CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA:
        payload["base_schema"] = str(
            manifest_payload.get("base_schema")
            or CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
        )
        payload["changed_object_count"] = len(payload["objects"])
        payload["changed_path_count"] = len(path_rows)
    return payload


def _write_code_package_source_object_state_section(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    head_commit_id: UUID,
    source_object_state_index: Mapping[str, object],
) -> dict[str, object]:
    source_index = {
        str(key): value
        for key, value in source_object_state_index.items()
        if isinstance(key, str)
    }
    source_index_schema = str(
        source_index.get("schema") or CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA
    )
    object_rows = _source_object_index_object_rows(source_index)
    object_rows_by_id = {
        str(row["source_object_id"]): row
        for row in object_rows
        if isinstance(row.get("source_object_id"), str)
    }
    path_rows = _source_object_index_path_rows(source_index)
    root_object = object_rows_by_id.get(str(code_package_id))
    manifest_path = code_package_text_snapshot_source_object_section_manifest_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        head_commit_id=head_commit_id,
    )
    with commit_perf_span(
        phase="code_package.snapshot_index.write_source_object_sections",
        category="code_package.snapshot_index",
        metadata={
            "object_count": len(object_rows),
            "path_count": len(path_rows),
        },
    ):
        shards: dict[int, list[dict[str, object]]] = {}
        for path_row in path_rows:
            relative_path = str(path_row["relative_path"])
            source_object_ids = tuple(
                str(UUID(str(source_object_id)))
                for source_object_id in path_row["source_object_ids"]
            )
            shard_index = _source_object_path_shard_index(relative_path)
            shards.setdefault(shard_index, []).append(
                {
                    "relative_path": relative_path,
                    "source_object_ids": list(source_object_ids),
                    "objects": [
                        object_rows_by_id[source_object_id]
                        for source_object_id in source_object_ids
                        if source_object_id in object_rows_by_id
                    ],
                }
            )
        for shard_index, rows in sorted(shards.items()):
            shard_payload = {
                "schema": CODE_PACKAGE_SOURCE_OBJECT_PATH_SHARD_SCHEMA,
                "v": CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
                "code_package_id": str(code_package_id),
                "head_commit_id": str(head_commit_id),
                "shard_index": shard_index,
                "paths": sorted(rows, key=lambda item: str(item["relative_path"])),
            }
            atomic_write_json(
                code_package_text_snapshot_source_object_section_shard_path(
                    store=store,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    code_package_id=code_package_id,
                    head_commit_id=head_commit_id,
                    shard_index=shard_index,
                ),
                shard_payload,
                sort_keys=False,
                phase_prefix="code_package.snapshot_index.write_source_object_shard",
                category="code_package.snapshot_index",
                metadata={"shard_index": shard_index, "path_count": len(rows)},
            )
        manifest_payload: dict[str, object] = {
            "schema": CODE_PACKAGE_SOURCE_OBJECT_STATE_SECTION_SCHEMA,
            "v": CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
            "code_package_id": str(code_package_id),
            "head_commit_id": str(head_commit_id),
            "source_index_schema": source_index_schema,
            "base_schema": source_index.get(
                "base_schema",
                CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
            ),
            "object_count": _source_object_index_count(source_index),
            "path_count": len(path_rows),
            "shard_count": _SOURCE_OBJECT_PATH_SHARD_COUNT,
        }
        if root_object is not None:
            manifest_payload["root_object"] = root_object
        atomic_write_json(
            manifest_path,
            manifest_payload,
            sort_keys=False,
            phase_prefix="code_package.snapshot_index.write_source_object_manifest",
            category="code_package.snapshot_index",
            metadata={
                "object_count": len(object_rows),
                "path_count": len(path_rows),
            },
        )
    return {
        "schema": CODE_PACKAGE_SOURCE_OBJECT_STATE_SECTION_SCHEMA,
        "path": _source_object_ref_relative_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            head_commit_id=head_commit_id,
        ),
    }


def _source_object_ref_relative_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    head_commit_id: UUID,
) -> str:
    base = code_package_text_snapshot_index_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    ).parent
    return (
        code_package_text_snapshot_source_object_section_manifest_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            head_commit_id=head_commit_id,
        )
        .relative_to(base)
        .as_posix()
    )


def _source_object_ref_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    ref: Mapping[str, object],
) -> Path | None:
    raw_path = ref.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        return None
    relative_path = Path(raw_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return None
    base = code_package_text_snapshot_index_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    ).parent
    return base / relative_path


def _source_object_section_manifest_matches(
    *,
    manifest: Mapping[str, object],
    root_payload: Mapping[str, object],
    code_package_id: UUID,
) -> bool:
    if manifest.get("schema") != CODE_PACKAGE_SOURCE_OBJECT_STATE_SECTION_SCHEMA:
        return False
    if manifest.get("v") != CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
        return False
    if manifest.get("code_package_id") != str(code_package_id):
        return False
    if manifest.get("head_commit_id") != root_payload.get("head_commit_id"):
        return False
    if _payload_int_value(manifest.get("object_count")) < 0:
        return False
    return True


def _load_source_object_path_shard(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    manifest: Mapping[str, object],
    shard_index: int,
) -> tuple[dict[str, object], ...] | None:
    head_commit_id = UUID(str(manifest["head_commit_id"]))
    payload = read_json_object_or_none(
        code_package_text_snapshot_source_object_section_shard_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            head_commit_id=head_commit_id,
            shard_index=shard_index,
        )
    )
    if payload is None:
        return ()
    if payload.get("schema") != CODE_PACKAGE_SOURCE_OBJECT_PATH_SHARD_SCHEMA:
        return None
    if payload.get("v") != CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
        return None
    if payload.get("code_package_id") != str(code_package_id):
        return None
    if payload.get("head_commit_id") != manifest.get("head_commit_id"):
        return None
    if payload.get("shard_index") != shard_index:
        return None
    raw_paths = payload.get("paths")
    if not isinstance(raw_paths, list):
        return None
    rows: list[dict[str, object]] = []
    for raw_item in raw_paths:
        if not isinstance(raw_item, Mapping):
            return None
        rows.append(
            {str(key): value for key, value in raw_item.items() if isinstance(key, str)}
        )
    return tuple(rows)


def _source_object_index_object_rows(
    source_index: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    raw_objects = source_index.get("objects")
    if not isinstance(raw_objects, list):
        return ()
    rows: list[dict[str, object]] = []
    for raw_item in raw_objects:
        if not isinstance(raw_item, Mapping):
            continue
        item = {
            str(key): value for key, value in raw_item.items() if isinstance(key, str)
        }
        try:
            item["source_object_id"] = str(UUID(str(item["source_object_id"])))
            item["class_config_id"] = str(UUID(str(item["class_config_id"])))
            item["class_instance_id"] = str(UUID(str(item["class_instance_id"])))
        except Exception:
            continue
        signature_hash = item.get("signature_hash")
        if not isinstance(signature_hash, str) or not signature_hash:
            continue
        rows.append(item)
    return tuple(sorted(rows, key=lambda item: str(item["source_object_id"])))


def _source_object_index_path_rows(
    source_index: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    raw_path_index = source_index.get("path_source_object_index")
    if not isinstance(raw_path_index, list):
        return ()
    rows: list[dict[str, object]] = []
    for raw_item in raw_path_index:
        if not isinstance(raw_item, Mapping):
            continue
        item = {
            str(key): value for key, value in raw_item.items() if isinstance(key, str)
        }
        relative_path = str(item.get("relative_path", "")).strip().strip("/")
        raw_source_object_ids = item.get("source_object_ids")
        if not relative_path or not isinstance(raw_source_object_ids, list):
            continue
        try:
            source_object_ids = [
                str(UUID(str(source_object_id)))
                for source_object_id in raw_source_object_ids
            ]
        except Exception:
            continue
        rows.append(
            {
                "relative_path": relative_path,
                "source_object_ids": sorted(set(source_object_ids)),
            }
        )
    return tuple(sorted(rows, key=lambda item: str(item["relative_path"])))


def _source_object_index_count(source_index: Mapping[str, object]) -> int:
    raw_count = source_index.get("object_count")
    if isinstance(raw_count, int):
        return raw_count
    return len(_source_object_index_object_rows(source_index))


def _source_object_path_shard_index(relative_path: str) -> int:
    digest = hashlib.sha256(relative_path.encode("utf-8")).digest()
    return int.from_bytes(digest[:2], "big") % _SOURCE_OBJECT_PATH_SHARD_COUNT


def _payload_int_value(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    return 0
