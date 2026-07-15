from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_environment.handlers.impl.environment import (
    environment as environment_impl,
)
from aware_environment.handlers.impl.process import (
    process as process_impl,
)
from aware_environment.handlers.impl.process import (
    process_config as process_config_impl,
)
from aware_environment.handlers.impl.thread import (
    thread as thread_impl,
)
from aware_environment.handlers.impl.thread import (
    thread_config as thread_config_impl,
)


class _StubWithImage:
    def __init__(self) -> None:
        self.image_id = None
        self.image = None


_IMPLS = [
    ("process_config", process_config_impl),
    ("thread_config", thread_config_impl),
    ("environment", environment_impl),
    ("process", process_impl),
    ("thread", thread_impl),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "impl", [impl for _, impl in _IMPLS], ids=[name for name, _ in _IMPLS]
)
async def test_update_picture_clears_when_all_args_are_null(impl) -> None:
    target = _StubWithImage()
    target.image_id = uuid4()
    target.image = object()

    await impl.update_picture(target)

    assert target.image_id is None
    assert target.image is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "impl", [impl for _, impl in _IMPLS], ids=[name for name, _ in _IMPLS]
)
async def test_update_picture_requires_complete_metadata(impl) -> None:
    target = _StubWithImage()

    with pytest.raises(ValueError):
        await impl.update_picture(
            target,
            image_sha="a" * 64,
            image_mime_type="image/png",
        )

    with pytest.raises(ValueError):
        await impl.update_picture(
            target,
            image_id=uuid4(),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "impl", [impl for _, impl in _IMPLS], ids=[name for name, _ in _IMPLS]
)
async def test_update_picture_creates_blob_and_sets_reference(
    impl, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _StubWithImage()
    blob_id = uuid4()
    fake_blob = SimpleNamespace(id=blob_id)

    async def _fake_create(*, sha: str, mime_type: str, size_bytes: int):
        assert sha == "a" * 64
        assert mime_type == "image/png"
        assert size_bytes == 42
        return fake_blob

    monkeypatch.setattr(impl.StorageBlob, "create", _fake_create)

    await impl.update_picture(
        target,
        image_id=blob_id,
        image_sha="a" * 64,
        image_mime_type="image/png",
        image_size_bytes=42,
    )

    assert target.image_id == blob_id
    assert target.image is fake_blob


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "impl", [impl for _, impl in _IMPLS], ids=[name for name, _ in _IMPLS]
)
async def test_update_picture_rejects_image_id_sha_mismatch(
    impl, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _StubWithImage()
    blob_id = uuid4()
    fake_blob = SimpleNamespace(id=blob_id)

    async def _fake_create(*, sha: str, mime_type: str, size_bytes: int):
        return fake_blob

    monkeypatch.setattr(impl.StorageBlob, "create", _fake_create)

    with pytest.raises(ValueError, match="image_id does not match StorageBlob.id"):
        await impl.update_picture(
            target,
            image_id=uuid4(),
            image_sha="a" * 64,
            image_mime_type="image/png",
            image_size_bytes=42,
        )
