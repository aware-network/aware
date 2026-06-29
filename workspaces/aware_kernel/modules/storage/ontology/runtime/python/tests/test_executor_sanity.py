from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import asyncio
from pathlib import Path
import threading

import pytest

import aware_storage.utils as storage_utils
from aware_storage.blob_store import LocalBlobStore, compute_blob_hash


_GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aware-storage-global-test")


@pytest.mark.asyncio
async def test_run_in_executor_returns_value() -> None:
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aware-storage-test")
    try:
        result = await loop.run_in_executor(executor, lambda: 123)
    finally:
        executor.shutdown(wait=True, cancel_futures=True)

    assert result == 123


@pytest.mark.asyncio
async def test_run_in_executor_with_global_executor() -> None:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(_GLOBAL_EXECUTOR, lambda: 456)
    assert result == 456


@pytest.mark.asyncio
async def test_run_in_executor_bytes_result_with_storage_executor() -> None:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(storage_utils._get_executor(), lambda: b"hello")  # type: ignore[attr-defined]
    assert result == b"hello"


@pytest.mark.asyncio
async def test_local_blob_store_get_in_storage_executor(tmp_path: Path) -> None:
    content = b"hello"
    sha = compute_blob_hash(content)

    store = LocalBlobStore(tmp_path / "blobs")
    store.put(sha, content)

    loop = asyncio.get_running_loop()
    executor = storage_utils._get_executor()  # type: ignore[attr-defined]
    cf = executor.submit(store.get, sha)

    def _on_done(_: object) -> None:
        print(
            "concurrent future done on",
            threading.current_thread().name,
            "loop.is_closed=",
            loop.is_closed(),
        )

    cf.add_done_callback(_on_done)
    data = await asyncio.wrap_future(cf, loop=loop)
    assert data == content
