from __future__ import annotations

import pytest

from aware_storage.handlers.impl.blob import storage_blob as storage_blob_handler
from aware_storage.stable_ids import stable_storage_blob_id

from aware_storage_ontology.blob.storage_blob import StorageBlob


@pytest.mark.asyncio
async def test_storage_blob_create_uses_cached_lookup_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha = "a" * 64
    blob_id = stable_storage_blob_id(sha=sha)
    existing = StorageBlob(
        id=blob_id,
        sha=sha,
        mime_type="text/plain",
        size_bytes=12,
        object_key=f"{sha[:2]}/{sha[2:]}",
        path_local=None,
        bucket_id=None,
    )
    seen: dict[str, object] = {}

    def _fake_get_by_id_cached(cls, obj_id):  # noqa: ANN001
        seen["obj_id"] = obj_id
        return existing

    async def _forbidden_get_by_id(cls, obj_id, cache_valid: bool = True, eager: bool = True):  # noqa: ANN001
        raise AssertionError("create must not call async get_by_id in write path")

    monkeypatch.setattr(StorageBlob, "get_by_id_cached", classmethod(_fake_get_by_id_cached))
    monkeypatch.setattr(StorageBlob, "get_by_id", classmethod(_forbidden_get_by_id))

    result = await storage_blob_handler.create(sha=sha, mime_type="text/plain", size_bytes=12)

    assert result is existing
    assert seen["obj_id"] == blob_id


@pytest.mark.asyncio
async def test_storage_blob_create_builds_new_blob_on_cache_miss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sha_input = "B" * 64
    normalized_sha = sha_input.lower()
    expected_blob_id = stable_storage_blob_id(sha=normalized_sha)
    seen: dict[str, object] = {}

    def _fake_get_by_id_cached(cls, obj_id):  # noqa: ANN001
        seen["obj_id"] = obj_id
        return None

    async def _forbidden_get_by_id(cls, obj_id, cache_valid: bool = True, eager: bool = True):  # noqa: ANN001
        raise AssertionError("create must not call async get_by_id in write path")

    monkeypatch.setattr(StorageBlob, "get_by_id_cached", classmethod(_fake_get_by_id_cached))
    monkeypatch.setattr(StorageBlob, "get_by_id", classmethod(_forbidden_get_by_id))

    result = await storage_blob_handler.create(sha=sha_input, mime_type=" ", size_bytes=0)

    assert seen["obj_id"] == expected_blob_id
    assert result.id == expected_blob_id
    assert result.sha == normalized_sha
    assert result.mime_type == "application/octet-stream"
    assert result.size_bytes == 0
    assert result.object_key == f"{normalized_sha[:2]}/{normalized_sha[2:]}"
