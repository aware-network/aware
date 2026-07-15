from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_identity.handlers.impl.identity import (
    identity_profile as identity_profile_impl,
)


class _StubIdentityProfile:
    def __init__(self) -> None:
        self.bio = None
        self.country_code = "US"
        self.language_code = "en"
        self.image_id = None
        self.image = None


@pytest.mark.asyncio
async def test_update_country_normalizes_and_validates() -> None:
    profile = _StubIdentityProfile()

    await identity_profile_impl.update_country(profile, " br ")
    assert profile.country_code == "BR"

    with pytest.raises(ValueError):
        await identity_profile_impl.update_country(profile, "brazil")


@pytest.mark.asyncio
async def test_update_language_normalizes_and_validates() -> None:
    profile = _StubIdentityProfile()

    await identity_profile_impl.update_language(profile, " PT ")
    assert profile.language_code == "pt"

    with pytest.raises(ValueError):
        await identity_profile_impl.update_language(profile, "portuguese")


@pytest.mark.asyncio
async def test_update_picture_clears_when_all_args_are_null() -> None:
    profile = _StubIdentityProfile()
    profile.image_id = uuid4()
    profile.image = object()

    await identity_profile_impl.update_picture(profile)

    assert profile.image_id is None
    assert profile.image is None


@pytest.mark.asyncio
async def test_update_picture_requires_complete_metadata() -> None:
    profile = _StubIdentityProfile()

    with pytest.raises(ValueError):
        await identity_profile_impl.update_picture(
            profile,
            image_sha="a" * 64,
            image_mime_type="image/png",
        )

    with pytest.raises(ValueError):
        await identity_profile_impl.update_picture(
            profile,
            image_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_update_picture_creates_blob_and_sets_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _StubIdentityProfile()
    blob_id = uuid4()
    fake_blob = SimpleNamespace(id=blob_id)

    async def _fake_create(*, sha: str, mime_type: str, size_bytes: int):
        assert sha == "a" * 64
        assert mime_type == "image/png"
        assert size_bytes == 42
        return fake_blob

    monkeypatch.setattr(identity_profile_impl.StorageBlob, "create", _fake_create)

    await identity_profile_impl.update_picture(
        profile,
        image_id=blob_id,
        image_sha="a" * 64,
        image_mime_type="image/png",
        image_size_bytes=42,
    )

    assert profile.image_id == blob_id
    assert profile.image is fake_blob


@pytest.mark.asyncio
async def test_update_picture_rejects_image_id_sha_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _StubIdentityProfile()
    blob_id = uuid4()
    fake_blob = SimpleNamespace(id=blob_id)

    async def _fake_create(*, sha: str, mime_type: str, size_bytes: int):
        return fake_blob

    monkeypatch.setattr(identity_profile_impl.StorageBlob, "create", _fake_create)

    with pytest.raises(ValueError, match="image_id does not match StorageBlob.id"):
        await identity_profile_impl.update_picture(
            profile,
            image_id=uuid4(),
            image_sha="a" * 64,
            image_mime_type="image/png",
            image_size_bytes=42,
        )
