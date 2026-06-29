from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

import aware_storage.utils as storage_utils
from aware_storage.blob_store import LocalBlobStore, compute_blob_hash

from aware_storage_ontology.bucket.storage_bucket import StorageBucket
from aware_storage_ontology.blob.storage_blob import StorageBlob
from aware_storage_ontology.bucket.storage_bucket_enums import StorageBackend


@pytest.mark.asyncio
async def test_download_blob_bytes_reads_from_local_blob_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    storage_utils.clear_blob_store_cache()
    storage_utils.set_blob_access_checker(None)

    content = b"hello-storage"
    sha = compute_blob_hash(content)

    root = tmp_path / "blobs"
    store = LocalBlobStore(root)
    store.put(sha, content)

    bucket = StorageBucket(
        id=uuid4(),
        name="test_bucket",
        backend=StorageBackend.local,
        config={"path_local": str(root)},
    )
    blob_id = uuid4()
    blob = StorageBlob(
        id=blob_id,
        sha=sha,
        size_bytes=len(content),
        mime_type="application/octet-stream",
        bucket=bucket,
        bucket_id=bucket.id,
        object_key=f"{sha[:2]}/{sha[2:]}",
        path_local=str(store._blob_path(sha)),  # type: ignore[attr-defined]
    )

    async def _fake_get_by_id(cls, obj_id, cache_valid: bool = True, eager: bool = True):  # noqa: ANN001
        return blob if obj_id == blob_id else None

    monkeypatch.setattr(StorageBlob, "get_by_id", classmethod(_fake_get_by_id))

    data = await storage_utils.download_blob_bytes(finance_entity_id=uuid4(), object_id=blob_id)
    assert data == content


@pytest.mark.asyncio
async def test_download_blob_bytes_calls_access_checker(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    storage_utils.clear_blob_store_cache()

    content = b"hello-access"
    sha = compute_blob_hash(content)

    root = tmp_path / "blobs"
    store = LocalBlobStore(root)
    store.put(sha, content)

    bucket = StorageBucket(
        id=uuid4(),
        name="test_bucket",
        backend=StorageBackend.local,
        config={"path_local": str(root)},
    )
    blob_id = uuid4()
    blob = StorageBlob(
        id=blob_id,
        sha=sha,
        size_bytes=len(content),
        mime_type="application/octet-stream",
        bucket=bucket,
        bucket_id=bucket.id,
        object_key=f"{sha[:2]}/{sha[2:]}",
        path_local=str(store._blob_path(sha)),  # type: ignore[attr-defined]
    )

    async def _fake_get_by_id(cls, obj_id, cache_valid: bool = True, eager: bool = True):  # noqa: ANN001
        return blob if obj_id == blob_id else None

    monkeypatch.setattr(StorageBlob, "get_by_id", classmethod(_fake_get_by_id))

    seen: dict[str, object] = {}

    async def _checker(finance_entity_id, checked_blob):  # noqa: ANN001
        seen["finance_entity_id"] = finance_entity_id
        seen["blob_id"] = checked_blob.id

    storage_utils.set_blob_access_checker(_checker)
    finance_entity_id = uuid4()
    data = await storage_utils.download_blob_bytes(finance_entity_id=finance_entity_id, object_id=blob_id)

    assert data == content
    assert seen["finance_entity_id"] == finance_entity_id
    assert seen["blob_id"] == blob_id


@pytest.mark.asyncio
async def test_download_file_writes_bytes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    storage_utils.clear_blob_store_cache()
    storage_utils.set_blob_access_checker(None)

    content = b"hello-file"
    sha = compute_blob_hash(content)

    root = tmp_path / "blobs"
    store = LocalBlobStore(root)
    store.put(sha, content)

    bucket = StorageBucket(
        id=uuid4(),
        name="test_bucket",
        backend=StorageBackend.local,
        config={"path_local": str(root)},
    )
    blob_id = uuid4()
    blob = StorageBlob(
        id=blob_id,
        sha=sha,
        size_bytes=len(content),
        mime_type="application/octet-stream",
        bucket=bucket,
        bucket_id=bucket.id,
        object_key=f"{sha[:2]}/{sha[2:]}",
        path_local=str(store._blob_path(sha)),  # type: ignore[attr-defined]
    )

    async def _fake_get_by_id(cls, obj_id, cache_valid: bool = True, eager: bool = True):  # noqa: ANN001
        return blob if obj_id == blob_id else None

    monkeypatch.setattr(StorageBlob, "get_by_id", classmethod(_fake_get_by_id))

    out_path = tmp_path / "out.bin"
    saved = await storage_utils.download_file(finance_entity_id=uuid4(), object_id=blob_id, save_path=str(out_path))
    assert saved == str(out_path)
    assert out_path.read_bytes() == content


@pytest.mark.asyncio
async def test_download_blob_bytes_raises_for_missing_blob(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage_utils.clear_blob_store_cache()
    storage_utils.set_blob_access_checker(None)

    async def _fake_get_by_id(cls, obj_id, cache_valid: bool = True, eager: bool = True):  # noqa: ANN001
        return None

    monkeypatch.setattr(StorageBlob, "get_by_id", classmethod(_fake_get_by_id))

    with pytest.raises(FileNotFoundError):
        await storage_utils.download_blob_bytes(finance_entity_id=uuid4(), object_id=uuid4())
